# Prospective validation readiness audit

Status: protocol only; no prospective trips have been collected or analyzed by this project. The existing PROSPECTIVE_VALIDATION_PROTOCOL.md remains the study proposal, subject to the clarifications below.

| Item | Finding | Required action before registration |
|---|---|---|
| Sample size | n=18 follows t(0.975,n-1)*0.10/sqrt(n)<=0.05; SD=0.10 is assumed, not estimated from independent archival trips | State that this targets modest utility precision, not 10% risk certification; retain SD/half-width sensitivity table |
| Independent unit | One separately scheduled trip per date; ticks/carriers within a drive are dependent | Freeze routes/time strata and sampling population; record shared events and route dependence |
| Repeated measures | Policies share opportunities within each trip | Pair comparisons within trip and resample whole trips; never pool ticks as independent replications |
| Missing audit outcomes | Missing outcomes are not successes or physical zero service | Keep all started trips; separate complete zeros, unavailable telemetry, feedback failure and lost audit records |
| Failed queries | Charge at issue, conservative missing score, cooldown resets at completion | Freeze the implemented behavior and label timestamps distinctly |
| Measurement | Fixed next-60-second endpoint and one-minute clock | Validate synchronization and mapping in an outcome-blinded engineering rehearsal; log bytes and deadlines |
| Initialization | Existing archived ten-label state proposed | Freeze actual IDs/residuals and predictor hash, not just a verbal description |
| Primary outcome | Mean paired trip utility difference, MARUR versus Periodic, cap ten | State observed-outcome conditioning; report risk, offer frequency and realized cost jointly |
| Secondary analyses | Other policies, costs and subgroups | Freeze family; descriptive reporting unless a justified inferential plan is registered |
| Stopping | Original 18 completed / 22 scheduled wording could permit selective replacement | Use the fixed-started-trip clarification below; never replace a bad or incomplete started trip |
| Provenance | No prospective run manifest exists | Before collection, write device/operator/configuration hashes, timestamps, trip IDs, cancellations, deviations and immutable raw-file hashes |

## Stopping and attrition clarification

Reserve up to 22 dated slots to obtain 18 started trips; allow cancellation replacement only before any measurement on that trip begins and for outcome-independent logistical reasons recorded in advance. Stop at 18 started trips or at the preregistered calendar endpoint, whichever occurs first. A started trip with failed or missing measurements remains in the trial and is not replaced because its data are unfavorable or incomplete. Record any alternative safety/logistical stopping rule before first collection.

The precision calculation assumes 18 usable independent paired trip utility values. Eighteen started trips do not guarantee that condition. If any trip's utility is undefined because no outcome is observed, report the loss and the selected estimand among measurable trips; do not claim planned precision or a population effect without addressing missingness. The 15% cancellation allowance is an expectation, not a probability guarantee. No outcome-dependent sample-size extension or stopping for favorable results is permitted.

## Inference limits

Eighteen trips are insufficient for an unconditional strong inferential claim. Even under SD=0.10 the planned interval is roughly ten percentage points wide. If SD is 0.15, the same precision needs 38 complete trips; at SD=0.20 it needs 64. With SD=0.10 and 2.5-percentage-point half-width, 64 complete trips are needed. Existing dependence and missingness can make these calculations optimistic.

The primary t interval assumes independent, sufficiently regular trip differences. Cluster bootstrap is a sensitivity analysis, not a remedy for unmeasured campaign dependence or informative audit loss. Finite-record risk bounds and sampling uncertainty must stay separate. Zero-positive trips remain reported; their undefined conditional risk must not be silently omitted from service reporting. Eighteen trips were not powered to certify worst-case positive-conditional risk below 10%, detect small utility improvements, compare multiple operators, or demonstrate live QoE benefit.

## Registration blockers

Operator/location, route and time sampling frame, collection dates, exact predictor and initialization artifacts, operational minimum useful-service threshold, instrumentation access, data permission and public registration location are not supplied. They cannot be fabricated from the archive. The protocol is ready for the investigator to complete these fields and register, not ready to be described as an executed study. Until then the manuscript must retain retrospective and exploratory language.
