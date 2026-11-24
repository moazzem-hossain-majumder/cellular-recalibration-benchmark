# Data, Software, and Dependency Licensing Inventory

This document separates repository-authored code and manuscript permissions from upstream third-party dataset and tooling licenses. Raw third-party datasets and compiled dependency binaries are excluded from repository commits and publication archives (`paper/submission_package.zip`).

## 1. Author-Originated Software and Artifacts
- **Scope:** Original source code (`src/`), benchmark and audit scripts (`scripts/`), configuration files (`configs/`), test suites (`tests/`), and author-written documentation/LaTeX templates (`paper/`).
- **License:** MIT License (see root `LICENSE`).
- **Copyright Holder:** Md. Moazzem Hossain Majumder (2026).

## 2. Third-Party Cellular Measurement Datasets (Excluded from Redistribution)
Reproducers retrieve external datasets directly from upstream providers using checksum-pinned scripts (`scripts/download_data.py`, `scripts/fetch_nuwins_drive3.py`, `scripts/validate_nuwins_drive2.py`, `scripts/replay_oslo_playback.py`). Upstream terms apply independently:

| Dataset Release | Repository Scripts / Usage | Upstream License / Terms | Redistribution in Repo/ZIP |
|---|---|---|---|
| **Rome 2020–2021** (Zenodo `8224890`) | Primary training, validation, source calibration, E0/E2, pre-2023 baseline | CC BY 4.0 | Excluded (pinned SHA-256 manifest only) |
| **Rome 2023 Active Tests** (Zenodo `14073311`) | E1/E3 target transfer and Ookla trace clock replay | CC BY 4.0 | Excluded (pinned SHA-256 manifest only) |
| **NUWiNS PAM 2025 Multi-Carrier** | US Drive 2 & Drive 3 replication (AT&T, T-Mobile, Verizon) | CC0 1.0 Public Domain (scholarly citation retained) | Excluded (fetched via pinned Git LFS pointers) |
| **UCC 5G Production Dataset** (`uccmisl/5Gdataset`) | Chronological driving-download & Sirhan external comparison | Repo code under GPL-3.0; raw measurement ZIP has no standalone permissive grant | Excluded from repository and ZIP |
| **Sirhan Analysis Deposit** (Mendeley `ncbdm2c36d/1`) | Published 30-seed external comparison protocol (`compare_sirhan_external.py`) | CC BY 4.0 (author deposit explicitly excludes raw UCC traces) | Excluded |
| **Oslo HSDPA Logs** (Simula / Riiser et al.) | Norwegian lag transfer and exploratory playback replay | Citation requested; no explicit OSI/CC raw-log license verified | Excluded |

**Important Legal Note:** Derived forecast ledgers stored under `results/` (`opportunities.csv.gz`, `matched_cost_actions.csv.gz`) include aggregated or aligned throughput/signal fields derived from public sources; users redistributing forks must respect upstream CC BY 4.0 attribution and confirm upstream dataset permissions for their jurisdiction.

## 3. Build Tools and Software Dependencies
Full installed metadata and license-file SHA-256 digests are archived in `results/runs/dependency_licenses.json`. Key distinctions:
- **Scientific Python stack** (`numpy`, `pandas`, `scipy`, `scikit-learn`, `torch`, `matplotlib`, `seaborn`, `pypdf`, `pytest`): BSD-3-Clause / MIT / PSF / Apache-2.0.
- **PDF Text Verification (`PyMuPDF`):** Dual-licensed under **AGPL-3.0** and commercial terms (`https://pymupdf.readthedocs.io/en/latest/about.html`); used solely as a local/CI QA validator and **not** bundled or redistributed in `paper/submission_package.zip`.
- **External CLI Tools (`Tectonic`, `Pandoc` via `pypandoc_binary`):** Invoked out-of-process during manuscript building; carry upstream GPL-2.0+ (`Pandoc`) and MIT (`Tectonic`) obligations independently.

## 4. Target Publication Venue Alignment
- **Primary Target:** *IEEE Transactions on Network and Service Management (IEEE TNSM)* (two-column `IEEEtran` journal style, empirical measurement & evaluation methodology scope).
- **Alternate Empirical Venue:** *IEEE Open Journal of the Communications Society (IEEE OJ-COMS)*.
- **IEEE Submission Compliance:** Formatted cleanly under `IEEEtran [journal,10pt]`; zero overfull horizontal boxes, verified BibTeX (`IEEEtran.bst`), separated supplementary appendix (`paper/supplementary.pdf`), and explicit AI-tool acknowledgment retained per IEEE author policy.
