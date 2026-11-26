from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from scripts.audit_policy import main as cli_main
from src.audit.recalibration_audit import audit_ledger

ROOT = Path(__file__).resolve().parents[2]


def _cluster_summary_fixture(*, unmatched_queries: bool = False, zero_offers: bool = False) -> pd.DataFrame:
    rows = []
    for idx in range(6):
        cid = f'D-{idx+1:02d}'
        rows.append({
            'policy': 'Periodic',
            'cluster_id': cid,
            'eligible': 100,
            'offers': 40,
            'violations': 10,
            'missing_outcomes': 2,
            'queries_charged': 10,
            'observed_sum': 1000.0,
            'delivered_sum': 20.0 + idx * 0.5,
        })
        rows.append({
            'policy': 'MARUR',
            'cluster_id': cid,
            'eligible': 100,
            'offers': 0 if zero_offers else 30,
            'violations': 0 if zero_offers else 9,
            'missing_outcomes': 0 if zero_offers else 3,
            'queries_charged': 25 if unmatched_queries else 10,
            'observed_sum': 1000.0,
            'delivered_sum': 0.0 if zero_offers else 22.0 + idx * (8.0 if idx % 2 == 0 else -5.0),
        })
    return pd.DataFrame(rows)


def test_audit_identity_bounds_warnings_and_tost():
    df = _cluster_summary_fixture(unmatched_queries=True, zero_offers=False)
    rep = audit_ledger(df, reference='Periodic', min_clusters=10, n_boot=400, seed=7)
    mar = rep['policies']['MARUR']
    assert mar['r_identity_max_abs_err'] < 1e-12
    assert np.isclose(mar['offer_frequency_A'], 0.30)
    assert np.isclose(mar['conditional_risk_lo'], 0.30)
    assert np.isclose(mar['conditional_risk_hi'], 0.40)
    assert any('fewer than 10 clusters' in w for w in mar['warnings'])

    comp = rep['comparisons'][0]
    assert not comp['queries_matched']
    assert any('queries unmatched across policies' in w for w in comp['warnings'])
    assert any('fewer than 10 clusters' in w for w in comp['warnings'])
    assert comp['mde80_du_pp'] > 0
    assert '+-1pp' in comp['tost_p_values'] and '+-2pp' in comp['tost_p_values']
    assert '+-50%' in comp['tost_eq_rel_p_values'] and '+-25%' in comp['tost_eq_rel_p_values']
    assert '+-50%' in comp['tost_pool_rel_p_values'] and '+-25%' in comp['tost_pool_rel_p_values']
    assert any('equal-cluster relative TOST +-50% inconclusive' in w for w in comp['warnings'])
    assert any('pooled-ratio TOST +-50% inconclusive' in w for w in comp['warnings'])


def test_audit_zero_offers_warning():
    df = _cluster_summary_fixture(zero_offers=True)
    rep = audit_ledger(df, reference='Periodic', min_clusters=4, n_boot=200)
    assert 'zero positive offers' in rep['policies']['MARUR']['warnings']
    assert 'zero positive offers' in rep['comparisons'][0]['warnings']
    assert np.isnan(rep['policies']['MARUR']['conditional_risk_hi'])


def test_audit_accepts_tick_level_ledger_and_cli(tmp_path, capsys):
    rows = []
    for c_idx in range(4):
        for pol in ('Periodic', 'MARUR'):
            for t in range(25):
                is_elig = t > 0
                y = np.nan if (t == 24) else 10.0 + c_idx
                lower = 0.0 if (not is_elig or t % 2 == 1) else ((12.0 if pol == 'MARUR' else 9.0) if t % 4 == 0 else (7.0 + c_idx * 0.5))
                rows.append({
                    'policy': pol,
                    'cluster_id': f'Day-{c_idx}',
                    'eligible': is_elig,
                    'lower': lower,
                    'y': y,
                    'query': int(t % 5 == 0),
                })
    csv_path = tmp_path / 'tick_ledger.csv'
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    rc = cli_main([str(csv_path), '--reference', 'Periodic', '--min-clusters', '10', '--n-boot', '200'])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'Empirical Recalibration Accounting Audit' in out
    assert 'Equal-cluster Relative TOST' in out
    assert 'Pooled-ratio Relative TOST' in out
    assert 'WARNING' in out


def test_relative_tost_estimands_use_matched_weighting():
    """Verify equal-cluster TOST tests eq_du against eq_ref_u while pooled-ratio TOST uses pooled totals."""
    from scipy import stats
    rows = []
    # 5 small clusters: Periodic U = 10%, Candidate U = 9% (eq diff = -1.0 pp);
    # 1 giant cluster (1000x weight): Periodic U = 0.2%, Candidate U = 0.8% (pool ratio strongly positive!)
    for idx in range(6):
        cid = f'C-{idx+1:02d}'
        obs = 100000.0 if idx == 5 else 100.0
        del_r = 200.0 if idx == 5 else 10.0
        del_c = 800.0 if idx == 5 else 9.0
        rows.append({'policy': 'Periodic', 'cluster_id': cid, 'eligible': 100, 'offers': 40, 'violations': 4, 'missing_outcomes': 0, 'queries_charged': 10, 'observed_sum': obs, 'delivered_sum': del_r})
        rows.append({'policy': 'PACER', 'cluster_id': cid, 'eligible': 100, 'offers': 40, 'violations': 4, 'missing_outcomes': 0, 'queries_charged': 10, 'observed_sum': obs, 'delivered_sum': del_c})
    rep = audit_ledger(pd.DataFrame(rows), reference='Periodic', min_clusters=4, n_boot=500, seed=7)
    comp = rep['comparisons'][0]
    # Equal-cluster Periodic U ~ 8.37% -> 50% margin = 4.18% >> 0.5 * ref_pooled (~0.12%), opposite sign to pooled!
    assert comp['ref_equal_u_pp'] > 8.0 and comp['ref_pooled_u_pp'] < 0.3
    assert comp['equal_cluster_du_pp'] < 0.0 and comp['pooled_rel_du_pct'] > 200.0
    expected_margin_eq = 0.50 * comp['ref_equal_u_pp']
    expected_p_eq = max(
        float(1.0 - stats.t.cdf((comp['equal_cluster_du_pp'] + expected_margin_eq) / comp['se_du_pp'], df=5)),
        float(stats.t.cdf((comp['equal_cluster_du_pp'] - expected_margin_eq) / comp['se_du_pp'], df=5)),
    )
    assert np.isclose(comp['tost_eq_rel_p_values']['+-50%'], expected_p_eq, rtol=0, atol=1e-12)
    assert not comp['pooled_rel_equiv']['+-50%']


def test_worked_heldout_c10_example_reproduces_headline_and_relative_results():
    """Verify worked CLI ledger reproduces paper held-out C=10 headline and separated relative TOST values."""
    worked_csv = ROOT / 'examples/worked_heldout_c10_ledger.csv'
    frame = pd.read_csv(worked_csv)
    rep = audit_ledger(frame, reference='Periodic', min_clusters=20, n_boot=2000, seed=42)
    pac = next(c for c in rep['comparisons'] if c['candidate'] == 'PACER')
    assert pac['clusters'] == 26
    assert np.isclose(pac['pooled_dpos_hi_pp'], -23.41, atol=0.01)
    assert np.isclose(pac['equal_cluster_dpos_hi_pp'], +0.37, atol=0.01)
    assert np.isclose(pac['ref_equal_u_pp'], 6.32, atol=0.01)
    assert np.isclose(pac['ref_pooled_u_pp'], 1.01, atol=0.01)
    assert np.isclose(pac['equal_cluster_du_pp'], -3.29, atol=0.01)
    assert np.isclose(pac['mde80_du_pp'], 4.01, atol=0.01)
    assert pac['zero_ref_u_clusters'] == 4 and pac['undef_u_clusters'] == 0
    assert np.isclose(pac['pooled_rel_du_pct'], +46.85, atol=0.05)
    assert pac['tost_eq_rel_p_values']['+-50%'] > 0.05
    assert pac['tost_eq_rel_p_values']['+-25%'] > 0.05
    assert not pac['pooled_rel_equiv']['+-50%']
