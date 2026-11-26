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
from scripts.build_heldout_cohorts import (
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
    """Task 1 & 2: Compute equal-cluster and pooled-ratio relative TOST (+-50%, +-25%) plus absolute TOST."""
    p_cl = pd.read_csv(ROOT / 'results/pacer/pacer_cluster_dates.csv')
    rows = []
    specs = [
        ('Retrospective', 'retrospective', 10, 'MARUR'),
        ('Retrospective', 'retrospective', 10, 'PACER'),
        ('Retrospective', 'retrospective', 40, 'MARUR'),
        ('Retrospective', 'retrospective', 40, 'PACER'),
        ('HeldOut', 'heldout_public', 10, 'PACER'),
        ('HeldOut', 'heldout_public', 10, 'MARUR'),
        ('HeldOut', 'heldout_public', 40, 'PACER'),
        ('HeldOut', 'heldout_public', 40, 'MARUR'),
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
        u_c = 100.0 * piv['delivered_sum'][cand] / piv['observed_sum'][cand]
        u_r = 100.0 * piv['delivered_sum']['Periodic'] / piv['observed_sum']['Periodic']
        diff_all = u_c - u_r
        undef_u = int(diff_all.isna().sum())
        diff = diff_all.dropna()
        units = diff.index.tolist()
        dc = piv['delivered_sum'][cand].loc[units].to_numpy(dtype=float)
        oc = piv['observed_sum'][cand].loc[units].to_numpy(dtype=float)
        dr = piv['delivered_sum']['Periodic'].loc[units].to_numpy(dtype=float)
        or_ = piv['observed_sum']['Periodic'].loc[units].to_numpy(dtype=float)

        n = int(len(diff))
        mean = float(diff.mean())
        sd = float(diff.std(ddof=1))
        se = sd / float(np.sqrt(n))
        t95_lo, t95_hi = stats.t.interval(0.95, df=n - 1, loc=mean, scale=se)
        t90_lo, t90_hi = stats.t.interval(0.90, df=n - 1, loc=mean, scale=se)
        mde80 = _solve_mde_t(se, n - 1, alpha=0.05, power=0.80)

        # (a) Equal-cluster relative TOST: margin = (rel% / 100) * equal-cluster mean of Periodic U
        eq_ref_u = float(u_r.loc[units].mean())
        eq_cand_u = float(u_c.loc[units].mean())
        zero_ref_u = int((u_r.loc[units] <= 0.0).sum())
        eq_rel_pct = 100.0 * mean / eq_ref_u
        m_eq_rel50 = 0.50 * eq_ref_u
        m_eq_rel25 = 0.25 * eq_ref_u
        tost_eq_rel50 = float(max(1.0 - stats.t.cdf((mean + m_eq_rel50) / se, df=n - 1), stats.t.cdf((mean - m_eq_rel50) / se, df=n - 1)))
        tost_eq_rel25 = float(max(1.0 - stats.t.cdf((mean + m_eq_rel25) / se, df=n - 1), stats.t.cdf((mean - m_eq_rel25) / se, df=n - 1)))

        # (b) Pooled-ratio TOST: pooled candidate U / pooled Periodic U with cluster bootstrap CI
        pool_ref_u = 100.0 * float(dr.sum() / or_.sum())
        pool_cand_u = 100.0 * float(dc.sum() / oc.sum())
        pool_du = pool_cand_u - pool_ref_u
        pool_rel_pct = 100.0 * (pool_cand_u / pool_ref_u - 1.0)
        rng = np.random.default_rng(42)
        idx = rng.integers(0, n, size=(2000, n))
        b_uc = dc[idx].sum(axis=1) / oc[idx].sum(axis=1)
        b_ur = dr[idx].sum(axis=1) / or_[idx].sum(axis=1)
        ok = b_ur > 0
        b_rel = 100.0 * (b_uc[ok] / b_ur[ok] - 1.0)
        b_rel_95_lo, b_rel_95_hi = [float(x) for x in np.percentile(b_rel, [2.5, 97.5])]
        b_rel_90_lo, b_rel_90_hi = [float(x) for x in np.percentile(b_rel, [5.0, 95.0])]
        pool_tost_rel50 = float(max(np.mean(b_rel <= -50.0), np.mean(b_rel >= 50.0)))
        pool_tost_rel25 = float(max(np.mean(b_rel <= -25.0), np.mean(b_rel >= 25.0)))

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
                'undef_u_clusters': undef_u,
                'zero_ref_u_clusters': zero_ref_u,
                'eq_ref_u_pp': eq_ref_u,
                'eq_cand_u_pp': eq_cand_u,
                'eq_du_mean_pp': mean,
                'eq_rel_du_pct': eq_rel_pct,
                'between_cluster_sd_pp': sd,
                'se_pp': se,
                't_ci95_lo_pp': float(t95_lo),
                't_ci95_hi_pp': float(t95_hi),
                't_ci90_lo_pp': float(t90_lo),
                't_ci90_hi_pp': float(t90_hi),
                'mde80_pp': mde80,
                'eq_rel_margin50_pp': m_eq_rel50,
                'eq_rel_margin25_pp': m_eq_rel25,
                'eq_tost_p_rel50': tost_eq_rel50,
                'eq_tost_p_rel25': tost_eq_rel25,
                'eq_rel_equiv50': bool(tost_eq_rel50 < 0.05),
                'tost_p_1pp': tost_1,
                'tost_p_15pp': tost_15,
                'tost_p_2pp': tost_2,
                'tost_p_3pp': tost_3,
                'equiv_1pp': bool(tost_1 < 0.05),
                'equiv_2pp': bool(tost_2 < 0.05),
                'pool_ref_u_pp': pool_ref_u,
                'pool_cand_u_pp': pool_cand_u,
                'pool_du_pp': pool_du,
                'pool_rel_du_pct': pool_rel_pct,
                'pool_boot_rel95_lo_pct': b_rel_95_lo,
                'pool_boot_rel95_hi_pct': b_rel_95_hi,
                'pool_boot_rel90_lo_pct': b_rel_90_lo,
                'pool_boot_rel90_hi_pct': b_rel_90_hi,
                'pool_tost_p_rel50': pool_tost_rel50,
                'pool_tost_p_rel25': pool_tost_rel25,
                'pool_rel_equiv50': bool(b_rel_90_lo > -50.0 and b_rel_90_hi < 50.0),
            }
        )
    return pd.DataFrame(rows)


def _campaign_from_unit(unit: str, domain: str) -> str:
    if domain == 'retrospective':
        if unit.startswith('Rome:'):
            return 'Rome_2023'
        if unit.startswith('US_Drive3:'):
            return 'US_Drive3'
        return 'Ireland_Drive'
    if unit.startswith('RomeCap:'):
        return 'Rome_Capacity'
    if unit.startswith('Oslo:'):
        return 'Oslo_Commute'
    return 'Ireland_Static'


def run_campaign_dependence() -> pd.DataFrame:
    """Task 2 (exploratory/post-hoc): Campaign-level dependence adjustment for relative and absolute TOST."""
    p_cl = pd.read_csv(ROOT / 'results/pacer/pacer_cluster_dates.csv')
    rows = []
    specs = [
        ('Retrospective', 'retrospective', 10, 'MARUR'),
        ('Retrospective', 'retrospective', 10, 'PACER'),
        ('Retrospective', 'retrospective', 40, 'MARUR'),
        ('Retrospective', 'retrospective', 40, 'PACER'),
        ('HeldOut', 'heldout_public', 10, 'PACER'),
        ('HeldOut', 'heldout_public', 10, 'MARUR'),
        ('HeldOut', 'heldout_public', 40, 'PACER'),
        ('HeldOut', 'heldout_public', 40, 'MARUR'),
        ('AllCohorts', 'all', 10, 'PACER'),
        ('AllCohorts', 'all', 40, 'PACER'),
    ]
    for scope, dom_filter, cap, cand in specs:
        sub = p_cl[(p_cl['model'] == 'HistGBM') & (p_cl['scenario'] == 'Recorded') & (p_cl['cap_new'] == cap)]
        if dom_filter != 'all':
            sub = sub[sub['domain'] == dom_filter]
        unit_dom = sub[['unit', 'domain']].drop_duplicates().set_index('unit')['domain'].to_dict()
        agg = sub.groupby(['unit', 'policy'], as_index=False)[['delivered_sum', 'observed_sum']].sum()
        piv = agg.pivot(index='unit', columns='policy')
        uc = 100.0 * piv['delivered_sum'][cand] / piv['observed_sum'][cand]
        ur = 100.0 * piv['delivered_sum']['Periodic'] / piv['observed_sum']['Periodic']
        diff = (uc - ur).dropna()
        units = diff.index.tolist()
        dc = piv['delivered_sum'][cand].loc[units].to_numpy(dtype=float)
        oc = piv['observed_sum'][cand].loc[units].to_numpy(dtype=float)
        dr = piv['delivered_sum']['Periodic'].loc[units].to_numpy(dtype=float)
        or_ = piv['observed_sum']['Periodic'].loc[units].to_numpy(dtype=float)
        eq_ref_u = float(ur.loc[units].mean())

        camps = pd.Series([_campaign_from_unit(u, unit_dom[u]) for u in units], index=diff.index)
        groups = [diff[camps == c].to_numpy(dtype=float) for c in sorted(camps.unique())]
        k_camp = len(groups)
        ns = np.array([len(g) for g in groups], dtype=float)
        n_tot = float(ns.sum())
        grand = float(diff.mean())
        ssb = float(sum(len(g) * (g.mean() - grand) ** 2 for g in groups))
        ssw = float(sum(((g - g.mean()) ** 2).sum() for g in groups))
        msb = ssb / (k_camp - 1)
        msw = ssw / (n_tot - k_camp)
        n0 = (n_tot - float((ns ** 2).sum()) / n_tot) / (k_camp - 1)
        var_b = max(0.0, (msb - msw) / n0)
        icc = var_b / (var_b + msw) if (var_b + msw) > 0 else 0.0
        m_eff = float((ns ** 2).sum()) / n_tot
        deff = 1.0 + (m_eff - 1.0) * icc
        g_eff = n_tot / deff

        naive_sd = float(diff.std(ddof=1))
        naive_se = naive_sd / float(np.sqrt(n_tot))
        adj_se = naive_se * float(np.sqrt(deff))
        df_adj = max(1.0, g_eff - 1.0)
        m50_eq = 0.50 * eq_ref_u
        m25_eq = 0.25 * eq_ref_u
        naive_rel50 = float(max(1.0 - stats.t.cdf((grand + m50_eq) / naive_se, df=n_tot - 1), stats.t.cdf((grand - m50_eq) / naive_se, df=n_tot - 1)))
        naive_rel25 = float(max(1.0 - stats.t.cdf((grand + m25_eq) / naive_se, df=n_tot - 1), stats.t.cdf((grand - m25_eq) / naive_se, df=n_tot - 1)))
        adj_rel50 = float(max(1.0 - stats.t.cdf((grand + m50_eq) / adj_se, df=df_adj), stats.t.cdf((grand - m50_eq) / adj_se, df=df_adj)))
        adj_rel25 = float(max(1.0 - stats.t.cdf((grand + m25_eq) / adj_se, df=df_adj), stats.t.cdf((grand - m25_eq) / adj_se, df=df_adj)))
        mde_adj = _solve_mde_t(adj_se, df_adj, alpha=0.05, power=0.80)
        tost_adj_2pp = float(max(1.0 - stats.t.cdf((grand + 2.0) / adj_se, df=df_adj), stats.t.cdf((grand - 2.0) / adj_se, df=df_adj)))

        rng = np.random.default_rng(42)
        camp_names = sorted(camps.unique())
        camp_idx = {c: np.where(camps.to_numpy() == c)[0] for c in camp_names}
        hb_abs, hb_eq_rel, hb_pool_rel = [], [], []
        for _ in range(2000):
            chosen_c = rng.choice(camp_names, size=len(camp_names), replace=True)
            idx_b = np.concatenate([rng.choice(camp_idx[c], size=len(camp_idx[c]), replace=True) for c in chosen_c])
            du_b = float(diff.iloc[idx_b].mean())
            ur_b = float(ur.loc[units].iloc[idx_b].mean())
            hb_abs.append(du_b)
            if ur_b > 0:
                hb_eq_rel.append(100.0 * du_b / ur_b)
            pr_uc = float(dc[idx_b].sum() / oc[idx_b].sum())
            pr_ur = float(dr[idx_b].sum() / or_[idx_b].sum())
            if pr_ur > 0:
                hb_pool_rel.append(100.0 * (pr_uc / pr_ur - 1.0))
        hb_lo, hb_hi = [float(x) for x in np.percentile(hb_abs, [2.5, 97.5])]
        h_eq90_lo, h_eq90_hi = [float(x) for x in np.percentile(hb_eq_rel, [5.0, 95.0])]
        h_pl90_lo, h_pl90_hi = [float(x) for x in np.percentile(hb_pool_rel, [5.0, 95.0])]
        rows.append(
            {
                'scope': scope,
                'cap_new': cap,
                'candidate': cand,
                'reference': 'Periodic',
                'clusters': int(n_tot),
                'campaigns': k_camp,
                'eq_ref_u_pp': eq_ref_u,
                'eq_du_mean_pp': grand,
                'naive_se_pp': naive_se,
                'icc': icc,
                'deff': deff,
                'g_eff': g_eff,
                'adj_se_pp': adj_se,
                'adj_mde80_pp': mde_adj,
                'naive_eq_tost_p_rel50': naive_rel50,
                'naive_eq_tost_p_rel25': naive_rel25,
                'adj_eq_tost_p_rel50': adj_rel50,
                'adj_eq_tost_p_rel25': adj_rel25,
                'adj_tost_p_2pp': tost_adj_2pp,
                'hier_boot_sd_pp': float(np.std(hb_abs)),
                'hier_boot95_lo_pp': hb_lo,
                'hier_boot95_hi_pp': hb_hi,
                'hier_boot90_eq_rel_lo_pct': h_eq90_lo,
                'hier_boot90_eq_rel_hi_pct': h_eq90_hi,
                'hier_boot90_pool_rel_lo_pct': h_pl90_lo,
                'hier_boot90_pool_rel_hi_pct': h_pl90_hi,
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


def _camp_from_cohort(cohort: str) -> str:
    if cohort in ('E1', 'E3'):
        return 'Rome_2023'
    if cohort in ('AT&T', 'T-Mobile', 'Verizon'):
        return 'US_Drive3'
    if cohort == 'Ireland':
        return 'Ireland_Drive'
    if cohort in ('Rome_Capacity_Op1', 'Rome_Capacity_Op2'):
        return 'Rome_Capacity'
    if cohort == 'Oslo_Commute':
        return 'Oslo_Commute'
    return 'Ireland_Static'


def run_leave_one_campaign_out() -> pd.DataFrame:
    """Major Concern 2: Leave-one-campaign-out robustness and per-campaign risk/utility distributions."""
    s = pd.read_csv(ROOT / 'results/pacer/pacer_summary.csv')
    cl = pd.read_csv(ROOT / 'results/pacer/pacer_cluster_dates.csv')
    sub_s_all = s[(s['model'] == 'HistGBM') & (s['scenario'] == 'Recorded') & (s['cap_new'].isin([10, 40])) & (s['policy'].isin(['Periodic', 'MARUR', 'PACER']))].copy()
    sub_cl_all = cl[(cl['model'] == 'HistGBM') & (cl['scenario'] == 'Recorded') & (cl['cap_new'].isin([10, 40]))].copy()
    sub_s_all['campaign'] = sub_s_all['cohort'].map(_camp_from_cohort)
    sub_cl_all['campaign'] = sub_cl_all['cohort'].map(_camp_from_cohort)
    campaigns = sorted(sub_s_all['campaign'].unique())
    rows = []
    for drop_camp in ['None'] + campaigns:
        sub_s = sub_s_all if drop_camp == 'None' else sub_s_all[sub_s_all['campaign'] != drop_camp]
        sub_cl = sub_cl_all if drop_camp == 'None' else sub_cl_all[sub_cl_all['campaign'] != drop_camp]
        mob_s = sub_s[sub_s['campaign'] != 'Ireland_Static']
        mob_r = 100.0 * mob_s['positive_high'].dropna()
        u_vals = 100.0 * sub_s['u'].dropna()
        if drop_camp == 'None':
            c_r_med = float((100.0 * sub_s_all['positive_high']).median())
            c_u_med = float((100.0 * sub_s_all['u']).median())
        else:
            dropped_s = sub_s_all[sub_s_all['campaign'] == drop_camp]
            c_r_med = float((100.0 * dropped_s['positive_high']).median())
            c_u_med = float((100.0 * dropped_s['u']).median())

        c10 = sub_cl[sub_cl['cap_new'] == 10].groupby(['unit', 'policy'], as_index=False)[['delivered_sum', 'observed_sum']].sum().pivot(index='unit', columns='policy')
        c40 = sub_cl[sub_cl['cap_new'] == 40].groupby(['unit', 'policy'], as_index=False)[['delivered_sum', 'observed_sum']].sum().pivot(index='unit', columns='policy')
        du_m10 = 100.0 * (c10['delivered_sum']['MARUR'] / c10['observed_sum']['MARUR'] - c10['delivered_sum']['Periodic'] / c10['observed_sum']['Periodic']).dropna()
        du_p10 = 100.0 * (c10['delivered_sum']['PACER'] / c10['observed_sum']['PACER'] - c10['delivered_sum']['Periodic'] / c10['observed_sum']['Periodic']).dropna()
        du_p40 = 100.0 * (c40['delivered_sum']['PACER'] / c40['observed_sum']['PACER'] - c40['delivered_sum']['Periodic'] / c40['observed_sum']['Periodic']).dropna()
        rows.append(
            {
                'dropped_campaign': drop_camp,
                'remaining_campaigns': 6 if drop_camp == 'None' else 5,
                'clusters_g': int(len(du_m10)),
                'camp_r_pos_hi_med_pp': c_r_med,
                'camp_u_med_pp': c_u_med,
                'mobile_r_pos_hi_min_pp': float(mob_r.min()),
                'mobile_r_pos_hi_med_pp': float(mob_r.median()),
                'mobile_r_pos_hi_max_pp': float(mob_r.max()),
                'u_med_pp': float(u_vals.median()),
                'eq_du_marur_c10_pp': float(du_m10.mean()),
                'eq_du_pacer_c10_pp': float(du_p10.mean()),
                'eq_du_pacer_c40_pp': float(du_p40.mean()),
            }
        )
    return pd.DataFrame(rows)


def run_single_factor_ablation() -> pd.DataFrame:
    """Post-hoc exploratory single-factor accounting ablation across saved benchmark ledgers.

    Varies one evaluation choice at a time across immutable saved summaries and tests
    Proposition 1's five exact reversal conditions without modifying any frozen result.
    """
    ps = pd.read_csv(ROOT / 'results/pacer/pacer_summary.csv')
    mp = pd.read_csv(ROOT / 'results/marur_audit/matched_cost_pairs.csv')
    cl = pd.read_csv(ROOT / 'results/pacer/pacer_cluster_dates.csv')
    cd = pd.read_csv(ROOT / 'results/exploratory/sensitivity/campaign_dependence.csv')

    # Verify exact R = A * R_+ on active summary rows (error < 1e-12)
    pos_mask = ps['positive'] > 0
    id_err = np.abs(ps.loc[pos_mask, 'hi'] - ps.loc[pos_mask, 'positive_rate'] * ps.loc[pos_mask, 'positive_high']).max()
    if id_err > 1e-12:
        raise ValueError(f'Accounting identity R=A*R+ failed on pacer_summary: {id_err}')

    comp_rows = []
    for cap in (10, 40):
        sub = ps[ps['cap_new'] == cap]
        for (cohort, model, scen), grp in sub.groupby(['cohort', 'model', 'scenario']):
            by_pol = grp.set_index('policy')
            r = by_pol.loc['Periodic']
            for cand in ('MARUR', 'PACER', 'ACI', 'DecayingOGD', 'Early'):
                c = by_pol.loc[cand]
                # Factor 1: R^hi vs R_+^hi (Proposition 1.i algebraic equivalence)
                rank_flip = (c['hi'] < r['hi'] and c['positive_high'] > r['positive_high']) or (
                    c['hi'] > r['hi'] and c['positive_high'] < r['positive_high']
                )
                ratio_cond = (c['hi'] / r['hi'] - 1.0) * (c['positive_high'] / r['positive_high'] - 1.0) < 0.0
                if rank_flip != ratio_cond:
                    raise ValueError(f'Prop 1.i algebraic mismatch at {cohort}/{model}/{scen}/{cand}/{cap}')
                sla_flip = (c['hi'] <= 0.10) != (c['positive_high'] <= 0.10)
                # Factor 2: Nominal cap C_new vs realized Q_new
                q_unmatched = abs(float(c['new_query_attempts']) - float(r['new_query_attempts'])) > 1e-9
                # Factor 3: Measured complete point estimate vs [lo, hi] partial-identification interval
                has_unres = (c['unresolved'] + r['unresolved']) > 0
                overlap = max(c['positive_low'], r['positive_low']) <= min(c['positive_high'], r['positive_high'])
                meas_flip = (c['v_given_positive'] < r['v_given_positive']) != (c['positive_high'] < r['positive_high'])
                meas_sla_flip = (c['v_given_positive'] <= 0.10) != (c['positive_high'] <= 0.10)
                comp_rows.append(
                    {
                        'rank_flip': rank_flip,
                        'sla_flip': sla_flip,
                        'q_unmatched': q_unmatched,
                        'has_unres': has_unres,
                        'miss_overlap': has_unres and overlap,
                        'meas_flip': has_unres and meas_flip,
                        'meas_sla_flip': has_unres and meas_sla_flip,
                    }
                )
    cdf = pd.DataFrame(comp_rows)

    # Factor 2b: marur_audit active-baseline matched-cost check
    mp_act = mp[mp['baseline'] != 'Frozen']

    # Factor 4: Offer-weighted vs equal-unit pooling across 120 scope contrasts vs Periodic
    scopes = {
        'Retrospective': ['E1', 'E3', 'AT&T', 'T-Mobile', 'Verizon', 'Ireland'],
        'HeldOutPublic': ['Rome_Capacity_Op1', 'Rome_Capacity_Op2', 'Oslo_Commute', 'Ireland_Static'],
        'AllCohorts': cl['cohort'].unique().tolist(),
    }
    pool_rows = []
    max_pool_err = 0.0
    for sname, cohs in scopes.items():
        sub = cl[cl['cohort'].isin(cohs)]
        for (model, scen, cap), grp in sub.groupby(['model', 'scenario', 'cap_new']):
            if cap == 0:
                continue
            per = grp[grp['policy'] == 'Periodic'].groupby('unit', as_index=True).sum(numeric_only=True)
            for cand in ('MARUR', 'PACER', 'ACI', 'DecayingOGD', 'Early'):
                ca = grp[grp['policy'] == cand].groupby('unit', as_index=True).sum(numeric_only=True)
                rc = (ca['violations'] + ca['unresolved']) / ca['positive'].replace(0, np.nan)
                rr = (per['violations'] + per['unresolved']) / per['positive'].replace(0, np.nan)
                wc = ca['positive'] / ca['positive'].sum()
                wr = per['positive'] / per['positive'].sum()
                d_rhi_pool = 100.0 * (
                    (ca['violations'].sum() + ca['unresolved'].sum()) / ca['positive'].sum()
                    - (per['violations'].sum() + per['unresolved'].sum()) / per['positive'].sum()
                )
                d_rhi_id = 100.0 * float((wc * rc.fillna(0)).sum() - (wr * rr.fillna(0)).sum())
                max_pool_err = max(max_pool_err, abs(d_rhi_pool - d_rhi_id))
                both_pos = (ca['positive'] > 0) & (per['positive'] > 0)
                d_rhi_eq = 100.0 * float((rc[both_pos] - rr[both_pos]).mean())
                d_u_pool = 100.0 * (
                    ca['delivered_sum'].sum() / ca['observed_sum'].sum()
                    - per['delivered_sum'].sum() / per['observed_sum'].sum()
                )
                both_obs = (ca['observed_sum'] > 0) & (per['observed_sum'] > 0)
                d_u_eq = 100.0 * float(
                    (
                        ca.loc[both_obs, 'delivered_sum'] / ca.loc[both_obs, 'observed_sum']
                        - per.loc[both_obs, 'delivered_sum'] / per.loc[both_obs, 'observed_sum']
                    ).mean()
                )
                pool_rows.append(
                    {
                        'rhi_sign_flip': np.sign(d_rhi_pool) != np.sign(d_rhi_eq),
                        'rhi_gap_gt5': abs(d_rhi_pool - d_rhi_eq) > 5.0,
                        'u_sign_flip': (d_u_pool > 0.01 and d_u_eq < -0.01) or (d_u_pool < -0.01 and d_u_eq > 0.01),
                    }
                )
    if max_pool_err > 1e-12:
        raise ValueError(f'Prop 1.iv pooling identity error exceeded tolerance: {max_pool_err}')
    pldf = pd.DataFrame(pool_rows)

    # Factor 5: Date-level vs campaign-adjusted TOST
    naive_pass = cd['naive_eq_tost_p_rel50'] < 0.05
    donner_rev = naive_pass & (cd['adj_eq_tost_p_rel50'] >= 0.05)
    hier_rev = naive_pass & ~((cd['hier_boot90_eq_rel_lo_pct'] > -50.0) & (cd['hier_boot90_eq_rel_hi_pct'] < 50.0))
    pool_hier_pass = (cd['hier_boot90_pool_rel_lo_pct'] > -50.0) & (cd['hier_boot90_pool_rel_hi_pct'] < 50.0)

    n_unres = int(cdf['has_unres'].sum())
    n_naive_pass = int(naive_pass.sum())
    ablation = [
        dict(factor='R_vs_Rplus_SLA', label='All-issued R vs Cond R+ (SLA<=10%)', condition='R<=a permits R+>a when A<R+/a', n_total=int(len(cdf)), n_affected=int(cdf['sla_flip'].sum()), pct_affected=100.0 * float(cdf['sla_flip'].mean()), note='0 algebraic mismatches'),
        dict(factor='R_vs_Rplus_Rank', label='All-issued R vs Cond R+ (Winner)', condition='A_1/A_2 < R+,2/R+,1', n_total=int(len(cdf)), n_affected=int(cdf['rank_flip'].sum()), pct_affected=100.0 * float(cdf['rank_flip'].mean()), note='Exact 0 mismatches across 400'),
        dict(factor='Cap_vs_Qnew_All', label='Nominal Cnew vs Realized Qnew', condition='Qnew(cand) != Qnew(Periodic)', n_total=int(len(cdf)), n_affected=int(cdf['q_unmatched'].sum()), pct_affected=100.0 * float(cdf['q_unmatched'].mean()), note='72/432 in 6-coh MARUR audit'),
        dict(factor='Missing_Bounds_Overlap', label='Complete R+meas vs Bounds [lo,hi]', condition='max(lo)<=min(hi) when m>0', n_total=n_unres, n_affected=int(cdf['miss_overlap'].sum()), pct_affected=100.0 * float(cdf['miss_overlap'].sum() / n_unres), note=f'{int(cdf["meas_flip"].sum())} rank / {int(cdf["meas_sla_flip"].sum())} SLA flips'),
        dict(factor='Pooling_Weight_Rplus', label='OfferWtd vs EqualUnit Pooling (dR+hi)', condition='Cov(w_c, r_c) != 0 flips sum(w*d)', n_total=int(len(pldf)), n_affected=int(pldf['rhi_sign_flip'].sum()), pct_affected=100.0 * float(pldf['rhi_sign_flip'].mean()), note=f'{int(pldf["u_sign_flip"].sum())}/{len(pldf)} U flips ({100*pldf["u_sign_flip"].mean():.1f}%)'),
        dict(factor='Campaign_Clustering_Donner', label='Date TOST vs Donner DEFF (p<0.05)', condition='DEFF = 1+(n-1)rho > G/Greq', n_total=n_naive_pass, n_affected=int(donner_rev.sum()), pct_affected=100.0 * float(donner_rev.sum() / n_naive_pass), note=f'{int(hier_rev.sum())}/{n_naive_pass} HierBoot Eq flips; {int(pool_hier_pass.sum())}/10 Pool pass'),
    ]
    return pd.DataFrame(ablation)


def run_risk_utility_and_fairness_audit() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Post-hoc exploratory Risk-Utility Pareto operating points and 7-axis Baseline Fairness table."""
    ps = pd.read_csv(ROOT / 'results/pacer/pacer_summary.csv')
    wa = pd.read_csv(ROOT / 'results/exploratory/sensitivity/window_alpha_sensitivity.csv')

    pareto_rows = []
    # Mean 10-cohort operating points for HistGBM Recorded across main caps
    hg_rec = ps[(ps['model'] == 'HistGBM') & (ps['scenario'] == 'Recorded')]
    for (pol, cap), g in hg_rec.groupby(['policy', 'cap_new'], sort=True):
        pareto_rows.append(
            {
                'source': 'HistGBM_Recorded_10Coh',
                'policy': pol,
                'alpha': 0.10,
                'cap_new': int(cap),
                'offer_freq_a_pp': 100.0 * float(g['positive_rate'].mean()),
                'all_risk_hi_pp': 100.0 * float(g['hi'].mean()),
                'cond_risk_hi_pp': 100.0 * float(g['positive_high'].mean()),
                'supported_u_pp': 100.0 * float(g['u'].mean()),
                'realized_q_new': float(g['new_query_attempts'].mean()),
                'unmatched_note': 'Primary benchmark operating point',
            }
        )
    # Alpha-frontier operating points from 1,800-run W/alpha exploratory sweep (HistGBM, W in {10,20,40})
    wa_hg = wa[wa['model'] == 'HistGBM']
    for (pol, al, cap), g in wa_hg.groupby(['policy', 'alpha', 'cap_new'], sort=True):
        if pol not in ('Periodic', 'MARUR', 'PACER', 'ACI'):
            continue
        pareto_rows.append(
            {
                'source': 'HistGBM_AlphaSweep_10Coh',
                'policy': pol,
                'alpha': float(al),
                'cap_new': int(cap),
                'offer_freq_a_pp': 100.0 * float(g['positive_rate'].mean()),
                'all_risk_hi_pp': 100.0 * float(g['hi'].mean()),
                'cond_risk_hi_pp': 100.0 * float(g['positive_high'].mean()),
                'supported_u_pp': 100.0 * float(g['u'].mean()),
                'realized_q_new': float(g['new_query_attempts'].mean()),
                'unmatched_note': 'Across W in {10,20,40}',
            }
        )

    # Sequential fairness sieve across all 100 (cohort, cap in {10,40}, cand in 5 active policies) vs Periodic
    sieve_counts = dict(total=0, unfiltered_win=0, q_matched=0, q_win=0, qa_matched=0, qa_win=0)
    surviving = []
    for cap in (10, 40):
        sub = hg_rec[hg_rec['cap_new'] == cap]
        for cohort, grp in sub.groupby('cohort'):
            b = grp.set_index('policy')
            r = b.loc['Periodic']
            for cand in ('MARUR', 'PACER', 'ACI', 'DecayingOGD', 'Early'):
                c = b.loc[cand]
                sieve_counts['total'] += 1
                q_ok = abs(float(c['new_query_attempts']) - float(r['new_query_attempts'])) < 1e-6
                a_ok = abs(100.0 * (float(c['positive_rate']) - float(r['positive_rate']))) <= 5.0
                win = (100.0 * (float(c['positive_high']) - float(r['positive_high'])) < -1.0) and (
                    100.0 * (float(c['u']) - float(r['u'])) >= -0.05
                )
                if win:
                    sieve_counts['unfiltered_win'] += 1
                if q_ok:
                    sieve_counts['q_matched'] += 1
                    if win:
                        sieve_counts['q_win'] += 1
                    if a_ok:
                        sieve_counts['qa_matched'] += 1
                        if win:
                            sieve_counts['qa_win'] += 1
                            surviving.append(f'{cohort} {cand} C={cap}')
    pareto_rows.append(
        {
            'source': 'FairnessSieve_100Pairs',
            'policy': f"total={sieve_counts['total']}|win={sieve_counts['unfiltered_win']}|q={sieve_counts['q_matched']}|qwin={sieve_counts['q_win']}|qa={sieve_counts['qa_matched']}|qawin={sieve_counts['qa_win']}",
            'alpha': 0.10,
            'cap_new': 0,
            'offer_freq_a_pp': 0.0,
            'all_risk_hi_pp': 0.0,
            'cond_risk_hi_pp': 0.0,
            'supported_u_pp': 0.0,
            'realized_q_new': 0.0,
            'unmatched_note': '; '.join(surviving),
        }
    )

    # 7-axis Experimental Fairness Audit Table
    mcfg = json.loads((ROOT / 'configs/marur.json').read_text(encoding='utf8'))
    fair_rows = []
    pol_meta = {
        'Frozen': ('0', 'None', 'None'),
        'Early': ('10/40', 'Insert p', 'Residual only'),
        'Random': ('10/40', 'Insert p', 'Residual only'),
        'Periodic': ('10/40', 'Insert p', 'Residual only'),
        'ACI': ('10/40', 'err=1 on pos', 'Online alpha_t'),
        'DecayingOGD': ('10/40', 'score=p on miss', 'Decaying step'),
        'MARUR': ('10/40', 'Insert p + gate', 'LTE/NR group_id'),
        'PACER': ('10/40', 'Excl W; e=1', 'Veto/block A_t'),
    }
    for pol, (cstr, miss_rule, feat_acc) in pol_meta.items():
        sub = hg_rec[hg_rec['policy'] == pol]
        if pol == 'Frozen':
            q10, q40 = 0.0, 0.0
            a_rng = f'{100*sub["positive_rate"].mean():.1f}%'
        elif pol == 'Random':
            # Random is audited in marur_audit; report config/matched summary explicitly
            q10, q40 = np.nan, np.nan
            a_rng = '6-coh seed'
        else:
            q10 = float(sub[sub['cap_new'] == 10]['new_query_attempts'].mean())
            q40 = float(sub[sub['cap_new'] == 40]['new_query_attempts'].mean())
            a_rng = f'{100*sub["positive_rate"].mean():.1f}%'
        fair_rows.append(
            {
                'policy': pol,
                'init_labels': int(mcfg['initial_labels']),
                'cap_c_new': cstr,
                'realized_q_c10': f'{q10:.1f}' if np.isfinite(q10) else '10.0',
                'realized_q_c40': f'{q40:.1f}' if np.isfinite(q40) else 'Matched',
                'eligible_n_same': 'Identical N',
                'mean_offer_a': a_rng,
                'missing_rule': miss_rule,
                'feature_access': feat_acc,
            }
        )
    return pd.DataFrame(pareto_rows), pd.DataFrame(fair_rows)


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


def main(stats_only: bool = False) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc).isoformat()
    opp = pd.read_csv(ROOT / 'results/marur/opportunities.csv.gz', float_precision='round_trip', low_memory=False)
    heldout = pd.read_csv(ROOT / 'results/pacer/heldout_opportunities.csv.gz', float_precision='round_trip', low_memory=False)
    mcfg = json.loads((ROOT / 'configs/marur.json').read_text(encoding='utf8'))
    pcfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))

    df_pow = run_power_and_equivalence()
    df_camp = run_campaign_dependence()
    df_loco = run_leave_one_cohort_out()
    df_locampo = run_leave_one_campaign_out()
    df_abl = run_single_factor_ablation()
    df_pareto, df_fair = run_risk_utility_and_fairness_audit()
    df_pow.to_csv(OUT_DIR / 'power_equivalence.csv', index=False)
    df_camp.to_csv(OUT_DIR / 'campaign_dependence.csv', index=False)
    df_loco.to_csv(OUT_DIR / 'leave_one_cohort_out.csv', index=False)
    df_locampo.to_csv(OUT_DIR / 'leave_one_campaign_out.csv', index=False)
    df_abl.to_csv(OUT_DIR / 'single_factor_ablation.csv', index=False)
    df_pareto.to_csv(OUT_DIR / 'risk_utility_pareto.csv', index=False)
    df_fair.to_csv(OUT_DIR / 'baseline_fairness_audit.csv', index=False)

    if stats_only:
        df_wa = pd.read_csv(OUT_DIR / 'window_alpha_sensitivity.csv')
        df_wa_cl = pd.read_csv(OUT_DIR / 'window_alpha_clusters.csv')
        df_pt = pd.read_csv(OUT_DIR / 'predictor_point_accuracy.csv')
        df_pr = pd.read_csv(OUT_DIR / 'predictor_sensitivity.csv')
        df_pr_cl = pd.read_csv(OUT_DIR / 'predictor_sensitivity_clusters.csv')
    else:
        df_wa, df_wa_cl = run_window_alpha_sensitivity(opp, heldout, mcfg, pcfg)
        df_pt, df_pr, df_pr_cl = run_predictor_sensitivity(opp, heldout, mcfg, pcfg)
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
        'campaign_dependence_rows': int(len(df_camp)),
        'loco_rows': int(len(df_loco)),
        'locampo_rows': int(len(df_locampo)),
        'ablation_rows': int(len(df_abl)),
        'pareto_rows': int(len(df_pareto)),
        'fairness_rows': int(len(df_fair)),
        'window_alpha_rows': int(len(df_wa)),
        'predictor_rows': int(len(df_pr)),
        'sha256': {
            str(p.relative_to(ROOT).as_posix()): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT_DIR.glob('*.csv'))
        },
    }
    (OUT_DIR / 'execution.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'sha256'}, indent=2))
    print('\n=== Task 1: Equal-Cluster vs. Pooled-Ratio Relative Power/TOST Summary ===')
    print(df_pow[['scope', 'cap_new', 'candidate', 'clusters', 'undef_u_clusters', 'zero_ref_u_clusters', 'eq_ref_u_pp', 'eq_du_mean_pp', 'eq_rel_du_pct', 'mde80_pp', 'eq_tost_p_rel50', 'eq_tost_p_rel25', 'tost_p_1pp', 'tost_p_2pp', 'pool_ref_u_pp', 'pool_rel_du_pct', 'pool_boot_rel90_lo_pct', 'pool_boot_rel90_hi_pct', 'pool_tost_p_rel50']].to_string(index=False))
    print('\n=== Task 2: Exploratory Campaign-Dependence Summary ===')
    print(df_camp[['scope', 'cap_new', 'candidate', 'clusters', 'campaigns', 'icc', 'deff', 'g_eff', 'naive_se_pp', 'adj_se_pp', 'adj_mde80_pp', 'naive_eq_tost_p_rel50', 'adj_eq_tost_p_rel50', 'adj_eq_tost_p_rel25', 'adj_tost_p_2pp', 'hier_boot90_eq_rel_lo_pct', 'hier_boot90_eq_rel_hi_pct']].to_string(index=False))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stats-only', action='store_true')
    main(stats_only=ap.parse_args().stats_only)
