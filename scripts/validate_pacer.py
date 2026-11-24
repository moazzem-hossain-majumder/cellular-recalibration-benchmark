"""Independent verifier for frozen Path A PACER artifacts and Theorem 1 checks."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_trip_level_inference import _paired_cluster_stats, physical_campaign_key
from src.evaluation.pacer import replay_pacer, theoretical_excess_bound

PACER_DIR = ROOT / 'results/pacer'


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def verify_lock_and_artifacts() -> dict:
    lock = json.loads((PACER_DIR / 'preregistration_lock.json').read_text(encoding='utf8'))
    for rel, expected in lock['sha256_lf'].items():
        actual = hashlib.sha256((ROOT / rel).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        _require(actual == expected, f'Pre-registration SHA-256 mismatch for {rel}: {actual} != {expected}')

    cfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))
    _require(cfg == lock['config'], 'configs/pacer.json does not match preregistration lock')
    _require(not cfg['tuning_allowed_after_unseal'], 'tuning_allowed_after_unseal must remain false')

    untouched = pd.read_csv(PACER_DIR / 'untouched_opportunities.csv.gz')
    expected_untouched = {'Rome_Capacity_Op1', 'Rome_Capacity_Op2', 'Oslo_Commute', 'Ireland_Static'}
    _require(set(untouched['cohort'].unique()) == expected_untouched, 'Unexpected untouched cohort set')

    for cohort, grp in untouched.groupby('cohort'):
        cal = grp[grp['partition'] == 'cal']
        test = grp[grp['partition'] == 'test']
        _require(len(cal) == cfg['initial_labels'], f'{cohort}: expected 10 initial labels, got {len(cal)}')
        _require(cal['y'].notna().all() and cal['HistGBM'].notna().all() and cal['Persistence'].notna().all(),
                 f'{cohort}: initial labels incomplete')
        _require(cal['ready'].max() <= test['issue'].min(), f'{cohort}: chronological cal/test overlap')

    summary = pd.read_csv(PACER_DIR / 'pacer_summary.csv')
    clusters = pd.read_csv(PACER_DIR / 'pacer_cluster_dates.csv')
    contrasts = pd.read_csv(PACER_DIR / 'pacer_paired_contrasts.csv')
    seeds = pd.read_csv(PACER_DIR / 'pacer_seed_sensitivity.csv')
    report = json.loads((PACER_DIR / 'pacer_audit_report.json').read_text(encoding='utf8'))

    _require(report['prospective_trips_collected'] == 0, 'prospective_trips_collected must stay 0')
    _require(report['preregistration_lock_verified'] is True, 'preregistration_lock_verified must be true')

    # Recompute cluster-level metrics and match summary row-for-row
    key_cols = ['cohort', 'model', 'scenario', 'cap_new', 'policy']
    cl_sums = clusters.groupby(key_cols, as_index=False)[
        ['eligible', 'positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum', 'queries_new']
    ].sum()
    merged = summary.merge(cl_sums, on=key_cols, suffixes=('', '_cl'))
    _require(len(merged) == len(summary), 'Missing cluster aggregation for summary rows')
    _require((merged['queries_new'] <= merged['cap_new']).all(), 'Query cap exceeded in cluster ledger')
    np.testing.assert_allclose(merged['eligible'], merged['eligible_cl'])
    np.testing.assert_allclose(merged['positive'], merged['positive_cl'])
    np.testing.assert_allclose(merged['violations'], merged['violations_cl'])
    np.testing.assert_allclose(merged['unresolved'], merged['unresolved_cl'])
    np.testing.assert_allclose(merged['observed_sum'], merged['observed_sum_cl'], rtol=1e-9, atol=1e-9)
    np.testing.assert_allclose(merged['delivered_sum'], merged['delivered_sum_cl'], rtol=1e-9, atol=1e-9)
    np.testing.assert_allclose(
        merged['u'], merged['delivered_sum'] / merged['observed_sum'], rtol=1e-9, atol=1e-12
    )
    pos_mask = merged['positive'] > 0
    np.testing.assert_allclose(
        merged.loc[pos_mask, 'positive_high'],
        (merged.loc[pos_mask, 'violations'] + merged.loc[pos_mask, 'unresolved']) / merged.loc[pos_mask, 'positive'],
        rtol=1e-9, atol=1e-12,
    )

    # Check exact agreement with prior authoritative results/marur/summary.csv on overlapping retrospective runs
    old_marur = pd.read_csv(ROOT / 'results/marur/summary.csv')
    old_marur['cap_new'] = old_marur['initial_label_plus_query_count'] - 10
    overlap = summary[(summary['domain'] == 'retrospective') & (summary['cap_new'].isin([10, 40]))].merge(
        old_marur,
        on=['cohort', 'model', 'scenario', 'cap_new', 'policy'],
        suffixes=('_new', '_old'),
    )
    _require(len(overlap) > 0, 'Expected overlapping cells with results/marur/summary.csv')
    np.testing.assert_allclose(overlap['u_new'], overlap['u_old'], rtol=1e-10, atol=1e-12, equal_nan=True)
    np.testing.assert_allclose(overlap['positive_high_new'], overlap['positive_high_old'], rtol=1e-10, atol=1e-12, equal_nan=True)

    # Verify Theorem 1 empirical seed average <= bound across all 40 cells
    seed_means = seeds.groupby(['domain', 'cohort', 'model', 'cap_new'], as_index=False).agg(
        mean_excess=('selective_excess_upper', 'mean'),
        bound=('theorem1_bound', 'first'),
    )
    _require(len(seed_means) == 40, f'Expected 40 seed_mean cells, got {len(seed_means)}')
    _require((seed_means['mean_excess'] <= seed_means['bound'] + 1e-12).all(), 'Theorem 1 upper bound violated')

    # Recompute one combined pooled paired cluster contrast directly and verify exact equality
    for ref_pol in ('Periodic', 'MARUR'):
        row = contrasts[
            (contrasts['scope'] == 'AllCohortsPooled')
            & (contrasts['model'] == 'HistGBM')
            & (contrasts['scenario'] == 'Recorded')
            & (contrasts['cap_new'] == 10)
            & (contrasts['reference'] == ref_pol)
        ].iloc[0]
        p_agg = clusters[
            (clusters['model'] == 'HistGBM') & (clusters['scenario'] == 'Recorded')
            & (clusters['cap_new'] == 10) & (clusters['policy'] == 'PACER')
        ].groupby('unit', sort=True)[['eligible', 'positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']].sum()
        r_agg = clusters[
            (clusters['model'] == 'HistGBM') & (clusters['scenario'] == 'Recorded')
            & (clusters['cap_new'] == 10) & (clusters['policy'] == ref_pol)
        ].groupby('unit', sort=True)[['eligible', 'positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']].sum()
        recomp = _paired_cluster_stats(p_agg, r_agg, n_boot=2000, seed=cfg['primary_seed'])
        _require(recomp['clusters'] == 42, f'Expected 42 physical clusters, got {recomp["clusters"]}')
        np.testing.assert_allclose(row['pool_du'], recomp['pool_du'], atol=1e-12)
        np.testing.assert_allclose(row['pool_dpos_hi'], recomp['pool_dpos_hi'], atol=1e-12)

    # Deterministic replay spot-check on untouched Ireland_Static HistGBM cap=40
    sub_ir = untouched[(untouched['cohort'] == 'Ireland_Static') & (untouched['partition'].isin(['cal', 'test']))].copy()
    sub_ir['point'] = sub_ir['HistGBM'].astype(float)
    cal_ir = sub_ir[sub_ir['partition'] == 'cal'].sort_values(['issue', 'id'])
    test_ir = sub_ir[sub_ir['partition'] == 'test'].sort_values(['issue', 'id']).reset_index(drop=True)
    act_ir, _ = replay_pacer(cal_ir, test_ir, 50, cfg, scenario='Recorded', seed=cfg['primary_seed'])
    _require((act_ir['last_feedback'] <= act_ir['issue']).all(), 'Causality check failed on replay')
    _require(int(act_ir['query'].sum()) <= 40, 'Replay exceeded new query cap')
    expected_row = summary[
        (summary['cohort'] == 'Ireland_Static') & (summary['model'] == 'HistGBM')
        & (summary['scenario'] == 'Recorded') & (summary['cap_new'] == 40) & (summary['policy'] == 'PACER')
    ].iloc[0]
    np.testing.assert_allclose(float((act_ir['lower'] > 0).mean()), float(expected_row['positive_rate']), atol=1e-12)

    return report


def main() -> None:
    report = verify_lock_and_artifacts()
    print('PACER audit verification passed:', json.dumps(report['physical_clusters']))


if __name__ == '__main__':
    main()
