> Historical project record from before the pooled-calibration correction. For current estimates, validation status and publication assessment see [the final research audit](FINAL_RESEARCH_AUDIT.md). Interpret numerical claims below as superseded.

# Mathematical Foundations and Methodology Audit (Phase 8)

**Project:** Cellular Recalibration Benchmark  
**Manuscript Title:** *How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry*  
**Repository:** `https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark`  
**Production Code:** `src/evaluation/conformal.py`, `src/models/baselines.py`, `src/models/bammo.py`, `src/models/neural.py`  
**Evaluation Standard:** IEEE Transactions on Network and Service Management / IEEE Open Journal of the Communications Society  

---

## 1. Conformal Prediction Foundations for Cellular Downlink Throughput

Let $(x_i, y_i) \in \mathcal{X} \times \mathbb{R}_{\ge 0}$ denote a cellular measurement instance, where $x_i$ is the causal feature vector (including lagged throughput, session duration, lag age, and pre-test radio metrics) and $y_i$ is the actual achieved downlink throughput (Mbps). 

Let $\hat{\mu}: \mathcal{X} \to \mathbb{R}$ denote a frozen point throughput estimator trained on a source development set $\mathcal{D}_{\text{train}}$. In telecommunications SLA assurance and adaptive video streaming, symmetric intervals $[\hat{y} - q, \hat{y} + q]$ are uninformative because committing higher bandwidth than delivered causes transport stalling and SLA violation. Instead, operators require a **conservative lower bound** $\hat{y}_i^{\text{lower}}$ satisfying:
$$P(y_{n+1} \ge \hat{y}_{n+1}^{\text{lower}}) \ge 1 - \alpha$$
where $\alpha \in (0, 1)$ is the nominal violation risk tolerance (typically $\alpha = 0.10$ for standard mobile broadband, or $\alpha = 0.01$ for ultra-reliable low-latency slices).

We define the asymmetric signed non-conformity score:
$$R_i = \hat{y}_i - y_i = \hat{\mu}(x_i) - y_i$$
A large positive score $R_i > 0$ indicates that the point predictor over-predicted actual network capacity (overcommitment error).

---

## 2. Mathematical Audit of Implemented Methods

### 2.1 Method 1: Global Split Conformal Calibration (Vovk et al.)

#### Mathematical Formulation
Given a calibration set $\mathcal{D}_{\text{cal}} = \{(x_j, y_j)\}_{j=1}^N$ with non-conformity scores $R_j = \hat{\mu}(x_j) - y_j$:
1. Compute the empirical conformal quantile at level $1 - \alpha$:
   $$\hat{q} = \text{Quantile}\left( \frac{\lceil (N+1)(1-\alpha) \rceil}{N}; \{R_j\}_{j=1}^N \right)$$
2. For an out-of-sample test instance $x_{n+1}$, compute the safe lower bound:
   $$\hat{y}_{n+1}^{\text{lower}} = \max\left(0, \hat{\mu}(x_{n+1}) - \hat{q}\right)$$

#### Lemma 1 (Small-Sample Activation Threshold)
**Statement:** For split conformal prediction with nominal risk $\alpha$, a finite empirical quantile $\hat{q} < \infty$ exists if and only if the calibration sample size $N$ satisfies:
$$N \ge \left\lceil \frac{1 - \alpha}{\alpha} \right\rceil = \left\lceil \frac{1}{\alpha} \right\rceil - 1$$
Specifically, for $\alpha = 0.10$:
$$N \ge \lceil 0.90(N+1) \rceil \iff 0.10 N \ge 0.90 \iff N \ge 9$$
**Proof:** The conformal quantile index is defined as $k = \lceil (N+1)(1-\alpha) \rceil$. Because an empirical sample of size $N$ has at most $N$ order statistics $R_{(1)} \le R_{(2)} \le \dots \le R_{(N)}$, the quantile index $k$ must not exceed $N$. If $k > N$, the probability mass assigned to $\infty$ is non-zero, yielding $\hat{q} = \infty$ (forcing lower bound $\hat{y}^{\text{lower}} = 0$). For $\alpha = 0.10$:
- $N = 8 \implies k = \lceil 9 \times 0.90 \rceil = \lceil 8.1 \rceil = 9 > 8 \implies \hat{q} = \infty$.
- $N = 9 \implies k = \lceil 10 \times 0.90 \rceil = \lceil 9.0 \rceil = 9 \le 9 \implies \hat{q} = R_{(9)} < \infty$. $\blacksquare$

#### Assumptions and Guarantees
- **Exchangeability:** If calibration and test instances are exchangeable (i.i.d.), the marginal coverage guarantee holds exactly in finite samples:
  $$1 - \alpha \le P(y_{n+1} \ge \hat{y}_{n+1}^{\text{lower}}) \le 1 - \alpha + \frac{1}{N+1}$$
- **Under Distribution Shift:** When transferring across operators (E2) or measurement campaigns (E1, E3), exchangeability is violated ($P_{\text{src}} \ne P_{\text{tgt}}$). The finite-sample guarantee no longer strictly holds, motivating target recalibration or weighted conformal prediction.

---

### 2.2 Method 2: Grouped (Missingness-Aware) Conformal Calibration

#### Motivation
In 3GPP Option 3X Non-Standalone networks, sessions with Dual LTE+NR connectivity (Group 3) exhibit higher mean throughput and higher variance due to bursty secondary carrier allocation compared to LTE-only sessions (Group 2). Applying a single global quantile $\hat{q}$ forces the model to be excessively conservative for Group 2 or under-covered for Group 3.

#### Mathematical Formulation
1. Partition calibration residuals into disjoint subsets based on observed telemetry group $g \in \{2, 3\}$:
   $$\mathcal{R}_g = \{ R_j \mid x_j \in \text{Group } g \}$$
2. For each group $g$, if the sample size $N_g = |\mathcal{R}_g| \ge N_{\text{min}}$ (with $N_{\text{min}} = 9$), compute the group-specific quantile:
   $$\hat{q}_g = \text{Quantile}\left( \frac{\lceil (N_g + 1)(1-\alpha) \rceil}{N_g}; \mathcal{R}_g \right)$$
3. **Fallback Hierarchy:** If $N_g < N_{\text{min}}$:
   - Fall back to target global quantile $\hat{q}_{\text{tgt}}$ if $N_{\text{tgt}} \ge 9$.
   - Otherwise, fall back to frozen source global quantile $q_{\text{source}}$.
4. At test time, evaluate:
   $$\hat{y}_{n+1}^{\text{lower}} = \max\left(0, \hat{\mu}(x_{n+1}) - \hat{q}_{g(x_{n+1})}\right)$$

#### Scientific Audit & The Coverage-Utility Trade-Off
- **Exchangeability Assumption:** Assumes exchangeability *conditional on group membership*: $(x_i, y_i) \mid (g_i = g) \sim P_g$.
- **Empirical Trade-off at Small $K$:** In E1 and E2 at $K=10$, target calibration has only $K=10$ total sessions. If Group 3 has 6 sessions and Group 2 has 4 sessions, both groups fall back or operate at the absolute edge of finite-sample support. 
- As audited in Stage A, Grouped Conformal achieves higher supported rate ($U = 0.189$ vs $0.018$ in E2) by accepting a higher violation rate ($V = 0.164$ vs $0.023$). **We do not claim exact group-conditional coverage in small samples; we report it as an operational risk-utility trade-off.**

---

### 2.3 Method 3: Bayes-Corrected Covariate-Shift Conformal Prediction (CS-CP)

#### Mathematical Formulation
Following Tibshirani et al. (2019), when the conditional label distribution is invariant ($P_{\text{src}}(Y|X) = P_{\text{tgt}}(Y|X)$) but the covariate feature distribution shifts ($P_{\text{src}}(X) \ne P_{\text{tgt}}(X)$), conformal prediction is valid if residuals are weighted by the likelihood ratio:
$$w(x) = \frac{p_{\text{tgt}}(x)}{p_{\text{src}}(x)}$$

#### Density Ratio Estimation with Bayes Class-Prior Correction
Let $D \in \{0, 1\}$ denote a domain indicator, with $D=0$ for source instances and $D=1$ for target instances. We train a regularized logistic regression domain discriminator $h(x) = P(D=1 \mid X=x)$.

By Bayes' rule:
$$P(X=x \mid D=1) = \frac{P(D=1 \mid X=x) P(X=x)}{P(D=1)}$$
$$P(X=x \mid D=0) = \frac{P(D=0 \mid X=x) P(X=x)}{P(D=0)}$$

Taking the ratio yields the exact likelihood ratio:
$$w(x) = \frac{p_{\text{tgt}}(x)}{p_{\text{src}}(x)} = \frac{P(X=x \mid D=1)}{P(X=x \mid D=0)} = \frac{P(D=1 \mid X=x)}{1 - P(D=1 \mid X=x)} \cdot \frac{P(D=0)}{P(D=1)}$$

Under empirical sampling with $N_{\text{src}}$ source calibration samples and $N_{\text{tgt}}$ target calibration samples, the empirical prior ratio is:
$$\frac{P(D=0)}{P(D=1)} = \frac{N_{\text{src}}}{N_{\text{tgt}}}$$
Therefore, the **Bayes-corrected density ratio** is:
$$w(x) = \frac{h(x)}{1 - h(x)} \cdot \frac{N_{\text{src}}}{N_{\text{tgt}}}$$

#### Conformal Quantile Computation
Let $\{R_j\}_{j=1}^{N_{\text{src}}}$ denote source calibration residuals with weights $w_j = w(x_j)$. For test instance $x_{n+1}$, define $w_{n+1} = w(x_{n+1})$.
1. Compute normalized conformal probability weights:
   $$p_j(x_{n+1}) = \frac{w_j}{\sum_{k=1}^{N_{\text{src}}} w_k + w_{n+1}}, \quad p_{n+1}(x_{n+1}) = \frac{w_{n+1}}{\sum_{k=1}^{N_{\text{src}}} w_k + w_{n+1}}$$
2. Sort source residuals $R_{(1)} \le R_{(2)} \le \dots \le R_{(N_{\text{src}})}$ and find the smallest index $k$ such that the cumulative sum of weights satisfies:
   $$\sum_{j=1}^k p_{(j)}(x_{n+1}) \ge 1 - \alpha$$
3. The lower bound is $\hat{y}_{n+1}^{\text{lower}} = \max(0, \hat{\mu}(x_{n+1}) - R_{(k)})$.

#### Weight Clipping and Effective Sample Size (ESS)
To prevent extreme weights from destroying calibration efficiency when the domain discriminator produces confident predictions ($h(x) \approx 1$):
- **Weight Clipping:** Weights are clipped to $[w_{\text{min}}, w_{\text{max}}] = [0.01, 100.0]$.
  *(Note: Weight clipping alters the empirical distribution and must be characterized as an operational regularizer, not as preserving the exact theoretical CS-CP guarantee).*
- **Effective Sample Size:** Tracked via Kish's formula:
  $$\text{ESS} = \frac{\left(\sum_{j=1}^{N} w_j\right)^2}{\sum_{j=1}^N w_j^2}$$

---

### 2.4 Method 4: Online Adaptive Conformal Inference (ACI)

#### Mathematical Formulation
When cellular distribution shifts are dynamic, non-stationary, or continuous (e.g. drive tests traversing different micro-cells), Gibbs and Candès (2021) and Zaffran et al. (2022) formulate online step-by-step risk adaptation:
1. Initialize effective risk $\alpha_1 = \alpha = 0.10$.
2. At step $t$, observe prediction $\hat{y}_t$, compute lower bound $\hat{y}_t^{\text{lower}} = \max(0, \hat{y}_t - q_t)$ using rolling empirical quantile at level $1 - \alpha_t$.
3. Observe actual throughput $y_t$. Determine violation indicator:
   $$v_t = \mathbf{1}\{y_t < \hat{y}_t^{\text{lower}}\}$$
4. Update effective risk parameter with learning rate $\gamma = 0.02$:
   $$\alpha_{t+1} = \alpha_t + \gamma (\alpha - v_t)$$
   - If a violation occurs ($v_t = 1$), $\alpha_{t+1} = \alpha_t + \gamma(\alpha - 1) = \alpha_t - 0.90\gamma$. The risk level decreases, expanding the safety margin $q_{t+1}$.
   - If coverage succeeds ($v_t = 0$), $\alpha_{t+1} = \alpha_t + \gamma\alpha$. The risk level increases slightly, contracting the margin to recover utility.

---

## 3. Computational Complexity Comparison

| Algorithm | Training Complexity | Inference Complexity (per session) | VRAM / RAM Footprint | Hardware Target |
|---|---|---|---|---|
| **Persistence** | $\mathcal{O}(1)$ | $\mathcal{O}(1)$ | $< 1\text{ MB}$ | Edge UE / CPU |
| **Ridge Regression** | $\mathcal{O}(N D^2 + D^3)$ | $\mathcal{O}(D)$ | $< 5\text{ MB}$ | Base Station / CPU |
| **HistGradientBoosting** | $\mathcal{O}(M \cdot N \cdot D)$ | $\mathcal{O}(M \cdot \text{depth})$ | $18.4\text{ MB}$ | MEC Host / CPU |
| **BAMMO** | $\mathcal{O}(2^K \cdot M \cdot N_{\text{sub}} \cdot D)$ | $\mathcal{O}(M \cdot \text{depth})$ | $22.1\text{ MB}$ | MEC Host / CPU |
| **GPU Tabular ResNet** | $\mathcal{O}(E \cdot N \cdot W^2)$ | $\mathcal{O}(W^2 \cdot L)$ | $24.7\text{ MB}$ VRAM | NVIDIA RTX 4060 GPU |
| **Global Conformal** | $\mathcal{O}(N_{\text{cal}} \log N_{\text{cal}})$ | $\mathcal{O}(1)$ | $< 2\text{ MB}$ | Edge UE / Base Station |
| **Grouped Conformal** | $\mathcal{O}(N_{\text{cal}} \log N_{\text{cal}})$ | $\mathcal{O}(1)$ hash lookup | $< 2\text{ MB}$ | Edge UE / Base Station |
| **Bayes CS-CP** | $\mathcal{O}(N_{\text{src}} D)$ discriminator | $\mathcal{O}(N_{\text{src}} \log N_{\text{src}})$ | $< 8\text{ MB}$ | Base Station Scheduler |
| **Adaptive ACI** | $\mathcal{O}(1)$ step update | $\mathcal{O}(1)$ | $< 1\text{ MB}$ | Mobile Handset / Modem |

---

## 4. Methodology Audit Summary

1. **Theoretical Boundaries:** Lemma 1 holds exactly; the finite-sample threshold $K \ge 9$ for $\alpha=0.10$ is mathematically verified and tested.
2. **Bayes Correction:** The class-prior correction $\frac{N_{\text{src}}}{N_{\text{tgt}}}$ is mathematically rigorous and prevents severe probability skew in small target datasets.
3. **Honest Characterization:** Grouped conformal prediction and weight-clipped CS-CP are documented with their explicit empirical trade-offs and operational assumptions.

