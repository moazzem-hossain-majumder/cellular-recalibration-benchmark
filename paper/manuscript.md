# When Does Recalibration Help Cellular Throughput Commitments? Accounting for Cost, Missingness, and Abstention

## Abstract

Calibration policies evaluated at identical nominal query caps can mislead through unequal probe spending, missing outcomes, and heavy abstention. We ask when sparse recalibration feedback helps cellular throughput commitments and how empirical accounting exposes false improvements. Across archived mobile evaluations under frozen tree predictors and fixed policies, conditional upper violation risk spans 9\% to 68\% (above nominal $\alpha=0.10$) while supported throughput remains 1\% to 3\%. At matched query cost, supported-throughput differences between adaptive and fixed-period recalibration are small in absolute points, yet two one-sided tests against a $\pm 50\%$ relative baseline margin are inconclusive: we cannot rule out large relative gains or losses. Overall, in these public archives with these frozen predictors and policies, sparse recalibration did not reliably improve commitments. We contribute an open-source accounting library, practitioner checklist, and command-line audit tool (\texttt{audit\_policy.py}) separating query attempts, finite-record missing-outcome bounds, selective decomposition $R=(M/N)R_+$, relative equivalence, and pooling checks. All evidence is retrospective from public archives without live field validation.

<div class="IEEEkeywords">

Cellular throughput, calibration feedback, selective prediction, cluster equivalence, measurement methodology.

</div>

# Introduction

An application committing to a minimum cellular throughput requires useful delivered bandwidth alongside tolerable failure rates. Point error, low all-issued violations, and equal nominal recalibration caps do not establish either property: under sparse feedback, a controller can appear safer simply by abstaining more often, exhausting probes early, spending unequal realized queries, or omitting unmeasured outcomes from failure counts.

We address an empirical measurement question: *when does recalibration feedback help cellular throughput commitments, and how do unequal query cost, missingness, and abstention make apparent gains misleading?* In these public archives, with these frozen predictors and policies, sparse recalibration did not reliably improve commitments. Alongside our empirical findings, our primary contribution is an open-source accounting library and CLI tool (`src/audit/recalibration_audit.py`, `scripts/audit_policy.py`) verified across six retrospective cohorts and four held-out public archives:

1.  **Causal ledger and reporting CLI:** Event-level separation of probe requests, horizon missingness, and finite-record bounds $`[e/M,(e+m)/M]`$ satisfying $`R=(M/N)R_+`$, paired with an automated warning CLI and practitioner checklist.

2.  **Cluster equivalence and dependence checks:** Matched-cost contrasts grouped by physical campaign-date ($`G=16`$ retrospective; $`G=26`$ held-out), leading with relative Two One-Sided Tests (TOST) alongside absolute Minimum Detectable Effect (MDE) and campaign-level dependence sensitivity.

3.  **Comparator and bound auditing:** Benchmarking *Missingness-Aware Recalibration under Uncertainty and Risk* (MARUR) and *Horizon-Paced Selective-Offer Conformal Control* (PACER) against standard baselines, exposing pooling-weight artifacts and vacuous small-budget regimes.

All evidence is retrospective from public archives and no live field validation was performed; all negative findings are retained. Evidence from these public archives also does not cover closed-loop congestion deployment, other user devices or cellular operators outside the logged traces, alternative measurement tools, or non-60s prediction horizons.

# Related Work

## Cellular Measurement, Prediction, and Rate Decisions

Operational measurements establish that cellular throughput depends on radio conditions, mobility, and collection protocol. Earlier channel/context traces (Raca et al. 2020) and commercial millimeter-wave (mmWave) fifth-generation (5G) campaigns (Narayanan et al. 2020) enabled context-aware rate prediction, while newer multi-technology datasets and machine-learning evaluations extend these insights to non-standalone 5G deployments (Kousias, Rajiullah, Caso, Ali, et al. 2024; Caso et al. 2024; Kousias, Rajiullah, Caso, Alay, et al. 2024). However, forecast errors sampled within a single route or shared drive are temporally correlated rather than independent replications, and low point error does not bound rate-commitment violations.

Missing inputs and deployment realism motivate complementary lines of work. The Boosted Additive Model for data with Missing Observations (BAMMO) handles missing covariates during commercial 5G throughput modeling (Jacobson et al. 2025), addressing unobserved inputs rather than unsuccessful acquisition of future calibration outcomes. Smartphone video streaming studies highlight real-time sampling shift (Raca et al. 2024), multi-carrier experiments document conflicting rate histories across links (Basit et al. 2024), and Sirhan (Sirhan 2026) compares global, regime-conditioned, and adaptive conformal intervals for mobile 5G rate selection. None of these studies audits how unequal probe spending, failed outcome horizon completions, and heavy abstention jointly distort controller comparisons.

## Missingness, Adaptation, and Budgeted Feedback

Conformal calibration with missing covariates separates marginal coverage from missingness-pattern conditioning (Zaffran et al. 2023), whereas covariate-shift reweighting (Tibshirani et al. 2019) and non-exchangeable weighted quantiles (Barber et al. 2023) rely on structural weights that degrade under unmodeled drift and outcome censoring. Sequential time-series conformal methods (Zaffran et al. 2022; Xu and Xie 2023; Lin et al. 2022; Gibbs and Candès 2024), Adaptive Conformal Inference (ACI) and online variants (Gibbs and Candès 2021; Bhatnagar et al. 2023; Angelopoulos et al. 2023; Anastasios Nikolas Angelopoulos et al. 2024; Podkopaev et al. 2024), and risk-controlling formulations (Bates et al. 2021; Anastasios N. Angelopoulos et al. 2024; Angelopoulos et al. 2025; Gibbs et al. 2025; Gauthier et al. 2026) assume complete label revelation after each step, while selective classification (Geifman and El-Yaniv 2017) and interval-stability critiques (Min et al. 2026) formalize abstention–risk interactions.

Recent work examines partial or costly feedback directly: upfront stopping rules under i.i.d. arrivals (Ilyas et al. 2026), semi-bandit feedback revealed by set inclusion (Ge et al. 2025), and sporadic edge–cloud calibration (Hou et al. 2025). Our study complements these directions by auditing real cellular ledgers jointly over probe expenditures, unobserved outcomes, $`R=(M/N)R_+`$, and physical cluster equivalence (Table I).

<div class="table*">

| **Work** | **Modality** | **Environment** | **Core Method** | **Audit Boundary** | **Present Contribution** |
|:---|:---|:---|:---|:---|:---|
| BAMMO (Jacobson et al. 2025) | Radio/context | Commercial mmWave 5G | Missing-covariate additive boosting | Missing inputs differ from missing future outcomes | Separates input vs. outcome missingness |
| Raca et al. (Raca et al. 2024) | Smartphone | Live video streaming | On-device throughput prediction | No selective commitment audit across caps | Causal trace ledger without live-QoE claim |
| Basit et al. (Basit et al. 2024) | Rate histories | Multi-carrier driving | Fine-grained ML predictability | Conflicting histories limit point accuracy | Audits conditional risk and supported rate |
| Sirhan (Sirhan 2026) | Rate, RAT, handover | Commercial mobile 5G | Global/grouped/adaptive conformal bounds | Full-outcome split; no attempt-budget ledger | Separates probe attempts and missing outcomes |
| Zaffran et al. (Zaffran et al. 2023) | Incomplete inputs | Regression missingness | Missing-pattern conformal sets | Input missingness differs from failed requests | Tracks probe failures vs. buffer admissions |
| Conformal PID (Angelopoulos et al. 2023) | Temporal scores | Forecasting series | Online PID quantile control | Assumes full score feedback every step | Audits delayed and censored sparse probes |
| Ilyas et al. (Ilyas et al. 2026) | IID arrivals | Label stopping | Cost-efficient stopping rule | Stationary arrivals differ from mobile drift | Accounts seed vs. new probes under drift |
| Ge et al. (Ge et al. 2025) | Partial labels | Semi-bandit sets | Online conformal regret bounds | Set-inclusion differs from probe failure | Tracks maturation delay and charged probes |
| Hou et al. (Hou et al. 2025) | Solver outputs | Edge–cloud systems | Sporadic-feedback calibration | Two-sided width differs from SLA rate risk | One-sided commitments and abstention |
| CRC (Anastasios N. Angelopoulos et al. 2024) | Scores/losses | Vision/language sets | Expected monotone-loss control | Population guarantees differ from finite logs | Finite-record $`[e/M,(e+m)/M]`$ risk intervals |
| Min et al. (Min et al. 2026) | Predictive sets | Regression/classif. | Coverage–length stability critique | Diagnostic rather than probe-cost ledger | Jointly tracks $`A`$, $`R_+`$, $`U`$, and query cost |
| Gauthier et al. (Gauthier et al. 2026) | Adaptive sets | Adaptive coverage | Learned coverage via e-values | Requires e-value policy design | Audits fixed-cadence vs. adaptive comparators |
| **Present study** | **Rate and radio** | **Ten cohorts (42 dates)** | **Causal acquisition and cluster audit** | **Public archives; zero live trips** | **CLI tool, checklist, MDE/TOST, pooling audit** |

</div>

# Decision Process, Accounting, and Audit Tool

At scheduled issue time $`t`$, a frozen predictor outputs point forecast $`p_t`$ from strictly prior lag throughput and radio telemetry. A controller selects nonnegative commitment $`L_t \ge 0`$ and decides whether to request outcome $`y_t`$ over the upcoming horizon (`ready` timestamp); ticks lacking a valid prior rate are marked ineligible ($`L_t = 0`$). All controllers begin with identical complete initial pre-test labels excluded from new target queries $`Q_{\text{new}}`$ under budget cap $`C_{\text{new}}`$.

Across $`N`$ eligible opportunities, let $`M = \sum_t \mathbf{1}\{L_t > 0\}`$ denote positive commitments, $`A = M/N`$ the positive-offer frequency, $`e`$ observed violations ($`L_t > y_t`$), and $`m`$ positive commitments lacking observed $`y_t`$. Because $`y_t \ge 0`$ prevents zero commitments from violating, all-issued risk $`R`$ and positive-offer conditional risk $`R_+`$ obey
``` math
\begin{equation}
\begin{aligned}
R &= A \cdot R_+,\qquad R \in [e/N, (e+m)/N],\\
R_+ &\in [e/M, (e+m)/M]\qquad (M > 0),
\end{aligned}
\label{eq:risk_bounds}
\end{equation}
```
where $`[e/M,(e+m)/M]`$ are exact finite-record partial-identification bounds (Manski 1989). Whenever abstention shrinks $`A`$, $`R \le \alpha`$ permits $`R_+ \approx \alpha/A \gg \alpha`$. Service utility is measured via supported throughput $`U = \sum_{t:y_t\text{ obs}}\min(L_t,y_t)/\sum_{t:y_t\text{ obs}}y_t`$.

## Practitioner Checklist and `audit_policy.py` Tool

To operationalize these checks, `src/audit/recalibration_audit.py` and `scripts/audit_policy.py` ingest cluster-summary or tick-level CSV ledgers, verify <a href="#eq:risk_bounds" data-reference-type="eqref" data-reference="eq:risk_bounds">[eq:risk_bounds]</a>, compute relative and absolute equivalence tests, cluster bootstrap and Student-$`t`$ intervals, between-cluster SD, and $`\text{MDE}_{80}`$, and emit automated deployment warnings (boxed checklist). Run on our exported held-out cap-10 ledger (`examples/worked_heldout_c10_ledger.csv`), the CLI flags zero-offer clusters, unmatched realized queries, inconclusive relative equivalence, and offer-count pooling divergence ($`-23.41`$ pp vs. $`+0.37`$ pp).

<figure data-latex-placement="!t">

</figure>

## Evaluated Controllers and Baselines

Nine policy families share this causal interface (Table II; decision taxonomy in Supplement Table S15): static *Frozen*, greedy *Early*, uniform *Random*, fixed *Periodic*, sparse *ACI* (Gibbs and Candès 2021), *Decaying Online Gradient Descent* (*DecayingOGD*) (Anastasios Nikolas Angelopoulos et al. 2024), reactive *MARUR* (60-minute or LTE/NR pattern triggers, window inserting predicted score on missingness, and pattern gates), and *PACER* (designed after inspecting retrospective MARUR failures; uniform block pacing excluding missingness and using smooth selective updates).

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

# Retrospective Inference and Power Analysis

Six retrospective cohorts operate on 60-second causal clocks (Kousias, Rajiullah, Caso, Ali, et al. 2024; Caso et al. 2024; NUWiNS 2025; Raca et al. 2020): Rome *E1* and *E3*, US Drive 3 (*AT&T*, *T-Mobile*, *Verizon*), and *Ireland* driving traces. Earliest Rome Op1 splits train the frozen Histogram Gradient Boosted Machine (*HistGBM*) on 57 source rows without future leakage; co-located carriers collapse onto three geographic campaigns and $`G=16`$ physical campaign-dates.

Across mobile-cohort *HistGBM* evaluations (*Periodic*, *MARUR*, *PACER*), conditional upper risk $`R_+^{\text{hi}}`$ spans $`9\%`$–$`68\%`$, well above $`\alpha=0.10`$, while quasi-stationary *Ireland Static* stays lower and supported throughput generally remains $`1\%`$–$`3\%`$ (Fig. 1; high-budget six-cohort breakdown in Supplement Table S14).

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

## Relative Equivalence, Power, and Campaign Dependence

At matched ten-query cost across $`16`$ retrospective dates (Table III), MARUR minus Periodic yields equal-cluster mean $`\Delta U = -0.09`$ pp (pooled $`+0.21`$ pp), while Periodic’s pooled baseline utility sits at only $`0.60\%`$.

Because absolute $`\pm 2`$ pp margins span more than three times this baseline, we evaluate relative equivalence against a primary $`\pm 50\%`$ margin relative to Periodic’s $`U`$ (ruling out at least halving or doubling baseline service) alongside $`\pm 25\%`$ sensitivity, reporting excluded zero-$`U`$ cluster counts.

Expressed relative to baseline utility (Table IV), retrospective MARUR yields a pooled relative ratio of $`+35.3\%`$ (excluding $`4`$ zero-$`U`$ clusters), with TOST inconclusive at $`\pm 50\%`$ ($`p=0.3564`$) and $`\pm 25\%`$: we cannot rule out substantial relative gains or losses of this magnitude in any retrospective, held-out, or pooled archive.

On the absolute scale preserved alongside relative tests in Table IV, retrospective power is limited ($`\text{MDE}_{80}=1.65`$ pp) with two-point TOST rejecting large differences ($`p=0.0018`$), while low-budget held-out PACER lowers equal-cluster utility ($`-3.29`$ pp).

In an exploratory post-hoc check for correlation among dates from the same field campaign ($`3`$ campaigns per scope), two-stage hierarchical bootstrap and ANOVA intraclass-correlation adjustments further contract effective sample size (Supplement Table S18): on retrospective MARUR, effective dates shrink from $`16`$ to $`3.84`$.

On high-budget held-out PACER, effective units similarly fall from $`26`$ to $`6.73`$, reversing naive two-point TOST ($`p=0.0132`$ to $`p=0.1388`$) and leaving hierarchical intervals inconclusive.

<div class="table*">

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scope | Cand | Cap | G | Z0 | RefU | PoolRel | Rel95CI | pRel50 | pRel25 | EqdU | MDE80 | p1pp | p2pp |
| Retro | MAR | 10 | 16 | 4 | 0.60 | +35.3 | -55.5 to +260.4 | 0.3564 | 0.4602 | -0.09 | 1.65 | 0.0609 | 0.0018 |
| Retro | PAC | 10 | 16 | 4 | 0.60 | +18.3 | -40.6 to +140.5 | 0.2917 | 0.4449 | -0.10 | 1.08 | 0.0122 | 0.0000 |
| HeldOut | MAR | 10 | 26 | 4 | 1.01 | +40.0 | -2.4 to +87.6 | 0.9605 | 0.9713 | -3.36 | 4.54 | 0.9286 | 0.8041 |
| HeldOut | PAC | 10 | 26 | 4 | 1.01 | +46.9 | -9.7 to +131.6 | 0.9731 | 0.9817 | -3.29 | 4.01 | 0.9457 | 0.8213 |
| HeldOut | PAC | 40 | 26 | 2 | 1.17 | +43.1 | -52.2 to +186.4 | 0.2508 | 0.3707 | +0.01 | 2.46 | 0.1261 | 0.0132 |
| AllCoh | PAC | 10 | 42 | 8 | 0.76 | +32.6 | -12.8 to +95.3 | 0.9682 | 0.9799 | -2.07 | 2.55 | 0.8831 | 0.5334 |
| AllCoh | PAC | 40 | 42 | 6 | 0.80 | +38.6 | -30.3 to +130.9 | 0.2436 | 0.3726 | +0.02 | 1.53 | 0.0372 | 0.0003 |

</div>

<figure id="fig:policy_summary" data-latex-placement="!t">
<embed src="figures/main_fig1_policy_summary.png" style="width:84.0%" />
<figcaption>Overview of (a) positive-offer frequency <span class="math inline"><em>A</em></span>, (b) conditional upper risk <span class="math inline"><em>R</em><sub>+</sub><sup>hi</sup></span> vs. <span class="math inline"><em>α</em> = 10%</span>, and (c) supported throughput <span class="math inline"><em>U</em></span> across all 10 archived cohorts (6 retrospective R, 4 held-out H) under frozen HistGBM and recorded feedback.</figcaption>
</figure>

# Held-Out Archives and Bound Audit

Four held-out public archives contribute $`G=26`$ additional physical campaign-dates ($`42`$ pooled clusters total): shared *Rome Capacity Op1/Op2* dates, post-2011 *Oslo Commute* (Riiser et al. 2013), and *Ireland Static*. Configuration and SHA-256 checksums (`docs/PACER_FROZEN_PROTOCOL.md`) were frozen prior to evaluation, although the authors had prior archive access and designed PACER after inspecting retrospective failures.

Per-cohort outcomes remain heterogeneous (Table V, Fig. 2): PACER lowers first-day risk on Oslo at low cap and keeps low risk on Ireland Static, yet matches or trails Periodic across most mobile cells. Table VI resolves why pooled headlines diverge: offer-weighted held-out contrast ($`-23.41`$ pp) reflects Oslo’s heavy Periodic offer share versus Ireland Static’s PACER share, vanishing under equal-cluster weighting ($`+0.37`$ pp); under Persistence at high cap, PACER cuts pooled utility by $`-29.95`$ pp relative to Frozen (full matrix in Supplement Table S16).

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
<embed src="figures/main_fig2_pacer_breakdown.png" style="width:78.0%" />
<figcaption>Per-cohort conditional upper risk <span class="math inline"><em>R</em><sub>+</sub><sup>hi</sup></span> comparing Periodic, MARUR, and PACER across held-out public archives and the 6-cohort retrospective mean at (a) <span class="math inline"><em>C</em><sub>new</sub> = 10</span> and (b) <span class="math inline"><em>C</em><sub>new</sub> = 40</span> (frozen HistGBM, recorded feedback).</figcaption>
</figure>

<div class="table*">

|            |     |             |       |        |                  |       |
|:-----------|:----|:------------|:------|:-------|:-----------------|:------|
| Scope      | Cap | WeightRule  | Units | dPosHi | Boot95           | dU    |
| HeldOut    | 10  | OfferWtd    | 26    | -23.41 | -37.04 to -5.91  | +0.47 |
| HeldOut    | 10  | EqualUnit   | 22/26 | +0.37  | paired valid     | -3.29 |
| HeldOut    | 10  | EqualCohort | 4 coh | -4.88  | unweighted       | -2.91 |
| HeldOut    | 40  | OfferWtd    | 26    | -0.83  | -16.13 to +11.46 | +0.51 |
| HeldOut    | 40  | EqualUnit   | 12/26 | +2.79  | paired valid     | +0.01 |
| HeldOut    | 40  | EqualCohort | 4 coh | +5.08  | unweighted       | +0.56 |
| AllCohorts | 10  | OfferWtd    | 42    | -14.37 | -26.80 to +0.85  | +0.25 |
| AllCohorts | 10  | EqualUnit   | 32/42 | -1.11  | paired valid     | -2.07 |
| AllCohorts | 40  | OfferWtd    | 42    | +3.29  | -7.49 to +12.49  | +0.31 |
| AllCohorts | 40  | EqualUnit   | 21/42 | -0.94  | paired valid     | +0.02 |

</div>

## Theorem 1 Bound Tightness and Operational Ceilings

PACER’s weighted selective-excess bound over $`K=\min(C_{\text{new}}, T)`$ uniform probes $`u_k \sim \mathrm{Uniform}(\mathcal{B}_k)`$ is
``` math
\begin{equation}
\mathbf{E}\!\left[A\left(R_+^{\text{upper}} - \alpha\right)\right] \le \frac{W_{\max}}{T} \cdot \frac{\alpha + a_{\text{veto}} + \gamma(1 - \alpha)(1 + D)}{\gamma},
\label{eq:t1_bound}
\end{equation}
```
where $`W_{\max}=\lceil T/K \rceil`$ and inter-block delay $`D \le 1`$ (verified empirically alongside block-constant thresholds under an oblivious stream (Vovk et al. 2005)). With locked parameters, <a href="#eq:t1_bound" data-reference-type="eqref" data-reference="eq:t1_bound">[eq:t1_bound]</a> yields $`B_1(K) \approx 6.8/K`$.

**Remark 1 (Vacuous Regime) and Proposition 1:** Every policy deterministically obeys $`A(R_+^{\text{upper}}-\alpha) \le 0.9A`$, so <a href="#eq:t1_bound" data-reference-type="eqref" data-reference="eq:t1_bound">[eq:t1_bound]</a> beats this trivial ceiling in only $`4/40`$ seed-mean cells (Fig. 3). Uniform pacing nevertheless bounds unprobed gaps at $`W_{\max}`$ unlike greedy exhaustion; Table VII maps these ceilings into deployment vetoes below $`A < 0.30`$ or under lag Persistence.

<figure id="fig:t1_bounds" data-latex-placement="!t">
<embed src="figures/main_fig3_theorem1_bounds.png" style="width:78.0%" />
<figcaption>PACER weighted selective-excess bound <span class="math inline"><em>B</em><sub>1</sub>(<em>K</em>) ≈ 6.8/<em>K</em></span>, trivial ceiling <span class="math inline">(1 − <em>α</em>)<em>A</em> = 0.9<em>A</em></span>, and 3-seed mean excess across all 40 cells (<span class="math inline"><em>C</em><sub>new</sub> = 10</span>: <span class="math inline">0.683</span>–<span class="math inline">0.714</span>; <span class="math inline"><em>C</em><sub>new</sub> = 40</span>: <span class="math inline">0.178</span>–<span class="math inline">0.192</span>). Only <span class="math inline">1/20</span> cells at cap 10 and <span class="math inline">3/20</span> at cap 40 (4/40 total) sit below <span class="math inline">0.9<em>A</em></span>.</figcaption>
</figure>

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

# Extended Exploratory Sensitivity and Scope

Under an explicitly *exploratory* label (`results/exploratory/sensitivity/`) preserving all frozen results, we extended window/$`\alpha`$ and source-only predictor evaluations to both *MARUR* and *PACER* across retrospective and held-out archives, plus a Leave-One-Cohort-Out (LOCO) check over all $`42`$ clusters (Table VIII; full LOCO in Supplement Table S17).

<div class="table*">

|  |  |  |  |  |  |  |  |  |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| Axis | Policy | Setting | Cap | CandHi | PerHi | CandU | Eq dU | tCI95 |
| Retro16 W/a | MARUR | a=0.05,W=40 | 40 | 24.06 | 15.15 | 0.33 | +0.16 | -0.28 to +0.59 |
| Retro16 W/a | MARUR | a=0.10,W=20 | 40 | 38.04 | 31.96 | 1.86 | +0.22 | -1.13 to +1.57 |
| Retro16 W/a | MARUR | a=0.20,W=20 | 40 | 45.75 | 44.33 | 6.82 | +2.25 | +0.48 to +4.03 |
| Retro16 W/a | PACER | a=0.05,W=40 | 40 | 40.48 | 15.15 | 0.21 | +0.18 | -0.54 to +0.90 |
| Retro16 W/a | PACER | a=0.10,W=20 | 40 | 44.19 | 31.96 | 0.76 | -0.22 | -1.14 to +0.70 |
| Retro16 W/a | PACER | a=0.20,W=20 | 40 | 43.63 | 44.33 | 1.93 | +0.15 | -0.51 to +0.82 |
| HeldOut26 W/a | MARUR | a=0.05,W=40 | 40 | 19.69 | 20.91 | 0.18 | -0.71 | -1.54 to +0.12 |
| HeldOut26 W/a | MARUR | a=0.10,W=20 | 40 | 19.49 | 24.90 | 1.17 | -1.33 | -2.14 to -0.52 |
| HeldOut26 W/a | MARUR | a=0.20,W=20 | 40 | 28.25 | 37.17 | 3.20 | -1.72 | -2.70 to -0.74 |
| HeldOut26 W/a | PACER | a=0.05,W=40 | 40 | 16.90 | 20.91 | 0.25 | +0.29 | -0.40 to +0.98 |
| HeldOut26 W/a | PACER | a=0.10,W=20 | 40 | 25.80 | 24.90 | 1.68 | +0.46 | -0.90 to +1.83 |
| HeldOut26 W/a | PACER | a=0.20,W=20 | 40 | 35.80 | 37.17 | 5.38 | +0.48 | -3.15 to +4.10 |
| Retro16 Pred | MARUR | ResNet57 | 40 | 23.90 | 28.14 | 0.31 | -0.43 | -1.02 to +0.16 |
| Retro16 Pred | PACER | ResNet57 | 40 | 25.81 | 28.14 | 0.33 | +0.38 | -0.76 to +1.51 |
| Retro16 Pred | MARUR | QGBM10 | 10 | 51.99 | 50.36 | 0.63 | +1.02 | +0.06 to +1.98 |
| Retro16 Pred | PACER | QGBM10 | 10 | 54.41 | 50.36 | 0.54 | -0.18 | -0.37 to +0.02 |
| Retro16 Pred | MARUR | ClkGBM112 | 40 | 37.87 | 44.13 | 1.57 | -2.46 | -4.75 to -0.16 |
| Retro16 Pred | PACER | ClkGBM112 | 40 | 42.41 | 44.13 | 1.28 | -1.72 | -3.62 to +0.17 |
| Retro16 Pred | MARUR | Persist | 10 | 65.73 | 64.21 | 9.50 | -4.03 | -12.18 to +4.12 |
| Retro16 Pred | PACER | Persist | 10 | 66.82 | 64.21 | 14.35 | -8.18 | -15.85 to -0.50 |
| HeldOut Pred | MARUR | ResNet57 | 40 | 8.43 | 41.38 | 0.13 | -1.11 | -3.35 to +1.13 |
| HeldOut Pred | PACER | ResNet57 | 40 | 19.38 | 41.38 | 0.11 | -1.08 | -3.33 to +1.17 |
| HeldOut Pred | MARUR | QGBM10 | 10 | 45.68 | 58.62 | 0.46 | -0.26 | -0.56 to +0.05 |
| HeldOut Pred | PACER | QGBM10 | 10 | 52.23 | 58.62 | 0.94 | +0.14 | -0.23 to +0.51 |
| HeldOut Pred | MARUR | Persist | 10 | 57.21 | 53.71 | 33.69 | +4.04 | -0.56 to +8.64 |
| HeldOut Pred | PACER | Persist | 10 | 59.82 | 53.71 | 39.21 | +0.80 | -12.71 to +14.32 |
| LOCO (10 cohorts) | MAR/PAC | Drop any 1/10 | 10 | 47.1-49.3 | 47.1 full | 0.67-1.17 | -2.38 to +0.12 | p95 G=35..42 |

</div>

**Window, Nominal $`\alpha`$, Source Predictors, and LOCO:** Enlarging windows or varying nominal levels leaves PACER and MARUR conditional risks elevated without consistent equal-cluster utility gains (Table VIII). Similarly, replaying lower-error source-only predictors (`ThroughputResNet`, `QuantileGBM`, `ClockGBM`, Oslo bus quantile regressor, and lag Persistence) either retains high conditional risk or suppresses throughput below 1%. Dropping any single cohort preserves mobile median conditional risk near $`47\%`$–$`49\%`$ while omitting Oslo removes the low-cap utility drop without revealing gains elsewhere.

**What Evidence Does Not Cover:** These archived traces do not measure closed-loop network deployment where commitments alter transport congestion or user quality of experience, large query budgets where Theorem 1 tightens across moderate offer rates, devices and cellular operators absent from European and US public archives, alternative active-probing measurement tools, or non-60s service horizons.

# Limitations, Reproducibility, and Conclusion

**Limitations and Reproducibility:** All evidence is retrospective from public archives and no live field validation was performed; our results do not establish performance on other devices, operators, measurement tools, or closed-loop deployments. All SHA-256 locked configurations run on CPU Python 3.11 via `scripts/reproduce_all.py` (with CPU fallback for neural models) alongside CI checks and `scripts/audit_policy.py`.

**Conclusion:** In these public archives, with these frozen predictors and policies, sparse recalibration did not reliably improve commitments. Crucially, relative equivalence against a $`\pm 50\%`$ baseline margin is inconclusive across every retrospective and held-out archive, so substantial relative changes in supported throughput cannot be ruled out; campaign-level clustering further shrinks effective sample sizes.

Across mobile evaluations, conditional upper violation risk spans $`9\%`$–$`68\%`$ above $`\alpha=0.10`$, supported throughput averages $`1\%`$–$`3\%`$, and finite-sample bounds are vacuous across most tested regimes. Adopting `scripts/audit_policy.py` and the six-item reporting checklist exposes abstention, missing-outcome, and pooling artifacts before deployment.

# Acknowledgment

OpenAI Codex assisted with code development, experimental checks, and manuscript drafting and revision.

<div id="refs" class="references csl-bib-body hanging-indent">

<div id="ref-angelopoulos2021ltt" class="csl-entry">

Angelopoulos, Anastasios N., Stephen Bates, Emmanuel J. Candès, Michael I. Jordan, and Lihua Lei. 2025. “<span class="nocase">Learn then test: Calibrating predictive algorithms to achieve risk control</span>.” *The Annals of Applied Statistics* 19 (2): 1641–62. <https://doi.org/10.1214/24-AOAS1998>.

</div>

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

NUWiNS. 2025. *PAM 2025 Multi-Carrier Dataset*. Public data and transfer intervals, commit 782b712. <https://github.com/NUWiNS/pam2025-multi-carrier-dataset>.

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

<div id="ref-vovk2005algorithmic" class="csl-entry">

Vovk, Vladimir, Alex Gammerman, and Glenn Shafer. 2005. *<span class="nocase">Algorithmic Learning in a Random World</span>*. Springer. <https://doi.org/10.1007/b106715>.

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
