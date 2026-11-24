# MARUR implementation specification

Scope: src/evaluation/marur.py, replay. MARUR is an empirical heuristic. This specification describes the existing implementation, including behaviors that could be redesigned only in a new experiment.

The optional information-clock extension is isolated in `configs/marur_information_experiment.json` and `docs/MARUR_INFORMATION_EXPERIMENT_PROTOCOL.md`. Default replay semantics below remain unchanged. `freshness_clock='observed'` changes only the age-trigger origin; pattern-change state still follows completed responses. `minimum_attempt_spacing_minutes` defaults to zero; the experiment sets it to five for both clock variants. `feedback_unavailable_ids` is a keyword-only set consulted at response completion, independent of policy scheduling. `log_information_clocks` adds last-attempt, last-completed-response, last-observed-label, and last-admitted-score times. A missing-label conservative score advances admission but not successful-observation freshness. Extended windows retain additional paid responses, never additional free initial labels.

## Interface and state

The separate reviewer baseline grid additionally validates `Random` (a fixed externally supplied eligible-ID schedule) and `DecayingOGD` (Periodic requests, an initial ten-score quantile, and completed-response updates with scale max(1, maximum absolute initial residual), exponent 0.6). `calibration_scope='pooled'` changes only score selection; `pattern_gate=False` removes only the gate. Defaults remain unchanged. This extension does not transfer a published conformal guarantee; see `REVIEWER_BASELINE_PROTOCOL.md` for signed-score, sparse-feedback and offline-schedule limitations.

Inputs are an initial DataFrame, a stream DataFrame, policy name, legacy hybrid budget B, configuration, and scenario. Required columns are id, issue, ready, point, y, pattern and date. issue/ready are seconds; point and y are Mbps. The runner supplies a frozen predictor and unique IDs. Initial rows are sorted by issue/id and the first ten complete labels are used; their maximum ready must precede the stream. B must be at least ten. The new-query cap is C=B-10. Only the recorded eight policy names and two scenarios are validated configurations; arbitrary API strings are not a supported policy registry.

State: a FIFO deque of at most W=10 signed-score entries (score, pattern, ready, id); cumulative hybrid count initialized to ten; nominal alpha initially 0.1; zero or one pending request; eligible ordinal initially zero; admission count; latest completed-response timestamp and pattern. Initialization uses maximum initial ready and the pattern of the last issue-sorted initial row. These need not describe the same row under arbitrary asynchronous input; the supplied archive has the documented chronological initialization. Actions and completed-response records are retained for auditing.

Outputs: an action DataFrame for every scheduled row and a response DataFrame for every paid new request. Actions include commitment, eligibility, query decision, trigger label, cumulative counts, alpha, support and last feedback time. y is attached for evaluator accounting after action construction. A response records request identity/time, ready time, observed/censored status, score, admission and updated alpha. The routine does not refit a predictor or optimize any objective.

## Exact pseudocode

```text
sort initial and stream by (issue,id)
take the first ten initial labels; reject incomplete or not-yet-ready initialization
initialize FIFO with point-y scores, hybrid_count=10, alpha=0.1
initialize last_ready=max(initial.ready), last_pattern=last initial issue-sorted pattern

receive(now):
  for each pending request whose ready <= now:
    read its requested row only now
    censor iff scenario=QueryCensor20 and its eligible ordinal is divisible by five
    observed := y present and not censored
    score := point-y if observed, else point
    admit iff observed or policy != MARUR_DropMissing
    if admitted: append score/pattern/ready/id, evict oldest past W, increment updates
    if ACI:
      error := (requested commitment > y) if observed else (requested commitment > 0)
      alpha := alpha + 0.05*(0.1-error)
    always set last_ready=ready and last_pattern=current requested pattern
    append response and remove pending request

for each distinct issue time:
  receive(issue)
  for each row at this time in id order:
    eligible := point is present
    find current-pattern entries in FIFO
    patterned := policy starts MARUR and policy != MARUR_NoPattern
    use pattern entries iff patterned and count >= 9, otherwise entire FIFO
    q := signed finite-sample quantile at alpha for ACI, else 0.1
    alpha <= 0 or empty scores => q=+infinity; alpha >= 1 => q=-infinity
    otherwise rank=ceil((n+1)*(1-alpha)); rank>n => q=+infinity
    L := max(0,point-q) if eligible, else zero
    for ACI cap L at point at every alpha
    if patterned and pattern count < 3: set L=0
    if eligible:
      increment ordinal
      stale := issue-last_ready >= 3600 seconds
      changed := patterned and pattern != last_pattern
      periodic := (ordinal-1) divisible by 15
      wants := Early OR (Periodic/ACI/MARUR_Periodic AND periodic)
               OR (other MARUR variant AND (stale OR changed))
      if wants AND hybrid_count < B AND no pending request:
        charge one; save pending position/ready/ordinal/L
    append action using the current state
after final issue, receive remaining paid request at its ready time
attach evaluator outcomes to actions and return both ledgers
```

Rows at one timestamp share calibration state. Query reservation still follows ID order; at most one new request can be pending. No reception occurs between simultaneous rows. A completed response at the issue timestamp is available. After budget exhaustion an outstanding request can still mature. The final receipt can contain an admitted update never used by a later forecast.

## Semantics and limitations

MARUR_DropMissing changes only admission of failed scores. It still updates completed-response cooldown/pattern, so failure can postpone another same-pattern query by sixty minutes even with no newly observed evidence. MARUR_NoPattern removes pattern triggering, grouping and gating together. MARUR_Periodic retains grouping/gating and replaces query timing. Frozen never queries. Periodic/ACI use eligible positions 1,16,31,...; QueryCensor20 masks 5,10,15,... and therefore aliases with that schedule. It does not mean twenty percent of queries fail.

The trigger field is a diagnostic priority label (pattern before age before schedule), not necessarily the unique causal reason for a request. In MARUR_Periodic, for example, a scheduled request can carry a pattern label. Analyze the actual policy and ordinal when attributing triggers.

The bound p-y<=p requires nonnegative latent y. The FIFO quantile at alpha=0.1 and n=9 or 10 is the maximum score. Selective querying, dependent observations and shifting networks invalidate importing ordinary exchangeable conformal guarantees. The positive-offer gate imposes no conditional-risk guarantee. The modified ACI rate cap and partial feedback also preclude inheriting the original full-feedback guarantee. Utility and risk are evaluated after the decisions; they are not optimized by replay.

## Cost and complexity

Historical successful labels are separate from new attempts. A missing response consumes one new attempt. Admissions include conservative synthetic scores; effective updates count admissions available to at least one subsequent scheduled row. Daily effective counts are cumulative and must not be added across dates. Ordinary lag measurements, audit instrumentation, bandwidth, energy and initial failed acquisitions are excluded from charged query cost.

For T stream rows and W window entries, input sorting costs O(T log T). Filtering the window is O(W) per row and the implementation sorts selected scores, O(W log W); total O(T log T + T W log W), plus initialization sorting. W=10 is fixed. Pending handling is O(1) because only one request is outstanding. Controller state alone is O(W), but the actual pandas replay copies/sorts the full input and retains all actions/responses, so memory is O(T+Q+W), not O(W) end to end. The runner additionally concatenates results across configurations. This is retrospective replay software, not a measured real-time implementation.
