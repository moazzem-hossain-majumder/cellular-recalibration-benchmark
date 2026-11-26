# IEEE-style submission decision

November 21, 2026. Recommendation: **Major Revision** for the current research submission. Do not submit it as a new algorithm with guaranteed risk control or demonstrated broad superiority. A focused empirical networking/measurement submission is plausible after selecting a venue, tightening the manuscript to its scope and obtaining prospective replication. This is an internal skeptical assessment, not an IEEE decision or an acceptance probability.

## Updated assessment

Using equal weights over eight reviewer dimensions (10 is strong, substantiated publication evidence): novelty 6.0; technical correctness 8.0; mathematical formulation 7.0; experimental design 7.5; statistical validity 6.5; external validity 6.0; reproducibility 8.5; manuscript quality/focus 7.0. Mean: 7.0625, reported as **7.1/10**. This stricter audit score is not directly comparable to earlier informal ratings and is not a confidence interval or probability of acceptance.

The strengths are executable causal feedback accounting, explicit missing-outcome bounds, full original and matched-cost replays, failure-trigger regression tests, retained negative results, and independent metric recomputation. The work's central result is that apparent reliability and service gains can reflect offer selection, smaller commitments, or different acquisition costs, with different mechanisms by cohort.

The limiting evidence is substantial. MARUR does not solve its motivating optimization problem, no deployment guarantee is proved, multiple components have established precedents, and equal-cost replay does not establish consistent superiority. Few dependent campaigns and known test suffixes limit inference. The failed-response trigger is a cooldown heuristic, not freshness of observed evidence. Position-based synthetic censoring aliases with periodic sampling. The manuscript still combines many historical analyses and requires venue-specific selection and formatting.

## What can be claimed now

An auditable retrospective empirical study of cellular commitment and calibration under missing telemetry and limited new feedback queries; arithmetic finite-record bounds under stated latent-outcome assumptions; implementation feasibility; and cohort-specific reliability/service/cost trade-offs. Exact-cost comparisons apply only where actual new-query counts match. Frozen is a zero-query reference. Both favorable and unfavorable results are legitimate contributions if presented as empirical findings.

## What is not supported

A new general conformal theorem, an optimization algorithm that maximizes utility subject to conditional risk, proven risk control under shifting delayed selective feedback, uniform performance superiority, total physical measurement savings, independent replication from simultaneous carriers, or live application benefit. The original hybrid counter cannot be described as total measurement attempts.

## Minimum path to stronger submission evidence

Carry out the preregistered prospective protocol: at least 18 independent completed trips for a five-percentage-point utility-difference half-width under assumed trip SD 0.10; schedule 22 with explicitly limited attrition assumptions. Tighter precision or greater heterogeneity needs more trips. This is a proposed experiment, not completed evidence. Select an IEEE venue and narrow the manuscript around the acquisition/decision audit. Author licensing and data-sharing choices remain separate release tasks. Do not promise acceptance after these steps.

Read FINAL_MARUR_CRITICAL_AUDIT.md for findings, MATCHED_COST_ANALYSIS.md for all configurations and metrics, and PROSPECTIVE_VALIDATION_PROTOCOL.md for precision assumptions and the frozen experiment. The implementation was not redesigned to improve scores.
