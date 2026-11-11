"""Synthetic unit tests for conformal prediction mathematics and calibrators."""
import pytest
import numpy as np
import pandas as pd
from src.evaluation.conformal import (
    compute_conformal_quantile,
    GlobalConformalCalibrator,
    GroupedConformalCalibrator,
    CovariateShiftConformalCalibrator,
    AdaptiveConformalCalibrator
)

@pytest.mark.unit
def test_conformal_quantile_formula():
    """Verify finite-sample conformal quantile: ceil((n+1)(1-alpha))/n."""
    scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    q = compute_conformal_quantile(scores, alpha=0.10)
    assert q == 9.0
    
    assert np.isinf(compute_conformal_quantile(np.array([]), alpha=0.10))
    assert np.isinf(compute_conformal_quantile(np.array([5.0]), alpha=0.10))

@pytest.mark.unit
def test_lemma1_exact_threshold():
    """Verify split conformal at alpha=0.10 requires n>=9 for finite quantile."""
    scores_8 = np.arange(1.0, 9.0)
    assert np.isinf(compute_conformal_quantile(scores_8, alpha=0.10)), "n=8 must return inf"
    
    scores_9 = np.arange(1.0, 10.0)
    assert not np.isinf(compute_conformal_quantile(scores_9, alpha=0.10)), "n=9 must return finite quantile"
    assert compute_conformal_quantile(scores_9, alpha=0.10) == 9.0

@pytest.mark.unit
def test_global_calibrator():
    """Verify GlobalConformalCalibrator lower bounds are valid and bounded."""
    calib = GlobalConformalCalibrator(alpha=0.10)
    np.random.seed(42)
    y_pred = np.linspace(20, 100, 50)
    y_true = y_pred - np.random.uniform(0, 10, 50)
    calib.fit(y_pred, y_true)
    
    test_pred = np.array([30.0, 50.0, 70.0])
    bounds, insufficient = calib.predict_lower_bound(test_pred)
    assert not insufficient.any()
    assert (bounds <= test_pred).all()
    assert (bounds >= 0.0).all()

@pytest.mark.unit
def test_grouped_fallback_hierarchy():
    """Verify GroupedConformalCalibrator cascades gracefully on small group support."""
    calib = GroupedConformalCalibrator(alpha=0.10, min_rows=10, min_sessions=2, fallback_source_q=5.0)
    
    y_pred = np.ones(20) * 50.0
    y_true = np.ones(20) * 45.0
    groups = np.array([2] * 15 + [3] * 5)
    sessions = np.array([1, 2] * 10)
    
    calib.fit(y_pred, y_true, groups, sessions)
    
    test_preds = np.array([50.0, 50.0, 50.0])
    test_groups = np.array([2, 3, 0])
    bounds, insuff = calib.predict_lower_bound(test_preds, test_groups)
    
    assert len(bounds) == 3
    assert (bounds >= 0.0).all()

@pytest.mark.unit
def test_covariate_shift_conformal():
    """Verify CovariateShiftConformalCalibrator prior ratio and clipping behavior."""
    np.random.seed(42)
    calib = CovariateShiftConformalCalibrator(alpha=0.10)
    
    X_src = pd.DataFrame({'f1': np.random.normal(0, 1, 40), 'f2': np.random.normal(0, 1, 40)})
    scores_src = np.random.uniform(5, 15, 40)
    X_tgt = pd.DataFrame({'f1': np.random.normal(2, 1, 30), 'f2': np.random.normal(2, 1, 30)})
    
    calib.fit_weights_and_scores(X_src, scores_src, X_tgt, feature_cols=['f1', 'f2'])
    
    expected_prior = 40.0 / 30.0
    assert abs(calib.prior_ratio - expected_prior) < 1e-5
    
    test_pred = np.array([40.0, 60.0])
    X_test = pd.DataFrame({'f1': [1.5, 2.5], 'f2': [1.5, 2.5]})
    bounds = calib.predict_lower_bound(test_pred, X_test)
    assert len(bounds) == 2
    assert (bounds >= 0.0).all()
    assert (bounds <= test_pred).all()

@pytest.mark.unit
def test_aci_calibrator_step():
    """Verify AdaptiveConformalCalibrator updates margin monotonically with error."""
    aci = AdaptiveConformalCalibrator(alpha=0.10, gamma=0.05, init_q=10.0)
    init_margin = aci.q
    
    # Violation step (true < predicted - q) -> margin should increase
    b1, v1 = aci.step(y_pred_t=50.0, y_true_t=35.0)  # error = 15 > 10 -> violation (v=1)
    assert v1 == 1
    assert aci.q > init_margin, "Margin must increase following violation"
    
    # Non-violation step (true >= predicted - q) -> margin should decrease slightly
    prev_q = aci.q
    b2, v2 = aci.step(y_pred_t=50.0, y_true_t=55.0)  # error = -5 <= q -> non-violation (v=0)
    assert v2 == 0
    assert aci.q < prev_q, "Margin must decrease following successful coverage"
