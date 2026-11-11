# Research proposal — Topic A

**Version 1.0 · 8 November 2026 · Phase 2 complete, awaiting proposal approval**

**Working title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*

Topic A is the sole selected direction. Topic D is not included. This document specifies proposed experiments, not results. Dataset acquisition, suitability verification and implementation remain subsequent phases. Numerical settings below are design choices, not measured properties of the datasets or operator requirements.

## 1. Plain-language overview

A network model can predict a plausible average speed yet be unsafe to rely on when some measurements disappear or it is moved to a different network. Our project asks how often its conservative throughput predictions fail, how useful those predictions remain, and how much new measurement data is needed to improve them.

For example, a prediction of 40 Mbps and a conservative lower bound of 25 Mbps mean different things. The point prediction estimates a typical outcome; the lower bound is intended to be exceeded by the observed throughput at a chosen frequency. These example numbers are illustrative. We will test the achieved frequency rather than promise it in advance.

The central scientific output is a reproducible characterization of **reliability versus target-network measurement budget**. A small missingness-aware calibration procedure is a candidate to evaluate, not an assumed winner. A credible result might show that simple global recalibration is preferable, or that transfer fails despite recalibration.

## 2. Research problem and scope

The question is:

> When a throughput predictor trained on one commercial cellular measurement domain is transferred to another, how do naturally missing radio measurements affect one-sided forecast reliability, and how much labeled target-domain data is needed to obtain useful lower bounds?

A domain means a documented operator × campaign × measurement-protocol combination, with device and radio technology recorded. Operator identifiers must come from documentation; they must not be inferred from performance. A campaign change within one operator is temporal transfer; a device/application change is measurement-domain transfer. These are distinct experiments and will not all be called cross-operator validation.

Primary scope: real, documented downlink measurement tests on LTE/5G NSA, with causally available predictors. No scheduling control, reinforcement learning, beam selection, churn, tower-failure prediction, or new radio hardware is proposed. We do not claim that achieved application throughput is unused cell capacity.

## 3. Prior work and precise novelty boundary

The prior-art review narrows rather than guarantees novelty:

- **BAMMO [1]** already handles missing predictors in cellular throughput modeling; its discussion identifies geographical transfer as further work. We cannot claim to invent missing-data throughput prediction.
- **Zaffran et al. [2]** already study conformal prediction with missing values and pattern-conditional coverage. We cannot claim that conditioning on a missingness pattern is a new general method.
- **Gibbs and Candès [3]** already provide adaptive conformal inference for distribution shift. Long-run adaptation does not itself establish useful bounds for every radio regime or target campaign.
- **Sirhan [4]** already evaluates handover/RAT-conditioned intervals and lower bounds on commercial traces, including fallback for small groups. It reports different conclusions for interval coverage and rate-selection objectives. Our proposed contribution cannot be a grouping/fallback rule alone.
- **Commercial-network studies [5–7]** establish the measurement setting and network evolution. Repeating their descriptive analysis or dual-connectivity classification would not be a contribution.

The proposed incremental contribution is the **joint evaluation of natural telemetry missingness, explicit source-to-target transfer and a finite target-label budget**, under a frozen forward evaluation and common prediction task. It is primarily an experimental/methodological contribution in telecommunications, not a new ML theorem or architecture.

Candidate claims, each requiring evidence:

1. **Benchmark claim:** the released protocol isolates transfer and recalibration costs without future information. Evidence: versioned domain manifests, timestamp audit, duplicate audit, fixed test windows and reproducible comparisons.
2. **Empirical finding claim:** native missingness groups have materially different transfer reliability. Evidence: group support, effect sizes and clustered uncertainty across independent sessions/domains. If this is absent, report it rather than manufacture a pattern with masking.
3. **Practical method claim:** the proposed calibration rule improves reliability/usefulness at the same budget. Evidence: fair global/grouped/adaptive/quantile baselines and ablations; no claim if the advantage is inconclusive.
4. **Measurement-budget claim:** a specified amount of calibration data is sufficient in the evaluated domains. Evidence: a prespecified budget curve and held-out results; never extrapolate this into a universal operator requirement.

No 'first-ever' wording is approved. The search is a targeted review, not a proof of absence. Full publisher access to [1] and [4] was intermittent; accessible publisher-indexed methods/discussion were examined. Recheck versions and recent citations before freezing the implementation protocol and before submission. If equivalent work is found, revise the claimed increment before running final experiments.

## 4. Questions, hypotheses and objectives

**RQ1 — Transfer failure:** How do coverage and usable lower bounds change between within-domain evaluation and held-out operator/campaign evaluation?

Hypothesis H1: source-only calibration has greater violation rates or more conservative bounds in at least some target domains. The null is that no practically meaningful deterioration occurs. Report both possibilities.

**RQ2 — Native missingness:** Does aggregate performance conceal worse reliability for observed missingness groups, after separating radio technology, protocol and feature staleness?

H2: some missingness groups have worse calibrated performance. This is an association, not proof that missing values cause poor throughput. Report raw and RAT-stratified results; structural absence of an NR field on an LTE-only observation must not be interpreted as a logger fault.

**RQ3 — Measurement budget:** How does lower-bound reliability and usefulness change with 0, 1, 2, 5 and 10 target calibration sessions?

H3: additional target sessions help, but gains may be nonmonotonic or domain-specific. Report row count, elapsed collection time and session count, rather than calling correlated rows independent labels.

**RQ4 — Method tradeoff:** Does missingness-aware calibration improve the joint violation/usefulness tradeoff over global calibration and established missing-value/adaptive methods at equal information budgets?

H4: a coarse missingness-aware rule can help some domains without universal dominance. This hypothesis may fail; retaining a global method is an acceptable technical outcome.

Objectives: verify data/feature provenance; define a reproducible transfer task; establish meaningful baselines; characterize subgroup failures and calibration cost; test the proposed rule; document negative results and limitations.

## 5. Dataset decision

### Selected primary collection family

Use **PERFORM's commercial measurement releases**:

- Earlier campaign: [Zenodo 8224890](https://zenodo.org/records/8224890), *A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements*.
- Later campaign: [Chronicles active measurements, Zenodo 14073311](https://zenodo.org/records/14073311).
- Passive companion: [Zenodo 17208870](https://zenodo.org/records/17208870), only if documentation establishes a valid connection to the active measurements.

Phase 1 verified CC BY 4.0 in their API metadata. This is a dataset-family selection, conditional on Phase 3 suitability. The earlier record contains a throughput-test CSV and separate passive files. The later paper describes active tests including Speedtest. Neither fact establishes that the files contain dense one-second forecasting sequences [5–7].

**Important refinement from discovery:** do not promise a one-second forecast from these records. The primary task below predicts a subsequent completed measurement test, with the actual lead time and test duration reported. If the files only support contemporaneous estimation, this proposal fails its forecasting gate; the task will not be quietly relabeled.

No whole-dataset active/passive join is assumed. Independently collected passive scans cannot become predictors merely because their coordinates are nearby. Prefer causal radio fields already attached to the active log. Supplemental joining is allowed only with documented device/session identity, time synchronization and a justified past-only tolerance.

### Independent replication

The [UCC production 5G dataset](https://github.com/uccmisl/5Gdataset) is the selected optional external replication candidate [8]. Its data-license scope, task timing and download versus streaming behavior must be checked. It will be analyzed as a separate protocol unless comparability is demonstrated. Its accompanying simulation is excluded.

Lumos5G is a reserve data lead, not an automatic replacement. A replacement primary collection or a substantive prediction-task change requires a documented proposal amendment and approval. PERFORM and Chronicles share collaborators and possibly older measurements; they do not count as two independent collection teams.

## 6. Task definition and telecom concepts

### Prediction time and outcome

For a documented continuous measurement sequence, let test j start at a_j, end at b_j, and report achieved downlink throughput y_j in Mbps. Predict y_j immediately before a_j using only information available by that time. The preceding test's throughput may be used only if it finished and its result was available before a_j. A same-test result, mean signal computed over the test, or future serving cell is prohibited.

Retain the recorded test's throughput definition and averaging procedure; do not reconstruct it by an incompatible mean of rates. If byte/time counters permit an independent audit, compare definitions explicitly. Store test duration b_j−a_j and time since the last completed measurement as metadata. Duration is a predictor only if scheduled/known beforehand; realized duration is not.

A forecast row requires at least one prior completed throughput measurement in the same sequence. Require the latest completed measurement to be no more than **60 seconds old** for the primary analysis. Evaluate 30- and 120-second freshness limits as prespecified sensitivity checks, not opportunities to choose the most favorable cohort. If the primary cutoff yields inadequate support, return to design review.

**Budget accounting clarification:** a causal predictor using past throughput consumes target outcomes as history, even when the calibrator is frozen. Therefore K measures sessions admitted to **calibrator fitting**, not all measurements acquired or all target labels visible to the system. Every method receives identical causal history; report historical-feature observations, calibration observations and online updates separately. The primary study cannot claim that only K sessions of total measurement collection were needed. A secondary radio-only predictor without target-throughput lags can examine a stricter label-access budget, using source-only fallback features; it is a separate information setting, not a direct like-for-like comparison. Monetary or probe-traffic savings require actual measurement-cost data and are outside the current claim.

The target is next-test achieved throughput, not a fixed one-second horizon. All reporting must state the distribution of lead times and test durations. Never bridge unrelated sessions to manufacture a time series.

### Features and meanings

- Previous completed throughput and up to three past observations; include their ages and missing-history indicators. Do not require three observations to retain a row.
- Documented LTE/NR RSRP, RSRQ and SINR/RSSNR where available and comparable, plus availability masks and age. RSRP concerns reference-signal power; SINR concerns signal relative to interference/noise. They do not directly measure free capacity.
- Radio access technology (RAT), which distinguishes technology states. Non-standalone 5G relies on LTE-related infrastructure, so missing NR fields may have a structural meaning.
- Serving-cell change indicator only from past observations with documented identifiers. It is not proof of an independently logged handover event.
- Speed and time-of-day only if consistently documented and available in the target. GPS, raw cell IDs, operator ID and campaign ID are excluded from the primary predictor to reduce geographical/domain memorization. IDs remain for grouping and audit.

Select the common feature schema from documentation before examining target test outcomes. Distinguish unsupported fields, structurally inapplicable fields, acquisition failures, stale measurements and unknown sentinels. Do not label every blank as an outage. No interpolation using future observations; no filling missing target throughput with zero. Measured zero throughput stays in the primary evaluation.

## 7. Proposed method and mathematical formulation

Let x_t contain available past information, m_t its telemetry-availability mask, and f(x_t,m_t) a nonnegative point prediction in Mbps. Fit f using source training data only. All methods in the core calibration comparison use this same fixed predictor.

On a separate calibration set define signed overprediction scores:

    s_i = f(x_i,m_i) − y_i.

For target violation level alpha=0.10 and n calibration observations, take k=ceil((n+1)(1−alpha)). Let q be the kth ordered score; if k>n, define q=+infinity. Return the lower bound:

    L_t = max(0, f(x_t,m_t) − q).

Then y_t < L_t is a lower-bound violation. Taking a conservative quantile of overprediction errors reduces optimistic predictions. Negative scores and negative quantiles are permitted; do not silently take absolute residuals, which correspond to a different task. If q is infinite, return L=0 with an insufficient-support flag. Throughput's nonnegative support justifies clipping below zero.

Under the applicable exchangeability assumptions, standard split-conformal reasoning supports marginal coverage [2]. Our temporal and cross-domain data may violate those assumptions. **We make no new finite-sample guarantee under arbitrary network shift.** All deployment reliability claims here are empirical. Row-based n is not an assertion of n independent observations.

### Candidate: coarse missingness-aware calibration with support fallback

Use a predeclared four-way availability grouping: LTE radio bundle observed/not fully observed × NR radio bundle observed/not fully observed. A bundle comprises only the fields retained in the frozen common schema. Preserve separate structural-missingness annotations and report RAT-stratified metrics. If a common bundle cannot be meaningfully defined, the method-design gate fails.

For a prediction, use the matching calibration group's signed-score quantile only when it contains at least **100 calibration rows from at least five distinct measurement sessions**. Otherwise use the pooled calibration quantile. If pooled calibration is empty, use the frozen source calibration quantile and explicitly label this source fallback. A wholly unknown group falls back; it never receives a test-derived quantile.

These support thresholds are pragmatic study settings, not validity theorems. Grouping/fallback are established ideas, including in [4]. Our contribution would be evidence about their behavior under the specified transfer and budget constraints, not inventing them. Sensitivity: 50/200 rows and 3/10 sessions, evaluated only as declared secondary analyses.

### Static and online tracks

The **primary track is static**: after the calibration prefix, f, q, grouping and parameters are frozen for the test suffix. No test outcomes update the model.

A **secondary online track** compares established adaptive conformal methods [3] and a rolling-window quantile baseline. It may update only after a label actually arrives. Its cumulative label cost includes every revealed test outcome. Never compare an online method consuming all labels with a static method consuming a small prefix as though their budgets were equal. A one-sided adaptation must be documented as an adaptation, not an exact reproduction of a published two-sided method.

## 8. Baselines and fair comparison

### Point-prediction baselines

1. Persistence: most recent completed throughput. Essential for slowly varying links.
2. Ridge regression on causal lag/radio features with train-only imputation and missingness indicators. Interpretable low-complexity comparator.
3. Histogram gradient boosting with native missing-value handling and explicit age/mask features. Proposed common predictor for the core calibration experiment; chosen for tabular suitability, not an assumed result.
4. BAMMO using the authors' implementation where reproducible [1]. It is a required closest methodological comparator for a strong missingness contribution. If its implementation cannot be reproduced fairly, document why and lower the strength of the comparison; do not omit it silently.

### Reliability baselines

Use the same feature information, target prefixes and test sets:

- Uncalibrated point commitment, showing the cost of optimism.
- Recent empirical throughput lower quantile, with a source fallback when history is insufficient.
- Source-only global conformal lower bound (zero target labels).
- Target-prefix global recalibration on the fixed predictor (principal comparator).
- RAT-group calibration with support fallback, to distinguish missingness information from technology state.
- Lower-quantile regression at alpha and its one-sided recalibrated version, trained on source data.
- CP-MDA from [2] where its assumptions/input representation apply. First reproduce its documented interval setting; a one-sided extension must be described and validated separately, with no inherited guarantee asserted without justification.
- Proposed missingness grouping, using exactly the same target labels as global/RAT calibration.

Adaptive/rolling calibration belongs in the secondary online track. A same-budget target-retrained model is a secondary comparator to test whether retraining is preferable to calibration-only adaptation; its training/calibration labels must be disjoint and fully charged to the budget. A model trained on abundant target data is an explicitly labeled reference, never a fair low-budget competitor.

For source predictor tuning, use a maximum of 30 development-only configurations per tunable method, identical chronological validation folds where feasible, and record CPU time. Tune point models on MAE and quantile models on pinball loss. Do not choose the common predictor or grouping by target final-test performance. Seeds for stochastic training: 11, 23, 37, 51, 79; deterministic methods run once. Seeds are not independent network deployments.

## 9. Data separation and calibration-budget protocol

### Source development

Group by original session and collection day; sessions from the same day stay in the same partition. Deduplicate before splitting, including overlaps between releases. Within eligible source domains use chronological blocks: earliest 60% of days for fitting, next 20% for development, final 20% for source calibration. Round at day boundaries and disclose actual proportions. Require at least two distinct days per source partition; otherwise revise the design before final experiments.

For multi-domain sources, fit only on source domains; the target has no role in hyperparameter selection. Use forward validation inside development if enough groups exist. Source calibration labels are not reused for model fitting after the predictor is frozen.

For a prospective chronological transfer claim, all source training, tuning and calibration information must precede the target test period. Cross-operator comparisons that cannot meet this calendar ordering may be reported only as retrospective domain-transfer experiments, clearly separated from prospective campaign-transfer evidence. The proposal does not assume that all operator campaigns overlap in time.

### Target partition

Order target collection days chronologically. Reserve the earliest 40% of days as a potential calibration pool and the remaining 60% as the **same fixed test suffix for all budgets and methods**. Do not allow a longer calibration budget to move the test set forward. Use complete sessions and keep day boundaries disjoint. Evaluation windows must not overlap the outcomes used for calibration.

Budgets are the first K whole sessions within that pool, K in {0,1,2,5,10}. Keep sessions in timestamp order with a stable ID tie-breaker. Unsupported budgets are marked unavailable, not replaced with sampled rows. The maximum-budget prefix must lie entirely before the test suffix. Report its number of days, rows and elapsed time. Include a row-budget sensitivity using prefix rows, labeled as a distinct correlated-observation budget, not as more independent evidence.

Source-only and smaller-budget methods wait through the unused calibration-pool period and are evaluated on the same suffix. Missing history at a test-session start is handled consistently; no calibration session is spliced into an unrelated target session. Report warm-up exclusions and denominator changes.

### Transfer experiments

- E0: within-domain chronological reference using the same preparation rules.
- E1: earlier campaign to later campaign for the same documented operator and comparable protocol.
- E2: held-out operator within a comparable campaign/protocol; evaluate each eligible direction, not just the best one.
- E3: joint campaign/operator shift where support exists, explicitly labeled a combined shift.
- E4: optional UCC independent-protocol replication. Separate results unless actual target/feature compatibility is established.

Preserve device/protocol strata and avoid attributing their changes solely to operator effects. Use every direction meeting the preregistered eligibility rules. Target domains must never become a tuning set for reporting other confirmatory target-domain results; exploratory cross-domain development must use separate source/development domains or be clearly labeled exploratory.

## 10. Evaluation metrics and decision rules

**Primary nominal setting:** alpha=0.10. Secondary alpha values: 0.05 and 0.20. These are experimental settings, not operator SLAs.

For a test set of N measurements:

- Violation rate V = mean[ y_t < L_t ]. Desired nominal behavior is V≤alpha, evaluated with uncertainty.
- Supported-rate fraction U = sum min(L_t,y_t) / sum y_t. This is an offline throughput-based proxy, not measured network utilization. If sum y=0, U is undefined and that stratum is reported separately.
- Mean committed lower bound in Mbps and fraction of L=0 outputs. An all-zero policy is reliable but uninformative.
- Overcommitment magnitude mean max(L_t−y_t,0), in Mbps.
- Point MAE/RMSE; quantile pinball loss for appropriate methods. Report both absolute and domain-normalized summaries using source-only scales.
- Subgroup violation, U, zero-bound fraction and sample/session counts for RAT and native missingness states; staleness strata as secondary analysis.
- Fit time, inference latency, calibration time, peak memory, and target measurement cost.

Report session-macro and row-micro estimates side by side; use equal-weight domain summaries for cross-domain comparisons. The primary inferential comparison uses session-macro V and the corresponding session-macro supported-rate fraction, with all-zero sessions listed separately for U. This changes the estimand from a row-level conformal statement; we explicitly evaluate empirical session reliability rather than claim a session guarantee from row calibration.

**Prespecified practical criteria:** tolerance delta=0.02 absolute violation rate; useful-effect target=0.03 absolute increase in U. These are research screening thresholds to make conclusions falsifiable, not universal engineering requirements.

At each budget compare the proposed rule against global target recalibration at fixed nominal alpha. A method is only called empirically acceptable on an evaluated domain when the one-sided 95% upper uncertainty bound for V is ≤alpha+delta. A useful improvement claim additionally requires the paired 95% lower bound for its U difference to exceed zero and the point estimate to exceed 0.03. Require confirmation in at least two eligible transfer domains; disclose failures elsewhere. These tests do not certify deployment safety.

If no method meets the reliability criterion, report that no tested budget established useful reliability. If confidence intervals are too wide, report insufficient evidence. Do not tune alpha or discard test rows to force acceptance.

The smallest qualifying K can be reported descriptively as an observed budget on these held-out domains. Choosing K from the same test curve does not prove it will work on a new deployment. A deployment recommendation needs budget selection on development domains followed by independent validation on unseen domains.

Test-set risk/usefulness curves are descriptive only. A threshold chosen using achieved test risk must not be presented as an operational policy selected without test labels. Any actionable threshold is chosen on development/calibration data and frozen before testing.

## 11. Statistical analysis

Use paired resampling of collection days, retaining complete sessions and all their observations. Use 2,000 bootstrap replicates with a fixed recorded seed. This reflects within-day dependence; also perform a moving-block-of-days sensitivity when chronological support permits. Resample differences on identical groups for paired method comparisons. Do not bootstrap individual rows as independent trials or treat random seeds as independent datasets.

At least ten held-out collection days per confirmatory target domain are a pragmatic minimum for clustered inference, not a proof of adequate power. With fewer days, results are exploratory and cannot support the planned confirmatory claim. At least five test sessions and 200 observations are required to give a subgroup its own descriptive interval; small groups remain visible with counts and an insufficient-support label. Eligibility depends on metadata/support, never observed method performance.

Estimate prospective precision from source/development variation after Phase 3; document whether the available groups can distinguish the declared effect. If not, narrow the claim or acquire additional approved data rather than reduce the effect threshold after seeing results.

For inferential tests across multiple budgets/domains, designate the largest common prespecified budget as the primary comparison before test access. Report Holm-adjusted tests for secondary families if p-values are used, and emphasize effect sizes/intervals. Unsupported domains are not pooled to create artificial significance. A small number of domains limits all generalization claims even with many rows.

## 12. Ablations, robustness and failure analysis

Primary ablations: remove missingness grouping while keeping the predictor fixed; replace it with RAT grouping; omit explicit mask predictors while preserving the learner's native missing handling; remove staleness features; compare pooled fallback with an explicit zero-bound insufficient-support output; repeat the calibration comparison with persistence to test dependence on the learned predictor.

Sensitivity: calibration support thresholds; freshness limits; alpha; feature intersection versus documented domain-specific features (separate task); session lengths; source-only versus target recalibration; and zero-throughput prevalence. Positive-throughput-only reporting is diagnostic and must not replace the all-observation primary result, since selecting by future y changes the task.

Supplementary stress tests: remove 10%, 30% and 50% of otherwise observed radio bundles with fixed seeds; mask contiguous telemetry runs where timing exists. Label these **artificial missingness on real measurements**. They cannot establish the existence or frequency of natural operator failures. Do not synthesize throughput outcomes or claim causal missingness effects.

Inspect failures by radio state, mobility, timestamp age and protocol where documented. Show representative preselected high-error and typical sessions without cherry-picking only favorable narratives. Explainability will prioritize feature ablation and telecom interpretations; any feature importance is associational, not proof of interference or congestion.

## 13. Phase 3 pass/fail conditions

Before implementation, produce a signed-off dataset suitability report answering:

1. Are exact versions, hashes, licenses and attribution requirements preserved?
2. Are test start/end times, throughput units and result-availability timing established? If not, forecasting fails.
3. Are there real sequential tests with prior outcomes and radio features available before prediction? If only same-test summaries exist, stop and propose redesign.
4. Can at least two scientifically meaningful source-to-target comparisons be formed? If only one operator exists, remove cross-operator claims through an approved amendment.
5. Are original sessions/days identifiable with sufficient independent support for the chosen inference? Never derive independence from arbitrary row chunks.
6. Are there meaningful native availability differences in at least one core radio bundle, across multiple sessions/domains? If all missingness is structural RAT absence, narrow the hypothesis or return to design.
7. Are joins legitimate and sentinel meanings documented? Unresolved fields are excluded with reasons, not guessed.
8. Can the calibration prefixes and fixed test suffixes support the proposed budgets without overlap?
9. Can the common task be implemented without mixing incompatible applications, protocols or target definitions?
10. Does refreshed prior-art review leave a defensible incremental contribution?

Failure returns to research design. It does not automatically switch to Topic D or authorize new data collection. These stringent gates may reject the selected collection; that is preferable to constructing an invalid experiment. Data quality analysis can inspect schema, counts and support in Phase 3, but final-test model performance remains unopened until methods are frozen.

## 14. Technical plan and reproducibility

Planned stack: Python, pandas/NumPy, SciPy, scikit-learn and Matplotlib; R or another required runtime only if needed for faithful BAMMO reproduction. No deep-learning framework, database, API or dashboard is presently justified. A CPU-first workflow is intended; exact RAM/runtime requirements remain unverified. Discuss hardware only after file inspection establishes actual needs.

Future repository artifacts: immutable raw-data manifest, source-attributed download instructions, schema and temporal-alignment audit, split manifests, experiment configuration, baseline/method implementation, tests, per-observation predictions, per-group metrics, figures, claim-to-result ledger and reproduction instructions. Store dataset hashes and configurations with each run. Preserve code/data licenses separately.

Future tests should cover causal feature timing, no overlapping outcomes across partitions, train-only preprocessing, zero/missing target distinctions, signed-score quantile edge cases, fallback determinism, fixed test cohorts across budgets, and metric behavior for all-zero sessions. No implementation or tests are written in Phase 2.

Planned figures: domain/measurement coverage; native missingness and staleness profiles; violation and usefulness versus calibration budget; subgroup reliability; paired method differences; ablation/runtime results. No placeholder result figures or invented tables will be produced.

## 15. Limitations and industry interpretation

Observed throughput includes device, transport, server and application effects. A Speedtest-style test is not equivalent to streaming goodput or unused scheduler capacity. Changes in devices, bands and measurement software can confound a cross-network comparison. Missingness may indicate technology state or measurement failure rather than propagation quality. Native missing outcomes cannot be assumed missing at random; missing-label rates and selection bias must be reported.

Existing traces are geographically and temporally limited. PERFORM and Chronicles are related collections, and independent replication remains conditional. Time dependence and shift prevent an unconditional statistical guarantee. Sparse calibration groups may force conservative zero bounds, making reliability operationally unhelpful.

Bangladesh relevance is performance-assurance competence: interpreting radio KPIs, auditing telemetry, testing transfer and quantifying measurement needs. No result will be attributed to Grameenphone, Banglalink, Robi or Teletalk without authorized local evidence. Live throughput improvement, reduced cost, improved QoE and congestion mitigation require separate operator trials. See [industry assessment](telecom_industry_relevance.md).

## 16. Milestones and decision outcomes

- **Now — Phase 2:** review and approve this proposal. No experiment result is available.
- **Phase 3:** acquire approved records, verify licenses/integrity, inspect documentation and data quality, and decide whether the forecasting/transfer task passes. Freeze any metadata-driven amendments before implementation.
- **Phase 4:** implement causal preprocessing, baselines, calibration methods, manifests and integrity tests.
- **Phase 5:** run frozen development/confirmatory experiments, ablations and robustness analyses; retain failures.
- **Phase 6 onward:** write from actual findings, select a suitable venue, complete portfolio artifacts, and critically review the submission.

Possible outcomes: useful method improvement; an informative benchmark showing simpler approaches are preferable; inconclusive evidence requiring more independent measurements; or rejection/redesign of the topic because the data/gap do not support it. A publication is an objective, not a guaranteed milestone. No venue is selected in this phase.

## 17. References and verification notes

[1] T. Jacobson, J. Ding and H. Zou, *Predicting 5G throughput with BAMMO, a boosted additive model for data with missing observations*, JRSS C, 74(1), 249–273, 2025 (online 2024). [DOI 10.1093/jrsssc/qlae054](https://doi.org/10.1093/jrsssc/qlae054). Publisher-indexed text reviewed; direct page access intermittent.

[2] M. Zaffran, A. Dieuleveut, J. Josse and Y. Romano, *Conformal Prediction with Missing Values*, ICML, PMLR 202, 40578–40604, 2023. [Official proceedings and paper](https://proceedings.mlr.press/v202/zaffran23a.html). Primary record and PDF accessed; exact assumptions must accompany any reproduced guarantee.

[3] I. Gibbs and E. Candès, *Adaptive Conformal Inference Under Distribution Shift*, NeurIPS 34, 2021. [Official proceedings](https://proceedings.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html).

[4] N. N. Sirhan, *Handover-Aware Conformal Throughput Intervals for Risk-Sensitive Rate Selection in Mobile 5G*, Network 6(4), 92, 2026. [DOI 10.3390/network6040092](https://doi.org/10.3390/network6040092). Publisher-indexed methods/results inspected; direct opening rate-limited. We do not adopt its claimed guarantees without checking assumptions independently.

[5] K. Kousias et al., *A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements*, IEEE Communications Magazine, 62(5), 44–49, 2024. [Dataset and paper citation](https://zenodo.org/records/8224890); DOI 10.1109/MCOM.011.2200707.

[6] G. Caso et al., *The Chronicles of 5G Non-Standalone: An Empirical Analysis of Performance and Service Evolution*, IEEE Open Journal of the Communications Society, 2024. [Institutional manuscript](https://iris.uniroma1.it/retrieve/f9a290b3-fc8b-4b41-bbe5-2d482862c261/Caso_Chronicles_2024.pdf); [active release](https://zenodo.org/records/14073311); [passive release](https://zenodo.org/records/17208870). Full final bibliographic metadata remain to be reconciled; dataset identifiers are explicit.

[7] K. Kousias et al., *Empirical performance analysis and ML-based modeling of 5G non-standalone networks*, Computer Networks 241, 110207, 2024. [DOI 10.1016/j.comnet.2024.110207](https://doi.org/10.1016/j.comnet.2024.110207).

[8] D. Raca, D. Leahy, C. J. Sreenan and J. J. Quinlan, *Beyond Throughput, The Next Generation: A 5G Dataset with Channel and Context Metrics*, ACM MMSys, 303–308, 2020. [DOI 10.1145/3339825.3394938](https://doi.org/10.1145/3339825.3394938); [original repository](https://github.com/uccmisl/5Gdataset).

## Approval requested

Approve this single-topic proposal to proceed to **Phase 3: Dataset Acquisition and Verification**, beginning with the selected PERFORM/Chronicles records. Approval is for suitability verification, not an assertion that the datasets already pass, that a method will outperform baselines, or that publication is assured. Stop after this Phase 2 deliverable until the user approves.
