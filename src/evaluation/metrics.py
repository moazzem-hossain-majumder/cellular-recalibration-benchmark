"""Evaluation metrics and clustered bootstrap uncertainty estimation."""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

@dataclass
class ReliabilityMetrics:
    violation_rate: float
    supported_rate_fraction: float
    mean_lower_bound: float
    zero_bound_fraction: float
    mean_overcommitment: float
    mae: float
    rmse: float
    sample_count: int

def compute_reliability_metrics(y_true: np.ndarray, y_pred: np.ndarray, lower_bounds: np.ndarray) -> ReliabilityMetrics:
    """Compute core telecommunications reliability and usefulness metrics."""
    n = len(y_true)
    if n == 0:
        return ReliabilityMetrics(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0)
        
    violations = (y_true < lower_bounds).astype(float)
    violation_rate = float(np.mean(violations))
    
    sum_y = np.sum(y_true)
    supported_y = np.sum(np.minimum(lower_bounds, y_true))
    supported_rate_fraction = float(supported_y / sum_y) if sum_y > 0 else 0.0
    
    mean_lower_bound = float(np.mean(lower_bounds))
    zero_bound_fraction = float(np.mean(lower_bounds <= 1e-6))
    
    overcommitment = np.maximum(0.0, lower_bounds - y_true)
    mean_overcommitment = float(np.mean(overcommitment))
    
    mae = float(np.mean(np.abs(y_pred - y_true)))
    rmse = float(np.sqrt(np.mean((y_pred - y_true) ** 2)))
    
    return ReliabilityMetrics(
        violation_rate=violation_rate,
        supported_rate_fraction=supported_rate_fraction,
        mean_lower_bound=mean_lower_bound,
        zero_bound_fraction=zero_bound_fraction,
        mean_overcommitment=mean_overcommitment,
        mae=mae,
        rmse=rmse,
        sample_count=n
    )

def compute_subgroup_metrics(y_true: np.ndarray, y_pred: np.ndarray, lower_bounds: np.ndarray,
                             group_ids: np.ndarray) -> Dict[int, ReliabilityMetrics]:
    """Compute metrics stratified by radio missingness availability groups."""
    subgroups = {}
    for g in np.unique(group_ids):
        mask = (group_ids == g)
        subgroups[int(g)] = compute_reliability_metrics(
            y_true[mask], y_pred[mask], lower_bounds[mask]
        )
    return subgroups

def paired_day_cluster_bootstrap(df_test: pd.DataFrame, y_true: np.ndarray,
                                 bounds_a: np.ndarray, bounds_b: np.ndarray,
                                 n_boot: int = 2000, random_seed: int = 42) -> Dict[str, Tuple[float, float, float]]:
    """Paired day-level cluster bootstrap for differences (Method B - Method A).
    
    Returns:
        Dict mapping metric name to (point_estimate, ci_lower_95, ci_upper_95)
    """
    rng = np.random.default_rng(random_seed)
    # Group indices by collection date
    dates = df_test['date'].unique()
    date_indices = {d: df_test[df_test['date'] == d].index.to_numpy() for d in dates}
    n_dates = len(dates)
    
    diff_v_boot = np.empty(n_boot)
    diff_u_boot = np.empty(n_boot)
    
    # Point estimates
    m_a = compute_reliability_metrics(y_true, y_true, bounds_a)
    m_b = compute_reliability_metrics(y_true, y_true, bounds_b)
    pt_diff_v = m_b.violation_rate - m_a.violation_rate
    pt_diff_u = m_b.supported_rate_fraction - m_a.supported_rate_fraction
    
    for b in range(n_boot):
        sample_dates = rng.choice(dates, size=n_dates, replace=True)
        sample_idx = np.concatenate([date_indices[d] for d in sample_dates])
        
        y_b = y_true[sample_idx]
        ba_b = bounds_a[sample_idx]
        bb_b = bounds_b[sample_idx]
        
        res_a = compute_reliability_metrics(y_b, y_b, ba_b)
        res_b = compute_reliability_metrics(y_b, y_b, bb_b)
        
        diff_v_boot[b] = res_b.violation_rate - res_a.violation_rate
        diff_u_boot[b] = res_b.supported_rate_fraction - res_a.supported_rate_fraction
        
    ci_v = (pt_diff_v, float(np.percentile(diff_v_boot, 2.5)), float(np.percentile(diff_v_boot, 97.5)))
    ci_u = (pt_diff_u, float(np.percentile(diff_u_boot, 2.5)), float(np.percentile(diff_u_boot, 97.5)))
    
    return {'delta_violation_rate': ci_v, 'delta_supported_fraction': ci_u}

