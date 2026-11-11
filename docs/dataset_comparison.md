# Dataset comparison and verification ledger

Checked 8 November 2026. **No raw datasets were downloaded or counted in this phase.** Repository pages, file inventories, documentation excerpts, and selected machine-readable metadata were inspected. 'Available' means a primary source exposes a record/file link; it does not mean byte-level acquisition and integrity checks have succeeded. Reported sample counts are publisher claims, not our measurements. Unknown values are explicitly retained.

## Verification levels

- **Metadata verified:** source exists, provenance documented, file inventory visible, reuse terms identified.
- **Listed, access not completed:** file links found, but authentication, download success, or licensing needs additional confirmation.
- **Conditional:** permission required, insufficiently documented, or unsuitable as primary evidence.

License summaries describe the verified license designation; downstream obligations must be preserved with the actual version. Publicly viewable data are not automatically licensed for every use. A software license must not casually be assumed to settle separate dataset rights.

## Comparison

| Dataset family | Evidence type / strength | Access and licensing | Main supported task | Principal limitation | Decision |
|---|---|---|---|---|---|
| PERFORM: 4G/NB-IoT/5G NSA | Commercial field measurements; strong institutional provenance | Zenodo file inventory and CC BY 4.0 API metadata verified | Throughput, latency, radio/coverage analysis | Active/passive alignment and usable independent sample count unverified | Preferred primary candidate |
| Chronicles active/passive | Later commercial campaigns; strong provenance | Both API records reachable; CC BY 4.0; separate archives | Temporal/operator transfer and service evolution | Related to earlier PERFORM work; do not double-count repeated older measurements | Preferred validation candidate |
| UCC 5G production dataset | Commercial field traces | Production ZIP listed; repository GPL-3.0; clarify scope for data redistribution | Sequential throughput and mobility | Application-dependent target; mixed repository also describes simulation | External replication candidate |
| Lumos5G | Commercial mmWave measurement study | Institutional download link; DataPort inaccessible to browser; CC BY 4.0 reported by BAMMO authors | Missing telemetry, throughput | Public subset versus full-study counts; different radio regime | Useful, access conditional |
| Telecom Italia Milan | Real operator-derived aggregate activity | Dataverse daily files; custom terms / ODbL documentation | Spatial/temporal activity forecasting | Old, aggregated, not PRB/energy/absolute capacity labels | Viable but weaker novelty |
| WiSig | Real experimental RF captures | Institutional downloads; CC BY-NC-SA 4.0 | Receiver/channel robustness, identification | Wi-Fi, noncommercial, overlapping subsets, limited days | Good signal-processing candidate |
| RANalyzer | Real over-the-air private 5G testbed | GitHub raw/processed files; CC BY 4.0 | Software-change performance monitoring | Conflicting counts/date ranges and inferred fault labels | Strong systems candidate with gates |
| NetMob23 | Real operator service-demand aggregates | Restricted application/agreement; continued usage requires extension | Modern multi-region traffic | Current authorization not obtained; substantial volume | Optional only |
| ColO-RAN / traffic twinning | Hardware/software experiments with RF emulation | Institutional descriptions; license not verified | Controlled RAN experiments | Not commercial field radio evidence | Supplementary only |
| DeepSense 6G | Real multimodal sensing/communication | Official scenarios; specific reuse terms not resolved here | Beam/sensing prediction | Overlap with existing DeepSenseV2V | Not advanced |
| BTRC tower statistics | Official aggregate statistics | Public page; reuse license not verified | Industry context | No site-level failures/KPIs | Context only |

## D1. A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements

- **Publisher/institutions:** Kousias and collaborators, University of Oslo, Karlstad University, Sapienza University of Rome and Rohde & Schwarz; hosted by Zenodo/PERFORM.
- **Identifier/source:** [10.5281/zenodo.8224890](https://zenodo.org/records/8224890). **Paper:** IEEE Communications Magazine 62(5), 44–49, 2024; DOI [10.1109/MCOM.011.2200707](https://doi.org/10.1109/MCOM.011.2200707).
- **Collection:** real operational networks, two operators, Rome, seven-week campaign. Exact session dates and row totals not established here; later paper situates earlier campaigns in 2020–2021.
- **Files/features:** 4G/5G/NB-IoT passive CSVs, active throughput and latency CSVs, description PDF. Radio indicators and connectivity support candidate features; exact schema/units need documentation and Phase 3 confirmation.
- **Targets:** measured throughput/latency; passive signal measures. No verified outage/fault labels.
- **Size/count:** repository lists approximately 2.6 GB; observation count unverified. Download-volume statistics are not dataset size.
- **Rights/access:** API metadata explicitly says `cc-by-4.0`, open. Research/commercial reuse with attribution is allowed under that license. Download named files from the record; checksums are listed.
- **Bias/limitations:** restricted geography/devices/campaign; active tests and passive scans are not automatically aligned. Do not infer general population service quality from measurement routes.

License verification source: [Zenodo API record](https://zenodo.org/api/records/8224890), successfully read in this session. No model-ready join was verified.

## D2. Dataset (active/passive) — The Chronicles of 5G Non-Standalone

- **Publisher:** Giuseppe Caso/Karlstad University with the paper's research collaboration; Zenodo/PERFORM.
- **Identifiers:** active [10.5281/zenodo.14073311](https://zenodo.org/records/14073311); passive [10.5281/zenodo.17208870](https://zenodo.org/records/17208870).
- **Paper:** *The Chronicles of 5G Non-Standalone: An Empirical Analysis of Performance and Service Evolution*, IEEE OJ-COMS, 2024; [institutional manuscript](https://iris.uniroma1.it/retrieve/f9a290b3-fc8b-4b41-bbe5-2d482862c261/Caso_Chronicles_2024.pdf).
- **Collection:** paper spans earlier and 2023 commercial campaigns, six operators across Rome, Stockholm and Karlstad. Exact contents of each archive must be reconciled with that broader paper scope.
- **Files/count:** active ZIP 82,284,534 bytes; passive 5G ZIP 995,182,507 bytes and 4G ZIP 154,555,780 bytes. Row/session counts unverified.
- **Features/targets:** active service/performance measurements and passive radio measurements; throughput is a candidate target. Exact field availability and time alignment unverified.
- **License/access:** both API records identify CC BY 4.0 and expose file inventories. Active and passive files are separate; the active record explicitly points to the passive record.
- **Limitations:** same collaboration and potentially reused earlier campaign data; not independent collection methodology. Separate by campaign and deduplicate before asserting external validation.

The browser could not open the passive page, but its [API](https://zenodo.org/api/records/17208870) succeeded. The [active API](https://zenodo.org/api/records/14073311) also succeeded. The paper's broader conclusions must not be treated as guarantees that every field is present in the public ZIPs.

## D3. UCC — Beyond Throughput, the Next Generation 5G production dataset

- **Publisher:** Raca/University of Sarajevo and UCC MISL collaborators. [Original repository](https://github.com/uccmisl/5Gdataset).
- **Permanent reference:** paper DOI [10.1145/3339825.3394938](https://doi.org/10.1145/3339825.3394938); separate dataset DOI not verified.
- **Method/location/time:** G-NetTrack Pro measurements from a major Irish operator, stationary and car scenarios, streaming and file downloading. Published 2020; exact capture dates and site boundaries not established here.
- **Observations/features:** original ZIP row/session counts not counted; channel, context, cell and throughput KPIs documented. The count used by a later paper is not automatically the original release's total.
- **Targets:** measured application throughput; cell changes may support derived mobility indicators if the schema supports them.
- **Evidence:** production ZIP is real measurements. The accompanying ns-3 framework is a separate simulation resource.
- **License/access:** repository displays GPL-3.0 and `5G-production-dataset.zip`. Download that file from the original repository after topic approval. Verify that the license's intended scope includes the data before redistribution; GPL is not a noncommercial-only license, but its application to data requires care.
- **Bias:** one operator and measurement platform; streaming can be application-limited. A served cell identifier is not automatically a globally unique base-station identity.

## D4. Lumos5G-v1.0

- **Publisher:** University of Minnesota Networking Research Group. [Official project/download page](https://networking.umn.edu/lumos5g).
- **Paper:** *Lumos5G: Mapping and Predicting Commercial mmWave 5G Throughput*, ACM IMC 2020; [DOI 10.1145/3419394.3423629](https://doi.org/10.1145/3419394.3423629). Separate dataset DOI not verified.
- **Collection:** real commercial mmWave 5G around Minneapolis; walking, driving and stationary campaigns. The full study reports six months and 563,840 per-second samples; exact public-archive coverage was not verified. [Author manuscript](https://www-users.cse.umn.edu/~fengqian/paper/5g_imc20.pdf).
- **Features/target:** location, mobility, LTE/NR connection measurements and delivered downlink throughput.
- **Subset warning:** BAMMO's analyzed loop data contain 67,764 observations over 118 repeated experiments; this is not the total full-study count. [BAMMO](https://doi.org/10.1093/jrsssc/qlae054).
- **License/access:** BAMMO's data statement identifies CC BY 4.0 and links [IEEE DataPort](https://ieee-dataport.org/open-access/lumos5g-dataset). DataPort access failed here; official UMN download link is visible but archive not acquired. License designation is author-reported, not independently checked inside the archive.
- **Limits:** native missingness is valuable, but mmWave propagation, devices and routes differ from mid-band NSA. Do not pool incompatible throughput protocols without justification.

## D5. Telecommunications — SMS, Call, Internet — MI

- **Publisher:** Telecom Italia, Harvard Dataverse. [DOI 10.7910/DVN/EGZHFV](https://doi.org/10.7910/DVN/EGZHFV).
- **Paper:** Barlacchi et al., Scientific Data 2015, [10.1038/sdata.2015.55](https://pmc.ncbi.nlm.nih.gov/articles/PMC4622222/).
- **Method/time/place:** anonymized operator CDR-derived activity aggregated spatially and in 10-minute intervals; Milan, November–December 2013.
- **Fields/targets:** grid identifiers, time, country codes and SMS/call/internet activity; forecast activity in its documented units. Exact row count not established; the repository lists 62 files, which is not 62 observations.
- **Real versus simulated:** derived aggregates of real operator records, not synthetic customers. Geographic redistribution/aggregation means this is not raw sector KPI data.
- **License/access:** Dataverse shows Custom Dataset Terms. The original [FBK/ODI project page](https://theodi.fbk.eu/openbigdata/) identifies ODbL. Preserve attribution and applicable database share-alike terms; inspect the exact Dataverse terms rather than relabeling it CC BY. ODbL generally permits commercial reuse subject to conditions.
- **Download:** select daily files individually; the repository warns that the entire dataset is too large for its combined download.
- **Limits:** old period, one operator, normalized/derived activity, absence-versus-zero ambiguity. Trentino's exact activity-release identifier was not independently pinned; do not use the distinct TN-to-TN call-interaction dataset as a substitute.

## D6. WiSig

- **Publisher:** UCLA CORES Lab authors, measurements on the ORBIT radio testbed. [Collection overview](https://cores.ee.ucla.edu/wisig/overview/).
- **Paper/identifier:** IEEE Access 2022, [10.1109/ACCESS.2022.3154790](https://cores.ee.ucla.edu/wisig/license/). Separate data DOI unverified.
- **Method/time/place:** actual 2.4 GHz Wi-Fi transmissions recorded by USRP receivers on ORBIT; four captures spanning a month. Exact calendar dates were not confirmed from the inspected primary overview.
- **Size/features/target:** overview reports 10 million packets, 174 transmitters and 41 receivers; raw and equalized 256-sample preambles, transmitter/receiver/capture identities. Target: transmitter identity; unknown identity is derived through held-out devices.
- **License:** CC BY-NC-SA 4.0, verified on the official license page. Noncommercial research is permitted subject to attribution/share-alike; commercial use needs separate permission.
- **Download:** [official downloads](https://cores.ee.ucla.edu/wisig/downloads/) list ManyRx 1.2 GB, ManyTx 2.5 GB, ManySig 1.4 GB and SingleDay 1 GB; full processed zipped data approximately 42 GB.
- **Limits:** compact subsets share signals/devices; they are not independent validation corpora. One testbed, limited dates, Wi-Fi rather than NR, and no verified real adversarial attack labels. Use processed subsets first, not the much larger raw capture collection.

## D7. RANalyzer-Dataset

- **Publisher:** Northeastern/WiNES Lab authors. [Repository, files and license](https://github.com/wineslab/RANalyzer-Dataset). **Paper:** [arXiv:2604.23153v1](https://arxiv.org/html/2604.23153v1); repository cites NetSoft 2026, final proceedings metadata not independently verified.
- **Method:** actual indoor over-the-air private 5G tests, OAI gNB, USRP X410 radios, commercial modems and Open5GS; not Colosseum RF emulation.
- **Data:** iPerf UDP downlink results, gNB logs and processed CSV; throughput/loss/jitter and radio/protocol features linked to releases. Degradation labels in the paper are inferred, not a verified incident registry.
- **Counts/time conflict:** repository says 69 releases and 9,430 runs; overview dates November 2023–December 2025 while introduction says July 2023–December 2025. Preprint abstract says over 8,600 tests. Distinguish raw/filtered/version differences through an actual inventory; do not choose the convenient number.
- **License/access:** CC BY 4.0, public repository; clone/download later and pin a commit. Research/commercial reuse subject to attribution.
- **Limits:** site city and exact independent fault count not verified. A single testbed and changing software/environment confound generalization and causal attribution. Do not treat each interval as an independent fault example.

## Additional sources screened

**NetMob23:** [official challenge](https://netmob2023challenge.networks.imdea.org/) and [dataset paper arXiv:2305.06933](https://arxiv.org/abs/2305.06933). Orange/IMDEA collaboration; real service-demand information covering 20 French urban areas, 68 services, 77 days, with 100 m spatial/15-minute temporal resolution. The site reports over 400 billion data points and 2.3 TB. Exact calendar window/row schema not audited. Access requires an application/agreement, and continued usage beyond October 6, 2025 requires an extension. No current permission was obtained; research/commercial/redistribution rights must follow the agreement. Do not describe it as unrestricted open data or make it a mandatory dependency.

**ColO-RAN:** [original experimental dataset description](https://openrangym.com/datasets/colosseum-coloran-dataset). RF-emulated Rome topology, real protocol-stack experiments; simulated propagation/traffic assumptions remain. Record counts, capture dates and dataset reuse license not verified. It can support supplementary control experiments but fails the requirement for field radio measurements as primary evidence.

**DeepSense 6G:** [official project](https://deepsense6g.net/) and [collection documentation](https://deepsense6g.net/data-collection). Real multimodal sensing/communication scenarios in Arizona; sensor modalities include camera/GPS and radio measurements. Scenario-specific dates/counts/targets and commercial rights were not audited. The site's citation request alone is not a complete commercial-use license. Not shortlisted because of overlap with the existing DeepSenseV2V work.

**MONROE SOMETIME:** [Zenodo 10.5281/zenodo.1300512](https://zenodo.org/records/1300512), University of Naples collaborators; real 4G bandwidth/throughput experiments, 654.5 MB archive, 2018 release. Log/packet records from multiple tools could support a separate measurement-method study. Exact campaign locations/dates, sample counts and license were not fully verified, so it is a lead rather than a recommended primary dataset.

**BTRC:** [official tower statistics](https://btrc.gov.bd/pages/static-pages/6922dbce933eb65569e0cab2). Monthly operator/tower-company aggregates; no verified site-level outage targets or measurement reuse license. Suitable for context, not predictive failure-model training. GSMA reports, 3GPP specifications, IEEE DataPort and CRAWDAD are sources to inspect by individual record, not dataset-level assurances of open access or suitable labels. No additional verified primary candidate from them is assumed here.

## Phase 3 verification requirements, if a topic is approved

Record the source version/commit, original filename, license text, bytes and SHA-256 hash; preserve publisher checksums. Count rows and independent sessions, identify units/sentinels and duplicate overlaps, inspect timestamps and label availability, and map every predictor to its availability time. For transfer, build a feature/target compatibility matrix before merging anything. An unmatched or undocumented measurement is not a valid missingness example merely because a join failed.

The key feasibility unknown for the leading topic is whether sufficiently long, causally aligned labeled sequences and meaningful native missingness exist in the chosen files. This report verifies credible candidate sources, not that the final data suitability test has already passed.
