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
    assert '+-50%' in comp['tost_rel_p_values'] and '+-25%' in comp['tost_rel_p_values']
    assert any('relative TOST +-50% inconclusive' in w for w in comp['warnings'])


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
    assert 'Relative TOST' in out
    assert 'WARNING' in out


def test_worked_heldout_c10_example_reproduces_headline_and_relative_results():
    """Verify worked CLI ledger reproduces paper held-out C=10 headline and relative TOST values."""
    worked_csv = ROOT / 'examples/worked_heldout_c10_ledger.csv'
    frame = pd.read_csv(worked_csv)
    rep = audit_ledger(frame, reference='Periodic', min_clusters=20, n_boot=2000, seed=42)
    pac = next(c for c in rep['comparisons'] if c['candidate'] == 'PACER')
    assert pac['clusters'] == 26
    assert np.isclose(pac['pooled_dpos_hi_pp'], -23.41, atol=0.01)
    assert np.isclose(pac['equal_cluster_dpos_hi_pp'], +0.37, atol=0.01)
    assert np.isclose(pac['equal_cluster_du_pp'], -3.29, atol=0.01)
    assert np.isclose(pac['mde80_du_pp'], 4.01, atol=0.01)
    assert pac['zero_ref_u_clusters'] == 4
    assert np.isclose(pac['pooled_rel_du_pct'], +46.85, atol=0.05)
    assert pac['tost_rel_p_values']['+-50%'] > 0.05
    assert pac['tost_rel_p_values']['+-25%'] > 0.05
