"""Validate targeted baselines and reconstruct descriptive failure mechanisms."""
import json,sys,hashlib
from pathlib import Path
from collections import deque
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_reviewer_baselines import random_schedule
from scripts.run_marur_information_experiment import masks
from src.evaluation.conformal import compute_conformal_quantile
OUT=ROOT/'results/exploratory/reviewer_baselines';KEYS=['cohort','model','scenario','new_query_cap','variant']

def decomposition(candidate,reference):
    a=candidate.set_index('id');b=reference.set_index('id').loc[a.index]
    np.testing.assert_allclose(a.y,b.y,equal_nan=True)
    ap=a.lower>0;bp=b.lower>0;af=a.lower>a.y;bf=b.lower>b.y
    au=np.minimum(a.lower,a.y).fillna(0);bu=np.minimum(b.lower,b.y).fillna(0)
    parts={'shared_service_delta_mbps':float((au-bu)[ap&bp].sum()),'added_offer_service_mbps':float(au[ap&~bp].sum()),'removed_offer_service_mbps':float(-bu[bp&~ap].sum())}
    np.testing.assert_allclose(sum(parts.values()),float((au-bu).sum()),atol=1e-8)
    return dict(**parts,shared_offers=int((ap&bp).sum()),removed_offers=int((bp&~ap).sum()),added_offers=int((ap&~bp).sum()),
        failures_removed=int((bf&~ap).sum()),failures_added=int((af&~bp).sum()),shared_failure_delta=int((af&bp).sum()-(bf&ap).sum()),
        shared_size_increases=int(((a.lower>b.lower)&ap&bp).sum()),shared_size_decreases=int(((a.lower<b.lower)&ap&bp).sum()))

def check_metrics(a,r,s):
    e=a[a.eligible];p=e.lower>0;v=(e.lower>e.y).sum();unknown=(p&e.y.isna()).sum();n=len(e);m=p.sum()
    d=np.nansum(np.minimum(e.lower,e.y));total=e.y.sum()
    values={'u':d/total if total else np.nan,'lo':v/n,'hi':(v+unknown)/n,'positive_low':v/m if m else np.nan,'positive_high':(v+unknown)/m if m else np.nan,
        'positive':m,'abstained':(a.lower==0).sum(),'positive_dates':a.loc[a.lower>0,'date'].nunique(),'new_query_attempts':a['query'].sum(),
        'successful_responses':r.observed.sum(),'unsuccessful_responses':(~r.observed).sum(),'admitted_calibration_updates':r.admitted.sum(),'effective_updates':a.updates.max()}
    for k,x in values.items():np.testing.assert_allclose(s[k],x,rtol=1e-11,atol=1e-12,equal_nan=True,err_msg=k)

def main():
    s=pd.read_csv(OUT/'summary.csv',float_precision='round_trip');a=pd.read_csv(OUT/'actions.csv.gz',float_precision='round_trip');r=pd.read_csv(OUT/'responses.csv.gz',float_precision='round_trip')
    source=pd.read_csv(ROOT/'results/marur/opportunities.csv.gz',float_precision='round_trip');spec=json.loads((ROOT/'configs/marur_reviewer_baselines.json').read_text())
    variants=['Frozen','Periodic','Early','ACI','MARUR','DecayingOGD','MARUR_Pooled','MARUR_PooledNoGate']+[f'Random{x}' for x in spec['random_schedule_seeds']]
    expected={(c,m,z,n,v) for c in source.cohort.unique() for m in spec['models'] for z in spec['feedback_conditions'] for n in spec['new_query_caps'] for v in variants}
    assert len(s)==len(expected)==792 and set(map(tuple,s[KEYS].to_numpy()))==expected
    assert not a.duplicated(KEYS+['id']).any() and not r.duplicated(KEYS+['id']).any()
    sg=s.set_index(KEYS);ag={k:g for k,g in a.groupby(KEYS,sort=False)};rg={k:g for k,g in r.groupby(KEYS,sort=False)}
    maskcfg=json.loads((ROOT/'configs/marur_information_experiment.json').read_text());masksets={}
    for cohort,f in source.groupby('cohort'):
        for scenario,hidden in masks(f[f.partition=='test'],maskcfg):masksets[cohort,scenario]=hidden
    for key,g in ag.items():
        cohort,model,scenario,cap,variant=key;rr=rg.get(key,r.iloc[:0]);f=source[source.cohort==cohort]
        col=('HistGBM' if cohort in ['E1','E3'] else 'Tree') if model=='HistGBM' else 'Persistence'
        f=f.assign(point=f[col]);test=f[f.partition=='test'].set_index('id');initial=f[f.partition=='cal'].sort_values(['issue','id']).head(10)
        assert set(g.id)==set(test.index);np.testing.assert_allclose(g.y,test.loc[g.id,'y'],equal_nan=True);np.testing.assert_allclose(g.point,test.loc[g.id,col],equal_nan=True)
        qrows=g[g['query']];assert len(qrows)<=cap and set(qrows.id)==set(rr.id)
        np.testing.assert_array_equal(g.attempts,10+g['query'].cumsum());assert qrows.eligible.all()
        if len(qrows)>1:assert np.all(qrows.issue.to_numpy()[1:]>=qrows.ready.to_numpy()[:-1])
        if variant.startswith('Random'):
            planned=set(random_schedule(test.reset_index(),cap,int(variant[6:])));assert set(qrows.id)<=planned
        for row in rr.itertuples():
            raw=test.loc[row.id];observed=pd.notna(raw.y) and row.id not in masksets[cohort,scenario]
            assert row.observed==observed and row.censored==(row.id in masksets[cohort,scenario])
            assert row.query_time==raw.issue and row.ready==raw.ready
            np.testing.assert_allclose(row.score,raw.point-raw.y if observed else raw.point)
        check_metrics(g,rr,sg.loc[key])
        if variant=='DecayingOGD':
            q=compute_conformal_quantile((initial.point-initial.y).to_numpy(),.1);scale=max(1.,float(abs(initial.point-initial.y).max()));j=0
            pending=list(rr.sort_values('ready').itertuples());pos=0
            for row in g.itertuples():
                while pos<len(pending) and pending[pos].ready<=row.issue:
                    j+=1;q+=scale/(j**.6)*(float(pending[pos].score>q)-.1);pos+=1
                np.testing.assert_allclose(row.offset,q,atol=1e-12)
                np.testing.assert_allclose(row.lower,max(0.,row.point-q) if row.eligible else 0.,atol=1e-12)
    pairs=[]
    comparisons=[('MARUR','Periodic'),('MARUR','Early'),('MARUR','ACI'),('DecayingOGD','Periodic'),('DecayingOGD','ACI'),('MARUR_Pooled','MARUR'),('MARUR_PooledNoGate','MARUR_Pooled')]+[('MARUR',f'Random{x}') for x in spec['random_schedule_seeds']]
    for key,group in s.groupby(KEYS[:-1]):
        x=group.set_index('variant')
        for candidate,reference in comparisons:
            c,b=x.loc[candidate],x.loc[reference];ca,ba=ag[(*key,candidate)],ag[(*key,reference)]
            if candidate.startswith('MARUR_Pooled') or candidate=='DecayingOGD':np.testing.assert_array_equal(ca['query'],ba['query'])
            pairs.append(dict(zip(KEYS[:-1],key),candidate=candidate,reference=reference,matched_cost=c.new_query_attempts==b.new_query_attempts,
                candidate_queries=c.new_query_attempts,reference_queries=b.new_query_attempts,**{k+'_delta':c[k]-b[k] for k in ['u','hi','positive_high','positive_rate','positive','abstained','positive_dates']},**decomposition(ca,ba)))
    pairs=pd.DataFrame(pairs);pairs.to_csv(OUT/'contrasts_and_mechanisms.csv',index=False)
    # Reconstruct retained scores in prior window experiment, without re-running/tuning policies.
    folder=ROOT/'results/exploratory/marur_information';old_a=pd.read_csv(folder/'actions.csv.gz',float_precision='round_trip');old_r=pd.read_csv(folder/'responses.csv.gz',float_precision='round_trip')
    old_s=pd.read_csv(folder/'summary.csv');old_rg={k:g for k,g in old_r.groupby(KEYS)};diagnostics=[]
    for key,g in old_a.groupby(KEYS,sort=False):
        cohort,model,scenario,cap,variant=key
        if '_W' not in variant:continue
        f=source[source.cohort==cohort];col=('HistGBM' if cohort in ['E1','E3'] else 'Tree') if model=='HistGBM' else 'Persistence'
        initial=f[f.partition=='cal'].sort_values(['issue','id']).head(10);window=deque([(x[col]-x.y,x.pattern,x.ready,True) for _,x in initial.iterrows()],maxlen=int(variant.split('_W')[1]))
        rr=old_rg.get(key,old_r.iloc[:0]).sort_values('ready');pending=list(rr.itertuples());pos=0;lookup=f.set_index('id');count=dict(binding_missing=0,bound_zero_with_binding_missing=0,gate_vetoes=0,threshold_age_over_60m=0,eligible=0)
        for row in g.itertuples():
            while pos<len(pending) and pending[pos].ready<=row.issue:
                v=pending[pos];window.append((v.score,lookup.loc[v.id,'pattern'],v.ready,bool(v.observed)));pos+=1
            pattern=[v for v in window if v[1]==row.pattern];use=pattern if len(pattern)>=9 else list(window)
            q=compute_conformal_quantile(np.array([v[0] for v in use]),.1);raw=max(0.,row.point-q) if row.eligible else 0.
            expected=0. if len(pattern)<3 else raw;np.testing.assert_allclose(row.lower,expected,atol=1e-10)
            if not row.eligible:continue
            bind=[v for v in use if v[0]==q];missing=any(not v[3] for v in bind)
            count['eligible']+=1;count['binding_missing']+=int(missing);count['bound_zero_with_binding_missing']+=int(missing and raw==0)
            count['gate_vetoes']+=int(raw>0 and len(pattern)<3);count['threshold_age_over_60m']+=int(any(row.issue-v[2]>3600 for v in bind))
        diagnostics.append(dict(zip(KEYS,key),**count))
    pd.DataFrame(diagnostics).to_csv(OUT/'window_score_diagnostics.csv',index=False)
    # Preserve all previous paired-offer decompositions, not only favorable examples.
    old_ag={k:g for k,g in old_a.groupby(KEYS,sort=False)};decomp=[]
    for row in pd.read_csv(folder/'contrasts.csv').itertuples():
        prefix=(row.cohort,row.model,row.scenario,row.new_query_cap)
        decomp.append(dict(cohort=row.cohort,model=row.model,scenario=row.scenario,new_query_cap=row.new_query_cap,candidate=row.candidate,reference=row.reference,matched_cost=row.matched_cost,
            **decomposition(old_ag[(*prefix,row.candidate)],old_ag[(*prefix,row.reference)])))
    pd.DataFrame(decomp).to_csv(OUT/'window_offer_decomposition.csv',index=False)
    result={'baseline_configurations':len(s),'baseline_actions':len(a),'baseline_responses':len(r),'baseline_contrasts':len(pairs),'reconstructed_window_configurations':len(diagnostics),'old_offer_decompositions':len(decomp),'status':'passed'}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
