# Phase 1: Data Integrity, Freshness, and Split Protocol Corrections

**Benchmark:** Cellular Throughput Recalibration Under Incomplete Telemetry  
**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Target Venue:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  
**Date:** March 2026  
**Status:** COMPLETED & VERIFIED  

---

## 1. Executive Summary

Phase 1 addressed all P0 and P1 data integrity, temporal causality, and partition validity issues identified during the initial research audit. Every change has been implemented in the primary codebase, verified against authentic raw measurement archives (Zenodo records 8224890 and 14073311), and confirmed through automated unit tests.

---

## 2. Detailed Root Cause Analysis & Solutions

### Issue 1: Throughput `NaN` vs Genuine Physical Zero
* **Prior Problem:** In `extract_sessions_8224890()`, `mean_dl_kbps` values that were missing or NaN could be coerced to `0.0`, conflating network dropouts / radio stalls with unrecorded telemetry.
* **Correction:** 
  - Preserved `np.nan` when `mean_dl_kbps` is missing: `mean_dl_mbps = (mean_dl_kbps / 1000.0) if pd.notna(mean_dl_kbps) else np.nan`.
  - In `build_forecast_instances()`, filtered out missing targets using `pd.notna(fdf['target_y'])`, while preserving physical zero-throughput measurements ($y=0.0$).
  - Audit confirmed: Zenodo 8224890 contains exactly 2 physical zero-throughput sessions (speedtest stalls); Zenodo 14073311 contains 23 physical zero-throughput segments. Neither dataset contains unrecorded `NaN` targets.

### Issue 2: Timestamp Parsing, Monotonicity, and Causal Freshness
* **Prior Problem:** In `load_14073311_ookla()`, missing timestamps were assigned an arbitrary `0.5s` default, and lag age could theoretically permit negative values under unhandled clock drift.
* **Correction:**
  - In `src/data/loader.py`, `lag_age_s` is calculated strictly when both `t_start` of the target session and `t_end` of the preceding session are valid non-null datetime timestamps:
    $$\Delta t = (t_{\text{start}} - t_{\text{prev, end}}).\text{total\_seconds}()$$
  - If either timestamp is null or invalid, `lag_age_s` is assigned `np.nan`.
  - Enforced a strict boolean filter:
    `pd.notna(lag_age_s) & (lag_age_s >= 0.0) & (lag_age_s <= float(window_seconds)) & pd.notna(target_y)`
  - Confirmed: Min lag age = 0.000s, Max lag age = 2.500s across all 1,001 causal instances. Zero negative lag ages, zero freshness violations ($>60$s).

### Issue 3: Session Segmentation and Ordering
* **Prior Problem:** In 14073311 Ookla Speedtest processing, test resets were grouped by `test_id` without strict verification of session chronology.
* **Correction:**
  - Segments are sorted chronologically by `t_start` prior to computing lag ages and prefixes.
  - Excluded warm-up sessions (sessions with no valid preceding test within the same campaign) from the active forecast set.
  - Gross sessions extracted: 1,132 (548 in 8224890, 584 in 14073311). Warm-up sessions excluded: 131. Usable causal instances: **1,001** (503 in 8224890, 498 in 14073311).

### Issue 4: E0 Split Detection Fragility
* **Prior Problem:** `create_experiment_splits()` determined whether an experiment was within-domain via object identity `source_df is target_df`. Calling `create_experiment_splits(src_df, src_df.copy())` silently fell back to transfer splitting (60/20/20 and 40/60) rather than the 5-way within-domain partition (35/10/15/15/25).
* **Correction:**
  - Updated `create_experiment_splits` signature to accept explicit `experiment_type: Optional[str] = None` and `regime: Optional[str] = None`.
  - Added robust content comparison fallback: if `session_id` and `date` columns are present, matches identical session sets and dates even if dataframes are distinct memory copies.
  - Eliminated mutable default argument `budgets: List[int] = [0, 1, 2, 5, 8, 9, 10, 15]` by defaulting to `None` and initializing inside the function.

### Issue 5: Discrete Day Support in E0 Within-Domain
* **Prior Problem:** E0 within-domain partitions assume continuous fractions (35%, 10%, 15%, 15%, 25%), but Operator 1 (2020–2021) spans only 7 distinct calendar dates.
* **Correction:**
  - `partition_by_chronological_days()` uses integer day boundaries that ensure all 5 blocks remain non-empty:
    - Train: Days 1–2 (57 instances, 38.0%)
    - Validation: Day 3 (9 instances, 6.0%)
    - Source Calibration: Day 4 (33 instances, 22.0%)
    - Target Calibration Pool: Day 5 (10 instances, 6.7%)
    - Target Test Suffix: Days 6–7 (41 instances, 27.3%)
  - Total: 150 instances across 7 dates.
  - Pairwise disjointness verified across all partitions ($S_i \cap S_j = \emptyset$ and $D_i \cap D_j = \emptyset$).
  - Day-cluster bootstrap on the test suffix ($N_{\text{clusters}}=2$) is explicitly labeled as **exploratory** due to asymptotic few-cluster bounds.

### Issue 6: Target Calibration Budget Integrity ($K=15$)
* **Prior Problem:** If a calibration pool contains fewer than $K$ sessions, code could silently truncate or reuse sessions.
* **Correction:**
  - In `create_experiment_splits()`, if `calib_pool_sorted['session_id'].nunique() < k`, `target_prefix_sessions[k]` is set strictly to `None`.
  - In `runner.py`, when `prefix_df is None`, the budget is reported as unavailable (`-`) without substituting smaller prefixes.
  - E0 calibration pool has 10 sessions; budget $K=15$ is reported as unavailable (`-`).

---

## 3. Code Modifications Summary

1. **`src/data/loader.py`:**
   - Preserved `NaN` in `mean_dl_mbps` extraction.
   - Enforced non-null, non-negative, and $\le 60$s freshness mask.
   - Removed artificial 0.5s default on missing timestamps in 14073311.
2. **`src/data/splits.py`:**
   - Replaced mutable default argument for `budgets`.
   - Added `experiment_type` argument and robust session-set content fallback.
   - Set unsupported budgets $K$ strictly to `None`.
   - Added `generate_split_summary()` diagnostic function.
3. **`src/experiments/runner.py`:**
   - Added `DIAGNOSTICS_DIR` (`results/diagnostics/`).
   - Integrated `generate_split_summary()` to output `split_summary.json`.
4. **`scripts/generate_data_quality_report.py`:**
   - Created standalone script that parses both raw archives and generates `docs/DATA_QUALITY_REPORT.md`.
5. **`docs/DATA_QUALITY_REPORT.md`:**
   - Created comprehensive data quality report documenting 867,710 raw rows, 1,132 gross sessions, 1,001 causal instances, and 0 freshness/acausal errors.

---

## 4. Verification & Test Results

All split protocol, causality, and mathematical unit tests pass without error:
- `tests/test_splits.py`: 5 passed in 15.30s
  - `test_split_independence_and_disjointness`: PASS
  - `test_e0_within_domain_split_disjointness`: PASS
  - `test_synthetic_e0_partitions_are_disjoint_and_budgets_are_explicit`: PASS
  - `test_transfer_domains_with_reused_local_session_ids_are_not_misclassified_as_e0`: PASS
  - `test_explicit_regime_and_within_domain_parameter`: PASS

Phase 1 is complete and ready for Phase 2 (Decoupled Testing & CI).

