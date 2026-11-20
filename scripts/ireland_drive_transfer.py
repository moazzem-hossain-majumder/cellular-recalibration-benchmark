"""Clock-based frozen Rome model transfer to Irish active-download driving traces."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.clock_frontier import metrics
from scripts.validate_clock_and_network import OUT
from src.data.loader import extract_sessions_8224890,load_raw_8224890
from src.data.splits import create_experiment_splits
from src.models.baselines import HistGradientBoostingThroughputPredictor


def main():
    raw=pd.read_parquet(ROOT/'data/raw/sirhan-external-work/consolidated.parquet').sort_values(['trace_id','row_in_trace'])
    raw['time']=pd.to_datetime(raw.Timestamp,format='%Y.%m.%d_%H.%M.%S')
    g=raw.groupby('trace_id')
    eligible=(g.time.shift()<raw.time)&(raw.time<g.time.shift(-1))&g.DL_Mbps.shift().notna()&g.DL_Mbps.shift(-1).notna()
    dates=sorted(raw.loc[eligible,'time'].dt.date.unique())
    cutoff=dates[round(.4*len(dates))]
    rows=[]
    for trace,b in raw[(raw.app=='Download')&(raw.mobility=='Driving')].groupby('trace_id'):
        b=b.set_index('time').sort_index(kind='stable')
        for t in pd.date_range(b.index.min().ceil('min'),b.index.max(),freq='min'):
            past=b[(b.index>=t-pd.Timedelta('1min'))&(b.index<t)]
            end=t+pd.Timedelta('1min')
            future=b[(b.index>=t)&(b.index<end)]
            lag=past.DL_Mbps.where(past.DL_Mbps>=0).dropna()
            y=future.DL_Mbps.where(future.DL_Mbps>=0).dropna()
            row=dict(trace=trace,date=t.date(),issue=t,end=end,scenario='OD',y_lag1=lag.iloc[-1] if len(lag) else np.nan,
                y=y.iloc[-1] if len(y) and end<=b.index.max() else np.nan,
                lag_age_s=(t-lag.index[-1]).total_seconds() if len(lag) else np.nan,
                prev_duration_s=(lag.index[-1]-lag.index[0]).total_seconds() if len(lag) else np.nan,
                sinr=np.nan,ss_sinr=np.nan)
            for src,dest in [('RSRP','rsrp'),('RSRQ','rsrq'),('NRxRSRP','ss_rsrp'),('NRxRSRQ','ss_rsrq')]:
                values=past[src].dropna()
                row[dest]=values.iloc[-1] if len(values) else np.nan
            rows.append(row)
    ticks=pd.DataFrame(rows).sort_values(['issue','trace'])
    ticks['has_lte']=ticks.rsrp.notna().astype(int)
    ticks['has_nr']=ticks.ss_rsrp.notna().astype(int)
    ticks['group_id']=2*ticks.has_lte+ticks.has_nr
    issued=ticks.y_lag1.notna()
    _,early=extract_sessions_8224890(load_raw_8224890())
    src=early[early.operator=='Op1']
    train=create_experiment_splits(src,src,'within_domain',[10]).train
    assert len(train)==57
    model=HistGradientBoostingThroughputPredictor().fit(train,train.target_y.to_numpy())
    ticks.loc[issued,'Tree']=model.predict(ticks[issued])
    ticks['Persistence']=ticks.y_lag1
    if ticks.loc[issued & ticks.y.notna() & (ticks.date<cutoff)].empty:
        cutoff=sorted(ticks.date.unique())[2]
    cal=ticks[(ticks.date<cutoff)&issued&ticks.y.notna()].head(10)
    test=ticks.date>=cutoff
    assert len(cal)==10 and cal.end.max()<ticks.loc[test,'issue'].min()
    ticks['partition']=np.where(test,'test','unused')
    ticks.loc[cal.index,'partition']='cal'
    rows=[]
    for name in ['Tree','Persistence']:
        q=(cal[name]-cal.y).max()
        ticks[name+'_lower']=(ticks[name]-q).clip(lower=0)
        for day in ['all',*sorted(ticks.loc[test,'date'].unique())]:
            group=ticks[test] if day=='all' else ticks[test&(ticks.date==day)]
            part=group[group.y_lag1.notna()]
            if len(part):
                rows.append(dict(model=name,date=day,offset=q,ticks=len(group),traces=group.trace.nunique(),
                            **metrics(part.y,part[name],part[name+'_lower'])))
    ticks.to_csv(OUT/'ireland_drive_ticks.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'ireland_drive_summary.csv',index=False)


if __name__=='__main__':
    main()

