"""Interactive Demonstration CLI for Cellular Throughput Forecasting and Conformal Recalibration."""
import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.loader import load_raw_8224890, extract_sessions_8224890, load_14073311_ookla
from src.data.splits import create_experiment_splits
from src.models.baselines import HistGradientBoostingThroughputPredictor
from src.evaluation.conformal import compute_conformal_quantile, GroupedConformalCalibrator
from src.evaluation.metrics import compute_reliability_metrics

def run_interactive_demo():
    print('='*75)
    print('CELLULAR THROUGHPUT PREDICTION & CONFORMAL RECALIBRATION DEMO')
    print('='*75)
    
    print('Loading datasets...')
    raw_822 = load_raw_8224890()
    sdf_822, fdf_822 = extract_sessions_8224890(raw_822)
    fdf_140 = load_14073311_ookla()
    
    source_df = fdf_822[fdf_822['operator'] == 'Op1'].copy()
    target_df = fdf_822[fdf_822['operator'] == 'Op2'].copy()
    
    print('Fitting primary predictor on source training split (Op1 2021)...')
    splits = create_experiment_splits(source_df, target_df, budgets=[10])
    model = HistGradientBoostingThroughputPredictor().fit(
        splits.train, splits.train['target_y'].to_numpy(dtype=float)
    )
    
    # Pre-compute source quantile
    src_preds = model.predict(splits.source_calib)
    q_src = compute_conformal_quantile(
        src_preds - splits.source_calib['target_y'].to_numpy(dtype=float), alpha=0.10
    )
    
    # Target prefix K=10
    prefix_10 = splits.target_prefix_sessions[10]
    y_pref = prefix_10['target_y'].to_numpy(dtype=float)
    y_pref_pred = model.predict(prefix_10)
    pref_grp = prefix_10['group_id'].to_numpy(dtype=int)
    
    calib = GroupedConformalCalibrator(alpha=0.10, min_rows=3, min_sessions=1, fallback_source_q=q_src)
    calib.fit(y_pref_pred, y_pref, pref_grp)
    
    test_df = splits.target_test.reset_index(drop=True)
    test_preds = model.predict(test_df)
    test_groups = test_df['group_id'].to_numpy(dtype=int)
    lower_bounds, _ = calib.predict_lower_bound(test_preds, test_groups)
    
    print('\nDemo Ready: Simulating 10 consecutive test sessions in Target Domain (Op2 2021)...')
    print('-'*75)
    print(f'{"Session":<8} | {"Lag (Mbps)":<10} | {"LTE RSRP":<9} | {"NR SS-RSRP":<11} | {"Pred (Mbps)":<11} | {"Lower Bound":<11} | {"Actual":<8} | {"Status":<10}')
    print('-'*75)
    
    for i in range(min(10, len(test_df))):
        row = test_df.iloc[i]
        lag = f"{row['y_lag1']:.1f}"
        rsrp = f"{row['rsrp']:.0f} dBm" if pd.notna(row['rsrp']) else "Missing"
        ss_rsrp = f"{row['ss_rsrp']:.0f} dBm" if pd.notna(row['ss_rsrp']) else "Missing (4G)"
        pred = f"{test_preds[i]:.1f}"
        lb = f"{lower_bounds[i]:.1f}"
        act = f"{row['target_y']:.1f}"
        violated = row['target_y'] < lower_bounds[i]
        status = "VIOLATION" if violated else "SAFE"
        
        print(f"#{i+1:<7} | {lag:<10} | {rsrp:<9} | {ss_rsrp:<11} | {pred:<11} | {lb:<11} | {act:<8} | {status:<10}")
        
    print('-'*75)
    print('Key observation:')
    print('  - Notice how sessions with "Missing (4G)" NR SS-RSRP naturally receive more conservative lower bounds.')
    print('  - Even when point predictions are high, the lower bound safeguards against overcommitment.')
    print('='*75)

if __name__ == '__main__':
    run_interactive_demo()

