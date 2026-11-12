# Can source measurements identify a more useful ten-label bound?

The source-only rule selected histogram gradient boosting with additive calibration, the original benchmark method. Higher throughput from persistence on some target networks did not translate into a choice supported by the source selection data.

We fit the tree on the original 57 earlier Op1 training observations. Six candidates combine tree and previous-session point predictions with persistence weights 0, 0.5 and 1, each with either an additive correction in Mbps or a correction on the log(1 + Mbps) scale. The first ten post-training development observations supply each candidate's calibration offset. On the next 32 observations we select the highest supported fraction among candidates with at most 10% violations. The script records the decision before evaluating the target suffixes. All 32 selection observations come from one collection date.

The selected candidate supported 11.18% of source throughput with one violation in 32. The equal-weight additive blend supported 52.55%, but had four violations (12.50%). The selection threshold would have allowed only three. Small changes in the source sample could therefore affect the choice.

For each target, every complete nonoverlapping block of ten observations from the chronological calibration pool was evaluated against the same later suffix. Each cell below gives blocks meeting the 10% violation target over all eligible blocks. Median supported fraction includes every block, including those exceeding the violation target.

| Target | Selected tree | Persistence | Median supported fraction, tree | Median supported fraction, persistence |
|---|---:|---:|---:|---:|
| E0, same operator and campaign | 1/1 | 0/1 | 2.85% | 12.70% |
| E1, later campaign | 8/14 | 6/14 | 8.58% | 20.55% |
| E2, different operator | 5/9 | 6/9 | 8.10% | 33.44% |
| E3, different operator and later campaign | 11/11 | 0/11 | 0.60% | 51.91% |

Persistence supported more throughput while meeting the target in 5 of 14 E1 blocks and 6 of 9 E2 blocks, compared with the tree on the same blocks. In E3 the tree met the target across all eleven calibration blocks at very low median support, while persistence missed the target in every block. Selecting a predictor separately after observing each target's outcomes would overstate deployable performance.

These are exploratory comparisons on previously inspected test sessions. Blocks share a test suffix and do not represent independent replications. An independent campaign is still needed to assess the frozen selection procedure prospectively.

Reproduce from the repository root with `python scripts/compare_persistence_prefixes.py` followed by `python scripts/compare_source_selected_bounds.py`. The second script checks test-session identities and outcomes and reproduces both comparator metrics for each block. Full-precision results are in [the source selection record](../results/exploratory/source_bound_selection.json) and [the paired target results](../results/exploratory/source_selected_bounds.csv).
