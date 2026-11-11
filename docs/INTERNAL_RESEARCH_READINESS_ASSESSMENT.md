# Internal Research Readiness and Technical Audit Assessment

**Project:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Target IEEE Venues:**  
- *IEEE Transactions on Network and Service Management (TNSM)*  
- *IEEE Open Journal of the Communications Society (OJ-COMS)*  
**Assessment Type:** Internal Pre-Submission Readiness Audit and Technical Integrity Verification  
**Date:** November 2026  

---

## 1. Executive Summary & Audit Scope

This document provides an internal technical readiness and research integrity audit of the *Cellular Recalibration Benchmark* following the completion of full research integrity remediations (Phases 1–16).

> [!IMPORTANT]
> **Audit Status Clarification:** This document is an **internal author audit and pre-submission technical readiness review**. It does not substitute for independent editorial peer review conducted by IEEE journals or conferences. All readiness evaluations represent internal technical audits verifying code correctness, data split independence, empirical consistency, and manuscript alignment against IEEE quality standards.

### 1.1 Summary of the Research Contribution
The benchmark investigates a central challenge in commercial mobile network analytics: **downlink throughput forecasting under structural telemetry missingness and multi-dimensional distribution shift**. Modern 5G Non-Standalone (NSA) Option 3X networks frequently detach secondary 5G NR carriers during idle or low-buffer states, causing missing radio telemetry in 53%–63% of drive-test sessions. While standard point regressors optimize symmetrical losses, they suffer catastrophic violation rates (33%–62%) under cross-operator and multi-year transfer.

This project establishes a rigorous, leak-free small-sample conformal recalibration benchmark on 1,001 verified causal forecast pairs (27 calendar collection dates) in Rome, Italy:
1. **Lemma 1 (Finite Order-Statistic Activation Cutoff):** Demonstrates that unstratified split conformal calibration at $\alpha=0.10$ mathematically requires at least $K \ge 9$ target sessions ($\lceil (K+1)(1-\alpha) \rceil \le K$), activating empirical quantiles sharply at $K=9$ while smaller budgets rely on principled source fallbacks.
2. **Missingness-Conditioned Conformal Recalibration:** Stratifies non-conformity scores by active carrier attachment (LTE-only vs. Dual LTE+NR), recovering up to $10.5\times$ higher capacity commitment ($U=0.189$ vs $0.018$ in E2) at the cost of modest violation trade-offs ($V=0.164$).
3. **Outlier-Resilient Bayes CS-CP:** Evaluates Covariate-Shift Conformal Prediction under both strict non-transductive (Protocol A) and transductive (Protocol B) regimes with Kish's Effective Sample Size (ESS) tracking, overcoming target zero-throughput stalls in Regime E3.
4. **Operational SLA Economic Optimization:** Demonstrates dominance of risk-bounded calibration for penalty regimes with $\lambda \ge 0.35$, reducing operational SLA losses by 25.7% to 83.8%.

---

## 2. Technical Audit Verification Summary

| Category # | Verification Dimension | Technical Evidence | Audit Finding |
|---|---|---|---|
| **1** | **Split Independence & E0 Leak-Free Partitioning** | 5-way disjoint chronological day splitting (35/10/15/15/25% days). Mandatory `experiment_type` parameter enforced in `create_experiment_splits()`. Zero date or session overlap verified by automated integration tests. | **VERIFIED** |
| **2** | **Causal Telemetry Freshness & Pre-Validation** | Strict 60s lookback gate ($\Delta t \le 60$ s) and causal radio window ($t_{\text{radio}} < t_{\text{start}}$). Pre-segmentation numeric cleaning (`clean_numeric`) strictly filters NaN and negative throughput across all rows. | **VERIFIED** |
| **3** | **2023 Session Segmentation Validation** | Full 43-file Ookla trace audit comparing threshold reset, relative drop, and active burst. High cross-strategy correlation ($r = 0.8365$), verified non-negative throughput (`non_negative_verified: true` across 100% files), median session duration 76.0 s recorded in `results/diagnostics/session_segmentation_comparison.json`. | **VERIFIED** |
| **4** | **Conformal Calibration & Dual CS-CP Protocol** | Covariate-Shift Conformal Prediction evaluated under both Protocol A (Strict Non-Transductive on calibration pool) and Protocol B (Transductive on test covariates) with Kish's ESS tracking and tight `[0.1, 10.0]` vs wide `[0.01, 100.0]` clipping. | **VERIFIED** |
| **5** | **Reproducibility & Test Suite** | 37 automated unit and integration tests passing in 74 seconds. Verified cryptographic SHA-256 checksums matching real raw archives recorded in `data/metadata/acquisition_manifest.json` and `results/runs/experiment_manifest.json`. | **VERIFIED** |
| **6** | **Scientific Transparency & Limitations** | Qualified bootstrap inference ($G=2$ exploratory in E0, $G \in [7, 8]$ in E1–E3). Reframed Bangladesh text as prospective external motivation. Honest reporting of $K=10$ grouped coverage ($V=0.122$ in E1, $0.164$ in E2) as a risk-utility trade-off. | **VERIFIED** |

---

## 3. Submission Readiness Recommendation

The research benchmark satisfies all technical prerequisites for peer-reviewed IEEE submission:
- Source code, data loaders, split protocols, and models are fully aligned with the manuscript.
- Cryptographic manifests, diagnostics, figures, and LaTeX tables are fully synchronized and reproducible.
- Empirical limitations, cluster counts, and trade-offs are presented with scientific honesty.

