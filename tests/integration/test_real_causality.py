"""Integration tests verifying causality, freshness, and physical ranges on real data."""
import pytest
from tests.conftest import skip_if_no_raw_data
from src.data.loader import load_raw_8224890, extract_sessions_8224890, load_14073311_ookla

@pytest.mark.integration
@skip_if_no_raw_data
def test_real_8224890_causal_lag_freshness_and_ordering():
    """Verify lag freshness, non-negativity, and realistic physical ranges in 8224890."""
    raw_df = load_raw_8224890()
    sdf, fdf = extract_sessions_8224890(raw_df)
    
    assert (fdf['lag_age_s'] >= 0.0).all(), 'Negative lag age detected (future leakage)!'
    assert (fdf['lag_age_s'] <= 60.0).all(), 'Lag age exceeds 60s freshness cutoff!'
    assert not (fdf['target_y'] == fdf['y_lag1']).all(), 'target_y identical to y_lag1'
    
    valid_rsrp = fdf['rsrp'].dropna()
    assert (valid_rsrp >= -140.0).all() and (valid_rsrp <= -40.0).all(), 'LTE RSRP out of realistic dBm range'
    
    valid_ss_rsrp = fdf['ss_rsrp'].dropna()
    assert (valid_ss_rsrp >= -140.0).all() and (valid_ss_rsrp <= -40.0).all(), '5G SS-RSRP out of realistic dBm range'
    assert set(fdf['group_id'].unique()).issubset({0, 1, 2, 3}), 'Invalid group_id value'

@pytest.mark.integration
@skip_if_no_raw_data
def test_real_14073311_causal_lag_freshness_and_ordering():
    """Verify lag freshness and non-negativity in 14073311."""
    fdf = load_14073311_ookla(window_seconds=60)
    
    assert (fdf['lag_age_s'] >= 0.0).all(), 'Negative lag age detected in 14073311!'
    assert (fdf['lag_age_s'] <= 60.0).all(), 'Lag age exceeds 60s freshness cutoff in 14073311!'
    assert len(fdf) > 0
    assert (fdf['target_y'] >= 0.0).all()

