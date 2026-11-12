# Statistical inference audit

Calendar collection date is the paired resampling unit. At K=10 the same forecast rows enter both methods. The bootstrap draws G dates with replacement 2,000 times (seed 42), pools their sessions, and recomputes the violation fraction and the ratio of supported to observed throughput. It weights sessions and delivered throughput respectively. Date independence is unverified. Repeated drives and shared conditions can connect dates. The analysis conditions on one development sample and one target prefix.

| Regime | Days | Single-day global V range | Omit-one-date global V range | Omit-one-date global U range |
|---|---:|---:|---:|---:|
| E0_WithinDomain_Op1_2021 | 2 | 0.0000 to 0.0000 | 0.0000 to 0.0000 | 0.0137 to 0.0370 |
| E1_CampaignTransfer_Op1_2023 | 7 | 0.0000 to 0.1429 | 0.0333 to 0.0826 | 0.0541 to 0.0788 |
| E2_CrossOperator_Op2_2021 | 8 | 0.0000 to 0.1154 | 0.0130 to 0.0286 | 0.0140 to 0.0187 |
| E3_JointShift_Op2_2023 | 7 | 0.0000 to 0.0000 | 0.0000 to 0.0000 | 0.0046 to 0.0070 |

The pointwise grouped and global bounds coincide at ten labels on these suffixes. Their paired differences and all percentile endpoints are zero. This arithmetic identity cannot establish population equivalence. E0 has only two dates, giving just three distinct date-count combinations in the bootstrap. All four regimes fall below the proposal’s ten-date threshold for confirmatory inference. The ranges above describe sensitivity without estimating uncertainty in future campaigns. No absolute performance confidence interval is claimed. Inspect calendar_day_influence.csv for each date, denominator and omission.
