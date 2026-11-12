# Comparable transfers and distinct endpoints

| Dataset | Technology | Prediction task | Horizon | Calibration | Test split |
|---|---|---|---|---|---|
| Rome earlier/later | Commercial LTE and non-standalone 5G | Next completed or reset-defined test endpoint | Variable session length | Source or target chronological prefix | Fixed date suffix by operator |
| Rome later clock | Same radios | Final numeric rate in upcoming clock window | Next minute; second-minute sensitivity | Frozen source predictor, target or source offset | Same seven suffix dates per operator |
| Ireland published | Commercial LTE/5G | Next recorded row | Row-based, not strictly one elapsed second | Per-split trace calibration | 30 overlapping whole-trace partitions |
| Ireland chronological | Same recordings | Strictly later next-row measurement | Variable measured interval | First ten or complete earlier pool | Last 16 of 27 dates |
| Norway | Telenor HSDPA | Bytes per elapsed time in following valid interval | One measurement interval | Ten earlier bus or metro labels | Two bus or three metro dates |

**Matched transfer.** After the first public route (bus), add the second listed route (metro). All 17 metro logs are downloaded using metro_manifest.json, alongside 17 bus logs. Use the original bus time cutoffs for both routes. Train before 1 October 2010; calibrate after that cutoff and before 30 January 2011. Predict on the metro suffix with the same two lag features and endpoint. The 2,893 intervals come from four logs on three dates. The bus training partition has three dates and the metro training partition five. This increases route diversity within a single historical operator. Run `python scripts/metro_transfer.py`. [Publisher](https://datasets.simula.no/hsdpa/)

| Train / calibrate | MAE Mbps | V (%) | U (%) |
|---|---:|---:|---:|
| Bus / bus | 0.325 | 0.24 | 5.30 |
| Bus / metro | 0.325 | 11.99 | 28.13 |
| Metro / bus | 0.161 | 86.17 | 95.64 |
| Metro / metro | 0.161 | 0.80 | 29.20 |

A lower point error does not repair a mismatched offset. In Rome the frozen earlier Op1 tree is also evaluated unchanged on later Op2. There is no scientifically matched pooled estimate across Rome, Ireland and Norway. The Norwegian release has no alternative operator or matching NR input. A Norwegian refit and an Irish trace reproduction are separate from frozen Rome transfer.

**Modern data search.** DoNext documents mobile iPerf test starts and radio measurements across Dortmund, but the authors removed exact mobile timestamps for privacy. A mapping from pseudonymous measurement runs to disjoint collection dates would be needed to reproduce this paper's calendar design. The static release emphasizes passive and latency measurements. No result on Dortmund is claimed. MONROE SOMETIME provides an openly downloadable 4G achievable-throughput archive, and the UMN 5G release includes stationary download and on/off disruption experiments. Neither has been harmonized here to the same clock endpoint, feature schema and operator/date blocks. Independent test starts remain a stronger next benchmark than a pooled score across incompatible tasks. [DoNext paper](https://doi.org/10.1109/TMLCN.2025.3564239) · [Release documentation](https://gitlab.kn.e-technik.tu-dortmund.de/donext-the-dortmund-dataset/dortmund-dataset-public/-/blob/main/README.md) · [MONROE archive](https://zenodo.org/records/1300512) · [UMN real measurements](https://github.com/mssn/5GMeas-Dataset/tree/main/imc-5g-onoff)
