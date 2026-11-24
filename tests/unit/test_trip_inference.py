import json
import pandas as pd
import numpy as np
import pytest
from scripts.publication_tables import ROOT
from scripts.audit_trip_level_inference import (
    physical_campaign_key,
    physical_campaign_name,
    t_quantile_975,
)


def test_cluster_mapping_collapses_shared_campaigns():
    assert physical_campaign_key('E1', '2023-05-27') == physical_campaign_key('E3', '2023-05-27')
    assert physical_campaign_key('AT&T', '2023-08-07') == physical_campaign_key('Verizon', '2023-08-07')
    assert physical_campaign_name('T-Mobile') == 'US_NUWiNS_Drive3'
    assert physical_campaign_name('Ireland') == 'Ireland_UCC_Drive'


def test_student_t_critical_values_monotone_and_bounded():
    prev = float('inf')
    for df in range(1, 21):
        q = t_quantile_975(df)
        assert 1.95 < q < prev
        prev = q
    assert t_quantile_975(30) == pytest.approx(1.95996398)
    assert np.isnan(t_quantile_975(0))


def test_saved_trip_level_inference_matches_authoritative_date_ledgers():
    payload = json.loads((ROOT / 'results/diagnostics/trip_level_inference.json').read_text(encoding='utf8'))
    df = pd.read_csv(ROOT / 'results/diagnostics/trip_level_inference.csv')
    dates = pd.read_csv(ROOT / 'results/marur_audit/matched_cost_dates.csv')

    assert payload['inventory']['geographic_campaigns'] == 3
    assert payload['inventory']['unique_physical_campaign_dates'] == 16
    assert payload['inventory']['ireland_test_traces'] == 11

    combined = df[(df['scope'] == 'Combined_CampaignDates') & (df['model'] == 'HistGBM') & (df['scenario'] == 'Recorded') & (df['new_query_cap'] == 10) & (df['baseline'] == 'Periodic')]
    assert len(combined) == 1
    row = combined.iloc[0]
    assert int(row['clusters']) == 16
    assert row['t_du_lo'] < 0.0 < row['t_du_hi']
    assert row['boot_du_lo'] < 0.0 < row['boot_du_hi']

    # Recompute exact E1 pooled and equal-date dU from saved matched_cost_dates
    e1 = dates[(dates['cohort'] == 'E1') & (dates['model'] == 'HistGBM') & (dates['scenario'] == 'Recorded') & (dates['new_query_cap'] == 10)]
    p = e1.pivot(index='date', columns='policy')
    expected_pool_du = float(p['delivered_sum']['MARUR'].sum() / p['observed_sum']['MARUR'].sum() - p['delivered_sum']['Periodic'].sum() / p['observed_sum']['Periodic'].sum())
    expected_eq_du = float((p['u']['MARUR'] - p['u']['Periodic']).mean())

    e1_row = df[(df['scope'] == 'E1') & (df['model'] == 'HistGBM') & (df['scenario'] == 'Recorded') & (df['new_query_cap'] == 10) & (df['baseline'] == 'Periodic')].iloc[0]
    np.testing.assert_allclose(e1_row['pool_du'], expected_pool_du, atol=1e-12)
    np.testing.assert_allclose(e1_row['eq_du_mean'], expected_eq_du, atol=1e-12)
    assert int(e1_row['cand_query_days']) == 1  # All 10 queries exhausted on Day 1
