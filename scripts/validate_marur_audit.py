"""Independently validate every MARUR audit pair against authoritative ledgers."""
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
KEYS=['cohort','model','scenario','new_query_cap','policy']
PAIR_KEYS=KEYS[:-1]+['baseline']
POLICIES=['Frozen','Periodic','Early','ACI','MARUR']
CAPS=[0,1,5,10,20,40]
DELTAS=['u','lo','hi','positive_low','positive_high','commitment_coverage','abstained','positive_dates']


def require(condition,where,message):
    if not condition:
        raise ValueError(f'{where}: {message}')


def same(actual,expected,where,field):
    try:
        np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-12,equal_nan=True)
    except (AssertionError,TypeError,ValueError) as error:
        raise ValueError(f'{where}: invalid {field}; expected {expected}, found {actual}') from error


def index_table(frame,keys,label,expected=None):
    require(not frame[keys].isna().any().any(),label,'missing configuration identity')
    duplicate=frame.duplicated(keys,keep=False)
    require(not duplicate.any(),label,f'duplicate identity {frame.loc[duplicate,keys].head(1).to_dict("records")}')
    result=frame.set_index(keys)
    if expected is not None:
        actual=set(result.index)
        missing=expected-actual; extra=actual-expected
        require(not missing and not extra,label,f'missing={sorted(missing)[:2]}, unexpected={sorted(extra)[:2]}')
    return result


def validate_frames(summary,actions,responses,pairs,decomposition,source,expected_keys):
    """Expected keys are an independently declared experimental design, not CSV flags."""
    lookup=index_table(summary,KEYS,'summary',expected_keys)
    index_table(actions,KEYS+['id'],'actions')
    index_table(responses,KEYS+['id'],'responses')
    ag={k:g.sort_values(['issue','id']) for k,g in actions.groupby(KEYS,sort=False)}
    rg={k:g for k,g in responses.groupby(KEYS,sort=False)}
    require(set(ag)==expected_keys,'actions','missing or unexpected configuration')
    require(set(rg)<=expected_keys,'responses','unexpected configuration')
    truth={}; aligned={}
    for key,a in ag.items():
        where=f'configuration {key}'
        s=lookup.loc[key]; r=rg.get(key,responses.iloc[:0])
        cohort,model,scenario,cap,policy=key
        ref=source[(source.cohort==cohort)&(source.partition=='test')].set_index('id')
        require(ref.index.is_unique,where,'duplicate authoritative opportunity')
        require(set(a.id)==set(ref.index),where,'missing or extra opportunity IDs')
        ref=ref.loc[a.id]
        column=('HistGBM' if cohort in ['E1','E3'] else 'Tree') if model=='HistGBM' else 'Persistence'
        for field in ['issue','ready','y','pattern']:
            same(a[field].to_numpy(),ref[field].to_numpy(),where,field)
        require(a.date.astype(str).tolist()==ref.date.astype(str).tolist(),where,'date identity mismatch')
        same(a.point.to_numpy(),ref[column].to_numpy(),where,'point predictor identity')
        require(a.eligible.equals(a.point.notna()),where,'invalid eligibility')
        require((np.isfinite(a.lower)&(a.lower>=0)).all(),where,'nonfinite or negative commitment')
        require((a.loc[~a.eligible,'lower']==0).all(),where,'ineligible positive commitment')
        require((a.last_feedback<=a.issue).all(),where,'future feedback used')
        q=int(a['query'].sum()); queried=a[a['query']].set_index('id')
        require(q<=cap,where,'query cap exceeded')
        require(q==len(r) and set(queried.index)==set(r.id),where,'query/response identity mismatch')
        same(a.attempts,10+a['query'].cumsum(),where,'cumulative hybrid count')
        if len(r):
            requests=queried.loc[r.id]
            same(r.query_time.to_numpy(),requests.issue.to_numpy(),where,'query_time')
            same(r.ready.to_numpy(),requests.ready.to_numpy(),where,'response ready')
            require((r.ready>r.query_time).all(),where,'response precedes completed horizon')
            ordinal=pd.Series(a.eligible.cumsum().to_numpy(),index=a.id).loc[r.id].to_numpy()
            censored=(ordinal%5==0) if scenario=='QueryCensor20' else np.zeros(len(r),dtype=bool)
            same(r.censored.to_numpy(),censored,where,'censoring identity')
            y=ref.loc[r.id,'y'].to_numpy()
            observed=np.isfinite(y)&~censored
            same(r.observed.to_numpy(),observed,where,'successful/unsuccessful feedback')
            same(r.score.to_numpy(),np.where(observed,requests.point.to_numpy()-y,requests.point.to_numpy()),where,'feedback score')
            # All five audit policies admit missing upper-bound scores; DropMissing is
            # only in the original ablation family, not the exact-cost audit grid.
            require(r.admitted.all(),where,'admitted update lost')
        admitted=r[r.admitted]
        counts=np.searchsorted(np.sort(admitted.ready.to_numpy()),a.issue.to_numpy(),side='right')
        same(a.updates.to_numpy(),counts,where,'effective update timing')
        eligible=a[a.eligible]; measured=eligible.y.notna(); positive=eligible.lower>0
        n=len(eligible); p=int(positive.sum()); e=int((eligible.lower>eligible.y).sum())
        missing=int((positive&~measured).sum()); scored=int(measured.sum())
        observed_sum=float(eligible.loc[measured,'y'].sum())
        delivered=float(np.minimum(eligible.loc[measured,'lower'],eligible.loc[measured,'y']).sum())
        error=(eligible.point-eligible.y).dropna()
        ratio=lambda x,y: x/y if y else np.nan
        values=dict(issued=n,scored=scored,unavailable=n-scored,violations=e,unresolved=missing,
            positive=p,positive_rate=ratio(p,n),positive_scored=p-missing,positive_covered=p-missing-e,
            v_given_positive=ratio(e,p-missing),positive_low=ratio(e,p),positive_high=ratio(e+missing,p),
            observed_sum=observed_sum,delivered_sum=delivered,v=ratio(e,scored),coverage=1-ratio(e,scored),
            lo=ratio(e,n),hi=ratio(e+missing,n),u=ratio(delivered,observed_sum),
            mae=float(error.abs().mean()),rmse=float(np.sqrt((error**2).mean())),median_absolute_error=float(error.abs().median()),
            scheduled=len(a),eligible=n,issued_point=n,abstained=len(a)-p,commitment_coverage=ratio(p,len(a)),
            positive_dates=a.loc[a.lower>0,'date'].nunique(),dates=a.date.nunique(),attempts=10+q,
            response_labels=int(r.observed.sum()),missing_responses=q-int(r.observed.sum()),
            recalibrations=len(admitted),effective_updates=int((admitted.ready<=a.issue.max()).sum()),
            initial_calibration_observations=10,new_query_attempts=q,successful_responses=int(r.observed.sum()),
            unsuccessful_responses=q-int(r.observed.sum()),admitted_calibration_updates=len(admitted),
            initial_label_plus_query_count=10+q,exact_cost=q==cap)
        for field,value in values.items():
            same(s[field],value,where,field)
        if policy=='Frozen':
            require(q==0,where,'Frozen must have zero new queries')
        truth[key]=values; aligned[key]=a.set_index('id')
    expected_pairs={k[:-1]+(b,) for k in expected_keys if k[-1]=='MARUR' for b in POLICIES[:-1]}
    pair_lookup=index_table(pairs,PAIR_KEYS,'pairs',expected_pairs)
    expected_decomp=set()
    for key,row in pair_lookup.iterrows():
        prefix=key[:-1]; baseline=key[-1]; where=f'pair {key}'
        ma=truth[prefix+('MARUR',)]; ba=truth[prefix+(baseline,)]
        equal=ma['new_query_attempts']==ba['new_query_attempts']==prefix[-1]
        same(row.matched,equal,where,'matched status from actual attempts')
        same(row.marur_queries,ma['new_query_attempts'],where,'marur_queries')
        same(row.baseline_queries,ba['new_query_attempts'],where,'baseline_queries')
        for field in DELTAS:
            same(row[field+'_delta'],ma[field]-ba[field],where,field+'_delta')
        if equal:
            expected_decomp.add(key)
    dec=index_table(decomposition,PAIR_KEYS,'offer decomposition',expected_decomp)
    for key,row in dec.iterrows():
        prefix=key[:-1]; a=aligned[prefix+('MARUR',)]; b=aligned[prefix+(key[-1],)].loc[a.index]
        mp=a.lower>0; bp=b.lower>0; mf=a.lower>a.y; bf=b.lower>b.y
        values=dict(shared_offers=int((mp&bp).sum()),removed_offers=int((bp&~mp).sum()),added_offers=int((mp&~bp).sum()),
            failures_removed_with_offers=int((bf&~mp).sum()),failures_added_with_offers=int((mf&~bp).sum()),
            shared_failure_delta=int((mf&bp).sum()-(bf&mp).sum()),failure_delta=int(mf.sum()-bf.sum()),
            lower_sum_delta=float(a.lower.sum()-b.lower.sum()))
        for field,value in values.items():
            same(row[field],value,f'decomposition {key}',field)
    return len(expected_keys),len(expected_pairs),len(expected_decomp)


def validate(root=ROOT):
    out=root/'results/marur_audit'
    read=lambda name: pd.read_csv(out/name,float_precision='round_trip')
    source=pd.read_csv(root/'results/marur/opportunities.csv.gz',float_precision='round_trip')
    expected=set(product(['E1','E3','AT&T','T-Mobile','Verizon','Ireland'],
                         ['HistGBM','Persistence'],['Recorded','QueryCensor20'],CAPS,POLICIES))
    counts=validate_frames(read('matched_cost_summary.csv'),read('matched_cost_actions.csv.gz'),
        read('matched_cost_responses.csv.gz'),read('matched_cost_pairs.csv'),read('offer_decomposition.csv'),source,expected)
    old=read('pre_audit_summary.csv'); new=pd.read_csv(root/'results/marur/summary.csv',float_precision='round_trip')
    cols=[c for c in old if c!='seconds']
    pd.testing.assert_frame_equal(old[cols],new[cols],check_exact=False,rtol=1e-12,atol=1e-12)
    print(f'Validated {counts[0]} configurations, all {counts[1]} stored pairs and {counts[2]} exact-cost decompositions; original metrics unchanged.')

if __name__=='__main__':
    validate()
