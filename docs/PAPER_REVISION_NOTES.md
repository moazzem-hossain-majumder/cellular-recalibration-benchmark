# Paper-Side Revision Notes & Actionable Checklist

> **Protocol Note:** Per task constraints, no automatic edits have been applied to [`paper/manuscript.tex`](../paper/manuscript.tex) or [`paper/supplementary.tex`](../paper/supplementary.tex). Use this checklist for the next manuscript revision pass alongside [`docs/PREDICTOR_ROBUSTNESS.md`](PREDICTOR_ROBUSTNESS.md).

---

## 1. Reframe Primary Contribution Around the Audit Framework
- [ ] Explicitly present the **measurement-accounting and statistical-audit framework** (Proposition 1 five-layer reversal conditions, `src/audit/recalibration_audit.py`, `scripts/audit_policy.py`, and the 6-item reporting checklist) as the **sole headline contribution**.
- [ ] Demote **PACER** throughout the Abstract, Introduction, RQ3, and Conclusion from a headline method proposal to an **illustrative frozen retrospective case study** demonstrating how pacing interacts with sparse offer rates ($B_1 < 0.9A$ tightening in only `4/40` cells) and pooling divergence (`-23.41 pp` offer-weighted vs. `+0.37 pp` equal-cluster).
- [ ] Cross-reference the exploratory predictor-robustness stress test (`Verdict = A` in [`results/exploratory/predictor_robustness/comparison_table.csv`](../results/exploratory/predictor_robustness/comparison_table.csv)): across `HistGBM_Reg`, monotonic `RSRP/SINR` `HistGBM`, `Ridge`, `ElasticNet`, `QuantileGBM (0.10, 0.90)`, date-blocked `CQR`, and `ACI (gamma in {0.005, 0.01, 0.05})`, mobile median $R_+^{\text{hi}}$ stays `40.5%–62.7%` (vs. $\alpha=10\%$) while single-factor reversal rates remain `19.0%–72.9%`. Highlight honestly that **supported throughput $U$ is predictor-sensitive** (`6.2%–9.6%` for regularized/monotonic/linear LOCampO vs. `0.9%` `HistGBM_57_Ref` vs. `0.16%–0.21%` CQR).

## 2. Ablation Percentages as Descriptive Contrasts + Campaign-Level Bootstrap CIs
- [ ] Label all ablation denominator counts (`400`, `285`, `120`, `140`, `280`) explicitly as **descriptive enumerations over non-independent factorial contrasts sharing underlying drives across `k=6` campaigns**, never as independent sample sizes for hypothesis testing.
- [ ] Pair every headline flip percentage in Table III and RQ1 with **campaign-level bootstrap 95% confidence intervals** resampling physical campaigns (`k=6`, `B=2,000`) rather than dates (from [`results/exploratory/predictor_robustness/ablation_by_predictor.csv`](../results/exploratory/predictor_robustness/ablation_by_predictor.csv) for `HistGBM_57_Ref` under 7 candidates: SLA `R -> R+` `64.3%` `[37.2%, 82.1%]`, Rank `R -> R+` `23.9%` `[17.3%, 32.1%]`, `Q_new` mismatch `22.1%` `[19.6%, 24.5%]`, Missing `[lo, hi]` overlap `60.2%` `[41.4%, 70.1%]`, Pooling sign reversal `44.0%` `[7.1%, 51.2%]`).

## 3. Add Dedicated Estimator & Accounting Notation Table
Insert a compact notation reference table in Section III covering all eight audit quantities:

| Symbol | Formal Definition | Weighting / Denominator |
|---|---|---|
| **`EqualCl`** | Equal-cluster mean across $G$ physical campaign-dates: $\frac{1}{G}\sum_{g=1}^G U_g$ | Unweighted per physical campaign-date $g$ (co-located links merged) |
| **`EqualUnit`** | Equal physical-unit contrast: $\frac{1}{G}\sum_{g=1}^G (R_{+,g}^{\text{cand}} - R_{+,g}^{\text{ref}})$ (synonymous with `EqualCl` unit weighting for risk & paired deltas) | Unweighted per valid active physical campaign-date $g$ |
| **`EqualCohort`** | Unweighted mean across archived cohort-series tables (each trace/operator table weighted `1`, regardless of $G_c$ days or ticks) | Unweighted per cohort ($10$ cohorts; $4$ held-out cohorts) |
| **`OfferWtd`** | Offer-weighted pooled conditional risk: $\frac{\sum_g (e_g + m_g)}{\sum_g M_g} = \sum_g w_g R_{+,g}^{\text{hi}}$, $w_g = M_g / \sum_j M_j$ | Weighted by policy positive-offer count $M_g$ per cluster |
| **`PoolRat`** | Pooled traffic-weighted utility ratio $\big(\frac{\sum_g \text{deliv}_g^{\text{cand}}/\sum_g \text{obs}_g^{\text{cand}}}{\sum_g \text{deliv}_g^{\text{ref}}/\sum_g \text{obs}_g^{\text{ref}}} - 1\big)$ | Weighted by total observed traffic $\sum_g y_t$ per cluster |
| **`R_+^{\text{hi}}`** | Manski upper bound on positive-offer conditional violation risk: $(e + m) / M$ ($M > 0$) | Positive commitments $M = \sum_t \mathbf{1}\{L_t > 0\}$ |
| **`U`** | Supported measured throughput fraction: $\frac{\sum_{t:y_t\,\text{obs}} \min(L_t, y_t)}{\sum_{t:y_t\,\text{obs}} y_t}$ | Observed-outcome ticks in each scope/cluster |
| **`Q_new`** | Realized new calibration probe queries attempted after the shared $10$-label initialization prefix (bounded by nominal $C_{\text{new}}$) | Post-initialization stream opportunities |

## 4. Expand Limitations Paragraph (Statistical & Protocol Transparency)
Add/expand an explicit Limitations paragraph covering all four points cleanly:
- [ ] **Small campaign count (`k=3` per geographic scope, `k=6` total):** Naive date-level standard errors ($G=16$ or $G=26$) understate uncertainty when observations cluster within campaigns; Donner $G_{\text{eff}}$ drops (`3.84/16`, `6.73/26`) and hierarchical two-stage bootstrap intervals remain wide across only 3 campaigns per scope. Report **Holm-Bonferroni and Benjamini-Hochberg multiplicity-adjusted exploratory p-values** (e.g., Donner passes drop from `68/180` unadjusted to `53/180` BH and `22/180` Holm across all `1,440` exploratory suite p-values).
- [ ] **Retrospective protocol provenance of PACER:** PACER was designed after inspecting retrospective `MARUR` failures (`E1`, `E3`, `US Drive 3`, `Ireland`) and with prior access to held-out public archives; thus [`configs/pacer.json`](../configs/pacer.json) separation creates a **frozen retrospective case study**, not blind independent external validation.
- [ ] **Post-hoc origin of original fairness sieve thresholds:** Explicitly disclose that the `HistGBM_57` Matched Fairness Sieve thresholds (`Q_new` exact match, $|\Delta A| \le 5\text{ pp}$, $\Delta R_+^{\text{hi}} < -1.0\text{ pp}$, $\Delta U \ge -0.05\text{ pp}$) were specified post-hoc in the original analysis (`3/28` / `3/100`), and cite the subsequent pre-committed verification across `9` additional predictors ([`configs/predictor_robustness_exploratory.json`](../configs/predictor_robustness_exploratory.json), commit `a7902bb`), where fair-win share of all `140` pairs remains `1.4%–10.0%`.
- [ ] **Chronological cross-era gap on early archives:** Under strict earlier-in-time LOCampO, `Oslo_Commute` (`2010–2011`) has zero external prior campaigns (only separate pre-cutoff `Oslo_Bus_2010` traces without radio telemetry), and `Ireland_Drive` (`2019`) is preceded only by 2010–2011 HSPA Oslo (`0–7` Mbps).

## 5. Concrete Prospective / External Validation Recommendation
- [ ] Recommend acquiring and scoring **at least one genuinely new, never-previously-inspected cellular measurement campaign and distinct operator/device trace set** (separate from Zenodo `8224890`/`14073311`, UCC `5G`, NUWiNS PAM `2025`, and Riiser `2013`), collected under a **pre-registered prediction & audit commit recorded before trace download**, ideally covering modern closed-loop NR/5G multi-operator mobility over `>= 10` physically independent campaigns so campaign-level MDE drops below policy effect sizes.
