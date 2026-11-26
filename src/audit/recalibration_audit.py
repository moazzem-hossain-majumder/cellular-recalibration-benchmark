"""Practical empirical recalibration audit library for cellular throughput ledgers.

Computes positive-offer frequency A, exact finite-record conditional risk bounds
R_+ in [e/M, (e+m)/M], all-issued identity R = A * R_+ consistency verification,
supported measured throughput U, realized query expenditure, pooled and paired
cluster bootstrap / Student-t confidence intervals, relative-scale TOST
equivalence (+-50% and +-25% of reference U), absolute-scale TOST (+-1 / +-2 pp),
80%-power MDE, and automated operational warnings.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from scipy import stats

REQUIRED_CLUSTER_COLUMNS = {
    'cluster_id',
    'eligible',
    'offers',
    'violations',
    'missing_outcomes',
    'queries_charged',
}


def _solve_mde_t(se: float, df: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """Solve minimum detectable effect for a two-sided one-sample t-test at target power."""
    if not np.isfinite(df) or df < 1.0 or not np.isfinite(se) or se <= 0.0:
        return float('nan')
    t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df))
    lo, hi = 0.0, max(1e-6, (t_crit + float(stats.t.ppf(power, df))) * se * 2.5)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        nc = mid / se
        upper = float(stats.nct.sf(t_crit, df, nc))
        lower = float(stats.nct.cdf(-t_crit, df, nc)) if nc < 6.0 else 0.0
        cur = (0.0 if math.isnan(upper) else upper) + (0.0 if math.isnan(lower) else lower)
        if cur < power:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def normalize_ledger(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize either pre-aggregated cluster counts or tick-level decision logs."""
    df = frame.copy()
    if 'policy' not in df.columns:
        df['policy'] = 'Policy'
    if 'cluster_id' not in df.columns:
        for alt in ('unit', 'physical_unit', 'date'):
            if alt in df.columns:
                df['cluster_id'] = df[alt].astype(str)
                break
        else:
            raise ValueError('Ledger CSV must contain cluster_id, unit, physical_unit, or date.')
    else:
        df['cluster_id'] = df['cluster_id'].astype(str)

    if 'positive' in df.columns and 'offers' not in df.columns:
        df['offers'] = df['positive']
    if 'unresolved' in df.columns and 'missing_outcomes' not in df.columns:
        df['missing_outcomes'] = df['unresolved']
    if 'queries_new' in df.columns and 'queries_charged' not in df.columns:
        df['queries_charged'] = df['queries_new']

    if REQUIRED_CLUSTER_COLUMNS.issubset(df.columns):
        work = df.copy()
        for col in ('eligible', 'offers', 'violations', 'missing_outcomes', 'queries_charged'):
            work[col] = pd.to_numeric(work[col], errors='raise').astype(float)
        if 'observed_outcomes' not in work.columns:
            work['observed_outcomes'] = work['offers'] - work['missing_outcomes']
        else:
            work['observed_outcomes'] = pd.to_numeric(work['observed_outcomes'], errors='raise').astype(float)
            mismatch = work['observed_outcomes'] + work['missing_outcomes'] - work['offers']
            if (np.abs(mismatch) > 1e-6).any():
                raise ValueError('observed_outcomes + missing_outcomes must equal positive offers.')
        if 'observed_sum' not in work.columns:
            work['observed_sum'] = np.nan
        if 'delivered_sum' not in work.columns:
            work['delivered_sum'] = np.nan
        return work.groupby(['policy', 'cluster_id'], as_index=False, sort=True).agg(
            eligible=('eligible', 'sum'),
            offers=('offers', 'sum'),
            observed_outcomes=('observed_outcomes', 'sum'),
            violations=('violations', 'sum'),
            missing_outcomes=('missing_outcomes', 'sum'),
            queries_charged=('queries_charged', 'sum'),
            observed_sum=('observed_sum', lambda s: float(s.sum()) if s.notna().all() else float('nan')),
            delivered_sum=('delivered_sum', lambda s: float(s.sum()) if s.notna().all() else float('nan')),
        )

    tick_req = {'eligible', 'lower', 'y', 'query'}
    if not tick_req.issubset(df.columns):
        missing_cols = sorted(tick_req.union({'offers', 'violations', 'missing_outcomes', 'queries_charged'}).difference(df.columns))
        raise ValueError(f'Unrecognized ledger schema; missing required columns: {missing_cols}')

    elig = df['eligible'].astype(bool)
    lower = pd.to_numeric(df['lower'], errors='coerce')
    y = pd.to_numeric(df['y'], errors='coerce')
    query = pd.to_numeric(df['query'], errors='raise')

    df['eligible_n'] = elig.astype(float)
    df['offers_n'] = (elig & (lower > 0)).astype(float)
    df['obs_out_n'] = (elig & (lower > 0) & y.notna()).astype(float)
    df['viol_n'] = (elig & (lower > 0) & y.notna() & (lower > y)).astype(float)
    df['miss_n'] = (elig & (lower > 0) & y.isna()).astype(float)
    df['query_n'] = query.astype(float)
    valid = elig & y.notna()
    df['obs_sum_n'] = np.where(valid, y, 0.0)
    df['deliv_sum_n'] = np.where(valid, np.minimum(lower, y), 0.0)

    return (
        df.groupby(['policy', 'cluster_id'], as_index=False, sort=True)
        .agg(
            eligible=('eligible_n', 'sum'),
            offers=('offers_n', 'sum'),
            observed_outcomes=('obs_out_n', 'sum'),
            violations=('viol_n', 'sum'),
            missing_outcomes=('miss_n', 'sum'),
            queries_charged=('query_n', 'sum'),
            observed_sum=('obs_sum_n', 'sum'),
            delivered_sum=('deliv_sum_n', 'sum'),
        )
    )


def summarize_single_policy(
    cluster_df: pd.DataFrame,
    *,
    policy: str,
    min_clusters: int = 20,
    alpha: float = 0.10,
) -> dict:
    """Compute aggregate accounting metrics, R = A * R_+ identity check, and warnings."""
    sub = cluster_df[cluster_df['policy'] == policy].copy()
    if sub.empty:
        raise ValueError(f'Policy {policy!r} not present in normalized ledger.')

    n_elig = float(sub['eligible'].sum())
    m_pos = float(sub['offers'].sum())
    e_viol = float(sub['violations'].sum())
    m_miss = float(sub['missing_outcomes'].sum())
    obs_out = float(sub['observed_outcomes'].sum())
    queries = float(sub['queries_charged'].sum())
    n_clusters = int(sub['cluster_id'].nunique())

    offer_freq = m_pos / n_elig if n_elig > 0 else float('nan')
    r_all_lo = e_viol / n_elig if n_elig > 0 else float('nan')
    r_all_hi = (e_viol + m_miss) / n_elig if n_elig > 0 else float('nan')
    r_pos_lo = e_viol / m_pos if m_pos > 0 else float('nan')
    r_pos_hi = (e_viol + m_miss) / m_pos if m_pos > 0 else float('nan')
    id_err = max(abs(r_all_lo - offer_freq * r_pos_lo), abs(r_all_hi - offer_freq * r_pos_hi)) if (m_pos > 0 and n_elig > 0) else 0.0

    has_u = bool(sub['observed_sum'].notna().all() and sub['delivered_sum'].notna().all() and sub['observed_sum'].sum() > 0)
    supported_u = float(sub['delivered_sum'].sum() / sub['observed_sum'].sum()) if has_u else float('nan')

    warnings: list[str] = []
    if m_pos == 0:
        warnings.append('zero positive offers')
    else:
        zero_clusters = int((sub['offers'] == 0).sum())
        if zero_clusters > 0:
            warnings.append(f'zero positive offers in {zero_clusters} of {n_clusters} clusters')
        if offer_freq < 0.25:
            warnings.append(f'heavy abstention (offer frequency A={offer_freq:.3f} < 0.25)')
        if r_pos_lo <= alpha < r_pos_hi:
            warnings.append(f'conditional risk bounds unresolved across alpha={alpha:.2f} ([{r_pos_lo:.3f}, {r_pos_hi:.3f}])')
        if m_miss / m_pos > 0.15:
            warnings.append(f'elevated missingness among positive offers ({int(m_miss)}/{int(m_pos)} = {m_miss/m_pos:.1%})')
    if n_clusters < min_clusters:
        warnings.append(f'fewer than {min_clusters} clusters (G={n_clusters})')

    return {
        'policy': policy,
        'clusters': n_clusters,
        'eligible_ticks': int(round(n_elig)),
        'positive_offers': int(round(m_pos)),
        'observed_offer_outcomes': int(round(obs_out)),
        'observed_violations': int(round(e_viol)),
        'missing_offer_outcomes': int(round(m_miss)),
        'realized_queries': int(round(queries)),
        'offer_frequency_A': offer_freq,
        'all_issued_risk_lo': r_all_lo,
        'all_issued_risk_hi': r_all_hi,
        'conditional_risk_lo': r_pos_lo,
        'conditional_risk_hi': r_pos_hi,
        'r_identity_max_abs_err': float(id_err),
        'supported_throughput_U': supported_u,
        'warnings': warnings,
    }


def _tost_p(mean: float, se: float, df: int, margin: float) -> float:
    if df < 1 or not np.isfinite(se) or se <= 0.0 or not np.isfinite(margin) or margin <= 0.0:
        return float('nan')
    p1 = float(1.0 - stats.t.cdf((mean + margin) / se, df=df))
    p2 = float(stats.t.cdf((mean - margin) / se, df=df))
    return max(p1, p2)


def compare_policies_paired(
    cluster_df: pd.DataFrame,
    *,
    candidate: str,
    reference: str,
    min_clusters: int = 20,
    n_boot: int = 2000,
    seed: int = 42,
    equiv_margins_pp: Sequence[float] = (1.0, 2.0),
    rel_margins_pct: Sequence[float] = (50.0, 25.0),
) -> dict:
    """Compute matched-cluster bootstrap CIs, t intervals, relative/absolute TOST, MDE, and warnings."""
    c_df = cluster_df[cluster_df['policy'] == candidate].set_index('cluster_id').sort_index()
    r_df = cluster_df[cluster_df['policy'] == reference].set_index('cluster_id').sort_index()
    if c_df.empty or r_df.empty:
        raise ValueError('Both candidate and reference policies must be present in ledger.')
    common = c_df.index.intersection(r_df.index)
    if len(common) == 0:
        raise ValueError('No aligned clusters shared between candidate and reference policies.')
    c_df = c_df.loc[common]
    r_df = r_df.loc[common]

    g_count = len(common)
    c_del = c_df['delivered_sum'].to_numpy(dtype=float)
    c_obs = c_df['observed_sum'].to_numpy(dtype=float)
    r_del = r_df['delivered_sum'].to_numpy(dtype=float)
    r_obs = r_df['observed_sum'].to_numpy(dtype=float)
    has_u = not (np.isnan(c_del).any() or np.isnan(c_obs).any() or np.isnan(r_del).any() or np.isnan(r_obs).any())

    c_v = c_df['violations'].to_numpy(dtype=float)
    c_m = c_df['missing_outcomes'].to_numpy(dtype=float)
    c_pos = c_df['offers'].to_numpy(dtype=float)
    r_v = r_df['violations'].to_numpy(dtype=float)
    r_m = r_df['missing_outcomes'].to_numpy(dtype=float)
    r_pos = r_df['offers'].to_numpy(dtype=float)

    pool_dpos_hi = (
        float((c_v.sum() + c_m.sum()) / c_pos.sum() - (r_v.sum() + r_m.sum()) / r_pos.sum())
        if c_pos.sum() > 0 and r_pos.sum() > 0
        else float('nan')
    )
    eq_c_pos = np.where(c_pos > 0, (c_v + c_m) / np.where(c_pos > 0, c_pos, 1.0), np.nan)
    eq_r_pos = np.where(r_pos > 0, (r_v + r_m) / np.where(r_pos > 0, r_pos, 1.0), np.nan)
    valid_pos = ~(np.isnan(eq_c_pos) | np.isnan(eq_r_pos))
    eq_dpos_hi = float(np.mean(eq_c_pos[valid_pos] - eq_r_pos[valid_pos])) if valid_pos.any() else float('nan')

    ref_pool_u_pp = float('nan')
    zero_ref_u_clusters = 0
    pooled_rel_du_pct = float('nan')
    boot_rel_du_ci95_pct = [float('nan'), float('nan')]
    boot_rel_du_ci90_pct = [float('nan'), float('nan')]
    tost_rel_p: dict[str, float] = {}
    tost_abs_p: dict[str, float] = {}

    if has_u and c_obs.sum() > 0 and r_obs.sum() > 0:
        pool_uc = float(c_del.sum() / c_obs.sum())
        pool_ur = float(r_del.sum() / r_obs.sum())
        pool_du = pool_uc - pool_ur
        ref_pool_u_pp = 100.0 * pool_ur
        pooled_rel_du_pct = 100.0 * (pool_uc / pool_ur - 1.0) if pool_ur > 0 else float('nan')

        c_u_cl = c_del / np.where(c_obs > 0, c_obs, np.nan)
        r_u_cl = r_del / np.where(r_obs > 0, r_obs, np.nan)
        zero_ref_u_clusters = int(np.sum(np.isfinite(r_u_cl) & (r_u_cl <= 0.0)))
        eq_u_diff = c_u_cl - r_u_cl
        valid_u = eq_u_diff[~np.isnan(eq_u_diff)] * 100.0
        n_u = len(valid_u)
        eq_du_pp = float(np.mean(valid_u)) if n_u > 0 else float('nan')
        sd_du_pp = float(np.std(valid_u, ddof=1)) if n_u > 1 else float('nan')
        se_du_pp = sd_du_pp / math.sqrt(n_u) if n_u > 1 else float('nan')
        if n_u > 1 and se_du_pp > 1e-12:
            t_lo, t_hi = stats.t.interval(0.95, df=n_u - 1, loc=eq_du_pp, scale=se_du_pp)
            mde_80 = _solve_mde_t(se_du_pp, n_u - 1)
            for mg in equiv_margins_pp:
                tost_abs_p[f'+-{mg:g}pp'] = _tost_p(eq_du_pp, se_du_pp, n_u - 1, mg)
            for rp in rel_margins_pct:
                mg_rel_pp = (rp / 100.0) * ref_pool_u_pp
                tost_rel_p[f'+-{rp:g}%'] = _tost_p(eq_du_pp, se_du_pp, n_u - 1, mg_rel_pp)
        elif n_u > 1:
            t_lo, t_hi, mde_80 = eq_du_pp, eq_du_pp, 0.0
            for mg in equiv_margins_pp:
                tost_abs_p[f'+-{mg:g}pp'] = 0.0 if abs(eq_du_pp) < mg else 1.0
            for rp in rel_margins_pct:
                mg_rel_pp = (rp / 100.0) * ref_pool_u_pp
                tost_rel_p[f'+-{rp:g}%'] = 0.0 if (np.isfinite(mg_rel_pp) and abs(eq_du_pp) < mg_rel_pp) else 1.0
        else:
            t_lo, t_hi, mde_80 = float('nan'), float('nan'), float('nan')
    else:
        pool_du = eq_du_pp = sd_du_pp = se_du_pp = t_lo = t_hi = mde_80 = float('nan')

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, g_count, size=(n_boot, g_count))
    boot_dpos_hi_lo = boot_dpos_hi_hi = boot_du_lo = boot_du_hi = float('nan')
    if has_u:
        co = c_obs[idx].sum(axis=1)
        ro = r_obs[idx].sum(axis=1)
        cd = c_del[idx].sum(axis=1)
        rd = r_del[idx].sum(axis=1)
        ok_u = (co > 0) & (ro > 0)
        if ok_u.any():
            bu_c = cd[ok_u] / co[ok_u]
            bu_r = rd[ok_u] / ro[ok_u]
            boot_du_lo, boot_du_hi = [float(x) for x in np.percentile(100.0 * (bu_c - bu_r), [2.5, 97.5])]
            ok_rel = bu_r > 0
            if ok_rel.any():
                brel = 100.0 * (bu_c[ok_rel] / bu_r[ok_rel] - 1.0)
                boot_rel_du_ci95_pct = [float(x) for x in np.percentile(brel, [2.5, 97.5])]
                boot_rel_du_ci90_pct = [float(x) for x in np.percentile(brel, [5.0, 95.0])]

    cp = c_pos[idx].sum(axis=1)
    rp = r_pos[idx].sum(axis=1)
    ok_p = (cp > 0) & (rp > 0)
    if ok_p.any():
        bp = 100.0 * ((c_v[idx][ok_p].sum(axis=1) + c_m[idx][ok_p].sum(axis=1)) / cp[ok_p] - (r_v[idx][ok_p].sum(axis=1) + r_m[idx][ok_p].sum(axis=1)) / rp[ok_p])
        boot_dpos_hi_lo, boot_dpos_hi_hi = [float(x) for x in np.percentile(bp, [2.5, 97.5])]

    q_cand = int(round(c_df['queries_charged'].sum()))
    q_ref = int(round(r_df['queries_charged'].sum()))
    warnings: list[str] = []
    if c_pos.sum() == 0 or r_pos.sum() == 0:
        warnings.append('zero positive offers')
    if q_cand != q_ref:
        warnings.append(f'queries unmatched across policies ({candidate}={q_cand} vs {reference}={q_ref})')
    if g_count < min_clusters:
        warnings.append(f'fewer than {min_clusters} clusters (G={g_count})')
    if np.isfinite(pool_dpos_hi) and np.isfinite(eq_dpos_hi) and abs(pool_dpos_hi - eq_dpos_hi) > 0.05:
        warnings.append(f'pooling sensitivity: offer-weighted dR+hi ({100*pool_dpos_hi:+.2f} pp) diverges from equal-cluster ({100*eq_dpos_hi:+.2f} pp)')
    if tost_rel_p.get('+-50%', 1.0) >= 0.05:
        warnings.append('relative TOST +-50% inconclusive (cannot rule out +-50% change relative to baseline U)')

    return {
        'candidate': candidate,
        'reference': reference,
        'clusters': g_count,
        'joint_active_clusters': int(valid_pos.sum()),
        'queries_candidate': q_cand,
        'queries_reference': q_ref,
        'queries_matched': q_cand == q_ref,
        'ref_pooled_u_pp': ref_pool_u_pp,
        'zero_ref_u_clusters': zero_ref_u_clusters,
        'pooled_rel_du_pct': pooled_rel_du_pct,
        'boot_rel_du_ci95_pct': boot_rel_du_ci95_pct,
        'boot_rel_du_ci90_pct': boot_rel_du_ci90_pct,
        'tost_rel_p_values': tost_rel_p,
        'pooled_du_pp': 100.0 * pool_du if np.isfinite(pool_du) else float('nan'),
        'boot_du_ci95_pp': [boot_du_lo, boot_du_hi],
        'equal_cluster_du_pp': eq_du_pp,
        'between_cluster_sd_pp': sd_du_pp,
        't_du_ci95_pp': [float(t_lo), float(t_hi)],
        'mde80_du_pp': mde_80,
        'tost_p_values': tost_abs_p,
        'pooled_dpos_hi_pp': 100.0 * pool_dpos_hi if np.isfinite(pool_dpos_hi) else float('nan'),
        'boot_dpos_hi_ci95_pp': [boot_dpos_hi_lo, boot_dpos_hi_hi],
        'equal_cluster_dpos_hi_pp': 100.0 * eq_dpos_hi if np.isfinite(eq_dpos_hi) else float('nan'),
        'warnings': warnings,
    }


def audit_ledger(
    frame: pd.DataFrame,
    *,
    reference: str | None = None,
    min_clusters: int = 20,
    alpha: float = 0.10,
    n_boot: int = 2000,
    seed: int = 42,
    equiv_margins_pp: Iterable[float] = (1.0, 2.0),
    rel_margins_pct: Iterable[float] = (50.0, 25.0),
) -> dict:
    """Run complete single-policy and paired-policy empirical accounting audit."""
    cluster_df = normalize_ledger(frame)
    policies = sorted(cluster_df['policy'].unique().tolist())
    summaries = {
        pol: summarize_single_policy(cluster_df, policy=pol, min_clusters=min_clusters, alpha=alpha)
        for pol in policies
    }
    comparisons = []
    if len(policies) >= 2:
        ref_pol = reference if reference in policies else ('Periodic' if 'Periodic' in policies else policies[0])
        margins = tuple(float(m) for m in equiv_margins_pp)
        rmargins = tuple(float(m) for m in rel_margins_pct)
        for pol in policies:
            if pol == ref_pol:
                continue
            comparisons.append(
                compare_policies_paired(
                    cluster_df,
                    candidate=pol,
                    reference=ref_pol,
                    min_clusters=min_clusters,
                    n_boot=n_boot,
                    seed=seed,
                    equiv_margins_pp=margins,
                    rel_margins_pct=rmargins,
                )
            )
    return {
        'policies': summaries,
        'comparisons': comparisons,
        'checklist': [
            'Report realized positive-offer frequency A = M/N alongside eligible denominator N.',
            'Report exact finite-record conditional risk bounds [e/M, (e+m)/M] rather than only all-issued R.',
            'Verify identity R = A * R_+ on both lower and upper endpoints.',
            'Report realized query attempts Q_new separately from initial pre-test calibration labels.',
            'Evaluate comparisons at physical cluster and campaign levels with between-cluster SD, MDE, and relative TOST.',
            'Declare how missing outcomes enter buffers and inspect equal-cluster vs. offer-weighted pooling.',
        ],
    }
