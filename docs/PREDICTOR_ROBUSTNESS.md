# Predictor Robustness Stress Test (Exploratory)

**Evidence Tier:** `exploratory` (run after archive inspection without modifying any frozen config or saved benchmark output).  
**Pre-Committed Configuration:** [`configs/predictor_robustness_exploratory.json`](../configs/predictor_robustness_exploratory.json) (git commit `a7902bbfb34f2ed4dda96c4dcbedb4fb741fb652`, LF SHA-256 `992a5443d3f8cd499e18106aad176526ce0fe665b30898e8b0869adc0828b8bf`, verified clean prior to executing held-out scoring).  
**Frozen Integrity Guarantee:** [`configs/pacer.json`](../configs/pacer.json), [`docs/PACER_FROZEN_PROTOCOL.md`](PACER_FROZEN_PROTOCOL.md), [`results/marur/`](../results/marur/), and [`results/pacer/`](../results/pacer/) were left 100% unmodified (`frozen_checksums_verified = true`).  
**Primary Result Directory:** [`results/exploratory/predictor_robustness/`](../results/exploratory/predictor_robustness/) (`Verdict = A`).

---

## 1. Plain-Language Verdict: **Verdict (A)**

> **Verdict (A): Conditional risk exceedance and measurement-accounting reversal rates both remain high across every tested predictor family and training pool — confirming that the paper's empirical accounting findings are NOT a weak-57-row-predictor artifact.**

Specifically:
1. **Conditional risk `R_+^hi` stays far above nominal `alpha = 0.10` across all 10 predictors (`40.5%` to `62.7%` mobile median vs. `47.6%` for frozen 57-row `HistGBM_57_Ref`):**
   - Training regularized `HistGBM_Reg_LOCampO`, monotonically constrained `HistGBM_Mono_LOCampO`, linear `Ridge_LOCampO`, and `ElasticNet_LOCampO` on **1,379 to 4,081 strictly earlier-in-time LOCampO rows** improves supported throughput `U` across mobile cohorts (`0.93% -> 6.25%–9.61%`), because larger multi-campaign pools and linear lag extrapolation avoid extreme conservative collapse. However, mobile median conditional upper risk **actually rises slightly to `55.2%–57.5%`** (`58.6%–60.0%` on post-2021 radio-equipped campaigns where 2,621–4,081 earlier rows exist).
   - Direct tail-targeting (`QuantileGBM_p10_LOCampO` and campaign-date-blocked `CQR_Unscaled_LOCampO` / `CQR_Scaled_LOCampO`) reduces median MAE (`41.43 -> 38.78–38.85` Mbps) and modestly lowers mobile median `R_+^hi` (`40.5%–44.8%`; `43.2%–47.3%` on post-2021 radio cohorts), yet still remains **`4x` above `alpha = 0.10`** while crushing mobile median supported utility down to **`0.16%–0.92%`** (`0.09%–0.63%` post-2021).
   - Adaptive Conformal Inference across `gamma in {0.005, 0.01, 0.05}` on the shared `Q_new` cap yields mobile median `R_+^hi` across `[36.36%, 65.08%]` (`U` in `[0.09%, 21.44%]`), failing to close the selective conditional risk gap at 10- to 40-query horizons.
2. **All five Proposition 1 single-factor accounting reversals remain pervasive across every predictor family:**
   - All-issued `R -> R_+` SLA flips (`45.7%–72.9%`), pairwise winner rank flips (`22.1%–36.1%`), realized query mismatches (`22.1%`), missing-outcome interval overlap (`57.1%–68.4%`), and Offer-Weighted vs. Equal-Unit sign flips (`19.0%–44.0%`) persist with positive campaign-level bootstrap 95% confidence bounds across `k=6` campaigns.
   - One important nuance on magnitude: the extreme `-23.41 pp` vs. `+0.37 pp` Held-Out `C=10` PACER pooling gap observed under `HistGBM_57_Ref` moderates to `1.1–9.5 pp` under LOCampO predictors, though **opposite-sign reversals persist** (`HistGBM_Mono_LOCampO`: `-5.43 pp` OfferWtd vs. `+0.10 pp` EqualCl; `CQR_Scaled_LOCampO`: `+3.74 pp` OfferWtd vs. `-0.61 pp` EqualCl; `QuantileGBM_p10_LOCampO`: `-6.99 pp` vs. `+2.50 pp`).

---

## 2. Strictly Causal LOCampO Setup & Hyperparameters

To prevent any future calendar leakage or target contamination, each held-out physical campaign $C$ was trained exclusively on rows from **other** archives/campaigns whose completion timestamp satisfied `ready < cutoff_issue(C)`, excluding the same-date overlapping 2023 Rome pair (`Rome_2023` $\leftrightarrow$ `Rome_Capacity`) from each other. Hyperparameters were selected exclusively via **chronological per-campaign date-blocked validation splits** inside the training pool (`val_frac = 0.20`; for CQR, `calib_frac = 0.20` strictly disjoint final dates per campaign, never random splits).

| Target Physical Campaign | Eval Start (UTC) | `n_train` (`dates`) | Source Archives Included (`ready < cutoff`) | Selected Hyperparameters (`Reg` / `Mono` / `Ridge` / `ElasticNet` / `Q10` / `Q90`) |
|---|---|---|---|---|
| `Oslo_Commute` | `2011-01-06 07:38` | `130` (`3`) | `Oslo_Bus_2010` (0 non-Oslo earlier campaigns exist in 2010) | Reg/Mono: `d=3, leaf=10, l2=0, iter=200`; Ridge: `a=0.1`; EN: `a=0.01, l1=0.9`; Q10: `d=4, leaf=10, l2=0, it=30` |
| `Ireland_Drive` | `2019-12-14 10:17` | `1379` (`23`) | `Oslo_Bus_2010; Oslo_Commute` (lag-only 2010–2011 HSPA; cross-era shift) | Reg/Mono: `d=4, leaf=10, l2=0, iter=120`; Ridge: `a=10.0`; EN: `a=0.1, l1=0.5`; Q10: `d=4, leaf=30, l2=10, it=50` |
| `Ireland_Static` | `2019-12-16 13:41` | `1466` (`25`) | `Oslo_Bus_2010; Oslo_Commute; Ireland_Drive` (`ready < cutoff`) | Reg: `d=4, leaf=10, l2=0, it=50`; Mono: `d=4, leaf=10, l2=10, it=200 (rsrp,ss_rsrp)`; Ridge: `a=0.1`; EN: `a=0.01, l1=0.9`; Q10: `d=3, leaf=30, l2=10, it=30` |
| `Rome_2023` (`E1, E3`) | `2023-03-29 18:25` | `2621` (`46`) | `Oslo_Bus_2010; Oslo_Commute; Ireland_Drive; Ireland_Static; Rome_2021_8224890` | Reg: `d=3, leaf=30, l2=10, it=60`; Mono: `d=4, leaf=30, l2=10, it=60`; Ridge: `a=0.1`; EN: `a=0.01, l1=0.9`; Q10: `d=4, leaf=30, l2=10, it=170` |
| `Rome_Capacity` (`Op1, Op2`) | `2023-03-29 17:11` | `2621` (`46`) | Same 4 earlier campaigns (excludes `Rome_2023` overlapping dates) | Same time-ordered LOCampO models as `Rome_2023` |
| `US_Drive3` (`ATT, T-Mob, Ver`) | `2023-08-05 15:21` | `4081` (`68`) | `Oslo + Ireland + Rome_2021 + Rome_2023 + Rome_Capacity` | Reg: `d=3, leaf=10, l2=10, it=100`; Mono: `d=3, leaf=30, l2=1, it=90`; Ridge: `a=100.0`; EN: `a=0.1, l1=0.9`; Q10: `d=4, leaf=30, l2=10, it=150` |

*Exact CQR date-blocked conformal calibration offsets/scales and validation losses for every fold are logged in [`results/exploratory/predictor_robustness/fold_training_summary.csv`](../results/exploratory/predictor_robustness/fold_training_summary.csv).*  
*Exact per-cohort MAE, RMSE, point violation rate, and pinball losses are logged in [`results/exploratory/predictor_robustness/point_accuracy.csv`](../results/exploratory/predictor_robustness/point_accuracy.csv).*

---

## 3. Comparison Table (`HistGBM_57_Ref` vs. Alternative Predictors)

All downstream rows below share the exact `src/audit/recalibration_audit.py` normalizer (`id_err <= 1e-12` everywhere), `alpha = 0.10`, caps `{10, 40}`, scenarios `{Recorded, QueryCensor20}`, `k=6` campaign-level bootstrap CIs (`B=2000`, resampling campaigns), and pre-committed fairness sieve (`|dQ_new| <= 1e-6`, `|dA| <= 5.0 pp`, `dR_+^hi < -1.0 pp`, `dU >= -0.05 pp`). Because `Oslo` precedes `Ireland` in calendar time (100x speed & missing-radio era shift), both **All-Mobile (`9` cohorts)** and **Post-2021 Radio-Equipped (`7` cohorts, `n_train = 2,621–4,081`)** columns are reported.

| Predictor | Med MAE (Mbps) | Mobile `R_+^hi` Med (Range, %) | Mobile `U` Med (%) | Post-2021 `R_+^hi` / `U` (%) | SLA Flip % [95% Camp CI] | Rank Flip % [95% Camp CI] | `Q_new` Mismatch % | Overlap % [95% Camp CI] | Pool!=Eq % [95% Camp CI] | Fair Sieve Wins (All 140) |
|---|---|---|---|---|---|---|---|---|---|---|
| `HistGBM_57_Ref` | `41.43` | `47.6` (`8.8–77.8`) | `0.93` | `50.0` / `0.60` | `64.3` `[37.2, 82.1]` | `23.9` `[17.3, 32.1]` | `22.1` | `60.2` `[41.4, 70.1]` | `44.0` `[7.1, 51.2]` | `3/67 (4.5%)` / `2.1%` |
| `Persistence` | `52.31` | `62.7` (`22.5–85.2`) | `19.38` | `63.8` / `17.41` | `45.7` `[29.9, 59.6]` | `31.4` `[21.4, 40.1]` | `22.1` | `58.2` `[34.5, 71.1]` | `31.0` `[8.3, 36.9]` | `2/64 (3.1%)` / `1.4%` |
| `HistGBM_Reg_LOCampO` | `46.90` | `57.3` (`10.1–75.0`) | `7.13` | `60.0` / `7.28` | `60.4` `[48.1, 72.7]` | `22.1` `[17.9, 26.9]` | `22.1` | `68.4` `[52.3, 80.4]` | `19.0` `[2.4, 27.4]` | `4/73 (5.5%)` / `2.9%` |
| `HistGBM_Mono_LOCampO` | `47.09` | `57.5` (`10.1–75.0`) | `6.25` | `58.6` / `6.68` | `72.9` `[59.3, 86.2]` | `27.9` `[22.3, 32.5]` | `22.1` | `57.1` `[48.4, 62.7]` | `40.5` `[7.1, 46.4]` | `7/63 (11.1%)` / `5.0%` |
| `Ridge_LOCampO` | `49.48` | `55.2` (`24.7–75.0`) | `9.61` | `59.2` / `8.23` | `60.0` `[48.2, 71.4]` | `26.1` `[20.5, 32.1]` | `22.1` | `57.7` `[44.0, 75.0]` | `39.3` `[10.7, 54.8]` | `5/64 (7.8%)` / `3.6%` |
| `ElasticNet_LOCampO` | `49.56` | `55.2` (`24.3–75.0`) | `9.60` | `59.2` / `8.24` | `60.7` `[52.0, 71.4]` | `23.6` `[17.5, 30.0]` | `22.1` | `57.1` `[42.1, 72.2]` | `44.0` `[11.9, 53.6]` | `6/63 (9.5%)` / `4.3%` |
| `QuantileGBM_p10_LOCampO` | `38.78` | `44.1` (`10.0–66.7`) | `0.92` | `47.3` / `0.63` | `53.9` `[32.6, 66.4]` | `23.2` `[17.9, 29.5]` | `22.1` | `61.5` `[40.0, 74.2]` | `25.0` `[8.3, 34.5]` | `2/62 (3.2%)` / `1.4%` |
| `QuantileGBM_p90_LOCampO` | `69.68` | `55.2` (`10.2–74.8`) | `4.48` | `59.4` / `6.10` | `65.7` `[51.8, 80.8]` | `29.6` `[21.2, 42.4]` | `22.1` | `59.9` `[53.4, 66.3]` | `33.3` `[14.3, 45.2]` | `2/55 (3.6%)` / `1.4%` |
| `CQR_Unscaled_LOCampO` | `38.79` | `40.5` (`0.0–100.0`) | `0.21` | `43.2` / `0.16` | `58.2` `[33.5, 81.4]` | `34.6` `[29.0, 38.3]` | `22.1` | `66.0` `[45.1, 77.5]` | `40.5` `[13.1, 50.0]` | `10/64 (15.6%)` / `7.1%` |
| `CQR_Scaled_LOCampO` | `38.85` | `44.8` (`0.0–100.0`) | `0.16` | `47.1` / `0.09` | `65.7` `[39.8, 82.9]` | `36.1` `[30.1, 40.7]` | `22.1` | `63.5` `[27.1, 80.1]` | `39.3` `[14.3, 47.6]` | `14/68 (20.6%)` / `10.0%` |

*(Note: Under exact 5-candidate parity `MARUR, PACER, ACI_g0.05, DecayingOGD, Early`, `HistGBM_57_Ref` reproduces `3/28 (10.7%)` fair / `3/100 (3.0%)` net and `0/20` PACER wins identically; across the 7-candidate grid above including `ACI_g0.005` & `ACI_g0.01`, `HistGBM_57_Ref` yields `3/67 (4.5%)` fair / `3/140 (2.1%)` net. While `CQR_Unscaled` / `CQR_Scaled` reach `15.6%–20.6%` among matched pairs, they do so only by driving supported throughput `U` down to `0.16%–0.21%` while still losing `79%–84%` of matched contrasts.)*

---

## 4. Multiplicity Control & Online ACI Grid Findings (`Exploratory`)

- **ACI Step-Size Sensitivity (`gamma in {0.005, 0.01, 0.05}`):** Across all 10 predictors (`AllMobile`, `Recorded`, `C=10, 40`), mobile median `R_+^hi` spans `[40.44%, 61.36%]` for `ACI_g0.005`, `[41.67%, 65.08%]` for `ACI_g0.01`, and `[36.36%, 63.41%]` for `ACI_g0.05` (vs. `PACER` `[33.87%, 65.38%]`, `MARUR` `[39.71%, 64.29%]`, and `Periodic` `[40.44%, 61.96%]`). Small step sizes adapt too slowly within `Q_new in {10, 40}`, while `gamma = 0.05` triggers erratic threshold swings under missing horizons.
- **Holm-Bonferroni & Benjamini-Hochberg Multiplicity Across All `1,440` New Exploratory `p`-Values (`180` rows x `8` checks):**
  - Unadjusted `p_eq_rel50 < 0.05`: `95/180` -> `74/180` BH -> **`36/180` Holm**.
  - Unadjusted Donner-adjusted `p_adj_eq_rel50 < 0.05`: `68/180` -> `53/180` BH -> **`22/180` Holm**.
  - In particular, on `HistGBM_57_Ref` Retrospective `C=10` PACER vs. Periodic, raw Donner-adjusted `p_adj_eq_rel50 = 0.0498` becomes **`0.1573` (BH)** and **`1.000` (Holm)** — underscoring that date-level naive equivalence signals collapse once campaign dependence and family-wise multiplicity are both enforced.
- **Visual Comparison:** [`results/exploratory/predictor_robustness/fig_predictor_robustness.png`](../results/exploratory/predictor_robustness/fig_predictor_robustness.png) ([PDF](../results/exploratory/predictor_robustness/fig_predictor_robustness.pdf)).

*(Notice in [`results/exploratory/predictor_robustness/ablation_by_predictor.csv`](../results/exploratory/predictor_robustness/ablation_by_predictor.csv), `Recorded`-only splits closely mirror the pooled `All`-scenario rates, confirming no synthetic-masking artifact: e.g., `HistGBM_57_Ref` `62.9%` SLA / `25.0%` Rank / `59.4%` Overlap / `40.5%` Pool!=Eq; `HistGBM_Mono_LOCampO` `70.0%` / `27.9%` / `56.0%` / `42.9%`; `CQR_Scaled_LOCampO` `63.6%` / `36.4%` / `63.2%` / `38.1%`.)*
