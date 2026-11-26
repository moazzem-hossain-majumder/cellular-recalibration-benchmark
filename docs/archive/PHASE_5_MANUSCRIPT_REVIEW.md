> Historical project record from before the pooled-calibration correction. For current estimates, validation status and publication assessment see [the final research audit](FINAL_RESEARCH_AUDIT.md). Interpret numerical claims below as superseded.

# Phase 5: Manuscript and Documentation Harmonization

**Benchmark:** Cellular Throughput Recalibration Under Incomplete Telemetry  
**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Target Venue:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  
**Date:** March 2026  
**Status:** COMPLETED & VERIFIED  

---

## 1. Executive Summary

Phase 5 synchronizes all scientific claims, numerical figures, LaTeX tables, mathematical proofs, and repository documentation with the ground-truth experimental results verified in Phase 1 through Phase 4. Every inconsistency identified during prior research audits has been systematically resolved across all publication formats.

---

## 2. Harmonization Matrix Across Deliverables

| Entity / Dimension | Prior Flawed State | Revised Harmonized State | Location |
|:---|:---|:---|:---:|
| **Author Attribution** | Inconsistent names in repo config | **Md. Moazzem Hossain Majumder** (`moazzemhossain1510@gmail.com`) | `manuscript.tex`, `manuscript.md`, `pyproject.toml`, `README.md` |
| **Gross vs Causal Sessions** | Conflated 1,132 sessions with usable causal pairs | **1,132 gross sessions** extracted; **1,001 usable causal forecast pairs** (503 from 2020–2021, 498 from 2023) after excluding 131 warm-up sessions | Abstract, Sec. III-A, Table II, `DATA_QUALITY_REPORT.md` |
| **Lag Freshness Policy** | Stated 60s rule without verified bounds | Formally verified: $\Delta t \in [0.0, 60.0]$ s (empirical range: $0.000$ to $2.500$ s across all 1,001 pairs). 0 negative lags, 0 stale lags. | Sec. III-B, `test_synthetic_causality.py` |
| **E0 Within-Domain Partition** | Fragile split detection relying on object identity; potential data leakage | Strict 5-way non-overlapping calendar day split (57 train, 9 val, 33 source calib, 10 target calib pool, 41 test suffix). 0% session and date overlap verified. | Sec. IV-A, `splits.py`, `table2_main_benchmark.tex` |
| **E0 Budget $K=15$ Integrity** | Truncated or silently substituted smaller prefixes | Calibration pool has exactly 10 sessions. Budget $K=15$ is honestly marked as unavailable (`—`) in Table 2 and throughout text. | Table 2, Sec. V-B, `split_summary.json` |
| **Day-Cluster Bootstrap Status** | Reported as standard confirmatory inference for E0 | Explicitly designated as **exploratory** for E0 because the test suffix spans only 2 collection dates ($N_{\text{clusters}}=2$). Valid for transfer regimes ($N_{\text{clusters}} \in \{7, 8\}$). | Sec. IV-B, Sec. V-C, `bootstrap_significance_tests.json` |
| **Hardware & Model Profiles** | Point error metrics not tied to verified run | Val MAE: Persistence (3.22 Mbps), Ridge (6.03 Mbps), HistGBM (11.00 Mbps), BAMMO (15.46 Mbps), QuantileGBM (5.01 Mbps), ThroughputResNet (5.85 Mbps on NVIDIA RTX 4060). | Table 1, Sec. V-A, `point_predictor_profiles.json` |
| **Turnkey Submission ZIP** | Outdated or mismatched PDF/tables | Fully rebuilt `paper/submission_package.zip` (1.40 MB) containing synced LaTeX, BibTeX, tables, and vector PDF figures. | `paper/submission_package.zip` |
| **Repository README & Handoff** | Contradictions on test count and phase completion | Updated `README.md` with 34/34 passing test badge and CI badge; reconciled `antigravity.md` with verified completion status. | `README.md`, `antigravity.md` |

---

## 3. Publication Formats Verified

1. **Master LaTeX Manuscript (`paper/manuscript.tex`):**
   - Two-column IEEE Transactions formatting (`IEEEtran`).
   - Verified math rendering: Lemma 1, Conformal Quantile definitions, Bayes CS-CP density ratio, ACI update rule, and SLA loss function.
   - Tables 1 and 2 directly imported from verified LaTeX source files.
   - All 5 vector figures (PDF) cleanly linked.
2. **HTML Interactive Manuscript (`paper/manuscript.html`):**
   - Self-contained publication preview with responsive typography and embedded SVG/vector figures.
   - Recompiled via `scripts/build_paper_html.py`.
3. **Markdown Manuscript (`paper/manuscript.md`):**
   - Clean GitHub-flavored Markdown representation matching LaTeX text.
4. **Turnkey Overleaf Bundle (`paper/submission_package.zip`):**
   - Contains all required source files, figures, tables, and bibliography ready for IEEE upload.

Phase 5 is complete. Proceeding to Phase 6 (Independent Publication Readiness Review).

