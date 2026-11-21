"""Recompute exact-cost metrics directly from the saved critical-audit ledgers."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
KEYS=['cohort','model','scenario','new_query_cap','policy']

def validate():
    out=ROOT/'results/marur_audit'
    summary=pd.read_csv(out/'matched_cost_summary.csv').set_index(KEYS)
    actions=pd.read_csv(out/'matched_cost_actions.csv.gz')
    responses=pd.read_csv(out/'matched_cost_responses.csv.gz')
    rg={k:g for k,g in responses.groupby(KEYS)}
    assert len(summary)==720 and summary.index.is_unique
    for key,a in actions.groupby(KEYS):
        s=summary.loc[key]; r=rg.get(key,responses.iloc[:0])
        q=int(a['query'].sum()); e=int((a.lower>a.y).sum())
        m=int(((a.lower>0)&a.y.isna()).sum()); p=int((a.lower>0).sum())
        n=int(a.eligible.sum()); observed=a.y.notna()&a.eligible
        assert q<=key[3] and q==len(r)==s.new_query_attempts
        assert s.initial_calibration_observations==10
        assert s.initial_label_plus_query_count==10+q
        assert s.successful_responses==r.observed.sum()
        assert s.unsuccessful_responses==q-r.observed.sum()
        assert s.admitted_calibration_updates==r.admitted.sum()
        assert s.effective_updates==((r.admitted)&(r.ready<=a.issue.max())).sum()
        assert s.exact_cost==(q==key[3])
        np.testing.assert_allclose([s.lo,s.hi,s.positive_low,s.positive_high,s.u,
            s.commitment_coverage,s.abstained,s.positive_dates],
            [e/n,(e+m)/n,e/p if p else np.nan,(e+m)/p if p else np.nan,
             np.minimum(a.loc[observed,'lower'],a.loc[observed,'y']).sum()/a.loc[observed,'y'].sum(),
             p/len(a),len(a)-p,a.loc[a.lower>0,'date'].nunique()],equal_nan=True,atol=1e-12)
        if p:
            np.testing.assert_allclose(s.hi,(p/n)*s.positive_high,atol=1e-12)
        if key[-1]=='Frozen':
            assert q==0
    pairs=pd.read_csv(out/'matched_cost_pairs.csv')
    for r in pairs.itertuples():
        prefix=(r.cohort,r.model,r.scenario,r.new_query_cap)
        a=summary.loc[prefix+('MARUR',)]; b=summary.loc[prefix+(r.baseline,)]
        assert r.matched==(a.new_query_attempts==b.new_query_attempts==r.new_query_cap)
        np.testing.assert_allclose(r.u_delta,a.u-b.u,atol=1e-12)
    dec=pd.read_csv(out/'offer_decomposition.csv')
    assert (dec.failure_delta==-dec.failures_removed_with_offers+
            dec.failures_added_with_offers+dec.shared_failure_delta).all()
    old=pd.read_csv(out/'pre_audit_summary.csv')
    new=pd.read_csv(ROOT/'results/marur/summary.csv')
    cols=[c for c in old if c!='seconds']
    pd.testing.assert_frame_equal(old[cols],new[cols])
    print(f'Validated {len(summary)} replay summaries and {int(pairs.matched.sum())} exact-cost contrasts; original scientific metrics unchanged.')

if __name__=='__main__':
    validate()
