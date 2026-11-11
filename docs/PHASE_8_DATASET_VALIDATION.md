# Dataset Provenance, Measurement Semantics, and Quality Audit (Phase 8)

**Project:** Cellular Recalibration Benchmark  
**Manuscript Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Audit Artifact:** `results/diagnostics/data_quality_audit.json`  
**Evaluation Standard:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  

---

## 1. Dataset Provenance and Specifications

The empirical evaluation of this benchmark is founded upon two independent, publicly available commercial cellular drive-test measurement campaigns collected in Rome, Italy.

### 1.1 Dataset 1: Earlier Campaign (Zenodo Record 8224890)
- **DOI / Record:** `10.5281/zenodo.8224890`
- **Primary Source / Reference:**  
  *G. Mattera et al., "5G and 4G Active and Passive Measurements in Rome," Zenodo, Aug. 2023.*  
  Accompanying paper: *G. Mattera, V. Sciancalepore, et al., "A Multi-Dataset Field Study on 5G NSA and 4G Performance in Urban Cellular Deployments," IEEE Communications Magazine, 2022/2023.*
- **Collection Period:** December 13, 2020 – January 27, 2021 (winter campaign).
- **Geographic Coverage:** Metropolitan Rome, Italy (urban drive tests covering radial arteries, commercial corridors, and peripheral ring routes).
- **Network Operators:**
  - **Operator 1 (Op1):** Telecom Italia Mobile (TIM, Italy), Mobile Country Code (MCC) 222, Mobile Network Code (MNC) 01.
  - **Operator 2 (Op2):** Vodafone Italy, MCC 222, MNC 10.
- **Network Architecture:** 3GPP Release 15 Non-Standalone (NSA) Option 3X EN-DC (E-UTRA - NR Dual Connectivity).
  - Primary Anchor: LTE Band 3 (1800 MHz) and Band 20 (800 MHz).
  - Secondary Cell: 5G NR Band n78 (3.5 GHz Time Division Duplex).
- **Measurement Equipment:** Commercial off-the-shelf 5G smartphones (Qualcomm Snapdragon X55 chipset) mounted on drive-test test benches with synchronized professional diagnostic logging (QualiPoc / Rohde & Schwarz / Accuver software).
- **Application Test:** Periodic Ookla Speedtest execution executing automated downlink TCP connections against regional CDN endpoints.
- **Dataset Scale:** 548 raw speedtest sessions. Under the causal 60-second freshness gate, **503 valid causal forecast instances** across **16 calendar dates** (150 Op1, 353 Op2).

### 1.2 Dataset 2: Recent Campaign (Zenodo Record 14073311, "5G Chronicles 2023")
- **DOI / Record:** `10.5281/zenodo.14073311`
- **Primary Source / Reference:**  
  *V. Sciancalepore et al., "5G Chronicles: A Multi-Operator Drive- and Walk-Test Cellular Measurement Campaign," Zenodo, Nov. 2024.*
- **Collection Period:** March 29, 2023 – July 5, 2023 (spring/summer campaign).
- **Geographic Coverage:** Rome, Italy, across three operational mobility scenarios:
  - **Indoor Stationary (IS):** Fixed indoor locations within public transit hubs and commercial buildings.
  - **Outdoor Stationary (OD):** Fixed outdoor urban plazas and roadside locations.
  - **Outdoor Walking (OW):** Pedestrian walk tests with handheld user equipment.
- **Network Operators:** Operator 1 (TIM) and Operator 2 (Vodafone).
- **Network Architecture:** Advanced 3GPP Release 16 NSA Option 3X EN-DC.
- **Measurement Equipment:** Dual commercial 5G smartphones (UE1: Op1, UE2: Op2) logged via high-frequency drive-test diagnostic suite recording network throughput, PHY/MAC statistics, and RF channel quality at 2 Hz sampling frequency (every 500 ms).
- **Application Test:** Systematic Ookla Speedtest traces (`Active Performance Dataset - 1/Ookla Speedtests/Op1 and Op2 - Italy/`).
- **Dataset Scale:** 43 drive/walk test CSV files. Under causal filtering, **498 valid causal forecast instances** across **12 calendar dates** (284 Op1, 214 Op2).

### 1.3 Total Experimental Sample
- **Total Valid Causal Forecast Sessions:** **1,001 sessions** (503 from 2021 + 498 from 2023).
- **Total Independent Calendar Days:** **27 distinct collection dates** (16 in 2021 + 12 in 2023, with 1 overlap in month-day format).
- **Geographic Domain:** 100% Metropolitan Rome, Italy. *(No real-world data from Bangladesh is present in the dataset).*

---

## 2. Measurement Semantics and Feature Harmonization

A major pitfall in multi-dataset telecommunications research is assuming that columns with similar names share identical measurement semantics.

| Parameter | Zenodo 8224890 (2020–2021) | Zenodo 14073311 (2023) | Harmonized Representation in Benchmark |
|---|---|---|---|
| **Timestamp** | `Date` (DD.MM.YYYY) + `Time` (HH:MM:SS.sss) | `Day` (YYYY-MM-DD or DD.MM.YYYY) + `Timestamp [dd.mm.yyyy,hh:mm:ss.ss]` | Converted to absolute UTC-equivalent `pd.Timestamp` |
| **Throughput (Target $y$)** | `Mean Netw. DL` (kBit/s) at completion mark (`DQA Result != '?'`) | `QoS Tester_Net Throughput_Mean Netw. DL [kBit/s]` evaluated at session completion | Converted to Mbps: $y = \frac{\text{kBit/s}}{1000.0}$ |
| **LTE PCell RSRP** | `RSRP` (dBm) | `LTE UE_PCell_RSRP, RSRP[MCG-PCell] [dBm]` | Continuous float, mean over pre-test 60s causal window |
| **LTE PCell RSRQ** | `RSRQ` (dB) | `LTE UE_PCell_RSRQ, RSRQ[MCG-PCell] [dB]` | Continuous float, mean over pre-test 60s causal window |
| **LTE PCell SINR** | `SINR` (dB) | `LTE UE_PCell_SINR, SINR[MCG-PCell] [dB]` | Continuous float, mean over pre-test 60s causal window |
| **5G NR SS-RSRP** | `SS-RSRP` (dBm) | `5G NR UE_5G NR Carriers_SS-RSRP, SS-RSRP[SCG-PCell] [dBm]` | Continuous float or `NaN` when 5G unattached |
| **5G NR SS-RSRQ** | `SS-RSRQ` (dB) | `5G NR UE_5G NR Carriers_SS-RSRQ, SS-RSRQ[SCG-PCell] [dB]` | Continuous float or `NaN` when 5G unattached |
| **5G NR SS-SINR** | `SS-SINR` (dB) | `5G NR UE_5G NR Carriers_SS-SINR, SS-SINR[SCG-PCell] [dB]` | Continuous float or `NaN` when 5G unattached |
| **Telemetry Missingness Group** | Derived from LTE / NR availability in lookback window | Derived from LTE / NR availability in lookback window | `group_id \in {2: \text{LTE only}, 3: \text{Dual LTE+NR}}` |

---

## 3. Physical Telemetry Missingness vs. Target Absence

### 3.1 Structural 5G NR Missingness
In 3GPP Option 3X Non-Standalone deployments, the user equipment maintains a persistent RRC connection to the 4G LTE Primary Cell (PCell) for control signaling, while the 5G NR Secondary Cell (SCG) is added dynamically through Secondary Node Addition procedures. During idle states or low-buffer periods, the network releases the NR carrier to conserve battery and spectrum resources.

As verified in `results/diagnostics/data_quality_audit.json`:
- **In 2020–2021 Campaign (8224890):**
  - **Group 2 (LTE PCell only, 5G NR unobserved):** **319 sessions (63.4%)**
  - **Group 3 (Dual LTE+NR observed):** **184 sessions (36.6%)**
  - *Finding:* Secondary 5G NR telemetry is structurally missing in exactly **63.4%** of sessions.
- **In 2023 Campaign (14073311):**
  - **Group 2 (LTE PCell only, 5G NR unobserved):** **266 sessions (53.4%)**
  - **Group 3 (Dual LTE+NR observed):** **232 sessions (46.6%)**
  - *Finding:* 5G NR availability increased to 46.6% in 2023 due to denser commercial mid-band gNodeB rollouts, but structural missingness remains high (53.4%).

### 3.2 Preservation of Missingness Semantics
1. **No Artificial Zeroes for Radio Metrics:** Unobserved RSRP/SINR values are strictly preserved as IEEE `NaN` or unobserved indicator flags (`has_nr = 0`). Imputing missing SS-RSRP as $0.0\text{ dBm}$ would represent an impossibly high signal power ($1\text{ mW}$), causing severe model distortion. Imputing $-140\text{ dBm}$ falsely treats an inactive secondary carrier as an active link with terrible coverage.
2. **Distinguishing Real Zeroes from Missing Targets:** In cellular operations, radio link failures or transport stalling can cause real zero throughput ($y = 0.0\text{ Mbps}$). The benchmark strictly distinguishes between:
   - Genuine zero throughput observations ($y = 0.0$, 2 instances in 2021, 23 instances in 2023), which are retained as valid target labels.
   - Missing/unrecorded throughput instances (`NaN` or `'?'`), which are excluded from supervised evaluation via `filter_causal_forecast_instances()`.

---

## 4. Empirical Data Quality and Distribution Audit

Summary statistics extracted from `results/diagnostics/data_quality_audit.json`:

| Statistic | Zenodo 8224890 (2020–2021) | Zenodo 14073311 (2023) | Combined Benchmark |
|---|---|---|---|
| **Total Causal Sessions** | 503 | 498 | **1,001** |
| **Mean Throughput ($y$)** | 32.58 Mbps | 35.03 Mbps | 33.80 Mbps |
| **Std Dev Throughput** | 48.93 Mbps | 45.43 Mbps | 47.23 Mbps |
| **Minimum Throughput** | 0.000 Mbps | 0.000 Mbps | 0.000 Mbps |
| **10th Percentile ($p_{10}$)** | 0.16 Mbps | 4.77 Mbps | 1.18 Mbps |
| **25th Percentile ($p_{25}$)** | 4.03 Mbps | 7.30 Mbps | 5.06 Mbps |
| **Median Throughput** | 10.27 Mbps | 16.14 Mbps | 13.01 Mbps |
| **75th Percentile ($p_{75}$)** | 31.23 Mbps | 39.35 Mbps | 34.99 Mbps |
| **90th Percentile ($p_{90}$)** | 113.69 Mbps | 107.87 Mbps | 110.02 Mbps |
| **Maximum Throughput** | 225.32 Mbps | 266.41 Mbps | 266.41 Mbps |
| **Zero Throughput Instances** | 2 (0.4%) | 23 (4.6%) | 25 (2.5%) |
| **Sub-1 Mbps Instances** | 63 (12.5%) | 35 (7.0%) | 98 (9.8%) |
| **Mean Lag Freshness ($\Delta t$)** | 0.17 seconds | 0.71 seconds | 0.44 seconds |
| **Max Lag Freshness ($\Delta t$)** | 1.20 seconds | 2.50 seconds | 2.50 seconds |
| **Unique Collection Dates** | 16 dates | 12 dates | 27 unique dates |

### Key Scientific Observations:
1. **Distribution Alignment:** Both campaigns exhibit remarkably similar right-skewed throughput distributions typical of mobile broadband networks, with means within 7% of each other (32.6 vs. 35.0 Mbps) and comparable maxima (225.3 vs. 266.4 Mbps).
2. **Zero-Throughput Outlier in 2023:** In the 2023 campaign, 23 sessions recorded true zero throughput due to transient connection drops in indoor walk-test environments. One such zero in the target calibration prefix of E3 triggers a severe conservative penalty in empirical target calibration, which is solved by Bayes-corrected Covariate-Shift Conformal Prediction (CS-CP).
3. **Causal Freshness:** In all 1,001 instances, the preceding test lag age $\Delta t$ is well within the 60-second operational window (mean 0.44s, max 2.50s), confirming excellent temporal proximity without stale memory or acausal lookahead.

