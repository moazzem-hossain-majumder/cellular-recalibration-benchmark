"""Fresh-environment controller reproduction from frozen authoritative opportunities.

Requires only numpy and pandas. Does not retrain predictors or reacquire raw data.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation.marur import replay
from scripts.validate_marur_audit import validate


def main():
    start=datetime.now(timezone.utc).isoformat()
    config=json.loads((ROOT/'configs/marur.json').read_text())
    source=pd.read_csv(ROOT/'results/marur/opportunities.csv.gz',float_precision='round_trip')
    count=0
    for folder,cap_field in [('marur','budget'),('marur_audit','new_query_cap')]:
        prefix='matched_cost_' if folder=='marur_audit' else ''
        actions=pd.read_csv(ROOT/f'results/{folder}/{prefix}actions.csv.gz',float_precision='round_trip')
        responses=pd.read_csv(ROOT/f'results/{folder}/{prefix}responses.csv.gz',float_precision='round_trip')
        keys=['cohort','model','scenario',cap_field,'policy']
        groups={k:g for k,g in responses.groupby(keys,sort=False)}
        for key,expected in actions.groupby(keys,sort=False):
            cohort,model,scenario,cap,policy=key
            frame=source[source.cohort==cohort].copy()
            column=('HistGBM' if cohort in ['E1','E3'] else 'Tree') if model=='HistGBM' else 'Persistence'
            frame['point']=frame[column]
            a,r=replay(frame[frame.partition=='cal'],frame[frame.partition=='test'],policy,
                       cap+10 if cap_field=='new_query_cap' else cap,config,scenario)
            ref=expected[a.columns].reset_index(drop=True)
            pd.testing.assert_frame_equal(a,ref,check_dtype=False,check_exact=False,rtol=1e-12,atol=1e-12)
            ref=groups.get(key,responses.iloc[:0])[r.columns].reset_index(drop=True)
            pd.testing.assert_frame_equal(r,ref,check_dtype=False,check_exact=False,rtol=1e-12,atol=1e-12)
            count+=1
    validate(ROOT)
    pinned=['src/evaluation/marur.py','src/evaluation/conformal.py','configs/marur.json',
            'results/marur/opportunities.csv.gz','scripts/reproduce_saved_marur.py',
            'scripts/validate_marur_audit.py']
    receipt=dict(start_utc=start,end_utc=datetime.now(timezone.utc).isoformat(),
        command=[sys.executable,'scripts/reproduce_saved_marur.py'],configurations=count,
        prefix=sys.prefix,base_prefix=sys.base_prefix,
        installed=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True).splitlines(),
        scope='All 576 original and 720 audit controllers replayed from saved frozen forecasts; no raw-data reacquisition, model fitting, PDF rebuild or full dependency-stack verification',
        status='passed',sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in pinned})
    (ROOT/'results/runs/clean_controller_reproduction.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(f'Reproduced all {count} controller action/response ledgers from frozen opportunities.')

if __name__=='__main__':
    main()
