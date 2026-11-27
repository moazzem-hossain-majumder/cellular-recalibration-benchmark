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


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ['torch','pandas','numpy','scipy','scikit-learn','matplotlib','seaborn',
            'pypdf','pymupdf','pytest','pypandoc_binary','beautifulsoup4','pyarrow']
PATTERNS = [
    'results/runs/reviewer_revision_completion.json',
    'results/exploratory/reviewer_baselines/*','results/exploratory/sensitivity/*',
    'results/exploratory/predictor_robustness/*',
    'results/exploratory/predictor_robustness/*',
    'results/exploratory/marur_information/*','docs/MARUR_INFORMATION_EXPERIMENT*.md',
    'literature_review/*.tex','literature_review/*.bib','literature_review/*.csv','literature_review/*.md','literature_review/*.pdf',
    'literature_review/_support/verification_sources.json','literature_review/_support/validation.json',
    "docs/*.md","docs/archive/*.md","results/runs/final_scientific_audit*.json",
    "results/runs/clean_controller_reproduction.json","results/runs/clean_audit_tests.xml","results/runs/dependency_licenses.json",
    'results/marur_audit/*','results/marur/*','configs/*.json',
    'results/runs/isolated_baseline_reproduction.json','results/runs/isolated_marur_reproduction.json',
    'src/**/*.py','scripts/*.py','scripts/archive/*','tests/**/*.py','examples/*','results/diagnostics/*',
    'results/metrics/*','results/tables/*','results/figures/*','results/pacer/*','paper/**/*','app/*',
    'data/metadata/*.json','README.md','LICENSE','requirements.txt','pyproject.toml',
    '.github/workflows/*','results/runs/final_tests.xml','results/runs/execution.json',
    'results/runs/ancillary_execution.json','results/exploratory/sirhan_external/*',
    'results/exploratory/published_global_comparison.csv',
    'results/runs/external_validation.json','results/external_validation/*',
    'results/clock_histgbm/*','constraints-research.txt'
]
TEXT_FORMATS = {'.py','.md','.json','.csv','.tex','.bib','.yaml','.yml','.toml','.txt','.html','.xml'}

def digest(path):
    payload = path.read_bytes()
    if path.suffix.lower() in TEXT_FORMATS or path.name == 'LICENSE':
        payload = payload.replace(b'\r\n',b'\n')
    return hashlib.sha256(payload).hexdigest()

def verify(root=ROOT):
    pointer = read_json(root/'results/runs/experiment_manifest.json')
    manifest = root/pointer['manifest']
    if digest(manifest)!=pointer['sha256']:
        raise ValueError('Manifest pointer digest mismatch')
    hashes = read_json(manifest)['sha256']
    for name,expected in hashes.items():
        if digest(root/name)!=expected:
            raise ValueError(f'File digest mismatch: {name}')
    print(f'Verified {len(hashes)} manifest entries.')

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
    import torch
    from pypdf import PdfReader
    runs = ROOT/'results/runs'
    receipt = read_json(runs/'external_validation.json')
    counts = test_counts(runs/'final_tests.xml')
    receipt.update(scope='Rome reset and clock protocols, Irish published and chronological evaluations, Norwegian external evaluation, and six-cohort MARUR feedback replay',
                   validated_manuscript_tables=len(list((ROOT/'paper/tables').glob('*.tex'))),
                   manuscript_pages=len(PdfReader(ROOT/'paper/manuscript.pdf').pages),
                   package_pages=len(PdfReader(ROOT/'paper/submission_package.pdf').pages),
                   tests={'outcomes_by_suite':counts,'report':'results/runs/final_tests.xml'})
    (runs/'external_validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
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
        'digest_scheme': {'algorithm':'SHA-256','normalize_crlf_to_lf':sorted(TEXT_FORMATS),
                          'other_files':'exact bytes; raw dataset pins in acquisition manifests use exact bytes'},
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'environment': {
            'platform': platform.platform(), 'python':sys.version,
            'tectonic':subprocess.check_output([os.environ.get('TECTONIC','tectonic'),'--version'],text=True).strip(),
            'dependencies': {p:version(p) for p in PACKAGES},
            'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            'cuda': torch.version.cuda
        },
        'datasets':read_json(ROOT/'data/metadata/acquisition_manifest.json'),
        'settings': {'clock_prefix_max':{'E1':178,'E3':254},'primary_window_seconds':60,'alpha':0.1,'budgets':[0,1,2,5,8,9,10,15],
                     'bootstrap_draws':2000,'bootstrap_seed':42,'mask_seed':42,'neural_seed':42},
        'marur': {'settings':read_json(ROOT/'configs/marur.json'),
                  'execution':read_json(ROOT/'results/marur/execution.json'),
                  'isolated_reproduction':read_json(runs/'isolated_marur_reproduction.json')},
        'execution':sorted(execution,key=lambda stage:stage['start_utc']),
        'tests':test_counts(runs/'final_tests.xml'),
        'ci':'Local working tree validated separately from hosted CI; no hosted result for these edits.',
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)}
    }
    out = ROOT/'docs/REPRODUCIBILITY_MANIFEST.json'
    out.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
    pointer = {'manifest':'docs/REPRODUCIBILITY_MANIFEST.json','sha256':digest(out)}
    (runs/'experiment_manifest.json').write_text(json.dumps(pointer,indent=2)+'\n',encoding='utf8')
    if any(digest(ROOT/name)!=expected for name,expected in meta['sha256'].items()):
        raise ValueError('File changed during provenance verification')

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true',help='Verify the existing manifest without updating any files')
    if parser.parse_args().verify:
        verify()
    else:
        main()

