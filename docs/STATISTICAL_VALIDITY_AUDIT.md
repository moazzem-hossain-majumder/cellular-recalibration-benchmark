# Statistical validity of the cellular recalibration benchmark

## Estimands and denominators

The Rome clock issues a lower bound on a whole-minute boundary using the last valid preceding-minute rate and radio measurements available before issuance. An eligible tick remains in the ledger when its next-minute target cannot be measured. Let N count issued ticks, m measured targets, e measured violations and h unavailable targets with positive commitments. The measured violation rate V is e/m. For a hypothetical nonnegative target at every tick, the all-issued fraction lies between e/N and (e+h)/N. Both endpoints are attainable by choosing feasible missing outcomes on either side of each positive commitment. Bounds of zero always cover nonnegative throughput. A terminated service with no meaningful throughput endpoint calls for a separate service definition. These endpoints describe missing-outcome uncertainty and carry no probability or confidence level. [Clock ledger](../results/clock_histgbm/issued_k10.csv)

Utility U sums min(lower bound, measured throughput) and divides by the sum of measured throughput over the same ticks. Recompute that ratio from the sums when pooling dates. Positive-commitment failure conditions on a decision the model controls, so always report the number of positive decisions and the number with observed outcomes. Each estimator answers a different operational question. [Daily numerators and denominators](../results/clock_histgbm/per_date.csv)

| Frozen global tree at K = 10 | E1 | E3 |
|---|---:|---:|
| Issued / measured / unavailable | 238 / 211 / 27 | 171 / 152 / 19 |
| Measured violations / measured targets | 67/211 (31.75%) | 2/152 (1.32%) |
| Positive commitments / issued | 130/238 (54.62%) | 3/171 (1.75%) |
| Measured violations / measured positive commitments | 67/122 (54.92%) | 2/3 (66.67%) |
| Missing positive commitments | 8 | 0 |
| All-issued violation range | 67/238–75/238 (28.15–31.51%) | 2/171 (1.17%) |
| All-positive violation range | 67/130–75/130 (51.54–57.69%) | 2/3 (66.67%) |

Both E3 failures and all three positive commitments occurred on June 10, 2023. U was 0.065% on E3 and 7.15% on E1. In E1, 26 of 27 unavailable targets ended at a trace boundary and one complete target window had no valid rate. The 19 unavailable E3 targets all reached a trace boundary. Both the observation process and frequency of issuing a positive lower bound affect interpretation. [Opportunity and status ledger](../results/clock_histgbm/ticks.csv) · [Daily decisions](../results/clock_histgbm/per_date.csv)

## Dependence and split integrity

The two clock evaluations contain 27 E1 and 19 E3 test traces across seven dates each. Six dates coincide, leaving eight distinct dates across the two settings. Shared sites, acquisition conditions and overlapping history give the tick count little meaning as an independent sample size. The original session evaluations E0 through E3 contain respectively two, seven, eight and seven test dates. The source tree was fitted on 57 earlier Op1 sessions. Compare its decisions with persistence within the same dates and issuance ledger. Conditional daily summaries carry the fixed source fit and chosen calibration prefix through every calculation. [Clock construction](CLOCK_TRIGGERED_PRIMARY_MODEL_AUDIT.md) · [Inference design](STATISTICAL_DESIGN_IMPROVEMENT.md)

Deleting one date at a time gave pooled measured tree V of 29.63–33.33% in E1 and 0–1.72% in E3. The E1 tree made more errors than persistence on each date. The E3 tree made fewer errors on six dates and tied once. This directional consistency coexists with substantial differences in utility and positive commitment rates. An inferential comparison would need genuinely new collection blocks spanning independent campaigns or operators. Tick-level tests, bootstrap confidence limits from two campaigns, and generalization of a directional count to new operators lack a defensible sampling basis here. [Paired dates](../results/clock_histgbm/per_date.csv)

The Irish chronological check uses 11 calibration dates and 16 held-out dates. Global and grouped K = 10 have identical V of 34.81% and U of 71.62%. Deleting one held-out date gives V of 34.03–36.68%. Grouping had insufficient prefix support across groups to change the aggregate result. The separate 30 random partitions reuse 83 traces. They measure split sensitivity. Norwegian bus and metro tests involve two and three dates respectively on one operator, with 17 logs per mode in the underlying collection. Each setting needs its own outcome definition and sampling unit. [Irish date summaries](../results/external_validation/irish_group_dates.csv) · [Norway transfer](../results/external_validation/metro_transfer.csv)

## Selection, feedback and claims

The fixed ten-label comparison is interpretable on the later suffix. The post-evaluation frontier searches many prefixes and can favor the observed suffix. A selected K or method needs an untouched later campaign before prospective superiority can be claimed. Daily rolling origins compare frozen calibration with the latest ten completed labels. The latter policy requires ongoing feedback, which changes the data acquisition cost even at fixed window size. Simulated radio deletions probe recorded rows under chosen masking rules. Repeated seeds describe mask variation conditional on these traces. They supply no independent network replication. [Frontier](../results/clock_histgbm/frontier.csv) · [Daily origins](../results/clock_histgbm/rolling.csv) · [Mask scenarios](../results/clock_histgbm/simulated_nr_metrics.csv)

**Reviewer judgment.** The audited design supports descriptive trade-offs, conditional missing-outcome bounds, and failed transfer examples. A claim of nominal coverage under deployment shift, superiority over published predictors across datasets, or a generally effective positive service commitment would require new evidence. Preserve the sparse-positive example and report which target, horizon, calibration budget and loss each external comparison actually matches.
