"""Unit tests for LOCampO zero-leakage splits, predictors, ACI update, campaign bootstrap, and Holm/BH."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.predictors.aci import aci_alpha_update, aci_policy_name, parse_aci_gamma, replay_policy_unified
from src.predictors.analysis import adjust_pvalues_holm_bh, compute_ablation_with_campaign_bootstrap
from src.predictors.datasets import COHORT_TO_CAMPAIGN, build_locampo_train_pool, chronological_date_splits, physical_unit_for_row
from src.predictors.models import EmptySafeTabularPreprocessor, fit_cqr_pair_blocked, fit_select_histgbm, fit_select_linear


def _synthetic_stream(n_days: int = 8, rows_per_day: int = 20, *, start_ts: float = 1_600_000_000.0, all_nan_radio: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    rows = []
    for d in range(n_days):
        for r in range(rows_per_day):
            issue = start_ts + d * 86400.0 + r * 60.0
            rsrp = np.nan if all_nan_radio else (-95.0 + 10.0 * np.sin(r / 3.0))
            sinr = np.nan if all_nan_radio else (10.0 + 4.0 * np.cos(r / 4.0))
            y_lag1 = max(0.2, 20.0 + 5.0 * np.sin(r / 2.0) + rng.normal(0.0, 2.0))
            y = max(0.0, 0.7 * y_lag1 + (0.0 if all_nan_radio else 0.3 * (sinr - 5.0)) + rng.normal(0.0, 3.0))
            rows.append({
                'id': f's-{d}-{r}',
                'date': f'2022-01-{d + 1:02d}',
                'issue': issue,
                'ready': issue + 60.0,
                'y_lag1': y_lag1,
                'prev_duration_s': 60.0,
                'lag_age_s': 60.0,
                'has_lte': 0 if all_nan_radio else 1,
                'has_nr': 0,
                'group_id': 0 if all_nan_radio else 2,
                'pattern': 0 if all_nan_radio else 2,
                'rsrp': rsrp,
                'rsrq': np.nan if all_nan_radio else -9.0,
                'sinr': sinr,
                'ss_rsrp': np.nan,
                'ss_rsrq': np.nan,
                'ss_sinr': np.nan,
                'scenario_IS': 1,
                'scenario_OD': 0,
                'scenario_OW': 0,
                'y': y,
                'point': y_lag1,
                'cohort': 'SynthA',
                'source_campaign': 'CampA',
                'partition': 'test' if d >= 2 else 'cal',
            })
    return pd.DataFrame(rows)


def test_aci_alpha_update_exact_formula():
    assert aci_alpha_update(0.10, 1.0, target_alpha=0.10, gamma=0.005) == pytest.approx(0.0955)
    assert aci_alpha_update(0.10, 0.0, target_alpha=0.10, gamma=0.01) == pytest.approx(0.101)
    assert aci_alpha_update(0.10, 1.0, target_alpha=0.10, gamma=0.05) == pytest.approx(0.055)
    assert parse_aci_gamma('ACI_g0.005') == pytest.approx(0.005)
    assert parse_aci_gamma('ACI_g0.01') == pytest.approx(0.01)
    assert parse_aci_gamma('ACI_g0.05') == pytest.approx(0.05)
    assert aci_policy_name(0.005) == 'ACI_g0.005'


def test_aci_replay_tracks_query_cap_and_updates_chronologically():
    df = _synthetic_stream(n_days=3, rows_per_day=30)
    cal = df.iloc[:10].copy()
    stream = df.iloc[10:].copy().reset_index(drop=True)
    mcfg = {'alpha': 0.10, 'initial_labels': 10, 'window': 10, 'period_ticks': 15, 'max_age_minutes': 60, 'minimum_pattern_support': 3, 'aci_step': 0.05}
    pcfg = {'alpha': 0.10, 'initial_labels': 10, 'pacer_gamma': 0.05, 'pacer_veto': 0.15, 'pacer_ext_scale': 2.0, 'pacer_obs_window': 20}
    act_small, resp_small = replay_policy_unified(cal, stream, 'ACI_g0.005', 20, mcfg, pcfg, scenario='Recorded', seed=42)
    act_large, resp_large = replay_policy_unified(cal, stream, 'ACI_g0.05', 20, mcfg, pcfg, scenario='Recorded', seed=42)
    assert int(act_small['query'].sum()) == int(act_large['query'].sum()) <= 10
    assert (act_small['alpha'] != act_large['alpha']).any()
    assert len(resp_small) == int(act_small['query'].sum())


def test_locampo_pool_enforces_strict_zero_future_leakage():
    early = _synthetic_stream(n_days=4, rows_per_day=15, start_ts=1_500_000_000.0)
    early['source_campaign'] = 'EarlierCamp'
    early['cohort'] = 'EarlyCoh'

    target = _synthetic_stream(n_days=4, rows_per_day=15, start_ts=1_600_000_000.0)
    target['source_campaign'] = 'TargetCamp'
    target['cohort'] = 'TargetCoh'
    target['partition'] = 'test'

    future = _synthetic_stream(n_days=4, rows_per_day=15, start_ts=1_700_000_000.0)
    future['source_campaign'] = 'FutureCamp'
    future['cohort'] = 'FutureCoh'

    overlap_target = _synthetic_stream(n_days=3, rows_per_day=10, start_ts=1_600_000_000.0 - 120.0)
    overlap_target['source_campaign'] = 'EarlierOverlap'
    overlap_target['ready'] = overlap_target['issue'] + 300.0  # completes AFTER target starts!

    eval_df = pd.concat([early, target, future, overlap_target], ignore_index=True)
    pool, meta = build_locampo_train_pool(eval_df, pd.DataFrame(columns=eval_df.columns), 'TargetCamp')
    assert not pool.empty
    assert set(pool['source_campaign']) == {'EarlierCamp'}
    assert float(pool['ready'].max()) < float(target['issue'].min())
    assert meta['target_campaign'] == 'TargetCamp'


def test_chronological_date_blocked_cqr_has_disjoint_dates_and_valid_predictions():
    df_a = _synthetic_stream(n_days=8, rows_per_day=20, start_ts=1_500_000_000.0)
    df_b = _synthetic_stream(n_days=6, rows_per_day=20, start_ts=1_600_000_000.0)
    df_b['source_campaign'] = 'CampB'
    df_b['date'] = [f'2022-02-{int(d[-2:]):02d}' for d in df_b['date']]
    df = pd.concat([df_a, df_b], ignore_index=True)

    tr, va, cal = chronological_date_splits(df, val_frac=0.20, calib_frac=0.20)
    for cp in ('CampA', 'CampB'):
        t_c = tr[tr['source_campaign'] == cp]
        v_c = va[va['source_campaign'] == cp]
        c_c = cal[cal['source_campaign'] == cp]
        assert not t_c.empty and not v_c.empty and not c_c.empty
        assert set(t_c['date']).isdisjoint(set(v_c['date']))
        assert set(t_c['date']).isdisjoint(set(c_c['date']))
        assert set(v_c['date']).isdisjoint(set(c_c['date']))
        assert float(t_c['ready'].max()) < float(c_c['issue'].min())

    q_grid = {'max_depth': [3], 'min_samples_leaf': [10], 'l2_regularization': [1.0], 'learning_rate': 0.05, 'max_iter_max': 30, 'iter_step': 10, 'patience': 2}
    cqr_cfg = {'lower_quantile': 0.10, 'upper_quantile': 0.90, 'alpha': 0.10, 'min_interval_width_mbps': 0.5}
    u_mod, s_mod = fit_cqr_pair_blocked(tr, va, cal, q_grid_cfg=q_grid, cqr_cfg=cqr_cfg, seed=42)
    pu = u_mod.predict(df.iloc[:15])
    ps = s_mod.predict(df.iloc[:15])
    assert np.isfinite(pu).all() and (pu >= 0.0).all()
    assert np.isfinite(ps).all() and (ps >= 0.0).all()


def test_empty_radio_linear_and_monotonic_predictors_handle_all_nan_cols():
    df_nan = _synthetic_stream(n_days=5, rows_per_day=25, all_nan_radio=True)
    tr, va, _ = chronological_date_splits(df_nan, val_frac=0.20)
    prep = EmptySafeTabularPreprocessor().fit(tr)
    X_t = prep.transform(va)
    assert X_t.shape[1] == 15 and np.isfinite(X_t).all()

    # Near-zero float jitter (< 1e-6 std) must not blow up out-of-sample scaling
    jitter_df = tr.copy()
    jitter_df['prev_duration_s'] = 59.0 + np.linspace(0.0, 1e-9, len(jitter_df))
    j_prep = EmptySafeTabularPreprocessor().fit(jitter_df)
    probe = va.iloc[:5].copy()
    probe['prev_duration_s'] = 60.0
    j_col_idx = list(probe.columns)
    X_j = j_prep.transform(probe)
    assert np.max(np.abs(X_j)) < 50.0

    ridge = fit_select_linear(tr, va, family='ridge', grid_cfg={'alpha': [1.0]}, seed=42)
    enet = fit_select_linear(tr, va, family='elasticnet', grid_cfg={'alpha': [0.1], 'l1_ratio': [0.5], 'max_iter': 1000}, seed=42)
    mono = fit_select_histgbm(
        tr, va, name='Mono', grid_cfg={'max_depth': [3], 'min_samples_leaf': [10], 'l2_regularization': [1.0], 'max_iter_max': 20, 'iter_step': 10, 'patience': 2},
        monotonic_features=('rsrp', 'sinr', 'ss_rsrp', 'ss_sinr'), seed=42,
    )
    for mod in (ridge, enet, mono):
        p = mod.predict(va)
        assert len(p) == len(va) and np.isfinite(p).all() and (p >= 0.0).all()


def test_monotonic_histgbm_enforces_non_decreasing_rsrp_sinr():
    df = _synthetic_stream(n_days=6, rows_per_day=30, all_nan_radio=False)
    tr, va, _ = chronological_date_splits(df, val_frac=0.20)
    mono = fit_select_histgbm(
        tr, va, name='Mono',
        grid_cfg={'max_depth': [3], 'min_samples_leaf': [10], 'l2_regularization': [0.0], 'max_iter_max': 40, 'iter_step': 10, 'patience': 2},
        monotonic_features=('rsrp', 'sinr', 'ss_rsrp', 'ss_sinr'), seed=42,
    )
    probe = va.iloc[:5].copy()
    probe_hi = probe.copy()
    probe_hi['sinr'] = probe_hi['sinr'] + 15.0
    probe_hi['rsrp'] = probe_hi['rsrp'] + 15.0
    assert (mono.predict(probe_hi) + 1e-12 >= mono.predict(probe)).all()


def test_adjust_pvalues_holm_bh_exact():
    from scipy.stats import false_discovery_control
    raw = [0.005, 0.04, np.nan, 0.02, 0.50]
    holm, bh = adjust_pvalues_holm_bh(raw)
    assert np.isnan(holm[2]) and np.isnan(bh[2])
    # Holm exact sorted [0.005, 0.02, 0.04, 0.50] * [4, 3, 2, 1] -> [0.02, 0.06, 0.08, 0.50]
    np.testing.assert_allclose(holm[[0, 3, 1, 4]], [0.02, 0.06, 0.08, 0.50], rtol=1e-12)
    expected_bh = false_discovery_control([0.005, 0.02, 0.04, 0.50], method='bh')
    np.testing.assert_allclose(bh[[0, 3, 1, 4]], expected_bh, rtol=1e-12)
    assert (holm[[0, 3, 1, 4]] + 1e-12 >= bh[[0, 3, 1, 4]]).all()


def test_campaign_level_bootstrap_reflects_between_campaign_heterogeneity():
    # Construct 6 campaigns: 3 with 100% SLA flip and 3 with 0% SLA flip (0 within-campaign variance)
    cohort_rows = []
    cluster_rows = []
    for coh, camp in COHORT_TO_CAMPAIGN.items():
        dom = 'retrospective' if camp in ('Rome_2023', 'US_Drive3', 'Ireland_Drive') else 'heldout_public'
        flip_camp = camp in ('Rome_2023', 'US_Drive3', 'Ireland_Drive')
        for pol in ('Periodic', 'MARUR'):
            hi = 0.05
            pos_hi = 0.30 if (pol == 'MARUR' and flip_camp) else 0.08
            cohort_rows.append({
                'predictor': 'Dummy', 'cohort': coh, 'domain': dom, 'campaign': camp, 'scenario': 'Recorded',
                'cap_new': 10, 'policy': pol, 'hi': hi, 'positive_high': pos_hi, 'positive_low': pos_hi * 0.8,
                'positive': 20, 'unresolved': 2, 'new_query_attempts': 10, 'positive_rate': 0.20, 'u': 0.02,
            })
            for d in range(3):
                cluster_rows.append({
                    'predictor': 'Dummy', 'cohort': coh, 'domain': dom, 'campaign': camp, 'scenario': 'Recorded',
                    'cap_new': 10, 'policy': pol, 'physical_unit': physical_unit_for_row(coh, f'2023-01-0{d+1}'),
                    'eligible': 50, 'offers': 10,
                    'violations': 3 if (pol == 'MARUR' and flip_camp) else 0,
                    'missing_outcomes': 1, 'queries_charged': 3,
                    'observed_sum': 100.0, 'delivered_sum': 2.0,
                })
    abl = compute_ablation_with_campaign_bootstrap(
        pd.DataFrame(cohort_rows), pd.DataFrame(cluster_rows), candidates=('MARUR',), n_boot=300, seed=42
    )
    sla_row = abl[(abl['scenario_filter'] == 'Recorded') & (abl['factor'] == 'R_vs_Rplus_SLA')].iloc[0]
    assert sla_row['campaigns_k'] == 6
    assert sla_row['camp_boot_ci95_lo'] < sla_row['pct_affected'] < sla_row['camp_boot_ci95_hi']


def test_predictor_robustness_validator_checks_report_and_paper_binding(tmp_path):
    from pathlib import Path
    import shutil
    from scripts.validate_manuscript_consistency import ROOT, validate_predictor_robustness

    validate_predictor_robustness(ROOT)
    # Verify paper binding catches mismatched numbers if a new predictor is cited in manuscript.tex
    fake_doc = ROOT / 'docs/PREDICTOR_ROBUSTNESS.md'
    assert fake_doc.is_file()
    fake_root = tmp_path / 'repo'
    (fake_root / 'results/exploratory').mkdir(parents=True)
    shutil.copytree(ROOT / 'results/exploratory/predictor_robustness', fake_root / 'results/exploratory/predictor_robustness')
    (fake_root / 'docs').mkdir()
    shutil.copy2(fake_doc, fake_root / 'docs/PREDICTOR_ROBUSTNESS.md')
    (fake_root / 'paper').mkdir()
    (fake_root / 'paper/manuscript.tex').write_text('CQR_Scaled_LOCampO achieves 99.9% risk and 88.88% utility.', encoding='utf8')
    (fake_root / 'paper/supplementary.tex').write_text('', encoding='utf8')
    with pytest.raises(ValueError, match='without matching CSV values'):
        validate_predictor_robustness(fake_root)

