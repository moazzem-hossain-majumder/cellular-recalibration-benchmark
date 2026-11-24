"""Build untouched held-out cohorts (Rome Capacity, Oslo Commute, Ireland Static).

Extracts causally aligned 60-second forecast opportunities from three completely
uninspected public cellular archives using ONLY frozen pre-existing models
(zero retraining on held-out targets) and strict chronological initial splits.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.clock_frontier import RADIO, clean_numeric, clock_pairs
from scripts.replay_oslo_playback import BUS, CUTOFF, OUT as OSLO_META_DIR
from scripts.run_prospective_validation import verify_frozen_assets
from src.features.builder import FEATURE_COLS

OUT_DIR = ROOT / 'results/pacer'


def _seconds(dt_series: pd.Series) -> np.ndarray:
    ts = pd.DatetimeIndex(pd.to_datetime(dt_series, utc=True))
    return (ts - pd.Timestamp('1970-01-01', tz='UTC')).total_seconds().to_numpy(dtype=np.float64)


def _rome_capacity_ticks(frozen_model) -> pd.DataFrame:
    """Extract chronological 60s pairs for Op1 & Op2 in untouched Rome Capacity Tests."""
    cap_dir = ROOT / 'data/extracted/14073311/Active Performance Dataset - 1/Capacity Tests/Op1 and Op2 - Italy'
    raw_rows = []
    for file in sorted(cap_dir.rglob('*.csv')):
        frame = pd.read_csv(file, sep=';', low_memory=False)
        frame.columns = frame.columns.str.strip()
        ts = pd.to_datetime(
            frame['Day'].astype(str).str.strip() + ' ' + frame['Timestamp [dd.mm.yyyy,hh:mm:ss.ss]'].astype(str).str.strip(),
            format='%d.%m.%Y %H:%M:%S.%f',
            errors='coerce',
        )
        frame = frame.assign(_ts=ts).dropna(subset=['_ts']).sort_values('_ts').set_index('_ts')
        if frame.empty:
            continue
        scen = 'IS' if '_IS_' in file.name else 'OD' if '_OD_' in file.name else 'OW'
        for op, cohort in ((1, 'Rome_Capacity_Op1'), (2, 'Rome_Capacity_Op2')):
            def _field(key: str):
                col = next((c for c in frame.columns if key in c and f': [{op}]' in c), None)
                return (clean_numeric(frame[col]) if col else pd.Series(np.nan, index=frame.index)), (col or '')

            rate, col = _field('Mean Netw. DL')
            rate = rate.where(rate >= 0) * (1.0 if '[MBit/s]' in col else 0.001)
            pairs = clock_pairs(rate, frame.index.min(), frame.index.max(), include_ineligible=True).set_index('time')
            prev = pairs.index - pd.Timedelta(minutes=1)
            times = rate.dropna().index.to_series().resample('min')
            tlast = times.last().reindex(prev)
            pairs['lag_age_s'] = (pairs.index - tlast.to_numpy()).dt.total_seconds() if hasattr(pairs.index - tlast.to_numpy(), 'dt') else (pairs.index - pd.DatetimeIndex(tlast)).total_seconds()
            pairs['prev_duration_s'] = (tlast - times.first().reindex(prev)).dt.total_seconds().to_numpy()
            for name, key in RADIO.items():
                pairs[name] = _field(key)[0].resample('min').last().reindex(prev).to_numpy()
            pairs['cohort'] = cohort
            pairs['trace'] = file.name
            pairs['scenario'] = scen
            pairs['date'] = pd.to_datetime(pairs.index).date.astype(str)
            pairs['issue'] = _seconds(pairs.index)
            pairs['ready'] = _seconds(pairs['end'])
            raw_rows.append(pairs.reset_index())

    data = pd.concat(raw_rows, ignore_index=True).sort_values(['cohort', 'issue', 'trace'])
    data['has_lte'] = data['rsrp'].notna().astype(int)
    data['has_nr'] = data['ss_rsrp'].notna().astype(int)
    data['group_id'] = 2 * data['has_lte'] + data['has_nr']
    data['pattern'] = data['group_id'].astype(int)
    data['y_lag1'] = data['lag'].astype(float)
    data['Persistence'] = data['y_lag1']
    data['scenario_IS'] = (data['scenario'] == 'IS').astype(int)
    data['scenario_OD'] = (data['scenario'] == 'OD').astype(int)
    data['scenario_OW'] = (data['scenario'] == 'OW').astype(int)

    issued = data['y_lag1'].notna()
    data['HistGBM'] = np.nan
    data.loc[issued, 'HistGBM'] = frozen_model.predict(data.loc[issued])
    data['id'] = [f"{c}:{i:05d}" for i, c in enumerate(data['cohort'])]
    data['physical_unit'] = 'RomeCap:' + data['date']

    # Chronological initial split per cohort before observing targets
    parts = []
    for cohort, grp in data.groupby('cohort', sort=False):
        grp = grp.sort_values(['issue', 'trace']).copy()
        complete_dates = sorted(grp.loc[grp['Persistence'].notna() & grp['y'].notna(), 'date'].unique())
        cutoff_date = None
        for idx in range(1, len(complete_dates)):
            prefix = grp[(grp['date'] < complete_dates[idx]) & grp['Persistence'].notna() & grp['y'].notna()]
            if len(prefix) >= 10:
                cutoff_date = complete_dates[idx]
                break
        if cutoff_date is None:
            raise RuntimeError(f'Insufficient pre-cutoff initial rows for {cohort}')
        cal_idx = grp[(grp['date'] < cutoff_date) & grp['Persistence'].notna() & grp['y'].notna()].head(10).index
        grp['partition'] = np.where(grp['date'] >= cutoff_date, 'test', 'unused')
        grp.loc[cal_idx, 'partition'] = 'cal'
        assert grp.loc[cal_idx, 'ready'].max() <= grp.loc[grp['partition'] == 'test', 'issue'].min()
        parts.append(grp)
    return pd.concat(parts, ignore_index=True)


def _oslo_commute_ticks(oslo_cutoff_iso: str) -> pd.DataFrame:
    """Build Oslo Multi-Route 60s causal stream with frozen pre-2010-10-01 bus regressor."""
    split = pd.Timestamp('2010-10-01', tz='UTC')
    cutoff = pd.Timestamp(oslo_cutoff_iso)

    def _minute_pairs_from_log(path: Path, route_name: str, check_sha: str | None = None) -> pd.DataFrame:
        if check_sha and hashlib.sha256(path.read_bytes()).hexdigest() != check_sha:
            raise ValueError(f'SHA mismatch: {path}')
        d = pd.read_csv(path, sep=r'\s+', header=None, names=['unix', 'ms', 'lat', 'lon', 'bytes', 'elapsed'])
        d = d.sort_values('ms', kind='stable')
        valid = (d['bytes'] >= 0) & (d['elapsed'] > 0) & (d['ms'].diff().eq(d['elapsed']) | (d.index == d.index[0]))
        rate = (.008 * d['bytes'] / d['elapsed']).where(valid)
        ts = pd.to_datetime(d['unix'], unit='s', utc=True)
        ser = pd.Series(rate.to_numpy(), index=ts).dropna()
        if ser.empty:
            return pd.DataFrame()
        # Handle identical-second duplicate timestamps deterministically
        ser = ser.groupby(level=0).last()
        pairs = clock_pairs(ser, ser.index.min(), ser.index.max(), include_ineligible=True)
        last_min = ser.resample('min').last()
        lag2 = last_min.reindex(pairs['time'] - pd.Timedelta(minutes=2)).to_numpy()
        pairs['lag2'] = np.where(np.isnan(lag2), pairs['lag'], lag2)
        pairs['trace'] = f'{route_name}/{path.name}'
        pairs['route'] = route_name
        pairs['date'] = pairs['time'].dt.date.astype(str)
        pairs['issue'] = _seconds(pairs['time'])
        pairs['ready'] = _seconds(pairs['end'])
        return pairs

    # Train lag tree strictly on pre-2010-10-01 Oslo bus logs
    manifest = json.loads((OSLO_META_DIR / 'dataset_manifest.json').read_text(encoding='utf8'))
    bus_frames = [
        _minute_pairs_from_log(BUS / name, 'bus', digest)
        for name, digest in manifest['norway_files'].items()
    ]
    bus_all = pd.concat([b for b in bus_frames if not b.empty], ignore_index=True)
    bus_train = bus_all[(bus_all['end'] < split) & bus_all['lag'].notna() & bus_all['lag2'].notna() & bus_all['y'].notna()]
    tree = HistGradientBoostingRegressor(max_iter=100, max_depth=5, learning_rate=0.05, random_state=42)
    tree.fit(bus_train[['lag', 'lag2']], bus_train['y'])

    # Load all multi-route Oslo playback logs (car, ferry, train, tram)
    pins = json.loads((ROOT / 'data/metadata/oslo_playback_sources.json').read_text(encoding='utf-8-sig'))
    commute_frames = [
        _minute_pairs_from_log(ROOT / 'data/raw/oslo-playback' / item['route'] / item['name'], item['route'], item['sha256'])
        for item in pins
    ]
    data = pd.concat([c for c in commute_frames if not c.empty], ignore_index=True)
    data = data.sort_values(['issue', 'trace']).reset_index(drop=True)
    issued = data['lag'].notna()
    data['Persistence'] = data['lag'].astype(float)
    data['HistGBM'] = np.nan
    data.loc[issued, 'HistGBM'] = np.maximum(0.0, tree.predict(data.loc[issued, ['lag', 'lag2']]))
    data['cohort'] = 'Oslo_Commute'
    data['pattern'] = 1  # Single-RAT HSPA archive (matches pre-cutoff commute regime)
    data['scenario'] = 'commute'
    data['has_lte'] = 0
    data['has_nr'] = 0
    data['group_id'] = 1
    data['id'] = [f'Oslo_Commute:{i:05d}' for i in range(len(data))]
    data['physical_unit'] = 'Oslo:' + data['date']

    pre = data[(data['end'] < cutoff) & data['Persistence'].notna() & data['y'].notna()].tail(10)
    post = data['time'] >= cutoff
    assert len(pre) == 10 and pre['ready'].max() <= data.loc[post, 'issue'].min()
    data['partition'] = np.where(post, 'test', 'unused')
    data.loc[pre.index, 'partition'] = 'cal'
    return data


def _ireland_static_ticks(frozen_model) -> pd.DataFrame:
    """Build Ireland Static Download 60s stream excluded from Driving replay."""
    raw = pd.read_parquet(ROOT / 'data/raw/sirhan-external-work/consolidated.parquet').sort_values(
        ['trace_id', 'row_in_trace']
    )
    raw['time'] = pd.to_datetime(raw['Timestamp'], format='%Y.%m.%d_%H.%M.%S')
    st = raw[(raw['app'] == 'Download') & (raw['mobility'] == 'Static')].copy()

    rows = []
    for trace, b in st.groupby('trace_id'):
        b = b.set_index('time').sort_index(kind='stable')
        for t in pd.date_range(b.index.min().ceil('min'), b.index.max(), freq='min'):
            past = b[(b.index >= t - pd.Timedelta('1min')) & (b.index < t)]
            end = t + pd.Timedelta('1min')
            future = b[(b.index >= t) & (b.index < end)]
            lag = past['DL_Mbps'].where(past['DL_Mbps'] >= 0).dropna()
            y_s = future['DL_Mbps'].where(future['DL_Mbps'] >= 0).dropna()
            row = {
                'trace': f'trace_{trace}',
                'date': str(t.date()),
                'time': t,
                'end': end,
                'scenario': 'IS',
                'y_lag1': float(lag.iloc[-1]) if len(lag) else np.nan,
                'y': float(y_s.iloc[-1]) if len(y_s) and end <= b.index.max() else np.nan,
                'lag_age_s': float((t - lag.index[-1]).total_seconds()) if len(lag) else np.nan,
                'prev_duration_s': float((lag.index[-1] - lag.index[0]).total_seconds()) if len(lag) else np.nan,
                'sinr': np.nan,
                'ss_sinr': np.nan,
            }
            for src, dest in [('RSRP', 'rsrp'), ('RSRQ', 'rsrq'), ('NRxRSRP', 'ss_rsrp'), ('NRxRSRQ', 'ss_rsrq')]:
                vals = past[src].dropna()
                row[dest] = float(vals.iloc[-1]) if len(vals) else np.nan
            rows.append(row)

    data = pd.DataFrame(rows).sort_values(['time', 'trace']).reset_index(drop=True)
    data['has_lte'] = data['rsrp'].notna().astype(int)
    data['has_nr'] = data['ss_rsrp'].notna().astype(int)
    data['group_id'] = 2 * data['has_lte'] + data['has_nr']
    data['pattern'] = data['group_id'].astype(int)
    data['Persistence'] = data['y_lag1']
    data['scenario_IS'] = 1
    data['scenario_OD'] = 0
    data['scenario_OW'] = 0

    issued = data['y_lag1'].notna()
    data['HistGBM'] = np.nan
    data.loc[issued, 'HistGBM'] = frozen_model.predict(data.loc[issued])
    data['cohort'] = 'Ireland_Static'
    data['issue'] = _seconds(data['time'])
    data['ready'] = _seconds(data['end'])
    data['id'] = [f'Ireland_Static:{i:05d}' for i in range(len(data))]
    data['physical_unit'] = 'IrelandStatic:' + data['date']

    dates = sorted(data.loc[issued & data['y'].notna(), 'date'].unique())
    cutoff_date = None
    for idx in range(1, len(dates)):
        pref = data[(data['date'] < dates[idx]) & issued & data['y'].notna()]
        if len(pref) >= 10:
            cutoff_date = dates[idx]
            break
    if cutoff_date is None:
        raise RuntimeError('Insufficient pre-cutoff initial rows for Ireland_Static')
    cal = data[(data['date'] < cutoff_date) & issued & data['y'].notna()].head(10)
    test = data['date'] >= cutoff_date
    assert len(cal) == 10 and cal['ready'].max() <= data.loc[test, 'issue'].min()
    data['partition'] = np.where(test, 'test', 'unused')
    data.loc[cal.index, 'partition'] = 'cal'
    return data


def build_all() -> pd.DataFrame:
    """Build and persist all untouched held-out cohorts cleanly."""
    cfg = json.loads((ROOT / 'configs/pacer.json').read_text(encoding='utf8'))
    frozen_model, _, _ = verify_frozen_assets()
    frames = [
        _rome_capacity_ticks(frozen_model),
        _oslo_commute_ticks(cfg['oslo_cutoff_utc']),
        _ireland_static_ticks(frozen_model),
    ]
    keep_cols = [
        'cohort', 'partition', 'date', 'issue', 'ready', 'id', 'pattern', 'y',
        'Persistence', 'HistGBM', 'trace', 'scenario', 'has_lte', 'has_nr',
        'group_id', 'physical_unit',
    ]
    combined = pd.concat([f[keep_cols] for f in frames], ignore_index=True)
    combined['domain'] = 'untouched_heldout'
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_DIR / 'untouched_opportunities.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
    return combined


if __name__ == '__main__':
    df = build_all()
    print(df.groupby(['cohort', 'partition']).agg(rows=('id', 'count'), dates=('date', 'nunique'), y_valid=('y', lambda s: int(s.notna().sum()))))
