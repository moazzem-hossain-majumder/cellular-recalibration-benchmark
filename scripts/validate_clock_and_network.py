"""Outcome-independent clock replay in Rome and chronological external evaluation in Norway."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.loader import clean_numeric
from src.evaluation.conformal import compute_conformal_quantile

OUT = ROOT / 'results/external_validation'
DIAG = ROOT / 'results/diagnostics'
BUS = ROOT / 'data/raw/oslo-bus'
URL = 'https://datasets.simula.no/downloads/hsdpa-tcp-logs/bus.ljansbakken-oslo/'


def evaluate(cal, test, method, cp, tp, setting):
    order = cal.sort_values(['time','trace']).index[:10]
    prefix = pd.Series(cp, index=cal.index).loc[order]
    assert len(prefix)==10 and cal.loc[order,'end'].max() <= test.time.min()
    q = compute_conformal_quantile(prefix.to_numpy()-cal.loc[order,'y'].to_numpy())
    y = test.y.to_numpy()
    rows = test[['trace','time','end','lag','y']].copy()
    rows = rows.assign(setting=setting,method=method,point=tp,lower=np.maximum(0,tp-q))
    v = float((rows.lower>y).mean())
    stats = dict(setting=setting,method=method,n=len(y),days=test.time.dt.date.nunique(),
                 prefix_n=len(prefix),q=q,violation=v,coverage=1-v,
                 point_violation=float(np.mean(np.asarray(tp)>y)),
                 point_supported=np.minimum(np.asarray(tp),y).sum()/y.sum(),
                 supported=np.minimum(rows.lower,y).sum()/y.sum(),mae=np.abs(tp-y).mean())
    return rows, stats


def clock_pairs(series, start, stop):
    # Index limits use the logger clock, even if the channel has no future value.
    ticks = pd.date_range(start.ceil('min'),stop.floor('min'),freq='min')
    last = series.dropna().resample('min').last() if series.notna().any() else series
    lag = last.reindex(ticks-pd.Timedelta(minutes=1)).to_numpy()
    y = last.reindex(ticks).to_numpy(dtype=float,copy=True)
    end = ticks + pd.Timedelta(minutes=1)
    y[end>stop] = np.nan
    return pd.DataFrame(dict(time=ticks,end=end,lag=lag,y=y)).dropna(subset=['lag'])


def rome():
    files = sorted((ROOT/'data/extracted/14073311').rglob('Ookla Speedtests/*Italy/*.csv'))
    assert len(files)==43
    rows = []
    for file in files:
        frame = pd.read_csv(file,sep=';',low_memory=False)
        frame.columns = frame.columns.str.strip()
        time = pd.to_datetime(frame.Day+' '+frame['Timestamp [dd.mm.yyyy,hh:mm:ss.ss]'],
                              format='%d.%m.%Y %H:%M:%S.%f',errors='raise')
        for i in (1,2):
            col, = [c for c in frame if 'Mean Netw. DL' in c and f': [{i}]' in c]
            rate = clean_numeric(frame[col]) * (1 if '[MBit/s]' in col else .001)
            series = pd.Series(rate.where(rate>=0).to_numpy(),index=time).sort_index()
            pairs = clock_pairs(series,time.min(),time.max())
            rows.append(pairs.assign(op=i,trace=file.name))
    data = pd.concat(rows,ignore_index=True)
    partitions = json.loads((DIAG/'split_summary.json').read_text())
    predictions, summary, issued = [], [], []
    for i,reg in [(1,'E1'),(2,'E3')]:
        part, = [p['partitions'] for name,p in partitions.items() if name.startswith(reg)]
        op = data[data.op==i]
        def select(key):
            dates = pd.to_datetime(part[key]['dates'],dayfirst=True).date
            return op[op.time.dt.date.isin(dates)]
        cal,test = select('target_calib_pool'),select('target_test')
        valid = test.dropna(subset=['y'])
        pool = cal.dropna(subset=['y'])
        forecasts,stats = evaluate(pool,valid,'Persistence',pool.lag,valid.lag,reg)
        predictions.append(forecasts)
        issued.append(test.assign(setting=reg,point=test.lag,lower=np.maximum(0,test.lag-stats['q'])))
        summary.append(dict(**stats,issued=len(test),unscored=len(test)-len(valid)))
    pd.concat(predictions).to_csv(DIAG/'clock_forecasts.csv',index=False)
    pd.concat(issued).to_csv(DIAG/'clock_issued.csv',index=False)
    (DIAG/'prediction_time_validity.json').write_text(json.dumps(summary,indent=2))


def norway():
    manifest = json.loads((OUT/'dataset_manifest.json').read_text())
    BUS.mkdir(parents=True,exist_ok=True)
    rows = []
    for name,digest in manifest['norway_files'].items():
        path = BUS/name
        if not path.exists():
            subprocess.run(['curl','-fsSL','--retry','2',URL+name,'-o',str(path)],check=True)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError(name)
        frame = pd.read_csv(path,sep=r'\s+',header=None,names=['unix','ms','lat','lon','bytes','elapsed'])
        frame = frame.sort_values('ms',kind='stable')
        # At completion of interval i, forecast the immediately following interval.
        rate = (.008*frame.bytes/frame.elapsed).where((frame.bytes>=0)&(frame.elapsed>0))
        time = pd.to_datetime(frame.unix,unit='s',utc=True)
        contiguous = frame.ms.diff().eq(frame.elapsed)
        rows.append(pd.DataFrame(dict(trace=name,time=time,end=time.shift(-1),lag=rate,
                                      lag2=rate.shift(),y=rate.shift(-1))).where(
                                          contiguous & contiguous.shift(-1,fill_value=False)).dropna())
    data = pd.concat(rows,ignore_index=True).sort_values(['time','trace'])
    dates = sorted(data.time.dt.date.unique())
    a,b = len(dates)//2,3*len(dates)//4
    train,cal,test = [data[data.time.dt.date.isin(ds)] for ds in [dates[:a],dates[a:b],dates[b:]]]
    assert train.end.max() <= cal.time.min() and cal.end.max() <= test.time.min()
    features = ['lag','lag2']
    tree = HistGradientBoostingRegressor(max_iter=100,max_depth=5,learning_rate=.05,random_state=42)
    tree.fit(train[features],train.y)
    methods = [('Persistence',cal.lag,test.lag),('HistGBM',tree.predict(cal[features]),tree.predict(test[features]))]
    results, predictions = [], []
    for method,cp,tp in methods:
        forecasts,stats = evaluate(cal,test,method,cp,tp,'Norway')
        results.append(stats)
        predictions.append(forecasts)
    pd.concat(predictions).to_csv(OUT/'norway_forecasts.csv',index=False)
    pd.DataFrame(results).to_csv(OUT/'norway_metrics.csv',index=False)
    (OUT/'norway_split.json').write_text(json.dumps(dict(train=list(map(str,dates[:a])),
        calibration=list(map(str,dates[a:b])),test=list(map(str,dates[b:])),
        traces=int(data.trace.nunique()),train_rows=len(train),calibration_rows=len(cal),test_rows=len(test)),indent=2))


if __name__=='__main__':
    rome()
    norway()
