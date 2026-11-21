"""Independently validate controller counts, delayed responses and frozen references."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
KEYS=['cohort','model','scenario','budget','policy']


def validate(root=ROOT):
    folder=root/'results/marur'
    a=pd.read_csv(folder/'actions.csv.gz',float_precision='round_trip')
    responses=pd.read_csv(folder/'responses.csv.gz',float_precision='round_trip')
    source=pd.read_csv(folder/'opportunities.csv.gz',float_precision='round_trip')
    summary=pd.read_csv(folder/'summary.csv',float_precision='round_trip')
    config=json.loads((root/'configs/marur.json').read_text())
    assert len(summary)==576 and not summary.duplicated(KEYS).any()
    grouped=a.groupby(KEYS,sort=False)
    lookup=summary.set_index(KEYS)
    assert set(grouped.groups)==set(lookup.index)
    for key,d in grouped:
        r=lookup.loc[key]
        records=responses
        for field,value in zip(KEYS,key):
            records=records[records[field]==value]
        initial=source[(source.cohort==key[0]) & (source.partition=='cal')]
        assert len(initial)==10 and initial.ready.max()<=d.issue.min()
        expected=source[(source.cohort==key[0]) & (source.partition=='test')].set_index('id')
        assert len(d)==len(expected) and d.id.is_unique and set(d.id)==set(expected.index)
        ref=expected.loc[d.id]
        np.testing.assert_allclose(d.y,ref.y,equal_nan=True)
        np.testing.assert_allclose(d.issue,ref.issue)
        column='HistGBM' if key[0] in ['E1','E3'] and key[1]=='HistGBM' else 'Tree' if key[1]=='HistGBM' else 'Persistence'
        np.testing.assert_allclose(d.point,ref[column],equal_nan=True)
        assert (d.last_feedback<=d.issue).all()
        queries=d[d['query']].set_index('id')
        assert len(queries)==len(records) and set(queries.index)==set(records.id)
        assert d.attempts.max()<=key[3]
        np.testing.assert_array_equal(d.attempts,10+d['query'].cumsum())
        if len(records):
            q=queries.loc[records.id]
            np.testing.assert_allclose(records.query_time,q.issue)
            np.testing.assert_allclose(records.ready,q.ready)
            assert (records.ready>records.query_time).all()
            queried_y=expected.loc[records.id,'y'].to_numpy()
            expected_observed=np.isfinite(queried_y)&~records.censored.to_numpy()
            np.testing.assert_array_equal(records.observed,expected_observed)
            points=q.point.to_numpy()
            np.testing.assert_allclose(records.score,np.where(expected_observed,points-queried_y,points))
            assert not records.censored.any() or key[2]=='QueryCensor20'
        eligible=d[d.eligible]
        lower=eligible.lower
        measured=eligible.y.notna()
        positives=lower>0
        failures=(lower>eligible.y).sum()
        missing=(positives & ~measured).sum()
        assert np.isfinite(d.lower).all() and (d.lower>=0).all()
        assert (d.loc[~d.eligible,'lower']==0).all()
        assert (len(d),len(eligible),measured.sum(),positives.sum(),failures,missing)==(
            r.scheduled,r.eligible,r.scored,r.positive,r.violations,r.unresolved)
        n=len(eligible)
        np.testing.assert_allclose([r.lo,r.hi,r.u,r.commitment_coverage],
            [failures/n,(failures+missing)/n,np.minimum(lower,eligible.y).sum()/eligible.y.sum(),positives.sum()/len(d)])
        assert r.attempts==10+len(records)
        assert r.response_labels==records.observed.sum()
        assert r.missing_responses==len(records)-records.observed.sum()
        assert r.initial_calibration_observations==10
        assert r.new_query_attempts==len(records)
        assert r.initial_label_plus_query_count==r.attempts==10+len(records)
        assert r.successful_responses==r.response_labels
        assert r.unsuccessful_responses==r.missing_responses
        assert r.admitted_calibration_updates==r.recalibrations==records.admitted.sum()
        assert r.effective_updates==((records.admitted)&(records.ready<=d.issue.max())).sum()
        if key[4]=='Frozen':
            col='HistGBM' if key[0] in ['E1','E3'] and key[1]=='HistGBM' else 'Tree' if key[1]=='HistGBM' else 'Persistence'
            residual=(initial[col]-initial.y).max()
            np.testing.assert_allclose(lower,np.maximum(0,eligible.point-residual))
        if key[4].startswith('MARUR') and key[4]!='MARUR_NoPattern':
            assert (d.loc[d.pattern_support<config['minimum_pattern_support'],'lower']==0).all()
    # All policies get the same point error and eligible opportunities within a cohort/model.
    counts=summary.groupby(['cohort','model'])[['scheduled','eligible','scored','mae','rmse','median_absolute_error']].nunique()
    assert (counts==1).all().all()
    assert len(a)==len(a.drop_duplicates(KEYS+['id']))
    for scope,fields in [('policy',KEYS[:4]),('date',KEYS[:4]+['date'])]:
        table=summary if scope=='policy' else pd.read_csv(folder/'dates.csv',float_precision='round_trip')
        cols=['u','hi','positive_high','attempts'] if scope=='policy' else ['u','hi','positive_high','commitment_coverage']
        base=table[table.policy=='Periodic'].set_index(fields)
        candidate=table[table.policy=='MARUR'].set_index(fields)
        expected=(candidate[cols]-base[cols]).sort_index()
        actual=pd.read_csv(folder/f'paired_{scope}_contrasts.csv').set_index(fields).sort_index()
        assert actual.index.equals(expected.index)
        np.testing.assert_allclose(actual[[c+'_delta' for c in cols]],expected,equal_nan=True,atol=1e-12)
    print(f'Validated {len(summary)} controller configurations, {len(a)} actions and {len(responses)} feedback responses.')


if __name__=='__main__':
    validate()
