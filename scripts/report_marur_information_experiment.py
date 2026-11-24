"""Describe all prespecified exploratory contrasts without selecting a winner."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/exploratory/marur_information'

def classify(d):
    d=d.copy();finite=d.u_delta.notna()&d.positive_high_delta.notna();eps=1e-12
    d['outcome']='undefined conditional risk'
    d.loc[finite,'outcome']='unchanged'
    d.loc[finite & ((d.u_delta.abs()>eps)|(d.positive_high_delta.abs()>eps)),'outcome']='trade-off or risk-only change'
    d.loc[finite & (d.u_delta>eps)&(d.positive_high_delta<=eps),'outcome']='utility gain without higher risk bound'
    d.loc[finite & (d.u_delta < -eps)&(d.positive_high_delta>=-eps),'outcome']='utility loss without lower risk bound'
    d.loc[~d.matched_cost,'outcome']='unmatched cost'
    return d

def main():
    d=classify(pd.read_csv(OUT/'contrasts.csv'));s=pd.read_csv(OUT/'summary.csv')
    d.to_csv(OUT/'classified_contrasts.csv',index=False)
    counts=d.groupby(['candidate','reference','cohort','model','outcome']).size().rename('configuration_contrasts').reset_index()
    counts.to_csv(OUT/'contrast_counts.csv',index=False)
    primary=d[(d.candidate=='observed_W10')&(d.reference=='completed_W10')]
    lines=['# MARUR information-clock and calibration-window experiment','',
        '**Exploratory evidence only.** Previously inspected cohorts, fixed archived point predictions, no new independent trips, and no policy promotion. The protocol and configuration were written before this run.','',
        f"Ran {len(s)} configurations: six cohorts, two fixed predictors, seven feedback conditions, two attempt caps, and eleven policy/window variants. All original result files remain separate.",'',
        'Primary comparison changes only the age-clock source (completed response versus successful observed label). Both use five-minute attempt spacing, ten initial labels, a ten-score window, identical pattern logic, and identical conservative failed-response admission. Secondary comparisons change the window to 20 or 40 without adding free labels.','',
        '## Results of the primary contrast','',
        'Counts below describe configuration contrasts, not independent experiments or statistical evidence. Seeds, caps, models, carriers and calendar dates can share observations. Some identical trajectories recur across caps. A gain means strictly greater supported-throughput fraction and a nonincreasing positive-conditional upper risk bound, with equal realized attempts. It is not a significance or noninferiority claim.','']
    for scope,group in [('Recorded feedback only',primary[primary.scenario=='Recorded']),('All seven feedback conditions',primary)]:
        values=group.outcome.value_counts().to_dict();lines += [f'**{scope}:** '+ '; '.join(f'{k}: {v}' for k,v in values.items())+'.','']
    for cohort,g in primary.groupby('cohort'):
        lines += [f'### {cohort}','']
        for model,mg in g.groupby('model'):
            matched=mg[mg.matched_cost];values=mg.outcome.value_counts().to_dict()
            desc='; '.join(f'{k}: {v}' for k,v in values.items())
            if len(matched):desc+=f'. Matched utility differences range from {100*matched.u_delta.min():.3f} to {100*matched.u_delta.max():.3f} percentage points; positive-conditional upper-risk differences range from {100*matched.positive_high_delta.min():.3f} to {100*matched.positive_high_delta.max():.3f} points'
            lines += [f'- {model}: {desc}.']
        lines += ['']
    lines += ['## Complete recorded-feedback operating points','',
        'The following lists every cohort for the fixed HistGBM predictor at cap 10, including unequal-cost cases. This is a predefined descriptive slice, not the best model/cap/seed. All other configurations and per-date summaries are in the accompanying CSVs. Utility is delivered measured throughput divided by measured available throughput. Risk is the upper finite-record violation bound conditional on positive offers.','']
    for cohort in sorted(s.cohort.unique()):
        g=s[(s.cohort==cohort)&(s.model=='HistGBM')&(s.scenario=='Recorded')&(s.new_query_cap==10)].set_index('variant')
        c,b=g.loc['observed_W10'],g.loc['completed_W10']
        lines += [f"- {cohort}: completed → observed: attempts {int(b.new_query_attempts)} → {int(c.new_query_attempts)}; utility {100*b.u:.3f}% → {100*c.u:.3f}%; conditional upper risk {100*b.positive_high:.3f}% → {100*c.positive_high:.3f}%; positive offers {int(b.positive)} → {int(c.positive)}; positive dates {int(b.positive_dates)} → {int(c.positive_dates)}."]
    lines += ['','## Recorded-feedback window sensitivity','',
        'For completeness, all six HistGBM cohorts at cap 40 are listed below. Actual costs differ across cohorts but remain identical across these window variants within a cohort. These are completed-response-clock policies with five-minute attempt spacing, not claims of improvement over every original baseline. Values are W10 → W20 → W40.','']
    for cohort in sorted(s.cohort.unique()):
        g=s[(s.cohort==cohort)&(s.model=='HistGBM')&(s.scenario=='Recorded')&(s.new_query_cap==40)].set_index('variant')
        rows=[g.loc[f'completed_W{w}'] for w in [10,20,40]]
        lines += [f"- {cohort}: {int(rows[0].new_query_attempts)} attempts each; utility "+' → '.join(f'{100*r.u:.3f}%' for r in rows)+'; conditional upper risk '+' → '.join(f'{100*r.positive_high:.3f}%' for r in rows)+'; positive offers '+' → '.join(str(int(r.positive)) for r in rows)+'.']
    lines += ['','The direction is cohort-specific: W20 improves both displayed metrics in E1 and T-Mobile, while W40 does so in AT&T and E1. E3 and Verizon lose substantial useful throughput as the window grows; Ireland shows a small utility/risk trade-off. These operating points are exploratory illustrations, not a policy-selection rule or evidence of acceptable absolute risk. In particular, many positive-conditional upper bounds remain far above 10%.','',
        '## Window sensitivity and reference policies','']
    for (candidate,reference),g in d.groupby(['candidate','reference']):
        if (candidate,reference)==('observed_W10','completed_W10'):continue
        lines += [f'- {candidate} versus {reference}: '+ '; '.join(f'{k}: {v}' for k,v in g.outcome.value_counts().items())+'.']
    lines += ['','## Interpretation and limits','',
        'Changing the clock changes when calibration information is acquired, not the frozen forecast model. Failed responses still add conservative scores, so retries may reduce future commitments and consume attempts without adding measured labels. Successful observations can instead refresh the residual window. Longer windows alter both retained residuals and missing-pattern support; their effects cannot be attributed solely to a less extreme quantile. Natural recorded feedback and synthetic feedback stress must be interpreted separately.','',
        'At zero positive offers, conditional risk is undefined and cannot count as an improvement. Equal caps are not equal costs; all unmatched rows are retained and excluded from matched gain/loss counts. Synthetic masks hide feedback only: the evaluator still uses archived outcomes where known. Actual missing outcomes contribute unresolved risk bounds. Risk bounds are not confidence intervals, and no independence-based p-values are reported.','',
        'The new supported-Mbps-per-eligible metric is a conservative observed contribution: missing outcomes contribute no supported service in its numerator. The original utility fraction uses measured available throughput as its denominator. Neither should be described as measured live application benefit.','',
        'No controller is selected automatically from these test results. A prospective, frozen comparison is required before claiming a reliable improvement or a new methodological advance. See the separately written protocol for assumptions and the full metric list.','',
        '## Reproduction','',
        '`python scripts/run_marur_information_experiment.py` regenerates the exploratory ledgers; `python scripts/validate_marur_information_experiment.py` independently checks events, masks, costs and key metrics; `python scripts/report_marur_information_experiment.py` regenerates this report and its figure.','']
    (ROOT/'docs/MARUR_INFORMATION_EXPERIMENT_RESULTS.md').write_text('\n'.join(lines),encoding='utf8')
    fig,axes=plt.subplots(2,3,figsize=(12,7),layout='constrained')
    for (cohort,g),ax in zip(primary.groupby('cohort'),axes.flat):
        for model,marker in [('HistGBM','o'),('Persistence','x')]:
            rows=g[(g.model==model)&g.matched_cost]
            ax.scatter(100*rows.u_delta,100*rows.positive_high_delta,label=model,marker=marker,alpha=.65,s=28)
        ax.axhline(0,color='gray',lw=.8);ax.axvline(0,color='gray',lw=.8)
        ax.set(title=cohort,xlabel='Supported-throughput change (pp)',ylabel='Positive-conditional upper-risk change (pp)')
    axes[0,0].legend(fontsize=8)
    fig.suptitle('Observed-label versus completed-response age: matched realized attempts\nExploratory archived cohorts; all mask seeds/caps; overlapping points are not independent',fontsize=11)
    for ext in ['png','pdf']:fig.savefig(OUT/f'primary_contrast.{ext}',dpi=180)
    plt.close(fig)
    print(primary.groupby('outcome').size().to_string())
if __name__=='__main__':main()
