"""Integration tests verifying split protocol on authentic Zenodo measurement archives."""
import pytest
from tests.conftest import skip_if_no_raw_data
from src.data.loader import load_raw_8224890, extract_sessions_8224890
from src.data.splits import create_experiment_splits

@pytest.mark.integration
@skip_if_no_raw_data
def test_real_8224890_split_disjointness():
    """Verify that transfer splits between real Op1 and Op2 have disjoint dates and valid subsets."""
    raw_df = load_raw_8224890()
    sdf, fdf = extract_sessions_8224890(raw_df)
    
    op1_df = fdf[fdf['operator'] == 'Op1'].copy()
    op2_df = fdf[fdf['operator'] == 'Op2'].copy()
    
    splits = create_experiment_splits(op1_df, op2_df, budgets=[0, 1, 2, 5, 10])
    
    train_dates = set(splits.train['date'].unique())
    val_dates = set(splits.val['date'].unique())
    source_calib_dates = set(splits.source_calib['date'].unique())
    
    assert train_dates.isdisjoint(val_dates)
    assert train_dates.isdisjoint(source_calib_dates)
    assert val_dates.isdisjoint(source_calib_dates)
    
    target_pool_dates = set(splits.target_calib_pool['date'].unique())
    target_test_dates = set(splits.target_test['date'].unique())
    assert target_pool_dates.isdisjoint(target_test_dates)

@pytest.mark.integration
@skip_if_no_raw_data
def test_real_e0_within_domain_split_disjointness():
    """Verify that E0 within-domain partitioning is 100% disjoint with zero train/test leakage."""
    raw_df = load_raw_8224890()
    sdf, fdf = extract_sessions_8224890(raw_df)
    op1_df = fdf[fdf['operator'] == 'Op1'].copy()
    
    splits = create_experiment_splits(op1_df, op1_df, budgets=[0, 1, 2, 5, 8, 9, 10, 15], experiment_type="within_domain")
    
    s_tr = set(splits.train['session_id'])
    s_va = set(splits.val['session_id'])
    s_ca = set(splits.source_calib['session_id'])
    s_po = set(splits.target_calib_pool['session_id'])
    s_te = set(splits.target_test['session_id'])
    
    parts = [s_tr, s_va, s_ca, s_po, s_te]
    for i, left in enumerate(parts):
        for right in parts[i + 1:]:
            assert left.isdisjoint(right), "FATAL LEAKAGE: Overlap between E0 partitions!"
            
    # Check budget 15 is None (only 10 sessions in calibration pool)
    assert splits.target_prefix_sessions[15] is None

