# Reviewer-style assessment of the revised benchmark

**Overall submission readiness: 7/10 for an empirical cellular-measurement paper.** This is an author-side assessment of the current working tree. The best contribution is the observed difference between an apparently reliable rate, the amount of rate it supports, and the effect of changing when a forecast can be issued.

| Category | Score / 10 | Evidence and limit |
|---|---:|---|
| Research novelty | 6 | Tables II, III and X combine chronological budget curves, endpoint sensitivity and a clock-triggered replay. Existing work supplies the predictors and calibration mathematics. |
| Scientific significance | 7 | Figure 6 exposes zero commitments on more than nine tenths of Rome E3 sessions at ten labels. No application received or acted on the forecasts. |
| Dataset quality | 6 | Two pinned Rome releases, 83 Irish traces and 17 Norwegian route logs. Later Rome session boundaries are inferred. |
| Experimental design | 7 | The budget grid shares fixed suffixes. Norway uses separate date blocks. Endpoint differences prevent a common cross-country test of exactly the Rome forecast. |
| Prediction-time validity | 7 | The Rome clock issues forecasts using strictly prior information and counts unscorable opportunities. The original next-test evaluation remains retrospective. |
| Statistical rigor | 6 | Paired date deletion, date resampling and Irish trace influence preserve clustering. Two to eight held-out dates per Rome regime and two in Norway limit inference. |
| Methodological correctness | 8 | Finite-rank edge cases, chronological target separation and group fallback are explicit and tested. Unverified exchangeability limits coverage claims. |
| External validation | 6 | Table X evaluates two local lag models on Norwegian traffic. Table XI exposes 34.81% violations for both ten-label rules on a chronological Irish suffix. The Irish next-row task and Norwegian interval task differ from the Rome inferred-session endpoint. |
| Reproducibility | 8 | Per-file pins, per-forecast records, executable rebuild, machine-checked publication tables and local JUnit evidence. The latest local edits have no hosted CI result or independent reproduction. |
| Manuscript quality | 7 | The paper reports adverse operating points, denominator changes and endpoint assumptions alongside the favorable Irish result. Target-specific typesetting and author metadata require the venue decision. |
| Overall submission readiness | 7 | Defensible for measurement or reproducibility review with the scope stated above. |

## Editorial decision and remaining work

**Critical for submission to a specific venue.** Choose the venue and supply its required corresponding-author details, affiliation if applicable, and disclosures. The current source is a single-column IEEEtran review copy. For example, IEEE Access requires its double-column template, author biographies, an ORCID for the submitter and AI-use disclosure. It recommends fewer than 20 pages. No venue or factual affiliation was assumed. [Official submission instructions](https://ieeeaccess.ieee.org/authors/submission-guidelines/)

**Major scientific limit.** The clock schedules can be implemented while logging, but scoring still conditions on the availability of future labels. Independent test-start markers are absent from the later Rome stream. For a prospective next-test or cross-operator deployment claim, log test-start events before measurement, archive every issued prediction, record completions and failures, and freeze the split and calibration rule before new dates arrive. None of the available scripts can reconstruct missing physical markers.

**Claims to qualify.** Ten labels achieved the observed Rome tree violation target with very low supported rates. Missingness grouping gave identical bounds at that budget. The Irish persistence gain describes overlapping test partitions. A third-country evaluation on one historical Norwegian bus route cannot establish contemporary 5G deployment reliability. Preserve the minimum hybrid's adverse results.

**Minor and procedural items.** Confirm author name and preferred contact, apply the chosen venue's supplementary-file rules and check the final typeset page count there. Hosted validation requires publishing the reviewed working tree and observing a workflow run for that exact commit. The local test evidence is recorded separately.

**Venue fit.** A telecommunications measurement, networking systems evaluation or reproducibility track that accepts careful empirical comparisons is a closer match than a methods venue requiring a new algorithm or theorem.

## Execution evidence

The full local Rome rebuild, clock and Norway replay, source compilation and post-build checks completed successfully. The post-build JUnit report recorded 57 passes, zero skips and zero failures. The validator checked eleven tables across LaTeX, Markdown, HTML and the two PDFs, six referenced figures, all packaged manuscript page renderings and the submission ZIP contents. The review manuscript is nine pages and the cover-plus-manuscript PDF is ten. The separate chronological Irish analysis was regenerated from the pre-imputation measurement file; the prior 30-split Irish reproduction was reused and its paired aggregate consistency rechecked. See results/runs/execution.json, results/runs/final_tests.xml and docs/REPRODUCIBILITY_MANIFEST.json.
