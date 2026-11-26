"""Frozen Path A evaluation across held-out public archives & retrospective cohorts.

Enforces SHA-256 frozen-configuration checksum verification before & after scoring,
executes PACER alongside Frozen, Periodic, Early, ACI, DecayingOGD, and MARUR
on identical opportunities, computes Theorem 1 empirical verification, and
computes physical-campaign cluster inference without modifying prior MARUR runs.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_trip_level_inference import _paired_cluster_stats, physical_campaign_key
from scripts.build_untouched_cohorts import build_all
from scripts.run_marur import aggregate
from src.evaluation.marur import replay as replay_marur
from src.evaluation.pacer import replay_pacer, theoretical_excess_bound

OUT_DIR = ROOT / 'results/pacer'


def _verify_frozen_checksums() -> dict:
    lock_path = OUT_DIR / 'frozen_config_checksums.json'
    if not lock_path.exists():
        raise RuntimeError('Missing results/pacer/frozen_config_checksums.json')
    lock = json.loads(lock_path.read_text(encoding='utf8'))
    for rel, expected in lock['sha256_lf'].items():
        actual = hashlib.sha256((ROOT / rel).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        if actual != expected:
            raise RuntimeError(f'Frozen checksum mismatch in {rel}: {actual} != {expected}')
    return lock


def _load_all_cohorts() -> pd.DataFrame:
    untouched = build_all()
    retro = pd.read_csv(ROOT / 'results/marur/opportunities.csv.gz', low_memory=False)
    retro = retro[retro['partition'].isin(['cal', 'test'])].copy()
    retro['HistGBM'] = np.where(retro['HistGBM'].notna(), retro['HistGBM'], retro['Tree'])
    retro['domain'] = 'retrospective'
    retro['physical_unit'] = [physical_campaign_key(c, str(d)) for c, d in zip(retro['cohort'], retro['date'])]
    cols = [
        'cohort', 'partition', 'date', 'issue', 'ready', 'id', 'pattern', 'y',
        'Persistence', 'HistGBM', 'trace', 'physical_unit', 'domain',
    ]
    return pd.concat([untouched[cols], retro[cols]], ignore_index=True)


def _cluster_metrics(ledger: pd.DataFrame, unit_map: dict[str, str]) -> pd.DataFrame:
    df = ledger.copy()
    df['unit'] = df['id'].map(unit_map).fillna(df['date'].astype(str))
    df['eligible_num'] = df['eligible'].astype(int)
    df['pos_num'] = (df['eligible'] & (df['lower'] > 0)).astype(int)
    df['valid'] = df['eligible'] & df['y'].notna()
    df['viol_num'] = (df['eligible'] & (df['lower'] > 0) & df['y'].notna() & (df['lower'] > df['y'])).astype(int)
    df['unres_num'] = (df['eligible'] & (df['lower'] > 0) & df['y'].isna()).astype(int)
    df['obs_y'] = np.where(df['valid'], df['y'], 0.0)
    df['deliv'] = np.where(df['valid'], np.minimum(df['lower'], df['y']), 0.0)
    return (
        df.groupby('unit', sort=True)
        .agg(
            eligible=('eligible_num', 'sum'),
            positive=('pos_num', 'sum'),
            violations=('viol_num', 'sum'),
            unresolved=('unres_num', 'sum'),
            observed_sum=('obs_y', 'sum'),
            delivered_sum=('deliv', 'sum'),
            queries_new=('query', 'sum'),
            updates=('updates', 'last'),
        )
    )


def run_study() -> None:
    lock = _verify_frozen_checksums()
    pacer_cfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))
    marur_cfg = json.loads((ROOT / 'configs/marur.json').read_text(encoding='utf8'))
    if pacer_cfg != lock['config']:
        raise RuntimeError('configs/pacer.json diverged from frozen configuration checksums')

    data = _load_all_cohorts()
    policies_baseline = ['Frozen', 'Periodic', 'ACI', 'DecayingOGD', 'MARUR', 'Early']
    summary_rows = []
    cluster_rows = []
    seed_rows = []
    ledgers: dict[tuple[str, str, str, int, str], pd.DataFrame] = {}

    for cohort, grp in data.groupby('cohort', sort=False):
        domain = str(grp['domain'].iloc[0])
        unit_map = dict(zip(grp['id'].astype(str), grp['physical_unit'].astype(str)))
        for model in ('HistGBM', 'Persistence'):
            frame = grp[grp['partition'].isin(['cal', 'test'])].copy()
            frame['point'] = frame[model].astype(float)
            cal = frame[frame['partition'] == 'cal'].sort_values(['issue', 'id']).head(pacer_cfg['initial_labels'])
            test = frame[frame['partition'] == 'test'].sort_values(['issue', 'id']).reset_index(drop=True)
            assert len(cal) == pacer_cfg['initial_labels']
            assert cal['ready'].max() <= test['issue'].min()

            for scenario in ('Recorded', 'QueryCensor20'):
                # Zero-cost baseline recorded once at budget=10
                act_f, resp_f = replay_marur(cal, test, 'Frozen', 10, marur_cfg, scenario=scenario)
                stat_f = aggregate(act_f, resp_f, initial=pacer_cfg['initial_labels'])
                stat_f.update(
                    cohort=cohort, domain=domain, model=model, scenario=scenario,
                    cap_new=0, budget=10, policy='Frozen', seed=0,
                    n_units=int(test['physical_unit'].nunique()),
                    n_dates=int(test['date'].nunique()),
                    selective_excess_upper=float(stat_f['positive_rate'] * (stat_f['positive_high'] - pacer_cfg['alpha']))
                    if pd.notna(stat_f['positive_high']) else 0.0,
                    theorem1_bound=np.nan,
                )
                summary_rows.append(stat_f)
                ledgers[(cohort, model, scenario, 0, 'Frozen')] = act_f
                cm_f = _cluster_metrics(act_f, unit_map).reset_index()
                cm_f['cohort'], cm_f['domain'], cm_f['model'], cm_f['scenario'], cm_f['cap_new'], cm_f['policy'] = (
                    cohort, domain, model, scenario, 0, 'Frozen'
                )
                cluster_rows.append(cm_f)

                for cap_new in (10, 40):
                    budget = pacer_cfg['initial_labels'] + cap_new
                    t1_bound = theoretical_excess_bound(
                        alpha=pacer_cfg['alpha'],
                        gamma=pacer_cfg['pacer_gamma'],
                        a_veto=pacer_cfg['pacer_veto'],
                        n_blocks=min(cap_new, len(test)),
                        n_rows=len(test),
                        max_block_delay=1,
                    )
                    for policy in policies_baseline[1:] + ['PACER']:
                        if policy == 'PACER':
                            act, resp = replay_pacer(
                                cal, test, budget, pacer_cfg, scenario=scenario, seed=pacer_cfg['primary_seed']
                            )
                        else:
                            act, resp = replay_marur(cal, test, policy, budget, marur_cfg, scenario=scenario)
                        st = aggregate(act, resp, initial=pacer_cfg['initial_labels'])
                        sel_exc = (
                            float(st['positive_rate'] * (st['positive_high'] - pacer_cfg['alpha']))
                            if pd.notna(st['positive_high'])
                            else 0.0
                        )
                        st.update(
                            cohort=cohort, domain=domain, model=model, scenario=scenario,
                            cap_new=cap_new, budget=budget, policy=policy,
                            seed=pacer_cfg['primary_seed'] if policy == 'PACER' else 0,
                            n_units=int(test['physical_unit'].nunique()),
                            n_dates=int(test['date'].nunique()),
                            selective_excess_upper=sel_exc,
                            theorem1_bound=t1_bound if policy == 'PACER' else np.nan,
                        )
                        summary_rows.append(st)
                        ledgers[(cohort, model, scenario, cap_new, policy)] = act
                        cm = _cluster_metrics(act, unit_map).reset_index()
                        cm['cohort'], cm['domain'], cm['model'], cm['scenario'], cm['cap_new'], cm['policy'] = (
                            cohort, domain, model, scenario, cap_new, policy
                        )
                        cluster_rows.append(cm)

                    # PACER sensitivity across pre-specified seeds on Recorded feedback
                    if scenario == 'Recorded':
                        for sd in pacer_cfg['sensitivity_seeds']:
                            act_s, resp_s = replay_pacer(cal, test, budget, pacer_cfg, scenario='Recorded', seed=sd)
                            st_s = aggregate(act_s, resp_s, initial=pacer_cfg['initial_labels'])
                            sel_s = (
                                float(st_s['positive_rate'] * (st_s['positive_high'] - pacer_cfg['alpha']))
                                if pd.notna(st_s['positive_high'])
                                else 0.0
                            )
                            st_s.update(
                                cohort=cohort, domain=domain, model=model, scenario='Recorded',
                                cap_new=cap_new, budget=budget, policy='PACER', seed=sd,
                                theorem1_bound=t1_bound, selective_excess_upper=sel_s,
                            )
                            seed_rows.append(st_s)

    summary_df = pd.DataFrame(summary_rows)
    cluster_df = pd.concat(cluster_rows, ignore_index=True)
    seed_df = pd.DataFrame(seed_rows)

    # Paired physical-campaign cluster contrasts: PACER vs comparators
    contrast_rows = []
    for scope_name, domains in (
        ('UntouchedHeldOut', ('untouched_heldout',)),
        ('Retrospective', ('retrospective',)),
        ('AllCohortsPooled', ('untouched_heldout', 'retrospective')),
    ):
        for model in ('HistGBM', 'Persistence'):
            for scenario in ('Recorded', 'QueryCensor20'):
                for cap_new in (10, 40):
                    p_sub = cluster_df[
                        (cluster_df['domain'].isin(domains))
                        & (cluster_df['model'] == model)
                        & (cluster_df['scenario'] == scenario)
                        & (cluster_df['cap_new'] == cap_new)
                        & (cluster_df['policy'] == 'PACER')
                    ]
                    p_agg = p_sub.groupby('unit', sort=True)[
                        ['eligible', 'positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']
                    ].sum()
                    for ref_pol in ('Frozen', 'Periodic', 'ACI', 'DecayingOGD', 'MARUR', 'Early'):
                        ref_cap = 0 if ref_pol == 'Frozen' else cap_new
                        r_sub = cluster_df[
                            (cluster_df['domain'].isin(domains))
                            & (cluster_df['model'] == model)
                            & (cluster_df['scenario'] == scenario)
                            & (cluster_df['cap_new'] == ref_cap)
                            & (cluster_df['policy'] == ref_pol)
                        ]
                        r_agg = r_sub.groupby('unit', sort=True)[
                            ['eligible', 'positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']
                        ].sum()
                        stats = _paired_cluster_stats(p_agg, r_agg, n_boot=2000, seed=pacer_cfg['primary_seed'])
                        contrast_rows.append(
                            {
                                'scope': scope_name,
                                'model': model,
                                'scenario': scenario,
                                'cap_new': cap_new,
                                'reference': ref_pol,
                                **stats,
                            }
                        )

    contrast_df = pd.DataFrame(contrast_rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUT_DIR / 'pacer_summary.csv', index=False)
    cluster_df.to_csv(OUT_DIR / 'pacer_cluster_dates.csv', index=False)
    seed_df.to_csv(OUT_DIR / 'pacer_seed_sensitivity.csv', index=False)
    contrast_df.to_csv(OUT_DIR / 'pacer_paired_contrasts.csv', index=False)

    # Check Theorem 1 empirical average excess across seeds & cohorts
    seed_mean = (
        seed_df.groupby(['domain', 'cohort', 'model', 'cap_new'], as_index=False)
        .agg(
            mean_excess=('selective_excess_upper', 'mean'),
            bound=('theorem1_bound', 'first'),
        )
    )
    seed_mean['satisfies_bound'] = seed_mean['mean_excess'] <= seed_mean['bound'] + 1e-12

    # Post-run checksum verification
    _verify_frozen_checksums()
    audit_report = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'frozen_config_checksums_verified': True,
        'heldout_cohorts': sorted(data.loc[data['domain'] == 'untouched_heldout', 'cohort'].unique().tolist()),
        'retrospective_cohorts': sorted(data.loc[data['domain'] == 'retrospective', 'cohort'].unique().tolist()),
        'physical_clusters': {
            'heldout_public': int(data.loc[(data['domain'] == 'untouched_heldout') & (data['partition'] == 'test'), 'physical_unit'].nunique()),
            'retrospective': int(data.loc[(data['domain'] == 'retrospective') & (data['partition'] == 'test'), 'physical_unit'].nunique()),
        },
        'prospective_trips_collected': 0,
        'theorem1_mean_excess_checks': {
            'total_cells': int(len(seed_mean)),
            'all_within_bound': bool(seed_mean['satisfies_bound'].all()),
            'max_mean_excess': float(seed_mean['mean_excess'].max()),
            'min_theorem1_bound': float(seed_mean['bound'].min()),
        },
    }
    (OUT_DIR / 'pacer_audit_report.json').write_text(json.dumps(audit_report, indent=2), encoding='utf8')
    print(json.dumps(audit_report, indent=2))


if __name__ == '__main__':
    run_study()
