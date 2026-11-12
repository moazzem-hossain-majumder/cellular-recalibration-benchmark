"""Irish chronological extension using measured signal availability before forward filling."""
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation.conformal import compute_conformal_quantile

def main():
    out = ROOT/'results/external_validation'
    raw = pd.read_parquet(ROOT/'data/raw/sirhan-external-work/consolidated.parquet')
    raw = raw.sort_values(['trace_id','row_in_trace'])
    raw['time'] = pd.to_datetime(raw.Timestamp,format='%Y.%m.%d_%H.%M.%S')
    raw['pattern'] = 2*raw.RSRP.notna().astype(int)+raw.NRxRSRP.notna().astype(int)
    by = raw.groupby('trace_id')
    raw['point'] = by.DL_Mbps.shift()
    raw['y'] = by.DL_Mbps.shift(-1)
    raw['end'] = by.time.shift(-1)
    # At forecast time the current signal is available; the target must be later.
    rows = raw[(by.time.shift()<raw.time) & (raw.time<raw.end)].dropna(subset=['point','y'])
    assert raw.groupby('trace_id').time.apply(lambda x:x.dt.date.nunique()).max()==1
    dates = sorted(rows.time.dt.date.unique())
    cut = dates[round(.4*len(dates))]
    pool = rows[rows.time.dt.date<cut].sort_values(['time','trace_id','row_in_trace'])
    test = rows[rows.time.dt.date>=cut].copy()
    assert pool.end.max()<test.time.min()
    records,forecasts = [],[]
    for k in [10,len(pool)]:
        cal = pool.iloc[:k]
        errors = cal.point-cal.y
        pooled = compute_conformal_quantile(errors.to_numpy())
        thresholds = {int(g):compute_conformal_quantile(errors.loc[idx].to_numpy())
                      for g,idx in cal.groupby('pattern').groups.items() if len(idx)>=9}
        for method in ['Global','Grouped']:
            offsets = test.pattern.map(thresholds).fillna(pooled) if method=='Grouped' else pooled
            lower = np.maximum(0,test.point-offsets)
            v = float((lower>test.y).mean())
            records.append(dict(k=k,method=method,n=len(test),test_days=test.time.dt.date.nunique(),
                coverage=1-v,violation=v,supported=np.minimum(lower,test.y).sum()/test.y.sum(),
                mae=(test.point-test.y).abs().mean(),group_rows=int(test.pattern.isin(thresholds).sum()) if method=='Grouped' else 0,
                cal_counts=cal.pattern.value_counts().to_dict(),test_counts=test.pattern.value_counts().to_dict()))
            forecasts.append(test[['trace_id','row_in_trace','time','pattern','point','y']].assign(k=k,method=method,lower=lower))
    frame = pd.concat(forecasts)
    frame.to_csv(out/'irish_group_forecasts.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    frame['date'] = frame.time.dt.date
    frame['violated'] = frame.lower>frame.y
    frame['delivered'] = np.minimum(frame.lower,frame.y)
    days = frame.groupby(['k','method','date']).agg(n=('y','size'),v=('violated','sum'),
                                                    supported=('delivered','sum'),observed=('y','sum'))
    omitted = days.groupby(level=[0,1]).transform('sum')-days
    days['omit_v'] = omitted.v/omitted.n
    days['omit_u'] = omitted.supported/omitted.observed
    days.to_csv(out/'irish_group_dates.csv')
    (out/'irish_group_validation.json').write_text(json.dumps(records,indent=2))

if __name__=='__main__':
    main()
