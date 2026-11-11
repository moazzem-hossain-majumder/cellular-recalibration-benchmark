# Research Integrity Remediation and Technical Audit Report

**Project Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Branch:** `fix/research-integrity-review`  
**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Date:** November 2026  

---

## 1. Executive Summary

This report documents the root-cause analysis, engineering remediation, and empirical validation of all technical and research-integrity issues identified in the initial review of the *Cellular Recalibration Benchmark*. Every issue has been resolved at the source-code level, independently tested with 37 automated unit and integration tests, cross-validated against authentic measurement data (Zenodo 8224890 & 14073311), and fully synchronized with the manuscript.

---

## 2. Comprehensive Remediation Matrix

| Defect ID | Severity | Root Cause Description | Source Files Remediated | Technical Verification & Evidence | Status |
|---|:---:|---|---|---|:---:|
| **P0-1** | **Critical** | **E0 Within-Domain Partition Overlap:** Within-domain evaluation previously re-used overlapping days for training, calibration, and testing, artificially suppressing empirical violation rates. | `src/data/splits.py`, `tests/test_splits.py`, `tests/integration/test_real_splits.py` | Implemented 5-way chronological day splitting (35% train, 10% val, 15% source calib, 15% target calib pool, 25% test suffix). Verified 100% disjoint session IDs and dates. Zero train/test leakage. | **RESOLVED** |
| **P0-2** | **Critical** | **Ambiguous Split Regime API:** `create_experiment_splits()` previously relied on DataFrame identity heuristics (`source_df is target_df`) to detect within-domain vs transfer regimes, creating fragile edge cases. | `src/data/splits.py`, `src/experiments/runner.py`, `src/experiments/ablations.py`, `tests/` | Made `experiment_type` a mandatory parameter (`'within_domain'` or `'transfer'`). Enforced strict `ValueError` on omitted or unsupported types across all callers. | **RESOLVED** |
| **P0-3** | **Critical** | **CS-CP Transductive Evaluation Leakage:** In `src/experiments/ablations.py`, `calib_cs.fit_weights_and_scores(...)` previously received `test_df` as the target reference set without explicit protocol disclosure, conflating transductive and non-transductive evaluation. | `src/evaluation/conformal.py`, `src/experiments/ablations.py`, `results/metrics/covariate_shift_conformal.json` | Implemented and benchmarked two explicit protocols: **Protocol A (Strict Non-Transductive)** using `splits.target_calib_pool` and **Protocol B (Transductive)** using `test_df`. Implemented Kish's Effective Sample Size (ESS) and evaluated tight (`[0.1, 10.0]`) vs wide (`[0.01, 100.0]`) clipping. | **RESOLVED** |
| **P0-4** | **Critical** | **2023 Ookla Session Segmentation Heuristic:** 2023 Ookla Speedtest sessions were segmented using a drop threshold without prior numeric data cleaning or cross-strategy validation. | `src/data/loader.py`, `scripts/audit_session_segmentation.py`, `results/diagnostics/session_segmentation_comparison.json` | Enforced pre-segmentation numeric validation (`val_mbps >= 0` and non-null). Audited all 43 Ookla trace files comparing threshold reset (-5/5 Mbps), relative drop (-2/1 Mbps), and active burst (>1 Mbps, 10s gap). Confirmed $r = 0.8365$ correlation and 100% non-negative rows. | **RESOLVED** |
| **P1-1** | **Major** | **Cryptographic Hash Inconsistencies:** `results/runs/experiment_manifest.json` contained synthetic SHA-256 hashes that diverged from the true cryptographic hashes of the raw Zenodo archives. | `scripts/generate_experiment_manifest.py`, `results/runs/experiment_manifest.json`, `data/metadata/acquisition_manifest.json` | Dynamically re-computed and verified authentic SHA-256 checksums from raw files on disk: `97de5593...` for 8224890 and `f8bc2a62...` for 14073311. | **RESOLVED** |
| **P1-2** | **Major** | **ACI Learning Rate Parameter Discrepancy:** The manuscript and documentation cited $\gamma = 0.02$, while code implementations utilized $\gamma = 0.05$. | `src/evaluation/conformal.py`, `src/experiments/runner.py`, `paper/manuscript.md`, `paper/manuscript.tex` | Reconciled parameter across codebase, figures, and manuscripts to $\gamma = 0.05$, providing explicit engineering justification (agile response to channel handovers without score volatility). | **RESOLVED** |
| **P1-3** | **Major** | **Overgeneralized Conformal Guarantee Claims:** Manuscript text asserted that split-conformal calibration universally guarantees $V \le 0.10$, glossing over the empirical $V=0.122$ (E1) and $V=0.164$ (E2) trade-offs at $K=10$. | `paper/manuscript.md`, `paper/manuscript.tex`, `scripts/build_paper_html.py` | Revised abstract, text, and conclusion: clarified that global conformal achieves conservative coverage ($V \le 0.072$), while grouped conformal offers an explicit risk-utility trade-off ($U$ up to $10.5\times$ higher with slightly elevated $V$). | **RESOLVED** |
| **P1-4** | **Major** | **Clarification of Lemma 1 Activation Cutoff:** Lemma 1 was framed as an operational panacea rather than a finite-sample mathematical order-statistic cutoff. | `paper/manuscript.md`, `paper/manuscript.tex` | Explicitly formalized Lemma 1 as the mathematical threshold where $\lceil (K+1)(1-\alpha) \rceil \le K$ first holds ($K=9$ for $\alpha=0.10$), below which empirical quantiles evaluate to $+\infty$. | **RESOLVED** |
| **P1-5** | **Major** | **Bootstrap Cluster Count Transparency:** Day-cluster bootstrap confidence intervals in E0 were computed over only $G=2$ clusters, leading to degenerate intervals ($[0.0, 0.0]$). | `paper/manuscript.md`, `paper/manuscript.tex`, `docs/PHASE_4_RESULTS_AND_STATISTICAL_RIGOR.md` | Explicitly labeled E0 bootstrap results as exploratory due to $G=2$ clusters, and disclosed that E1–E3 contain $G \in [7, 8]$ clusters, advising caution regarding asymptotic inference. | **RESOLVED** |
| **P1-6** | **Major** | **Reframing of Prospective Deployment Text:** Mentions of Bangladesh telecom infrastructure could be misconstrued as empirical measurement sites rather than prospective applications. | `paper/manuscript.md`, `paper/manuscript.tex`, `docs/bangladesh_telecom_case_study.md` | Re-framed all South Asian text as prospective industry motivation, stating unequivocally that all empirical data originated from Rome, Italy. | **RESOLVED** |

---

## 3. Detailed Technical Remediation Evidence

### 3.1 P0-1 & P0-2: Leak-Free 5-Way Day Splitting & Mandatory API
In `src/data/splits.py`:
- `create_experiment_splits(source_df, target_df, experiment_type=...)` requires `experiment_type` as a string (`'within_domain'` or `'transfer'`).
- In `'within_domain'`, the dataset is partitioned into 5 chronological day blocks:
  - Train: 35% days (57 instances across 2 dates: 17.12.2020, 04.01.2021)
  - Validation: 10% days (9 instances across 1 date: 05.01.2021)
  - Source Calibration: 15% days (33 instances across 1 date: 06.01.2021)
  - Target Calibration Pool: 15% days (10 instances across 1 date: 11.01.2021)
  - Target Fixed Test Suffix: 25% days (41 instances across 2 dates: 14.01.2021, 27.01.2021)
- Programmatic assertions in `tests/test_splits.py` verify pairwise session ID and date disjointness across all 5 partitions:
  $$\text{Train} \cap \text{Test} = \emptyset, \quad \text{Val} \cap \text{Test} = \emptyset, \quad \text{Calib} \cap \text{Test} = \emptyset.$$

### 3.2 P0-3: Covariate-Shift Conformal Prediction Dual Protocol & Kish's ESS
In `src/evaluation/conformal.py` and `src/experiments/ablations.py`:
- Implemented `compute_effective_sample_size(weights)` calculating Kish's formula:
  $$\text{ESS} = \frac{\left(\sum_{i=1}^n w_i\right)^2}{\sum_{i=1}^n w_i^2}.$$
- Implemented two protocols:
  1. **Protocol A (Strict Non-Transductive):** Domain discriminator and weights fitted exclusively on source calibration and the independent target calibration pool (`splits.target_calib_pool`), keeping the test suffix strictly out-of-sample.
  2. **Protocol B (Transductive Benchmark):** Evaluated access to unlabeled test covariates.
- Results recorded in `results/metrics/covariate_shift_conformal.json`:
  - E1 (Tight `[0.1, 10.0]`): Protocol A yields $V=0.007, U=0.013$, Source ESS $= 3.35$, Test ESS $= 121.86$. Protocol B yields $V=0.014, U=0.006$.
  - E2 (Tight `[0.1, 10.0]`): Protocol A yields $V=0.016, U=0.030$, Source ESS $= 7.78$, Test ESS $= 67.57$. Protocol B yields $V=0.047, U=0.079$.
  - E3 (Tight `[0.1, 10.0]`): Protocol A yields $V=0.010, U=0.016$, Source ESS $= 22.11$, Test ESS $= 126.83$. Protocol B yields $V=0.000, U=0.010$.

### 3.3 P0-4: Pre-Segmentation Numeric Validation & 43-Trace Comparison
In `src/data/loader.py`:
- `clean_numeric(series)` is applied and filtered for `cleaned_vals.notna() & (cleaned_vals >= 0.0)` before any segmentation boundaries are evaluated.
- Evaluated all 43 Ookla trace files via `scripts/audit_session_segmentation.py`:
  - Total sessions extracted under Baseline Threshold Reset: **584 sessions** (median duration 76.0 s, median throughput 19.65 Mbps).
  - Total sessions under Relative Drop: **712 sessions** (median duration 64.0 s).
  - Total sessions under Active Burst: **930 sessions** (median duration 50.0 s).
  - Correlation between threshold reset and relative drop: $r = 0.8365$.
  - Correlation between threshold reset and active burst: $r = 0.6603$.
  - Non-negative verification: **100% of rows non-negative across all 43 files**.
- Saved full audit artifact: `results/diagnostics/session_segmentation_comparison.json`.

---

## 4. Test Suite and Build Verification

All 37 automated tests pass with 100% success rate:
```powershell
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Telecom
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.13.0, dash-4.4.1, asyncio-1.4.0
collected 37 items

tests\integration\test_real_causality.py ..                              [  5%]
tests\integration\test_real_splits.py ..                                 [ 10%]
tests\test_causality.py ..                                               [ 16%]
tests\test_conformal.py .....                                            [ 29%]
tests\test_metrics.py .                                                  [ 32%]
tests\test_splits.py .....                                               [ 45%]
tests\unit\test_synthetic_causality.py ......                            [ 62%]
tests\unit\test_synthetic_conformal.py ......                            [ 78%]
tests\unit\test_synthetic_metrics.py ...                                 [ 86%]
tests\unit\test_synthetic_splits.py .....                                [100%]

======================== 37 passed in 73.92s (0:01:13) ========================
```

---

## 5. Conclusion

All critical and major defects identified during the initial integrity review have been rigorously remediated. The codebase, experimental outputs, manifests, diagnostics, and manuscripts are completely synchronized, mathematically defensible, and ready for peer-reviewed IEEE submission.

