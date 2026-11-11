# Data Quality Report and Phase 3 Suitability Decision

**Project:** Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry  
**Auditor:** Research Engineering Lead  
**Audit Date:** 10 November 2026  
**Final Status:** Phase 3 PASSED (All 10 Gates Satisfied)

---

## 1. Data Quality and Integrity Audit

### 1.1 Transport and Byte-Level Integrity
- All raw datasets were downloaded from Zenodo and verified against official publisher metadata:
  - `Throughput Tests - Speedtest - Active Measurements.csv` (8224890): Verified MD5 `4c6d46d645df9fbd7b050e4464040b5f`, SHA-256 `97de559315f6ec872ef87f4165587251f30e42bd5c7a3d67df1042919d6dbd3f` (94,963,907 bytes).
  - `description.pdf` (8224890): Verified MD5 `cb10809b854ecfd3f97a74d91c42e163`, SHA-256 `8b298651cf9ebc78cee331367ac42bbb5ca439789f82d0465e39a46c3ce6d2d1` (82,632 bytes).
  - `Active Performance Dataset - 1.zip` (14073311): Verified MD5 `59684dec4e26bd882cf6e6551cce50ad`, SHA-256 `f8bc2a621268775d0cf983524f062d1ffbddd365af1166c6b93e76991c881155` (82,284,534 bytes).
- Both licenses confirmed as `cc-by-4.0` in the Zenodo API responses and recorded in `data/metadata/acquisition_manifest.json`.

### 1.2 Extraction and Path Sanitization
- `Active Performance Dataset - 1.zip` was extracted to `data/extracted/14073311/Active Performance Dataset - 1/`.
- Archive paths containing invalid Windows characters (colons `:` and trailing directory spaces) were sanitized safely while preserving file uniqueness and verifying that no path traversal (`..`) occurred.
- A complete member inventory of 258 extracted items was recorded in `data/metadata/archive_inventory_14073311.json`.

### 1.3 Duplicate and Monotonicity Checks
- Within each campaign in `8224890`, timestamps are strictly monotonically increasing.
- Consecutive sessions within a campaign have zero timestamp overlap.
- Campaigns are concatenated in the raw CSV; sorting within campaigns preserves pure forward-causal ordering.
- No synthetic duplicate rows were detected.

### 1.4 Schema and Unit Harmonization
- The 2021 dataset records throughput in **kb/s**.
- In the 2023 dataset, 23 files record throughput in **kb/s** and 20 files in **Mb/s**.
- All throughput values are converted to **Mbps** using standard decimal conversion ($1\text{ Mbps} = 1000\text{ kb/s}$).
- Missing radio values are represented by literal `?` and converted to `NaN` with explicit binary missingness indicator masks.

---

## 2. Evaluation of Phase 3 Pass/Fail Gates

Below is the formal audit against the 10 gates prespecified in Section 13 of `docs/research_proposal.md`:

| Gate | Criterion | Evidence / Finding | Verdict |
|---|---|---|:---:|
| **Gate 1** | Exact versions, hashes, licenses, and attribution preserved | Pinned MD5 and SHA-256 verified for all files; CC BY 4.0 confirmed via Zenodo API; manifest stored in `data/metadata/acquisition_manifest.json`. | **PASS** |
| **Gate 2** | Test start/end times, throughput units, and result availability timing established | Millisecond timestamps (`Date` + `Time`) verified; test durations ($57.7 \pm 11.9\text{ s}$) and units ($kb/s$ vs $Mb/s \to Mbps$) established; session end demarcated by DQA result. | **PASS** |
| **Gate 3** | Real sequential tests with prior outcomes and radio features available before prediction | 503 valid consecutive test pairs in 8224890 with lead times $< 1.20\text{ s}$ ($\le 60\text{ s}$ cutoff); prior throughput $y_{j-1}$ and pre-test radio telemetry are strictly available before $a_j$. | **PASS** |
| **Gate 4** | At least two scientifically meaningful source-to-target comparisons formable | Four explicit transfer regimes formed: E0 (within-domain reference), E1 (campaign transfer: Op1 2021 $\to$ Op1 2023), E2 (cross-operator: Op1 $\to$ Op2), E3 (joint shift: Op1 2021 $\to$ Op2 2023). | **PASS** |
| **Gate 5** | Original sessions/days identifiable with sufficient independent support | 16 distinct calendar days in 8224890; over 1,100 sessions across 45 campaigns and 43 traces; exceeds the 10-day minimum gate for clustered inference. | **PASS** |
| **Gate 6** | Meaningful native availability differences in core radio bundles across sessions | 63.4% LTE-only (Group 2) vs 36.6% dual LTE+NR (Group 3); distribution consistent across both operators ($N > 50$ per stratum), providing ample support for grouped calibration. | **PASS** |
| **Gate 7** | Legitimate joins and documented sentinels | Sentinels (`?`) mapped to missing values; causal radio telemetry extracted directly from active trace time window $[a_j - 60\text{s}, a_j]$; no unaligned passive scans joined. | **PASS** |
| **Gate 8** | Calibration prefixes and fixed test suffixes support budgets without overlap | Early 40% of target sessions allocated as calibration pool (for budgets $K \in \{0, 1, 2, 5, 10\}$); remaining 60% frozen as fixed test suffix for all methods. | **PASS** |
| **Gate 9** | Common task implemented without mixing incompatible applications or protocols | Both datasets evaluate the identical active application: multi-threaded downlink Speedtest throughput following ETSI / Ookla methodology. | **PASS** |
| **Gate 10** | Refreshed prior-art review leaves a defensible incremental contribution | Confirmed against 2024–2026 literature (BAMMO, Sirhan 2026, Zaffran 2023, Gibbs & Candès 2021); the joint evaluation of native missing telemetry, network transfer, and finite calibration budget is unaddressed in existing literature. | **PASS** |

---

## 3. Suitability Verdict

**DECISION: PROCEED TO PHASE 4 (IMPLEMENTATION)**

The acquired data completely satisfy all scientific, engineering, and integrity requirements. The dataset supports the formulated forward-causal forecasting task, exhibits natural radio telemetry missingness, contains distinct commercial operators and measurement campaigns over sufficient independent calendar days, and allows fair, leak-free evaluation of calibration budgets.

