"""Adaptive Conformal Inference (Gibbs & Candes 2021) policy runner and helpers."""
from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.evaluation.marur import replay as replay_marur
from src.evaluation.pacer import replay_pacer

_ACI_RE = re.compile(r'^ACI_g([0-9]+(?:\.[0-9]+)?)$')


def aci_alpha_update(
    alpha_t: float,
    err_t: float,
    *,
    target_alpha: float = 0.10,
    gamma: float = 0.05,
) -> float:
    """Apply Gibbs & Candes (2021) ACI update: alpha_{t+1} = alpha_t + gamma * (alpha - err_t)."""
    return float(alpha_t + float(gamma) * (float(target_alpha) - float(err_t)))


def parse_aci_gamma(policy: str, default_gamma: float = 0.05) -> float | None:
    """Extract ACI step size gamma from a policy name such as 'ACI_g0.005' or 'ACI'."""
    if policy == 'ACI':
        return float(default_gamma)
    m = _ACI_RE.match(policy)
    if m:
        return float(m.group(1))
    return None


def aci_policy_name(gamma: float) -> str:
    """Format canonical policy name for a given ACI step size gamma."""
    return f'ACI_g{float(gamma):g}'


def replay_policy_unified(
    initial: pd.DataFrame,
    stream: pd.DataFrame,
    policy: str,
    budget: int,
    marur_cfg: dict[str, Any],
    pacer_cfg: dict[str, Any],
    *,
    scenario: str = 'Recorded',
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Dispatch any baseline, PACER, or parameterized ACI_g* policy over identical clock & cap contracts."""
    if policy == 'PACER':
        return replay_pacer(initial, stream, budget, pacer_cfg, scenario=scenario, seed=seed)
    gamma = parse_aci_gamma(policy)
    if gamma is not None:
        cfg = dict(marur_cfg, aci_step=gamma)
        return replay_marur(initial, stream, 'ACI', budget, cfg, scenario=scenario)
    return replay_marur(initial, stream, policy, budget, marur_cfg, scenario=scenario)
