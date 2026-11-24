# Independent validation: executable preparation, collection not performed

This is a proposed study, not a registration or a completed experiment. No new trip, device, network endpoint or live-video measurement has been fabricated. It refines the earlier generic protocol; contradictions must be resolved before registration. The original 18-pair calculation is retained as a utility-only sensitivity point, not a universal minimum.

## Proposed application and practical requirements

Use non-safety-critical adaptive video streaming. An initial engineering screening profile is in `configs/prospective_video_profile.json`: a 1 Mbps minimum video representation, a 1.5 Mbps offered-service threshold (50% nominal throughput headroom), useful-service offers on at least 80% of eligible ticks, positive-conditional violation risk at most 5%, and a five-percentage-point supported-utility gain at no greater feedback cost. An allowed risk increase of one percentage point is a separate proposed noninferiority margin and does not waive the absolute 5% ceiling.

These values are transparent design proposals, not established user requirements or thresholds chosen because MARUR meets them. The 5% rate-commitment criterion is not equivalent to a 5% playback-stall probability: buffer state, bitrate switches and segment deadlines intervene. Validate the ladder, headroom, buffer policy, minimum acceptable picture quality and tolerable stalls with the intended application before registration. If requirements change, freeze them before collecting confirmatory outcomes. Current archives often fail this profile; that does not justify relaxing it after viewing results.

The completed retrospective analysis remains a trade-off study because no application-derived acceptance thresholds were fixed beforehand. Do not retrofit the new profile into confirmatory pass/fail claims for those data.

## Equipment and field procedure

Use one Android cellular handset capable of exporting timestamped serving LTE/NR signal measurements and application payload counters, a laptop for synchronized logging/controller replay, and an endpoint explicitly permitted to receive the measurement traffic. Do not presume a model feature is available simply because a phone is marketed as 5G. Use a stationary, outcome-blinded instrumentation rehearsal to verify timestamps, feature names/units, missing flags, clock drift, actual 60-second payload accounting and model compatibility. Document phone/modem/OS, SIM/operator, location, route, vehicle, observer and collection permissions. These details are currently unknown, so acquisition is not authorized against any invented endpoint.

Begin with shadow measurement, not concurrent competing streaming applications. Schedule separate 120-minute trips on distinct days using a route/time-stratum roster fixed before outcomes. A fresh trip is a separately scheduled collection, not a segment cut from an earlier drive. Concurrent carriers remain one campaign cluster. Every minute issue forecasts from the frozen model using information strictly before issue; define the next full 60-second outcome as delivered payload bits divided by 60 seconds. Keep the full roster, including no-lag ticks and failed measurement intervals.

Distinguish physical audit-measurement traffic from virtual controller feedback access. The evaluator records outcomes independently of controller requests; a controller receives an outcome only if it requested that tick, after its deadline. Such shadow feedback budgets are label-access costs, not demonstrated savings in bytes, battery or network load. Record physical payload, control overhead and energy separately. A dedicated live trial is needed to test actual measurement-cost savings.

Use the unchanged baseline MARUR (window ten and completed-response trigger), Periodic, Early, modified ACI, Frozen, a seeded nonadaptive online query comparator, and the delayed DecayingOGD adaptation as prespecified secondary methods. Do not prospectively deploy the retrospective random-priority comparator unchanged: it knows the full eligible roster. A prospective randomized comparator must instead draw a fixed tick schedule before departure and skip ineligible/pending ticks, without looking ahead or charging successful-label-only cost. All use the same fixed model, preprocessing and ten initial observation IDs, reset identically at trip start. Freeze hashes and seeds. No variant is chosen from the best archive row.

## Precision and stopping

Run `python scripts/prospective_precision_review.py` to regenerate the utility and cluster-risk sensitivity grids. Paired SD 0.10 and two-sided 95% half-width 0.05 imply 18 complete independent trip pairs under the stated t approximation. With SD 0.20 this becomes 64. These calculations do not address rare violations.

For risk, an illustrative equal-cluster approximation with anticipated failure probability 0.05, 80 positive offers per trip, intratrip correlation 0.20 and half-width 0.025 requires approximately 62 independent trips. This depends strongly on unknown clustering and service frequency, uses a normal approximation, and is not a certification calculation. Unequal cluster sizes, all-missing trips, zero offers, correlated days or more severe drift may require more evidence. If the true risk is at the acceptance boundary, increased precision alone does not make its upper confidence bound fall below that boundary. Do not announce either 18 or 62 trips as a guaranteed sufficient sample.

Obtain a separately identified engineering/development pilot to estimate variance, missingness, positive-offer counts and within-trip correlation without selecting a favorable treatment effect. Pilot data are not confirmatory. Set a single confirmatory number of started trips and calendar end date before registration, using the primary utility precision and the risk/offer-frequency requirements jointly. The pilot size is a feasibility decision, not an invented powered sample size. A blinded sample-size rule must be written before pilot inspection if the same team will use it.

Include every started trip, including equipment failures and wholly missing outcomes. Pre-departure cancellations may occupy prescheduled spare slots; started trips cannot be replaced because their data or results are unfavorable. No stopping after a desirable result. If incomplete observation prevents the planned precision, report that failure and preregister a separate extension.

## Outcomes and analysis

Primary comparison: baseline MARUR versus Periodic, paired mean supported-utility difference at a fixed cap, with actual attempts reported jointly. A claim of practical benefit additionally requires useful-offer frequency, absolute conditional risk, proposed risk noninferiority, and no greater realized cost. If costs differ, label the comparison unequal-cost rather than infer superiority. Exact-cost secondary comparisons retain the full trip suffix; Frozen remains a zero-cost reference.

Compute paired trip-level utility intervals and whole-trip paired bootstrap sensitivity. For conditional risk, resample trips and recompute total violations/positive offers; carry both missing-outcome endpoints through the resampling. Report undefined bootstrap replicates and zero-positive trips. A wholly missing trip has undefined observed utility, not zero measured utility; retaining it in the report does not eliminate missingness selection. Present both equally weighted trip utility and pooled service totals, with their different estimands. Never treat ticks, mask seeds or same-drive carriers as independent observations. Secondary inferential families need prespecified multiplicity control; otherwise report descriptively.

Reliable zero delivered payload during a complete observation is y=0. An unrecoverable audit outcome is missing. Missing positive outcomes count as possible violations in the upper bound; missing controller responses cost attempts even if the evaluator later reconstructs their outcome. A five-percent acceptance conclusion requires an appropriate upper sampling bound on the worst-case conditional-risk endpoint, under defended sampling assumptions. The finite-record bound alone is insufficient.

## Separate live-application milestone

After the shadow protocol is frozen and feasibility established, conduct a separately registered randomized comparison of complete streaming policies on independent trips. Run only one traffic-generating treatment per assigned trip/device, or use a crossover design with explicit route/time balance and carryover/washout rules; concurrent policies on one link interfere. Fix video content, encoding ladder, buffer, startup policy, server, randomization and failure definitions. Measure stall seconds/minute, startup delay, delivered bitrate, switch frequency, failed segment deadlines, bytes/energy spent on measurements and logging outages. Analyze at the randomized trip unit. Shadow replay cannot substitute for this milestone, and its precision calculation cannot automatically power QoE endpoints.

## Frozen assets already prepared

`results/prospective_planning/frozen_rome_histgbm.joblib` recreates the existing 57-row Rome fit. `model_freeze.json` records its hash, feature order and software versions; 877 archived Rome predictions agree within 3.6e-15 Mbps. `proposed_initial_observations.csv` exports ten earlier E1 calibration observations, and their IDs are pinned in the proposed profile. This is an initialization proposal, not evidence that these residuals transfer to the future network. Verify the artifact hash before loading this locally generated joblib object. Field feature mapping remains unverified.

## What is still required

Actual operator/location/routes; compatible handset and logger; permitted endpoint; checked feature mapping and acceptance of the proposed frozen model/initial state; application-owner acceptance of requirements; pilot-based precision review; and public or timestamped preregistration. `results/prospective_planning/readiness.json` reports missing prerequisites explicitly. Code and a protocol cannot supply independent field evidence by themselves.
