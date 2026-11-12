# Cellular throughput recalibration benchmark

How much can a short chronological prefix of labeled target sessions improve a lower forecast of downlink throughput when radio telemetry is incomplete? This benchmark measures the frequency with which a bound exceeds measured throughput (V) alongside the fraction of measured throughput it supports (U). The contribution is the empirical comparison across operators, campaigns and definitions of a session.

Two public Rome measurement releases supply the data. The earlier active throughput CSV is [Zenodo 8224890](https://zenodo.org/records/8224890). The later archive contains the 43 Ookla traces used here [Zenodo 14073311](https://zenodo.org/records/14073311). Both releases identify CC BY 4.0. The acquisition manifest pins the raw bytes. The primary regime uses a common source-trained histogram gradient boosting predictor, chronological calibration prefixes and fixed held-out target dates. Labels used as lagged inputs are distinct from labels counted in the target recalibration budget.

| Regime | Held-out sessions / days | Point V | Source-only global V | Ten-label global V | Ten-label global U |
|---|---:|---:|---:|---:|---:|
| E0, within earlier Op1 | 41 / 2 | 0.4390 | 0.1220 | 0.0000 | 0.0285 |
| E1, later Op1 | 139 / 7 | 0.4101 | 0.1655 | 0.0719 | 0.0725 |
| E2, earlier Op2 | 256 / 8 | 0.6211 | 0.1641 | 0.0234 | 0.0177 |
| E3, later Op2 | 103 / 7 | 0.3301 | 0.1262 | 0.0000 | 0.0060 |

These proportions use four decimal places. At K=0,1,2,5,8 the global rule uses a source offset and exceeds 10% in every regime. At K=9 the maximum target score first yields a finite offset at alpha=0.10. Grouped and global bounds coincide at K=10. At K=15 grouped E1 narrowly exceeds the target. Use the [full benchmark CSV](results/metrics/calibration_budget_results.csv) for all 124 available regime/budget/method combinations and the [manuscript](paper/manuscript.pdf) for the rendered tables. There is no established universal measurement budget.

The later sessions are heuristic. Changing their endpoints substantially changes violations. Two to eight test dates per regime, a single chronological prefix and two campaigns in the same city limit inference. The test-day bootstrap conditions on the fitted model and prefix. See the [segmentation audit](docs/SESSION_SEGMENTATION_AUDIT.md), [statistical audit](docs/STATISTICAL_INFERENCE_AUDIT.md), [final audit](docs/FINAL_RESEARCH_AUDIT.md) and [readiness assessment](docs/FINAL_RESEARCH_READINESS_MATRIX.md).

## Reproduction

Use Python 3.11, a matching PyTorch build and the dependencies in requirements.txt. Install the Tectonic LaTeX compiler on PATH or set TECTONIC to its executable. Its first run may download TeX resources. The local run used an RTX 4060 for the neural comparator. The primary histogram model runs on CPU. From the repository root run:

```sh
python -m pip install -r requirements.txt
python scripts/download_data.py
python scripts/reproduce_all.py
```

The entry point checks the archive, materializes matching individual traces, verifies downloads, exercises the test suite, fits the models, runs the ablations, rebuilds diagnostics, generates and checks manuscript artifacts and runs the tests again. The [manifest](docs/REPRODUCIBILITY_MANIFEST.json) records the commands, environment, counts and SHA-256 evidence for the working tree. The [consistency procedure](docs/MANUSCRIPT_CONSISTENCY_VALIDATION.md) identifies the source for each table. The [submission package](paper/submission_package.pdf) contains the cover letter and manuscript. [HTML](paper/manuscript.html) and [Markdown](paper/manuscript.md) are generated from the same LaTeX.

Both local test runs, before and after the publication build, executed 55 tests each with no failures, skips or deselections. Of these, 38 are unit-directory tests (30 synthetic or mathematical and 8 publication checks), 4 are real-data integration tests and 13 are legacy tests. Three legacy tests also read real data. The local real-data pipeline and both PDF checks passed. The post-build results are recorded in results/runs/final_tests.xml. The original commit 890fb28 passed its unit-selected [GitHub workflow run](https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark/actions/runs/43069521042). The corrected workflow runs artifact validation and the complete test suite with downloaded data. Local execution evidence is recorded separately from remote CI. Historical reviews and old outputs describe earlier implementations.

## Reproducing the external comparison

The Irish comparison uses the Raca 5G production archive at `data/raw/ucc-external/5G-production-dataset.zip` and Sirhan's [version 1 replication archive](https://data.mendeley.com/datasets/ncbdm2c36d/1). With the Rome input files in place, run the following from the repository root. The ordinary manuscript build reads the saved external results.

```text
python scripts/compare_sirhan_external.py PATH_TO_MENDELEY_V1_ZIP
python scripts/compare_published_global_rule.py
python scripts/audit_external_traces.py
python scripts/report_sirhan_external.py
python scripts/build_paper_html.py
python scripts/validate_manuscript_consistency.py
```
