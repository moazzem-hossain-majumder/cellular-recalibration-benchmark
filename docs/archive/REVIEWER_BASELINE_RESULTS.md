# Targeted reviewer baseline and mechanism results

Exploratory on previously inspected archives. All 792 prespecified configurations completed: six cohorts, two fixed predictors, three feedback conditions, two caps and eleven variants. No winner selected for deployment. The single stress seed per missingness mechanism and three random schedule seeds are sensitivity choices, not independent experiments.

## What the added controls establish

- Pooled versus pattern quantiles with the original pattern gate held fixed produced identical utility and conditional risk in all 72 paired configurations. This grid supplies no evidence of benefit from pattern-specific quantiles at window ten. It does not prove equality for every possible stream or larger window.
- Removing only the gate never reduces utility in this implementation because it leaves the query schedule and score updates unchanged and can only restore previously zeroed bounds. Conditional risk can move either way. Monotonic utility is an implementation consequence, not a discovered universal calibration theorem.
- Random query schedules expose seed-dependent comparisons. Equal-cost gains against one seed cannot establish that adaptive timing is generally better.
- DecayingOGD produces both gains and regressions, including higher conditional risk. More recent calibration machinery does not automatically solve sparse-feedback cellular commitments. The implementation adapts a published update, not its guarantee.

## Every predeclared comparison

Counts are dependent configuration contrasts. A utility gain means strictly greater supported-throughput fraction with a nonincreasing positive-conditional upper risk bound and equal realized attempts. No practical margin or significance is inferred. Undefined conditional risk cannot count as a gain.

- DecayingOGD versus ACI: trade-off or risk-only change: 38; utility gain without higher risk bound: 19; utility loss without lower risk bound: 15.
- DecayingOGD versus Periodic: trade-off or risk-only change: 45; utility loss without lower risk bound: 18; utility gain without higher risk bound: 9.
- MARUR versus ACI: unmatched cost: 36; trade-off or risk-only change: 16; utility gain without higher risk bound: 13; utility loss without lower risk bound: 7.
- MARUR versus Early: trade-off or risk-only change: 34; utility gain without higher risk bound: 21; unmatched cost: 12; utility loss without lower risk bound: 5.
- MARUR versus Periodic: unmatched cost: 36; utility gain without higher risk bound: 13; trade-off or risk-only change: 13; utility loss without lower risk bound: 10.
- MARUR versus Random123: trade-off or risk-only change: 29; utility gain without higher risk bound: 19; unmatched cost: 12; utility loss without lower risk bound: 12.
- MARUR versus Random2026: trade-off or risk-only change: 37; utility gain without higher risk bound: 16; unmatched cost: 12; utility loss without lower risk bound: 7.
- MARUR versus Random42: trade-off or risk-only change: 33; utility gain without higher risk bound: 18; unmatched cost: 12; utility loss without lower risk bound: 9.
- MARUR_Pooled versus MARUR: unchanged: 72.
- MARUR_PooledNoGate versus MARUR_Pooled: unchanged: 46; utility gain without higher risk bound: 16; trade-off or risk-only change: 10.

## Every cohort: recorded-feedback HistGBM, cap ten

The fixed descriptive slice below retains all cohorts and all planned comparisons; other predictors/caps/stress conditions remain in the complete ledger. Utility and risk differences are percentage points, candidate minus reference. An equal cap alone is not used to claim matching.

### AT&T

- MARUR versus Periodic: costs 10/10, matched=True; utility +2.582 pp; conditional upper risk -7.831 pp; shared/removed/added offers 11/0/90.
- MARUR versus Early: costs 10/10, matched=True; utility +2.688 pp; conditional upper risk +0.124 pp; shared/removed/added offers 8/0/93.
- MARUR versus ACI: costs 10/10, matched=True; utility +2.590 pp; conditional upper risk -12.376 pp; shared/removed/added offers 8/0/93.
- DecayingOGD versus Periodic: costs 10/10, matched=True; utility +0.231 pp; conditional upper risk +8.392 pp; shared/removed/added offers 6/5/7.
- DecayingOGD versus ACI: costs 10/10, matched=True; utility +0.239 pp; conditional upper risk +3.846 pp; shared/removed/added offers 6/2/7.
- MARUR_Pooled versus MARUR: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 101/0/0.
- MARUR_PooledNoGate versus MARUR_Pooled: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 101/0/0.
- MARUR versus Random42: costs 10/10, matched=True; utility +0.567 pp; conditional upper risk -0.973 pp; shared/removed/added offers 57/0/44.
- MARUR versus Random123: costs 10/10, matched=True; utility +0.567 pp; conditional upper risk -0.973 pp; shared/removed/added offers 57/0/44.
- MARUR versus Random2026: costs 10/10, matched=True; utility +2.090 pp; conditional upper risk +9.554 pp; shared/removed/added offers 57/0/44.

### E1

- MARUR versus Periodic: costs 10/10, matched=True; utility +2.384 pp; conditional upper risk -10.404 pp; shared/removed/added offers 18/4/27.
- MARUR versus Early: costs 10/10, matched=True; utility +2.413 pp; conditional upper risk -5.380 pp; shared/removed/added offers 17/2/28.
- MARUR versus ACI: costs 10/10, matched=True; utility +2.659 pp; conditional upper risk -20.000 pp; shared/removed/added offers 8/1/37.
- DecayingOGD versus Periodic: costs 10/10, matched=True; utility -0.523 pp; conditional upper risk +31.818 pp; shared/removed/added offers 1/21/0.
- DecayingOGD versus ACI: costs 10/10, matched=True; utility -0.248 pp; conditional upper risk +22.222 pp; shared/removed/added offers 1/8/0.
- MARUR_Pooled versus MARUR: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 45/0/0.
- MARUR_PooledNoGate versus MARUR_Pooled: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +2.639 pp; shared/removed/added offers 45/0/3.
- MARUR versus Random42: costs 10/10, matched=True; utility +0.081 pp; conditional upper risk -2.639 pp; shared/removed/added offers 25/23/20.
- MARUR versus Random123: costs 10/10, matched=True; utility -0.837 pp; conditional upper risk -2.786 pp; shared/removed/added offers 43/28/2.
- MARUR versus Random2026: costs 10/10, matched=True; utility -1.816 pp; conditional upper risk -3.838 pp; shared/removed/added offers 45/54/0.

### E3

- MARUR versus Periodic: costs 10/10, matched=True; utility +0.662 pp; conditional upper risk +2.470 pp; shared/removed/added offers 19/0/30.
- MARUR versus Early: costs 10/10, matched=True; utility +1.202 pp; conditional upper risk +35.102 pp; shared/removed/added offers 13/2/36.
- MARUR versus ACI: costs 10/10, matched=True; utility +0.662 pp; conditional upper risk +2.470 pp; shared/removed/added offers 19/0/30.
- DecayingOGD versus Periodic: costs 10/10, matched=True; utility +0.877 pp; conditional upper risk +1.422 pp; shared/removed/added offers 10/9/27.
- DecayingOGD versus ACI: costs 10/10, matched=True; utility +0.877 pp; conditional upper risk +1.422 pp; shared/removed/added offers 10/9/27.
- MARUR_Pooled versus MARUR: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 49/0/0.
- MARUR_PooledNoGate versus MARUR_Pooled: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 49/0/0.
- MARUR versus Random42: costs 10/10, matched=True; utility +1.030 pp; conditional upper risk -4.898 pp; shared/removed/added offers 5/0/44.
- MARUR versus Random123: costs 10/10, matched=True; utility +0.976 pp; conditional upper risk -4.898 pp; shared/removed/added offers 10/0/39.
- MARUR versus Random2026: costs 10/10, matched=True; utility +1.202 pp; conditional upper risk -11.565 pp; shared/removed/added offers 3/0/46.

### Ireland

- MARUR versus Periodic: costs 10/10, matched=True; utility -2.988 pp; conditional upper risk -8.805 pp; shared/removed/added offers 159/0/0.
- MARUR versus Early: costs 10/10, matched=True; utility +0.994 pp; conditional upper risk -27.559 pp; shared/removed/added offers 11/0/148.
- MARUR versus ACI: costs 10/10, matched=True; utility -2.163 pp; conditional upper risk -11.195 pp; shared/removed/added offers 120/0/39.
- DecayingOGD versus Periodic: costs 10/10, matched=True; utility -0.587 pp; conditional upper risk +12.727 pp; shared/removed/added offers 71/88/18.
- DecayingOGD versus ACI: costs 10/10, matched=True; utility +0.238 pp; conditional upper risk +10.337 pp; shared/removed/added offers 32/88/57.
- MARUR_Pooled versus MARUR: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 159/0/0.
- MARUR_PooledNoGate versus MARUR_Pooled: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 159/0/0.
- MARUR versus Random42: costs 10/10, matched=True; utility -2.429 pp; conditional upper risk -21.683 pp; shared/removed/added offers 82/0/77.
- MARUR versus Random123: costs 10/10, matched=True; utility -9.314 pp; conditional upper risk -21.552 pp; shared/removed/added offers 159/65/0.
- MARUR versus Random2026: costs 10/10, matched=True; utility -0.685 pp; conditional upper risk -27.365 pp; shared/removed/added offers 47/0/112.

### T-Mobile

- MARUR versus Periodic: costs 10/10, matched=True; utility -0.018 pp; conditional upper risk +6.944 pp; shared/removed/added offers 16/2/0.
- MARUR versus Early: costs 10/10, matched=True; utility +0.012 pp; conditional upper risk +22.500 pp; shared/removed/added offers 10/0/6.
- MARUR versus ACI: costs 10/10, matched=True; utility -0.015 pp; conditional upper risk -6.731 pp; shared/removed/added offers 11/2/5.
- DecayingOGD versus Periodic: costs 10/10, matched=True; utility +0.089 pp; conditional upper risk +3.419 pp; shared/removed/added offers 17/1/22.
- DecayingOGD versus ACI: costs 10/10, matched=True; utility +0.092 pp; conditional upper risk -10.256 pp; shared/removed/added offers 13/0/26.
- MARUR_Pooled versus MARUR: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 16/0/0.
- MARUR_PooledNoGate versus MARUR_Pooled: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 16/0/0.
- MARUR versus Random42: costs 10/10, matched=True; utility -0.417 pp; conditional upper risk +11.851 pp; shared/removed/added offers 16/61/0.
- MARUR versus Random123: costs 10/10, matched=True; utility -0.239 pp; conditional upper risk +4.318 pp; shared/removed/added offers 16/39/0.
- MARUR versus Random2026: costs 10/10, matched=True; utility -0.072 pp; conditional upper risk +3.409 pp; shared/removed/added offers 16/6/0.

### Verizon

- MARUR versus Periodic: costs 10/10, matched=True; utility +0.544 pp; conditional upper risk +27.619 pp; shared/removed/added offers 5/0/37.
- MARUR versus Early: costs 10/10, matched=True; utility -0.859 pp; conditional upper risk -4.304 pp; shared/removed/added offers 42/10/0.
- MARUR versus ACI: costs 10/10, matched=True; utility +0.544 pp; conditional upper risk +27.619 pp; shared/removed/added offers 5/0/37.
- DecayingOGD versus Periodic: costs 10/10, matched=True; utility +2.093 pp; conditional upper risk +53.333 pp; shared/removed/added offers 0/5/15.
- DecayingOGD versus ACI: costs 10/10, matched=True; utility +2.093 pp; conditional upper risk +53.333 pp; shared/removed/added offers 0/5/15.
- MARUR_Pooled versus MARUR: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 42/0/0.
- MARUR_PooledNoGate versus MARUR_Pooled: costs 10/10, matched=True; utility +0.000 pp; conditional upper risk +0.000 pp; shared/removed/added offers 42/0/0.
- MARUR versus Random42: costs 10/10, matched=True; utility +0.547 pp; conditional upper risk +47.619 pp; shared/removed/added offers 1/0/41.
- MARUR versus Random123: costs 10/10, matched=True; utility +0.547 pp; conditional upper risk +47.619 pp; shared/removed/added offers 1/0/41.
- MARUR versus Random2026: costs 10/10, matched=True; utility +0.547 pp; conditional upper risk +47.619 pp; shared/removed/added offers 1/0/41.

## Reconstructing why windows fail

The score audit reconstructs all 1,008 clock/window configurations from initial scores and completed response histories, and verifies every lower bound against the saved ledger. A threshold may tie across several scores; “binding missing” means at least one tied threshold score came from conservative missing-feedback completion. It does not prove that score uniquely caused the decision. “Older than 60 minutes” describes timestamp age, not proof of distribution shift. Gate vetoes count a positive raw bound changed to zero by insufficient pattern support.

In recorded-feedback HistGBM at cap 40, Verizon W20 has a conservative missing score tied at the threshold on 159 of 287 eligible opportunities; all 159 have a zero pre-gate bound. This supports a specific conservative-score explanation for that operating point. Verizon W40 has no missing score tied at the threshold but still loses substantial utility, so missing-score domination cannot explain every regression. In E3, no missing score binds and no gate veto occurs at any tested window in this slice; retained observed residuals and the changed quantile explain the recorded lower bounds, although the archives cannot establish a causal physical cause of the residual shift.

All-cohort recorded HistGBM cap-40 score diagnostics follow, for W10/W20/W40.

- AT&T: binding-missing ticks 0/12/0; zero raw bound with binding missing 0/7/0; gate vetoes 0/0/0; threshold age >60 min 252/271/296; eligible ticks 296.
- E1: binding-missing ticks 0/0/0; zero raw bound with binding missing 0/0/0; gate vetoes 4/1/1; threshold age >60 min 146/169/212; eligible ticks 238.
- E3: binding-missing ticks 0/0/0; zero raw bound with binding missing 0/0/0; gate vetoes 0/0/0; threshold age >60 min 149/171/171; eligible ticks 171.
- Ireland: binding-missing ticks 0/0/0; zero raw bound with binding missing 0/0/0; gate vetoes 0/0/0; threshold age >60 min 292/290/256; eligible ticks 334.
- T-Mobile: binding-missing ticks 0/0/0; zero raw bound with binding missing 0/0/0; gate vetoes 3/1/1; threshold age >60 min 224/252/279; eligible ticks 294.
- Verizon: binding-missing ticks 4/159/0; zero raw bound with binding missing 3/159/0; gate vetoes 0/0/0; threshold age >60 min 255/277/281; eligible ticks 287.

## Offer-level attribution

Every old window contrast and new baseline contrast decomposes measured supported-service differences into shared-offer size changes, newly added offers and removed offers. The components are checked to sum exactly to the total difference. Separate failure counts identify removed failures, added failures and changes on shared offers. This is an arithmetic decomposition on policy-selected sets, not causal mediation or an independent-sample comparison.

On the prior Ireland ten-query MARUR/Periodic comparison, the same 159 positive offers and fourteen fewer shared failures show a size/reliability trade-off, not extra abstention. Conversely, the prior Verizon comparison with Early removes ten offers and six failures without improving shared-offer failures. The new full decomposition files retain every contradictory case rather than only these examples.

## Reviewer recommendation

Retain the unchanged default for reproducibility, not because it is proven optimal. Drop claims that pattern-specific quantiles, information clocks, or larger windows consistently improve service. Present the work as empirical acquisition/decision methodology with controlled ablations and explicit failures. Independent prospective data and application requirements remain unfulfilled. No higher readiness score or acceptance claim follows from adding baseline rows.
