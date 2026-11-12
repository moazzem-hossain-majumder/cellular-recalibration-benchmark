# External data provenance

Sources inspected on 12 November 2026. The SHA-256 pins for every Norwegian log, the Irish data ZIP, the analysis ZIP and the three executed upstream scripts are in results/external_validation/dataset_manifest.json.

**Norway.** Riiser, Vigmostad, Griwodz and Halvorsen released TCP streaming measurements on Telenor's Norwegian HSDPA network. We selected the first route in the publisher's route table, Ljansbakken–Jernbanetorget, before comparing outcomes. We obtained all 17 report logs in that route directory over HTTPS. The publisher asks users to cite the dataset. The landing page gives no explicit open-data license for the raw logs; the repository provides checksums and download instructions. Each record gives a Unix timestamp, local monotonic clock, position, bytes received and elapsed milliseconds. It contains no LTE/NR signal fields. [Publisher and format](https://datasets.simula.no/hsdpa/) · [Route directory](https://datasets.simula.no/downloads/hsdpa-tcp-logs/bus.ljansbakken-oslo/)

**Ireland.** Raca et al. released commercial measurements separately from their simulator. We used the production ZIP in repository commit 306d92eba81cb4f1195d8b8eba625666a02a10ec. The repository contains a GPL-3.0 license and asks for citation. Its README gives no separate license specific to the measurement ZIP. The simulator does not enter any table. Sirhan's version 1 code and derived data deposit carries CC BY 4.0. The deposit excludes the raw traces. Its Python 3.12/scikit-learn 1.8 environment differs from the recorded local Python 3.11/scikit-learn 1.9 rerun. Published rounded values and rerun values are displayed separately. [Raw measurements](https://github.com/uccmisl/5Gdataset) · [Analysis release](https://data.mendeley.com/datasets/ncbdm2c36d/1) · [Published comparator](https://www.mdpi.com/2673-8732/6/4/92)


## Raw-data commands for the Irish reproduction

From the repository root, with Git, curl and the Python dependencies installed:

```sh
git clone https://github.com/uccmisl/5Gdataset.git data/raw/ucc-external
git -C data/raw/ucc-external checkout 306d92eba81cb4f1195d8b8eba625666a02a10ec
curl -fL https://data.mendeley.com/public-api/zip/ncbdm2c36d/download/1 -o data/raw/sirhan-v1.zip
python scripts/compare_sirhan_external.py data/raw/sirhan-v1.zip
python scripts/audit_external_traces.py
python scripts/report_sirhan_external.py
python scripts/validate_irish_groups.py
```

The archived tree fits its median imputer on training traces alone. The raw-data loader and feature script construct a trace-local lagged series, then the released multiseed script repartitions traces. The wrapper alters paths and inserts paired scoring of minimum and persistence. The chronological extension uses the consolidated pre-imputation file independently of those splits.
