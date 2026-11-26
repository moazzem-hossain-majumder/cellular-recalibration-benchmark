"""Machine-readable table specifications shared by the manuscript builders."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METHODS = ['Uncalibrated', 'Global_Conformal', 'RAT_Grouped', 'Proposed_Missingness_Aware']
BUDGETS = (0, 1, 2, 5, 8, 9, 10, 15)


def read_json(path):
    return json.loads(path.read_text(encoding='utf8'))


def _main_tables(root: Path) -> dict:
    """Build main-manuscript tables strictly matching appearance order (Table II..VIII)."""
    mcfg = read_json(root / 'configs/marur.json')
    rbcfg = read_json(root / 'configs/marur_reviewer_baselines.json')
    pcfg = read_json(root / 'configs/pacer.json')
    caps_str = '/'.join(str(c) for c in rbcfg['new_query_caps'])
    seeds_str = ','.join(str(s) for s in rbcfg['random_schedule_seeds'])

    # Table II: Evaluated policies and protocols
    baseline_rows = [
        ['Frozen', 'None (C=0)', 'Static Init10', f'init={mcfg["initial_labels"]}', 'None', 'Zero-cost anchor'],
        ['Early', 'Every elig tick', f'FIFO W={mcfg["window"]}', f'C={caps_str}', 'Insert score=p', 'Day-1 exhaust'],
        ['Random', 'Uniform seed', f'FIFO W={mcfg["window"]}', f'seeds={seeds_str}', 'Insert score=p', 'Nonadaptive'],
        ['Periodic', f'Every P={mcfg["period_ticks"]} ticks', f'FIFO W={mcfg["window"]}', f'P={mcfg["period_ticks"]}, W={mcfg["window"]}', 'Insert score=p', 'Fixed cadence'],
        ['ACI', f'Every P={mcfg["period_ticks"]} ticks', 'Online level a', f'eta={mcfg["aci_step"]}, W={mcfg["window"]}', 'err=1 on pos', 'Sparse ACI'],
        ['DecayingOGD', f'Every P={mcfg["period_ticks"]} ticks', 'Decaying step', f'exp={rbcfg["decaying_ogd_exponent"]}', 'score=p on miss', 'Decaying OGD'],
        ['MARUR', f'Age {mcfg["max_age_minutes"]}m or RAT', f'Pat/Pool W={mcfg["window"]}', f'age={mcfg["max_age_minutes"]}m, min={mcfg["minimum_pattern_support"]}', 'Insert p + gate', 'Heuristic'],
        ['MARUR ablat.', 'Age or Periodic', 'Pool/DropMiss', 'NoPat/NoGate/Drop', 'Drop or Periodic', 'Gate/miss check'],
        ['PACER', 'Uniform K blk', f'Smooth sel W={pcfg["pacer_obs_window"]}', f'g={pcfg["pacer_gamma"]}, v={pcfg["pacer_veto"]}', 'Excl W; e=1', 'Paced comparator'],
    ]

    # Table III: Physical campaign-date paired cluster inference (G=16)
    cluster_rows = []
    cluster_df = pd.read_csv(root / 'results/diagnostics/trip_level_inference.csv')
    c_slice = cluster_df[
        (cluster_df.model == 'HistGBM')
        & (cluster_df.scenario == 'Recorded')
        & (cluster_df.new_query_cap == 10)
        & (cluster_df.baseline == 'Periodic')
    ]
    order = ['E1', 'E3', 'AT&T', 'T-Mobile', 'Verizon', 'Ireland', 'Combined_CampaignDates', 'Ireland_Traces']
    c_map = {r.scope: r for r in c_slice.itertuples()}
    labels = {'AT&T': 'ATT', 'Combined_CampaignDates': 'All (16 Dates)', 'Ireland_Traces': 'Ireland (Traces)'}
    for key in order:
        r = c_map[key]
        label = labels.get(key, key)
        cluster_rows.append([
            label,
            str(int(r.clusters)),
            f'{int(r.cand_query_days)}/{int(r.base_query_days)}',
            f'{int(r.cand_pos_days)}/{int(r.base_pos_days)}',
            f'{100 * r.pool_du:+.2f}',
            f'{100 * r.boot_du_lo:+.2f}',
            f'{100 * r.boot_du_hi:+.2f}',
            f'{100 * r.eq_du_mean:+.2f}',
            f'{100 * r.t_du_lo:+.2f}',
            f'{100 * r.t_du_hi:+.2f}',
            f'{100 * r.pool_dhi:+.2f}',
        ])

    # Table IV: Separated Estimands - Equal-cluster (EqualCl) vs Pooled-ratio (PoolRat) Relative & Absolute TOST
    pow_df = pd.read_csv(root / 'results/exploratory/sensitivity/power_equivalence.csv')
    scope_short = {'Retrospective': 'Retro', 'HeldOut': 'HeldOut', 'AllCohorts': 'AllCoh'}
    cand_short = {'MARUR': 'MAR', 'PACER': 'PAC'}
    pow_rows = []
    for sc, cap, cand in [
        ('Retrospective', 10, 'MARUR'),
        ('Retrospective', 10, 'PACER'),
        ('HeldOut', 10, 'MARUR'),
        ('HeldOut', 10, 'PACER'),
        ('HeldOut', 40, 'PACER'),
        ('AllCohorts', 40, 'PACER'),
    ]:
        r = pow_df[(pow_df['scope'] == sc) & (pow_df['cap_new'] == cap) & (pow_df['candidate'] == cand)].iloc[0]
        pow_rows.append([
            scope_short[sc],
            cand_short[cand],
            str(int(r.cap_new)),
            'EqualCl',
            str(int(r.clusters)),
            str(int(r.zero_ref_u_clusters)),
            f'{r.eq_ref_u_pp:.2f}',
            f'{r.eq_du_mean_pp:+.2f}',
            f'{r.eq_rel_du_pct:+.1f}',
            f'MDE {r.mde80_pp:.2f}',
            f'{r.eq_tost_p_rel50:.4f}',
            f'{r.eq_tost_p_rel25:.4f}',
            f'{r.tost_p_1pp:.4f}',
            f'{r.tost_p_2pp:.4f}',
        ])
        pow_rows.append([
            scope_short[sc],
            cand_short[cand],
            str(int(r.cap_new)),
            'PoolRat',
            str(int(r.clusters)),
            str(int(r.zero_ref_u_clusters)),
            f'{r.pool_ref_u_pp:.2f}',
            f'{r.pool_du_pp:+.2f}',
            f'{r.pool_rel_du_pct:+.1f}',
            f'{r.pool_boot_rel90_lo_pct:+.1f} to {r.pool_boot_rel90_hi_pct:+.1f}',
            f'{r.pool_tost_p_rel50:.4f}',
            f'{r.pool_tost_p_rel25:.4f}',
            'NA',
            'NA',
        ])

    # Table V: Per-cohort and per-cap breakdown across held-out public archives & retro mean
    ps = pd.read_csv(root / 'results/pacer/pacer_summary.csv')
    psd = pd.read_csv(root / 'results/pacer/pacer_seed_sensitivity.csv')
    psm = (
        psd.groupby(['domain', 'cohort', 'model', 'cap_new'], as_index=False)['selective_excess_upper']
        .mean()
        .rename(columns={'selective_excess_upper': 'mean_excess'})
    )
    psub = ps[
        (ps['model'] == 'HistGBM')
        & (ps['scenario'] == 'Recorded')
        & (ps['cap_new'].isin([10, 40]))
        & (ps['policy'].isin(['Periodic', 'MARUR', 'PACER']))
    ]
    pacer_rows = []
    for cohort, label in [
        ('Ireland_Static', 'Ireland Static (4d)'),
        ('Oslo_Commute', 'Oslo Commute (7d)'),
        ('Rome_Capacity_Op1', 'Rome Cap Op1 (15d)'),
        ('Rome_Capacity_Op2', 'Rome Cap Op2 (15d)'),
    ]:
        for cap in (10, 40):
            blk = psub[(psub['cohort'] == cohort) & (psub['cap_new'] == cap)].set_index('policy')
            mx = float(psm[(psm['cohort'] == cohort) & (psm['model'] == 'HistGBM') & (psm['cap_new'] == cap)]['mean_excess'].iloc[0])
            pacer_rows.append([
                label, str(cap),
                f"{100 * blk.loc['Periodic', 'positive_high']:.2f}",
                f"{100 * blk.loc['MARUR', 'positive_high']:.2f}",
                f"{100 * blk.loc['PACER', 'positive_high']:.2f}",
                f"{100 * blk.loc['Periodic', 'u']:.2f}",
                f"{100 * blk.loc['MARUR', 'u']:.2f}",
                f"{100 * blk.loc['PACER', 'u']:.2f}",
                f"{100 * blk.loc['PACER', 'positive_rate']:.1f}",
                f"{mx:.3f}",
                f"{blk.loc['PACER', 'theorem1_bound']:.3f}",
            ])
    for cap in (10, 40):
        blk = psub[(psub['domain'] == 'retrospective') & (psub['cap_new'] == cap)].groupby('policy')[['positive_high', 'u', 'positive_rate', 'theorem1_bound']].mean()
        mx = float(psm[(psm['domain'] == 'retrospective') & (psm['model'] == 'HistGBM') & (psm['cap_new'] == cap)]['mean_excess'].mean())
        pacer_rows.append([
            'Retro Mean (6 coh.)', str(cap),
            f"{100 * blk.loc['Periodic', 'positive_high']:.2f}",
            f"{100 * blk.loc['MARUR', 'positive_high']:.2f}",
            f"{100 * blk.loc['PACER', 'positive_high']:.2f}",
            f"{100 * blk.loc['Periodic', 'u']:.2f}",
            f"{100 * blk.loc['MARUR', 'u']:.2f}",
            f"{100 * blk.loc['PACER', 'u']:.2f}",
            f"{100 * blk.loc['PACER', 'positive_rate']:.1f}",
            f"{mx:.3f}",
            f"{blk.loc['PACER', 'theorem1_bound']:.3f}",
        ])

    # Table VI: Pooling-rule decomposition (compact main summary; full 18 rows in Supplement Table S16)
    cl = pd.read_csv(root / 'results/pacer/pacer_cluster_dates.csv')
    con = pd.read_csv(root / 'results/pacer/pacer_paired_contrasts.csv')
    pool_all_rows = []
    for scope_lbl, con_scope, doms in [
        ('HeldOut', 'HeldOutPublic', ['heldout_public']),
        ('Retrospective', 'Retrospective', ['retrospective']),
        ('AllCohorts', 'AllCohortsPooled', ['heldout_public', 'retrospective']),
    ]:
        for cap in (10, 40):
            ow = con[
                (con['scope'] == con_scope)
                & (con['model'] == 'HistGBM')
                & (con['scenario'] == 'Recorded')
                & (con['cap_new'] == cap)
                & (con['reference'] == 'Periodic')
            ].iloc[0]
            pool_all_rows.append([
                scope_lbl, str(cap), 'OfferWtd', str(int(ow.clusters)),
                f'{100 * ow.pool_dpos_hi:+.2f}',
                f'{100 * ow.boot_dpos_hi_lo:+.2f} to {100 * ow.boot_dpos_hi_hi:+.2f}',
                f'{100 * ow.pool_du:+.2f}',
            ])
            sub = cl[
                (cl['domain'].isin(doms))
                & (cl['model'] == 'HistGBM')
                & (cl['scenario'] == 'Recorded')
                & (cl['cap_new'] == cap)
                & (cl['policy'].isin(['PACER', 'Periodic']))
            ]
            g = sub.groupby(['unit', 'policy'])[['positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']].sum().reset_index()
            g['pos_hi'] = (g['violations'] + g['unresolved']) / g['positive'].replace(0, np.nan)
            g['u'] = g['delivered_sum'] / g['observed_sum'].replace(0, np.nan)
            piv_hi = g.pivot(index='unit', columns='policy', values='pos_hi')
            piv_u = g.pivot(index='unit', columns='policy', values='u')
            d_hi = (piv_hi['PACER'] - piv_hi['Periodic']).dropna()
            d_u = (piv_u['PACER'] - piv_u['Periodic']).dropna()
            cs = ps[
                (ps['domain'].isin(doms))
                & (ps['model'] == 'HistGBM')
                & (ps['scenario'] == 'Recorded')
                & (ps['cap_new'] == cap)
                & (ps['policy'].isin(['PACER', 'Periodic']))
            ]
            cpiv_hi = cs.pivot(index='cohort', columns='policy', values='positive_high')
            cpiv_u = cs.pivot(index='cohort', columns='policy', values='u')
            pool_all_rows.append([
                scope_lbl, str(cap), 'EqualUnit', f'{len(d_hi)}/{len(piv_hi)}',
                f'{100 * d_hi.mean():+.2f}', 'paired valid', f'{100 * d_u.mean():+.2f}',
            ])
            pool_all_rows.append([
                scope_lbl, str(cap), 'EqualCohort', f'{len(cpiv_hi)} coh',
                f'{100 * (cpiv_hi["PACER"] - cpiv_hi["Periodic"]).mean():+.2f}', 'unweighted',
                f'{100 * (cpiv_u["PACER"] - cpiv_u["Periodic"]).mean():+.2f}',
            ])
    # Main Table VI keeps the 9 core contrast rows (HeldOut C=10/40 + AllCohorts C=10 OfferWtd/EqualUnit/EqualCohort; full 18 rows in S16)
    main_pool_rows = [r for r in pool_all_rows if r[0] == 'HeldOut' or (r[0] == 'AllCohorts' and r[1] == '40') or (r[0] == 'AllCohorts' and r[2] == 'OfferWtd')][:9]
    main_pool_rows = [
        r for r in pool_all_rows
        if (r[0] == 'HeldOut') or (r[0] == 'AllCohorts' and r[2] in {'OfferWtd', 'EqualUnit'})
    ][:10]

    # Table VII: Conditional-risk ceilings vs observed risk and non-deployment rules
    p40 = ps[(ps['model'] == 'HistGBM') & (ps['scenario'] == 'Recorded') & (ps['cap_new'] == 40) & (ps['policy'] == 'PACER')]
    p10 = ps[(ps['model'] == 'HistGBM') & (ps['scenario'] == 'Recorded') & (ps['cap_new'] == 10) & (ps['policy'] == 'PACER')]
    b10_mean = float(p10['theorem1_bound'].mean())
    b40_mean = float(p40['theorem1_bound'].mean())

    def _ceil_row(label, lo, hi, a_ref, cohorts_lbl, rule):
        sub = p40[(p40['positive_rate'] >= lo) & (p40['positive_rate'] < hi)]
        c10 = min(1.0, pcfg['alpha'] + b10_mean / a_ref)
        c40 = min(1.0, pcfg['alpha'] + b40_mean / a_ref)
        rng = f'{100 * sub["positive_high"].min():.2f}-{100 * sub["positive_high"].max():.2f}' if len(sub) > 1 else f'{100 * sub["positive_high"].iloc[0]:.2f}'
        return [label, f'{a_ref:.2f}', f'{100 * c10:.1f}', f'{100 * c40:.1f}', rng, cohorts_lbl, rule]

    pers40 = con[
        (con['scope'] == 'AllCohortsPooled')
        & (con['model'] == 'Persistence')
        & (con['scenario'] == 'Recorded')
        & (con['cap_new'] == 40)
        & (con['reference'] == 'Frozen')
    ].iloc[0]
    ceiling_rows = [
        _ceil_row('A below 0.15', 0.0, 0.15, 0.10, 'E1,E3,ATT,Ver,Rome1/2', 'DO NOT DEPLOY'),
        _ceil_row('A 0.15 to 0.30', 0.15, 0.30, 0.22, 'T-Mobile, Ireland', 'DO NOT DEPLOY (SLA)'),
        _ceil_row('A 0.30 to 0.70', 0.30, 0.70, 0.50, 'Oslo Commute', 'Advisory Only'),
        _ceil_row('A 0.70 or more', 0.70, 1.01, 0.85, 'Ireland Static', 'Usable Target'),
        ['Persistence Lag', 'All', 'T1 0.714', 'T1 0.192', f'{100 * pers40.pool_du:+.2f}pp U vs Frz', 'All 10 cohorts (42u)', 'DO NOT DEPLOY'],
    ]

    # Table VIII: Compact exploratory summary (Task 3: MARUR & PACER across Retro & HeldOut + LOCO min-max)
    wa_cl = pd.read_csv(root / 'results/exploratory/sensitivity/window_alpha_clusters.csv')
    pr_cl = pd.read_csv(root / 'results/exploratory/sensitivity/predictor_sensitivity_clusters.csv')
    loco_df = pd.read_csv(root / 'results/exploratory/sensitivity/leave_one_cohort_out.csv')
    sens_rows = []
    for sc_lbl, sc_key in [('Retro16', 'retrospective'), ('HeldOut26', 'heldout_exploratory')]:
        for cand in ('MARUR', 'PACER'):
            for al, win, cap in [(0.05, 40, 40), (0.10, 20, 40), (0.20, 20, 40)]:
                r = wa_cl[
                    (wa_cl['scope'] == sc_key)
                    & (wa_cl['alpha'] == al)
                    & (wa_cl['window'] == win)
                    & (wa_cl['model'] == 'HistGBM')
                    & (wa_cl['cap_new'] == cap)
                    & (wa_cl['candidate'] == cand)
                ].iloc[0]
                sens_rows.append([
                    f'{sc_lbl} W/a', cand, f'a={al:.2f},W={win}', str(cap),
                    f'{100 * r.cand_pos_hi:.2f}', f'{100 * r.ref_pos_hi:.2f}',
                    f'{100 * r.cand_u:.2f}', f'{100 * r.eq_du_mean:+.2f}',
                    f'{100 * r.t_du_lo:+.2f} to {100 * r.t_du_hi:+.2f}',
                ])
    for dom_lbl, dom_key, pnames in [
        ('Retro16 Pred', 'retrospective', ['ThroughputResNet_57', 'QuantileGBM_p10_57', 'HistGBM_Clock112', 'Persistence']),
        ('HeldOut Pred', 'heldout_rome_ireland', ['ThroughputResNet_57', 'QuantileGBM_p10_57', 'Persistence']),
    ]:
        short_pred = {
            'ThroughputResNet_57': 'ResNet57',
            'QuantileGBM_p10_57': 'QGBM10',
            'HistGBM_Clock112': 'ClkGBM112',
            'Persistence': 'Persist',
        }
        for pname in pnames:
            for cand in ('MARUR', 'PACER'):
                cap = 40 if pname in ('ThroughputResNet_57', 'HistGBM_Clock112') else 10
                r = pr_cl[
                    (pr_cl['domain'] == dom_key)
                    & (pr_cl['predictor'] == pname)
                    & (pr_cl['cap_new'] == cap)
                    & (pr_cl['candidate'] == cand)
                ].iloc[0]
                sens_rows.append([
                    dom_lbl, cand, short_pred[pname], str(cap),
                    f'{100 * r.cand_pos_hi:.2f}', f'{100 * r.ref_pos_hi:.2f}',
                    f'{100 * r.cand_u:.2f}', f'{100 * r.eq_du_mean:+.2f}',
                    f'{100 * r.t_du_lo:+.2f} to {100 * r.t_du_hi:+.2f}',
                ])
    # Add compact 1-row Leave-One-Cohort-Out & 1-row Leave-One-Campaign-Out invariant summaries (excluding full row)
    loco_drops = loco_df[loco_df['dropped_cohort'] != 'None']
    sens_rows.append([
        'LOCO (10 cohorts)', 'MAR/PAC', 'Drop any 1/10', '10',
        f'{loco_drops["mobile_r_pos_hi_med_pp"].min():.1f}-{loco_drops["mobile_r_pos_hi_med_pp"].max():.1f}',
        '47.1 full',
        f'{loco_drops["u_med_pp"].min():.2f}-{loco_drops["u_med_pp"].max():.2f}',
        f'{loco_drops["eq_du_pacer_c10_pp"].min():+.2f} to {loco_drops["eq_du_pacer_c10_pp"].max():+.2f}',
        'p95 G=35..42',
    ])
    locampo_df = pd.read_csv(root / 'results/exploratory/sensitivity/leave_one_campaign_out.csv', keep_default_na=False)
    locampo_drops = locampo_df[locampo_df['dropped_campaign'] != 'None']
    sens_rows.append([
        'LOCampO (6 camp)', 'MAR/PAC', 'Drop any 1/6', '10',
        f'{locampo_drops["mobile_r_pos_hi_med_pp"].min():.1f}-{locampo_drops["mobile_r_pos_hi_med_pp"].max():.1f}',
        '47.6 full',
        f'{locampo_drops["u_med_pp"].min():.2f}-{locampo_drops["u_med_pp"].max():.2f}',
        f'{locampo_drops["eq_du_pacer_c10_pp"].min():+.2f} to {locampo_drops["eq_du_pacer_c10_pp"].max():+.2f}',
        'p95 G=27..39',
    ])

    return {
        'table_m2_baselines': (
            'Evaluated controller and comparator rules generated from frozen repository configurations.',
            ['Policy', 'Trigger', 'Calibration', 'KeyParams', 'MissingRule', 'Rationale'],
            baseline_rows,
        ),
        'table_m3_cluster_inference': (
            'Physical campaign-date accounting and paired MARUR minus Periodic contrasts at matched ten new queries (HistGBM, recorded feedback). G counts collection dates (or 11 Irish traces; All pools co-located carriers onto 16 physical dates). Boot and t intervals span 95 percent.',
            ['Scope', 'G', 'QDays', 'PosDays', 'Pool dU', 'BootLo', 'BootHi', 'Eq dU', 'tLo', 'tHi', 'dRhi'],
            cluster_rows,
        ),
        'table_m4_power_equivalence': (
            'Estimand-matched exploratory relative (+-50 percent coarse screening primary, +-25 percent sensitivity) and absolute (+-1.0 / +-2.0 pp) TOST checks (HistGBM, recorded; three physical campaigns in Retro and HeldOut, six total). EqualCl tests equal-cluster mean dU against +-50/25 percent of equal-cluster Periodic U (zero-U clusters Z0 retained; 0 undefined excluded); PoolRat tests pooled ratio against +-50/25 percent via 90 percent cluster bootstrap CIs.',
            ['Scope', 'Cand', 'Cap', 'Estimand', 'G', 'Z0', 'RefU', 'Delta', 'RelPct', 'SpreadOrMDE', 'pRel50', 'pRel25', 'pAbs1', 'pAbs2'],
            pow_rows,
        ),
        'table_m5_pacer_breakdown': (
            'Per-cohort and per-cap comparator results across held-out public archives (26 campaign-dates) and retrospective mean (16 campaign-dates) under frozen HistGBM and recorded feedback. Per, MAR, and PAC denote Periodic, MARUR, and PACER; Exc is 3-seed mean excess vs Theorem 1 bound Bnd.',
            ['Cohort', 'Cap', 'PerHi', 'MARHi', 'PACHi', 'PerU', 'MARU', 'PACU', 'PACA', 'Exc', 'Bnd'],
            pacer_rows,
        ),
        'table_m6_pooling_rules': (
            'Pooling-rule sensitivity for PACER minus Periodic contrasts across held-out (26 dates) and combined (42 dates) clusters (HistGBM, recorded, percentage points; full 18-row table in Supplement Table S16).',
            ['Scope', 'Cap', 'WeightRule', 'Units', 'dPosHi', 'Boot95', 'dU'],
            main_pool_rows,
        ),
        'table_m7_risk_ceilings': (
            'Theoretical Theorem 1 conditional-risk ceilings min(1, alpha + Bnd / RefA) versus empirical PACER HistGBM cap-40 upper risk (percent unless noted) and operational deployment rules.',
            ['OfferStratum', 'RefA', 'CeilC10', 'CeilC40', 'EmpPosHiC40', 'EmpCohortsC40', 'PolicyRule'],
            ceiling_rows,
        ),
        'table_m8_sensitivity': (
            'Extended exploratory sensitivity (MARUR and PACER vs Periodic) across window/alpha, source-only predictors on retrospective (16 dates) and held-out Rome/Ireland Static (19u) archives, plus leave-one-cohort-out (LOCO) and 6-campaign leave-one-campaign-out (LOCampO) median ranges.',
            ['Axis', 'Policy', 'Setting', 'Cap', 'CandHi', 'PerHi', 'CandU', 'Eq dU', 'tCI95'],
            sens_rows,
        ),
    }


def _supp_extra_tables(root: Path) -> dict:
    pacer_df = pd.read_csv(root / 'results/pacer/pacer_summary.csv')
    con_df = pd.read_csv(root / 'results/pacer/pacer_paired_contrasts.csv')
    cl = pd.read_csv(root / 'results/pacer/pacer_cluster_dates.csv')

    # S14: Moved from main paper - cap=40 six-cohort breakdown
    controller = pd.read_csv(root / 'results/marur/summary.csv')
    chosen = controller[
        (controller.model == 'HistGBM')
        & (controller.scenario == 'Recorded')
        & (controller.budget == 50)
        & controller.policy.isin(['Frozen', 'Periodic', 'MARUR'])
    ]
    controller_rows = [
        ['ATT' if r.cohort == 'AT&T' else r.cohort, r.policy, str(r.new_query_attempts), str(r.positive),
         f'{100 * r.positive_low:.2f}', f'{100 * r.positive_high:.2f}', f'{100 * r.u:.3f}']
        for r in chosen.itertuples()
    ]

    # S15: Operational comparator taxonomy (MARUR vs PACER)
    retro40 = pacer_df[(pacer_df['domain'] == 'retrospective') & (pacer_df['model'] == 'HistGBM') & (pacer_df['scenario'] == 'Recorded') & (pacer_df['cap_new'] == 40)].groupby('policy')[['positive_high', 'u']].mean()
    unt10 = con_df[(con_df['scope'] == 'HeldOutPublic') & (con_df['model'] == 'HistGBM') & (con_df['scenario'] == 'Recorded') & (con_df['cap_new'] == 10) & (con_df['reference'] == 'Periodic')].iloc[0]
    pers40 = con_df[(con_df['scope'] == 'AllCohortsPooled') & (con_df['model'] == 'Persistence') & (con_df['scenario'] == 'Recorded') & (con_df['cap_new'] == 40) & (con_df['reference'] == 'Frozen')].iloc[0]
    taxonomy_rows = [
        ['Static high offer (A at least 0.50)', 'PACER', 'T1 O(1/K)', '5.12-6.98 PosHi IrelandSt', 'Needs horizon length T'],
        ['Budget-starved multi-day (C=10)', 'PACER', 'T2 Wmax blk', f'{100 * unt10.pool_dpos_hi:+.2f}pp OfferWtd vs Per', 'Driven by Oslo offers'],
        ['Short rapid shift (C=40, T 300)', 'MARUR', 'Heuristic W=10', 'Forgets init faster on Op1', 'Day-1 churn; miss freeze'],
        ['Stationary / Retro C=40', 'Periodic', 'Fixed cadence', f'{100 * retro40.loc["Periodic", "positive_high"]:.2f} vs PAC {100 * retro40.loc["PACER", "positive_high"]:.2f} PosHi', 'Day-1 blind when P x C low'],
        ['Low A or uncalibrated Persist', 'Halt/Refuse', 'Fail safe', f'Avoids {100 * pers40.pool_du:+.2f}pp U drop', 'No SLA rate valid'],
    ]

    # S16: Full 18-row Pooling-Rule Matrix
    pool_rows = []
    for scope_lbl, con_scope, doms in [
        ('HeldOut', 'HeldOutPublic', ['heldout_public']),
        ('Retrospective', 'Retrospective', ['retrospective']),
        ('AllCohorts', 'AllCohortsPooled', ['heldout_public', 'retrospective']),
    ]:
        for cap in (10, 40):
            ow = con_df[(con_df['scope'] == con_scope) & (con_df['model'] == 'HistGBM') & (con_df['scenario'] == 'Recorded') & (con_df['cap_new'] == cap) & (con_df['reference'] == 'Periodic')].iloc[0]
            pool_rows.append([scope_lbl, str(cap), 'OfferWtd', str(int(ow.clusters)), f'{100 * ow.pool_dpos_hi:+.2f}', f'{100 * ow.boot_dpos_hi_lo:+.2f} to {100 * ow.boot_dpos_hi_hi:+.2f}', f'{100 * ow.pool_du:+.2f}'])
            sub = cl[(cl['domain'].isin(doms)) & (cl['model'] == 'HistGBM') & (cl['scenario'] == 'Recorded') & (cl['cap_new'] == cap) & (cl['policy'].isin(['PACER', 'Periodic']))]
            g = sub.groupby(['unit', 'policy'])[['positive', 'violations', 'unresolved', 'observed_sum', 'delivered_sum']].sum().reset_index()
            g['pos_hi'] = (g['violations'] + g['unresolved']) / g['positive'].replace(0, np.nan)
            g['u'] = g['delivered_sum'] / g['observed_sum'].replace(0, np.nan)
            piv_hi = g.pivot(index='unit', columns='policy', values='pos_hi')
            piv_u = g.pivot(index='unit', columns='policy', values='u')
            d_hi = (piv_hi['PACER'] - piv_hi['Periodic']).dropna()
            d_u = (piv_u['PACER'] - piv_u['Periodic']).dropna()
            cs = pacer_df[(pacer_df['domain'].isin(doms)) & (pacer_df['model'] == 'HistGBM') & (pacer_df['scenario'] == 'Recorded') & (pacer_df['cap_new'] == cap) & (pacer_df['policy'].isin(['PACER', 'Periodic']))]
            cpiv_hi = cs.pivot(index='cohort', columns='policy', values='positive_high')
            cpiv_u = cs.pivot(index='cohort', columns='policy', values='u')
            pool_rows.append([scope_lbl, str(cap), 'EqualUnit', f'{len(d_hi)}/{len(piv_hi)}', f'{100 * d_hi.mean():+.2f}', 'paired valid', f'{100 * d_u.mean():+.2f}'])
            pool_rows.append([scope_lbl, str(cap), 'EqualCohort', f'{len(cpiv_hi)} coh', f'{100 * (cpiv_hi["PACER"] - cpiv_hi["Periodic"]).mean():+.2f}', 'unweighted', f'{100 * (cpiv_u["PACER"] - cpiv_u["Periodic"]).mean():+.2f}'])

    # S17: Full 11-row Leave-One-Cohort-Out Audit
    loco_df = pd.read_csv(root / 'results/exploratory/sensitivity/leave_one_cohort_out.csv', keep_default_na=False)
    loco_rows = []
    for r in loco_df.itertuples():
        lbl = 'ATT' if r.dropped_cohort == 'AT&T' else str(r.dropped_cohort).replace('_', ' ')
        loco_rows.append([
            lbl, str(int(r.clusters_g)),
            f'{r.mobile_r_pos_hi_min_pp:.1f}-{r.mobile_r_pos_hi_max_pp:.1f}',
            f'{r.mobile_r_pos_hi_med_pp:.1f}',
            f'{r.u_med_pp:.2f}',
            f'{r.eq_du_marur_c10_pp:+.2f}',
            f'{r.eq_du_pacer_c10_pp:+.2f}',
            f'{r.eq_du_pacer_c40_pp:+.2f}',
        ])

    # S18: Exploratory campaign-level dependence sensitivity (adjusted relative & absolute TOST + hierarchical bootstrap)
    camp_df = pd.read_csv(root / 'results/exploratory/sensitivity/campaign_dependence.csv')
    scope_short = {'Retrospective': 'Retro', 'HeldOut': 'HeldOut', 'AllCohorts': 'AllCoh'}
    cand_short = {'MARUR': 'MAR', 'PACER': 'PAC'}
    camp_rows = []
    for r in camp_df.itertuples():
        camp_rows.append([
            scope_short[r.scope],
            cand_short[r.candidate],
            str(int(r.cap_new)),
            str(int(r.clusters)),
            str(int(r.campaigns)),
            f'{r.icc:.2f}',
            f'{r.deff:.2f}',
            f'{r.g_eff:.2f}',
            f'{r.naive_eq_tost_p_rel50:.4f}',
            f'{r.adj_eq_tost_p_rel50:.4f}',
            f'{r.adj_eq_tost_p_rel25:.4f}',
            f'{r.adj_tost_p_2pp:.4f}',
            f'{r.adj_mde80_pp:.2f}',
            f'{r.hier_boot90_eq_rel_lo_pct:+.1f} to {r.hier_boot90_eq_rel_hi_pct:+.1f}',
        ])

    # S19: Full 7-row Leave-One-Campaign-Out Audit + Per-Campaign Medians (6 physical campaigns)
    locampo_df = pd.read_csv(root / 'results/exploratory/sensitivity/leave_one_campaign_out.csv', keep_default_na=False)
    locampo_rows = []
    for r in locampo_df.itertuples():
        locampo_rows.append([
            str(r.dropped_campaign).replace('_', ' '),
            str(int(r.remaining_campaigns)),
            str(int(r.clusters_g)),
            f'{r.camp_r_pos_hi_med_pp:.1f}',
            f'{r.camp_u_med_pp:.2f}',
            f'{r.mobile_r_pos_hi_med_pp:.1f}',
            f'{r.u_med_pp:.2f}',
            f'{r.eq_du_pacer_c10_pp:+.2f}',
            f'{r.eq_du_pacer_c40_pp:+.2f}',
        ])

    return {
        'table_s14_marur_audit': (
            'Retrospective six-cohort controllers at new-query cap 40 under frozen HistGBM and recorded feedback (with ten initial successful labels).',
            ['Cohort', 'Policy', 'Queries', 'Offers', 'PosLow', 'PosHigh', 'U'],
            controller_rows,
        ),
        'table_s15_marur_vs_pacer': (
            'Operational comparator taxonomy across regimes, assumptions, and primary failure modes (rates and differences in percent / percentage points).',
            ['Regime', 'Method', 'Property', 'ObservedMetric', 'PrimaryFailure'],
            taxonomy_rows,
        ),
        'table_s16_pooling_full': (
            'Complete 18-row pooling-rule sensitivity for PACER minus Periodic contrasts across HeldOut, Retrospective, and AllCohorts (HistGBM, recorded, percentage points).',
            ['Scope', 'Cap', 'WeightRule', 'Units', 'dPosHi', 'Boot95', 'dU'],
            pool_rows,
        ),
        'table_s17_loco': (
            'Leave-one-cohort-out check across all 10 cohorts (42 total clusters, HistGBM, recorded feedback). Mobile risk range excludes static Ireland; U is median supported throughput.',
            ['Dropped', 'G', 'MobRhiRng', 'MobRhiMed', 'UMed', 'EqdU MAR10', 'EqdU PAC10', 'EqdU PAC40'],
            loco_rows,
        ),
        'table_s18_campaign_dependence': (
            'Exploratory campaign-level dependence sensitivity across physical geographic campaigns (Camp=3 Retrospective, 3 HeldOut, 6 AllCohorts; HistGBM, recorded). Compares naive equal-cluster +-50 percent relative TOST p (Naive50) with Donner-adjusted relative TOST p (Adj50, Adj25), adjusted +-2 pp p (Adjp2), effective date count (Geff), adjusted MDE80 (pp), and two-stage hierarchical bootstrap 90 percent equal-cluster relative intervals (percent).',
            ['Scope', 'Cand', 'Cap', 'G', 'Camp', 'ICC', 'DEFF', 'Geff', 'Naive50', 'Adj50', 'Adj25', 'Adjp2', 'AdjMDE', 'HierBoot90Rel'],
            camp_rows,
        ),
        'table_s19_locampo': (
            'Leave-one-campaign-out (LOCampO) robustness and per-campaign medians across all 6 physical field campaigns (HistGBM, recorded; percentages and percentage points). None denotes full 6-campaign pool; CampRhiMed and CampUMed report the omitted campaign median across cap in {10, 40}.',
            ['DroppedCamp', 'RemC', 'G', 'CampRhiMed', 'CampUMed', 'RemMobRhiMed', 'RemUMed', 'EqdU PAC10', 'EqdU PAC40'],
            locampo_rows,
        ),
    }


def tables(root=ROOT):
    metrics = root / 'results/metrics'
    diagnostics = root / 'results/diagnostics'
    data = pd.read_csv(metrics / 'calibration_budget_results.csv')
    data['domain'] = data.regime.str[:2]
    records = data.set_index(['domain', 'budget_K', 'method'])
    if not records.index.is_unique:
        raise ValueError('Duplicate publication key')
    splits = read_json(diagnostics / 'split_summary.json')
    rows = []
    keys = set()
    for r in range(4):
        regime = f'E{r}'
        split, = [v['partitions'] for k, v in splits.items() if k.startswith(regime)]
        for k in BUDGETS:
            if k > split['target_calib_pool']['n_sessions']:
                continue
            values = []
            for method in METHODS:
                key = (regime, k, method)
                row = records.loc[key]
                keys.add(key)
                if int(row.test_samples) != split['target_test']['n_samples']:
                    raise ValueError(f'Sample count differs: {key}')
                values.extend([f'{row.violation_rate:.4f}', f'{row.supported_fraction:.4f}'])
            rows.append([f'{regime}K{k}', str(int(row.test_samples)), *values])
    if keys != set(records.index):
        raise ValueError('Unexpected benchmark key')
    profiles = read_json(metrics / 'point_predictor_profiles.json')
    profiles = [[m.replace('_', ' '), f"{p['val_mae']:.2f}", f"{p['val_rmse']:.2f}", f"{p['fit_time_seconds']:.3f}"] for m, p in profiles.items()]
    sens = read_json(diagnostics / 'session_boundary_sensitivity.json')
    boundaries = []
    for method, key in [('Reset', 'reset'), ('Drop', 'relative_drop'), ('Burst', 'active_burst')]:
        d = sens[key]
        x = d['downstream_evaluation']
        boundaries.append([method, str(d['total_extracted_sessions']), str(d['throughput_distribution']['zero_throughput_sessions']), *[f"{v['conformal_violation_rate_k0']:.4f}" for v in [x['e1_campaign_transfer'], x['e3_joint_shift']]]])
    boot = read_json(metrics / 'bootstrap_significance_tests.json')
    contrasts = []
    for r, b in sorted(boot.items()):
        p = splits[r]['partitions']['target_test']
        contrasts.append([r[:2] + 'D', str(p['n_days']), *[f'{v:.4f}' for metric in ['delta_V', 'delta_U'] for v in [b[metric]['point'], *b[metric]['ci_95']]]])
    secondary = []
    for reg, b in read_json(metrics / 'online_aci_results.json').items():
        secondary.append([reg[:2] + 'Online', f"{b['violation_rate']:.4f}", f"{b['supported_fraction']:.4f}"])
    for reg, b in read_json(metrics / 'covariate_shift_conformal.json').items():
        for proto, variants in b['protocols'].items():
            for clip, entry in variants.items():
                key = reg[:2] + proto.split('_')[1] + clip.split('_')[0]
                secondary.append([key, f"{entry['violation_rate']:.4f}", f"{entry['supported_fraction']:.4f}"])
    external = root / 'results/exploratory/sirhan_external'
    frontier = pd.read_csv(external / 'matched_frontier.csv')
    frontier_rows = []
    for (budget, block), published in zip(frontier.groupby('budget'), [33.1, 47.2, 56.9], strict=True):
        values = block.pivot(index='seed', columns='method', values='U')
        paired = (values.persistence - values['global']).dropna()
        frontier_rows.append([str(round(100 * budget)), f'{published:.1f}',
                              *[f'{100 * values[m].mean():.2f}' for m in ['global', 'minimum', 'persistence']],
                              f'{100 * paired.mean():.2f}', f'{(paired > 0).sum()}/{len(paired)}'])
    curves = pd.read_csv(external / 'decision_curves.csv')
    fixed_rows = []
    for method, block in curves[curves.beta.round(5) == .1].groupby('method'):
        fixed_rows.append([method.title(), f'{100 * block.V.mean():.2f}', f'{100 * block.U.mean():.2f}',
                           str((block.V <= .1).sum())])
    transitions = pd.read_csv(external / 'lag_transitions.csv')
    exclusions = pd.read_csv(external / 'trace_exclusions.csv')
    exclusion_rows = [[r.sample, str(r.excluded), f'{r.mean_gain_pp:.2f}', str(r.positive_splits),
                       f'{100 * r.tree_v:.2f}', f'{100 * r.persistence_v:.2f}'] for r in exclusions.itertuples()]
    transition_rows = [[r.setting, str(r.n), f'{r.pearson:.2f}', f'{r.spearman:.2f}', f'{r.mae:.2f}',
                        *[f'{100 * x:.1f}' for x in [r.near_zero, r.fall, r.rise]]] for r in transitions.itertuples()]
    clock = read_json(diagnostics / 'prediction_time_validity.json')
    norway = pd.read_csv(root / 'results/external_validation/norway_metrics.csv').to_dict('records')
    replay = [[r['setting'], r['method'], str(r['n']), str(r['days']), f"{r['mae']:.2f}",
               f"{r['q']:.2f}", f"{100 * r['violation']:.2f}", f"{100 * r['supported']:.2f}"] for r in clock + norway]
    groups = read_json(root / 'results/external_validation/irish_group_validation.json')
    group_rows = [[str(r['k']), r['method'], str(r['group_rows']), f"{100 * r['coverage']:.2f}",
                   f"{100 * r['violation']:.2f}", f"{100 * r['supported']:.2f}"] for r in groups]
    curve = pd.read_csv(root / 'results/clock_histgbm/frontier.csv')
    issued_rows = [[r.regime, r.model, str(r.issued), str(r.scored), f'{r.positive_scored}/{r.positive}', str(r.violations),
                    f'{100 * r.lo:.2f}', f'{100 * r.hi:.2f}', f'{100 * r.u:.2f}']
                   for r in curve[(curve.k == 10) & (curve.policy == 'Global')].itertuples()]
    drive = pd.read_csv(root / 'results/external_validation/drive3_results.csv')
    drive_rows = []
    for r in drive[(drive.date == 'all') & (drive.model != 'Tree_noNR')].itertuples():
        carrier = 'ATT' if r.carrier == 'AT&T' else r.carrier
        drive_rows.append([carrier, r.model, str(int(r.issued)), str(int(r.scored)), str(int(r.positive)),
                           str(int(r.violations)), f'{100 * r.lo:.2f}', f'{100 * r.hi:.2f}', f'{100 * r.u:.4f}'])

    return {
        'table1_point_predictors': ('Source validation errors in Mbps and measured fit time in seconds.', ['Model', 'MAE', 'RMSE', 'Seconds'], profiles),
        'table2_main_benchmark': ('Test sessions and lower-bound performance by regime and target prefix. P denotes point, G global, R radio access and M missingness groups. V denotes violations and U supported fraction.', ['Regime/K', 'N', 'PV', 'PU', 'GV', 'GU', 'RV', 'RU', 'MV', 'MU'], rows),
        'table3_segmentation': ('Source-only sensitivity across all eligible later-campaign pairs.', ['Boundary', 'Segments', 'Zeros', 'E1V', 'E3V'], boundaries),
        'table4_clusters': ('Grouped minus global at ten sessions. Exploratory paired date bootstrap percentile endpoints.', ['Contrast', 'Days', 'dV', 'Vlo', 'Vhi', 'dU', 'Ulo', 'Uhi'], contrasts),
        'table5_secondary': ('Online feedback and covariate weighting. A uses calibration-pool features and B uses test features. Tight and wide denote weight clipping ranges.', ['Protocol', 'Violation', 'Supported'], secondary),
        'table6_irish_frontier': ('Irish retrospective frontier. Budget and supported throughput are percentages. Gain is persistence minus rerun global in percentage points on jointly feasible splits. Wins counts positive paired gains.', ['Budget', 'Published', 'Rerun', 'Minimum', 'Persistence', 'Gain', 'Wins'], frontier_rows),
        'table7_irish_fixed': ('Irish fixed nominal ten percent. Mean violation and supported throughput are percentages. Passes counts splits meeting the target out of thirty.', ['Predictor', 'MeanV', 'MeanU', 'Passes'], fixed_rows),
        'table8_influence': ('Irish fixed-setting exclusions from test scoring. Gain is the paired change in supported throughput in percentage points. Wins counts positive splits. Violation rates are percentages.', ['Sample', 'Omitted', 'Gain', 'Wins', 'TreeV', 'LagV'], exclusion_rows),
        'table9_lag': ('Lag versus endpoint on unique Irish rows and held-out Rome sessions. MAE is in Mbps. NearZero, Fall and Rise are percentages.', ['Setting', 'Pairs', 'Pearson', 'Spearman', 'LagMAE', 'NearZero', 'Fall', 'Rise'], transition_rows),
        'table10_protocols': ('Ten-label calibration for clock-triggered Rome forecasts and Norwegian interval forecasts. Error and offset are in Mbps. Violation and supported fractions are percentages.', ['Cohort', 'Model', 'Scored', 'Dates', 'MAE', 'Offset', 'Viol', 'Util'], replay),
        'table11_irish_groups': ('Chronological Irish persistence forecasts on 108519 rows from sixteen suffix dates. Local counts forecasts using a group-specific offset. Performance measures are percentages.', ['Labels', 'Rule', 'Local', 'Coverage', 'Violation', 'Supported'], group_rows),
        'table12_issued': ('Ten-label Rome clock forecasts. Positive gives measured positive commitments divided by issued positive commitments as counts. Errors counts measured violations. Low and High bound the all-issued violation percentage. U is supported throughput on measured outcomes in percent.', ['Regime', 'Predictor', 'Issued', 'Scored', 'Positive', 'Errors', 'Low', 'High', 'U'], issued_rows),
        'table13_drive3': ('US Drive 3 with ten earlier labels per carrier. Pos counts issued positive commitments. Fail counts observed violations. Risk bounds and supported throughput are percentages.', ['Carrier', 'Model', 'Issued', 'Scored', 'Pos', 'Fail', 'Low', 'High', 'U'], drive_rows),
        **_supp_extra_tables(root),
        **_main_tables(root),
    }


def latex(spec):
    caption, header, rows = spec
    prose = header[0] in {'Policy', 'Regime', 'OfferStratum', 'Scope', 'Axis', 'Dropped', 'DroppedCamp'}
    wide_pow = len(header) >= 12
    size = r'\centering\footnotesize\setlength{\tabcolsep}{' + ('2.2pt' if wide_pow else '3.5pt') + '}' if prose else r'\centering\small'
    align = (('llll' + 'r' * (len(header) - 4)) if len(header) > 3 and header[3] == 'Estimand' else ('ll' + 'r' * (len(header) - 2))) if wide_pow else ('l' * len(header) if prose else 'l' + 'r' * (len(header) - 1))
    lines = [r'\begin{table*}[!ht]', size, r'\caption{' + caption + '}', r'\begin{tabular}{' + align + '}', r'\hline']
    for row in [header, *rows]:
        lines.append(' & '.join(row) + r' \\')
    lines += [r'\hline', r'\end{tabular}', r'\end{table*}']
    return '\n'.join(lines) + '\n'
