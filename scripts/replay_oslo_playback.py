"""Replay a serial two-second video client under independently recorded service."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.validate_clock_and_network import BUS,URL,OUT,route_pairs
from src.evaluation.conformal import compute_conformal_quantile

LADDER=np.array([.15,.3,.75,1.5,3.])
CUTOFF=pd.Timestamp('2011-01-30',tz='UTC')


def playback(seconds,capacity,offers,segment_s=2.,request_delay_s=0.):
    """Service is in Mbit and seconds. Two initial observations warm up all policies."""
    t=np.r_[0,np.cumsum(seconds)]
    service=np.r_[0,np.cumsum(capacity*seconds)]
    clock=t[2]
    origin=clock
    buffer=stalled=sent=0.
    completed=0
    startup=np.nan
    partial=0.
    while clock<t[-1]:
        i=min(np.searchsorted(t,clock,side='right')-1,len(capacity)-1)
        rate=LADDER[max(0,np.searchsorted(LADDER,offers[i-1],side='right')-1)]
        request_start=min(clock+request_delay_s,t[-1])
        if request_start==t[-1]:
            if completed:
                stalled+=max(0,t[-1]-clock-buffer)
            break
        i=min(np.searchsorted(t,request_start,side='right')-1,len(capacity)-1)
        used=service[i]+(request_start-t[i])*capacity[i]
        needed=used+segment_s*rate
        j=np.searchsorted(service,needed,side='left')
        finished=j<len(service)
        end=t[j-1]+(needed-service[j-1])/capacity[j-1] if finished else t[-1]
        end=min(end,t[-1])
        duration=end-clock
        if completed:
            stalled+=max(0,duration-buffer)
            buffer=max(0,buffer-duration)
        if not finished:
            partial=max(0,service[-1]-used)*125000
            break
        if not completed:
            startup=end-origin
        completed+=1
        sent+=segment_s*rate
        buffer+=segment_s
        clock=end
    post=t[-1]-origin-startup
    return dict(segments=completed,startup_s=startup,stall_s=stalled,post_start_s=post,
                duration_s=t[-1]-origin,stall_fraction=stalled/post if post>0 else np.nan,
                media_mbit=sent,mean_bitrate=sent/(segment_s*completed) if completed else np.nan,
                unfinished_bytes=partial)


def run(sensitivity=False):
    bus=route_pairs(BUS,URL,json.loads((OUT/'dataset_manifest.json').read_text())['norway_files'])
    split=pd.Timestamp('2010-10-01',tz='UTC')
    train=bus[bus.end<split]
    cal=bus[(bus.time>=split)&(bus.end<CUTOFF)].head(10)
    assert len(cal)==10 and train.end.max()<cal.time.min()
    tree=HistGradientBoostingRegressor(max_iter=100,max_depth=5,learning_rate=.05,random_state=42)
    features=['lag','lag2']
    tree.fit(train[features],train.y)
    offsets={k:compute_conformal_quantile(p-cal.y) for k,p in
             [('Tree',tree.predict(cal[features])),('Persistence',cal.lag)]}
    pins=json.loads((ROOT/'data/metadata/oslo_playback_sources.json').read_text(encoding='utf-8-sig'))
    rows=[]; inventory=[]
    for f in pins:
        path=ROOT/'data/raw/oslo-playback'/f['route']/f['name']
        if not path.exists():
            path.parent.mkdir(exist_ok=True,parents=True)
            subprocess.run(['curl','-fsSL','--retry','2',f['url'],'-o',str(path)],check=True)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=f['sha256']:
            raise ValueError(path)
        d=pd.read_csv(path,sep=r'\s+',header=None,names=['unix','ms','lat','lon','bytes','elapsed'])
        date=pd.Timestamp(d.unix.iloc[0],unit='s',tz='UTC')
        used=date>=CUTOFF
        inventory.append(dict(route=f['route'],trace=f['name'],date=str(date.date()),eligible=used,intervals=len(d)))
        if not used:
            continue
        valid=(d.bytes>=0)&(d.elapsed>0)
        groups=(~valid | ~valid.shift(fill_value=False) | d.ms.diff().ne(d.elapsed)).cumsum()
        for block,b in d[valid].groupby(groups[valid]):
            if len(b)<3:
                continue
            rate=(.008*b.bytes/b.elapsed).to_numpy()
            points=tree.predict(pd.DataFrame(dict(lag=rate,lag2=np.r_[rate[0],rate[:-1]])))
            policies={'Minimum':np.full(len(b),LADDER[0]),'Tree':points,'Persistence':rate,
                      'TreeLower':np.maximum(0,points-offsets['Tree']),
                      'PersistenceLower':np.maximum(0,rate-offsets['Persistence'])}
            settings=[(2.,0.)] if not sensitivity else [(duration,delay) for duration in [1.,2.,4.] for delay in [0.,.1,.3]]
            for policy,offers in policies.items():
                for duration,delay in settings:
                    rows.append(dict(route=f['route'],trace=f['name'],date=str(date.date()),block=block,policy=policy,
                                     **({'segment_s':duration,'request_delay_s':delay} if sensitivity else {}),
                                     **playback(b.elapsed.to_numpy()/1000,rate,offers,duration,delay)))
    rows=pd.DataFrame(rows)
    if sensitivity:
        rows.to_csv(OUT/'playback_sensitivity.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        return
    rows.to_csv(OUT/'playback_runs.csv',index=False)
    pd.DataFrame(inventory).to_csv(OUT/'playback_inventory.csv',index=False)
    # Zero-completion blocks are reported separately and contribute no post-start exposure.
    daily=rows.groupby(['route','date','policy']).agg(stall_s=('stall_s','sum'),post_s=('post_start_s','sum'),
        segments=('segments','sum'),media_mbit=('media_mbit','sum'),blocks=('block','size'),
        no_completion=('segments',lambda s:(s==0).sum()),startup_mean_s=('startup_s','mean')).reset_index()
    daily['stall_fraction']=daily.stall_s/daily.post_s.replace(0,np.nan)
    daily['mean_bitrate']=daily.media_mbit/(2*daily.segments.replace(0,np.nan))
    daily.to_csv(OUT/'playback_dates.csv',index=False)


if __name__=='__main__':
    run(sensitivity='--sensitivity' in sys.argv)
