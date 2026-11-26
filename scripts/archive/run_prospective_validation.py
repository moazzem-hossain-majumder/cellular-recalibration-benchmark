"""Frozen execution harness for prospective independent cellular trips.

Loads the SHA-256-verified frozen Rome HistGBM predictor and fixed initial
observations, checks readiness prerequisites, and runs MARUR (W=10, C_new=10)
against the prespecified Periodic (P=15) baseline and zero-cost Frozen control
without post-hoc parameter tuning. Refuses to label any run 'confirmatory'
unless genuine external registration prerequisites in readiness/campaign metadata
are satisfied.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.clock_frontier import metrics
from scripts.run_marur import aggregate
from src.evaluation.marur import replay
from src.features.builder import FEATURE_COLS

PLAN_DIR = ROOT / 'results/prospective_planning'
DEFAULT_CONFIG = {
    'alpha': 0.1,
    'initial_labels': 10,
    'window': 10,
    'period_ticks': 15,
    'max_age_minutes': 60,
    'minimum_pattern_support': 3,
    'aci_step': 0.05,
    'new_query_cap': 10,
    'clock_seconds': 60,
    'horizon_seconds': 60,
}
REQUIRED_CAMPAIGN_FIELDS = (
    'network_operator',
    'location_and_route_strata',
    'device_and_modem',
    'approved_measurement_endpoint',
    'registered_protocol_url',
)


def verify_frozen_assets(plan_dir: Path = PLAN_DIR) -> tuple[object, pd.DataFrame, dict]:
    """Load frozen model and initialization records after verifying SHA-256 and feature order."""
    freeze_meta = json.loads((plan_dir / 'model_freeze.json').read_text(encoding='utf8'))
    model_path = plan_dir / 'frozen_rome_histgbm.joblib'
    actual_sha = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if actual_sha != freeze_meta['model_sha256']:
        raise ValueError(f"Frozen model SHA-256 mismatch: {actual_sha} != {freeze_meta['model_sha256']}")
    if list(freeze_meta['features']) != list(FEATURE_COLS):
        raise ValueError('Frozen model feature list does not match FEATURE_COLS')
    model = joblib.load(model_path)
    init_df = pd.read_csv(plan_dir / 'proposed_initial_observations.csv', float_precision='round_trip')
    if len(init_df) != 10 or init_df['y'].isna().any() or init_df['point'].isna().any():
        raise ValueError('Frozen initialization requires 10 complete pre-test observations')
    return model, init_df, freeze_meta


def assess_registration_status(campaign_meta: dict) -> tuple[str, list[str]]:
    """Return ('confirmatory', []) only when every field prerequisite is documented and true."""
    missing = [k for k in REQUIRED_CAMPAIGN_FIELDS if not campaign_meta.get(k)]
    if not campaign_meta.get('requirements_validated_by_application_owner', False):
        missing.append('requirements_validated_by_application_owner')
    if not campaign_meta.get('field_feature_mapping_verified', False):
        missing.append('field_feature_mapping_verified')
    if campaign_meta.get('is_synthetic_rehearsal', False):
        missing.append('is_synthetic_rehearsal_must_be_false')
    status = 'confirmatory' if not missing else 'rehearsal_or_nonconfirmatory'
    return status, missing


def run_prospective_trip(
    stream_df: pd.DataFrame,
    campaign_meta: dict | None = None,
    *,
    plan_dir: Path = PLAN_DIR,
    new_query_cap: int = DEFAULT_CONFIG['new_query_cap'],
) -> dict:
    """Execute locked MARUR vs Periodic vs Frozen on one chronologically ordered trip frame.

    Parameters
    ----------
    stream_df:
        DataFrame with at least columns ['id', 'date', 'issue', 'ready', 'y'] plus
        FEATURE_COLS for model prediction (where unavailable lag sets point=NaN and is ineligible).
    campaign_meta:
        Optional trip/registration metadata dict for preregistration checks.
    """
    campaign_meta = dict(campaign_meta or {})
    status, missing_prereqs = assess_registration_status(campaign_meta)
    model, init_df, freeze_meta = verify_frozen_assets(plan_dir)

    df = stream_df.copy().sort_values(['issue', 'id']).reset_index(drop=True)
    required_cols = {'id', 'date', 'issue', 'ready', 'y', *FEATURE_COLS}
    absent = required_cols.difference(df.columns)
    if absent:
        raise ValueError(f'Missing required prospective input columns: {sorted(absent)}')

    if 'scenario' not in df.columns:
        df['scenario'] = np.where(
            df['scenario_IS'] == 1, 'IS',
            np.where(df['scenario_OW'] == 1, 'OW', 'OD'),
        )
    if df['id'].duplicated().any():
        raise ValueError('Duplicate scheduled opportunity IDs in prospective trip stream')
    if (df['ready'] < df['issue']).any():
        raise ValueError('Acausal opportunity horizon (ready < issue) detected')

    eligible_mask = df['y_lag1'].notna() & np.isfinite(df['y_lag1'])
    df['point'] = np.nan
    if eligible_mask.any():
        df.loc[eligible_mask, 'point'] = model.predict(df.loc[eligible_mask])
    df['has_lte'] = df['has_lte'].fillna(0).astype(int)
    df['has_nr'] = df['has_nr'].fillna(0).astype(int)
    df['pattern'] = 2 * df['has_lte'] + df['has_nr']

    # Align initialization timestamps strictly prior to the incoming trip's first issue time
    init_local = init_df.copy().sort_values(['issue', 'id']).reset_index(drop=True)
    shift_s = float(init_local['ready'].max() - df['issue'].min() + 1.0)
    if shift_s > 0:
        init_local['issue'] = init_local['issue'] - shift_s
        init_local['ready'] = init_local['ready'] - shift_s

    cfg = dict(DEFAULT_CONFIG, log_information_clocks=True, log_score_diagnostics=True)
    budget = len(init_local) + int(new_query_cap)

    summaries = {}
    ledgers = {}
    responses = {}
    for policy in ('Frozen', 'Periodic', 'MARUR'):
        act, resp = replay(init_local, df, policy, budget, cfg, scenario='Recorded')
        summaries[policy] = aggregate(act, resp, initial=len(init_local))
        ledgers[policy] = act
        responses[policy] = resp

    marur_s = summaries['MARUR']
    per_s = summaries['Periodic']
    return {
        'run_utc': datetime.now(timezone.utc).isoformat(),
        'validation_status': status,
        'unmet_prerequisites': missing_prereqs,
        'model_sha256': freeze_meta['model_sha256'],
        'new_query_cap': int(new_query_cap),
        'scheduled_ticks': int(len(df)),
        'eligible_ticks': int(eligible_mask.sum()),
        'matched_realized_cost': bool(marur_s['new_query_attempts'] == per_s['new_query_attempts'] == new_query_cap),
        'paired_marur_minus_periodic': {
            'u_delta': float(marur_s['u'] - per_s['u']) if pd.notna(marur_s['u']) and pd.notna(per_s['u']) else float('nan'),
            'hi_delta': float(marur_s['hi'] - per_s['hi']),
            'positive_high_delta': (
                float(marur_s['positive_high'] - per_s['positive_high'])
                if pd.notna(marur_s['positive_high']) and pd.notna(per_s['positive_high'])
                else float('nan')
            ),
            'query_delta': int(marur_s['new_query_attempts'] - per_s['new_query_attempts']),
        },
        'policies': summaries,
        'ledgers': ledgers,
        'responses': responses,
    }


def main():
    if len(sys.argv) < 2:
        # Check-only dry verification when no external raw trip CSV is supplied
        model, init_df, meta = verify_frozen_assets()
        readiness = json.loads((PLAN_DIR / 'readiness.json').read_text(encoding='utf8'))
        print(json.dumps({
            'harness': 'ready',
            'model_verified': meta['model_sha256'],
            'initial_observations': len(init_df),
            'field_readiness': readiness,
        }, indent=2))
        return

    input_csv = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else (PLAN_DIR / 'runs' / input_csv.stem)
    out_dir.mkdir(parents=True, exist_ok=True)
    stream = pd.read_csv(input_csv, float_precision='round_trip')
    meta_path = input_csv.with_suffix('.json')
    meta = json.loads(meta_path.read_text(encoding='utf8')) if meta_path.exists() else {}
    res = run_prospective_trip(stream, meta)
    for pol in ('Frozen', 'Periodic', 'MARUR'):
        res['ledgers'][pol].to_csv(out_dir / f'{pol.lower()}_actions.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
        res['responses'][pol].to_csv(out_dir / f'{pol.lower()}_responses.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
    receipt = {k: v for k, v in res.items() if k not in ('ledgers', 'responses')}
    (out_dir / 'trip_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: receipt[k] for k in ('validation_status', 'scheduled_ticks', 'eligible_ticks', 'matched_realized_cost', 'paired_marur_minus_periodic')}, indent=2))


if __name__ == '__main__':
    main()
