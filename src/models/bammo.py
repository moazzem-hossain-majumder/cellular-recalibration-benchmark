"""BAMMO: Boosted Additive Model for Data with Missing Observations.

Reference:
T. Jacobson, J. Ding, and H. Zou, 'Predicting 5G throughput with BAMMO, a boosted additive model
for data with missing observations', Journal of the Royal Statistical Society Series C: Applied Statistics,
vol. 74, no. 1, pp. 249-273, 2025.
"""
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from src.features.builder import prepare_feature_dataframe

class BAMMOThroughputPredictor:
    """Component-wise boosted additive model with pattern-specific base learners."""
    def __init__(self, n_stages: int = 80, learning_rate: float = 0.05, max_depth: int = 3, random_state: int = 42):
        self.n_stages = n_stages
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state
        self.pattern_models: Dict[int, List[DecisionTreeRegressor]] = {}
        self.init_mean: float = 0.0

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        X_feats = prepare_feature_dataframe(X)
        self.init_mean = float(np.mean(y))
        residuals = y - self.init_mean
        
        # Partition by observed missingness pattern (group_id: 2 for LTE only, 3 for Dual LTE+NR)
        unique_groups = X_feats['group_id'].unique()
        for g in unique_groups:
            self.pattern_models[int(g)] = []
            
        rng = np.random.RandomState(self.random_state)
        
        # Component-wise boosting across pattern groups
        for stage in range(self.n_stages):
            for g in unique_groups:
                mask = (X_feats['group_id'] == g)
                if mask.sum() < 5:
                    continue
                
                # Active observed features for this pattern
                # If LTE-only (group 2), drop NR features (which are all NaN)
                if g == 2:
                    sub_cols = [c for c in X_feats.columns if not c.startswith('ss_') and c != 'has_nr']
                else:
                    sub_cols = list(X_feats.columns)
                    
                X_sub = X_feats.loc[mask, sub_cols].fillna(0.0)
                y_res = residuals[mask]
                
                tree = DecisionTreeRegressor(
                    max_depth=self.max_depth,
                    random_state=rng.randint(0, 10000)
                )
                tree.fit(X_sub, y_res)
                
                # Update residuals
                pred_update = tree.predict(X_sub)
                residuals[mask] -= self.learning_rate * pred_update
                self.pattern_models[int(g)].append((sub_cols, tree))
                
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_feats = prepare_feature_dataframe(X)
        preds = np.full(len(X_feats), self.init_mean, dtype=float)
        
        for g, stage_list in self.pattern_models.items():
            mask = (X_feats['group_id'] == g)
            if not mask.any():
                continue
            
            for sub_cols, tree in stage_list:
                X_sub = X_feats.loc[mask, sub_cols].fillna(0.0)
                preds[mask] += self.learning_rate * tree.predict(X_sub)
                
        # Handle unseen groups with fallback
        unseen_mask = ~X_feats['group_id'].isin(self.pattern_models.keys())
        if unseen_mask.any():
            preds[unseen_mask] = self.init_mean
            
        return np.maximum(0.0, preds)

