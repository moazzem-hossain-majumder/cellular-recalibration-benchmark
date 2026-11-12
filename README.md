# Cellular throughput recalibration benchmark

How much can a short chronological prefix of labeled target sessions improve a lower forecast of downlink throughput when radio telemetry is incomplete? This benchmark measures the frequency with which a bound exceeds measured throughput (V) alongside the fraction of measured throughput it supports (U). The contribution is the empirical comparison across operators, campaigns and definitions of a session.

Two public Rome releases supply the primary benchmark data. The earlier active throughput CSV is [Zenodo 8224890](https://zenodo.org/records/8224890). The later archive contains the 43 Ookla traces used here [Zenodo 14073311](https://zenodo.org/records/14073311). Both releases identify CC BY 4.0. The acquisition manifest pins the raw bytes. The primary regime uses a common source-trained histogram gradient boosting predictor, chronological calibration prefixes and fixed held-out target dates. Labels used as lagged inputs are distinct from labels counted in the target recalibration budget.

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
python -m pip install -r requirements.txt
python scripts/reproduce_all.py
```

The entry point checks the archive, materializes matching individual traces, verifies downloads, exercises the test suite, fits the models, runs the ablations, rebuilds diagnostics, generates and checks manuscript artifacts and runs the tests again. The [manifest](docs/REPRODUCIBILITY_MANIFEST.json) records the commands, environment, counts and SHA-256 evidence for the working tree. The [consistency procedure](docs/MANUSCRIPT_CONSISTENCY_VALIDATION.md) identifies the source for each table. The [submission package](paper/submission_package.pdf) contains the cover letter and manuscript. [HTML](paper/manuscript.html) and [Markdown](paper/manuscript.md) are generated from the same LaTeX.

The scope and outcomes of the latest local run are recorded in [execution.json](results/runs/execution.json) and the [post-build JUnit report](results/runs/final_tests.xml). The current working tree has no hosted CI result. The workflow checks the published artifacts, fetches the Rome data, runs the full test suite, rejects skipped tests and uploads the report.

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
