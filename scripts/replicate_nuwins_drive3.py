"""Replay the locked Rome tree on the three US Drive 3 carrier cohorts."""
import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clock_frontier import metrics
from scripts.validate_nuwins_drive2 import RAW, META, RATE, acquire
from src.data.loader import extract_sessions_8224890, load_raw_8224890
from src.data.splits import create_experiment_splits
from src.models.baselines import HistGradientBoostingThroughputPredictor

OUT = ROOT/'results/external_validation'
CARRIERS = {'atnt':'AT&T','tmobile':'T-Mobile','verizon':'Verizon'}
RADIO = dict(rsrp='LTE KPI PCell Serving RSRP[dBm]',rsrq='LTE KPI PCell Serving RSRQ[dB]',
             sinr='LTE KPI PCell SINR[dB]',ss_rsrp='5G KPI PCell RF Serving SS-RSRP [dBm]',
             ss_rsrq='5G KPI PCell RF Serving SS-RSRQ [dB]',ss_sinr='5G KPI PCell RF Serving SS-SINR [dB]')


def load_day(processed,raw):
    frame = pd.read_csv(processed,usecols=['TIME_STAMP','GPS Time',RATE]).dropna(subset=['GPS Time'])
    frame['key'] = (frame.TIME_STAMP*1e6).round().astype('int64')
    if not raw.exists():
        if raw.name != 'verizon_day_4.csv':
            raise FileNotFoundError(raw)
        return frame.assign(**{k:np.nan for k in RADIO}),0
    radio = pd.read_csv(raw,usecols=lambda c:c in ['TIME_STAMP',RATE,*RADIO.values()],low_memory=False)
    # Join on the device timestamp of the same record. GPS time for that record comes
    # directly from the publisher's processed shard. Only unique clock mappings enter.
    local = pd.to_datetime(radio.TIME_STAMP,format='mixed',errors='coerce')
    naive = local.dt.tz_localize('UTC').astype('datetime64[us, UTC]').astype('int64')
    # Logger epoch conversion is a whole-hour displacement. Establish it from
    # timestamps alone, requiring a unique best alignment across plausible US zones.
    device_keys = pd.Index(frame.key.unique())
    candidates = {h:np.count_nonzero((naive+h*3600_000000).isin(device_keys)) for h in range(3,9)}
    hour = max(candidates,key=candidates.get)
    if candidates[hour]==0 or list(candidates.values()).count(candidates[hour])!=1:
        raise ValueError(f'Ambiguous logger alignment: {raw.name} {candidates}')
    radio['key'] = naive+hour*3600_000000
    radio = radio.rename(columns={**{v:k for k,v in RADIO.items()}, RATE:'raw_rate'}).reindex(columns=['key','raw_rate',*RADIO])
    radio[list(RADIO)] = radio[list(RADIO)].apply(pd.to_numeric,errors='coerce')
    # Duplicate device timestamps can represent different measurements. Omit
    # ambiguous rows from the radio join, retaining every scheduled opportunity.
    unique = radio.loc[~radio.key.duplicated(keep=False)]
    clock_counts=frame.groupby('key')['GPS Time'].nunique()
    unique=unique[~unique.key.isin(clock_counts[clock_counts>1].index)]
    merged = frame.merge(unique,on='key',how='left',validate='many_to_one',indicator=True)
    comparable = merged.dropna(subset=['raw_rate',RATE])
    if len(comparable)==0 or not np.allclose(comparable.raw_rate,comparable[RATE],atol=1e-5,rtol=1e-6):
        raise ValueError(f'Raw and processed same-record rates disagree: {raw.name}')
    return merged, int((merged._merge=='both').sum())


def opportunities(frame,intervals,dates):
    frame=frame.sort_values(['GPS Time','TIME_STAMP'],kind='stable').set_index('GPS Time')
    records=[]
    for start,end in sorted(intervals):
        day=pd.Timestamp(start,unit='s',tz='UTC').date().isoformat()
        if day not in dates:
            continue
        window=frame.loc[start:end]
        rates=window[RATE].where(np.isfinite(window[RATE]) & (window[RATE]>=0)).dropna()
        for tick in range(math.ceil(start/60)*60,math.floor(end)+1,60):
            prior=rates[(rates.index>=tick-60)&(rates.index<tick)]
            future=rates[(rates.index>=tick)&(rates.index<tick+60)]
            recent=window[(window.index>=tick-60)&(window.index<tick)]
            row=dict(date=pd.Timestamp(tick,unit='s',tz='UTC').date().isoformat(),start=start,end=end,issue=tick,y=future.iloc[-1] if len(future) else np.nan,
                     lag_time=prior.index[-1] if len(prior) else np.nan,
                     target_time=future.index[-1] if len(future) else np.nan,
                     y_lag1=prior.iloc[-1] if len(prior) else np.nan,
                     prev_duration_s=prior.index[-1]-prior.index[0] if len(prior) else np.nan,
                     lag_age_s=tick-prior.index[-1] if len(prior) else np.nan,scenario='OD')
            for k in RADIO:
                readings=recent[k].dropna()
                row[k]=readings.iloc[-1] if len(readings) else np.nan
            records.append(row)
    return pd.DataFrame(records).sort_values('issue').reset_index(drop=True)


def main():
    from fetch_nuwins_drive3 import main as fetch
    fetch()
    acquire()  # authenticates the static interval roster before deserialization
    intervals=pickle.loads((RAW/META).read_bytes())
    _,early=extract_sessions_8224890(load_raw_8224890())
    source=early[early.operator=='Op1']
    train=create_experiment_splits(source,source,'within_domain',[10]).train
    assert len(train)==57
    tree=HistGradientBoostingThroughputPredictor().fit(train,train.target_y.to_numpy())
    manifest=json.loads((ROOT/'data/metadata/nuwins_drive3_inputs.json').read_text(encoding='utf-8-sig'))
    ledgers=[]
    summary=[]
    alignment=[]
    for short,name in CARRIERS.items():
        frames=[]
        for item in manifest:
            path=RAW/item['path']
            if path.parent.name!='DL' or path.parent.parent.name!=short:
                continue
            raw=RAW/'datasets/raw_files/xcal_raw/drive_trip_3'/path.name.replace('_d3_dl','')
            frame,matched=load_day(path,raw)
            frames.append(frame)
            alignment.append(dict(carrier=name,shard=path.name,raw_present=raw.exists(),rows=len(frame),matched=matched))
        frame=pd.concat(frames)
        dates=sorted(set(pd.to_datetime(frame['GPS Time'],unit='s',utc=True).dt.date.astype(str)))
        ticks=opportunities(frame,intervals[name],dates)
        ticks['carrier']=name
        ticks['has_lte']=ticks.rsrp.notna().astype(int)
        ticks['has_nr']=ticks.ss_rsrp.notna().astype(int)
        ticks['group_id']=2*ticks.has_lte+ticks.has_nr
        issued=ticks.y_lag1.notna()
        ticks['Persistence']=ticks.y_lag1
        ticks.loc[issued,'Tree']=tree.predict(ticks[issued])
        masked=ticks[issued].assign(ss_rsrp=np.nan,ss_rsrq=np.nan,ss_sinr=np.nan,has_nr=0)
        masked['group_id']=2*masked.has_lte
        ticks.loc[issued,'Tree_noNR']=tree.predict(masked)
        cal=ticks[ticks.date.isin(dates[:2]) & issued & ticks.y.notna()].head(10)
        assert len(cal)==10 and cal.target_time.max()<ticks[ticks.date.isin(dates[2:])].issue.min()
        ticks['partition']=np.where(ticks.date.isin(dates[2:]),'test','unused')
        ticks.loc[cal.index,'partition']='cal'
        for model in ['Persistence','Tree','Tree_noNR']:
            ref='Tree' if model=='Tree_noNR' else model
            offset=(cal[ref]-cal.y).max()
            ticks[model+'_lower']=(ticks[model]-offset).clip(lower=0)
            test=ticks[ticks.partition=='test']
            for date in ['all',*dates[2:]]:
                subset=test if date=='all' else test[test.date==date]
                scored=subset[subset.y_lag1.notna()]
                row=dict(carrier=name,date=date,model=model,offset=offset,ticks=len(subset),issued=len(scored),
                         has_lte=scored.has_lte.sum(),has_nr=scored.has_nr.sum())
                if len(scored):
                    row.update(metrics(scored.y,scored[model],scored[model+'_lower']))
                summary.append(row)
        ledgers.append(ticks)
    paired=[]
    for ledger in ledgers:
        test=ledger[(ledger.partition=='test') & ledger.y_lag1.notna()]
        for date,day in test.groupby('date'):
            observed=day.dropna(subset=['y'])
            tree_bad=observed.Tree_lower>observed.y
            lag_bad=observed.Persistence_lower>observed.y
            paired.append(dict(carrier=day.carrier.iloc[0],date=date,issued=len(day),scored=len(observed),
                               both_violate=int((tree_bad & lag_bad).sum()),
                               tree_only=int((tree_bad & ~lag_bad).sum()),
                               persistence_only=int((~tree_bad & lag_bad).sum()),
                               neither_violates=int((~tree_bad & ~lag_bad).sum())))
    pd.DataFrame(paired).to_csv(OUT/'drive3_paired_dates.csv',index=False)
    pd.concat(ledgers).to_csv(OUT/'drive3_forecasts.csv',index=False)
    pd.DataFrame(summary).to_csv(OUT/'drive3_results.csv',index=False)
    pd.DataFrame(alignment).to_csv(OUT/'drive3_alignment.csv',index=False)


if __name__=='__main__':
    main()
