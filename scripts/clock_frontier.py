"""Reproduce the frozen Rome models, all target prefix sizes and delayed-feedback checks."""
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.validate_clock_and_network import clock_pairs
from src.data.loader import clean_numeric, extract_sessions_8224890, load_raw_8224890
from src.data.splits import create_experiment_splits
from src.models.baselines import HistGradientBoostingThroughputPredictor
from src.evaluation.conformal import compute_conformal_quantile as quantile

OUT = ROOT/'results/clock_histgbm'
RADIO = dict(rsrp='LTE UE_PCell_RSRP',rsrq='LTE UE_PCell_RSRQ',sinr='LTE UE_PCell_SINR',
             ss_rsrp='5G NR Carriers_SS-RSRP',ss_rsrq='5G NR Carriers_SS-RSRQ',ss_sinr='5G NR Carriers_SS-SINR')


def load_ticks():
    rows = []
    for file in sorted((ROOT/'data/extracted/14073311').rglob('Ookla Speedtests/*Italy/*.csv')):
        frame = pd.read_csv(file,sep=';',low_memory=False)
        frame.columns = frame.columns.str.strip()
        frame.index = pd.to_datetime(frame.Day+' '+frame['Timestamp [dd.mm.yyyy,hh:mm:ss.ss]'],format='%d.%m.%Y %H:%M:%S.%f')
        frame = frame.sort_index()
        for op,regime in [(1,'E1'),(2,'E3')]:
            def field(key):
                col = next((c for c in frame if key in c and f': [{op}]' in c),None)
                return (clean_numeric(frame[col]) if col else pd.Series(np.nan,index=frame.index)),col
            rate,col = field('Mean Netw. DL')
            rate = rate.where(rate>=0)*(1 if '[MBit/s]' in col else .001)
            pairs = clock_pairs(rate,frame.index.min(),frame.index.max()).set_index('time')
            prev = pairs.index-pd.Timedelta(minutes=1)
            times = rate.dropna().index.to_series().resample('min')
            tlast = times.last().reindex(prev)
            pairs['lag_age_s'] = (pairs.index-tlast.to_numpy()).total_seconds()
            pairs['prev_duration_s'] = (tlast-times.first().reindex(prev)).dt.total_seconds().to_numpy()
            for name,key in RADIO.items():
                pairs[name] = field(key)[0].resample('min').last().reindex(prev).to_numpy()
            # Alternative horizon: endpoint of the *second* minute after issuance.
            later = pairs.index+pd.Timedelta(minutes=1)
            pairs['y2'] = rate.resample('min').last().reindex(later).to_numpy()
            pairs.loc[later+pd.Timedelta(minutes=1)>frame.index.max(),'y2'] = np.nan
            rows.append(pairs.assign(regime=regime,trace=file.name,scenario='IS' if '_IS_' in file.name else 'OD' if '_OD_' in file.name else 'OW').reset_index())
    data = pd.concat(rows,ignore_index=True).sort_values(['time','trace','regime'])
    data['has_lte'] = data.rsrp.notna().astype(int)
    data['has_nr'] = data.ss_rsrp.notna().astype(int)
    data['group_id'] = 2*data.has_lte+data.has_nr
    return data.assign(y_lag1=data.lag,Persistence=data.lag,date=data.time.dt.date)


def metrics(y,point,lower):
    y,point,lower = map(np.asarray,(y,point,lower))
    valid = np.isfinite(y)
    v = int((lower>y).sum())
    unknown = int(((~valid)&(lower>0)).sum())
    total = np.nansum(y)
    return dict(issued=len(y),scored=int(valid.sum()),unavailable=int((~valid).sum()),violations=v,
                unresolved=unknown,positive=int((lower>0).sum()),observed_sum=total,
                delivered_sum=np.nansum(np.minimum(lower,y)),v=v/valid.sum() if valid.any() else np.nan,
                coverage=1-v/valid.sum() if valid.any() else np.nan,
                lo=v/len(y),hi=(v+unknown)/len(y),u=np.nansum(np.minimum(lower,y))/total if total else np.nan,
                mae=np.mean(abs(point[valid]-y[valid])) if valid.any() else np.nan)


def calibrate(cal,test,model,source_q,grouped):
    scores = (cal[model]-cal.y).to_numpy()
    q = quantile(scores) if len(cal)>=9 else source_q
    offsets = np.full(len(test),q)
    if grouped:
        for group in cal.group_id.unique():
            sub = scores[cal.group_id==group]
            if len(sub)>=9:
                offsets[test.group_id==group] = quantile(sub)
    return offsets,np.maximum(0,test[model].to_numpy()-offsets)


def run():
    OUT.mkdir(exist_ok=True,parents=True)
    _,early = extract_sessions_8224890(load_raw_8224890())
    src = early[early.operator=='Op1']
    dev = create_experiment_splits(src,src,'within_domain',[10])
    tree = HistGradientBoostingThroughputPredictor().fit(dev.train,dev.train.target_y.to_numpy())
    data = load_ticks()
    data['HistGBM'] = tree.predict(data)
    settings = json.loads((ROOT/'results/diagnostics/split_summary.json').read_text())
    curves,ledger,dates,stress,rolling = [],[],[],[],[]
    for reg,frame in data.groupby('regime'):
        split, = [s['partitions'] for name,s in settings.items() if name.startswith(reg)]
        testdates = pd.to_datetime(split['target_test']['dates'],dayfirst=True).date
        caldates = pd.to_datetime(split['target_calib_pool']['dates'],dayfirst=True).date
        frame = frame[frame.date.isin([*caldates,*testdates])]
        pool = frame[frame.date.isin(caldates)].dropna(subset=['y'])
        test = frame[frame.date.isin(testdates)]
        assert pool.end.max()<=test.time.min()
        data.loc[frame.index,'partition'] = np.where(frame.date.isin(testdates),'test','calibration')
        for model in ['Persistence','HistGBM']:
            source = dev.source_calib
            pred = source.y_lag1 if model=='Persistence' else tree.predict(source)
            sq = quantile(np.asarray(pred)-source.target_y.to_numpy())
            for policy in ['Global','Grouped']:
                for k in range(len(pool)+1):
                    q,lower = calibrate(pool.iloc[:k],test,model,sq,policy=='Grouped')
                    meta = dict(regime=reg,model=model,policy=policy,k=k)
                    curves.append(dict(**meta,q_min=q.min(),q_max=q.max(),source_q=sq,**metrics(test.y,test[model],lower)))
                    if k!=10:
                        continue
                    detail = test.assign(model=model,policy=policy,q=q,lower=lower,point=test[model])
                    ledger.append(detail)
                    for date,b in detail.groupby('date'):
                        dates.append(dict(**meta,date=date,**metrics(b.y,b.point,b.lower)))
                    for label,mask in dict(drop10=test.lag-test.y>=10,zero=test.y==0,noNR=test.has_nr==0,
                                           dual=test.group_id==3,shortSpan=test.prev_duration_s<=10,
                                           longSpan=test.prev_duration_s>=50).items():
                        if mask.any():
                            stress.append(dict(**meta,condition=label,**metrics(test.y[mask],test[model][mask],lower[mask])))
            # Recalibrate on consecutive dates. Each day uses only ten completed
            # prior outcomes. First/last prefixes have equal training-label counts.
            for date,b in test.groupby('date'):
                history = frame[(frame.end<=b.time.min()) & frame.y.notna()].sort_values(['end','trace'])
                for policy,cal in [('Frozen10',pool.iloc[:10]),('Latest10',history.tail(10))]:
                    _,lower = calibrate(cal,b,model,sq,False)
                    rolling.append(dict(regime=reg,date=date,model=model,policy=policy,used=len(cal),
                                        available=len(history),**metrics(b.y,b[model],lower)))
            # Same ten *initial* labels and same stream of subsequently observable feedback.
            # Update a signed-score offset by 1 Mbps times (violation - .10).
            q = quantile((pool[model]-pool.y).iloc[:10].to_numpy())
            pending = []
            updates = 0
            for tick,b in test.groupby('time',sort=True):
                ready = [v for end,v in pending if end<=tick]
                pending = [(end,v) for end,v in pending if end>tick]
                q += sum(ready)
                updates += len(ready)
                lower = np.maximum(0,b[model]-q)
                for end,y,l in zip(b.end,b.y,lower):
                    if pd.notna(y):
                        pending.append((end,float(l>y)-.10))
                rolling.append(dict(regime=reg,date=tick,model=model,policy='OffsetFeedback',used=10+updates,
                                    available=10+updates,**metrics(b.y,b[model],lower)))
            # Prespecified abstention rule and other-operator calibration on earlier dates.
            _,base = calibrate(pool.head(10),test,model,sq,False)
            stress.append(dict(regime=reg,model=model,policy='NoNRZero',k=10,condition='all',
                               **metrics(test.y,test[model],np.where(test.has_nr,base,0))))
            other = data[(data.regime!=reg)&(data.date.isin(caldates))&(data.end<=test.time.min())].dropna(subset=['y']).head(10)
            assert len(other)==10
            _,transferred = calibrate(other,test,model,sq,False)
            stress.append(dict(regime=reg,model=model,policy='OtherOperator',k=10,condition='all',
                               **metrics(test.y,test[model],transferred)))
            if model=='HistGBM':
                # Without a session start, an alternative mapping leaves duration unknown.
                cal = pool.head(10).assign(prev_duration_s=np.nan)
                tp = tree.predict(test.assign(prev_duration_s=np.nan))
                offset = quantile(tree.predict(cal)-cal.y.to_numpy())
                stress.append(dict(regime=reg,model=model,policy='DurationMissing',k=10,condition='all',
                                   **metrics(test.y,tp,np.maximum(0,tp-offset))))
            hpool = frame[~frame.date.isin(testdates)].dropna(subset=['y2']).head(10)
            q2 = quantile((hpool[model]-hpool.y2).to_numpy())
            stress.append(dict(regime=reg,model=model,policy='Global',k=10,condition='secondMinute',
                               **metrics(test.y2,test[model],np.maximum(0,test[model]-q2))))
    daily = pd.DataFrame(dates)
    totals = daily.groupby(['regime','model','policy'])[['violations','unresolved','issued','scored','observed_sum','delivered_sum']].transform('sum')
    omitted = totals-daily[totals.columns]
    daily['omit_v'] = omitted.violations/omitted.scored
    daily['omit_u'] = omitted.delivered_sum/omitted.observed_sum
    daily['omit_low'] = omitted.violations/omitted.issued
    daily['omit_high'] = (omitted.violations+omitted.unresolved)/omitted.issued
    curves = pd.DataFrame(curves)
    data['partition'] = data.partition.fillna('outside_original_dates')
    for name,frame in [('frontier',curves),('ticks',data),('issued_k10',pd.concat(ledger)),
                       ('per_date',daily),('stress',pd.DataFrame(stress)),('rolling',pd.DataFrame(rolling))]:
        frame.to_csv(OUT/(name+'.csv'),index=False)
    plot_frontier(curves)


def plot_frontier(curves):
    fig,axes = plt.subplots(1,2,figsize=(8,3.3),sharey=True,layout='constrained')
    envelopes = []
    for (reg,b),ax in zip(curves.groupby('regime'),axes):
        for (model,policy),d in b.groupby(['model','policy']):
            ordered = d.sort_values(['v','u','k'],ascending=[True,False,True]).drop_duplicates('v')
            efficient = ordered[ordered.u>ordered.u.cummax().shift(fill_value=-1)]
            envelopes.append(efficient)
            color = 'steelblue' if model=='HistGBM' else 'darkorange'
            ax.plot(100*efficient.u,100*efficient.v,color=color,alpha=.65,lw=.8,
                    ls='-' if policy=='Global' else ':')
            ax.scatter(100*d.u,100*d.v,s=10,alpha=.65,marker='o' if policy=='Global' else 'x',
                       color='steelblue' if model=='HistGBM' else 'darkorange',label=model+' '+policy)
        ax.axhline(10,color='grey',ls='--',lw=1)
        ax.set(title=reg,xlabel='Supported throughput on scored ticks (%)')
    axes[0].set_ylabel('Violations on scored ticks (%)')
    axes[1].legend(fontsize=7)
    for ext in ['png','pdf']:
        fig.savefig(ROOT/f'results/figures/fig7_clock_frontier.{ext}',dpi=300)
    plt.close(fig)
    pd.concat(envelopes).to_csv(OUT/'nondominated.csv',index=False)

if __name__=='__main__':
    run()
