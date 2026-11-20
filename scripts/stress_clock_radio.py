"""Replay hypothetical test-period NR feed losses after fitting the original calibration."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clock_frontier import OUT, metrics
from src.data.loader import extract_sessions_8224890, load_raw_8224890
from src.data.splits import create_experiment_splits
from src.evaluation.conformal import compute_conformal_quantile
from src.models.baselines import HistGradientBoostingThroughputPredictor

NR_FIELDS = ['ss_rsrp', 'ss_rsrq', 'ss_sinr']
RANDOM_SEEDS = range(20)


def remove_nr(frame):
    """Rebuild the model's indicators when the NR feed is entirely unavailable."""
    altered = frame.copy()
    altered[NR_FIELDS] = np.nan
    altered['has_nr'] = 0
    altered['group_id'] = 2 * altered.has_lte
    return altered


def observed_runs(calibration):
    """Count bounded runs of missing NR between observed minutes of the same trace."""
    lengths = []
    for _, trace in calibration.groupby(['regime', 'trace']):
        trace = trace.sort_values('time')
        blocks = trace.time.diff().ne(pd.Timedelta(minutes=1)).cumsum()
        for _, block in trace.groupby(blocks):
            run_ids = block.has_nr.ne(block.has_nr.shift()).cumsum()
            runs = block.groupby(run_ids).has_nr.agg(['first', 'size']).iloc[1:-1]
            lengths.extend(runs.loc[runs['first'] == 0, 'size'].tolist())
    return lengths


def scenarios(test, burst_minutes, weak_cut, original_lower, removed_lower):
    """Mask choices use issue-time radio, clock or candidate rates only."""
    eligible = test.has_nr.to_numpy(dtype=bool)
    minutes = test.time.dt.hour.to_numpy() * 60 + test.time.dt.minute.to_numpy()
    yield 'Recorded', -1, np.zeros(len(test), dtype=bool)
    yield 'Periodic', -1, eligible & (minutes % 4 == 0)
    yield 'Burst', -1, eligible & (minutes % (4 * burst_minutes) < burst_minutes)
    yield 'WeakSignal', -1, eligible & (test.ss_rsrp.to_numpy() <= weak_cut)
    yield 'MinRate', -1, eligible & (removed_lower < original_lower)
    yield 'MaxRate', -1, eligible & (removed_lower > original_lower)
    for seed in RANDOM_SEEDS:
        yield 'Random', seed, eligible & (np.random.default_rng(seed).random(len(test)) < .25)


def pretest_runs(ticks):
    """Use only telemetry completed by the earliest issue in either target regime."""
    first_issue = ticks.loc[ticks.partition == 'test', 'time'].min()
    return observed_runs(ticks[(ticks.partition == 'calibration') & (ticks.end <= first_issue)])


def main():
    ticks = pd.read_csv(OUT/'ticks.csv', parse_dates=['time', 'end'], float_precision='round_trip')
    runs = pretest_runs(ticks)
    if not runs:
        raise ValueError('No bounded calibration runs to estimate burst length')
    burst_minutes = max(1, int(np.median(runs)))
    _, early = extract_sessions_8224890(load_raw_8224890())
    source = early[early.operator == 'Op1']
    split = create_experiment_splits(source, source, 'within_domain', [10])
    tree = HistGradientBoostingThroughputPredictor().fit(split.train, split.train.target_y.to_numpy())
    forecasts, records = [], []
    for regime, frame in ticks.groupby('regime'):
        frame = frame.sort_values(['time', 'trace'])
        cal = frame[frame.partition == 'calibration']
        test = frame[frame.partition == 'test']
        assert cal.end.max() <= test.time.min()
        labeled = cal.dropna(subset=['y']).iloc[:10]
        assert len(labeled) == 10
        q = compute_conformal_quantile(tree.predict(labeled) - labeled.y.to_numpy())
        original = tree.predict(test)
        np.testing.assert_allclose(original, test.HistGBM, rtol=1e-12)
        removed = tree.predict(remove_nr(test))
        base_lower = np.maximum(0, original-q)
        removed_lower = np.maximum(0, removed-q)
        weak_cut = cal.loc[cal.has_nr == 1, 'ss_rsrp'].quantile(.25)
        for name, seed, mask in scenarios(test, burst_minutes, weak_cut, base_lower, removed_lower):
            pred = np.where(mask, removed, original)
            lower = np.maximum(0, pred-q)
            record = metrics(test.y, pred, lower)
            records.append(dict(regime=regime, scenario=name, seed=seed, k=10, q=q,
                                eligible_nr=int(test.has_nr.sum()), masked=int(mask.sum()),
                                calibration_runs=len(runs),
                                burst_minutes=burst_minutes, weak_cut_dbm=weak_cut, **record))
            forecasts.append(test[['time', 'trace', 'has_nr', 'y']].assign(
                regime=regime, scenario=name, seed=seed, masked=mask, point=pred, lower=lower))
    pd.DataFrame(records).to_csv(OUT/'simulated_nr_metrics.csv', index=False)
    pd.concat(forecasts, ignore_index=True).to_csv(OUT/'simulated_nr_forecasts.csv.gz', index=False,
                                                  compression={'method':'gzip', 'mtime':0})


if __name__ == '__main__':
    main()
