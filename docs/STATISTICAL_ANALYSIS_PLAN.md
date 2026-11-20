# Statistical analysis plan for the adaptive recalibration investigation

This plan is written before reviewing the new MARUR outcomes. Prior project suffixes are historically known, so the new study is exploratory. Freeze the candidate rules, budgets, event timing and baselines in the method and design documents before running them. A later independent campaign is needed for a confirmatory assessment.

## Experimental unit and target quantities

The scheduled unit is a clock tick within an observed trace. Eligibility requires the prespecified causal history. A policy can issue a positive rate, issue zero, abstain, or request an available label for a subsequent update. Recalibration can coincide with a later prediction and should not be encoded as an outcome. Count scheduled opportunities S, eligible opportunities E, issued predictions N, positive offers M, measured positive offers M_obs, observed violations e, unresolved positive offers u, and observed honored positive offers M_obs-e.

Report eligibility E/S, commitment coverage N/E, positive-offer rate M/N and M/E, observed violation e/O where O is all measured issued outcomes, and conditional observed failure e/M_obs. A zero denominator is undefined. Zero offers are visible in the service counts. Do not replace undefined conditional risk with zero.

For nonnegative latent outcomes at every issued opportunity, report the finite-record all-issued interval [e/N,(e+u)/N] and positive-conditional interval [e/M,(e+u)/M]. These are partial-identification bounds, without a confidence level. Unresolved outcomes include completed windows without a measurement and truncated recordings, which need distinct status fields. A scheduled service that never existed is outside the latent-outcome interpretation.

Supported throughput sums min(commitment, measured outcome) over observed issued rows and divides by their total measured outcome. Also give mean positive rate, offered rate and abstention frequency. Utility over measured outcomes does not identify realized utility on unresolved rows. Compute point MAE, RMSE and median absolute error on the same eligible measured outcomes for every frozen predictor; abstention must not improve the point-model sample by selecting easy targets. An optional selective-error summary uses a clearly labeled second denominator.

## Label budgets and feedback

State whether B counts queried outcomes or measured outcomes used. The principal resource accounting should count attempts, since the availability of a future label cannot be known when requesting it. Report both attempts and successfully consumed distinct labels. Prefix labels, labels purchased for validation, repeated access to the same label, window size, number of refits and feedback used for trigger monitoring are different quantities. Every policy receives the same exogenous history allowed for its lag features. If all completed rate observations are already free feedback, the experimental budget represents restricted use for recalibration rather than paid network measurement acquisition.

At decision time t, only outcomes with completion or declared availability time at or before t may change the calibrator. If several forecasts share t, make all actions from the same pre-t state before processing their later outcomes. Within-window trace termination must never become an input feature. Define outstanding queries and missing-label expiration so the finite budget cannot be bypassed.

## Prespecified comparisons

For each predictor and dataset, compare the proposed policy to the frozen ten-label offset, a matched fixed update schedule, a matched rolling update schedule and an appropriate feedback baseline. Publish every tested budget and every configured rule. Compare the proposed rule and its ablations using identical opportunities and the same maximum budget; report realized usage when a trigger leaves budget unspent.

The primary empirical question is whether an adaptive policy increases supported throughput without worsening the declared risk criterion or exceeding the label budget. Present paired risk and utility changes together. A rule that offers zero rates fails a positive-service requirement even if its all-issued risk is zero. Any minimum offer-frequency or utility floor is a design choice that must be fixed before the new run and tested in a limited declared sensitivity. Do not pick a favorable test budget or threshold and call it optimal deployment policy.

An adaptive alpha rule, a fixed quantile rule and a direct offset update use different mechanisms. Name them correctly. A finite exact-binomial bound can be reported as an independence-assuming benchmark only. It is not an assurance for adaptive, correlated, censored throughput observations.

## Grouped reporting and uncertainty

Keep Rome E1 and E3, each US carrier, Ireland and the Norwegian protocol in separate panels. Report dates, traces, physical trips where known, campaign identifiers and model training provenance. Shared carrier-date measurements are paired exposures. The final US midnight date is a continuation of the same trip and must not be promoted to an independent physical drive.

For each dataset and budget, save per-date numerators and denominators, pooled estimates, equal-date estimates and omit-one-date estimates. When pooling utility use the pooled numerator and denominator. When reporting equal-date utility average date ratios and state that estimand. Also report the number of dates with any positive promise, observed positive promise and failure. The existing E3 tree concentrates positive service on a single date, so aggregate precision is especially misleading.

Use paired differences within the same dates for comparisons. Do not treat ticks as independent trials in p-values, standard errors or resampling. Given the current small number of campaigns, omit-one-date ranges and raw paired dates are the primary sensitivity report. If a cluster bootstrap is additionally shown, resample entire shared calendar-date blocks together for all policies, fix the seed and draw count, label it exploratory, and state that independence between dates is unverified. It conditions on the frozen fitted model, chosen prefix and known campaign. No universal minimum number of clusters makes those assumptions true.

A new prospective trial should plan positive-offer exposure and between-trip variance on a separate pilot, fix collection duration before observing results, and use independently scheduled trips as the intended experimental unit. Increasing the number of ticks in existing recordings cannot supply that experiment.

## Multiplicity and subgroup analyses

Report all prespecified budgets, policy ablations and missingness strata. The principal comparison should be chosen in the method formulation. Treat additional budget frontiers, adversarial predictor masks and threshold searches as exploratory. If inferential tests are used in a future adequately replicated study, control the declared family of primary hypotheses. Repeated simulation seeds quantify simulator or mask variation conditional on the input records.

Subgroups should be defined using available issue-time telemetry, such as measured NR presence. Label-defined groups such as a future sharp rate drop are retrospective failure diagnostics. A test-time classifier fitted to the complete target covariate suffix is transductive; it must appear separately from causal online methods even when labels are hidden.

## Failure, falsification and reproducibility criteria

The adaptive hypothesis fails on a cohort when improvement in utility comes with violation of the selected risk ceiling, when improvement disappears under matched label cost, or when only zero/rare offers achieve the apparent reliability. Preserve such results. A heuristic can have a useful empirical operating point without a formal guarantee. Any theorem must state assumptions that apply to the implementation, including missing outcomes, querying, dependence and nonstationarity.

Store the complete timestamped action and feedback ledger, source hashes, configurations, software versions and actual execution receipt. Validate query times, budget accounting, unique label consumption, risk bounds, utility and all rendered tables independently. Unit tests should cover simultaneous timestamps, delayed labels, unavailable outcomes, exhausted budgets, no eligible predictions and unsupported telemetry patterns. Reproduction receipts identify the revision and distinguish local tests from hosted CI.
