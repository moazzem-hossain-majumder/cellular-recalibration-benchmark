# Final repository scientific audit

Base commit: dff33228b2741909f04551b54c50b5b960c844b1, matching the supplied revision. The checkout was clean before this task. The 372 tracked files were inventoried and hashed before edits in results/runs/final_scientific_audit_baseline.json. All src/scripts/tests Python files were parsed; the specified method, validator, configuration, ledgers, manuscript, table generators, figure generators, bibliography, documentation, CI and provenance records were reviewed. This is a computational repository audit, not an external IEEE editorial review or a new raw-data collection.

## Issues and resolution

| Issue | Severity | Evidence/File | Required correction | Status |
|---|---|---|---|---|
| Only utility delta checked in paired audit | Major | scripts/validate_marur_audit.py at base commit | Independently recompute every stored difference from action/response ledgers | Fixed: all eight delta columns and both cost columns checked |
| Missing/duplicate pairs not rejected | Major | Same validator | Compare exact identity set to independently declared experimental grid | Fixed: all 576 candidate pairs required exactly once |
| Offer decomposition checked only by identity | Major | offer_decomposition.csv and base validator | Recompute shared/removed/added offers and their failure counts | Fixed: every field independently recomputed for all 384 exact-cost pairs |
| Summary and feedback could agree on an incorrect cost | Major | Base validator counted rows without full identity/timing verification | Bind each response to its query and authoritative opportunity; verify masks, outcomes, admissions and availability | Fixed; no reliance on a matched flag alone |
| Figure 4 hides high risk and labels reference a guarantee | Major | Original y-axis upper limit 0.35; E2 observed V=0.4336 in multi_alpha_frontier.json | Expand axis from actual saved maximum; correct legend | Fixed by regeneration, with regression test |
| No corruption tests for audit files | Major | tests/unit | Corrupt differences, identities, responses, costs and balanced decompositions | Added 35 tests, including CSV round trips |
| Original action receipts remain valid | Informational | results/marur and results/marur_audit | Preserve all data, decisions and unfavorable results | No controller or experimental metric changed in this task |
| Abstract mixed measured conditional estimate and upper bound | Moderate | Previous abstract's 7.74-to-10.06 phrase | Use matched-cost findings with explicit outcomes/denominators | Rewritten from saved E1/Ireland evidence |
| Method lacked exact state/complexity description | Moderate | paper/manuscript.tex and marur.py | Document reception order, final pending response, gate and runtime/storage | Specification and manuscript sequence added |
| Trigger diagnostic label can differ from scheduling cause | Moderate | MARUR_Periodic uses pattern-priority trigger label | Explain that trigger string is not causal attribution | Documented; policy unchanged |
| Fresh environment not established by old working-copy reruns | Moderate | Earlier isolated reproduction receipts | Execute a fresh minimal dependency environment for all saved controller replays | Current result recorded in clean_controller_reproduction.json; scope excludes model refitting/raw reacquisition |
| CI did not run paired-audit validation | Moderate | .github/workflows | Run corruption tests and the complete audit validator; pin direct requirements | Updated; no hosted success claimed |
| Historical readiness scores and Bangladesh guarantees | Major | FINAL_PUBLICATION_READINESS_REPORT.md, critical_academic_review.md, bangladesh_telecom_case_study.md | Withdraw old verdicts as current claims and remove unsupported deployment claims | Historical records labeled; guarantee statements corrected |
| Prospective replacement/stopping ambiguity | Major | 18 completed/22 scheduled wording | Count every started trip; allow only pre-departure outcome-independent replacement | Protocol/readiness audit clarified; no collection performed |
| Sample size insufficient for broad risk certification | Major | Assumed SD=0.10, half-width=0.05 | Limit n=18 claim to conditional planning precision | Explicit; missing evidence remains |
| Novelty and deployment evidence remain limited | Major | Cohort results and prior work | Empirical contribution, no general algorithmic novelty or universal superiority | Manuscript and novelty audit narrowed |
| Source/data/dependency permissions unresolved | Release limitation | No project LICENSE; Irish ZIP and Norwegian raw terms; PyMuPDF licensing | Document distinct rights, retain attribution, avoid assuming download implies redistribution | Inventory completed; author/provider decisions remain |

## Evidence chain and generated artifacts

Hand-maintained sources are manuscript.tex, references.bib, cover_letter.tex, configs, source code and explanatory documentation. scripts/publication_tables.py generates both copies of every LaTeX table. scripts/build_paper_html.py builds HTML/Markdown/PDF/ZIP from the same LaTeX. Results CSV/JSON and compressed forecast/response ledgers are authoritative saved experimental evidence, not numbers to edit to fit prose. Figure files are generated from the source records below. Hashes distinguish current corrections from the base snapshot.

| Artifact | Authoritative evidence and calculation |
|---|---|
| Table 1 | results/metrics/point_predictor_profiles.json; validation MAE/RMSE and recorded fit time |
| Table 2; Figure 1 | calibration_budget_results.csv; regime/K/method V and U, with counts checked against split_summary.json; figure uses U |
| Figure 2 | Same CSV: E2 subgroup violation columns and per-regime mean_overcommitment versus U |
| Table 3 | results/diagnostics/session_boundary_sensitivity.json; segmentation counts and downstream V |
| Table 4 | bootstrap_significance_tests.json and split_summary.json; stored paired date-resampling contrasts, with small-cluster limitations |
| Table 5 | online_aci_results.json and covariate_shift_conformal.json; historical score-offset and weighted-calibration analyses, distinct from MARUR's modified ACI |
| Figure 3 | online_aci_results.json q_trajectory; score-offset against normalized stream index |
| Figure 4 | multi_alpha_frontier.json; stored proposed V/U by nominal alpha; scripts/plot_saved_frontier.py now shows all values |
| Figure 5 | sla_cost_analysis.json costs/lambdas derived by src/experiments/ablations.py; illustrative normalized loss, not monetary savings |
| Table 6 | results/exploratory/sirhan_external/matched_frontier.csv; per-seed means and paired differences; published 33.1/47.2/56.9 percentages explicitly remain external reported references |
| Table 7 | decision_curves.csv at beta=0.1; mean V/U and number of seeds meeting empirical threshold |
| Table 8 | trace_exclusions.csv; influence sensitivity after named trace exclusions |
| Table 9 | lag_transitions.csv; lag correlation/errors and transition fractions |
| Table 10 | prediction_time_validity.json and norway_metrics.csv; cohort-specific clock endpoint/units remain distinct |
| Table 11 | irish_group_validation.json; coverage and supported fraction by calibration size and method |
| Table 12; Figure 7 | results/clock_histgbm/frontier.csv; k=10 ledger table and all-prefix risk/utility curves; plotted frontier is exploratory |
| Table 13 | results/external_validation/drive3_results.csv; all-date carrier/model aggregates, no independent-carrier trip count |
| Table 14; Figure 8 | results/marur/summary.csv; Recorded HistGBM cap B=50 table reports NEW queries B-10, with actual spending; figure shows all original caps |
| Figure 6 | calibration_budget_results.csv Global_Conformal zero_bound_fraction times 100 |
| Abstract and matched-cost subsection | matched_cost_summary.csv and offer_decomposition.csv, HistGBM/Recorded/new cap ten; E1 U 2.907 vs 0.523%, upper risk 10.924 vs 6.303%; Ireland 159 shared offers and fourteen fewer failures |
| 576 / 720 / 384 counts | Original summary rows / audit summary rows / independently established equal-cost pairs; replays share observations and are not independent experiments |
| Prospective 18 / 22 / 38 / 64 | prospective_precision.csv from the stated t half-width equation; planning assumptions, not observed sample sizes |
| Other historical prose | Source-defined endpoints and split counts in diagnostics; external source-selection and trace-influence records; clock/Drive3/Irish ledgers; playback_sensitivity.csv and campaign robustness outputs under results/external_validation |

The automated publication validator compares ordered cells in CSV-derived specifications, LaTeX, HTML, Markdown and both PDFs, checks source digests and saved-forecast aggregates, and checks figure-copy identity. The added all-table test regenerates every table specification. Numerical interpretation of historical literature values and observational assumptions still requires scholarly review; an automated text scan is not proof of every scientific claim. Every major result has a named evidence source above. Manuscript claims are supported at their explicitly retrospective/descriptive scope; population validity, physical acquisition savings and prospective benefit remain unsupported and are not claimed.

## Statistical assessment

No new significance tests or archival confidence intervals were added. The few shared campaigns do not justify tick-level independence. The strengthened validator checks effect sizes and finite-record bounds, not inferential validity. U and supported throughput are the same metric here, not two independent endpoints. commitment_coverage is positive-offer frequency on scheduled rows; it is not conditional nonviolation coverage. lo/hi use eligible issued forecasts, positive_low/high use positive offers, and missing audit outcomes widen identification bounds. Day-wise effective_updates is cumulative, not additive. All 192 unmatched candidate pairs remain in the file and must not be presented as exact-cost effects.

## Licensing and source provenance

Rome Zenodo records 8224890 and 14073311 have CC-BY-4.0 metadata in the archived acquisition manifest; cite the dataset papers, retain attribution and identify transformations. Publisher records were reopened during this audit. [Rome 2023 release](https://zenodo.org/records/8224890), [later active release](https://zenodo.org/records/14073311).

The [NUWiNS release](https://github.com/NUWiNS/pam2025-multi-carrier-dataset) identifies CC0-1.0; retain scholarly attribution and pinned file/commit provenance. The [Irish repository](https://github.com/uccmisl/5Gdataset) identifies GPL-3.0, but there is no separately established measurement-ZIP grant in this audit. The [Sirhan analysis deposit](https://data.mendeley.com/datasets/ncbdm2c36d/1) is CC BY 4.0 and explicitly excludes raw traces; that grant must not be transferred to the Irish raw archive. The Norwegian publisher previously supplied citation instructions without an explicit raw-log license; its landing page timed out on the current check. That permission remains unresolved rather than newly verified.

Raw data are excluded from the submission ZIP. Derived ledgers containing original throughput or other trace fields may still carry upstream obligations; being derived does not automatically clear redistribution. Preserve existing research evidence, but resolve Irish/Norwegian sharing terms before a redistribution release. The project has no selected source-code license; no license was chosen on the author's behalf.

results/runs/dependency_licenses.json records installed direct and applicable transitive dependency metadata and license-file hashes for 45 distributions. Most direct scientific packages identify BSD/MIT/Apache/PSF-style terms. PyMuPDF identifies dual AGPL-3.0/commercial licensing ([official terms](https://pymupdf.readthedocs.io/en/latest/about.html)); it must not be described as permissively licensed. pypandoc_binary's wrapper metadata does not replace the bundled Pandoc binary's license, and wheel metadata does not exhaust bundled vendor obligations. No dependency binaries are added to the submission ZIP. Tectonic and Pandoc remain external build tools with their own distribution terms. This is a documented permission inventory, not a claim that all redistribution questions are settled.

## Self-review and submission decision

| Dimension | Score / 10 | Evidence | Remaining weakness |
|---|---:|---|---|
| Novelty | 6.0 | Explicit acquisition/service evidence and matched-cost decomposition | Established conceptual components; no broad priority or theorem |
| Technical correctness | 8.5 | Complete paired validation, corruption tests and corrected figure range | Replay instrumentation still differs from live collection |
| Mathematical formulation | 8.0 | Exact heuristic/state specification; separate identification and sampling uncertainty | No risk-control or optimization proof |
| Experimental design | 7.5 | Fixed clocks, full suffixes, actual-cost contrasts and negative results | Previously inspected archives and synthetic-mask aliasing |
| Statistical validity | 6.5 | No unjustified new tests; dependence and missingness explicit | Few independent campaigns; uncertain population precision |
| External validity | 6.0 | Multiple archived contexts with endpoint caveats | No prospective or live deployment evidence |
| Reproducibility | 8.5 | Ledgers, complete validators, tests, hash inventory and documented clean replay scope | Full training/acquisition stack not newly reproduced in a fresh environment |
| Manuscript quality | 7.5 | Aligned questions/abstract, exact method and corrected graphics | Still broad; venue-specific shortening and formatting unresolved |

Equal-weight mean: 7.3125, reported as **7.3/10**. This is an internal qualitative assessment, not an acceptance probability. Recommendation remains **Major Revision**. Engineering and reporting corrections improve defensibility but cannot substitute for independent evidence. The paper is not yet recommended for an unconditional IEEE submission.

The three priorities are (1) preregister and collect independent prospective campaigns with the precision limitations stated, (2) choose a suitable empirical networking venue and narrow the manuscript around acquisition/decision evidence, and (3) resolve release permissions and execute the full pinned reproduction/CI on the final release. The exact modified-file inventory and executed checks are recorded in the final audit execution receipt; no hosted CI success or prospective collection is asserted.
