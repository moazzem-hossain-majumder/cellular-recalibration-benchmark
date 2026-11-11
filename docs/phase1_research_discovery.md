# Phase 1 — Telecommunications research discovery

**Evidence checked: 8 November 2026 (Asia/Dhaka). Status: discovery completed; topic approval pending.**

This is a research decision document, not a claim of novelty, an experimental result, or a publication-ready proposal. No project implementation, model training, bulk dataset acquisition, or manuscript results were produced. Recommendations are conditional on the explicitly listed feasibility gates.

Companion documents:
- [Literature review matrix](literature_review.md)
- [Dataset provenance, access, licensing, and quality comparison](dataset_comparison.md)
- [Bangladesh industry relevance](telecom_industry_relevance.md)

## 1. Recommendation

**Recommend for approval: Cross-network reliability of cellular throughput forecasts under naturally missing telemetry and limited recalibration.**

The most defensible initial contribution is an experimental benchmark and engineering method evaluation: establish when predicted throughput bounds remain useful after changing operator, campaign, or telemetry availability, and quantify the amount of target-network data needed to recover reliability. It is not a claim to invent conformal prediction, missing-value learning, or throughput prediction.

Start with the real commercial-network PERFORM measurements and their later Chronicles release. Treat these as related measurement campaigns, not independent research institutions. Use the independently collected UCC traces as a possible external replication only after units, applications, sampling, licenses, and prediction horizons are reconciled. Lumos5G is another candidate, but mmWave propagation and download access introduce additional uncertainty. Sources and limits are in the dataset comparison.

The runner-up is **sequential detection of 5G software performance regressions with explicit control of alert burden**, using actual over-the-air RANalyzer tests. It offers stronger systems-engineering exposure, but trustworthy regression ground truth and software/environment confounding are major risks.

Neither topic should be finalized solely from the ranking: the scores differ by only 1.5 points. The approval sought is to develop one into a Phase 2 proposal, with a clear obligation to reject or redesign it if the data cannot support the question.

## 2. Search scope and strength of evidence

The discovery pass searched primary research and dataset sources for cellular throughput, uncertainty calibration, missing measurements, traffic forecasting, cross-network transfer, RF fingerprinting, NB-IoT coverage, RAN software validation, and Bangladesh connectivity evidence. Searches included IEEE/ACM publication records, university author manuscripts, Elsevier, Wiley, Springer, arXiv, Zenodo, Harvard Dataverse, institutional project sites, and BTRC. Priority was 2021–2026; older dataset and methodological papers were retained when necessary.

This is a targeted scoping review, not an exhaustive systematic review of all telecom publications. Publisher access was uneven. The matrix marks inspected full-text sections separately from abstract or indexed-text screening; a search result is not represented as a fully read paper. Direct searches deliberately sought work that would invalidate the initially attractive ideas. Sources published by the cutoff were considered; crawl dates were not treated as publication dates.

Important counterevidence:
- Handover-conditioned conformal throughput intervals and one-sided rate decisions are already studied in an October 2026 article [P6].
- Missing-feature throughput learning is already addressed by BAMMO [P5]. Missingness-conditioned conformal prediction is already addressed in general ML [P8].
- Cellular traffic conformal prediction and few-shot transfer are already combined in MetaSTNet [P10].
- Cross-receiver open-set RF fingerprinting, including temporal-shift analysis, is already investigated in a July 2026 preprint [P13].
- Software-aware, environment-adjusted regression analysis is already the core of RANalyzer [P14].

Therefore, adding SHAP, an LSTM, a transformer, or a conformal wrapper is not sufficient novelty for any shortlisted topic. The paper IDs above resolve to direct primary-source links in the literature matrix.

## 3. Research landscape

### Network performance and service reliability — strongest immediate fit

Real commercial measurements make throughput and radio-quality analysis feasible. The scientific opportunity is reliable transfer and decision-making, rather than another within-dataset accuracy comparison. Throughput is delivered data per unit time; it depends on more than received signal strength. A strong radio signal alone does not establish available capacity or low latency. The PERFORM and Chronicles studies document commercial-network performance and connectivity complexity [P3–P4].

Useful questions include calibration under changing operators, failures during telemetry gaps, and the cost of obtaining fresh measurements. End-user traces do not directly expose scheduler state, cell-wide load, or the effects of changing resource-allocation actions. They cannot by themselves establish that a new scheduler increases network capacity.

### AI-native RAN and network reliability — strong engineering value, harder attribution

RANalyzer provides a promising real-hardware software-validation direction [P14]. In contrast, ColO-RAN and twinned traffic experiments use RF emulation [P15–P16]. They are valuable supplementary test environments, but do not satisfy a claim of real commercial field evidence. Offline logged actions also do not automatically support counterfactual reinforcement-learning evaluation.

### Spatiotemporal traffic prediction — accessible but crowded

Telecom Italia enables reproducible activity forecasting, but its grid activity is not directly measured Mbps, PRB utilization, energy consumption, or congestion. Modern work already includes uncertainty and transfer [P10]. NetMob23 is richer but permission-controlled. A focused benchmark of failure under reporting gaps is more defensible than another architecture comparison; publication prospects remain modest without a new finding or method.

### RF fingerprinting and signal processing — rigorous, less directly cellular

WiSig has actual received waveforms across radios and capture days. It supports studying receiver and channel effects. Yet generic cross-receiver recognition and open-set rejection are already researched [P12–P13]. The dataset concerns Wi-Fi; it must not be marketed as measured LTE/NR authentication. Its noncommercial license limits deployment reuse.

### NB-IoT and radio-coverage engineering — feasible if measurements can be paired

LTE and NB-IoT measurement families enable an examination of cross-technology coverage prediction. Coverage analysis itself is established [P17]. A possible contribution concerns how sparse NB-IoT measurements can be supported by LTE observations without hiding errors in poorly covered areas. Receiving a signal does not establish successful sensor attachment, packet delivery, battery lifetime, or indoor coverage.

### Disaster resilience and Bangladesh-specific optimization — high value, presently data-limited

BTRC publishes infrastructure aggregates, but the reviewed public tower-count page does not supply geolocated incident histories, restoration times, failure causes, or per-site power conditions. It cannot support supervised tower-failure prediction. A Bangladesh flood-resilience model would need authorized event-level operator records and aligned flood/power data. No such dataset was verified in this discovery pass. [BTRC tower statistics](https://btrc.gov.bd/pages/static-pages/6922dbce933eb65569e0cab2).

### Directions not advanced

Customer churn is excluded by the brief. DeepSense beam tracking substantially overlaps the existing DeepSenseV2V portfolio. Massive-MIMO/channel estimation and spectrum-control ideas were not advanced because this pass did not establish a sufficiently documented, licensed field dataset with the necessary labels/actions and a stronger gap than the shortlist. That is an evidence limitation, not a statement that suitable datasets do not exist. Purely simulated 6G/RL projects do not meet the primary-evidence requirement.

## 4. Five candidate topics

### A. Cross-network reliability of cellular throughput forecasts under missing telemetry

**Problem.** A useful throughput estimate must communicate its uncertainty when radio measurements disappear or the model is applied to a new network. Overconfident estimates can cause bad service commitments; extremely conservative bounds may be operationally useless.

**Existing work and gap.** BAMMO covers missing predictors; generic missingness-aware conformal methods exist; handover-aware rate bounds exist. The narrower candidate gap is a reproducible, causally ordered evaluation of their interaction with operator/campaign shift and a limited target calibration budget. The reviewed work does not establish a universal solution to that combined deployment question. This is a provisional gap, not a first-ever claim [P5–P9].

**Research questions.** (1) Does overall coverage conceal failure for natural missingness patterns or an unseen operator? (2) How much labeled target data restores useful lower bounds? (3) Does missingness-aware calibration beat global calibration at matched operational risk and measurement budget?

**Proposed contribution.** A common-feature benchmark, transfer and calibration-budget protocol, and a parsimonious calibration strategy with fallback when a subgroup lacks support. Contribution type: new experimental evaluation plus a potentially useful combination of existing methods. Algorithmic novelty is not established.

**Data.** PERFORM 2023 release, Chronicles active/passive releases, optional UCC external replication. Availability and CC BY licenses for the Zenodo records were verified through repository metadata. Ability to align active labels with causally available covariates is not yet verified.

**Methodology to investigate.** Persistence and rolling empirical quantiles; an interpretable regression baseline; a missingness-capable boosted-tree or additive model; BAMMO where reproducible; global split calibration, adaptive calibration, and CP-MDA where assumptions apply. Avoid a new neural architecture unless simple methods expose a specific limitation. Use native missingness first; artificial masking is only a separately labeled stress test.

**Demonstration.** Leave one campaign/operator/session group out; reserve an early target prefix for calibration and a later suffix for testing. Measure lower-bound exceedance, interval coverage and width, subgroup failures, point error, inference cost, and calibration sample cost. Compare committed rate against measured achieved throughput as an offline decision proxy. This is not a demonstrated increase in radio capacity, actual playback QoE, or an SLA guarantee.

**Feasibility.** Moderate; CPU-first work with ordinary tabular tools appears reasonable. Full data sizes are modest enough to avoid mandatory GPU infrastructure, although memory and processing requirements remain estimates until schema inspection.

**Publication category.** Measurement/benchmark and network-management methodology. A focused conference paper is plausible if the transfer findings are robust; a journal requires a sufficiently broad and well-supported contribution.

**Bangladesh relevance.** RAN performance assurance, drive-test analysis, telemetry quality, and reliable model transfer between regions or network upgrades. Actual operator benefit requires local validation.

**Failure gates.** Reject forecasting if no usable temporal sequences exist; do not silently switch to contemporaneous estimation. Reject cross-operator claims if identifiers are absent. Redesign if naturally missing fields are too rare, target protocols are incompatible, or the result merely reproduces P5/P6/P8. A result with no improvement can still support a useful negative benchmark, but publication is not assured.

### B. Cellular activity forecasting under spatial transfer and interrupted reporting

**Problem.** Historical activity forecasts may deteriorate when reporting gaps are clustered or the deployment region differs from training.

**Gap and questions.** MetaSTNet already combines transfer and calibrated intervals; online reporting policies have also been studied [P10–P11]. The candidate question is which lightweight forecasting/calibration strategy remains reliable under jointly held-out geography and explicitly modeled reporting interruption. Do gains survive seasonal-naive and persistence baselines? How sensitive are conclusions to interpreting absent records?

**Contribution.** A transparent evaluation protocol and empirical reliability/complexity frontier; possible method improvement only if justified. Not a new forecasting paradigm and not a claim to be the first cross-city model.

**Data.** Telecom Italia Milan; Trentino is a potential second region once its exact release and terms are pinned. NetMob23 is conditional on approved access, not part of the guaranteed plan.

**Method.** Seasonal naive, linear autoregression, gradient boosting, and one justified spatiotemporal baseline. Preserve train-only scaling and hold out contiguous regions and future time blocks. Test real missingness if identifiable; otherwise explicitly call the interruption experiments artificial masking of real observations.

**Experimental contribution.** MAE/MASE, peak underprediction, coverage and width, regional error, memory/runtime, and degradation versus reporting-gap length. Any capacity-allocation replay is a supplementary model with declared assumptions; activity units cannot be converted into measured Mbps or energy savings.

**Feasibility/publication.** Moderate implementation, substantial novelty risk; likely a focused benchmark/workshop unless a broader finding emerges. Full grid models can be memory intensive; reduced-region analysis should be justified before inspecting results.

**Bangladesh value.** Demand monitoring and capacity-planning concepts, with limited evidence of direct operational savings.

**Main risks.** Old and heavily reused data, missing-versus-zero ambiguity, spatial leakage, and overlap with recent conformal/transfer forecasting. Stop if the contribution is only a different architecture.

### C. Calibration stress testing of RF device rejection across receivers and capture days

**Problem.** A receiver may accept an unseen transmitter or reject an enrolled device when hardware/channel conditions change.

**Gap and questions.** Cross-receiver open-set identification is already addressed by CRODA-ST, including source-only thresholding and temporal-shift analyses [P13]. The remaining candidate is an independently reproducible stress test of threshold transfer over multiple receiver/day combinations under an explicit enrollment-data budget. Does claimed rejection reliability survive new capture groups? Is target-domain adaptation worth its data and compute cost?

**Contribution.** Benchmark replication/extension and calibrated deployment policy; a genuinely new algorithm would require a later technical advance. Novelty confidence is low because the most obvious claim is already occupied.

**Data.** WiSig compact subsets or a disjoint selection from full WiSig. Subsets overlap and are not independent external validation datasets. CC BY-NC-SA 4.0 permits noncommercial research subject to its terms; commercial reuse is not authorized by that license.

**Method.** Equalized/raw-signal baselines, small CNN, established open-set scores and published adaptation methods. Split transmitter identities for unknown-device testing and receivers/days for distribution shift. Never calibrate thresholds on the held-out unknown test devices.

**Demonstration.** False acceptance and false rejection at fixed operating points; OSCR, AUROC, known-device accuracy, uncertainty over independent capture groups, and inference cost. Compare raw/equalized inputs and source-only versus budgeted adaptation.

**Feasibility/publication.** Medium-to-high complexity; a GPU is helpful, not assumed available. Signal-processing publication potential is conditional on exceeding existing cross-domain evaluation, not just reproducing it.

**Bangladesh value.** Wireless measurement, physical-layer security, IoT and private-network competence. Indirect relevance to public cellular RAN operations.

**Main risks.** One testbed, only a few capture days, no real adversarial spoofing ground truth, subset overlap, commercial licensing restrictions, and close 2026 prior art. Unseen benign radios are a proxy for unknown identities, not evidence of defeating intelligent attackers.

### D. Sequential detection of 5G software regressions under changing radio conditions

**Problem.** Throughput drops after a software update may reflect load, radio variation, or a code regression. Engineers need actionable alerts without excessive false alarms.

**Gap and questions.** RANalyzer already models environment-adjusted residuals and software risk [P14]. A candidate extension is release-forward sequential evidence accumulation: how many real tests are needed before issuing an alert, at a stated false-alert burden? Does it outperform fixed residual thresholds and classical sequential monitoring? Are apparent software effects robust to covariate and label choices?

**Contribution.** A release-aware benchmark and sequential monitoring procedure adapted from existing statistical methods. No claim of new causal identification. This is materially different from customer analytics and beam tracking.

**Data.** Actual over-the-air RANalyzer testbed records and release identifiers, CC BY 4.0. Paper and repository counts/date ranges disagree; reconcile before analysis. A public testbed is real experimental evidence, but not a commercial operator deployment.

**Method.** Reproduce the published residual detector, then compare EWMA/CUSUM or other justified sequential tests on matched workloads. Train only on earlier releases. Keep tests from the same release together. Separate detection after test completion from prediction before a test; the latter must exclude post-test BLER, loss, or throughput-derived covariates.

**Demonstration.** Alerts per release, tests-to-detection, workload-stratified reliability, calibration and runtime. Use independently documented bug/fix episodes where available. If labels are generated from the same residual threshold being evaluated, precision/recall is circular and unacceptable as the primary result.

**Feasibility/publication.** Moderate-to-high, requiring log interpretation and careful statistics. Good network-softwarization and management fit if credible labels and sufficient independent releases exist.

**Bangladesh value.** Vendor acceptance testing, change assurance, automated troubleshooting, and KPI interpretation; especially relevant skills for modern software-driven networks.

**Main risks.** Few independent regression episodes, nonrandom software deployment, incomplete environmental measurements, and data-derived labels. Without independent evidence, describe performance-anomaly detection rather than causally proven software-fault identification. Matched replays or rollback tests would materially strengthen the study but are not currently available.

### E. Sparse-measurement transfer from LTE to NB-IoT radio-coverage estimation

**Problem.** NB-IoT coverage surveys require measurement effort. Existing LTE measurements might help prioritize where more NB-IoT measurements are needed.

**Gap and questions.** Cross-technology coverage and deployment characterization already exist [P17]. The candidate is a carefully paired evaluation of the NB-IoT sample budget needed for accurate weak-coverage estimation on unseen spatial areas/operators. When does LTE-assisted transfer beat an NB-IoT-only model? Does it systematically miss weak-signal areas?

**Contribution.** Application/evaluation and measurement-budget methodology, not an assertion of a new propagation model. Novelty search confidence is lower here than for A/D; further targeted coverage-map literature review is required in Phase 2.

**Data.** PERFORM LTE/NB-IoT passive measurements. The earlier Oslo/Rome study is an external-validation lead; its current downloadable artifact/license were not verified. Co-location, timestamp tolerance, operator mapping, and frequency information are go/no-go conditions.

**Method.** Geographic interpolation, LTE-only regression, NB-IoT-only regression, and a simple calibrated multi-task/transfer model. Separate measurement locations into spatial blocks with buffers. Learn selection rules only from development regions; compare random, spatially uniform, and uncertainty-guided sampling at equal budgets.

**Demonstration.** Signal prediction error in dB, calibration, weak-signal miss rate at predeclared engineering thresholds, and performance against NB-IoT sample count. Report paired-location retention and selection bias. A scanner's detection floor is not proof of zero service availability.

**Feasibility/publication.** Moderate and CPU-feasible in principle. Applied measurement/IoT paper potential is modest unless sample-efficiency or failure-mode findings are substantial.

**Bangladesh value.** Coverage planning and IoT measurement competencies, with possible relevance to utilities and rural telemetry. No assertion that a named Bangladeshi operator currently offers the studied NB-IoT configuration.

**Main risks.** Unpairable measurements, selection on detectable cells, confounded bands and antenna configurations, limited independent geography, and no packet-delivery or power measurements. Do not claim energy, battery, or indoor reliability improvements from RSRP alone.

## 5. Defensible gap register

These are unresolved questions within the inspected evidence, not certified gaps across all literature.

| Gap | Closest counterevidence | Narrow question still worth investigating | Evidence needed / reason to reject |
|---|---|---|---|
| G1: Reliable throughput bounds under natural missingness plus network shift | BAMMO; missing-value CP; handover-aware CP | Calibration data required for useful one-sided reliability across operator/campaign and missingness groups | Harmonized field traces and strong baselines; reject if gains require future information or only random masking |
| G2: Forecast reliability under joint spatial transfer/reporting interruption | MetaSTNet; online cellular prediction; 2026 cross-city forecasting | Which existing methods remain reliable under the combined constraint at equal compute/data budget? | Real activity traces, transparent missingness semantics; reject a mere architecture ranking |
| G3: Release-forward alert reliability for RAN software changes | RANalyzer residual and risk analysis | Detection delay versus alert burden on independent future releases | Independent bug/fix evidence or clearly limited anomaly claims; reject circular labels |
| G4: Receiver/day rejection reliability at a limited enrollment budget | WiSig; CRODA-ST | Multi-group reproducibility and calibration-budget tradeoff beyond existing temporal checks | Disjoint capture/device protocol and strong published baselines; reject if existing study already answers it |
| G5: Sample-efficient LTE-assisted weak-coverage mapping | Existing LTE/NB-IoT coverage analysis | Whether transfer reduces NB-IoT sampling needs without hiding weak-coverage errors | Properly paired observations and spatial/operator holdouts; reject if pairing or novelty fails |

G1 and G3 currently have the best balance of actionable question, data credibility, and engineering value. G2/G4 are crowded; G5 has an unresolved data-alignment prerequisite. No proposal claims unqualified distribution-free coverage after arbitrary domain shift.

## 6. Weighted ranking

Scores are **analyst judgments**, not measured publication probabilities. Each criterion uses 1–5: 1 = major weakness/blocker, 3 = plausible with substantial unresolved risks, 5 = unusually strong evidence/fit. Half-points indicate intermediate judgments. Publication potential assesses the prospective contribution, not acceptance odds. Novelty scores are deliberately limited by recent prior art.

Total out of 100 = 20 × (0.25N + 0.20D + 0.15T + 0.15P + 0.15B + 0.05F + 0.05R).

| Rank | Topic | Novelty 25% | Data 20% | Technical 15% | Publication 15% | Bangladesh 15% | Feasibility 5% | Recruitment 5% | Total /100 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | A: Throughput reliability across networks | 3 | 5 | 4 | 3.5 | 4.5 | 4 | 4.5 | 79.5 |
| 2 | D: Sequential RAN regression detection | 3.5 | 4 | 4.5 | 3.5 | 4 | 3.5 | 5 | 78.0 |
| 3 | E: LTE-to-NB-IoT coverage transfer | 3 | 4 | 3.5 | 3 | 4 | 4 | 4 | 70.5 |
| 4 | C: RF rejection calibration across domains | 2.5 | 4 | 4 | 3 | 3 | 3 | 4 | 65.5 |
| 5 | B: Activity forecasting with reporting gaps | 2.5 | 4 | 3 | 2.5 | 4 | 4 | 4 | 65.0 |

**Rationale.** A's data score reflects several traceable commercial measurement releases with accessible licenses, not proven schema compatibility. D's real OTA data and systems depth are offset by label and provenance inconsistencies. E has credible passive measurements but pairing uncertainty. C has excellent signal provenance but a noncommercial license, a single testbed, and very close prior art. B is accessible but old activity data have limited engineering labels and a crowded research literature.

**Sensitivity.** Reducing A's data score from 5 to 4 lowers its total to 75.5 and makes D first. Reducing D's novelty by 0.5 lowers its total by 2.5. Thus A/D should be treated as a close decision, not an objective ordering. Access and label quality are hard gates that outweigh a weighted total. This ranking does not justify proceeding with a failed dataset.

## 7. Scientific safeguards to carry into Phase 2

These are design requirements, not the finalized experimental protocol.

1. Define whether the target is future throughput, contemporaneous estimation, or anomaly detection. Specify when every covariate becomes available. Do not use same-interval achieved throughput as a predictor of itself.
2. Group by session/capture/release and use chronological and geographic separation as appropriate. Fit scalers, imputers, feature selectors, thresholds, and hyperparameters on development data only.
3. Keep calibration separate from model selection and final testing. For target-network adaptation, spend a declared early target prefix and evaluate only later observations.
4. Use session/release/day-level uncertainty estimates. Thousands of adjacent rows are not thousands of independent experiments. Report the number of independent groups and variation across them.
5. Match baselines on features, timing, target labels, calibration budget, and tuning effort. Include simple persistence/seasonal/threshold baselines relevant to the task.
6. Distinguish native missingness from artificial masking, actual OTA measurements from RF emulation, measured performance from offline decision proxies, and real faults from inferred labels.
7. Predefine primary metrics, subgroup rules, practical effect sizes, and ablations. A narrow interval is not good if it misses too often; a zero lower bound is not useful merely because it is conservative.
8. Treat classical conformal exchangeability assumptions explicitly. Time dependence and distribution shift can invalidate finite-sample guarantees; adaptive long-run coverage is not per-session or per-subgroup safety [P8–P9].
9. Report all investigated domains and negative outcomes. Do not select only favorable routes, radios, releases, or missingness patterns.
10. Explain effects through telecom mechanisms and measurement limitations. Feature importance is associational and does not prove interference, congestion, or root cause.

## 8. Publication routes to investigate after results

No venue or submission date is selected. Scope matches below are judgments, not promises of acceptance.

- **CNSM and IEEE Transactions on Network and Service Management:** strongest conceptual fit for performance assurance, telemetry reliability, and software-change monitoring. [CNSM scope](https://cnsm-conf.org/); [TNSM](https://www.comsoc.org/publications/journals/ieee-transactions-network-and-service-management).
- **IEEE NetSoft:** natural candidate for D if the contribution is software-driven RAN validation; the RANalyzer work is an immediate comparison, not a template to recreate [P14].
- **IEEE ICC/GLOBECOM workshops or relevant symposia:** investigate for focused communication-performance or coverage contributions after identifying the eventual track and evidence depth.
- **Computer Networks:** plausible for a substantial empirical networking contribution, with P3 providing a closely related example. [Publisher article](https://doi.org/10.1016/j.comnet.2024.110207).
- **ACM IMC:** consider only if a broad measurement finding and strong reproducibility justify it; one small public-dataset ML comparison is unlikely to be sufficient. Lumos5G illustrates the measurement depth of relevant prior work [P2].
- **IEEE Open Journal of the Communications Society:** possible for an expanded, rigorous multi-campaign communication study; Chronicles provides relevant prior art [P4].
- **IEEE Access:** broad-scope fallback to investigate, not an automatic acceptance route or a substitute for novelty; WiSig's publication is an example [P12].

The 2026 CNSM dates shown on its website have already passed as of this report. Future calls, fees, indexing, review policies, and page limits must be checked when choosing a venue.

## 9. Risks that could prevent publication

The most serious risk is **insufficient incremental contribution** against 2025–2026 papers. Other decisive risks are incompatible cross-dataset measurement protocols; inadequate native missingness; no independent regression labels; small effective sample size; stale or geographically narrow data; temporal/spatial leakage; threshold selection on test outcomes; relying on a simulated action outcome to claim network improvement; and licensing constraints that prevent reproducibility.

A technically correct negative finding can be publishable if it changes understanding and is supported across meaningful settings. It is not publishable merely because many models were evaluated. A polished repository or manuscript cannot compensate for an unsupported claim.

## 10. Approval boundary

**Phase 1 stops here.** Recommended approval: A, subject to a Phase 2 proposal that makes the novelty and data-alignment gates explicit. D is a strong alternative if software/network systems engineering is the preferred emphasis. No final topic has been selected, and no Phase 2 proposal, dataset-processing pipeline, or experiment has been started.
