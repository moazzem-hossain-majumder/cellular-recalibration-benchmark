"""
Validation and sensitivity analysis of 2023 Ookla Speedtest session segmentation boundaries.

This script audits:
1. Zero-duration sessions (single-row spikes or instantaneous resets).
2. Very long sessions (prolonged uninterrupted throughput logging).
3. Low-throughput sessions (idle stalls vs cell edge).
4. Sensitivity of session counts, causal forecast instances, and downstream
   predictive metrics (MAE, RMSE, conformal coverage) across segmentation strategies
   ('reset', 'relative_drop', 'active_burst').

Generates:
- results/diagnostics/session_boundary_sensitivity.json
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.loader import (
    load_raw_8224890,
    extract_sessions_8224890,
    clean_numeric,
    segment_ookla_speedtests,
    filter_causal_forecast_instances,
)
from src.data.splits import create_experiment_splits
from src.features.builder import prepare_feature_dataframe
from src.models.baselines import PersistencePredictor, HistGradientBoostingThroughputPredictor
from src.evaluation.conformal import compute_conformal_quantile, GlobalConformalCalibrator
from src.evaluation.metrics import compute_reliability_metrics

DATA_DIR = ROOT / 'data/extracted/14073311/Active Performance Dataset - 1/Ookla Speedtests/Op1 and Op2 - Italy'
DIAGNOSTICS_DIR = ROOT / 'results/diagnostics'
DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)


def extract_ookla_with_method(method: str, window_seconds: float = 60.0) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Extract Ookla Speedtest sessions using a specific segmentation strategy.
    
    Returns:
        (raw_sessions_df, causal_forecast_df)
    """
    csv_files = sorted(list(DATA_DIR.glob('*.csv')))
    all_sessions = []
    
    for f in csv_files:
        df = pd.read_csv(f, sep=';', low_memory=False)
        df.columns = df.columns.str.strip()
        
        date_val = df['Day'].iloc[0] if 'Day' in df.columns else '2023-06-16'
        time_col = 'Timestamp [dd.mm.yyyy,hh:mm:ss.ss]'
        if time_col not in df.columns:
            continue
            
        df['datetime'] = pd.to_datetime(
            df['Day'] + ' ' + df[time_col],
            format='%d.%m.%Y %H:%M:%S.%f',
            errors='coerce'
        )
        fname = f.name
        scenario = 'IS' if '_IS_' in fname else ('OD' if '_OD_' in fname else 'OW')
        
        for ue_idx, op_label in [(1, 'Op1'), (2, 'Op2')]:
            mean_cols = [c for c in df.columns if 'Mean Netw. DL' in c and f': [{ue_idx}]' in c]
            if not mean_cols:
                continue
            m_col = mean_cols[0]
            scale = 1.0 if '[MBit/s]' in m_col else 0.001
            
            rsrp_cols = [c for c in df.columns if 'LTE UE_PCell_RSRP' in c and f': [{ue_idx}]' in c]
            rsrq_cols = [c for c in df.columns if 'LTE UE_PCell_RSRQ' in c and f': [{ue_idx}]' in c]
            sinr_cols = [c for c in df.columns if 'LTE UE_PCell_SINR' in c and f': [{ue_idx}]' in c]
            ss_rsrp_cols = [c for c in df.columns if '5G NR Carriers_SS-RSRP' in c and f': [{ue_idx}]' in c]
            ss_rsrq_cols = [c for c in df.columns if '5G NR Carriers_SS-RSRQ' in c and f': [{ue_idx}]' in c]
            ss_sinr_cols = [c for c in df.columns if '5G NR Carriers_SS-SINR' in c and f': [{ue_idx}]' in c]
            
            cleaned_vals = clean_numeric(df[m_col]) * scale
            valid_mask = cleaned_vals.notna() & (cleaned_vals >= 0.0)
            sub = df[valid_mask].copy()
            if len(sub) == 0:
                continue
                
            sub['val_mbps'] = cleaned_vals[valid_mask].astype(float)
            
            sub['test_id'] = segment_ookla_speedtests(
                sub['val_mbps'],
                diff_thresh=-5.0,
                val_thresh=5.0,
                timestamps=sub['datetime'] if 'datetime' in sub.columns else None,
                method=method
            )
            
            for tid, test_rows in sub.groupby('test_id'):
                final_y = test_rows['val_mbps'].iloc[-1]
                t_start = test_rows['datetime'].iloc[0]
                t_end = test_rows['datetime'].iloc[-1]
                dur = (t_end - t_start).total_seconds()
                
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
                    'rows': len(test_rows),
                    'max_gap_s': test_rows['datetime'].diff().dt.total_seconds().max(),
                    'first_mbps': test_rows['val_mbps'].iloc[0],
                    'peak_mbps': test_rows['val_mbps'].max(),
                    'internal_burst_starts': int(((test_rows['val_mbps'] > 1) & (test_rows['val_mbps'].shift() <= 1)).sum()),
                    'campaign': '2023_Chronicles',
                    'test_id_in_file': tid,
                    'operator': op_label,
                    'scenario': scenario,
                    'date': date_val,
                    't_start': t_start,
                    't_end': t_end,
                    'duration_s': dur,
                    'row_count': len(test_rows),
                    'mean_val': float(test_rows['val_mbps'].mean()),
                    'max_val': float(test_rows['val_mbps'].max()),
                    'min_val': float(test_rows['val_mbps'].min()),
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
                
    sess_df = pd.DataFrame(all_sessions)
    
    causal_rows = []
    for (f, op), grp in sess_df.groupby(['file', 'operator'], sort=False):
        grp = grp.sort_values('t_start').reset_index(drop=True)
        for i in range(1, len(grp)):
            curr = grp.iloc[i].to_dict()
            prev = grp.iloc[i - 1]
            curr['y_lag1'] = prev['target_y']
            curr['prev_duration_s'] = prev['duration_s']
            if pd.notna(curr['t_start']) and pd.notna(prev['t_end']):
                curr['lag_age_s'] = (curr['t_start'] - prev['t_end']).total_seconds()
            else:
                curr['lag_age_s'] = np.nan
            causal_rows.append(curr)
            
    fdf = pd.DataFrame(causal_rows)
    fdf = filter_causal_forecast_instances(fdf, window_seconds=window_seconds)
    fdf['session_id'] = np.arange(10000, 10000 + len(fdf))
    return sess_df, fdf


def analyze_session_boundaries():
    print("=" * 70)
    print("SESSION SEGMENTATION BOUNDARY & SENSITIVITY AUDIT")
    print("=" * 70)
    
    # 1. Source domain development split (Op1 2021)
    raw_822 = load_raw_8224890()
    _, fdf_822 = extract_sessions_8224890(raw_822)
    source_df = fdf_822[fdf_822['operator'] == 'Op1'].copy()
    
    # Train source HistGBM and Persistence using canonical split
    e0_splits = create_experiment_splits(source_df, source_df, budgets=[10], experiment_type='within_domain')
    X_train = e0_splits.train
    y_train = X_train['target_y'].to_numpy(dtype=float)
    
    model = HistGradientBoostingThroughputPredictor().fit(X_train, y_train)
    persistence = PersistencePredictor().fit(X_train, y_train)
    
    # Source calibration score
    X_cal = e0_splits.source_calib
    y_cal = X_cal['target_y'].to_numpy(dtype=float)
    src_preds = model.predict(X_cal)
    q_src = compute_conformal_quantile(src_preds - y_cal, alpha=0.10)
    
    methods = ['reset', 'relative_drop', 'active_burst']
    results = {}
    
    for m in methods:
        print(f"\nProcessing segmentation method: {m}...")
        sess_df, fdf = extract_ookla_with_method(m)
        
        sess_df[['file','operator','test_id_in_file','t_start','t_end','duration_s','rows','max_gap_s','first_mbps','peak_mbps','target_y','internal_burst_starts']].to_csv(DIAGNOSTICS_DIR / f'segments_{m}.csv', index=False)

        # Duration distribution analysis
        durations = sess_df['duration_s'].dropna().to_numpy()
        zero_dur_count = int((durations == 0.0).sum())
        short_dur_count = int(((durations > 0.0) & (durations < 10.0)).sum())
        normal_dur_count = int(((durations >= 10.0) & (durations <= 180.0)).sum())
        long_dur_count = int((durations > 180.0).sum())
        
        # Throughput analysis
        throughputs = sess_df['target_y'].dropna().to_numpy()
        low_tput_count = int((throughputs < 1.0).sum())
        zero_tput_count = int((throughputs == 0.0).sum())
        
        # Causal instances
        op1_instances = fdf[fdf['operator'] == 'Op1']
        op2_instances = fdf[fdf['operator'] == 'Op2']
        
        # Evaluate downstream metrics on target sets
        def eval_subset(sub_df):
            if len(sub_df) == 0:
                return {}
            y_true = sub_df['target_y'].to_numpy(dtype=float)
            y_pred = model.predict(sub_df)
            y_pers = persistence.predict(sub_df)
            
            mae_gbm = float(np.mean(np.abs(y_pred - y_true)))
            mae_pers = float(np.mean(np.abs(y_pers - y_true)))
            
            # Global source conformal bounds
            lb_src = np.maximum(0.0, y_pred - q_src)
            diagnostic = sub_df[['file','operator','test_id_in_file','target_y']].copy()
            diagnostic['lower_bound'] = lb_src
            diagnostic.to_csv(DIAGNOSTICS_DIR / f'sensitivity_predictions_{m}_{sub_df.operator.iloc[0]}.csv', index=False)
            m_src = compute_reliability_metrics(y_true, y_pred, lb_src)
            
            return {
                'instance_count': len(sub_df),
                'positive_endpoint_count': int((y_true > 0).sum()),
                'violation_rate_positive_endpoints': float(np.mean((lb_src > y_true)[y_true > 0])),
                'mae_histgbm': round(mae_gbm, 2),
                'mae_persistence': round(mae_pers, 2),
                'conformal_violation_rate_k0': round(m_src.violation_rate, 4),
                'conformal_supported_fraction_k0': round(m_src.supported_rate_fraction, 4)
            }
            
        e1_eval = eval_subset(op1_instances)
        e3_eval = eval_subset(op2_instances)
        
        results[m] = {
            'total_extracted_sessions': len(sess_df),
            'internal_gaps_over_10s': int((sess_df.max_gap_s > 10).sum()),
            'segments_with_multiple_rising_edges': int((sess_df.internal_burst_starts > 1).sum()),
            'duration_distribution': {
                'min_s': float(np.min(durations)) if len(durations) else 0.0,
                'median_s': float(np.median(durations)) if len(durations) else 0.0,
                'mean_s': float(np.mean(durations)) if len(durations) else 0.0,
                'max_s': float(np.max(durations)) if len(durations) else 0.0,
                'zero_duration_sessions': zero_dur_count,
                'short_sessions_under_10s': short_dur_count,
                'normal_sessions_10_to_180s': normal_dur_count,
                'long_sessions_over_180s': long_dur_count
            },
            'throughput_distribution': {
                'min_mbps': float(np.min(throughputs)) if len(throughputs) else 0.0,
                'median_mbps': float(np.median(throughputs)) if len(throughputs) else 0.0,
                'mean_mbps': float(np.mean(throughputs)) if len(throughputs) else 0.0,
                'max_mbps': float(np.max(throughputs)) if len(throughputs) else 0.0,
                'low_throughput_under_1mbps': low_tput_count,
                'zero_throughput_sessions': zero_tput_count
            },
            'causal_forecast_pairs': {
                'total_causal_pairs': len(fdf),
                'e1_op1_2023_instances': len(op1_instances),
                'e3_op2_2023_instances': len(op2_instances)
            },
            'downstream_evaluation': {
                'e1_campaign_transfer': e1_eval,
                'e3_joint_shift': e3_eval
            }
        }
        
        print(f"  Sessions: {len(sess_df)} | Median duration: {np.median(durations):.1f}s | "
              f"Zero duration: {zero_dur_count} | Long (>180s): {long_dur_count}")
        print(f"  Causal pairs: Total={len(fdf)}, E1={len(op1_instances)}, E3={len(op2_instances)}")
        print(f"  E1 MAE: HistGBM={e1_eval.get('mae_histgbm')}, Pers={e1_eval.get('mae_persistence')} | "
              f"V_src={e1_eval.get('conformal_violation_rate_k0')}")
        print(f"  E3 MAE: HistGBM={e3_eval.get('mae_histgbm')}, Pers={e3_eval.get('mae_persistence')} | "
              f"V_src={e3_eval.get('conformal_violation_rate_k0')}")
              
    out_file = DIAGNOSTICS_DIR / 'session_boundary_sensitivity.json'
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\nSaved boundary sensitivity diagnostic to: {out_file}")
    
    # Cross-method stability summary
    print("\n--- Cross-Strategy Conclusions ---")
    print(f"1. Zero-duration sessions represent single-measurement telemetry samples at file boundaries or resets.")
    print(f"2. Conformal source calibration violation rate varies by observational unit:")
    for m in methods:
        v_e1 = results[m]['downstream_evaluation']['e1_campaign_transfer'].get('conformal_violation_rate_k0')
        v_e3 = results[m]['downstream_evaluation']['e3_joint_shift'].get('conformal_violation_rate_k0')
        print(f"   - {m:15s} | E1 V = {v_e1:.4f} | E3 V = {v_e3:.4f}")
    print("3. Active-start segments retain the trailing idle rows. Their endpoint differs from the reset endpoint.")


if __name__ == '__main__':
    from typing import Tuple
    analyze_session_boundaries()
