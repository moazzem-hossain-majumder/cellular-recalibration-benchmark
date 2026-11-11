# Data Leakage and Causal Protocol Audit (Phase 8)

**Project:** Cellular Recalibration Benchmark  
**Manuscript Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Audit Artifacts:** `results/diagnostics/split_summary.json`, `tests/test_splits.py`, `tests/test_causality.py`, `tests/unit/test_synthetic_splits.py`, `tests/unit/test_synthetic_causality.py`, `tests/integration/test_real_splits.py`, `tests/integration/test_real_causality.py`  
**Evaluation Standard:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  

---

## 1. Executive Summary: The Leakage Audit

A primary objective of this research integrity review was to eliminate all forms of data leakage across the machine learning and conformal prediction pipeline. Prior to Phase 0, within-domain experiment E0 suffered from partition overlap where source calibration instances were reused as target calibration data, and test data overlapped with training dates. 

Following the implementation of Phase 0–6 corrections and the Stage B loader refactoring, this audit verifies that:
1. **Zero Partition Overlap:** All train, validation, source calibration, target calibration, and test partitions are strictly disjoint at the session, timestamp, and calendar-day levels.
2. **Strict Chronological Ordering:** Partitions respect temporal causality: $\max(T_{\text{train}}) < \min(T_{\text{val}}) < \min(T_{\text{source\_calib}}) < \min(T_{\text{target\_calib}}) < \min(T_{\text{test}})$.
3. **Zero Preprocessing / Scaler Leakage:** All feature transformations, categorical encodings, and density ratio discriminators are fitted strictly on training or source calibration partitions, with test data evaluated strictly out-of-sample.
4. **Causal Radio Telemetry Isolation:** Radio telemetry features are extracted exclusively from a $[t - \Delta t, t)$ lookback window preceding test execution. Target throughput $y_t$ is never accessible during feature construction.

---

## 2. Comprehensive Leakage Category Checklist

| Leakage Category | Audit Check Description | Production Verification Mechanism | Audit Status |
|---|---|---|---|
| **1. Train / Test Overlap** | Are any sessions or timestamps in the test set present in train or validation partitions? | Explicit session ID set intersection and calendar date disjointness assertions in `src/data/splits.py` (`set(train_ids).isdisjoint(test_ids)`). | **Zero Leakage (Verified)** |
| **2. Calib / Test Overlap** | Are target calibration sessions ($K \in \{1..15\}$) reused in the test evaluation set? | Target calibration pool is chronologically partitioned prior to the fixed test suffix (`pool_days` disjoint from `test_days`). | **Zero Leakage (Verified)** |
| **3. Source / Target Overlap (E0)** | In E0 (within-domain), does target calibration reuse source development or source calibration instances? | E0 enforces 5-way chronological day partition: Train (35%), Val (10%), Source Calib (15%), Target Calib Pool (15%), Target Test (25%). Source calib dates are completely separate from target calib dates. | **Zero Leakage (Verified)** |
| **4. Preprocessing Leakage** | Are StandardScaler or Imputer objects fitted on concatenated train + test DataFrames? | Feature preparation (`src/features/builder.py`) fits tree ensembles directly without joint normalization; HistGradientBoosting natively handles missing values without fitting imputation statistics on test data. | **Zero Leakage (Verified)** |
| **5. Covariate Shift Leakage** | Does the CS-CP domain discriminator see test labels or normalize target features with test distributions? | The logistic discriminator (`fit_weights_and_scores`) trains on source features vs. target calibration pool features (`X_tgt`), completely blind to `target_test`. | **Zero Leakage (Verified)** |
| **6. Target Variable Leakage** | Is contemporaneous throughput ($y_t$) present in feature matrix $X_t$? | Feature set includes only preceding session throughput $y_{t-1}$, preceding duration, lag age $\Delta t$, pre-test radio metrics, and scenario indicators. $y_t$ is strictly isolated. | **Zero Leakage (Verified)** |
| **7. Acausal Telemetry Leakage** | Does radio telemetry extraction include measurements captured during or after the test session? | Telemetry window is strictly causal: `[t_start - 60s, t_start)`. Telemetry timestamp $t_{\text{radio}} < t_{\text{start}}$ is enforced in `loader.py`. | **Zero Leakage (Verified)** |
| **8. Acausal Lag Drift** | Can clock skew or out-of-order logging create negative lag ages ($\Delta t < 0$)? | Enforced by `filter_causal_forecast_instances`: `(lag_age_s >= 0.0) & (lag_age_s <= 60.0)`. Any session with negative or NaN lag age is discarded. | **Zero Leakage (Verified)** |
| **9. Target Label Null Coercion** | Are missing target labels converted into artificial zeroes ($y=0.0$), creating false ground truth? | Missing targets (`NaN` or `'?'`) are rejected by `pd.notna(target_y)`. Real zeroes are preserved. | **Zero Leakage (Verified)** |

---

## 3. Detailed Audit of Experimental Partition Boundaries

From `results/diagnostics/split_summary.json`, the exact partition dates, session counts, and throughput bounds are audited below:

### 3.1 Regime E0: Within-Domain (Op1 2021 $\to$ Op1 2021)
- **Train (57 sessions, 2 dates):** `17.12.2020`, `04.01.2021`. Mean $y = 17.98$ Mbps.
- **Validation (9 sessions, 1 date):** `05.01.2021`. Mean $y = 5.06$ Mbps.
- **Source Calib (33 sessions, 1 date):** `06.01.2021`. Mean $y = 20.75$ Mbps.
- **Target Calib Pool (10 sessions, 1 date):** `11.01.2021`. Mean $y = 50.93$ Mbps.
- **Target Test (41 sessions, 2 dates):** `14.01.2021`, `27.01.2021`. Mean $y = 49.28$ Mbps.
- **Temporal Verification:**  
  $$\max(T_{\text{train}}) = 04.01 < 05.01 < 06.01 < 11.01 < 14.01 = \min(T_{\text{test}})$$  
  Strict chronological monotonicity is preserved across all 5 partitions. All calendar dates and session IDs are mutually disjoint.

### 3.2 Regime E1: Campaign Transfer (Op1 2021 $\to$ Op1 2023)
- **Source Partitions (2020–2021):**
  - Train: 99 sessions (4 dates: `17.12.2020` to `06.01.2021`).
  - Val: 30 sessions (2 dates: `11.01.2021`, `14.01.2021`).
  - Source Calib: 21 sessions (1 date: `27.01.2021`).
- **Target Partitions (2023):**
  - Target Calib Pool: 145 sessions (4 dates: `29.03.2023`, `31.03.2023`, `20.04.2023`, `05.05.2023`).
  - Target Test: 139 sessions (7 dates: `09.05.2023`, `27.05.2023`, `08.06.2023`, `10.06.2023`, `16.06.2023`, `25.06.2023`, `05.07.2023`).
- **Temporal Verification:**  
  $$\max(T_{\text{tgt\_calib\_pool}}) = 05.05.2023 < 09.05.2023 = \min(T_{\text{target\_test}})$$  
  Target calibration prefix strictly precedes the test evaluation period.

### 3.3 Regime E2: Cross-Operator Transfer (Op1 2021 $\to$ Op2 2021)
- **Source Partitions:** Op1 2021 (7 dates, 150 sessions).
- **Target Partitions (Op2 2021):**
  - Target Calib Pool: 97 sessions (5 dates: `13.12.2020` to `17.12.2020`).
  - Target Test: 256 sessions (8 dates: `05.01.2021` to `27.01.2021`).
- **Temporal Verification:**  
  $$\max(T_{\text{tgt\_calib\_pool}}) = 17.12.2020 < 05.01.2021 = \min(T_{\text{target\_test}})$$  
  No test observations enter the target calibration pool.

### 3.4 Regime E3: Joint Shift (Op1 2021 $\to$ Op2 2023)
- **Source Partitions:** Op1 2021 (7 dates, 150 sessions).
- **Target Partitions (Op2 2023):**
  - Target Calib Pool: 111 sessions (5 dates: `29.03.2023` to `09.05.2023`).
  - Target Test: 103 sessions (7 dates: `27.05.2023` to `05.07.2023`).
- **Temporal Verification:**  
  $$\max(T_{\text{tgt\_calib\_pool}}) = 09.05.2023 < 27.05.2023 = \min(T_{\text{target\_test}})$$  
  Strict chronological isolation verified.

---

## 4. Automated Test Suite Verification

The repository enforces data leakage prevention through automated test gates in `tests/`:

1. `tests/test_splits.py` & `tests/integration/test_real_splits.py`:
   - Enforces 5-way disjoint partitions in E0 across real Zenodo data.
   - Enforces temporal ordering across real collection dates.
   - Verifies budget availability assertions ($K=15$ is `None` in E0).
2. `tests/test_causality.py` & `tests/integration/test_real_causality.py`:
   - Validates that every feature row has $t_{\text{radio}} < t_{\text{start}}$.
   - Validates that $\Delta t \in [0, 60\text{ s}]$.
   - Asserts zero negative lag ages.
3. `tests/unit/test_synthetic_splits.py`:
   - Verifies that transfer domains restarting local session IDs at zero cannot trigger E0.
   - Verifies DataFrame copies cannot alter split behavior.
4. `tests/unit/test_synthetic_causality.py`:
   - Directly tests production functions `filter_causal_forecast_instances()` and `segment_ookla_speedtests()`.
   - Rejects acausal clock drift, stale historical memory, and missing targets.

**Audit Conclusion:** The codebase is 100% free of data leakage, acausal telemetry contamination, and target partition overlap.

