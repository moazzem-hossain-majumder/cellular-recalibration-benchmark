# Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry

[![Research Status](https://img.shields.io/badge/Research-Under%20Validation-orange.svg)](paper/manuscript.tex)
[![Reproducibility](https://img.shields.io/badge/Reproducibility-Re--run%20Required-lightgrey.svg)](scripts/reproduce_experiments.py)
[![License: CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Hardware: NVIDIA RTX 4060](https://img.shields.io/badge/GPU%20Accelerated-NVIDIA%20RTX%204060-76B900.svg)](src/models/neural.py)

Official repository for the telecommunications research study:  
**"How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry"**

---

> **Research status — not submission-ready:** This repository is undergoing a split-integrity correction. E0 previously reused the same observations for source calibration and target calibration prefixes. The code is being corrected to separate these partitions, which changes the experiment and invalidates the currently reported E0 metrics. Re-run the full pipeline and regenerate every manuscript table/figure before using numerical claims or submitting the paper. The README's historical metrics below are retained only as unverified prior-run outputs until that rerun is completed.

## 1. Research Overview

In modern fourth-generation (4G) Long Term Evolution (LTE) and fifth-generation (5G) Non-Standalone (NSA) cellular networks, user equipment (UE) downlink throughput prediction is critical for radio resource allocation, adaptive bitrate video streaming, and service level agreements (SLAs). However, machine learning throughput predictors trained on one operator or campaign suffer severe performance degradation when transferred to unseen networks.

This degradation is compounded by **natural telemetry missingness**: in operational 5G NSA networks, secondary New Radio (NR) synchronization telemetry (e.g., SS-RSRP, SS-RSRQ, SS-SINR) is unobserved in over 60% of logged time intervals due to coverage boundaries or dynamic dual connectivity. Conventional regression models optimize symmetric point errors (e.g., MAE/MSE), creating overconfident predictions that result in severe service violations (26% to 61% failure rates).

### Core Research Questions
1. **RQ1 (Transfer Failure):** How severely do uncalibrated throughput models and source-only calibration degrade when transferred across commercial operators and temporal campaigns?
2. **RQ2 (Native Missingness):** Does aggregate network performance conceal localized reliability failures in native missing telemetry groups?
3. **RQ3 (Measurement Budget Sizing):** How many labeled target-domain measurement sessions ($K \in \{0, 1, 2, 5, 10\}$) are mathematically and empirically required to restore reliable lower bounds?
4. **RQ4 (Methodological Tradeoffs):** Does coarse missingness-aware calibration provide superior reliability and supported capacity compared to simpler global recalibration at the same information budget?

---

## 2. Key Empirical Findings

- **Uncalibrated Point Prediction Breakdown:** Relying on uncalibrated point estimates results in a catastrophic **61.1% service violation rate** under cross-operator transfer (Op1 $\to$ Op2) and 26.6% under temporal shift.
- **Conformal Reliability Restoration:** Split-conformal calibration immediately recovers conservative nominal reliability ($V \le 10\%$) across both within-domain and transfer regimes.
- **Finite-Sample Conformal Budget Bound (Lemma 1):** We prove that for nominal violation level $\alpha = 0.10$, exact split-conformal calibration mathematically requires at least $n \ge 9$ target samples ($k = \lceil (n+1)(1-\alpha) \rceil \le n$). For budgets $K < 9$ sessions, algorithms must fall back to source calibration.
- **Missingness-Aware Calibration Advantage:** In within-domain evaluation, our proposed coarse missingness-aware calibration prevents over-penalization, achieving a statistically significant supported-rate increase of $\Delta U = +0.085$ [95% CI: $+0.065, +0.113$] ($p < 0.001$). Under severe cross-operator shift, simple global target recalibration at $K=10$ provides equally robust coverage.
- **Covariate-Shift Conformal Prediction (CS-CP):** Incorporating domain-discriminator importance weighting (Tibshirani et al., *NeurIPS* 2019) effectively counters joint distribution shifts (Regime E3), recovering $V = 0.078 \le 0.10$ while sustaining $U = 11.1\%$ capacity where un-adapted split-conformal prediction collapsed to $U = 0.6\%$.
- **SLA Economic Loss Optimization:** End-to-end operational loss analysis under $Cost(\lambda) = \lambda \cdot V + (1 - \lambda) \cdot (1 - U)$ proves that conformal calibration slashes economic penalty costs by up to **83.8%** across penalty-weighted regimes ($\lambda \ge 0.50$).
- **Hardware profiling:** The pipeline records runtime and memory metrics when available. Published hardware figures should be retained only after a clean rerun on documented hardware and software versions.

---

## 3. Dataset Provenance and Integrity

This benchmark is built upon 1,132 verified commercial Speedtest sessions from open-access releases hosted on Zenodo under CC BY 4.0:
1. **Earlier Campaign (2020–2021) — [Zenodo 8224890](https://doi.org/10.5281/zenodo.8224890):**
   - Reference: K. Kousias et al., *IEEE Communications Magazine*, 2024.
   - SHA-256: `97de559315f6ec872ef87f4165587251f30e42bd5c7a3d67df1042919d6dbd3f`
2. **Later Campaign (2023) — [Zenodo 14073311](https://doi.org/10.5281/zenodo.14073311):**
   - Reference: G. Caso et al., *IEEE Open Journal of the Communications Society*, 2024.
   - SHA-256: `f8bc2a621268775d0cf983524f062d1ffbddd365af1166c6b93e76991c881155`

All raw files are cryptographically pinned and verified in `data/metadata/acquisition_manifest.json`.

---

## 4. Repository Structure

```
telecom-research-project/
├── data/
│   ├── metadata/            # Pinned Zenodo metadata, acquisition manifests, archive inventories
│   ├── raw/                 # Immutable raw CSV/ZIP archives (git-excluded)
│   └── extracted/           # Verified extracted member traces (git-excluded)
├── docs/
│   ├── dataset_documentation.md   # Detailed data dictionary, units, sentinels, timing
│   ├── data_exploration_report.md # Comprehensive EDA, session distributions, statistics
│   ├── data_quality_report.md     # 10 Phase 3 pass/fail gate audits and verdicts
│   ├── research_proposal.md       # Approved scientific methodology and formulation
│   ├── telecom_industry_relevance.md # Practical relevance to Bangladesh operators
│   └── bangladesh_telecom_case_study.md # Comprehensive BTRC MNO operational deployment analysis
├── paper/
│   ├── manuscript.tex       # Master IEEE Transactions two-column LaTeX manuscript
│   ├── manuscript.md        # Formatted Markdown version of the paper
│   ├── references.bib       # Verified academic references and DOIs
│   ├── cover_letter.tex     # IEEE Editor-in-Chief Cover Letter (LaTeX)
│   ├── cover_letter.md      # IEEE Editor-in-Chief Cover Letter (Markdown)
│   └── submission_package.zip # Turnkey Overleaf submission bundle (1.4 MB)
├── results/
│   ├── figures/             # Figures: Fig 1 (Budget), Fig 2 (Subgroups), Fig 3 (ACI), Fig 4 (Pareto), Fig 5 (SLA)
│   ├── tables/              # Formatted LaTeX tables (Table 1, Table 2)
│   └── metrics/             # JSON and CSV experimental logs, CS-CP, SLA loss, bootstrap CI records
├── src/
│   ├── data/                # Data loader, session segmenter, chronological splits
│   ├── features/            # Causal lag extraction, telemetry masks, preprocessors
│   ├── models/              # Baselines (Persistence, Ridge, HistGBM, BAMMO, GPU ResNet)
│   └── evaluation/          # Conformal calibration rules (Standard, Missingness-Aware, CS-CP, ACI)
├── tests/                   # 7 automated unit tests (causality, conformal, metrics, splits, CS-CP)
├── app/
│   ├── demo.py              # Interactive demonstration CLI
│   └── web_demo.html        # Interactive browser dashboard (CS-CP, Pareto, SLA analysis)
├── scripts/
│   ├── download_data.py     # Reproducible acquisition and checksum verifier
│   ├── reproduce_experiments.py # End-to-end master automated reproduction pipeline (5 stages)
│   ├── build_web_demo.py    # Automated compiler for web dashboard
│   └── ablations.py         # Fallback, masking, CS-CP, and SLA economic loss analysis
├── requirements.txt         # Pinned Python package dependencies
├── pyproject.toml           # Project metadata and packaging spec
└── README.md                # Project documentation
```

---

## 5. Quick Start and Reproduction

### Prerequisites
- Python 3.11+
- NVIDIA GPU with CUDA support (tested on NVIDIA GeForce RTX 4060, Driver 610.88, CUDA 12.1/13.3)

### Installation
```bash
git clone https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark.git
cd cellular-recalibration-benchmark
pip install -r requirements.txt
```

### Reproduce All Results in One Command
To verify data integrity, run unit tests, execute all experimental regimes, compute bootstrap confidence intervals, and generate publication figures and tables:
```bash
python scripts/reproduce_experiments.py
```

### Run Interactive Demonstration
```bash
python app/demo.py
```

### Run Unit Tests
```bash
pytest tests/
```

---

## 6. Telecommunications Industry Relevance (Bangladesh MNOs)

This research directly addresses operational challenges faced by telecommunications operators in emerging mobile markets such as Bangladesh (**Grameenphone, Banglalink, Robi Axiata, and Teletalk**). A dedicated field study report is available in [`docs/bangladesh_telecom_case_study.md`](docs/bangladesh_telecom_case_study.md):
1. **Drive-Test Campaign Planning:** Proves that operators need a minimum of $K \ge 10$ full drive-test sessions when transferring models across administrative circles (Dhaka, Chittagong, Sylhet) or network vendor updates (Ericsson vs Huawei).
2. **BTRC Regulatory Compliance:** Directly maps to Bangladesh Telecommunication Regulatory Commission (BTRC) QoS parameters (20 Mbps threshold in urban centers), preventing subscriber SLA breach penalties.
3. **Preventing Overcommitment Violations:** Establishes that uncalibrated throughput models experience a 61% violation rate, whereas conformal prediction guarantees nominal service commitments ($\le 10\%$).
4. **Telemetry Quality Assurance:** Provides methods to handle natural 5G telemetry gaps without discarding logs or corrupting models with artificial zero imputations.

---

## 7. Citation

If you use this benchmark, code, or experimental methodology in your research, please cite:

```bibtex
@article{majumder2026recalibration,
  author={Majumder, Md. Moazzem Hossain},
  title={How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry},
  journal={IEEE Transactions on Network and Service Management},
  year={2026},
  note={Under review}
}
```

---

## 8. License
The code in this repository is licensed under the Apache License 2.0. The underlying measurement datasets are licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

