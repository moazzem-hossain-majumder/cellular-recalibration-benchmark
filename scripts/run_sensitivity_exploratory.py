"""Exploratory power/equivalence, window/alpha, predictor, and leave-one-cohort-out suite.

Strict integrity boundaries:
  1. Never alters frozen configs, frozen predictors, results/marur, or results/pacer.
  2. Never tunes on held-out cohorts (Rome_Capacity_Op1/Op2, Oslo_Commute, Ireland_Static);
     held-out sensitivity sweeps run frozen parameters/predictors under an explicit exploratory label.
  3. All alternative predictors are trained strictly on source data (2021 Op1 or pre-2010-10-01 Oslo bus).
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
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_trip_level_inference import _paired_cluster_stats, physical_campaign_key
from scripts.build_untouched_cohorts import (
    _ireland_static_ticks,
    _load_frozen_rome_model,
    _rome_capacity_ticks,
)
from scripts.clock_frontier import clean_numeric, clock_pairs
from scripts.replay_oslo_playback import BUS, OUT as OSLO_META_DIR
from scripts.run_marur import aggregate
from src.audit.recalibration_audit import _solve_mde_t
from src.data.loader import extract_sessions_8224890, load_raw_8224890
from src.data.splits import create_experiment_splits
from src.evaluation.marur import replay as replay_marur
from src.evaluation.pacer import replay_pacer
from src.models.baselines import HistGradientBoostingThroughputPredictor, QuantileBoostingPredictor
from src.models.neural import GPUThroughputNeuralPredictor

OUT_DIR = ROOT / 'results/exploratory/sensitivity'


def _cluster_rows_from_actions(act: pd.DataFrame, cohort: str) -> pd.DataFrame:
    df = act.copy()
    if cohort in ('Rome_Capacity_Op1', 'Rome_Capacity_Op2'):
        df['unit'] = 'RomeCap:' + df['date'].astype(str)
    elif cohort == 'Oslo_Commute':
        df['unit'] = 'Oslo:' + df['date'].astype(str)
    elif cohort == 'Ireland_Static':
        df['unit'] = 'IrelandStatic:' + df['date'].astype(str)
    else:
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


def _build_oslo_bus_quantile_predictor(oslo_cutoff_iso: str) -> HistGradientBoostingRegressor:
    split = pd.Timestamp('2010-10-01', tz='UTC')
    manifest = json.loads((OSLO_META_DIR / 'dataset_manifest.json').read_text(encoding='utf8'))
    frames = []
    for name in manifest['norway_files']:
        d = pd.read_csv(BUS / name, sep=r'\s+', header=None, names=['unix', 'ms', 'lat', 'lon', 'bytes', 'elapsed'])
        d = d.sort_values('ms', kind='stable')
        valid = (d['bytes'] >= 0) & (d['elapsed'] > 0) & (d['ms'].diff().eq(d['elapsed']) | (d.index == d.index[0]))
        rate = (.008 * d['bytes'] / d['elapsed']).where(valid)
        ser = pd.Series(rate.to_numpy(), index=pd.to_datetime(d['unix'], unit='s', utc=True)).dropna()
        ser = ser.groupby(level=0).last()
        pairs = clock_pairs(ser, ser.index.min(), ser.index.max(), include_ineligible=False)
        last_min = ser.resample('min').last()
        lag2 = last_min.reindex(pairs['time'] - pd.Timedelta(minutes=2)).to_numpy()
        pairs['lag2'] = np.where(np.isnan(lag2), pairs['lag'], lag2)
        frames.append(pairs)
    bus_all = pd.concat(frames, ignore_index=True)
    tr = bus_all[(bus_all['end'] < split) & bus_all['lag'].notna() & bus_all['lag2'].notna() & bus_all['y'].notna()]
    return HistGradientBoostingRegressor(
        loss='quantile', quantile=0.10, max_iter=100, max_depth=5, learning_rate=0.05, random_state=42
    ).fit(tr[['lag', 'lag2']], tr['y'])


def run_power_and_equivalence() -> pd.DataFrame:
    """Task 2: Compute 80%-power MDE and TOST (+-1.0, +-1.5, +-2.0, +-3.0 pp) from frozen cluster ledgers."""
    p_cl = pd.read_csv(ROOT / 'results/pacer/pacer_cluster_dates.csv')
    rows = []
    specs = [
        ('Retrospective', 'retrospective', 10, 'MARUR'),
        ('Retrospective', 'retrospective', 10, 'PACER'),
        ('Retrospective', 'retrospective', 40, 'MARUR'),
        ('Retrospective', 'retrospective', 40, 'PACER'),
        ('HeldOut', 'untouched_heldout', 10, 'PACER'),
        ('HeldOut', 'untouched_heldout', 10, 'MARUR'),
        ('HeldOut', 'untouched_heldout', 40, 'PACER'),
        ('HeldOut', 'untouched_heldout', 40, 'MARUR'),
        ('AllCohorts', 'all', 10, 'PACER'),
        ('AllCohorts', 'all', 10, 'MARUR'),
        ('AllCohorts', 'all', 40, 'PACER'),
        ('AllCohorts', 'all', 40, 'MARUR'),
    ]
    for scope, dom_filter, cap, cand in specs:
        sub = p_cl[(p_cl['model'] == 'HistGBM') & (p_cl['scenario'] == 'Recorded') & (p_cl['cap_new'] == cap)]
        if dom_filter != 'all':
            sub = sub[sub['domain'] == dom_filter]
        agg = sub.groupby(['unit', 'policy'], as_index=False)[['delivered_sum', 'observed_sum']].sum()
        piv = agg.pivot(index='unit', columns='policy')
        diff = (100.0 * (piv['delivered_sum'][cand] / piv['observed_sum'][cand] - piv['delivered_sum']['Periodic'] / piv['observed_sum']['Periodic'])).dropna()
        n = int(len(diff))
        mean = float(diff.mean())
        sd = float(diff.std(ddof=1))
        se = sd / float(np.sqrt(n))
        t95_lo, t95_hi = stats.t.interval(0.95, df=n - 1, loc=mean, scale=se)
        t90_lo, t90_hi = stats.t.interval(0.90, df=n - 1, loc=mean, scale=se)
        mde80 = _solve_mde_t(se, n - 1, alpha=0.05, power=0.80)
        tost_1 = float(max(1.0 - stats.t.cdf((mean + 1.0) / se, df=n - 1), stats.t.cdf((mean - 1.0) / se, df=n - 1)))
        tost_15 = float(max(1.0 - stats.t.cdf((mean + 1.5) / se, df=n - 1), stats.t.cdf((mean - 1.5) / se, df=n - 1)))
        tost_2 = float(max(1.0 - stats.t.cdf((mean + 2.0) / se, df=n - 1), stats.t.cdf((mean - 2.0) / se, df=n - 1)))
        tost_3 = float(max(1.0 - stats.t.cdf((mean + 3.0) / se, df=n - 1), stats.t.cdf((mean - 3.0) / se, df=n - 1)))
        rows.append(
            {
                'scope': scope,
                'cap_new': cap,
                'candidate': cand,
                'reference': 'Periodic',
                'clusters': n,
                'eq_du_mean_pp': mean,
                'between_cluster_sd_pp': sd,
                'se_pp': se,
                't_ci95_lo_pp': float(t95_lo),
                't_ci95_hi_pp': float(t95_hi),
                't_ci90_lo_pp': float(t90_lo),
                't_ci90_hi_pp': float(t90_hi),
                'mde80_pp': mde80,
                'tost_p_1pp': tost_1,
                'tost_p_15pp': tost_15,
                'tost_p_2pp': tost_2,
                'tost_p_3pp': tost_3,
                'equiv_1pp': bool(tost_1 < 0.05),
                'equiv_2pp': bool(tost_2 < 0.05),
            }
        )
    return pd.DataFrame(rows)


def run_leave_one_cohort_out() -> pd.DataFrame:
    """Task 3: Verify conclusions under leave-one-cohort-out across all 10 cohorts."""
    s = pd.read_csv(ROOT / 'results/pacer/pacer_summary.csv')
    cl = pd.read_csv(ROOT / 'results/pacer/pacer_cluster_dates.csv')
    cohorts = sorted(s['cohort'].unique())
    rows = []
    for drop_c in ['None'] + cohorts:
        sub_s = s[(s['model'] == 'HistGBM') & (s['scenario'] == 'Recorded') & (s['cap_new'].isin([10, 40])) & (s['policy'].isin(['Periodic', 'MARUR', 'PACER']))]
        sub_cl = cl[(cl['model'] == 'HistGBM') & (cl['scenario'] == 'Recorded') & (cl['cap_new'].isin([10, 40]))]
        if drop_c != 'None':
            sub_s = sub_s[sub_s['cohort'] != drop_c]
            sub_cl = sub_cl[sub_cl['cohort'] != drop_c]
        r_vals = 100.0 * sub_s['positive_high'].dropna()
        u_vals = 100.0 * sub_s['u'].dropna()
        mob_s = sub_s[sub_s['cohort'] != 'Ireland_Static']
        mob_r = 100.0 * mob_s['positive_high'].dropna()

        c10 = sub_cl[sub_cl['cap_new'] == 10].groupby(['unit', 'policy'], as_index=False)[['delivered_sum', 'observed_sum', 'violations', 'unresolved', 'positive']].sum()
        p10 = c10.pivot(index='unit', columns='policy')
        du_mar10 = (100.0 * (p10['delivered_sum']['MARUR'] / p10['observed_sum']['MARUR'] - p10['delivered_sum']['Periodic'] / p10['observed_sum']['Periodic'])).dropna()
        du_pac10 = (100.0 * (p10['delivered_sum']['PACER'] / p10['observed_sum']['PACER'] - p10['delivered_sum']['Periodic'] / p10['observed_sum']['Periodic'])).dropna()

        c40 = sub_cl[sub_cl['cap_new'] == 40].groupby(['unit', 'policy'], as_index=False)[['delivered_sum', 'observed_sum']].sum()
        p40 = c40.pivot(index='unit', columns='policy')
        du_pac40 = (100.0 * (p40['delivered_sum']['PACER'] / p40['observed_sum']['PACER'] - p40['delivered_sum']['Periodic'] / p40['observed_sum']['Periodic'])).dropna()

        def _pw(piv_df, cand):
            return 100.0 * float((piv_df['violations'][cand].sum() + piv_df['unresolved'][cand].sum()) / piv_df['positive'][cand].sum()
                                 - (piv_df['violations']['Periodic'].sum() + piv_df['unresolved']['Periodic'].sum()) / piv_df['positive']['Periodic'].sum())

        rows.append(
            {
                'dropped_cohort': drop_c,
                'remaining_cohorts': 10 if drop_c == 'None' else 9,
                'clusters_g': int(len(du_mar10)),
                'mobile_r_pos_hi_min_pp': float(mob_r.min()),
                'mobile_r_pos_hi_med_pp': float(mob_r.median()),
                'mobile_r_pos_hi_max_pp': float(mob_r.max()),
                'all_r_pos_hi_med_pp': float(r_vals.median()),
                'u_med_pp': float(u_vals.median()),
                'u_q25_pp': float(u_vals.quantile(0.25)),
                'u_q75_pp': float(u_vals.quantile(0.75)),
                'eq_du_marur_c10_pp': float(du_mar10.mean()),
                'eq_du_pacer_c10_pp': float(du_pac10.mean()),
                'eq_du_pacer_c40_pp': float(du_pac40.mean()),
                'pool_dpos_hi_pacer_c10_pp': _pw(p10, 'PACER'),
            }
        )
    return pd.DataFrame(rows)


def run_window_alpha_sensitivity(
    opp: pd.DataFrame, heldout: pd.DataFrame, mcfg: dict, pcfg: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Task 3 + Task 5a: Exploratory sweep over W in {10,20,40} and alpha in {0.05,0.10,0.20} on BOTH domains."""
    rows = []
    cluster_store: list[pd.DataFrame] = []

    datasets = [
        ('retrospective', opp),
        ('heldout_exploratory', heldout),
    ]
    for domain, frame_src in datasets:
        for alpha in (0.05, 0.10, 0.20):
            for window in (10, 20, 40):
                cfg_m = dict(mcfg, alpha=alpha, window=window)
                cfg_p = dict(pcfg, alpha=alpha, pacer_obs_window=window)
                for cohort, grp in frame_src.groupby('cohort', sort=True):
                    for model in ('HistGBM', 'Persistence'):
                        if model == 'HistGBM':
                            col = 'HistGBM' if ('HistGBM' in grp.columns and grp['HistGBM'].notna().any()) else 'Tree'
                        else:
                            col = 'Persistence'
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
                                meta = dict(domain=domain, alpha=alpha, window=window, cohort=cohort, model=model, cap_new=cap, policy=policy)
                                rows.append(dict(**meta, **st))
                                cm = _cluster_rows_from_actions(act, cohort).reset_index()
                                for k, v in meta.items():
                                    cm[k] = v
                                cluster_store.append(cm)

    df_rows = pd.DataFrame(rows)
    df_cl = pd.concat(cluster_store, ignore_index=True)

    cluster_contrasts = []
    agg_cols = ['eligible', 'positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']
    for scope in ('retrospective', 'heldout_exploratory', 'all_pooled'):
        sub_cl = df_cl if scope == 'all_pooled' else df_cl[df_cl['domain'] == scope]
        for (alpha, window, model, cap), grp in sub_cl.groupby(['alpha', 'window', 'model', 'cap_new'], sort=True):
            cd = grp.groupby(['unit', 'policy'], sort=True)[agg_cols].sum().reset_index()
            ref = cd[cd['policy'] == 'Periodic'].set_index('unit').sort_index()
            for cand_pol in ('MARUR', 'PACER', 'ACI'):
                cand = cd[cd['policy'] == cand_pol].set_index('unit').sort_index()
                st_cl = _paired_cluster_stats(cand, ref, n_boot=2000, seed=42)
                pos_cand = cand['positive'].sum()
                pos_ref = ref['positive'].sum()
                cluster_contrasts.append(
                    {
                        'scope': scope,
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
                        **st_cl,
                    }
                )
    return df_rows, pd.DataFrame(cluster_contrasts)


def run_predictor_sensitivity(
    opp: pd.DataFrame, heldout_summary: pd.DataFrame, mcfg: dict, pcfg: dict
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Task 3 + Task 5b: Exploratory source-only alternative predictors on retrospective & held-out archives."""
    raw = load_raw_8224890()
    _, early = extract_sessions_8224890(raw)
    src = early[early['operator'] == 'Op1']
    dev = create_experiment_splits(src, src, 'within_domain', [10])
    src_dates = set(pd.concat([dev.train, dev.val, dev.source_calib])['date'].unique())
    clk_src = _build_clock_source_op1(src_dates)

    predictors = {
        'HistGBM_57': None,
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

    # Build held-out 14-feature frames without changing frozen artifacts
    frozen_model, _ = _load_frozen_rome_model()
    rome_cap = _rome_capacity_ticks(frozen_model)
    ire_static = _ireland_static_ticks(frozen_model)
    heldout_14f = pd.concat([rome_cap, ire_static], ignore_index=True)

    point_rows = []
    policy_rows = []
    cluster_store = []

    domains = [
        ('retrospective', opp),
        ('heldout_rome_ireland', heldout_14f),
    ]
    for dom_name, src_df in domains:
        for pred_name, pred_obj in predictors.items():
            for cohort, grp in src_df.groupby('cohort', sort=True):
                frame = grp.copy()
                frame['date'] = frame['date'].astype(str)
                if pred_name == 'HistGBM_57':
                    col = 'HistGBM' if ('HistGBM' in frame.columns and frame['HistGBM'].notna().any()) else 'Tree'
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
                        'domain': dom_name,
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
                        meta = dict(domain=dom_name, predictor=pred_name, cohort=cohort, cap_new=cap, policy=policy)
                        policy_rows.append(dict(**meta, **st))
                        cm = _cluster_rows_from_actions(act, cohort).reset_index()
                        for k, v in meta.items():
                            cm[k] = v
                        cluster_store.append(cm)

    # Also evaluate Oslo_Commute with lag-only pre-2010-10-01 bus quantile predictor vs frozen Oslo HistGBM and Persistence
    oslo_df = heldout_summary[heldout_summary['cohort'] == 'Oslo_Commute'].copy()
    oslo_q10 = _build_oslo_bus_quantile_predictor(pcfg['oslo_cutoff_utc'])
    # Reconstruct lag2 deterministically from trace ordering on Oslo_Commute
    oslo_df = oslo_df.sort_values(['trace', 'issue']).copy()
    oslo_df['lag2'] = oslo_df.groupby('trace')['Persistence'].shift(1).fillna(oslo_df['Persistence'])
    for pred_name in ('OsloBus_HistGBM', 'OsloBus_QuantileGBM_p10', 'Persistence'):
        frame = oslo_df.copy()
        frame['date'] = frame['date'].astype(str)
        if pred_name == 'OsloBus_HistGBM':
            frame['point'] = frame['HistGBM'].astype(float)
        elif pred_name == 'Persistence':
            frame['point'] = frame['Persistence'].astype(float)
        else:
            elig = frame['Persistence'].notna()
            frame['point'] = np.nan
            x_in = frame.loc[elig, ['Persistence', 'lag2']].rename(columns={'Persistence': 'lag'})
            frame.loc[elig, 'point'] = np.maximum(0.0, oslo_q10.predict(x_in))
        test_eval = frame[(frame['partition'] == 'test') & frame['y'].notna() & frame['point'].notna()]
        point_rows.append(
            {
                'domain': 'heldout_oslo',
                'predictor': pred_name,
                'cohort': 'Oslo_Commute',
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
                meta = dict(domain='heldout_oslo', predictor=pred_name, cohort='Oslo_Commute', cap_new=cap, policy=policy)
                policy_rows.append(dict(**meta, **st))
                cm = _cluster_rows_from_actions(act, 'Oslo_Commute').reset_index()
                for k, v in meta.items():
                    cm[k] = v
                cluster_store.append(cm)

    df_point = pd.DataFrame(point_rows)
    df_policy = pd.DataFrame(policy_rows)
    df_cl = pd.concat(cluster_store, ignore_index=True)

    cluster_contrasts = []
    agg_cols = ['eligible', 'positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']
    for (dom_name, pred_name, cap), grp in df_cl.groupby(['domain', 'predictor', 'cap_new'], sort=True):
        cd = grp.groupby(['unit', 'policy'], sort=True)[agg_cols].sum().reset_index()
        ref = cd[cd['policy'] == 'Periodic'].set_index('unit').sort_index()
        for cand_pol in ('MARUR', 'PACER'):
            cand = cd[cd['policy'] == cand_pol].set_index('unit').sort_index()
            st_cl = _paired_cluster_stats(cand, ref, n_boot=2000, seed=42)
            pos_cand = cand['positive'].sum()
            pos_ref = ref['positive'].sum()
            cluster_contrasts.append(
                {
                    'domain': dom_name,
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
                    **st_cl,
                }
            )
    return df_point, df_policy, pd.DataFrame(cluster_contrasts)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc).isoformat()
    opp = pd.read_csv(ROOT / 'results/marur/opportunities.csv.gz', float_precision='round_trip', low_memory=False)
    heldout = pd.read_csv(ROOT / 'results/pacer/untouched_opportunities.csv.gz', float_precision='round_trip', low_memory=False)
    mcfg = json.loads((ROOT / 'configs/marur.json').read_text(encoding='utf8'))
    pcfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))

    df_pow = run_power_and_equivalence()
    df_loco = run_leave_one_cohort_out()
    df_wa, df_wa_cl = run_window_alpha_sensitivity(opp, heldout, mcfg, pcfg)
    df_pt, df_pr, df_pr_cl = run_predictor_sensitivity(opp, heldout, mcfg, pcfg)

    df_pow.to_csv(OUT_DIR / 'power_equivalence.csv', index=False)
    df_loco.to_csv(OUT_DIR / 'leave_one_cohort_out.csv', index=False)
    df_wa.to_csv(OUT_DIR / 'window_alpha_sensitivity.csv', index=False)
    df_wa_cl.to_csv(OUT_DIR / 'window_alpha_clusters.csv', index=False)
    df_pt.to_csv(OUT_DIR / 'predictor_point_accuracy.csv', index=False)
    df_pr.to_csv(OUT_DIR / 'predictor_sensitivity.csv', index=False)
    df_pr_cl.to_csv(OUT_DIR / 'predictor_sensitivity_clusters.csv', index=False)

    receipt = {
        'start_utc': start,
        'end_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'exploratory_sensitivity_only',
        'heldout_cohorts_exploratory': True,
        'frozen_results_modified': False,
        'power_equivalence_rows': int(len(df_pow)),
        'loco_rows': int(len(df_loco)),
        'window_alpha_rows': int(len(df_wa)),
        'predictor_rows': int(len(df_pr)),
        'sha256': {
            str(p.relative_to(ROOT).as_posix()): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT_DIR.glob('*.csv'))
        },
    }
    (OUT_DIR / 'execution.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'sha256'}, indent=2))
    print('\n=== Task 2: Power and Equivalence Summary ===')
    print(df_pow[['scope', 'cap_new', 'candidate', 'clusters', 'eq_du_mean_pp', 'between_cluster_sd_pp', 'mde80_pp', 'tost_p_1pp', 'tost_p_2pp']].to_string(index=False))
    print('\n=== Task 3: Leave-One-Cohort-Out Summary ===')
    print(df_loco[['dropped_cohort', 'clusters_g', 'mobile_r_pos_hi_med_pp', 'u_med_pp', 'eq_du_marur_c10_pp', 'eq_du_pacer_c10_pp', 'eq_du_pacer_c40_pp']].to_string(index=False))
    print('\n=== Task 3: PACER vs Periodic Window/Alpha (HeldOut & Retro, HistGBM) ===')
    sub_p = df_wa_cl[(df_wa_cl['model'] == 'HistGBM') & (df_wa_cl['candidate'] == 'PACER') & (df_wa_cl['scope'].isin(['retrospective', 'heldout_exploratory']))]
    print(sub_p[['scope', 'alpha', 'window', 'cap_new', 'cand_pos_rate', 'cand_pos_hi', 'ref_pos_hi', 'cand_u', 'eq_du_mean', 't_du_lo', 't_du_hi']].to_string(index=False))
    print('\n=== Task 3: Source-Only Predictor Summary (PACER & MARUR vs Periodic) ===')
    print(df_pr_cl[['domain', 'predictor', 'cap_new', 'candidate', 'cand_pos_rate', 'cand_pos_hi', 'ref_pos_hi', 'cand_u', 'eq_du_mean']].to_string(index=False))


if __name__ == '__main__':
    main()
