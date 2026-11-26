# Cellular Throughput Recalibration Benchmark

[![Research validation](https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark/actions/workflows/tests.yml/badge.svg)](https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark/actions/workflows/tests.yml)

**Central Research Question:** *Do nominally matched cellular throughput recalibration policies remain comparable once evaluated over realized measurement opportunities, finite-record missing-outcome bounds, and campaign-level dependence?*

Across six retrospective cellular cohorts (`16` physical campaign-dates across `3` campaigns: Rome 2023, US Drive 3, and Ireland driving logs) and four held-out public archives (`26` additional dates across `3` campaigns: Rome Capacity Op1/Op2, Oslo Multi-Route Commute, and Ireland Static) evaluated under frozen tree predictors and fixed policies, conditional upper violation risk `R_+^hi` spans **`9--68%`** across mobile cohorts (far above nominal `alpha = 0.10`) while supported measured throughput `U` generally remains **`1--3%`**. High-risk mobile campaigns (`Rome_2023`, `Rome_Capacity`, `US_Drive3`) are simultaneously the low-throughput campaigns (`47.5--54.2%` median `R_+^hi` vs. `0.35--1.35%` median `U`), and leaving out any single physical campaign keeps mobile median conditional risk tightly at **`45.8--49.3%`**. This repository provides an open-source measurement-accounting library (`src/audit/recalibration_audit.py`), practitioner checklist, and CLI tool (`scripts/audit_policy.py`) separating realized queries, finite-record bounds `[e/M, (e+m)/M]`, selective decomposition `R = (M/N) R_+`, offer-weighted vs. equal-cluster pooling, and estimand-matched relative TOST equivalence (`Equal-cluster` vs. `Pooled-ratio`). Even against a coarse `+-50%` screening margin (paired with `+-25%` sensitivity), `3` campaigns per scope cannot reliably establish utility equivalence.

All evidence is retrospective from public archives and no live field validation was performed; it does not cover other devices, operators, measurement tools, or closed-loop deployment.

## How Measurement Accounting Flips Conclusions

| Evaluation Regime | Naive / Conventional Appearance | Audited Accounting Reality |
|---|---|---|
| **Shared-offer rate shrinkage (`Ireland C=10`)** | `MARUR` cuts all-issued risk (`R_all`) and removes `14` failures across `159` shared offers vs. `Periodic` | Cuts supported throughput (`4.117% -> 1.129%`) by shrinking offered rates rather than better tail calibration |
| **Nominal cap vs. realized queries (`Rome E1 C=40`)** | Equal nominal `C_new=40` cap suggests fair comparison (`2.02%` vs. `1.01% U`) | `MARUR` spends `40` new queries vs. `Periodic` spending only `16`; `MARUR` positive risk stays `44.83%` |
| **Offer-weighted vs. equal-cluster (`HeldOut PACER C=10`)** | Offer-weighted pooling claims **`-23.41 pp`** conditional upper-risk reduction over `Periodic` | Equal-cluster mean gives **`+0.37 pp`** risk change and **`-3.29 pp`** equal-cluster `U` (`pEq50 = 0.5369`) |
| **Naive date-level vs. campaign clustering (`HeldOut PACER C=40`)** | Naive `G=26` date TOST passes `+-50%` equal-cluster equivalence (`p=0.0071`) and `+-2 pp` (`p=0.0132`) | Adjusting for `k=3` campaigns (`G_eff = 6.73/26`) reverses both to inconclusive (`p=0.1153` / `p=0.1388`), and `PoolRat` fails (`p=0.4155`) |

## Protocol Separation: Frozen vs. Exploratory

- **Source training:** The primary `HistGBM` predictor was trained solely on `57` earliest `Rome Op1` (`2021`) source rows without future target leakage.
- **Non-blind SHA-256 frozen held-out protocol:** `PACER` hyperparameters were checksum-locked ([`configs/pacer.json`](configs/pacer.json), [`docs/PACER_FROZEN_PROTOCOL.md`](docs/PACER_FROZEN_PROTOCOL.md)) prior to scoring the four held-out public archives, explicitly disclosed as designed after inspecting retrospective `MARUR` failures (not blind discovery).
- **Post-hoc exploratory robustness suite:** All `W in {10, 20, 40}`, `alpha in {0.05, 0.10, 0.20}`, source-only alternative predictors, `10`-cohort `LOCO`, `6`-campaign `LOCampO`, and campaign-dependence adjustments run in [`results/exploratory/sensitivity/`](results/exploratory/sensitivity/) without changing any frozen configuration or benchmark metric.

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
| `[Equal-cluster] refU`, `dU`, `Rel TOST` | Equal-cluster mean baseline `U` (`undef_U_excl` omitted), mean `dU` (`%` of `eq_ref_u`), `SD`, `MDE80`, `+-50%`/`+-25%` & `+-1`/`+-2 pp` TOST `p` |
| `[Pooled-ratio] refU`, `PoolRel`, `Rel TOST` | Pooled aggregate baseline `U`, ratio `(U_cand/U_ref - 1)`, cluster bootstrap `90%`/`95%` CIs, and pooled-ratio TOST (`90% CI inside margin`) |
| `Pool dR+hi` vs `Eq dR+hi` | Offer-weighted vs. equal-cluster conditional risk difference exposing offer-count pooling divergences |

| Emitted Warning Flag | Trigger Condition & Actionable Interpretation |
|---|---|
| `fewer than <N> clusters` | Cluster count `G` is below `--min-clusters` (or campaign-level `G_eff` is smaller due to clustering) |
| `zero positive offers` | Policy makes `0` positive offers in one or more clusters (flagged separately from zero-`U` clusters) |
| `queries unmatched across policies` | Realized `Q_new` differs between candidate and reference at the same nominal query cap |
| `pooling sensitivity` | Offer-weighted `dR+hi` and equal-cluster `dR+hi` diverge markedly across heterogeneous cohorts |
| `equal-cluster relative TOST +-50% inconclusive` | Equal-cluster `t`-TOST `max(p) >= 0.05` against `+-50%` of `ref_equal_u_pp` |
| `pooled-ratio TOST +-50% inconclusive` | Cluster bootstrap `90%` CI on `pooled_rel_du_pct` extends beyond `+-50%` |

## Results at a Glance

| Scope | Comparison (HistGBM, Recorded) | Physical Units (`k` Camp) | Key Empirical Metric | Observed Value |
|---|---|---|---|---|
| All mobile (`54` cells) | `Periodic`, `MARUR`, `PACER` (`C=10, 40`) | 42 dates (`5` mob / `6` tot) | Conditional upper risk `R+^hi` & supported `U` | `9--68%` (`8.8--68.2%`, med `47.6%`) / `1--3%` |
| Retrospective (`G=16`, `k=3`) | MARUR vs. Periodic (`C=10`, EqualCl) | 16 dates (`3` camp, `Z0=4`) | `EqRefU`, `EqdU` (`%` of eq ref), `MDE80` & `+-50%` TOST | `1.52%`, `-0.09 pp (-6.2%)`, `1.65 pp` (`p=0.1228`) |
| Retrospective (`G=16`, `k=3`) | MARUR vs. Periodic (`C=10`, PoolRat) | 16 dates (`3` camp, `Z0=4`) | `PlRefU`, `PoolRel` (`90%` boot CI) & pooled `dU` | `0.60%`, `+35.3%` (`-44.3 to +207.3%`, `p=0.4145`) / `+0.21 pp` |
| Campaign adj. (Retro `k=3`) | PACER vs. Periodic (`C=10`, EqualCl) | 3 camp (`G_eff=14.77/16`) | Naive `p` -> Donner `Adjp50` / Hier `90%` eq-rel CI | `p=0.0430` -> `0.0498` / `[-45.3, +268.9%]` |
| Campaign adj. (Retro `k=3`) | MARUR vs. Periodic (`C=10`, EqualCl) | 3 camp (`G_eff=3.84/16`) | Naive `p` -> Donner `Adjp50` / Abs `+-1 / +-2 pp` TOST | `p=0.1228` -> `0.2988` / naive `p=0.0609 / 0.0018` |
| Held-out public (`G=26`, `k=3`) | PACER vs. Periodic (`C=10`, OfferWtd / PoolRat) | 26 dates (`3` camp, `Z0=4`) | Offer-wtd `dPosHi` / `PlRefU` & `PoolRel` (`90%` boot) | `-23.41 pp` (`-37.04 to -5.91`) / `1.01%`, `+46.9%` (`-1.5 to +114.7%`) |
| Held-out public (`G=26`, `k=3`) | PACER vs. Periodic (`C=10`, EqualUnit / EqualCl) | 22/26 active (`3` camp) | `EqdPosHi` / `EqRefU`, `EqdU` (`MDE80`, `pEq50`) | `+0.37 pp` / `6.32%`, `-3.29 pp` (`4.01 pp`, `p=0.5369`) |
| Held-out public (`G=26`, `k=3`) | PACER vs. Periodic (`C=40`, EqualCl / CampAdj) | 26 dates (`G_eff=6.73/26`) | Naive `pEq50` -> `Adjp50` / Abs `MDE80` (`p=+-2 pp`) | `p=0.0071` -> `0.1153` / `2.46 pp` (`0.0132 -> 0.1388`) |
| Held-out public (`G=26`, `k=3`) | PACER vs. Periodic (`C=40`, OfferWtd) | 26 dates (`3` camp) | Offer-weighted `dPosHi` (95% boot CI) | `-0.83 pp` (-16.13 to +11.46) |
| All cohorts (`G=42`, `k=6`) | PACER vs. Periodic (`C=40`, OfferWtd / EqualCl) | 42 dates (`6` camp) | Offer-wtd `dPosHi` / `Adjp50` & Hier `90%` rel CI | `+3.29 pp` (`-7.49 to +12.49`) / `p=0.0341`, `[-50.6, +93.9%]` |
| Theory bound audit | PACER Theorem 1 vs. trivial `0.9A` | 40 cells (`6` camp) | Informative cells (`B_1 < 0.9A`) | `4/40` (1/20 C=10; 3/20 C=40) |
| Leave-One-Cohort-Out | Drop any 1 of 10 cohorts (`C=10`) | 35–42 dates | Mobile median `R+^hi` (range) | `47.1–49.3%` |
| Leave-One-Campaign-Out | Drop any 1 of 6 campaigns (`C=10`) | 27–39 dates (`5` rem camp) | Mobile median `R+^hi` & all-`U` median | `45.8–49.3%` / `0.61–1.28%` |

## Full Reproduction and CI

To rebuild all experiments, execution logs (`results/runs/execution.json`), and manuscripts from raw archives (set `TECTONIC` to your `tectonic` binary path if not on `PATH`):

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
python scripts/audit_policy.py examples/worked_heldout_c10_ledger.csv --reference Periodic --min-clusters 20
python scripts/generate_experiment_manifest.py --verify
```

## Data, Licensing, and Archive History

- **Code & Assets:** Repository source code is released under the MIT License ([LICENSE](LICENSE)). Third-party public datasets retain their upstream terms (Zenodo 8224890/14073311 CC BY 4.0, Raca et al. 5G trace dataset, Riiser HSDPA logs, NUWiNS PAM 2025 traces) and are excluded from redistribution ([docs/DATA_AND_SOFTWARE_LICENSING.md](docs/DATA_AND_SOFTWARE_LICENSING.md)).
- **Protocols & Result Audits:** Active data, mathematical, statistical, citation check ([docs/CITATION_CHECK.md](docs/CITATION_CHECK.md)), and frozen configuration checksum documents live in [docs/](docs/).
- **Historical Archive:** Superseded planning drafts, archived helper scripts ([scripts/archive/](scripts/archive/)), internal scorecards, and historical phase logs are stored in [docs/archive/](docs/archive/).
