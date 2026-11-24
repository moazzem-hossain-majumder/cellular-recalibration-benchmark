import numpy as np
import pandas as pd
from tests.unit.test_marur import data,CONFIG
from src.evaluation.marur import replay
from scripts.run_reviewer_baselines import random_schedule

def test_random_schedule_is_nested_and_outcome_independent():
    _,s=data();a=random_schedule(s,2,42);b=random_schedule(s,4,42)
    assert set(a)<=set(b)
    assert a==random_schedule(s.assign(y=np.nan),2,42)
    initial,s=data();cfg=dict(CONFIG,query_schedule_ids=a)
    x,_=replay(initial,s,'Random',12,cfg)
    assert set(x.loc[x['query'],'id'])==set(a)

def test_decaying_update_has_right_sign_scale_and_delay():
    initial,s=data();cfg=dict(CONFIG,period_ticks=1,log_score_diagnostics=True)
    a,r=replay(initial,s,'DecayingOGD',12,cfg)
    assert a.iloc[0].offset==0
    assert a.iloc[1].offset==.9 # scale floor 1, first score 10 > 0
    assert np.isclose(a.iloc[2].offset,.9-.1/(2**.6))
    changed=s.copy();changed.loc[0,'y']=10
    b,_=replay(initial,changed,'DecayingOGD',12,cfg)
    assert b.iloc[0].lower==a.iloc[0].lower
    assert b.iloc[1].offset==-.1

def test_pooled_gate_ablation_preserves_queries():
    initial,s=data();s['pattern']=0
    a,_=replay(initial,s,'MARUR',15,CONFIG)
    b,_=replay(initial,s,'MARUR',15,dict(CONFIG,calibration_scope='pooled'))
    c,_=replay(initial,s,'MARUR',15,dict(CONFIG,calibration_scope='pooled',pattern_gate=False))
    pd.testing.assert_series_equal(a['query'],b['query']);pd.testing.assert_series_equal(b['query'],c['query'])
    assert a.iloc[0].lower==b.iloc[0].lower==0 and c.iloc[0].lower==10
