"""Unified 15-feature chronological archive loader and strict zero-leakage LOCampO splits."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from scripts.audit_trip_level_inference import physical_campaign_key
from scripts.build_heldout_cohorts import (
    _ireland_static_ticks,
    _load_frozen_rome_model,
    _oslo_commute_ticks,
    _rome_capacity_ticks,
)
from scripts.clock_frontier import clock_pairs
from scripts.replay_oslo_playback import BUS, OUT as OSLO_META_DIR
from src.data.loader import extract_sessions_8224890, load_raw_8224890
from src.features.builder import FEATURE_COLS, prepare_feature_dataframe

ROOT = Path(__file__).resolve().parents[2]

COHORT_TO_CAMPAIGN = {
    'E1': 'Rome_2023',
    'E3': 'Rome_2023',
    'AT&T': 'US_Drive3',
    'T-Mobile': 'US_Drive3',
    'Verizon': 'US_Drive3',
    'Ireland': 'Ireland_Drive',
    'Rome_Capacity_Op1': 'Rome_Capacity',
    'Rome_Capacity_Op2': 'Rome_Capacity',
    'Oslo_Commute': 'Oslo_Commute',
    'Ireland_Static': 'Ireland_Static',
}

# Overlapping same-city collections collected on identical dates must not train on each other.
OVERLAPPING_CAMPAIGN_PAIRS = {
    'Rome_2023': {'Rome_Capacity'},
    'Rome_Capacity': {'Rome_2023'},
}


def physical_unit_for_row(cohort: str, date_str: str) -> str:
    """Return exact physical cluster-date identifier matching results/pacer conventions."""
    if cohort in ('Rome_Capacity_Op1', 'Rome_Capacity_Op2'):
        return f'RomeCap:{date_str}'
    if cohort == 'Oslo_Commute':
        return f'Oslo:{date_str}'
    if cohort == 'Ireland_Static':
        return f'IrelandStatic:{date_str}'
    return physical_campaign_key(cohort, str(date_str))


def _ensure_unified_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all 15 FEATURE_COLS plus metadata columns exist without modifying targets."""
    out = df.copy()
    if 'y_lag1' not in out.columns:
        out['y_lag1'] = out['Persistence'].astype(float) if 'Persistence' in out.columns else out['lag'].astype(float)
    if 'prev_duration_s' not in out.columns:
        out['prev_duration_s'] = np.nan
    if 'lag_age_s' not in out.columns:
        out['lag_age_s'] = np.nan
    for col in ('rsrp', 'rsrq', 'sinr', 'ss_rsrp', 'ss_rsrq', 'ss_sinr'):
        if col not in out.columns:
            out[col] = np.nan
    if 'scenario' not in out.columns:
        out['scenario'] = 'IS'
    if 'has_lte' not in out.columns:
        out['has_lte'] = out['rsrp'].notna().astype(int)
    if 'has_nr' not in out.columns:
        out['has_nr'] = out['ss_rsrp'].notna().astype(int)
    if 'group_id' not in out.columns:
        out['group_id'] = 2 * out['has_lte'].astype(int) + out['has_nr'].astype(int)
    feats = prepare_feature_dataframe(out)
    for col in FEATURE_COLS:
        out[col] = feats[col]
    return out


def load_oslo_bus_source(cutoff_utc: str = '2010-10-01T00:00:00Z') -> pd.DataFrame:
    """Load strictly pre-cutoff Oslo Bus source traces (< 2010-10-01) in unified feature schema."""
    split = pd.Timestamp(cutoff_utc)
    if split.tzinfo is None:
        split = split.tz_localize('UTC')
    manifest = json.loads((OSLO_META_DIR / 'dataset_manifest.json').read_text(encoding='utf8'))
    frames = []
    for name in sorted(manifest['norway_files']):
        d = pd.read_csv(BUS / name, sep=r'\s+', header=None, names=['unix', 'ms', 'lat', 'lon', 'bytes', 'elapsed'])
        d = d.sort_values('ms', kind='stable')
        valid = (d['bytes'] >= 0) & (d['elapsed'] > 0) & (d['ms'].diff().eq(d['elapsed']) | (d.index == d.index[0]))
        rate = (0.008 * d['bytes'] / d['elapsed']).where(valid)
        ts = pd.to_datetime(d['unix'], unit='s', utc=True)
        ser = pd.Series(rate.to_numpy(), index=ts).dropna().groupby(level=0).last()
        pairs = clock_pairs(ser, ser.index.min(), ser.index.max(), include_ineligible=False)
        pairs = pairs[pairs['end'] < split].copy().reset_index(drop=True)
        if pairs.empty:
            continue
        prev = pd.DatetimeIndex(pd.to_datetime(pairs['time'], utc=True)) - pd.Timedelta(minutes=1)
        times = pd.Series(ser.index, index=ser.index).resample('min')
        t_pair_utc = pd.to_datetime(pairs['time'], utc=True).reset_index(drop=True)
        t_end_utc = pd.to_datetime(pairs['end'], utc=True).reset_index(drop=True)
        tlast_utc = pd.to_datetime(times.last().reindex(prev).to_numpy(), utc=True)
        tfirst_utc = pd.to_datetime(times.first().reindex(prev).to_numpy(), utc=True)
        pairs['lag_age_s'] = (pd.DatetimeIndex(t_pair_utc) - pd.DatetimeIndex(tlast_utc)).total_seconds().to_numpy()
        pairs['prev_duration_s'] = (pd.DatetimeIndex(tlast_utc) - pd.DatetimeIndex(tfirst_utc)).total_seconds().to_numpy()
        pairs['trace'] = f'bus/{name}'
        pairs['date'] = t_pair_utc.dt.date.astype(str)
        epoch = pd.Timestamp('1970-01-01', tz='UTC')
        pairs['issue'] = (t_pair_utc - epoch).dt.total_seconds().to_numpy()
        pairs['ready'] = (t_end_utc - epoch).dt.total_seconds().to_numpy()
        frames.append(pairs)
    bus = pd.concat(frames, ignore_index=True)
    bus = bus.dropna(subset=['lag', 'y']).copy()
    bus['y_lag1'] = bus['lag'].astype(float)
    bus['has_lte'] = 0
    bus['has_nr'] = 0
    bus['group_id'] = 1
    bus['scenario'] = 'OW'
    bus['cohort'] = 'Oslo_Bus_2010'
    bus['source_campaign'] = 'Oslo_Bus_2010'
    bus['domain'] = 'source_archive'
    return _ensure_unified_features(bus)


def load_rome_2021_source() -> pd.DataFrame:
    """Load full Zenodo 8224890 (2020-12 to 2021-01 Op1+Op2) session source data in unified schema."""
    raw = load_raw_8224890()
    _, fdf = extract_sessions_8224890(raw)
    out = fdf.copy()
    out['y'] = out['target_y'].astype(float)
    t_start = pd.to_datetime(out['t_start'], format='mixed').dt.tz_localize('Europe/Rome', ambiguous='infer').dt.tz_convert('UTC')
    t_end = pd.to_datetime(out['t_end'], format='mixed').dt.tz_localize('Europe/Rome', ambiguous='infer').dt.tz_convert('UTC')
    epoch = pd.Timestamp('1970-01-01', tz='UTC')
    out['issue'] = (t_start - epoch).dt.total_seconds().astype(float)
    out['ready'] = (t_end - epoch).dt.total_seconds().astype(float)
    out['date'] = t_start.dt.date.astype(str)
    out['cohort'] = 'Rome_2021_' + out['operator'].astype(str)
    out['source_campaign'] = 'Rome_2021_8224890'
    out['domain'] = 'source_archive'
    return _ensure_unified_features(out)


def _enrich_oslo_commute_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Populate exact causal lag_age_s/prev_duration_s/y_lag1 on Oslo_Commute from raw logs."""
    out = df.copy()
    out['y_lag1'] = out['Persistence'].astype(float)
    pins = json.loads((ROOT / 'data/metadata/oslo_playback_sources.json').read_text(encoding='utf-8-sig'))
    timing_rows = []
    epoch = pd.Timestamp('1970-01-01', tz='UTC')
    for item in pins:
        path = ROOT / 'data/raw/oslo-playback' / item['route'] / item['name']
        d = pd.read_csv(path, sep=r'\s+', header=None, names=['unix', 'ms', 'lat', 'lon', 'bytes', 'elapsed']).sort_values('ms', kind='stable')
        valid = (d['bytes'] >= 0) & (d['elapsed'] > 0) & (d['ms'].diff().eq(d['elapsed']) | (d.index == d.index[0]))
        rate = (0.008 * d['bytes'] / d['elapsed']).where(valid)
        ts = pd.to_datetime(d['unix'], unit='s', utc=True)
        ser = pd.Series(rate.to_numpy(), index=ts).dropna().groupby(level=0).last()
        if ser.empty:
            continue
        pairs = clock_pairs(ser, ser.index.min(), ser.index.max(), include_ineligible=True).reset_index(drop=True)
        t_pair = pd.to_datetime(pairs['time'], utc=True)
        prev = pd.DatetimeIndex(t_pair) - pd.Timedelta(minutes=1)
        times = pd.Series(ser.index, index=ser.index).resample('min')
        tlast = pd.to_datetime(times.last().reindex(prev).to_numpy(), utc=True)
        tfirst = pd.to_datetime(times.first().reindex(prev).to_numpy(), utc=True)
        timing_rows.append(pd.DataFrame({
            'trace': f"{item['route']}/{item['name']}",
            'issue': (t_pair - epoch).dt.total_seconds().to_numpy(),
            'lag_age_s': (pd.DatetimeIndex(t_pair) - pd.DatetimeIndex(tlast)).total_seconds().to_numpy(),
            'prev_duration_s': (pd.DatetimeIndex(tlast) - pd.DatetimeIndex(tfirst)).total_seconds().to_numpy(),
        }))
    timings = pd.concat(timing_rows, ignore_index=True).drop_duplicates(['trace', 'issue'])
    out = out.drop(columns=['lag_age_s', 'prev_duration_s'], errors='ignore').merge(
        timings, on=['trace', 'issue'], how='left', validate='one_to_one'
    )
    out['scenario'] = 'OW'
    return _ensure_unified_features(out)


def load_all_evaluation_cohorts() -> pd.DataFrame:
    """Load all 10 benchmark cohorts preserving exact cal/test partitions and reconstructing all 15 features."""
    cfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))
    frozen_model, _ = _load_frozen_rome_model()

    retro = pd.read_csv(ROOT / 'results/marur/opportunities.csv.gz', float_precision='round_trip', low_memory=False)
    retro = retro.copy()
    retro['HistGBM'] = np.where(retro['HistGBM'].notna(), retro['HistGBM'], retro['Tree'])
    retro['domain'] = 'retrospective'
    retro['date'] = retro['date'].astype(str)
    retro['physical_unit'] = [physical_unit_for_row(c, d) for c, d in zip(retro['cohort'], retro['date'])]
    retro = _ensure_unified_features(retro)

    rc = _rome_capacity_ticks(frozen_model)
    rc['domain'] = 'heldout_public'
    rc = _ensure_unified_features(rc)

    ist = _ireland_static_ticks(frozen_model)
    ist['domain'] = 'heldout_public'
    ist = _ensure_unified_features(ist)

    oc = _oslo_commute_ticks(cfg['oslo_cutoff_utc'])
    oc['domain'] = 'heldout_public'
    oc = _enrich_oslo_commute_lag_features(oc)

    keep_cols = sorted(
        set(FEATURE_COLS).union(
            {
                'cohort', 'partition', 'date', 'issue', 'ready', 'id', 'pattern', 'y',
                'Persistence', 'HistGBM', 'trace', 'scenario', 'has_lte', 'has_nr',
                'group_id', 'physical_unit', 'domain',
            }
        )
    )
    all_df = pd.concat([retro[keep_cols], rc[keep_cols], ist[keep_cols], oc[keep_cols]], ignore_index=True)
    all_df['source_campaign'] = all_df['cohort'].map(COHORT_TO_CAMPAIGN)
    return all_df


def build_locampo_train_pool(
    eval_cohorts_df: pd.DataFrame,
    source_archives_df: pd.DataFrame,
    target_campaign: str,
    *,
    exclude_overlapping_city_pair: bool = True,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Build strictly earlier-in-time LOCampO training pool for target_campaign with zero future leakage."""
    target_rows = eval_cohorts_df[
        (eval_cohorts_df['source_campaign'] == target_campaign)
        & (eval_cohorts_df['partition'].isin(['cal', 'test']))
    ]
    if target_rows.empty:
        raise ValueError(f'Unknown or empty target_campaign: {target_campaign}')

    cutoff_issue = float(target_rows['issue'].min())
    excluded = {target_campaign}
    if exclude_overlapping_city_pair:
        excluded |= OVERLAPPING_CAMPAIGN_PAIRS.get(target_campaign, set())

    combined_pool = pd.concat([eval_cohorts_df, source_archives_df], ignore_index=True)
    mask = (
        (~combined_pool['source_campaign'].isin(excluded))
        & (combined_pool['ready'] < cutoff_issue)
        & combined_pool['y'].notna()
        & (combined_pool['y'] >= 0.0)
        & combined_pool['y_lag1'].notna()
    )
    train_df = combined_pool[mask].copy()
    train_df = train_df.sort_values(['ready', 'issue', 'cohort'], kind='mergesort').reset_index(drop=True)

    # Assert strict chronological zero-leakage invariant
    if not train_df.empty:
        if float(train_df['ready'].max()) >= cutoff_issue:
            raise AssertionError('Future leakage detected: train ready >= target cutoff_issue')
        if set(train_df['source_campaign']).intersection(excluded):
            raise AssertionError('Target or excluded overlapping campaign leaked into LOCampO training pool')

    meta = {
        'target_campaign': target_campaign,
        'target_cal_start_utc': pd.to_datetime(cutoff_issue, unit='s', utc=True).isoformat(),
        'n_train_rows': int(len(train_df)),
        'n_train_dates': int(train_df['date'].nunique()) if not train_df.empty else 0,
        'source_campaigns_used': sorted(train_df['source_campaign'].unique().tolist()) if not train_df.empty else [],
        'n_other_eval_campaigns': int(
            len([c for c in train_df['source_campaign'].unique() if c in set(COHORT_TO_CAMPAIGN.values())])
        )
        if not train_df.empty
        else 0,
    }
    return train_df, meta


def chronological_date_splits(
    train_df: pd.DataFrame,
    *,
    val_frac: float = 0.20,
    calib_frac: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    """Chronologically block-split training rows by (source_campaign, date) within each campaign.

    Never uses random row splits. Within each prior source campaign present in `train_df`,
    whole calendar dates are ordered chronologically so earlier dates go to proper_train,
    middle dates go to validation, and final dates go to cqr_calib.
    """
    work = train_df.copy()
    tr_parts: list[pd.DataFrame] = []
    va_parts: list[pd.DataFrame] = []
    cal_parts: list[pd.DataFrame] = []

    for camp, grp in work.groupby('source_campaign', sort=True):
        grp = grp.copy()
        grp['_dt'] = grp['date'].astype(str)
        date_order = grp.groupby('_dt')['ready'].min().sort_values(kind='mergesort').index.tolist()
        n_d = len(date_order)

        if n_d == 1:
            # Rare 1-date fallback: chronological prefix vs suffix by ready timestamp
            g_sorted = grp.sort_values(['ready', 'issue'], kind='mergesort')
            n_g = len(g_sorted)
            if calib_frac <= 0.0:
                cut = max(1, int(round((1.0 - val_frac) * n_g)))
                tr_parts.append(g_sorted.iloc[:cut])
                va_parts.append(g_sorted.iloc[cut:])
            else:
                c1 = max(1, int(round((1.0 - val_frac - calib_frac) * n_g)))
                c2 = max(c1 + 1, int(round((1.0 - calib_frac) * n_g)))
                tr_parts.append(g_sorted.iloc[:c1])
                va_parts.append(g_sorted.iloc[c1:c2])
                cal_parts.append(g_sorted.iloc[c2:])
            continue

        if calib_frac <= 0.0:
            n_val = max(1, int(round(val_frac * n_d)))
            n_val = min(n_val, n_d - 1)
            tr_d = date_order[:-n_val]
            va_d = date_order[-n_val:]
            while len(tr_d) < n_d - 1 and int(grp['_dt'].isin(tr_d).sum()) < 25:
                tr_d = date_order[: len(tr_d) + 1]
                va_d = date_order[len(tr_d) :]
            tr_parts.append(grp[grp['_dt'].isin(tr_d)])
            va_parts.append(grp[grp['_dt'].isin(va_d)])
            continue

        # 3-way split preserving strictly disjoint chronological dates for CQR
        if n_d == 2:
            # Hold second date strictly as cqr_calib; earliest date split chronologically for inner train/val
            d_early = grp[grp['_dt'] == date_order[0]].sort_values(['ready', 'issue'], kind='mergesort')
            cut = max(1, int(round((1.0 - val_frac) * len(d_early))))
            tr_parts.append(d_early.iloc[:cut])
            va_parts.append(d_early.iloc[cut:])
            cal_parts.append(grp[grp['_dt'] == date_order[1]])
        elif n_d == 3:
            # Reserve final date strictly untouched as cqr_calib; earlier 2 dates chronological if small day 1
            cal_d = [date_order[-1]]
            d_early = grp[grp['_dt'].isin(date_order[:-1])].sort_values(['ready', 'issue'], kind='mergesort')
            if int((grp['_dt'] == date_order[0]).sum()) >= 20:
                tr_parts.append(grp[grp['_dt'] == date_order[0]])
                va_parts.append(grp[grp['_dt'] == date_order[1]])
            else:
                cut = max(25, int(round(0.75 * len(d_early))))
                tr_parts.append(d_early.iloc[:cut])
                va_parts.append(d_early.iloc[cut:])
            cal_parts.append(grp[grp['_dt'].isin(cal_d)])
        else:
            n_cal = max(1, int(round(calib_frac * n_d)))
            n_val = max(1, int(round(val_frac * n_d)))
            if n_cal + n_val >= n_d:
                n_cal = 1
                n_val = 1
            cal_d = date_order[-n_cal:]
            va_d = date_order[-(n_cal + n_val) : -n_cal]
            tr_d = date_order[: -(n_cal + n_val)]
            while len(tr_d) < n_d - 2 and int(grp['_dt'].isin(tr_d).sum()) < 25:
                idx = len(tr_d) + 1
                tr_d = date_order[:idx]
                va_d = date_order[idx:-n_cal]
                if not va_d:
                    va_d = [date_order[-2]]
                    cal_d = [date_order[-1]]
                    tr_d = date_order[:-2]
                    break
            assert set(tr_d).isdisjoint(set(cal_d)) and set(va_d).isdisjoint(set(cal_d))
            tr_parts.append(grp[grp['_dt'].isin(tr_d)])
            va_parts.append(grp[grp['_dt'].isin(va_d)])
            cal_parts.append(grp[grp['_dt'].isin(cal_d)])

    tr_df = pd.concat(tr_parts, ignore_index=True).drop(columns=['_dt'], errors='ignore')
    va_df = pd.concat(va_parts, ignore_index=True).drop(columns=['_dt'], errors='ignore')
    cal_df = (
        pd.concat(cal_parts, ignore_index=True).drop(columns=['_dt'], errors='ignore')
        if calib_frac > 0.0
        else None
    )
    return tr_df, va_df, cal_df
