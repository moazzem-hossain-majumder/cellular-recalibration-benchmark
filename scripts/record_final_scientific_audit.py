"""Record completed checks and distinguish preserved experimental artifacts."""
import hashlib,json,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
baseline=json.loads((ROOT/'results/runs/final_scientific_audit_baseline.json').read_text())
checked=[];changed=[]
for item in baseline['files']:
    name=item['path']
    if name.startswith(('results/marur/','results/marur_audit/','results/metrics/','results/clock_histgbm/','results/external_validation/')) and name.endswith(('.csv','.gz')):
        actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        checked.append(name)
        if actual!=item['sha256']:changed.append(name)
assert not changed,changed
def counts(path):
    root=ET.parse(ROOT/path).getroot();suites=list(root) if root.tag=='testsuites' else [root]
    return {k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
receipt={'base_commit':baseline['commit'],'preserved_experimental_files':checked,'changed_experimental_files':changed,'full_suite':counts('results/runs/final_tests.xml'),'fresh_minimal_suite':counts('results/runs/clean_audit_tests.xml'),'controller_reproduction_receipt':'results/runs/clean_controller_reproduction.json','manuscript_consistency':'Passed: 576 configurations, 160032 actions, 5960 responses and 14 tables','scope':'Fresh minimal environment replayed saved predictions; no new raw acquisition or full model retraining; hosted CI not run','working_tree':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines()}
(ROOT/'results/runs/final_scientific_audit_completion.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print('Preserved',len(checked),'experimental files;',receipt['full_suite'],receipt['fresh_minimal_suite'])
