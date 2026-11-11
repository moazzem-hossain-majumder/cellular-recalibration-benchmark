# Dataset Documentation

**Project:** Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry  
**Verification Date:** 10 November 2026  
**Status:** Phase 3 Audited and Verified

---

## 1. Provenance and Licensing

The research relies on two official commercial measurement releases from the PERFORM research consortium (University of Oslo, Karlstad University, Sapienza University of Rome, and Rohde & Schwarz):

### Earlier Campaign (2020–2021)
- **Title:** *A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements*
- **Persistent Identifier (DOI):** [10.5281/zenodo.8224890](https://doi.org/10.5281/zenodo.8224890)
- **Publication Reference:** K. Kousias et al., *A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements*, IEEE Communications Magazine, vol. 62, no. 5, pp. 44–49, May 2024. [DOI: 10.1109/MCOM.011.2200707](https://doi.org/10.1109/MCOM.011.2200707).
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **File Used:** `Throughput Tests - Speedtest - Active Measurements.csv` (94,963,907 bytes; MD5: `4c6d46d645df9fbd7b050e4464040b5f`; SHA-256: `97de559315f6ec872ef87f4165587251f30e42bd5c7a3d67df1042919d6dbd3f`).
- **Companion File:** `description.pdf` (82,632 bytes; MD5: `cb10809b854ecfd3f97a74d91c42e163`; SHA-256: `8b298651cf9ebc78cee331367ac42bbb5ca439789f82d0465e39a46c3ce6d2d1`).

### Later Campaign (2023)
- **Title:** *The Chronicles of 5G Non-Standalone: Active Performance Dataset*
- **Persistent Identifier (DOI):** [10.5281/zenodo.14073311](https://doi.org/10.5281/zenodo.14073311)
- **Publication Reference:** G. Caso et al., *The Chronicles of 5G Non-Standalone: An Empirical Analysis of Performance and Service Evolution*, IEEE Open Journal of the Communications Society (OJ-COMS), 2024.
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **File Used:** `Active Performance Dataset - 1.zip` (82,284,534 bytes; MD5: `59684dec4e26bd882cf6e6551cce50ad`; SHA-256: `f8bc2a621268775d0cf983524f062d1ffbddd365af1166c6b93e76991c881155`).
- **Archive Contents:** 43 Ookla Speedtest CSV traces under `Ookla Speedtests/Op1 and Op2 - Italy/` logging side-by-side commercial measurements across Indoor Static (IS), Outdoor Driving (OD), and Outdoor Walking (OW) scenarios.

---

## 2. Measurement Architecture and Logging Protocol

Measurements were collected using commercial 5G-capable smartphones running ETSI-compliant measurement software (Rohde & Schwarz QualiPoc / DQA software) connected to operational cellular networks in Rome, Italy.

### Operators and Cellular Infrastructure
- **Op1:** Major Italian mobile network operator providing commercial 4G LTE and 5G Non-Standalone (NSA) connectivity.
- **Op2:** Competing major Italian mobile network operator providing commercial 4G LTE and 5G NSA connectivity.
- **Architecture:** 3GPP Option 3X (EN-DC: E-UTRA-NR Dual Connectivity). The user equipment (UE) maintains an LTE anchor carrier for the Master Cell Group (MCG) and adds an NR carrier for the Secondary Cell Group (SCG) when 5G signal quality permits.

### Temporal Structure of a Speedtest Session
1. **Preamble and Latency Phase:** The UE establishes connection to the measurement server and measures Round Trip Time (RTT).
2. **Downlink Phase:** Multi-threaded HTTP/TCP payload download for approximately 15–20 seconds. Intermediate instantaneous and running mean throughput are logged at subsecond intervals (`Current Netw. DL` and `Mean Netw. DL`).
3. **Uplink Phase:** Multi-threaded HTTP/TCP payload upload for approximately 15–20 seconds.
4. **Session Conclusion Event:** The Data Quality Analyser (DQA) logs a session conclusion event (`DQA Result: Good Session`, `Application Error`, `Blocked Session`, or `Dropped Session`). The achieved mean downlink throughput of the test is frozen as the session result.
5. **Session Duration:** Average test duration is $57.7 \pm 11.9$ seconds (range: 39.3s to 107.6s).
6. **Inter-test Gap:** Tests are executed sequentially within automated campaigns. The elapsed time between the conclusion of test $j-1$ and the start of test $j$ has a mean of 0.17 seconds (range: 0.0s to 1.2s), providing an immediate causal link.

---

## 3. Schema Harmonization and Unit Standards

### Units
- In the raw 8224890 file, Speedtest throughput is recorded in **kb/s**.
- In the 14073311 release, 23 files record throughput in **kb/s** (`[kBit/s]`) and 20 files record throughput in **Mb/s** (`[MBit/s]`).
- **Standardized Target Unit:** Megabits per second (**Mbps**), where:
  $$\text{Throughput (Mbps)} = \begin{cases} \text{Value (kb/s)} / 1000.0 & \text{if unit is kb/s} \\ \text{Value (Mb/s)} & \text{if unit is Mb/s} \end{cases}$$
- Physical-layer transport throughput (`5G PDSCH Throughput`, `LTE PDSCH Throughput`) is explicitly distinguished from end-to-end application Speedtest throughput and is not substituted for the application target.

### Sentinels and Missingness Semantics
- **Literal `?`:** Indicates unrecorded or unmeasured values in the ETSI logging output. For radio telemetry, this represents natural telemetry missingness (e.g., NR carrier unsynchronized, scanner measurement cycle skipped, or device in LTE-only mode).
- **Distinction between Zero and Missing:**
  - Measured throughput $y = 0$ is a valid operational observation (e.g., stall, application error, or transport blockage) and is retained in evaluation.
  - Missing throughput labels are not imputed as zero; test instances lacking a valid target label are excluded from confirmatory evaluation.
  - Telemetry features missing in the pre-test causal window are preserved as missing with explicit binary indicator masks ($m_i \in \{0, 1\}$).

---

## 4. Causal Feature Availability (Information Budget)

For each test $j$ starting at timestamp $a_j$:
1. **Target:** $y_j$, the final achieved mean downlink Speedtest throughput of test $j$ in Mbps.
2. **Prior Throughput Lags:**
   - $y_{j-1}$: Achieved throughput of the preceding completed test in the same campaign (Mbps).
   - $\Delta t_{j-1} = a_j - b_{j-1}$: Elapsed time between completion of test $j-1$ and start of test $j$ (seconds).
   - $d_{j-1} = b_{j-1} - a_{j-1}$: Realized duration of the preceding completed test (seconds).
3. **Causal Radio Telemetry (extracted from the $[a_j - 60\text{s}, a_j]$ window):**
   - LTE RSRP (dBm), LTE RSRQ (dB), LTE SINR (dB).
   - NR SS-RSRP (dBm), NR SS-RSRQ (dB), NR SS-SINR (dB).
   - Radio Availability Indicators: $m_{\text{LTE}} = \mathbf{1}(\text{LTE telemetry observed})$, $m_{\text{NR}} = \mathbf{1}(\text{NR telemetry observed})$.
   - Radio Technology State: Serving Cell PCI change indicator, RAT Info (`LTE` vs `5G EN-DC`).
   - Context: Scenario (`IS`, `OD`, `OW`).
4. **Strict Causal Rule:** No same-test observations, post-start measurements, or future information are permitted in the predictor.

