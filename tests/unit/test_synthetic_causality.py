"""Synthetic unit tests for production data loading, causal lag freshness, and session segmentation."""
import pytest
import numpy as np
import pandas as pd
from src.data.loader import filter_causal_forecast_instances, segment_ookla_speedtests

@pytest.mark.unit
def test_production_freshness_gate_boundary():
    """Verify that the production 60-second lag freshness gate strictly excludes stale lags."""
    test_df = pd.DataFrame({
        'session_id': [1, 2, 3, 4, 5],
        'lag_age_s': [0.0, 10.0, 59.9, 60.0, 60.001],
        'target_y': [50.0, 60.0, 70.0, 80.0, 90.0]
    })
    gated_df = filter_causal_forecast_instances(test_df, window_seconds=60.0)
    assert len(gated_df) == 4
    assert (gated_df['lag_age_s'] <= 60.0).all()
    assert 60.001 not in gated_df['lag_age_s'].values

@pytest.mark.unit
def test_production_negative_lag_age_rejection():
    """Verify that negative lag ages (acausal drift / future leakage) are strictly rejected by production filter."""
    test_df = pd.DataFrame({
        'session_id': [1, 2, 3],
        'lag_age_s': [-0.001, -5.0, 1.0],
        'target_y': [20.0, 30.0, 40.0]
    })
    gated_df = filter_causal_forecast_instances(test_df, window_seconds=60.0)
    assert len(gated_df) == 1
    assert gated_df['session_id'].iloc[0] == 3

@pytest.mark.unit
def test_production_missing_timestamp_rejection():
    """Verify that sessions with missing or null timestamps produce NaN lag age and are rejected by production filter."""
    test_df = pd.DataFrame({
        'session_id': [1, 2, 3],
        'lag_age_s': [np.nan, None, 5.0],
        'target_y': [20.0, 30.0, 40.0]
    })
    gated_df = filter_causal_forecast_instances(test_df, window_seconds=60.0)
    assert len(gated_df) == 1
    assert gated_df['session_id'].iloc[0] == 3

@pytest.mark.unit
def test_production_zero_throughput_vs_nan_label_handling():
    """Verify that genuine zero throughput (y=0.0) is retained while NaN target is rejected by production filter."""
    test_df = pd.DataFrame({
        'session_id': [1, 2, 3],
        'lag_age_s': [1.0, 2.0, 3.0],
        'target_y': [0.0, np.nan, 45.0]
    })
    gated_df = filter_causal_forecast_instances(test_df, window_seconds=60.0)
    assert len(gated_df) == 2
    assert 0.0 in gated_df['target_y'].values
    assert not gated_df['target_y'].isna().any()

@pytest.mark.unit
def test_production_segment_ookla_speedtests_standard_reset():
    """Verify production segment_ookla_speedtests detects genuine throughput resets."""
    # Simulates active test (ramp up, plateau, then drop to near zero at reset)
    series = pd.Series([10.0, 50.0, 100.0, 80.0, 0.001, 15.0, 60.0, 90.0, 0.002])
    test_ids = segment_ookla_speedtests(series, diff_thresh=-5.0, val_thresh=5.0, method="reset")
    # Resets occur at index 4 (80.0 -> 0.001) and index 8 (90.0 -> 0.002)
    assert test_ids.nunique() == 3
    assert test_ids.iloc[0] == 0
    assert test_ids.iloc[4] == 1
    assert test_ids.iloc[8] == 2

@pytest.mark.unit
def test_production_segment_ookla_speedtests_relative_drop():
    """Verify production segment_ookla_speedtests supports relative_drop strategy for low-rate tests."""
    series = pd.Series([2.5, 4.5, 4.2, 0.001, 3.0, 4.8, 0.001])
    # Standard reset (-5.0 threshold) would miss a drop from 4.2 to 0.001 (diff = -4.199)
    test_ids_std = segment_ookla_speedtests(series, diff_thresh=-5.0, val_thresh=5.0, method="reset")
    assert test_ids_std.nunique() == 1  # Missed because drop < 5 Mbps
    
    # Relative drop strategy captures the reset
    test_ids_rel = segment_ookla_speedtests(series, method="relative_drop")
    assert test_ids_rel.nunique() == 3
