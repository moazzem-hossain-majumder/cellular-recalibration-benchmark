"""Data loading, session extraction, and causal feature construction for cellular throughput."""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

def clean_numeric(series: pd.Series) -> pd.Series:
    """Convert string series with '?' sentinels to float."""
    return pd.to_numeric(series.replace('?', np.nan), errors='coerce')

def segment_ookla_speedtests(series: pd.Series,
                            diff_thresh: float = -5.0,
                            val_thresh: float = 5.0,
                            timestamps: Optional[pd.Series] = None,
                            method: str = "reset") -> pd.Series:
    """Identify discrete Ookla Speedtest session boundaries.
    
    Args:
        series: Numeric series of throughput measurements over time.
        diff_thresh: Throughput drop threshold for reset detection (default: -5.0 Mbps).
        val_thresh: Absolute throughput ceiling after reset (default: 5.0 Mbps).
        timestamps: Optional datetime series for time-gap based burst detection.
        method: Segmentation strategy ('reset', 'relative_drop', or 'active_burst').
    
    Returns:
        Series of integer session IDs (cumsum).
    """
    if method == "reset":
        is_reset = (series.diff() < diff_thresh) & (series < val_thresh)
    elif method == "relative_drop":
        is_reset = (series.diff() < -2.0) & (series < 1.0)
    elif method == "active_burst":
        is_active = series > 1.0
        active_start = is_active & (~is_active.shift(1, fill_value=False))
        if timestamps is not None and len(timestamps) == len(series):
            time_diffs = timestamps.diff().dt.total_seconds().fillna(0.0)
            time_gap = time_diffs > 10.0
            is_reset = active_start | time_gap
        else:
            is_reset = active_start
    else:
        raise ValueError(f"Unknown segmentation method: {method}")
    return is_reset.cumsum()

def filter_causal_forecast_instances(df: pd.DataFrame, window_seconds: float = 60.0) -> pd.DataFrame:
    """Enforce strict causal lag freshness, non-negativity, and valid target labels.
    
    1. lag_age_s must be non-null and non-negative (reject acausal clock drift / future leakage).
    2. lag_age_s must be <= window_seconds (reject stale historical memory).
    3. target_y must be valid and non-null (exclude missing targets from supervised forecasting).
    
    Args:
        df: DataFrame containing 'lag_age_s' and 'target_y' columns.
        window_seconds: Maximum permissible lookback horizon in seconds (default: 60s).
    
    Returns:
        Filtered DataFrame free of acausal clock drift, stale historical lags, or missing targets.
    """
    valid_mask = (
        pd.notna(df['lag_age_s']) &
        (df['lag_age_s'] >= 0.0) &
        (df['lag_age_s'] <= float(window_seconds)) &
        pd.notna(df['target_y'])
    )
    return df[valid_mask].copy().reset_index(drop=True)

def load_raw_8224890(csv_path: Path = None) -> pd.DataFrame:
    """Load and parse earlier campaign (Zenodo 8224890) CSV."""
    if csv_path is None:
        csv_path = ROOT / 'data/raw/8224890/Throughput Tests - Speedtest - Active Measurements.csv'
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d.%m.%Y %H:%M:%S.%f')
    
    # Clean radio features
    df['rsrp'] = clean_numeric(df['RSRP'])
    df['rsrq'] = clean_numeric(df['RSRQ'])
    df['sinr'] = clean_numeric(df['SINR'])
    df['ss_rsrp'] = clean_numeric(df['SS-RSRP'])
    df['ss_rsrq'] = clean_numeric(df['SS-RSRQ'])
    df['ss_sinr'] = clean_numeric(df['SS-SINR'])
    df['pci_lte'] = clean_numeric(df['LTE PCI'])
    df['pci_5g'] = clean_numeric(df['5G  PCI'])
    
    return df

def extract_sessions_8224890(df: pd.DataFrame, window_seconds: int = 60) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Extract discrete Speedtest sessions and build forward-causal forecast dataset.
    
    Args:
        df: Raw DataFrame from Zenodo 8224890 active measurements.
        window_seconds: Telemetry lookback window duration in seconds (default: 60s).
    
    Returns:
        sdf: DataFrame of session metadata (548 sessions)
        fdf: DataFrame of causal forecast instances (503 instances)
    """
    sessions = []
    sess_global_id = 0
    
    for camp, group in df.groupby('Campaign', sort=False):
        dqa_sub = group[group['DQA Result'] != '?'].index.tolist()
        last_idx = group.index[0]
        
        for sess_num, end_idx in enumerate(dqa_sub):
            start_idx = last_idx
            sess_rows = df.loc[start_idx:end_idx]
            t_start = sess_rows['datetime'].iloc[0]
            t_end = sess_rows['datetime'].iloc[-1]
            dur_s = (t_end - t_start).total_seconds()
            
            dl_rows = sess_rows[sess_rows['Mean Netw. DL'] != '?']
            mean_dl_kbps = float(dl_rows['Mean Netw. DL'].iloc[-1]) if len(dl_rows) > 0 else np.nan
            # Preserve missing target labels as NaN; never silently coerce missing targets to zero.
            mean_dl_mbps = (mean_dl_kbps / 1000.0) if pd.notna(mean_dl_kbps) else np.nan
            
            op = sess_rows['Operator'].iloc[-1]
            scen = sess_rows['Scenario'].iloc[-1]
            date = sess_rows['Date'].iloc[-1]
            dqa_res = sess_rows['DQA Result'].iloc[-1]
            
            sessions.append({
                'session_id': sess_global_id,
                'campaign': camp,
                'sess_num_in_campaign': sess_num,
                'start_idx': start_idx,
                'end_idx': end_idx,
                't_start': t_start,
                't_end': t_end,
                'duration_s': dur_s,
                'y_mbps': mean_dl_mbps,
                'operator': op,
                'scenario': scen,
                'date': date,
                'dqa_result': dqa_res
            })
            sess_global_id += 1
            last_idx = end_idx + 1

    sdf = pd.DataFrame(sessions)
    
    # Build forward-causal forecast dataset (sessions with preceding completed test in same campaign)
    forecast_rows = []
    for i in range(len(sdf)):
        row = sdf.iloc[i]
        if row['sess_num_in_campaign'] == 0:
            continue  # Warm-up session providing lag for session 1
            
        prev_row = sdf.iloc[i - 1]
        assert prev_row['campaign'] == row['campaign']
        
        # Freshness is only defined when both timestamps are valid non-null datetime values
        if pd.notna(row['t_start']) and pd.notna(prev_row['t_end']):
            lag_age_s = (row['t_start'] - prev_row['t_end']).total_seconds()
        else:
            lag_age_s = np.nan
        
        # Second lag (if available)
        if row['sess_num_in_campaign'] >= 2:
            prev_prev_row = sdf.iloc[i - 2]
            y_lag2 = prev_prev_row['y_mbps']
            has_lag2 = 1.0
        else:
            y_lag2 = prev_row['y_mbps']
            has_lag2 = 0.0
            
        # Causal pre-test radio window: telemetry in [t_start - window_seconds, t_start]
        t_start = row['t_start']
        window_start = t_start - pd.Timedelta(seconds=window_seconds)
        
        pred_rows = df.loc[prev_row['start_idx']:row['start_idx'] - 1]
        pred_window = pred_rows[pred_rows['datetime'] >= window_start]
        
        has_lte = int(pred_window['rsrp'].notna().any())
        has_nr = int(pred_window['ss_rsrp'].notna().any())
        
        latest_rsrp = pred_window['rsrp'].dropna().iloc[-1] if has_lte else np.nan
        latest_rsrq = pred_window['rsrq'].dropna().iloc[-1] if has_lte else np.nan
        latest_sinr = pred_window['sinr'].dropna().iloc[-1] if has_lte else np.nan
        
        latest_ss_rsrp = pred_window['ss_rsrp'].dropna().iloc[-1] if has_nr else np.nan
        latest_ss_rsrq = pred_window['ss_rsrq'].dropna().iloc[-1] if has_nr else np.nan
        latest_ss_sinr = pred_window['ss_sinr'].dropna().iloc[-1] if has_nr else np.nan
        
        # Radio group: 0: None, 1: NR only, 2: LTE only, 3: Dual LTE+NR
        group_id = has_lte * 2 + has_nr
        
        # Serving cell identifiers
        latest_pci_lte = pred_window['pci_lte'].dropna().iloc[-1] if pred_window['pci_lte'].notna().any() else -1.0
        latest_pci_5g = pred_window['pci_5g'].dropna().iloc[-1] if pred_window['pci_5g'].notna().any() else -1.0
        
        forecast_rows.append({
            'session_id': row['session_id'],
            'campaign': row['campaign'],
            'sess_num': row['sess_num_in_campaign'],
            'date': row['date'],
            't_start': row['t_start'],
            't_end': row['t_end'],
            'duration_s': row['duration_s'],
            'operator': row['operator'],
            'scenario': row['scenario'],
            'y_lag1': prev_row['y_mbps'],
            'y_lag2': y_lag2,
            'has_lag2': has_lag2,
            'lag_age_s': lag_age_s,
            'prev_duration_s': prev_row['duration_s'],
            'has_lte': has_lte,
            'has_nr': has_nr,
            'group_id': group_id,
            'rsrp': latest_rsrp,
            'rsrq': latest_rsrq,
            'sinr': latest_sinr,
            'ss_rsrp': latest_ss_rsrp,
            'ss_rsrq': latest_ss_rsrq,
            'ss_sinr': latest_ss_sinr,
            'pci_lte': latest_pci_lte,
            'pci_5g': latest_pci_5g,
            'target_y': row['y_mbps']
        })

    fdf = pd.DataFrame(forecast_rows)
    fdf = filter_causal_forecast_instances(fdf, window_seconds=window_seconds)
    return sdf, fdf

def load_14073311_ookla(extract_dir: Path = None, window_seconds: int = 60) -> pd.DataFrame:
    """Load and parse the 2023 campaign (Chronicles 14073311) Ookla Speedtest traces.
    
    Args:
        extract_dir: Path to directory containing Ookla Speedtest CSVs.
        window_seconds: Telemetry lookback window duration in seconds (default: 60s).
    
    Returns:
        DataFrame of extracted sessions and causal lags for both Op1 (UE1) and Op2 (UE2).
    """
    if extract_dir is None:
        extract_dir = ROOT / 'data/extracted/14073311/Active Performance Dataset - 1/Ookla Speedtests/Op1 and Op2 - Italy'
    
    csv_files = sorted(list(extract_dir.glob('*.csv')))
    all_sessions = []
    
    for f in csv_files:
        df = pd.read_csv(f, sep=';', low_memory=False)
        df.columns = df.columns.str.strip()
        
        # Date column
        date_val = df['Day'].iloc[0] if 'Day' in df.columns else '2023-06-16'
        time_col = 'Timestamp [dd.mm.yyyy,hh:mm:ss.ss]'
        if time_col not in df.columns:
            continue
            
        df['datetime'] = pd.to_datetime(df['Day'] + ' ' + df[time_col], format='%d.%m.%Y %H:%M:%S.%f', errors='coerce')
        
        # Scenario from filename
        fname = f.name
        scenario = 'IS' if '_IS_' in fname else ('OD' if '_OD_' in fname else 'OW')
        
        for ue_idx, op_label in [(1, 'Op1'), (2, 'Op2')]:
            # Locate Mean DL column
            mean_cols = [c for c in df.columns if 'Mean Netw. DL' in c and f': [{ue_idx}]' in c]
            if not mean_cols:
                continue
            m_col = mean_cols[0]
            scale = 1.0 if '[MBit/s]' in m_col else 0.001
            
            # Locate radio columns
            rsrp_cols = [c for c in df.columns if 'LTE UE_PCell_RSRP' in c and f': [{ue_idx}]' in c]
            rsrq_cols = [c for c in df.columns if 'LTE UE_PCell_RSRQ' in c and f': [{ue_idx}]' in c]
            sinr_cols = [c for c in df.columns if 'LTE UE_PCell_SINR' in c and f': [{ue_idx}]' in c]
            ss_rsrp_cols = [c for c in df.columns if '5G NR Carriers_SS-RSRP' in c and f': [{ue_idx}]' in c]
            ss_rsrq_cols = [c for c in df.columns if '5G NR Carriers_SS-RSRQ' in c and f': [{ue_idx}]' in c]
            ss_sinr_cols = [c for c in df.columns if '5G NR Carriers_SS-SINR' in c and f': [{ue_idx}]' in c]
            
            # Clean and validate numeric values before segmentation
            cleaned_vals = clean_numeric(df[m_col]) * scale
            valid_mask = cleaned_vals.notna() & (cleaned_vals >= 0.0)
            sub = df[valid_mask].copy()
            if len(sub) == 0:
                continue
                
            sub['val_mbps'] = cleaned_vals[valid_mask].astype(float)
            
            # Identify test segments by resets: drop > 5 Mbps to < 5 Mbps
            sub['test_id'] = segment_ookla_speedtests(
                sub['val_mbps'], diff_thresh=-5.0, val_thresh=5.0,
                timestamps=sub['datetime'] if 'datetime' in sub.columns else None,
                method='reset'
            )
            
            # Group by test_id
            for tid, test_rows in sub.groupby('test_id'):
                final_y = test_rows['val_mbps'].iloc[-1]
                t_start = test_rows['datetime'].iloc[0]
                t_end = test_rows['datetime'].iloc[-1]
                dur = (t_end - t_start).total_seconds()
                
                # Check radio telemetry in window before start
                window_start = t_start - pd.Timedelta(seconds=window_seconds)
                pre_df = df[(df['datetime'] >= window_start) & (df['datetime'] < t_start)]
                
                rsrp_val = clean_numeric(pre_df[rsrp_cols[0]]).dropna().iloc[-1] if (rsrp_cols and len(pre_df) and clean_numeric(pre_df[rsrp_cols[0]]).notna().any()) else np.nan
                rsrq_val = clean_numeric(pre_df[rsrq_cols[0]]).dropna().iloc[-1] if (rsrq_cols and len(pre_df) and clean_numeric(pre_df[rsrq_cols[0]]).notna().any()) else np.nan
                sinr_val = clean_numeric(pre_df[sinr_cols[0]]).dropna().iloc[-1] if (sinr_cols and len(pre_df) and clean_numeric(pre_df[sinr_cols[0]]).notna().any()) else np.nan
                
                ss_rsrp_val = clean_numeric(pre_df[ss_rsrp_cols[0]]).dropna().iloc[-1] if (ss_rsrp_cols and len(pre_df) and clean_numeric(pre_df[ss_rsrp_cols[0]]).notna().any()) else np.nan
                ss_rsrq_val = clean_numeric(pre_df[ss_rsrq_cols[0]]).dropna().iloc[-1] if (ss_rsrq_cols and len(pre_df) and clean_numeric(pre_df[ss_rsrq_cols[0]]).notna().any()) else np.nan
                ss_sinr_val = clean_numeric(pre_df[ss_sinr_cols[0]]).dropna().iloc[-1] if (ss_sinr_cols and len(pre_df) and clean_numeric(pre_df[ss_sinr_cols[0]]).notna().any()) else np.nan
                
                has_lte = int(not np.isnan(rsrp_val))
                has_nr = int(not np.isnan(ss_rsrp_val))
                grp = has_lte * 2 + has_nr
                
                all_sessions.append({
                    'file': fname,
                    'campaign': '2023_Chronicles',
                    'test_id_in_file': tid,
                    'operator': op_label,
                    'scenario': scenario,
                    'date': date_val,
                    't_start': t_start,
                    't_end': t_end,
                    'duration_s': dur,
                    'has_lte': has_lte,
                    'has_nr': has_nr,
                    'group_id': grp,
                    'rsrp': rsrp_val,
                    'rsrq': rsrq_val,
                    'sinr': sinr_val,
                    'ss_rsrp': ss_rsrp_val,
                    'ss_rsrq': ss_rsrq_val,
                    'ss_sinr': ss_sinr_val,
                    'target_y': final_y
                })
                
    cf_df = pd.DataFrame(all_sessions)
    
    # Form causal lags within each file
    causal_rows = []
    for (f, op), grp in cf_df.groupby(['file', 'operator'], sort=False):
        grp = grp.sort_values('t_start').reset_index(drop=True)
        for i in range(1, len(grp)):
            curr = grp.iloc[i].to_dict()
            prev = grp.iloc[i - 1]
            curr['y_lag1'] = prev['target_y']
            curr['prev_duration_s'] = prev['duration_s']
            # Freshness is only defined when both timestamps are valid non-null datetime values
            if pd.notna(curr['t_start']) and pd.notna(prev['t_end']):
                curr['lag_age_s'] = (curr['t_start'] - prev['t_end']).total_seconds()
            else:
                curr['lag_age_s'] = np.nan
            causal_rows.append(curr)
            
    fdf = pd.DataFrame(causal_rows)
    fdf = filter_causal_forecast_instances(fdf, window_seconds=window_seconds)
    fdf['session_id'] = np.arange(10000, 10000 + len(fdf))
    return fdf

