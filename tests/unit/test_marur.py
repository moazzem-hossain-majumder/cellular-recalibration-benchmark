import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from scripts.validate_clock_and_network import clock_pairs
from src.evaluation.marur import replay

CONFIG=json.loads((Path(__file__).resolve().parents[2]/'configs/marur.json').read_text())


def data():
    initial=pd.DataFrame(dict(id=['c'+str(i) for i in range(10)],issue=np.arange(10)*60.,
        ready=(np.arange(10)+1)*60.,point=10.,y=10.,pattern=3,date='2020-01-01'))
    stream=pd.DataFrame(dict(id=['t'+str(i) for i in range(6)],issue=10000.+np.arange(6)*60,
        ready=10060.+np.arange(6)*60,point=10.,y=[0.,10.,10.,10.,10.,10.],
        pattern=3,date='2020-01-02'))
    return initial,stream


def test_query_selected_before_outcome_and_revealed_at_horizon():
    initial,stream=data()
    first,_=replay(initial,stream,'Early',11,CONFIG)
    changed=stream.copy()
    changed.loc[0,'y']=10.
    second,_=replay(initial,changed,'Early',11,CONFIG)
    pd.testing.assert_series_equal(first.iloc[0].drop('y'),second.iloc[0].drop('y'))
    assert first.iloc[1].lower==0 and second.iloc[1].lower==10
    assert first['query'].sum()==1 and first.attempts.max()==11


def test_future_labels_cannot_change_earlier_actions():
    initial,stream=data()
    altered=stream.copy()
    altered.loc[3:,'y']=np.nan
    a,_=replay(initial,stream,'Early',15,CONFIG)
    b,_=replay(initial,altered,'Early',15,CONFIG)
    pd.testing.assert_frame_equal(a.iloc[:4].drop(columns='y'),b.iloc[:4].drop(columns='y'))


def test_missing_queries_cost_budget_and_conservative_score():
    initial,stream=data()
    stream.loc[0,'y']=np.nan
    actions,responses=replay(initial,stream,'Early',11,CONFIG)
    assert len(responses)==1 and not responses.iloc[0].observed
    assert responses.iloc[0].score==10
    assert actions.iloc[1].lower==0 and actions.attempts.max()==11


def test_same_timestamp_receives_identical_state():
    initial,stream=data()
    stream.loc[1,['issue','ready']]=stream.loc[0,['issue','ready']].to_numpy()
    actions,responses=replay(initial,stream,'Early',12,CONFIG)
    assert actions.iloc[0].lower==actions.iloc[1].lower==10
    assert actions.iloc[:2]['query'].sum()==1
    assert responses.query_time.is_unique


def test_unsupported_pattern_abstains_and_no_lag_is_retained():
    initial,stream=data()
    stream.loc[0,'point']=np.nan
    stream.loc[1:,'pattern']=0
    actions,_=replay(initial,stream,'MARUR',10,CONFIG)
    assert len(actions)==len(stream) and not actions.iloc[0].eligible
    assert actions.lower.sum()==0
    assert set(actions.reason)=={'no_lag','unsupported_pattern'}


def test_aci_changes_nominal_level_at_completion():
    initial,stream=data()
    actions,responses=replay(initial,stream,'ACI',11,CONFIG)
    assert responses.iloc[0].alpha_after==pytest.approx(.055)
    assert actions.iloc[0].alpha==.1
    assert actions.iloc[1].alpha==pytest.approx(.055)


def test_clock_roster_includes_scheduled_no_lag_rows():
    times=pd.to_datetime(['2020-01-01 00:00','2020-01-01 00:01','2020-01-01 00:02'])
    series=pd.Series([np.nan,10.,8.],index=times)
    all_ticks=clock_pairs(series,times.min(),times.max(),include_ineligible=True)
    old=clock_pairs(series,times.min(),times.max())
    assert len(all_ticks)==3 and len(old)==1
    pd.testing.assert_frame_equal(all_ticks.dropna(subset=['lag']),old)


@pytest.mark.parametrize('policy',['MARUR','MARUR_DropMissing'])
def test_failed_response_resets_trigger_even_if_not_admitted(policy):
    initial,stream=data()
    stream.loc[:,'y']=np.nan
    stream.loc[:,'pattern']=0
    # All later rows have the same new pattern. Failure resets both trigger state
    # variables, so there is no repeated query just because support remains zero.
    a,r=replay(initial,stream,policy,50,CONFIG)
    assert a['query'].tolist()==[True,False,False,False,False,False]
    assert a.iloc[1].last_feedback==stream.iloc[0].ready
    assert len(r)==1 and not r.iloc[0].observed
    assert bool(r.iloc[0].admitted)==(policy=='MARUR')


def test_failed_response_age_trigger_waits_sixty_minutes_from_completion():
    initial,stream=data()
    stream=stream.iloc[:3].copy()
    stream.loc[:,'issue']=[10000.,13600.,13660.]
    stream.loc[:,'ready']=stream.issue+60
    stream.loc[:,'y']=np.nan
    a,r=replay(initial,stream,'MARUR_DropMissing',50,CONFIG)
    assert a['query'].tolist()==[True,False,True]
    assert not r.admitted.any()


def test_dropmissing_changes_admission_but_not_query_schedule():
    initial,stream=data()
    stream.loc[:,'y']=np.nan
    stream.loc[:,'pattern']=[0,0,3,3,0,0]
    a,ra=replay(initial,stream,'MARUR',50,CONFIG)
    b,rb=replay(initial,stream,'MARUR_DropMissing',50,CONFIG)
    pd.testing.assert_series_equal(a['query'],b['query'])
    pd.testing.assert_series_equal(a.last_feedback,b.last_feedback)
    assert ra.admitted.all() and not rb.admitted.any()
