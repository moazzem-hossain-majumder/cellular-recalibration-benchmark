import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_marur import aggregate
from scripts.run_marur_information_experiment import masks
from src.evaluation.marur import replay
OUT=ROOT/'results/exploratory/reviewer_baselines'

def random_schedule(stream,cap,seed):
    eligible=stream[stream.point.notna()].sort_values(['issue','id'])
    priority=np.random.default_rng(seed).random(len(eligible))
    return eligible.iloc[np.argsort(priority)[:cap]].id.tolist()

def main():
    OUT.mkdir(parents=True,exist_ok=True);start=datetime.now(timezone.utc).isoformat()
    spec=json.loads((ROOT/'configs/marur_reviewer_baselines.json').read_text())
    base=json.loads((ROOT/'configs/marur.json').read_text());base.update(log_information_clocks=True,log_score_diagnostics=True)
    maskcfg=json.loads((ROOT/'configs/marur_information_experiment.json').read_text())
    sourcepath=ROOT/'results/marur/opportunities.csv.gz';source=pd.read_csv(sourcepath,float_precision='round_trip')
    rows=[];actions=[];feedback=[];days=[];plans=[]
    for cohort,frame in source.groupby('cohort',sort=True):
        conditions=[(name,ids) for name,ids in masks(frame[frame.partition=='test'],maskcfg) if name in spec['feedback_conditions']]
        for model in spec['models']:
            col=('HistGBM' if cohort in ['E1','E3'] else 'Tree') if model=='HistGBM' else 'Persistence'
            data=frame.assign(point=frame[col],date=frame.date.astype(str));initial=data[data.partition=='cal'];stream=data[data.partition=='test']
            for scenario,hidden in conditions:
                for cap in spec['new_query_caps']:
                    variants=[(p,p,dict(base)) for p in ['Frozen','Periodic','Early','ACI','MARUR','DecayingOGD']]
                    variants += [('MARUR_Pooled','MARUR',dict(base,calibration_scope='pooled')),('MARUR_PooledNoGate','MARUR',dict(base,calibration_scope='pooled',pattern_gate=False))]
                    for seed in spec['random_schedule_seeds']:
                        ids=random_schedule(stream,cap,seed)
                        variants.append((f'Random{seed}','Random',dict(base,query_schedule_ids=ids)))
                        plans.extend(dict(cohort=cohort,model=model,scenario=scenario,new_query_cap=cap,variant=f'Random{seed}',id=x) for x in ids)
                    query_ids={}
                    for name,policy,cfg in variants:
                        a,r=replay(initial,stream,policy,10+cap,cfg,feedback_unavailable_ids=hidden)
                        meta=dict(cohort=cohort,model=model,scenario=scenario,new_query_cap=cap,variant=name)
                        rows.append(dict(**meta,**aggregate(a,r)));actions.append(a.assign(**meta));feedback.append(r.assign(**meta))
                        query_ids[name]=a.loc[a['query'],'id'].tolist()
                        for date,day in a.groupby('date'):days.append(dict(**meta,date=date,**aggregate(day,r[r.id.isin(day.id)],initial=0)))
                    assert query_ids['MARUR']==query_ids['MARUR_Pooled']==query_ids['MARUR_PooledNoGate']
                    assert query_ids['Periodic']==query_ids['ACI']==query_ids['DecayingOGD']
            print('Completed',cohort,model,flush=True)
    pd.DataFrame(rows).to_csv(OUT/'summary.csv',index=False)
    pd.DataFrame(days).to_csv(OUT/'dates.csv',index=False);pd.DataFrame(plans).to_csv(OUT/'random_schedules.csv',index=False)
    for name,parts in [('actions',actions),('responses',feedback)]:pd.concat(parts).to_csv(OUT/(name+'.csv.gz'),index=False,compression={'method':'gzip','mtime':0})
    receipt={'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'configurations':len(rows),'spec':spec,'status':'exploratory',
        'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [sourcepath,Path(__file__),ROOT/'src/evaluation/marur.py',ROOT/'configs/marur_reviewer_baselines.json',ROOT/'docs/archive/REVIEWER_BASELINE_PROTOCOL.md',*OUT.glob('*.csv*')]}}
    (OUT/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Saved',len(rows),'configurations')
if __name__=='__main__':main()
