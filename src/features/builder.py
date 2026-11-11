"""Feature extraction, encoding, and preprocessing for tabular throughput models."""
from typing import List, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

FEATURE_COLS = [
    'y_lag1',
    'prev_duration_s',
    'lag_age_s',
    'has_lte',
    'has_nr',
    'group_id',
    'rsrp',
    'rsrq',
    'sinr',
    'ss_rsrp',
    'ss_rsrq',
    'ss_sinr',
    'scenario_IS',
    'scenario_OD',
    'scenario_OW'
]

def prepare_feature_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Extract standard features and one-hot encode scenarios."""
    df_out = pd.DataFrame(index=df.index)
    df_out['y_lag1'] = df['y_lag1'].astype(float)
    df_out['prev_duration_s'] = df['prev_duration_s'].astype(float)
    df_out['lag_age_s'] = df['lag_age_s'].astype(float)
    df_out['has_lte'] = df['has_lte'].astype(int)
    df_out['has_nr'] = df['has_nr'].astype(int)
    df_out['group_id'] = df['group_id'].astype(int)
    
    for col in ['rsrp', 'rsrq', 'sinr', 'ss_rsrp', 'ss_rsrq', 'ss_sinr']:
        df_out[col] = df[col].astype(float) if col in df.columns else np.nan
        
    scenario = df['scenario'].astype(str) if 'scenario' in df.columns else 'IS'
    df_out['scenario_IS'] = (scenario == 'IS').astype(int)
    df_out['scenario_OD'] = (scenario == 'OD').astype(int)
    df_out['scenario_OW'] = (scenario == 'OW').astype(int)
    
    return df_out[FEATURE_COLS]

class TabularPreprocessor:
    """Leak-free preprocessing: fits imputer and scaler strictly on training split."""
    def __init__(self):
        self.imputer = SimpleImputer(strategy='median')
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def fit(self, X: pd.DataFrame):
        X_imp = self.imputer.fit_transform(X)
        self.scaler.fit(X_imp)
        self.is_fitted = True
        return self
        
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError('Preprocessor must be fitted on training data first.')
        X_imp = self.imputer.transform(X)
        return self.scaler.transform(X_imp)
        
    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        return self.fit(X).transform(X)

