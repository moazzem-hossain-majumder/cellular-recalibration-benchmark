"""Independent event, mask, cost, and metric checks on exploratory artifacts."""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'results/exploratory/marur_information'
KEYS=['cohort','model','scenario','new_query_cap','variant']
def main():
    a=pd.read_csv(OUT/'actions.csv.gz',float_precision='round_trip')
    r=pd.read_csv(OUT/'responses.csv.gz',float_precision='round_trip')
    s=pd.read_csv(OUT/'summary.csv',float_precision='round_trip')
    masks=pd.read_csv(OUT/'feedback_masks.csv.gz')
    source=pd.read_csv(ROOT/'results/marur/opportunities.csv.gz',float_precision='round_trip')
    spec=json.loads((ROOT/'configs/marur_information_experiment.json').read_text())
    variants=['Frozen','Periodic','Early','ACI','MARUR']+[f'{c}_W{w}' for c in spec['freshness_sources'] for w in spec['windows']]
    scenarios=['Recorded']+[f'{c}_seed{seed}' for c in ['IID20','Burst20'] for seed in spec['mask_seeds']]
    expected={(c,m,z,n,v) for c in source.cohort.unique() for m in spec['models'] for z in scenarios for n in spec['new_query_caps'] for v in variants}
    assert len(s)==len(expected) and set(map(tuple,s[KEYS].to_numpy()))==expected
    assert not a.duplicated(KEYS+['id']).any() and not r.duplicated(KEYS+['id']).any()
    assert not masks.duplicated(['cohort','scenario','id']).any()
    # Independently reconstruct the fixed exogenous mask from timestamp bins.
    for (cohort,scenario),g in masks.groupby(['cohort','scenario']):
        ref=source[(source.cohort==cohort)&(source.partition=='test')].set_index('id')
        assert set(g.id)==set(ref.index)
        np.testing.assert_allclose(g.issue,ref.loc[g.id,'issue'],rtol=0,atol=0)
        if scenario=='Recorded':assert not g.feedback_hidden.any()
        else:
            kind,seed=scenario.split('_seed');times=np.sort(ref.issue.unique())
            units=times if kind=='IID20' else np.unique(np.floor(times/(60*spec['burst_bin_minutes'])))
            hidden=units[np.random.default_rng(int(seed)).random(len(units))<spec['mask_probability']]
            targets=g.issue if kind=='IID20' else np.floor(g.issue/(60*spec['burst_bin_minutes']))
            np.testing.assert_array_equal(g.feedback_hidden,np.isin(targets,hidden))
    rg={k:g for k,g in r.groupby(KEYS)};sg=s.set_index(KEYS)
    mg={k:g.set_index('id') for k,g in masks.groupby(['cohort','scenario'])}
    for key,g in a.groupby(KEYS,sort=False):
        cohort,model,scenario,cap,variant=key;summary=sg.loc[key];feedback=rg.get(key,r.iloc[:0])
        raw=source[source.cohort==cohort];test=raw[raw.partition=='test'].set_index('id');initial=raw[raw.partition=='cal'].sort_values(['issue','id']).head(10)
        assert set(g.id)==set(test.index)
        np.testing.assert_allclose(g.y,test.loc[g.id,'y'],equal_nan=True)
        field=('HistGBM' if cohort in ['E1','E3'] else 'Tree') if model=='HistGBM' else 'Persistence'
        np.testing.assert_allclose(g.point,test.loc[g.id,field],equal_nan=True)
        queries=g[g['query']];assert set(queries.id)==set(feedback.id)
        assert len(queries)<=cap and len(queries)==summary.new_query_attempts
        assert queries.eligible.all()
        np.testing.assert_allclose(g.last_query_attempt,g.issue.where(g['query']).ffill(),equal_nan=True)
        if len(queries)>1:assert np.all(queries.issue.to_numpy()[1:]>=queries.ready.to_numpy()[:-1])
        if variant=='Frozen':assert len(queries)==0
        if '_W' in variant:assert (queries.issue.diff().dropna()>=300).all()
        np.testing.assert_array_equal(g.attempts,10+g['query'].cumsum())
        mask=mg[cohort,scenario]
        if len(feedback):
            original=test.loc[feedback.id]
            observed=original.y.notna().to_numpy() & ~mask.loc[feedback.id,'feedback_hidden'].to_numpy()
            np.testing.assert_array_equal(feedback.observed,observed)
            np.testing.assert_array_equal(feedback.censored,mask.loc[feedback.id,'feedback_hidden'])
            np.testing.assert_allclose(feedback.ready,original.ready,rtol=0,atol=0)
            np.testing.assert_allclose(feedback.query_time,original.issue,rtol=0,atol=0)
            np.testing.assert_allclose(feedback.score,np.where(observed,original[field]-original.y,original[field]))
        for field,subset in [('last_completed_response',feedback),('last_observed_label',feedback[feedback.observed]),('last_admitted_score',feedback[feedback.admitted])]:
            times=np.sort(subset.ready.to_numpy())
            index=np.searchsorted(times,g.issue.to_numpy(),side='right')
            expected_clock=np.concatenate([[initial.ready.max()],times])[index]
            np.testing.assert_array_equal(g[field],expected_clock)
        admitted_times=np.sort(feedback.loc[feedback.admitted,'ready'].to_numpy())
        updates=np.searchsorted(admitted_times,g.issue.to_numpy(),side='right')
        np.testing.assert_array_equal(g.updates,updates)
        np.testing.assert_array_equal(g.window_size,np.minimum(int(variant.split('_W')[1]) if '_W' in variant else 10,10+updates))
        e=g[g.eligible];positive=e.lower>0;known=e.y.notna();fail=e.lower>e.y
        n=len(e);p=int(positive.sum());v=int(fail.sum());u=int((positive&~known).sum())
        delivered=float(np.nansum(np.minimum(e.lower,e.y)))
        measured=float(e.y.sum())
        checks={'positive':p,'violations':v,'unresolved':u,'lo':v/n,'hi':(v+u)/n,
            'positive_low':v/p if p else np.nan,'positive_high':(v+u)/p if p else np.nan,
            'u':delivered/measured if measured else np.nan,'supported_mbps_per_eligible':delivered/n,
            'positive_dates':g.loc[g.lower>0,'date'].nunique(),'abstained':int((g.lower==0).sum()),
            'successful_responses':int(feedback.observed.sum()),'unsuccessful_responses':int((~feedback.observed).sum()),
            'admitted_calibration_updates':int(feedback.admitted.sum()),'effective_updates':g.updates.max()}
        for field,value in checks.items():np.testing.assert_allclose(summary[field],value,rtol=1e-10,atol=1e-12,equal_nan=True,err_msg=str((key,field)))
    contrasts=pd.read_csv(OUT/'contrasts.csv')
    assert len(contrasts)==len(source.cohort.unique())*len(spec['models'])*len(scenarios)*len(spec['new_query_caps'])*11
    assert not contrasts.duplicated(['cohort','model','scenario','new_query_cap','candidate','reference']).any()
    for row in contrasts.itertuples():
        prefix=(row.cohort,row.model,row.scenario,row.new_query_cap)
        c,b=sg.loc[(*prefix,row.candidate)],sg.loc[(*prefix,row.reference)]
        assert row.matched_cost==bool(c.new_query_attempts==b.new_query_attempts)
        assert row.candidate_queries==c.new_query_attempts and row.reference_queries==b.new_query_attempts
        for col in contrasts.columns:
            if col.endswith('_delta'):np.testing.assert_allclose(getattr(row,col),c[col[:-6]]-b[col[:-6]],atol=1e-12,equal_nan=True)
    result={'configurations':len(s),'actions':len(a),'responses':len(r),'contrasts':len(contrasts),'status':'passed'}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
