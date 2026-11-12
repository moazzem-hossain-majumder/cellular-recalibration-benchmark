# What the frozen forecaster knew at each tick

Run `python scripts/clock_frontier.py` from the repository root after preparing the pinned Rome releases. This performs the source fit, clock replay, calibration, stress tests, per-date analysis and frontier plot. The results directory is results/clock_histgbm. The tree is the original 100-iteration, depth-five, learning-rate 0.05 histogram estimator with seed 42 fitted to 57 earlier Op1 training sessions. Its 33 source calibration rows are disjoint. Persistence has no fitted coefficients and uses these same source calibration dates for its own fallback.

Issue on whole-minute boundaries while the logger runs if the preceding minute has a valid rate. Use the last valid rate, elapsed time since it and span of the preceding minute's valid readings. The span is a proxy for the original completed-session duration. An explicit missing-duration sensitivity preserved the ten-label aggregate results. Take the latest value of each radio field in the preceding half-open minute. Encode scenario from the filename. The target is the last numeric rate in the following fully elapsed minute. A missing label or trace end leaves the issued commitment in the ledger. Twenty clock ticks outside the original calibration and test date blocks are flagged separately (18 E1, two E3). Both predictors share every in-scope key. The validator joins the historical clock replay on time and trace.

| Operator / predictor | Issued / scored / missing | Offset Mbps | Point MAE Mbps | Measured V / coverage (%) | Measured U (%) | Positive / missing positive | Issued V range (%) |
|---|---|---:|---:|---:|---:|---:|---:|
| E1 persistence | 238 / 211 / 27 | 114.00 | 44.35 | 8.06 / 91.94 | 8.29 | 23 / 1 | 7.14–7.56 |
| E1 frozen tree | 238 / 211 / 27 | 15.36 | 32.20 | 31.75 / 68.25 | 7.15 | 130 / 8 | 28.15–31.51 |
| E3 persistence | 171 / 152 / 19 | 53.90 | 50.72 | 13.82 / 86.18 | 16.00 | 37 / 1 | 12.28–12.87 |
| E3 frozen tree | 171 / 152 / 19 | 31.05 | 39.76 | 1.32 / 98.68 | 0.065 | 3 / 0 | 1.17–1.17 |

These are ten-label results. The E1 prefix contains eight LTE-only and two dual-radio rows. E3 contains ten dual rows. Global and grouped bounds coincide at ten. At every integer K through 178 or 254, frontier.csv records thresholds, positive predictions, errors, utility and risk ranges. Below nine labels the original finite source offset applies. nondominated.csv retains one representative per tied point on each policy's empirical scored frontier. It is computed after evaluation. No parameter was chosen from this envelope.

Among measured and missing E1 targets, respectively, preceding NR was available on 43.1% and 14.8% of ticks; for E3 the rates were 39.5% and 15.8%. Median prior rates were 2.20 versus 2.99 Mbps in E1 and 1.87 versus 2.03 Mbps in E3. Observed conditions differ; this cannot identify the missing throughput. The interval concerns possible nonnegative completions of the issued ledger. An absent physical service requires a different endpoint definition. No all-issued throughput ratio is estimated.
