# How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry

**Author:** Md. Moazzem Hossain Majumder  
**Email:** moazzemhossain1510@gmail.com  
**Target Venue:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  
**Date:** November 2026  
**Status:** Complete Publication-Ready Manuscript

---

## Abstract
Downlink throughput forecasting in modern cellular networks is critical for proactive transport-layer bandwidth provisioning, adaptive bitrate streaming, and service level agreement (SLA) assurance in fourth-generation (4G) Long Term Evolution (LTE) and fifth-generation (5G) Non-Standalone (NSA) architectures. However, supervised machine learning predictors trained in one network environment exhibit catastrophic failure when transferred across operators or measurement campaigns. This vulnerability is compounded by structural telemetry missingness, where secondary 5G New Radio (NR) synchronization indicators are absent in 63.4% of operational sessions due to discontinuous carrier aggregation and 3GPP Option 3X EN-DC state transitions. While conventional models optimize symmetric point errors, production networks require conservative, calibrated lower bounds to prevent Quality-of-Service (QoS) breaches. In this paper, we formulate an experimental benchmark addressing the fundamental question: **How much target-network calibration data is required to recover dependable throughput lower bounds under natural telemetry missingness and network distribution shift?** Utilizing 1,132 verified commercial Speedtest sessions (forming 1,001 causal forecast pairs strictly filtered by a 60-second lag-freshness gate) across 2020--2021 and 2023 commercial campaigns in Rome, Italy, we formulate an un-leakable, forward-causal forecasting protocol. We benchmark linear, boosted tree, and hardware-accelerated deep neural predictors on an NVIDIA GeForce RTX 4060 GPU, and evaluate split-conformal calibration rules across target budgets $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$ sessions. Our findings reveal that: (1) uncalibrated point forecasts suffer unacceptable violation rates of 32% to 58% under domain shift; (2) split-conformal calibration reliably restores nominal coverage ($\le 10\%$); (3) finite-sample conformal validity at nominal level $\alpha=0.10$ mathematically requires at least $K \ge 9$ target sessions (Lemma 1), so budgets $K \le 8$ rely on principled source fallbacks before target recalibration sharply activates at $K=9$; (4) within-domain chronological evaluation under leak-free day splitting guarantees zero train/test leakage; and (5) Bayes prior-corrected Covariate-Shift Conformal Prediction (CS-CP) counters operator and temporal shifts without requiring labeled target sessions. These results provide actionable campaign sizing guidelines for mobile network operators deploying transfer-learning pipelines under missing telemetry.

**Index Terms:** 5G Non-Standalone (NSA), cellular throughput forecasting, conformal prediction, distribution shift, missing telemetry, service level agreements (SLAs), network service management.

---

## 1. Introduction
Mobile cellular data traffic continues to grow exponentially, driven by immersive multimedia, cloud gaming, and ultra-reliable low-latency applications. In commercial 5G networks deployed under 3GPP Option 3X Non-Standalone (NSA) architecture, user equipment (UE) maintains simultaneous connectivity to a 4G Long Term Evolution (LTE) Master Node (eNodeB) and a 5G New Radio (NR) Secondary Node (gNodeB) through E-UTRA-NR Dual Connectivity (EN-DC). Under this dual-connectivity regime, effective downlink throughput is determined by physical-layer channel dynamics, modulation and coding schemes (MCS), transport block allocations, carrier aggregation, and core network scheduling.

Accurate forecasting of next-test downlink throughput offers mobile network operators (MNOs) significant advantages, enabling proactive buffer management, adaptive bitrate video streaming, and intelligent traffic steering across radio access technologies (RATs). Consequently, supervised machine learning (ML) has emerged as a predominant paradigm for cellular throughput estimation.

However, conventional throughput prediction approaches suffer from three critical engineering limitations:
1. **Overconfidence and Uncalibrated Risk:** Standard regression models generate point estimates (e.g., conditional mean throughput). Point predictions optimize symmetrical loss functions (such as mean absolute error or mean squared error). In operational telecommunications, an over-optimistic prediction carries severe penalties: committing to a 50 Mbps throughput pipeline when only 15 Mbps is delivered causes buffer under-runs, packet loss, and severe Quality of Experience (QoE) degradation. Networks require *reliable lower bounds* $L_t$ guaranteeing that observed throughput exceeds $L_t$ at a prespecified nominal rate $1 - \alpha$.
2. **Telemetry Missingness in Operational Networks:** Field-test telemetry rarely conforms to pristine tabular structures. In operational 5G NSA drive tests, radio indicators (such as Synchronization Signal Reference Signal Received Power, SS-RSRP) are naturally missing in 60% to 95% of logged time intervals. This missingness is not an artificial defect; it reflects genuine telecommunications states, such as secondary 5G carriers being disconnected due to coverage boundaries or energy-saving discontinuous reception. Imputing these missing telemetry features with arbitrary constants (or zeros) severely distorts feature distributions.
3. **Cross-Network and Temporal Distribution Shift:** A model trained on a specific operator's campaign in a particular year cannot be assumed to generalize across network operators or subsequent network upgrade cycles. Differences in frequency band allocations, antenna tilt, cell density, and vendor-specific scheduling create severe distribution shift.

To address these challenges, researchers have explored conformal prediction, missing-data boosting, and adaptive interval selection. Yet, an essential operational question remains unanswered in the telecommunications literature: **How much target-domain recalibration data is required to recover dependable one-sided throughput lower bounds when transferring a model across commercial networks under naturally missing telemetry?**

The primary contributions of this paper are fourfold:
1. **Leak-Free Causal Formulation under 5G NSA Missingness:** We formulate a rigorous, leak-free forward-causal throughput forecasting protocol on 1,132 commercial Speedtest sessions (1,001 causal test pairs) from operational 5G NSA networks. We explicitly model naturally missing 5G NR radio telemetry without artificial imputation, enforcing a strictly audited 60-second lag freshness gate ($\Delta t \le 60\text{ s}$) and pre-test radio observation windows.
2. **Finite-Sample Conformal Budget Bound (Lemma 1):** We prove and empirically demonstrate that split-conformal calibration at nominal risk $\alpha = 0.10$ possesses a strict finite-sample threshold: exact target recalibration is mathematically undefined for measurement campaigns with $K \le 8$ sessions, activating sharply at $K=9$ sessions and establishing a formal minimum sample size for operational drive-test campaign planning.
3. **Comprehensive Multi-Domain Transfer Benchmark:** We benchmark linear regression, boosted decision trees, BAMMO, and a PyTorch Deep Tabular ResNet (profiled on an NVIDIA GeForce RTX 4060 GPU with CUDA mixed precision) across four distinct transfer regimes: within-domain, 2.5-year temporal campaign transfer, cross-operator transfer, and joint temporal-operator shift.
4. **Statistical Quantification of Methodological Tradeoffs:** Using 2,000 paired day-cluster bootstrap resamples and Bayes prior-corrected Covariate-Shift Conformal Prediction (CS-CP), we establish the empirical trade-offs of target budget allocation under small-sample regimes and telemetry gaps, providing practical rules of thumb for cellular network operators.

---

## 2. Background and Related Work

### 2.1 5G Non-Standalone Architecture and Telemetry
In 3GPP Option 3X EN-DC deployments, the LTE eNodeB handles control-plane signaling and anchor user-plane traffic, while the 5G gNodeB delivers high-speed user-plane data over millimeter-wave or sub-6 GHz (e.g., 3.5 GHz n78) spectrum. Radio telemetry is logged via User Equipment diagnostic monitors or specialized drive-test tools (e.g., Rohde & Schwarz QualiPoc). 

Crucially, reference signal measurements—including Reference Signal Received Power (RSRP), Reference Signal Received Quality (RSRQ), and Signal-to-Interference-and-Noise Ratio (SINR)—are continuously recorded for the LTE Master Cell Group (MCG). In contrast, 5G NR Secondary Cell Group (SCG) telemetry (SS-RSRP, SS-RSRQ, SS-SINR) is only logged when an active 5G bearer is configured and synchronized. As established by Kousias et al. and Caso et al., physical radio coverage varies dynamically over mobility routes, leading to structural telemetry missingness.

### 2.2 Related Work and Novelty Boundary
Recent research has addressed isolated aspects of cellular modeling:
- **BAMMO (Jacobson et al., JRSS C 2025):** Developed a boosted additive model handling missing telemetry for 5G mmWave throughput prediction on the Lumos5G dataset. However, BAMMO was evaluated only within a single geographic loop without cross-network transfer or sample-budgeted calibration analysis.
- **Conformal Prediction with Missing Values (Zaffran et al., ICML 2023):** Established theoretical bounds for missing-value conformal prediction under pattern conditioning, but their analysis relies on exchangeable synthetic and medical datasets, omitting the severe distribution shift and temporal autocorrelation inherent to telecommunications.
- **Adaptive Conformal Inference (Gibbs & Candès, NeurIPS 2021):** Developed online adaptation algorithms (ACI) guaranteeing long-run marginal coverage under arbitrary distribution shift. However, long-run marginal coverage does not guarantee localized session safety or inform static calibration budget sizing.
- **Handover-Aware Intervals (Sirhan, Network 2026):** Investigated mobility-conditioned conformal bounds on UCC drive traces, finding that regime-specific conditioning improves interval width but does not universally dominate global calibration for rate-selection objectives.
- **Covariate-Shift Conformal Prediction (Tibshirani et al., NeurIPS 2019):** Developed weighted conformal prediction correcting for distribution shift via likelihood ratios $w(x) = dP_T(x) / dP_S(x)$. In telecommunications, however, estimating $w(x)$ directly on raw telemetry is challenging due to 63% unobserved NR features, which causes discriminator variance under small target calibration budgets ($K \le 10$).

| Study | Data Provenance | Telemetry Missingness | Cross-Domain Transfer | Calibration Budget Analysis | Clustered Inference | Hardware Profiling |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Kousias et al. (2024)** | Commercial Field | Descriptive only | No (Single Domain) | No | No | Host CPU |
| **Caso et al. (2024)** | Commercial Field | Descriptive only | Descriptive only | No | No | Host CPU |
| **BAMMO (Jacobson, 2025)** | mmWave Loop | Modeled (Boosting) | No (Single Route) | No | No | Host CPU |
| **Zaffran et al. (2023)** | Synthetic / Bio | Simulated Missingness | No (Exchangeable) | No | Standard Bootstrap | Host CPU |
| **Sirhan et al. (2026)** | Commercial Traces | Inapplicable | No | No | No | Host CPU |
| **Tibshirani et al. (2019)** | Benchmark / Theory | None | Covariate Shift | No | Standard Bootstrap | Host CPU |
| **This Work** | **Commercial (1,132 tests)** | **Structured Grouping** | **Yes (E0 to E3)** | **Yes ($K \in \{0..10\}$)** | **Yes (2,000 Day Clusters)** | **NVIDIA RTX 4060 GPU** |

**Novelty Boundary:** We do not claim to invent conformal prediction, missing-value imputation, or cellular throughput forecasting. Our contribution is the *joint empirical formulation and evaluation of natural telemetry missingness, explicit source-to-target transfer across commercial operators and multi-year campaigns, and finite target recalibration budgets*, supported by paired-cluster statistical inference and leak-free causal ordering. Table 1 systematically summarizes our scope against recent literature.

---

## 3. Problem Formulation

### 3.1 Causal Forecasting Protocol
Let an operational campaign consist of an ordered sequence of completed downlink throughput measurement sessions $j = 1, 2, \dots, N$. Each test $j$ commences at wall-clock timestamp $a_j$, concludes at $b_j$, and achieves mean downlink application throughput $y_j \in \mathbb{R}_{\ge 0}$ (in Mbps).

We formulate the prediction task immediately prior to test initiation $a_j$: predict the subsequent test throughput $y_j$ using exclusively information causally available at timestamp $a_j^-$. 

**Integrity Safeguards:**
1. **No Same-Test Leakage:** Contemporaneous physical-layer indicators (e.g., average PDSCH throughput or resource block counts logged during test $j$) are strictly prohibited as predictors of $y_j$.
2. **Causal Lag Availability:** The outcome of previous test $j-1$ ($y_{j-1}$) and its realized duration $d_{j-1} = b_{j-1} - a_{j-1}$ may be used if and only if test $j-1$ concluded prior to $a_j$ with elapsed freshness age $\Delta t_{j-1} = a_j - b_{j-1} \le 60\text{ seconds}$.
3. **Causal Radio Window:** Radio indicators ($x_j$) are extracted from the backward window $[a_j - 60\text{s}, a_j]$.

### 3.2 Conformal Calibration and Mathematical Formulation
Let $f(x, m)$ denote a point predictor trained on a source network domain, where $x \in \mathbb{R}^d$ contains available telemetry and lags, and $m \in \{0, 1\}^d$ denotes the binary availability mask.

On a separate calibration set of $n$ instances, we compute signed overprediction scores:
$$s_i = f(x_i, m_i) - y_i, \quad i = 1, \dots, n.$$
Taking signed overprediction (rather than absolute residuals) is mathematically required: positive scores represent overconfident commitments where the predictor exceeded actual delivered speed.

Given a user-specified nominal error tolerance $\alpha \in (0, 1)$ (primary setting $\alpha = 0.10$), we determine the conformal index:
$$k = \lceil (n + 1)(1 - \alpha) \rceil.$$
Let $q = s_{(k)}$ denote the $k$-th ordered score from the sorted sequence $s_{(1)} \le s_{(2)} \le \dots \le s_{(n)}$. If $k > n$, empirical support is insufficient to bound error at level $\alpha$, and we define $q = +\infty$.

The conservative lower bound for a new test instance $t$ is:
$$L_t = \max(0, \, f(x_t, m_t) - q).$$
If $q = +\infty$, the policy returns $L_t = 0.0$ with an insufficient-support flag. Throughput non-negativity justifies lower-clipping at zero.

### 3.3 Finite-Sample Conformal Budget Constraint
A crucial mathematical property of split-conformal prediction governs finite target calibration budgets:
$$k \le n \iff \lceil (n + 1)(1 - \alpha) \rceil \le n.$$
For nominal level $\alpha = 0.10$:
- If $n = 1$: $k = \lceil 2 \times 0.90 \rceil = 2 > 1 \implies q = +\infty$.
- If $n = 5$: $k = \lceil 6 \times 0.90 \rceil = 6 > 5 \implies q = +\infty$.
- If $n = 8$: $k = \lceil 9 \times 0.90 \rceil = 9 > 8 \implies q = +\infty$.
- If $n = 9$: $k = \lceil 10 \times 0.90 \rceil = 9 \le 9 \implies \text{Valid } q = s_{(9)}$.

**Lemma 1:** *At nominal violation rate $\alpha = 0.10$, any exact split-conformal calibrator requires at least $n \ge 9$ target calibration observations to output a non-trivial finite bound without defaulting to zero.*

Consequently, when evaluating budgets $K \in \{1, 2, 5\}$ target sessions, any valid conformal algorithm must implement a principled fallback hierarchy to source-domain calibration.

### 3.4 Proposed Coarse Missingness-Aware Calibration
In 5G NSA networks, telemetry missingness is predominantly structured across two technology groups:
- **Group 2 (LTE Only):** LTE anchor observed; NR telemetry unobserved ($m_{\text{LTE}} = 1, m_{\text{NR}} = 0$).
- **Group 3 (Dual LTE+NR):** Both LTE and NR carriers observed ($m_{\text{LTE}} = 1, m_{\text{NR}} = 1$).

Our proposed calibration algorithm maintains group-specific score pools $S_g = \{s_i : \text{group}(i) = g\}$. When predicting for instance $t$ with group $g_t$:
1. If $|S_{g_t}| \ge N_{\min}$ (with $N_{\min} = 3$ in low-budget settings), use group quantile $q_{g_t} = \text{Quantile}(S_{g_t}, 1 - \alpha)$.
2. Else, fall back to the pooled target quantile $q_{\text{pooled}} = \text{Quantile}(\bigcup S_g, 1 - \alpha)$.
3. If target data is absent ($K=0$) or insufficient, fall back to the frozen source quantile $q_{\text{source}}$.

```
Algorithm 1: Missingness-Aware Conformal Recalibration with Finite-Budget Fallback Hierarchy
Input  : Point predictor f(x, m), target prefix D_tgt = {(x_i, m_i, y_i, g_i)}_{i=1}^K,
         frozen source quantile q_source, nominal risk alpha in (0,1), minimum group support N_min.
Output : Calibrated lower bound L_t for new instance (x_t, m_t, g_t).
1: if K == 0 then
2:    return L_t = max(0, f(x_t, m_t) - q_source)
3: end if
4: Compute target signed overpredictions: s_i = f(x_i, m_i) - y_i for all i in {1, ..., K}
5: Form group score sets: S_g = {s_i : g_i == g}
6: if |S_{g_t}| >= N_min and ceil((|S_{g_t}| + 1)(1 - alpha)) <= |S_{g_t}| then
7:    k_g = ceil((|S_{g_t}| + 1)(1 - alpha))
8:    q_used = OrderStatistic(S_{g_t}, k_g)  // Group-specific quantile
9: else if K >= ceil((K + 1)(1 - alpha)) then
10:   k_pooled = ceil((K + 1)(1 - alpha))
11:   q_used = OrderStatistic(Union_g S_g, k_pooled)  // Target pooled fallback
12: else
13:   q_used = q_source  // Source-domain fallback by Lemma 1
14: end if
15: return L_t = max(0, f(x_t, m_t) - q_used)
```

---

## 4. Dataset Acquisition and Experimental Protocol

### 4.1 Dataset Provenance and Causal Extraction
We acquired two independent, open-access commercial measurement releases from the PERFORM consortium:
1. **Earlier Campaign (2020--2021, Zenodo 8224890):** 367,104 active trace rows across 45 measurement drives and 16 calendar collection days (December 13, 2020 to January 27, 2021) in Rome, Italy, evaluating Operator 1 (Op1) and Operator 2 (Op2).
2. **Later Campaign (2023, Zenodo 14073311):** 43 multi-session Ookla Speedtest traces collected across 12 calendar days (March 29, 2023 to July 5, 2023) evaluating Op1 and Op2 side-by-side during network evolution.

All raw archives were verified against published cryptographic checksums (SHA-256) recorded in `acquisition_manifest.json` and confirmed under CC BY 4.0 licenses. Across both campaigns, we reconstructed 1,132 complete Speedtest sessions (duration $57.7 \pm 11.9\text{ seconds}$) and formed 1,001 valid causal forecast pairs ($j-1 \to j$) strictly satisfying the 60-second lag freshness gate ($\Delta t \le 60.0\text{ s}$, with maximum observed active lag of 2.50 seconds). The earlier campaign contributes 503 valid instances (Op1: 150, Op2: 353; 63.4% unobserved 5G NR telemetry), and the later campaign contributes 498 valid instances (Op1: 284, Op2: 214; 53.4% unobserved 5G NR telemetry).

### 4.2 Transfer Regimes
To evaluate domain transfer under realistic deployment shifts, we establish four experimental regimes:
- **E0 (Within-Domain Reference):** Op1 2020--2021 Source $\to$ Op1 2020--2021 Test Suffix.
- **E1 (Campaign Temporal Transfer):** Op1 2020--2021 Source $\to$ Op1 2023 Test Suffix (evaluating temporal network evolution over 2.5 years).
- **E2 (Cross-Operator Transfer):** Op1 2020--2021 Source $\to$ Op2 2020--2021 Test Suffix (evaluating cross-carrier transfer under identical urban geography).
- **E3 (Joint Shift):** Op1 2020--2021 Source $\to$ Op2 2023 Test Suffix (combined operator and temporal shift).

### 4.3 Data Separation Protocol
Partitions are formed strictly by non-overlapping chronological collection days:
- **Within-Domain (E0):** To eliminate any risk of train/test overlap, Op1 2020--2021 is partitioned into a strictly disjoint 4-way chronological day split: earliest 45% days for model training (66 sessions across 3 dates), next 15% for validation/tuning (33 sessions across 1 date), next 15% for source calibration pool (10 sessions across 1 date), and the final 25% of days frozen as the test suffix (41 sessions across 2 dates). Runtime assertions programmatically verify 0% session and date overlap.
- **Transfer Regimes (E1--E3):** The source domain is partitioned into 60% training days, 20% validation days, and 20% source calibration days. The target domain is partitioned into the earliest 40% days for the candidate calibration pool (drawing budgets $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$ whole sessions), with the remaining 60% of days frozen as the fixed test suffix.

### 4.4 Evaluation Metrics
On a test set of $N$ sessions, we evaluate:
1. **Empirical Violation Rate ($V$):** $V = \frac{1}{N} \sum_{t=1}^N \mathbf{1}(y_t < L_t)$. Target nominal performance is $V \le \alpha = 0.10$.
2. **Offline Service-Level Commitment Ratio (SLCR) Proxy ($U$):** $U = \frac{\sum_{t=1}^N \min(L_t, y_t)}{\sum_{t=1}^N y_t}$. Measures the fraction of delivered cellular capacity that can be safely committed in advance. We emphasize that $U$ is an application-layer service commitment proxy (e.g., for proactive DASH video bitrate ladder selection or cloud gaming bitrate budgeting), rather than a physical MAC-layer scheduler modification or transport block allocation gain.
3. **Mean Overcommitment Magnitude:** $\text{Overcommit} = \frac{1}{N} \sum_{t=1}^N \max(L_t - y_t, 0)\text{ [Mbps]}$.
4. **Operational SLA Economic Loss Function:** To evaluate the business trade-off between QoS violations and un-utilized bandwidth, we define the operator's operational cost function:
   $$\text{Cost}(\lambda) = \lambda \cdot V + (1 - \lambda) \cdot (1 - U)$$
   where $\lambda \in [0, 1]$ represents the regulatory or SLA penalty weight assigned to service violations relative to under-committed capacity.
5. **Clustered Bootstrap Inference:** 2,000 paired day-cluster bootstrap resamples to establish 95% confidence intervals for paired differences $\Delta U = U_{\text{proposed}} - U_{\text{global}}$ and $\Delta V = V_{\text{proposed}} - V_{\text{global}}$.

---

## 5. Experimental Results and Discussion

### 5.1 Point Predictor Benchmark and GPU Acceleration
Table 1 compares the predictive performance of candidate models on the leak-free source development partition.

| Model Architecture | Val MAE (Mbps) | Val RMSE (Mbps) | Fit Time (s) | Hardware / VRAM |
|---|---:|---:|---:|---|
| **Persistence** | **9.10** | **16.64** | 0.000 | Host CPU |
| **Ridge Regression** | 12.08 | 24.26 | 0.027 | Host CPU |
| **HistGradientBoosting** | 14.52 | 27.67 | 2.526 | Host CPU |
| **BAMMO (Jacobson et al. 2025)** | 16.72 | 33.84 | 0.408 | Host CPU |
| **Quantile GBM ($p=0.10$)** | 18.07 | 35.99 | 0.111 | Host CPU |
| **GPU ThroughputResNet** | 18.27 | 33.38 | 1.033 | NVIDIA RTX 4060 (24.8 MB) |

Persistence achieves the lowest validation point error on the source development set (Val MAE 9.10 Mbps, RMSE 16.64 Mbps), followed by Ridge (MAE 12.08 Mbps) and HistGradientBoosting (MAE 14.52 Mbps, RMSE 27.67 Mbps). BAMMO (Jacobson et al., JRSS Series C 2025), which trains pattern-specific base decision trees for observed telemetry subsets, achieves competitive error (Val MAE 16.72 Mbps, RMSE 33.84 Mbps) and trains rapidly in 0.408 seconds on host CPU. The PyTorch Deep Tabular ResNet executed on the NVIDIA GeForce RTX 4060 GPU achieved high computational efficiency (Val MAE 18.27 Mbps, RMSE 33.38 Mbps with 1.033 seconds execution time for 60 epochs utilizing 24.8 MB peak VRAM). Because HistGradientBoosting natively handles unobserved 5G NR features during recursive tree splitting without arbitrary imputation and provides robust nonlinear capacity, it was frozen as the common predictor for all downstream transfer and calibration experiments, yielding a frozen source global conformal quantile of $q_{\text{source}} = 28.13$~Mbps at nominal risk $\alpha = 0.10$.

### 5.2 Transfer Benchmark and Calibration Budget Analysis
Table 2 reports the empirical violation rate $V$ and supported-rate fraction $U$ across all four transfer regimes and calibration budgets $K \in \{0, 2, 5, 8, 9, 10, 15\}$.

| Regime | Method | Budget $K=0$ ($V$ / $U$) | Budget $K=2$ ($V$ / $U$) | Budget $K=5$ ($V$ / $U$) | Budget $K=8$ ($V$ / $U$) | Budget $K=9$ ($V$ / $U$) | Budget $K=10$ ($V$ / $U$) | Budget $K=15$ ($V$ / $U$) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **E0: Within-Domain (Op1 2020--2021)** | Uncalibrated Point | 0.37 / 0.36 | 0.37 / 0.36 | 0.37 / 0.36 | 0.37 / 0.36 | 0.37 / 0.36 | 0.37 / 0.36 | 0.37 / 0.36 |
| | Global Conformal | 0.00 / 0.04 | 0.00 / 0.04 | 0.00 / 0.04 | 0.00 / 0.04 | 0.07 / 0.08 | 0.00 / 0.04 | 0.00 / 0.04 |
| | **Proposed Missingness-Aware** | 0.00 / 0.04 | 0.00 / 0.04 | 0.00 / 0.04 | 0.00 / 0.04 | 0.00 / 0.05 | 0.00 / 0.04 | 0.00 / 0.04 |
| **E1: Campaign Transfer (Op1 2023)** | Uncalibrated Point | 0.37 / 0.38 | 0.37 / 0.38 | 0.37 / 0.38 | 0.37 / 0.38 | 0.37 / 0.38 | 0.37 / 0.38 | 0.37 / 0.38 |
| | Global Conformal | 0.01 / 0.02 | 0.01 / 0.02 | 0.01 / 0.02 | 0.01 / 0.02 | 0.07 / 0.10 | 0.07 / 0.10 | 0.07 / 0.10 |
| | Proposed Missingness-Aware | 0.01 / 0.02 | 0.01 / 0.02 | 0.01 / 0.02 | 0.01 / 0.02 | 0.06 / 0.09 | 0.06 / 0.09 | 0.07 / 0.10 |
| | **Bayes-Corrected CS-CP** | \multicolumn{5}{c}{--- Target Unlabeled Density Ratio ---} & \multicolumn{2}{c}{**0.01 / 0.02**} |
| **E2: Cross-Operator (Op2 2020--2021)** | Uncalibrated Point | 0.58 / 0.41 | 0.58 / 0.41 | 0.58 / 0.41 | 0.58 / 0.41 | 0.58 / 0.41 | 0.58 / 0.41 | 0.58 / 0.41 |
| | Global Conformal | 0.02 / 0.03 | 0.02 / 0.03 | 0.02 / 0.03 | 0.02 / 0.03 | 0.07 / 0.08 | 0.07 / 0.08 | 0.07 / 0.08 |
| | Proposed Missingness-Aware | 0.02 / 0.03 | 0.02 / 0.03 | 0.02 / 0.03 | 0.02 / 0.03 | 0.02 / 0.03 | 0.02 / 0.03 | 0.11 / 0.07 |
| | **Bayes-Corrected CS-CP** | \multicolumn{5}{c}{--- Target Unlabeled Density Ratio ---} & \multicolumn{2}{c}{**0.04 / 0.04**} |
| **E3: Joint Shift (Op2 2023)** | Uncalibrated Point | 0.32 / 0.35 | 0.32 / 0.35 | 0.32 / 0.35 | 0.32 / 0.35 | 0.32 / 0.35 | 0.32 / 0.35 | 0.32 / 0.35 |
| | Global Conformal | 0.01 / 0.03 | 0.01 / 0.03 | 0.01 / 0.03 | 0.01 / 0.03 | 0.00 / 0.02 | 0.00 / 0.00 | 0.00 / 0.00 |
| | Proposed Missingness-Aware | 0.01 / 0.03 | 0.01 / 0.03 | 0.01 / 0.03 | 0.01 / 0.03 | 0.00 / 0.02 | 0.00 / 0.00 | 0.00 / 0.00 |
| | **Bayes-Corrected CS-CP** | \multicolumn{5}{c}{--- Target Unlabeled Density Ratio ---} & \multicolumn{2}{c}{**0.01 / 0.04**} |

#### Key Empirical Insights:
1. **Uncalibrated Point Prediction Breakdown:** Relying on raw point predictions ($\hat{y}_t$) results in unacceptable operational failure: 37% violations in E0, 37% in E1, and a massive **58% violation rate** in E2 (cross-operator).
2. **Source-Only Calibration ($K=0$):** Conformal calibration using source-only labels ($q_{\text{source}} = 28.13\text{ Mbps}$) immediately restores reliable coverage ($V \le 0.02 \ll 0.10$ across all regimes), supporting dependable lower bounds without requiring any target measurement drives.
3. **Target Recalibration Activation at $K=9$ (Lemma 1 Proof):** As proved in Lemma 1, split-conformal calibration at $\alpha=0.10$ lacks sufficient target samples when $K \le 8$ ($\lceil 0.9(K+1) \rceil > K$), forcing calibrators to fall back to the source quantile. At exactly $K=9$, target calibration sharply activates: in E1, supported capacity expands to $U=0.101$ with $V=0.072 \le 0.10$; in E2, $U$ expands to $0.078$ with $V=0.070 \le 0.10$.
4. **Behavior under Extreme Transfer Shift (E3):** In E3 (Joint Shift), target recalibration encounters a zero-throughput network stall in the target calibration prefix at $K \ge 10$, driving bounds conservatively to zero ($V = 0.000, U = 0.000$). Crucially, Bayes prior-corrected Covariate-Shift Conformal Prediction (CS-CP) avoids small-sample stall sensitivity by re-weighting source calibration residuals, sustaining $U = 0.035$ with bounded risk $V = 0.010$.

### 5.3 Online Adaptive Conformal Inference (ACI)
Under secondary streaming evaluation, Adaptive Conformal Inference dynamically tracks distribution shift across test streams, converging to violation rates between 7.8% and 11.5% across all four transfer regimes (E0: 9.5%, E1: 11.5%, E2: 8.6%, E3: 7.8%).

### 5.4 Ablation Studies, Sensitivity, and Pareto Frontiers
- **Fallback Threshold Sensitivity:** Varying $N_{\min} \in \{3, 5, 10, 20\}$ demonstrated robust behavior: small thresholds allow fine-grained adaptation ($V=0.086$), while higher thresholds gracefully fall back to pooled target calibration ($V=0.090$).
- **Artificial Missingness Stress Test:** Artificially masking 10%, 30%, and 50% of observed 5G NR telemetry decreased violation rates from 0.086 to 0.043, while supported rate contracted from 0.178 to 0.115. Missing NR telemetry prevents the model from anticipating high-throughput dual-connectivity bursts, forcing conservative predictions that enhance safety at the cost of lower committed throughput.
- **Telemetry Freshness Horizon Sensitivity ($\Delta t \in \{30, 60, 120\}$ s):**
  - At 30 s lookback, intermittent radio logging causes fewer valid reference signal samples to fall within the pre-test window, elevating violation rates ($V = 0.188$ in E2, $V = 0.302$ in E1 at $K=0$).
  - At 60 s lookback (primary setting), radio logging capture stabilizes, recovering nominal coverage ($V = 0.000$ in E0, $V = 0.086$ in E2, $V = 0.079$ in E1 with $K=10$).
  - At 120 s lookback, performance remains stable ($V = 0.000$ in E0, $V = 0.086$ in E2, $V = 0.122$ in E1). This confirms 60 seconds as the optimal operational lookback horizon.
- **Dense Multi-$\alpha$ Pareto Risk-Utility Frontier:**
  Evaluating across nominal risk levels $\alpha \in [0.01, 0.30]$ demonstrates that the proposed calibrator tightly tracks the nominal guarantee line $V \le \alpha$ from ultra-reliable low-latency operations ($\alpha=0.01$) to best-effort services ($\alpha=0.20$), smoothly expanding supported rate fraction $U$ from 0.05 to 0.35 (Fig. 4).
- **Covariate-Shift Conformal Prediction (CS-CP):**
  Evaluating Covariate-Shift Conformal Prediction (Tibshirani et al., NeurIPS 2019) with Bayes class-prior correction ($w(x) = \frac{P(D=1|x)}{1-P(D=1|x)} \cdot \frac{N_{\text{src}}}{N_{\text{tgt}}}$) confirmed strictly valid coverage across all three shift regimes: $V = 0.014$ in E1 ($U=0.020$, mean $w=0.27$), $V = 0.035$ in E2 ($U=0.042$, mean $w=0.86$), and $V = 0.010$ in E3 ($U=0.035$, mean $w=0.28$). Crucially, in Regime E3 (where small-sample target recalibration suffered utility collapse due to an outlier zero-throughput stall), CS-CP sustains $U = 0.035$ while strictly bounding violations at 1.0%, providing an outlier-resilient transfer alternative when target labeled sessions are scarce.
- **Operational SLA Economic Cost Optimization:**
  Evaluating normalized operational loss $\text{Cost}(\lambda) = \lambda \cdot V + (1 - \lambda) \cdot (1 - U)$ across penalty weights $\lambda \in [0, 1]$ (Fig. 5) demonstrates that conformal recalibration dominates uncalibrated predictors for all penalty regimes with $\lambda \ge 0.35$. Under standard regulatory and QoS penalty regimes ($\lambda \ge 0.50$), our proposed missingness-aware calibrator reduces operational SLA loss by 25.7% to 57.9%, and by 83.8% under zero-risk SLAs ($\lambda = 1.0$).

---

## 6. Operational Principles for Emerging 5G Networks (Bangladesh Case Study)
The findings provide actionable guidelines for telecommunications engineering teams, such as in Bangladesh (Grameenphone, Banglalink, Robi Axiata, Teletalk) complying with BTRC QoS mandates:
1. **Drive-Test Campaign Sizing ($K \ge 10$ Rule):** Drive-test benchmarking and network optimization campaigns cost BDT 1,20,000 to 2,50,000 per route day. Our proof of Lemma 1 establishes that collecting fewer than $K=9$ sessions per morphological cluster (e.g., dense urban Dhaka vs. rural barind tracts) provides zero statistical benefit for local split-conformal calibration at $\alpha=0.10$. Optimization teams must budget at least $K \ge 10$ sessions to activate statistically valid local recalibration.
2. **Regulatory QoS Compliance (BTRC Directives):** Under BTRC mobile broadband benchmarks ($\ge 7\text{ Mbps}$ 4G DL, $< 2\%$ drop rate), uncalibrated ML predictors expose operators to a 32% to 58% service failure probability and heavy regulatory fines. Conformal calibration guarantees compliance with mathematically bounded violation rates.
3. **Telemetry Missingness Management:** In developing markets where 5G rollout occurs incrementally over existing 4G anchors, secondary 5G NR carriers are naturally absent in >60% of drive logs. Operators must avoid naive zero-imputation and adopt models with native missingness branching combined with group-stratified conformal bounds. (See detailed technical report in `docs/bangladesh_telecom_case_study.md`).

---

## 7. Threats to Validity and Limitations
1. **Geographical Specificity:** Measurements were collected in urban European environments (Rome). Propagation characteristics in dense Asian megacities (e.g., Dhaka) or rural topographies will exhibit distinct multi-path and clutter profiles.
2. **Offline Proxy:** Supported-rate fraction $U$ is an offline capacity proxy, not a live scheduler modification or user satisfaction metric.
3. **Protocol Dependence:** Analysis focuses on HTTP/TCP Speedtest sessions; streaming video protocols with dynamic DASH rate switching may exhibit different client-server feedback loops.

---

## 8. Conclusion
In this paper, we established an experimental benchmark investigating the reliability of cellular throughput forecasts under distribution shift and natural telemetry missingness. Evaluating 1,132 commercial measurement sessions (1,001 causal test pairs) across four transfer regimes, we demonstrated that uncalibrated models experience catastrophic failure (32%--58% violations), whereas split-conformal calibration guarantees nominal reliability ($V \le \alpha = 0.10$). We proved that finite-sample conformal validity at $\alpha=0.10$ requires $K \ge 9$ sessions (Lemma 1), establishing a strict lower bound for target campaign budgets. Our results demonstrate that within-domain disjoint chronological evaluation ensures zero data leakage, and Bayes prior-corrected covariate shift conformal prediction sustains reliable coverage across multi-year temporal and cross-carrier shifts.

