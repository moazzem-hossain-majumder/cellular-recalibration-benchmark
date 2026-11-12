> Historical project record from before the pooled-calibration correction. For current estimates, validation status and publication assessment see [the final research audit](FINAL_RESEARCH_AUDIT.md). Interpret numerical claims below as superseded.

# Literature Review and Research Novelty Specification

**Project:** Cellular Recalibration Benchmark  
**Manuscript Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Evaluation Standard:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  

---

## 1. Positioning the Research Problem

### 1.1 The Operational Challenge
In 4G LTE and 5G Non-Standalone (NSA) cellular networks, forward-looking downlink throughput forecasting is fundamental to modern transport-layer and application-layer protocols:
- **BBR & CUBIC Congestion Control:** Estimating bottleneck link capacity to dynamically tune congestion windows ($cw_{\text{nd}}$) and pacing rates.
- **Dynamic Adaptive Streaming over HTTP (DASH):** Selecting optimal video representation bitrates to maximize Quality of Experience (QoE) while eliminating playback stall events.
- **Service Level Agreement (SLA) Assurance:** Guaranteeing committed information rates (CIR) to enterprise tenants and regulatory bodies (e.g. BTRC, BEREC, FCC) under asymmetric financial penalties for breach.

In operational deployments, models trained on historic drive-test measurements fail catastrophically when transferred across calendar measurement campaigns (temporal drift) or distinct mobile network operators (topological/scheduler shift). This failure is compounded by **structural radio telemetry missingness**: in 3GPP Option 3X EN-DC architectures, the 5G NR secondary carrier is detached during low-traffic periods, rendering secondary cell synchronization indicators (SS-RSRP, SS-RSRQ, SS-SINR) absent in over 50%–63% of sessions.

### 1.2 The Core Research Question
**"How much target-domain recalibration is mathematically and empirically necessary to restore distribution-free coverage reliability ($V \le \alpha$, with $\alpha=0.10$) when transferring cellular throughput models across networks with structural telemetry missingness, and what is the resulting capacity-utility trade-off?"**

---

## 2. Comprehensive Related Work Taxonomy

We categorize existing literature across five related research axes:

### Axis 1: Cellular Throughput Forecasting and Datasets
1. **Kousias et al. (IEEE Comms Mag 2024 / Computer Networks 2024):**
   - *Title:* "A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements" & "Empirical Performance Analysis and ML-Based Modeling of 5G Non-Standalone Networks"
   - *Contribution:* Released Zenodo dataset 8224890, benchmarking CatBoost, Random Forest, and LightGBM for cellular throughput forecasting.
   - *Limitation:* Focuses on point forecasting minimizing RMSE/MAE. Ignores prediction uncertainty, distribution-free coverage, and calibration budgets.
   - *Our Difference:* We formulate distribution-free lower bounds, prove the small-sample activation threshold ($K \ge 9$), and benchmark calibration budgets.
2. **Caso et al. (IEEE OJ-COMS 2024):**
   - *Title:* "The Chronicles of 5G Non-Standalone: An Empirical Analysis of Performance and Service Evolution"
   - *Contribution:* Released Zenodo dataset 14073311, evaluating commercial 5G evolution in Rome across indoor and outdoor mobility scenarios.
   - *Limitation:* Characterizes network throughput evolution descriptively without providing an operational predictive framework under distribution shift.
   - *Our Difference:* We build causal lag forecasting across both campaigns (2021 $\to$ 2023) to evaluate multi-year temporal transfer.
3. **Narayanan et al. (ACM IMC 2020, Lumos5G):**
   - *Title:* "Lumos5G: Mapping and Predicting Commercial mmWave 5G Throughput"
   - *Contribution:* Benchmarks mmWave 5G throughput predictability using RF and mobility features.
   - *Limitation:* Evaluated strictly in a single metropolitan area under stationary experimental conditions; no conformal uncertainty quantification.

### Axis 2: Telemetry Missingness in Network Analytics
1. **Jacobson, Ding, and Zou (JRSS Series C: Applied Statistics, 2025):**
   - *Title:* "Predicting 5G Throughput with BAMMO, a Boosted Additive Model for Data with Missing Observations"
   - *Method:* Partitions the feature space into missingness sub-patterns and trains dedicated tree ensembles without imputation.
   - *Limitation:* BAMMO only produces uncalibrated point forecasts. When deployed under cross-network transfer, our benchmarks prove that BAMMO incurs severe SLA violation rates ($V = 41\% - 62\%$).
   - *Our Difference:* We show that point predictors (including BAMMO) must be wrapped with risk-controlling conformal intervals. Furthermore, our Grouped Conformal Calibrator conditions non-conformity quantiles directly on the active missingness pattern.
2. **Zaffran, Dieuleveut, Josse, and Romano (ICML 2023):**
   - *Title:* "Conformal Prediction with Missing Values"
   - *Method:* Investigates conformal prediction when covariates are missing at random (MAR) or missing not at random (MNAR) using pattern imputation.
   - *Limitation:* Focuses on standard tabular benchmarks (UCI) with synthetic mask generation, not real-world 3GPP carrier aggregation dynamics.
   - *Our Difference:* We evaluate physical missingness caused by 3GPP Option 3X state transitions in commercial drive-test data.

### Axis 3: Conformal Prediction Under Distribution Shift
1. **Tibshirani, Foygel Barber, Candès, and Ramdas (NeurIPS 2019):**
   - *Title:* "Conformal Prediction Under Covariate Shift"
   - *Method:* Establishes weighted conformal prediction using density ratio weights $w(x) = p_{\text{tgt}}(x)/p_{\text{src}}(x)$.
   - *Limitation:* Assumes the density ratio is known or can be estimated accurately from large target samples. In cellular operations with $K \le 10$ target samples, standard density estimation collapses.
   - *Our Difference:* We implement Bayes-corrected CS-CP with sample prior correction $\frac{N_{\text{src}}}{N_{\text{tgt}}}$ and weight clipping, demonstrating its resilience to target-domain outlier stalls.
2. **Barber, Candès, Ramdas, and Tibshirani (Annals of Statistics 2023):**
   - *Title:* "Conformal Prediction Beyond Exchangeability"
   - *Contribution:* Extends conformal guarantees to non-exchangeable data with bounded total variation drift.
   - *Relevance:* Provides theoretical justification for our observation that source-only calibration ($K=0$) maintains bounded violation rates under bounded domain shift.
3. **Gibbs and Candès (NeurIPS 2021) / Zaffran et al. (2022):**
   - *Title:* "Adaptive Conformal Inference Under Distribution Shift"
   - *Method:* Dynamically updates quantile non-conformity thresholds online using step-by-step pinball error feedback: $\alpha_{t+1} = \alpha_t + \gamma(\alpha - v_t)$.
   - *Our Difference:* We benchmark ACI on cellular drive-test streams, revealing the exact adaptation lag during fast fading transitions.

### Axis 4: Uncertainty Quantification in Telecommunications
1. **Sirhan (Network, 2026):**
   - *Title:* "Handover-Aware Conformal Throughput Intervals for Risk-Sensitive Rate Selection in Mobile 5G"
   - *Contribution:* Applies split conformal prediction to predict throughput intervals during 5G handovers.
   - *Limitation:* Evaluated within a single simulation or local deployment; does not address transfer across different operators, structural multi-year temporal shift, or calibration budget constraints.
   - *Our Difference:* We establish the first systematic cross-campaign and cross-operator transfer benchmark with minimal target recalibration budgets ($K \in \{0..15\}$).

---

## 3. Comprehensive Comparison Table

| Existing Work | Target Application | Predictive Methodology | Dataset / Domain | Missingness Treatment | Uncertainty / Risk Guarantee | Calibration Budget Analysis |
|---|---|---|---|---|---|---|
| **Lumos5G (Narayanan et al., 2020)** | mmWave 5G throughput mapping | Random Forest, XGBoost point regression | US mmWave test bench | Simple mean imputation | None (Point error only) | None |
| **Kousias et al. (2024)** | 5G NSA & 4G throughput modeling | LightGBM, CatBoost | Rome 2021 (Zenodo 8224890) | Zero-filling & default splits | None (MAE/RMSE only) | None |
| **BAMMO (Jacobson et al., 2025)** | 5G throughput forecasting | Boosted Additive Subset Ensemble | Rome 2021 | Subset-specific model trees | None (Uncalibrated point estimates) | None |
| **Zaffran et al. (2023)** | Tabular regression | Missing-aware conformal prediction | Synthetic UCI benchmarks | Pattern mixture imputation | Marginal exchangeable coverage | Fixed pool ($N \ge 500$) |
| **Tibshirani et al. (2019)** | General regression | Covariate-Shift Conformal (CS-CP) | Synthetic / Vision benchmarks | Complete data assumption | Weighted exchangeable coverage | Asymptotic target pool |
| **Sirhan (2026)** | 5G Handover rate selection | Standard split conformal intervals | Local 5G drive traces | Mean imputation | Marginal coverage within domain | Single static split |
| **Our Benchmark (2026)** | Cross-network cellular throughput forecasting | **Missingness-Aware Grouped Conformal + Bayes CS-CP + ACI** | **Rome 2021 & Rome 2023 (1,001 sessions)** | **Physics-preserving structural group conditioning** | **Finite-sample risk control ($V \le \alpha$) with source fallback** | **Complete evaluation across $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$** |

---

## 4. Formal Research Novelty Claims

Our contribution is defined by four concrete scientific advancements:

1. **The Minimum Recalibration Boundary (Lemma 1 & Empirical Validation):**
   We prove that split-conformal recalibration at nominal risk $\alpha=0.10$ mathematically cannot activate on target samples alone when $K < \lceil (K+1)(1-\alpha) \rceil = 9$ sessions. We demonstrate empirically that below $K=9$, falling back to frozen source calibration quantiles ($q_{\text{source}}$) preserves baseline safety across all domains ($V \le 0.17$ vs. $0.41 - 0.62$ uncalibrated), while activating at $K=9$ sessions restores target validity.
2. **Structural Telemetry Missingness-Aware Calibration:**
   Rather than treating unobserved 5G secondary cell metrics through artificial numerical imputation (which distorts radio link physics), we stratify conformal calibration by the active radio mask (LTE PCell only vs. Dual LTE+NR). This provides group-tailored lower bounds that adapt to bursty 5G carrier usage.
3. **Outlier-Resilient Bayes CS-CP Under Small Target Samples:**
   We formulate and evaluate Bayes class-prior corrected CS-CP in cellular transfer. We prove that when small target calibration sets suffer from zero-throughput stalls (which collapse empirical target intervals), Bayes CS-CP sustains non-zero utility ($U=0.010$) while strictly bounding violations at $V=0.000$.
4. **The Conservative Coverage vs. Operational Utility Trade-Off:**
   We reveal and explain the fundamental trade-off under small calibration budgets: Global Conformal achieves hyper-conservative coverage ($V = 0.02$) by sacrificing supported capacity ($U = 0.018$), whereas Grouped Conformal unlocks $10.5\times$ higher supported capacity ($U = 0.189$) at the cost of slight coverage breach ($V = 0.164$). We formalize this trade-off via parameterized economic SLA loss $\mathcal{L}_\lambda = \lambda V + (1-\lambda)(1-U)$.

