# Path A Theory and Frozen Preregistration: Horizon-Paced Selective Conformal Control (PACER)

**Status:** Mathematical formulation and hyperparameter freeze written **prior** to running any evaluation on untouched held-out archives (`Rome 2023 Capacity Tests`, `Oslo Multi-Route Commute`, `Ireland Static Download`). Zero parameters may be adjusted after unsealing held-out cohorts.

## 1. Selective-Offer Identity and Three Mathematical Failure Modes

Let $t \in \{1, \dots, T\}$ index scheduled opportunities with nonnegative throughput $Y_t \ge 0$, point forecast $p_t$ (ineligible ticks have $L_t = 0$), and committed lower bound $L_t = \max(0, \min(p_t, p_t - q_t))$. Let $I_t = \mathbf{1}\{L_t > 0\}$ denote a positive offer, $O_t \in \{0,1\}$ outcome resolution, $M = \sum_{t=1}^T I_t$, and positive-offer frequency $A = M / T$. Define the conservative upper conditional error indicator:
$$e_t^{\text{cons}} := O_t \mathbf{1}\{L_t > Y_t\} + (1 - O_t).$$

Three exact mechanisms explain why prior sparse-feedback controllers fail on cellular commitments:
1. **Zero-Offer Gradient Dilution:** Standard ACI / DecayingOGD update on $(\mathbf{1}\{L_t > Y_t\} - \alpha)$ across all ticks. Since $L_t = 0 \implies \mathbf{1}\{0 > Y_t\} = 0$, every zero commitment injects $-\alpha < 0$ downward pressure on safety offsets, enforcing $R_{\text{all}} = A \cdot R_+ \approx \alpha \implies R_+ \approx \alpha / A$ (reaching 40–62% conditional risk when $A \approx 0.15\text{–}0.25$).
2. **Discontinuous Sample-Max Cliff:** For window length $n = 10$, conformal rank $r = \lceil 11(1-a) \rceil$ satisfies $r > 10$ whenever $a < 1/11 = 0.0909$, snapping abruptly from $\max(\mathcal{W})$ to $+\infty$ after a single mistake (`gamma = 0.05` drops `0.10` to `0.055`).
3. **Greedy Budget Depletion & Missing-Score Quantile Poisoning:** Front-loaded querying (`MARUR`, `Early`) exhausts budget $C$ on Day 1, leaving remaining days unadapted, while inserting $s_t = p_t$ on unresolved responses into a fixed `max` buffer freezes bounds to zero across non-missing regimes.

## 2. Formal Algorithm (`PACER`)

1. Partition scheduled indices $\{0, \dots, T-1\}$ into $K = \min(C, T)$ disjoint contiguous blocks $\mathcal{B}_0, \dots, \mathcal{B}_{K-1}$ of size $W_k \in \{\lfloor T/K \rfloor, \lceil T/K \rceil\}$.
2. Prior to evaluation, draw one probe index $u_k \sim \text{Uniform}(\mathcal{B}_k)$ independently per block.
3. Maintain block-frozen quantile $q_{(k)} = q_{\text{smooth}}(a_k; \mathcal{W}_k)$ updated strictly at block boundaries using all completed probes:
   - Smooth threshold $q_{\text{smooth}}(a; \mathcal{W})$ returns $+\infty$ iff $a \le -a_{\text{veto}}$; linearly interpolates empirical order statistics on $[1/(n+1), 1]$; and extends continuously above $s_{(n)}$ for $a \in (-a_{\text{veto}}, 1/(n+1))$ scaled by $\kappa_{\text{ext}} \cdot \max(1, s_{(n)} - \text{med}(\mathcal{W}), q_{0.9}(\mathcal{W}) - \text{med}(\mathcal{W}), Q_{0.9}(|\mathcal{W}|))$.
   - If a completed probe returned $O = 1$, append observed residual $p - y$ to observed FIFO buffer $\mathcal{W}$ (cap $W_{\text{obs}} = 20$); missing probes never corrupt $\mathcal{W}$.
   - If a completed probe belonged to a positive commitment ($I = 1$), update selective level:
     $$a_{k+1} = \min\!\left(1,\; a_k + \gamma I_{u_k}(\alpha - e_{u_k}^{\text{cons}})\right).$$

## 3. Exact Theorems (Bounded Arbitrary Sequences)

**Theorem 1 (Selective Excess Violation Control Under Delayed Missing Feedback).** Let $(p_t, Y_t, O_t)_{t=1}^T$ be any arbitrary bounded stream with $Y_t \ge 0$, query budget $C \ge 1$, and inter-block completion delay bounded by at most $D \le 1$ block. Under PACER:
1. $a_k \in [-a_{\text{veto}} - \gamma(1 - \alpha),\; 1]$ deterministically for every block $k$, because $a_k \le -a_{\text{veto}} \implies I_t \equiv 0$.
2. Total query attempts satisfy $Q_{\text{new}} \le C$ with probability $1$.
3. Taking expectation over the stratified uniform block probes $(u_0, \dots, u_{K-1})$:
   $$\mathbb{E}\!\left[\frac{1}{T}\sum_{t=1}^T I_t \left(e_t^{\text{cons}} - \alpha\right)\right] = \mathbb{E}\!\left[A \left(R_+^{\text{upper}} - \alpha\right)\right] \le \frac{W_{\max}}{T} \cdot \frac{\alpha + a_{\text{veto}} + \gamma(1 - \alpha)(1 + D)}{\gamma},$$
   where $W_{\max} = \lceil T / K \rceil \implies \frac{W_{\max}}{T} \approx \frac{1}{K} + \frac{1}{T}$. Notice this bounds violation excess strictly against **positive commitments $\alpha M$**, closing the zero-offer dilution loophole ($R_{\text{all}} \le \alpha$ permitting $R_+ = \alpha/A \gg \alpha$).

**Proof Sketch:** Because $a_{k+1} \le a_k + \gamma I_{u_k}(\alpha - e_{u_k}^{\text{cons}})$ pathwise (truncation at $1$ only lowers $a_{k+1}$), $I_{u_k}(e_{u_k}^{\text{cons}} - \alpha) \le (a_k - a_{k+1}) / \gamma$ for every undelayed block (with at most $\gamma D(1 - \alpha)$ boundary drift across $D$ pending blocks). Summing $k = 0, \dots, K-1$ telescopes to $(a_0 - a_{\text{end}})/\gamma + D(1-\alpha) \le (\alpha + a_{\text{veto}} + \gamma(1-\alpha)(1+D))/\gamma$. By block-constant measurability of $q_{(k)}$ across $\mathcal{B}_k$, $\mathbb{E}[I_{u_k}(e_{u_k}^{\text{cons}} - \alpha) \mid \mathcal{F}_{k-1}, \mathcal{B}_k] = W_k^{-1} \sum_{t \in \mathcal{B}_k} I_t(e_t^{\text{cons}} - \alpha)$. Multiplying by $W_k \le W_{\max}$ and averaging over $T$ completes the bound. $\square$

**Theorem 2 (Adversarial Blind-Suffix Lower Bound for Front-Loaded Probing).** For any controller spending its entire budget $C$ by index $\tau_C < T$ ($Q_t \equiv 0$ for $t > \tau_C$), holding threshold $q_t$ fixed across $M_{\text{post}}$ positive suffix commitments, there exists an outcome-shifted continuation identical on $[1, \tau_C]$ whose conditional violation satisfies $R_+^{\text{upper}} \ge M_{\text{post}} / M$. Whenever horizon pacing keeps $\pi_k \ge 1/W_{\max} > 0$ across all $K$ blocks, blind frozen suffixes are bounded by $W_{\max}$ ticks rather than $T - \tau_C$. $\square$

## 4. Pre-Committed Evaluation Protocol (Frozen Parameters in `configs/pacer.json`)

- **Frozen parameters:** $\alpha = 0.10$, $\gamma = 0.05$, $a_{\text{veto}} = 0.15$, $\kappa_{\text{ext}} = 2.0$, $W_{\text{obs}} = 20$, primary seed `42` (sensitivity seeds `42, 123, 2026`), caps $C_{\text{new}} \in \{10, 40\}$.
- **Untouched Held-Out Public Archives:**
  1. `Oslo Multi-Route Commute` (`data/raw/oslo-playback/`, post-cutoff logs `>= 2011-01-30`, 7 routes across 7 calendar dates, lag-trained tree and persistence).
  2. `Rome 2023 Capacity Tests` (`data/extracted/14073311/.../Capacity Tests/`, Op1 and Op2 active capacity CSVs converted to identical 60s clock protocol with frozen Rome `HistGBM` + `Persistence`).
  3. `Ireland Static Download` (`data/raw/sirhan-external-work/consolidated.parquet`, static download traces excluded from driving-only replay, evaluated with frozen Rome `HistGBM` + `Persistence`).
- **Baseline Comparators on Exact Shared Opportunities:** `Frozen`, `Periodic`, `ACI`, `DecayingOGD`, `MARUR`, and `PACER`. Report all gains, ties, and regressions honestly, using cluster-level (`date` / `route` / `location`) paired comparisons.
