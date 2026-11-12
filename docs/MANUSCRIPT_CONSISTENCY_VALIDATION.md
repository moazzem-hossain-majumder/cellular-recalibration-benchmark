# Source to publication checks

The experiment runner saves test_forecasts.csv keyed by regime, chronological budget and session. Each record has a date, target and the four method bounds. The validator re-aggregates these into the calibration_budget_results.csv keys and checks the row count, violation rate, supported fraction, mean bound, zero fraction and mean excess. Full-precision aggregate comparisons tolerate only numerical summation differences. The split JSON independently supplies the available budgets and suffix denominator. Missing or duplicated cells are errors.

| Published table | Authoritative input | Display precision |
|---|---|---|
| Point predictors | point_predictor_profiles.json, measured source-validation errors and fit times | 2 decimals for Mbps, 3 for seconds |
| Main benchmark | calibration_budget_results.csv checked against individual forecasts and split_summary.json | 4 decimals, exact integer counts |
| Boundary sensitivity | session_boundary_sensitivity.json checked against per-segment and per-operator forecast CSVs | 4 decimals, exact counts |
| Cluster contrasts | bootstrap_significance_tests.json, rerun paired resampling on per-date forecast records | 4 decimals, exact dates count |
| Secondary protocols | online_aci_results.json and each protocol/clip entry in covariate_shift_conformal.json | 4 decimals |
| Irish frontier | matched_frontier.csv checked against the feasible grid in decision_curves.csv | 2 decimals for reruns, exact paired counts |
| Irish fixed level and exclusions | fixed_trace_totals.csv aggregated by seed and method, with persistent IDs for exclusions | 2 decimals, exact counts |
| Lag transitions | lag_transitions.csv generated from unique Irish feature rows and the Rome held-out suffixes | 2 decimals for errors and correlations, 1 decimal for percentages |

scripts/publication_tables.py enumerates the named columns and budgets. The builder emits both copies of each LaTeX table, synchronizes figures, compiles the sources with Tectonic and converts the LaTeX to Markdown and HTML with Pandoc. The PDF package combines the cover letter with the same manuscript pages. A SHA-256 source fingerprint covers LaTeX, bibliography, tables and figures. It detects edits made after PDF generation.

scripts/validate_manuscript_consistency.py parses every data row and the headers in both TeX directories, Markdown and HTML. It extracts complete normalized table lines from both PDFs with PyMuPDF, in page and row order, and compares their cells with the named table specifications. Each table has a unique header and fits on one page in this layout. A layout that wraps cells needs an explicit parser update. Checks use the exact displayed rounding string. The validator also checks the README summary by regime and compares manuscript and packaged page renderings. Page content comparison and a source fingerprint check complement the cell comparison. Negative tests cover a swapped row, swapped cells, incorrect value, removed method, omitted regime, one last-place rounding error and stale PDF.

These checks validate reported numeric tables. They do not prove scientific assumptions such as exchangeability or the accuracy of inferred physical session boundaries.
