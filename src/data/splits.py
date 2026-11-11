"""Chronological and domain splitting protocol conforming to the approved research proposal."""
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path
import numpy as np
import pandas as pd

@dataclass
class DomainSplits:
    train: pd.DataFrame
    val: pd.DataFrame
    source_calib: pd.DataFrame
    target_calib_pool: pd.DataFrame
    target_test: pd.DataFrame
    target_prefix_sessions: Dict[int, Optional[pd.DataFrame]]  # K -> dataframe, or None when K sessions are unsupported

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
    if n_dates < len(fractions):
        raise ValueError(
            f"Cannot create {len(fractions)} non-empty chronological partitions "
            f"from only {n_dates} collection dates."
        )

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

def create_experiment_splits(source_df: pd.DataFrame,
                             target_df: pd.DataFrame,
                             budgets: Optional[List[int]] = None,
                             is_within_domain: Optional[bool] = None,
                             regime: Optional[str] = None,
                             experiment_type: Optional[str] = None) -> DomainSplits:
    """Create chronological source-development, source-calibration, target-calibration,
    and fixed-test partitions without reusing calibration labels.

    Args:
        source_df: Source domain measurement instances.
        target_df: Target domain measurement instances.
        budgets: Target calibration budgets K to extract. Defaults to [0, 1, 2, 5, 8, 9, 10, 15].
        is_within_domain: Optional explicit boolean flag. If provided, overrides implicit detection.
        regime: Optional experiment regime name (e.g. 'E0_WithinDomain_Op1_2021').
        experiment_type: Optional explicit regime category: 'within_domain' or 'transfer'.

    E0 within-domain uses five disjoint chronological blocks (35/10/15/15/25
    percent of days): train, validation, source calibration, target calibration
    pool, and fixed test suffix. The source-calibration block is never reused
    as target calibration data.

    Transfer regimes use source 60/20/20 and target 40/60 chronological blocks.
    """
    if budgets is None:
        budgets = [0, 1, 2, 5, 8, 9, 10, 15]

    if experiment_type is not None:
        within_domain = (experiment_type.strip().lower() in ("within_domain", "e0", "within"))
    elif is_within_domain is not None:
        within_domain = bool(is_within_domain)
    elif regime is not None:
        within_domain = regime.startswith('E0') or 'within' in regime.lower()
    else:
        # Detect E0 by shared dataframe identity or exact session/date set match
        if source_df is target_df:
            within_domain = True
        elif ('session_id' in source_df.columns and 'session_id' in target_df.columns and
              'date' in source_df.columns and 'date' in target_df.columns):
            within_domain = (
                len(source_df) == len(target_df) and
                set(source_df['session_id']) == set(target_df['session_id']) and
                set(source_df['date']) == set(target_df['date'])
            )
        else:
            within_domain = False
    
    if within_domain:
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

    # Verify disjointness only within a domain. Numeric IDs and dates from
    # separate datasets are not globally unique and must not be compared across
    # domains. Within E0, every partition must be pairwise disjoint.
    if 'session_id' in train_df.columns and 'session_id' in val_df.columns:
        assert set(train_df['session_id']).isdisjoint(set(val_df['session_id'])), "FATAL LEAKAGE: Source train and validation overlap!"
        assert set(train_df['session_id']).isdisjoint(set(source_calib_df['session_id'])), "FATAL LEAKAGE: Source train and source calibration overlap!"
        assert set(val_df['session_id']).isdisjoint(set(source_calib_df['session_id'])), "FATAL LEAKAGE: Source validation and calibration overlap!"
        assert set(calib_pool_df['session_id']).isdisjoint(set(test_df['session_id'])), "FATAL LEAKAGE: Target calibration pool and test overlap!"
        if within_domain:
            source_ids = set(source_df['session_id'])
            target_ids = set(target_df['session_id'])
            assert source_ids == target_ids, "E0 should use the same underlying session set for source and target."
            parts = [train_df, val_df, source_calib_df, calib_pool_df, test_df]
            for i, left in enumerate(parts):
                for right in parts[i + 1:]:
                    assert set(left['session_id']).isdisjoint(set(right['session_id'])), "FATAL LEAKAGE: E0 partitions overlap!"
                    assert set(left['date']).isdisjoint(set(right['date'])), "FATAL LEAKAGE: E0 dates overlap!"

    # Sort calibration pool chronologically
    calib_pool_sorted = calib_pool_df.sort_values('t_start').reset_index(drop=True)
    
    # Extract K sessions for budgets
    target_prefixes = {}
    for k in budgets:
        if k == 0:
            target_prefixes[0] = calib_pool_sorted.iloc[:0].copy()
        elif 'session_id' in calib_pool_sorted.columns:
            unique_sessions = calib_pool_sorted['session_id'].unique()
            if len(unique_sessions) < k:
                # Never silently report a smaller prefix as if it were budget K.
                target_prefixes[k] = None
            else:
                selected_sessions = unique_sessions[:k]
                target_prefixes[k] = calib_pool_sorted[calib_pool_sorted['session_id'].isin(selected_sessions)].copy()
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


def generate_split_summary(splits: DomainSplits,
                           experiment_name: str,
                           dataset_id: str,
                           output_path: Optional[Path] = None) -> Dict:
    """Generate detailed split audit metadata and save to JSON.
    
    Tracks exact sample counts, session counts, dates, and budget availability
    for experimental integrity reporting.
    """
    def _summarize_df(df: pd.DataFrame) -> Dict:
        if df is None or len(df) == 0:
            return {"n_samples": 0, "n_sessions": 0, "n_days": 0, "dates": []}
        return {
            "n_samples": int(len(df)),
            "n_sessions": int(df['session_id'].nunique()) if 'session_id' in df.columns else int(len(df)),
            "n_days": int(df['date'].nunique()) if 'date' in df.columns else 0,
            "dates": sorted(df['date'].unique().tolist()) if 'date' in df.columns else [],
            "mean_y": float(df['target_y'].mean()) if 'target_y' in df.columns else None,
            "min_y": float(df['target_y'].min()) if 'target_y' in df.columns else None,
            "max_y": float(df['target_y'].max()) if 'target_y' in df.columns else None,
        }

    budget_info = {}
    for k, p_df in splits.target_prefix_sessions.items():
        if p_df is None:
            budget_info[str(k)] = {"available": False, "n_samples": 0, "n_sessions": 0}
        else:
            n_sess = int(p_df['session_id'].nunique()) if 'session_id' in p_df.columns else int(len(p_df))
            budget_info[str(k)] = {
                "available": True,
                "n_samples": int(len(p_df)),
                "n_sessions": n_sess
            }

    summary = {
        "experiment_name": experiment_name,
        "dataset_id": dataset_id,
        "partitions": {
            "train": _summarize_df(splits.train),
            "val": _summarize_df(splits.val),
            "source_calib": _summarize_df(splits.source_calib),
            "target_calib_pool": _summarize_df(splits.target_calib_pool),
            "target_test": _summarize_df(splits.target_test),
        },
        "budget_availability": budget_info
    }

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        # If output file exists and is a json containing a dict of summaries, merge
        existing = {}
        if out.exists():
            try:
                with open(out, 'r') as f:
                    existing = json.load(f)
            except Exception:
                existing = {}
        existing[experiment_name] = summary
        with open(out, 'w') as f:
            json.dump(existing, f, indent=2)

    return summary

