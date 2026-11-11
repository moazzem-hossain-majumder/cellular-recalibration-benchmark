"""Empirical validation and cross-strategy comparison of 2023 Ookla Speedtest session segmentation.

Evaluates all 43 Ookla Speedtest trace files in Chronicles 14073311 (Active Performance Dataset - 1)
across three segmentation strategies:
1. Threshold Reset: Throughput drop < -5.0 Mbps to < 5.0 Mbps (Baseline)
2. Relative Drop: Throughput drop < -2.0 Mbps to < 1.0 Mbps
3. Active Burst: Throughput > 1.0 Mbps with idle time gaps > 10s

Generates diagnostic report: results/diagnostics/session_segmentation_comparison.json.
"""
from datetime import datetime
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data/extracted/14073311/Active Performance Dataset - 1/Ookla Speedtests/Op1 and Op2 - Italy'
OUTPUT_FILE = ROOT / 'results/diagnostics/session_segmentation_comparison.json'

def clean_numeric(series: pd.Series) -> pd.Series:
    """Convert string series with '?' sentinels to float."""
    return pd.to_numeric(series.replace('?', np.nan), errors='coerce')

def segment_ookla(series: pd.Series, method: str = 'reset', timestamps: pd.Series = None) -> pd.Series:
    """Segment series into sessions using specified method."""
    if method == 'reset':
        is_boundary = (series.diff() < -5.0) & (series < 5.0)
    elif method == 'relative_drop':
        is_boundary = (series.diff() < -2.0) & (series < 1.0)
    elif method == 'active_burst':
        is_active = series > 1.0
        active_start = is_active & (~is_active.shift(1, fill_value=False))
        if timestamps is not None and len(timestamps) == len(series):
            time_diffs = timestamps.diff().dt.total_seconds().fillna(0.0)
            time_gap = time_diffs > 10.0
            is_boundary = active_start | time_gap
        else:
            is_boundary = active_start
    else:
        raise ValueError(f"Unknown method: {method}")
    return is_boundary.cumsum()

def run_segmentation_audit():
    print(f"Scanning directory: {DATA_DIR}")
    csv_files = sorted(list(DATA_DIR.glob('*.csv')))
    print(f"Found {len(csv_files)} trace files to audit.")
    
    file_results = []
    
    strategy_metrics = {
        'threshold_reset': {'durations': [], 'throughputs': [], 'session_counts': []},
        'relative_drop': {'durations': [], 'throughputs': [], 'session_counts': []},
        'active_burst': {'durations': [], 'throughputs': [], 'session_counts': []}
    }
    
    for idx, f in enumerate(csv_files, 1):
        df = pd.read_csv(f, sep=';', low_memory=False)
        df.columns = df.columns.str.strip()
        fname = f.name
        scenario = 'IS' if '_IS_' in fname else ('OD' if '_OD_' in fname else 'OW')
        date_val = df['Day'].iloc[0] if 'Day' in df.columns else '2023-06-16'
        
        time_col = 'Timestamp [dd.mm.yyyy,hh:mm:ss.ss]'
        has_time = time_col in df.columns
        if has_time:
            timestamps = pd.to_datetime(df['Day'] + ' ' + df[time_col], format='%d.%m.%Y %H:%M:%S.%f', errors='coerce')
        else:
            timestamps = None
            
        file_info = {
            'file_id': idx,
            'filename': fname,
            'scenario': scenario,
            'date': str(date_val),
            'total_raw_rows': len(df),
            'operators': {}
        }
        
        for ue_idx, op_label in [(1, 'Op1'), (2, 'Op2')]:
            mean_cols = [c for c in df.columns if 'Mean Netw. DL' in c and f': [{ue_idx}]' in c]
            if not mean_cols:
                continue
            m_col = mean_cols[0]
            scale = 1.0 if '[MBit/s]' in m_col else 0.001
            
            raw_series = df[m_col]
            cleaned_vals = clean_numeric(raw_series) * scale
            valid_mask = cleaned_vals.notna() & (cleaned_vals >= 0.0)
            
            sub_vals = cleaned_vals[valid_mask].astype(float)
            sub_times = timestamps[valid_mask] if timestamps is not None else None
            
            op_stat = {
                'valid_rows': int(len(sub_vals)),
                'non_negative_verified': bool((sub_vals >= 0.0).all()),
                'strategies': {}
            }
            
            if len(sub_vals) > 0:
                for strat_name, method in [('threshold_reset', 'reset'),
                                           ('relative_drop', 'relative_drop'),
                                           ('active_burst', 'active_burst')]:
                    test_ids = segment_ookla(sub_vals, method=method, timestamps=sub_times)
                    n_sessions = int(test_ids.nunique())
                    op_stat['strategies'][strat_name] = {'sessions_detected': n_sessions}
                    strategy_metrics[strat_name]['session_counts'].append(n_sessions)
                    
                    # Compute per-session stats
                    sess_df = pd.DataFrame({'test_id': test_ids, 'val': sub_vals})
                    if sub_times is not None:
                        sess_df['time'] = sub_times
                        for _, grp in sess_df.groupby('test_id'):
                            dur = (grp['time'].iloc[-1] - grp['time'].iloc[0]).total_seconds()
                            strategy_metrics[strat_name]['durations'].append(float(dur))
                            strategy_metrics[strat_name]['throughputs'].append(float(grp['val'].iloc[-1]))
                    else:
                        for _, grp in sess_df.groupby('test_id'):
                            strategy_metrics[strat_name]['throughputs'].append(float(grp['val'].iloc[-1]))
            
            file_info['operators'][op_label] = op_stat
            
        file_results.append(file_info)
        
    # Aggregate summaries across all 43 files
    summary_by_strategy = {}
    for strat, data in strategy_metrics.items():
        s_counts = np.array(data['session_counts']) if data['session_counts'] else np.array([0])
        durs = np.array(data['durations']) if data['durations'] else np.array([0])
        thrs = np.array(data['throughputs']) if data['throughputs'] else np.array([0])
        
        summary_by_strategy[strat] = {
            'total_sessions': int(np.sum(s_counts)),
            'mean_sessions_per_trace': round(float(np.mean(s_counts)), 2),
            'median_sessions_per_trace': round(float(np.median(s_counts)), 2),
            'min_sessions_per_trace': int(np.min(s_counts)),
            'max_sessions_per_trace': int(np.max(s_counts)),
            'duration_stats_seconds': {
                'mean': round(float(np.mean(durs)), 2),
                'median': round(float(np.median(durs)), 2),
                'min': round(float(np.min(durs)), 2),
                'max': round(float(np.max(durs)), 2),
                'iqr': round(float(np.percentile(durs, 75) - np.percentile(durs, 25)), 2)
            },
            'final_throughput_stats_mbps': {
                'mean': round(float(np.mean(thrs)), 2),
                'median': round(float(np.median(thrs)), 2),
                'min': round(float(np.min(thrs)), 2),
                'max': round(float(np.max(thrs)), 2)
            }
        }
        
    # Correlation between threshold_reset and alternatives
    counts_reset = np.array(strategy_metrics['threshold_reset']['session_counts'])
    counts_rel = np.array(strategy_metrics['relative_drop']['session_counts'])
    counts_burst = np.array(strategy_metrics['active_burst']['session_counts'])
    
    corr_reset_rel = float(np.corrcoef(counts_reset, counts_rel)[0, 1]) if len(counts_reset) > 1 else 1.0
    corr_reset_burst = float(np.corrcoef(counts_reset, counts_burst)[0, 1]) if len(counts_reset) > 1 else 1.0
    
    output_payload = {
        'audit_metadata': {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'dataset_id': '14073311',
            'dataset_title': 'Chronicles 2023 Cellular Measurement Campaign',
            'total_files_audited': len(csv_files),
            'geographic_region': 'Rome, Italy',
            'target_operators': ['Op1 (Iliad)', 'Op2 (TIM/Vodafone)'],
            'numeric_prevalidation': 'clean_numeric applied; NaN and negative values strictly filtered prior to segmentation'
        },
        'strategy_definitions': {
            'threshold_reset': {
                'description': 'Speedtest boundary triggered by active download completion: throughput drop < -5.0 Mbps to below 5.0 Mbps ceiling.',
                'role': 'Benchmark Baseline (Primary Protocol)'
            },
            'relative_drop': {
                'description': 'More sensitive reset condition: throughput drop < -2.0 Mbps down to below 1.0 Mbps ceiling.',
                'role': 'Sensitivity Comparison Strategy'
            },
            'active_burst': {
                'description': 'Continuous active download activity > 1.0 Mbps delimited by idle periods exceeding 10.0 seconds.',
                'role': 'Continuous Duty Cycle Alternative'
            }
        },
        'cross_strategy_correlations': {
            'corr_threshold_reset_vs_relative_drop': round(corr_reset_rel, 4),
            'corr_threshold_reset_vs_active_burst': round(corr_reset_burst, 4)
        },
        'aggregate_strategy_summary': summary_by_strategy,
        'per_file_trace_audit': file_results
    }
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_payload, f, indent=2)
    print(f"Segmentation audit saved successfully to: {OUTPUT_FILE}")
    print(f"Summary: Total files: {len(csv_files)}")
    print(f"  Threshold Reset: {summary_by_strategy['threshold_reset']['total_sessions']} sessions")
    print(f"  Relative Drop:   {summary_by_strategy['relative_drop']['total_sessions']} sessions")
    print(f"  Active Burst:    {summary_by_strategy['active_burst']['total_sessions']} sessions")

if __name__ == '__main__':
    run_segmentation_audit()

