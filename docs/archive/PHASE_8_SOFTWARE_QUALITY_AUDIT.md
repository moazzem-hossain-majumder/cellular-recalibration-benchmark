> Historical project record from before the pooled-calibration correction. For current estimates, validation status and publication assessment see [the final research audit](FINAL_RESEARCH_AUDIT.md). Interpret numerical claims below as superseded.

# Software Quality, Testing, and CI/CD Audit (Phase 8)

**Project:** Cellular Recalibration Benchmark  
**Manuscript Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Test Suite:** `tests/` (36 automated tests)  
**CI/CD Configuration:** `.github/workflows/tests.yml`  
**Evaluation Standard:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  

---

## 1. Executive Summary

A critical standard for publication-ready computational research is that software engineering and testing practices must guarantee scientific reproducibility. A common failure mode in academic machine learning repositories is that test suites test synthetic mock implementations rather than production code, masking bugs in data loading, feature engineering, and calibration.

Following the Stage B refactoring, this audit verifies that:
1. **Direct Production Testing:** All unit and integration tests import and directly exercise production functions and classes under `src/`.
2. **Two-Tier Test Architecture:** The test suite is cleanly bifurcated into:
   - **Synthetic Unit Tests (`tests/unit/`):** Fast, standalone tests executable in CI environments without external dataset downloads.
   - **Real-Data Integration Tests (`tests/integration/`):** Comprehensive integration tests validating physical causality, chronological partitions, and mathematical metrics directly against downloaded Zenodo records (8224890 and 14073311).
3. **100% Pass Rate:** All 36 automated test cases pass with zero warnings or failures.

---

## 2. Test Suite Architecture and Inventory

The test suite contains 36 dedicated test functions across 10 test modules:

```
tests/
├── conftest.py                             # Pytest fixtures and shared configuration
├── unit/                                   # Fast synthetic unit tests (CI-enabled)
│   ├── test_synthetic_causality.py         # 6 tests: lag freshness, clock drift, segmentation
│   ├── test_synthetic_conformal.py         # 6 tests: Lemma 1, fallback hierarchy, CS-CP, ACI
│   ├── test_synthetic_metrics.py           # 3 tests: edge cases, zero targets, paired bootstrap
│   └── test_synthetic_splits.py            # 4 tests: 5-way E0 split, transfer disjointness
├── integration/                            # Real-data integration tests (Zenodo validated)
│   ├── test_real_causality.py              # 2 tests: real telemetry lookback, non-negativity
│   └── test_real_splits.py                 # 2 tests: real campaign partition dates, budgets
├── test_causality.py                       # 2 tests: legacy causality verification
├── test_conformal.py                       # 5 tests: quantile indexing, split conformal bounds
├── test_metrics.py                         # 1 test: standard SLA loss and supported rates
└── test_splits.py                          # 5 tests: regime integrity and chronological splits
```

### 2.1 Test Category Matrix

| Test Module | Test Focus | Production Module Exercised | Test Count | Status |
|---|---|---|---|---|
| `test_synthetic_causality.py` | Freshness gate, clock drift, `segment_ookla_speedtests()` | `src.data.loader` | 6 tests | **Passed** |
| `test_synthetic_conformal.py` | Lemma 1 cutoff, fallback hierarchy, CS-CP prior, ACI update | `src.evaluation.conformal` | 6 tests | **Passed** |
| `test_synthetic_metrics.py` | Violation rate, supported fraction, paired cluster bootstrap | `src.evaluation.metrics` | 3 tests | **Passed** |
| `test_synthetic_splits.py` | 5-way E0 split, transfer disjointness, budget metadata | `src.data.splits` | 4 tests | **Passed** |
| `test_real_causality.py` | Causal radio window ($t_{\text{radio}} < t_{\text{start}}$) on real Zenodo traces | `src.data.loader` | 2 tests | **Passed** |
| `test_real_splits.py` | Chronological date partitions and budgets on real Zenodo data | `src.data.splits` | 2 tests | **Passed** |
| `test_splits.py` | Chronological partition bounds and budget availability | `src.data.splits` | 5 tests | **Passed** |
| `test_conformal.py` | Conformal quantile indexing and lower bounds | `src.evaluation.conformal` | 5 tests | **Passed** |
| `test_metrics.py` | Telecommunication SLA and reliability metrics | `src.evaluation.metrics` | 1 test | **Passed** |
| `test_causality.py` | Timestamp alignment and lag freshness validation | `src.data.loader` | 2 tests | **Passed** |
| **Total Test Suite** | **Full End-to-End Pipeline Verification** | **`src/` (All modules)** | **36 tests** | **36 Passed (100%)** |

---

## 3. CI/CD Pipeline Verification

The repository incorporates continuous integration via GitHub Actions (`.github/workflows/tests.yml`):

### 3.1 Workflow Specification
- **Trigger Events:** Automated execution on every `push` and `pull_request` targeting `main`, `master`, and `fix/**` branches.
- **Operating Environment:** `ubuntu-latest` with Python 3.11.
- **Dependency Isolation:** Installs minimal required scientific dependencies (`torch`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `pytest`).
- **CI Test Target:** Executes `pytest -m unit -v --durations=10`.
  - Because large raw datasets (~1.5 GB) are excluded from Git via `.gitignore`, the CI runner executes all 19 synthetic unit tests in less than 3 seconds, ensuring immediate feedback on pull requests without requiring gigabyte-scale data downloads.

---

## 4. Code Quality, Type Annotations, and Maintainability

1. **Explicit Type Hints:** Production modules under `src/` utilize Python typing annotations (`Optional`, `Union`, `Tuple`, `Dict`, `List`, `Path`, `pd.DataFrame`, `np.ndarray`) across all function signatures.
2. **Defensive Error Handling:** Functions enforce parameter validation with descriptive exceptions:
   - `segment_ookla_speedtests()` raises `ValueError` on unsupported segmentation methods.
   - `create_experiment_splits()` emits clear `UserWarning` if experiment type is not explicitly provided.
   - Conformal calibrators return infinite quantiles (`np.inf`) and flag `insufficient_data` when calibration sets are too small.
3. **Hardware Agnostic Execution:** Neural baseline (`GPUThroughputNeuralPredictor` in `src/models/neural.py`) automatically detects CUDA availability. If an NVIDIA GPU (e.g. RTX 4060) is present, it accelerates training; otherwise, it falls back seamlessly to CPU execution without crashing.

