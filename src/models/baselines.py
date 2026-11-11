"""Baseline predictors for cellular throughput forecasting."""
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor, GradientBoostingRegressor
from src.features.builder import prepare_feature_dataframe, TabularPreprocessor

class PersistencePredictor:
    """Predicts next-test throughput as the most recently completed test throughput."""
    def fit(self, X: pd.DataFrame, y: np.ndarray):
        return self
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.maximum(0.0, X['y_lag1'].to_numpy(dtype=float))

class RidgeThroughputPredictor:
    """Interpretable linear baseline with train-only median imputation and scaling."""
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.preprocessor = TabularPreprocessor()
        self.model = Ridge(alpha=self.alpha, positive=True)
        
    def fit(self, X: pd.DataFrame, y: np.ndarray):
        X_feats = prepare_feature_dataframe(X)
        X_scaled = self.preprocessor.fit_transform(X_feats)
        self.model.fit(X_scaled, y)
        return self
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_feats = prepare_feature_dataframe(X)
        X_scaled = self.preprocessor.transform(X_feats)
        preds = self.model.predict(X_scaled)
        return np.maximum(0.0, preds)

class HistGradientBoostingThroughputPredictor:
    """Tree-based boosting baseline with native NaN handling and interaction learning."""
    def __init__(self, max_iter: int = 100, max_depth: int = 5, learning_rate: float = 0.05, random_state: int = 42):
        self.model = HistGradientBoostingRegressor(
            max_iter=max_iter,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            loss='squared_error'
        )
        
    def fit(self, X: pd.DataFrame, y: np.ndarray):
        X_feats = prepare_feature_dataframe(X)
        self.model.fit(X_feats, y)
        return self
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_feats = prepare_feature_dataframe(X)
        preds = self.model.predict(X_feats)
        return np.maximum(0.0, preds)

class QuantileBoostingPredictor:
    """Direct lower-quantile regression baseline (nominal alpha=0.10) using pinball loss."""
    def __init__(self, alpha: float = 0.10, n_estimators: int = 100, max_depth: int = 4, learning_rate: float = 0.05, random_state: int = 42):
        self.alpha = alpha
        self.preprocessor = TabularPreprocessor()
        self.model = GradientBoostingRegressor(
            loss='quantile',
            alpha=self.alpha,
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state
        )
        
    def fit(self, X: pd.DataFrame, y: np.ndarray):
        X_feats = prepare_feature_dataframe(X)
        X_scaled = self.preprocessor.fit_transform(X_feats)
        self.model.fit(X_scaled, y)
        return self
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_feats = prepare_feature_dataframe(X)
        X_scaled = self.preprocessor.transform(X_feats)
        preds = self.model.predict(X_scaled)
        return np.maximum(0.0, preds)

