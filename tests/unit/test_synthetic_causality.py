"""Synthetic unit tests for causal lag freshness, non-negativity, and target label handling."""
import pytest
import numpy as np
import pandas as pd

@pytest.mark.unit
def test_freshness_gate_boundary():
    """Verify that the 60-second lag freshness gate strictly excludes stale lags."""
    test_df = pd.DataFrame({
        'session_id': [1, 2, 3, 4, 5],
        'lag_age_s': [0.0, 10.0, 59.9, 60.0, 60.001],
        'target_y': [50.0, 60.0, 70.0, 80.0, 90.0]
    })
    valid_mask = (
        pd.notna(test_df['lag_age_s']) &
        (test_df['lag_age_s'] >= 0.0) &
        (test_df['lag_age_s'] <= 60.0) &
        pd.notna(test_df['target_y'])
    )
    gated_df = test_df[valid_mask]
    assert len(gated_df) == 4
    assert (gated_df['lag_age_s'] <= 60.0).all()
    assert 60.001 not in gated_df['lag_age_s'].values

@pytest.mark.unit
def test_negative_lag_age_rejection():
    """Verify that negative lag ages (acausal drift / future leakage) are strictly rejected."""
    test_df = pd.DataFrame({
        'session_id': [1, 2, 3],
        'lag_age_s': [-0.001, -5.0, 1.0],
        'target_y': [20.0, 30.0, 40.0]
    })
    valid_mask = (
        pd.notna(test_df['lag_age_s']) &
        (test_df['lag_age_s'] >= 0.0) &
        (test_df['lag_age_s'] <= 60.0) &
        pd.notna(test_df['target_y'])
    )
    gated_df = test_df[valid_mask]
    assert len(gated_df) == 1
    assert gated_df['session_id'].iloc[0] == 3

@pytest.mark.unit
def test_missing_timestamp_rejection():
    """Verify that sessions with missing or null timestamps produce NaN lag age and are rejected."""
    test_df = pd.DataFrame({
        'session_id': [1, 2, 3],
        'lag_age_s': [np.nan, None, 5.0],
        'target_y': [20.0, 30.0, 40.0]
    })
    valid_mask = (
        pd.notna(test_df['lag_age_s']) &
        (test_df['lag_age_s'] >= 0.0) &
        (test_df['lag_age_s'] <= 60.0) &
        pd.notna(test_df['target_y'])
    )
    gated_df = test_df[valid_mask]
    assert len(gated_df) == 1
    assert gated_df['session_id'].iloc[0] == 3

@pytest.mark.unit
def test_zero_throughput_vs_nan_label_handling():
    """Verify that genuine zero throughput (y=0.0) is retained while NaN target is rejected."""
    test_df = pd.DataFrame({
        'session_id': [1, 2, 3],
        'lag_age_s': [1.0, 2.0, 3.0],
        'target_y': [0.0, np.nan, 45.0]
    })
    valid_mask = (
        pd.notna(test_df['lag_age_s']) &
        (test_df['lag_age_s'] >= 0.0) &
        (test_df['lag_age_s'] <= 60.0) &
        pd.notna(test_df['target_y'])
    )
    gated_df = test_df[valid_mask]
    assert len(gated_df) == 2
    assert 0.0 in gated_df['target_y'].values
    assert not gated_df['target_y'].isna().any()

