# Final execution report

The November 20 [reviewer-risk revision](REJECTION_RISK_REVISIONS.md) strengthens the claim formulation, collection-date analysis and playback sensitivity. Venue-specific assessment remains pending. Earlier general readiness judgments below are provisional.


## Separate trips and client playback

The [latest report](TRIP_AND_APPLICATION_RESULTS.md) adds an Irish frozen-tree comparison on five later driving dates and an application replay on 22 Norwegian recordings. The current weighted score is 7.75/10. The previous sections below document the progression of evidence.

## Subsequent Drive 3 replication

The initial A–H assessment below predates the completed three-carrier test. The [replication report](DRIVE3_REPLICATION.md) supersedes its one-drive external evidence limitation. The updated manuscript includes Table XIII. The current weighted score is 7.60/10. The original reviewer scores are retained as historical assessments. A repeat raw-to-forecast run produced byte-identical alignment, forecast, paired-date and summary CSVs. All 66 local tests passed and the manuscript checker validated 13 tables and the submission package.

## A. What the audit found

The fixed-clock and reset-triggered experiments ask different questions. Ten target labels made the session-based tree appear conservative. On a one-minute clock the tree broke at least 67 of 238 E1 commitments. The E3 tree made three positive offers across 171 issued ticks, all on June 10, and two failed. Among all 46 missing clock outcomes, 45 forecast horizons crossed the end of the trace. The release does not say what happened to service after logging stopped. The two Rome suffixes contain eight distinct dates in total. Treating every tick as an independent replication would severely overstate precision. The original manifest was sensitive to checkout line endings and had stale digests. See the [repository audit](INDEPENDENT_RESEARCH_AUDIT.md) and [statistical audit](STATISTICAL_VALIDITY_AUDIT.md).

## B. What changed

Local revision of baseline commit 29325ecb5106e29c4cfa09ff694516271531910f. The clock generator now distinguishes truncated recordings from full windows without a valid rate and reports positive, measured-positive and honored-positive decisions. Figure 7 adds the positive-offer frequency at every budget. Table XII gives measured-positive and issued-positive counts. New scripts replay telemetry masks, select a risk-constrained rule using earlier dates, and validate a US drive. The full reproduction entry point includes all three. New tests cover denominators, masks, temporal overlap, selection and portable hashes. The artifact checker reaggregates clock, mask and US records. Direct dependency versions, read-only hash verification, the CI workflow, README and Antigravity handoff were updated. The cover letter, manuscript, bibliography, rendered copies and submission archive were rebuilt. The [literature comparison](UPDATED_LITERATURE_AND_NOVELTY_REVIEW.md) and [external data review](EXTERNAL_VALIDATION_PLAN.md) document scope and overlap.

## C. Executed experiments and checks

Commands below are run from the repository root with Python 3.11. All listed commands completed successfully.

- `python scripts/clock_frontier.py` â€” Rome, 43 later Ookla traces and an earlier source tree fitted on 57 sessions. E1 had 238 issued, 211 measured forecasts. E3 had 171 issued, 152 measured. Seven test dates per regime, six shared. The combined dates in 2023 were May 9 and 27, June 8, 10, 16 and 25, and July 4 and 5. At ten labels the E1 tree supported 7.15% of measured throughput, with issued risk 28.15â€“31.51%. E3 supported 0.065%, with issued risk 1.17%. The 434 feasible regime/budget pairs give 1,736 rows across model and offset policies. Per-date, date-deletion, rolling-offset and endpoint stress results accompany the [frontier](../results/clock_histgbm/frontier.csv) and [ledger](../results/clock_histgbm/issued_k10.csv).
- `python scripts/stress_clock_radio.py` â€” same 409 test ticks and dates, 52 summaries of 10,634 simulated forecasts. The E1 weak-signal mask reduced violations from 67 to 48 while reducing supported throughput from 7.15% to 4.76%. E3's prediction-minimizing intervention eliminated positive offers and violations. Date ordering and eight earlier bounded missingness runs determine the burst specification. [Methods and metrics](NR_STRESS_AUDIT.md)
- `python scripts/select_clock_policy.py` â€” same 409 test ticks. The first target date supplies candidate prefixes. Three later validation dates yielded 155 measured outcomes on E1, four yielded 231 on E3. The empirical validation ceiling counts every unresolved positive offer as a violation. E1 selected nine-label global persistence, matching the fixed ten-label persistence outcome. E3 selected twenty-label global persistence, supporting 19.52% of measured throughput at 15.20â€“15.79% all-issued risk. Prespecified ten-label persistence supported 16.00% at 12.28â€“12.87% risk. The selector incurred validation-label costs and failed the target on E3. The held-out suffix was already known to the investigators. [Validation](../results/clock_histgbm/selection_validation.csv) Â· [Test](../results/clock_histgbm/selection_test.csv)
- `python scripts/validate_nuwins_drive2.py` â€” NUWiNS AT&T Drive 2. Six pinned input files, 243 scheduled ticks overall. May 13â€“14, 2023 supplied 203 eligible calibration pairs, of which the first ten set the offset. May 15â€“16 were reserved. Only May 16 supplied eligible intervals, with 36 ticks, three abstentions, 33 measured forecasts, eight positive offers and six violations. Risk 18.18%, supported throughput 49.46%, point MAE 100.09 Mbps. A repeat run gave byte-identical output files. [US forecast records and source hashes](../results/external_validation/nuwins_drive2_summary.json)
- `python scripts/build_paper_html.py` and `python scripts/validate_manuscript_consistency.py` â€” rebuilt TeX, figures, twelve tables, both PDFs, web formats and ZIP, validated ordered table cells and forecast aggregates, and compared manuscript page rendering in the package. The 11-page combined PDF was also inspected visually.
- `python -m pytest -q --junitxml=results/runs/final_tests.xml` â€” 65 passed in the local research environment. The three Rome raw releases/files in the acquisition manifest were independently rehashed against their exact-byte SHA-256 records. [JUnit results](../results/runs/final_tests.xml)
- `python scripts/generate_experiment_manifest.py` and `python scripts/generate_experiment_manifest.py --verify` generate and validate the artifact inventory. The historical full-pipeline receipt remains in [execution.json](../results/runs/execution.json). The archived Irish, Norwegian, neural and session experiments were retained. This revision reran the affected experiments only. A raw-data-free copy uses the clean Python environment for the publication and hash checks. The [hosted workflow at the baseline SHA](https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark/actions/runs/43261645668) passed. The revised local files have no hosted run.

## D. Scientific improvements

Identical opportunities now expose the difference between risk across the whole ledger and risk conditional on actually making a positive offer. The missing-window classification describes the observation process without assigning outcomes. The fixed-offset interventions isolate the effect of changing recorded NR inputs on this predictor. The earlier-date selector tests whether a higher validation utility at a constrained risk survives a temporal change. The US publisher's interval metadata supplies an independent opportunity definition for a persistence check. None of these additions provides a population-level error guarantee.

## E. Final peer review

Telecommunications 7.0, machine learning 7.0, methodology 7.4. Reviewer mean 7.13/10. The distinct weighted project rubric gives 7.40/10. [Three reviews](FINAL_ADVERSARIAL_PEER_REVIEW.md) Â· [Weighted scorecard](FINAL_SCORECARD.md)

## F. Remaining blockers

Only eight distinct test dates underlie the two Rome clock suffixes. All E3 positive tree offers occupy one date. One US carrier-date contributes external test forecasts. Technologies, endpoints and logged features vary between external releases. The full frozen Rome tree and missing-input intervention lack an independent matched replication. Performance compared with published work is protocol-dependent. A hosted raw-to-paper rerun of the revised files and venue-specific length, formatting and author declarations remain outstanding.

## G. Submission recommendation

**Potentially suitable for a specialized conference**, particularly a wireless measurement or reproducibility track. The all-issued ledger and positive-offer counts give a falsifiable measurement result. Results do not establish a state-of-the-art forecaster or a universally sufficient budget.

## H. Next steps in order of scientific value

1. Lock predictor, ten-label baseline, decision timing, outcomes and success criteria before collecting new dates. Capture attempts, starts, completions, failures and telemetry availability independently of realized throughput.
2. Replay the frozen tree and persistence on another compatible carrier/device combination. Report date-level exposure to positive offers and support alongside risk. Plan the number of independent dates from a target precision and between-date variation.
3. Test whether an application's realized delivery or stall outcomes track the retrospective supported-throughput proxy.
4. Run the revised revision on a separate host from pinned raw inputs, archive that receipt, and format the manuscript for a specific call.
