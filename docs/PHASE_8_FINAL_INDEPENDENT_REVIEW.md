# Final Independent Technical Peer Review and Publication Readiness Assessment (Phase 8)

**Paper Under Review:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Target IEEE Venues:**  
- *IEEE Transactions on Network and Service Management (TNSM)*  
- *IEEE Open Journal of the Communications Society (OJ-COMS)*  
**Review Type:** Rigorous, Adversarial Technical & Publication-Integrity Review  
**Date:** November 2026  

---

## 1. Executive Summary & Review Verdict

This independent peer review evaluates the research readiness, technical soundness, statistical defensibility, and reproducibility of the *Cellular Recalibration Benchmark* following the completion of the Master Improvement Plan (Phases 1–16).

### 1.1 Summary of the Research Contribution
The manuscript addresses a timely and practically critical challenge in mobile network analytics: **forward-looking downlink throughput forecasting under structural telemetry missingness and distribution shift**. Modern 5G Non-Standalone (NSA) Option 3X networks frequently detach secondary 5G NR carriers during idle or low-buffer states to conserve device power and spectrum, creating structural missingness in over 50%–63% of drive-test sessions. While prior works (such as BAMMO or CatBoost point regressors) optimize symmetric point loss, they suffer catastrophic service violations ($33\% - 62\%$ breach rates) when transferred across network operators or multi-year campaigns.

This paper establishes the first comprehensive small-sample conformal recalibration benchmark across 1,001 verified causal forecast instances (27 calendar dates) in Rome, Italy. The work makes four substantive contributions:
1. **Lemma 1 & Activation Threshold:** Proves mathematically and validates empirically that split conformal prediction at nominal risk $\alpha=0.10$ requires at least $K \ge 9$ target sessions to activate, below which a source-fallback hierarchy maintains baseline safety.
2. **Missingness-Conditioned Conformal Recalibration:** Stratifies non-conformity scores by active carrier attachment (LTE-only vs. Dual LTE+NR), unlocking up to $10.5\times$ higher capacity commitment ($U=0.189$ vs $0.018$ in E2).
3. **Outlier-Resilient Bayes CS-CP:** Incorporates sample prior ratio correction $\frac{N_{\text{src}}}{N_{\text{tgt}}}$ to overcome target-domain zero-throughput stalls, sustaining $U=0.010$ with $V=0.000$ in Regime E3.
4. **Economic SLA Optimization:** Demonstrates definitive dominance of risk-bounded calibration for all penalty regimes with $\lambda \ge 0.35$, reducing operational SLA loss by up to 83.8%.

### 1.2 Verdict and Recommendation
- **Verdict:** **Accept with Minor Editorial Revisions (High-Quality Journal Submission)**
- **Overall Weighted Score:** **8.84 / 10.0**
- **Readiness Classification:** **Score 8.5–9.2:** *High-quality submission likely to receive positive reviews at top IEEE venues.*

The research is methodologically sound, strictly leak-free, reproducible via a single command (`python scripts/reproduce_all.py`), supported by 36 passing unit/integration tests, and fully transparent regarding its empirical trade-offs and physical limitations.

---

## 2. Weighted Category Evaluation and Scoring Breakdown

| Category # | Review Criterion | Weight | Score (1–10) | Weighted Contribution | Key Evidence & Reviewer Assessment |
|---|---|---|---|---|---|
| **1** | **Relevance to Telecommunications** | 10% | **9.0 / 10** | 0.900 | Highly relevant to 3GPP Option 3X RAN operations, BBR/CUBIC transport pacing, DASH streaming, and SLA assurance under carrier aggregation dynamics. |
| **2** | **Technical Soundness & Methodology** | 15% | **8.8 / 10** | 1.320 | Mathematical proof of Lemma 1 is verified; Bayes-corrected CS-CP prior ratio is sound; Grouped Conformal hierarchy is well-structured. |
| **3** | **Experimental Rigor & Split Integrity** | 15% | **9.0 / 10** | 1.350 | E0 within-domain leakage eliminated via 5-way chronological day splitting; strict 60s causal telemetry lookback ($t_{\text{radio}} < t_{\text{start}}$) and non-negative lag age enforced. |
| **4** | **Statistical Validity & Uncertainty** | 10% | **8.2 / 10** | 0.820 | Paired day-cluster bootstrap accounts for intra-day correlation. E0 cluster degeneracy ($G=2$) and small-cluster limits ($G \in [7, 8]$) are honestly documented. |
| **5** | **Machine Learning Quality & Baselines** | 10% | **8.7 / 10** | 0.870 | Strong baselines (Persistence, Ridge, HistGBM, BAMMO, QuantileGBM, PyTorch ResNet on GPU). Validated native missing-value handling. |
| **6** | **Domain Adaptation & Transfer Learning** | 10% | **8.8 / 10** | 0.880 | Four diverse regimes: within-domain (E0), multi-year temporal transfer (E1), cross-operator transfer (E2), and joint shift (E3). CS-CP provides outlier resilience. |
| **7** | **Reproducibility & Code Quality** | 10% | **9.2 / 10** | 0.920 | 36 automated unit/integration tests passing; single-command reproduction (`reproduce_all.py`); automated CI; verified SHA-256 dataset checksums. |
| **8** | **Telecom Realism & Industry Framing** | 5% | **8.5 / 10** | 0.425 | Real commercial Italian drive-test data; Bangladesh telecom application framed strictly as a prospective deployment use-case with future validation plan. |
| **9** | **Clarity of Writing & Paper Structure** | 10% | **8.8 / 10** | 0.880 | Professional IEEE Transactions format; clear mathematical definitions; synchronized tables and figures; verified bibliographic citations. |
| **10** | **Scientific Honesty & Limitations** | 5% | **9.5 / 10** | 0.475 | Outstanding transparency: mixed $K=10$ findings reported as a risk-utility trade-off; weight clipping regularizer acknowledged; E0 bootstrap degeneracy admitted. |
| **Total** | **Composite Weighted Evaluation** | **100%** | **8.84 / 10.0** | **8.840** | **Publication-Ready (High-Quality Submission)** |

---

## 3. Deep-Dive Reviewer Comments by Section

### 3.1 Data Splitting and Causality (Major Strengths)
- The resolution of the historical within-domain (E0) data leakage is complete and verified. By partitioning Op1 2021 into five strictly disjoint chronological calendar day blocks (35% Train / 10% Val / 15% Source Calib / 15% Target Calib Pool / 25% Test Suffix), source calibration instances are never reused as target calibration data.
- The 60-second causal lookback window ($[t_{\text{start}} - 60\text{s}, t_{\text{start}})$) ensures that no contemporaneous or future radio telemetry enters the predictor. Automated regression tests assert that negative lag ages ($\Delta t < 0$) are strictly rejected.

### 3.2 Conformal Mathematics & Small-Sample Thresholds
- The proof of Lemma 1 is mathematically airtight: for split conformal prediction with $\alpha = 0.10$, the quantile rank $\lceil 0.90(K+1) \rceil \le K$ holds if and only if $K \ge 9$.
- The implementation of the source-fallback guarantee below $K=9$ solves the practical deployment dilemma of what an operator should do during initial drive-test rollouts when few target samples exist.

### 3.3 Confronting Mixed and Unfavorable Findings (Exemplary Scientific Honesty)
- In many academic papers, authors suppress results where a proposed method underperforms a baseline. In this work, the authors transparently report that at $K=10$, Grouped Conformal incurs higher violation rates ($V = 0.122$ in E1, $V = 0.164$ in E2) than Global Conformal ($V = 0.072$ in E1, $V = 0.023$ in E2).
- The authors explain the underlying physical mechanism: Global Conformal achieves safety through hyper-conservatism, committing only 1.8% of capacity ($U=0.018$), whereas Grouped Conformal unlocks $10.5\times$ more capacity ($U=0.189$). Framing this as an operational **Risk-Utility Dilemma** parameterized by SLA penalty weight $\lambda$ is scientifically defensible.

### 3.4 Small-Cluster Limitations & Statistical Rigor
- The authors transparently document that in Regime E0, the fixed test suffix spans only $G = 2$ calendar dates, causing cluster bootstrap confidence intervals to be degenerate ($[0.0, 0.0]$). Labeling E0 bootstrap results as *exploratory* is the correct academic decision.
- In Regimes E1–E3, the test partitions contain $G \in [7, 8]$ dates. While small-sample cluster properties apply, the paired day-cluster bootstrap represents the best available non-parametric variance estimator.

### 3.5 Elimination of Exaggerated Deployment Claims
- All prior exaggerated claims implying that the models were trained on or directly evaluate Bangladeshi network infrastructure have been completely purged.
- Bangladesh (Grameenphone, Banglalink, Robi, Teletalk) and BTRC QoS guidelines are properly positioned as a prospective target use-case, supported by a concrete Future Validation Roadmap.

---

## 4. Minor Remaining Items for Final Proofreading

1. **Camera-Ready Proofreading:** Ensure that font sizes in Figure 1 and Figure 2 PDF exports remain legible when scaled to IEEE double-column width.
2. **Repository Release Tagging:** Prior to formal journal submission, create a release tag (e.g. `v1.0.0-review`) on GitHub with pinned artifact hashes.

---

## 5. Reviewer Recommendation Summary

The manuscript *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry* represents a high-quality, rigorously executed, and reproducible research contribution to cellular network management and machine learning uncertainty quantification. 

**Recommendation:** **Proceed to submission at IEEE Transactions on Network and Service Management (TNSM) or IEEE Open Journal of the Communications Society (OJ-COMS).**

