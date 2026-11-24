"""Horizon-Paced Selective-Offer Conformal Control (PACER).

Targets positive-conditional violation risk directly while eliminating Day-1
budget exhaustion, zero-offer gradient dilution, and missing-score quantile
poisoning under delayed, incomplete cellular feedback.
"""
from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np
import pandas as pd


def smooth_selective_quantile(
    scores: np.ndarray,
    level_a: float,
    *,
    a_veto: float = 0.15,
    ext_scale: float = 2.0,
) -> float:
    """Compute monotone smooth threshold from finite observed residuals.

    Returns +inf when level_a <= -a_veto (abstention regime), interpolates the
    empirical conformal quantile cleanly for level_a in [1/(n+1), 1], and extends
    smoothly above max(scores) using robust observed dispersion for
    level_a in (-a_veto, 1/(n+1)).
    """
    if level_a <= -a_veto:
        return float('inf')
    arr = np.sort(np.asarray(scores, dtype=float))
    n = len(arr)
    if n == 0 or not np.isfinite(arr).all():
        return float('inf')
    if level_a >= 1.0:
        return float(arr[0])

    crit_min = 1.0 / (n + 1.0)
    if level_a >= crit_min:
        # Rank on 1..n matching split-conformal indexing r = (n+1)*(1-a)
        rank = (n + 1.0) * (1.0 - level_a)
        rank = min(float(n), max(1.0, rank))
        lo_idx = int(np.floor(rank)) - 1
        hi_idx = min(n - 1, lo_idx + 1)
        frac = rank - np.floor(rank)
        return float((1.0 - frac) * arr[lo_idx] + frac * arr[hi_idx])

    # Smooth monotone margin extension above max(scores) without inf jump
    s_max = float(arr[-1])
    med = float(np.median(arr))
    q90 = float(np.quantile(arr, 0.90))
    disp = max(1.0, s_max - med, q90 - med, float(np.quantile(np.abs(arr), 0.90)))
    weight = (crit_min - level_a) / (crit_min + a_veto)
    return float(s_max + ext_scale * weight * disp)


def theoretical_excess_bound(
    *,
    alpha: float,
    gamma: float,
    a_veto: float,
    n_blocks: int,
    n_rows: int,
    max_block_delay: int = 1,
) -> float:
    """Return proved upper bound on E[(M/T)*(R_+^upper - alpha)] (Theorem 1)."""
    if n_blocks <= 0 or n_rows <= 0:
        return float('inf')
    w_max = int(np.ceil(n_rows / n_blocks))
    return float(
        (w_max / n_rows) * ((alpha + a_veto + gamma * (1.0 - alpha) * (1.0 + max_block_delay)) / gamma)
    )


def replay_pacer(
    initial: pd.DataFrame,
    stream: pd.DataFrame,
    budget: int,
    config: dict[str, Any],
    scenario: str = 'Recorded',
    *,
    seed: int = 42,
    feedback_unavailable_ids: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run PACER under the identical causal ledger contract as replay()."""
    first = initial.sort_values(['issue', 'id']).head(config['initial_labels'])
    df = stream.sort_values(['issue', 'id']).reset_index(drop=True)
    if len(first) != config['initial_labels'] or first.y.isna().any():
        raise ValueError('Initial labels must be complete')
    if first.ready.max() > df.issue.min():
        raise ValueError('Initial labels must precede target stream')
    n_init = len(first)
    if budget < n_init:
        raise ValueError('Budget must cover initial labels')
    new_cap = int(budget - n_init)

    alpha = float(config['alpha'])
    gamma = float(config.get('pacer_gamma', 0.05))
    a_veto = float(config.get('pacer_veto', 0.15))
    ext_scale = float(config.get('pacer_ext_scale', 2.0))
    obs_win_len = int(config.get('pacer_obs_window', 20))

    obs_window: deque[float] = deque(
        (float(r.point - r.y) for r in first.itertuples()),
        maxlen=obs_win_len,
    )
    level_a = alpha
    n_rows = len(df)
    n_blocks = min(new_cap, n_rows) if new_cap > 0 else 0
    if n_blocks > 0:
        blocks = [blk.tolist() for blk in np.array_split(np.arange(n_rows), n_blocks)]
        rng = np.random.default_rng(int(seed))
        probe_positions = {int(rng.choice(blk)) for blk in blocks}
        block_of_pos = np.empty(n_rows, dtype=int)
        for b_idx, blk in enumerate(blocks):
            block_of_pos[blk] = b_idx
        block_starts = {blk[0]: b_idx for b_idx, blk in enumerate(blocks)}
    else:
        probe_positions = set()
        block_of_pos = np.zeros(n_rows, dtype=int)
        block_starts = {}

    feedback_unavailable_ids = set(feedback_unavailable_ids or ())
    attempts = n_init
    updates = 0
    last_ready = float(first.ready.max())
    pending: list[dict[str, Any]] = []
    ready_buffer: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    ordinal = 0

    # Frozen block-level threshold q_block, updated cleanly at block boundaries
    current_q = smooth_selective_quantile(
        np.asarray(obs_window, dtype=float), level_a, a_veto=a_veto, ext_scale=ext_scale
    )

    def poll_completions(now: float) -> None:
        nonlocal last_ready
        due = [p for p in pending if p['ready'] <= now]
        for req in due:
            row = df.iloc[req['position']]
            censored = (
                scenario == 'QueryCensor20' and req['ordinal'] % 5 == 0
            ) or (row.id in feedback_unavailable_ids)
            y_val = np.nan if censored else row.y
            observed = bool(pd.notna(y_val))
            # Selective upper failure indicator on positive offer:
            # 1{L > y} when observed, conservatively 1 when missing.
            cons_err = float(req['lower'] > y_val) if observed else 1.0
            score = float(row.point - y_val) if observed else float(row.point)
            ready_buffer.append(
                {
                    'id': row.id,
                    'query_time': row.issue,
                    'ready': row.ready,
                    'observed': observed,
                    'censored': censored,
                    'score': score,
                    'positive_offer': req['lower'] > 0.0,
                    'cons_err': cons_err,
                    'block_idx': req['block_idx'],
                }
            )
            last_ready = float(row.ready)
            pending.remove(req)

    def apply_block_updates() -> None:
        nonlocal level_a, updates, current_q
        if not ready_buffer:
            return
        for item in ready_buffer:
            if item['observed']:
                obs_window.append(item['score'])
                updates += 1
            if item['positive_offer']:
                level_a = min(1.0, level_a + gamma * (alpha - item['cons_err']))
            responses.append(
                {
                    'id': item['id'],
                    'query_time': item['query_time'],
                    'ready': item['ready'],
                    'observed': item['observed'],
                    'censored': item['censored'],
                    'score': item['score'],
                    'admitted': item['observed'],
                    'alpha_after': level_a,
                }
            )
        ready_buffer.clear()
        current_q = smooth_selective_quantile(
            np.asarray(obs_window, dtype=float), level_a, a_veto=a_veto, ext_scale=ext_scale
        )

    for pos, row in df.iterrows():
        poll_completions(float(row.issue))
        if pos in block_starts:
            apply_block_updates()

        eligible = bool(pd.notna(row.point))
        if eligible:
            ordinal += 1
            raw_bound = 0.0 if np.isinf(current_q) else float(row.point - current_q)
            lower = float(max(0.0, min(float(row.point), raw_bound)))
            reason = 'positive' if lower > 0.0 else ('abstention_veto' if np.isinf(current_q) else 'nonpositive_bound')
        else:
            lower = 0.0
            reason = 'no_lag'

        request = False
        trigger = 'none'
        if (
            eligible
            and (pos in probe_positions)
            and (attempts < budget)
        ):
            request = True
            trigger = 'paced_block'
            attempts += 1
            pending.append(
                {
                    'position': pos,
                    'ready': float(row.ready),
                    'ordinal': ordinal,
                    'lower': lower,
                    'block_idx': int(block_of_pos[pos]),
                }
            )

        actions.append(
            {
                'id': row.id,
                'date': row.date,
                'issue': row.issue,
                'ready': row.ready,
                'pattern': row.pattern,
                'point': row.point,
                'eligible': eligible,
                'lower': lower,
                'reason': reason,
                'query': request,
                'trigger': trigger,
                'attempts': attempts,
                'updates': updates,
                'alpha': level_a,
                'window_size': len(obs_window),
                'pattern_support': len(obs_window),
                'last_feedback': last_ready,
                'offset': current_q,
            }
        )

    if pending:
        poll_completions(float(max(p['ready'] for p in pending)))
    if ready_buffer:
        apply_block_updates()

    ledger = pd.DataFrame(actions)
    ledger['y'] = df['y'].to_numpy()
    resp_cols = ['id', 'query_time', 'ready', 'observed', 'censored', 'score', 'admitted', 'alpha_after']
    return ledger, pd.DataFrame(responses, columns=resp_cols)
