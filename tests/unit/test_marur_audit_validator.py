"""Corruption tests for CSV-backed audit validation, without raw network downloads."""
from itertools import product
from pathlib import Path
import pandas as pd
import pytest
from scripts.validate_marur_audit import validate_frames, DELTAS, POLICIES

ROOT=Path(__file__).resolve().parents[2]
FILES=['matched_cost_summary.csv','matched_cost_actions.csv.gz','matched_cost_responses.csv.gz',
       'matched_cost_pairs.csv','offer_decomposition.csv']

@pytest.fixture(scope='module')
def saved():
    frames=[]
    for name in FILES:
        f=pd.read_csv(ROOT/'results/marur_audit'/name,float_precision='round_trip')
        f=f[(f.cohort=='E1')&(f.model=='HistGBM')&f.new_query_cap.isin([0,10])].reset_index(drop=True)
        frames.append(f)
    source=pd.read_csv(ROOT/'results/marur/opportunities.csv.gz',float_precision='round_trip')
    expected=set(product(['E1'],['HistGBM'],['Recorded','QueryCensor20'],[0,10],POLICIES))
    return frames,source,expected


def check(frames,saved):
    return validate_frames(*frames,saved[1],saved[2])


def test_valid_saved_ledgers(saved):
    assert check(saved[0],saved)[0]==20


@pytest.mark.parametrize('field', [c+'_delta' for c in DELTAS]+['marur_queries','baseline_queries'])
def test_reject_corrupted_pair_csv(saved,tmp_path,field):
    frames=[f.copy(deep=True) for f in saved[0]]
    frames[3].loc[0,field]+=1
    path=tmp_path/'pairs.csv'; frames[3].to_csv(path,index=False)
    frames[3]=pd.read_csv(path,float_precision='round_trip')
    with pytest.raises(ValueError,match=field):
        check(frames,saved)


@pytest.mark.parametrize('table',[0,1,2,3,4])
@pytest.mark.parametrize('fault',['duplicate','missing'])
def test_reject_duplicate_or_missing_csv_rows(saved,tmp_path,table,fault):
    frames=[f.copy(deep=True) for f in saved[0]]
    f=frames[table]
    frames[table]=pd.concat([f,f.iloc[[0]]],ignore_index=True) if fault=='duplicate' else f.iloc[1:]
    path=tmp_path/'corrupted.csv'; frames[table].to_csv(path,index=False)
    frames[table]=pd.read_csv(path,float_precision='round_trip')
    with pytest.raises(ValueError):
        check(frames,saved)


@pytest.mark.parametrize('fault',['false_match','wrong_cap','wrong_model','wrong_scenario','query_count',
    'successful_response','failed_response','admission','effective','budget_overrun','frozen_query',
    'decomposition_balanced','wrong_response_id','future_feedback'])
def test_reject_accounting_and_identity_corruption(saved,fault):
    frames=[f.copy(deep=True) for f in saved[0]]
    s,a,r,p,d=frames
    if fault=='false_match':
        i=p.index[~p.matched][0]; p.loc[i,'matched']=True
    elif fault in ['wrong_cap','wrong_model','wrong_scenario']:
        column,value={'wrong_cap':('new_query_cap',99),'wrong_model':('model','Unknown'),
                      'wrong_scenario':('scenario','MissingScenario')}[fault]
        p.loc[0,column]=value
    elif fault=='query_count': s.loc[0,'new_query_attempts']+=1
    elif fault=='successful_response': r.loc[0,'observed']=False
    elif fault=='failed_response':
        i=r.index[~r.observed][0]; r.loc[i,'observed']=True
    elif fault=='admission': r.loc[0,'admitted']=False
    elif fault=='effective': s.loc[0,'effective_updates']+=1
    elif fault in ['budget_overrun','frozen_query']:
        i=a.index[(a.new_query_cap==0)&(a.policy==('Frozen' if fault=='frozen_query' else 'MARUR'))][0]
        a.loc[i,'query']=True
    elif fault=='decomposition_balanced':
        # Preserves the old algebraic identity but invents a shared failure.
        d.loc[0,'shared_failure_delta']+=1; d.loc[0,'failure_delta']+=1
    elif fault=='wrong_response_id': r.loc[0,'id']='nonexistent'
    else: a.loc[0,'last_feedback']=a.loc[0,'issue']+1
    with pytest.raises(ValueError):
        check(frames,saved)
