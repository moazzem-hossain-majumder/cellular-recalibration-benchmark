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
                             budgets: List[int] = [0, 1, 2, 5, 8, 9, 10, 15]) -> DomainSplits:
    """Create strictly disjoint source train/val/calib and target calibration pool / test suffix splits.
    
    For within-domain evaluation (source == target):
        Single 4-way chronological day partition (45% train, 15% dev, 15% calib pool, 25% test suffix).
        Guarantees 0% leakage: train, val, calib, and test dates and sessions are 100% disjoint.
        
    For transfer regimes (source != target):
        Source domain: earliest 60% days for train, next 20% for dev, final 20% for source calib.
        Target domain: earliest 40% days for calibration pool, remaining 60% days for fixed test suffix.
    """
    # Detect whether this is a within-domain experiment (overlapping session pool)
    has_sid_src = 'session_id' in source_df.columns
    has_sid_tgt = 'session_id' in target_df.columns
    if has_sid_src and has_sid_tgt:
        overlap_sessions = set(source_df['session_id']).intersection(set(target_df['session_id']))
        is_within_domain = len(overlap_sessions) > 0
    else:
        is_within_domain = (source_df is target_df or len(source_df) == len(target_df))
        overlap_sessions = set()
    
    if is_within_domain:
        # Strictly disjoint 4-way chronological split of the single domain
        # 45% train, 15% val, 15% calib pool, 25% test
        e0_splits = partition_by_chronological_days(source_df, (0.45, 0.15, 0.15, 0.25))
        train_df = e0_splits[0]
        val_df = e0_splits[1]
        calib_pool_df = e0_splits[2]
        source_calib_df = calib_pool_df.copy()  # In within-domain, source calib is the calib pool
        test_df = e0_splits[3]
    else:
        # Transfer regime: source and target are already distinct domains
        if has_sid_src and has_sid_tgt:
            assert len(overlap_sessions) == 0, "Source and target unexpectedly share session IDs in transfer regime!"
        # Source partitions (60 / 20 / 20)
        source_splits = partition_by_chronological_days(source_df, (0.60, 0.20, 0.20))
        train_df, val_df, source_calib_df = source_splits[0], source_splits[1], source_splits[2]
        
        # Target partitions (40 / 60)
        target_splits = partition_by_chronological_days(target_df, (0.40, 0.60))
        calib_pool_df, test_df = target_splits[0], target_splits[1]

    # Verify strict disjointness assertions
    if 'session_id' in train_df.columns and 'session_id' in test_df.columns:
        assert set(train_df['session_id']).isdisjoint(set(test_df['session_id'])), "FATAL LEAKAGE: Train and Test overlap!"
        assert set(val_df['session_id']).isdisjoint(set(test_df['session_id'])), "FATAL LEAKAGE: Val and Test overlap!"
        assert set(calib_pool_df['session_id']).isdisjoint(set(test_df['session_id'])), "FATAL LEAKAGE: Calib Pool and Test overlap!"
        assert set(source_calib_df['session_id']).isdisjoint(set(test_df['session_id'])), "FATAL LEAKAGE: Source Calib and Test overlap!"
    
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

