# When Does Recalibration Help Cellular Throughput Commitments? Accounting for Cost, Missingness, and Abstention

## Abstract

Across six retrospective cohorts and four held-out public archives evaluated under frozen tree predictors and fixed policies, mobile conditional upper violation risk spans 9\% to 68\%---far above nominal $\alpha=0.10$---while supported measured throughput remains 1\% to 3\%, forfeiting most achievable capacity. Why do nominally matched controllers often appear safer in conventional evaluations? Our principal contribution formalizes five necessary single-factor accounting conditions and tests them empirically across non-independent factorial contrasts using controlled ablations and an open-source CLI (\texttt{audit\_policy.py}). Unpacking all-issued risk via $R=(M/N)R_+$, matching realized queries, bounding missing outcomes via $[e/M,(e+m)/M]$, separating offer-weighted from equal-cluster pooling, and adjusting for campaign clustering systematically reverse risk rankings, leave only three wins among twenty-eight jointly fair contrasts (representing three percent of all initial comparisons), and render $\pm 50\%$ utility screening largely inconclusive across three campaigns per scope. Held-out evaluations remain frozen retrospective case studies rather than independent external replication, without closed-loop deployment.

<div class="IEEEkeywords">

Cellular throughput, measurement methodology, selective risk, cluster equivalence, sparse feedback.

</div>

# Introduction

Across archived mobile cellular traces under frozen tree predictors and sparse recalibration, conditional upper violation risk spans $`9\%`$–$`68\%`$ above nominal $`\alpha=0.10`$ while supported measured throughput remains around $`1\%`$–$`3\%`$. Conventional evaluations built around point accuracy, all-issued error rates, or equal nominal probe caps obscure these failures because a controller can appear safer merely by abstaining more often, triggering queries inconsistently, or omitting censored horizon outcomes.

We ask: *do nominally matched cellular throughput recalibration policies remain comparable once evaluated over realized measurement opportunities, finite-record missing-outcome bounds, and campaign-level dependence?* Rather than proposing a headline recalibration controller or bundling unrelated benchmarks, our single primary contribution is establishing and testing exact conditions under which evaluation choices reverse controller comparisons on cellular traces, operationalized via an open-source accounting library, fairness/reporting checklists, and CLI tool (`src/audit/recalibration_audit.py`, `scripts/audit_policy.py`). We organize our evidence around four research questions across $`G=16`$ retrospective and $`G=26`$ held-out dates spanning six physical campaigns:

1.  **RQ1 (Reversal conditions & ablation):** Under what formal conditions do individual accounting layers reverse comparisons (Proposition 1), and how often do single-factor flips occur?

2.  **RQ2 (Risk–utility & fair matching):** Do adaptive controllers improve supported throughput $`U`$ per unit conditional risk $`R_+^{\text{hi}}`$ once realized queries $`Q_{\text{new}}`$ and offer rates $`A`$ are jointly matched?

3.  **RQ3 (Frozen case study & formal limits):** How do MARUR and PACER behave as frozen retrospective case studies, and when do formal pacing bounds hold vacuously?

4.  **RQ4 (Campaign precision & scope):** What precision limits remain across three campaigns per geographic scope?

All evidence comes from retrospective public archives without independent external replication or live field validation, and it does not cover other devices, operators, measurement tools, or closed-loop deployment; all negative findings are retained.

# Related Work

## Cellular Measurement, Prediction, and Rate Decisions

Operational measurements establish that cellular throughput depends on radio conditions, mobility, and collection protocol. Earlier channel/context traces (Raca et al. 2020) and commercial millimeter-wave (mmWave) fifth-generation (5G) campaigns (Narayanan et al. 2020) enabled context-aware rate prediction, while newer multi-technology datasets and machine-learning evaluations extend these insights to non-standalone 5G deployments (Kousias, Rajiullah, Caso, Ali, et al. 2024; Caso et al. 2024; Kousias, Rajiullah, Caso, Alay, et al. 2024). However, forecast errors sampled within a single route or shared drive are temporally correlated rather than independent replications, and low point error does not bound rate-commitment violations.

Missing inputs and deployment realism motivate complementary lines of work. The Boosted Additive Model for data with Missing Observations (BAMMO) addresses missing input covariates in commercial 5G prediction (Jacobson et al. 2025), rather than failed acquisition of future calibration outcomes. Smartphone streaming traces expose real-time sampling shift (Raca et al. 2024), multi-carrier measurements reveal divergent link predictability (Basit et al. 2024), and *CellReplay* (Sentosa et al. 2025) solves trace-replay emulation drift caused by adaptive workload feedback. Even without emulation-workload drift on fixed logs, however, global, grouped, and adaptive conformal baselines such as Sirhan (Sirhan 2026) evaluate full-outcome splits without auditing probe budgets or missing completions.

## Why Isolated Accounting Adjustments Are Insufficient

Existing statistical methodologies examine missingness, adaptation, or sparse labels individually: missing-pattern conformal prediction (Zaffran et al. 2023) and covariate-shift or weighted quantiles (Tibshirani et al. 2019; Barber et al. 2023) focus on covariate or smooth distributional drift; sequential time-series conformal methods (Zaffran et al. 2022; Xu and Xie 2023; Lin et al. 2022; Gibbs and Candès 2024), ACI/OGD (Gibbs and Candès 2021; Bhatnagar et al. 2023; Angelopoulos et al. 2023; Anastasios Nikolas Angelopoulos et al. 2024; Podkopaev et al. 2024), and risk control (Bates et al. 2021; Anastasios N. Angelopoulos et al. 2024; Angelopoulos et al. 2025; Gibbs et al. 2025; Gauthier et al. 2026) generally assume complete step-wise feedback; while upfront stopping (Ilyas et al. 2026), semi-bandit feedback (Ge et al. 2025), sporadic feedback (Hou et al. 2025), and selective abstention/stability analyses (Geifman and El-Yaniv 2017; Min et al. 2026) treat isolated aspects of cost or abstention. On real cellular logs, however, evaluation failures compound across layers: shrinking offer frequency masks conditional risk spikes while simultaneously changing realized cooldown queries, position-locked missingness interacts asymmetrically with periodic updates, and offer-count covariance across heterogeneous cohorts flips pooled contrasts. Auditing these multi-layer failures jointly motivates Proposition 1 and Table I.

<div class="table*">

| **Work** | **Modality** | **Environment** | **Core Method** | **Audit Boundary** | **Present Contribution** |
|:---|:---|:---|:---|:---|:---|
| BAMMO (Jacobson et al. 2025) | Radio/context | Commercial mmWave 5G | Missing-covariate additive boosting | Missing inputs differ from missing future outcomes | Separates input vs. outcome missingness |
| Raca et al. (Raca et al. 2024) | Smartphone | Live video streaming | On-device throughput prediction | No selective commitment audit across caps | Temporally ordered trace ledger without live-QoE claim |
| CellReplay (Sentosa et al. 2025) | Emulated traces | Live cellular workloads | Multi-workload replay interpolation | Addresses replay workload drift rather than probe accounting | Audits fixed-trace probe cost, missingness, and clustering |
| Basit et al. (Basit et al. 2024) | Rate histories | Multi-carrier driving | Fine-grained ML predictability | Conflicting histories limit point accuracy | Audits conditional risk and supported rate |
| Sirhan (Sirhan 2026) | Rate, RAT, handover | Commercial mobile 5G | Global/grouped/adaptive conformal bounds | Full-outcome split; no attempt-budget ledger | Separates probe attempts and missing outcomes |
| Zaffran et al. (Zaffran et al. 2023) | Incomplete inputs | Regression missingness | Missing-pattern conformal sets | Input missingness differs from failed requests | Tracks probe failures vs. buffer admissions |
| Conformal PID (Angelopoulos et al. 2023) | Temporal scores | Forecasting series | Online PID quantile control | Assumes full score feedback every step | Audits delayed and censored sparse probes |
| Ilyas et al. (Ilyas et al. 2026) | IID arrivals | Label stopping | Cost-efficient stopping rule | Stationary arrivals differ from mobile drift | Accounts seed vs. new probes under drift |
| Ge et al. (Ge et al. 2025) | Partial labels | Semi-bandit sets | Online conformal regret bounds | Set-inclusion differs from probe failure | Tracks maturation delay and charged probes |
| Hou et al. (Hou et al. 2025) | Solver outputs | Edge–cloud systems | Sporadic-feedback calibration | Two-sided width differs from SLA rate risk | One-sided commitments and abstention |
| CRC (Anastasios N. Angelopoulos et al. 2024) | Scores/losses | Vision/language sets | Expected monotone-loss control | Population guarantees differ from finite logs | Finite-record $`[e/M,(e+m)/M]`$ risk intervals |
| Min et al. (Min et al. 2026) | Predictive sets | Regression/classif. | Coverage–length stability critique | Diagnostic rather than probe-cost ledger | Jointly tracks $`A`$, $`R_+`$, $`U`$, and query cost |
| Gauthier et al. (Gauthier et al. 2026) | Adaptive sets | Adaptive coverage | Learned coverage via e-values | Requires e-value policy design | Audits fixed-cadence vs. adaptive comparators |
| **Present study** | **Rate and radio** | **Ten cohorts (42 dates)** | **Measurement ledger and cluster audit** | **Public archives; zero live trips** | **CLI tool, checklist, MDE/TOST, pooling audit** |

</div>

# Measurement-Accounting Framework and Assumptions

Fig. 1 summarizes the complete workflow, explicitly separating source training (*Rome Op1* 57 rows), retrospective policy design, frozen held-out scoring (with prior archive access), and post-hoc exploratory audits.

<figure id="fig:pipeline" data-latex-placement="!t">
<embed src="figures/main_fig0_pipeline_flow.png" style="width:85.0%" />
<figcaption>End-to-end study workflow explicitly distinguishing source predictor fitting, retrospective design, SHA-256 frozen retrospective scoring (prior archive access, not independent external replication), five-layer accounting (Proposition 1), and post-hoc exploratory audits.</figcaption>
</figure>

## Decision Clock, Accounting Identity, and Reversal Conditions

At scheduled issue time $`t`$, a frozen predictor outputs point forecast $`p_t`$ from strictly prior lag throughput and radio telemetry. A controller selects nonnegative commitment $`L_t \ge 0`$ and decides whether to probe $`y_t`$ over a 60-second horizon (`ready` timestamp); ticks lacking a valid prior rate are marked ineligible ($`L_t = 0`$). All controllers receive identical pre-test initial labels excluded from new target queries $`Q_{\text{new}}`$ under nominal cap $`C_{\text{new}}`$.

Across $`N`$ eligible opportunities, let $`M = \sum_t \mathbf{1}\{L_t > 0\}`$ denote positive commitments, $`A = M/N`$ positive-offer frequency, $`e`$ observed violations ($`L_t > y_t`$), and $`m`$ positive offers lacking observed $`y_t`$. Because $`y_t \ge 0`$ prevents zero commitments from violating, all-issued risk $`R`$ and positive-offer conditional risk $`R_+`$ satisfy
``` math
\begin{equation}
\begin{aligned}
R &= A \cdot R_+,\qquad R \in [e/N, (e+m)/N],\\
R_+ &\in [e/M, (e+m)/M]\qquad (M > 0),
\end{aligned}
\label{eq:risk_bounds}
\end{equation}
```
and service utility is measured by supported throughput $`U = \sum_{t:y_t\text{ obs}}\min(L_t,y_t)/\sum_{t:y_t\text{ obs}}y_t`$.

**Proposition 1 (Algebraic & Structural Evaluation Reversal Conditions):** Throughout, physical campaign-dates ($`G`$ units) combine co-located links on shared drive dates, so *equal-cluster* and *equal-unit* both denote unweighted averaging across those $`G`$ dates (distinct from unweighted cohort averaging and offer- or traffic-weighted pooling). Proposition 1 states exact algebraic and design conditions defining when an ordering or rejection flips across finite ledgers; the empirical question tested in RQ1 is how frequently real cellular logs trigger them across physical campaigns:

1.  *Abstention rank/SLA flip ($`R`$ vs. $`R_+`$):* Pairwise risk order reverses ($`R_a < R_b`$ with $`R_{+,a} > R_{+,b}`$) iff $`A_a/A_b < R_{+,b}/R_{+,a}`$, and nominal compliance $`R_a \le \alpha`$ admits $`R_{+,a} > \alpha`$ whenever $`A_a < R_{+,a}/\alpha`$.

2.  *Query disparity ($`C_{\text{new}}`$ vs. $`Q_{\text{new}}`$):* Nominal-cap equality misallocates measurement effort whenever trigger or cooldown logic produces $`Q_{\text{new},a} \ne Q_{\text{new},b}`$.

3.  *Missing-outcome indeterminacy ($`R_+^{\text{meas}}`$ vs. $`[R_+^{\text{lo}}, R_+^{\text{hi}}]`$):* Complete-case orderings lose worst-case identifiability whenever $`\max(R_+^{\text{lo},a}, R_+^{\text{lo},b}) \le \min(R_+^{\text{hi},a}, R_+^{\text{hi},b})`$ with $`m_a + m_b > 0`$.

4.  *Pooling-weight reversal ($`\Delta_{\text{pool}}`$ vs. $`\Delta_{\text{eq}}`$):* Offer-weighted risk contrast $`\sum_c w_c^a R_{+,c}^a - \sum_c w_c^b R_{+,c}^b`$ (with $`w_c = M_c / \sum_j M_j`$) reverses equal-unit mean $`\Delta_{\text{eq}}`$ whenever cohort risk covaries with offer shares or weights differ across policies.

5.  *Clustering variance reversal ($`G`$ vs. $`G_{\text{eff}}`$):* Date-level rejections reverse under campaign dependence whenever intra-campaign correlation $`\rho > 0`$ inflates $`\text{DEFF}=1+(\bar{n}-1)\rho`$ such that effective units $`G_{\text{eff}}=G/\text{DEFF}`$ fail critical significance, or hierarchical bootstrap across $`k`$ campaigns fails containment.

## Missingness Mechanisms, Margin Choice, and Utility Meaning

Missing horizon outcomes arise from two distinct mechanisms in the logs: natural trace or session truncation censoring past log completion (`Recorded`), and synthetic deterministic masking (`QueryCensor20`), which suppresses every fifth eligible tick and selectively skips fixed periodic updates while hitting asynchronous triggers. Partial-identification bounds <a href="#eq:risk_bounds" data-reference-type="eqref" data-reference="eq:risk_bounds">[eq:risk_bounds]</a> (Manski 1989) require only binary bounded loss outcomes without assuming missingness-at-random, identifying the range of possible finite-record risk on historical logs rather than a sampling distribution for future unseen deployment; because those mechanisms differ, we report natural truncation separately from synthetic masking in Table III and Supplement Table S21, while supported throughput $`U`$ remains conditional on observed outcomes.

Because multiple controllers and cohorts share underlying drive traces, all $`p`$-values and TOST checks act as exploratory retrospective diagnostics without family-wise multiple-testing adjustment. No standard cellular SLA defines a universal relative utility equivalence threshold, so $`\pm 50\%`$ (and $`\pm 25\%`$ sensitivity) serve explicitly as *exploratory precision-screening benchmarks* asking whether three campaigns can rule out halving or doubling baseline throughput—not production acceptability thresholds. Fixed one-point and two-point margins likewise span excessive fractions of a $`1\%`$–$`3\%`$ baseline, while operationally forfeiting almost all measured throughput via abstention and conservative backoffs.

## Fairness Checklist, Reporting CLI, and Evaluated Policies

Table II consolidates all nine evaluated policy families alongside a seven-axis fairness audit confirming identical initial labels, identical slots $`N`$, unequal realized query spend ($`Q_{10}/Q_{40}`$), distinct offer rates, missingness rules, and feature access. Our library (`src/audit/recalibration_audit.py`) and CLI (`scripts/audit_policy.py`) enforce <a href="#eq:risk_bounds" data-reference-type="eqref" data-reference="eq:risk_bounds">[eq:risk_bounds]</a>, emit warnings from the six-item checklist, and compute separated equal-cluster and pooled-ratio TOST tests. Run on `examples/worked_heldout_c10_ledger.csv`, the CLI flags zero-offer clusters, unmatched queries, inconclusive equivalence, and offer-count pooling divergence ($`-23.41`$ vs. $`+0.37`$ pp).

<figure data-latex-placement="!t">

</figure>

<div class="table*">

|  |  |  |  |  |  |  |
|:---|:---|:---|:---|:---|:---|:---|
| Policy | Trigger | Calibration | KeyParams | Q10/Q40 | MeanA | Missing/Access |
| Frozen | None (C=0) | Static Init10 | init=10 | 0.0 | 35.9 | None / None |
| Early | Every elig | FIFO W=10 | C=10/40 | 10.0/40.0 | 28.3 | Insert p / Resid |
| Random | Uniform seed | FIFO W=10 | seeds=42,123,2026 | 10/Match | 6-coh seed | Insert p / Resid |
| Periodic | Every P=15 | FIFO W=10 | P=15, W=10 | 10.0/21.6 | 22.1 | Insert p / Resid |
| ACI | Every P=15 | Online alpha | eta=0.05, W=10 | 10.0/21.6 | 18.1 | err=1 / Online a |
| DecayingOGD | Every P=15 | Decaying step | exp=0.6 | 10.0/21.6 | 27.2 | p miss / Step |
| MARUR | Age 60m/RAT | Pat/Pool W=10 | age=60m, min=3 | 9.5/30.3 | 30.6 | p+gate / LTE-NR |
| MARUR ablat. | Age/Periodic | Pool/DropMiss | NoPat/NoGate/Drop | Matched | 6-coh abl | Drop / Gate check |
| PACER | Uniform K blk | Smooth sel W=20 | g=0.05, v=0.15 | 9.9/37.8 | 24.5 | Excl W / Veto A |

</div>

# Empirical Results

Six retrospective cohorts operate on 60-second forward-ordered measurement clocks (Kousias, Rajiullah, Caso, Ali, et al. 2024; Caso et al. 2024; NUWiNS 2025; Raca et al. 2020): Rome *E1* and *E3*, US Drive 3 (*AT&T*, *T-Mobile*, *Verizon*), and *Ireland* driving logs, collapsed across co-located links onto three physical campaigns and $`G=16`$ campaign-dates under frozen 57-row *HistGBM*.

Across mobile evaluations, conditional upper risk $`R_+^{\text{hi}}`$ spans $`9\%`$–$`68\%`$ above nominal tolerance while $`U`$ remains around $`1\%`$–$`3\%`$ (Fig. 3; high-budget breakdown in Supplement Table S14).

## RQ1: Controlled Single-Factor Accounting Ablation

Testing Proposition 1 one accounting choice at a time across immutable saved ledgers proves that evaluation reversals are widespread rather than isolated anomalies (Table III, Fig. 2a). Across $`400`$ cohort-model-scenario-cap comparisons versus Periodic, switching from all-issued risk $`R^{\text{hi}}`$ to conditional risk $`R_+^{\text{hi}}`$ flips nominal ten-percent SLA compliance in $`228/400`$ ($`57.0\%`$) cases and reverses pairwise winners in $`33.8\%`$.

Crucially, these ablation denominators enumerate non-independent factorial contrasts sharing drives across six physical campaigns rather than independent trials: $`400`$ crosses ten cohorts, five active policies versus Periodic, two caps, two models, and two feedback scenarios; $`285`$ selects unresolved contrasts; and $`120`$ crosses three scopes under those same axes.

Evaluating nominal caps without auditing realized spend $`Q_{\text{new}}`$ mismatches probe effort in $`124/400`$ ($`31.0\%`$) comparisons (plus $`72/432`$ active contrasts in the MARUR audit).

Accounting for missingness bounds across unresolved comparisons leaves $`47.4\%`$ ($`135/285`$) with overlapping $`[R_+^{\text{lo}}, R_+^{\text{hi}}]`$ intervals and nine worst-case rank flips.

Separating naturally truncated `Recorded` runs ($`200`$ contrasts) from synthetic `QueryCensor20` confirms that flips are not artifacts of artificial masking: natural truncation alone yields $`55.5\%`$ SLA flips, $`35.5\%`$ rank flips, $`31.0\%`$ query mismatches, and $`47.6\%`$ unresolved overlap across truncated pairs.

Varying pooling rules flips $`\Delta R_+^{\text{hi}}`$ sign in $`47/120`$ ($`39.2\%`$) contrasts and shifts $`\Delta U`$ sign in $`20.8\%`$.

This pooling reversal persists across $`21/60`$ ($`35.0\%`$) naturally truncated `Recorded` contrasts.

Across individual physical campaigns (Supplement Table S21), SLA flips span $`27.5\%`$–$`75.8\%`$ and rank flips span $`10.0\%`$–$`50.0\%`$.

Per-campaign query mismatches span $`20.0\%`$–$`40.0\%`$ across all six campaigns, while Table IV details date-level MARUR mechanisms at matched ten new queries ($`-0.09`$ pp equal-cluster mean across $`G=16`$; *Ireland* removes $`-14`$ shared-offer failures by cutting offers).

<div class="table*">

|  |  |  |  |  |  |
|:---|:---|:---|:---|:---|:---|
| AccountingChoice | Prop1Condition | Affected | AllPct | RecPct | SecondaryAuditNote |
| All-issued R vs Cond R+ (SLA max 10 pct) | R le a permits R+ above a | 228/400 | 57.0 | 55.5 | 0 algebraic mismatches |
| All-issued R vs Cond R+ (Winner) | A1/A2 below R+2/R+1 | 135/400 | 33.8 | 35.5 | Exact 0 mismatches across 400 |
| Nominal Cnew vs Realized Qnew | Qnew(cand) not eq Qnew(Periodic) | 124/400 | 31.0 | 31.0 | 72/432 in 6-coh MARUR audit |
| Complete R+meas vs Bounds (lo, hi) | max(lo) at most min(hi), m positive | 135/285 | 47.4 | 47.6 | 9 rank / 8 SLA revs |
| OfferWtd vs EqualUnit Pooling (dR+hi) | Cov(w c, r c) not eq 0 revs sum(w d) | 47/120 | 39.2 | 35.0 | 25/120 U revs (20.8 pct) |
| Date TOST vs Donner DEFF (p below 0.05) | DEFF = 1+(n-1)rho above G/Greq | 2/5 | 40.0 | 40.0 | 4/5 HierBoot Eq revs; 0/10 Pool pass |

</div>

<figure id="fig:ablation_pareto" data-latex-placement="!t">
<embed src="figures/main_fig4_ablation_pareto.png" style="width:80.0%" />
<figcaption>Exploratory verification of Proposition 1 across saved factorial contrasts sharing six campaigns: (a) single-factor reversal/ambiguity rates (Donner DEFF flips 2/5, hierarchical bootstrap flips 4/5 naive passes), and (b) 10-cohort Risk–Utility trade-off showing only 3/28 wins among jointly fair pairs (3/100 of all initial contrasts).</figcaption>
</figure>

<div class="table*">

|                  |     |       |         |         |        |        |       |       |       |        |
|:-----------------|:----|:------|:--------|:--------|:-------|:-------|:------|:------|:------|:-------|
| Scope            | G   | QDays | PosDays | Pool dU | BootLo | BootHi | Eq dU | tLo   | tHi   | dRhi   |
| E1               | 7   | 1/3   | 6/6     | +2.38   | +0.76  | +3.70  | +1.45 | -0.01 | +2.90 | +4.62  |
| E3               | 7   | 3/7   | 5/2     | +0.66   | +0.03  | +1.80  | +0.78 | -0.45 | +2.02 | +9.94  |
| ATT              | 3   | 1/2   | 2/2     | +2.58   | +0.00  | +2.90  | +1.65 | -2.05 | +5.36 | +11.15 |
| T-Mobile         | 3   | 1/1   | 1/1     | -0.02   | -0.05  | +0.00  | -0.02 | -0.08 | +0.05 | +0.00  |
| Verizon          | 3   | 1/2   | 1/1     | +0.54   | +0.00  | +1.96  | +0.65 | -2.16 | +3.46 | +6.62  |
| Ireland          | 5   | 2/3   | 5/5     | -2.99   | -4.00  | -1.40  | -2.46 | -4.76 | -0.15 | -4.19  |
| All (16 Dates)   | 16  | 7/13  | 14/13   | +0.21   | -1.26  | +0.79  | -0.09 | -1.27 | +1.08 | +4.07  |
| Ireland (Traces) | 11  | 4/4   | 10/10   | -2.99   | -4.83  | -1.88  | -4.20 | -7.31 | -1.10 | -4.19  |

</div>

## RQ2: Risk–Utility Pareto Frontier and Matched Fairness Audit

Plot (b) of Fig. 2 shows the mean ten-cohort $`(U, R_+^{\mathrm{hi}})`$ trade-off across nominal levels $`\alpha \in \{0.05, 0.10, 0.20\}`$ and $`1800`$ sensitivity runs (Supplement Table S20).

No controller reaches the high-utility, low-risk quadrant: tightening nominal tolerance to five percent shrinks throughput below one percent ($`0.32\%`$–$`0.92\%`$) while conditional risk remains $`28.5\%`$–$`49.3\%`$.

Relaxing nominal tolerance lifts supported throughput to $`4.4\%`$–$`7.4\%`$ only at $`42.9\%`$–$`47.1\%`$ conditional upper risk.

Applying a sequential fairness sieve across $`100`$ *HistGBM Recorded* contrasts versus Periodic drops unfiltered risk–utility wins from $`15/100`$ to $`8/69`$ at matched realized queries.

Further matching positive-offer frequency within five percentage points leaves $`28`$ jointly fair contrasts, yielding a $`3/28`$ ($`10.7\%`$) win rate among jointly fair comparisons.

Relative to the initial candidate pool, those three winners (*E1* and *T-Mobile* Early at low cap, plus *Rome Capacity Op1* MARUR at low cap) represent $`3/100`$ ($`3.0\%`$) of all original comparisons, while PACER achieves $`0/20`$ jointly fair wins.

<figure id="fig:policy_summary" data-latex-placement="!t">
<embed src="figures/main_fig1_policy_summary.png" style="width:70.0%" />
<figcaption>Overview of (a) positive-offer frequency <span class="math inline"><em>A</em></span>, (b) conditional upper risk <span class="math inline"><em>R</em><sub>+</sub><sup>hi</sup></span> vs. <span class="math inline"><em>α</em> = 10%</span>, and (c) supported throughput <span class="math inline"><em>U</em></span> across all 10 archived cohorts (6 retrospective R, 4 held-out H) under frozen HistGBM and recorded feedback.</figcaption>
</figure>

## RQ3: Frozen Held-Out Case Study and Formal Bound Limits

Four held-out public archives contribute $`G=26`$ additional physical campaign-dates ($`42`$ pooled clusters total): shared *Rome Capacity Op1/Op2* dates, post-2011 *Oslo Commute* (Riiser et al. 2013), and *Ireland Static*. We separate the retrospective design phase (inspecting MARUR failures to specify PACER) from the frozen scoring phase (SHA-256 protocol in `docs/PACER_FROZEN_PROTOCOL.md`). Because the authors had prior archive access, held-out results form a frozen retrospective case study rather than independent external confirmation.

Case-study performance remains mixed (Table V, Fig. 4; pooling in Table VI, full matrix in Supplement Table S16): offer-weighted pooling claims a $`-23.41`$ pp low-cap risk improvement for PACER driven by Oslo versus Ireland offer weights, reversing to $`+0.37`$ pp equal-unit, while Persistence PACER loses $`-29.95`$ pp utility.

Formally, PACER’s block-pacing bound ($`6.8/K`$ under locked settings; Supplement Table S22, Fig. S9) assumes an oblivious stream (Vovk et al. 2005) and tightens below the deterministic ceiling $`0.9A`$ in only $`4/40`$ seed-mean cells. Because sparse cellular commitments commonly yield low $`A`$, non-vacuous bounds would require stronger stationarity absent across mobile handovers; practitioners should inspect empirical bounds and $`U`$ directly.

<div class="table*">

|                     |     |       |       |       |       |      |       |      |        |       |
|:--------------------|----:|------:|------:|------:|------:|-----:|------:|-----:|-------:|------:|
| Cohort              | Cap | PerHi | MARHi | PACHi |  PerU | MARU |  PACU | PACA |    Exc |   Bnd |
| Ireland Static (4d) |  10 |  7.84 |  4.65 |  5.12 |  0.06 | 0.14 |  0.79 | 86.7 | -0.044 | 0.685 |
| Ireland Static (4d) |  40 |  8.14 |  4.65 |  6.98 |  0.55 | 0.14 |  3.42 | 86.7 |  0.010 | 0.192 |
| Oslo Commute (7d)   |  10 | 48.70 | 16.23 | 17.69 | 22.46 | 6.85 |  8.83 | 38.0 |  0.020 | 0.683 |
| Oslo Commute (7d)   |  40 | 20.68 | 25.62 | 32.40 | 13.05 | 9.70 | 13.86 | 57.2 |  0.078 | 0.178 |
| Rome Cap Op1 (15d)  |  10 | 46.91 | 44.09 | 52.38 |  1.17 | 1.80 |  1.41 | 17.8 |  0.097 | 0.691 |
| Rome Cap Op1 (15d)  |  40 | 47.19 | 45.76 | 62.96 |  1.30 | 1.89 |  0.55 |  7.6 |  0.038 | 0.182 |
| Rome Cap Op2 (15d)  |  10 | 47.37 | 61.54 | 56.10 |  1.01 | 2.17 |  2.04 | 23.0 |  0.112 | 0.691 |
| Rome Cap Op2 (15d)  |  40 | 53.62 | 45.90 | 47.62 |  1.25 | 1.62 |  0.55 |  5.9 |  0.024 | 0.182 |
| Retro Mean (6 coh.) |  10 | 43.24 | 44.90 | 49.26 |  0.92 | 1.45 |  1.05 | 15.5 |  0.064 | 0.699 |
| Retro Mean (6 coh.) |  40 | 35.67 | 46.74 | 47.81 |  0.85 | 1.85 |  0.94 | 12.3 |  0.037 | 0.184 |

</div>

<figure id="fig:pacer_breakdown" data-latex-placement="!t">
<embed src="figures/main_fig2_pacer_breakdown.png" style="width:66.0%" />
<figcaption>Per-cohort conditional upper risk <span class="math inline"><em>R</em><sub>+</sub><sup>hi</sup></span> comparing Periodic, MARUR, and PACER across frozen held-out archives and the 6-cohort retrospective mean at (a) <span class="math inline"><em>C</em><sub>new</sub> = 10</span> and (b) <span class="math inline"><em>C</em><sub>new</sub> = 40</span> (HistGBM, recorded).</figcaption>
</figure>

<div class="table*">

|            |     |             |       |        |                  |       |
|:-----------|:----|:------------|:------|:-------|:-----------------|:------|
| Scope      | Cap | WeightRule  | Units | dPosHi | Boot95           | dU    |
| HeldOut    | 10  | OfferWtd    | 26    | -23.41 | -37.04 to -5.91  | +0.47 |
| HeldOut    | 10  | EqualUnit   | 22/26 | +0.37  | paired valid     | -3.29 |
| HeldOut    | 10  | EqualCohort | 4 coh | -4.88  | unweighted       | -2.91 |
| HeldOut    | 40  | OfferWtd    | 26    | -0.83  | -16.13 to +11.46 | +0.51 |
| HeldOut    | 40  | EqualUnit   | 12/26 | +2.79  | paired valid     | +0.01 |
| HeldOut    | 40  | EqualCohort | 4 coh | +5.08  | unweighted       | +0.56 |
| AllCohorts | 10  | OfferWtd    | 42    | -14.37 | -26.80 to +0.85  | +0.25 |
| AllCohorts | 10  | EqualUnit   | 32/42 | -1.11  | paired valid     | -2.07 |
| AllCohorts | 40  | OfferWtd    | 42    | +3.29  | -7.49 to +12.49  | +0.31 |
| AllCohorts | 40  | EqualUnit   | 21/42 | -0.94  | paired valid     | +0.02 |

</div>

## RQ4: Estimand-Matched Equivalence and Campaign Precision

Table VII separates equal-cluster (*EqualCl*, $`1.52\%`$ retrospective and $`6.32\%`$ held-out Periodic baseline $`U`$) from pooled-ratio (*PoolRat*, $`0.60\%`$ and $`1.01\%`$) relative equivalence checks.

At naive campaign-date precision under a $`\pm 50\%`$ margin, equal-cluster TOST is inconclusive for retrospective MARUR ($`p=0.1228`$) and low-cap held-out PACER ($`p=0.5369`$), while passing for retrospective PACER ($`p=0.0430`$) and high-cap held-out PACER ($`p=0.0071`$); pooled-ratio TOST fails everywhere.

Re-applying exploratory, low-precision campaign clustering over three campaigns per scope (Supplement Table S18) shrinks effective units to $`3.84/16`$ on retrospective MARUR ($`p=0.2988`$) and $`6.73/26`$ on high-cap held-out PACER.

This adjustment reverses high-cap held-out equivalence ($`p=0.0071 \to 0.1153`$). Where Donner’s three-campaign variance stays near zero on retrospective PACER ($`G_{\text{eff}}=14.77/16`$, $`p=0.0498`$ at low cap), two-stage hierarchical bootstrap intervals cannot create campaign signal and exceed fifty percent everywhere.

Extended sweeps (Supplement Table S23) and leave-one-out checks (Supplement Table S17, Table S19) confirm mobile median risk remains $`47.1\%`$–$`49.3\%`$ across cohort drops and $`45.8\%`$–$`49.3\%`$ across all six campaign exclusions (five remaining campaigns per drop).

High-risk campaigns (early Rome 2023, Rome capacity, and US Drive 3) coincide with low throughput ($`47.5\%`$–$`54.2\%`$ median risk; $`0.35\%`$–$`1.35\%`$ utility). Non-significant TOST checks establish low campaign precision, never equivalence.

<div class="table*">

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|:---|:---|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scope | Cand | Cap | Estimand | G | Z0 | RefU | Delta | RelPct | SpreadOrMDE | pRel50 | pRel25 | pAbs1 | pAbs2 |
| Retro | MAR | 10 | EqualCl | 16 | 4 | 1.52 | -0.09 | -6.2 | MDE 1.65 | 0.1228 | 0.3060 | 0.0609 | 0.0018 |
| Retro | MAR | 10 | PoolRat | 16 | 4 | 0.60 | +0.21 | +35.3 | -44.3 to +207.3 | 0.4145 | 0.5560 | NA | NA |
| Retro | PAC | 10 | EqualCl | 16 | 4 | 1.52 | -0.10 | -6.6 | MDE 1.08 | 0.0430 | 0.2239 | 0.0122 | 0.0000 |
| Retro | PAC | 10 | PoolRat | 16 | 4 | 0.60 | +0.11 | +18.3 | -32.5 to +108.3 | 0.2260 | 0.4255 | NA | NA |
| HeldOut | MAR | 10 | EqualCl | 26 | 4 | 6.32 | -3.36 | -53.1 | MDE 4.54 | 0.5497 | 0.8675 | 0.9286 | 0.8041 |
| HeldOut | MAR | 10 | PoolRat | 26 | 4 | 1.01 | +0.40 | +40.0 | +4.4 to +81.9 | 0.3235 | 0.7325 | NA | NA |
| HeldOut | PAC | 10 | EqualCl | 26 | 4 | 6.32 | -3.29 | -52.0 | MDE 4.01 | 0.5369 | 0.8872 | 0.9457 | 0.8213 |
| HeldOut | PAC | 10 | PoolRat | 26 | 4 | 1.01 | +0.47 | +46.9 | -1.5 to +114.7 | 0.4240 | 0.7285 | NA | NA |
| HeldOut | PAC | 40 | EqualCl | 26 | 2 | 4.47 | +0.01 | +0.3 | MDE 2.46 | 0.0071 | 0.1008 | 0.1261 | 0.0132 |
| HeldOut | PAC | 40 | PoolRat | 26 | 2 | 1.17 | +0.51 | +43.1 | -39.5 to +154.0 | 0.4155 | 0.5925 | NA | NA |
| AllCoh | PAC | 40 | EqualCl | 42 | 6 | 3.27 | +0.02 | +0.8 | MDE 1.53 | 0.0021 | 0.0721 | 0.0372 | 0.0003 |
| AllCoh | PAC | 40 | PoolRat | 42 | 6 | 0.80 | +0.31 | +38.6 | -21.2 to +113.6 | 0.3575 | 0.6105 | NA | NA |

</div>

# Discussion, Limitations, and Conclusion

**Implications for Cellular Evaluation Practice:** Our findings urge four concrete changes in cellular adaptation evaluation: (1) report $`R_+`$, $`[e/M,(e+m)/M]`$, and $`U`$ jointly rather than all-issued $`R`$ alone; (2) match baselines on both realized probes $`Q_{\text{new}}`$ and offer frequency $`A`$; (3) pair offer-weighted contrasts with equal-unit and campaign-adjusted intervals; and (4) distinguish frozen retrospective case studies from independent external trials.

**Limitations and Scope:** All evidence comes from retrospective public archives across six physical campaigns ($`42`$ dates) under frozen parameters rather than independent external replication or live field validation (PACER followed MARUR inspection with prior archive access). These archives do not cover other user devices, absent operators, alternative probing tools, non-60s horizons, or closed-loop congestion; reproduction runs CPU-only via `scripts/reproduce_all.py` and `scripts/audit_policy.py`.

**Conclusion:** Joint measurement-accounting and inference choices systematically reverse controller evaluations on cellular logs: conditional risk spans $`9\%`$–$`68\%`$ above $`\alpha=0.10`$ while supported throughput generally stays around $`1\%`$–$`3\%`$.

Single-factor choices flip $`31\%`$–$`57\%`$ of factorial contrasts across all six physical campaigns, and matching realized queries and offer rates yields $`3/28`$ ($`10.7\%`$) jointly fair wins.

Across the initial pool, only $`3/100`$ ($`3.0\%`$) survive joint fairness as wins, and three-campaign TOST intervals remain statistically inconclusive due to low campaign precision rather than equivalence, with no independent external validation or closed-loop deployment.

# Acknowledgment

OpenAI Codex assisted with code development, experimental checks, and manuscript drafting and revision.

<div id="refs" class="references csl-bib-body hanging-indent">

<div id="ref-angelopoulos2021ltt" class="csl-entry">

Angelopoulos, Anastasios N., Stephen Bates, Emmanuel J. Candès, Michael I. Jordan, and Lihua Lei. 2025. “<span class="nocase">Learn then test: Calibrating predictive algorithms to achieve risk control</span>.” *The Annals of Applied Statistics* 19 (2): 1641–62. <https://doi.org/10.1214/24-AOAS1998>.

</div>

<div id="ref-angelopoulos2024risk" class="csl-entry">

Angelopoulos, Anastasios N., Stephen Bates, Adam Fisch, Lihua Lei, and Tal Schuster. 2024. “Conformal Risk Control.” *Proceedings of the International Conference on Learning Representations (ICLR)*. <https://openreview.net/forum?id=33XGfHLtZg>.

</div>

<div id="ref-pid2023" class="csl-entry">

Angelopoulos, Anastasios N., Emmanuel J. Candès, and Ryan J. Tibshirani. 2023. “<span class="nocase">Conformal PID Control for Time Series Prediction</span>.” *Advances in Neural Information Processing Systems (NeurIPS)* 36: 23047–74. <https://doi.org/10.52202/075280-1000>.

</div>

<div id="ref-angelopoulos2024online" class="csl-entry">

Angelopoulos, Anastasios Nikolas, Rina Barber, and Stephen Bates. 2024. “<span class="nocase">Online conformal prediction with decaying step sizes</span>.” *Proceedings of the 41st International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 235: 1616–30. <https://proceedings.mlr.press/v235/angelopoulos24a.html>.

</div>

<div id="ref-barber2023" class="csl-entry">

Barber, Rina Foygel, Emmanuel J. Candès, Aaditya Ramdas, and Ryan J. Tibshirani. 2023. “<span class="nocase">Conformal prediction beyond exchangeability</span>.” *The Annals of Statistics* 51 (2): 816–45. <https://doi.org/10.1214/23-AOS2276>.

</div>

<div id="ref-basit2024" class="csl-entry">

Basit, Omar, Phuc Dinh, Imran Khan, et al. 2024. “<span class="nocase">On the Predictability of Fine-Grained Cellular Network Throughput Using Machine Learning Models</span>.” *2024 IEEE 21st International Conference on Mobile Ad-Hoc and Smart Systems (MASS)*, 47–56. <https://doi.org/10.1109/MASS62177.2024.00018>.

</div>

<div id="ref-bates2021" class="csl-entry">

Bates, Stephen, Anastasios Angelopoulos, Lihua Lei, Jitendra Malik, and Michael Jordan. 2021. “<span class="nocase">Distribution-free, Risk-controlling Prediction Sets</span>.” *Journal of the ACM* 68 (6): 1–34. <https://doi.org/10.1145/3478535>.

</div>

<div id="ref-bhatnagar2023" class="csl-entry">

Bhatnagar, Aadyot, Huan Wang, Caiming Xiong, and Yu Bai. 2023. “<span class="nocase">Improved Online Conformal Prediction via Strongly Adaptive Online Learning</span>.” *Proceedings of the 40th International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 202: 2337–63. <https://proceedings.mlr.press/v202/bhatnagar23a.html>.

</div>

<div id="ref-caso2024" class="csl-entry">

Caso, Giuseppe, Mohammad Rajiullah, Konstantinos Kousias, et al. 2024. “<span class="nocase">The Chronicles of 5G Non-Standalone: An Empirical Analysis of Performance and Service Evolution</span>.” *IEEE Open Journal of the Communications Society* 5: 7380–99. <https://doi.org/10.1109/OJCOMS.2024.3499370>.

</div>

<div id="ref-gauthier2026" class="csl-entry">

Gauthier, Etienne, Francis Bach, and Michael I. Jordan. 2026. “<span class="nocase">Adaptive Coverage Policies in Conformal Prediction</span>.” *Proceedings of the 29th International Conference on Artificial Intelligence and Statistics (AISTATS)*, Proceedings of machine learning research, vol. 300: 3196–204. <https://proceedings.mlr.press/v300/gauthier26a.html>.

</div>

<div id="ref-ge2025" class="csl-entry">

Ge, Haosen, Hamsa Bastani, and Osbert Bastani. 2025. “<span class="nocase">Stochastic Online Conformal Prediction with Semi-Bandit Feedback</span>.” *Proceedings of the 42nd International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 267: 18954–65. <https://proceedings.mlr.press/v267/ge25a.html>.

</div>

<div id="ref-geifman2017" class="csl-entry">

Geifman, Yonatan, and Ran El-Yaniv. 2017. “<span class="nocase">Selective Classification for Deep Neural Networks</span>.” *Advances in Neural Information Processing Systems (NeurIPS)* 30: 4878–87. <https://proceedings.neurips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html>.

</div>

<div id="ref-gibbs2021" class="csl-entry">

Gibbs, Isaac, and Emmanuel J. Candès. 2021. “Adaptive Conformal Inference Under Distribution Shift.” *Advances in Neural Information Processing Systems (NeurIPS)* 34: 1660–72. <https://proceedings.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html>.

</div>

<div id="ref-gibbs2024" class="csl-entry">

Gibbs, Isaac, and Emmanuel J. Candès. 2024. “<span class="nocase">Conformal Inference for Online Prediction with Arbitrary Distribution Shifts</span>.” *Journal of Machine Learning Research* 25 (162): 1–36. <https://jmlr.org/papers/v25/22-1218.html>.

</div>

<div id="ref-gibbs2025" class="csl-entry">

Gibbs, Isaac, John J. Cherian, and Emmanuel J. Candès. 2025. “<span class="nocase">Conformal prediction with conditional guarantees</span>.” *Journal of the Royal Statistical Society Series B: Statistical Methodology* 87 (4): 1100–1126. <https://doi.org/10.1093/jrsssb/qkaf008>.

</div>

<div id="ref-hou2025" class="csl-entry">

Hou, Qiushuo, Sangwoo Park, Matteo Zecchin, Yunlong Cai, Guanding Yu, and Osvaldo Simeone. 2025. “<span class="nocase">Online Conformal Probabilistic Numerics via Adaptive Edge-Cloud Offloading</span>.” *Proceedings of the First International Conference on Probabilistic Numerics*, Proceedings of machine learning research, vol. 271: 138–46. <https://proceedings.mlr.press/v271/hou25a.html>.

</div>

<div id="ref-ilyas2026" class="csl-entry">

Ilyas, Andrew, Joonhyuk Ko, Jingwu Tang, Steven Wu, and Jiahao Zhang. 2026. “Provably Label-Efficient Conformal Prediction.” *Proceedings of the 43rd International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 306: 49578–97. <https://proceedings.mlr.press/v306/ilyas26a.html>.

</div>

<div id="ref-jacobson2025" class="csl-entry">

Jacobson, Tate, Jie Ding, and Hui Zou. 2025. “<span class="nocase">Predicting 5G throughput with BAMMO, a boosted additive model for data with missing observations</span>.” *Journal of the Royal Statistical Society Series C: Applied Statistics* 74 (1): 249–73. <https://doi.org/10.1093/jrsssc/qlae054>.

</div>

<div id="ref-kousias2024data" class="csl-entry">

Kousias, Konstantinos, Mohammad Rajiullah, Giuseppe Caso, Usman Ali, et al. 2024. “<span class="nocase">A Large-Scale Dataset of 4G, NB-IoT, and 5G Non-Standalone Network Measurements</span>.” *IEEE Communications Magazine* 62 (5): 44–49. <https://doi.org/10.1109/MCOM.011.2200707>.

</div>

<div id="ref-kousias2024model" class="csl-entry">

Kousias, Konstantinos, Mohammad Rajiullah, Giuseppe Caso, Ozgu Alay, et al. 2024. “<span class="nocase">Empirical performance analysis and ML-based modeling of 5G non-standalone networks</span>.” *Computer Networks* 241: 110207. <https://doi.org/10.1016/j.comnet.2024.110207>.

</div>

<div id="ref-lin2022" class="csl-entry">

Lin, Zhen, Shubhendu Trivedi, and Jimeng Sun. 2022. “<span class="nocase">Conformal Prediction with Temporal Quantile Adjustments</span>.” *Advances in Neural Information Processing Systems (NeurIPS)* 35: 31017–30. <https://doi.org/10.52202/068431-2249>.

</div>

<div id="ref-manski1989selection" class="csl-entry">

Manski, Charles F. 1989. “<span class="nocase">Anatomy of the Selection Problem</span>.” *Journal of Human Resources* 24 (3): 343–60. <https://doi.org/10.2307/145818>.

</div>

<div id="ref-min2026" class="csl-entry">

Min, Yizhou, Yizhou Lu, Lanqi Li, Zhen Zhang, and Jiaye Teng. 2026. “<span class="nocase">Questioning the Coverage-Length Metric in Conformal Prediction: When Shorter Intervals Are Not Better</span>.” *Proceedings of the 43rd International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 306: 88935–63. <https://proceedings.mlr.press/v306/min26c.html>.

</div>

<div id="ref-narayanan2020" class="csl-entry">

Narayanan, Arvind, Eman Ramadan, Rishabh Mehta, et al. 2020. “<span class="nocase">Lumos5G: Mapping and Predicting Commercial mmWave 5G Throughput</span>.” *Proceedings of the ACM Internet Measurement Conference (IMC)*, 176–93. <https://doi.org/10.1145/3419394.3423629>.

</div>

<div id="ref-nuwinsarchive" class="csl-entry">

NUWiNS. 2025. *PAM 2025 Multi-Carrier Dataset*. Public data and transfer intervals, commit 782b712. <https://github.com/NUWiNS/pam2025-multi-carrier-dataset>.

</div>

<div id="ref-podkopaev2024" class="csl-entry">

Podkopaev, Aleksandr, Dong Xu, and Kuang-Chih Lee. 2024. “<span class="nocase">Adaptive Conformal Inference by Betting</span>.” *Proceedings of the 41st International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 235: 40886–907. <https://proceedings.mlr.press/v235/podkopaev24a.html>.

</div>

<div id="ref-raca2020" class="csl-entry">

Raca, Darijo, Dylan Leahy, Cormac J. Sreenan, and Jason J. Quinlan. 2020. “<span class="nocase">Beyond throughput, the next generation: a 5G dataset with channel and context metrics</span>.” *Proceedings of the 11th ACM Multimedia Systems Conference (MMSys)*, 303–8. <https://doi.org/10.1145/3339825.3394938>.

</div>

<div id="ref-raca2024" class="csl-entry">

Raca, Darijo, Ahmed H. Zahran, Cormac J. Sreenan, Rakesh K. Sinha, Emir Halepovic, and Vijay Gopalakrishnan. 2024. “<span class="nocase">Device-Based Cellular Throughput Prediction for Video Streaming: Lessons From a Real-World Evaluation</span>.” *IEEE Transactions on Machine Learning in Communications and Networking* 2: 318–34. <https://doi.org/10.1109/TMLCN.2024.3352541>.

</div>

<div id="ref-riiser2013commute" class="csl-entry">

Riiser, Haakon, Paul Vigmostad, Carsten Griwodz, and Pål Halvorsen. 2013. “<span class="nocase">Commute Path Bandwidth Traces from 3G Networks: Analysis and Applications</span>.” *Proceedings of the 4th ACM Multimedia Systems Conference (MMSys)*, 114–18. <https://doi.org/10.1145/2483977.2483991>.

</div>

<div id="ref-sentosa2025cellreplay" class="csl-entry">

Sentosa, William, Balakrishnan Chandrasekaran, P. Brighten Godfrey, and Haitham Hassanieh. 2025. “CellReplay: Towards Accurate Record-and-Replay for Cellular Networks.” *Proceedings of the 22nd USENIX Symposium on Networked Systems Design and Implementation (NSDI 25)*, 1169–86. <https://www.usenix.org/conference/nsdi25/presentation/sentosa>.

</div>

<div id="ref-sirhan2026" class="csl-entry">

Sirhan, Najem N. 2026. “<span class="nocase">Handover-Aware Conformal Throughput Intervals for Risk-Sensitive Rate Selection in Mobile 5G</span>.” *Network* 6 (4): 92. <https://doi.org/10.3390/network6040092>.

</div>

<div id="ref-tibshirani2019" class="csl-entry">

Tibshirani, Ryan J., Rina Foygel Barber, Emmanuel J. Candès, and Aaditya Ramdas. 2019. “Conformal Prediction Under Covariate Shift.” *Advances in Neural Information Processing Systems (NeurIPS)* 32: 2530–40. <https://proceedings.neurips.cc/paper_files/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html>.

</div>

<div id="ref-vovk2005algorithmic" class="csl-entry">

Vovk, Vladimir, Alex Gammerman, and Glenn Shafer. 2005. *<span class="nocase">Algorithmic Learning in a Random World</span>*. Springer. <https://doi.org/10.1007/b106715>.

</div>

<div id="ref-xu2023" class="csl-entry">

Xu, Chen, and Yao Xie. 2023. “<span class="nocase">Sequential Predictive Conformal Inference for Time Series</span>.” *Proceedings of the 40th International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 202: 38707–27. <https://proceedings.mlr.press/v202/xu23r.html>.

</div>

<div id="ref-zaffran2023" class="csl-entry">

Zaffran, Margaux, Aymeric Dieuleveut, Julie Josse, and Yaniv Romano. 2023. “<span class="nocase">Conformal Prediction with Missing Values</span>.” *Proceedings of the 40th International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 202: 40578–604. <https://proceedings.mlr.press/v202/zaffran23a.html>.

</div>

<div id="ref-zaffran2022" class="csl-entry">

Zaffran, Margaux, Olivier Feron, Yannig Goude, Julie Josse, and Aymeric Dieuleveut. 2022. “<span class="nocase">Adaptive Conformal Predictions for Time Series</span>.” *Proceedings of the 39th International Conference on Machine Learning (ICML)*, Proceedings of machine learning research, vol. 162: 25834–66. <https://proceedings.mlr.press/v162/zaffran22a.html>.

</div>

</div>
