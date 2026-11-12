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
    return {
        'table1_point_predictors': ('Source validation errors in Mbps and measured fit time in seconds.', ['Model','MAE','RMSE','Seconds'],profiles),
        'table2_main_benchmark': ('Test sessions and lower-bound performance by regime and target prefix. P denotes point, G global, R radio access and M missingness groups. V denotes violations and U supported fraction.', ['Regime/K','N','PV','PU','GV','GU','RV','RU','MV','MU'],rows),
        'table3_segmentation': ('Source-only sensitivity across all eligible later-campaign pairs.', ['Boundary','Segments','Zeros','E1V','E3V'],boundaries),
        'table4_clusters': ('Grouped minus global at ten sessions. Exploratory paired date bootstrap percentile endpoints.', ['Contrast','Days','dV','Vlo','Vhi','dU','Ulo','Uhi'],contrasts),
        'table5_secondary': ('Online feedback and covariate weighting. A uses calibration-pool features and B uses test features. Tight and wide denote weight clipping ranges.', ['Protocol','Violation','Supported'],secondary),
        'table6_irish_frontier': ('Irish retrospective frontier. Budget and supported throughput are percentages. Gain is persistence minus rerun global in percentage points on jointly feasible splits. Wins counts positive paired gains.', ['Budget','Published','Rerun','Minimum','Persistence','Gain','Wins'],frontier_rows),
        'table7_irish_fixed': ('Irish fixed nominal ten percent. Mean violation and supported throughput are percentages. Passes counts splits meeting the target out of thirty.', ['Predictor','MeanV','MeanU','Passes'],fixed_rows),
        'table8_influence': ('Irish fixed-setting exclusions from test scoring. Gain is the paired change in supported throughput in percentage points. Wins counts positive splits. Violation rates are percentages.', ['Sample','Omitted','Gain','Wins','TreeV','LagV'],exclusion_rows),
        'table9_lag': ('Lag versus endpoint on unique Irish rows and held-out Rome sessions. MAE is in Mbps. NearZero, Fall and Rise are percentages.', ['Setting','Pairs','Pearson','Spearman','LagMAE','NearZero','Fall','Rise'],transition_rows)}

def latex(spec):
    caption, header, rows = spec
    lines = [r'\begin{table*}[!ht]',r'\centering\small',r'\caption{'+caption+'}',r'\begin{tabular}{'+'l'+'r'*(len(header)-1)+'}',r'\hline']
    for row in [header,*rows]:
        lines.append(' & '.join(row)+r' \\')
    lines += [r'\hline',r'\end{tabular}',r'\end{table*}']
    return '\n'.join(lines)+'\n'
