"""Unit tests for conformal prediction math and fallback behavior."""
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.conformal import (
    compute_conformal_quantile,
    GlobalConformalCalibrator,
    GroupedConformalCalibrator,
    CovariateShiftConformalCalibrator
)

def test_conformal_quantile_formula():
    # Synthetic scores: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0] (n=9)
    # For alpha=0.10: k = ceil(10 * 0.9) = 9. So q = 9.0.
    scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    q = compute_conformal_quantile(scores, alpha=0.10)
    assert q == 9.0
    
    # Empty scores: returns infinity
    assert np.isinf(compute_conformal_quantile(np.array([]), alpha=0.10))
    
    # n=1, alpha=0.10: k = ceil(2 * 0.9) = 2 > n, returns infinity
    assert np.isinf(compute_conformal_quantile(np.array([5.0]), alpha=0.10))

def test_global_calibrator():
    calib = GlobalConformalCalibrator(alpha=0.10)
    # y_pred = 50.0, y_true = 40.0 -> score = 10.0
    y_pred = np.linspace(20, 100, 50)
    y_true = y_pred - np.random.uniform(0, 10, 50)  # overprediction
    calib.fit(y_pred, y_true)
    
    test_pred = np.array([30.0, 50.0, 70.0])
    bounds, insufficient = calib.predict_lower_bound(test_pred)
    assert not insufficient.any()
    assert (bounds <= test_pred).all()
    assert (bounds >= 0.0).all()

def test_grouped_fallback_hierarchy():
    # Only group 2 has enough support (min_rows=10, min_sessions=2)
    calib = GroupedConformalCalibrator(alpha=0.10, min_rows=10, min_sessions=2, fallback_source_q=5.0)
    
    y_pred = np.ones(20) * 50.0
    y_true = np.ones(20) * 45.0  # score = 5.0
    groups = np.array([2] * 15 + [3] * 5)
    sessions = np.array([1, 2] * 10)
    
    calib.fit(y_pred, y_true, groups, sessions)
    
    # Query group 2 (supported) and group 3 (insufficient -> pooled fallback) and unknown group 0 (fallback)
    test_preds = np.array([50.0, 50.0, 50.0])
    test_groups = np.array([2, 3, 0])
    bounds, insuff = calib.predict_lower_bound(test_preds, test_groups)
    
    assert len(bounds) == 3
    assert (bounds >= 0.0).all()

def test_covariate_shift_conformal():
    import pandas as pd
    calib = CovariateShiftConformalCalibrator(alpha=0.10)
    
    # Source: 40 samples, feature centered at 0.0
    X_src = pd.DataFrame({'f1': np.random.normal(0, 1, 40), 'f2': np.random.normal(0, 1, 40)})
    scores_src = np.random.uniform(5, 15, 40)
    
    # Target: 30 samples, feature shifted to 2.0
    X_tgt = pd.DataFrame({'f1': np.random.normal(2, 1, 30), 'f2': np.random.normal(2, 1, 30)})
    
    calib.fit_weights_and_scores(X_src, scores_src, X_tgt, feature_cols=['f1', 'f2'])
    
    test_pred = np.array([40.0, 60.0])
    X_test = pd.DataFrame({'f1': [1.5, 2.5], 'f2': [1.5, 2.5]})
    bounds = calib.predict_lower_bound(test_pred, X_test)
    
    assert len(bounds) == 2
    assert (bounds >= 0.0).all()
    assert (bounds <= test_pred).all()

if __name__ == '__main__':
    test_conformal_quantile_formula()
    test_global_calibrator()
    test_grouped_fallback_hierarchy()
    test_covariate_shift_conformal()
    print('All conformal unit tests PASSED.')

