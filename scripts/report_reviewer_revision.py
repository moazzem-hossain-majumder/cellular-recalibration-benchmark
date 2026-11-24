"""Generate complete reviewer-facing baseline and mechanism summaries."""
from pathlib import Path
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.report_marur_information_experiment import classify
OUT=ROOT/'results/exploratory/reviewer_baselines'
d=classify(pd.read_csv(OUT/'contrasts_and_mechanisms.csv'));d.to_csv(OUT/'classified_contrasts.csv',index=False)
counts=d.groupby(['candidate','reference','cohort','model','outcome']).size().rename('configuration_contrasts').reset_index();counts.to_csv(OUT/'contrast_counts.csv',index=False)
lines=['# Targeted reviewer baseline and mechanism results','',
       'Exploratory on previously inspected archives. All 792 prespecified configurations completed: six cohorts, two fixed predictors, three feedback conditions, two caps and eleven variants. No winner selected for deployment. The single stress seed per missingness mechanism and three random schedule seeds are sensitivity choices, not independent experiments.','',
       '## What the added controls establish','',
       '- Pooled versus pattern quantiles with the original pattern gate held fixed produced identical utility and conditional risk in all 72 paired configurations. This grid supplies no evidence of benefit from pattern-specific quantiles at window ten. It does not prove equality for every possible stream or larger window.',
       '- Removing only the gate never reduces utility in this implementation because it leaves the query schedule and score updates unchanged and can only restore previously zeroed bounds. Conditional risk can move either way. Monotonic utility is an implementation consequence, not a discovered universal calibration theorem.',
       '- Random query schedules expose seed-dependent comparisons. Equal-cost gains against one seed cannot establish that adaptive timing is generally better.',
       '- DecayingOGD produces both gains and regressions, including higher conditional risk. More recent calibration machinery does not automatically solve sparse-feedback cellular commitments. The implementation adapts a published update, not its guarantee.','',
       '## Every predeclared comparison','',
       'Counts are dependent configuration contrasts. A utility gain means strictly greater supported-throughput fraction with a nonincreasing positive-conditional upper risk bound and equal realized attempts. No practical margin or significance is inferred. Undefined conditional risk cannot count as a gain.','']
for (candidate,reference),g in d.groupby(['candidate','reference']):
    lines += [f'- {candidate} versus {reference}: '+ '; '.join(f'{k}: {v}' for k,v in g.outcome.value_counts().items())+'.']
lines += ['','## Every cohort: recorded-feedback HistGBM, cap ten','',
          'The fixed descriptive slice below retains all cohorts and all planned comparisons; other predictors/caps/stress conditions remain in the complete ledger. Utility and risk differences are percentage points, candidate minus reference. An equal cap alone is not used to claim matching.','']
for cohort,g in d[(d.model=='HistGBM')&(d.scenario=='Recorded')&(d.new_query_cap==10)].groupby('cohort'):
    lines += [f'### {cohort}','']
    for x in g.itertuples():lines += [f'- {x.candidate} versus {x.reference}: costs {int(x.candidate_queries)}/{int(x.reference_queries)}, matched={x.matched_cost}; utility {100*x.u_delta:+.3f} pp; conditional upper risk {100*x.positive_high_delta:+.3f} pp; shared/removed/added offers {x.shared_offers}/{x.removed_offers}/{x.added_offers}.']
    lines += ['']
lines += ['## Reconstructing why windows fail','',
          'The score audit reconstructs all 1,008 clock/window configurations from initial scores and completed response histories, and verifies every lower bound against the saved ledger. A threshold may tie across several scores; “binding missing” means at least one tied threshold score came from conservative missing-feedback completion. It does not prove that score uniquely caused the decision. “Older than 60 minutes” describes timestamp age, not proof of distribution shift. Gate vetoes count a positive raw bound changed to zero by insufficient pattern support.','',
          'In recorded-feedback HistGBM at cap 40, Verizon W20 has a conservative missing score tied at the threshold on 159 of 287 eligible opportunities; all 159 have a zero pre-gate bound. This supports a specific conservative-score explanation for that operating point. Verizon W40 has no missing score tied at the threshold but still loses substantial utility, so missing-score domination cannot explain every regression. In E3, no missing score binds and no gate veto occurs at any tested window in this slice; retained observed residuals and the changed quantile explain the recorded lower bounds, although the archives cannot establish a causal physical cause of the residual shift.','',
          'All-cohort recorded HistGBM cap-40 score diagnostics follow, for W10/W20/W40.','']
diag=pd.read_csv(OUT/'window_score_diagnostics.csv')
for cohort,g in diag[(diag.model=='HistGBM')&(diag.scenario=='Recorded')&(diag.new_query_cap==40)&diag.variant.str.startswith('completed')].groupby('cohort'):
    g=g.set_index('variant').loc[['completed_W10','completed_W20','completed_W40']]
    lines += [f"- {cohort}: binding-missing ticks "+'/'.join(str(int(v)) for v in g.binding_missing)+'; zero raw bound with binding missing '+ '/'.join(str(int(v)) for v in g.bound_zero_with_binding_missing)+'; gate vetoes '+ '/'.join(str(int(v)) for v in g.gate_vetoes)+'; threshold age >60 min '+ '/'.join(str(int(v)) for v in g.threshold_age_over_60m)+f'; eligible ticks {int(g.eligible.iloc[0])}.']
lines += ['','## Offer-level attribution','',
          'Every old window contrast and new baseline contrast decomposes measured supported-service differences into shared-offer size changes, newly added offers and removed offers. The components are checked to sum exactly to the total difference. Separate failure counts identify removed failures, added failures and changes on shared offers. This is an arithmetic decomposition on policy-selected sets, not causal mediation or an independent-sample comparison.','',
          'On the prior Ireland ten-query MARUR/Periodic comparison, the same 159 positive offers and fourteen fewer shared failures show a size/reliability trade-off, not extra abstention. Conversely, the prior Verizon comparison with Early removes ten offers and six failures without improving shared-offer failures. The new full decomposition files retain every contradictory case rather than only these examples.','',
          '## Reviewer recommendation','',
          'Retain the unchanged default for reproducibility, not because it is proven optimal. Drop claims that pattern-specific quantiles, information clocks, or larger windows consistently improve service. Present the work as empirical acquisition/decision methodology with controlled ablations and explicit failures. Independent prospective data and application requirements remain unfulfilled. No higher readiness score or acceptance claim follows from adding baseline rows.','']
(ROOT/'docs/REVIEWER_BASELINE_RESULTS.md').write_text('\n'.join(lines),encoding='utf8')
print(d.groupby(['candidate','reference','outcome']).size().to_string())
