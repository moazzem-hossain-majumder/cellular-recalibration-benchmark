# When Limited Recalibration Fails: Accounting for Cellular Throughput Commitments

## Abstract

Cellular throughput commitments depend on both the forecast and the feedback available to recalibrate it. Comparing calibration policies at the same nominal budget can conceal unequal acquisition cost, failed responses and abstention. We present an empirical acquisition-and-decision framework with frozen predictors, delayed query receipts and finite-record bounds for missing outcomes. Its provisional MARUR controller uses age and telemetry-pattern heuristics; it does not optimize utility or guarantee conditional risk. Six archived cohorts support 576 original configurations and 720 additional full-suffix replays, yielding 384 exact-cost contrasts. At ten new queries on Rome E1, MARUR supports 2.907 percent of measured throughput versus Periodic's 0.523 percent, while all-issued upper risk rises from 6.303 to 10.924 percent. On Ireland, both policies issue 159 positive commitments; MARUR removes fourteen observed violations by reducing commitment sizes, with supported throughput falling from 4.117 to 1.129 percent. Across only 16 distinct physical campaign-dates spanning three geographic drives, matched ten-query equal-campaign-date utility differences average -0.09 percentage points (95 percent interval -1.27 to +1.08), and MARUR exhausts its budget on Day 1 in four of six cohorts. Other cohorts and baselines show mixed trade-offs and no consistent superiority. The framework separates service selection, commitment size, cluster counts and acquisition cost, keeping all findings retrospective, exploratory and strictly within cellular throughput measurement rather than live application QoE.

<div class="IEEEkeywords">

Cellular throughput, calibration feedback, selective prediction, cluster inference, measurement methodology.

</div>

# Introduction

An application that commits to a rate needs useful service and a tolerable frequency of broken commitments. Accurate point forecasts, low average violations and small nominal calibration budgets do not independently establish those properties. A controller can make fewer positive offers, avoid expensive feedback, exhaust its query cap early, or encounter unobserved outcomes. Each changes the meaning of a favorable reported number.

We focus on a concrete empirical question: when does calibration feedback acquisition improve cellular throughput commitments, and when do missing feedback, abstention and unequal measurement costs make the apparent improvement misleading? We study frozen predictors on outcome-independent scheduled opportunities. MARUR combines established concepts—online quantile adjustment, selective prediction, cost-constrained probing and partial-feedback updating—as an implemented heuristic to expose these mechanisms. It is neither a novel general conformal prediction algorithm nor a method with guaranteed positive-conditional risk.

The contribution comprises three empirical findings: attempted measurements differ from information available to later forecasts; low overall risk can conceal poor reliability among positive commitments or single-date concentration; and calibration choices produce cohort-dependent utility–risk trade-offs that vanish across independent physical campaign-dates. The accompanying event ledgers, exact-cost comparisons, cluster-level decompositions and MIT-licensed software make these findings auditable. All archives were inspected during method development, zero prospective trips have been collected, and negative results are retained without post-hoc deployment selection.

# Related Work

## Cellular Measurement, Prediction, and Rate Decisions

Operational measurements establish that cellular throughput depends on radio conditions, mobility, and the collection regime. The channel/context dataset of Raca et al. (Raca et al. 2020) and the commercial mmWave measurements underlying Lumos5G (Narayanan et al. 2020) support context-aware prediction. More recent multi-technology measurements, longitudinal service analysis, and machine-learning modeling extend this evidence to evolving non-standalone networks (Kousias, Rajiullah, Caso, Ali, et al. 2024; Caso et al. 2024; Kousias, Rajiullah, Caso, Alay, et al. 2024). These resources support evaluation across conditions, but forecast counts within a shared route or campaign do not constitute independent replications. Moreover, prediction-error metrics do not directly measure the risk of promising an unsustainable rate.

Missing predictors and deployment constraints motivate complementary approaches. BAMMO incorporates missing covariates into additive boosting and variable-importance estimation on commercial 5G data (Jacobson et al. 2025). Its treatment of absent radio measurements addresses the input side of prediction; unsuccessful acquisition of future calibration outcomes is a separate problem. Real-time smartphone experiments demonstrate the importance of sampling, labeling, distribution shift, and application integration (Raca et al. 2024). Conversely, fine-grained multi-carrier experiments expose conflicting measurement histories and limits to achievable prediction accuracy (Basit et al. 2024). Together, these findings favor evaluation at a specified prediction horizon and operational objective rather than comparisons of headline accuracy across incompatible datasets.

The closest application-level work is Sirhan’s comparison of global, regime-conditioned, and adaptive conformal throughput intervals (Sirhan 2026). Conditioning on radio-access technology and handover state can improve two-sided interval behavior without improving one-sided rate selection; a global bound can yield a better utilization–stall trade-off. Thus, neither conformal throughput bounds nor decision-oriented evaluation is a new contribution here. Our question concerns how the resulting commitments behave when acquiring calibration feedback consumes a limited number of attempts, responses can be unsuccessful, and telemetry patterns change.

## Missingness and Calibration Beyond Exchangeability

Conformal calibration under missing covariates explicitly distinguishes marginal validity from coverage conditional on missingness patterns (Zaffran et al. 2023). Partitioning a calibration sample by pattern can address heterogeneous errors but reduces the number of available scores. A pattern-specific quantile obtained from a small, adaptively collected window cannot inherit a coverage statement solely because its construction resembles conformal prediction. Similarly, likelihood-ratio weighting under covariate shift (Tibshirani et al. 2019) and weighted methods beyond exchangeability (Barber et al. 2023) establish results under specified distributional and weighting conditions, rather than under unrestricted temporal drift and outcome-dependent observation.

Time-series methods exploit temporal structure in different ways. Adaptive conformal aggregation (Zaffran et al. 2022), sequential prediction of residual quantiles (Xu and Xie 2023), and temporal quantile adjustments (Lin et al. 2022) evaluate coverage together with interval efficiency. Online conformal inference also studies arbitrary distribution shifts and long-run calibration (Gibbs and Candès 2024). Their guarantees concern different sampling models and coverage targets: asymptotic conditional validity, longitudinal or cross-sectional behavior, and time-averaged coverage are not interchangeable. For cellular commitments, the relevant distinction is between missing input telemetry, a requested label that never becomes usable, and a label unavailable until its measurement horizon closes. Evaluation must retain these distinctions instead of removing unresolved outcomes from the denominator.

## Online Adaptation and Limited Feedback

Adaptive conformal inference adjusts the nominal error level using observed mistakes (Gibbs and Candes 2021). Strongly adaptive online learning emphasizes performance over local time intervals (Bhatnagar et al. 2023); conformal PID control uses feedback and score forecasting (Angelopoulos et al. 2023); decaying step sizes connect retrospective coverage with stable-distribution quantile estimation (Anastasios Nikolas Angelopoulos et al. 2024); and betting-based adaptation reduces manual learning-rate selection (Podkopaev et al. 2024). These developments provide substantive methodological baselines. However, replacing their feedback stream with selectively requested, delayed, or imputed scores changes the assumptions and does not preserve their guarantees automatically.

Label efficiency and partial feedback have also been studied directly. Ilyas et al. (Ilyas et al. 2026) balance upfront calibration-label cost against prediction-set efficiency using a stopping rule for independently and identically distributed arrivals. Ge et al. (Ge et al. 2025) analyze stochastic online conformal prediction when the label is revealed through inclusion in the selected prediction set. Hou et al. (Hou et al. 2025) calibrate probabilistic linear-system solvers using sporadic cloud feedback and examine coverage, set size, and cloud usage. Therefore, adaptive querying, sparse feedback, and calibration-cost trade-offs are established research directions. The cellular setting considered here differs in its physical measurement attempts, unsuccessful responses, delayed admission of scores, and one-sided throughput commitments. These differences motivate an explicit event ledger and matched realized-cost evaluation; they do not by themselves establish algorithmic novelty or a new theoretical guarantee.

## Selective Risk and Decision-Oriented Evaluation

Selective classification formalizes the trade-off between accepting predictions and reducing conditional error (Geifman and El-Yaniv 2017). Risk-controlling prediction sets (Bates et al. 2021) and conformal risk control (Anastasios N. Angelopoulos et al. 2024) extend calibration beyond a single coverage event, subject to their respective risk definitions and assumptions. Conditional conformal guarantees can target specified classes of shifts or subgroups (Gibbs et al. 2025), while adaptive coverage policies use a dedicated statistical construction to choose example-dependent coverage levels (Gauthier et al. 2026). A heuristic abstention gate is not equivalent to any of these constructions.

Metric choice is consequential. Min et al. (Min et al. 2026) demonstrate that coverage and average interval length can conceal undesirable prediction behavior. For nonnegative throughput and zero-rate abstention, an analogous accounting distinction is elementary but essential: with a common eligible-opportunity denominator, all-issued violation risk equals the positive-offer frequency multiplied by violation risk conditional on a positive offer. Lower all-issued risk can therefore accompany unchanged or worse reliability among actual commitments. Missing outcomes additionally require finite-record risk bounds, which are not confidence intervals or prospective coverage guarantees. Supported throughput, positive-offer frequency, abstention, unresolved outcomes, and dates with positive commitments must consequently be reported alongside risk and realized query cost.

<div class="table*">

| **Work** | **Modality** | **Dataset or environment** | **Core method** | **Relevant limitation** | **Ours: distinction** |
|:---|:---|:---|:---|:---|:---|
| BAMMO (Jacobson et al. 2025) | Radio/context | Commercial mmWave 5G | Missing-covariate additive boosting | Outcome acquisition differs from missing predictors | Separates input and feedback missingness |
| Raca et al. (Raca et al. 2024) | Smartphone telemetry | Live cellular video streaming | On-device throughput prediction | No corresponding selective conformal guarantee | Retrospective commitment audit; no live-deployment claim |
| Basit et al. (Basit et al. 2024) | Rate histories/context | Multi-carrier LTE/5G driving | Fine-grained prediction feasibility | Accuracy limits depend on task and horizon | Reports commitment risk and useful service |
| Sirhan (Sirhan 2026) | Rate, RAT, handover | Commercial mobile 5G traces | Global/group/adaptive conformal rate bounds | Does not establish MARUR’s failed-query accounting | Matched attempts and unresolved-outcome accounting |
| Zaffran et al. (Zaffran et al. 2023) | Incomplete covariates | Regression with missing inputs | Missing-pattern conformal calibration | Input-pattern validity differs from missing labels | Logs unsuccessful requested responses separately |
| Conformal PID (Angelopoulos et al. 2023) | Temporal scores | Public forecasting time series | Feedback and predictive quantile control | Feedback assumptions require rechecking | Delayed and unsuccessful response ledger |
| Ilyas et al. (Ilyas et al. 2026) | Labeled and unlabeled data | IID calibration arrivals | Cost-efficient stopping rule | Upfront labels differ from drifting online probes | Realized new attempts distinguished from seed labels |
| Ge et al. (Ge et al. 2025) | Sets and partial labels | Stochastic semi-bandit tasks | Online conformal regret analysis | Set-dependent reveal mechanism differs | Failed physical feedback and temporal availability |
| Hou et al. (Hou et al. 2025) | Solver outputs | Edge–cloud linear systems | Sporadic-feedback calibration | Solution-set coverage differs from rate risk | One-sided throughput commitments |
| CRC (Anastasios N. Angelopoulos et al. 2024) | Scores and losses | Vision/language examples | Expected monotone-loss control | Assumptions do not imply MARUR validity | Empirical risk bounds; no transferred theorem |
| Min et al. (Min et al. 2026) | Predictive sets | Regression and classification | Coverage–length critique; stability | Diagnostic, not cellular controller | Separates abstention from commitment reliability |
| Gauthier et al. (Gauthier et al. 2026) | Covariates and sets | Adaptive-coverage tasks | E-values; learned coverage policy | Dedicated validity construction required | Pattern gate is treated as a heuristic |
| **Present study** | **Rate and missing telemetry** | **Six retrospective cohorts** | **MARUR query/commit/abstain heuristic** | **Correlated trips; no formal conditional guarantee** | **Auditable events, matched costs, and risk–utility decomposition** |

</div>

#### Research Gap and Contribution

The reviewed literature already establishes missingness-aware prediction, adaptive calibration, selective risk, and label-cost optimization. The defensible contribution of the present study is their operational evaluation under explicitly accounted cellular feedback constraints, rather than their combination under a new name. We examine whether a fixed, missingness-aware query/commit/abstain controller improves useful throughput at matched realized attempts without concealing risk through abstention or unresolved outcomes. The evaluation uses outcome-independent scheduled opportunities and distinguishes initial successful calibration observations, new attempts, successful responses, admitted scores, and updates used by later forecasts. Comparisons are reported separately by cohort and include adverse results. This supports an empirical systems contribution; a claim of optimal recalibration, guaranteed conditional risk, or consistent superiority requires additional theory or independent prospective evidence.

# Decision Process and Evaluation

## Scheduled opportunities and acquisition accounting

At issue time $`t`$, a frozen predictor outputs $`p_t`$ using only information available before issue. The controller returns a nonnegative commitment $`L_t`$ and may request the future outcome. Its response is revealed only after the measurement horizon closes. All scheduled opportunities remain in the ledger; those without a usable predictor are marked ineligible. The eligible denominator includes zero commitments.

Every policy starts with the same ten historical successful labels. Their original acquisition attempts are unknown and are not counted as ten physical measurement attempts. We charge each new query when issued, including requests that fail or finish after the last forecast. We separately record successful responses, unsuccessful responses, admitted calibration scores and updates available to later forecasts. Lag-rate and evaluator measurements remain outside this feedback-access budget. Accordingly, a reduction in requested labels does not demonstrate physical byte, energy or measurement savings.

The primary comparison retains a fixed full suffix and reports actual query attempts. Equal caps do not ensure equal costs. Frozen incurs zero new attempts and cannot be presented as an equal-cost positive-budget comparator. Unmatched comparisons remain descriptive and are not interpolated into matched operating points.

## Risk, service and abstention

For $`N`$ eligible opportunities, let $`M`$ denote positive offers, $`e`$ observed violations, and $`m`$ positive offers with missing outcomes. Since throughput is nonnegative and zero offers cannot violate, all-issued risk and positive-conditional risk satisfy $`R=(M/N)R_+`$. Thus reducing acceptance can reduce overall risk without improving the reliability of actual commitments.
``` math
R\in[e/N,(e+m)/N],\quad R_+\in[e/M,(e+m)/M],\quad M>0.
```
These are finite-record identification bounds, not confidence intervals or prospective guarantees. If $`M=0`$, conditional risk is undefined. At trace ends, an unobserved latent service outcome additionally requires a clearly defined measurement target; logs cannot establish that service continued after recording stopped.

Supported-throughput utility is $`U=\sum_{t:y_t\text{ observed}}\min(L_t,y_t)/\sum_{t:y_t\text{ observed}}y_t`$. It is conditional on measured service. We also report observed supported Mbps per eligible opportunity, with no credited service for missing outcomes. Neither metric measures live application benefit. We report offer frequency, abstention, positive dates, unknown outcomes and feedback costs beside risk and utility. No operational superiority is asserted without independently specified utility, offer-frequency and risk requirements.

## Implemented policies

MARUR maintains ten recent admitted scores $`s=p-y`$. A missing requested outcome contributes the conservative upper score $`p`$, since $`y\geq0`$. At nominal $`\alpha=0.1`$, the corrected quantile uses rank $`\lceil(n+1)(1-\alpha)\rceil`$; with ten scores this is the maximum. The commitment is $`\max(0,p-q)`$. Matching-pattern scores are used only with at least nine entries; fewer than three matching entries causes abstention. Query triggers use a sixty-minute completed-response age or a telemetry-pattern change, subject to the remaining cap and at most one pending request. Failed completed responses reset the original trigger state even when an ablation discards their scores.

This is a heuristic with a stated design objective, not a solution to constrained utility maximization. Conservative completion bounds an individual missing score but does not establish a sequential calibration theorem under selective feedback and drift. Periodic, Early and modified ACI share the same feedback interface; ACI here is an explicitly modified sparse-feedback comparator.

# Experimental Evidence

## Cohorts and dependence

The main replay uses Rome E1 and E3, three carriers from one US drive, and an Irish cohort. Both the archived histogram-gradient-boosted predictor and persistence are evaluated. Rome has seven test dates per cohort with six shared dates; the US carriers share one campaign with two substantial driving days and a short third calendar date; the Irish cohort has five test dates. Multiple carriers, forecast ticks and repeated masks do not increase independent-trip replication.

The supplementary document preserves session-endpoint comparisons, alternative boundaries, weighting, prediction-model selection, external endpoint protocols, calibration-prefix curves and playback simulations. Those analyses have different units or splits and cannot be pooled as if they were additional samples from the main experiment. Playback is simulation over recorded service, not randomized deployment evidence.

## Equal-cost comparisons and conditional risk

The original 576 configurations and 720 audit replays yield 384 exact-cost contrasts across the audit family. On E1 with the frozen tree and ten new queries, MARUR supports 2.907 percent of measured throughput versus Periodic’s 0.523 percent, while the all-issued upper-risk bound increases from 6.303 to 10.924 percent. This is a service–risk trade-off, not a reliability gain.

On Ireland both issue 159 positive offers; MARUR eliminates fourteen observed violations on shared offers by reducing their sizes, while support declines from 4.117 to 1.129 percent. On Verizon, removing ten of Early’s offers removes six violations, with no failure improvement on the shared offers. The former reflects conservative sizing; the latter reflects selection. Neither establishes a uniformly better policy.

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

The table reports all six cohorts at a common cap but displays realized costs explicitly; its rows are not automatically matched-cost comparisons. Positive-conditional risk is frequently high even when overall risk appears low. At ten new queries in the completed-clock, five-minute-spacing experiment, recorded HistGBM conditional upper-risk bounds range from approximately 8.8 percent in Ireland to 62.5 percent in E3. A blanket claim of reliable positive commitments is therefore unsupported.

## Controlled freshness and window sensitivity

An additional 1,848-configuration experiment uses fixed timestamp-based independent and burst feedback masks. It separates latest attempt, completed response, successful observed label and admitted-score times. The primary contrast changes only the age clock, with identical five-minute attempt spacing and pattern logic. All 24 recorded-feedback comparisons are unchanged. Across recorded and stressed conditions there are six matched utility gains without higher conditional upper risk, seven losses without lower risk, eight trade-offs or risk-only changes, 129 unchanged cases and eighteen unmatched-cost cases. These dependent configuration counts are descriptive, not replication counts.

Increasing the window to twenty or forty adds no free initial labels. Some cohorts gain utility with nonincreasing conditional upper risk, while E3 and Verizon lose substantial useful throughput. Retaining more scores changes both their ages and pattern support; improvement cannot be attributed solely to quantile stabilization. The main conclusion is heterogeneity, not an optimal window selected from these results.

## Targeted baselines and mechanism checks

Three seeded nonadaptive random query schedules test whether adaptive timing adds value beyond acquiring labels. A decaying-step quantile tracker, motivated by online conformal prediction (Anastasios Nikolas Angelopoulos et al. 2024), uses the Periodic feedback schedule. Its signed scores, delayed responses and conservative missing-feedback substitution differ from the published setting, so no theorem is transferred. Separate ablations compare pattern and pooled quantiles with the gate fixed, then remove only the gate with the query schedule fixed. Every cohort, cap and feedback condition is retained. Complete operating points and offer decompositions are provided in the reviewer-baseline supplement; no best test schedule is promoted.

The targeted grid contains 792 configurations. Pattern versus pooled quantiles give identical utility and conditional risk in all 72 paired configurations with the gate fixed. Removing the gate yields sixteen utility gains without higher conditional upper risk, ten trade-offs or risk-only changes and 46 unchanged cases. Against Periodic, the decaying-step adaptation yields nine utility gains without higher conditional upper risk, eighteen losses without lower risk, and 45 trade-offs or risk-only changes. Random-schedule comparisons also vary by seed and cohort. These configuration counts share observations and do not constitute statistical replication.

Reconstructing the retained scores identifies specific failure mechanisms. In recorded HistGBM Verizon at cap forty and window twenty, a conservative missing-response score is tied at the quantile on 159 of 287 eligible ticks; all 159 have a zero raw bound. Yet window forty has no such binding missing score and still loses substantial utility. E3 has neither binding missing scores nor gate vetoes in this recorded window comparison. Thus neither missing-score completion nor abstention alone explains all losses. The complete shared/added/removed-offer decomposition is descriptive; it does not identify the physical cause of temporal residual changes.

## Independent collection units and empirical synthesis

Configuration counts (576, 720, 1,848, 792) are deterministic sweeps over the same archives, not independent statistical replications. Pooling across cohorts reveals only three geographic campaigns and sixteen unique calendar-date clusters: eight dates in Rome (E1 and E3 share six), three shared US Drive 3 dates across AT&T, T-Mobile and Verizon, and five Irish driving dates spanning eleven traces. Table III reports paired MARUR minus Periodic contrasts clustered strictly at these collection units under matched ten-query cost.

<div class="table*">

|                  |     |       |         |         |        |        |       |       |       |        |
|:-----------------|----:|------:|--------:|--------:|-------:|-------:|------:|------:|------:|-------:|
| Scope            |   G | QDays | PosDays | Pool dU | BootLo | BootHi | Eq dU |   tLo |   tHi |   dRhi |
| E1               |   7 |   1/3 |     6/6 |   +2.38 |  +0.76 |  +3.70 | +1.45 | -0.01 | +2.90 |  +4.62 |
| E3               |   7 |   3/7 |     5/2 |   +0.66 |  +0.03 |  +1.80 | +0.78 | -0.45 | +2.02 |  +9.94 |
| ATT              |   3 |   1/2 |     2/2 |   +2.58 |  +0.00 |  +2.90 | +1.65 | -2.05 | +5.36 | +11.15 |
| T-Mobile         |   3 |   1/1 |     1/1 |   -0.02 |  -0.05 |  +0.00 | -0.02 | -0.08 | +0.05 |  +0.00 |
| Verizon          |   3 |   1/2 |     1/1 |   +0.54 |  +0.00 |  +1.96 | +0.65 | -2.16 | +3.46 |  +6.62 |
| Ireland          |   5 |   2/3 |     5/5 |   -2.99 |  -4.00 |  -1.40 | -2.46 | -4.76 | -0.15 |  -4.19 |
| All (16 Dates)   |  16 |  7/13 |   14/13 |   +0.21 |  -1.26 |  +0.79 | -0.09 | -1.27 | +1.08 |  +4.07 |
| Ireland (Traces) |  11 |   4/4 |   10/10 |   -2.99 |  -4.83 |  -1.88 | -4.20 | -7.31 | -1.10 |  -4.19 |

</div>

Across all sixteen combined physical campaign-dates, MARUR yields a pooled $`\Delta U`$ of +0.21 percentage points (95 percent cluster bootstrap -1.26 to +0.79) and equal-campaign-date mean -0.09 percentage points (95 percent $`t`$ interval -1.27 to +1.08), while all-issued upper risk changes by +4.07 percentage points (-0.11 to +6.38). Five of six within-cohort equal-date $`t`$ intervals cross zero, and conditional risk improvements are absent on AT&T, T-Mobile and Verizon. Moreover, MARUR spends all ten new queries on Day 1 in E1, AT&T, T-Mobile and Verizon (1/7 to 1/3 query days versus Periodic’s 13/16 combined dates), and restricts positive commitments to a single test date in T-Mobile and Verizon. On Ireland, evaluating the eleven individual driving traces shows negative paired utility on all nine active later traces (-2.99 percentage points pooled, bootstrap -4.83 to -1.88) alongside reduced conditional upper risk (-8.81 percentage points), reflecting conservative offer shrinkage rather than improved timing. Together, these contrasts establish that apparent multi-day gains can stem from Day-1 budget exhaustion, unequal query spending or offer shrinkage rather than uniform calibration superiority.

# Limitations and Prospective Scope

The random-priority comparator knows the full eligible-opportunity roster. It is an offline nonadaptive control, not a deployable policy with unknown future eligibility. A prospective random comparator must fix its tick schedule before departure and explicitly retain skipped and unsuccessful requests in its accounting. All empirical results use previously inspected archives; zero independent prospective field trips have been collected. Clocks are outcome-independent, but queried observations remain selectively acquired. Finite-record missingness bounds do not quantify uncertainty over future campaigns, synthetic feedback masks do not estimate physical outages, and a 60-second clock horizon differs from transfer-truncated session endpoints.

This paper remains strictly focused on physical cellular throughput measurement and commitment reliability. Prior screening thresholds (such as 1.0 or 1.5 Mbps targets, 80 percent offer frequency, or 5 percent conditional risk) are unvalidated engineering assumptions, not application-owner criteria. Supported throughput is a physical capacity metric and does not establish end-to-end adaptive video quality of experience (QoE), buffering probability, startup latency, playback interruptions, or bitrate switching; live application QoE validation is deferred to a separate follow-up study.

To support future external validation without retroactive tuning, we provide the serialized frozen Rome model artifact (SHA-256 verified), fixed preprocessing, initial residual IDs, and an executable verification harness that rejects incomplete registration metadata. As a precision planning point, 18 independent paired trips yield roughly five percentage points of utility precision under an assumed SD of 0.10, whereas certifying a 5 percent conditional-risk bound under realistic intra-trip correlation requires at least 62 independent trips. True prospective field collection on new operators, hardware and routes remains an open requirement.

# Conclusion

Limited recalibration does not consistently improve cellular throughput commitments across existing commercial networks. Separating initial labels, new attempts, unsuccessful responses, abstention gates and physical collection-unit clusters exposes when apparent gains reflect unequal cost, Day-1 budget depletion, or commitment shrinkage rather than reliable online adaptation. Across sixteen unique campaign-dates spanning three geographic drives, matched ten-query paired utility spans zero while all-issued upper risk increases. The contribution is an auditable empirical evaluation methodology and matched-cost failure analysis; optimal conformal control, live QoE benefit and deployment risk guarantees remain unestablished without new prospective trials.

# Acknowledgment

OpenAI Codex assisted with code development, experimental checks, and manuscript drafting and revision.

<div id="refs" class="references csl-bib-body hanging-indent">

<div id="ref-angelopoulos2024risk" class="csl-entry">

Angelopoulos, Anastasios N., Stephen Bates, Adam Fisch, Lihua Lei, and Tal Schuster. 2024. “Conformal Risk Control.” *Proceedings of the International Conference on Learning Representations*. <https://openreview.net/forum?id=33XGfHLtZg>.

</div>

<div id="ref-angelopoulos2024online" class="csl-entry">

Angelopoulos, Anastasios Nikolas, Rina Barber, and Stephen Bates. 2024. “<span class="nocase">Online conformal prediction with decaying step sizes</span>.” *Proceedings of the International Conference on Machine Learning*, Proceedings of machine learning research, vol. 235: 1616–30. <https://proceedings.mlr.press/v235/angelopoulos24a.html>.

</div>

<div id="ref-pid2023" class="csl-entry">

Angelopoulos, Anastasios, Emmanuel Candes, and Ryan J Tibshirani. 2023. “<span class="nocase">Conformal PID Control for Time Series Prediction</span>.” *Advances in Neural Information Processing Systems* 36: 23047–74. <https://doi.org/10.52202/075280-1000>.

</div>

<div id="ref-barber2023" class="csl-entry">

Barber, Rina Foygel, Emmanuel J. Candès, Aaditya Ramdas, and Ryan J. Tibshirani. 2023. “<span class="nocase">Conformal prediction beyond exchangeability</span>.” *The Annals of Statistics* 51 (2): 816–45. <https://doi.org/10.1214/23-aos2276>.

</div>

<div id="ref-basit2024" class="csl-entry">

Basit, Omar, Phuc Dinh, Imran Khan, et al. 2024. “<span class="nocase">On the Predictability of Fine-Grained Cellular Network Throughput Using Machine Learning Models</span>.” *2024 IEEE 21st International Conference on Mobile Ad-Hoc and Smart Systems (MASS)*, 47–56. <https://doi.org/10.1109/mass62177.2024.00018>.

</div>

<div id="ref-bates2021" class="csl-entry">

Bates, Stephen, Anastasios Angelopoulos, Lihua Lei, Jitendra Malik, and Michael Jordan. 2021. “<span class="nocase">Distribution-free, Risk-controlling Prediction Sets</span>.” *Journal of the ACM* 68 (6): 1–34. <https://doi.org/10.1145/3478535>.

</div>

<div id="ref-bhatnagar2023" class="csl-entry">

Bhatnagar, Aadyot, Huan Wang, Caiming Xiong, and Yu Bai. 2023. “<span class="nocase">Improved Online Conformal Prediction via Strongly Adaptive Online Learning</span>.” *Proceedings of the International Conference on Machine Learning*, Proceedings of machine learning research, vol. 202: 2337–63. <https://proceedings.mlr.press/v202/bhatnagar23a.html>.

</div>

<div id="ref-caso2024" class="csl-entry">

Caso, Giuseppe, Mohammad Rajiullah, Konstantinos Kousias, et al. 2024. “<span class="nocase">The Chronicles of 5G Non-Standalone: An Empirical Analysis of Performance and Service Evolution</span>.” *IEEE Open Journal of the Communications Society* 5: 7380–99. <https://doi.org/10.1109/ojcoms.2024.3499370>.

</div>

<div id="ref-gauthier2026" class="csl-entry">

Gauthier, Etienne, Francis Bach, and Michael I. Jordan. 2026. “<span class="nocase">Adaptive Coverage Policies in Conformal Prediction</span>.” *Proceedings of the International Conference on Artificial Intelligence and Statistics*, Proceedings of machine learning research, vol. 300: 3196–204. <https://proceedings.mlr.press/v300/gauthier26a.html>.

</div>

<div id="ref-ge2025" class="csl-entry">

Ge, Haosen, Hamsa Bastani, and Osbert Bastani. 2025. “<span class="nocase">Stochastic Online Conformal Prediction with Semi-Bandit Feedback</span>.” *Proceedings of the International Conference on Machine Learning*, Proceedings of machine learning research, vol. 267: 18954–65. <https://proceedings.mlr.press/v267/ge25a.html>.

</div>

<div id="ref-geifman2017" class="csl-entry">

Geifman, Yonatan, and Ran El-Yaniv. 2017. “<span class="nocase">Selective Classification for Deep Neural Networks</span>.” *Advances in Neural Information Processing Systems* 30. <https://proceedings.neurips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html>.

</div>

<div id="ref-gibbs2021" class="csl-entry">

Gibbs, Isaac, and Emmanuel Candes. 2021. “Adaptive Conformal Inference Under Distribution Shift.” *Advances in Neural Information Processing Systems* 34: 1660–72. <https://proceedings.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html>.

</div>

<div id="ref-gibbs2024" class="csl-entry">

Gibbs, Isaac, and Emmanuel J. Candès. 2024. “<span class="nocase">Conformal Inference for Online Prediction with Arbitrary Distribution Shifts</span>.” *Journal of Machine Learning Research* 25 (162): 1–36. <https://jmlr.org/papers/v25/22-1218.html>.

</div>

<div id="ref-gibbs2025" class="csl-entry">

Gibbs, Isaac, John J Cherian, and Emmanuel J Candès. 2025. “<span class="nocase">Conformal prediction with conditional guarantees</span>.” *Journal of the Royal Statistical Society Series B: Statistical Methodology* 87 (4): 1100–1126. <https://doi.org/10.1093/jrsssb/qkaf008>.

</div>

<div id="ref-hou2025" class="csl-entry">

Hou, Qiushuo, Sangwoo Park, Matteo Zecchin, Yunlong Cai, Guanding Yu, and Osvaldo Simeone. 2025. “<span class="nocase">Online Conformal Probabilistic Numerics via Adaptive Edge-Cloud Offloading</span>.” *Proceedings of the First International Conference on Probabilistic Numerics*, Proceedings of machine learning research, vol. 271: 138–46. <https://proceedings.mlr.press/v271/hou25a.html>.

</div>

<div id="ref-ilyas2026" class="csl-entry">

Ilyas, Andrew, Joonhyuk Ko, Jingwu Tang, Steven Wu, and Jiahao Zhang. 2026. “Provably Label-Efficient Conformal Prediction.” *Proceedings of the International Conference on Machine Learning*, Proceedings of machine learning research, vol. 306: 49578–97. <https://proceedings.mlr.press/v306/ilyas26a.html>.

</div>

<div id="ref-jacobson2025" class="csl-entry">

Jacobson, Tate, Jie Ding, and Hui Zou. 2025. “<span class="nocase">Predicting 5G throughput with BAMMO, a boosted additive model for data with missing observations</span>.” *Journal of the Royal Statistical Society Series C: Applied Statistics* 74 (1): 249–73. <https://doi.org/10.1093/jrsssc/qlae054>.

</div>

<div id="ref-kousias2024data" class="csl-entry">

Kousias, Konstantinos, Mohammad Rajiullah, Giuseppe Caso, Usman Ali, et al. 2024. “<span class="nocase">A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements</span>.” *IEEE Communications Magazine* 62 (5): 44–49. <https://doi.org/10.1109/mcom.011.2200707>.

</div>

<div id="ref-kousias2024model" class="csl-entry">

Kousias, Konstantinos, Mohammad Rajiullah, Giuseppe Caso, Ozgu Alay, et al. 2024. “<span class="nocase">Empirical performance analysis and ML-based modeling of 5G non-standalone networks</span>.” *Computer Networks* 241: 110207. <https://doi.org/10.1016/j.comnet.2024.110207>.

</div>

<div id="ref-lin2022" class="csl-entry">

Lin, Zhen, Shubhendu Trivedi, and Jimeng Sun. 2022. “<span class="nocase">Conformal Prediction with Temporal Quantile Adjustments</span>.” *Advances in Neural Information Processing Systems* 35: 31017–30. <https://doi.org/10.52202/068431-2249>.

</div>

<div id="ref-min2026" class="csl-entry">

Min, Yizhou, Yizhou Lu, Lanqi Li, Zhen Zhang, and Jiaye Teng. 2026. “<span class="nocase">Questioning the Coverage-Length Metric in Conformal Prediction: When Shorter Intervals Are Not Better</span>.” *Proceedings of the International Conference on Machine Learning*, Proceedings of machine learning research, vol. 306: 88935–63. <https://proceedings.mlr.press/v306/min26c.html>.

</div>

<div id="ref-narayanan2020" class="csl-entry">

Narayanan, Arvind, Eman Ramadan, Rishabh Mehta, et al. 2020. “<span class="nocase">Lumos5G: Mapping and Predicting Commercial mmWave 5G Throughput</span>.” *Proceedings of the ACM Internet Measurement Conference*, 176–93. <https://doi.org/10.1145/3419394.3423629>.

</div>

<div id="ref-podkopaev2024" class="csl-entry">

Podkopaev, Aleksandr, Dong Xu, and Kuang-Chih Lee. 2024. “<span class="nocase">Adaptive Conformal Inference by Betting</span>.” *Proceedings of the International Conference on Machine Learning*, Proceedings of machine learning research, vol. 235: 40886–907. <https://proceedings.mlr.press/v235/podkopaev24a.html>.

</div>

<div id="ref-raca2020" class="csl-entry">

Raca, Darijo, Dylan Leahy, Cormac J. Sreenan, and Jason J. Quinlan. 2020. “<span class="nocase">Beyond throughput, the next generation: a 5G dataset with channel and context metrics</span>.” *Proceedings of the 11th ACM Multimedia Systems Conference*, 303–8. <https://doi.org/10.1145/3339825.3394938>.

</div>

<div id="ref-raca2024" class="csl-entry">

Raca, Darijo, Ahmed H. Zahran, Cormac J. Sreenan, Rakesh K. Sinha, Emir Halepovic, and Vijay Gopalakrishnan. 2024. “<span class="nocase">Device-Based Cellular Throughput Prediction for Video Streaming: Lessons From a Real-World Evaluation</span>.” *IEEE Transactions on Machine Learning in Communications and Networking* 2: 318–34. <https://doi.org/10.1109/tmlcn.2024.3352541>.

</div>

<div id="ref-sirhan2026" class="csl-entry">

Sirhan, Najem N. 2026. “<span class="nocase">Handover-Aware Conformal Throughput Intervals for Risk-Sensitive Rate Selection in Mobile 5G</span>.” *Network* 6 (4): 92. <https://doi.org/10.3390/network6040092>.

</div>

<div id="ref-tibshirani2019" class="csl-entry">

Tibshirani, Ryan J, Rina Foygel Barber, Emmanuel Candes, and Aaditya Ramdas. 2019. “Conformal Prediction Under Covariate Shift.” *Advances in Neural Information Processing Systems* 32. <https://proceedings.neurips.cc/paper_files/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html>.

</div>

<div id="ref-xu2023" class="csl-entry">

Xu, Chen, and Yao Xie. 2023. “<span class="nocase">Sequential Predictive Conformal Inference for Time Series</span>.” *Proceedings of the International Conference on Machine Learning*, Proceedings of machine learning research, vol. 202: 38707–27. <https://proceedings.mlr.press/v202/xu23r.html>.

</div>

<div id="ref-zaffran2023" class="csl-entry">

Zaffran, Margaux, Aymeric Dieuleveut, Julie Josse, and Yaniv Romano. 2023. “<span class="nocase">Conformal Prediction with Missing Values</span>.” *Proceedings of the International Conference on Machine Learning*, Proceedings of machine learning research, vol. 202: 40578–604. <https://proceedings.mlr.press/v202/zaffran23a.html>.

</div>

<div id="ref-zaffran2022" class="csl-entry">

Zaffran, Margaux, Olivier Feron, Yannig Goude, Julie Josse, and Aymeric Dieuleveut. 2022. “<span class="nocase">Adaptive Conformal Predictions for Time Series</span>.” *Proceedings of the International Conference on Machine Learning*, Proceedings of machine learning research, vol. 162: 25834–66. <https://proceedings.mlr.press/v162/zaffran22a.html>.

</div>

</div>
