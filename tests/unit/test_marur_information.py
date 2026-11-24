import numpy as np
import pandas as pd
from tests.unit.test_marur import data,CONFIG
from src.evaluation.marur import replay
from scripts.run_marur_information_experiment import masks

def test_failed_response_does_not_refresh_observed_clock():
    initial,stream=data()
    stream=stream.iloc[:4].copy()
    stream['issue']=[10000.,10240.,10300.,10600.];stream['ready']=stream.issue+60
    cfg=dict(CONFIG,minimum_attempt_spacing_minutes=5,log_information_clocks=True)
    hidden=set(stream.id)
    completed,cr=replay(initial,stream,'MARUR',14,cfg,feedback_unavailable_ids=hidden)
    observed,rr=replay(initial,stream,'MARUR',14,dict(cfg,freshness_clock='observed'),feedback_unavailable_ids=hidden)
    assert completed['query'].tolist()==[True,False,False,False]
    assert observed['query'].tolist()==[True,False,True,True]
    assert (observed.last_observed_label==initial.ready.max()).all()
    assert observed.iloc[1].last_completed_response==10060
    assert observed.iloc[1].last_admitted_score==10060
    assert observed.iloc[1].last_query_attempt==10000
    assert rr.admitted.all() and not rr.observed.any()
    assert observed.iloc[0].lower==completed.iloc[0].lower==10

def test_success_makes_clocks_equivalent():
    initial,stream=data()
    cfg=dict(CONFIG,minimum_attempt_spacing_minutes=5,log_information_clocks=True)
    a,r=replay(initial,stream,'MARUR',15,cfg)
    b,s=replay(initial,stream,'MARUR',15,dict(cfg,freshness_clock='observed'))
    pd.testing.assert_frame_equal(a,b);pd.testing.assert_frame_equal(r,s)

def test_mask_does_not_change_issue_decision_or_evaluation_outcomes():
    initial,stream=data()
    a,r=replay(initial,stream,'Early',11,CONFIG)
    b,s=replay(initial,stream,'Early',11,CONFIG,feedback_unavailable_ids={'t0'})
    pd.testing.assert_series_equal(a.iloc[0],b.iloc[0])
    pd.testing.assert_series_equal(a.y,b.y)
    assert r.iloc[0].observed and not s.iloc[0].observed

def test_larger_window_adds_no_free_labels_and_preserves_query_schedule():
    initial,stream=data()
    a,_=replay(initial,stream,'Early',16,CONFIG)
    b,_=replay(initial,stream,'Early',16,dict(CONFIG,window=40))
    assert a.iloc[0].window_size==b.iloc[0].window_size==10
    assert b.window_size.max()==15
    pd.testing.assert_series_equal(a['query'],b['query'])

def test_masks_are_shared_by_timestamp_and_do_not_use_outcomes():
    _,stream=data();stream=pd.concat([stream,stream.assign(id=stream.id+'duplicate')])
    spec=dict(burst_bin_minutes=10,mask_seeds=[42],mask_probability=.5)
    before=list(masks(stream,spec));after=list(masks(stream.assign(y=999.),spec))
    assert before==after
    for _,hidden in before:
        for ident in ['t0','t1','t2','t3','t4','t5']:
            assert (ident in hidden)==(ident+'duplicate' in hidden)
