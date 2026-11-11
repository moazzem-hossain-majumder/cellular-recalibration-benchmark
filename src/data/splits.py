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
    target_prefix_sessions: Dict[int, object]  # K -> dataframe, or None when K sessions are unsupported

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
    previous_cut = 0
    for i, frac in enumerate(fractions[:-1]):
        cum += frac
        # Keep every partition non-empty when there are enough collection days;
        # Python's round-to-even can otherwise create duplicate cut points.
        remaining_partitions = len(fractions) - i - 1
        proposed = int(round(cum * n_dates))
        idx = max(previous_cut + 1, proposed)
        idx = min(idx, n_dates - remaining_partitions)
        cutoffs.append(idx)
        previous_cut = idx
        
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
    """Create chronological source-development, source-calibration, target-calibration,
    and fixed-test partitions without reusing calibration labels.

    E0 within-domain uses five disjoint chronological blocks (35/10/15/15/25
    percent of days): train, validation, source calibration, target calibration
    pool, and fixed test suffix. The source-calibration block is never reused
    as target calibration data.

    Transfer regimes use source 60/20/20 and target 40/60 chronological blocks.
    """

    # Detect E0 by shared dataframe identity, not by session_id overlap:
    # IDs can restart at zero in independently loaded campaigns.
    is_within_domain = source_df is target_df
    
    if is_within_domain:
        # Five disjoint chronological blocks are necessary here: the frozen
        # source quantile must not use labels later exposed as target calibration
        # prefixes. The fixed test suffix remains the final 25% of collection days.
        e0_splits = partition_by_chronological_days(
            source_df, (0.35, 0.10, 0.15, 0.15, 0.25)
        )
        train_df = e0_splits[0]
        val_df = e0_splits[1]
        source_calib_df = e0_splits[2]
        calib_pool_df = e0_splits[3]
        test_df = e0_splits[4]
    else:
        # Transfer regime: source and target are distinct domains. Their local
        # session IDs and dates may legitimately collide across datasets.
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
        assert set(source_calib_df['session_id']).isdisjoint(set(calib_pool_df['session_id'])), "FATAL LEAKAGE: Source and target calibration overlap!"
    
    # The source calibration labels and target calibration pool must be disjoint
    # in every regime; assert this explicitly before producing any prefixes.
    if 'session_id' in source_calib_df.columns and 'session_id' in calib_pool_df.columns:
        assert set(source_calib_df['session_id']).isdisjoint(
            set(calib_pool_df['session_id'])
        ), "FATAL LEAKAGE: Source and target calibration overlap!"

    # Sort calibration pool chronologically
    calib_pool_sorted = calib_pool_df.sort_values('t_start').reset_index(drop=True)
    
    # Extract K sessions for budgets
    target_prefixes = {}
    for k in budgets:
        if k == 0:
            target_prefixes[0] = calib_pool_sorted.iloc[:0].copy()
        elif 'session_id' in calib_pool_sorted.columns and calib_pool_sorted['session_id'].nunique() < k:
            # Never silently report a smaller prefix as if it were budget K.
            target_prefixes[k] = None
        elif len(calib_pool_sorted) < k:
            target_prefixes[k] = None
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

