import pandas as pd
from scripts.select_clock_policy import select
from scripts.generate_experiment_manifest import digest


def test_selection_counts_missing_positives_and_resolves_ties():
    rows = pd.DataFrame([
        (0, 10, 0, 0, 0.0, 0),
        (1, 10, 1, 1, 0.9, 9),
        (2, 10, 0, 1, 0.5, 10),
        (3, 10, 0, 1, 0.5, 9),
        (4, 10, 0, 1, 0.5, 9),
    ], columns=['order', 'issued', 'violations', 'unresolved', 'u', 'k'])
    assert select(rows)['order'] == 3
    assert select(rows.iloc[:2])['order'] == 0


def test_manifest_handles_checkout_line_endings(tmp_path):
    for extension, same in [('md', True), ('pdf', False)]:
        file = tmp_path / f'example.{extension}'
        file.write_bytes(b'a\nb')
        original = digest(file)
        file.write_bytes(b'a\r\nb')
        assert (digest(file) == original) == same


def test_single_factor_ablation_and_pareto_sieve():
    from scripts.run_sensitivity_exploratory import run_single_factor_ablation, run_risk_utility_and_fairness_audit

    abl = run_single_factor_ablation().set_index('factor')
    assert abl.loc['R_vs_Rplus_SLA', 'n_affected'] == 228
    assert abl.loc['R_vs_Rplus_Rank', 'n_affected'] == 135
    assert abl.loc['Cap_vs_Qnew_All', 'n_affected'] == 124
    assert abl.loc['Missing_Bounds_Overlap', 'n_affected'] == 135
    assert abl.loc['Pooling_Weight_Rplus', 'n_affected'] == 47
    assert abl.loc['Campaign_Clustering_Donner', 'n_affected'] == 2

    pareto, fair = run_risk_utility_and_fairness_audit()
    sieve = pareto[pareto['source'] == 'FairnessSieve_100Pairs'].iloc[0]
    assert 'total=100|win=15|q=69|qwin=8|qa=28|qawin=3' == sieve['policy']
    assert len(fair) == 8
