"""Point and tail-targeting predictors with strictly chronological validation & CQR calibration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.preprocessing import StandardScaler

from src.evaluation.conformal import compute_conformal_quantile
from src.features.builder import FEATURE_COLS, prepare_feature_dataframe

MONOTONIC_RADIO_FEATURES = ('rsrp', 'sinr', 'ss_rsrp', 'ss_sinr')


def extract_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Extract ordered FEATURE_COLS frame cleanly without requiring raw scenario strings when pre-encoded."""
    if all(col in df.columns for col in FEATURE_COLS):
        out = pd.DataFrame(index=df.index)
        for col in FEATURE_COLS:
            dtype = int if col in ('has_lte', 'has_nr', 'group_id', 'scenario_IS', 'scenario_OD', 'scenario_OW') else float
            out[col] = df[col].astype(dtype)
        return out
    return prepare_feature_dataframe(df)


def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, quantile: float) -> float:
    """Compute mean pinball (check) loss at target quantile."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    err = y_t - y_p
    return float(np.mean(np.maximum(quantile * err, (quantile - 1.0) * err)))


class EmptySafeTabularPreprocessor:
    """Train-only median imputer + StandardScaler safe when entire columns are NaN in train."""

    def __init__(self) -> None:
        self.medians_: np.ndarray | None = None
        self.scaler = StandardScaler()

    def fit(self, X: pd.DataFrame) -> 'EmptySafeTabularPreprocessor':
        arr = X[FEATURE_COLS].to_numpy(dtype=float, copy=True)
        medians = np.zeros(arr.shape[1], dtype=float)
        for j in range(arr.shape[1]):
            col = arr[:, j]
            fin = np.isfinite(col)
            if fin.any():
                med = float(np.median(col[fin]))
            else:
                med = 0.0
            medians[j] = med
            col[~fin] = med
        self.medians_ = medians
        self.scaler.fit(arr)
        self.scaler.scale_ = np.where(self.scaler.scale_ < 1e-6, 1.0, self.scaler.scale_)
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        if self.medians_ is None:
            raise RuntimeError('Preprocessor must be fitted before transform().')
        arr = X[FEATURE_COLS].to_numpy(dtype=float, copy=True)
        for j in range(arr.shape[1]):
            col = arr[:, j]
            fin = np.isfinite(col)
            if not fin.all():
                col[~fin] = self.medians_[j]
        return self.scaler.transform(arr)

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        return self.fit(X).transform(X)


@dataclass
class FittedTabularPredictor:
    """Uniform wrapper around a fitted regression or tail predictor."""

    name: str
    estimator: Any
    preprocessor: EmptySafeTabularPreprocessor | None = None
    feature_cols: list[str] | None = None
    selected_params: dict[str, Any] = field(default_factory=dict)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        X = extract_feature_matrix(df)
        cols = self.feature_cols if self.feature_cols is not None else FEATURE_COLS
        if self.preprocessor is not None:
            X_in = self.preprocessor.transform(X)
        else:
            X_in = X[cols]
        preds = np.asarray(self.estimator.predict(X_in), dtype=float)
        return np.maximum(0.0, preds)


@dataclass
class CQRPredictorWrapper:
    """Conformalized Quantile Regression predictor (unscaled or interval-width scaled)."""

    name: str
    q_lo_pred: FittedTabularPredictor
    q_hi_pred: FittedTabularPredictor | None
    offset: float
    scaled: bool = False
    min_width: float = 0.5
    selected_params: dict[str, Any] = field(default_factory=dict)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        lo_raw = self.q_lo_pred.predict(df)
        if not self.scaled:
            return np.maximum(0.0, lo_raw - self.offset)
        if self.q_hi_pred is None:
            raise RuntimeError('Scaled CQR requires upper quantile estimator.')
        hi_raw = self.q_hi_pred.predict(df)
        width = np.maximum(self.min_width, hi_raw - lo_raw)
        return np.maximum(0.0, lo_raw - self.offset * width)


def _warm_start_early_stopping(
    *,
    X_tr: pd.DataFrame,
    y_tr: np.ndarray,
    X_va: pd.DataFrame,
    y_va: np.ndarray,
    loss: str,
    quantile: float | None,
    max_depth: int,
    min_samples_leaf: int,
    l2_regularization: float,
    monotonic_cst: list[int] | None,
    learning_rate: float = 0.05,
    max_iter_max: int = 200,
    iter_step: int = 10,
    patience: int = 3,
    seed: int = 42,
) -> tuple[int, float]:
    """Run deterministic warm-start boosting with chronological validation early stopping."""
    kwargs: dict[str, Any] = dict(
        loss=loss,
        learning_rate=learning_rate,
        max_depth=int(max_depth),
        min_samples_leaf=int(min_samples_leaf),
        l2_regularization=float(l2_regularization),
        early_stopping=False,
        warm_start=True,
        max_iter=iter_step,
        random_state=int(seed),
    )
    if quantile is not None:
        kwargs['quantile'] = float(quantile)
    if monotonic_cst is not None:
        kwargs['monotonic_cst'] = monotonic_cst

    est = HistGradientBoostingRegressor(**kwargs)
    best_loss = float('inf')
    best_iter = iter_step
    stale = 0
    for n_iter in range(iter_step, max_iter_max + 1, iter_step):
        est.set_params(max_iter=n_iter)
        est.fit(X_tr, y_tr)
        pred_va = np.maximum(0.0, np.asarray(est.predict(X_va), dtype=float))
        if quantile is not None:
            cur_loss = pinball_loss(y_va, pred_va, quantile)
        else:
            cur_loss = float(np.mean((y_va - pred_va) ** 2))
        if cur_loss < best_loss - 1e-6:
            best_loss = cur_loss
            best_iter = n_iter
            stale = 0
        else:
            stale += 1
            if stale >= patience:
                break
    return best_iter, best_loss


def fit_select_histgbm(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    *,
    name: str,
    grid_cfg: dict[str, Any],
    loss: str = 'squared_error',
    quantile: float | None = None,
    monotonic_features: tuple[str, ...] = (),
    seed: int = 42,
    refit_on_train_plus_val: bool = True,
) -> FittedTabularPredictor:
    """Grid-search regularized or quantile HistGBM with strictly time-ordered validation early stopping."""
    X_tr_full = extract_feature_matrix(train_df)
    active_cols = [c for c in FEATURE_COLS if X_tr_full[c].notna().any()]
    if not active_cols:
        raise ValueError('Training DataFrame has zero non-NaN feature columns.')
    X_tr = X_tr_full[active_cols]
    y_tr = train_df['y'].to_numpy(dtype=float)
    X_va = extract_feature_matrix(val_df)[active_cols]
    y_va = val_df['y'].to_numpy(dtype=float)

    mono_cst: list[int] | None = None
    active_mono: list[str] = []
    if monotonic_features:
        mono_cst = []
        for col in active_cols:
            if col in monotonic_features and X_tr[col].dropna().nunique() >= 2:
                mono_cst.append(1)
                active_mono.append(col)
            else:
                mono_cst.append(0)
        if not any(mono_cst):
            mono_cst = None

    best_cfg: dict[str, Any] | None = None
    best_val_loss = float('inf')
    for depth in grid_cfg['max_depth']:
        for leaf in grid_cfg['min_samples_leaf']:
            for l2 in grid_cfg['l2_regularization']:
                n_iter, vloss = _warm_start_early_stopping(
                    X_tr=X_tr,
                    y_tr=y_tr,
                    X_va=X_va,
                    y_va=y_va,
                    loss=loss,
                    quantile=quantile,
                    max_depth=int(depth),
                    min_samples_leaf=int(leaf),
                    l2_regularization=float(l2),
                    monotonic_cst=mono_cst,
                    learning_rate=float(grid_cfg.get('learning_rate', 0.05)),
                    max_iter_max=int(grid_cfg.get('max_iter_max', 200)),
                    iter_step=int(grid_cfg.get('iter_step', 10)),
                    patience=int(grid_cfg.get('patience', 3)),
                    seed=seed,
                )
                if vloss < best_val_loss:
                    best_val_loss = vloss
                    best_cfg = {
                        'max_depth': int(depth),
                        'min_samples_leaf': int(leaf),
                        'l2_regularization': float(l2),
                        'max_iter': int(n_iter),
                        'val_loss': float(vloss),
                        'monotonic_active_cols': active_mono,
                        'train_n': int(len(train_df)),
                        'val_n': int(len(val_df)),
                    }
    assert best_cfg is not None
    final_kwargs: dict[str, Any] = dict(
        loss=loss,
        learning_rate=float(grid_cfg.get('learning_rate', 0.05)),
        max_depth=best_cfg['max_depth'],
        min_samples_leaf=best_cfg['min_samples_leaf'],
        l2_regularization=best_cfg['l2_regularization'],
        max_iter=best_cfg['max_iter'],
        early_stopping=False,
        random_state=int(seed),
    )
    if quantile is not None:
        final_kwargs['quantile'] = float(quantile)
    if mono_cst is not None:
        final_kwargs['monotonic_cst'] = mono_cst

    fit_df = pd.concat([train_df, val_df], ignore_index=True) if refit_on_train_plus_val else train_df
    X_fit = extract_feature_matrix(fit_df)[active_cols]
    y_fit = fit_df['y'].to_numpy(dtype=float)
    best_cfg['refit_n'] = int(len(fit_df))
    best_cfg['active_feature_cols'] = active_cols
    est = HistGradientBoostingRegressor(**final_kwargs).fit(X_fit, y_fit)
    return FittedTabularPredictor(
        name=name, estimator=est, preprocessor=None, feature_cols=active_cols, selected_params=best_cfg
    )


def fit_select_linear(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    *,
    family: str,
    grid_cfg: dict[str, Any],
    seed: int = 42,
) -> FittedTabularPredictor:
    """Fit Ridge or ElasticNet with train-only preprocessing tuned on chronological val split."""
    X_tr = extract_feature_matrix(train_df)
    y_tr = train_df['y'].to_numpy(dtype=float)
    X_va = extract_feature_matrix(val_df)
    y_va = val_df['y'].to_numpy(dtype=float)

    prep = EmptySafeTabularPreprocessor().fit(X_tr)
    X_tr_s = prep.transform(X_tr)
    X_va_s = prep.transform(X_va)

    best_loss = float('inf')
    best_cfg: dict[str, Any] = {}
    if family == 'ridge':
        for alpha in grid_cfg['alpha']:
            est = Ridge(alpha=float(alpha), random_state=int(seed)).fit(X_tr_s, y_tr)
            pred_va = np.maximum(0.0, est.predict(X_va_s))
            mse = float(np.mean((y_va - pred_va) ** 2))
            if mse < best_loss:
                best_loss = mse
                best_cfg = {'alpha': float(alpha), 'val_loss': mse}
        fit_df = pd.concat([train_df, val_df], ignore_index=True)
        final_prep = EmptySafeTabularPreprocessor().fit(extract_feature_matrix(fit_df))
        final_est = Ridge(alpha=best_cfg['alpha'], random_state=int(seed)).fit(
            final_prep.transform(extract_feature_matrix(fit_df)),
            fit_df['y'].to_numpy(dtype=float),
        )
    elif family == 'elasticnet':
        max_iter = int(grid_cfg.get('max_iter', 5000))
        for alpha in grid_cfg['alpha']:
            for l1_ratio in grid_cfg['l1_ratio']:
                est = ElasticNet(
                    alpha=float(alpha),
                    l1_ratio=float(l1_ratio),
                    max_iter=max_iter,
                    random_state=int(seed),
                ).fit(X_tr_s, y_tr)
                pred_va = np.maximum(0.0, est.predict(X_va_s))
                mse = float(np.mean((y_va - pred_va) ** 2))
                if mse < best_loss:
                    best_loss = mse
                    best_cfg = {'alpha': float(alpha), 'l1_ratio': float(l1_ratio), 'val_loss': mse}
        fit_df = pd.concat([train_df, val_df], ignore_index=True)
        final_prep = EmptySafeTabularPreprocessor().fit(extract_feature_matrix(fit_df))
        final_est = ElasticNet(
            alpha=best_cfg['alpha'],
            l1_ratio=best_cfg['l1_ratio'],
            max_iter=max_iter,
            random_state=int(seed),
        ).fit(
            final_prep.transform(extract_feature_matrix(fit_df)),
            fit_df['y'].to_numpy(dtype=float),
        )
    else:
        raise ValueError(f'Unknown linear family: {family}')

    best_cfg['train_n'] = int(len(train_df))
    best_cfg['val_n'] = int(len(val_df))
    best_cfg['refit_n'] = int(len(train_df) + len(val_df))
    return FittedTabularPredictor(
        name='Ridge_LOCampO' if family == 'ridge' else 'ElasticNet_LOCampO',
        estimator=final_est,
        preprocessor=final_prep,
        selected_params=best_cfg,
    )


def fit_cqr_pair_blocked(
    proper_train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    cqr_calib_df: pd.DataFrame,
    *,
    q_grid_cfg: dict[str, Any],
    cqr_cfg: dict[str, Any],
    seed: int = 42,
) -> tuple[CQRPredictorWrapper, CQRPredictorWrapper]:
    """Fit campaign-date-blocked Conformalized Quantile Regression (unscaled & width-scaled)."""
    q_lo = fit_select_histgbm(
        proper_train_df,
        val_df,
        name='CQR_q10_base',
        grid_cfg=q_grid_cfg,
        loss='quantile',
        quantile=float(cqr_cfg.get('lower_quantile', 0.10)),
        seed=seed,
        refit_on_train_plus_val=True,
    )
    q_hi = fit_select_histgbm(
        proper_train_df,
        val_df,
        name='CQR_q90_base',
        grid_cfg=q_grid_cfg,
        loss='quantile',
        quantile=float(cqr_cfg.get('upper_quantile', 0.90)),
        seed=seed,
        refit_on_train_plus_val=True,
    )
    alpha = float(cqr_cfg.get('alpha', 0.10))
    min_width = float(cqr_cfg.get('min_interval_width_mbps', 0.5))

    pred_cal_lo = q_lo.predict(cqr_calib_df)
    pred_cal_hi = q_hi.predict(cqr_calib_df)
    y_cal = cqr_calib_df['y'].to_numpy(dtype=float)

    scores_unscaled = pred_cal_lo - y_cal
    offset_unscaled = compute_conformal_quantile(scores_unscaled, alpha=alpha)
    if np.isinf(offset_unscaled):
        offset_unscaled = float(np.quantile(scores_unscaled, 1.0 - alpha))

    width_cal = np.maximum(min_width, pred_cal_hi - pred_cal_lo)
    scores_scaled = scores_unscaled / width_cal
    offset_scaled = compute_conformal_quantile(scores_scaled, alpha=alpha)
    if np.isinf(offset_scaled):
        offset_scaled = float(np.quantile(scores_scaled, 1.0 - alpha))

    base_meta = {
        'q10_params': q_lo.selected_params,
        'q90_params': q_hi.selected_params,
        'calib_n': int(len(cqr_calib_df)),
        'calib_dates': int(cqr_calib_df['date'].nunique()),
    }
    cqr_unscaled = CQRPredictorWrapper(
        name='CQR_Unscaled_LOCampO',
        q_lo_pred=q_lo,
        q_hi_pred=None,
        offset=float(offset_unscaled),
        scaled=False,
        min_width=min_width,
        selected_params={**base_meta, 'conformal_offset': float(offset_unscaled)},
    )
    cqr_scaled = CQRPredictorWrapper(
        name='CQR_Scaled_LOCampO',
        q_lo_pred=q_lo,
        q_hi_pred=q_hi,
        offset=float(offset_scaled),
        scaled=True,
        min_width=min_width,
        selected_params={**base_meta, 'conformal_scale': float(offset_scaled)},
    )
    return cqr_unscaled, cqr_scaled
