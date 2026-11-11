# Phase 2: Decoupled Testing & CI Pipeline

**Benchmark:** Cellular Throughput Recalibration Under Incomplete Telemetry  
**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Target Venue:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  
**Date:** March 2026  
**Status:** COMPLETED & VERIFIED  

---

## 1. Overview and Testing Philosophy

In empirical wireless communications and machine learning research, test suites often fail in continuous integration (CI) environments because raw drive-test datasets are too large to commit to Git or require authenticated external download scripts.

Phase 2 established a strict decoupling between:
1. **Deterministic Unit Tests (`tests/unit/`):** Fast, standalone tests that construct synthetic telemetry and forecast frames in memory. They rigorously verify all mathematical formulas, boundary conditions, edge cases, data leakage guards, and split invariants without external files.
2. **Real-Data Integration Tests (`tests/integration/`):** End-to-end integration tests that execute against authentic Zenodo measurement archives (8224890 and 14073311) when present on disk. When raw datasets are absent, integration tests skip gracefully using `@pytest.mark.skipif`.
3. **Automated CI Workflow (`.github/workflows/tests.yml`):** Automatically executes the complete unit test suite on Python 3.11 for every pull request and commit.

---

## 2. Test Suite Architecture

```
tests/
├── conftest.py                       # Global fixtures, raw data detection, skip decorators
├── unit/                             # Deterministic CI Unit Tests (17 tests, ~1.5s runtime)
│   ├── __init__.py
│   ├── test_synthetic_splits.py      # E0 5-way partition, K-budget integrity, disjointness
│   ├── test_synthetic_causality.py   # Lag freshness [0, 60s], negative lag rejection, y=0 vs NaN
│   ├── test_synthetic_conformal.py   # Quantile formula, Lemma 1 n>=9 threshold, CS-CP, ACI
│   └── test_synthetic_metrics.py     # Violation rate, supported fraction, cluster bootstrap
└── integration/                      # Real Field-Data Integration Tests (4 tests, ~50s runtime)
    ├── __init__.py
    ├── test_real_splits.py           # Authentic Zenodo partitions and date disjointness
    └── test_real_causality.py        # Real-world lag ages, RSRP/SS-RSRP physical ranges
```

---

## 3. Unit Test Coverage & Verification

### `tests/unit/test_synthetic_splits.py`
- `test_synthetic_e0_partitions_are_disjoint_and_budgets_are_explicit`: Verifies that E0 creates 5 mutually disjoint partitions across sessions and dates, and that unavailable budgets ($K=15$ when $N_{\text{calib}}=10$) return `None` rather than a truncated prefix.
- `test_transfer_domains_with_reused_local_session_ids_are_not_misclassified_as_e0`: Verifies that transfer datasets with overlapping local session IDs are not erroneously classified as E0.
- `test_explicit_regime_and_within_domain_parameter`: Verifies that passing `experiment_type='within_domain'` or `regime='E0...'` enforces the 5-way split even on DataFrame copies.
- `test_generate_split_summary_structure`: Validates the structure and fields of the split diagnostics metadata.

### `tests/unit/test_synthetic_causality.py`
- `test_freshness_gate_boundary`: Tests boundary conditions: 0.0s, 59.9s, 60.0s (all accepted) vs 60.001s (rejected).
- `test_negative_lag_age_rejection`: Confirms that clock-drifted negative lag ages ($\Delta t < 0$) are strictly discarded to eliminate forward-looking leakage.
- `test_missing_timestamp_rejection`: Confirms that missing or invalid timestamps produce NaN lag ages and are excluded.
- `test_zero_throughput_vs_nan_label_handling`: Verifies that physical zero throughput ($y=0.0$) is preserved while unrecorded labels ($y=\text{NaN}$) are dropped.

### `tests/unit/test_synthetic_conformal.py`
- `test_conformal_quantile_formula`: Validates finite-sample conformal quantile formula $\lceil (n+1)(1-\alpha) \rceil / n$.
- `test_lemma1_exact_threshold`: Proves Lemma 1 empirically: for $\alpha=0.10$, $n \le 8$ yields infinite margin (undefined), while $n \ge 9$ yields a finite calibrated quantile ($q=9.0$ at $n=9$).
- `test_global_calibrator`: Validates that `GlobalConformalCalibrator` produces non-negative, bounded lower predictions.
- `test_grouped_fallback_hierarchy`: Validates hierarchical pooling fallback when subgroup sample size is insufficient.
- `test_covariate_shift_conformal`: Verifies Bayes class-prior ratio calculation $w(x) = \frac{P(T|x)}{P(S|x)} \cdot \frac{N_{\text{src}}}{N_{\text{tgt}}}$ and weight clipping.
- `test_aci_calibrator_step`: Validates that online Adaptive Conformal Inference adjusts the margin upwards on violation and downwards on coverage.

### `tests/unit/test_synthetic_metrics.py`
- `test_metrics_edge_cases`: Verifies violation rate ($V$), supported rate fraction ($U$), and zero-bound fraction ($Z$) under perfect bounds, complete violation, all-zero policy, and physical zero targets.
- `test_subgroup_metrics_synthetic`: Verifies conditional metric evaluation across heterogeneous radio availability groups.
- `test_paired_day_cluster_bootstrap_synthetic`: Validates paired day-cluster bootstrap resampling and 95% confidence interval estimation.

---

## 4. Test Execution Results

### Fast Unit Tests (CI Suite):
```
pytest -m unit -v
====================== 17 passed, 17 deselected in 1.54s ======================
```

### Real-Data Integration Tests:
```
pytest -m integration -v
====================== 4 passed, 30 deselected in 50.84s ======================
```

### Continuous Integration Configuration:
`.github/workflows/tests.yml` runs automatically on Python 3.11 in GitHub Actions, executing the 17 unit tests on every PR.

Phase 2 is complete. Proceeding to Phase 3 (Methodology & ML Pipeline Audit).

