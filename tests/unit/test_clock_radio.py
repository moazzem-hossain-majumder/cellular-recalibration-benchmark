import numpy as np
import pandas as pd
from scripts.stress_clock_radio import NR_FIELDS, observed_runs, pretest_runs, remove_nr, scenarios


def test_nr_removal_keeps_lte_and_original_input():
    data = pd.DataFrame({'has_lte':[0,1], 'has_nr':[1,1], 'group_id':[1,3], 'rsrp':[np.nan,-95],
                         **{field:[-70.,-90.] for field in NR_FIELDS}})
    removed = remove_nr(data)
    assert removed[NR_FIELDS].isna().all().all()
    assert removed.group_id.tolist() == [0,2]
    pd.testing.assert_series_equal(removed.rsrp, data.rsrp)
    assert data.has_nr.tolist() == [1,1]


def test_issue_time_masks_and_extreme_commitments():
    data = pd.DataFrame({'time':pd.date_range('2020-01-01', periods=6, freq='min'),
                         'has_nr':[1,1,0,0,1,1], 'ss_rsrp':[-100,-80,np.nan,np.nan,-98,-90]})
    before = np.array([0,1,0,1,1,1])
    after = np.array([1,0,0,1,2,1])
    masks = {(s,n):m for s,n,m in scenarios(data,2,-98,before,after)}
    assert not any(mask[2:4].any() for mask in masks.values())
    np.testing.assert_array_equal(np.where(masks['MaxRate',-1], after, before), np.maximum(before,after))
    np.testing.assert_array_equal(np.where(masks['MinRate',-1], after, before), np.minimum(before,after))
    assert observed_runs(data.assign(trace='A',regime='R')) == [2]
    assert observed_runs(data.drop(index=2).assign(trace='A',regime='R')) == []
    shuffled = data.assign(y=[7,4,2,8,9,5])
    for s,n,m in scenarios(shuffled,2,-98,before,after):
        np.testing.assert_array_equal(masks[s,n],m)


def test_pooled_burst_estimate_precedes_both_test_periods():
    times = pd.date_range('2023-05-09 10:00', periods=6, freq='min')
    calibration = pd.DataFrame({
        'regime': 'E3', 'trace': 'B', 'partition': 'calibration',
        'time': times, 'end': times + pd.Timedelta(minutes=1), 'has_nr': [1, 0, 1, 0, 0, 1],
    })
    first_issue = calibration.iloc[[3]].assign(regime='E1', partition='test')
    assert observed_runs(calibration) == [1, 2]
    assert pretest_runs(pd.concat([calibration, first_issue])) == [1]
