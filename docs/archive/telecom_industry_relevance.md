# Telecom industry relevance — Phase 1 assessment

This document describes prospective engineering relevance, not measured commercial benefits. No Grameenphone, Banglalink, Robi Axiata, or Teletalk private network data have been accessed, and none of the reviewed foreign datasets represents those operators.

## Industry problem

Network teams need to distinguish low user throughput caused by radio conditions, measurement limitations, service behavior and network changes. A model that looks accurate on one campaign can be misleading elsewhere. Software updates introduce a different reliability problem: a performance deterioration may be due to the update, the environment, or the test workload. The reviewed commercial-measurement and RANalyzer papers establish that these are concrete research settings; our proposed improvements remain untested. See [literature review](literature_review.md), P3–P6 and P14.

## Leading topic: reliable throughput estimates

The proposed research would evaluate a forecast accompanied by a conservative rate bound and a clear indication of when evidence is insufficient. The engineering question is how dependable that output remains when telemetry is missing or the deployment domain changes, and how many new labeled measurements are needed to recalibrate it.

Potential applications include performance assurance, assessing the reliability of analytics across regions, and identifying where additional measurements are needed. Offline evaluation can establish prediction/calibration behavior. It cannot, by itself, demonstrate a reduction in live congestion, higher spectral efficiency, improved customer QoE, fewer outages, or lower operating cost.

## Information needed from an operator

- Timestamped throughput measurements with test direction, duration, server, application, transport protocol and units.
- Session/device identifiers, radio technology, band, serving-cell identifiers and measurement timestamps, with privacy-preserving handling.
- Available radio indicators and their missing/sentinel-value definitions; reporting delays and sampling intervals.
- Network-change and configuration context where authorized, plus relevant workload information.
- A representative set of regions, devices, time periods and service conditions for local validation.
- An operational decision, its tolerated error cost, and a realistic label/measurement budget.

For software-regression detection, also require release identifiers, test configurations, known bug/fix or rollback evidence, repeated matched tests, and an agreed alert-review process. A commit message alone is not fault ground truth.

## Competencies demonstrated

| Research work | Telecommunications responsibility it demonstrates |
|---|---|
| Interpreting RSRP/RSRQ/SINR and technology state | Radio-performance and drive-test analysis |
| Separating delivered throughput from nominal radio capacity | KPI interpretation and service assurance |
| Time-aware, session-aware data validation | Trustworthy network analytics |
| Cross-operator/campaign evaluation | Model transfer and deployment acceptance |
| Missingness and calibration-budget analysis | Telemetry quality and measurement planning |
| Release-linked monitoring and independent fault validation | Software-change assurance and troubleshooting |
| Reproducible experiments and clear failure reporting | Engineering handoff and technical documentation |

RSRP describes reference-signal received power; RSRQ combines reference-signal power with received-wideband conditions; SINR compares desired signal power with interference and noise. These are related to radio quality but are not interchangeable and do not directly reveal every scheduler, transport or application bottleneck. Exact definitions and units must match the logger and radio technology used.

## Bangladesh-specific limitations

Foreign traces cannot establish performance in Dhaka, rural Bangladesh, or disaster-affected districts. Local spectrum configurations, topology, buildings, devices, traffic, backhaul and power conditions may differ; their effect must be measured rather than assumed. BTRC's [tower-count statistics](https://btrc.gov.bd/pages/static-pages/6922dbce933eb65569e0cab2) provide infrastructure context but do not supply the per-site incident histories needed for flood-outage prediction.

Do not equate missing telemetry with a flood, power failure or congestion event. Missing values can arise from logger behavior, unsupported measurements, non-serving technologies or failed alignment. Nor should an NB-IoT coverage model claim battery-life or reliable sensor delivery benefits without the relevant measurements.

## Before production deployment

Validate on authorized local measurements and unseen devices/regions; assess group-level failures, inference latency, telemetry cost and monitoring drift. Run a shadow-mode study before connecting predictions to actual service or network-control decisions. Quantify benefits in an appropriately designed pilot with a fallback policy. Human review is especially important for a software-fault attribution that has not been confirmed through matched tests or rollback.

The appropriate portfolio claim after a successful research project would be specific: for example, 'evaluated throughput-bound reliability across named public measurement campaigns with a reproducible, time-aware protocol.' Claims of improving a named operator's performance must wait for actual operator evidence.
