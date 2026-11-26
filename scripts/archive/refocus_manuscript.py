"""One-time manuscript refocus; preserves prior analyses as a separate supplement."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'paper'
old=(P/'manuscript.tex').read_text(encoding='utf8')
if (P/'supplementary.tex').exists():raise SystemExit('Already refocused; edit sources directly')
abstract=old.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0]
supp=old.replace('How Much Recalibration Is Enough? Reliability of Cellular Throughput Forecasts Across Networks with Missing Radio Telemetry','Supplementary Analyses: Cellular Throughput Recalibration')
supp=supp.replace(abstract,'Supporting analyses preserve the original experimental protocols, results and limitations. The main article presents the narrower acquisition-cost and selective-risk argument. These retrospective analyses are not independent confirmatory trials.')
supp=supp.replace(r'\input{tables/table14_marur}',r'\noindent The controller table is reproduced in the main article.')
supp=supp.replace('Table XIV','the main-text controller table')
(P/'supplementary.tex').write_text(supp,encoding='utf8')
(P/'related_work.tex').write_text((ROOT/'literature_review/related_work.tex').read_text(encoding='utf-8-sig'),encoding='utf8')
existing=(P/'references.bib').read_text(encoding='utf8');new=(ROOT/'literature_review/references.bib').read_text(encoding='utf8')
keys=set(re.findall(r'@\w+\{([^,]+)',existing))
for entry in re.split(r'(?=@(?:article|inproceedings)\{)',new)[1:]:
    key=re.search(r'@\w+\{([^,]+)',entry)[1]
    if key not in keys:existing+='\n'+entry
(P/'references.bib').write_text(existing,encoding='utf8')
body=r'''\documentclass[journal,10pt]{IEEEtran}
\usepackage[T1]{fontenc}
\usepackage{amsmath,graphicx,url,array,tabularx,cite}
\begin{document}
\title{When Limited Recalibration Fails: Accounting for Cellular Throughput Commitments}
\author{Md. Moazzem Hossain Majumder}
\maketitle
\begin{abstract}
ABSTRACT
\end{abstract}
\begin{IEEEkeywords}Cellular throughput, calibration feedback, selective prediction, measurement methodology.\end{IEEEkeywords}
\section{Introduction}
An application that commits to a rate needs useful service and a tolerable frequency of broken commitments. Accurate point forecasts, low average violations and small nominal calibration budgets do not independently establish those properties. A controller can make fewer positive offers, avoid expensive feedback, or encounter unobserved outcomes. Each changes the meaning of a favorable reported number.

We ask: when does limited recalibration provide useful cellular throughput commitments, and when do missing feedback and abstention make apparent reliability misleading? We study frozen predictors on outcome-independent scheduled opportunities. MARUR is an implemented age-and-pattern heuristic used to expose these effects. It is neither an optimal acquisition rule nor a method with guaranteed positive-conditional risk.

The contribution comprises three empirical findings: attempted measurements differ from information available to later forecasts; low overall risk can conceal poor reliability among positive commitments; and calibration choices produce cohort-dependent utility--risk trade-offs. The accompanying event ledgers, exact-cost comparisons and offer decompositions make these findings auditable. The archives were already inspected during method development, so subsequent experiments are exploratory. We retain negative findings and do not select a deployment policy from test performance.

\input{related_work.tex}

\section{Decision Process and Evaluation}
\subsection{Scheduled opportunities and acquisition accounting}
At issue time $t$, a frozen predictor outputs $p_t$ using only information available before issue. The controller returns a nonnegative commitment $L_t$ and may request the future outcome. Its response is revealed only after the measurement horizon closes. All scheduled opportunities remain in the ledger; those without a usable predictor are marked ineligible. The eligible denominator includes zero commitments.

Every policy starts with the same ten historical successful labels. Their original acquisition attempts are unknown and are not counted as ten physical measurement attempts. We charge each new query when issued, including requests that fail or finish after the last forecast. We separately record successful responses, unsuccessful responses, admitted calibration scores and updates available to later forecasts. Lag-rate and evaluator measurements remain outside this feedback-access budget. Accordingly, a reduction in requested labels does not demonstrate physical byte, energy or measurement savings.

The primary comparison retains a fixed full suffix and reports actual query attempts. Equal caps do not ensure equal costs. Frozen incurs zero new attempts and cannot be presented as an equal-cost positive-budget comparator. Unmatched comparisons remain descriptive and are not interpolated into matched operating points.

\subsection{Risk, service and abstention}
For $N$ eligible opportunities, let $M$ denote positive offers, $e$ observed violations, and $m$ positive offers with missing outcomes. Since throughput is nonnegative and zero offers cannot violate, all-issued risk and positive-conditional risk satisfy $R=(M/N)R_+$. Thus reducing acceptance can reduce overall risk without improving the reliability of actual commitments.
\[
R\in[e/N,(e+m)/N],\quad R_+\in[e/M,(e+m)/M],\quad M>0.
\]
These are finite-record identification bounds, not confidence intervals or prospective guarantees. If $M=0$, conditional risk is undefined. At trace ends, an unobserved latent service outcome additionally requires a clearly defined measurement target; logs cannot establish that service continued after recording stopped.

Supported-throughput utility is $U=\sum_{t:y_t\text{ observed}}\min(L_t,y_t)/\sum_{t:y_t\text{ observed}}y_t$. It is conditional on measured service. We also report observed supported Mbps per eligible opportunity, with no credited service for missing outcomes. Neither metric measures live application benefit. We report offer frequency, abstention, positive dates, unknown outcomes and feedback costs beside risk and utility. No operational superiority is asserted without independently specified utility, offer-frequency and risk requirements.

\subsection{Implemented policies}
MARUR maintains ten recent admitted scores $s=p-y$. A missing requested outcome contributes the conservative upper score $p$, since $y\geq0$. At nominal $\alpha=0.1$, the corrected quantile uses rank $\lceil(n+1)(1-\alpha)\rceil$; with ten scores this is the maximum. The commitment is $\max(0,p-q)$. Matching-pattern scores are used only with at least nine entries; fewer than three matching entries causes abstention. Query triggers use a sixty-minute completed-response age or a telemetry-pattern change, subject to the remaining cap and at most one pending request. Failed completed responses reset the original trigger state even when an ablation discards their scores.

This is a heuristic with a stated design objective, not a solution to constrained utility maximization. Conservative completion bounds an individual missing score but does not establish a sequential calibration theorem under selective feedback and drift. Periodic, Early and modified ACI share the same feedback interface; ACI here is an explicitly modified sparse-feedback comparator.

\section{Experimental Evidence}
\subsection{Cohorts and dependence}
The main replay uses Rome E1 and E3, three carriers from one US drive, and an Irish cohort. Both the archived histogram-gradient-boosted predictor and persistence are evaluated. Rome has seven test dates per cohort with six shared dates; the US carriers share one campaign with two substantial driving days and a short third calendar date; the Irish cohort has five test dates. Multiple carriers, forecast ticks and repeated masks do not increase independent-trip replication.

The supplementary document preserves session-endpoint comparisons, alternative boundaries, weighting, prediction-model selection, external endpoint protocols, calibration-prefix curves and playback simulations. Those analyses have different units or splits and cannot be pooled as if they were additional samples from the main experiment. Playback is simulation over recorded service, not randomized deployment evidence.

\subsection{Equal-cost comparisons and conditional risk}
The original 576 configurations and 720 audit replays yield 384 exact-cost contrasts across the audit family. On E1 with the frozen tree and ten new queries, MARUR supports 2.907 percent of measured throughput versus Periodic's 0.523 percent, while the all-issued upper-risk bound increases from 6.303 to 10.924 percent. This is a service--risk trade-off, not a reliability gain.

On Ireland both issue 159 positive offers; MARUR eliminates fourteen observed violations on shared offers by reducing their sizes, while support declines from 4.117 to 1.129 percent. On Verizon, removing ten of Early's offers removes six violations, with no failure improvement on the shared offers. The former reflects conservative sizing; the latter reflects selection. Neither establishes a uniformly better policy.

\input{tables/table14_marur}
The table reports all six cohorts at a common cap but displays realized costs explicitly; its rows are not automatically matched-cost comparisons. Positive-conditional risk is frequently high even when overall risk appears low. At ten new queries in the completed-clock, five-minute-spacing experiment, recorded HistGBM conditional upper-risk bounds range from approximately 8.8 percent in Ireland to 62.5 percent in E3. A blanket claim of reliable positive commitments is therefore unsupported.

\subsection{Controlled freshness and window sensitivity}
An additional 1,848-configuration experiment uses fixed timestamp-based independent and burst feedback masks. It separates latest attempt, completed response, successful observed label and admitted-score times. The primary contrast changes only the age clock, with identical five-minute attempt spacing and pattern logic. All 24 recorded-feedback comparisons are unchanged. Across recorded and stressed conditions there are six matched utility gains without higher conditional upper risk, seven losses without lower risk, eight trade-offs or risk-only changes, 129 unchanged cases and eighteen unmatched-cost cases. These dependent configuration counts are descriptive, not replication counts.

Increasing the window to twenty or forty adds no free initial labels. Some cohorts gain utility with nonincreasing conditional upper risk, while E3 and Verizon lose substantial useful throughput. Retaining more scores changes both their ages and pattern support; improvement cannot be attributed solely to quantile stabilization. The main conclusion is heterogeneity, not an optimal window selected from these results.

\subsection{Targeted baselines and mechanism checks}
Three seeded nonadaptive random query schedules test whether adaptive timing adds value beyond acquiring labels. A decaying-step quantile tracker, motivated by online conformal prediction~\cite{angelopoulos2024online}, uses the Periodic feedback schedule. Its signed scores, delayed responses and conservative missing-feedback substitution differ from the published setting, so no theorem is transferred. Separate ablations compare pattern and pooled quantiles with the gate fixed, then remove only the gate with the query schedule fixed. Every cohort, cap and feedback condition is retained. Complete operating points and offer decompositions are provided in the reviewer-baseline supplement; no best test schedule is promoted.

\section{Limitations and Prospective Validation}
All reported optimization and added comparisons use previously inspected archives. The clocks are outcome-independent, but requested observations remain selectively acquired. Finite-record missingness bounds do not quantify uncertainty over future independent trips. Synthetic feedback failures test specified mechanisms rather than estimating physical outage processes. In addition, a prospective full-minute service definition will not perfectly reproduce every archive's transfer-truncated endpoint.

The next study must freeze predictor hashes, feature mappings, initialization, policies, schedules, application requirements and analysis before collection. We propose an adaptive-video-streaming application, first using a synchronized shadow measurement study and subsequently a separate randomized live application trial. These are unexecuted designs. Practical thresholds are planning assumptions requiring application validation, not values inferred from favorable archive results.

Eighteen usable paired trips provide roughly five-percentage-point utility precision only under an assumed paired standard deviation of 0.10. This does not justify rare-violation precision or a ten-percent conditional-risk certification. The protocol retains all started trips, clusters simultaneous carriers, records zero-positive and wholly missing trips, and requires a new precision calculation using outcome-blinded pilot variability before registration. Live QoE claims require application outcomes and measurement-overhead accounting, not replay alone.

\section{Conclusion}
Limited recalibration does not consistently produce useful, reliable positive throughput commitments across the examined cellular cohorts. An auditable decision ledger distinguishes acquisition attempts, usable information, selective offers and unresolved outcomes. Matched-cost and controlled ablation results expose both benefits and substantial failures. The defensible contribution is empirical measurement and evaluation methodology; claims of optimal control, guaranteed conditional risk or deployment superiority remain unestablished.
\section*{Acknowledgment}
OpenAI Codex assisted with code development, experimental checks, and manuscript drafting and revision.
\bibliographystyle{IEEEtran}
\bibliography{references}
\end{document}
'''.replace('ABSTRACT',abstract.strip())
(P/'manuscript.tex').write_text(body,encoding='utf8')
print('Main manuscript refocused; historical analyses retained in supplementary.tex')
