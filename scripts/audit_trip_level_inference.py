"""Independent collection-unit accounting and paired cluster inference for MARUR.

Computes whole-date and physical-campaign-date paired comparisons, exact
cluster bootstrap CIs, paired Student-t intervals, leave-one-date-out
sensitivity ranges, and budget-exhaustion / single-date concentration metrics
from saved authoritative MARUR ledgers without modifying existing outcomes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Exact two-sided Student-t 97.5th percentile quantiles (df = 1..20) checked against scipy.stats.t.ppf
T_CRIT_975 = {
    1: 12.70620474,
    2: 4.30265273,
    3: 3.18244631,
    4: 2.77644511,
    5: 2.57058184,
    6: 2.44691185,
    7: 2.36462425,
    8: 2.30600414,
    9: 2.26215716,
    10: 2.22813885,
    11: 2.20098516,
    12: 2.17881283,
    13: 2.16036866,
    14: 2.14478669,
    15: 2.13144955,
    16: 2.11990530,
    17: 2.10981558,
    18: 2.10092204,
    19: 2.09302405,
    20: 2.08596345,
}


def t_quantile_975(df: int) -> float:
    """Return two-sided 95% Student-t critical multiplier for df >= 1."""
    if df < 1:
        return float('nan')
    if df in T_CRIT_975:
        return T_CRIT_975[df]
    return 1.95996398


def physical_campaign_key(cohort: str, date: str) -> str:
    """Map cohort-date rows to shared physical campaign-date clusters."""
    if cohort in ('E1', 'E3'):
        return f'Rome:{date}'
    if cohort in ('AT&T', 'T-Mobile', 'Verizon'):
        return f'US_Drive3:{date}'
    return f'{cohort}:{date}'


def physical_campaign_name(cohort: str) -> str:
    """Map cohort identifier to underlying physical driving campaign."""
    if cohort in ('E1', 'E3'):
        return 'Rome_2023'
    if cohort in ('AT&T', 'T-Mobile', 'Verizon'):
        return 'US_NUWiNS_Drive3'
    return 'Ireland_UCC_Drive'


def _paired_cluster_stats(
    cand: pd.DataFrame,
    ref: pd.DataFrame,
    *,
    n_boot: int = 2000,
    seed: int = 42,
) -> dict:
    """Compute paired cluster-level differences (cand - ref) over aligned rows."""
    if not cand.index.equals(ref.index):
        raise ValueError('Cluster indexes do not match')
    g_count = len(cand)
    m_del = cand['delivered_sum'].to_numpy(dtype=float)
    m_obs = cand['observed_sum'].to_numpy(dtype=float)
    b_del = ref['delivered_sum'].to_numpy(dtype=float)
    b_obs = ref['observed_sum'].to_numpy(dtype=float)

    m_viol = cand['violations'].to_numpy(dtype=float)
    m_unres = cand['unresolved'].to_numpy(dtype=float)
    m_pos = cand['positive'].to_numpy(dtype=float)
    m_elig = cand['eligible'].to_numpy(dtype=float)

    b_viol = ref['violations'].to_numpy(dtype=float)
    b_unres = ref['unresolved'].to_numpy(dtype=float)
    b_pos = ref['positive'].to_numpy(dtype=float)
    b_elig = ref['eligible'].to_numpy(dtype=float)

    pool_du = float(m_del.sum() / m_obs.sum() - b_del.sum() / b_obs.sum())
    pool_dhi = float((m_viol.sum() + m_unres.sum()) / m_elig.sum() - (b_viol.sum() + b_unres.sum()) / b_elig.sum())
    pool_dpos_hi = (
        float((m_viol.sum() + m_unres.sum()) / m_pos.sum() - (b_viol.sum() + b_unres.sum()) / b_pos.sum())
        if m_pos.sum() > 0 and b_pos.sum() > 0
        else float('nan')
    )

    eq_m_u = np.where(m_obs > 0, m_del / np.where(m_obs > 0, m_obs, 1.0), np.nan)
    eq_b_u = np.where(b_obs > 0, b_del / np.where(b_obs > 0, b_obs, 1.0), np.nan)
    eq_du = eq_m_u - eq_b_u
    valid_eq = eq_du[~np.isnan(eq_du)]
    eq_mean = float(np.mean(valid_eq))
    if len(valid_eq) > 1:
        sd = float(np.std(valid_eq, ddof=1))
        hw = t_quantile_975(len(valid_eq) - 1) * sd / float(np.sqrt(len(valid_eq)))
        t_lo, t_hi = eq_mean - hw, eq_mean + hw
    else:
        t_lo, t_hi = float('nan'), float('nan')

    # Whole-cluster bootstrap with replacement
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, g_count, size=(n_boot, g_count))
    boot_m_obs = m_obs[idx].sum(axis=1)
    boot_b_obs = b_obs[idx].sum(axis=1)
    valid_u_boot = (boot_m_obs > 0) & (boot_b_obs > 0)
    du_boot = (
        m_del[idx].sum(axis=1)[valid_u_boot] / boot_m_obs[valid_u_boot]
        - b_del[idx].sum(axis=1)[valid_u_boot] / boot_b_obs[valid_u_boot]
    )
    dhi_boot = (m_viol[idx].sum(axis=1) + m_unres[idx].sum(axis=1)) / m_elig[idx].sum(axis=1) - (
        b_viol[idx].sum(axis=1) + b_unres[idx].sum(axis=1)
    ) / b_elig[idx].sum(axis=1)

    bm_pos = m_pos[idx].sum(axis=1)
    bb_pos = b_pos[idx].sum(axis=1)
    valid_pos = (bm_pos > 0) & (bb_pos > 0)
    if valid_pos.any():
        dpos_boot = (
            (m_viol[idx].sum(axis=1)[valid_pos] + m_unres[idx].sum(axis=1)[valid_pos]) / bm_pos[valid_pos]
            - (b_viol[idx].sum(axis=1)[valid_pos] + b_unres[idx].sum(axis=1)[valid_pos]) / bb_pos[valid_pos]
        )
        pos_boot_lo = float(np.percentile(dpos_boot, 2.5))
        pos_boot_hi = float(np.percentile(dpos_boot, 97.5))
    else:
        pos_boot_lo = pos_boot_hi = float('nan')

    # Leave-one-cluster-out range for pooled dU
    loo_du = []
    if g_count > 1:
        for i in range(g_count):
            mask = np.arange(g_count) != i
            if m_obs[mask].sum() > 0 and b_obs[mask].sum() > 0:
                loo_du.append(float(m_del[mask].sum() / m_obs[mask].sum() - b_del[mask].sum() / b_obs[mask].sum()))

    return {
        'clusters': int(g_count),
        'pool_du': pool_du,
        'boot_du_lo': float(np.percentile(du_boot, 2.5)),
        'boot_du_hi': float(np.percentile(du_boot, 97.5)),
        'eq_du_mean': eq_mean,
        't_du_lo': float(t_lo),
        't_du_hi': float(t_hi),
        'eq_du_positive_clusters': int(np.sum(valid_eq > 0)),
        'eq_du_negative_clusters': int(np.sum(valid_eq < 0)),
        'loo_du_min': float(min(loo_du)) if loo_du else float('nan'),
        'loo_du_max': float(max(loo_du)) if loo_du else float('nan'),
        'pool_dhi': pool_dhi,
        'boot_dhi_lo': float(np.percentile(dhi_boot, 2.5)),
        'boot_dhi_hi': float(np.percentile(dhi_boot, 97.5)),
        'pool_dpos_hi': pool_dpos_hi,
        'boot_dpos_hi_lo': pos_boot_lo,
        'boot_dpos_hi_hi': pos_boot_hi,
        'valid_pos_boot_draws': int(np.sum(valid_pos)),
        'boot_draws': int(n_boot),
    }


def run_audit(root: Path = ROOT) -> dict:
    """Compute complete collection-unit paired comparisons and cluster inference."""
    audit_dir = root / 'results/marur_audit'
    diag_dir = root / 'results/diagnostics'
    dates = pd.read_csv(audit_dir / 'matched_cost_dates.csv', float_precision='round_trip')
    dates['campaign_date'] = [physical_campaign_key(c, dt) for c, dt in zip(dates['cohort'], dates['date'])]
    dates['campaign'] = [physical_campaign_name(c) for c in dates['cohort']]

    rows = []
    # Per-cohort date-cluster inference
    for (model, scenario, cap, cohort), grp in dates.groupby(['model', 'scenario', 'new_query_cap', 'cohort'], sort=True):
        cand_df = grp[grp['policy'] == 'MARUR'].set_index('date').sort_index()
        for baseline in ['Periodic', 'Early', 'ACI', 'Frozen']:
            ref_df = grp[grp['policy'] == baseline].set_index('date').sort_index()
            stats = _paired_cluster_stats(cand_df, ref_df)
            q_m = int(cand_df['new_query_attempts'].sum())
            q_b = int(ref_df['new_query_attempts'].sum())
            rows.append({
                'scope': cohort,
                'level': 'cohort_date',
                'model': model,
                'scenario': scenario,
                'new_query_cap': int(cap),
                'candidate': 'MARUR',
                'baseline': baseline,
                'matched_cost': bool(q_m == q_b == cap),
                'cand_queries': q_m,
                'base_queries': q_b,
                'cand_query_days': int((cand_df['new_query_attempts'] > 0).sum()),
                'base_query_days': int((ref_df['new_query_attempts'] > 0).sum()),
                'cand_pos_days': int((cand_df['positive'] > 0).sum()),
                'base_pos_days': int((ref_df['positive'] > 0).sum()),
                **stats,
            })

    # Shared physical campaign-date clustering across ALL cohorts (G_phys = 16 unique dates across 3 campaigns)
    agg_cols = ['delivered_sum', 'observed_sum', 'violations', 'unresolved', 'positive', 'eligible', 'new_query_attempts']
    for (model, scenario, cap), grp in dates.groupby(['model', 'scenario', 'new_query_cap'], sort=True):
        cd = grp.groupby(['campaign_date', 'policy'], sort=True)[agg_cols].sum().reset_index()
        cand_cd = cd[cd['policy'] == 'MARUR'].set_index('campaign_date').sort_index()
        for baseline in ['Periodic', 'Early', 'ACI', 'Frozen']:
            ref_cd = cd[cd['policy'] == baseline].set_index('campaign_date').sort_index()
            stats = _paired_cluster_stats(cand_cd, ref_cd)
            q_m = int(cand_cd['new_query_attempts'].sum())
            q_b = int(ref_cd['new_query_attempts'].sum())
            rows.append({
                'scope': 'Combined_CampaignDates',
                'level': 'physical_campaign_date',
                'model': model,
                'scenario': scenario,
                'new_query_cap': int(cap),
                'candidate': 'MARUR',
                'baseline': baseline,
                'matched_cost': bool(all(
                    (grp[grp['policy'] == 'MARUR'].groupby('cohort')['new_query_attempts'].sum() == cap).all()
                    for _ in [0]
                ) and (grp[grp['policy'] == baseline].groupby('cohort')['new_query_attempts'].sum() == cap).all()),
                'cand_queries': q_m,
                'base_queries': q_b,
                'cand_query_days': int((cand_cd['new_query_attempts'] > 0).sum()),
                'base_query_days': int((ref_cd['new_query_attempts'] > 0).sum()),
                'cand_pos_days': int((cand_cd['positive'] > 0).sum()),
                'base_pos_days': int((ref_cd['positive'] > 0).sum()),
                **stats,
            })

    # Ireland within-cohort individual driving-trace clustering (11 traces across 5 dates)
    opp = pd.read_csv(root / 'results/marur/opportunities.csv.gz', usecols=['cohort', 'id', 'trace'])
    ie_traces = opp[opp['cohort'] == 'Ireland'][['id', 'trace']]
    act = pd.read_csv(audit_dir / 'matched_cost_actions.csv.gz', float_precision='round_trip')
    ie_act = act[(act['cohort'] == 'Ireland') & act['eligible']].merge(ie_traces, on='id', how='left', validate='many_to_one')
    ie_rows = []
    for (model, scenario, cap, policy, tr), grp in ie_act.groupby(['model', 'scenario', 'new_query_cap', 'policy', 'trace'], sort=True):
        pos = grp['lower'] > 0
        ie_rows.append({
            'model': model,
            'scenario': scenario,
            'new_query_cap': int(cap),
            'policy': policy,
            'trace': str(tr),
            'delivered_sum': float(np.nansum(np.minimum(grp['lower'], grp['y']))),
            'observed_sum': float(grp['y'].sum()),
            'violations': int((grp['lower'] > grp['y']).sum()),
            'unresolved': int((pos & grp['y'].isna()).sum()),
            'positive': int(pos.sum()),
            'eligible': int(len(grp)),
            'new_query_attempts': int(grp['query'].sum()),
        })
    ie_df = pd.DataFrame(ie_rows)
    for (model, scenario, cap), grp in ie_df.groupby(['model', 'scenario', 'new_query_cap'], sort=True):
        cand_tr = grp[grp['policy'] == 'MARUR'].set_index('trace').sort_index()
        for baseline in ['Periodic', 'Early', 'ACI', 'Frozen']:
            ref_tr = grp[grp['policy'] == baseline].set_index('trace').sort_index()
            stats = _paired_cluster_stats(cand_tr, ref_tr)
            rows.append({
                'scope': 'Ireland_Traces',
                'level': 'driving_trace',
                'model': model,
                'scenario': scenario,
                'new_query_cap': int(cap),
                'candidate': 'MARUR',
                'baseline': baseline,
                'matched_cost': bool(int(cand_tr['new_query_attempts'].sum()) == int(ref_tr['new_query_attempts'].sum()) == cap),
                'cand_queries': int(cand_tr['new_query_attempts'].sum()),
                'base_queries': int(ref_tr['new_query_attempts'].sum()),
                'cand_query_days': int((cand_tr['new_query_attempts'] > 0).sum()),
                'base_query_days': int((ref_tr['new_query_attempts'] > 0).sum()),
                'cand_pos_days': int((cand_tr['positive'] > 0).sum()),
                'base_pos_days': int((ref_tr['positive'] > 0).sum()),
                **stats,
            })

    out_df = pd.DataFrame(rows)
    diag_dir.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(diag_dir / 'trip_level_inference.csv', index=False)

    payload = {
        'inventory': {
            'geographic_campaigns': int(dates['campaign'].nunique()),
            'campaign_names': sorted(dates['campaign'].unique().tolist()),
            'unique_physical_campaign_dates': int(dates['campaign_date'].nunique()),
            'cohort_date_counts': {k: int(v) for k, v in dates.groupby('cohort')['date'].nunique().items()},
            'ireland_test_traces': int(ie_df['trace'].nunique()),
            'rome_shared_test_dates': int(dates[dates['cohort'].isin(['E1', 'E3'])]['date'].nunique()),
            'us_drive3_shared_test_dates': int(dates[dates['cohort'].isin(['AT&T', 'T-Mobile', 'Verizon'])]['date'].nunique()),
        },
        'primary_slice': out_df[
            (out_df['model'] == 'HistGBM')
            & (out_df['scenario'] == 'Recorded')
            & (out_df['new_query_cap'] == 10)
            & (out_df['baseline'] == 'Periodic')
        ].to_dict(orient='records'),
        'all_records_count': int(len(out_df)),
    }
    (diag_dir / 'trip_level_inference.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf8')
    return payload


if __name__ == '__main__':
    res = run_audit()
    print(f"Audited {res['all_records_count']} cluster-level contrasts across {res['inventory']['unique_physical_campaign_dates']} physical campaign-dates and {res['inventory']['geographic_campaigns']} campaigns.")
