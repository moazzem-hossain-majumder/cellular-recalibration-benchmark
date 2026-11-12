> Historical project record from before the pooled-calibration correction. For current estimates, validation status and publication assessment see [the final research audit](FINAL_RESEARCH_AUDIT.md). Interpret numerical claims below as superseded.

# Experimental Protocol and Chronological Split Specification (Phase 8)

**Project:** Cellular Recalibration Benchmark  
**Manuscript Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Production Code:** `src/data/splits.py` (`create_experiment_splits()`, `partition_by_chronological_days()`)  
**Audit Artifact:** `results/diagnostics/split_summary.json`  
**Evaluation Standard:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  

---

## 1. Experimental Design and Objectives

The primary objective of the experimental protocol is to evaluate the reliability and capacity trade-offs of cellular throughput forecasts under structural distribution shifts and telemetry missingness.

To ensure total reproducibility and scientific rigor:
1. All partitions are partitioned chronologically by calendar collection dates (clusters) rather than independent row sampling.
2. The split protocol enforces zero leakage between training, validation, source calibration, target calibration, and evaluation partitions.
3. Every experiment explicitly declares its regime category (`experiment_type='within_domain'` or `'transfer'`).

---

## 2. Experimental Regimes

The benchmark formulates four complementary distribution-shift regimes originating from source domain **Operator 1 (2020–2021 Campaign)**:

```
                      +---------------------------------------+
                      |   Source Domain: Op1 (2020-2021)      |
                      |   150 Causal Sessions (7 Dates)       |
                      +---------------------------------------+
                                          |
         +--------------------------------+--------------------------------+
         |                                |                                |
         v                                v                                v
+------------------+             +------------------+             +------------------+
| E0: Within-Domain|             | E1: Temporal     |             | E2: Cross-Op     |
| Op1 2021 -> Op1  |             | Op1 2021 -> Op1  |             | Op1 2021 -> Op2  |
| 2021 (Late Suffix|             | 2023 (New Year)  |             | 2021 (Diff Net)  |
+------------------+             +------------------+             +------------------+
                                          |
                                          v
                                 +------------------+
                                 | E3: Joint Shift  |
                                 | Op1 2021 -> Op2  |
                                 | 2023 (Time + Op) |
                                 +------------------+
```

### 2.1 E0: Within-Domain Temporal Benchmark (Op1 2021 $\to$ Op1 2021)
- **Goal:** Benchmark baseline forecasting reliability under stationary network topology and identical operator radio configurations, evaluating temporal drift over a 6-week window.
- **Partitioning Strategy:** 5-way disjoint chronological day partition (35% Train / 10% Val / 15% Source Calib / 15% Target Calib Pool / 25% Fixed Test Suffix).
  - *Train:* 57 sessions across 2 days (`17.12.2020`, `04.01.2021`). Mean $y = 17.98$ Mbps.
  - *Validation:* 9 sessions across 1 day (`05.01.2021`). Mean $y = 5.06$ Mbps.
  - *Source Calibration:* 33 sessions across 1 day (`06.01.2021`). Mean $y = 20.75$ Mbps.
  - *Target Calibration Pool:* 10 sessions across 1 day (`11.01.2021`). Mean $y = 50.93$ Mbps.
  - *Fixed Test Suffix:* 41 sessions across 2 days (`14.01.2021`, `27.01.2021`). Mean $y = 49.28$ Mbps.
- **Budget Sizing:** Budgets $K \in \{0, 1, 2, 5, 8, 9, 10\}$ are extracted from the 10-session target pool. Budget $K=15$ is marked **unavailable** (`None`) without artificial substitution.

### 2.2 E1: Campaign Temporal Transfer (Op1 2021 $\to$ Op1 2023)
- **Goal:** Benchmark multi-year temporal transfer across network infrastructure upgrades (Release 15 NSA $\to$ Release 16 NSA) and environmental scenarios (outdoor drive $\to$ indoor/outdoor walk).
- **Source Partitioning (Op1 2021):** Chronological 60/20/20 split.
  - *Train:* 99 sessions (4 days). Mean $y = 17.73$ Mbps.
  - *Val:* 30 sessions (2 days). Mean $y = 59.83$ Mbps.
  - *Source Calib:* 21 sessions (1 day). Mean $y = 34.99$ Mbps.
- **Target Partitioning (Op1 2023):** Chronological 40/60 split.
  - *Target Calib Pool:* 145 sessions across 4 days (`29.03.2023` to `05.05.2023`). Mean $y = 26.39$ Mbps.
  - *Target Test:* 139 sessions across 7 days (`09.05.2023` to `05.07.2023`). Mean $y = 39.73$ Mbps.
- **Budget Sizing:** All budgets $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$ are fully supported.

### 2.3 E2: Cross-Operator Transfer (Op1 2021 $\to$ Op2 2021)
- **Goal:** Benchmark transfer across competing cellular operators deployed in the same geographical city during the same time period. Evaluates disparate base station topologies, carrier frequencies, and scheduler configurations.
- **Source Partitioning:** Op1 2021 (same leak-free source model trained on 99 sessions).
- **Target Partitioning (Op2 2021):** Chronological 40/60 split of Operator 2.
  - *Target Calib Pool:* 97 sessions across 5 days (`13.12.2020` to `17.12.2020`). Mean $y = 44.61$ Mbps.
  - *Target Test:* 256 sessions across 8 days (`05.01.2021` to `27.01.2021`). Mean $y = 30.36$ Mbps.
- **Budget Sizing:** All budgets $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$ are fully supported.

### 2.4 E3: Joint Shift (Op1 2021 $\to$ Op2 2023)
- **Goal:** Benchmark simultaneous cross-operator and multi-year temporal distribution shift. Represents the most severe operational transfer scenario.
- **Source Partitioning:** Op1 2021 (same leak-free source model).
- **Target Partitioning (Op2 2023):** Chronological 40/60 split.
  - *Target Calib Pool:* 111 sessions across 5 days (`29.03.2023` to `09.05.2023`). Mean $y = 23.75$ Mbps.
  - *Target Test:* 103 sessions across 7 days (`27.05.2023` to `05.07.2023`). Mean $y = 52.99$ Mbps.
- **Budget Sizing:** All budgets $K \in \{0, 1, 2, 5, 8, 9, 10, 15\}$ are fully supported.

---

## 3. Calibration Budget Extraction Specification

Target calibration instances are drawn strictly in chronological order from the target calibration pool prefix:
$$\mathcal{D}_{\text{cal}}^{(K)} = \{ (x_i, y_i) \}_{i=1}^K \subset \mathcal{D}_{\text{cal\_pool}}$$

- For $K = 0$: No target data is utilized. The calibrator relies exclusively on the frozen source quantile $q_{\text{source}}$.
- For $K \in \{1, 2, 5, 8\}$: Target data is collected, but finite-sample conformal quantile cannot activate (Lemma 1). The calibrator safely falls back to $q_{\text{source}}$.
- For $K = 9$: Target recalibration activates for the first time ($\lceil 10 \times 0.90 \rceil = 9$).
- For $K = 10, 15$: Target recalibration refines non-conformity quantiles.
- **Unsupported Budget Rule:** When $|\mathcal{D}_{\text{cal\_pool}}| < K$ (e.g. $K=15$ in E0), `splits.target_prefix_sessions[K]` returns `None`. Downstream runners record `-` (unavailable) rather than substituting historical data.

---

## 4. Production Split Contract

In `src/data/splits.py`, the function `create_experiment_splits` enforces:
1. `experiment_type`: Mandatory specification (`'within_domain'` or `'transfer'`).
2. Disjointness Assertion:
   $$\forall A, B \in \{\text{train}, \text{val}, \text{source\_calib}, \text{target\_calib\_pool}, \text{target\_test}\}, A \cap B = \emptyset$$
3. Immutability: Slices are extracted as deep copies (`.copy()`), preventing accidental index contamination.

