"""Fixed exploratory information-clock and window sensitivity, preserving published results."""
import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.evaluation.marur import replay
from scripts.run_marur import aggregate
OUT=ROOT/'results/exploratory/marur_information'

def masks(stream,spec):
    times=np.sort(stream.issue.unique())
    yield 'Recorded',set()
    for kind in ['IID20','Burst20']:
        units=times if kind=='IID20' else np.unique(np.floor(times/(60*spec['burst_bin_minutes'])))
        for seed in spec['mask_seeds']:
            rng=np.random.default_rng(seed);hidden=set(units[rng.random(len(units))<spec['mask_probability']])
            value=stream.issue if kind=='IID20' else np.floor(stream.issue/(60*spec['burst_bin_minutes']))
            yield f'{kind}_seed{seed}',set(stream.loc[value.isin(hidden),'id'])

def variants(base,spec):
    for policy in ['Frozen','Periodic','Early','ACI','MARUR']:
        yield policy,policy,dict(base,log_information_clocks=True)
    for clock in spec['freshness_sources']:
        for window in spec['windows']:
            yield f'{clock}_W{window}','MARUR',dict(base,freshness_clock=clock,window=window,
                minimum_attempt_spacing_minutes=spec['minimum_attempt_spacing_minutes'],log_information_clocks=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True);start=datetime.now(timezone.utc).isoformat()
    spec=json.loads((ROOT/'configs/marur_information_experiment.json').read_text())
    base=json.loads((ROOT/'configs/marur.json').read_text())
    source_path=ROOT/'results/marur/opportunities.csv.gz';source=pd.read_csv(source_path,float_precision='round_trip')
    rows=[];actions=[];responses=[];dates=[];maskrows=[]
    for cohort,frame in source.groupby('cohort',sort=True):
        frame=frame.copy();frame['date']=frame.date.astype(str)
        conditions=list(masks(frame[frame.partition=='test'],spec))
        for scenario,hidden in conditions:
            for row in frame[frame.partition=='test'].itertuples():
                maskrows.append(dict(cohort=cohort,scenario=scenario,id=row.id,issue=row.issue,feedback_hidden=row.id in hidden))
        for model in spec['models']:
            column=('HistGBM' if cohort in ['E1','E3'] else 'Tree') if model=='HistGBM' else 'Persistence'
            data=frame.assign(point=frame[column]);initial=data[data.partition=='cal'];stream=data[data.partition=='test']
            for scenario,hidden in conditions:
                for cap in spec['new_query_caps']:
                    cache={}
                    for name,policy,config in variants(base,spec):
                        a,r=replay(initial,stream,policy,10+cap,config,'Recorded',feedback_unavailable_ids=hidden)
                        stats=aggregate(a,r);stats['supported_mbps_per_eligible']=stats['delivered_sum']/stats['eligible'] if stats['eligible'] else np.nan
                        meta=dict(cohort=cohort,model=model,scenario=scenario,new_query_cap=cap,variant=name)
                        rows.append(dict(**meta,**stats));actions.append(a.assign(**meta));responses.append(r.assign(**meta))
                        assert stats['new_query_attempts']<=cap and len(r)==stats['new_query_attempts']
                        if name.startswith(('completed_','observed_')):
                            queried=a.loc[a['query'],'issue'].to_numpy();assert np.all(np.diff(queried)>=300)
                            clock=name.split('_')[0]
                            if clock in cache:np.testing.assert_array_equal(cache[clock],a['query'].to_numpy())
                            else:cache[clock]=a['query'].to_numpy()
                        for date,day in a.groupby('date'):
                            dates.append(dict(**meta,date=date,**aggregate(day,r[r.id.isin(day.id)],initial=0)))
            print('Completed',cohort,model,flush=True)
    summary=pd.DataFrame(rows);summary.to_csv(OUT/'summary.csv',index=False)
    for name,parts in [('actions',actions),('responses',responses)]:
        pd.concat(parts,ignore_index=True).to_csv(OUT/(name+'.csv.gz'),index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame(dates).to_csv(OUT/'dates.csv',index=False)
    pd.DataFrame(maskrows).to_csv(OUT/'feedback_masks.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    fields=['u','supported_mbps_per_eligible','lo','hi','positive_low','positive_high','positive_rate','positive','abstained','positive_dates','successful_responses','unsuccessful_responses','effective_updates']
    contrasts=[('observed_W10','completed_W10'),('completed_W10','MARUR')]
    contrasts += [(f'{c}_W{w}',f'{c}_W10') for c in ['completed','observed'] for w in [20,40]]
    contrasts += [('observed_W10',b) for b in ['Periodic','Early','ACI','MARUR','Frozen']]
    paired=[]
    for keys,g in summary.groupby(['cohort','model','scenario','new_query_cap']):
        g=g.set_index('variant')
        for candidate,reference in contrasts:
            c,b=g.loc[candidate],g.loc[reference]
            paired.append(dict(zip(['cohort','model','scenario','new_query_cap'],keys),candidate=candidate,reference=reference,
                matched_cost=bool(c.new_query_attempts==b.new_query_attempts),candidate_queries=int(c.new_query_attempts),reference_queries=int(b.new_query_attempts),
                **{f+'_delta':c[f]-b[f] for f in fields}))
    pd.DataFrame(paired).to_csv(OUT/'contrasts.csv',index=False)
    receipt=dict(start_utc=start,end_utc=datetime.now(timezone.utc).isoformat(),configurations=len(rows),spec=spec,
        input_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),status='exploratory; no policy promotion',
        sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/evaluation/marur.py',ROOT/'configs/marur_information_experiment.json',Path(__file__),*OUT.glob('*.csv*')]})
    (OUT/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Saved',len(rows),'configurations',flush=True)
if __name__=='__main__':main()
