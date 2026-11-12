"""Exploratory paired ten-label comparison on the existing, previously seen suffixes."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.loader import load_raw_8224890, extract_sessions_8224890, load_14073311_ookla
from src.data.splits import create_experiment_splits
from src.models.baselines import HistGradientBoostingThroughputPredictor, PersistencePredictor
from src.evaluation.conformal import GlobalConformalCalibrator
from src.evaluation.metrics import compute_reliability_metrics


def main():
    _, earlier = extract_sessions_8224890(load_raw_8224890())
    later = load_14073311_ookla()
    source = earlier[earlier.operator == 'Op1']
    targets = [source, later[later.operator == 'Op1'], earlier[earlier.operator == 'Op2'], later[later.operator == 'Op2']]
    development = create_experiment_splits(source, source, 'within_domain', [10])
    models = {'HistGBM': HistGradientBoostingThroughputPredictor(), 'Persistence': PersistencePredictor()}
    for model in models.values():
        model.fit(development.train, development.train.target_y.to_numpy())
    reference = pd.read_csv(ROOT/'results/metrics/calibration_budget_results.csv')
    saved = pd.read_csv(ROOT/'results/diagnostics/test_forecasts.csv')
    records = []
    for i, target in enumerate(targets):
        regime = f'E{i}'
        splits = create_experiment_splits(source, target, 'within_domain' if i == 0 else 'transfer', [10])
        pool = splits.target_calib_pool.sort_values('t_start')
        test = splits.target_test
        truth = test.target_y.to_numpy()
        check = saved[(saved.regime.str.startswith(regime)) & (saved.budget_K == 10)]
        np.testing.assert_array_equal(check.session_id, test.session_id)
        np.testing.assert_allclose(check.target, truth)
        assert pool.session_id.is_unique and pool.t_start.max() < test.t_start.min()
        # First ten match the primary protocol. Every subsequent complete,
        # disjoint ten-session block is included, with the identical test suffix.
        for start in range(0, len(pool)-9, 10):
            block = pool.iloc[start:start+10]
            for name, model in models.items():
                point = model.predict(test)
                calibrator = GlobalConformalCalibrator(.10).fit(model.predict(block), block.target_y.to_numpy())
                lower, _ = calibrator.predict_lower_bound(point)
                if not np.isfinite(lower).all():
                    raise ValueError('Nonfinite lower forecast')
                scores = compute_reliability_metrics(truth, point, lower)
                if start == 0 and name == 'HistGBM':
                    ref = reference[(reference.regime.str.startswith(regime)) & (reference.budget_K == 10) & (reference.method == 'Global_Conformal')].iloc[0]
                    np.testing.assert_allclose([scores.violation_rate,scores.supported_rate_fraction],[ref.violation_rate,ref.supported_fraction])
                    np.testing.assert_allclose(lower,check.Global_Conformal)
                records.append(dict(regime=regime, calibration_block=start//10+1, model=name,
                                    observations=len(test),dates=test.date.nunique(),q_mbps=calibrator.q,
                                    violation=scores.violation_rate,supported=scores.supported_rate_fraction,
                                    point_mae_mbps=scores.mae))
    frame = pd.DataFrame(records)
    path = ROOT/'results/exploratory/persistence_prefixes.csv'
    path.parent.mkdir(exist_ok=True)
    frame.to_csv(path,index=False)
    print(frame[frame.calibration_block==1].to_string(index=False))
    for regime, rows in frame.groupby('regime'):
        v = rows.pivot(index='calibration_block',columns='model',values='violation')
        u = rows.pivot(index='calibration_block',columns='model',values='supported')
        print(regime, len(v), 'blocks;', int(((v.Persistence<=.1)&(u.Persistence>u.HistGBM)).sum()), 'with higher persistence U and V <= .10')


if __name__ == '__main__':
    main()
