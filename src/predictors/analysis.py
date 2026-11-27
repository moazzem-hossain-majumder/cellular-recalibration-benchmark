"""Downstream audit, campaign-level bootstrap ablation, TOST/DEFF, sieve, and multiplicity."""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy import stats

from src.audit.recalibration_audit import _solve_mde_t, compare_policies_paired
from src.predictors.datasets import COHORT_TO_CAMPAIGN

ALL_CAMPAIGNS = sorted(set(COHORT_TO_CAMPAIGN.values()))
RETRO_CAMPAIGNS = sorted({v for k, v in COHORT_TO_CAMPAIGN.items() if k in ('E1', 'E3', 'AT&T', 'T-Mobile', 'Verizon', 'Ireland')})
HELDOUT_CAMPAIGNS = sorted({v for k, v in COHORT_TO_CAMPAIGN.items() if k not in ('E1', 'E3', 'AT&T', 'T-Mobile', 'Verizon', 'Ireland')})


def adjust_pvalues_holm_bh(p_values: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    """Compute exact Holm-Bonferroni and Benjamini-Hochberg adjusted p-values, preserving NaNs."""
    raw = np.asarray(p_values, dtype=float)
    holm = np.full_like(raw, np.nan, dtype=float)
    bh = np.full_like(raw, np.nan, dtype=float)
    valid_idx = np.where(np.isfinite(raw))[0]
    m = len(valid_idx)
    if m == 0:
        return holm, bh

    vals = np.clip(raw[valid_idx], 0.0, 1.0)
    order = np.argsort(vals, kind='mergesort')
    sorted_p = vals[order]

    # Step-down Holm-Bonferroni
    mult_holm = m - np.arange(m, dtype=float)
    adj_h = np.minimum(1.0, np.maximum.accumulate(sorted_p * mult_holm))
    holm[valid_idx[order]] = adj_h

    # Step-up Benjamini-Hochberg FDR
    ranks = np.arange(1, m + 1, dtype=float)
    raw_bh = sorted_p * (m / ranks)
    adj_b = np.minimum(1.0, np.maximum(0.0, np.minimum.accumulate(raw_bh[::-1])[::-1]))
    bh[valid_idx[order]] = adj_b
    return holm, bh


def _donner_campaign_tost(
    cand_df: pd.DataFrame,
    ref_df: pd.DataFrame,
    unit_to_campaign: dict[str, str],
    *,
    rel_margins_pct: Sequence[float] = (50.0, 25.0),
    abs_margins_pp: Sequence[float] = (1.0, 2.0),
    n_boot: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute naive and Donner/campaign-DEFF adjusted TOST plus hierarchical two-stage campaign bootstrap."""
    common = cand_df.index.intersection(ref_df.index)
    c = cand_df.loc[common]
    r = ref_df.loc[common]

    uc = 100.0 * np.where(c['observed_sum'] > 0, c['delivered_sum'] / c['observed_sum'], np.nan)
    ur = 100.0 * np.where(r['observed_sum'] > 0, r['delivered_sum'] / r['observed_sum'], np.nan)
    valid_u = np.isfinite(uc) & np.isfinite(ur)
    units = common[valid_u]
    diff = pd.Series(uc[valid_u] - ur[valid_u], index=units)
    ur_ser = pd.Series(ur[valid_u], index=units)

    n_tot = len(diff)
    if n_tot < 2:
        return {
            'campaigns': 0,
            'icc': float('nan'),
            'deff': float('nan'),
            'g_eff': float('nan'),
            'adj_se_pp': float('nan'),
            'adj_mde80_pp': float('nan'),
            'adj_eq_tost_p_rel50': float('nan'),
            'adj_eq_tost_p_rel25': float('nan'),
            'adj_tost_p_1pp': float('nan'),
            'adj_tost_p_2pp': float('nan'),
            'hier_boot90_eq_rel_lo_pct': float('nan'),
            'hier_boot90_eq_rel_hi_pct': float('nan'),
        }

    camps = pd.Series([unit_to_campaign[u] for u in units], index=units)
    groups = [diff[camps == cp].to_numpy(dtype=float) for cp in sorted(camps.unique())]
    k_camp = len(groups)
    ns = np.array([len(g) for g in groups], dtype=float)
    grand = float(diff.mean())
    eq_ref_u = float(ur_ser.mean())
    naive_sd = float(diff.std(ddof=1))
    naive_se = naive_sd / math.sqrt(n_tot)

    if k_camp >= 2 and n_tot > k_camp:
        ssb = float(sum(len(g) * (g.mean() - grand) ** 2 for g in groups))
        ssw = float(sum(((g - g.mean()) ** 2).sum() for g in groups))
        msb = ssb / (k_camp - 1)
        msw = ssw / (n_tot - k_camp)
        n0 = (n_tot - float((ns ** 2).sum()) / n_tot) / (k_camp - 1)
        var_b = max(0.0, (msb - msw) / n0) if n0 > 0 else 0.0
        icc = var_b / (var_b + msw) if (var_b + msw) > 0 else 0.0
        m_eff = float((ns ** 2).sum()) / n_tot
        deff = 1.0 + (m_eff - 1.0) * icc
    else:
        icc = 0.0
        deff = 1.0

    g_eff = n_tot / deff
    adj_se = naive_se * math.sqrt(deff)
    df_adj = max(1.0, g_eff - 1.0)

    def _tost(margin: float) -> float:
        if not np.isfinite(adj_se) or adj_se <= 1e-12 or not np.isfinite(margin) or margin <= 0.0:
            return 0.0 if (np.isfinite(margin) and margin > 0 and abs(grand) < margin) else float('nan')
        p1 = float(1.0 - stats.t.cdf((grand + margin) / adj_se, df=df_adj))
        p2 = float(stats.t.cdf((grand - margin) / adj_se, df=df_adj))
        return max(p1, p2)

    mde_adj = _solve_mde_t(adj_se, df_adj, alpha=0.05, power=0.80) if adj_se > 1e-12 else float('nan')

    rng = np.random.default_rng(seed)
    camp_names = sorted(camps.unique())
    camp_idx = {cp: np.where(camps.to_numpy() == cp)[0] for cp in camp_names}
    hb_eq_rel = []
    for _ in range(n_boot):
        chosen = rng.choice(camp_names, size=len(camp_names), replace=True)
        idx_b = np.concatenate([rng.choice(camp_idx[cp], size=len(camp_idx[cp]), replace=True) for cp in chosen])
        du_b = float(diff.iloc[idx_b].mean())
        ur_b = float(ur_ser.iloc[idx_b].mean())
        if ur_b > 0.0:
            hb_eq_rel.append(100.0 * du_b / ur_b)
    h90_lo, h90_hi = (
        [float(x) for x in np.percentile(hb_eq_rel, [5.0, 95.0])]
        if hb_eq_rel
        else [float('nan'), float('nan')]
    )
    out: dict[str, Any] = {
        'campaigns': int(k_camp),
        'icc': float(icc),
        'deff': float(deff),
        'g_eff': float(g_eff),
        'adj_se_pp': float(adj_se),
        'adj_mde80_pp': float(mde_adj),
        'hier_boot90_eq_rel_lo_pct': h90_lo,
        'hier_boot90_eq_rel_hi_pct': h90_hi,
    }
    for rp in rel_margins_pct:
        m_rel = (rp / 100.0) * eq_ref_u
        out[f'adj_eq_tost_p_rel{int(rp)}'] = _tost(m_rel)
    for mp in abs_margins_pp:
        out[f'adj_tost_p_{int(mp)}pp'] = _tost(float(mp))
    return out


def compute_ablation_with_campaign_bootstrap(
    cohort_df: pd.DataFrame,
    cluster_df: pd.DataFrame,
    *,
    candidates: Sequence[str],
    reference: str = 'Periodic',
    alpha: float = 0.10,
    n_boot: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    """Compute Proposition 1 single-factor ablation flip rates per predictor with campaign-level bootstrap CIs."""
    cl = cluster_df.copy()
    if 'offers' in cl.columns and 'positive' not in cl.columns:
        cl['positive'] = cl['offers']
    if 'missing_outcomes' in cl.columns and 'unresolved' not in cl.columns:
        cl['unresolved'] = cl['missing_outcomes']

    rows = []
    unit_camp_map = cl[['physical_unit', 'campaign']].drop_duplicates().set_index('physical_unit')['campaign'].to_dict()

    for pred_name, pred_coh in cohort_df.groupby('predictor', sort=False):
        pred_cl = cl[cl['predictor'] == pred_name]
        # Pair candidate rows vs Periodic baseline across cohort x scenario x cap_new
        comp_list = []
        for (coh, scen, cap), grp in pred_coh.groupby(['cohort', 'scenario', 'cap_new'], sort=True):
            if int(cap) == 0:
                continue
            by_pol = grp.set_index('policy')
            if reference not in by_pol.index:
                continue
            r = by_pol.loc[reference]
            for cand in candidates:
                if cand not in by_pol.index:
                    continue
                c = by_pol.loc[cand]
                # Handle zero-offer edge cleanly
                c_pos_hi = float(c['positive_high'])
                r_pos_hi = float(r['positive_high'])
                c_hi = float(c['hi'])
                r_hi = float(r['hi'])
                valid_pos = np.isfinite(c_pos_hi) and np.isfinite(r_pos_hi) and c['positive'] > 0 and r['positive'] > 0
                rank_flip = (
                    ((c_hi < r_hi) and (c_pos_hi > r_pos_hi)) or ((c_hi > r_hi) and (c_pos_hi < r_pos_hi))
                ) if valid_pos else False
                if np.isfinite(c_hi) and np.isfinite(r_hi) and np.isfinite(c_pos_hi) and np.isfinite(r_pos_hi):
                    # Self-level SLA flip vs ceiling alpha when all-issued R <= alpha permits R_+ > alpha
                    cand_sla_flip = (c_hi <= alpha) != (c_pos_hi <= alpha)
                else:
                    cand_sla_flip = False
                q_unmatched = abs(float(c['new_query_attempts']) - float(r['new_query_attempts'])) > 1e-9
                has_unres = (c['unresolved'] + r['unresolved']) > 0 and valid_pos
                overlap = (
                    max(float(c['positive_low']), float(r['positive_low']))
                    <= min(float(c['positive_high']), float(r['positive_high']))
                ) if has_unres else False
                comp_list.append({
                    'campaign': COHORT_TO_CAMPAIGN[coh],
                    'scenario': scen,
                    'sla_flip': bool(cand_sla_flip),
                    'rank_flip': bool(rank_flip),
                    'q_unmatched': bool(q_unmatched),
                    'has_unres': bool(has_unres),
                    'miss_overlap': bool(has_unres and overlap),
                })
        cdf = pd.DataFrame(comp_list)

        # Pooling contrasts across physical units per scenario x cap_new x candidate x scope
        scopes = {
            'Retrospective': RETRO_CAMPAIGNS,
            'HeldOutPublic': HELDOUT_CAMPAIGNS,
            'AllCohorts': ALL_CAMPAIGNS,
        }
        pool_rows = []
        unit_pool_slices = []  # store per-slice per-unit counts for exact campaign-level bootstrap
        for (scen, cap), grp in pred_cl.groupby(['scenario', 'cap_new'], sort=True):
            if int(cap) == 0:
                continue
            per = grp[grp['policy'] == reference].groupby('physical_unit', sort=True)[
                ['positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']
            ].sum()
            for cand in candidates:
                ca = grp[grp['policy'] == cand].groupby('physical_unit', sort=True)[
                    ['positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']
                ].sum()
                common_u = ca.index.intersection(per.index)
                ca_c = ca.loc[common_u]
                per_c = per.loc[common_u]
                camps_u = pd.Series([unit_camp_map[u] for u in common_u], index=common_u)
                rc = (ca_c['violations'] + ca_c['unresolved']) / ca_c['positive'].replace(0, np.nan)
                rr = (per_c['violations'] + per_c['unresolved']) / per_c['positive'].replace(0, np.nan)
                valid_rc = np.isfinite(rc) & np.isfinite(rr)
                unit_pool_slices.append({
                    'scenario': scen,
                    'camps': camps_u.to_numpy(),
                    'ca_v': ca_c['violations'].to_numpy(dtype=float),
                    'ca_m': ca_c['unresolved'].to_numpy(dtype=float),
                    'ca_p': ca_c['positive'].to_numpy(dtype=float),
                    'pr_v': per_c['violations'].to_numpy(dtype=float),
                    'pr_m': per_c['unresolved'].to_numpy(dtype=float),
                    'pr_p': per_c['positive'].to_numpy(dtype=float),
                    'diff_u_r': np.where(valid_rc, (rc - rr).to_numpy(dtype=float), np.nan),
                })
                for sname, s_camps in scopes.items():
                    smask = camps_u.isin(s_camps).to_numpy()
                    if not smask.any():
                        continue
                    cp = ca_c['positive'].to_numpy()[smask].sum()
                    rp = per_c['positive'].to_numpy()[smask].sum()
                    if cp <= 0 or rp <= 0:
                        continue
                    d_pool = (ca_c['violations'].to_numpy()[smask].sum() + ca_c['unresolved'].to_numpy()[smask].sum()) / cp - (
                        per_c['violations'].to_numpy()[smask].sum() + per_c['unresolved'].to_numpy()[smask].sum()
                    ) / rp
                    um = smask & valid_rc.to_numpy()
                    if not um.any():
                        continue
                    d_eq = float(np.mean((rc - rr).to_numpy()[um]))
                    pool_rows.append({
                        'scope': sname,
                        'scenario': scen,
                        'rhi_sign_flip': bool(np.sign(d_pool) != np.sign(d_eq)),
                    })
        pldf = pd.DataFrame(pool_rows)

        # Vectorized campaign-level bootstrap (resampling the k=6 physical campaigns with replacement!)
        for scen_filter in ('All', 'Recorded'):
            c_sub = cdf if scen_filter == 'All' else cdf[cdf['scenario'] == 'Recorded']
            p_sub = pldf if scen_filter == 'All' else pldf[pldf['scenario'] == 'Recorded']
            u_slices = unit_pool_slices if scen_filter == 'All' else [s for s in unit_pool_slices if s['scenario'] == 'Recorded']

            # Pre-aggregate cohort counts per campaign
            c_idx = {cp: c_sub[c_sub['campaign'] == cp] for cp in ALL_CAMPAIGNS}
            rng = np.random.default_rng(seed)
            boot_draws = [rng.choice(ALL_CAMPAIGNS, size=len(ALL_CAMPAIGNS), replace=True) for _ in range(n_boot)]

            # Precompute slice masks by campaign for pooling bootstrap across drawn campaigns
            slice_camp_masks = [
                {cp: (sl['camps'] == cp) for cp in ALL_CAMPAIGNS}
                for sl in u_slices
            ]

            for factor, label, col, mask_col in [
                ('R_vs_Rplus_SLA', 'All-issued R vs Cond R+ (SLA<=10%)', 'sla_flip', None),
                ('R_vs_Rplus_Rank', 'All-issued R vs Cond R+ (Winner)', 'rank_flip', None),
                ('Cap_vs_Qnew_All', 'Nominal Cnew vs Realized Qnew', 'q_unmatched', None),
                ('Missing_Bounds_Overlap', 'Complete R+meas vs Bounds [lo,hi]', 'miss_overlap', 'has_unres'),
            ]:
                base_sub = c_sub[c_sub[mask_col]] if mask_col else c_sub
                n_tot = int(len(base_sub))
                n_aff = int(base_sub[col].sum()) if n_tot > 0 else 0
                pct_obs = 100.0 * (n_aff / n_tot) if n_tot > 0 else float('nan')

                boots = []
                for drawn in boot_draws:
                    num = 0
                    den = 0
                    for cp in drawn:
                        g = c_idx[cp]
                        if mask_col:
                            g = g[g[mask_col]]
                        den += len(g)
                        num += int(g[col].sum())
                    if den > 0:
                        boots.append(100.0 * num / den)
                ci_lo, ci_hi = [float(x) for x in np.percentile(boots, [2.5, 97.5])] if boots else [float('nan'), float('nan')]
                rows.append({
                    'predictor': pred_name,
                    'scenario_filter': scen_filter,
                    'factor': factor,
                    'label': label,
                    'evidence_tier': 'exploratory',
                    'campaigns_k': len(ALL_CAMPAIGNS),
                    'n_total': n_tot,
                    'n_affected': n_aff,
                    'pct_affected': pct_obs,
                    'camp_boot_ci95_lo': ci_lo,
                    'camp_boot_ci95_hi': ci_hi,
                })

            # Pooling sign flip with exact campaign-level bootstrap over AllCohorts + domains represented in draw
            n_ptot = int(len(p_sub))
            n_paff = int(p_sub['rhi_sign_flip'].sum()) if n_ptot > 0 else 0
            pct_pobs = 100.0 * (n_paff / n_ptot) if n_ptot > 0 else float('nan')
            p_boots = []
            for drawn in boot_draws:
                mults = {cp: int(np.sum(drawn == cp)) for cp in ALL_CAMPAIGNS}
                flips = 0
                tot_s = 0
                scope_sets = [('AllCohorts', ALL_CAMPAIGNS)]
                if any(mults[c] > 0 for c in RETRO_CAMPAIGNS):
                    scope_sets.append(('Retrospective', RETRO_CAMPAIGNS))
                if any(mults[c] > 0 for c in HELDOUT_CAMPAIGNS):
                    scope_sets.append(('HeldOutPublic', HELDOUT_CAMPAIGNS))
                for sl, smasks in zip(u_slices, slice_camp_masks):
                    for _, s_camps in scope_sets:
                        cnum = cden = rnum = rden = 0.0
                        eq_vals = []
                        for cp in s_camps:
                            w = mults[cp]
                            if w == 0:
                                continue
                            mk = smasks[cp]
                            if not mk.any():
                                continue
                            cnum += w * float(sl['ca_v'][mk].sum() + sl['ca_m'][mk].sum())
                            cden += w * float(sl['ca_p'][mk].sum())
                            rnum += w * float(sl['pr_v'][mk].sum() + sl['pr_m'][mk].sum())
                            rden += w * float(sl['pr_p'][mk].sum())
                            dv = sl['diff_u_r'][mk]
                            fin = dv[np.isfinite(dv)]
                            if len(fin) > 0:
                                eq_vals.extend([fin] * w)
                        if cden > 0 and rden > 0 and eq_vals:
                            d_p = cnum / cden - rnum / rden
                            d_e = float(np.mean(np.concatenate(eq_vals)))
                            flips += int(np.sign(d_p) != np.sign(d_e))
                            tot_s += 1
                if tot_s > 0:
                    p_boots.append(100.0 * flips / tot_s)
            pci_lo, pci_hi = [float(x) for x in np.percentile(p_boots, [2.5, 97.5])] if p_boots else [float('nan'), float('nan')]
            rows.append({
                'predictor': pred_name,
                'scenario_filter': scen_filter,
                'factor': 'Pooling_Weight_Rplus',
                'label': 'OfferWtd vs EqualUnit Pooling (dR+hi)',
                'evidence_tier': 'exploratory',
                'campaigns_k': len(ALL_CAMPAIGNS),
                'n_total': n_ptot,
                'n_affected': n_paff,
                'pct_affected': pct_pobs,
                'camp_boot_ci95_lo': pci_lo,
                'camp_boot_ci95_hi': pci_hi,
            })
    return pd.DataFrame(rows)


def compute_tost_and_divergence_table(
    cluster_df: pd.DataFrame,
    *,
    candidates: Sequence[str] = ('MARUR', 'PACER', 'ACI_g0.05'),
    reference: str = 'Periodic',
    n_boot: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    """Reuse compare_policies_paired() + Donner G_eff across predictors and adjust all p-values (Holm & BH)."""
    unit_camp_map = cluster_df[['physical_unit', 'campaign']].drop_duplicates().set_index('physical_unit')['campaign'].to_dict()
    rows = []
    scopes = (
        ('Retrospective', ('retrospective',)),
        ('HeldOutPublic', ('heldout_public',)),
        ('AllCohorts', ('retrospective', 'heldout_public')),
    )
    for pred_name, pred_cl in cluster_df.groupby('predictor', sort=False):
        rec_cl = pred_cl[pred_cl['scenario'] == 'Recorded']
        for scope_name, domains in scopes:
            sc_cl = rec_cl[rec_cl['domain'].isin(domains)]
            for cap_new in (10, 40):
                cap_cl = sc_cl[sc_cl['cap_new'] == cap_new]
                # Build audit-compatible normalized ledger over physical_unit clusters
                agg = cap_cl.groupby(['policy', 'physical_unit'], as_index=False)[
                    ['eligible', 'offers', 'violations', 'missing_outcomes', 'queries_charged', 'observed_sum', 'delivered_sum']
                ].sum()
                agg = agg.rename(columns={'physical_unit': 'cluster_id'})
                agg['observed_outcomes'] = agg['offers'] - agg['missing_outcomes']

                ref_idx = agg[agg['policy'] == reference].set_index('cluster_id').sort_index()
                if ref_idx.empty:
                    continue
                for cand in candidates:
                    cand_idx = agg[agg['policy'] == cand].set_index('cluster_id').sort_index()
                    if cand_idx.empty:
                        continue
                    pair = compare_policies_paired(
                        agg,
                        candidate=cand,
                        reference=reference,
                        min_clusters=20,
                        n_boot=n_boot,
                        seed=seed,
                        equiv_margins_pp=(1.0, 2.0),
                        rel_margins_pct=(50.0, 25.0),
                    )
                    don = _donner_campaign_tost(
                        cand_idx, ref_idx, unit_camp_map, rel_margins_pct=(50.0, 25.0), abs_margins_pp=(1.0, 2.0), n_boot=n_boot, seed=seed
                    )
                    rows.append({
                        'predictor': pred_name,
                        'scope': scope_name,
                        'cap_new': int(cap_new),
                        'candidate': cand,
                        'reference': reference,
                        'evidence_tier': 'exploratory',
                        'clusters_g': pair['clusters'],
                        'campaigns_k': don['campaigns'],
                        'g_eff': don['g_eff'],
                        'icc': don['icc'],
                        'deff': don['deff'],
                        'queries_matched': pair['queries_matched'],
                        'q_cand': pair['queries_candidate'],
                        'q_ref': pair['queries_reference'],
                        'ref_equal_u_pp': pair['ref_equal_u_pp'],
                        'eq_du_pp': pair['equal_cluster_du_pp'],
                        'eq_rel_du_pct': pair['equal_cluster_rel_du_pct'],
                        'pool_dpos_hi_pp': pair['pooled_dpos_hi_pp'],
                        'eq_dpos_hi_pp': pair['equal_cluster_dpos_hi_pp'],
                        'pool_vs_eq_rhi_gap_pp': pair['pooled_dpos_hi_pp'] - pair['equal_cluster_dpos_hi_pp'],
                        'pool_rel_du_pct': pair['pooled_rel_du_pct'],
                        'adj_mde80_pp': don['adj_mde80_pp'],
                        'hier_boot90_eq_rel_lo_pct': don['hier_boot90_eq_rel_lo_pct'],
                        'hier_boot90_eq_rel_hi_pct': don['hier_boot90_eq_rel_hi_pct'],
                        'p_eq_rel50': pair['tost_eq_rel_p_values'].get('+-50%', float('nan')),
                        'p_eq_rel25': pair['tost_eq_rel_p_values'].get('+-25%', float('nan')),
                        'p_pool_rel50': pair['tost_pool_rel_p_values'].get('+-50%', float('nan')),
                        'p_abs_1pp': pair['tost_p_values'].get('+-1pp', float('nan')),
                        'p_abs_2pp': pair['tost_p_values'].get('+-2pp', float('nan')),
                        'p_adj_eq_rel50': don['adj_eq_tost_p_rel50'],
                        'p_adj_eq_rel25': don['adj_eq_tost_p_rel25'],
                        'p_adj_2pp': don['adj_tost_p_2pp'],
                    })

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    # Jointly adjust across ALL reported p-values in the exploratory robustness suite (Holm & BH)
    p_cols = ['p_eq_rel50', 'p_eq_rel25', 'p_pool_rel50', 'p_abs_1pp', 'p_abs_2pp', 'p_adj_eq_rel50', 'p_adj_eq_rel25', 'p_adj_2pp']
    flat_p = np.concatenate([out[c].to_numpy(dtype=float) for c in p_cols])
    holm_all, bh_all = adjust_pvalues_holm_bh(flat_p)
    n_rows = len(out)
    for idx, col in enumerate(p_cols):
        out[f'{col}_holm'] = holm_all[idx * n_rows : (idx + 1) * n_rows]
        out[f'{col}_bh'] = bh_all[idx * n_rows : (idx + 1) * n_rows]
    return out


def compute_fairness_sieve_by_predictor(
    cohort_df: pd.DataFrame,
    *,
    candidates: Sequence[str],
    reference: str = 'Periodic',
    sieve_cfg: dict[str, Any],
) -> pd.DataFrame:
    """Apply pre-committed Matched Fairness Sieve (Q_new, |dA| <= 5 pp) identically per predictor."""
    q_tol = float(sieve_cfg['q_match_tol'])
    da_max = float(sieve_cfg['offer_rate_diff_max_pp'])
    dr_max = float(sieve_cfg['win_dpos_hi_max_pp'])
    du_min = float(sieve_cfg['win_du_min_pp'])
    scen = str(sieve_cfg.get('primary_scenario', 'Recorded'))

    rows = []
    rec_df = cohort_df[cohort_df['scenario'] == scen]
    for pred_name, pred_sub in rec_df.groupby('predictor', sort=False):
        total = unfilt_win = q_matched = q_win = qa_matched = qa_win = pacer_qa_win = aci_qa_win = 0
        winners: list[str] = []
        for cap in (10, 40):
            sub_cap = pred_sub[pred_sub['cap_new'] == cap]
            for cohort, grp in sub_cap.groupby('cohort', sort=True):
                by_pol = grp.set_index('policy')
                if reference not in by_pol.index:
                    continue
                r = by_pol.loc[reference]
                for cand in candidates:
                    if cand not in by_pol.index:
                        continue
                    c = by_pol.loc[cand]
                    total += 1
                    q_ok = abs(float(c['new_query_attempts']) - float(r['new_query_attempts'])) <= q_tol
                    a_ok = abs(100.0 * (float(c['positive_rate']) - float(r['positive_rate']))) <= da_max
                    rhi_diff = 100.0 * (float(c['positive_high']) - float(r['positive_high']))
                    du_pp = 100.0 * (float(c['u']) - float(r['u']))
                    win = bool(np.isfinite(rhi_diff) and np.isfinite(du_pp) and (rhi_diff < dr_max) and (du_pp >= du_min))
                    if win:
                        unfilt_win += 1
                    if q_ok:
                        q_matched += 1
                        if win:
                            q_win += 1
                        if a_ok:
                            qa_matched += 1
                            if win:
                                qa_win += 1
                                winners.append(f'{cohort}:{cand}(C={cap})')
                                if cand == 'PACER':
                                    pacer_qa_win += 1
                                if cand.startswith('ACI'):
                                    aci_qa_win += 1
        rows.append({
            'predictor': pred_name,
            'evidence_tier': 'exploratory',
            'scenario': scen,
            'total_contrasts': total,
            'unfiltered_wins': unfilt_win,
            'q_matched': q_matched,
            'q_matched_wins': q_win,
            'qa_matched': qa_matched,
            'qa_matched_wins': qa_win,
            'fair_win_rate_pct': 100.0 * qa_win / qa_matched if qa_matched > 0 else float('nan'),
            'net_all_win_rate_pct': 100.0 * qa_win / total if total > 0 else float('nan'),
            'pacer_fair_wins': pacer_qa_win,
            'aci_fair_wins': aci_qa_win,
            'winning_pairs': '; '.join(winners),
        })
    return pd.DataFrame(rows)
