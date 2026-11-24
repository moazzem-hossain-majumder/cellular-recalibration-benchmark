import json
from pathlib import Path
import numpy as np
import pandas as pd

from src.evaluation.marur import replay as replay_marur
from src.evaluation.pacer import (
    replay_pacer,
    smooth_selective_quantile,
    theoretical_excess_bound,
)

ROOT = Path(__file__).resolve().parents[2]


def _make_initial(n: int = 10, scale: float = 2.0) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                'id': f'CAL-{i}',
                'date': '2026-01-01',
                'issue': float(i * 60),
                'ready': float((i + 1) * 60),
                'pattern': 3,
                'point': 10.0,
                'y': 10.0 - (i % 4) * 0.5 * scale,
            }
            for i in range(n)
        ]
    )


def _make_stream(n: int, *, point_fn, y_fn, lag_valid_fn=None, pattern_fn=None) -> pd.DataFrame:
    rows = []
    for t in range(n):
        issue = float(1000 + t * 60)
        day_idx = t // 30 + 2
        pt = point_fn(t) if (lag_valid_fn is None or lag_valid_fn(t)) else np.nan
        pat = int(pattern_fn(t)) if pattern_fn is not None else 3
        rows.append(
            {
                'id': f'T-{t:04d}',
                'date': f'2026-01-{day_idx:02d}',
                'issue': issue,
                'ready': issue + 60.0,
                'pattern': pat,
                'point': pt,
                'y': float(y_fn(t)),
            }
        )
    return pd.DataFrame(rows)


def test_smooth_quantile_continuity_and_veto():
    scores = np.array([-2.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0])
    assert smooth_selective_quantile(scores, 1.0) == -2.0
    q_edge = smooth_selective_quantile(scores, 1.0 / 11.0)
    assert q_edge == 10.0
    q_below = smooth_selective_quantile(scores, 0.0)
    assert np.isfinite(q_below) and q_below > q_edge
    assert np.isinf(smooth_selective_quantile(scores, -0.15))
    assert np.isinf(smooth_selective_quantile(scores, -0.50))


def test_pacer_theorem1_selective_excess_bound_under_adversarial_late_shift():
    """Verify Theorem 1 empirically across random probing seeds under severe post-Day1 shift."""
    cfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))
    init = _make_initial(scale=0.5)  # Tight initial residuals (~0..1.5 Mbps)
    # Regime: first 80 ticks mild with multi-pattern churn (LTE/5G alternation),
    # exhausting front-loaded budgets; then at t>=80 actual throughput drops from 18 to 8 (+12 Mbps overprediction).
    stream = _make_stream(
        240,
        point_fn=lambda t: 20.0 if t % 2 == 0 else 2.0,
        y_fn=lambda t: 18.0 if t < 80 else 8.0,
        pattern_fn=lambda t: (t % 2) + 1 if t < 80 else 1,
    )
    init = init.copy()
    init['pattern'] = [1 + (i % 2) for i in range(len(init))]
    cap_new = 40
    bound = theoretical_excess_bound(
        alpha=cfg['alpha'],
        gamma=cfg['pacer_gamma'],
        a_veto=cfg['pacer_veto'],
        n_blocks=cap_new,
        n_rows=len(stream),
    )

    excess_vals = []
    for seed in range(40):
        act, _ = replay_pacer(init, stream, 10 + cap_new, cfg, scenario='Recorded', seed=seed)
        assert int(act['query'].sum()) <= cap_new
        pos = act['lower'] > 0
        # Weighted selective violation excess: sum(I_t * (e_t - alpha)) / T
        err = np.where(act['y'].isna(), 1.0, (act['lower'] > act['y']).astype(float))
        excess = float(np.mean(pos.astype(float) * (err - cfg['alpha'])))
        excess_vals.append(excess)

    mean_excess = float(np.mean(excess_vals))
    assert mean_excess <= bound + 1e-12

    # Contrast with MARUR & Early exhausting queries on Day 1 under Theorem 2 (blind suffix)
    marur_cfg = json.loads((ROOT / 'configs/marur.json').read_text(encoding='utf8'))
    for front_policy in ('Early', 'MARUR'):
        f_act, _ = replay_marur(init, stream, front_policy, 10 + cap_new, marur_cfg, scenario='Recorded')
        assert int(f_act.loc[f_act['issue'] >= 1000 + 80 * 60, 'query'].sum()) == 0
        f_late = f_act.iloc[80:]
        f_pos_late = f_late[f_late['lower'] > 0]
        assert len(f_pos_late) > 0
        assert float((f_pos_late['lower'] > f_pos_late['y']).mean()) > 0.90


def test_pacer_avoids_zero_offer_abstention_dilution_trap():
    """Verify PACER prevents zero-offer gradient dilution that breaks standard ACI."""
    cfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))
    marur_cfg = json.loads((ROOT / 'configs/marur.json').read_text(encoding='utf8'))
    init = _make_initial(scale=0.5)
    # Periodic ticks (t % 15 == 0) have low forecast (point=1.0 -> L=0 abstained),
    # while off-schedule ticks have optimistic overprediction (point=25.0, y=10.0).
    stream = _make_stream(
        300,
        point_fn=lambda t: 1.0 if t % 3 == 0 else 25.0,
        y_fn=lambda t: 10.0,
    )
    p_act, _ = replay_pacer(init, stream, 50, cfg, scenario='Recorded', seed=42)
    a_act, _ = replay_marur(init, stream, 'ACI', 50, marur_cfg, scenario='Recorded')

    p_pos = p_act[p_act['lower'] > 0]
    a_pos = a_act[a_act['lower'] > 0]
    p_rplus = float((p_pos['lower'] > p_pos['y']).mean()) if len(p_pos) else 0.0
    a_rplus = float((a_pos['lower'] > a_pos['y']).mean()) if len(a_pos) else 0.0
    # ACI probes hit zero-offer ticks -> error=0 -> alpha inflates toward 1.0 -> severe R+ breach!
    assert a_rplus > 0.50
    assert p_rplus <= 0.15


def test_pacer_does_not_poison_quantile_window_on_missing_responses():
    cfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))
    init = _make_initial(scale=0.5)
    stream = _make_stream(120, point_fn=lambda t: 20.0, y_fn=lambda t: 18.0)
    # Censor 50% of scheduled rows deterministically
    hidden = {f'T-{t:04d}' for t in range(0, 120, 2)}
    act, resp = replay_pacer(init, stream, 20, cfg, feedback_unavailable_ids=hidden, seed=42)
    assert len(resp) > 0
    unobs = resp[~resp['observed']]
    if len(unobs):
        assert (unobs['admitted'] == False).all()
    assert (resp['admitted'] == resp['observed']).all()
    assert int(act['updates'].iloc[-1]) <= int(resp['observed'].sum())

    # Total unavailability must yield zero window admissions while still decrementing level_a conservatively on positive offers
    all_hidden = {f'T-{t:04d}' for t in range(120)}
    act_hide, resp_hide = replay_pacer(init, stream, 20, cfg, feedback_unavailable_ids=all_hidden, seed=42)
    assert int(act_hide['updates'].max()) == 0
    assert not resp_hide['admitted'].any()
    assert act_hide['alpha'].iloc[-1] < act_hide['alpha'].iloc[0]

    # Must remain deterministic on fixed seed and respect causality (query_time < ready)
    act2, resp2 = replay_pacer(init, stream, 20, cfg, feedback_unavailable_ids=hidden, seed=42)
    pd.testing.assert_frame_equal(act, act2)
    pd.testing.assert_frame_equal(resp, resp2)
    if len(resp):
        assert (resp['query_time'] < resp['ready']).all()


def test_pacer_theorem1_holds_with_5min_delay_and_missingness():
    """Verify Theorem 1 with 5-minute maturation delay (D=1 block) and 20% censoring."""
    cfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))
    init = _make_initial(scale=0.5)
    stream = _make_stream(400, point_fn=lambda t: 22.0, y_fn=lambda t: 18.0 if t < 120 else 9.0)
    stream['ready'] = stream['issue'] + 300.0  # 5-minute maturation (5 ticks; block size = 10 ticks -> D <= 1)
    cap_new = 40
    bound = theoretical_excess_bound(
        alpha=cfg['alpha'],
        gamma=cfg['pacer_gamma'],
        a_veto=cfg['pacer_veto'],
        n_blocks=cap_new,
        n_rows=len(stream),
        max_block_delay=1,
    )
    hidden = {f'T-{t:04d}' for t in range(0, 400, 5)}
    excess_vals = []
    for seed in range(40):
        act, _ = replay_pacer(init, stream, 10 + cap_new, cfg, feedback_unavailable_ids=hidden, seed=seed)
        pos = act['lower'] > 0
        err = np.where(act['y'].isna(), 1.0, (act['lower'] > act['y']).astype(float))
        excess_vals.append(float(np.mean(pos.astype(float) * (err - cfg['alpha']))))
    assert float(np.mean(excess_vals)) <= bound + 1e-12
