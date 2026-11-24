"""Machine-readable table specifications shared by the manuscript builders."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METHODS = ['Uncalibrated','Global_Conformal','RAT_Grouped','Proposed_Missingness_Aware']
BUDGETS = (0,1,2,5,8,9,10,15)

def read_json(path):
    return json.loads(path.read_text(encoding='utf8'))

def tables(root=ROOT):
    metrics = root/'results/metrics'
    diagnostics = root/'results/diagnostics'
    data = pd.read_csv(metrics/'calibration_budget_results.csv')
    data['domain'] = data.regime.str[:2]
    records = data.set_index(['domain','budget_K','method'])
    if not records.index.is_unique:
        raise ValueError('Duplicate publication key')
    splits = read_json(diagnostics/'split_summary.json')
    rows = []
    keys = set()
    for r in range(4):
        regime = f'E{r}'
        split, = [v['partitions'] for k,v in splits.items() if k.startswith(regime)]
        for k in BUDGETS:
            if k > split['target_calib_pool']['n_sessions']:
                continue
            values = []
            for method in METHODS:
                key = (regime,k,method)
                row = records.loc[key]
                keys.add(key)
                if int(row.test_samples) != split['target_test']['n_samples']:
                    raise ValueError(f'Sample count differs: {key}')
                values.extend([f'{row.violation_rate:.4f}',f'{row.supported_fraction:.4f}'])
            rows.append([f'{regime}K{k}',str(int(row.test_samples)),*values])
    if keys != set(records.index):
        raise ValueError('Unexpected benchmark key')
    profiles = read_json(metrics/'point_predictor_profiles.json')
    profiles = [[m.replace('_',' '),f"{p['val_mae']:.2f}",f"{p['val_rmse']:.2f}",f"{p['fit_time_seconds']:.3f}"] for m,p in profiles.items()]
    sens = read_json(diagnostics/'session_boundary_sensitivity.json')
    boundaries = []
    for method,key in [('Reset','reset'),('Drop','relative_drop'),('Burst','active_burst')]:
        d = sens[key]
        x = d['downstream_evaluation']
        boundaries.append([method,str(d['total_extracted_sessions']),str(d['throughput_distribution']['zero_throughput_sessions']),*[f"{v['conformal_violation_rate_k0']:.4f}" for v in [x['e1_campaign_transfer'],x['e3_joint_shift']]]])
    boot = read_json(metrics/'bootstrap_significance_tests.json')
    contrasts = []
    for r,b in sorted(boot.items()):
        p = splits[r]['partitions']['target_test']
        contrasts.append([r[:2]+'D',str(p['n_days']),*[f'{v:.4f}' for metric in ['delta_V','delta_U'] for v in [b[metric]['point'],*b[metric]['ci_95']]]])
    secondary = []
    for reg,b in read_json(metrics/'online_aci_results.json').items():
        secondary.append([reg[:2]+'Online',f"{b['violation_rate']:.4f}",f"{b['supported_fraction']:.4f}"])
    for reg,b in read_json(metrics/'covariate_shift_conformal.json').items():
        for proto,variants in b['protocols'].items():
            for clip,entry in variants.items():
                key = reg[:2]+proto.split('_')[1]+clip.split('_')[0]
                secondary.append([key,f"{entry['violation_rate']:.4f}",f"{entry['supported_fraction']:.4f}"])
    external = root/'results/exploratory/sirhan_external'
    frontier = pd.read_csv(external/'matched_frontier.csv')
    frontier_rows = []
    for (budget, block), published in zip(frontier.groupby('budget'), [33.1,47.2,56.9], strict=True):
        values = block.pivot(index='seed',columns='method',values='U')
        paired = (values.persistence-values['global']).dropna()
        frontier_rows.append([str(round(100*budget)),f'{published:.1f}',
                              *[f'{100*values[m].mean():.2f}' for m in ['global','minimum','persistence']],
                              f'{100*paired.mean():.2f}',f'{(paired>0).sum()}/{len(paired)}'])
    curves = pd.read_csv(external/'decision_curves.csv')
    fixed_rows = []
    for method, block in curves[curves.beta.round(5)==.1].groupby('method'):
        fixed_rows.append([method.title(),f'{100*block.V.mean():.2f}',f'{100*block.U.mean():.2f}',
                           str((block.V<=.1).sum())])
    transitions = pd.read_csv(external/'lag_transitions.csv')
    exclusions = pd.read_csv(external/'trace_exclusions.csv')
    exclusion_rows = [[r.sample,str(r.excluded),f'{r.mean_gain_pp:.2f}',str(r.positive_splits),
                       f'{100*r.tree_v:.2f}',f'{100*r.persistence_v:.2f}'] for r in exclusions.itertuples()]
    transition_rows = [[r.setting,str(r.n),f'{r.pearson:.2f}',f'{r.spearman:.2f}',f'{r.mae:.2f}',
                        *[f'{100*x:.1f}' for x in [r.near_zero,r.fall,r.rise]]] for r in transitions.itertuples()]
    clock = read_json(diagnostics/'prediction_time_validity.json')
    norway = pd.read_csv(root/'results/external_validation/norway_metrics.csv').to_dict('records')
    replay = [[r['setting'],r['method'],str(r['n']),str(r['days']),f"{r['mae']:.2f}",
               f"{r['q']:.2f}",f"{100*r['violation']:.2f}",f"{100*r['supported']:.2f}"] for r in clock+norway]
    groups = read_json(root/'results/external_validation/irish_group_validation.json')
    group_rows = [[str(r['k']),r['method'],str(r['group_rows']),f"{100*r['coverage']:.2f}",
                   f"{100*r['violation']:.2f}",f"{100*r['supported']:.2f}"] for r in groups]
    curve = pd.read_csv(root/'results/clock_histgbm/frontier.csv')
    issued_rows = [[r.regime,r.model,str(r.issued),str(r.scored),f'{r.positive_scored}/{r.positive}',str(r.violations),
                    f'{100*r.lo:.2f}',f'{100*r.hi:.2f}',f'{100*r.u:.2f}']
                   for r in curve[(curve.k==10)&(curve.policy=='Global')].itertuples()]
    drive = pd.read_csv(root/'results/external_validation/drive3_results.csv')
    drive_rows = []
    for r in drive[(drive.date=='all') & (drive.model!='Tree_noNR')].itertuples():
        carrier = 'ATT' if r.carrier=='AT&T' else r.carrier
        drive_rows.append([carrier,r.model,str(int(r.issued)),str(int(r.scored)),str(int(r.positive)),
                           str(int(r.violations)),f'{100*r.lo:.2f}',f'{100*r.hi:.2f}',f'{100*r.u:.4f}'])
    controller=pd.read_csv(root/'results/marur/summary.csv')
    chosen=controller[(controller.model=='HistGBM')&(controller.scenario=='Recorded')&
                      (controller.budget==50)&controller.policy.isin(['Frozen','Periodic','MARUR'])]
    controller_rows=[]
    for r in chosen.itertuples():
        label='ATT' if r.cohort=='AT&T' else r.cohort
        controller_rows.append([label,r.policy,str(r.new_query_attempts),str(r.positive),
            f'{100*r.positive_low:.2f}',f'{100*r.positive_high:.2f}',f'{100*r.u:.3f}'])
    cluster_rows=[]
    cluster_df=pd.read_csv(diagnostics/'trip_level_inference.csv')
    c_slice=cluster_df[(cluster_df.model=='HistGBM')&(cluster_df.scenario=='Recorded')&
                       (cluster_df.new_query_cap==10)&(cluster_df.baseline=='Periodic')]
    order=['E1','E3','AT&T','T-Mobile','Verizon','Ireland','Combined_CampaignDates','Ireland_Traces']
    c_map={r.scope:r for r in c_slice.itertuples()}
    labels={'AT&T':'ATT','Combined_CampaignDates':'All (16 Dates)','Ireland_Traces':'Ireland (Traces)'}
    for key in order:
        r=c_map[key]
        label=labels.get(key,key)
        cluster_rows.append([
            label,
            str(int(r.clusters)),
            f'{int(r.cand_query_days)}/{int(r.base_query_days)}',
            f'{int(r.cand_pos_days)}/{int(r.base_pos_days)}',
            f'{100*r.pool_du:+.2f}',
            f'{100*r.boot_du_lo:+.2f}',
            f'{100*r.boot_du_hi:+.2f}',
            f'{100*r.eq_du_mean:+.2f}',
            f'{100*r.t_du_lo:+.2f}',
            f'{100*r.t_du_hi:+.2f}',
            f'{100*r.pool_dhi:+.2f}',
        ])
    pacer_rows = []
    psumm_path = root / 'results/pacer/pacer_summary.csv'
    pseed_path = root / 'results/pacer/pacer_seed_sensitivity.csv'
    if psumm_path.is_file() and pseed_path.is_file():
        ps = pd.read_csv(psumm_path)
        psd = pd.read_csv(pseed_path)
        psm = (
            psd.groupby(['domain', 'cohort', 'model', 'cap_new'], as_index=False)['selective_excess_upper']
            .mean()
            .rename(columns={'selective_excess_upper': 'mean_excess'})
        )
        psub = ps[(ps['model'] == 'HistGBM') & (ps['scenario'] == 'Recorded') & (ps['cap_new'].isin([10, 40])) & (ps['policy'].isin(['Periodic', 'MARUR', 'PACER']))]
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
    return {
        'table1_point_predictors': ('Source validation errors in Mbps and measured fit time in seconds.', ['Model','MAE','RMSE','Seconds'],profiles),
        'table2_main_benchmark': ('Test sessions and lower-bound performance by regime and target prefix. P denotes point, G global, R radio access and M missingness groups. V denotes violations and U supported fraction.', ['Regime/K','N','PV','PU','GV','GU','RV','RU','MV','MU'],rows),
        'table3_segmentation': ('Source-only sensitivity across all eligible later-campaign pairs.', ['Boundary','Segments','Zeros','E1V','E3V'],boundaries),
        'table4_clusters': ('Grouped minus global at ten sessions. Exploratory paired date bootstrap percentile endpoints.', ['Contrast','Days','dV','Vlo','Vhi','dU','Ulo','Uhi'],contrasts),
        'table5_secondary': ('Online feedback and covariate weighting. A uses calibration-pool features and B uses test features. Tight and wide denote weight clipping ranges.', ['Protocol','Violation','Supported'],secondary),
        'table6_irish_frontier': ('Irish retrospective frontier. Budget and supported throughput are percentages. Gain is persistence minus rerun global in percentage points on jointly feasible splits. Wins counts positive paired gains.', ['Budget','Published','Rerun','Minimum','Persistence','Gain','Wins'],frontier_rows),
        'table7_irish_fixed': ('Irish fixed nominal ten percent. Mean violation and supported throughput are percentages. Passes counts splits meeting the target out of thirty.', ['Predictor','MeanV','MeanU','Passes'],fixed_rows),
        'table8_influence': ('Irish fixed-setting exclusions from test scoring. Gain is the paired change in supported throughput in percentage points. Wins counts positive splits. Violation rates are percentages.', ['Sample','Omitted','Gain','Wins','TreeV','LagV'],exclusion_rows),
        'table9_lag': ('Lag versus endpoint on unique Irish rows and held-out Rome sessions. MAE is in Mbps. NearZero, Fall and Rise are percentages.', ['Setting','Pairs','Pearson','Spearman','LagMAE','NearZero','Fall','Rise'],transition_rows),
        'table10_protocols': ('Ten-label calibration for clock-triggered Rome forecasts and Norwegian interval forecasts. Error and offset are in Mbps. Violation and supported fractions are percentages.', ['Cohort','Model','Scored','Dates','MAE','Offset','Viol','Util'],replay),
        'table11_irish_groups': ('Chronological Irish persistence forecasts on 108519 rows from sixteen suffix dates. Local counts forecasts using a group-specific offset. Performance measures are percentages.', ['Labels','Rule','Local','Coverage','Violation','Supported'],group_rows),
        'table12_issued': ('Ten-label Rome clock forecasts. Positive gives measured positive commitments divided by issued positive commitments as counts. Errors counts measured violations. Low and High bound the all-issued violation percentage. U is supported throughput on measured outcomes in percent.', ['Regime','Predictor','Issued','Scored','Positive','Errors','Low','High','U'],issued_rows),
        'table13_drive3': ('US Drive 3 with ten earlier labels per carrier. Pos counts issued positive commitments. Fail counts observed violations. Risk bounds and supported throughput are percentages.', ['Carrier','Model','Issued','Scored','Pos','Fail','Low','High','U'],drive_rows),
        'table14_marur': ('Frozen-tree controllers under a new-query cap of 40, with ten initial successful labels. Queries counts new attempts; historical acquisition cost is unknown. Offers counts positive commitments. PosLow and PosHigh bound violation among positive commitments, in percent. U is supported measured throughput in percent. Every model, budget, ablation and scenario is in the public ledger.', ['Cohort','Policy','Queries','Offers','PosLow','PosHigh','U'],controller_rows),
        'table15_cluster_inference': ('Independent-unit accounting and paired MARUR minus Periodic contrasts at matched ten new queries (HistGBM, recorded feedback). G counts collection dates (or 11 Irish driving traces; All pools co-located carriers onto 16 physical campaign-dates across 3 drives). QDays and PosDays give days with queries and positive offers (MARUR/Periodic). Utility differences are in percentage points: pooled dU with 2,000-draw cluster bootstrap 95 percent interval (BootLo, BootHi), equal-cluster mean (Eq dU) with two-sided t interval (tLo, tHi), and pooled all-issued upper risk difference (dRhi).', ['Scope','G','QDays','PosDays','Pool dU','BootLo','BootHi','Eq dU','tLo','tHi','dRhi'],cluster_rows),
        'table16_pacer': ('Locked Path A validation across four untouched held-out archives (26 campaign-dates) and six-cohort retrospective mean (16 campaign-dates), using frozen HistGBM and recorded feedback at new-query caps 10 and 40. Per, MAR, and PAC denote Periodic, MARUR, and PACER. Hi reports positive-offer upper risk and U reports useful delivered throughput in percent; A gives PACER offer frequency in percent; Exc is mean selective excess across seeds 42, 123, and 2026 versus Theorem 1 bound Bnd.', ['Cohort','Cap','PerHi','MARHi','PACHi','PerU','MARU','PACU','PACA','Exc','Bnd'],pacer_rows)}

def latex(spec):
    caption, header, rows = spec
    lines = [r'\begin{table*}[!ht]',r'\centering\small',r'\caption{'+caption+'}',r'\begin{tabular}{'+'l'+'r'*(len(header)-1)+'}',r'\hline']
    for row in [header,*rows]:
        lines.append(' & '.join(row)+r' \\')
    lines += [r'\hline',r'\end{tabular}',r'\end{table*}']
    return '\n'.join(lines)+'\n'
