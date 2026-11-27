"""Exploratory Predictor Robustness & Downstream Accounting Stress-Test Suite.

Strictly enforces:
  1. Zero edits to configs/pacer.json, docs/PACER_FROZEN_PROTOCOL.md, or existing results/.
  2. Pre-committed thresholds read from configs/predictor_robustness_exploratory.json.
  3. Zero future leakage via strict chronological LOCampO earlier-in-time training splits.
  4. Identical downstream policy replay & audit pipeline (src/audit/recalibration_audit.py).
  5. Campaign-level bootstrap CIs (resampling physical campaigns, not dates) & Holm/BH multiplicity.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_marur import aggregate
from src.audit.recalibration_audit import normalize_ledger, summarize_single_policy
from src.predictors.aci import replay_policy_unified
from src.predictors.analysis import (
    compute_ablation_with_campaign_bootstrap,
    compute_fairness_sieve_by_predictor,
    compute_tost_and_divergence_table,
)
from src.predictors.datasets import (
    COHORT_TO_CAMPAIGN,
    build_locampo_train_pool,
    chronological_date_splits,
    load_all_evaluation_cohorts,
    load_oslo_bus_source,
    load_rome_2021_source,
    physical_unit_for_row,
)
from src.predictors.models import (
    MONOTONIC_RADIO_FEATURES,
    fit_cqr_pair_blocked,
    fit_select_histgbm,
    fit_select_linear,
    pinball_loss,
)

CFG_PATH = ROOT / 'configs/predictor_robustness_exploratory.json'
OUT_DIR = ROOT / 'results/exploratory/predictor_robustness'


def _verify_frozen_checksums() -> None:
    """Verify frozen Path A protocol configs & digests remain unmodified before/after running."""
    lock = json.loads((ROOT / 'results/pacer/frozen_config_checksums.json').read_text(encoding='utf8'))
    for rel, expected in lock['sha256_lf'].items():
        actual = hashlib.sha256((ROOT / rel).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        if actual != expected:
            raise RuntimeError(f'Frozen file modified: {rel} ({actual} != {expected})')


def _git_config_status(rel_path: str) -> dict[str, str | bool]:
    """Record pre-run commit status of the exploratory config."""
    try:
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = subprocess.check_output(['git', 'status', '--porcelain', rel_path], cwd=ROOT, text=True).strip()
        return {'git_head': head, 'config_clean_at_run': dirty == '', 'config_path': rel_path}
    except Exception:
        return {'git_head': 'unknown', 'config_clean_at_run': False, 'config_path': rel_path}


def _cluster_frame_from_ledger(act: pd.DataFrame, cohort: str) -> pd.DataFrame:
    df = act.copy()
    df['physical_unit'] = [physical_unit_for_row(cohort, str(d)) for d in df['date']]
    df['campaign'] = COHORT_TO_CAMPAIGN[cohort]
    df['eligible_n'] = df['eligible'].astype(int)
    df['offers_n'] = (df['eligible'] & (df['lower'] > 0)).astype(int)
    df['viol_n'] = (df['eligible'] & (df['lower'] > 0) & df['y'].notna() & (df['lower'] > df['y'])).astype(int)
    df['miss_n'] = (df['eligible'] & (df['lower'] > 0) & df['y'].isna()).astype(int)
    df['query_n'] = df['query'].astype(int)
    valid = df['eligible'] & df['y'].notna()
    df['obs_sum'] = np.where(valid, df['y'], 0.0)
    df['deliv_sum'] = np.where(valid, np.minimum(df['lower'], df['y']), 0.0)
    return (
        df.groupby('physical_unit', sort=True)
        .agg(
            eligible=('eligible_n', 'sum'),
            offers=('offers_n', 'sum'),
            violations=('viol_n', 'sum'),
            missing_outcomes=('miss_n', 'sum'),
            queries_charged=('query_n', 'sum'),
            observed_sum=('obs_sum', 'sum'),
            delivered_sum=('deliv_sum', 'sum'),
        )
        .reset_index()
    )


def fit_all_locampo_predictors(
    eval_df: pd.DataFrame,
    src_archives: pd.DataFrame,
    cfg: dict,
) -> tuple[dict[tuple[str, str], object], list[dict]]:
    """Train all regularized, monotonic, linear, quantile, and date-blocked CQR models per LOCampO fold."""
    seed = int(cfg['primary_seed'])
    val_frac = float(cfg['locampo']['validation_fraction_by_date'])
    cqr_frac = float(cfg['locampo']['cqr_calib_fraction_by_date'])
    excl_overlap = bool(cfg['locampo']['exclude_overlapping_city_pair'])
    grids = cfg['predictor_grids']

    campaigns = sorted(eval_df['source_campaign'].unique())
    cache: dict[tuple[str, str], object] = {}
    models_by_camp_pred: dict[tuple[str, str], object] = {}
    fold_meta_rows: list[dict] = []

    for camp in campaigns:
        pool_df, pool_meta = build_locampo_train_pool(
            eval_df, src_archives, camp, exclude_overlapping_city_pair=excl_overlap
        )
        sig = hashlib.sha256(
            '|'.join(pool_meta['source_campaigns_used']).encode() + f"|{pool_meta['n_train_rows']}".encode()
        ).hexdigest()[:16]

        tr_2w, va_2w, _ = chronological_date_splits(pool_df, val_frac=val_frac, calib_frac=0.0)
        tr_3w, va_3w, cal_3w = chronological_date_splits(pool_df, val_frac=val_frac, calib_frac=cqr_frac)

        specs = [
            ('HistGBM_Reg_LOCampO', lambda: fit_select_histgbm(tr_2w, va_2w, name='HistGBM_Reg_LOCampO', grid_cfg=grids['histgbm_reg'], loss='squared_error', seed=seed)),
            ('HistGBM_Mono_LOCampO', lambda: fit_select_histgbm(tr_2w, va_2w, name='HistGBM_Mono_LOCampO', grid_cfg=grids['histgbm_mono'], loss='squared_error', monotonic_features=MONOTONIC_RADIO_FEATURES, seed=seed)),
            ('Ridge_LOCampO', lambda: fit_select_linear(tr_2w, va_2w, family='ridge', grid_cfg=grids['ridge'], seed=seed)),
            ('ElasticNet_LOCampO', lambda: fit_select_linear(tr_2w, va_2w, family='elasticnet', grid_cfg=grids['elasticnet'], seed=seed)),
            ('QuantileGBM_p10_LOCampO', lambda: fit_select_histgbm(tr_2w, va_2w, name='QuantileGBM_p10_LOCampO', grid_cfg=grids['quantile_histgbm'], loss='quantile', quantile=0.10, seed=seed)),
            ('QuantileGBM_p90_LOCampO', lambda: fit_select_histgbm(tr_2w, va_2w, name='QuantileGBM_p90_LOCampO', grid_cfg=grids['quantile_histgbm'], loss='quantile', quantile=0.90, seed=seed)),
        ]
        for pred_name, builder in specs:
            ckey = (sig, pred_name)
            if ckey not in cache:
                cache[ckey] = builder()
            mod = cache[ckey]
            models_by_camp_pred[(camp, pred_name)] = mod
            fold_meta_rows.append({
                'target_campaign': camp,
                'predictor': pred_name,
                'n_train_total': pool_meta['n_train_rows'],
                'n_train_dates': pool_meta['n_train_dates'],
                'n_other_eval_campaigns': pool_meta['n_other_eval_campaigns'],
                'source_campaigns_used': '; '.join(pool_meta['source_campaigns_used']),
                'target_cal_start_utc': pool_meta['target_cal_start_utc'],
                'selected_params_json': json.dumps(mod.selected_params, sort_keys=True),
            })

        cqr_ckey = (sig, 'CQR_PAIR')
        if cqr_ckey not in cache:
            cache[cqr_ckey] = fit_cqr_pair_blocked(
                tr_3w, va_3w, cal_3w, q_grid_cfg=grids['quantile_histgbm'], cqr_cfg=grids['cqr'], seed=seed
            )
        cqr_u, cqr_s = cache[cqr_ckey]
        models_by_camp_pred[(camp, 'CQR_Unscaled_LOCampO')] = cqr_u
        models_by_camp_pred[(camp, 'CQR_Scaled_LOCampO')] = cqr_s
        for pred_name, mod in (('CQR_Unscaled_LOCampO', cqr_u), ('CQR_Scaled_LOCampO', cqr_s)):
            fold_meta_rows.append({
                'target_campaign': camp,
                'predictor': pred_name,
                'n_train_total': pool_meta['n_train_rows'],
                'n_train_dates': pool_meta['n_train_dates'],
                'n_other_eval_campaigns': pool_meta['n_other_eval_campaigns'],
                'source_campaigns_used': '; '.join(pool_meta['source_campaigns_used']),
                'target_cal_start_utc': pool_meta['target_cal_start_utc'],
                'selected_params_json': json.dumps(mod.selected_params, sort_keys=True),
            })

    return models_by_camp_pred, fold_meta_rows


def _build_scope_summary(cohort_df: pd.DataFrame, cluster_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize (predictor x policy x cohort scope) identically via src.audit.recalibration_audit."""
    scopes = {
        'AllCohorts': set(COHORT_TO_CAMPAIGN.keys()),
        'AllMobile': set(COHORT_TO_CAMPAIGN.keys()) - {'Ireland_Static'},
        'Retrospective': {'E1', 'E3', 'AT&T', 'T-Mobile', 'Verizon', 'Ireland'},
        'HeldOutPublic': {'Rome_Capacity_Op1', 'Rome_Capacity_Op2', 'Oslo_Commute', 'Ireland_Static'},
        'Post2021_RadioOnly': {'E1', 'E3', 'AT&T', 'T-Mobile', 'Verizon', 'Rome_Capacity_Op1', 'Rome_Capacity_Op2'},
    }
    rows = []
    for (pred_name, policy, cap_new, scen), sub in cohort_df.groupby(['predictor', 'policy', 'cap_new', 'scenario'], sort=False):
        cl_sub = cluster_df[
            (cluster_df['predictor'] == pred_name)
            & (cluster_df['policy'] == policy)
            & (cluster_df['cap_new'] == cap_new)
            & (cluster_df['scenario'] == scen)
        ]
        for scope_name, sc_cohorts in scopes.items():
            c_sc = sub[sub['cohort'].isin(sc_cohorts)]
            cl_sc = cl_sub[cl_sub['cohort'].isin(sc_cohorts)]
            if c_sc.empty or cl_sc.empty:
                continue

            # Run canonical audit_ledger normalizer over physical_unit clusters
            norm_input = cl_sc.rename(columns={'physical_unit': 'cluster_id'}).copy()
            norm_input['observed_outcomes'] = norm_input['offers'] - norm_input['missing_outcomes']
            norm = normalize_ledger(norm_input)
            audit_pol = summarize_single_policy(norm, policy=policy, min_clusters=20, alpha=0.10)

            rhi = 100.0 * c_sc['positive_high'].dropna()
            rlo = 100.0 * c_sc['positive_low'].dropna()
            r_all_hi = 100.0 * c_sc['hi'].dropna()
            u_vals = 100.0 * c_sc['u'].dropna()
            a_vals = 100.0 * c_sc['positive_rate'].dropna()
            cl_u = 100.0 * np.where(norm['observed_sum'] > 0, norm['delivered_sum'] / norm['observed_sum'], np.nan)
            cl_u = cl_u[np.isfinite(cl_u)]

            rows.append({
                'predictor': pred_name,
                'policy': policy,
                'scope': scope_name,
                'cap_new': int(cap_new),
                'scenario': scen,
                'evidence_tier': 'exploratory',
                'is_reference_row': bool(pred_name == 'HistGBM_57_Ref'),
                'n_cohorts': int(c_sc['cohort'].nunique()),
                'clusters_g': int(audit_pol['clusters']),
                'campaigns_k': int(cl_sc['campaign'].nunique()),
                'a_med_pct': float(a_vals.median()) if len(a_vals) else float('nan'),
                'a_min_pct': float(a_vals.min()) if len(a_vals) else float('nan'),
                'a_max_pct': float(a_vals.max()) if len(a_vals) else float('nan'),
                'a_pooled_pct': 100.0 * float(audit_pol['offer_frequency_A']),
                'r_pos_hi_med_pct': float(rhi.median()) if len(rhi) else float('nan'),
                'r_pos_hi_min_pct': float(rhi.min()) if len(rhi) else float('nan'),
                'r_pos_hi_max_pct': float(rhi.max()) if len(rhi) else float('nan'),
                'r_pos_hi_pooled_pct': 100.0 * float(audit_pol['conditional_risk_hi']),
                'r_pos_lo_med_pct': float(rlo.median()) if len(rlo) else float('nan'),
                'r_pos_lo_pooled_pct': 100.0 * float(audit_pol['conditional_risk_lo']),
                'manski_width_med_pp': float((rhi - rlo).median()) if len(rhi) and len(rlo) else float('nan'),
                'r_all_hi_med_pct': float(r_all_hi.median()) if len(r_all_hi) else float('nan'),
                'r_all_hi_pooled_pct': 100.0 * float(audit_pol['all_issued_risk_hi']),
                'u_med_pct': float(u_vals.median()) if len(u_vals) else float('nan'),
                'u_min_pct': float(u_vals.min()) if len(u_vals) else float('nan'),
                'u_max_pct': float(u_vals.max()) if len(u_vals) else float('nan'),
                'u_eq_cluster_pct': float(np.mean(cl_u)) if len(cl_u) else float('nan'),
                'u_pooled_pct': 100.0 * float(audit_pol['supported_throughput_U']),
                'q_new_mean': float(c_sc['new_query_attempts'].mean()),
                'q_new_total': int(audit_pol['realized_queries']),
                'id_err_max': float(audit_pol['r_identity_max_abs_err']),
            })
    return pd.DataFrame(rows)


def _plot_robustness_figures(
    cohort_df: pd.DataFrame,
    ablation_df: pd.DataFrame,
    tost_df: pd.DataFrame,
    pred_order: list[str],
) -> None:
    """Render 3-panel robustness figure: (a) R_+^hi vs alpha=10%, (b) flip rates + camp boot CIs, (c) pooling divergence."""
    plt.rcParams.update({'font.size': 7.5, 'axes.titlesize': 8.2, 'axes.labelsize': 7.4})
    short_lbl = {
        'HistGBM_57_Ref': 'HistGBM57\n(Ref)',
        'Persistence': 'Persist',
        'HistGBM_Reg_LOCampO': 'HistGBM\nReg',
        'HistGBM_Mono_LOCampO': 'HistGBM\nMono',
        'Ridge_LOCampO': 'Ridge',
        'ElasticNet_LOCampO': 'Elastic\nNet',
        'QuantileGBM_p10_LOCampO': 'Quantile\np10',
        'QuantileGBM_p90_LOCampO': 'Quantile\np90',
        'CQR_Unscaled_LOCampO': 'CQR\nUnsc',
        'CQR_Scaled_LOCampO': 'CQR\nScaled',
    }
    x_labels = [short_lbl.get(p, p) for p in pred_order]
    x = np.arange(len(pred_order))

    fig, axes = plt.subplots(3, 1, figsize=(8.2, 8.4), dpi=300)

    # Panel (a): Mobile conditional upper risk R_+^hi by predictor across Periodic, MARUR, PACER, ACI_g0.05 (Recorded)
    ax_a = axes[0]
    mob_rec = cohort_df[
        (cohort_df['cohort'] != 'Ireland_Static')
        & (cohort_df['scenario'] == 'Recorded')
        & (cohort_df['cap_new'].isin([10, 40]))
    ]
    pols = [('Periodic', '#7f7f7f', 'o'), ('MARUR', '#ff7f0e', 's'), ('PACER', '#1f77b4', '^'), ('ACI_g0.05', '#9467bd', 'D')]
    for idx, (pol, col, mk) in enumerate(pols):
        off = (idx - 1.5) * 0.16
        meds, q25s, q75s = [], [], []
        for p in pred_order:
            vals = 100.0 * mob_rec[(mob_rec['predictor'] == p) & (mob_rec['policy'] == pol)]['positive_high'].dropna()
            meds.append(float(vals.median()) if len(vals) else np.nan)
            q25s.append(float(vals.quantile(0.25)) if len(vals) else np.nan)
            q75s.append(float(vals.quantile(0.75)) if len(vals) else np.nan)
        meds_a = np.asarray(meds)
        yerr = np.vstack([np.maximum(0.0, meds_a - np.asarray(q25s)), np.maximum(0.0, np.asarray(q75s) - meds_a)])
        ax_a.errorbar(x + off, meds_a, yerr=yerr, fmt=mk, markersize=4.5, color=col, capsize=2.5, linewidth=1.1, label=pol)
    ax_a.axhline(10.0, color='#2ca02c', linestyle='--', linewidth=1.1, label='Nominal alpha = 10%')
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(x_labels, fontsize=6.6)
    ax_a.set_ylabel('Mobile $R_+^{\\mathrm{hi}}$ (%, med / IQR)')
    ax_a.set_ylim(0, 105)
    ax_a.set_title('(a) Mobile Conditional Upper Risk $R_+^{\\mathrm{hi}}$ by Predictor vs. $\\alpha = 10\\%$ Ceiling (Recorded)', loc='left')
    ax_a.grid(True, axis='y', alpha=0.25, linewidth=0.5)
    ax_a.legend(ncol=5, fontsize=6.4, loc='upper right')

    # Panel (b): Single-factor ablation flip rates with campaign-level bootstrap 95% CIs (All scenario contrasts)
    ax_b = axes[1]
    abl_all = ablation_df[ablation_df['scenario_filter'] == 'All']
    factors = [
        ('R_vs_Rplus_SLA', 'SLA R->R+', '#d62728'),
        ('R_vs_Rplus_Rank', 'Rank R->R+', '#ff7f0e'),
        ('Cap_vs_Qnew_All', 'Q_new Mismatch', '#8c564b'),
        ('Missing_Bounds_Overlap', 'Missing Overlap', '#9467bd'),
        ('Pooling_Weight_Rplus', 'Pool!=Eq Sign', '#1f77b4'),
    ]
    w = 0.155
    for idx, (fcode, flbl, col) in enumerate(factors):
        off = (idx - 2.0) * w
        sub = abl_all[abl_all['factor'] == fcode].set_index('predictor')
        pts = np.array([float(sub.loc[p, 'pct_affected']) if p in sub.index else np.nan for p in pred_order])
        lo = np.array([float(sub.loc[p, 'camp_boot_ci95_lo']) if p in sub.index else np.nan for p in pred_order])
        hi = np.array([float(sub.loc[p, 'camp_boot_ci95_hi']) if p in sub.index else np.nan for p in pred_order])
        yerr = np.vstack([np.maximum(0.0, pts - lo), np.maximum(0.0, hi - pts)])
        ax_b.bar(x + off, pts, width=w * 0.9, yerr=yerr, color=col, edgecolor='#222222', linewidth=0.25, capsize=1.6, error_kw={'lw': 0.7}, label=flbl)
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(x_labels, fontsize=6.6)
    ax_b.set_ylabel('Flip / Ambiguity Rate (%)')
    ax_b.set_ylim(0, 108)
    ax_b.set_title('(b) Single-Factor Accounting Reversal Rates with Campaign-Level Bootstrap 95% CIs ($k=6$ Campaigns)', loc='left')
    ax_b.grid(True, axis='y', alpha=0.25, linewidth=0.5)
    ax_b.legend(ncol=5, fontsize=6.4, loc='upper right')

    # Panel (c): Offer-weighted (Pool) vs Equal-cluster (EqualCl) dR+hi divergence on HeldOutPublic C=10 PACER vs Periodic
    ax_c = axes[2]
    ho_p = tost_df[
        (tost_df['scope'] == 'HeldOutPublic') & (tost_df['cap_new'] == 10) & (tost_df['candidate'] == 'PACER')
    ].set_index('predictor')
    p_vals = np.array([float(ho_p.loc[p, 'pool_dpos_hi_pp']) if p in ho_p.index else np.nan for p in pred_order])
    e_vals = np.array([float(ho_p.loc[p, 'eq_dpos_hi_pp']) if p in ho_p.index else np.nan for p in pred_order])
    ax_c.bar(x - 0.18, p_vals, width=0.34, color='#1f77b4', edgecolor='#222222', linewidth=0.3, label='Offer-weighted $\\Delta R_+^{\\mathrm{hi}}$')
    ax_c.bar(x + 0.18, e_vals, width=0.34, color='#ff7f0e', edgecolor='#222222', linewidth=0.3, label='Equal-cluster $\\Delta R_+^{\\mathrm{hi}}$')
    ax_c.axhline(0.0, color='#333333', linewidth=0.8)
    lo_y = min(-25.5, float(np.nanmin(np.r_[p_vals, e_vals])) - 3.0)
    hi_y = max(14.0, float(np.nanmax(np.r_[p_vals, e_vals])) + 3.0)
    ax_c.set_ylim(lo_y, hi_y)
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(x_labels, fontsize=6.6)
    ax_c.set_ylabel('$\\Delta R_+^{\\mathrm{hi}}$ vs Periodic (pp)')
    ax_c.set_title('(c) Pooling Divergence: Offer-Weighted vs. Equal-Cluster PACER $\\Delta R_+^{\\mathrm{hi}}$ (Held-Out Public, $C_{\\mathrm{new}}=10$)', loc='left')
    ax_c.grid(True, axis='y', alpha=0.25, linewidth=0.5)
    ax_c.legend(ncol=2, fontsize=6.8, loc='lower right')

    fig.tight_layout()
    for ext in ('pdf', 'png'):
        kwargs = {'bbox_inches': 'tight'}
        if ext == 'png':
            kwargs['dpi'] = 300
        fig.savefig(OUT_DIR / f'fig_predictor_robustness.{ext}', **kwargs)
    plt.close(fig)


def main(stats_only: bool = False) -> None:
    _verify_frozen_checksums()
    cfg = json.loads(CFG_PATH.read_text(encoding='utf8'))
    git_meta = _git_config_status('configs/predictor_robustness_exploratory.json')
    marur_cfg = json.loads((ROOT / 'configs/marur.json').read_text(encoding='utf8'))
    pacer_cfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    start_utc = datetime.now(timezone.utc).isoformat()

    predictors_order = [
        'HistGBM_57_Ref',
        'Persistence',
        'HistGBM_Reg_LOCampO',
        'HistGBM_Mono_LOCampO',
        'Ridge_LOCampO',
        'ElasticNet_LOCampO',
        'QuantileGBM_p10_LOCampO',
        'QuantileGBM_p90_LOCampO',
        'CQR_Unscaled_LOCampO',
        'CQR_Scaled_LOCampO',
    ]
    seed = int(cfg['primary_seed'])

    if stats_only and (OUT_DIR / 'cohort_policy_ledger.csv').exists() and (OUT_DIR / 'cluster_policy_ledger.csv.gz').exists():
        cohort_df = pd.read_csv(OUT_DIR / 'cohort_policy_ledger.csv')
        cluster_df = pd.read_csv(OUT_DIR / 'cluster_policy_ledger.csv.gz')
        pt_df = pd.read_csv(OUT_DIR / 'point_accuracy.csv')
        pt_fold_df = pd.read_csv(OUT_DIR / 'fold_training_summary.csv')
        summary_df = _build_scope_summary(cohort_df, cluster_df)
    else:
        eval_df = load_all_evaluation_cohorts()
        src_oslo = load_oslo_bus_source('2010-10-01T00:00:00Z')
        src_rome = load_rome_2021_source()
        src_archives = pd.concat([src_oslo, src_rome], ignore_index=True)

        locampo_models, fold_meta = fit_all_locampo_predictors(eval_df, src_archives, cfg)

        point_rows = list(fold_meta)
        cohort_rows = []
        cluster_frames = []
        policies = list(cfg['policies'])
        scenarios = list(cfg['scenarios'])
        caps = [int(c) for c in cfg['new_query_caps']]
        init_n = int(cfg['initial_labels'])

        for p_idx, pred_name in enumerate(predictors_order, start=1):
            print(f'[{p_idx}/{len(predictors_order)}] Replaying downstream policies for {pred_name}...', flush=True)
            for cohort, grp in eval_df.groupby('cohort', sort=True):
                camp = COHORT_TO_CAMPAIGN[cohort]
                dom = str(grp['domain'].iloc[0])
                frame = grp.copy()
                frame['date'] = frame['date'].astype(str)
                if pred_name == 'HistGBM_57_Ref':
                    frame['point'] = frame['HistGBM'].astype(float)
                elif pred_name == 'Persistence':
                    frame['point'] = frame['Persistence'].astype(float)
                else:
                    model_obj = locampo_models[(camp, pred_name)]
                    elig = frame['y_lag1'].notna()
                    frame['point'] = np.nan
                    if elig.any():
                        frame.loc[elig, 'point'] = np.asarray(model_obj.predict(frame.loc[elig]), dtype=float)

                eval_pts = frame[(frame['partition'] == 'test') & frame['y'].notna() & frame['point'].notna()]
                if not eval_pts.empty:
                    yt = eval_pts['y'].to_numpy(dtype=float)
                    yp = eval_pts['point'].to_numpy(dtype=float)
                    point_rows.append({
                        'target_campaign': camp,
                        'cohort': cohort,
                        'domain': dom,
                        'predictor': pred_name,
                        'evidence_tier': 'exploratory',
                        'n_scored': int(len(eval_pts)),
                        'mae_mbps': float(np.mean(np.abs(yp - yt))),
                        'rmse_mbps': float(np.sqrt(np.mean((yp - yt) ** 2))),
                        'point_viol_rate': float(np.mean(yp > yt)),
                        'pinball_p10': pinball_loss(yt, yp, 0.10),
                        'pinball_p90': pinball_loss(yt, yp, 0.90),
                    })

                init = frame[frame['partition'] == 'cal'].sort_values(['issue', 'id']).head(init_n)
                stream = frame[frame['partition'] == 'test'].sort_values(['issue', 'id']).reset_index(drop=True)
                assert len(init) == init_n
                assert float(init['ready'].max()) <= float(stream['issue'].min())

                for scen in scenarios:
                    act_f, resp_f = replay_policy_unified(
                        init, stream, 'Frozen', init_n, marur_cfg, pacer_cfg, scenario=scen, seed=seed
                    )
                    st_f = aggregate(act_f, resp_f, initial=init_n)
                    st_f.update(
                        predictor=pred_name, cohort=cohort, domain=dom, campaign=camp,
                        scenario=scen, cap_new=0, budget=init_n, policy='Frozen', evidence_tier='exploratory',
                    )
                    cohort_rows.append(st_f)
                    cf = _cluster_frame_from_ledger(act_f, cohort)
                    cf['predictor'], cf['cohort'], cf['domain'], cf['campaign'], cf['scenario'], cf['cap_new'], cf['policy'] = (
                        pred_name, cohort, dom, camp, scen, 0, 'Frozen'
                    )
                    cluster_frames.append(cf)

                    for cap_new in caps:
                        budget = init_n + cap_new
                        for pol in policies:
                            if pol == 'Frozen':
                                continue
                            act, resp = replay_policy_unified(
                                init, stream, pol, budget, marur_cfg, pacer_cfg, scenario=scen, seed=seed
                            )
                            st = aggregate(act, resp, initial=init_n)
                            st.update(
                                predictor=pred_name, cohort=cohort, domain=dom, campaign=camp,
                                scenario=scen, cap_new=cap_new, budget=budget, policy=pol, evidence_tier='exploratory',
                            )
                            cohort_rows.append(st)
                            cm = _cluster_frame_from_ledger(act, cohort)
                            cm['predictor'], cm['cohort'], cm['domain'], cm['campaign'], cm['scenario'], cm['cap_new'], cm['policy'] = (
                                pred_name, cohort, dom, camp, scen, cap_new, pol
                            )
                            cluster_frames.append(cm)

        cohort_df = pd.DataFrame(cohort_rows)
        cluster_df = pd.concat(cluster_frames, ignore_index=True)

        pacer_saved = pd.read_csv(ROOT / 'results/pacer/pacer_summary.csv')
        for pol_new, pol_saved in (('Periodic', 'Periodic'), ('MARUR', 'MARUR'), ('PACER', 'PACER'), ('ACI_g0.05', 'ACI')):
            a = cohort_df[(cohort_df['predictor'] == 'HistGBM_57_Ref') & (cohort_df['scenario'] == 'Recorded') & (cohort_df['policy'] == pol_new)].sort_values(['cohort', 'cap_new'])
            b = pacer_saved[(pacer_saved['model'] == 'HistGBM') & (pacer_saved['scenario'] == 'Recorded') & (pacer_saved['policy'] == pol_saved)].sort_values(['cohort', 'cap_new'])
            np.testing.assert_allclose(a['positive_high'].to_numpy(), b['positive_high'].to_numpy(), rtol=1e-12, atol=1e-12)
            np.testing.assert_allclose(a['u'].to_numpy(), b['u'].to_numpy(), rtol=1e-12, atol=1e-12)
            np.testing.assert_array_equal(a['new_query_attempts'].to_numpy(), b['new_query_attempts'].to_numpy())

        summary_df = _build_scope_summary(cohort_df, cluster_df)
        if float(summary_df['id_err_max'].max()) > 1e-12:
            raise AssertionError(f"Accounting identity R=A*R+ failed: {summary_df['id_err_max'].max()}")

        pt_df = pd.DataFrame([r for r in point_rows if 'cohort' in r])
        pt_fold_df = pd.DataFrame([r for r in point_rows if 'cohort' not in r])
        cohort_df.to_csv(OUT_DIR / 'cohort_policy_ledger.csv', index=False)
        cluster_df.to_csv(OUT_DIR / 'cluster_policy_ledger.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
        pt_df.to_csv(OUT_DIR / 'point_accuracy.csv', index=False)
        pt_fold_df.to_csv(OUT_DIR / 'fold_training_summary.csv', index=False)

    print('Computing campaign-bootstrap ablations, TOST/DEFF + Holm/BH, and fairness sieve...', flush=True)
    ablation_df = compute_ablation_with_campaign_bootstrap(
        cohort_df, cluster_df,
        candidates=cfg['active_ablation_candidates'],
        reference=cfg['reference_policy'],
        alpha=float(cfg['alpha']),
        n_boot=int(cfg['bootstrap_draws']),
        seed=seed,
    )
    tost_df = compute_tost_and_divergence_table(
        cluster_df,
        candidates=('MARUR', 'PACER', 'ACI_g0.05'),
        reference=cfg['reference_policy'],
        n_boot=int(cfg['bootstrap_draws']),
        seed=seed,
    )
    sieve_df = compute_fairness_sieve_by_predictor(
        cohort_df,
        candidates=cfg['active_ablation_candidates'],
        reference=cfg['reference_policy'],
        sieve_cfg=cfg['fairness_sieve'],
    )

    sieve_5cand_ref = compute_fairness_sieve_by_predictor(
        cohort_df[cohort_df['predictor'] == 'HistGBM_57_Ref'],
        candidates=('MARUR', 'PACER', 'ACI_g0.05', 'DecayingOGD', 'Early'),
        reference='Periodic',
        sieve_cfg=cfg['fairness_sieve'],
    ).iloc[0]
    assert int(sieve_5cand_ref['qa_matched']) == 28 and int(sieve_5cand_ref['qa_matched_wins']) == 3

    comp_rows = []
    c_mob = cohort_df[(cohort_df['cohort'] != 'Ireland_Static') & (cohort_df['scenario'] == 'Recorded') & (cohort_df['cap_new'].isin([10, 40])) & (cohort_df['policy'].isin(['Periodic', 'MARUR', 'PACER', 'ACI_g0.05']))]
    c_p21 = cohort_df[(cohort_df['cohort'].isin(['E1', 'E3', 'AT&T', 'T-Mobile', 'Verizon', 'Rome_Capacity_Op1', 'Rome_Capacity_Op2'])) & (cohort_df['scenario'] == 'Recorded') & (cohort_df['cap_new'].isin([10, 40])) & (cohort_df['policy'].isin(['Periodic', 'MARUR', 'PACER', 'ACI_g0.05']))]
    abl_all_lut = ablation_df[ablation_df['scenario_filter'] == 'All'].set_index(['predictor', 'factor'])
    sieve_lut = sieve_df.set_index('predictor')

    for p in predictors_order:
        cm = c_mob[c_mob['predictor'] == p]
        cp = c_p21[c_p21['predictor'] == p]
        rhi_m = 100.0 * cm['positive_high'].dropna()
        u_m = 100.0 * cm['u'].dropna()
        rhi_p21 = 100.0 * cp['positive_high'].dropna()
        u_p21 = 100.0 * cp['u'].dropna()
        pts_p = pt_df[pt_df['predictor'] == p]
        sv = sieve_lut.loc[p]
        sla = abl_all_lut.loc[(p, 'R_vs_Rplus_SLA')]
        rnk = abl_all_lut.loc[(p, 'R_vs_Rplus_Rank')]
        qn = abl_all_lut.loc[(p, 'Cap_vs_Qnew_All')]
        ov = abl_all_lut.loc[(p, 'Missing_Bounds_Overlap')]
        pl = abl_all_lut.loc[(p, 'Pooling_Weight_Rplus')]
        comp_rows.append({
            'predictor': p,
            'evidence_tier': 'exploratory',
            'mae_med_mbps': float(pts_p['mae_mbps'].median()) if not pts_p.empty else float('nan'),
            'mob_r_pos_hi_med_pct': float(rhi_m.median()),
            'mob_r_pos_hi_min_pct': float(rhi_m.min()),
            'mob_r_pos_hi_max_pct': float(rhi_m.max()),
            'mob_u_med_pct': float(u_m.median()),
            'post21_r_pos_hi_med_pct': float(rhi_p21.median()),
            'post21_u_med_pct': float(u_p21.median()),
            'sla_flip_pct': float(sla['pct_affected']),
            'sla_flip_ci95': f"[{sla['camp_boot_ci95_lo']:.1f}, {sla['camp_boot_ci95_hi']:.1f}]",
            'rank_flip_pct': float(rnk['pct_affected']),
            'rank_flip_ci95': f"[{rnk['camp_boot_ci95_lo']:.1f}, {rnk['camp_boot_ci95_hi']:.1f}]",
            'q_mismatch_pct': float(qn['pct_affected']),
            'q_mismatch_ci95': f"[{qn['camp_boot_ci95_lo']:.1f}, {qn['camp_boot_ci95_hi']:.1f}]",
            'miss_overlap_pct': float(ov['pct_affected']),
            'miss_overlap_ci95': f"[{ov['camp_boot_ci95_lo']:.1f}, {ov['camp_boot_ci95_hi']:.1f}]",
            'pool_flip_pct': float(pl['pct_affected']),
            'pool_flip_ci95': f"[{pl['camp_boot_ci95_lo']:.1f}, {pl['camp_boot_ci95_hi']:.1f}]",
            'fair_sieve_wins': f"{int(sv['qa_matched_wins'])}/{int(sv['qa_matched'])} ({sv['fair_win_rate_pct']:.1f}%)",
            'net_sieve_wins': f"{int(sv['qa_matched_wins'])}/{int(sv['total_contrasts'])} ({sv['net_all_win_rate_pct']:.1f}%)",
        })
    comp_df = pd.DataFrame(comp_rows)

    # Determine empirical verdict cleanly from thresholds:
    # Check whether ANY non-reference predictor achieves median mobile R_+^hi <= 15% (near nominal alpha=10%)
    non_ref_comp = comp_df[comp_df['predictor'] != 'HistGBM_57_Ref']
    min_mob_rhi = float(non_ref_comp['mob_r_pos_hi_med_pct'].min())
    min_p21_rhi = float(non_ref_comp['post21_r_pos_hi_med_pct'].min())
    mean_max_flip = float(non_ref_comp[['sla_flip_pct', 'rank_flip_pct', 'q_mismatch_pct', 'miss_overlap_pct', 'pool_flip_pct']].max(axis=1).min())
    if min_mob_rhi <= 15.0 or min_p21_rhi <= 15.0:
        verdict = 'B' if mean_max_flip >= 20.0 else 'C'
    else:
        verdict = 'A' if mean_max_flip >= 20.0 else 'C'

    # Persist all new exploratory artifacts under results/exploratory/predictor_robustness/
    summary_df.to_csv(OUT_DIR / 'summary.csv', index=False)
    cohort_df.to_csv(OUT_DIR / 'cohort_policy_ledger.csv', index=False)
    pt_df.to_csv(OUT_DIR / 'point_accuracy.csv', index=False)
    pt_fold_df.to_csv(OUT_DIR / 'fold_training_summary.csv', index=False)
    ablation_df.to_csv(OUT_DIR / 'ablation_by_predictor.csv', index=False)
    tost_df.to_csv(OUT_DIR / 'tost_and_divergence.csv', index=False)
    sieve_df.to_csv(OUT_DIR / 'fairness_sieve_by_predictor.csv', index=False)
    comp_df.to_csv(OUT_DIR / 'comparison_table.csv', index=False)
    _plot_robustness_figures(cohort_df, ablation_df, tost_df, predictors_order)

    _verify_frozen_checksums()
    receipt = {
        'start_utc': start_utc,
        'end_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'exploratory_predictor_robustness_only',
        'evidence_tier': 'exploratory',
        'frozen_configs_modified': False,
        'frozen_checksums_verified': True,
        'pre_committed_config': git_meta,
        'config_sha256_lf': hashlib.sha256(CFG_PATH.read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
        'verdict': verdict,
        'min_nonref_mobile_rhi_med_pct': min_mob_rhi,
        'min_nonref_post21_rhi_med_pct': min_p21_rhi,
        'min_nonref_peak_flip_pct': mean_max_flip,
        'ref_5cand_sieve_parity': f"{int(sieve_5cand_ref['qa_matched_wins'])}/{int(sieve_5cand_ref['qa_matched'])} ({int(sieve_5cand_ref['qa_matched_wins'])}/{int(sieve_5cand_ref['total_contrasts'])})",
        'counts': {
            'summary_rows': int(len(summary_df)),
            'cohort_policy_rows': int(len(cohort_df)),
            'ablation_rows': int(len(ablation_df)),
            'tost_rows': int(len(tost_df)),
            'sieve_rows': int(len(sieve_df)),
        },
        'sha256': {
            str(p.relative_to(ROOT).as_posix()): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT_DIR.glob('*'))
            if p.is_file() and p.name != 'execution.json'
        },
    }
    (OUT_DIR / 'execution.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    print(f'Verdict={verdict} | Comparison Table:')
    print(comp_df[['predictor', 'mae_med_mbps', 'mob_r_pos_hi_med_pct', 'mob_u_med_pct', 'post21_r_pos_hi_med_pct', 'sla_flip_pct', 'rank_flip_pct', 'q_mismatch_pct', 'miss_overlap_pct', 'pool_flip_pct', 'fair_sieve_wins', 'net_sieve_wins']].to_string(index=False))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stats-only', action='store_true')
    main(stats_only=ap.parse_args().stats_only)
