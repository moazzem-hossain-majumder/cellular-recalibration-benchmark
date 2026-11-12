"""Audit data quality, schemas, and missingness across both Zenodo datasets."""
from datetime import datetime, timezone
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from src.data.loader import load_raw_8224890, extract_sessions_8224890, load_14073311_ookla

def run_audit():
    print("Loading Zenodo 8224890...")
    raw_822 = load_raw_8224890()
    sdf_822, fdf_822 = extract_sessions_8224890(raw_822)
    print("Loading Zenodo 14073311...")
    fdf_140 = load_14073311_ookla()

    def audit_df(df, name):
        report = {
            'name': name,
            'total_rows': len(df),
            'unique_dates': int(df['date'].nunique()),
            'date_list': sorted([str(d) for d in df['date'].unique()]),
            'operators': {k: int(v) for k, v in df['operator'].value_counts().items()},
            'missingness': {},
            'throughput_stats': {
                'mean': float(df['target_y'].mean()),
                'std': float(df['target_y'].std()),
                'min': float(df['target_y'].min()),
                'p10': float(df['target_y'].quantile(0.10)),
                'p25': float(df['target_y'].quantile(0.25)),
                'median': float(df['target_y'].median()),
                'p75': float(df['target_y'].quantile(0.75)),
                'p90': float(df['target_y'].quantile(0.90)),
                'max': float(df['target_y'].max()),
                'zeros_count': int((df['target_y'] == 0.0).sum()),
                'sub_1mbps_count': int((df['target_y'] < 1.0).sum()),
            },
            'freshness_stats': {
                'mean_lag_age_s': float(df['lag_age_s'].mean()),
                'median_lag_age_s': float(df['lag_age_s'].median()),
                'min_lag_age_s': float(df['lag_age_s'].min()),
                'max_lag_age_s': float(df['lag_age_s'].max()),
            },
            'telemetry_groups': {str(k): int(v) for k, v in df['group_id'].value_counts().items()} if 'group_id' in df else {}
        }
        for col in df.columns:
            null_cnt = int(df[col].isna().sum())
            report['missingness'][col] = {
                'null_count': null_cnt,
                'null_pct': float(round(100.0 * null_cnt / len(df), 2))
            }
        return report

    rep_822 = audit_df(fdf_822, 'Zenodo_8224890_2021')
    rep_140 = audit_df(fdf_140, 'Zenodo_14073311_2023')

    full_report = {
        'audit_timestamp': datetime.now(timezone.utc).isoformat(),
        'total_causal_forecast_instances': len(fdf_822) + len(fdf_140),
        'datasets': {
            '8224890': rep_822,
            '14073311': rep_140
        }
    }

    out_path = Path('results/diagnostics/data_quality_audit.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=2)

    print("Saved data_quality_audit.json successfully!")
    print(f"Total instances: {full_report['total_causal_forecast_instances']}")
    print(f"8224890 dates: {len(rep_822['date_list'])}, instances: {rep_822['total_rows']}")
    print(f"14073311 dates: {len(rep_140['date_list'])}, instances: {rep_140['total_rows']}")

if __name__ == '__main__':
    run_audit()
