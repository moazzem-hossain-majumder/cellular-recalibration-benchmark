# What the literature changes for MARUR

The review strengthens the positioning, but does not raise the project's results or establish a new algorithm. The current contribution remains primarily empirical: an auditable cellular decision process with limited attempts, delayed/unsuccessful feedback, explicit unresolved outcomes, and matched-cost evaluation. Current evidence does not establish universal superiority or formal positive-conditional risk control.

## Claims to narrow

- Sirhan (2026) already evaluates conformal throughput bounds through rate-selection utility. One-sided bounds and operational utility alone are not novelty.
- Zaffran et al. (2023) and BAMMO address missing predictors. Claiming to be the first missingness-aware throughput framework would be too broad.
- Ilyas et al. (2026), Ge et al. (2025), and Hou et al. (2025) already study label costs, partial observations, and sporadic feedback. Combining querying with calibration is insufficient for an algorithmic novelty claim.
- Gauthier et al. (2026) provide a dedicated adaptive-coverage construction. MARUR's pattern gate does not inherit that validity.
- Raca et al. (2024) have live smartphone/streaming evidence. Trace replay cannot be presented as equally strong deployment evidence.

The strongest present claim is narrower: **under outcome-independent prediction opportunities, distinguish feedback acquisition cost from information actually used, and determine when apparent reliability gains reflect useful conservative commitments versus abstention.** This is testable and relevant even when a proposed controller loses.

## Highest-priority improvement experiment

Investigate whether **information freshness**, rather than completion of any response, should drive recalibration. The implementation resets `last_ready` and `last_pattern` after unsuccessful responses, including responses discarded by DropMissing. A failed response therefore changes future query timing even when it contributes no measured label. This is a design choice, not automatically a bug.

Freeze the prediction model, initial ten successful observations, schedule, windows, quantiles, gates, and maximum new attempts. Compare the existing completed-response clock against a clock updated only by successfully observed labels. Log three times separately: latest attempt, latest completed response, and latest successfully observed calibration label. Also retain the latest admitted score time, because a conservative bound score is admitted information without being an observed label. Never conflate those clocks.

Specify the failed-query backoff in advance: an observation-freshness trigger without backoff may consume its entire budget on repeated failures. Test one explicit alternative with the same minimum attempt spacing as its reference and only change the trigger's freshness source. This isolates the mechanism. A second experiment may compare a predeclared backoff rule, but must not be described as a single-component ablation of the first.

Use externally generated, timestamp-based missing-response masks shared by every policy. Include natural failures, independent missingness, and burst outages. Query-ordinal censoring is a separate sensitivity analysis: different query schedules encounter different masks, and Periodic can accidentally avoid every fifth eligible ordinal. Repeat stochastic masks with fixed published seeds and pair policies by trip and mask.

Select any trigger/backoff configuration using development campaigns only. Existing test cohorts are already inspected, so further optimization on them is exploratory. Evaluate the frozen winner once on new independently scheduled trips. No number of additional retrospective tuning runs makes those old cohorts confirmatory again.

## Metrics and decision rule

At each actual new-attempt count compare against Frozen (zero attempts only), Periodic, Early, ACI, and the current MARUR. Include a nonadaptive randomized query schedule to separate the value of adaptive timing from merely obtaining more labels. Never fabricate equal-cost Frozen observations or select the best test operating point after seeing outcomes.

Report supported throughput per scheduled eligible opportunity, positive-offer frequency, abstention, all-issued and positive-conditional risk bounds, unknown outcomes, successful responses, admitted scores, effective later-use updates, and trips/dates with positive offers. Risk bounds describe the observed record, not uncertainty over future trips. Present common-positive-offer comparisons as descriptive mechanism analysis, because conditioning on policy selections changes the target population.

Predeclare a practically meaningful utility gain and a noninferiority tolerance for positive-conditional risk using application requirements. They cannot be derived honestly from the best observed test difference. Estimate paired differences at the independent-trip level, with uncertainty and separate cohort results. Existing proposed 18 usable trip pairs follows an assumed paired SD of 0.10 and roughly 0.05 precision; it is not proof of adequate precision for rare violations. Recompute sample requirements for the chosen utility/risk estimands using pilot variability before registering the prospective experiment.

## Other literature-motivated checks

1. Compare pooled and missing-pattern calibration at fixed window and cost. Sirhan's evidence cautions that better subgroup/two-sided calibration need not improve one-sided decisions. Do not presume pattern conditioning wins.
2. Evaluate robustness of positive offers and utility to small input perturbations and randomized masks. Min et al. motivate checking stability, but their randomized interval counterexample does not prove MARUR suffers the same pathology.
3. Adapt a stronger online calibrator only as a separately labeled baseline, with identical delayed-feedback access. ACI, PID, betting, and decaying-step guarantees must be reassessed when outcomes are missing; copying the update formula does not import the theorem.
4. Keep live application validation as a distinct milestone. Evaluate stall time, delivered quality, switching, and measurement overhead on independent campaigns using a frozen application policy. A replay simulator remains useful, but cannot establish that milestone.

## Recommendation

Do the controlled freshness/failed-feedback experiment first; do not add another point-prediction model merely for novelty. It directly examines an implemented mechanism and can explain both improvements and regressions. Better values are possible but unproven, and a negative result must be retained. No experimental values were changed or generated by this literature-review task. Publication readiness still depends on the full audit, independent validation, and a chosen venue; the literature review alone does not justify an increased readiness score.
