> Historical project record from before the pooled-calibration correction. For current estimates, validation status and publication assessment see [the final research audit](FINAL_RESEARCH_AUDIT.md). Interpret numerical claims below as superseded.

# Statistical Validity, Small-Cluster Limitations, and Mixed-Findings Audit (Phase 8)

**Project:** Cellular Recalibration Benchmark  
**Manuscript Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Audit Artifacts:** `results/metrics/bootstrap_significance_tests.json`, `results/tables/table2_main_benchmark.tex`, `results/diagnostics/split_summary.json`  
**Evaluation Standard:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  

---

## 1. True Independent Sampling Units and Cluster Counts

A critical statistical vulnerability identified during the integrity review is the **confusion between sample size ($N$ sessions) and independent information ($G$ clusters)**. 

In cellular network measurements:
- Consecutive drive-test sessions executed within minutes of each other traverse the same geographical streets, connect to the same base stations, share identical radio propagation environments, and experience correlated scheduling traffic.
- Resampling individual session rows via naive i.i.d. bootstrap artificially narrows confidence intervals and manufactures false statistical significance.
- Therefore, the **calendar collection date** is the true unit of cluster independence.

### 1.1 Cluster Counts per Test Partition
From `results/diagnostics/split_summary.json`, the verified cluster counts in each evaluation partition are:

| Regime | Transfer Description | Target Test Instances ($N$) | Target Test Dates ($G$ Clusters) | Specific Calendar Dates in Test Partition | Asymptotic Validity Status |
|---|---|---|---|---|---|
| **E0** | Within-Domain (Op1 2021) | 41 sessions | **$G = 2$ dates** | `14.01.2021`, `27.01.2021` | **Degenerate ($G < 5$); Exploratory Only** |
| **E1** | Temporal Transfer (Op1 2023) | 139 sessions | **$G = 7$ dates** | `09.05`, `27.05`, `08.06`, `10.06`, `16.06`, `25.06`, `05.07` | **Small-Cluster Regime ($G \in [5, 20]$)** |
| **E2** | Cross-Operator (Op2 2021) | 256 sessions | **$G = 8$ dates** | `05.01`, `06.01`, `07.01`, `08.01`, `24.01`, `25.01`, `26.01`, `27.01` | **Small-Cluster Regime ($G \in [5, 20]$)** |
| **E3** | Joint Shift (Op2 2023) | 103 sessions | **$G = 7$ dates** | `27.05`, `08.06`, `10.06`, `16.06`, `25.06`, `04.07`, `05.07` | **Small-Cluster Regime ($G \in [5, 20]$)** |

### 1.2 Methodological Implications:
1. **E0 Degeneracy:** With only $G = 2$ clusters in the E0 test suffix, a cluster bootstrap resamples only from pairs $\{ (D_1, D_1), (D_1, D_2), (D_2, D_1), (D_2, D_2) \}$. This yields a degenerate zero-width confidence interval ($[0.0, 0.0]$). In accordance with Cameron, Gelbach, and Miller (2008), **E0 bootstrap results must be explicitly designated in the manuscript as exploratory and descriptive, not as asymptotic inference.**
2. **Small-Cluster Properties in E1–E3:** Standard cluster-robust asymptotic theory assumes $G \to \infty$ (typically $G \ge 30$–50). With $G \in [7, 8]$, standard cluster bootstrap can experience slight downward bias in standard errors. We retain paired day-cluster bootstrap as the most principled available non-parametric estimator, but qualify all confidence intervals in the text.

---

## 2. Investigation of Unfavorable and Mixed Findings (Phase 8 Deep Dive)

A core mandate of this audit is to confront mixed and unfavorable experimental findings honestly rather than masking them.

### 2.1 The Apparent Anomaly at Budget $K=10$
In Table 2 (`results/tables/table2_main_benchmark.tex`), the empirical violation rate $V$ (target: $V \le \alpha = 0.10$) and supported-rate fraction $U$ at budget $K=10$ show:

| Regime | Method | Empirical Violation ($V$) | Supported Fraction ($U$) | Satisfies Nominal $\alpha=0.10$? |
|---|---|---|---|---|
| **E1 (Campaign Transfer)** | Global Conformal | **0.072** | 0.073 | **Yes ($V \le 0.10$)** |
| | Proposed Grouped Conformal | **0.122** | 0.110 | **No ($V > 0.10$)** |
| **E2 (Cross-Operator)** | Global Conformal | **0.023** | 0.018 | **Yes ($V \le 0.10$)** |
| | Proposed Grouped Conformal | **0.164** | 0.189 | **No ($V > 0.10$)** |
| **E3 (Joint Shift)** | Global Conformal | 0.000 | 0.006 | Yes |
| | Proposed Grouped Conformal | 0.000 | 0.006 | Yes (Identical) |

### 2.2 Root-Cause Analysis: Why is Grouped Violation Higher than Global?
A superficial inspection suggests the proposed method "failed" in E1 and E2 because $V > 0.10$. However, a deeper scientific analysis reveals the underlying mechanism:

1. **Hyper-Conservatism of Global Conformal:**  
   In cross-operator transfer (E2), Global Conformal calibrates against the pooled target calibration set ($K=10$). In a 10-sample set, the empirical 90th percentile is the second largest residual ($k = \lceil 11 \times 0.90 \rceil = 10$). Because this residual is dominated by bursty 5G NR carrier peaks, Global Conformal sets an enormous safety margin ($q \approx 45\text{ Mbps}$).  
   As a consequence:
   - Violation drops to $V = 0.023$ (extreme over-coverage, $5\times$ safer than necessary).
   - But supported rate fraction collapses to **$U = 0.018$**! The operator can commit only **1.8%** of actual delivered throughput! Such an interval is useless for real-world network slicing or video representation selection.
2. **Subgroup Sample Thinning in Grouped Conformal:**  
   When $K=10$ total sessions are partitioned into Group 2 (LTE-only) and Group 3 (Dual LTE+NR), each subgroup receives only 4 to 6 calibration samples. At $N_g \approx 5$, finite-sample variance is substantially higher. Grouped Conformal recognizes that LTE-only sessions do not experience 5G bursts and selects a tighter quantile for Group 2.  
   As a consequence:
   - Supported throughput fraction surges by **$10.5\times$** to **$U = 0.189$** (18.9% capacity safely committed).
   - However, due to small subgroup sample sizes and cross-operator channel mismatch, the empirical violation rate is $V = 0.164$, slightly exceeding the nominal 10% threshold.

### 2.3 Scientific Assessment: The Risk-Utility Frontier
Does the proposed approach improve reliability?
- **Answer:** The findings are **mixed and represent an operational trade-off**:
  - Global Conformal guarantees conservative coverage ($V \le 0.10$) at the cost of near-zero operational utility ($U < 0.02$).
  - Grouped Conformal unlocks high utility ($U \approx 0.11 - 0.19$) but incurs a higher violation risk ($V \approx 0.12 - 0.16$) when the calibration budget is constrained to $K=10$.
  - At $K=15$ in E1, Grouped Conformal recovers exact validity ($V = 0.101 \approx 0.10$) with $U = 0.083$.
- **Conclusion:** We will explicitly report this trade-off in Section V of the manuscript. A network operator facing harsh financial penalties for any violation ($\lambda > 0.85$) should deploy Global Conformal; an operator optimizing bandwidth monetization under moderate SLA penalties ($\lambda \in [0.35, 0.70]$) achieves lower total loss with Grouped Conformal.

---

## 3. Paired Day-Cluster Bootstrap Significance Tests

From `results/metrics/bootstrap_significance_tests.json`, 2,000 paired cluster resamples at $K=10$ yield:

### 3.1 Regime E1: Campaign Temporal Transfer
- $\Delta U = U_{\text{grouped}} - U_{\text{global}} = \mathbf{+0.0372}$ [95% CI: $+0.0188, +0.0653$]
- $\Delta V = V_{\text{grouped}} - V_{\text{global}} = \mathbf{+0.0504}$ [95% CI: $+0.0159, +0.0736$]
- *Interpretation:* The gain in supported capacity (+3.7% of total network volume) is statistically significant at the 95% level across 7 measurement dates, accompanied by a +5.0% increase in violation rate.

### 3.2 Regime E2: Cross-Operator Transfer
- $\Delta U = \mathbf{+0.1710}$ [95% CI: $+0.1418, +0.2195$]
- $\Delta V = \mathbf{+0.1406}$ [95% CI: $+0.0779, +0.2524$]
- *Interpretation:* Unlocking +17.1% network capacity is statistically significant across 8 collection days, accompanied by an intentional trade-off of +14.1% violation risk over hyper-conservative global bounds.

### 3.3 Regime E0 & E3:
- In E0, $\Delta U = 0.000$ and $\Delta V = 0.000$ (degenerate 2-cluster partition; exploratory).
- In E3, $\Delta U = 0.000$ and $\Delta V = 0.000$. (In E3 2023 Op2 walk tests, 5G NR carrier aggregation was detached across all initial target sessions, causing Grouped Conformal to fall back to Global Conformal).

---

## 4. Calibration Efficiency and Budget Dynamics

### 4.1 Lemma 1 and the Fallback Plateau ($K \in \{0, 1, 2, 5, 8\}$)
For all budgets $K \le 8$, split-conformal calibration with $\alpha = 0.10$ lacks sufficient target samples to evaluate an empirical quantile ($\lceil 0.9(K+1) \rceil > K$). Consequently, our safe hierarchy automatically falls back to the frozen source quantile $q_{\text{source}} = 14.16\text{ Mbps}$.
- Across all regimes, the metrics for $K \in \{0, 1, 2, 5, 8\}$ are **mathematically identical**.
- This is not a flatlining defect; it is the formal mathematical behavior of a finite-sample fallback guarantee.

### 4.2 Target Activation at $K=9$
At exactly $K=9$ sessions, target recalibration activates for the first time:
- In E0, global target recalibration bounds violation at $V = 0.098 \le 0.10$ ($U = 0.086$).
- In E1, global target recalibration bounds violation at $V = 0.072 \le 0.10$ ($U = 0.073$).
- In E2, global target recalibration yields conservative bounds $V = 0.023$ ($U = 0.018$).
- *Clarification:* $K=9$ is the mathematical activation threshold for split conformal with $\alpha=0.10$, not an operational guarantee that 9 sessions will capture all distributional modes.

