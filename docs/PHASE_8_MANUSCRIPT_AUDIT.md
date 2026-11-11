# Comprehensive Manuscript Audit and Alignment Report (Phase 8)

**Project:** Cellular Recalibration Benchmark  
**Manuscript Reviewed:** `paper/manuscript.tex`, `paper/manuscript.md`  
**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Target Submission:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  
**Evaluation Standard:** Adversarial Peer-Review Audit for IEEE Journal Quality  

---

## 1. Section-by-Section Manuscript Audit

### 1.1 Title
- **Current Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*
- **Assessment:** **Strong and Defensible.** The title directly reflects the central research inquiry without overpromising universal optimality or claiming production deployment. It targets the core trade-off between target calibration sample size ($K$) and forecast reliability under distribution shift and missing telemetry.

### 1.2 Abstract
- **Audit Findings:**
  - *Telemetry Missingness:* The abstract correctly notes that 5G NR secondary carrier indicators are absent in 63.4% of sessions in the 2021 campaign (verified in `results/diagnostics/data_quality_audit.json`).
  - *Sample Size Harmonization:* The abstract must explicitly state the exact leak-free causal sample size: **1,001 causal forecast instances** across **27 calendar dates** (503 from 2021, 498 from 2023), eliminating any legacy references to uncurated counts (e.g. "1,132 sessions").
  - *Numerical Precision:* Verified that point predictor violation rates (33%–62%), source calibration quantile ($q_{\text{source}} = 14.16\text{ Mbps}$), Lemma 1 activation threshold ($K=9$), and economic loss reduction (25.7%–57.9%) match final experiment artifacts exactly.
  - *Tone Calibration:* Replaced any absolute claims of "guaranteeing reliability under arbitrary shifts" with precise mathematical statements: "recovering distribution-free validity under bounded distribution shift with safe source-fallback guarantees."

### 1.3 Introduction
- **Audit Findings:**
  - Clearly articulates why cellular throughput prediction matters for transport pacing (BBR/CUBIC), video streaming (DASH), and SLA commitment.
  - Explains the physical origin of structural missingness in 3GPP Option 3X EN-DC (dynamic Secondary Node Addition/Release).
  - Explicitly states the research gap: prior works (e.g. Lumos5G, BAMMO) focus on point forecasting minimizing symmetric error, leaving operational networks unprotected against catastrophic SLA breaches during cross-operator or multi-year transfer.
  - States the exact contributions cleanly.

### 1.4 Background and Related Work
- **Audit Findings:**
  - Positions the work systematically against 4 literature axes: (1) 5G performance benchmarks (Kousias et al., Caso et al.), (2) missing data modeling (BAMMO, Zaffran et al.), (3) conformal prediction under distribution shift (Tibshirani et al. CS-CP, Gibbs & Candès ACI), and (4) uncertainty in telecommunications (Sirhan).
  - Contrasts BAMMO: BAMMO optimizes symmetric point loss and incurs 41%–62% SLA violation rates under domain transfer; our framework adds distribution-free risk bounds on top of missing telemetry.

### 1.5 Problem Formulation & Lemma 1
- **Audit Findings:**
  - Signed non-conformity score $R_i = \hat{y}_i - y_i$ is properly formulated for lower-bound commitment.
  - Lemma 1 proof is mathematically complete: $\lceil 0.90(K+1) \rceil \le K \iff K \ge 9$.
  - Fallback hierarchy is explicitly formalized: below $K=9$, the calibrator safely falls back to frozen source quantile $q_{\text{source}}$.

### 1.6 Dataset Acquisition & Experimental Protocol
- **Audit Findings:**
  - Causal 60-second telemetry lookback is defined: $[t_{\text{start}} - 60\text{s}, t_{\text{start}})$.
  - Preceding test lag freshness $\Delta t \in [0, 60\text{ s}]$ is formalized.
  - Partitions across E0, E1, E2, E3 are fully specified with verified session and cluster counts.
  - Enforces that all evaluation partitions are strictly disjoint at the calendar day level.

### 1.7 Experimental Results and Discussion
- **Audit Findings:**
  - **Honest Reporting of Mixed Findings:** In E1 and E2 at $K=10$, Grouped Conformal exhibits higher violation rates ($V = 0.122$ in E1, $V = 0.164$ in E2) than Global Conformal ($V = 0.072$ in E1, $V = 0.023$ in E2). Rather than obscuring this, the text explains the underlying mechanism: Global Conformal achieves safety through hyper-conservatism, committing only 1.8% of network capacity ($U = 0.018$), whereas Grouped Conformal unlocks $10.5\times$ more capacity ($U = 0.189$). This is documented as an operational **Risk-Utility Trade-Off**.
  - **Exploratory Designation for E0 Bootstrap:** The text explicitly notes that E0 target test contains only $G = 2$ calendar dates, rendering the bootstrap $[0.0, 0.0]$ confidence interval degenerate and exploratory.
  - **CS-CP in Regime E3:** Highlights that Bayes-corrected CS-CP sustains $U = 0.0101$ with $V = 0.0000$, overcoming target-domain outlier zero-stalls.

### 1.8 Limitations and Threats to Validity
- **Audit Findings:**
  - Comprehensively discusses:
    1. Geographic limitation: all empirical traces originate from Rome, Italy.
    2. Small cluster sample sizes ($G \in [2, 8]$ dates).
    3. Heuristic session segmentation in 2023 Ookla speedtests.
    4. Subgroup thinning at small calibration budgets ($K=10$).
    5. Absence of live over-the-air cellular base station closed-loop control.

---

## 2. Audit of Industry and Bangladesh Telecom Framing

### 2.1 Critical Distinction
All empirical datasets were collected in Rome, Italy (Zenodo 8224890 and 14073311).  
**Strict Integrity Rule:** The manuscript must NEVER state or imply that experimental results evaluate Bangladeshi mobile networks or that the models were trained on Bangladeshi field data.

### 2.2 Revisions Made:
1. **Figure 5 Caption:** Removed phrasing claiming the loss curve "minimizes total operational loss under BTRC QoS mandates." Replaced with: "minimizing total operational SLA loss across representative regulatory and commercial penalty regimes (including standard broadband QoS benchmarks)."
2. **Section VI (Operational Principles for Emerging Networks):**
   - Reframed Bangladesh (Grameenphone, Banglalink, Robi Axiata, Teletalk) strictly as a **prospective motivation and target application scenario**.
   - Outlines how emerging markets with dense urban topographies (e.g. Dhaka) and capital constraints can deploy minimal drive-testing recalibration ($K=9$ sessions per morphology cluster) rather than multi-month exhaustive drive testing.
3. **Future Validation Roadmap:** Formulates a concrete 3-stage validation plan specifying the exact local measurements required to deploy this benchmark in Bangladesh:
   - *Phase 1:* Drive-test data acquisition across major Bangladeshi telecom corridors (e.g. Mirpur-Airport Road, Dhaka; Chittagong Highway).
   - *Phase 2:* Synchronized extraction of LTE Band 1/3/8 (Grameenphone/Banglalink/Robi) and prospective 5G Band n78 telemetry.
   - *Phase 3:* Transfer evaluation benchmarking source European models transferred to Bangladeshi radio environments.

---

## 3. Reference and Citation Audit

All citations in `references.bib` have been verified for publication venue, authorship, and active DOI:
1. `kousias2024large`: IEEE Communications Magazine, DOI: `10.1109/MCOM.011.2200707` (Verified).
2. `caso2024chronicles`: IEEE Open Journal of the Communications Society, DOI: `10.1109/OJCOMS.2024.3392811` (Verified).
3. `jacobson2025predicting`: Journal of the Royal Statistical Society Series C, DOI: `10.1093/jrsssc/qlae054` (Verified).
4. `zaffran2023conformal`: ICML 2023, PMLR Vol. 202, pp. 40578–40604 (Verified).
5. `gibbs2021adaptive`: NeurIPS 2021, Vol. 34, pp. 1660–1672 (Verified).
6. `sirhan2026handover`: Network, DOI: `10.3390/network6040092` (Verified).
7. `raca2020beyond`: ACM MMSys 2020, DOI: `10.1145/3339825.3394938` (Verified).
8. `narayanan2020lumos5g`: ACM IMC 2020, DOI: `10.1145/3419394.3423629` (Verified).
9. `kousias2024empirical`: Computer Networks 2024, DOI: `10.1016/j.comnet.2024.110207` (Verified).
10. `vovk2005algorithmic`: Springer, 2005 (Verified).
11. `tibshirani2019conformal`: NeurIPS 2019, Vol. 32, pp. 2530–2540 (Verified).

---

## 4. Manuscript Audit Sign-off

The manuscript files (`paper/manuscript.tex`, `paper/manuscript.md`, `paper/manuscript.html`) are audited, aligned with verified empirical artifacts, free of exaggerated deployment claims, and prepared for independent technical peer review.

