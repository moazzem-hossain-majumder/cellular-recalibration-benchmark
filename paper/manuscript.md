# When Does Recalibration Help Cellular Throughput Commitments? Accounting for Cost, Missingness, and Abstention

## Abstract

Calibration policies evaluated at the same nominal query cap can mislead through unequal probe spending, unobserved outcomes, and heavy abstention. Across 16 physical campaign-dates pooling retrospective multi-carrier archives, matched-cost supported-throughput differences between Missingness-Aware Recalibration under Uncertainty and Risk (MARUR) and periodic recalibration are statistically indistinguishable from zero. Across mobile cellular cohorts under frozen tree predictors, positive-offer upper violation risk averages roughly 17--63\%---far above nominal $\alpha=0.10$---while supported measured throughput remains only 1--3\% of observed rate. We establish an auditable empirical accounting framework separating realized probe attempts, finite-record missing-outcome risk intervals, selective offer decomposition $R=(M/N)R_+$, and physical cluster inference, benchmarking MARUR against Fixed-Period recalibration (Periodic) and Horizon-Paced Selective-Offer Conformal Control (PACER) across retrospective and held-out public archives. Exploratory sensitivity analyses across conformal windows, nominal error levels, and alternative source-only predictors confirm these trade-offs, while live prospective field trips remain absent.

<div class="IEEEkeywords">

Cellular throughput, calibration feedback, selective prediction, cluster inference, measurement methodology.

</div>

# Introduction

An application that commits to a minimum cellular throughput needs both useful delivered bandwidth and a tolerable rate of broken promises. Point forecast error, low all-issued average violations, and equal nominal recalibration budgets do not independently establish either property. Under sparse feedback, a calibration policy can appear safer simply by abstaining more often, avoiding expensive probes, front-loading its query budget before distribution shifts arrive, or omitting unmeasured horizon outcomes from its failure rate.

This paper asks a concrete empirical measurement question: *when does recalibration feedback help cellular throughput commitments, and how do unequal query cost, missing responses, and abstention make apparent gains misleading?* Rather than claiming a universally superior conformal controller, our central contribution is an auditable evaluation and accounting framework tested across six retrospective cellular cohorts and four held-out public archives. Specifically, we contribute:

1.  **Causal acquisition accounting:** An event-ledger methodology separating initial pre-test labels from charged new probes, unsuccessful horizon completions, residual-window admissions, and delayed availability for subsequent forecasts.

2.  **Selective-risk and missing-outcome bounds:** Exact finite-record bounds $`[e/M,(e+m)/M]`$ alongside the identity $`R = (M/N)R_+`$, demonstrating how all-issued reliability conceals conditional failure rates of roughly $`17`$–$`63\%`$ under heavy abstention.

3.  **Physical-cluster and matched-cost inference:** Pairing policies at equal realized probe expenditures over physical campaign-dates ($`G=16`$ retrospective dates; $`G=26`$ held-out dates), showing that large configuration grids ($`576`$–$`1{,}848`$ runs) do not multiply independent statistical evidence.

4.  **Honest comparator and bound auditing:** Benchmarking *Missingness-Aware Recalibration under Uncertainty and Risk* (MARUR) and *Horizon-Paced Selective-Offer Conformal Control* (PACER) against established baselines, alongside algebraic limits showing where sparse-budget guarantees become vacuous and where controllers should not be deployed.

All evaluations use retrospective and frozen held-out public archives; zero prospective live field trips have been collected, and all negative findings are retained.

# Related Work

## Cellular Measurement, Prediction, and Rate Decisions

Operational measurements establish that cellular throughput depends on radio conditions, mobility, and the collection regime. The channel/context dataset of Raca et al. (Raca et al. 2020) and the commercial mmWave measurements underlying Lumos5G (Narayanan et al. 2020) support context-aware prediction. More recent multi-technology measurements, longitudinal service analysis, and machine-learning modeling extend this evidence to evolving non-standalone networks (Kousias, Rajiullah, Caso, Ali, et al. 2024; Caso et al. 2024; Kousias, Rajiullah, Caso, Alay, et al. 2024). However, forecast counts within a shared route or campaign are temporally correlated rather than independent replications, and point error does not measure commitment violation risk.

Missing predictors and deployment constraints motivate complementary approaches. BAMMO incorporates missing covariates into additive boosting on commercial 5G data (Jacobson et al. 2025), addressing missing inputs rather than unsuccessful acquisition of future calibration outcomes. Real-time smartphone evaluations highlight sampling, labeling, and distribution shift (Raca et al. 2024), while multi-carrier experiments reveal conflicting histories that limit fine-grained accuracy (Basit et al. 2024). The closest work to our decision objective is Sirhan’s evaluation of global, regime-conditioned, and adaptive conformal throughput intervals (Sirhan 2026), which shows that mobility conditioning can aid two-sided intervals while a global one-sided bound performs competitively for rate selection. Neither work audits how unequal probe spending, unsuccessful responses, and heavy abstention interact across budgets and physical campaigns.

## Missingness, Adaptation, and Budgeted Feedback

Conformal calibration under missing covariates distinguishes marginal coverage from missingness-pattern conditioning (Zaffran et al. 2023). Covariate-shift weighting (Tibshirani et al. 2019) and non-exchangeable weighted conformal methods (Barber et al. 2023) establish bounds under structural assumptions that break under unrestricted temporal drift and outcome censoring. Time-series conformal methods (Zaffran et al. 2022; Xu and Xie 2023; Lin et al. 2022; Gibbs and Candès 2024), online level adaptation (Gibbs and Candès 2021; Bhatnagar et al. 2023; Angelopoulos et al. 2023; Anastasios Nikolas Angelopoulos et al. 2024; Podkopaev et al. 2024), and risk-controlling formulations (Bates et al. 2021; Anastasios N. Angelopoulos et al. 2024; Gibbs et al. 2025; Gauthier et al. 2026) establish strong full-feedback baselines, while selective classification (Geifman and El-Yaniv 2017) and stability critiques (Min et al. 2026) formalize the link between abstention and conditional error.

Budgeted and partial-feedback calibration has recently gained direct attention. Ilyas et al. (Ilyas et al. 2026) analyze upfront stopping rules for i.i.d. arrivals, Ge et al. (Ge et al. 2025) study stochastic semi-bandit feedback revealed by set inclusion, and Hou et al. (Hou et al. 2025) calibrate probabilistic solvers via sporadic edge–cloud feedback. Our empirical contribution bridges these threads inside real cellular logs by accounting jointly for charged measurement probes, failed responses, selective offer frequency $`R = (M/N)R_+`$, and physical collection-date dependence across established reactive (MARUR) and paced (PACER) comparators. Table I summarizes the closest related publications.

<div class="table*">

| **Work** | **Modality** | **Dataset or environment** | **Core method** | **Relevant limitation** | **Present study distinction** |
|:---|:---|:---|:---|:---|:---|
| BAMMO (Jacobson et al. 2025) | Radio/context | Commercial mmWave 5G | Missing-covariate additive boosting | Missing inputs differ from missing future outcomes | Separates input vs. feedback missingness |
| Raca et al. (Raca et al. 2024) | Smartphone telemetry | Live cellular video streaming | On-device throughput prediction | No selective commitment audit across caps | Retrospective ledger audit; no live-QoE claim |
| Basit et al. (Basit et al. 2024) | Rate histories/context | Multi-carrier LTE/5G driving | Fine-grained prediction feasibility | Conflicting samples limit point accuracy | Evaluates conditional risk and supported rate |
| Sirhan (Sirhan 2026) | Rate, RAT, handover | Commercial mobile 5G traces | Global/group/adaptive conformal rate bounds | Full-outcome split; no attempt-budget ledger | Tracks realized probe cost and unresolved labels |
| Zaffran et al. (Zaffran et al. 2023) | Incomplete covariates | Regression with missing inputs | Missing-pattern conformal calibration | Input patterns differ from failed label requests | Logs failed probes separately from buffer updates |
| Conformal PID (Angelopoulos et al. 2023) | Temporal scores | Forecasting time series | Online PID quantile control | Assumes full score feedback per step | Audits delayed and censored sparse probes |
| Ilyas et al. (Ilyas et al. 2026) | IID data arrivals | Upfront label stopping | Cost-efficient stopping rule | Stationary arrivals differ from mobile drift | Accounts seed vs. new probes over shifts |
| Ge et al. (Ge et al. 2025) | Sets and partial labels | Stochastic semi-bandit tasks | Online conformal regret analysis | Set-inclusion feedback differs from probe failure | Tracks maturation delay and probe attempts |
| Hou et al. (Hou et al. 2025) | Solver outputs | Edge–cloud linear systems | Sporadic-feedback calibration | Two-sided set size differs from SLA rate risk | One-sided throughput commitments and abstention |
| CRC (Anastasios N. Angelopoulos et al. 2024) | Scores and losses | Vision/language benchmarks | Expected monotone-loss control | Population guarantees differ from finite ledgers | Finite-record $`[e/M,(e+m)/M]`$ risk intervals |
| Min et al. (Min et al. 2026) | Predictive sets | Regression and classification | Coverage–length stability critique | Diagnostic rather than budgeted query ledger | Jointly tracks $`A`$, $`R_+`$, $`U`$, and query cost |
| Gauthier et al. (Gauthier et al. 2026) | Covariates and sets | Adaptive-coverage tasks | Learned coverage policies via e-values | Requires dedicated validity construction | Heuristic vs. finite-horizon comparators |
| **Present study** | **Rate and missing telemetry** | **Ten cohorts (42 campaign-dates)** | **Causal acquisition and selective-risk accounting** | **Retrospective archives; 0 live trips** | **Joint probe cost, missing bounds, $`R=(M/N)R_+`$, cluster inference** |

</div>

# Decision Process and Accounting Framework

## Scheduled Opportunities and Acquisition Ledger

At scheduled issue time $`t`$, a frozen source-trained predictor outputs point forecast $`p_t`$ using only telemetry and lagged throughput measured strictly before issue. The controller issues a nonnegative throughput commitment $`L_t \ge 0`$ and decides whether to request the future outcome $`y_t`$ over the measurement horizon (`ready` timestamp). All scheduled intervals enter the decision ledger; ticks lacking a valid prior rate are marked ineligible ($`L_t = 0`$).

Every policy begins with identical historical pre-test labels (ten complete initial calibration rows per cohort), whose prior physical acquisition attempts are unknown and accounted separately from new target queries $`Q_{\text{new}}`$. Each new feedback request is charged against budget $`C_{\text{new}}`$ at issue time, including queries whose responses arrive missing (unsuccessful), time out, or mature after the evaluation stream ends. The ledger logs five distinct quantities: issued requests $`Q_{\text{new}}`$, completed observed responses, failed responses, residuals admitted to the calibration buffer, and updates actually available before later issue times. Because raw lag-throughput monitoring and oracle evaluation labels remain outside the calibration query budget, fewer requested calibration labels do not establish physical energy or radio byte savings. Unmatched operating points where policies consume unequal realized queries are never interpolated into equal-cost claims.

## Abstention, Conditional Risk, and Supported Service

Across $`N`$ eligible opportunities, let $`M = \sum_{t} \mathbf{1}\{L_t > 0\}`$ denote positive commitments ($`A = M/N`$ the positive-offer frequency), $`e`$ observed violations ($`L_t > y_t`$), and $`m`$ positive commitments whose horizon outcomes $`y_t`$ are unobserved. Because throughput is nonnegative ($`y_t \ge 0`$) and zero commitments ($`L_t = 0`$) cannot violate, all-issued risk $`R`$ and positive-offer conditional risk $`R_+`$ satisfy
``` math
\begin{equation}
\begin{aligned}
R &= A \cdot R_+,\qquad R \in [e/N, (e+m)/N],\\
R_+ &\in [e/M, (e+m)/M]\qquad (M > 0).
\end{aligned}
\label{eq:risk_bounds}
\end{equation}
```
Here $`R_+^{\text{lo}} = e/M`$ and $`R_+^{\text{hi}} = (e+m)/M`$ are exact finite-record partial-identification bounds (Manski 1989) attained by setting unobserved outcomes to $`L_t`$ or $`0`$, respectively; they are neither asymptotic confidence intervals nor population guarantees. Whenever $`A`$ shrinks via abstention, $`R \le \alpha`$ permits conditional failure $`R_+ \approx \alpha / A \gg \alpha`$.

We measure delivered service via conditional supported-throughput fraction $`U = \sum_{t:y_t\text{ obs}}\min(L_t,y_t)/\sum_{t:y_t\text{ obs}}y_t`$ and observed supported Mbps per eligible tick. Both measure offline trace agreement rather than live application Quality of Experience (QoE). Reliable interpretation requires reporting $`(Q_{\text{new}}, A, [R_+^{\text{lo}}, R_+^{\text{hi}}], U)`$ alongside independent cluster counts.

## Evaluated Controllers and Baselines

We evaluate nine policy families under a common causal interface (Table II; implementation details and the MARUR-vs.-PACER decision taxonomy appear in Supplementary Table S14):

- **Static and nonadaptive baselines:** *Frozen* ($`C_{\text{new}}=0`$, initial 10 labels only), *Early* (queries every eligible tick until cap exhaustion), *Random* (pre-drawn uniform schedules over seeds $`\{42, 123, 2026\}`$), and *Periodic* (fixed spacing every $`P=15`$ ticks).

- **Online sparse-feedback comparators:** Adapted *ACI* (Gibbs and Candès 2021) ($`\eta=0.05`$, updating $`\alpha_t`$ conservatively on missing requested responses with $`L_t \le p_t`$) and *DecayingOGD* (Anastasios Nikolas Angelopoulos et al. 2024) (step exponent $`0.6`$). Neither retains full-feedback theoretical assumptions under delayed selective censoring.

- **MARUR (reactive comparator) and ablations:** Triggers probes on 60-minute response age or LTE/NR pattern switches, maintains a FIFO buffer ($`W=10`$) inserting conservative upper residual $`p_t`$ when missing, requires at least nine matching-pattern residuals for pattern quantiles (otherwise pooled), and abstains below three matching entries. Note failed responses still reset the cooldown clock even when an ablation drops missing scores.

- **PACER (paced comparator):** Formulated *after* inspecting MARUR failures on the retrospective cohorts, PACER divides a finite horizon $`T`$ into $`K = \min(C_{\text{new}}, T)`$ contiguous blocks, draws one uniform probe per block, excludes missing responses from an observed residual buffer ($`W_{\text{obs}}=20`$), updates its threshold $`a_k`$ only on positive offers via smooth interpolation/veto ($`a_{\text{veto}}=0.15`$), and freezes thresholds within each block.

<div class="table*">

|  |  |  |  |  |  |
|:---|:---|:---|:---|:---|:---|
| Policy | Trigger | Calibration | KeyParams | MissingRule | Rationale |
| Frozen | None (C=0) | Static Init10 | init=10 | None | Zero-cost anchor |
| Early | Every elig tick | FIFO W=10 | C=10/40 | Insert score=p | Day-1 exhaust |
| Random | Uniform seed | FIFO W=10 | seeds=42,123,2026 | Insert score=p | Nonadaptive |
| Periodic | Every P=15 ticks | FIFO W=10 | P=15, W=10 | Insert score=p | Fixed cadence |
| ACI | Every P=15 ticks | Online level a | eta=0.05, W=10 | err=1 on pos | Sparse ACI |
| DecayingOGD | Every P=15 ticks | Decaying step | exp=0.6 | score=p on miss | Decaying OGD |
| MARUR | Age 60m or RAT | Pat/Pool W=10 | age=60m, min=3 | Insert p + gate | Heuristic |
| MARUR ablat. | Age or Periodic | Pool/DropMiss | NoPat/NoGate/Drop | Drop or Periodic | Gate/miss check |
| PACER | Uniform K blk | Smooth sel W=20 | g=0.05, v=0.15 | Excl W; e=1 | Paced comparator |

</div>

# Retrospective Evaluation and Physical Cluster Inference

## Cohorts, Dependency Structure, and Predictor Choice

The retrospective benchmark spans six cohorts evaluated at 60-second causal intervals (Kousias, Rajiullah, Caso, Ali, et al. 2024; Caso et al. 2024; NUWiNS 2025; Raca et al. 2020): Rome *E1* (2023 Op1) and *E3* (2023 Op2), US Drive 3 (*AT&T*, *T-Mobile*, *Verizon*), and *Ireland* driving downloads. To avoid temporal or cross-carrier leakage across chronologically ordered partitions, all five retrospective splits of earliest Rome Op1 (Zenodo 8224890) reserve distinct calendar dates (35/10/15/15/25% of days), leaving exactly 57 causal training rows (two dates), 9 validation rows, and 33 source-calibration rows for the frozen Histogram Gradient Boosted Machine (*HistGBM*) predictor. While a 57-row fit exhibits high cross-domain point violation rates ($`57`$–$`79\%`$ across held-out suffixes), Section <a href="#sec:sensitivity" data-reference-type="ref" data-reference="sec:sensitivity">6</a> verifies that replacing it with a lower-MAE neural predictor trained on the same split (`ThroughputResNet`), a pinball quantile regressor, a 112-row clock-minute source tree, or raw lag *Persistence* leaves every accounting conclusion intact.

Critically, evaluating multiple carriers during the same drive (three carriers sharing US Drive 3; Op1 and Op2 sharing six of seven Rome collection dates) or running large parameter sweeps does not increase independent sample size. Pooling all six retrospective cohorts yields only three distinct geographic campaigns and $`G=16`$ physical campaign-dates: 8 Rome dates, 3 shared US dates, and 5 Irish driving dates spanning 11 traces.

## Matched-Cost Mechanisms, Conditional Risk, and Null Cluster Utility

Table III summarizes the six-cohort behavior at new-query cap $`C_{\text{new}}=40`$, showing that nominal cap equality hides disparate actual spending ($`16`$ vs. $`40`$ queries on E1; $`23`$ vs. $`20`$ on Ireland) and that conditional upper risk stays high ($`7.55\%`$–$`65.38\%`$) whenever offers occur. Across the full matched-cost audit ($`576`$ original runs, $`720`$ full-suffix replays, $`384`$ exact-cost pairs), apparent gains stem from distinct mechanisms rather than reliable calibration: on Rome E1 at $`10`$ queries, MARUR increases supported throughput over Periodic ($`2.907\%`$ vs. $`0.523\%`$) while raising all-issued upper risk ($`10.924\%`$ vs. $`6.303\%`$); on Ireland, both issue $`159`$ positive offers and MARUR removes $`14`$ observed violations by shrinking commitment magnitude, dropping support from $`4.117\%`$ to $`1.129\%`$; on Verizon, MARUR drops $`10`$ of Early’s offers rather than reducing failures on shared offers.

<div class="table*">

|          |          |         |        |        |         |       |
|:---------|---------:|--------:|-------:|-------:|--------:|------:|
| Cohort   |   Policy | Queries | Offers | PosLow | PosHigh |     U |
| E1       |   Frozen |       0 |    130 |  51.54 |   57.69 | 7.154 |
| E1       | Periodic |      16 |     33 |  42.42 |   51.52 | 1.008 |
| E1       |    MARUR |      40 |     29 |  44.83 |   44.83 | 2.025 |
| E3       |   Frozen |       0 |      3 |  66.67 |   66.67 | 0.065 |
| E3       | Periodic |      12 |     16 |  43.75 |   50.00 | 0.605 |
| E3       |    MARUR |      29 |     20 |  45.00 |   55.00 | 0.504 |
| ATT      |   Frozen |       0 |     57 |  38.60 |   38.60 | 2.252 |
| ATT      | Periodic |      20 |     30 |  23.33 |   23.33 | 0.402 |
| ATT      |    MARUR |      40 |    111 |  43.24 |   43.24 | 6.481 |
| T-Mobile |   Frozen |       0 |    236 |  52.12 |   52.12 | 1.254 |
| T-Mobile | Periodic |      20 |     47 |  55.32 |   55.32 | 0.141 |
| T-Mobile |    MARUR |      40 |     52 |  65.38 |   65.38 | 0.337 |
| Verizon  |   Frozen |       0 |      1 |   0.00 |    0.00 | 0.003 |
| Verizon  | Periodic |      20 |      5 |  20.00 |   20.00 | 0.006 |
| Verizon  |    MARUR |      40 |     21 |  61.90 |   61.90 | 0.597 |
| Ireland  |   Frozen |       0 |    159 |  27.04 |   29.56 | 7.740 |
| Ireland  | Periodic |      23 |    159 |  11.32 |   13.84 | 2.966 |
| Ireland  |    MARUR |      20 |    159 |   7.55 |   10.06 | 1.175 |

</div>

Clustering strictly at the $`G=16`$ physical campaign-dates under matched $`10`$-query cost (Table IV) resolves whether MARUR improves over Periodic: it does not. Pooled $`\Delta U`$ across the $`16`$ clusters is $`+0.21`$ percentage points (2,000-draw cluster bootstrap 95% CI $`-1.26`$ to $`+0.79`$), equal-campaign-date mean $`\Delta U`$ is $`-0.09`$ percentage points (95% $`t`$-interval $`-1.27`$ to $`+1.08`$), and all-issued upper risk shifts by $`+4.07`$ percentage points ($`-0.11`$ to $`+6.38`$). Five of six within-cohort intervals cross zero, MARUR spends all $`10`$ queries on Day 1 in E1, AT&T, T-Mobile, and Verizon (1/7–1/3 query days vs. Periodic’s 13/16 dates), and across Ireland’s 11 traces MARUR loses $`-2.99`$ percentage points pooled utility ($`-4.83`$ to $`-1.88`$) via offer shrinkage. Across all $`10`$ retrospective and held-out cohorts (Fig. 1), low all-issued risk routinely masks conditional violation rates of $`17`$–$`68\%`$ well above $`\alpha=0.10`$, while supported throughput typically remains $`1`$–$`3\%`$ on LTE/5G cohorts.

<div class="table*">

|                  |     |       |         |         |        |        |       |       |       |        |
|:-----------------|:----|:------|:--------|:--------|:-------|:-------|:------|:------|:------|:-------|
| Scope            | G   | QDays | PosDays | Pool dU | BootLo | BootHi | Eq dU | tLo   | tHi   | dRhi   |
| E1               | 7   | 1/3   | 6/6     | +2.38   | +0.76  | +3.70  | +1.45 | -0.01 | +2.90 | +4.62  |
| E3               | 7   | 3/7   | 5/2     | +0.66   | +0.03  | +1.80  | +0.78 | -0.45 | +2.02 | +9.94  |
| ATT              | 3   | 1/2   | 2/2     | +2.58   | +0.00  | +2.90  | +1.65 | -2.05 | +5.36 | +11.15 |
| T-Mobile         | 3   | 1/1   | 1/1     | -0.02   | -0.05  | +0.00  | -0.02 | -0.08 | +0.05 | +0.00  |
| Verizon          | 3   | 1/2   | 1/1     | +0.54   | +0.00  | +1.96  | +0.65 | -2.16 | +3.46 | +6.62  |
| Ireland          | 5   | 2/3   | 5/5     | -2.99   | -4.00  | -1.40  | -2.46 | -4.76 | -0.15 | -4.19  |
| All (16 Dates)   | 16  | 7/13  | 14/13   | +0.21   | -1.26  | +0.79  | -0.09 | -1.27 | +1.08 | +4.07  |
| Ireland (Traces) | 11  | 4/4   | 10/10   | -2.99   | -4.83  | -1.88  | -4.20 | -7.31 | -1.10 | -4.19  |

</div>

<figure id="fig:policy_summary" data-latex-placement="!t">
<embed src="figures/main_fig1_policy_summary.png" style="width:92.0%" />
<figcaption>Joint overview of (a) positive-offer frequency <span class="math inline"><em>A</em></span>, (b) positive-offer upper risk <span class="math inline"><em>R</em><sub>+</sub><sup>hi</sup></span> versus <span class="math inline"><em>α</em> = 10%</span>, and (c) supported measured throughput <span class="math inline"><em>U</em></span> across all 10 archived cohorts (6 retrospective R, 4 held-out public archives H) under frozen HistGBM and recorded feedback.</figcaption>
</figure>

# Held-Out Public Archives and Bound Audit

## Cohort-by-Cohort Performance and Pooling-Rule Sensitivity

We next evaluate all comparators on four held-out public archives not used during retrospective controller comparisons, with PACER’s configuration (`configs/pacer.json`) and SHA-256 checksums frozen before evaluation on the held-out archives (the authors had prior access to the public archives, and PACER was designed after diagnosing MARUR failures on the retrospective cohorts). These four held-out cohorts add $`26`$ physical campaign-dates: *Rome Capacity Op1* and *Op2* (sharing $`15`$ calendar dates merged into 15 physical `RomeCap` units), *Oslo Commute* ($`7`$ post-2011-01-30 dates (Riiser et al. 2013)), and *Ireland Static* ($`4`$ static-download dates excluded from driving evaluation), yielding $`42`$ pooled physical clusters across all $`10`$ cohorts.

<div class="table*">

|                     |     |       |       |       |       |      |       |      |        |       |
|:--------------------|----:|------:|------:|------:|------:|-----:|------:|-----:|-------:|------:|
| Cohort              | Cap | PerHi | MARHi | PACHi |  PerU | MARU |  PACU | PACA |    Exc |   Bnd |
| Ireland Static (4d) |  10 |  7.84 |  4.65 |  5.12 |  0.06 | 0.14 |  0.79 | 86.7 | -0.044 | 0.685 |
| Ireland Static (4d) |  40 |  8.14 |  4.65 |  6.98 |  0.55 | 0.14 |  3.42 | 86.7 |  0.010 | 0.192 |
| Oslo Commute (7d)   |  10 | 48.70 | 16.23 | 17.69 | 22.46 | 6.85 |  8.83 | 38.0 |  0.020 | 0.683 |
| Oslo Commute (7d)   |  40 | 20.68 | 25.62 | 32.40 | 13.05 | 9.70 | 13.86 | 57.2 |  0.078 | 0.178 |
| Rome Cap Op1 (15d)  |  10 | 46.91 | 44.09 | 52.38 |  1.17 | 1.80 |  1.41 | 17.8 |  0.097 | 0.691 |
| Rome Cap Op1 (15d)  |  40 | 47.19 | 45.76 | 62.96 |  1.30 | 1.89 |  0.55 |  7.6 |  0.038 | 0.182 |
| Rome Cap Op2 (15d)  |  10 | 47.37 | 61.54 | 56.10 |  1.01 | 2.17 |  2.04 | 23.0 |  0.112 | 0.691 |
| Rome Cap Op2 (15d)  |  40 | 53.62 | 45.90 | 47.62 |  1.25 | 1.62 |  0.55 |  5.9 |  0.024 | 0.182 |
| Retro Mean (6 coh.) |  10 | 43.24 | 44.90 | 49.26 |  0.92 | 1.45 |  1.05 | 15.5 |  0.064 | 0.699 |
| Retro Mean (6 coh.) |  40 | 35.67 | 46.74 | 47.81 |  0.85 | 1.85 |  0.94 | 12.3 |  0.037 | 0.184 |

</div>

<figure id="fig:pacer_breakdown" data-latex-placement="!t">
<embed src="figures/main_fig2_pacer_breakdown.png" style="width:88.0%" />
<figcaption>Per-cohort conditional upper risk <span class="math inline"><em>R</em><sub>+</sub><sup>hi</sup></span> comparing Periodic, MARUR, and PACER across held-out public archives and the 6-cohort retrospective mean at (a) <span class="math inline"><em>C</em><sub>new</sub> = 10</span> and (b) <span class="math inline"><em>C</em><sub>new</sub> = 40</span> (frozen HistGBM, recorded feedback). Improvements concentrate at Oslo Commute <span class="math inline"><em>C</em><sub>new</sub> = 10</span>, while PACER matches or trails Periodic in Rome Op1, Oslo <span class="math inline"><em>C</em><sub>new</sub> = 40</span>, and the retrospective mean.</figcaption>
</figure>

Table V and Fig. 2 reveal heterogeneous outcomes rather than uniform dominance. On Oslo Commute at $`C_{\text{new}}=10`$, PACER eliminates Periodic’s Day-1 over-committing ($`17.69\%`$ vs. $`48.70\%`$ upper risk) and keeps risk at $`5.12\%`$–$`6.98\%`$ on quasi-stationary Ireland Static. However, PACER performs worse than or similar to Periodic across most mobile cells: Rome Capacity Op1 ($`52.38\%`$ vs. $`46.91\%`$ at cap 10; $`62.96\%`$ vs. $`47.19\%`$ at cap 40), Rome Capacity Op2 cap 10 ($`56.10\%`$ vs. $`47.37\%`$), Oslo Commute cap 40 ($`32.40\%`$ vs. $`20.68\%`$), and the 6-cohort retrospective mean ($`49.26\%`$ vs. $`43.24\%`$ at cap 10; $`47.81\%`$ vs. $`35.67\%`$ at cap 40, where PACER’s 20-sample residual buffer forgets stale initial scores slower than Periodic’s 10-sample buffer).

Table VI explains how pooling definitions alter the aggregate headline. Under offer-weighted pooling ($`\sum (e_u + m_u)/\sum M_u`$, merging shared Rome dates across Op1 and Op2), PACER minus Periodic at $`C_{\text{new}}=10`$ on the $`26`$ held-out clusters equals $`-23.41`$ percentage points (95% bootstrap $`-37.04`$ to $`-5.91`$, $`\Delta U=+0.47`$ pp). That aggregate figure is driven by offer-count imbalance: Oslo Commute contributes $`499`$ of Periodic’s $`688`$ total positive offers ($`72.5\%`$), while Ireland Static ($`5.12\%`$ risk) supplies $`215`$ of PACER’s $`620`$ offers. When clusters with active offers on both policies are weighted equally (EqualUnit, $`22/26`$ clusters), the difference vanishes to $`+0.37`$ percentage points ($`\Delta U = -3.29`$ pp); under equal cohort weighting, it is $`-4.88`$ pp. Across $`C_{\text{new}}=40`$, offer-weighted held-out contrast is $`-0.83`$ pp ($`-16.13`$ to $`+11.46`$), equal-unit is $`+2.79`$ pp, retrospective cohorts show $`+8.83`$ to $`+16.26`$ pp worse risk for PACER, and across all $`42`$ pooled clusters both cap 10 ($`-14.37`$ pp, CI $`-26.80`$ to $`+0.85`$) and cap 40 ($`+3.29`$ pp, CI $`-7.49`$ to $`+12.49`$) cross zero. Under Persistence, PACER’s conservative abstention lowers pooled utility by $`-29.95`$ pp vs. Frozen across 42 clusters at cap 40.

<div class="table*">

|               |     |             |        |        |                  |       |
|:--------------|:----|:------------|:-------|:-------|:-----------------|:------|
| Scope         | Cap | WeightRule  | Units  | dPosHi | Boot95           | dU    |
| HeldOut       | 10  | OfferWtd    | 26     | -23.41 | -37.04 to -5.91  | +0.47 |
| HeldOut       | 10  | EqualUnit   | 22/26  | +0.37  | paired valid     | -3.29 |
| HeldOut       | 10  | EqualCohort | 4 coh  | -4.88  | unweighted       | -2.91 |
| HeldOut       | 40  | OfferWtd    | 26     | -0.83  | -16.13 to +11.46 | +0.51 |
| HeldOut       | 40  | EqualUnit   | 12/26  | +2.79  | paired valid     | +0.01 |
| HeldOut       | 40  | EqualCohort | 4 coh  | +5.08  | unweighted       | +0.56 |
| Retrospective | 10  | OfferWtd    | 16     | +8.83  | -2.16 to +13.99  | +0.11 |
| Retrospective | 10  | EqualUnit   | 10/16  | -4.36  | paired valid     | -0.10 |
| Retrospective | 10  | EqualCohort | 6 coh  | +6.02  | unweighted       | +0.13 |
| Retrospective | 40  | OfferWtd    | 16     | +16.26 | +4.68 to +24.93  | +0.19 |
| Retrospective | 40  | EqualUnit   | 9/16   | -5.93  | paired valid     | +0.05 |
| Retrospective | 40  | EqualCohort | 6 coh  | +12.15 | unweighted       | +0.08 |
| AllCohorts    | 10  | OfferWtd    | 42     | -14.37 | -26.80 to +0.85  | +0.25 |
| AllCohorts    | 10  | EqualUnit   | 32/42  | -1.11  | paired valid     | -2.07 |
| AllCohorts    | 10  | EqualCohort | 10 coh | +1.66  | unweighted       | -1.09 |
| AllCohorts    | 40  | OfferWtd    | 42     | +3.29  | -7.49 to +12.49  | +0.31 |
| AllCohorts    | 40  | EqualUnit   | 21/42  | -0.94  | paired valid     | +0.02 |
| AllCohorts    | 40  | EqualCohort | 10 coh | +9.32  | unweighted       | +0.27 |

</div>

## Bound Tightness, Proof Assumptions, and Conditional Ceilings

To clarify the limits of finite-sample guarantees under sparse queries, consider PACER’s weighted selective-excess bound over $`K = \min(C_{\text{new}}, T)`$ uniform block probes $`u_k \sim \mathrm{Uniform}(\mathcal{B}_k)`$ with block-constant threshold $`q_{(k)}`$ updated at block boundaries (protocol and derivation in `docs/PACER_THEORY_AND_PREREGISTRATION.md`):
``` math
\begin{equation}
\mathbf{E}\!\left[A\left(R_+^{\text{upper}} - \alpha\right)\right] \le \frac{W_{\max}}{T} \cdot \frac{\alpha + a_{\text{veto}} + \gamma(1 - \alpha)(1 + D)}{\gamma},
\label{eq:t1_bound}
\end{equation}
```
where $`W_{\max} = \lceil T/K \rceil`$, $`D \le 1`$ is inter-block completion delay (verified $`D=0`$ across evaluated streams), and $`\mathbf{E}[\cdot]`$ holds under two explicit independence assumptions: (i) an oblivious stream $`(p_t, Y_t, O_t)_{t=1}^T`$ whose covariates, outcomes, and censoring do not adapt to realized probe indices $`(u_1,\dots,u_K)`$, and (ii) block-constant thresholds $`q_{(k)}`$ frozen throughout $`\mathcal{B}_k`$ prior to revealing $`u_k`$ so $`\mathbf{E}[I_{u_k}(e_{u_k}^{\text{cons}}-\alpha)\mid \mathcal{F}_{k-1}] = |\mathcal{B}_k|^{-1}\sum_{t\in\mathcal{B}_k} I_t(e_t^{\text{cons}}-\alpha)`$.

**Remark 1 (Vacuous Regime at Small $`K`$ or Low Offer Frequency):** Plugging locked parameters ($`\alpha=0.10, \gamma=0.05, a_{\text{veto}}=0.15, D=1`$) into <a href="#eq:t1_bound" data-reference-type="eqref" data-reference="eq:t1_bound">[eq:t1_bound]</a> yields $`(0.10+0.15+0.05\cdot 0.90\cdot 2)/0.05 = 6.8`$, giving bound $`B_1(K) = 6.8 W_{\max}/T \approx 6.8/K`$ ($`0.683`$–$`0.714`$ at $`K=10`$; $`0.178`$–$`0.192`$ at $`K=40`$). Meanwhile, since $`R_+^{\text{upper}} \le 1`$, *every* policy deterministically satisfies $`A(R_+^{\text{upper}}-\alpha) \le (1-\alpha)A = 0.9A`$. Consequently, <a href="#eq:t1_bound" data-reference-type="eqref" data-reference="eq:t1_bound">[eq:t1_bound]</a> is strictly trivial whenever $`B_1(K) \ge 0.9A`$ ($`A \le 0.76`$ at $`K=10`$; $`A \le 0.20`$ at $`K=40`$). As Fig. 3 confirms across all 40 seed-averaged cohort–model–cap cells, <a href="#eq:t1_bound" data-reference-type="eqref" data-reference="eq:t1_bound">[eq:t1_bound]</a> falls below the trivial ceiling on only $`1`$ of $`20`$ cells at $`C_{\text{new}}=10`$ (Ireland Static HistGBM) and $`3`$ of $`20`$ cells at $`C_{\text{new}}=40`$ ($`4/40`$ overall); $`40/40`$ satisfaction therefore reflects small $`A`$ and large $`6.8/K`$ rather than tight conditional risk control. Informative bounds require either $`C_{\text{new}} \ge 40`$ at high $`A`$ or substantially larger $`K`$ (e.g., guaranteeing $`R_+^{\text{upper}}-\alpha \le 0.10`$ at $`A=0.50`$ requires $`K \ge 136`$).

**Proposition 1 (Blind-Suffix Risk Under Budget Exhaustion):** Any policy exhausting $`C_{\text{new}}`$ at index $`\tau < T`$ holds $`q_t`$ frozen over all $`M_{\text{post}}`$ post-exhaustion positive offers, admitting an outcome shift on $`(\tau, T]`$ with $`R_+^{\text{upper}} \ge M_{\text{post}}/M`$, whereas block pacing caps unprobed gaps at $`W_{\max} \le \lceil T/K \rceil`$ ticks.

<figure id="fig:t1_bounds" data-latex-placement="!t">
<embed src="figures/main_fig3_theorem1_bounds.png" style="width:88.0%" />
<figcaption>Comparison of PACER’s weighted selective-excess bound <span class="math inline"><em>B</em><sub>1</sub>(<em>K</em>) ≈ 6.8/<em>K</em></span>, the deterministic trivial ceiling <span class="math inline">(1 − <em>α</em>)<em>A</em> = 0.9<em>A</em></span>, and 3-seed mean observed excess across all 40 cohort–model–cap cells. At <span class="math inline"><em>C</em><sub>new</sub> = 10</span>, 19/20 cells lie inside the vacuous region <span class="math inline"><em>B</em><sub>1</sub> ≥ 0.9<em>A</em></span>; only 4/40 cells overall (Ireland Static cap 10/40; Ireland and Oslo Commute cap 40) sit below <span class="math inline">0.9<em>A</em></span>.</figcaption>
</figure>

Table VII converts $`R_+^{\text{upper}} \le \alpha + B_1(K)/A`$ into operational deployment boundaries. When $`A < 0.25`$–$`0.30`$ (observed across E1, E3, AT&T, T-Mobile, Verizon, Ireland driving, and Rome Capacity Op1/Op2) or under uncalibrated lag predictors, controllers must **not be deployed** for SLA-backed rate commitments.

<div class="table*">

|  |  |  |  |  |  |  |
|:---|:---|:---|:---|:---|:---|:---|
| OfferStratum | RefA | CeilC10 | CeilC40 | EmpPosHiC40 | EmpCohortsC40 | PolicyRule |
| A below 0.15 | 0.10 | 100.0 | 100.0 | 47.62-62.96 | E1,E3,ATT,Ver,Rome1/2 | DO NOT DEPLOY |
| A 0.15 to 0.30 | 0.22 | 100.0 | 93.5 | 36.84-44.26 | T-Mobile, Ireland | DO NOT DEPLOY (SLA) |
| A 0.30 to 0.70 | 0.50 | 100.0 | 46.7 | 32.40 | Oslo Commute | Advisory Only |
| A 0.70 or more | 0.85 | 91.7 | 31.6 | 6.98 | Ireland Static | Usable Target |
| Persistence Lag | All | T1 0.714 | T1 0.192 | -29.95pp U vs Frz | All 10 cohorts (42u) | DO NOT DEPLOY |

</div>

# Exploratory Sensitivity and Robustness

To ensure findings are not artifacts of the $`W=10`$ sample-max quantile ($`\lceil 11 \times 0.9 \rceil = 10`$) or the 57-row HistGBM predictor, we conducted strictly exploratory sensitivity runs over the 6 retrospective cohorts ($`G=16`$ physical dates; held-out public archives remained isolated from any model or hyperparameter change).

<div class="table*">

|           |                     |     |         |       |       |      |       |                 |
|:----------|:--------------------|:----|:--------|:------|:------|:-----|:------|:----------------|
| Axis      | Setting             | Cap | PosRate | MARHi | PerHi | MARU | Eq dU | tCI95           |
| Win/Alpha | a=0.05, W=10        | 10  | 0.0     | undef | undef | 0.00 | +0.00 | all zero        |
| Win/Alpha | a=0.05, W=20        | 40  | 2.5     | 52.50 | 15.15 | 0.12 | -0.08 | -0.48 to +0.32  |
| Win/Alpha | a=0.05, W=40        | 40  | 11.5    | 24.06 | 15.15 | 0.33 | +0.16 | -0.28 to +0.59  |
| Win/Alpha | a=0.10, W=10        | 10  | 25.4    | 32.77 | 29.49 | 0.82 | -0.09 | -1.27 to +1.08  |
| Win/Alpha | a=0.10, W=20        | 40  | 34.1    | 38.04 | 31.96 | 1.86 | +0.22 | -1.13 to +1.57  |
| Win/Alpha | a=0.10, W=40        | 40  | 23.1    | 30.67 | 32.30 | 0.78 | -0.30 | -1.52 to +0.93  |
| Win/Alpha | a=0.20, W=10        | 10  | 36.3    | 45.58 | 42.23 | 2.33 | -0.22 | -1.19 to +0.75  |
| Win/Alpha | a=0.20, W=20        | 40  | 45.1    | 45.75 | 44.33 | 6.82 | +2.25 | +0.48 to +4.03  |
| Win/Alpha | a=0.20, W=40        | 40  | 43.1    | 46.85 | 45.28 | 3.41 | +1.58 | +0.47 to +2.69  |
| Predictor | HistGBM57 (E1 32.2) | 10  | 25.4    | 32.77 | 29.49 | 0.82 | -0.09 | -1.27 to +1.08  |
| Predictor | ResNet57 (E1 29.7)  | 10  | 21.5    | 37.97 | 27.10 | 0.23 | -0.47 | -1.05 to +0.11  |
| Predictor | ResNet57 (E1 29.7)  | 40  | 31.1    | 23.90 | 28.14 | 0.31 | -0.43 | -1.02 to +0.16  |
| Predictor | QGBM10 (E1 29.7)    | 10  | 17.1    | 51.99 | 50.36 | 0.63 | +1.02 | +0.06 to +1.98  |
| Predictor | ClkGBM112 (E1 32.5) | 40  | 14.5    | 37.87 | 44.13 | 1.57 | -2.46 | -4.75 to -0.16  |
| Predictor | Persist (E1 44.3)   | 10  | 17.7    | 65.73 | 64.21 | 9.50 | -4.03 | -12.18 to +4.12 |

</div>

**Window Length ($`n \in \{10,20,40\}`$) and Nominal Level ($`\alpha \in \{0.05,0.10,0.20\}`$):** As Table VIII shows, eliminating the max-of-10 discontinuity via larger windows ($`n=20`$ selects rank $`19/20`$; $`n=40`$ selects $`37/40`$) or relaxed $`\alpha=0.20`$ ($`9/10`$ at $`n=10`$) preserves every qualitative finding. At $`\alpha=0.05`$, $`n=10`$ abstains completely ($`q=+\infty`$, $`0.0\%`$ offers), while $`n=20,40`$ recover $`2.5\%`$–$`11.5\%`$ offers yet yield $`24.1\%`$–$`52.5\%`$ conditional risk and near-zero $`\Delta U`$. At $`\alpha=0.10`$, enlarging to $`W=20,40`$ leaves MARUR conditional upper risk at $`30.7\%`$–$`38.0\%`$ (Periodic $`32.0\%`$–$`33.0\%`$), utility below $`1.9\%`$, and every equal-date $`\Delta U`$ interval crossing zero. Even at $`\alpha=0.20`$, risk reaches $`45.0\%`$–$`46.9\%`$ ($`>2\times \alpha`$) with modest cap-40 utility gains ($`+1.58`$ to $`+2.25`$ pp).

**Source-Only Alternative Predictors:** Evaluated strictly on the chronological Op1 2021 source split (never touching held-out dates), `ThroughputResNet_57` (Val MAE $`5.91`$ Mbps vs. HistGBM’s $`11.00`$) achieves lower point MAE across every retrospective cohort ($`29.67`$ vs. $`32.20`$ on E1; $`28.24`$ vs. $`32.60`$ on Ireland; $`149.07`$ vs. $`154.22`$ on T-Mobile). Replaying it alongside pinball `QuantileGBM_p10_57` (Val MAE $`5.01`$), a 112-row source clock-minute `HistGBM_Clock112`, and Persistence shows all core conclusions survive: bounded source predictors keep MARUR conditional upper risk at $`23.9\%`$–$`56.4\%`$ and utility at $`0.23\%`$–$`1.57\%`$, whereas Persistence raises utility to $`9.50\%`$ at $`65.73\%`$ conditional risk while losing $`-4.03`$ pp equal-date utility relative to Periodic ($`t`$-CI $`-12.18`$ to $`+4.12`$). Note also that parameter sweep counts ($`576`$, $`720`$, $`792`$, $`1{,}848`$) remain deterministic permutations over the same archives; effective independent evidence resides in the $`16`$ retrospective and $`26`$ held-out campaign-dates.

# Limitations, Reproducibility, and Scope

**Threats to Validity:** (1) *Internal:* Random baselines use full-horizon eligibility offline; prospective runs require pre-committed schedules. Fixed 60-second clock intervals differ from transport-level transfer completions, and position-based `QueryCensor20` does not replicate correlated physical radio outages. (2) *External and statistical:* All ten evaluated cohorts come from historical public archives; `prospective_trips_collected` remains $`0`$. Frozen artifact `frozen_rome_histgbm.joblib` and harness `scripts/run_prospective_validation.py` remain ready without modification, alongside an empty prospective pilot template in the supplement, should live trips be collected later. (3) *Construct and secondary scope:* Results strictly evaluate cellular throughput commitment accounting; session boundary sensitivity, random-split trace analyses (Raca et al. 2020; Sirhan 2026), trace-driven Oslo video QoE replays, and the detailed MARUR-vs.-PACER comparator taxonomy reside in the accompanying supplementary document.

**Reproducibility and Hardware:** Locked configurations, SHA-256 checksums, and MIT-licensed scripts run end-to-end on standard x86-64 CPUs in Python 3.11 (verified in a fresh virtual environment via `scripts/reproduce_all.py` with CPU fallback for the optional `ThroughputResNet` neural comparator, which also supports CUDA 12.1 / RTX 4060). Continuous integration runs CPU unit tests alongside automated manuscript-table verification and manifest digest checks.

# Conclusion

Evaluated rigorously over $`16`$ retrospective and $`26`$ held-out physical campaign-dates, sparse recalibration feedback does not automatically improve cellular throughput commitments. Matched-cost cluster utility differences between MARUR and Periodic are statistically indistinguishable from zero ($`-0.09`$ pp equal-date mean), conditional upper violation risks routinely span $`17\%`$–$`63\%`$ far above $`\alpha=0.10`$, supported throughput generally remains $`1\%`$–$`3\%`$, and favorable pooled risk headlines (such as $`-23.41`$ pp at cap 10) can hinge on offer-count weighting across heterogeneous cohorts while vanishing under equal-cluster weighting ($`+0.37`$ pp) or higher query caps. Separating realized costs, missing-outcome bounds, offer frequency, and cluster units—while recognizing when theoretical bounds hold trivially—prevents misleading deployment claims until genuinely prospective field validation becomes available.

# Acknowledgment

OpenAI Codex assisted with code development, experimental checks, and manuscript drafting and revision.

<div id="refs" class="references csl-bib-body hanging-indent">

<div id="ref-angelopoulos2024risk" class="csl-entry">

Angelopoulos, Anastasios N., Stephen Bates, Adam Fisch, Lihua Lei, and Tal Schuster. 2024. “Conformal Risk Control.” *Proceedings of the International Conference on Learning Representations (ICLR)*. <https://openreview.net/forum?id=33XGfHLtZg>.

</div>

<div id="ref-pid2023" class="csl-entry">

Angelopoulos, Anastasios N., Emmanuel J. Candès, and Ryan J. Tibshirani. 2023. “<span class="nocase">Conformal PID Control for Time Series Prediction</span>.” *Advances in Neural Information Processing Systems (NeurIPS)* 36: 23047–74. <https://doi.org/10.52202/075280-1000>.

</div>

<div id="ref-angelopoulos2024online" class="csl-entry">

Angelopoulos, Anastasios Nikolas, Rina Barber, and Stephen Bates. 2024. “<span class="nocase">Online conformal prediction with decaying step sizes</span>.” *Proceedings of the 41st International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 235: 1616–30. <https://proceedings.mlr.press/v235/angelopoulos24a.html>.

</div>

<div id="ref-barber2023" class="csl-entry">

Barber, Rina Foygel, Emmanuel J. Candès, Aaditya Ramdas, and Ryan J. Tibshirani. 2023. “<span class="nocase">Conformal prediction beyond exchangeability</span>.” *The Annals of Statistics* 51 (2): 816–45. <https://doi.org/10.1214/23-AOS2276>.

</div>

<div id="ref-basit2024" class="csl-entry">

Basit, Omar, Phuc Dinh, Imran Khan, et al. 2024. “<span class="nocase">On the Predictability of Fine-Grained Cellular Network Throughput Using Machine Learning Models</span>.” *2024 IEEE 21st International Conference on Mobile Ad-Hoc and Smart Systems (MASS)*, 47–56. <https://doi.org/10.1109/MASS62177.2024.00018>.

</div>

<div id="ref-bates2021" class="csl-entry">

Bates, Stephen, Anastasios Angelopoulos, Lihua Lei, Jitendra Malik, and Michael Jordan. 2021. “<span class="nocase">Distribution-free, Risk-controlling Prediction Sets</span>.” *Journal of the ACM* 68 (6): 1–34. <https://doi.org/10.1145/3478535>.

</div>

<div id="ref-bhatnagar2023" class="csl-entry">

Bhatnagar, Aadyot, Huan Wang, Caiming Xiong, and Yu Bai. 2023. “<span class="nocase">Improved Online Conformal Prediction via Strongly Adaptive Online Learning</span>.” *Proceedings of the 40th International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 202: 2337–63. <https://proceedings.mlr.press/v202/bhatnagar23a.html>.

</div>

<div id="ref-caso2024" class="csl-entry">

Caso, Giuseppe, Mohammad Rajiullah, Konstantinos Kousias, et al. 2024. “<span class="nocase">The Chronicles of 5G Non-Standalone: An Empirical Analysis of Performance and Service Evolution</span>.” *IEEE Open Journal of the Communications Society* 5: 7380–99. <https://doi.org/10.1109/OJCOMS.2024.3499370>.

</div>

<div id="ref-gauthier2026" class="csl-entry">

Gauthier, Etienne, Francis Bach, and Michael I. Jordan. 2026. “<span class="nocase">Adaptive Coverage Policies in Conformal Prediction</span>.” *Proceedings of the 29th International Conference on Artificial Intelligence and Statistics (AISTATS)*, Proceedings of machine learning research, vol. 300: 3196–204. <https://proceedings.mlr.press/v300/gauthier26a.html>.

</div>

<div id="ref-ge2025" class="csl-entry">

Ge, Haosen, Hamsa Bastani, and Osbert Bastani. 2025. “<span class="nocase">Stochastic Online Conformal Prediction with Semi-Bandit Feedback</span>.” *Proceedings of the 42nd International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 267: 18954–65. <https://proceedings.mlr.press/v267/ge25a.html>.

</div>

<div id="ref-geifman2017" class="csl-entry">

Geifman, Yonatan, and Ran El-Yaniv. 2017. “<span class="nocase">Selective Classification for Deep Neural Networks</span>.” *Advances in Neural Information Processing Systems (NeurIPS)* 30: 4878–87. <https://proceedings.neurips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html>.

</div>

<div id="ref-gibbs2021" class="csl-entry">

Gibbs, Isaac, and Emmanuel J. Candès. 2021. “Adaptive Conformal Inference Under Distribution Shift.” *Advances in Neural Information Processing Systems (NeurIPS)* 34: 1660–72. <https://proceedings.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html>.

</div>

<div id="ref-gibbs2024" class="csl-entry">

Gibbs, Isaac, and Emmanuel J. Candès. 2024. “<span class="nocase">Conformal Inference for Online Prediction with Arbitrary Distribution Shifts</span>.” *Journal of Machine Learning Research* 25 (162): 1–36. <https://jmlr.org/papers/v25/22-1218.html>.

</div>

<div id="ref-gibbs2025" class="csl-entry">

Gibbs, Isaac, John J. Cherian, and Emmanuel J. Candès. 2025. “<span class="nocase">Conformal prediction with conditional guarantees</span>.” *Journal of the Royal Statistical Society Series B: Statistical Methodology* 87 (4): 1100–1126. <https://doi.org/10.1093/jrsssb/qkaf008>.

</div>

<div id="ref-hou2025" class="csl-entry">

Hou, Qiushuo, Sangwoo Park, Matteo Zecchin, Yunlong Cai, Guanding Yu, and Osvaldo Simeone. 2025. “<span class="nocase">Online Conformal Probabilistic Numerics via Adaptive Edge-Cloud Offloading</span>.” *Proceedings of the First International Conference on Probabilistic Numerics*, Proceedings of machine learning research, vol. 271: 138–46. <https://proceedings.mlr.press/v271/hou25a.html>.

</div>

<div id="ref-ilyas2026" class="csl-entry">

Ilyas, Andrew, Joonhyuk Ko, Jingwu Tang, Steven Wu, and Jiahao Zhang. 2026. “Provably Label-Efficient Conformal Prediction.” *Proceedings of the 43rd International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 306: 49578–97. <https://proceedings.mlr.press/v306/ilyas26a.html>.

</div>

<div id="ref-jacobson2025" class="csl-entry">

Jacobson, Tate, Jie Ding, and Hui Zou. 2025. “<span class="nocase">Predicting 5G throughput with BAMMO, a boosted additive model for data with missing observations</span>.” *Journal of the Royal Statistical Society Series C: Applied Statistics* 74 (1): 249–73. <https://doi.org/10.1093/jrsssc/qlae054>.

</div>

<div id="ref-kousias2024data" class="csl-entry">

Kousias, Konstantinos, Mohammad Rajiullah, Giuseppe Caso, Usman Ali, et al. 2024. “<span class="nocase">A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements</span>.” *IEEE Communications Magazine* 62 (5): 44–49. <https://doi.org/10.1109/MCOM.011.2200707>.

</div>

<div id="ref-kousias2024model" class="csl-entry">

Kousias, Konstantinos, Mohammad Rajiullah, Giuseppe Caso, Ozgu Alay, et al. 2024. “<span class="nocase">Empirical performance analysis and ML-based modeling of 5G non-standalone networks</span>.” *Computer Networks* 241: 110207. <https://doi.org/10.1016/j.comnet.2024.110207>.

</div>

<div id="ref-lin2022" class="csl-entry">

Lin, Zhen, Shubhendu Trivedi, and Jimeng Sun. 2022. “<span class="nocase">Conformal Prediction with Temporal Quantile Adjustments</span>.” *Advances in Neural Information Processing Systems (NeurIPS)* 35: 31017–30. <https://doi.org/10.52202/068431-2249>.

</div>

<div id="ref-manski1989selection" class="csl-entry">

Manski, Charles F. 1989. “<span class="nocase">Anatomy of the Selection Problem</span>.” *Journal of Human Resources* 24 (3): 343–60. <https://doi.org/10.2307/145818>.

</div>

<div id="ref-min2026" class="csl-entry">

Min, Yizhou, Yizhou Lu, Lanqi Li, Zhen Zhang, and Jiaye Teng. 2026. “<span class="nocase">Questioning the Coverage-Length Metric in Conformal Prediction: When Shorter Intervals Are Not Better</span>.” *Proceedings of the 43rd International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 306: 88935–63. <https://proceedings.mlr.press/v306/min26c.html>.

</div>

<div id="ref-narayanan2020" class="csl-entry">

Narayanan, Arvind, Eman Ramadan, Rishabh Mehta, et al. 2020. “<span class="nocase">Lumos5G: Mapping and Predicting Commercial mmWave 5G Throughput</span>.” *Proceedings of the ACM Internet Measurement Conference (IMC)*, 176–93. <https://doi.org/10.1145/3419394.3423629>.

</div>

<div id="ref-nuwinsarchive" class="csl-entry">

NUWiNS. 2025. *PAM 2025 Multi-Carrier Dataset*. Public data and transfer intervals, commit 782b712.

</div>

<div id="ref-podkopaev2024" class="csl-entry">

Podkopaev, Aleksandr, Dong Xu, and Kuang-Chih Lee. 2024. “<span class="nocase">Adaptive Conformal Inference by Betting</span>.” *Proceedings of the 41st International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 235: 40886–907. <https://proceedings.mlr.press/v235/podkopaev24a.html>.

</div>

<div id="ref-raca2020" class="csl-entry">

Raca, Darijo, Dylan Leahy, Cormac J. Sreenan, and Jason J. Quinlan. 2020. “<span class="nocase">Beyond throughput, the next generation: a 5G dataset with channel and context metrics</span>.” *Proceedings of the 11th ACM Multimedia Systems Conference (MMSys)*, 303–8. <https://doi.org/10.1145/3339825.3394938>.

</div>

<div id="ref-raca2024" class="csl-entry">

Raca, Darijo, Ahmed H. Zahran, Cormac J. Sreenan, Rakesh K. Sinha, Emir Halepovic, and Vijay Gopalakrishnan. 2024. “<span class="nocase">Device-Based Cellular Throughput Prediction for Video Streaming: Lessons From a Real-World Evaluation</span>.” *IEEE Transactions on Machine Learning in Communications and Networking* 2: 318–34. <https://doi.org/10.1109/TMLCN.2024.3352541>.

</div>

<div id="ref-riiser2013commute" class="csl-entry">

Riiser, Haakon, Paul Vigmostad, Carsten Griwodz, and Pål Halvorsen. 2013. “<span class="nocase">Commute Path Bandwidth Traces from 3G Networks: Analysis and Applications</span>.” *Proceedings of the 4th ACM Multimedia Systems Conference (MMSys)*, 114–18. <https://doi.org/10.1145/2483977.2483991>.

</div>

<div id="ref-sirhan2026" class="csl-entry">

Sirhan, Najem N. 2026. “<span class="nocase">Handover-Aware Conformal Throughput Intervals for Risk-Sensitive Rate Selection in Mobile 5G</span>.” *Network* 6 (4): 92. <https://doi.org/10.3390/network6040092>.

</div>

<div id="ref-tibshirani2019" class="csl-entry">

Tibshirani, Ryan J., Rina Foygel Barber, Emmanuel J. Candès, and Aaditya Ramdas. 2019. “Conformal Prediction Under Covariate Shift.” *Advances in Neural Information Processing Systems (NeurIPS)* 32: 2530–40. <https://proceedings.neurips.cc/paper_files/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html>.

</div>

<div id="ref-xu2023" class="csl-entry">

Xu, Chen, and Yao Xie. 2023. “<span class="nocase">Sequential Predictive Conformal Inference for Time Series</span>.” *Proceedings of the 40th International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 202: 38707–27. <https://proceedings.mlr.press/v202/xu23r.html>.

</div>

<div id="ref-zaffran2023" class="csl-entry">

Zaffran, Margaux, Aymeric Dieuleveut, Julie Josse, and Yaniv Romano. 2023. “<span class="nocase">Conformal Prediction with Missing Values</span>.” *Proceedings of the 40th International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 202: 40578–604. <https://proceedings.mlr.press/v202/zaffran23a.html>.

</div>

<div id="ref-zaffran2022" class="csl-entry">

Zaffran, Margaux, Olivier Feron, Yannig Goude, Julie Josse, and Aymeric Dieuleveut. 2022. “<span class="nocase">Adaptive Conformal Predictions for Time Series</span>.” *Proceedings of the 39th International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 162: 25834–66. <https://proceedings.mlr.press/v162/zaffran22a.html>.

</div>

</div>
