# How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry

Md. Moazzem Hossain Majumder

## Abstract

We study whether a small chronological prefix of labeled sessions can calibrate a lower forecast of downlink throughput in two commercial measurement campaigns in Rome. The source-calibrated forecaster exceeds a nominal ten percent violation rate in all four held-out evaluations. At ten target labels the global correction meets the empirical target in each regime, but its supported fraction ranges from 0.006 to 0.073. Missingness-group calibration gives the same results at that budget. Replacing throughput-reset segments with segments beginning at active transitions substantially changes the endpoint distribution and measured violations. On a separate Irish next-row benchmark, calibrated persistence raised supported throughput from 55.60 to 59.44 percent with mean violations of 9.71 percent. Under joint campaign and operator shift in Rome, persistence violated 20.39 percent of forecasts. The small number of held-out collection dates limits inference about future deployments.

# Question and related work

An application that chooses a sending rate before a download needs to know how often its forecast exceeds delivered throughput and how much usable rate it gives up to reduce those violations. We ask how those quantities change when an operator has only a few labeled examples from the destination network. The contribution is an empirical comparison on released traces, with a common predictor and a fixed test suffix across label budgets. Prior work characterizes the underlying campaigns (Kousias et al. 2024; Caso et al. 2024), additive prediction with missing observations (Jacobson et al. 2025), and conditional calibration under missing covariates (Zaffran et al. 2023). The BAMMO-inspired baseline uses our pattern-specific boosted trees. We did not replicate the original authors’ implementation. Grouping by recorded telemetry availability gives a simple comparator. Its interpretation depends on support within each group.

# Measurements and prediction time

The earlier campaign uses the active throughput CSV in Zenodo 8224890. We take the last available mean download throughput at a DQA completion marker within a campaign and convert kb/s to Mbps. In the later active archive (Zenodo 14073311), we use 43 Ookla traces and process each operator’s nonnegative numeric mean-download series separately, converting its documented column units to Mbps. With reset segmentation the releases yield 1,132 operational sessions and 1,001 eligible forecast pairs across development and evaluation. The main evaluation uses only held-out suffixes. Each forecast uses the preceding result, elapsed time since that segment ended, its duration, recent radio measurements and availability indicators, and scenario. Among the 1,001 eligible pairs, 585 have only LTE measurements and 416 have both LTE and NR. No eligible pair lacks LTE. Consequently, grouping by NR presence and grouping by the two radio indicators define the same partition in this sample. In the later archive, the first throughput reading triggering a reset identifies the prediction time retrospectively. An online deployment would need an independent test-start signal. Even when predictors exclude that reading, selecting forecast times from the outcome trajectory can change the evaluated population. The primary protocol allows up to 60 seconds of lag age. Missing indicators describe what the logger observed. A missing NR signal by itself cannot identify a particular network state or its cause. Lagged throughput requires feedback from completed tests throughout evaluation. A budget of zero refers only to target labels used to fit the calibration offset.

E0 uses five successive blocks of earlier Op1 collection days for training, validation, source calibration, target prefixes and testing. The first three blocks contribute 57, 9 and 33 observations. The benchmark freezes that predictor and source offset for all four regimes. E1 moves to later Op1, E2 to earlier Op2 and E3 to later Op2. Transfer calibration and test blocks use the first approximately 40 percent and last approximately 60 percent of target days, respectively, with integer day boundaries. We take the first $`K`$ eligible sessions in timestamp order from the calibration pool. E0 has ten available, so its fifteen-session comparison is unavailable. Cross-operator analysis on contemporaneous campaigns is retrospective.

# Calibration and metrics

Let $`f`$ denote the frozen histogram gradient boosting model and $`y`$ the endpoint throughput. Split calibration orders the signed scores $`f(x_i)-y_i`$. For $`n`$ finite scores, take rank $`r=\lceil(n+1)(1-\alpha)\rceil`$ in ascending order. When $`r>n`$ we use positive infinity. The lower forecast is $`L=\max(0,f(x)-q)`$. A tie at the bound counts as covered. Since $`r\le n`$ is equivalent to $`(n+1)(1-\alpha)\le n`$, finite scores yield a finite selected order statistic exactly when $`n\geq\lceil1/\alpha\rceil-1`$. At $`\alpha=0.10`$ the first finite rank occurs at nine scores and selects their maximum. Ten also selects the maximum. This calculation gives no estimate of the campaign size needed for a useful rate. The rank argument follows the standard conformal construction (Vovk et al. 2005). Under exchangeability of calibration and future scores conditional on an independently fitted predictor, the rank construction yields marginal coverage of at least $`1-\alpha`$. The data do not establish this assumption across consecutive sessions, dates or networks. With an infinite target quantile the benchmark uses a frozen source offset. Its target-domain coverage is empirical. The grouped rules try a finite group offset, then a finite pooled target offset, then the source offset. The row gate is three and the session gate one. A group still needs enough scores for a finite rank. The RAT proxy groups by recorded NR presence. The missingness rule also uses LTE availability.

We compute $`V=\sum_i\mathbf{1}\{y_i<L_i\}/N`$ and $`U=\sum_i\min(L_i,y_i)/\sum_i y_i`$. A near-zero bound can yield few violations while providing little usable throughput. These are offline measures. The benchmark does not measure an application outage, a contractual breach or a revenue loss.

<div class="table*">

|                      |       |       |         |
|:---------------------|------:|------:|--------:|
| Model                |   MAE |  RMSE | Seconds |
| Persistence          |  3.22 |  7.21 |   0.000 |
| Ridge                |  6.03 |  8.78 |   0.046 |
| HistGradientBoosting | 11.00 | 12.00 |   0.041 |
| BAMMO                | 15.46 | 23.86 |   0.323 |
| QuantileGBM p10      |  5.01 |  8.68 |   0.072 |
| GPU ThroughputResNet |  5.85 |  8.33 |   0.737 |

</div>

<div class="table*">

|          |     |        |        |        |        |        |        |        |        |
|:---------|----:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| Regime/K |   N |     PV |     PU |     GV |     GU |     RV |     RU |     MV |     MU |
| E0K0     |  41 | 0.4390 | 0.3705 | 0.1220 | 0.1761 | 0.1220 | 0.1761 | 0.1220 | 0.1761 |
| E0K1     |  41 | 0.4390 | 0.3705 | 0.1220 | 0.1761 | 0.1220 | 0.1761 | 0.1220 | 0.1761 |
| E0K2     |  41 | 0.4390 | 0.3705 | 0.1220 | 0.1761 | 0.1220 | 0.1761 | 0.1220 | 0.1761 |
| E0K5     |  41 | 0.4390 | 0.3705 | 0.1220 | 0.1761 | 0.1220 | 0.1761 | 0.1220 | 0.1761 |
| E0K8     |  41 | 0.4390 | 0.3705 | 0.1220 | 0.1761 | 0.1220 | 0.1761 | 0.1220 | 0.1761 |
| E0K9     |  41 | 0.4390 | 0.3705 | 0.0976 | 0.0858 | 0.0976 | 0.0858 | 0.0976 | 0.0858 |
| E0K10    |  41 | 0.4390 | 0.3705 | 0.0000 | 0.0285 | 0.0000 | 0.0285 | 0.0000 | 0.0285 |
| E1K0     | 139 | 0.4101 | 0.4102 | 0.1655 | 0.1717 | 0.1655 | 0.1717 | 0.1655 | 0.1717 |
| E1K1     | 139 | 0.4101 | 0.4102 | 0.1655 | 0.1717 | 0.1655 | 0.1717 | 0.1655 | 0.1717 |
| E1K2     | 139 | 0.4101 | 0.4102 | 0.1655 | 0.1717 | 0.1655 | 0.1717 | 0.1655 | 0.1717 |
| E1K5     | 139 | 0.4101 | 0.4102 | 0.1655 | 0.1717 | 0.1655 | 0.1717 | 0.1655 | 0.1717 |
| E1K8     | 139 | 0.4101 | 0.4102 | 0.1655 | 0.1717 | 0.1655 | 0.1717 | 0.1655 | 0.1717 |
| E1K9     | 139 | 0.4101 | 0.4102 | 0.0719 | 0.0725 | 0.0719 | 0.0725 | 0.0719 | 0.0725 |
| E1K10    | 139 | 0.4101 | 0.4102 | 0.0719 | 0.0725 | 0.0719 | 0.0725 | 0.0719 | 0.0725 |
| E1K15    | 139 | 0.4101 | 0.4102 | 0.0719 | 0.0725 | 0.1007 | 0.0833 | 0.1007 | 0.0833 |
| E2K0     | 256 | 0.6211 | 0.4232 | 0.1641 | 0.1888 | 0.1641 | 0.1888 | 0.1641 | 0.1888 |
| E2K1     | 256 | 0.6211 | 0.4232 | 0.1641 | 0.1888 | 0.1641 | 0.1888 | 0.1641 | 0.1888 |
| E2K2     | 256 | 0.6211 | 0.4232 | 0.1641 | 0.1888 | 0.1641 | 0.1888 | 0.1641 | 0.1888 |
| E2K5     | 256 | 0.6211 | 0.4232 | 0.1641 | 0.1888 | 0.1641 | 0.1888 | 0.1641 | 0.1888 |
| E2K8     | 256 | 0.6211 | 0.4232 | 0.1641 | 0.1888 | 0.1641 | 0.1888 | 0.1641 | 0.1888 |
| E2K9     | 256 | 0.6211 | 0.4232 | 0.0234 | 0.0177 | 0.0234 | 0.0177 | 0.0234 | 0.0177 |
| E2K10    | 256 | 0.6211 | 0.4232 | 0.0234 | 0.0177 | 0.0234 | 0.0177 | 0.0234 | 0.0177 |
| E2K15    | 256 | 0.6211 | 0.4232 | 0.0234 | 0.0177 | 0.0977 | 0.0993 | 0.0977 | 0.0993 |
| E3K0     | 103 | 0.3301 | 0.3527 | 0.1262 | 0.1451 | 0.1262 | 0.1451 | 0.1262 | 0.1451 |
| E3K1     | 103 | 0.3301 | 0.3527 | 0.1262 | 0.1451 | 0.1262 | 0.1451 | 0.1262 | 0.1451 |
| E3K2     | 103 | 0.3301 | 0.3527 | 0.1262 | 0.1451 | 0.1262 | 0.1451 | 0.1262 | 0.1451 |
| E3K5     | 103 | 0.3301 | 0.3527 | 0.1262 | 0.1451 | 0.1262 | 0.1451 | 0.1262 | 0.1451 |
| E3K8     | 103 | 0.3301 | 0.3527 | 0.1262 | 0.1451 | 0.1262 | 0.1451 | 0.1262 | 0.1451 |
| E3K9     | 103 | 0.3301 | 0.3527 | 0.0291 | 0.0578 | 0.0291 | 0.0578 | 0.0291 | 0.0578 |
| E3K10    | 103 | 0.3301 | 0.3527 | 0.0000 | 0.0060 | 0.0000 | 0.0060 | 0.0000 | 0.0060 |
| E3K15    | 103 | 0.3301 | 0.3527 | 0.0000 | 0.0060 | 0.0000 | 0.0060 | 0.0000 | 0.0060 |

</div>

# Results

Persistence had a lower validation MAE than the histogram model on nine source-validation observations. We use the common histogram predictor to isolate differences between calibration rules. We examine persistence separately on the external benchmark and in the joint-shift analysis below. The point baseline exceeds the measured throughput in roughly one third to three fifths of held-out sessions. With source calibration, every regime exceeds ten percent violations at each tested budget below nine. At ten labels the global method records zero violations in E0 and E3, approximately seven percent in E1 and two percent in E2. In E3 it supports less than one percent of measured rate. At fifteen labels the grouped E1 rule exceeds the nominal target (0.1007), while grouped E2 increases supported fraction to 0.0993 with a violation rate of 0.0977. All four regimes give identical global and missingness-group results at ten labels when the pooled fallback is applied consistently. Thus this comparison provides no evidence of a grouping advantage at that budget. Prefix composition and endpoint construction both matter when interpreting apparent reliability.

<figure data-latex-placement="!ht">
<embed src="figures/fig1_budget_vs_usefulness.png" />
<figcaption>Performance across chronological calibration budgets. The same suffix is used at every available budget within a regime.</figcaption>
</figure>

<figure data-latex-placement="!ht">
<embed src="figures/fig2_subgroup_and_tradeoff.png" />
<figcaption>Subgroup performance and the empirical rate trade-off on the observed campaigns.</figcaption>
</figure>

# Sensitivity to the observational unit

After numeric filtering, reset starts a segment on a drop exceeding 5 Mbps to below 5 Mbps. Relative drop starts on a drop exceeding 2 Mbps to below 1 Mbps. The active-start rule begins on an upward crossing above 1 Mbps or a gap over ten seconds. All three retain the last numeric row as the target. The active-start rule therefore frequently attaches the subsequent idle tail to the preceding burst. Its endpoint can differ even on a continuously logged trace. We retain it as a negative control for changing the observational unit. The sensitivity analysis evaluates all eligible later pairs with a source-fitted model. Its denominator differs from the held-out benchmark. After excluding zero endpoints from scoring while keeping the fitted predictor, burst violations remain 0.3742 and 0.4651 on the two operators. Thus zero endpoints explain only part of the shift. Relative drop also changes the sample and the rates. None of these heuristics establishes ground-truth session boundaries.

<div class="table*">

|          |          |       |        |        |
|:---------|---------:|------:|-------:|-------:|
| Boundary | Segments | Zeros |    E1V |    E3V |
| Reset    |      584 |    23 | 0.1479 | 0.2523 |
| Drop     |      712 |    23 | 0.1339 | 0.2172 |
| Burst    |      930 |   183 | 0.4024 | 0.4918 |

</div>

# Uncertainty and secondary experiments

We resample collection dates with replacement, retaining all sessions from each selected date and pairing methods within each draw. The percentile endpoints from 2,000 draws describe empirical between-date variability conditional on this fitted model and prefix. Two to eight observed dates per regime offer little information about the population of future dates. A zero contrast interval follows algebraically when bounds coincide. Shared routes, equipment and measurement schedules can induce dependence across dates.

<div class="table*">

|          |      |        |        |        |        |        |        |
|:---------|-----:|-------:|-------:|-------:|-------:|-------:|-------:|
| Contrast | Days |     dV |    Vlo |    Vhi |     dU |    Ulo |    Uhi |
| E0D      |    2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| E1D      |    7 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| E2D      |    8 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| E3D      |    7 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

</div>

The repository includes every date’s estimates and leave-one-date-out contrasts. Single-prefix testing leaves calibration-prefix variability unmeasured. Thirty-, sixty- and 120-second sensitivity runs change the eligible cohort and covariates together. Sixty seconds is the selected primary window. The supplementary analyses also examine group-support gates and artificial removal of observed NR fields. Artificial removal tests model response to controlled masking and does not identify why telemetry was absent in the field.

The online experiment updates an offset after each observed label with a fixed step size. Its feedback requirements differ from static prefix calibration. This score-offset update is inspired by adaptive conformal inference (Gibbs and Candès 2021). The weighted experiment estimates source-to-target density ratios with a domain classifier and compares two clipping ranges. One variant uses calibration-pool covariates and the other uses unlabeled test covariates. The tight weight range is 0.1 to 10 and the wide range 0.01 to 100. Covariate-shift theory requires a stable conditional outcome law and appropriate density ratios (Tibshirani et al. 2019). Estimated, clipped weights and small effective sample sizes limit this interpretation. The alpha sweep and convex offline cost proxy show how the chosen threshold or penalty affects the displayed trade-off. The secondary sensitivity fits can use regime-specific source splits and should be compared within their own protocols.

<figure data-latex-placement="!ht">
<embed src="figures/fig3_aci_adaptation.png" />
<figcaption>Offset trajectory as labeled test sessions arrive in the online experiment.</figcaption>
</figure>

<figure data-latex-placement="!ht">
<embed src="figures/fig4_pareto_frontier.png" />
<figcaption>Observed violations and supported throughput at the tested nominal levels.</figcaption>
</figure>

<figure data-latex-placement="!ht">
<embed src="figures/fig5_sla_cost_curve.png" />
<figcaption>Offline loss under alternative weights on violations and unsupported throughput.</figcaption>
</figure>

<div class="table*">

|          |           |           |
|:---------|----------:|----------:|
| Protocol | Violation | Supported |
| E0Online |    0.1220 |    0.1762 |
| E1Online |    0.1583 |    0.1653 |
| E2Online |    0.1562 |    0.1775 |
| E3Online |    0.1262 |    0.1447 |
| E1Atight |    0.0072 |    0.0127 |
| E1Awide  |    0.0288 |    0.0450 |
| E1Btight |    0.0144 |    0.0063 |
| E1Bwide  |    0.0000 |    0.0003 |
| E2Atight |    0.0156 |    0.0304 |
| E2Awide  |    0.0156 |    0.0295 |
| E2Btight |    0.0469 |    0.0791 |
| E2Bwide  |    0.0664 |    0.1130 |
| E3Atight |    0.0097 |    0.0159 |
| E3Awide  |    0.0097 |    0.0083 |
| E3Btight |    0.0000 |    0.0096 |
| E3Bwide  |    0.0000 |    0.0085 |

</div>

# External comparison and the value of a previous measurement

We reproduced Sirhan’s global one-sided forecast on the Irish 5G traces of Raca et al. (Sirhan 2026; Raca et al. 2020). Each of 30 splits assigns whole traces to training, calibration and testing. We retained the released features, predictor training and signed-error calibration. For target row $`t+1`$, persistence uses the downlink measurement at $`t-1`$, the latest throughput feature available to the tree. A second candidate takes the smaller of that lag and the nonnegative tree estimate before calibration. The Rome experiments informed the candidate choice before its Irish evaluation.

The published frontier chooses among twenty nominal levels using the realized test violations. Table VI averages the best supported fractions over feasible splits for each method. At ten percent, 29 splits were feasible for the global rule and all 30 for persistence and the minimum. The paired persistence gain was 3.58 percentage points on the 29 jointly feasible splits. The minimum lost 3.83 points on the corresponding comparison with global.

<div class="table*">

|        |           |       |         |             |      |       |
|:-------|----------:|------:|--------:|------------:|-----:|------:|
| Budget | Published | Rerun | Minimum | Persistence | Gain |  Wins |
| 2      |      33.1 | 33.22 |   32.48 |       34.25 | 1.05 | 13/24 |
| 5      |      47.2 | 47.14 |   45.27 |       49.73 | 2.58 | 22/28 |
| 10     |      56.9 | 56.98 |   53.30 |       60.54 | 3.58 | 27/29 |

</div>

At a fixed nominal level of 0.10, all splits contribute. Persistence increased mean supported throughput from 55.60 to 59.44 percent and mean violations from 9.60 to 9.71 percent. Each rule met the ten percent target on 18 of 30 splits. The minimum reduced mean supported throughput to 52.81 percent.

<div class="table*">

|             |       |       |        |
|:------------|------:|------:|-------:|
| Predictor   | MeanV | MeanU | Passes |
| Global      |  9.60 | 55.60 |     18 |
| Minimum     |  9.72 | 52.81 |     17 |
| Persistence |  9.71 | 59.44 |     18 |

</div>

We kept each fitted forecast and calibration offset fixed and omitted traces only from test scoring. After dropping any one trace from every split in which it appeared, the mean paired gain ranged from 3.53 to 4.64 percentage points. Separately, we averaged each trace’s utility difference over its test appearances. Persistence improved 79 of 83 traces, with a median gain of 5.04 points. The five largest download traces contributed 54.4 percent of the sum of measured rates across unique rows. Removing those traces raised the gain to 6.81 points. Removing all 21 download traces left 62 streaming traces and a gain of 10.96 points, alongside a higher violation rate than the tree. These sensitivity estimates reuse overlapping partitions of the same recordings.

<div class="table*">

|               |         |       |      |       |      |
|:--------------|--------:|------:|-----:|------:|-----:|
| Sample        | Omitted |  Gain | Wins | TreeV | LagV |
| All           |       0 |  3.84 |   27 |  9.60 | 9.71 |
| OmitTop5      |       5 |  6.81 |   29 |  5.89 | 7.14 |
| OmitDownloads |      21 | 10.96 |   30 |  2.90 | 4.86 |

</div>

Table IX compares recorded throughput transitions. NearZero counts endpoints at or below 0.001 Mbps. Fall and Rise count changes of at least 10 Mbps from the available lag in the indicated direction. NearZero can overlap Fall. A near-zero measurement does not identify an application stall. In Ireland the lag had a 6.59 Mbps mean absolute error. In the Rome joint shift (E3) it had a 35.44 Mbps error and 40.8 percent of endpoints fell at least 10 Mbps below the lag. On the first ten calibration sessions in E3, persistence supported 51.65 percent with 20.39 percent violations. The tree supported 0.60 percent with zero violations. With the same held-out suffix and eleven disjoint ten-label calibration blocks, persistence met the violation target zero times and the tree eleven times. The higher frequency of large downward changes is consistent with a riskier lag-based lower bound. Forecast horizon, endpoint construction, traffic mix and collection conditions differ together across the two datasets, so this comparison cannot isolate a cause.

<div class="table*">

|         |        |         |          |        |          |      |      |
|:--------|-------:|--------:|---------:|-------:|---------:|-----:|-----:|
| Setting |  Pairs | Pearson | Spearman | LagMAE | NearZero | Fall | Rise |
| Ireland | 188545 |    0.77 |     0.67 |   6.59 |     45.0 |  5.8 |  6.3 |
| E0      |     41 |    0.29 |     0.41 |  35.14 |      0.0 | 22.0 | 22.0 |
| E1      |    139 |    0.52 |     0.57 |  32.69 |      7.2 | 37.4 | 14.4 |
| E2      |    256 |    0.70 |     0.61 |  17.57 |      2.0 | 19.1 | 16.0 |
| E3      |    103 |    0.49 |     0.55 |  35.44 |      1.0 | 40.8 | 24.3 |

</div>

# Conclusion

A short prefix produced conservative lower forecasts in these traces, sometimes at the cost of nearly all usable throughput. The first finite target rank at nine labels is specific to the chosen nominal level. The burst-endpoint diagnostic and sparse calendar-day support limit generalization. Independent measurement dates, externally identified test boundaries and an untouched network would permit a stronger test of calibration usefulness.

<div id="refs" class="references csl-bib-body hanging-indent">

<div id="ref-caso2024chronicles" class="csl-entry">

Caso, Giuseppe, Mohammad Rajiullah, Konstantinos Kousias, et al. 2024. “The Chronicles of 5G Non-Standalone: An Empirical Analysis of Performance and Service Evolution.” *IEEE Open Journal of the Communications Society* 5: 7380–99. <https://doi.org/10.1109/OJCOMS.2024.3499370>.

</div>

<div id="ref-gibbs2021adaptive" class="csl-entry">

Gibbs, Isaac, and Emmanuel Candès. 2021. “Adaptive Conformal Inference Under Distribution Shift.” *Advances in Neural Information Processing Systems (NeurIPS)* 34: 1660–72.

</div>

<div id="ref-jacobson2025predicting" class="csl-entry">

Jacobson, Tate, Jie Ding, and Hui Zou. 2025. “Predicting 5G Throughput with BAMMO, a Boosted Additive Model for Data with Missing Observations.” *Journal of the Royal Statistical Society Series C: Applied Statistics* 74 (1): 249–73. <https://doi.org/10.1093/jrsssc/qlae054>.

</div>

<div id="ref-kousias2024large" class="csl-entry">

Kousias, Konstantinos, Mohammad Rajiullah, Giuseppe Caso, et al. 2024. “A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements.” *IEEE Communications Magazine* 62 (5): 44–49. <https://doi.org/10.1109/MCOM.011.2200707>.

</div>

<div id="ref-raca2020beyond" class="csl-entry">

Raca, Darijo, Dylan Leahy, Cormac J. Sreenan, and Jason J. Quinlan. 2020. “Beyond Throughput, the Next Generation: A 5G Dataset with Channel and Context Metrics.” *Proceedings of the 11th ACM Multimedia Systems Conference (MMSys)*, 303–8. <https://doi.org/10.1145/3339825.3394938>.

</div>

<div id="ref-sirhan2026handover" class="csl-entry">

Sirhan, N. N. 2026. “Handover-Aware Conformal Throughput Intervals for Risk-Sensitive Rate Selection in Mobile 5G.” *Network* 6 (4): 92. <https://doi.org/10.3390/network6040092>.

</div>

<div id="ref-tibshirani2019conformal" class="csl-entry">

Tibshirani, Ryan J., Rina Foygel Barber, Emmanuel Candès, and Aaditya Ramdas. 2019. “Conformal Prediction Under Covariate Shift.” *Advances in Neural Information Processing Systems (NeurIPS)* 32: 2530–40.

</div>

<div id="ref-vovk2005algorithmic" class="csl-entry">

Vovk, Vladimir, Alex Gammerman, and Glenn Shafer. 2005. *Algorithmic Learning in a Random World*. Springer.

</div>

<div id="ref-zaffran2023conformal" class="csl-entry">

Zaffran, Margaux, Aymeric Dieuleveut, Julie Josse, and Yaniv Romano. 2023. “Conformal Prediction with Missing Values.” *Proceedings of the 40th International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 202: 40578–604.

</div>

</div>
