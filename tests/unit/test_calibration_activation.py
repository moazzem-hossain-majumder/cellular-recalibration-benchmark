import numpy as np
import pytest
from src.evaluation.conformal import compute_conformal_quantile, GroupedConformalCalibrator

@pytest.mark.parametrize("alpha,n,rank",[(.1,0,None),(.1,8,None),(.1,9,9),(.1,10,10),(.1,19,18),(.2,3,None),(.2,4,4),(.05,18,None),(.05,19,19)])
def test_order_statistic(alpha,n,rank):
    scores = np.arange(n,0,-1)
    assert compute_conformal_quantile(scores,alpha) == (np.inf if rank is None else rank)

def test_ties_and_pooled_fallback():
    scores = np.ones(10)
    cal = GroupedConformalCalibrator(.1,3,1,99).fit(scores,np.zeros(10),np.repeat([0,1],5))
    assert compute_conformal_quantile(scores,.1) == 1
    lower, missing = cal.predict_lower_bound(np.array([5.]),np.array([0]))
    assert lower.tolist() == [4.] and not missing.any()
