import numpy as np
from scripts.clock_frontier import metrics


def test_sharp_issued_bounds_include_missing_positive_only():
    point = np.array([7.,9.,10.,3.,3.])
    lower = np.array([3.,4.,0.,2.,1.])
    y = np.array([2.,4.,np.nan,np.nan,5.])
    result = metrics(y,point,lower)
    assert (result['scored'],result['violations'],result['unresolved'])==(3,1,1)
    assert result['lo']==(lower>np.where(np.isnan(y),lower,y)).mean()
    assert result['hi']==(lower>np.nan_to_num(y)).mean()


def test_missing_only_keeps_issued_risk_and_undefined_utility():
    result = metrics([np.nan,np.nan],[2,3],[0,2])
    assert result['lo']==0 and result['hi']==.5 and np.isnan(result['u'])
