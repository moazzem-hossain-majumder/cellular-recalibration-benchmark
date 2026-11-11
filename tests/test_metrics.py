"""Unit tests for telecommunications evaluation metrics and edge cases."""
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import compute_reliability_metrics

def test_metrics_edge_cases():
    # 1. Perfect bounds (bounds equal true throughput)
    y_true = np.array([10.0, 20.0, 30.0])
    bounds = np.array([10.0, 20.0, 30.0])
    m = compute_reliability_metrics(y_true, y_true, bounds)
    assert m.violation_rate == 0.0
    assert m.supported_rate_fraction == 1.0
    assert m.mean_overcommitment == 0.0
    
    # 2. Complete violation (bounds strictly greater than true)
    bounds_high = np.array([15.0, 25.0, 35.0])
    m_high = compute_reliability_metrics(y_true, y_true, bounds_high)
    assert m_high.violation_rate == 1.0
    assert m_high.mean_overcommitment == 5.0
    
    # 3. All-zero policy (L=0)
    bounds_zero = np.zeros(3)
    m_zero = compute_reliability_metrics(y_true, y_true, bounds_zero)
    assert m_zero.violation_rate == 0.0
    assert m_zero.supported_rate_fraction == 0.0
    assert m_zero.zero_bound_fraction == 1.0
    
    # 4. Measured zero throughput in ground truth
    y_with_zero = np.array([0.0, 10.0, 20.0])
    bounds_test = np.array([0.0, 5.0, 10.0])
    m_w_zero = compute_reliability_metrics(y_with_zero, y_with_zero, bounds_test)
    assert m_w_zero.violation_rate == 0.0
    assert m_w_zero.supported_rate_fraction == (0.0 + 5.0 + 10.0) / (0.0 + 10.0 + 20.0)

if __name__ == '__main__':
    test_metrics_edge_cases()
    print('Metrics integrity tests PASSED.')

