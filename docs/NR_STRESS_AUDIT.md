# Simulated loss of the NR telemetry feed

How sensitive are the frozen tree's issued commitments to losing its NR signal measurements? This replay intervenes only on the information delivered to the predictor. The recorded issue times, LTE fields, historical throughput and future outcome ledger stay fixed. It represents a telemetry failure. Physical removal of 5G service could alter throughput and requires separate evidence.

## Design and reproduction

From the repository root, generate the matched clock benchmark with `python scripts/clock_frontier.py`, then run `python scripts/stress_clock_radio.py` and `python -m pytest tests/unit/test_clock_radio.py -q`. The stress script refits the original Rome Op1 HistGBM on its 57 training sessions, verifies its predictions against the stored clock ticks, and uses the first ten labeled target calibration ticks per operator. The fixed global prediction-minus-outcome offsets are 15.364004 Mbps in E1 and 31.054314 Mbps in E3. All rates are clipped at zero after offset subtraction.

The Rome E1 test dates in 2023 are May 9 and 27, June 8, 10, 16 and 25, and July 5. E3 test dates are May 27, June 8, 10, 16 and 25, and July 4 and 5. E1 issued 238 forecasts with 211 observed targets and 95 issues eligible for NR removal. E3 issued 171 forecasts with 152 observed targets and 63 eligible issues. A mask clears SS-RSRP, SS-RSRQ and SS-SINR and rebuilds the NR and radio-group indicators. No mask adds unavailable measurements.

- Random masking uses Bernoulli probability 0.25 at eligible issues and NumPy seeds 0 through 19.
- Periodic masking removes eligible issues at minutes divisible by four. Burst masking removes the first two minutes of each eight-minute cycle. The two-minute duration is the median of eight bounded calibration runs of missing NR, pooled across operators and completed by the first test issue of either operator. Runs cannot cross gaps, trace boundaries, or unobserved block edges. The cycle and phase are design choices.
- Weak-signal masking uses the operator's calibration lower quartile of observed SS-RSRP, at or below −107.25 dBm for E1 and −109.25 dBm for E3. Realized mask counts differ between designs.
- At each eligible issue, the minimum-rate and maximum-rate rules compare the two possible commitments with the feed present or removed. They use no future target. Their extrema bound every binary whole-feed mask for this frozen rule on these ticks. They place no bounds on individual-field corruption or physical network changes.

## Matched results

U is the sum of the smaller of the commitment and the observed target divided by the sum of observed targets. For each scenario, the all-issued violation fraction lies between measured violations divided by issued forecasts and measured violations plus missing-target positive commitments divided by issued forecasts. These intervals allow any nonnegative missing throughput. They describe the finite ledger.

| Operator | Mask | Additional masks | Measured violations | All-issued violation range (%) | Measured U (%) |
|---|---|---:|---:|---:|---:|
| E1 | Recorded | 0 | 67 | 28.15–31.51 | 7.154 |
| E1 | Periodic | 21 | 55 | 23.11–26.47 | 5.929 |
| E1 | Burst | 18 | 60 | 25.21–28.57 | 5.776 |
| E1 | Weak signal | 33 | 48 | 20.17–23.53 | 4.758 |
| E1 | Minimum rate | 95 | 21 | 8.82–11.34 | 1.488 |
| E1 | Maximum rate | 0 | 67 | 28.15–31.51 | 7.154 |
| E3 | Recorded | 0 | 2 | 1.17–1.17 | 0.0650 |
| E3 | Periodic | 12 | 2 | 1.17–1.17 | 0.0650 |
| E3 | Burst | 12 | 2 | 1.17–1.17 | 0.0650 |
| E3 | Weak signal | 3 | 2 | 1.17–1.17 | 0.0650 |
| E3 | Minimum rate | 3 | 0 | 0–0 | 0 |
| E3 | Maximum rate | 0 | 2 | 1.17–1.17 | 0.0650 |

Across the twenty random masks, E1 loses 17–33 additional NR readings, with 48–60 measured violations and U of 5.033–6.382%. E3 loses 8–21 readings, with 0–2 measured violations and U of 0.0000103–0.0650%. These are ranges over simulated masks on the same dates. Each deterministic E3 schedule leaves the measured U unchanged except the minimum-rate rule, which removes the three positive commitments. E1's apparent safety gain under masking accompanies a loss in the share of measured throughput delivered. No recorded E1 or E3 commitment increases when NR is removed.

## Verification and limits

The three unit tests passed, including a regression check for overlapping operator calendars. An independent keyed comparison of the recorded scenario to `results/clock_histgbm/issued_k10.csv` matched all 409 predictions, commitments and targets, including missing outcomes. Recomputing counts, U, violation bounds and checking the minimum/maximum ordering from all 10,634 forecast rows agreed with all 52 summaries. The reproduced `results/clock_histgbm/simulated_nr_forecasts.csv.gz` SHA-256 is `19c39aa4232c6b0d18bc17039ccab1411c3d12d3e0ab828046ef21a3388d016a`. The companion `simulated_nr_metrics.csv` SHA-256 is `fdca88d8d1be3d9240e4362b17c04e7e2e39cf429264021806705a60906a3ddb`.

Eight interior runs offer limited information about outage lengths. The burst duration uses all preceding calibration telemetry, whereas fitting the rate offset uses ten target labels. The weak-signal scenario assumes an observer can see the issue-time signal before suppressing the feed. Natural missingness, missing outcomes, correlated LTE failures and model adaptation to persistent loss remain open. Persistence uses no NR fields and hence issues the same commitments throughout.
