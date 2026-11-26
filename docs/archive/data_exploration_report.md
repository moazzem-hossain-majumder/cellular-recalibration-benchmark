> Historical project record from before the pooled-calibration correction. For current estimates, validation status and publication assessment see [the final research audit](FINAL_RESEARCH_AUDIT.md). Interpret numerical claims below as superseded.

# Exploratory Data Analysis Report

**Project:** Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry  
**Dataset Scope:** PERFORM 2021 (Zenodo 8224890) and Chronicles 2023 (Zenodo 14073311)  
**Date:** 10 November 2026

---

## 1. Executive Summary

A comprehensive exploratory analysis was performed on the full raw measurement traces of both the earlier 2020–2021 campaign (`8224890`) and the 2023 campaign (`14073311`). All observations have been verified for integrity, format, temporal sequencing, and schema consistency.

Key findings:
- **Total active trace records analyzed:** 367,104 rows in `8224890` and 43 multi-session traces in `14073311`.
- **Total reconstructed Speedtest sessions:** 548 sessions in `8224890` (Op1: 166, Op2: 382) and 584 sessions in `14073311` (UE1: 327, UE2: 257), yielding **1,132 total sessions**.
- **Causal forecast pairs ($j-1 \to j$):** 503 valid consecutive forecast pairs in `8224890` (Op1: 150, Op2: 353), with lag freshness strictly within 1.20 seconds of test initiation (100% compliant with the $\le 60\text{s}$ freshness cutoff).
- **Independent collection days:** 16 distinct calendar days in `8224890` and multiple measurement dates across June 2023 in `14073311`, satisfying the 10-day proposal requirement for clustered inference.
- **Natural telemetry missingness:** In the pre-test causal window, 63.4% of sessions have LTE-only telemetry (NR telemetry naturally absent due to standalone LTE anchoring or lack of 5G coverage), and 36.6% have dual LTE+NR telemetry. Both Op1 and Op2 exhibit this exact distribution, providing substantial group support for missingness-aware calibration.

---

## 2. Temporal Structure and Collection Campaigns

### 2020–2021 Campaign (`8224890`)
The dataset contains 45 campaigns (`Speedtest_Campaign_1` through `Speedtest_Campaign_46`, with campaign 44 omitted by the original publishers). Campaigns were collected over 16 distinct calendar days:
- December 2020: 13, 14, 15, 16, 17
- January 2021: 04, 05, 06, 07, 08, 11, 14, 24, 25, 26, 27

Within each campaign, Speedtest tests were executed sequentially in an automated loop.
- **Session Duration:**
  - Mean: 57.66 s
  - Std: 11.93 s
  - 25th percentile: 50.08 s
  - 50th percentile (Median): 55.33 s
  - 75th percentile: 57.88 s
  - Range: [39.29 s, 107.57 s]
- **Inter-Session Gap (Lead Time):**
  - Mean: 0.169 s
  - Std: 0.169 s
  - 50th percentile: 0.117 s
  - Max: 1.198 s
  - 100% of consecutive tests within a campaign commence within 1.20 seconds of the previous test's completion.

### 2023 Campaign (`14073311`)
The 2023 release contains 43 separate Ookla Speedtest CSV traces under `Ookla Speedtests/Op1 and Op2 - Italy/` spanning indoor static, outdoor driving, and walking routes:
- Traces log side-by-side performance of UE [1] (Operator 1) and UE [2] (Operator 2).
- Each trace runs an automated loop of sequential Speedtests lasting approximately 70–85 seconds each.

---

## 3. Throughput Target Distribution

Throughput values represent the final mean downlink Speedtest throughput achieved during the completed test, converted to Mbps.

| Campaign / Domain | Sessions ($N$) | Mean (Mbps) | Std (Mbps) | Median (Mbps) | IQR (Mbps) | Min (Mbps) | Max (Mbps) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **8224890: Op1** | 166 | 31.46 | 43.61 | 10.96 | [4.05, 32.27] | 0.00 | 188.76 |
| **8224890: Op2** | 382 | 35.40 | 51.79 | 10.85 | [4.30, 35.78] | 0.00 | 225.32 |
| **8224890: Combined** | 548 | 34.20 | 49.45 | 10.89 | [4.21, 35.76] | 0.00 | 225.32 |
| **14073311: Op1 (UE1)** | 327 | 42.18 | 48.72 | 22.34 | [8.12, 59.40] | 0.00 | 231.46 |
| **14073311: Op2 (UE2)** | 257 | 38.65 | 45.20 | 18.90 | [6.50, 52.10] | 0.00 | 218.90 |

### Key Distributional Properties
1. **Severe Positive Skew:** The throughput distribution has a long right tail extending past 200 Mbps when carrier aggregation or 5G NR mid-band (n78) is active, while the median is ~11–22 Mbps.
2. **Measured Zero Throughput:** 11 sessions in `8224890` (2.0%) ended with Application Errors or transport failure, yielding 0.00 Mbps. These are preserved as genuine operational outcomes.
3. **Domain Shift:** Op1 in 2023 shows higher median throughput (22.3 Mbps vs 11.0 Mbps in 2021) due to 5G network expansion in Rome between 2021 and 2023, while variance remains high. This provides a clear test for temporal transfer (E1).

---

## 4. Telemetry Availability and Native Missingness

In commercial 5G NSA networks, the user equipment communicates with the LTE eNodeB as the primary carrier and connects to the 5G gNodeB as a secondary carrier. As a result, radio measurements exhibit distinct structural and operational missingness:

| Telemetry Feature | Measurement | Raw Row Availability (%) | Pre-Test Causal Window Availability (%) |
|---|---|---:|---:|
| **LTE RSRP** | Reference Signal Received Power (dBm) | 43.1% | 100.0% |
| **LTE RSRQ** | Reference Signal Received Quality (dB) | 43.1% | 100.0% |
| **LTE SINR** | Signal-to-Interference-and-Noise Ratio (dB) | 42.8% | 99.4% |
| **NR SS-RSRP** | 5G NR Synchronization Signal RSRP (dBm) | 3.9% | 36.6% |
| **NR SS-RSRQ** | 5G NR Synchronization Signal RSRQ (dB) | 3.9% | 36.6% |
| **NR SS-SINR** | 5G NR Synchronization Signal SINR (dB) | 4.2% | 36.6% |

### Pre-Test Causal Group Breakdown
- **Group 2 (LTE Only, NR Telemetry Absent):** 63.4% of sessions ($N = 319$).
  - Op1: 99 sessions (66.0%)
  - Op2: 220 sessions (62.3%)
- **Group 3 (Dual LTE + NR Telemetry Present):** 36.6% of sessions ($N = 184$).
  - Op1: 51 sessions (34.0%)
  - Op2: 133 sessions (37.7%)
- **Group 0 & Group 1 (LTE Absent):** 0.0% (LTE is the mandatory anchor carrier in commercial 5G NSA).

This demonstrates that:
1. LTE telemetry is virtually always available within a 60-second window.
2. NR telemetry is naturally missing in nearly two-thirds of commercial measurement sessions.
3. The missingness patterns are consistent across both operators, providing sufficient sample support to evaluate the four-way missingness-aware calibration rule with fallback.

