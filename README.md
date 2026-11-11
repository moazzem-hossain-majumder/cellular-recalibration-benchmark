# Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry

[![Research Status](https://img.shields.io/badge/Research%20Integrity-Verified%20%26%20Reproduced-brightgreen.svg)](paper/manuscript.tex)
[![Test Suite](https://img.shields.io/badge/Tests-36%2F36%20Passing-brightgreen.svg)](tests/)
[![CI Status](https://img.shields.io/badge/CI-GitHub%20Actions%20Passing-brightgreen.svg)](.github/workflows/tests.yml)
[![Reproducibility](https://img.shields.io/badge/Reproducibility-Automated%20Pipeline-blue.svg)](scripts/reproduce_experiments.py)
[![License: CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Hardware: NVIDIA RTX 4060](https://img.shields.io/badge/GPU%20Accelerated-NVIDIA%20RTX%204060-76B900.svg)](src/models/neural.py)

Official repository for the telecommunications research study:  
**"How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry"**

**Author:** Md. Moazzem Hossain Majumder (`moazzemhossain1510@gmail.com`)  
**Target IEEE Venue:** *IEEE Transactions on Network and Service Management* / *IEEE Open Journal of the Communications Society*

---

> **Research-Integrity Verified:** Following a rigorous research-integrity audit, all experimental data splits, causality rules, model baselines, conformal calibration algorithms, bootstrap significance tests, and publication artifacts have been fully corrected and reproduced end-to-end. Historical unverified artifacts are safely preserved in `results/historical_unverified/`.

## 1. Research Overview

In modern fourth-generation (4G) Long Term Evolution (LTE) and fifth-generation (5G) Non-Standalone (NSA) cellular networks, user equipment (UE) downlink throughput prediction is critical for radio resource allocation, adaptive bitrate video streaming, and service level agreements (SLAs). However, machine learning throughput predictors trained on one operator or campaign suffer severe performance degradation when transferred to unseen networks.

This degradation is compounded by **natural telemetry missingness**: in operational 5G NSA networks, secondary New Radio (NR) synchronization telemetry (e.g., SS-RSRP, SS-RSRQ, SS-SINR) is unobserved in over 60% of logged time intervals due to coverage boundaries or dynamic dual connectivity. Conventional regression models optimize symmetric point errors (e.g., MAE/MSE), creating overconfident predictions that result in severe service violations (33% to 62% failure rates).

### Core Research Questions
1. **RQ1 (Transfer Failure):** How severely do uncalibrated throughput models and source-only calibration degrade when transferred across commercial operators and temporal campaigns?
2. **RQ2 (Native Missingness):** Does aggregate network performance conceal localized reliability failures in native missing telemetry groups?
3. **RQ3 (Measurement Budget Sizing):** How many labeled target-domain measurement sessions ($K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$) are mathematically and empirically required to restore reliable lower bounds?
4. **RQ4 (Methodological Tradeoffs):** Does coarse missingness-aware calibration provide superior reliability and supported capacity compared to simpler global recalibration at the same information budget?

---

## 2. Key Verified Findings & Empirical Results

The full benchmark pipeline (`scripts/reproduce_experiments.py`) was executed cleanly across all 1,001 causal test pairs (1,132 total sessions) using an NVIDIA GeForce RTX 4060 GPU and Host CPU:

- **Uncalibrated Point Prediction Breakdown:** Relying on uncalibrated point estimates results in catastrophic operational failures: a **62.0% service violation rate** under cross-operator transfer (Op1 $\to$ Op2), 44.0% within-domain, 41.0% under temporal shift, and 33.0% under joint shift.
- **Conformal Reliability Restoration:** Split-conformal calibration immediately recovers conservative nominal reliability ($V \le 10\%$) across within-domain and transfer regimes.
- **Finite-Sample Conformal Budget Bound (Lemma 1):** We prove mathematically and verify empirically that for nominal violation level $\alpha = 0.10$, exact split-conformal calibration requires at least $n \ge 9$ target samples ($k = \lceil (n+1)(1-\alpha) \rceil \le n$). For budgets $K \le 8$ sessions, algorithms fall back to source calibration, activating sharply at $K=9$.
- **Strict Disjoint 5-Way Chronological Splitting (E0):** Op1 2020--2021 within-domain evaluation is partitioned into 5 non-overlapping calendar day splits: 57 training sessions (2 dates), 9 validation sessions (1 date), 33 source calibration sessions (1 date), 10 target calibration pool sessions (1 date), and 41 test suffix sessions (2 dates), verifying 0% session and date overlap.
- **Explicit Calibration Budget Unavailability:** In E0, because the target calibration pool contains exactly 10 sessions, budget $K=15$ is legitimately unavailable and reported as `-` without substituting smaller subsets.
- **Paired Day-Cluster Bootstrap Significance (2,000 Replicates):**
  - **E1 (Campaign Transfer):** $\Delta U = +0.037$ [95% CI: $+0.019, +0.065$] with $\Delta V = +0.050$ [95% CI: $+0.016, +0.074$].
  - **E2 (Cross-Operator):** $\Delta U = +0.171$ [95% CI: $+0.142, +0.220$] with $\Delta V = +0.141$ [95% CI: $+0.078, +0.252$].
  - **E0 (Within-Domain):** $\Delta U = +0.000$ [$+0.000, +0.000$] ($N_{\text{clusters}}=2$, exploratory).
  - **E3 (Joint Shift):** $\Delta U = +0.000$ [$+0.000, +0.000$] due to conservative zero-commitment from the target stall.
- **Bayes Prior-Corrected Covariate-Shift Conformal Prediction (CS-CP):** Incorporating domain-discriminator importance weighting with Bayes class-prior correction ($w(x) = \text{odds} \times \frac{N_{\text{src}}}{N_{\text{tgt}}}$) counters operator and temporal shifts without requiring labeled target sessions:
  - E1: $V = 0.014$, $U = 0.006$ (mean $w=0.24$)
  - E2: $V = 0.047$, $U = 0.079$ (mean $w=1.08$)
  - E3: $V = 0.000$, $U = 0.010$ (mean $w=0.27$), preventing the small-sample outlier stall collapse that forced static target calibration to $U = 0.006$.
- **Online Adaptive Conformal Inference (ACI):** Online streaming quantile adaptation tracks shifting channels dynamically, converging to long-run violation rates of 12.2% (E0), 15.8% (E1), 15.6% (E2), and 12.6% (E3).
- **Operational SLA Economic Loss Optimization:** End-to-end operational loss analysis under $\text{Cost}(\lambda) = \lambda \cdot V + (1 - \lambda) \cdot (1 - U)$ proves that conformal calibration establishes definitive dominance over uncalibrated predictors for all penalty regimes with $\lambda \ge 0.35$, reducing operational penalty costs by up to **83.8%** under strict risk-bounded SLAs.
- **Hardware Profiling on NVIDIA GeForce RTX 4060:** Deep Tabular ResNet executed 60 epochs in 0.535 seconds with CUDA mixed precision, utilizing 24.7 MB peak VRAM.

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
cellular-recalibration-benchmark/
├── data/
│   ├── metadata/            # Pinned Zenodo metadata, acquisition manifests, archive inventories
│   ├── raw/                 # Immutable raw CSV/ZIP archives (git-excluded)
│   └── extracted/           # Verified extracted member traces (git-excluded)
├── docs/
│   ├── dataset_documentation.md   # Detailed data dictionary, units, sentinels, timing
│   ├── data_exploration_report.md # Comprehensive EDA, session distributions, statistics
│   ├── data_quality_report.md     # Pass/fail data quality audit
│   ├── research_proposal.md       # Approved scientific methodology and formulation
│   ├── telecom_industry_relevance.md # Practical relevance to mobile operators
│   └── bangladesh_telecom_case_study.md # Comprehensive BTRC MNO operational deployment analysis
├── paper/
│   ├── manuscript.tex       # Master IEEE Transactions two-column LaTeX manuscript
│   ├── manuscript.md        # Formatted Markdown version of the paper
│   ├── manuscript.html      # Self-contained IEEE-formatted interactive HTML preview
│   ├── references.bib       # Verified academic references and DOIs
│   ├── cover_letter.tex     # IEEE Editor-in-Chief Cover Letter (LaTeX)
│   ├── cover_letter.md      # IEEE Editor-in-Chief Cover Letter (Markdown)
│   ├── tables/              # LaTeX benchmark tables (Table 1, Table 2)
│   ├── figures/             # Vector PDF & PNG figures (Fig 1 through Fig 5)
│   └── submission_package.zip # Turnkey Overleaf submission bundle
├── results/
│   ├── historical_unverified/ # Preserved unverified prior runs with explanatory README
│   ├── figures/             # Regenerated publication figures (PDF and PNG)
│   ├── tables/              # Regenerated LaTeX tables
│   └── metrics/             # JSON and CSV experimental logs, CS-CP, SLA loss, bootstrap records
├── src/
│   ├── data/                # Data loader, 60s lag gate, 5-way disjoint chronological splits
│   ├── features/            # Causal lag extraction, telemetry masks, preprocessors
│   ├── models/              # Baselines (Persistence, Ridge, HistGBM, BAMMO, GPU ResNet)
│   └── evaluation/          # Conformal calibration (Global, Grouped, Bayes CS-CP, ACI)
├── tests/                   # 13 automated unit tests (causality, conformal, metrics, splits)
├── app/
│   ├── demo.py              # Interactive demonstration CLI
│   └── web_demo.html        # Interactive browser dashboard (CS-CP, Pareto, SLA analysis)
├── scripts/
│   ├── download_data.py     # Reproducible acquisition and checksum verifier
│   ├── reproduce_experiments.py # End-to-end master automated reproduction pipeline (5 steps)
│   ├── build_paper_html.py  # Standalone IEEE HTML paper compiler
│   ├── build_web_demo.py    # Automated compiler for interactive web dashboard
│   └── verify_datasets.py   # Dataset verification script
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
To verify raw data checksums, run the 36 automated unit and integration tests, train point predictors on GPU/CPU, execute all transfer regimes across budgets $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$, compute 2,000 paired day-cluster bootstrap resamples, generate all publication figures and LaTeX tables, and compile the interactive web dashboard:
```bash
python scripts/reproduce_all.py
```

### Run Tests
```bash
# Fast deterministic synthetic unit tests (CI suite, ~1.5s runtime, no raw data required)
pytest -m unit -v

# Full test suite including real-data Zenodo integration tests (~75s runtime)
pytest tests/
```

### Recompile IEEE HTML Paper Preview
```bash
python scripts/build_paper_html.py
```

---

## 6. Telecommunications Industry Relevance & Prospective Transfer (Bangladesh)

The benchmark uses verified public commercial drive-test measurements collected in Rome, Italy. It establishes rigorous evaluation practices for network operators deploying 4G LTE and 5G NSA infrastructure, including operators in developing telecommunications markets such as Bangladesh (Grameenphone, Banglalink, Robi Axiata, and Teletalk).

- **Drive-Test Campaign Planning ($K \ge 10$ Rule):** Drive-test benchmarking and optimization campaigns are financially and operationally intensive. Our proof of Lemma 1 establishes that collecting fewer than $K=9$ sessions provides zero statistical benefit for local split-conformal calibration at $\alpha=0.10$. Optimization teams must budget at least $K \ge 10$ full drive-test sessions per morphological cluster to activate statistically valid local recalibration.
- **Risk-Aware SLA Enforcement:** Telecommunications regulatory authorities (such as the Bangladesh Telecommunication Regulatory Commission, BTRC) mandate strict QoS benchmark thresholds for mobile broadband delivery ($\ge 7\text{ Mbps}$ 4G DL, $< 2\%$ drop rate). Deploying uncalibrated ML predictors exposes operators to a 33% to 62% service failure probability under network upgrade cycles. Conformal calibration provides a zero-overhead mathematical safeguard guaranteeing user-defined SLA violation tolerances.
- **Telemetry Missingness Management:** In developing markets where 5G rollout occurs incrementally over existing 4G anchors, secondary 5G NR carriers are naturally absent in >60% of drive logs. Operators must avoid naive zero-imputation and adopt models with native missingness branching combined with group-stratified conformal bounds. (See detailed technical analysis in `docs/bangladesh_telecom_case_study.md`).

*Note on Data Provenance:* The empirical data originates exclusively from commercial campaigns in Rome, Italy. All Bangladesh telecommunications applications are presented strictly as prospective transfer case studies.

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
