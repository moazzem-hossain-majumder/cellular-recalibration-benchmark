# Cellular Throughput Recalibration Benchmark

This repository provides an empirical measurement and causal-accounting benchmark asking **when recalibration feedback helps cellular throughput commitments, and how unequal probe costs, missing responses, and heavy abstention make apparent improvements misleading**. Across six retrospective cohorts (`16` physical campaign-dates across Rome 2023, US Drive 3, and Ireland driving logs) and four held-out public archives (`26` additional physical dates spanning Rome Capacity Op1/Op2, Oslo Multi-Route Commute, and Ireland Static), the framework separates realized query attempts, finite-record missing-outcome bounds `[e/M, (e+m)/M]`, positive-offer selective decomposition `R = (M/N) R_+`, and physical collection-unit cluster inference, comparing `MARUR` (Missingness-Aware Recalibration under Uncertainty and Risk) and `PACER` (Horizon-Paced Selective-Offer Conformal Control) against `Frozen`, `Periodic`, `Early`, `Random`, `ACI`, and `DecayingOGD` baselines under CPU-reproducible locked configurations.

## Results at a Glance

| Scope | Comparison (HistGBM, Recorded) | Physical Units | Key Empirical Metric | Observed Value |
|---|---|---:|---|---|
| Retrospective (`G=16`) | MARUR vs. Periodic (`C=10`) | 16 dates | Equal-cluster mean `dU` (95% t-CI) | -0.09 pp (-1.27 to +1.08) |
| Retrospective (`G=16`) | MARUR vs. Periodic (`C=10`) | 16 dates | Pooled `dU` (95% boot CI) | +0.21 pp (-1.26 to +0.79) |
| Held-out public (`G=26`) | PACER vs. Periodic (`C=10`, OfferWtd) | 26 dates | Offer-weighted `dPosHi` (95% boot CI) | -23.41 pp (-37.04 to -5.91) |
| Held-out public (`G=26`) | PACER vs. Periodic (`C=10`, EqualUnit) | 22/26 active | Equal-unit paired `dPosHi` | +0.37 pp (dU -3.29 pp) |
| Held-out public (`G=26`) | PACER vs. Periodic (`C=40`, OfferWtd) | 26 dates | Offer-weighted `dPosHi` (95% boot CI) | -0.83 pp (-16.13 to +11.46) |
| All cohorts pooled (`G=42`) | PACER vs. Periodic (`C=40`, OfferWtd) | 42 dates | Offer-weighted `dPosHi` (95% boot CI) | +3.29 pp (-7.49 to +12.49) |
| Theory bound audit | PACER Theorem 1 vs. trivial `0.9A` | 40 cells | Informative cells (`B_1 < 0.9A`) | 4/40 (1/20 C=10; 3/20 C=40) |
| Prospective pilot (`Task 6`) | Frozen harness (`run_prospective_validation.py`) | 0 trips | `prospective_trips_collected` | 0 (no live field trips yet) |

Across archived mobile cohorts under frozen `HistGBM`, positive-offer upper violation risk averages roughly `17--63%` (far above nominal `alpha = 0.10`), while supported measured throughput typically remains `1--3%`. Sensitivity analyses over calibration windows `W in {10, 20, 40}`, nominal levels `alpha in {0.05, 0.10, 0.20}`, and source-only alternative predictors (`ThroughputResNet`, `QuantileGBM_p10`, `HistGBM_Clock112`, `Persistence`) confirm these qualitative findings without altering frozen configs or held-out cohorts (`results/exploratory/sensitivity/`).

## Reproduction and CI

Use Python `3.11` with pinned constraints (and Tectonic on `PATH` or `TECTONIC` to recompile PDFs):

```sh
python -m pip install -r requirements.txt -c constraints-research.txt
python scripts/reproduce_all.py
```

For fast local or hosted CI verification without raw archive downloads (matching `.github/workflows/tests.yml`):

```sh
python -m pytest tests/unit -ra
python scripts/validate_marur_audit.py
python scripts/audit_trip_level_inference.py
python scripts/validate_pacer.py
python scripts/validate_manuscript_consistency.py
python scripts/generate_experiment_manifest.py --verify
```

To execute the frozen prospective harness once genuine chronological field logs are collected (`prospective_trips_collected = 0` currently), see [scripts/run_prospective_validation.py](scripts/run_prospective_validation.py) and [paper/supplementary.pdf](paper/supplementary.pdf).

## Data, Licensing, and Archive History

- **Code & Assets:** Repository source code is released under the MIT License ([LICENSE](LICENSE)). Third-party public datasets retain their upstream terms (Zenodo 8224890/14073311 CC BY 4.0, Raca et al. 5G trace dataset, Riiser HSDPA logs, NUWiNS PAM 2025 traces) and are excluded from redistribution ([docs/DATA_AND_SOFTWARE_LICENSING.md](docs/DATA_AND_SOFTWARE_LICENSING.md)).
- **Protocols & Result Audits:** Active data, mathematical, statistical, and experimental protocol documents live in [docs/](docs/).
- **Historical Archive:** Assistant handoff notes, internal scorecards, self-assessments, and superseded phase/reviewer logs are archived in [docs/archive/](docs/archive/).
