# Cellular Throughput Recalibration Benchmark

[![Research validation](https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark/actions/workflows/tests.yml/badge.svg)](https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark/actions/workflows/tests.yml)

This repository provides a practical measurement-accounting library (`src/audit/recalibration_audit.py`), CLI tool (`scripts/audit_policy.py`), and multi-cohort cellular benchmark asking **when recalibration feedback helps cellular throughput commitments, and how unequal probe costs, missing responses, and heavy abstention make apparent improvements misleading**. In these public archives, with these frozen predictors and policies, sparse recalibration did not reliably improve commitments. Across six retrospective cohorts (`16` physical campaign-dates across Rome 2023, US Drive 3, and Ireland driving logs) and four held-out public archives (`26` additional physical dates spanning Rome Capacity Op1/Op2, Oslo Multi-Route Commute, and Ireland Static), the framework separates realized query attempts, finite-record missing-outcome bounds `[e/M, (e+m)/M]`, positive-offer selective decomposition `R = (M/N) R_+`, relative and absolute physical-cluster equivalence, campaign-level dependence sensitivity, and pooling-weight checks comparing `MARUR` (Missingness-Aware Recalibration under Uncertainty and Risk) and `PACER` (Horizon-Paced Selective-Offer Conformal Control) against `Frozen`, `Periodic`, `Early`, `Random`, `ACI`, and `DecayingOGD` baselines.

All evidence is retrospective from public archives and no live field validation was performed. Evidence from these archives also does not cover closed-loop congestion deployment, other user devices or operators, alternative measurement tools, or non-60s prediction horizons.

## Quick Start: Auditing Any Policy Ledger

Install dependencies in Python `3.11` and run the accounting CLI directly on the included held-out `C=10` worked example CSV (zero trace downloads required):

```sh
python -m pip install -r requirements.txt -c constraints-research.txt
python scripts/audit_policy.py examples/worked_heldout_c10_ledger.csv --reference Periodic --min-clusters 20
```

### CLI Output Fields and Deployment Warnings

| Output Field | Meaning & Formula / Role |
|---|---|
| `A`, `R+`, `R_all`, `U` | Offer frequency `M/N`, finite-record bounds `[e/M, (e+m)/M]`, all-issued identity `R = A*R_+`, and supported throughput `U` |
| `Q_new`, `id_err` | Realized new probe attempts after initialization and max identity error `|R_all - A*R+|` (exact machine precision) |
| `PoolRel dU`, `Rel TOST` | Pooled relative utility change relative to baseline `U` (`+-50%` primary / `+-25%` sensitivity), cluster bootstrap CI, zero-`U` cluster count |
| `Eq dU`, `MDE80`, `Abs TOST` | Equal-cluster mean `dU`, between-cluster SD, 80%-power minimum detectable effect, and `+-1 / +-2 pp` TOST `p`-values |
| `Pool dR+hi` vs `Eq dR+hi` | Offer-weighted vs. equal-cluster conditional risk difference exposing large offer-count pooling shifts |

| Emitted Warning Flag | Trigger Condition & Actionable Interpretation |
|---|---|
| `fewer than <N> clusters` | Cluster count `G` is below `--min-clusters` (or campaign-level `G_eff` is smaller due to clustering) |
| `zero positive offers` | Baseline or candidate makes `0` positive offers in one or more clusters (excluded from per-cluster ratio / conditional risk) |
| `queries unmatched across policies` | Realized `Q_new` differs between candidate and reference at the same nominal query cap |
| `pooling sensitivity` | Offer-weighted `dR+hi` and equal-cluster `dR+hi` diverge markedly across heterogeneous cohorts |
| `relative TOST +-50% inconclusive` | Relative TOST `max(p) >= 0.05` against `+-50%` of baseline `U` (cannot rule out large relative gains or losses) |

## Results at a Glance

| Scope | Comparison (HistGBM, Recorded) | Physical Units | Key Empirical Metric | Observed Value |
|---|---|---|---|---|
| Retrospective (`G=16`) | MARUR vs. Periodic (`C=10`) | 16 dates (4 zero-`U` excl) | Pooled relative `dU` (95% boot CI) & `+-50%/+-25%` TOST | +35.3% (-55.5 to +260.4%), `p=0.3564 / 0.4602` |
| Retrospective (`G=16`) | MARUR vs. Periodic (`C=10`) | 16 dates | Equal-cluster `dU` (95% t-CI), `MDE80`, `+-1 / +-2 pp` TOST | -0.09 pp (-1.27 to +1.08), 1.65 pp (`p=0.0609 / 0.0018`) |
| Retrospective (`G=16`) | MARUR vs. Periodic (`C=10`) | 16 dates | Pooled absolute `dU` (95% boot CI) | +0.21 pp (-1.26 to +0.79) |
| Campaign dependence | MARUR `C=10` Retro / PACER `C=40` HeldOut | 3 campaigns / scope | Effective units `G_eff` (`ICC` / Donner `DEFF`) & `+-2 pp` TOST | `3.84/16` (`p=0.0971`) / `6.73/26` (`p=0.1388`) |
| Held-out public (`G=26`) | PACER vs. Periodic (`C=10`, OfferWtd) | 26 dates (4 zero-`U` excl) | Offer-weighted `dPosHi` & Relative `dU` (95% boot CI) | -23.41 pp (-37.04 to -5.91) / +46.85% (`p=0.9731`) |
| Held-out public (`G=26`) | PACER vs. Periodic (`C=10`, EqualUnit) | 22/26 active | Equal-unit `dPosHi` / `dU` (`MDE80`) | +0.37 pp / -3.29 pp (4.01 pp) |
| Held-out public (`G=26`) | PACER vs. Periodic (`C=40`, OfferWtd) | 26 dates | Offer-weighted `dPosHi` (95% boot CI) | -0.83 pp (-16.13 to +11.46) |
| Held-out public (`G=26`) | PACER vs. Periodic (`C=40`, EqualUnit) | 26 dates (2 zero-`U` excl) | `MDE80`, `+-1 / +-2 pp` TOST & `+-50%` rel TOST | 2.46 pp (`p=0.1261 / 0.0132`) & rel `p=0.2508` |
| All cohorts pooled (`G=42`) | PACER vs. Periodic (`C=40`, OfferWtd) | 42 dates | Offer-weighted `dPosHi` (95% boot CI) | +3.29 pp (-7.49 to +12.49) |
| Theory bound audit | PACER Theorem 1 vs. trivial `0.9A` | 40 cells | Informative cells (`B_1 < 0.9A`) | 4/40 (1/20 C=10; 3/20 C=40) |
| Leave-One-Cohort-Out | Drop any 1 of 10 cohorts (`C=10`) | 35–42 dates | Mobile median `R+^hi` (IQR) | 47.1–49.3% |

Across all 54 mobile-cohort `HistGBM`/recorded `C in {10, 40}` cells (`Periodic`, `MARUR`, `PACER`), conditional upper violation risk `R_+^hi` spans `9--68%` (`8.8%--68.2%`, median `47.6%`, far above nominal `alpha = 0.10`), while supported measured throughput `U` typically remains `1--3%` (`Ireland Static` stays at `4.7%--8.1%`). Extended exploratory sweeps over windows `W in {10, 20, 40}`, nominal levels `alpha in {0.05, 0.10, 0.20}`, source-only predictors (`ThroughputResNet`, `QuantileGBM_p10`, `HistGBM_Clock112`, Oslo pre-2010 `QuantileGBM_p10`, `Persistence`), campaign-level dependence (`results/exploratory/sensitivity/campaign_dependence.csv`), and Leave-One-Cohort-Out reside strictly under [`results/exploratory/sensitivity/`](results/exploratory/sensitivity/).

## Full Reproduction and CI

To rebuild all experiments and manuscripts from raw archives (set `TECTONIC` to your `tectonic` binary path if not on `PATH`):

```sh
python scripts/reproduce_all.py
```

For fast local or hosted CI verification without raw archive downloads (matching [`.github/workflows/tests.yml`](.github/workflows/tests.yml)):

```sh
python -m pytest tests/unit -ra
python scripts/validate_marur_audit.py
python scripts/audit_trip_level_inference.py
python scripts/validate_pacer.py
python scripts/validate_manuscript_consistency.py
python scripts/generate_experiment_manifest.py --verify
```

## Data, Licensing, and Archive History

- **Code & Assets:** Repository source code is released under the MIT License ([LICENSE](LICENSE)). Third-party public datasets retain their upstream terms (Zenodo 8224890/14073311 CC BY 4.0, Raca et al. 5G trace dataset, Riiser HSDPA logs, NUWiNS PAM 2025 traces) and are excluded from redistribution ([docs/DATA_AND_SOFTWARE_LICENSING.md](docs/DATA_AND_SOFTWARE_LICENSING.md)).
- **Protocols & Result Audits:** Active data, mathematical, statistical, citation check ([docs/CITATION_CHECK.md](docs/CITATION_CHECK.md)), and frozen configuration checksum documents live in [docs/](docs/).
- **Historical Archive:** Superseded planning drafts, archived helper scripts ([scripts/archive/](scripts/archive/)), internal scorecards, and historical phase logs are stored in [docs/archive/](docs/archive/).
