"""Conformal prediction and calibration rules for one-sided cellular throughput lower bounds."""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

def compute_conformal_quantile(scores: np.ndarray, alpha: float = 0.10) -> float:
    """Compute (1 - alpha) conformal quantile of signed overprediction scores."""
    n = len(scores)
    if n == 0:
        return float('inf')
    k = int(np.ceil((n + 1) * (1.0 - alpha)))
    if k > n:
        return float('inf')
    sorted_scores = np.sort(scores)
    return float(sorted_scores[k - 1])

class GlobalConformalCalibrator:
    """Standard global split-conformal calibrator using signed overprediction scores."""
    def __init__(self, alpha: float = 0.10):
        self.alpha = alpha
        self.q = float('inf')
        self.n_calib = 0
        
    def fit(self, y_pred: np.ndarray, y_true: np.ndarray):
        scores = y_pred - y_true
        self.n_calib = len(scores)
        self.q = compute_conformal_quantile(scores, self.alpha)
        return self
        
    def predict_lower_bound(self, y_pred: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (lower_bounds, insufficient_support_flags)."""
        if np.isinf(self.q):
            return np.zeros_like(y_pred), np.ones_like(y_pred, dtype=bool)
        bounds = np.maximum(0.0, y_pred - self.q)
        return bounds, np.zeros_like(y_pred, dtype=bool)

class GroupedConformalCalibrator:
    """Grouped conformal calibrator with support threshold and 3-tier fallback hierarchy (Algorithm 1).
    
    Fallback Hierarchy:
      Tier 1: Subgroup Target Quantile (activated when |D_cal,g^tgt| >= min_rows and >= min_sessions)
      Tier 2: Pooled Target Quantile (activated when pooled |D_cal^tgt| >= ceil((1-alpha)/alpha) = 9)
      Tier 3: Source Domain Conservative Fallback (used when target budget K < 9)
    """
    def __init__(self, alpha: float = 0.10, min_rows: int = 10, min_sessions: int = 2,
                 fallback_source_q: Optional[float] = None):
        self.alpha = alpha
        self.min_rows = min_rows
        self.min_sessions = min_sessions
        self.fallback_source_q = fallback_source_q if fallback_source_q is not None else float('inf')
        self.group_quantiles: Dict[int, float] = {}
        self.pooled_q = float('inf')
        self.group_counts: Dict[int, int] = {}

    def fit(self, y_pred: np.ndarray, y_true: np.ndarray,
            group_ids: np.ndarray, session_ids: Optional[np.ndarray] = None):
        scores = y_pred - y_true
        self.pooled_q = compute_conformal_quantile(scores, self.alpha)
        
        unique_groups = np.unique(group_ids)
        for g in unique_groups:
            mask = (group_ids == g)
            g_scores = scores[mask]
            g_rows = len(g_scores)
            self.group_counts[int(g)] = g_rows
            
            # Check session count if available
            g_sessions = len(np.unique(session_ids[mask])) if session_ids is not None else g_rows
            
            if g_rows >= self.min_rows and g_sessions >= self.min_sessions:
                self.group_quantiles[int(g)] = compute_conformal_quantile(g_scores, self.alpha)
            else:
                # Fallback to pooled target quantile
                self.group_quantiles[int(g)] = self.pooled_q
                
        return self

    def predict_lower_bound(self, y_pred: np.ndarray, group_ids: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        lower_bounds = np.zeros_like(y_pred)
        insufficient_support = np.zeros_like(y_pred, dtype=bool)
        
        for i in range(len(y_pred)):
            g = int(group_ids[i])
            # Hierarchy: group quantile -> pooled target quantile -> source fallback
            q = self.group_quantiles.get(g, self.pooled_q)
            if np.isinf(q):
                q = self.fallback_source_q
                
            if np.isinf(q):
                lower_bounds[i] = 0.0
                insufficient_support[i] = True
            else:
                lower_bounds[i] = max(0.0, y_pred[i] - q)
                
        return lower_bounds, insufficient_support

class AdaptiveConformalCalibrator:
    """Adaptive Conformal Inference (Gibbs & Candès 2021) for online tracking."""
    def __init__(self, alpha: float = 0.10, gamma: float = 0.05, init_q: float = 0.0):
        self.alpha = alpha
        self.gamma = gamma
        self.q = init_q
        self.history: List[float] = []
        
    def step(self, y_pred_t: float, y_true_t: float) -> Tuple[float, bool]:
        """Predict lower bound at t, then update q based on observed label."""
        bound = max(0.0, y_pred_t - self.q)
        violated = bool(y_true_t < bound)
        # Gradient update on coverage error: err_t = 1 if violated else 0
        err_t = 1.0 if violated else 0.0
        self.q += self.gamma * (err_t - self.alpha)
        self.history.append(self.q)
        return bound, violated

class CovariateShiftConformalCalibrator:
    """Covariate-Shift Conformal Prediction (Tibshirani et al., NeurIPS 2019).
    
    Weights source calibration scores using likelihood ratio weights w(x) = dP_tgt(x) / dP_src(x),
    estimated via a logistic domain discriminator trained on source vs target features.
    """
    def __init__(self, alpha: float = 0.10, clip_weight_max: float = 10.0, clip_weight_min: float = 0.1):
        self.alpha = alpha
        self.clip_weight_max = clip_weight_max
        self.clip_weight_min = clip_weight_min
        self.source_scores: np.ndarray = np.array([])
        self.source_weights: np.ndarray = np.array([])
        self.discriminator = None
        self.feature_cols: List[str] = []

    def fit_weights_and_scores(self, X_source_calib: pd.DataFrame, scores_source: np.ndarray,
                               X_target_ref: pd.DataFrame, feature_cols: List[str]):
        """Fit domain discriminator between source and target, and store weighted source scores."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        
        self.feature_cols = feature_cols
        self.source_scores = np.asarray(scores_source, dtype=float)
        
        # Prepare feature matrices with zero imputation and scaling
        X_src = X_source_calib[self.feature_cols].fillna(0.0).to_numpy(dtype=float)
        X_tgt = X_target_ref[self.feature_cols].fillna(0.0).to_numpy(dtype=float)
        
        scaler = StandardScaler()
        X_comb = np.vstack([X_src, X_tgt])
        X_comb_scaled = scaler.fit_transform(X_comb)
        self.scaler = scaler
        
        y_comb = np.concatenate([np.zeros(len(X_src)), np.ones(len(X_tgt))])
        
        # Logistic discriminator
        self.discriminator = LogisticRegression(C=0.5, max_iter=500, random_state=42)
        self.discriminator.fit(X_comb_scaled, y_comb)
        
        # Bayes class-prior correction: w(x) = [P(Tgt|x)/P(Src|x)] * [P(Src)/P(Tgt)] = odds * (N_src / N_tgt)
        self.prior_ratio = float(len(X_src)) / float(max(1, len(X_tgt)))
        
        X_src_scaled = scaler.transform(X_src)
        probs_src = self.discriminator.predict_proba(X_src_scaled)[:, 1]
        probs_src = np.clip(probs_src, 1e-4, 1.0 - 1e-4)
        raw_weights_src = (probs_src / (1.0 - probs_src)) * self.prior_ratio
        self.source_weights = np.clip(raw_weights_src, self.clip_weight_min, self.clip_weight_max)
        return self

    def predict_lower_bound(self, y_pred_test: np.ndarray, X_test: pd.DataFrame) -> np.ndarray:
        """Compute point-wise weighted conformal lower bounds for test instances."""
        if self.discriminator is None or len(self.source_scores) == 0:
            return np.maximum(0.0, y_pred_test)
            
        X_te = X_test[self.feature_cols].fillna(0.0).to_numpy(dtype=float)
        X_te_scaled = self.scaler.transform(X_te)
        probs_te = self.discriminator.predict_proba(X_te_scaled)[:, 1]
        probs_te = np.clip(probs_te, 1e-4, 1.0 - 1e-4)
        prior_ratio = getattr(self, 'prior_ratio', 1.0)
        raw_weights_te = (probs_te / (1.0 - probs_te)) * prior_ratio
        weights_te = np.clip(raw_weights_te, self.clip_weight_min, self.clip_weight_max)
        
        n_src = len(self.source_scores)
        lower_bounds = np.zeros(len(y_pred_test), dtype=float)
        
        # Sort source scores
        sort_idx = np.argsort(self.source_scores)
        sorted_scores = self.source_scores[sort_idx]
        sorted_src_weights = self.source_weights[sort_idx]
        
        for i in range(len(y_pred_test)):
            w_te = weights_te[i]
            denom = np.sum(sorted_src_weights) + w_te
            p_src = sorted_src_weights / denom
            
            # Cumulative probability function of sorted scores
            cum_p = np.cumsum(p_src)
            valid_idx = np.where(cum_p >= (1.0 - self.alpha))[0]
            if len(valid_idx) > 0:
                q_weighted = sorted_scores[valid_idx[0]]
            else:
                q_weighted = sorted_scores[-1]
                
            lower_bounds[i] = max(0.0, y_pred_test[i] - q_weighted)
            
        return lower_bounds


