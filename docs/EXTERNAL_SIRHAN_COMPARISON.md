# External comparison on the Irish 5G traces

We ran the one-sided 30-seed experiment from Sirhan’s archived code on the public Raca et al. traces. The candidate takes the smaller of nonnegative tree throughput and the published dl_lag1 feature, then fits the same signed-error calibration rule. Persistence uses that lag alone. The target is next-row downlink Mbps. For target row t+1, dl_lag1 is the observation at t−1, the most recent throughput feature given to the published tree. All methods use identical calibration and test traces within each split. The Rome results informed the choice of candidate; the Irish results were first evaluated after fixing that choice.

## Published one-sided frontier

Numbers below are percentages. For each seed the paper sweeps 20 nominal error levels from 0.01 to 0.20 and retains the largest supported fraction among settings satisfying the measured test violation budget. The mean excludes seeds without a feasible grid point. This is a retrospective frontier. Each method's feasible seed count is shown in parentheses.

| Budget | Published global | Rerun global | Minimum | Persistence | Paired minimum minus global (pp) | Minimum wins / jointly feasible |
|---:|---:|---:|---:|---:|---:|---:|
| 2% | 33.1 | 33.22 (24) | 32.48 (24) | 34.25 (25) | -0.74 | 8/24 |
| 5% | 47.2 | 47.14 (28) | 45.27 (28) | 49.73 (28) | -1.87 | 4/28 |
| 10% | 56.9 | 56.98 (29) | 53.30 (30) | 60.54 (30) | -3.83 | 2/29 |

The independent persistence comparison on jointly feasible splits is:

| Budget | Persistence minus global (pp) | Persistence wins / jointly feasible |
|---:|---:|---:|
| 2% | +1.05 | 13/24 |
| 5% | +2.58 | 22/28 |
| 10% | +3.58 | 27/29 |

## Fixed nominal error of 0.10

These settings are chosen before seeing test outcomes. Each seed uses its own calibration set. All 30 test splits contribute, including violations of the target.

| Method | Mean violation | Mean supported fraction | Splits meeting 10% |
|---|---:|---:|---:|
| global | 9.60% | 55.60% | 18/30 |
| minimum | 9.72% | 52.81% | 17/30 |
| persistence | 9.71% | 59.44% | 18/30 |

Seeds repartition the same 83 traces. Win counts describe paired split behavior and do not establish independence or population significance. This is an external test of the forecasting rule with the Irish paper’s feature and training protocol. It does not test a frozen Rome-trained model or a ten-session adaptation budget.

## Reproduction

Use the [Mendeley V1 analysis archive](https://data.mendeley.com/datasets/ncbdm2c36d/1) and [Raca et al. data](https://github.com/uccmisl/5Gdataset/tree/306d92eba81cb4f1195d8b8eba625666a02a10ec). Place the data ZIP in data/raw/ucc-external and run scripts/compare_sirhan_external.py with the analysis ZIP as its argument, then scripts/report_sirhan_external.py. The wrapper pins all three upstream source files and the data archive by SHA-256, relocates paths and inserts a scoring hook that shares the fitted predictions. The upstream global frontier and independently scored global frontier are checked on every seed and budget. See the [paper, Table 4](https://www.mdpi.com/2673-8732/6/4/92), results/exploratory/sirhan_external/run.json for software versions and the accompanying CSVs for all seed results.

## Influence at the fixed nominal level

Across 83 leave-one-trace-out scoring runs the gain ranged from 3.53 to 4.64 percentage points. Across individual traces, 79 had a positive mean gain and the median gain was 5.04 points.

Removing the five downloads with the largest sum of measured rates yielded a 6.81-point gain. Mean violations were 5.89% for the tree and 7.14% for persistence.

Removing all download traces yielded a 10.96-point gain. Mean violations were 2.90% for the tree and 4.86% for persistence.

The exclusions affect scoring only. Rebuild the trace totals with the archived rerun, then run scripts/audit_external_traces.py before generating this report.
