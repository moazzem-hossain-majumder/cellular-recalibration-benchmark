import numpy as np
import pandas as pd
import pytest

from scripts.validate_clock_and_network import clock_pairs
from src.evaluation.conformal import compute_conformal_quantile


def test_future_reading_cannot_trigger_or_change_issued_forecast():
    times = pd.to_datetime(['2023-01-02 00:00:50','2023-01-02 00:01:00','2023-01-02 00:02:00'])
    def replay(value):
        return clock_pairs(pd.Series([10.,value,4.],index=times),times.min(),times.max()).iloc[0]
    measured,missing = replay(500.),replay(np.nan)
    assert measured.time==missing.time==times[1]
    assert measured.lag==missing.lag==10.
    assert measured.y==500 and np.isnan(missing.y)


def test_decimal_quantile_boundary_and_invalid_calibration():
    # (10 * (1 - .7)) is exactly three.
    assert compute_conformal_quantile(np.arange(1,10),.7)==3
    with pytest.raises(ValueError,match='finite'):
        compute_conformal_quantile(np.array([np.nan]*10))
