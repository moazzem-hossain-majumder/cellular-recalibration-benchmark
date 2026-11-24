# MARUR literature review

Prepared for the existing paper on reliable cellular throughput commitments under missing telemetry and limited calibration feedback. Exactly **30 peer-reviewed publications**, **24 from 2022–2026 (80%)**, grouped into four themes. No venue was specified, so the section uses generic IEEEtran conventions rather than claiming compliance with a particular page limit.

- `related_work.tex`: Section II module, four thematic subsections, 12-paper comparison plus a present-study row, and a research-gap paragraph.
- `references.bib`: the 30 cited publications only. Do not replace the main manuscript bibliography without merging its other entries.
- `review_matrix.csv`: the requested seven-column audit log. Limitations are specifically relative to this research problem.
- `NOVELTY_AND_EXPERIMENT_OPPORTUNITIES.md`: implications and a frozen-model experiment plan. No new numerical performance claims.

Include `array` and `tabularx` in the parent document, insert the section after the introduction, and use `\bibliographystyle{IEEEtran}` with this bibliography. The standalone `review_preview.tex` demonstrates compilation and sets the section counter to one so the review is Section II.

## Verification and bibliographic exceptions

Publisher-deposited Crossref records, official PMLR/NeurIPS/JMLR proceedings metadata, and the published ICLR paper identify the publications. `_support/verification_sources.json` records the exact source and metadata for each key; original metadata responses are archived beside it. These are a focused, purposive review, not a claimed exhaustive systematic search or meta-analysis. Metadata verification and a scoped methodological reading are not independent replications of the cited experiments.

Optional BibTeX fields are explicitly empty where the consulted publication record supplies none. Conference papers generally have no journal issue number; ICLR supplies no proceedings volume or page range; many PMLR/JMLR publications supply no DOI. The official NeurIPS BibTeX records leave pages empty for the 2017 selective-classification and 2019 covariate-shift papers, so this export preserves that omission. Unknown metadata is not invented to fill a template. Article identifiers (e.g., 92 and 110207) occupy the publisher's page/article field.

BAMMO is cited as 2025, the year of its final volume/issue; its online-first date is October 2024. PMLR author spellings follow proceedings metadata, including Dong Xu for the betting paper. Original titles are case-protected in BibTeX. The review does not compare percentage improvements across different horizons, datasets, splits, denominators, or measurement costs.

The section has now been integrated as `paper/related_work.tex` in the refocused six-page main manuscript; its bibliography entries are merged with the repository bibliography. The historical detailed analyses are in a separate fifteen-page supplement. This directory retains the standalone thirty-paper review and preview. The actual venue/template still requires selection and checking. A polished review does not establish that the full research is ready for acceptance.
