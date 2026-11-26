# Reviewer-style assessment after the matched clock replay

These are author-side judgments, not external peer review. Weighted scores are the sum of weight × rating divided by 100. The evidence supports submission as a measurement and reproducibility study after venue preparation. A new general-purpose calibration algorithm and broad operational reliability are unsubstantiated.

## Scientific contribution

| Category | Weight | Rating / 10 | Evidence and reason |
|---|---:|---:|---|
| Originality | 20% | 6.5 | RESEARCH_GAP_AND_NOVELTY_REVIEW.md and Table XII. Auditing all issued rates with nonnegative outcomes is informative; the bounds and calibrators are established ideas. |
| Significance | 10% | 7.5 | results/clock_histgbm/issued_k10.csv. An observed violation on at least 67/238 ticks and only three positive commitments on the other operator materially change the interpretation of a nominal target. |
| Methodological correctness | 15% | 8.5 | scripts/clock_frontier.py and tests/unit/test_issued_risk.py. Outcome-independent ticks, attainable bounds and delayed feedback; duration is a proxy and physical service may cease before the horizon. |
| Experimental design | 15% | 8.0 | results/clock_histgbm/ticks.csv, frontier.csv and rolling.csv. Matched opportunities, full prefixes and disjoint daily test periods; common earlier source fit is small. |
| Statistical rigor | 10% | 6.5 | results/clock_histgbm/per_date.csv and STATISTICAL_DESIGN_IMPROVEMENT.md. Conditional paired deletion and distinct denominators are sound. Seven dates per operator give little independent evidence about new campaigns. |
| External validity | 10% | 6.0 | results/external_validation/metro_transfer.csv and irish_group_validation.json. Route transfer aligns the interval endpoint; the historical single-operator HSDPA data and Irish next-row task cannot externally validate Rome's minute target. |
| Reproducibility | 10% | 8.5 | results/runs/execution.json, final_tests.xml and scripts/validate_manuscript_consistency.py. Raw replay and numeric checks ran locally. No independent clean-machine or final-commit hosted verification. |
| Evidence and interpretation | 10% | 8.5 | Table XII and ADVERSARIAL_ROBUSTNESS_AUDIT.md. Negative and unresolved results persist; utility still conditions on future measurement availability. |

**Weighted science score: 7.475/10 (7.48 rounded).**

## Manuscript and submission

| Category | Weight | Rating / 10 | Evidence and reason |
|---|---:|---:|---|
| Abstract and introduction | 10% | 8.0 | paper/manuscript.tex, abstract and research questions. States adverse primary results and defines the deployment question. |
| Related work | 10% | 7.5 | paper/references.bib and RESEARCH_GAP_AND_NOVELTY_REVIEW.md. Covers nearest cellular comparison, selection and conformal risk; review is targeted. |
| Methodology clarity | 15% | 8.0 | CLOCK_TRIGGERED_PRIMARY_MODEL_AUDIT.md and the all-issued section. Feature mapping and estimand are explicit; several endpoint definitions require careful reading. |
| Results and figures | 15% | 8.0 | Tables II, XI, XII and Fig. 7. Complete prefixes and shared denominators; individual overlapping budget points are easier to explore in the CSV. |
| Discussion and limitations | 15% | 8.0 | Paper conclusion and CROSS_NETWORK_GENERALIZATION.md. Sparse dates, physical endpoint and measurement-availability assumptions are explicit. |
| References | 10% | 8.0 | paper/references.bib. Includes primary empirical and methodological sources and attribution for the identification argument. |
| IEEE formatting | 10% | 6.5 | paper/manuscript.pdf and paper/cover_letter.tex. A single-column IEEEtran review draft still needs the chosen venue template and corresponding-author details. |
| Reproducibility documentation | 15% | 8.5 | README.md, docs/REPRODUCIBILITY_MANIFEST.json and the submission ZIP supplement. Local evidence is available; third-party availability remains a dependency. |

**Weighted manuscript score: 7.875/10 (7.88 rounded).**

## Submission decision

A skeptical reviewer can reproduce the counterexample and see the limits of each claim. The paper does not establish that ten labels suffice, that grouping is generally better, or that a conservative bound is useful. Stronger claims would require a modern independent network using the same clock, more independent collection dates and a definition of service performance when measurement ends. Unannotated change points preclude statements about recovery latency. The author must choose the venue and confirm author metadata and disclosures before submitting. The package has not been submitted and no hosted CI result is claimed for these local changes.
