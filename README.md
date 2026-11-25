> **Latest IEEE review updates (Items 2--7):** Reconciled `MARUR` vs. `PACER` contribution framing across [manuscript.tex](paper/manuscript.tex) and [related_work.tex](paper/related_work.tex) (`Table I` + three-way delta paragraph), added [baseline specification table](paper/tables/table17_baselines.tex) (`Table II`), [MARUR-vs-PACER decision taxonomy](paper/tables/table18_marur_vs_pacer.tex) (`Table VI`), and [operational risk ceilings / Do-Not-Deploy rules](paper/tables/table19_risk_ceilings.tex) (`Table VII`), consolidated `Limitations and Threats to Validity`, documented CPU vs. optional RTX 4060 GPU reproducibility, and regenerated a fresh clean-venv end-to-end execution receipt ([execution.json](results/runs/execution.json)). Note `prospective_trips_collected` remains `0` pending live field or post-design trace collection (Item 1).

> **Latest Path A update (locked theory & untouched validation):** Introduced Horizon-Paced Selective-Offer Conformal Control ([PACER](src/evaluation/pacer.py)) with proved selective-excess and blind-suffix bounds ([theory and SHA-256 pre-registration](docs/PACER_THEORY_AND_PREREGISTRATION.md)), validated across **42 physical campaign-dates in 10 cohorts** including **26 newly unsealed held-out public campaign-dates** (`Rome_Capacity_Op1`, `Rome_Capacity_Op2`, `Oslo_Commute`, `Ireland_Static`) via `python scripts/run_pacer_study.py` and `python scripts/validate_pacer.py`. Theorem 1 holds across **40/40 cells**, while zero live prospective field trips (`prospective_trips_collected = 0`) and raw conditional-risk ceilings under low service frequency remain transparently documented.

> **Latest audit & release update (Nov 24):** Added explicit project source [MIT License](LICENSE) and [third-party data licensing inventory](docs/DATA_AND_SOFTWARE_LICENSING.md), added [physical campaign-date paired cluster inference (`G=16` unique dates across 3 drives)](scripts/audit_trip_level_inference.py) (`Table III` in the seven-page main paper / `table15_cluster_inference`), added the [frozen prospective validation harness](scripts/run_prospective_validation.py) (`prospective_trips_collected = 0`), and strictly refocused the [main manuscript](paper/manuscript.pdf) around cellular throughput commitment accounting while deferring live video QoE trials to a separate follow-up study.

> Latest reviewer revision: [all six recommendations and outstanding evidence](docs/REVIEWER_REVISION_COMPLETION.md), [792 targeted baseline runs and mechanisms](docs/REVIEWER_BASELINE_RESULTS.md), [seven-page main paper](paper/manuscript.pdf), [separate detailed supplement](paper/supplementary.pdf), and [deferred QoE follow-up design](docs/PROSPECTIVE_VIDEO_VALIDATION_PLAN.md). The original results are preserved. No prospective trips, live application evidence, external IEEE review or acceptance guarantee is claimed.

> Prior final audit: [scientific findings and score](docs/FINAL_REPOSITORY_SCIENTIFIC_AUDIT.md), [contribution](docs/NOVELTY_AND_CONTRIBUTION_AUDIT.md), [exact implementation](docs/MARUR_IMPLEMENTATION_SPECIFICATION.md), and [prospective readiness](docs/PROSPECTIVE_VALIDATION_READINESS_AUDIT.md). Major revision remains the recommendation.

> November 21 critical audit: the legacy MARUR budget/attempt counter is ten historical successful labels plus NEW query attempts, not total measurement cost. See docs/FINAL_MARUR_CRITICAL_AUDIT.md, docs/MATCHED_COST_ANALYSIS.md and docs/IEEE_SUBMISSION_DECISION.md (paths relative to repository root) for the current assessment.

# Cellular throughput recalibration benchmark

The [MARUR research extension](docs/FINAL_RESEARCH_READINESS.md) evaluates an empirical budgeted query-and-commitment controller on six archived cohorts. It includes 576 configurations, all scheduled opportunities, actual query costs and unsuccessful response accounting. The results show trade-offs and failures across networks. [Method](docs/PROPOSED_METHOD_FORMULATION.md) · [Novelty comparison](docs/NOVELTY_COMPARISON_MATRIX.md) · [Reviewer assessment](docs/IEEE_REVIEWER_RESPONSE.md)

Run the full benchmark first with python scripts/reproduce_all.py, or run the extension against its prepared inputs with python scripts/run_marur.py and python scripts/validate_marur.py. The [configuration](configs/marur.json), [scientific summaries](results/marur/summary.csv), [action ledger](results/marur/actions.csv.gz), and [feedback ledger](results/marur/responses.csv.gz) record the complete comparison. Repository source code is released under the [MIT License](LICENSE); third-party raw datasets retain upstream permissions and are excluded from redistribution ([data and software licensing](docs/DATA_AND_SOFTWARE_LICENSING.md)). Run `python scripts/audit_trip_level_inference.py` for physical campaign-date (`G=16` unique dates across 3 drives) paired cluster inference and `python scripts/run_prospective_validation.py` to inspect the frozen prospective harness (`prospective_trips_collected = 0`).


The [November 20 revision](docs/REJECTION_RISK_REVISIONS.md) adds finite-record decision criteria, collection-date sensitivity and nine playback settings.

The [positive-offer feasibility analysis and submission decision](docs/POSITIVE_OFFER_SELECTION.md) reports the outcome of imposing joint risk, frequency and throughput requirements.

The [Irish drive and Norwegian playback experiments](docs/TRIP_AND_APPLICATION_RESULTS.md) extend the comparison to separate trips and measure simulated client stalls, startup and bitrate.

The [US Drive 3 replication](docs/DRIVE3_REPLICATION.md) evaluates the frozen Rome tree and persistence on matched opportunities for AT&T, T-Mobile and Verizon. Run `python scripts/replicate_nuwins_drive3.py` to reproduce the release-file checks, forecasts and carrier/date summaries.

**Primary analysis.** The clock-triggered Rome comparison measures all issued opportunities. At ten labels the frozen tree violated 67 of 122 measurable positive commitments on E1 and two of three on E3. Of 46 missing outcomes, 45 forecast horizons extended past the recording. The session-triggered results below provide the endpoint comparison.

How much can a short chronological prefix of labeled target sessions improve a lower forecast of downlink throughput when radio telemetry is incomplete? This benchmark measures the frequency with which a bound exceeds measured throughput (V) alongside the fraction of measured throughput it supports (U). The contribution is the empirical comparison across operators, campaigns and definitions of a session.

Two public Rome releases supply the primary benchmark data. The earlier active throughput CSV is [Zenodo 8224890](https://zenodo.org/records/8224890). The later archive contains the 43 Ookla traces used here [Zenodo 14073311](https://zenodo.org/records/14073311). Both releases identify CC BY 4.0. The acquisition manifest pins the raw bytes. The session analysis uses a common source-trained histogram gradient boosting predictor, chronological calibration prefixes and fixed held-out target dates. Labels used as lagged inputs are distinct from labels counted in the target recalibration budget.

| Regime | Held-out sessions / days | Point V | Source-only global V | Ten-label global V | Ten-label global U |
|---|---:|---:|---:|---:|---:|
| E0, within earlier Op1 | 41 / 2 | 0.4390 | 0.1220 | 0.0000 | 0.0285 |
| E1, later Op1 | 139 / 7 | 0.4101 | 0.1655 | 0.0719 | 0.0725 |
| E2, earlier Op2 | 256 / 8 | 0.6211 | 0.1641 | 0.0234 | 0.0177 |
| E3, later Op2 | 103 / 7 | 0.3301 | 0.1262 | 0.0000 | 0.0060 |

These proportions use four decimal places. At K=0,1,2,5,8 the global rule uses a source offset and exceeds 10% in every regime. At K=9 the maximum target score first yields a finite offset at alpha=0.10. Grouped and global bounds coincide at K=10. At K=15 grouped E1 narrowly exceeds the target. Use the [full benchmark CSV](results/metrics/calibration_budget_results.csv) for all 124 available regime/budget/method combinations and the [manuscript](paper/manuscript.pdf) for the rendered tables. There is no established universal measurement budget.

The later sessions are heuristic. Changing their endpoints substantially changes violations. Two to eight test dates per regime, a single chronological prefix and two campaigns in the same city limit inference. The test-day bootstrap conditions on the fitted model and prefix. See the [segmentation audit](docs/SESSION_SEGMENTATION_AUDIT.md), [statistical audit](docs/STATISTICAL_INFERENCE_AUDIT.md), [final audit](docs/FINAL_RESEARCH_AUDIT.md) and [readiness assessment](docs/FINAL_RESEARCH_READINESS_MATRIX.md).

## Reliability across issued forecasts

At ten target labels the frozen tree violated at least 67 of 238 E1 clock forecasts, even if every unmeasured throughput covered its commitment. On E3 it made only three positive commitments across 171 issued forecasts. The finite-record risk interval accounts for the fact that a zero commitment cannot violate a nonnegative target. It does not estimate future deployment risk.

Run `python scripts/clock_frontier.py` for the matched Rome experiment, every feasible target prefix and the frontier plot. The [clock audit](docs/CLOCK_TRIGGERED_PRIMARY_MODEL_AUDIT.md), [statistical design](docs/STATISTICAL_DESIGN_IMPROVEMENT.md), [transfer protocol](docs/CROSS_NETWORK_GENERALIZATION.md) and [stress analysis](docs/ADVERSARIAL_ROBUSTNESS_AUDIT.md) document the denominators, feedback and limits. The [reviewer assessment](docs/FINAL_REVIEW.md) separates scientific contribution from manuscript preparation.

## Reproduction

Use Python 3.11, a matching PyTorch build and the dependencies in requirements.txt. Install the Tectonic LaTeX compiler on PATH or set TECTONIC to its executable. Its first run may download TeX resources. The local run used an RTX 4060 for the neural comparator. The primary histogram model runs on CPU. From the repository root run:

```sh
python -m pip install -r requirements.txt -c constraints-research.txt
python scripts/reproduce_all.py
```

The entry point checks the archive, materializes matching individual traces, verifies downloads, exercises the test suite, fits the models, runs the ablations, rebuilds diagnostics, generates and checks manuscript artifacts and runs the tests again. The [manifest](docs/REPRODUCIBILITY_MANIFEST.json) records the commands, environment, counts and SHA-256 evidence for the working tree. The [consistency procedure](docs/MANUSCRIPT_CONSISTENCY_VALIDATION.md) identifies the source for each table. The [submission package](paper/submission_package.pdf) contains the cover letter and manuscript. [HTML](paper/manuscript.html) and [Markdown](paper/manuscript.md) are generated from the same LaTeX.

The original full-run record and its associated stages are recorded in [execution.json](results/runs/execution.json) and the updated [JUnit report](results/runs/final_tests.xml). The current working tree has no hosted CI result. The workflow checks the published artifacts, fetches the Rome data, runs the full test suite, rejects skipped tests and uploads the report.

The [revision execution report](docs/FINAL_EXECUTION_REPORT.md) lists commands for the revised experiments, [methodological review](docs/INDEPENDENT_RESEARCH_AUDIT.md), and [submission assessment](docs/FINAL_SCORECARD.md). Run `python scripts/generate_experiment_manifest.py --verify` for a read-only integrity check.

## Prediction-time and independent validation

A clock-triggered replay preserves the Rome target dates and records all issued forecasts, including those without a measurable future label. The independent Norwegian bus-route evaluation uses seven chronological dates, 17 logs, two lag-based predictors and ten calibration labels. See the [prediction-time audit](docs/PREDICTION_TIME_VALIDITY_AUDIT.md), [external protocol](docs/EXTERNAL_VALIDATION_PROTOCOL.md), [data provenance](docs/EXTERNAL_DATA_PROVENANCE.md), and [current reviewer assessment](docs/FINAL_REVIEW.md). The aggregate evidence supports an empirical measurement paper. The full pipeline obtains the pinned raw inputs, rebuilds the Irish reproduction and replays both Norwegian routes. The following commands also run the Irish analyses separately.

## Reproducing the external comparison

The Irish comparison uses the Raca 5G production archive at `data/raw/ucc-external/5G-production-dataset.zip` and Sirhan's [version 1 replication archive](https://data.mendeley.com/datasets/ncbdm2c36d/1). With the Rome input files in place, run the following from the repository root. The ordinary manuscript build reads the saved external results.

```text
python scripts/compare_sirhan_external.py PATH_TO_MENDELEY_V1_ZIP
python scripts/compare_published_global_rule.py
python scripts/audit_external_traces.py
python scripts/report_sirhan_external.py
python scripts/validate_irish_groups.py
python scripts/build_paper_html.py
python scripts/validate_manuscript_consistency.py
```

## November 21 critical audit

The [critical audit](docs/FINAL_MARUR_CRITICAL_AUDIT.md), [all matched-cost results](docs/MATCHED_COST_ANALYSIS.md), [prospective protocol](docs/PROSPECTIVE_VALIDATION_PROTOCOL.md), and [submission decision](docs/IEEE_SUBMISSION_DECISION.md) supersede earlier readiness ratings. Reproduce the added audit with `python scripts/audit_marur.py`, validate with `python scripts/validate_marur_audit.py`, and render its report with `python scripts/write_matched_cost_report.py`. The full reproduction pipeline includes these stages.

## Reproducing the final scientific checks

Use Python 3.11. For the complete research environment, install `python -m pip install -r requirements.txt -c constraints-research.txt`; supply Tectonic through `TECTONIC`. The full `python scripts/reproduce_all.py` acquires/verifies data, refits original models (CPU fallback or CUDA GPU for optional neural comparator), replays policies, rebuilds all 19 tables and PDF/HTML exports, and logs every stage into [execution.json](results/runs/execution.json) from a clean Python 3.11 virtual environment.

A smaller clean-environment check of every stored controller decision requires only NumPy and pandas:

```sh
python -m venv .venv-audit
# Activate .venv-audit using your platform's activation command.
python -m pip install -c constraints-research.txt numpy pandas pytest
python scripts/reproduce_saved_marur.py
python -m pytest tests/unit/test_marur_audit_validator.py -q
```

This replays all 576 original and 720 matched-cost configurations from frozen saved opportunities, compares every action/response field, and independently validates all 576 candidate pairs (384 exact-cost). It does not reacquire raw archives, refit predictors, or validate the complete dependency stack. The execution receipt records the actual interpreter, packages, inputs and result. Fresh dependencies and stored forecasts are different reproducibility boundaries.

With the full environment installed, run `python scripts/validate_manuscript_consistency.py`, `python -m pytest -q --junitxml=results/runs/final_tests.xml`, then regenerate and verify the artifact manifest after any source/artifact changes. Table 14 reports NEW queries, never an assumed physical cost for ten historical labels. Frozen's positive-cap rows remain lower-cost references. The synthetic feedback mask is position-based and aliases with Periodic.
# Exploratory information-freshness extension

The fixed-model clock/window experiment is documented in [its protocol](docs/MARUR_INFORMATION_EXPERIMENT_PROTOCOL.md) and [complete results](docs/MARUR_INFORMATION_EXPERIMENT_RESULTS.md). It is exploratory on previously inspected cohorts, uses shared timestamp-based feedback masks, and preserves the original MARUR outputs. The observed-label freshness clock is optional; production defaults are unchanged. Reproduce with `python scripts/run_marur_information_experiment.py`, validate with `python scripts/validate_marur_information_experiment.py`, and regenerate the report with `python scripts/report_marur_information_experiment.py`.
