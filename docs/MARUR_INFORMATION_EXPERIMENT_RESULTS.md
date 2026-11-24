# MARUR information-clock and calibration-window experiment

**Exploratory evidence only.** Previously inspected cohorts, fixed archived point predictions, no new independent trips, and no policy promotion. The protocol and configuration were written before this run.

Ran 1848 configurations: six cohorts, two fixed predictors, seven feedback conditions, two attempt caps, and eleven policy/window variants. All original result files remain separate.

Primary comparison changes only the age-clock source (completed response versus successful observed label). Both use five-minute attempt spacing, ten initial labels, a ten-score window, identical pattern logic, and identical conservative failed-response admission. Secondary comparisons change the window to 20 or 40 without adding free labels.

## Results of the primary contrast

Counts below describe configuration contrasts, not independent experiments or statistical evidence. Seeds, caps, models, carriers and calendar dates can share observations. Some identical trajectories recur across caps. A gain means strictly greater supported-throughput fraction and a nonincreasing positive-conditional upper risk bound, with equal realized attempts. It is not a significance or noninferiority claim.

**Recorded feedback only:** unchanged: 24.

**All seven feedback conditions:** unchanged: 129; unmatched cost: 18; trade-off or risk-only change: 8; utility loss without lower risk bound: 7; utility gain without higher risk bound: 6.

### AT&T

- HistGBM: unchanged: 14. Matched utility differences range from 0.000 to 0.000 percentage points; positive-conditional upper-risk differences range from 0.000 to 0.000 points.
- Persistence: unchanged: 14. Matched utility differences range from 0.000 to 0.000 percentage points; positive-conditional upper-risk differences range from 0.000 to 0.000 points.

### E1

- HistGBM: unchanged: 9; trade-off or risk-only change: 3; unmatched cost: 2. Matched utility differences range from 0.000 to 1.062 percentage points; positive-conditional upper-risk differences range from 0.000 to 4.085 points.
- Persistence: unchanged: 10; unmatched cost: 2; trade-off or risk-only change: 1; utility gain without higher risk bound: 1. Matched utility differences range from -0.463 to 0.621 percentage points; positive-conditional upper-risk differences range from -4.762 to 0.000 points.

### E3

- HistGBM: unchanged: 10; trade-off or risk-only change: 2; unmatched cost: 2. Matched utility differences range from -0.216 to 0.000 percentage points; positive-conditional upper-risk differences range from -17.045 to 0.000 points.
- Persistence: unchanged: 10; utility loss without lower risk bound: 2; unmatched cost: 2. Matched utility differences range from -13.044 to 0.000 percentage points; positive-conditional upper-risk differences range from 0.000 to 6.818 points.

### Ireland

- HistGBM: unchanged: 9; unmatched cost: 5. Matched utility differences range from 0.000 to 0.000 percentage points; positive-conditional upper-risk differences range from 0.000 to 0.000 points.
- Persistence: unchanged: 7; unmatched cost: 5; trade-off or risk-only change: 1; utility gain without higher risk bound: 1. Matched utility differences range from -1.313 to 1.980 percentage points; positive-conditional upper-risk differences range from -3.778 to 0.000 points.

### T-Mobile

- HistGBM: unchanged: 14. Matched utility differences range from 0.000 to 0.000 percentage points; positive-conditional upper-risk differences range from 0.000 to 0.000 points.
- Persistence: unchanged: 13; utility gain without higher risk bound: 1. Matched utility differences range from 0.000 to 0.022 percentage points; positive-conditional upper-risk differences range from 0.000 to 0.000 points.

### Verizon

- HistGBM: unchanged: 9; utility loss without lower risk bound: 2; utility gain without higher risk bound: 2; trade-off or risk-only change: 1. Matched utility differences range from -0.159 to 0.365 percentage points; positive-conditional upper-risk differences range from -8.135 to 1.692 points.
- Persistence: unchanged: 10; utility loss without lower risk bound: 3; utility gain without higher risk bound: 1. Matched utility differences range from -0.937 to 0.731 percentage points; positive-conditional upper-risk differences range from -7.018 to 2.727 points.

## Complete recorded-feedback operating points

The following lists every cohort for the fixed HistGBM predictor at cap 10, including unequal-cost cases. This is a predefined descriptive slice, not the best model/cap/seed. All other configurations and per-date summaries are in the accompanying CSVs. Utility is delivered measured throughput divided by measured available throughput. Risk is the upper finite-record violation bound conditional on positive offers.

- AT&T: completed → observed: attempts 10 → 10; utility 4.782% → 4.782%; conditional upper risk 41.584% → 41.584%; positive offers 101 → 101; positive dates 2 → 2.
- E1: completed → observed: attempts 10 → 10; utility 2.907% → 2.907%; conditional upper risk 56.818% → 56.818%; positive offers 44 → 44; positive dates 6 → 6.
- E3: completed → observed: attempts 10 → 10; utility 0.451% → 0.451%; conditional upper risk 62.500% → 62.500%; positive offers 16 → 16; positive dates 4 → 4.
- Ireland: completed → observed: attempts 10 → 10; utility 1.129% → 1.129%; conditional upper risk 8.805% → 8.805%; positive offers 159 → 159; positive dates 5 → 5.
- T-Mobile: completed → observed: attempts 10 → 10; utility 0.137% → 0.137%; conditional upper risk 58.140% → 58.140%; positive offers 43 → 43; positive dates 2 → 2.
- Verizon: completed → observed: attempts 10 → 10; utility 0.480% → 0.480%; conditional upper risk 45.238% → 45.238%; positive offers 42 → 42; positive dates 1 → 1.

## Recorded-feedback window sensitivity

For completeness, all six HistGBM cohorts at cap 40 are listed below. Actual costs differ across cohorts but remain identical across these window variants within a cohort. These are completed-response-clock policies with five-minute attempt spacing, not claims of improvement over every original baseline. Values are W10 → W20 → W40.

- AT&T: 40 attempts each; utility 2.528% → 1.689% → 3.707%; conditional upper risk 49.091% → 48.077% → 41.758%; positive offers 55 → 52 → 91.
- E1: 39 attempts each; utility 2.205% → 3.354% → 2.928%; conditional upper risk 51.282% → 50.602% → 47.761%; positive offers 39 → 83 → 67.
- E3: 23 attempts each; utility 0.441% → 0.290% → 0.065%; conditional upper risk 60.000% → 54.545% → 50.000%; positive offers 15 → 11 → 4.
- Ireland: 19 attempts each; utility 1.162% → 1.129% → 1.173%; conditional upper risk 9.434% → 8.805% → 10.063%; positive offers 159 → 159 → 159.
- T-Mobile: 40 attempts each; utility 0.327% → 0.430% → 0.283%; conditional upper risk 54.930% → 48.889% → 47.692%; positive offers 71 → 90 → 65.
- Verizon: 40 attempts each; utility 0.732% → 0.059% → 0.009%; conditional upper risk 55.556% → 52.000% → 50.000%; positive offers 27 → 25 → 22.

The direction is cohort-specific: W20 improves both displayed metrics in E1 and T-Mobile, while W40 does so in AT&T and E1. E3 and Verizon lose substantial useful throughput as the window grows; Ireland shows a small utility/risk trade-off. These operating points are exploratory illustrations, not a policy-selection rule or evidence of acceptable absolute risk. In particular, many positive-conditional upper bounds remain far above 10%.

## Window sensitivity and reference policies

- completed_W10 versus MARUR: trade-off or risk-only change: 52; unmatched cost: 42; unchanged: 30; utility loss without lower risk bound: 22; utility gain without higher risk bound: 22.
- completed_W20 versus completed_W10: trade-off or risk-only change: 79; utility loss without lower risk bound: 52; utility gain without higher risk bound: 20; unchanged: 17.
- completed_W40 versus completed_W10: trade-off or risk-only change: 90; utility loss without lower risk bound: 37; utility gain without higher risk bound: 24; unchanged: 17.
- observed_W10 versus ACI: unmatched cost: 84; utility gain without higher risk bound: 35; trade-off or risk-only change: 34; utility loss without lower risk bound: 15.
- observed_W10 versus Early: trade-off or risk-only change: 66; utility gain without higher risk bound: 43; unmatched cost: 38; utility loss without lower risk bound: 14; unchanged: 7.
- observed_W10 versus Frozen: unmatched cost: 168.
- observed_W10 versus MARUR: trade-off or risk-only change: 57; unmatched cost: 38; unchanged: 30; utility gain without higher risk bound: 22; utility loss without lower risk bound: 21.
- observed_W10 versus Periodic: unmatched cost: 84; trade-off or risk-only change: 33; utility gain without higher risk bound: 26; utility loss without lower risk bound: 19; unchanged: 6.
- observed_W20 versus observed_W10: trade-off or risk-only change: 78; utility loss without lower risk bound: 53; utility gain without higher risk bound: 21; unchanged: 16.
- observed_W40 versus observed_W10: trade-off or risk-only change: 84; utility loss without lower risk bound: 41; utility gain without higher risk bound: 27; unchanged: 16.

## Interpretation and limits

Changing the clock changes when calibration information is acquired, not the frozen forecast model. Failed responses still add conservative scores, so retries may reduce future commitments and consume attempts without adding measured labels. Successful observations can instead refresh the residual window. Longer windows alter both retained residuals and missing-pattern support; their effects cannot be attributed solely to a less extreme quantile. Natural recorded feedback and synthetic feedback stress must be interpreted separately.

At zero positive offers, conditional risk is undefined and cannot count as an improvement. Equal caps are not equal costs; all unmatched rows are retained and excluded from matched gain/loss counts. Synthetic masks hide feedback only: the evaluator still uses archived outcomes where known. Actual missing outcomes contribute unresolved risk bounds. Risk bounds are not confidence intervals, and no independence-based p-values are reported.

The new supported-Mbps-per-eligible metric is a conservative observed contribution: missing outcomes contribute no supported service in its numerator. The original utility fraction uses measured available throughput as its denominator. Neither should be described as measured live application benefit.

No controller is selected automatically from these test results. A prospective, frozen comparison is required before claiming a reliable improvement or a new methodological advance. See the separately written protocol for assumptions and the full metric list.

## Reproduction

`python scripts/run_marur_information_experiment.py` regenerates the exploratory ledgers; `python scripts/validate_marur_information_experiment.py` independently checks events, masks, costs and key metrics; `python scripts/report_marur_information_experiment.py` regenerates this report and its figure.
