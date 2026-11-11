"""Unit tests for causal lag ordering and leakage prevention."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.loader import load_raw_8224890, extract_sessions_8224890

def test_causal_lag_freshness_and_ordering():
    raw_df = load_raw_8224890()
    sdf, fdf = extract_sessions_8224890(raw_df)
    
    # 1. Check that all lag ages are non-negative and <= 60 seconds
    assert (fdf['lag_age_s'] >= 0.0).all(), 'Negative lag age detected (future leakage)!'
    assert (fdf['lag_age_s'] <= 60.0).all(), 'Lag age exceeds 60s freshness cutoff!'
    
    # 2. Check that target_y does not equal y_lag1 identically (no circular assignment)
    assert not (fdf['target_y'] == fdf['y_lag1']).all(), 'target_y identical to y_lag1'
    
    # 3. Check that radio features are physically realistic
    valid_rsrp = fdf['rsrp'].dropna()
    assert (valid_rsrp >= -140.0).all() and (valid_rsrp <= -40.0).all(), 'LTE RSRP out of realistic dBm range'
    
    valid_ss_rsrp = fdf['ss_rsrp'].dropna()
    assert (valid_ss_rsrp >= -140.0).all() and (valid_ss_rsrp <= -40.0).all(), '5G SS-RSRP out of realistic dBm range'
    
    # 4. Check group_id integrity
    assert set(fdf['group_id'].unique()).issubset({0, 1, 2, 3}), 'Invalid group_id value'
    
if __name__ == '__main__':
    test_causal_lag_freshness_and_ordering()
    print('Causality and leakage tests PASSED.')

