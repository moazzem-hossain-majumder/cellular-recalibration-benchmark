# Scientific Reproducibility and Audit Report (Phase 8)

**Project:** Cellular Recalibration Benchmark  
**Manuscript Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Master Reproduction Entry Point:** `python scripts/reproduce_all.py`  
**Evaluation Standard:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  

---

## 1. System Environment and Dependencies

To ensure deterministic reproduction across independent research laboratories:

### 1.1 Hardware Specifications
- **Host OS:** Windows 11 / Linux (Ubuntu 22.04 LTS verified via GitHub Actions).
- **CPU:** Multi-core x86_64 CPU (Intel Core i7 / AMD Ryzen).
- **GPU (Optional):** NVIDIA GeForce RTX 4060 with CUDA 12.x support (utilized for Deep Tabular ResNet acceleration; pipeline automatically falls back to CPU if no GPU is detected).
- **System Memory:** Minimum 16 GB RAM.

### 1.2 Python Environment
- **Python Version:** `Python 3.11.9`
- **Primary Package Dependencies:**
  - `torch >= 2.0.0`
  - `numpy >= 1.24.0`
  - `scipy >= 1.10.0`
  - `pandas >= 2.0.0`
  - `scikit-learn >= 1.3.0`
  - `matplotlib >= 3.7.0`
  - `seaborn >= 0.12.0`
  - `pytest >= 7.4.0`

---

## 2. Dataset Acquisition and Cryptographic Checksums

All measurement data originates from peer-reviewed public Zenodo repositories. Automated download and verification are managed by `scripts/download_data.py`:

| Dataset Family | Zenodo Record | File / Directory | Size | SHA-256 Checksum |
|---|---|---|---|---|
| **2021 Campaign** | `8224890` | `Throughput Tests - Speedtest - Active Measurements.csv` | ~12.4 MB | Verified in acquisition manifest |
| **2023 Campaign** | `14073311` | `Active Performance Dataset - 1/Ookla Speedtests/` (43 CSVs) | ~1.4 GB | Verified in acquisition manifest |

To verify raw dataset integrity without re-downloading:
```bash
python scripts/download_data.py --verify-only
```

---

## 3. Step-by-Step Reproduction Workflow

An independent researcher can reproduce all experiments, figures, tables, and diagnostics from scratch:

### Step 1: Run Full Test Suite (Verification of Code & Causality)
```bash
python -m pytest tests/ -v
```
*Expected Result:* 36 passed tests in ~80 seconds.

### Step 2: Execute Point Predictor Benchmark & Main Calibration Transfer Benchmark
```bash
python src/experiments/runner.py
```
*Generated Artifacts:*
- `results/metrics/point_predictor_profiles.json`
- `results/metrics/calibration_budget_results.csv`
- `results/metrics/bootstrap_significance_tests.json`
- `results/tables/table1_point_predictors.tex`
- `results/tables/table2_main_benchmark.tex`
- `results/figures/fig1_budget_vs_usefulness.{pdf,png}`
- `results/figures/fig2_subgroup_and_tradeoff.{pdf,png}`
- `results/diagnostics/split_summary.json`

### Step 3: Execute Ablations, CS-CP, and SLA Cost Optimization
```bash
python src/experiments/ablations.py
```
*Generated Artifacts:*
- `results/metrics/ablation_artificial_masking.json`
- `results/metrics/freshness_sensitivity.json`
- `results/metrics/ablation_fallback_thresholds.json`
- `results/metrics/multi_alpha_frontier.json`
- `results/metrics/covariate_shift_conformal.json`
- `results/metrics/online_aci_results.json`
- `results/metrics/sla_cost_analysis.json`
- `results/figures/fig3_aci_adaptation.{pdf,png}`
- `results/figures/fig4_pareto_frontier.{pdf,png}`
- `results/figures/fig5_sla_cost_curve.{pdf,png}`

### Step 4: Build Interactive Dashboard & HTML Paper Package
```bash
python scripts/build_web_demo.py
python scripts/build_paper_html.py
```
*Generated Artifacts:*
- `app/web_demo.html` (Interactive browser dashboard)
- `paper/manuscript.html` & `paper/submission_package.zip`

---

## 4. Single-Command End-to-End Reproduction

The entire workflow is automated via the master reproduction script:
```bash
python scripts/reproduce_all.py
```
This executes data verification, the complete test suite, point predictor profiling on GPU, the main transfer benchmark across all four regimes, all ablation experiments, and dashboard generation.

---

## 5. Artifact Manifest and Traceability

| Paper Item | Generated File Path | Script Source | Underlying Method |
|---|---|---|---|
| **Table 1** | `results/tables/table1_point_predictors.tex` | `src/experiments/runner.py` | Persistence, Ridge, HistGBM, BAMMO, QuantileGBM, ResNet (GPU) |
| **Table 2** | `results/tables/table2_main_benchmark.tex` | `src/experiments/runner.py` | Uncalibrated, Global Conformal, Grouped Conformal ($K \in \{0..15\}$) |
| **Figure 1** | `results/figures/fig1_budget_vs_usefulness.pdf` | `src/experiments/runner.py` | Supported capacity $U$ across budgets $K$ (Regimes E0–E3) |
| **Figure 2** | `results/figures/fig2_subgroup_and_tradeoff.pdf` | `src/experiments/runner.py` | Subgroup violation in E2 and risk-utility frontier |
| **Figure 3** | `results/figures/fig3_aci_adaptation.pdf` | `src/experiments/ablations.py` | Online ACI tracking across 139 test steps in E1 ($\gamma=0.02$) |
| **Figure 4** | `results/figures/fig4_pareto_frontier.pdf` | `src/experiments/ablations.py` | Calibration curve $V(\alpha)$ and Pareto frontier $U(V)$ across $\alpha \in [0.01, 0.30]$ |
| **Figure 5** | `results/figures/fig5_sla_cost_curve.pdf` | `src/experiments/ablations.py` | Economic SLA loss $\mathcal{L}_\lambda$ across penalty weights $\lambda \in [0, 1]$ |
| **Bootstrap** | `results/metrics/bootstrap_significance_tests.json` | `src/experiments/runner.py` | 2,000 paired day-cluster resamples on $\Delta V$ and $\Delta U$ |

