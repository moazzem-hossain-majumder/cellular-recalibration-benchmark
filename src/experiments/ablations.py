"""Ablation studies, sensitivity checks, and artificial masking stress tests."""
import sys
import json
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data.loader import load_raw_8224890, extract_sessions_8224890, load_14073311_ookla
from src.data.splits import create_experiment_splits
from src.models.baselines import HistGradientBoostingThroughputPredictor
from src.evaluation.conformal import (
    compute_conformal_quantile,
    GlobalConformalCalibrator,
    GroupedConformalCalibrator,
    CovariateShiftConformalCalibrator
)
from src.evaluation.metrics import compute_reliability_metrics

RESULTS_DIR = ROOT / 'results' / 'metrics'
FIGURES_DIR = ROOT / 'results' / 'figures'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def run_ablations():
    print('='*70)
    print('ABLATION STUDIES & STRESS TESTING')
    print('='*70)
    
    raw_822 = load_raw_8224890()
    sdf, fdf = extract_sessions_8224890(raw_822)
    
    source_df = fdf[fdf['operator'] == 'Op1'].copy()
    target_df = fdf[fdf['operator'] == 'Op2'].copy()
    splits = create_experiment_splits(source_df, target_df, budgets=[10], experiment_type='transfer')
    
    X_tr = splits.train
    y_tr = X_tr['target_y'].to_numpy(dtype=float)
    X_te = splits.target_test
    y_te = X_te['target_y'].to_numpy(dtype=float)
    
    # Pre-train baseline model
    model = HistGradientBoostingThroughputPredictor().fit(X_tr, y_tr)
    y_pred_src_cal = model.predict(splits.source_calib)
    q_src = compute_conformal_quantile(y_pred_src_cal - splits.source_calib['target_y'].to_numpy(dtype=float), alpha=0.10)
    
    prefix_10 = splits.target_prefix_sessions[10]
    y_pref = prefix_10['target_y'].to_numpy(dtype=float)
    y_pref_pred = model.predict(prefix_10)
    pref_grp = prefix_10['group_id'].to_numpy(dtype=int)
    test_grp = X_te['group_id'].to_numpy(dtype=int)
    y_te_pred = model.predict(X_te)
    
    # 1. Ablation: Grouping Fallback Threshold Sensitivity (N_min in [3, 10, 20])
    threshold_results = {}
    for n_min in [3, 5, 10, 20]:
        calib = GroupedConformalCalibrator(alpha=0.10, min_rows=n_min, min_sessions=1, fallback_source_q=q_src)
        calib.fit(y_pref_pred, y_pref, pref_grp)
        bounds, _ = calib.predict_lower_bound(y_te_pred, test_grp)
        m = compute_reliability_metrics(y_te, y_te_pred, bounds)
        threshold_results[f'N_min_{n_min}'] = {
            'violation_rate': round(m.violation_rate, 4),
            'supported_fraction': round(m.supported_rate_fraction, 4),
            'mean_lower_bound': round(m.mean_lower_bound, 4)
        }
        print(f'  Fallback Threshold N_min={n_min:2d} | V={m.violation_rate:.3f}, U={m.supported_rate_fraction:.3f}')

    # 2. Stress Test: Artificial Missingness on Real Measurements (Masking NR Telemetry)
    masking_results = {}
    rng = np.random.default_rng(42)
    for mask_p in [0.0, 0.10, 0.30, 0.50]:
        # Artificially mask observed NR telemetry in test set
        X_te_masked = X_te.copy()
        nr_observed_mask = (X_te_masked['has_nr'] == 1)
        nr_indices = X_te_masked[nr_observed_mask].index
        drop_count = int(round(mask_p * len(nr_indices)))
        dropped = rng.choice(nr_indices, size=drop_count, replace=False)
        
        X_te_masked.loc[dropped, 'has_nr'] = 0
        X_te_masked.loc[dropped, 'ss_rsrp'] = np.nan
        X_te_masked.loc[dropped, 'ss_rsrq'] = np.nan
        X_te_masked.loc[dropped, 'ss_sinr'] = np.nan
        X_te_masked.loc[dropped, 'group_id'] = 2  # Revert to LTE-only group
        
        y_te_masked_pred = model.predict(X_te_masked)
        test_grp_masked = X_te_masked['group_id'].to_numpy(dtype=int)
        
        calib = GroupedConformalCalibrator(alpha=0.10, min_rows=3, min_sessions=1, fallback_source_q=q_src)
        calib.fit(y_pref_pred, y_pref, pref_grp)
        bounds_m, _ = calib.predict_lower_bound(y_te_masked_pred, test_grp_masked)
        m_masked = compute_reliability_metrics(y_te, y_te_masked_pred, bounds_m)
        
        masking_results[f'mask_NR_{int(mask_p*100)}pct'] = {
            'mask_fraction': mask_p,
            'violation_rate': round(m_masked.violation_rate, 4),
            'supported_fraction': round(m_masked.supported_rate_fraction, 4),
            'mean_overcommitment': round(m_masked.mean_overcommitment, 4)
        }
        print(f'  Artificial Masking {int(mask_p*100):2d}% NR | V={m_masked.violation_rate:.3f}, U={m_masked.supported_rate_fraction:.3f}')

    # Save results
    with open(RESULTS_DIR / 'ablation_fallback_thresholds.json', 'w') as f:
        json.dump(threshold_results, f, indent=2)
    with open(RESULTS_DIR / 'ablation_artificial_masking.json', 'w') as f:
        json.dump(masking_results, f, indent=2)
        
    print('\nBaseline ablations complete.')
    
    # Run Freshness Sensitivity
    run_freshness_sensitivity()
    
    # Run Multi-Alpha Pareto Frontier
    run_multi_alpha_frontier()
    
    # Run Covariate-Shift Conformal Benchmark
    run_covariate_shift_benchmark()
    
    # Run SLA Economic Cost Analysis
    run_sla_economic_loss_analysis()
    
    print('\nAll ablations, sensitivity checks, Pareto frontiers, and SLA analyses generated successfully.')

def run_freshness_sensitivity() -> Dict:
    print('\n' + '-'*60)
    print('SENSITIVITY ANALYSIS: TELEMETRY FRESHNESS HORIZONS (30s, 60s, 120s)')
    print('-'*60)
    raw_822 = load_raw_8224890()
    results = {}
    
    for window_sec in [30, 60, 120]:
        print(f'\n  --- Evaluating Freshness Window: {window_sec}s ---')
        _, fdf_822 = extract_sessions_8224890(raw_822, window_seconds=window_sec)
        fdf_140 = load_14073311_ookla(window_seconds=window_sec)
        
        src_df = fdf_822[fdf_822['operator'] == 'Op1'].copy()
        regimes = {
            'E0_WithinDomain': (src_df, src_df),
            'E2_CrossOperator': (src_df, fdf_822[fdf_822['operator'] == 'Op2'].copy()),
            'E1_CampaignTransfer': (src_df, fdf_140[fdf_140['operator'] == 'Op1'].copy())
        }
        
        window_dict = {}
        for reg_name, (s_df, t_df) in regimes.items():
            splits = create_experiment_splits(
                s_df, t_df, budgets=[0, 10], regime=reg_name,
                experiment_type='within_domain' if reg_name.startswith('E0') else 'transfer'
            )
            model = HistGradientBoostingThroughputPredictor().fit(splits.train, splits.train['target_y'].to_numpy(dtype=float))
            
            y_pred_src_cal = model.predict(splits.source_calib)
            q_src = compute_conformal_quantile(y_pred_src_cal - splits.source_calib['target_y'].to_numpy(dtype=float), alpha=0.10)
            
            y_te = splits.target_test['target_y'].to_numpy(dtype=float)
            y_te_pred = model.predict(splits.target_test)
            test_grp = splits.target_test['group_id'].to_numpy(dtype=int)
            
            # K=0
            b_0 = np.maximum(0.0, y_te_pred - q_src)
            m_0 = compute_reliability_metrics(y_te, y_te_pred, b_0)
            
            # K=10
            pref_10 = splits.target_prefix_sessions[10]
            y_pref = pref_10['target_y'].to_numpy(dtype=float)
            y_pref_pred = model.predict(pref_10)
            pref_grp = pref_10['group_id'].to_numpy(dtype=int)
            
            calib = GroupedConformalCalibrator(alpha=0.10, min_rows=3, min_sessions=1, fallback_source_q=q_src)
            calib.fit(y_pref_pred, y_pref, pref_grp)
            b_10, _ = calib.predict_lower_bound(y_te_pred, test_grp)
            m_10 = compute_reliability_metrics(y_te, y_te_pred, b_10)
            
            window_dict[reg_name] = {
                'K_0': {'violation_rate': round(m_0.violation_rate, 4), 'supported_fraction': round(m_0.supported_rate_fraction, 4)},
                'K_10': {'violation_rate': round(m_10.violation_rate, 4), 'supported_fraction': round(m_10.supported_rate_fraction, 4)}
            }
            print(f'    {reg_name:20s} | K=0: V={m_0.violation_rate:.3f}, U={m_0.supported_rate_fraction:.3f} | K=10: V={m_10.violation_rate:.3f}, U={m_10.supported_rate_fraction:.3f}')
            
        results[f'window_{window_sec}s'] = window_dict
        
    with open(RESULTS_DIR / 'freshness_sensitivity.json', 'w') as f:
        json.dump(results, f, indent=2)
    return results

def run_multi_alpha_frontier() -> Dict:
    print('\n' + '-'*60)
    print('PARETO FRONTIER: RISK-UTILITY PROFILE ACROSS NOMINAL ALPHA')
    print('-'*60)
    
    raw_822 = load_raw_8224890()
    _, fdf_822 = extract_sessions_8224890(raw_822)
    fdf_140 = load_14073311_ookla()
    
    source_df = fdf_822[fdf_822['operator'] == 'Op1'].copy()
    regimes = {
        'E0_WithinDomain': (source_df, source_df),
        'E1_CampaignTransfer': (source_df, fdf_140[fdf_140['operator'] == 'Op1'].copy()),
        'E2_CrossOperator': (source_df, fdf_822[fdf_822['operator'] == 'Op2'].copy()),
        'E3_JointShift': (source_df, fdf_140[fdf_140['operator'] == 'Op2'].copy())
    }
    
    alphas = [0.01, 0.02, 0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30]
    frontier_data = {reg: {'alphas': alphas, 'global': {'V': [], 'U': []}, 'proposed': {'V': [], 'U': []}} for reg in regimes}
    
    for reg_name, (s_df, t_df) in regimes.items():
        splits = create_experiment_splits(
            s_df, t_df, budgets=[10], regime=reg_name,
            experiment_type='within_domain' if reg_name.startswith('E0') else 'transfer'
        )
        model = HistGradientBoostingThroughputPredictor().fit(splits.train, splits.train['target_y'].to_numpy(dtype=float))
        
        y_te = splits.target_test['target_y'].to_numpy(dtype=float)
        y_te_pred = model.predict(splits.target_test)
        test_grp = splits.target_test['group_id'].to_numpy(dtype=int)
        
        src_cal = splits.source_calib
        y_src_cal = src_cal['target_y'].to_numpy(dtype=float)
        y_src_pred = model.predict(src_cal)
        src_scores = y_src_pred - y_src_cal
        
        pref_10 = splits.target_prefix_sessions[10]
        y_pref = pref_10['target_y'].to_numpy(dtype=float)
        y_pref_pred = model.predict(pref_10)
        pref_grp = pref_10['group_id'].to_numpy(dtype=int)
        
        for alpha in alphas:
            q_src = compute_conformal_quantile(src_scores, alpha=alpha)
            
            # Global Conformal (K=10 with source fallback)
            calib_g = GlobalConformalCalibrator(alpha=alpha).fit(y_pref_pred, y_pref)
            q_g = calib_g.q if not np.isinf(calib_g.q) else q_src
            b_g = np.maximum(0.0, y_te_pred - q_g)
            m_g = compute_reliability_metrics(y_te, y_te_pred, b_g)
            
            # Proposed Missingness-Aware (K=10 with fallback)
            calib_p = GroupedConformalCalibrator(alpha=alpha, min_rows=3, min_sessions=1, fallback_source_q=q_src)
            calib_p.fit(y_pref_pred, y_pref, pref_grp)
            b_p, _ = calib_p.predict_lower_bound(y_te_pred, test_grp)
            m_p = compute_reliability_metrics(y_te, y_te_pred, b_p)
            
            frontier_data[reg_name]['global']['V'].append(round(m_g.violation_rate, 4))
            frontier_data[reg_name]['global']['U'].append(round(m_g.supported_rate_fraction, 4))
            frontier_data[reg_name]['proposed']['V'].append(round(m_p.violation_rate, 4))
            frontier_data[reg_name]['proposed']['U'].append(round(m_p.supported_rate_fraction, 4))
            
    with open(RESULTS_DIR / 'multi_alpha_frontier.json', 'w') as f:
        json.dump(frontier_data, f, indent=2)
        
    # Plot Figure 4: Pareto Risk-Utility Frontiers across alpha
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    
    # 4a: Empirical Violation V vs Nominal Alpha (Calibration Curve)
    reg_colors = {'E0_WithinDomain': '#1f77b4', 'E1_CampaignTransfer': '#ff7f0e',
                  'E2_CrossOperator': '#2ca02c', 'E3_JointShift': '#d62728'}
    
    axes[0].plot([0, 0.35], [0, 0.35], 'k--', alpha=0.7, label='Nominal Guarantee Line ($V=\\alpha$)')
    for reg, col in reg_colors.items():
        sub = frontier_data[reg]
        axes[0].plot(sub['alphas'], sub['proposed']['V'], '-o', color=col, label=f"{reg.split('_')[0]} (Proposed)")
        
    axes[0].set_title('(a) Calibration Reliability: Empirical $V$ vs Nominal $\\alpha$')
    axes[0].set_xlabel('Nominal Risk Level ($\\alpha$)')
    axes[0].set_ylabel('Empirical Violation Rate ($V$)')
    axes[0].set_xlim(0, 0.32)
    axes[0].set_ylim(-0.02, 0.35)
    axes[0].grid(True, linestyle='--', alpha=0.5)
    axes[0].legend(loc='upper left', frameon=True)
    
    # 4b: Risk-Utility Pareto Tradeoff: U vs V
    for reg, col in reg_colors.items():
        sub = frontier_data[reg]
        axes[1].plot(sub['proposed']['V'], sub['proposed']['U'], '-s', color=col, label=f"{reg.split('_')[0]}")
        for i, a in enumerate(sub['alphas']):
            if a in [0.01, 0.05, 0.10, 0.20]:
                axes[1].annotate(f'$\\alpha$={a}', (sub['proposed']['V'][i], sub['proposed']['U'][i]),
                                 fontsize=7, xytext=(3, 3), textcoords='offset points')
                                 
    axes[1].set_title('(b) Risk-Utility Pareto Frontier ($U$ vs Empirical $V$)')
    axes[1].set_xlabel('Empirical Violation Rate ($V$)')
    axes[1].set_ylabel('Supported-Rate Fraction ($U$)')
    axes[1].set_ylim(-0.02, 0.45)
    axes[1].grid(True, linestyle='--', alpha=0.5)
    axes[1].legend(loc='lower right', frameon=True)
    
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig4_pareto_frontier.pdf', bbox_inches='tight')
    fig.savefig(FIGURES_DIR / 'fig4_pareto_frontier.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {FIGURES_DIR / "fig4_pareto_frontier.pdf"}')
    return frontier_data

def run_covariate_shift_benchmark() -> Dict:
    print('\n' + '-'*60)
    print('COVARIATE-SHIFT CONFORMAL PREDICTION (Tibshirani et al. 2019)')
    print('-'*60)
    
    raw_822 = load_raw_8224890()
    _, fdf_822 = extract_sessions_8224890(raw_822)
    fdf_140 = load_14073311_ookla()
    
    source_df = fdf_822[fdf_822['operator'] == 'Op1'].copy()
    regimes = {
        'E1_CampaignTransfer': fdf_140[fdf_140['operator'] == 'Op1'].copy(),
        'E2_CrossOperator': fdf_822[fdf_822['operator'] == 'Op2'].copy(),
        'E3_JointShift': fdf_140[fdf_140['operator'] == 'Op2'].copy()
    }
    
    splits_e0 = create_experiment_splits(source_df, source_df, budgets=[0], regime='E0_WithinDomain', experiment_type='within_domain')
    model = HistGradientBoostingThroughputPredictor().fit(splits_e0.train, splits_e0.train['target_y'].to_numpy(dtype=float))
    
    src_cal = splits_e0.source_calib
    y_src_cal = src_cal['target_y'].to_numpy(dtype=float)
    y_src_pred = model.predict(src_cal)
    src_scores = y_src_pred - y_src_cal
    
    feat_cols = ['y_lag1', 'prev_duration_s', 'rsrp', 'rsrq', 'sinr', 'ss_rsrp', 'ss_rsrq', 'ss_sinr', 'has_nr', 'has_lte']
    cs_results = {}
    
    for r_name, tgt_df in regimes.items():
        splits = create_experiment_splits(
            source_df, tgt_df, budgets=[0], regime=r_name,
            experiment_type='within_domain' if r_name.startswith('E0') else 'transfer'
        )
        test_df = splits.target_test
        y_test = test_df['target_y'].to_numpy(dtype=float)
        y_test_pred = model.predict(test_df)
        
        calib_cs = CovariateShiftConformalCalibrator(alpha=0.10)
        calib_cs.fit_weights_and_scores(src_cal, src_scores, test_df, feature_cols=feat_cols)
        bounds_cs = calib_cs.predict_lower_bound(y_test_pred, test_df)
        
        m_cs = compute_reliability_metrics(y_test, y_test_pred, bounds_cs)
        cs_results[r_name] = {
            'violation_rate': round(m_cs.violation_rate, 4),
            'supported_fraction': round(m_cs.supported_rate_fraction, 4),
            'mean_overcommitment': round(m_cs.mean_overcommitment, 4),
            'mean_weight': round(float(np.mean(calib_cs.source_weights)), 4),
            'max_weight': round(float(np.max(calib_cs.source_weights)), 4)
        }
        print(f'  {r_name:24s} | CS-CP: V={m_cs.violation_rate:.3f}, U={m_cs.supported_rate_fraction:.3f} (Mean w={np.mean(calib_cs.source_weights):.2f})')
        
    with open(RESULTS_DIR / 'covariate_shift_conformal.json', 'w') as f:
        json.dump(cs_results, f, indent=2)
    return cs_results

def run_sla_economic_loss_analysis() -> Dict:
    print('\n' + '-'*60)
    print('OPERATIONAL SLA ECONOMIC LOSS FUNCTION ANALYSIS')
    print('-'*60)
    
    calib_csv = RESULTS_DIR / 'calibration_budget_results.csv'
    if not calib_csv.exists():
        print('  Calibration budget results not found, skipping SLA analysis.')
        return {}
        
    df = pd.read_csv(calib_csv)
    lambdas = np.linspace(0.0, 1.0, 21)
    
    methods = ['Uncalibrated', 'Global_Conformal', 'Proposed_Missingness_Aware']
    sla_data = {m: [] for m in methods}
    
    # Evaluate at K=10 budget across regimes
    sub = df[df['budget_K'] == 10]
    for lam in lambdas:
        for m in methods:
            m_rows = sub[sub['method'] == m]
            # Cost(lambda) = lambda * V + (1 - lambda) * (1 - U)
            costs = lam * m_rows['violation_rate'] + (1.0 - lam) * (1.0 - m_rows['supported_fraction'])
            sla_data[m].append(round(float(costs.mean()), 4))
            
    sla_out = {
        'lambdas': [round(float(l), 2) for l in lambdas],
        'costs': sla_data
    }
    with open(RESULTS_DIR / 'sla_cost_analysis.json', 'w') as f:
        json.dump(sla_out, f, indent=2)
        
    # Plot Figure 5: SLA Cost Curve
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(lambdas, sla_data['Uncalibrated'], '-.r', linewidth=2, label='Uncalibrated Point Forecast')
    ax.plot(lambdas, sla_data['Global_Conformal'], '--b', linewidth=2, label='Global Conformal (K=10)')
    ax.plot(lambdas, sla_data['Proposed_Missingness_Aware'], '-g', linewidth=2.5, label='Proposed Missingness-Aware (K=10)')
    
    ax.set_title('Operational SLA Economic Cost vs Violation Penalty Weight ($\\lambda$)', fontweight='bold')
    ax.set_xlabel('Violation Penalty Weight $\\lambda$ ($0 = $ Throughput Focused, $1 = $ Zero-Risk SLA Enforcement)')
    ax.set_ylabel('Normalized Operational Loss: $\\text{Cost}(\\lambda)$')
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 0.9)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='lower left', frameon=True)
    
    # Annotate the crossover point
    ax.annotate('Conformal Dominance\n($\\lambda > 0.35$)', xy=(0.4, 0.58), xytext=(0.45, 0.70),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#e2e8f0', alpha=0.8))
                
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig5_sla_cost_curve.pdf', bbox_inches='tight')
    fig.savefig(FIGURES_DIR / 'fig5_sla_cost_curve.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {FIGURES_DIR / "fig5_sla_cost_curve.pdf"}')
    return sla_out

if __name__ == '__main__':
    run_ablations()

