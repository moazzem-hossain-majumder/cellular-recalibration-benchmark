# Revisions addressing reviewer risks

The November 20 revision strengthens the empirical contribution and tests dependence on collection dates and client assumptions. The previous readiness statements were too general. Venue-specific assessment and formatting remain necessary before submission. This revision gives no acceptance estimate and keeps the existing subjective score unchanged.

## Contribution and related work

The manuscript now leads with the question of whether an overall reliability threshold describes the positive service a customer receives. A decision-criteria section derives the identity R = A times R-positive, where A is the positive-offer fraction. With e observed violations, m unresolved positive outcomes, M positive promises and N issued promises, finite-record risk lies in [e/N,(e+m)/N] and conditional risk in [e/M,(e+m)/M]. A positive-promise target is satisfied under every possible completion exactly when e+m <= alpha M. It is violated under every completion when e > alpha M. The other case remains unresolved. With no positive offers, conditional risk is undefined. The derivation requires nonnegative latent outcomes and makes no sampling guarantee.

This sharp decision criterion connects the accounting to an auditable service requirement. The identity and worst-case logic are elementary and have precedents in selective prediction and partial identification. The contribution is the empirical demonstration and the reproducible decision ledger. Risk-controlling prediction sets address population risk under their assumptions; the paper does not inherit those guarantees from this arithmetic. [Bates et al., primary paper](https://arxiv.org/abs/2101.02703) · [Geifman and El-Yaniv](https://papers.neurips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html)

## Collection units

The new analysis aggregates every fixed-policy opportunity by its carrier or regime and calendar date. It gives equal weight to dates and recalculates the aggregate after deleting each date. These diagnostics describe influence without pretending collection days were randomly sampled. A new date within a campaign can still share route, device and conditions. The final US midnight continuation contributes few ticks; equal-date weighting is an intentionally distinct sensitivity, and the individual date counts remain visible.

For Ireland the equal-date issued failure rate is 12.43% for the tree and 9.43% for persistence, while supported throughput is 7.09% and 17.31%. The Rome E3 tree has positive promises on one of seven dates and Verizon on one of three. Removing the sole Rome E3 positive-offer date leaves no positive service, which precludes interpreting a zero failure fraction as evidence of reliable positive offers. [Date ledger](../results/external_validation/cross_campaign_dates.csv) · [Date-deletion sensitivity](../results/external_validation/cross_campaign_date_sensitivity.csv)

## Application assumptions

The replay now supports one-, two- and four-second segments and fixed request delays of 0, 100 and 300 milliseconds. These are a prespecified grid for this robustness analysis, chosen after the original two-second replay was known. All requests choose their representation using information available before request delay. Delay consumes buffer and advances the service clock. Incomplete final requests retain their contributed bytes and startup failures remain explicit.

All routes sharing a calendar date are pooled before comparing policies, giving seven date groups. In every date group under all nine settings, the calibrated tree lowers stall fraction and bitrate together. Across settings, median paired stall changes range from -11.81 to -5.50 percentage points and median bitrate changes from -0.764 to -0.708 Mbps. The base replay splits into 1,473 continuity blocks per policy. Resetting playback at those breaks is a material assumption. The sensitivity does not model a closed-loop cellular scheduler, capped buffer or actual viewer preference. [All simulated blocks](../results/external_validation/playback_sensitivity.csv.gz) · [Date summaries](../results/external_validation/playback_sensitivity_dates.csv) · [Nine-setting comparison](../results/external_validation/playback_sensitivity_summary.csv)

## Manuscript focus and reproduction

The abstract now states one measurement question, the Irish example, feasibility result, application trade-off and limits. The early decision-criteria section defines the central claim. Session-defined endpoints and published-baseline sections are identified as supporting comparisons. Existing adverse outcomes and all tables remain available. A selected venue's page limit will determine which supporting sections belong in its supplement. The recommended main-paper sequence is decision criteria, clock construction, matched Rome evidence, frozen-model US and Irish replication, then limitations. Session-defined endpoints, neural comparators, published Irish reproduction, full prefix curves and playback parameter records can move to the supplement once the venue permits it. The current package retains those analyses because the target venue and its supplemental-material rules are still unspecified.

Run python scripts/replay_oslo_playback.py --sensitivity, followed by python scripts/check_campaign_robustness.py. The full reproduction entry point includes both stages. New unit tests cover latency exhausting a trace and alternative segment durations. Manuscript artifacts are rebuilt from the revised TeX.

The remaining substantive gaps are independent prospective collection with a frozen policy, observed application outcomes from live clients, and a contribution review against a specific venue. Additional archive analyses do not remove those gaps.

## Verification receipt

The local suite passed all 71 tests. The default playback mode reproduced its three existing output files byte for byte after the parameter extension. The sensitivity run produced 66,285 policy/block/setting rows. The manuscript validator independently reconstructs the date summaries, nine-setting paired contrasts and collection-date deletion summaries from the saved detailed records.
