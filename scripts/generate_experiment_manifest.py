"""Capture measured local validation evidence and verify the final artifact hashes."""
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET

import torch

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ['torch','pandas','numpy','scipy','scikit-learn','matplotlib','seaborn',
            'pypdf','pymupdf','pytest','pypandoc_binary','beautifulsoup4']
PATTERNS = [
    'src/**/*.py','scripts/*.py','tests/**/*.py','results/diagnostics/*',
    'results/metrics/*','results/tables/*','results/figures/*','paper/**/*','app/*',
    'data/metadata/*.json','docs/*AUDIT.md','docs/MANUSCRIPT_CONSISTENCY_VALIDATION.md',
    'docs/FINAL_RESEARCH_READINESS_MATRIX.md','README.md','requirements.txt','pyproject.toml',
    '.github/workflows/*','results/runs/final_tests.xml','results/runs/execution.json',
    'results/runs/ancillary_execution.json','results/exploratory/sirhan_external/*',
    'results/exploratory/published_global_comparison.csv','docs/EXTERNAL_SIRHAN_COMPARISON.md',
    'results/runs/external_validation.json','antigravity.md'
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding='utf8'))

def test_counts(report):
    counts = {}
    for case in ET.parse(report).iter('testcase'):
        name = case.get('classname').split('.')
        group = 'integration' if 'integration' in name else 'unit' if 'unit' in name else 'legacy'
        status = next((s for s in ('failure','error','skipped') if case.find(s) is not None),'passed')
        outcomes = counts.setdefault(group,{})
        outcomes[status] = outcomes.get(status,0)+1
    return counts

def main():
    runs = ROOT/'results/runs'
    paths = {p for pattern in PATTERNS for p in ROOT.glob(pattern)
             if p.is_file() and '__pycache__' not in p.parts}
    execution = read_json(runs/'execution.json')
    auxiliary = runs/'ancillary_execution.json'
    commands = [stage['command'] for stage in execution]
    if auxiliary.exists():
        execution.extend(stage for stage in read_json(auxiliary) if stage['command'] not in commands)
    meta = {
        'base_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'working_tree': 'Local corrections identified by individual SHA-256 hashes',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'environment': {
            'platform': platform.platform(), 'python':sys.version,
            'tectonic':subprocess.check_output([os.environ.get('TECTONIC','tectonic'),'--version'],text=True).strip(),
            'dependencies': {p:version(p) for p in PACKAGES},
            'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            'cuda': torch.version.cuda
        },
        'datasets':read_json(ROOT/'data/metadata/acquisition_manifest.json'),
        'settings': {'primary_window_seconds':60,'alpha':0.1,'budgets':[0,1,2,5,8,9,10,15],
                     'bootstrap_draws':2000,'bootstrap_seed':42,'mask_seed':42,'neural_seed':42},
        'execution':sorted(execution,key=lambda stage:stage['start_utc']),
        'tests':test_counts(runs/'final_tests.xml'),
        'ci':'Local corrections have no hosted run. Original commit passed run 43069521042.',
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)}
    }
    out = ROOT/'docs/REPRODUCIBILITY_MANIFEST.json'
    out.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
    pointer = {'manifest':'docs/REPRODUCIBILITY_MANIFEST.json','sha256':digest(out)}
    (runs/'experiment_manifest.json').write_text(json.dumps(pointer,indent=2)+'\n',encoding='utf8')
    if any(digest(ROOT/name)!=expected for name,expected in meta['sha256'].items()):
        raise ValueError('File changed during provenance verification')

if __name__=='__main__':
    main()

