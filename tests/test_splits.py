"""Unit tests for split protocol integrity and disjoint windows."""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.loader import load_raw_8224890, extract_sessions_8224890
from src.data.splits import create_experiment_splits

def test_split_independence_and_disjointness():
    raw_df = load_raw_8224890()
    sdf, fdf = extract_sessions_8224890(raw_df)
    
    op1_df = fdf[fdf['operator'] == 'Op1'].copy()
    op2_df = fdf[fdf['operator'] == 'Op2'].copy()
    
    splits = create_experiment_splits(op1_df, op2_df, budgets=[0, 1, 2, 5, 10])
    
    # 1. Check that source splits are disjoint in dates
    train_dates = set(splits.train['date'].unique())
    val_dates = set(splits.val['date'].unique())
    source_calib_dates = set(splits.source_calib['date'].unique())
    
    assert train_dates.isdisjoint(val_dates), 'Overlap between source train and val dates!'
    assert train_dates.isdisjoint(source_calib_dates), 'Overlap between source train and source calib dates!'
    assert val_dates.isdisjoint(source_calib_dates), 'Overlap between source val and source calib dates!'
    
    # 2. Check that target calibration pool and fixed test suffix are disjoint
    target_pool_dates = set(splits.target_calib_pool['date'].unique())
    target_test_dates = set(splits.target_test['date'].unique())
    assert target_pool_dates.isdisjoint(target_test_dates), 'Overlap between target calib pool and test suffix dates!'
    
    # 3. Check that budgets prefixes are subsets of calibration pool
    for k in [1, 2, 5, 10]:
        prefix_df = splits.target_prefix_sessions[k]
        assert len(prefix_df) <= k
        if len(prefix_df) > 0:
            assert set(prefix_df['session_id']).issubset(set(splits.target_calib_pool['session_id']))
            assert set(prefix_df['session_id']).isdisjoint(set(splits.target_test['session_id']))

def test_e0_within_domain_split_disjointness():
    """Verify that E0 within-domain partitioning is 100% disjoint with zero train/test leakage."""
    raw_df = load_raw_8224890()
    sdf, fdf = extract_sessions_8224890(raw_df)
    op1_df = fdf[fdf['operator'] == 'Op1'].copy()
    
    # E0: Within-domain splits
    splits = create_experiment_splits(op1_df, op1_df, budgets=[0, 1, 2, 5, 8, 9, 10])
    
    s_tr = set(splits.train['session_id'])
    s_va = set(splits.val['session_id'])
    s_ca = set(splits.source_calib['session_id'])
    s_te = set(splits.target_test['session_id'])
    
    # Assert pairwise session ID disjointness
    assert s_tr.isdisjoint(s_te), "CRITICAL LEAKAGE: E0 train overlaps with test suffix!"
    assert s_va.isdisjoint(s_te), "CRITICAL LEAKAGE: E0 val overlaps with test suffix!"
    assert s_ca.isdisjoint(s_te), "CRITICAL LEAKAGE: E0 calib overlaps with test suffix!"
    s_target_cal = set(splits.target_calib_pool['session_id'])
    assert s_ca.isdisjoint(s_target_cal), "CRITICAL LEAKAGE: E0 source calibration overlaps target calibration pool!"
    assert s_tr.isdisjoint(s_va), "E0 train overlaps with val!"
    assert s_tr.isdisjoint(s_ca), "E0 train overlaps with calib!"
    
    # Assert date disjointness
    d_tr = set(splits.train['date'].unique())
    d_te = set(splits.target_test['date'].unique())
    assert d_tr.isdisjoint(d_te), "E0 train dates overlap with test dates!"
    d_src_cal = set(splits.source_calib['date'].unique())
    d_tgt_cal = set(splits.target_calib_pool['date'].unique())
    assert d_src_cal.isdisjoint(d_tgt_cal), "E0 source-calibration dates overlap target-calibration dates!"

if __name__ == '__main__':
    test_split_independence_and_disjointness()
    test_e0_within_domain_split_disjointness()
    print('Split integrity tests PASSED.')

