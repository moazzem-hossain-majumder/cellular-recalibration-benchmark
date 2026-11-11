"""Synthetic unit tests for telecommunications reliability metrics and statistical bootstrap."""
import pytest
import numpy as np
import pandas as pd
from src.evaluation.metrics import (
    compute_reliability_metrics,
    compute_subgroup_metrics,
    paired_day_cluster_bootstrap,
    ReliabilityMetrics
)

@pytest.mark.unit
def test_metrics_edge_cases():
    """Verify metrics under perfect bounds, complete violation, all-zero policy, and physical zero targets."""
    # 1. Perfect bounds
    y_true = np.array([10.0, 20.0, 30.0])
    bounds = np.array([10.0, 20.0, 30.0])
    m = compute_reliability_metrics(y_true, y_true, bounds)
    assert m.violation_rate == 0.0
    assert m.supported_rate_fraction == 1.0
    assert m.mean_overcommitment == 0.0
    
    # 2. Complete violation
    bounds_high = np.array([15.0, 25.0, 35.0])
    m_high = compute_reliability_metrics(y_true, y_true, bounds_high)
    assert m_high.violation_rate == 1.0
    assert m_high.mean_overcommitment == 5.0
    
    # 3. All-zero policy
    bounds_zero = np.zeros(3)
    m_zero = compute_reliability_metrics(y_true, y_true, bounds_zero)
    assert m_zero.violation_rate == 0.0
    assert m_zero.supported_rate_fraction == 0.0
    assert m_zero.zero_bound_fraction == 1.0
    
    # 4. Measured zero throughput
    y_with_zero = np.array([0.0, 10.0, 20.0])
    bounds_test = np.array([0.0, 5.0, 10.0])
    m_w_zero = compute_reliability_metrics(y_with_zero, y_with_zero, bounds_test)
    assert m_w_zero.violation_rate == 0.0
    assert m_w_zero.supported_rate_fraction == (0.0 + 5.0 + 10.0) / (0.0 + 10.0 + 20.0)

@pytest.mark.unit
def test_subgroup_metrics_synthetic():
    """Verify subgroup calculation across heterogeneous radio groups."""
    y_true = np.array([10.0, 20.0, 30.0, 40.0])
    y_pred = np.array([12.0, 22.0, 28.0, 38.0])
    bounds = np.array([8.0, 18.0, 25.0, 35.0])
    groups = np.array([0, 0, 2, 3])
    
    sg = compute_subgroup_metrics(y_true, y_pred, bounds, groups)
    assert 0 in sg
    assert 2 in sg
    assert 3 in sg
    assert sg[0].sample_count == 2
    assert sg[2].sample_count == 1
    assert sg[3].sample_count == 1

@pytest.mark.unit
def test_paired_day_cluster_bootstrap_synthetic():
    """Verify paired cluster bootstrap produces finite point estimates and confidence intervals."""
    test_df = pd.DataFrame({
        'date': ['2026-01-01'] * 10 + ['2026-01-02'] * 10 + ['2026-01-03'] * 10,
        'y': np.random.uniform(20, 80, 30)
    })
    y_true = test_df['y'].to_numpy()
    bounds_baseline = y_true - 5.0
    bounds_proposed = y_true - 2.0
    
    boot = paired_day_cluster_bootstrap(
        test_df, y_true, bounds_baseline, bounds_proposed, n_boot=200, random_seed=42
    )
    assert 'delta_violation_rate' in boot
    assert 'delta_supported_fraction' in boot
    assert len(boot['delta_violation_rate']) == 3
    assert boot['delta_violation_rate'][1] <= boot['delta_violation_rate'][2]

