"""Chronological and domain splitting protocol conforming to the approved research proposal."""
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

@dataclass
class DomainSplits:
    train: pd.DataFrame
    val: pd.DataFrame
    source_calib: pd.DataFrame
    target_calib_pool: pd.DataFrame
    target_test: pd.DataFrame
    target_prefix_sessions: Dict[int, pd.DataFrame]  # K -> df for K in [0, 1, 2, 5, 10]

def partition_by_chronological_days(df: pd.DataFrame, fractions: Tuple[float, ...]) -> List[pd.DataFrame]:
    """Partition a dataframe into non-overlapping chronological blocks by collection date."""
    assert abs(sum(fractions) - 1.0) < 1e-5
    # Sort distinct dates chronologically
    df_temp = df.copy()
    # Ensure datetime for sorting
    if not np.issubdtype(df_temp['t_start'].dtype, np.datetime64):
        df_temp['t_start'] = pd.to_datetime(df_temp['t_start'])
        
    date_order = df_temp.groupby('date')['t_start'].min().sort_values().index.tolist()
    n_dates = len(date_order)
    
    # Calculate cutoff indices
    cutoffs = []
    cum = 0.0
    for frac in fractions[:-1]:
        cum += frac
        idx = max(1, int(round(cum * n_dates)))
        cutoffs.append(idx)
        
    splits = []
    start_idx = 0
    for cut in cutoffs:
        d_block = date_order[start_idx:cut]
        splits.append(df[df['date'].isin(d_block)].copy())
        start_idx = cut
    splits.append(df[df['date'].isin(date_order[start_idx:])].copy())
    return splits

def create_experiment_splits(source_df: pd.DataFrame, target_df: pd.DataFrame,
                             budgets: List[int] = [0, 1, 2, 5, 10]) -> DomainSplits:
    """Create source train/val/calib and target calibration pool / test suffix splits.
    
    Source: earliest 60% of days for fitting, next 20% for dev, final 20% for source calib.
    Target: earliest 40% of days for calibration pool, remaining 60% for fixed test suffix.
    """
    # 1. Source partitions (60 / 20 / 20)
    source_splits = partition_by_chronological_days(source_df, (0.60, 0.20, 0.20))
    train_df, val_df, source_calib_df = source_splits[0], source_splits[1], source_splits[2]
    
    # 2. Target partitions (40 / 60)
    target_splits = partition_by_chronological_days(target_df, (0.40, 0.60))
    calib_pool_df, test_df = target_splits[0], target_splits[1]
    
    # Sort calibration pool chronologically
    calib_pool_sorted = calib_pool_df.sort_values('t_start').reset_index(drop=True)
    
    # Extract K sessions for budgets
    target_prefixes = {}
    for k in budgets:
        if k == 0:
            target_prefixes[0] = calib_pool_sorted.iloc[:0].copy()
        else:
            target_prefixes[k] = calib_pool_sorted.iloc[:k].copy()
            
    return DomainSplits(
        train=train_df.reset_index(drop=True),
        val=val_df.reset_index(drop=True),
        source_calib=source_calib_df.reset_index(drop=True),
        target_calib_pool=calib_pool_df.reset_index(drop=True),
        target_test=test_df.reset_index(drop=True),
        target_prefix_sessions=target_prefixes
    )

