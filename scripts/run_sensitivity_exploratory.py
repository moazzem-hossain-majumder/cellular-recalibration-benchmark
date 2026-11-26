"""Exploratory conformal-window, nominal-alpha, and source-predictor sensitivity suite.

Strict integrity boundaries:
  1. Never alters frozen configs, frozen predictors, results/marur, or results/pacer.
  2. Never touches held-out cohorts (Rome_Capacity_Op1/Op2, Oslo_Commute, Ireland_Static).
  3. All alternative predictors are trained strictly on source 2021 Op1 data (dates <= 06.01.2021).
  4. All outputs are written strictly under results/exploratory/sensitivity/ and labeled exploratory.
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
from scripts.clock_frontier import clean_numeric, clock_pairs
from scripts.run_marur import aggregate
from src.data.loader import extract_sessions_8224890, load_raw_8224890
from src.data.splits import create_experiment_splits
from src.evaluation.marur import replay as replay_marur
from src.evaluation.pacer import replay_pacer
from src.models.baselines import HistGradientBoostingThroughputPredictor, QuantileBoostingPredictor
from src.models.neural import GPUThroughputNeuralPredictor

OUT_DIR = ROOT / 'results/exploratory/sensitivity'


def _cluster_rows_from_actions(act: pd.DataFrame, cohort: str) -> pd.DataFrame:
    df = act.copy()
    df['unit'] = [physical_campaign_key(cohort, str(d)) for d in df['date']]
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
        )
    )


def _build_clock_source_op1(allowed_dates: set[str]) -> pd.DataFrame:
    raw = load_raw_8224890()
    op1_raw = raw[raw['Operator'].astype(str).str.strip() == 'Op1'].copy()
    op1_raw['date_str'] = op1_raw['datetime'].dt.strftime('%d.%m.%Y')
    op1_src = op1_raw[op1_raw['date_str'].isin(allowed_dates)].sort_values('datetime').set_index('datetime')
    rate = clean_numeric(op1_src['Mean Netw. DL'])
    rate = rate.where(rate >= 0) * 0.001
    pairs = clock_pairs(rate, op1_src.index.min(), op1_src.index.max(), include_ineligible=False).set_index('time')
    prev = pairs.index - pd.Timedelta(minutes=1)
    times = rate.dropna().index.to_series().resample('min')
    tlast = times.last().reindex(prev)
    pairs['lag_age_s'] = (pairs.index - pd.DatetimeIndex(tlast)).total_seconds()
    pairs['prev_duration_s'] = (pd.DatetimeIndex(tlast) - pd.DatetimeIndex(times.first().reindex(prev))).total_seconds()
    for col in ['rsrp', 'rsrq', 'sinr', 'ss_rsrp', 'ss_rsrq', 'ss_sinr']:
        pairs[col] = op1_src[col].resample('min').last().reindex(prev).to_numpy()
    pairs['y_lag1'] = pairs['lag'].astype(float)
    pairs['has_lte'] = pairs['rsrp'].notna().astype(int)
    pairs['has_nr'] = pairs['ss_rsrp'].notna().astype(int)
    pairs['group_id'] = 2 * pairs['has_lte'] + pairs['has_nr']
    pairs['scenario'] = (
        op1_src['Scenario'].astype(str).str.strip().resample('min').last().reindex(pairs.index).fillna('IS').to_numpy()
    )
    return pairs.dropna(subset=['y_lag1', 'y']).copy()


def run_window_alpha_sensitivity(opp: pd.DataFrame, mcfg: dict, pcfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Task 5a: Exploratory sweep across windows {10, 20, 40} and alphas {0.05, 0.10, 0.20}."""
    rows = []
    cluster_store: list[pd.DataFrame] = []
    for alpha in (0.05, 0.10, 0.20):
        for window in (10, 20, 40):
            cfg_m = dict(mcfg, alpha=alpha, window=window)
            cfg_p = dict(pcfg, alpha=alpha, pacer_obs_window=window)
            for cohort, grp in opp.groupby('cohort', sort=True):
                for model in ('HistGBM', 'Persistence'):
                    col = ('HistGBM' if cohort in ('E1', 'E3') else 'Tree') if model == 'HistGBM' else 'Persistence'
                    data = grp.assign(point=grp[col], date=grp['date'].astype(str))
                    init = data[data['partition'] == 'cal'].sort_values(['issue', 'id']).head(cfg_m['initial_labels'])
                    stream = data[data['partition'] == 'test'].sort_values(['issue', 'id']).reset_index(drop=True)
                    for cap in (10, 40):
                        for policy in ('Frozen', 'Periodic', 'MARUR', 'ACI', 'PACER'):
                            budget = 10 if policy == 'Frozen' else (10 + cap)
                            if policy == 'PACER':
                                act, resp = replay_pacer(init, stream, budget, cfg_p, scenario='Recorded', seed=cfg_p['primary_seed'])
                            else:
                                act, resp = replay_marur(init, stream, policy, budget, cfg_m, scenario='Recorded')
                            st = aggregate(act, resp, initial=cfg_m['initial_labels'])
                            meta = dict(alpha=alpha, window=window, cohort=cohort, model=model, cap_new=cap, policy=policy)
                            rows.append(dict(**meta, **st))
                            cm = _cluster_rows_from_actions(act, cohort).reset_index()
                            for k, v in meta.items():
                                cm[k] = v
                            cluster_store.append(cm)

    df_rows = pd.DataFrame(rows)
    df_cl = pd.concat(cluster_store, ignore_index=True)

    cluster_contrasts = []
    agg_cols = ['eligible', 'positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']
    for (alpha, window, model, cap), grp in df_cl.groupby(['alpha', 'window', 'model', 'cap_new'], sort=True):
        cd = grp.groupby(['unit', 'policy'], sort=True)[agg_cols].sum().reset_index()
        ref = cd[cd['policy'] == 'Periodic'].set_index('unit').sort_index()
        for cand_pol in ('MARUR', 'PACER', 'ACI'):
            cand = cd[cd['policy'] == cand_pol].set_index('unit').sort_index()
            stats = _paired_cluster_stats(cand, ref, n_boot=2000, seed=42)
            # Also capture pooled levels for cand and ref
            pos_cand = cand['positive'].sum()
            pos_ref = ref['positive'].sum()
            cluster_contrasts.append(
                {
                    'alpha': alpha,
                    'window': int(window),
                    'model': model,
                    'cap_new': int(cap),
                    'candidate': cand_pol,
                    'reference': 'Periodic',
                    'cand_u': float(cand['delivered_sum'].sum() / cand['observed_sum'].sum()),
                    'ref_u': float(ref['delivered_sum'].sum() / ref['observed_sum'].sum()),
                    'cand_pos_rate': float(pos_cand / cand['eligible'].sum()),
                    'ref_pos_rate': float(pos_ref / ref['eligible'].sum()),
                    'cand_pos_hi': float((cand['violations'].sum() + cand['unresolved'].sum()) / pos_cand) if pos_cand > 0 else np.nan,
                    'ref_pos_hi': float((ref['violations'].sum() + ref['unresolved'].sum()) / pos_ref) if pos_ref > 0 else np.nan,
                    **stats,
                }
            )
    return df_rows, pd.DataFrame(cluster_contrasts)


def run_predictor_sensitivity(opp: pd.DataFrame, mcfg: dict, pcfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Task 5b: Exploratory evaluation of source-only alternative predictors on retrospective cohorts."""
    raw = load_raw_8224890()
    _, early = extract_sessions_8224890(raw)
    src = early[early['operator'] == 'Op1']
    dev = create_experiment_splits(src, src, 'within_domain', [10])
    src_dates = set(pd.concat([dev.train, dev.val, dev.source_calib])['date'].unique())
    clk_src = _build_clock_source_op1(src_dates)

    predictors = {
        'HistGBM_57': None,  # Authoritative frozen predictor already stored in opp['HistGBM'/'Tree']
        'ThroughputResNet_57': GPUThroughputNeuralPredictor(
            hidden_dim=256, num_blocks=3, epochs=60, batch_size=32, random_seed=42
        ).fit(dev.train, dev.train['target_y'].to_numpy(dtype=float), dev.val, dev.val['target_y'].to_numpy(dtype=float)),
        'QuantileGBM_p10_57': QuantileBoostingPredictor(
            alpha=0.10, n_estimators=80, learning_rate=0.05, random_state=42
        ).fit(dev.train, dev.train['target_y'].to_numpy(dtype=float)),
        'HistGBM_Clock112': HistGradientBoostingThroughputPredictor(
            max_iter=150, max_depth=4, learning_rate=0.05, random_state=42
        ).fit(clk_src, clk_src['y'].to_numpy(dtype=float)),
        'Persistence': None,
    }

    point_rows = []
    policy_rows = []
    cluster_store = []
    for pred_name, pred_obj in predictors.items():
        for cohort, grp in opp.groupby('cohort', sort=True):
            frame = grp.copy()
            frame['date'] = frame['date'].astype(str)
            if pred_name == 'HistGBM_57':
                col = 'HistGBM' if cohort in ('E1', 'E3') else 'Tree'
                frame['point'] = frame[col].astype(float)
            elif pred_name == 'Persistence':
                frame['point'] = frame['Persistence'].astype(float)
            else:
                elig = frame['y_lag1'].notna()
                frame['point'] = np.nan
                if elig.any():
                    frame.loc[elig, 'point'] = np.asarray(pred_obj.predict(frame.loc[elig]), dtype=float)

            test_eval = frame[(frame['partition'] == 'test') & frame['y'].notna() & frame['point'].notna()]
            point_rows.append(
                {
                    'predictor': pred_name,
                    'cohort': cohort,
                    'n_scored': int(len(test_eval)),
                    'mae_mbps': float(np.mean(np.abs(test_eval['point'] - test_eval['y']))),
                    'point_viol_rate': float(np.mean(test_eval['point'] > test_eval['y'])),
                }
            )

            init = frame[frame['partition'] == 'cal'].sort_values(['issue', 'id']).head(mcfg['initial_labels'])
            stream = frame[frame['partition'] == 'test'].sort_values(['issue', 'id']).reset_index(drop=True)
            for cap in (10, 40):
                for policy in ('Frozen', 'Periodic', 'MARUR', 'ACI', 'PACER'):
                    budget = 10 if policy == 'Frozen' else (10 + cap)
                    if policy == 'PACER':
                        act, resp = replay_pacer(init, stream, budget, pcfg, scenario='Recorded', seed=pcfg['primary_seed'])
                    else:
                        act, resp = replay_marur(init, stream, policy, budget, mcfg, scenario='Recorded')
                    st = aggregate(act, resp, initial=mcfg['initial_labels'])
                    meta = dict(predictor=pred_name, cohort=cohort, cap_new=cap, policy=policy)
                    policy_rows.append(dict(**meta, **st))
                    cm = _cluster_rows_from_actions(act, cohort).reset_index()
                    for k, v in meta.items():
                        cm[k] = v
                    cluster_store.append(cm)

    df_point = pd.DataFrame(point_rows)
    df_policy = pd.DataFrame(policy_rows)
    df_cl = pd.concat(cluster_store, ignore_index=True)

    cluster_contrasts = []
    agg_cols = ['eligible', 'positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']
    for (pred_name, cap), grp in df_cl.groupby(['predictor', 'cap_new'], sort=True):
        cd = grp.groupby(['unit', 'policy'], sort=True)[agg_cols].sum().reset_index()
        ref = cd[cd['policy'] == 'Periodic'].set_index('unit').sort_index()
        for cand_pol in ('MARUR', 'PACER'):
            cand = cd[cd['policy'] == cand_pol].set_index('unit').sort_index()
            stats = _paired_cluster_stats(cand, ref, n_boot=2000, seed=42)
            pos_cand = cand['positive'].sum()
            pos_ref = ref['positive'].sum()
            cluster_contrasts.append(
                {
                    'predictor': pred_name,
                    'cap_new': int(cap),
                    'candidate': cand_pol,
                    'reference': 'Periodic',
                    'cand_u': float(cand['delivered_sum'].sum() / cand['observed_sum'].sum()),
                    'ref_u': float(ref['delivered_sum'].sum() / ref['observed_sum'].sum()),
                    'cand_pos_rate': float(pos_cand / cand['eligible'].sum()),
                    'ref_pos_rate': float(pos_ref / ref['eligible'].sum()),
                    'cand_pos_hi': float((cand['violations'].sum() + cand['unresolved'].sum()) / pos_cand) if pos_cand > 0 else np.nan,
                    'ref_pos_hi': float((ref['violations'].sum() + ref['unresolved'].sum()) / pos_ref) if pos_ref > 0 else np.nan,
                    **stats,
                }
            )
    return df_point, df_policy, pd.DataFrame(cluster_contrasts)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc).isoformat()
    opp = pd.read_csv(ROOT / 'results/marur/opportunities.csv.gz', float_precision='round_trip', low_memory=False)
    mcfg = json.loads((ROOT / 'configs/marur.json').read_text(encoding='utf8'))
    pcfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))

    df_wa, df_wa_cl = run_window_alpha_sensitivity(opp, mcfg, pcfg)
    df_pt, df_pr, df_pr_cl = run_predictor_sensitivity(opp, mcfg, pcfg)

    df_wa.to_csv(OUT_DIR / 'window_alpha_sensitivity.csv', index=False)
    df_wa_cl.to_csv(OUT_DIR / 'window_alpha_clusters.csv', index=False)
    df_pt.to_csv(OUT_DIR / 'predictor_point_accuracy.csv', index=False)
    df_pr.to_csv(OUT_DIR / 'predictor_sensitivity.csv', index=False)
    df_pr_cl.to_csv(OUT_DIR / 'predictor_sensitivity_clusters.csv', index=False)

    receipt = {
        'start_utc': start,
        'end_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'exploratory_retrospective_only',
        'heldout_cohorts_touched': False,
        'window_alpha_rows': int(len(df_wa)),
        'predictor_rows': int(len(df_pr)),
        'sha256': {
            str(p.relative_to(ROOT).as_posix()): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT_DIR.glob('*.csv'))
        },
    }
    (OUT_DIR / 'execution.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'sha256'}, indent=2))
    print('\n=== Task 5a: MARUR vs Periodic across window & alpha (HistGBM, cap=10 & 40) ===')
    sub5a = df_wa_cl[(df_wa_cl['model'] == 'HistGBM') & (df_wa_cl['candidate'] == 'MARUR')]
    print(sub5a[['alpha', 'window', 'cap_new', 'cand_pos_rate', 'cand_pos_hi', 'ref_pos_hi', 'cand_u', 'ref_u', 'eq_du_mean', 't_du_lo', 't_du_hi']].to_string(index=False))
    print('\n=== Task 5b: Predictor Point MAE & MARUR vs Periodic Cluster Summary ===')
    print(df_pt.pivot(index='cohort', columns='predictor', values='mae_mbps').round(2).to_string())
    sub5b = df_pr_cl[df_pr_cl['candidate'] == 'MARUR']
    print(sub5b[['predictor', 'cap_new', 'cand_pos_rate', 'cand_pos_hi', 'ref_pos_hi', 'cand_u', 'ref_u', 'eq_du_mean', 't_du_lo', 't_du_hi']].to_string(index=False))


if __name__ == '__main__':
    main()
