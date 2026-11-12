# Final research audit

**Reviewer-style verdict: Major revisions required, 6/10.** The corrected study provides a retrospective benchmark of rate commitments on two Rome measurement campaigns. Its scientific contribution is the observed dependence on calibration prefix and endpoint choice. The standard conformal rank formula contributes no new theorem.

## Corrections and numerical evidence

The grouped implementation previously jumped from an infinite group quantile directly to a source offset even when a finite pooled target offset was available. The correction in src/evaluation/conformal.py restores the documented fallback. At ten labels the previous grouped-minus-global supported-rate differences were +0.0372 in E1 and +0.1710 in E2. They become zero in both. Individual bounds coincide in all four regimes. The baseline report identifies the commit containing the original results.

| Regime | Test sessions | Dates | Point V | Source V | Global V at K=9 | Global V at K=10 | Global U at K=10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| E0 |41|2|0.4390|0.1220|0.0976|0.0000|0.0285|
| E1 |139|7|0.4101|0.1655|0.0719|0.0719|0.0725|
| E2 |256|8|0.6211|0.1641|0.0234|0.0234|0.0177|
| E3 |103|7|0.3301|0.1262|0.0291|0.0000|0.0060|

Proportions use four decimal places from results/metrics/calibration_budget_results.csv. Table II contains every available budget and method. All source-fallback settings exceed 10%. At 15 labels grouped E1 has 14 violations in 139 forecasts. Rounding to two decimal places masks its threshold crossing. E0 has ten available calibration observations.

The per-trace diagnostic retains the adverse active-start rates. Source-only E1/E3 violation rates reach 0.4024/0.4918 rather than the 0.1479/0.2523 seen under reset. Filtering zero endpoints from scoring only partly reduces the discrepancy. Measured durations, raw timestamp gaps and example segments are in SESSION_SEGMENTATION_AUDIT.md. The source-only diagnostic uses all eligible later pairs, whereas the main test uses held-out dates.

Nine calibration scores activate a finite rank for alpha=0.10. This says nothing about practical usefulness or exchangeability under shift. Even at ten labels the chosen quantile is the largest observed score. The previously claimed operational campaign minimum was withdrawn. Source partitions recorded for the main benchmark now reflect the frozen predictor and offset actually used across regimes.

The re-estimated cluster contrasts and day-deletion estimates are in STATISTICAL_INFERENCE_AUDIT.md. All regimes fall below the proposed ten-date threshold for confirmatory inference. The same-day grouped and global estimates coincide at ten labels, giving a degenerate paired interval. This cannot establish population equivalence.

## Artifacts and execution

The manuscript, Markdown, HTML, figures and cover package derive from the same source. The IEEE-style draft removes unverified membership, received date, volume and issue. The BAMMO author names and later campaign citation were corrected. The paper retains online and weighted calibration, artificial masking, minimum group support, lookback, nominal-risk and offline penalty analyses. MANUSCRIPT_CONSISTENCY_VALIDATION.md maps the numerical tables to their authoritative outputs. The benchmark and sensitivity predictions provide a record for independent aggregation.

The full local suite passed before and after artifact generation. Each run executed 55 tests with zero skipped, deselected or failed, including four integration-directory tests and three legacy checks using real measurements. The remaining ten legacy tests are data-free. Thirty unit-directory tests exercise synthetic or mathematical cases and eight exercise publication artifacts. The local run used the RTX 4060 for the neural comparator. Tectonic reported a host Fontconfig configuration warning, and the compiled pages were rendered and inspected. No unresolved citation or overfull-box indication survived the build check. The final pytest run completed in 86.78 seconds. Both archived raw releases and 43 extracted trace CSVs were verified locally. All five numerical tables passed structural checks in both PDFs. The reproducibility manifest records the working-tree source hashes, JUnit test outcomes, environment and run stages. The old manifest hard-coded its test results. The original commit passed [workflow run 43069521042](https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark/actions/runs/43069521042) using the unit marker. It supplies no remote evidence for the local corrections. Updated CI checks published artifacts and runs the complete suite with pinned real inputs.

## Remaining publication risks

No independent test-start or completion record validates the later units. A throughput reset is itself recognized retrospectively, limiting prospective applicability. The sparse test dates and single chronological prefix make absolute estimates fragile. Persistence beats the common histogram predictor on the nine source-validation observations. NR-presence and LTE/NR-pattern groups induce identical partitions in these eligible data. The offline supported fraction does not measure user experience, operator revenue or performance in Bangladesh.

The strongest additional evidence would come from an untouched network with independently logged test boundaries, multiple chronological calibration prefixes and more independent held-out dates. The software and source checks cannot supply those observations.
