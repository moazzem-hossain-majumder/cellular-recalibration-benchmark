"""Comprehensive experimental runner for cellular throughput transfer, calibration budgets, and ablations."""
import os
import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.data.loader import load_raw_8224890, extract_sessions_8224890, load_14073311_ookla
from src.data.splits import create_experiment_splits, DomainSplits, generate_split_summary
from src.features.builder import prepare_feature_dataframe
from src.models.baselines import (
    PersistencePredictor,
    RidgeThroughputPredictor,
    HistGradientBoostingThroughputPredictor,
    QuantileBoostingPredictor
)
from src.models.bammo import BAMMOThroughputPredictor
from src.models.neural import GPUThroughputNeuralPredictor
from src.evaluation.conformal import (
    compute_conformal_quantile,
    GlobalConformalCalibrator,
    GroupedConformalCalibrator,
    AdaptiveConformalCalibrator
)
from src.evaluation.metrics import (
    compute_reliability_metrics,
    compute_subgroup_metrics,
    paired_day_cluster_bootstrap,
    ReliabilityMetrics
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / 'results'
FIGURES_DIR = RESULTS_DIR / 'figures'
TABLES_DIR = RESULTS_DIR / 'tables'
METRICS_DIR = RESULTS_DIR / 'metrics'
DIAGNOSTICS_DIR = RESULTS_DIR / 'diagnostics'

for d in [FIGURES_DIR, TABLES_DIR, METRICS_DIR, DIAGNOSTICS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Set publication style for matplotlib
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 13

def run_all_experiments() -> Dict:
    print('='*70)
    print('TELECOMMUNICATIONS RESEARCH BENCHMARK: EXECUTION PIPELINE')
    print('='*70)
    
    # 1. Load both dataset families
    print('\n[1/6] Loading verified commercial measurement datasets...')
    raw_822 = load_raw_8224890()
    sdf_822, fdf_822 = extract_sessions_8224890(raw_822)
    fdf_140 = load_14073311_ookla()
    
    print(f'  2021 Campaign (8224890): {len(fdf_822)} forecast instances')
    print(f'    Op1: {(fdf_822["operator"] == "Op1").sum()} | Op2: {(fdf_822["operator"] == "Op2").sum()}')
    print(f'  2023 Campaign (14073311): {len(fdf_140)} forecast instances')
    print(f'    Op1: {(fdf_140["operator"] == "Op1").sum()} | Op2: {(fdf_140["operator"] == "Op2").sum()}')
    
    # 2. Build Experimental Regimes
    # Source is always Op1 2021 (earliest commercial deployment)
    source_df = fdf_822[fdf_822['operator'] == 'Op1'].copy()
    
    regimes = {
        'E0_WithinDomain_Op1_2021': (source_df, source_df),
        'E1_CampaignTransfer_Op1_2023': (source_df, fdf_140[fdf_140['operator'] == 'Op1'].copy()),
        'E2_CrossOperator_Op2_2021': (source_df, fdf_822[fdf_822['operator'] == 'Op2'].copy()),
        'E3_JointShift_Op2_2023': (source_df, fdf_140[fdf_140['operator'] == 'Op2'].copy())
    }
    
    budgets = [0, 1, 2, 5, 8, 9, 10, 15]
    results_all = {}
    
    # 3. Model Benchmark on Source Development Split
    print('\n[2/6] Training & Profiling Point Predictors on Source (including RTX 4060 GPU)...')
    e0_splits = create_experiment_splits(source_df, source_df, budgets=budgets, regime='E0_WithinDomain_Op1_2021', experiment_type='within_domain')
    X_train, y_train = e0_splits.train, e0_splits.train['target_y'].to_numpy(dtype=float)
    X_val, y_val = e0_splits.val, e0_splits.val['target_y'].to_numpy(dtype=float)
    
    models = {
        'Persistence': PersistencePredictor(),
        'Ridge': RidgeThroughputPredictor(alpha=10.0),
        'HistGradientBoosting': HistGradientBoostingThroughputPredictor(max_iter=100, learning_rate=0.05),
        'BAMMO': BAMMOThroughputPredictor(n_stages=80, learning_rate=0.05),
        'QuantileGBM_p10': QuantileBoostingPredictor(alpha=0.10, n_estimators=80, learning_rate=0.05),
        'GPU_ThroughputResNet': GPUThroughputNeuralPredictor(hidden_dim=256, num_blocks=3, epochs=60, batch_size=32)
    }
    
    model_profiles = {}
    for name, model in models.items():
        t0 = time.time()
        if name == 'GPU_ThroughputResNet':
            model.fit(X_train, y_train, X_val, y_val)
            fit_time = model.profiling_info['train_time_seconds']
        else:
            model.fit(X_train, y_train)
            fit_time = time.time() - t0
            
        preds_val = model.predict(X_val)
        val_mae = float(np.mean(np.abs(preds_val - y_val)))
        val_rmse = float(np.sqrt(np.mean((preds_val - y_val)**2)))
        
        model_profiles[name] = {
            'fit_time_seconds': round(fit_time, 4),
            'val_mae': round(val_mae, 4),
            'val_rmse': round(val_rmse, 4)
        }
        if name == 'GPU_ThroughputResNet':
            model_profiles[name].update(model.profiling_info)
        print(f'  {name:22s} | Fit time: {fit_time:.3f}s | Val MAE: {val_mae:.2f} Mbps | Val RMSE: {val_rmse:.2f} Mbps')

    with open(METRICS_DIR / 'point_predictor_profiles.json', 'w') as f:
        json.dump(model_profiles, f, indent=2)

    # We select HistGradientBoosting as the primary common predictor for core calibration experiments
    primary_predictor = models['HistGradientBoosting']
    primary_predictor.fit(X_train, y_train)
    
    # Pre-compute source calibration scores
    X_src_calib = e0_splits.source_calib
    y_src_calib = X_src_calib['target_y'].to_numpy(dtype=float)
    y_src_pred = primary_predictor.predict(X_src_calib)
    source_calib_scores = y_src_pred - y_src_calib
    source_global_q = compute_conformal_quantile(source_calib_scores, alpha=0.10)
    print(f'  Frozen Source Global Conformal Quantile (alpha=0.10): q_source = {source_global_q:.3f} Mbps')

    # 4. Multi-Domain Transfer & Calibration Budget Experiments
    print('\n[3/6] Running Transfer Regimes across Budgets K in {0, 1, 2, 5, 8, 9, 10, 15}...')
    calibration_records = []
    forecast_blocks = []
    
    for regime_name, (src_d, tgt_d) in regimes.items():
        print(f'\n  --- Evaluating Regime: {regime_name} ---')
        splits = create_experiment_splits(
            src_d, tgt_d, budgets=budgets, regime=regime_name,
            experiment_type='within_domain' if regime_name.startswith('E0') else 'transfer'
        )
        splits.train, splits.val, splits.source_calib = e0_splits.train, e0_splits.val, e0_splits.source_calib
        generate_split_summary(splits, regime_name, "8224890_to_14073311", output_path=DIAGNOSTICS_DIR / 'split_summary.json')
        df_test = splits.target_test
        y_test = df_test['target_y'].to_numpy(dtype=float)
        test_groups = df_test['group_id'].to_numpy(dtype=int)
        
        # Point predictions on fixed test suffix
        y_test_pred = primary_predictor.predict(df_test)
        
        for k in budgets:
            prefix_df = splits.target_prefix_sessions[k]
            if prefix_df is None:
                print(f'    K={k:2d} | UNAVAILABLE: calibration pool has fewer than K sessions; not substituting a smaller prefix.')
                continue
            y_prefix = prefix_df['target_y'].to_numpy(dtype=float) if k > 0 else np.array([])
            prefix_groups = prefix_df['group_id'].to_numpy(dtype=int) if k > 0 else np.array([])
            prefix_sessions = prefix_df['session_id'].to_numpy(dtype=int) if (k > 0 and 'session_id' in prefix_df.columns) else np.arange(k)
            y_prefix_pred = primary_predictor.predict(prefix_df) if k > 0 else np.array([])
            
            # --- Method 1: Uncalibrated Point Baseline ---
            bounds_uncal = np.maximum(0.0, y_test_pred)
            m_uncal = compute_reliability_metrics(y_test, y_test_pred, bounds_uncal)
            
            # --- Method 2: Global Conformal Recalibration ---
            if k == 0:
                # Source-only global conformal
                bounds_global = np.maximum(0.0, y_test_pred - source_global_q)
            else:
                calib_global = GlobalConformalCalibrator(alpha=0.10)
                calib_global.fit(y_prefix_pred, y_prefix)
                # If target prefix is too small, fallback to source quantile
                q_used = calib_global.q if not np.isinf(calib_global.q) else source_global_q
                bounds_global = np.maximum(0.0, y_test_pred - q_used)
            m_global = compute_reliability_metrics(y_test, y_test_pred, bounds_global)
            
            # --- Method 3: Proposed Coarse Missingness-Aware Calibration ---
            if k == 0:
                bounds_missing = bounds_global
            else:
                calib_grp = GroupedConformalCalibrator(
                    alpha=0.10, min_rows=3, min_sessions=1, fallback_source_q=source_global_q
                )
                calib_grp.fit(y_prefix_pred, y_prefix, prefix_groups, prefix_sessions)
                bounds_missing, _ = calib_grp.predict_lower_bound(y_test_pred, test_groups)
            m_missing = compute_reliability_metrics(y_test, y_test_pred, bounds_missing)
            
            # --- Method 4: RAT-Grouped Calibration ---
            # Group by RAT (has_nr = 1 for 5G, 0 for LTE)
            if k == 0:
                bounds_rat = bounds_global
            else:
                calib_rat = GroupedConformalCalibrator(
                    alpha=0.10, min_rows=3, min_sessions=1, fallback_source_q=source_global_q
                )
                prefix_rat = prefix_df['has_nr'].to_numpy(dtype=int) if k > 0 else np.array([])
                test_rat = df_test['has_nr'].to_numpy(dtype=int)
                calib_rat.fit(y_prefix_pred, y_prefix, prefix_rat, prefix_sessions)
                bounds_rat, _ = calib_rat.predict_lower_bound(y_test_pred, test_rat)
            m_rat = compute_reliability_metrics(y_test, y_test_pred, bounds_rat)

            forecast_blocks.append(pd.DataFrame({
                'regime': regime_name, 'budget_K': k, 'session_id': df_test['session_id'],
                'date': df_test['date'], 'group_id': test_groups, 'target': y_test,
                'Uncalibrated': bounds_uncal, 'Global_Conformal': bounds_global,
                'RAT_Grouped': bounds_rat, 'Proposed_Missingness_Aware': bounds_missing
            }))

            # Subgroup metrics for proposed missingness method
            sub_missing = compute_subgroup_metrics(y_test, y_test_pred, bounds_missing, test_groups)

            # Record metrics
            for m_name, m_obj in [('Uncalibrated', m_uncal), ('Global_Conformal', m_global),
                                  ('RAT_Grouped', m_rat), ('Proposed_Missingness_Aware', m_missing)]:
                rec = {
                    'regime': regime_name,
                    'budget_K': k,
                    'method': m_name,
                    'violation_rate': m_obj.violation_rate,
                    'supported_fraction': m_obj.supported_rate_fraction,
                    'mean_lower_bound': m_obj.mean_lower_bound,
                    'zero_bound_fraction': m_obj.zero_bound_fraction,
                    'mean_overcommitment': m_obj.mean_overcommitment,
                    'test_samples': m_obj.sample_count
                }
                if m_name == 'Proposed_Missingness_Aware':
                    rec['subgroup_V_LTE_only'] = sub_missing.get(2, ReliabilityMetrics(0,0,0,0,0,0,0,0)).violation_rate
                    rec['subgroup_V_Dual_NR'] = sub_missing.get(3, ReliabilityMetrics(0,0,0,0,0,0,0,0)).violation_rate
                    rec['subgroup_U_LTE_only'] = sub_missing.get(2, ReliabilityMetrics(0,0,0,0,0,0,0,0)).supported_rate_fraction
                    rec['subgroup_U_Dual_NR'] = sub_missing.get(3, ReliabilityMetrics(0,0,0,0,0,0,0,0)).supported_rate_fraction
                calibration_records.append(rec)

            print(f'    K={k:2d} | Global: V={m_global.violation_rate:.3f}, U={m_global.supported_rate_fraction:.3f} | '
                  f'Proposed: V={m_missing.violation_rate:.3f}, U={m_missing.supported_rate_fraction:.3f}')

    pd.concat(forecast_blocks).to_csv(DIAGNOSTICS_DIR / 'test_forecasts.csv', index=False)
    calib_df = pd.DataFrame(calibration_records)
    calib_df.to_csv(METRICS_DIR / 'calibration_budget_results.csv', index=False)
    
    # 5. Bootstrap Hypothesis Testing (RQ1–RQ4)
    print('\n[4/6] Running Paired Day-Cluster Bootstrap Resampling (2,000 Replicates)...')
    bootstrap_results = {}
    for regime_name in regimes.keys():
        sub_e = calib_df[(calib_df['regime'] == regime_name) & (calib_df['budget_K'] == 10)]
        splits = create_experiment_splits(
            regimes[regime_name][0], regimes[regime_name][1], budgets=[10], regime=regime_name,
            experiment_type='within_domain' if regime_name.startswith('E0') else 'transfer'
        )
        df_test = splits.target_test
        y_test = df_test['target_y'].to_numpy(dtype=float)
        test_groups = df_test['group_id'].to_numpy(dtype=int)
        y_test_pred = primary_predictor.predict(df_test)
        
        # Bootstrap comparison is defined only when a full K=10 prefix exists.
        prefix_10 = splits.target_prefix_sessions[10]
        if prefix_10 is None:
            bootstrap_results[regime_name] = {'status': 'unavailable', 'reason': 'fewer than 10 target calibration sessions'}
            print(f'  {regime_name:30s} | Bootstrap comparison unavailable: fewer than 10 target calibration sessions')
            continue
        y_pref = prefix_10['target_y'].to_numpy(dtype=float)
        pref_grp = prefix_10['group_id'].to_numpy(dtype=int)
        pref_sess = prefix_10['session_id'].to_numpy(dtype=int) if 'session_id' in prefix_10.columns else np.arange(len(prefix_10))
        y_pref_pred = primary_predictor.predict(prefix_10)
        
        c_glob = GlobalConformalCalibrator(alpha=0.10).fit(y_pref_pred, y_pref)
        q_g = c_glob.q if not np.isinf(c_glob.q) else source_global_q
        b_glob = np.maximum(0.0, y_test_pred - q_g)
        
        c_grp = GroupedConformalCalibrator(alpha=0.10, min_rows=3, min_sessions=1, fallback_source_q=source_global_q)
        c_grp.fit(y_pref_pred, y_pref, pref_grp, pref_sess)
        b_prop, _ = c_grp.predict_lower_bound(y_test_pred, test_groups)
        
        boot_diff = paired_day_cluster_bootstrap(df_test, y_test, b_glob, b_prop, n_boot=2000, random_seed=42)
        bootstrap_results[regime_name] = {
            'delta_V': {'point': round(boot_diff['delta_violation_rate'][0], 4),
                        'ci_95': [round(boot_diff['delta_violation_rate'][1], 4), round(boot_diff['delta_violation_rate'][2], 4)]},
            'delta_U': {'point': round(boot_diff['delta_supported_fraction'][0], 4),
                        'ci_95': [round(boot_diff['delta_supported_fraction'][1], 4), round(boot_diff['delta_supported_fraction'][2], 4)]}
        }
        print(f'  {regime_name:30s} | Delta U: {boot_diff["delta_supported_fraction"][0]:+.3f} '
              f'[{boot_diff["delta_supported_fraction"][1]:+.3f}, {boot_diff["delta_supported_fraction"][2]:+.3f}] | '
              f'Delta V: {boot_diff["delta_violation_rate"][0]:+.3f} '
              f'[{boot_diff["delta_violation_rate"][1]:+.3f}, {boot_diff["delta_violation_rate"][2]:+.3f}]')

    with open(METRICS_DIR / 'bootstrap_significance_tests.json', 'w') as f:
        json.dump(bootstrap_results, f, indent=2)

    # 6. Secondary Online Track: Adaptive Conformal Inference (ACI)
    print('\n[5/6] Running Online Adaptive Conformal Inference (Gibbs & Candes) Simulation...')
    aci_sims = {}
    for regime_name, (src_d, tgt_d) in regimes.items():
        splits = create_experiment_splits(
            src_d, tgt_d, budgets=[0], regime=regime_name,
            experiment_type='within_domain' if regime_name.startswith('E0') else 'transfer'
        )
        df_test = splits.target_test.sort_values('t_start').reset_index(drop=True)
        y_test = df_test['target_y'].to_numpy(dtype=float)
        y_preds = primary_predictor.predict(df_test)
        
        aci = AdaptiveConformalCalibrator(alpha=0.10, gamma=0.05, init_q=source_global_q)
        aci_bounds = []
        aci_violations = []
        for i in range(len(y_test)):
            b, v = aci.step(y_preds[i], y_test[i])
            aci_bounds.append(b)
            aci_violations.append(v)
            
        m_aci = compute_reliability_metrics(y_test, y_preds, np.array(aci_bounds))
        aci_sims[regime_name] = {
            'violation_rate': m_aci.violation_rate,
            'supported_fraction': m_aci.supported_rate_fraction,
            'final_q': aci.q,
            'q_trajectory': aci.history[::max(1, len(aci.history)//50)]
        }
        print(f'  {regime_name:30s} | ACI Violation Rate: {m_aci.violation_rate:.3f} | Supported Fraction: {m_aci.supported_rate_fraction:.3f}')

    with open(METRICS_DIR / 'online_aci_results.json', 'w') as f:
        json.dump(aci_sims, f, indent=2)

    # 7. Generate Publication Figures and Tables
    print('\n[6/6] Generating Publication-Quality Figures & LaTeX Tables...')
    generate_publication_figures(calib_df, aci_sims, model_profiles)
    # The publication builder renders all tables after sensitivity diagnostics.
    
    print('\n' + '='*70)
    print('ALL EXPERIMENTS SUCCESSFULLY EXECUTED AND ARTIFACTS GENERATED')
    print('='*70)
    return results_all

def generate_publication_figures(calib_df: pd.DataFrame, aci_sims: Dict, model_profiles: Dict):
    """Generate high-resolution vector and PNG figures for the manuscript."""
    
    # FIGURE 1: Reliability & Usefulness vs Calibration Budget K
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharex=True)
    regimes = ['E0_WithinDomain_Op1_2021', 'E1_CampaignTransfer_Op1_2023',
               'E2_CrossOperator_Op2_2021', 'E3_JointShift_Op2_2023']
    titles = ['(a) E0: Within-Domain (Op1 2021)', '(b) E1: Campaign Transfer (Op1 2023)',
              '(c) E2: Cross-Operator (Op2 2021)', '(d) E3: Joint Shift (Op2 2023)']
    
    for idx, (reg, title) in enumerate(zip(regimes, titles)):
        ax = axes[idx // 2, idx % 2]
        sub = calib_df[calib_df['regime'] == reg]
        
        for m, style, col in [('Global_Conformal', '--o', '#1f77b4'),
                              ('Proposed_Missingness_Aware', '-s', '#2ca02c'),
                              ('RAT_Grouped', ':^', '#ff7f0e'),
                              ('Uncalibrated', '-.x', '#d62728')]:
            m_data = sub[sub['method'] == m]
            ax.plot(m_data['budget_K'], m_data['supported_fraction'], style, color=col, label=m.replace('_', ' '))
            
        ax.set_title(title, fontweight='bold')
        ax.set_ylabel('Supported-Rate Fraction ($U$)')
        ax.set_ylim(-0.05, 0.85)
        ax.grid(True, linestyle='--', alpha=0.5)
        if idx >= 2:
            ax.set_xlabel('Target Calibration Budget $K$ (Sessions)')
        if idx == 0:
            ax.legend(loc='upper left', frameon=True)
            
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig1_budget_vs_usefulness.pdf', bbox_inches='tight')
    fig.savefig(FIGURES_DIR / 'fig1_budget_vs_usefulness.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {FIGURES_DIR / "fig1_budget_vs_usefulness.pdf"}')

    # FIGURE 2: Violation Rate vs Nominal Alpha & Subgroup Analysis
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    
    # 2a: Subgroup Violation in E2 (Op2 2021)
    e2_prop = calib_df[(calib_df['regime'] == 'E2_CrossOperator_Op2_2021') &
                       (calib_df['method'] == 'Proposed_Missingness_Aware')]
    axes[0].plot(e2_prop['budget_K'], e2_prop['subgroup_V_LTE_only'], '-o', color='#1f77b4', label='LTE-Only (Group 2)')
    axes[0].plot(e2_prop['budget_K'], e2_prop['subgroup_V_Dual_NR'], '-s', color='#2ca02c', label='Dual LTE+NR (Group 3)')
    axes[0].plot(e2_prop['budget_K'], e2_prop['violation_rate'], '--k', label='Aggregate Population')
    axes[0].axhline(0.10, color='r', linestyle=':', label=r'Nominal $\alpha = 0.10$')
    axes[0].set_title('(a) Subgroup Violation Rate under Cross-Operator Transfer (E2)')
    axes[0].set_xlabel('Target Calibration Budget $K$ (Sessions)')
    axes[0].set_ylabel('Empirical Violation Rate ($V$)')
    axes[0].set_ylim(0.0, 0.35)
    axes[0].legend(loc='upper right', frameon=True)
    axes[0].grid(True, linestyle='--', alpha=0.5)

    # 2b: Tradeoff between Overcommitment and Supported Fraction
    for reg, col, marker in zip(regimes, ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'], ['o', 's', '^', 'D']):
        sub = calib_df[(calib_df['regime'] == reg) & (calib_df['method'] == 'Proposed_Missingness_Aware')]
        axes[1].plot(sub['mean_overcommitment'], sub['supported_fraction'], marker=marker, color=col, label=reg.split('_')[0])
    axes[1].set_title('(b) Risk-Utility Frontier: Overcommitment vs Supported Rate')
    axes[1].set_xlabel('Mean Overcommitment Magnitude (Mbps)')
    axes[1].set_ylabel('Supported-Rate Fraction ($U$)')
    axes[1].legend(loc='lower right', frameon=True)
    axes[1].grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig2_subgroup_and_tradeoff.pdf', bbox_inches='tight')
    fig.savefig(FIGURES_DIR / 'fig2_subgroup_and_tradeoff.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {FIGURES_DIR / "fig2_subgroup_and_tradeoff.pdf"}')

    # FIGURE 3: Online Adaptive Conformal Inference (ACI) Trajectory
    fig, ax = plt.subplots(figsize=(8, 4))
    for reg, col in zip(regimes, ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']):
        traj = aci_sims[reg]['q_trajectory']
        x = np.linspace(0, 100, len(traj))
        ax.plot(x, traj, label=reg.split('_')[0], color=col, linewidth=1.5)
    ax.set_title('Online score-offset tracking')
    ax.set_xlabel('Test Stream Progression (%)')
    ax.set_ylabel('Adaptive Score Offset $q_t$ (Mbps)')
    ax.legend(loc='upper right', frameon=True)
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig3_aci_adaptation.pdf', bbox_inches='tight')
    fig.savefig(FIGURES_DIR / 'fig3_aci_adaptation.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {FIGURES_DIR / "fig3_aci_adaptation.pdf"}')

if __name__ == '__main__':
    run_all_experiments()
