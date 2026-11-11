# Phase 3: Methodology and Machine Learning Pipeline Audit

**Benchmark:** Cellular Throughput Recalibration Under Incomplete Telemetry  
**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Target Venue:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  
**Date:** March 2026  
**Status:** COMPLETED & VERIFIED  

---

## 1. Executive Summary

Phase 3 audits the end-to-end mathematical, predictive, and uncertainty quantification pipeline. We establish:
1. Strict data leakage safeguards across feature preparation, point forecasting, and conformal calibration.
2. Comprehensive theoretical assumptions, finite-sample guarantees, and operational failure modes for all five uncertainty quantification methods.
3. Rigorous validation of point forecasting models (HistGradientBoosting, BAMMO, Ridge, QuantileGBM, and GPU ThroughputResNet on NVIDIA GeForce RTX 4060).
4. Explicit methodological designation of statistical tests, particularly clarifying asymptotic constraints on few-cluster block bootstrap resampling.

---

## 2. Data Leakage Safeguards & Invariant Auditing

| Pipeline Stage | Potential Leakage Vector | Implemented Safeguard & Code Invariant | Verification Status |
|:---|:---|:---|:---:|
| **Feature Extraction** | Future radio measurements leaking into prior state | Lookback window is strictly causal ($t \in [t_{\text{start}} - 60\text{s}, t_{\text{start}}]$). Features are extracted exclusively from pre-test rows. | **VERIFIED PASS** |
| **Lag Feature Construction** | Target throughput copied into lag feature | Asserted $\text{target\_y} \neq y_{\text{lag1}}$ identically. Enforced lag age $\Delta t \in [0.0, 60.0]$ s. | **VERIFIED PASS** |
| **Missingness Imputation & Scaling** | Target or validation statistics leaking into training | `TabularPreprocessor` fits `SimpleImputer(strategy='median')` and `StandardScaler()` strictly on the training partition (`fit_transform`). Test/validation partitions only invoke `transform()`. | **VERIFIED PASS** |
| **Domain Partitioning** | Identical sessions or calendar dates shared across train/test | Enforced chronological day blocking. Disjointness check strictly asserts $S_{\text{train}} \cap S_{\text{test}} = \emptyset$ and $D_{\text{train}} \cap D_{\text{test}} = \emptyset$. | **VERIFIED PASS** |
| **Conformal Calibration** | Target test labels exposed during calibration quantile tuning | Calibration prefixes ($K$ sessions) are drawn strictly from the chronologically preceding calibration pool ($D_{\text{pool}} < D_{\text{test}}$). Test suffix labels are never exposed to calibration. | **VERIFIED PASS** |

---

## 3. Mathematical Foundations & Assumptions of Uncertainty Quantification Methods

### Method 1: Standard Split Conformal Prediction (Global SCP)
* **Mathematical Definition:**
  - One-sided non-conformity score: $s_i = \hat{y}(x_i) - y_i$.
  - Calibrated quantile: $\hat{q} = \text{Quantile}\left(\frac{\lceil (n+1)(1-\alpha) \rceil}{n}; \{s_i\}_{i=1}^n\right)$.
  - Lower prediction bound: $L(x) = \max(0, \hat{y}(x) - \hat{q})$.
* **Underlying Theoretical Assumption:** Exchangeability of $(s_1, \dots, s_n, s_{n+1})$.
* **Finite-Sample Guarantee:** Under exchangeability, $P(Y_{n+1} \ge L(X_{n+1})) \ge 1 - \alpha$.
* **Finite-Sample Support Threshold (Lemma 1):** For coverage level $1 - \alpha = 0.90$, the quantile rank index $\lceil (n+1) \cdot 0.90 \rceil \le n$ is mathematically impossible for $n \le 8$. Split conformal is undefined ($q = +\infty, L(x) = 0$) for $K \in \{1, 2, 5, 8\}$ and first becomes well-defined at $n = 9$.
* **Telecom Failure Mode:** When transferred to an unseen network or time period with different radio propagation or missingness, exchangeability is violated. If the base model overpredicts, the violation rate spikes ($V \gg \alpha$), invalidating service level agreements (SLAs).

### Method 2: Grouped Conformal Calibrator (Subgroup-Conditioned SCP)
* **Mathematical Definition:**
  - Residuals are partitioned by observed radio group $g \in \{0, 1, 2, 3\}$.
  - Pattern-specific quantile: $\hat{q}_g = \text{Quantile}\left(\frac{\lceil (n_g+1)(1-\alpha) \rceil}{n_g}; \{s_i : g_i = g\}\right)$.
  - Lower prediction bound: $L(x) = \max(0, \hat{y}(x) - \hat{q}_{g(x)})$.
* **Theoretical Guarantee:** Group-conditional coverage $P(Y \ge L(X) \mid G=g) \ge 1 - \alpha$.
* **Sample Size Requirement & Fallback Hierarchy:**
  - Requires $n_g \ge 9$ instances within group $g$.
  - In low-budget regimes ($K < 10$), individual radio groups lack sufficient support.
  - Cascading fallback: Pattern-specific quantile $\to$ Pooled target calibration quantile $\to$ Frozen source quantile.

### Method 3: Covariate-Shift Conformal Prediction (CS-CP)
* **Mathematical Definition:**
  - Non-conformity scores from the source domain are reweighted by the density ratio $w(x) = \frac{dP_{\text{tgt}}(x)}{dP_{\text{src}}(x)}$.
  - Logistic domain discriminator estimates $P(\text{Tgt} \mid x)$. By Bayes rule:
    $$w(x) = \frac{P(\text{Tgt} \mid x)}{1 - P(\text{Tgt} \mid x)} \cdot \frac{N_{\text{src}}}{N_{\text{tgt}}}$$
  - Normalized point-mass probabilities: $p_i = \frac{w(x_i)}{\sum_{j=1}^{n_{\text{src}}} w(x_j) + w(x_{\text{test}})}$.
  - Quantile is obtained from the cumulative distribution function of weighted source scores.
* **Core Assumption:** *Covariate shift only* ($P_{\text{src}}(Y \mid X) = P_{\text{tgt}}(Y \mid X)$, while $P_{\text{src}}(X) \neq P_{\text{tgt}}(X)$).
* **Operational Strengths:** Zero-shot target transfer ($K=0$ target labels required).
* **Telecom Failure Mode:** In wireless networks, changes in RAN scheduling, carrier aggregation policies, or cell interference alter the conditional throughput distribution $P(Y \mid X)$ (concept drift). CS-CP cannot account for shifts in $P(Y \mid X)$ without target labels.

### Method 4: Adaptive Conformal Inference (ACI)
* **Mathematical Definition:**
  - Online recursive update rule (Gibbs & Candès, 2021):
    $$L_t = \max(0, \hat{y}_t - q_t)$$
    $$\text{err}_t = \mathbb{I}(y_t < L_t)$$
    $$q_{t+1} = q_t + \gamma (\text{err}_t - \alpha)$$
* **Theoretical Guarantee:** Asymptotic long-run coverage $\lim_{T \to \infty} \frac{1}{T} \sum_{t=1}^T \text{err}_t = \alpha$ without requiring exchangeability or stationarity.
* **Trade-offs:** 
  - Parameter $\gamma$ governs responsiveness: large $\gamma$ adapts quickly to macro-cell handovers but induces high variance in throughput commitments; small $\gamma$ is robust but slow to react to abrupt coverage drops.
  - Requires immediate ground-truth feedback after each forecast step (streaming/online mode).

### Method 5: Paired Day-Cluster Block Bootstrap
* **Mathematical Definition:**
  - Cluster resampling where each calendar date $d \in \mathcal{D}_{\text{test}}$ is treated as an independent cluster block, preserving intra-day temporal correlation.
  - 2,000 bootstrap iterations compute paired difference distributions:
    $$\Delta V = V_{\text{prop}} - V_{\text{base}}, \quad \Delta U = U_{\text{prop}} - U_{\text{base}}$$
* **Few-Cluster Methodological Limitation:**
  - Asymptotic cluster bootstrap guarantees require $N_{\text{clusters}} \ge 20$ to 30.
  - In within-domain regime E0, the fixed test suffix spans only 2 distinct calendar collection dates ($N_{\text{clusters}}=2$).
  - **Explicit Methodological Designation:** E0 cluster bootstrap confidence intervals are designated as **exploratory**. Transfer regimes E1, E2, and E3 possess 7 to 8 test cluster dates, offering reliable non-parametric comparison.

---

## 4. Point Predictor Benchmarking & Computational Profiles

All candidate predictors were benchmarked on the source development split (train $N=57$, validation $N=9$):

| Predictor Architecture | Primary Characteristics | Val MAE (Mbps) | Val RMSE (Mbps) | Hardware Execution |
|:---|:---|:---:|:---:|:---:|
| **HistGradientBoosting** | Tree boosting with native NaN missingness routing | **25.29** | **31.39** | CPU |
| **BAMMO** | Component-wise additive boosting over missingness patterns | 25.56 | 31.75 | CPU |
| **Ridge Regression** | L2-regularized linear model with median imputation | 27.67 | 34.02 | CPU |
| **Quantile Boosting (p10)** | Asymmetric pinball loss gradient boosting | 48.06 | 55.45 | CPU |
| **Persistence Predictor** | Causal previous-session throughput ($y_{\text{lag1}}$) | 36.31 | 45.42 | CPU |
| **ThroughputResNet** | 3-block Deep Tabular MLP with LayerNorm & SiLU | 28.71 | 35.12 | **NVIDIA RTX 4060 GPU** (CUDA) |

*Decision:* `HistGradientBoosting` achieves the lowest validation error (MAE 25.29 Mbps) and native handling of unobserved 5G telemetry. It serves as the primary backbone predictor for conformal recalibration.

---

## 5. Summary of Pipeline Integrity Verification

1. All features are causal and leak-free.
2. Quantile calculations obey finite-sample split conformal mathematics (Lemma 1 verified).
3. The offline recalibration track and online ACI track operate under explicitly stated mathematical regimes.
4. Statistical significance tests are transparently qualified regarding cluster count constraints.

Phase 3 is complete and verified. Proceeding to Phase 4 (Full Experiment Rerun & Artifact Regeneration).

