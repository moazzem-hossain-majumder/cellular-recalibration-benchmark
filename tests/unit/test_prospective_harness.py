import numpy as np
import pandas as pd
import pytest

from scripts.run_prospective_validation import (
    assess_registration_status,
    run_prospective_trip,
    verify_frozen_assets,
)
from src.features.builder import FEATURE_COLS


def _synthetic_trip(n_ticks: int = 24, *, missing_y_idx: tuple[int, ...] = (5, 23), no_lag_idx: tuple[int, ...] = (0,)) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    base_issue = 1700000000.0
    rows = []
    for i in range(n_ticks):
        issue = base_issue + i * 60.0
        row = {
            'id': f'SYN-{i:03d}',
            'date': '2026-12-01',
            'issue': issue,
            'ready': issue + 60.0,
            'y_lag1': np.nan if i in no_lag_idx else float(12.0 + rng.normal(0.0, 2.0)),
            'prev_duration_s': 45.0,
            'lag_age_s': 5.0,
            'has_lte': 1,
            'has_nr': int(i % 2 == 0),
            'group_id': 2 + int(i % 2 == 0),
            'rsrp': -88.0,
            'rsrq': -10.0,
            'sinr': 12.0,
            'ss_rsrp': -95.0 if i % 2 == 0 else np.nan,
            'ss_rsrq': -11.0 if i % 2 == 0 else np.nan,
            'ss_sinr': 9.0 if i % 2 == 0 else np.nan,
            'scenario_IS': 0,
            'scenario_OD': 1,
            'scenario_OW': 0,
            'y': np.nan if i in missing_y_idx else float(max(0.0, 14.0 + rng.normal(0.0, 4.0))),
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    assert set(FEATURE_COLS).issubset(df.columns)
    return df


def test_frozen_assets_verify_hash_and_schema():
    model, init_df, meta = verify_frozen_assets()
    assert len(init_df) == 10
    assert list(meta['features']) == list(FEATURE_COLS)
    assert hasattr(model, 'predict')


def test_registration_gate_rejects_incomplete_or_synthetic_runs():
    status, missing = assess_registration_status({})
    assert status == 'rehearsal_or_nonconfirmatory'
    assert 'network_operator' in missing
    full_meta = {
        'network_operator': 'TestOp',
        'location_and_route_strata': 'Route A',
        'device_and_modem': 'Pixel/X70',
        'approved_measurement_endpoint': 'https://example.invalid/iperf',
        'registered_protocol_url': 'https://osf.io/example',
        'requirements_validated_by_application_owner': True,
        'field_feature_mapping_verified': True,
        'is_synthetic_rehearsal': True,
    }
    status2, missing2 = assess_registration_status(full_meta)
    assert status2 == 'rehearsal_or_nonconfirmatory'
    assert 'is_synthetic_rehearsal_must_be_false' in missing2


def test_prospective_harness_enforces_causality_and_accounting():
    trip = _synthetic_trip()
    res = run_prospective_trip(trip, {'is_synthetic_rehearsal': True})
    assert res['validation_status'] == 'rehearsal_or_nonconfirmatory'
    assert res['scheduled_ticks'] == 24
    assert res['eligible_ticks'] == 23
    assert set(res['policies']) == {'Frozen', 'Periodic', 'MARUR'}
    assert res['policies']['Frozen']['new_query_attempts'] == 0
    assert res['policies']['MARUR']['new_query_attempts'] <= 10
    assert res['policies']['Periodic']['new_query_attempts'] <= 10
    # Ensure ineligible tick 0 produced abstention (lower == 0) in every policy
    for pol in ('Frozen', 'Periodic', 'MARUR'):
        act = res['ledgers'][pol]
        assert not bool(act.iloc[0]['eligible'])
        assert act.iloc[0]['lower'] == 0.0

    # Acausal horizon (ready < issue) must raise ValueError
    broken = trip.copy()
    broken.loc[2, 'ready'] = broken.loc[2, 'issue'] - 1.0
    with pytest.raises(ValueError, match='Acausal'):
        run_prospective_trip(broken)
