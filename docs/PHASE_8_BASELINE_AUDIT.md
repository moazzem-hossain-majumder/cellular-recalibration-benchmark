> Historical project record from before the pooled-calibration correction. For current estimates, validation status and publication assessment see [the final research audit](FINAL_RESEARCH_AUDIT.md). Interpret numerical claims below as superseded.

# Research Baseline and Scientific Integrity Audit (Phase 8 Baseline Audit)

**Project:** Cellular Recalibration Benchmark  
**Manuscript Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Audit Date:** November 2026  
**Auditor:** Multidisciplinary Research, Engineering & Publication-Integrity Team  
**Evaluation Standard:** Adversarial, Evidence-Based Scientific Audit for IEEE Transactions / Open Journal Submissions  

---

## Executive Summary

This document establishes the **True Research Baseline** for the project, following the directives of the Master Improvement Plan (Stage A). It conducts an adversarial, strictly evidence-based inspection across all source code, datasets, experiment runners, generated artifacts, unit/integration tests, and manuscript files.

The core research question is scientifically compelling: in cellular networks (specifically 4G LTE and 5G Non-Standalone Option 3X EN-DC architectures), operational cellular throughput forecasting is vulnerable to catastrophic failure under environmental and operator transfer, especially when secondary cell (5G NR) radio telemetry is structurally missing due to intermittent carrier aggregation. 

However, prior iterations of this project suffered from methodological flaws, data leakage in within-domain splits, unverified heuristics in 2023 session segmentation, and statistical overreach regarding small-cluster inference. While Phase 0–6 corrections successfully addressed direct E0 data leakage and introduced rigorous causal lag constraints, an exhaustive audit reveals remaining scientific gaps that must be methodically resolved before submitting to a top-tier IEEE venue.

---

## 1. Fifteen Core Baseline Audit Questions

### Q1: What is the exact research question?
**Formal Formulation:**  
"For downlink throughput forecasting in cellular networks under 3GPP Option 3X EN-DC architectures with structural telemetry missingness, how many target-domain measurement sessions ($K$) are mathematically and empirically necessary to restore distribution-free coverage reliability ($V \le \alpha$, with nominal risk $\alpha=0.10$), and what is the quantitative trade-off with supported throughput capacity ($U$) across within-domain temporal, cross-operator, and joint temporal-operator distribution shifts?"

### Q2: What is the research hypothesis?
**Formal Hypothesis:**  
1. *Point Prediction Failure:* Supervised machine learning throughput estimators (including tree ensembles, deep neural networks, and subset models like BAMMO) trained in a source domain suffer unacceptable empirical SLA violation rates ($V \in [33\%, 62\%]$) under domain shift when used as lower bounds.
2. *Small-Sample Calibration Threshold:* Split conformal calibration with nominal risk $\alpha = 0.10$ mathematically cannot activate on target samples alone when $K < \lceil (K+1)(1-\alpha) \rceil = 9$ sessions (Lemma 1). Below this threshold, falling back to frozen source calibration quantiles ($q_{\text{source}}$) preserves coverage without catastrophic failure.
3. *Missingness-Conditioned Recalibration:* Conditioning conformal calibration on the observed telemetry missingness pattern (Grouped Conformal: LTE-only vs. Dual LTE+NR) or re-weighting source calibration residuals via Bayes-corrected covariate density ratios (Bayes CS-CP) can improve supported capacity ($U$) or maintain validity under distribution shift compared to unweighted global recalibration.

### Q3: What is the claimed novelty?
1. **First Small-Sample Conformal Recalibration Benchmark for Cellular Throughput:** Formulating and empirically evaluating the minimum target budget $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$ required to recover reliable lower bounds under cellular distribution shifts.
2. **Structural Telemetry Missingness Conditioning:** Proposing missingness-aware (grouped) conformal calibration that directly stratifies calibration non-conformity scores by the active radio mask (LTE vs. Dual LTE+NR) rather than relying on arbitrary imputation.
3. **Small-Sample Activation Lemma & Fallback Guarantee:** Formalizing the finite-sample cutoff ($K \ge 9$ for $\alpha=0.10$) and implementing a safe source-fallback hierarchy.
4. **Bayes-Corrected Covariate-Shift Conformal Prediction (CS-CP):** Incorporating the sample-size prior ratio $\frac{N_{\text{src}}}{N_{\text{tgt}}}$ into density ratio estimation to overcome outlier zero-throughput stalls in target calibration.
5. **Operational SLA Economic Loss Framework:** Formalizing an asymmetric economic loss metric $\mathcal{L}_\lambda = \lambda V + (1-\lambda)(1-U)$ parameterized by the regulatory/operator penalty weight $\lambda \in [0, 1]$.

### Q4: What is the contribution compared with existing research?
- **vs. BAMMO (Jacobson et al., 2025):** BAMMO trains partitioned models across observed telemetry feature subsets to produce point forecasts. However, BAMMO optimizes symmetric point loss (MAE/RMSE) and fails to provide risk guarantees, resulting in 41%–62% SLA violation rates under domain shift. Our framework builds risk-controlling prediction intervals on top of telemetry missingness.
- **vs. Covariate-Shift Conformal Prediction (Tibshirani et al., 2019; Barber et al., 2023):** Standard CS-CP assumes accessible target feature density ratios $w(x) = p_{\text{tgt}}(x)/p_{\text{src}}(x)$. Under extreme cellular sample size imbalances (e.g., $N_{\text{src}}=21$ vs. $N_{\text{tgt}}=100+$), uncorrected discriminators yield biased importance weights. We implement Bayes class-prior correction and weight clipping.
- **vs. Adaptive Conformal Inference (Zaffran et al., 2022; Gibbs & Candes, 2021):** ACI adjusts prediction intervals online using step-by-step feedback. We evaluate ACI's tracking performance under cellular non-stationarity and quantify the tracking lag during rapid channel fading.
- **vs. Wireless Conformal Prediction (Sirhan et al., 2024):** Prior wireless conformal prediction works assume stationary, i.i.d. channel conditions for CSI feedback. Our work is the first to benchmark multi-year temporal transfer (2021 $\to$ 2023) and cross-operator transfer with missing secondary carrier indicators.

### Q5: What datasets are used?
Two publicly accessible commercial cellular measurement datasets collected in Rome, Italy:
1. **Dataset 1 (Zenodo Record 8224890):**
   - *Timeframe:* December 2020 – January 2021.
   - *Environment:* Rome drive tests across major arterial routes.
   - *Operators:* Operator 1 (TIM, Italy) and Operator 2 (Vodafone, Italy).
   - *Telemetry:* Synchronized LTE PCell (RSRP, RSRQ, SINR) and 5G NR secondary cell metrics, alongside application-layer throughput.
   - *Causal Forecast Instances:* **503 valid sessions** (150 for Op1, 353 for Op2) spanning 15 calendar collection dates.
2. **Dataset 2 (Zenodo Record 14073311, "5G Chronicles 2023"):**
   - *Timeframe:* March 2023 – July 2023.
   - *Environment:* Rome mobility campaigns across three scenarios: Indoor Stationary (IS), Outdoor Stationary (OD), and Outdoor Walking (OW).
   - *Operators:* Operator 1 (TIM) and Operator 2 (Vodafone).
   - *Telemetry:* Ookla Speedtest DL traces with synchronized QoS tester metrics and radio carrier indicators.
   - *Causal Forecast Instances:* **498 valid sessions** (284 for Op1, 214 for Op2) spanning 12 calendar collection dates.
- **Grand Total:** **1,001 valid causal forecast instances** across 27 distinct calendar collection dates. *(Note: Prior AI reports cited "1,132 sessions"; the true causal count under the strict 60s freshness rule is exactly 1,001).*

### Q6: What is the unit of observation?
An **individual downlink throughput test instance** (forecast step $t$) paired with causal features:
- Preceding session throughput $y_{t-1}$ (Mbps).
- Preceding session duration (seconds).
- Telemetry lag freshness age $\Delta t = t_{\text{start}, t} - t_{\text{end}, t-1} \in [0, 60\text{ s}]$.
- Radio telemetry summary (mean RSRP, RSRQ, SINR for LTE PCell and 5G NR secondary cell) captured strictly within a 60-second causal window prior to $t_{\text{start}, t}$.
- Mobility/environment scenario indicators (IS, OD, OW).

### Q7: What is the unit of independence?
The **measurement campaign date (calendar day cluster)**.  
Consecutive test sessions executed along the same drive route within the same hour share identical base station deployments, multipath fading channels, local weather, and background traffic. Therefore, individual rows are highly autocorrelated. All experimental splits (train, validation, calibration, test) and bootstrap significance tests must partition at the calendar date level.

### Q8: What are the experimental regimes?
Four distinct transfer regimes originating from source domain **Op1 (2020–2021)**:
1. **E0: Within-Domain Benchmark (Op1 2021 $\to$ Op1 2021):**
   - *Train:* 57 sessions (2 dates: 17.12.2020, 04.01.2021).
   - *Validation:* 9 sessions (1 date: 05.01.2021).
   - *Source Calib:* 33 sessions (1 date: 06.01.2021).
   - *Target Calib Pool:* 10 sessions (1 date: 11.01.2021).
   - *Target Test:* 41 sessions (2 dates: 14.01.2021, 27.01.2021).
   - *Budget Availability:* $K \in \{0, 1, 2, 5, 8, 9, 10\}$. ($K=15$ is unavailable because the pool contains 10 sessions).
2. **E1: Campaign Temporal Transfer (Op1 2021 $\to$ Op1 2023):**
   - *Source Development:* 99 train (4 dates), 30 val (2 dates), 21 source calib (1 date).
   - *Target Calib Pool:* 145 sessions (4 dates).
   - *Target Test:* 139 sessions (7 dates).
   - *Budget Availability:* All $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$.
3. **E2: Cross-Operator Transfer (Op1 2021 $\to$ Op2 2021):**
   - *Source Development:* 99 train (4 dates), 30 val (2 dates), 21 source calib (1 date).
   - *Target Calib Pool:* 97 sessions (5 dates).
   - *Target Test:* 256 sessions (8 dates).
   - *Budget Availability:* All $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$.
4. **E3: Joint Temporal and Cross-Operator Shift (Op1 2021 $\to$ Op2 2023):**
   - *Source Development:* 99 train (4 dates), 30 val (2 dates), 21 source calib (1 date).
   - *Target Calib Pool:* 111 sessions (5 dates).
   - *Target Test:* 103 sessions (7 dates).
   - *Budget Availability:* All $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$.

### Q9: What are the proposed methods?
1. **Fallback Split Conformal Calibrator:**
   Computes lower bound $\hat{y}_i^{\text{lower}} = \max(0, \hat{y}_i - q)$, where $q$ is the empirical non-conformity quantile of residuals $R_j = \hat{y}_j - y_j$. If target sample size $N_{\text{cal}} < 9$, safely falls back to $q_{\text{source}} = 14.16\text{ Mbps}$.
2. **Grouped (Missingness-Aware) Conformal Calibrator:**
   Stratifies calibration into subgroups based on observed telemetry: Group 2 (LTE PCell only, 5G NR unobserved) vs. Group 3 (Dual LTE+NR). Evaluates subgroup quantile $q_g$. If subgroup size $< 9$, falls back to global quantile $q$.
3. **Bayes-Corrected Covariate-Shift Conformal Prediction (CS-CP):**
   Estimates importance weights $w(x) = \frac{P(D=1|x)}{1 - P(D=1|x)} \cdot \frac{N_{\text{src}}}{N_{\text{tgt}}}$ using a regularized logistic domain discriminator, with weight clipping $[0.01, 100.0]$ and effective sample size (ESS) tracking.
4. **Adaptive Conformal Inference (ACI):**
   Dynamically adjusts quantile risk level online via $\alpha_{t+1} = \alpha_t + \gamma (\alpha - \mathbf{1}\{y_t < \hat{y}_t^{\text{lower}}\})$ with step size $\gamma = 0.02$.

### Q10: What are the baselines?
- **Point Predictors:**
  1. *Persistence Baseline:* $\hat{y}_t = y_{t-1}$.
  2. *Ridge Regression:* $L_2$-regularized linear model with mean imputation for missing telemetry.
  3. *HistGradientBoostingRegressor:* Histogram-based tree ensemble with native missing-value splitting support (frozen primary predictor).
  4. *BAMMO (Jacobson et al., 2025):* Partitioned tree ensemble trained separately on observed telemetry subsets.
  5. *QuantileGBM:* Gradient boosted trees optimized with pinball loss at $\tau = 0.10$.
  6. *Deep Tabular ResNet:* PyTorch neural architecture with skip connections, trained on NVIDIA GeForce RTX 4060 GPU.
- **Uncertainty / Interval Baselines:**
  1. *Uncalibrated Lower Bound:* $\hat{y}_i^{\text{lower}} = \hat{y}_i$ (standard ML point forecast).
  2. *Direct QuantileGBM:* Pinball loss lower bound without conformalization.
  3. *Global Conformal Calibrator:* Standard split conformal prediction (Vovk et al.) ignoring missingness patterns.

### Q11: What are the evaluation metrics?
1. **Empirical Violation Rate ($V$):**  
   $$V = \frac{1}{N_{\text{test}}} \sum_{i=1}^{N_{\text{test}}} \mathbf{1}\{y_i < \hat{y}_i^{\text{lower}}\}$$  
   *Target:* $V \le \alpha = 0.10$ (90% nominal coverage).
2. **Supported-Rate Fraction ($U$, Utility):**  
   $$U = \frac{\sum_{i=1}^{N_{\text{test}}} \max(0, \hat{y}_i^{\text{lower}})}{\sum_{i=1}^{N_{\text{test}}} y_i}$$  
   Measures fraction of delivered capacity safely committed. Higher is better, provided $V \le \alpha$.
3. **Overcommitment Magnitude ($\text{Overcommit}$):**  
   $$\text{Overcommit} = \frac{\sum_{i=1}^{N_{\text{test}}} \max(0, \hat{y}_i^{\text{lower}} - y_i)}{\sum_{i=1}^{N_{\text{test}}} y_i}$$  
   Measures severe SLA under-delivery normalized by total traffic.
4. **Economic SLA Loss ($\mathcal{L}_\lambda$):**  
   $$\mathcal{L}_\lambda = \lambda V + (1 - \lambda)(1 - U)$$  
   where $\lambda \in [0, 1]$ represents the regulatory/contractual penalty weight.

### Q12: What results are currently supported by actual experiment artifacts?
All results in `results/metrics/` and `results/tables/` are directly reproducible from source data:
- `table1_point_predictors.tex` & `point_predictor_profiles.json`: Source Val MAE values (Persistence: 3.22 Mbps, Ridge: 6.03 Mbps, QuantileGBM: 5.01 Mbps, GPU ResNet: 5.85 Mbps, HistGBM: 11.00 Mbps, BAMMO: 15.46 Mbps).
- `table2_main_benchmark.tex` & `calibration_budget_results.csv`: Complete grid of $V$ and $U$ across E0–E3 for $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$.
- `bootstrap_significance_tests.json`: Paired day-cluster bootstrap tests for $\Delta V$ and $\Delta U$ at $K=10$.
- `online_aci_results.json` & `fig3_aci_adaptation.pdf`: Online ACI tracking across 139 steps in E1.
- `multi_alpha_frontier.json` & `fig4_pareto_frontier.pdf`: Coverage and utility across $\alpha \in [0.01, 0.30]$.
- `sla_cost_analysis.json` & `fig5_sla_cost_curve.pdf`: Economic loss curves across $\lambda \in [0, 1]$.
- `covariate_shift_conformal.json`: CS-CP coverage across E1–E3.
- `ablation_artificial_masking.json`, `ablation_fallback_thresholds.json`, `freshness_sensitivity.json`: Complete parameter sensitivity analyses.

### Q13: Which results are only described in the manuscript (or require alignment)?
- The manuscript in earlier drafts cited "1,132 total sessions"; the actual leak-free dataset yields 1,001 causal forecast sessions.
- In Section V-C, the manuscript asserts that Grouped Conformal outperforms Global Conformal at $K=10$, but glosses over the fact that in E1 and E2, Grouped Conformal violates the nominal risk $\alpha=0.10$ ($V=0.12$ in E1, $V=0.16$ in E2). This is a risk-utility trade-off, not a pure win.
- The manuscript claims BTRC QoS mandates were directly evaluated in Figure 5; in reality, BTRC was used as a motivating regulatory example, while the loss formula is an abstract linear trade-off.

### Q14: Which claims are unsupported or overreaching?
1. **Asymptotic validity of E0 bootstrap:** E0 target test has only 2 unique dates. Resampling 2 clusters cannot yield asymptotic 95% confidence intervals; the resulting $[0.0, 0.0]$ interval is degenerate and must be explicitly labeled *exploratory*.
2. **Dominance of Grouped Conformal:** Grouped Conformal does not uniformly dominate Global Conformal. Global Conformal guarantees conservative coverage ($V=0.07 \le 0.10$ in E1, $V=0.02 \le 0.10$ in E2) at low utility ($U=0.07, 0.02$), while Grouped Conformal trades off coverage ($V=0.12, 0.16$) for higher utility ($U=0.11, 0.19$).
3. **Bangladeshi Field Deployment:** No empirical data from Bangladesh is present in the repository. All data is from Rome, Italy. Any reference to Bangladesh must be strictly positioned as prospective applicability or motivational context.

### Q15: Which limitations could prevent publication?
1. **Small Cluster Counts in Test Sets:** E0 has 2 dates; E1, E2, E3 have 7–8 dates. A skeptical reviewer will challenge whether 7–8 clusters are sufficient for cluster-robust inference. We must discuss small-sample cluster bootstrap properties (e.g., Cameron, Gelbach, Miller 2008).
2. **Ookla Session Segmentation Heuristic:** The 2023 segmentation relies on `(diff < -5.0) & (val < 5.0)`. This heuristic must be scientifically defended and compared against time-gap segmentation.
3. **Target Calibration Stalls in E3:** In E3 at $K \ge 10$, a zero-throughput stall in the calibration set forces $q$ to equal $\hat{y}$, causing utility collapse ($U = 0.006$). The paper must explain why CS-CP succeeds where empirical target calibration collapses.

---

## 2. Comprehensive Claim-Evidence Table

The following table audits every major research claim in the project, categorizing verification status into **Verified**, **Partially Verified**, **Unsupported**, **Contradicted**, or **Not Yet Tested**.

| # | Research Claim | Supporting Evidence | Evidence Location | Verification Status | Required Action |
|---|---|---|---|---|---|
| **C1** | Uncalibrated point throughput predictors fail catastrophically under domain transfer ($V \in [33\%, 62\%]$). | Benchmark results across E0–E3 show uncalibrated $V$: E0=0.44, E1=0.41, E2=0.62, E3=0.33. | `table2_main_benchmark.tex`, `calibration_budget_results.csv` | **Verified** | None. Evidence is solid and reproducible. |
| **C2** | Split conformal prediction cannot activate on target samples alone for $K < 9$ under $\alpha=0.10$. | Conformal quantile formula requires index $\lceil (K+1)(1-\alpha) \rceil \le K$. For $\alpha=0.10$, $\lceil 0.9(K+1) \rceil \le K \iff K \ge 9$. | Lemma 1 proof; identical CSV entries for $K \in \{0, 2, 5, 8\}$. | **Verified** | Retain Lemma 1 proof in manuscript. |
| **C3** | Source-only calibration ($K=0$) bounds violation rates across all transfer domains without target data. | At $K=0$, $q_{\text{source}}=14.16$ yields $V=0.12$ (E0), $0.17$ (E1), $0.16$ (E2), $0.13$ (E3), reducing violations by 60%–74% vs uncalibrated. | `table2_main_benchmark.tex` | **Partially Verified** | Clarify that while $V$ drops dramatically from uncalibrated 41%–62%, it exceeds 10% target due to distribution shift. |
| **C4** | Missingness-aware (grouped) conformal calibration outperforms global calibration at $K=10$. | In E1, Grouped $U=0.11$ vs Global $0.07$ ($\Delta U = +0.037$); in E2, Grouped $U=0.19$ vs Global $0.02$ ($\Delta U = +0.171$). However, Grouped $V=0.12$ (E1) and $0.16$ (E2) exceed $\alpha=0.10$, whereas Global $V=0.07$ and $0.02$ satisfy $\alpha$. | `table2_main_benchmark.tex`, `bootstrap_significance_tests.json` | **Contradicted (as uniform dominance); Partially Verified (as risk-utility trade-off)** | Reframe claim: Grouped calibration trades conservative overcoverage for higher utility. Discuss honestly as a risk-utility trade-off. |
| **C5** | E0 bootstrap delivers statistically significant 95% confidence intervals ($\Delta V = 0, \Delta U = 0$). | E0 test partition has only 2 distinct calendar dates. The 2-cluster bootstrap resamples only pairs from 2 points, yielding degenerate zero width $[0.0, 0.0]$. | `results/diagnostics/split_summary.json`, `bootstrap_significance_tests.json` | **Unsupported (as asymptotic inference)** | Explicitly designate E0 bootstrap as exploratory; explain 2-cluster degeneracy in text and limitations. |
| **C6** | Bayes-corrected CS-CP overcomes target outlier stalls in E3, maintaining valid coverage ($V=0.000$) with non-zero utility ($U=0.010$). | CS-CP re-weights source residuals, sustaining $U=0.010$ vs $0.006$ for target conformal at $K=10$, with $V=0.000$. | `covariate_shift_conformal.json` | **Verified** | Highlight in Section V and Section VI as solution to target sample corruption. |
| **C7** | Online Adaptive Conformal Inference (ACI) dynamically recovers nominal 90% coverage under non-stationary drift. | ACI running with $\gamma=0.02$ over 139 steps in E1 achieves average coverage 89.2% ($V=0.108$), closely tracking nominal $\alpha=0.10$. | `online_aci_results.json`, `fig3_aci_adaptation.pdf` | **Verified** | Retain Figure 3 and analysis in manuscript. |
| **C8** | 60 seconds is the optimal lookback horizon for radio telemetry extraction. | Freshness ablation across 30s, 60s, 120s shows 30s has elevated violations ($V=0.188$ in E2, $0.302$ in E1), while 60s and 120s stabilize at $V \approx 0.086$ and $0.122$. | `freshness_sensitivity.json` | **Verified** | Retain sensitivity analysis in Section V. |
| **C9** | Proposed method minimizes total operational loss under BTRC QoS mandates. | Loss formula $\mathcal{L}_\lambda = \lambda V + (1-\lambda)(1-U)$ is an abstract economic parameterization, not an official BTRC formula. | `sla_cost_analysis.json`, `manuscript.tex` line 524 | **Unsupported (as literal BTRC mandate)** | Remove claim of literal BTRC formula; reframe as "under illustrative regulatory penalty regimes such as BTRC QoS benchmarks". |
| **C10** | The benchmark is evaluated on 1,132 commercial sessions. | Current leak-free, causality-filtered dataset contains 503 sessions (2021) + 498 sessions (2023) = 1,001 sessions. | `loader.py`, diagnostic run output | **Contradicted** | Update all manuscript and README instances to "1,001 verified causal sessions". |
| **C11** | 2023 Ookla test segmentation accurately extracts discrete speedtest instances via reset heuristic `(diff < -5) & (val < 5)`. | Code uses heuristic. Total extracted sessions = 498. Heuristic has not been cross-validated against time-gap segmentation. | `src/data/loader.py` lines 220–222 | **Not Yet Tested (Scientifically)** | Complete Stage B session segmentation audit and validation. |
| **C12** | Deep Tabular ResNet executed on NVIDIA RTX 4060 GPU achieves efficient throughput prediction (Val MAE 5.85 Mbps, 0.535s execution). | PyTorch ResNet implementation verified in `src/models/neural.py`; profiling results recorded in JSON. | `point_predictor_profiles.json`, `table1_point_predictors.tex` | **Verified** | Retain GPU profiling in Section V-A. |

---

## 3. Deep Dive into Critical Vulnerabilities

### 3.1 Unfavorable and Mixed Results: The Grouped Conformal Dilemma
In transfer regimes E1 and E2 at budget $K=10$:
- **In E1 (Temporal Transfer):**
  - Global Conformal: $V = 0.072 \le 0.10$, $U = 0.073$.
  - Grouped Conformal: $V = 0.122 > 0.10$, $U = 0.110$.
- **In E2 (Cross-Operator Transfer):**
  - Global Conformal: $V = 0.023 \le 0.10$, $U = 0.018$.
  - Grouped Conformal: $V = 0.164 > 0.10$, $U = 0.189$.

**Scientific Assessment:**  
A superficial reading might consider this an unfavorable result for the proposed method because $V$ exceeds the nominal 10% risk bound. However, scientifically, Global Conformal achieves $V \le 0.10$ by becoming **hyper-conservative**: in E2, Global Conformal commits only 1.8% of network capacity ($U = 0.018$), which is practically useless for bandwidth reservation! Grouped Conformal unlocks 18.9% capacity ($10.5\times$ higher utility) but incurs a 16.4% violation rate.  
**Resolution:** This trade-off must be reported completely and transparently. We will formulate this as the **Conservative Coverage vs. Operational Utility Dilemma** under small calibration budgets, showing how operators can choose between conservative global bounds or higher-utility subgroup intervals based on their SLA penalty weight $\lambda$.

### 3.2 Small-Cluster Statistical Limitations
- In E0, the test suffix has only $N_{\text{clusters}} = 2$ calendar dates.
- In E1, E2, E3, the target test partitions have 7, 8, and 7 calendar dates, respectively.

**Scientific Assessment:**  
Standard cluster bootstrap asymptotic theory requires $G \to \infty$ (typically $G \ge 30$–50 clusters). With $G \in [2, 8]$, wild cluster bootstrap or standard cluster bootstrap can suffer from under-coverage or point degeneracy.  
**Resolution:**  
1. Explicitly document cluster sample sizes ($G=2$ for E0, $G \in [7, 8]$ for E1–E3) in all table captions and methodology text.
2. Formally declare that E0 bootstrap results are descriptive/exploratory.
3. Cite Cameron, Gelbach, and Miller (2008) regarding small-cluster inference properties in observational telemetry.

### 3.3 2023 Session Segmentation Validation (Phase 4 / Stage B Preview)
The current 2023 loader in `src/data/loader.py` identifies test boundaries via:
```python
is_reset = (sub['val_mbps'].diff() < -5.0) & (sub['val_mbps'] < 5.0)
sub['test_id'] = is_reset.cumsum()
```
**Scientific Assessment:**  
This heuristic assumes every test begins below 5 Mbps and drops sharply from above 5 Mbps. Potential failure modes:
1. Multi-stage Ookla tests with sudden rate drops during active transfer could be falsely split into multiple sessions.
2. Back-to-back tests separated by idle periods where the rate decayed gradually might not trigger a $<-5$ Mbps step.  
**Resolution:** In Stage B, we will audit inter-session time gaps $\Delta t_{\text{idle}}$, active test durations ($\sim 15$s standard Ookla duration), and validate the segmentation against physical drive-test timestamps.

### 3.4 Framing of Bangladesh Telecommunications Context
All empirical drive-test data originates from Rome, Italy (Zenodo 8224890 and 14073311).  
**Scientific Assessment:**  
Claiming that the models were trained on or directly evaluate Bangladeshi network infrastructure is factually false and would be an instant desk-reject for research integrity.  
**Resolution:**  
1. Clearly state in the Abstract, Introduction, and Methodology that all empirical experiments utilize verified European 5G/4G measurement campaigns from Rome.
2. Frame Bangladesh (Grameenphone, Banglalink, Robi, Teletalk) and BTRC QoS guidelines strictly as an **exemplar use-case for prospective transfer**: showing how emerging telecom markets with high density and resource constraints can leverage recalibration with minimal drive testing ($K=9$ sessions).

---

## 4. Stage A Audit Checklist and Sign-off

- [x] Repository thoroughly inspected across code, data, tests, scripts, and documentation.
- [x] All 15 core baseline research questions answered in technical depth.
- [x] Comprehensive Claim-Evidence Table constructed with 12 major claims classified.
- [x] Discrepancies between manuscript text, code, and artifacts documented.
- [x] Unfavorable/mixed results ($V > 0.10$ for Grouped at $K=10$) analyzed and framed as a risk-utility trade-off.
- [x] Statistical limitations of small cluster counts ($G=2$ in E0) documented.
- [x] True sample size established at exactly 1,001 causal sessions.
- [x] Framing of Bangladesh telecom context corrected to prospective motivation.

**Stage A Verdict:** Complete and rigorous. Ready to proceed to **Stage B: Data Integrity and Session Segmentation Validation**.

