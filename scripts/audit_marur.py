"""Exploratory exact-cost replay; no policy selection, interpolation or refitting."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.stats import t

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_marur import aggregate
from src.evaluation.marur import replay

OUT=ROOT/'results/marur_audit'
POLICIES=['Frozen','Periodic','Early','ACI','MARUR']
CAPS=[0,1,5,10,20,40]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    start=datetime.now(timezone.utc).isoformat()
    config=json.loads((ROOT/'configs/marur.json').read_text())
    source=pd.read_csv(ROOT/'results/marur/opportunities.csv.gz',float_precision='round_trip')
    rows=[]; actions=[]; responses=[]; dates=[]; pairs=[]; mechanisms=[]
    for cohort,frame in source.groupby('cohort',sort=True):
        for model in ['HistGBM','Persistence']:
            column=('HistGBM' if cohort in ['E1','E3'] else 'Tree') if model=='HistGBM' else 'Persistence'
            data=frame.assign(point=frame[column])
            initial=data[data.partition=='cal']; stream=data[data.partition=='test']
            for scenario in config['scenarios']:
                for cap in CAPS:
                    group={}
                    for policy in POLICIES:
                        a,r=replay(initial,stream,policy,10+cap,config,scenario)
                        meta=dict(cohort=cohort,model=model,scenario=scenario,new_query_cap=cap,policy=policy)
                        stats=aggregate(a,r)
                        rows.append(dict(**meta,**stats,exact_cost=stats['new_query_attempts']==cap))
                        actions.append(a.assign(**meta)); responses.append(r.assign(**meta))
                        group[policy]=(a,r,stats)
                        for date,day in a.groupby('date'):
                            dr=r[r.id.isin(day.id)]
                            row=aggregate(day,dr,initial=0)
                            # Effective updates are cumulative admissions available by this
                            # day's last forecast, matching the original ledger definition.
                            dates.append(dict(**meta,date=date,**row))
                    ma,_,ms=group['MARUR']
                    for baseline in POLICIES[:-1]:
                        ba,_,bs=group[baseline]
                        equal=ms['new_query_attempts']==bs['new_query_attempts']==cap
                        pairs.append(dict(cohort=cohort,model=model,scenario=scenario,new_query_cap=cap,
                            baseline=baseline,matched=equal,marur_queries=ms['new_query_attempts'],
                            baseline_queries=bs['new_query_attempts'],
                            **{c+'_delta':ms[c]-bs[c] for c in ['u','lo','hi','positive_low',
                                'positive_high','commitment_coverage','abstained','positive_dates']}))
                        if equal:
                            # Exact ledger decomposition: lower risk can arise by removing offers
                            # or changing bounds on shared offers, not necessarily better calibration.
                            assert ma.id.equals(ba.id)
                            mp=ma.lower>0; bp=ba.lower>0
                            mf=ma.lower>ma.y; bf=ba.lower>ba.y
                            mechanisms.append(dict(cohort=cohort,model=model,scenario=scenario,
                                new_query_cap=cap,baseline=baseline,
                                shared_offers=int((mp&bp).sum()),removed_offers=int((bp&~mp).sum()),
                                added_offers=int((mp&~bp).sum()),
                                failures_removed_with_offers=int((bf&~mp).sum()),
                                failures_added_with_offers=int((mf&~bp).sum()),
                                shared_failure_delta=int((mf&bp).sum()-(bf&mp).sum()),
                                failure_delta=int(mf.sum()-bf.sum()),
                                lower_sum_delta=float(ma.lower.sum()-ba.lower.sum())))
    summary=pd.DataFrame(rows)
    summary.to_csv(OUT/'matched_cost_summary.csv',index=False)
    pd.DataFrame(pairs).to_csv(OUT/'matched_cost_pairs.csv',index=False)
    pd.DataFrame(mechanisms).to_csv(OUT/'offer_decomposition.csv',index=False)
    pd.DataFrame(dates).to_csv(OUT/'matched_cost_dates.csv',index=False)
    for name,frames in [('actions',actions),('responses',responses)]:
        pd.concat(frames).to_csv(OUT/f'matched_cost_{name}.csv.gz',index=False,
                                compression={'method':'gzip','mtime':0})
    # Assumed SD of paired trip-level differences; no tick-independence assumption.
    precision=[]
    for sd in [.05,.10,.15,.20]:
        for halfwidth in [.025,.05]:
            n=next(n for n in range(3,10000) if t.ppf(.975,n-1)*sd/np.sqrt(n)<=halfwidth)
            precision.append(dict(assumed_trip_difference_sd=sd,target_halfwidth=halfwidth,
                                  complete_independent_trips=n,scheduled_with_15pct_attrition=int(np.ceil(n/.85))))
    pd.DataFrame(precision).to_csv(OUT/'prospective_precision.csv',index=False)
    receipt=dict(start_utc=start,end_utc=datetime.now(timezone.utc).isoformat(),
        command=['python','scripts/audit_marur.py'],new_query_caps=CAPS,policies=POLICIES,
        scope='Exploratory full-suffix replay; exact achieved-cost matches only; Frozen zero-query reference',
        sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [ROOT/'src/evaluation/marur.py',ROOT/'configs/marur.json',
                          ROOT/'results/marur/opportunities.csv.gz',Path(__file__)]})
    (OUT/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(f'Completed {len(summary)} full-suffix replays; {sum(p["matched"] for p in pairs)} exact-cost pairs.')

if __name__=='__main__':
    main()
