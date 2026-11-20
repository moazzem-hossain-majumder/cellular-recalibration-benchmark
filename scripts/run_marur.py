"""Run the predeclared controller family on a shared clock and external ledgers."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.clock_frontier import load_ticks,metrics
from src.evaluation.marur import replay

OUT=ROOT/'results/marur'


def seconds(values):
    return pd.to_datetime(values,utc=True).astype('datetime64[ns, UTC]').astype('int64')/1e9


def cohorts():
    existing=pd.read_csv(ROOT/'results/clock_histgbm/ticks.csv')
    full=load_ticks(include_ineligible=True)
    full['time']=full.time.astype(str)
    merged=full.merge(existing[['regime','trace','time','HistGBM','partition']],
                      on=['regime','trace','time'],how='left',validate='one_to_one')
    for regime,g in merged.groupby('regime'):
        old=existing[existing.regime==regime]
        caldates=set(old.loc[old.partition=='calibration','date'])
        testdates=set(old.loc[old.partition=='test','date'])
        g=g[g.date.astype(str).isin(caldates|testdates)].copy()
        g['partition']=np.where(g.date.astype(str).isin(testdates),'test','unused')
        g['issue']=seconds(g.time)
        g['ready']=seconds(g.end)
        g['pattern']=g.group_id
        g=g.sort_values(['issue','trace']).reset_index(drop=True)
        g['id']=regime+'-'+g.index.astype(str)
        initial=g[(g.partition!='test') & g.y.notna() & g.lag.notna()].head(10)
        g.loc[initial.index,'partition']='cal'
        yield regime,g,{'HistGBM':'HistGBM','Persistence':'Persistence'}
    for name,file in [('US','drive3_forecasts.csv'),('Ireland','ireland_drive_ticks.csv')]:
        full=pd.read_csv(ROOT/'results/external_validation'/file)
        if name=='US':
            full['ready']=np.minimum(full.end,full.issue+60)
        else:
            full['issue']=seconds(full.issue)
            full['ready']=seconds(full.end)
            full['carrier']='Ireland'
        full['pattern']=full.group_id
        full['id']=name+'-'+full.index.astype(str)
        for carrier,g in full.groupby('carrier'):
            yield carrier,g,{'HistGBM':'Tree','Persistence':'Persistence'}


def aggregate(ledger,responses,initial=10):
    part=ledger[ledger.eligible]
    stats=metrics(part.y,part.point,part.lower) if len(part) else dict(
        issued=0,scored=0,unavailable=0,violations=0,unresolved=0,positive=0,positive_rate=np.nan,
        positive_scored=0,positive_covered=0,v_given_positive=np.nan,positive_low=np.nan,
        positive_high=np.nan,observed_sum=0.,delivered_sum=0.,v=np.nan,coverage=np.nan,
        lo=np.nan,hi=np.nan,u=np.nan,mae=np.nan)
    errors=(part.point-part.y).dropna()
    stats.update(scheduled=len(ledger),eligible=len(part),issued_point=len(part),abstained=int((ledger.lower==0).sum()),
        commitment_coverage=float((ledger.lower>0).mean()),positive_dates=int(ledger.loc[ledger.lower>0,'date'].nunique()),
        dates=int(ledger.date.nunique()),rmse=float(np.sqrt((errors**2).mean())),
        median_absolute_error=float(errors.abs().median()),attempts=initial+int(ledger['query'].sum()),
        response_labels=int(responses.observed.sum()) if len(responses) else 0,
        missing_responses=int((~responses.observed).sum()) if len(responses) else 0,
        recalibrations=int(responses.admitted.sum()) if len(responses) else 0,
        effective_updates=int(ledger.updates.max()) if len(ledger) else 0)
    return stats


def main():
    start=datetime.now(timezone.utc).isoformat()
    config=json.loads((ROOT/'configs/marur.json').read_text())
    OUT.mkdir(parents=True,exist_ok=True)
    summaries=[];ledgers=[];feedback=[];date_rows=[];inputs=[]
    for cohort,frame,models in cohorts():
        frame['date']=frame.date.astype(str)
        inputs.append(frame.assign(cohort=cohort))
        for model,column in models.items():
            data=frame.assign(point=frame[column])
            initial=data[data.partition=='cal']
            stream=data[data.partition=='test']
            for scenario in config['scenarios']:
                for budget in config['total_attempt_budgets']:
                    for policy in config['policies']:
                        tick=time.perf_counter()
                        ledger,responses=replay(initial,stream,policy,budget,config,scenario)
                        meta=dict(cohort=cohort,model=model,scenario=scenario,budget=budget,policy=policy)
                        summaries.append(dict(**meta,**aggregate(ledger,responses),seconds=time.perf_counter()-tick))
                        ledgers.append(ledger.assign(**meta))
                        if len(responses):
                            feedback.append(responses.assign(**meta))
                        for date,day in ledger.groupby('date'):
                            r=responses[responses.id.isin(day.id)] if len(responses) else responses
                            date_rows.append(dict(**meta,date=date,**aggregate(day,r,initial=0)))
    pd.concat(inputs).to_csv(OUT/'opportunities.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame(summaries).to_csv(OUT/'summary.csv',index=False)
    pd.concat(ledgers).to_csv(OUT/'actions.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.concat(feedback).to_csv(OUT/'responses.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame(date_rows).to_csv(OUT/'dates.csv',index=False)
    summary=pd.DataFrame(summaries)
    daily=pd.DataFrame(date_rows)
    comparison_keys=['cohort','model','scenario','budget']
    baseline=summary[summary.policy=='Periodic'].set_index(comparison_keys)
    candidate=summary[summary.policy=='MARUR'].set_index(comparison_keys)
    columns=['u','hi','positive_high','attempts']
    (candidate[columns]-baseline[columns]).add_suffix('_delta').reset_index().to_csv(
        OUT/'paired_policy_contrasts.csv',index=False)
    day_keys=comparison_keys+['date']
    baseline=daily[daily.policy=='Periodic'].set_index(day_keys)
    candidate=daily[daily.policy=='MARUR'].set_index(day_keys)
    columns=['u','hi','positive_high','commitment_coverage']
    (candidate[columns]-baseline[columns]).add_suffix('_delta').reset_index().to_csv(
        OUT/'paired_date_contrasts.csv',index=False)
    plot(summary)
    receipt=dict(start_utc=start,end_utc=datetime.now(timezone.utc).isoformat(),
                 command=['python','scripts/run_marur.py'],config=config,scope='Existing archived clock cohorts',
                 sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.csv*')})
    (OUT/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n')


def plot(summary):
    cohorts=list(summary.cohort.unique())
    fig,axes=plt.subplots(2,3,figsize=(10,6),layout='constrained')
    for cohort,ax in zip(cohorts,axes.flat):
        d=summary[(summary.cohort==cohort)&(summary.model=='HistGBM')&(summary.scenario=='Recorded')]
        for policy in ['Frozen','Periodic','Early','ACI','MARUR']:
            rows=d[d.policy==policy].sort_values('budget')
            ax.errorbar(100*rows.u,100*rows.lo,yerr=np.array([np.zeros(len(rows)),100*(rows.hi-rows.lo)]),
                        marker='o',markersize=4,linewidth=1,label=policy,capsize=2)
        ax.axhline(10,ls=':',color='gray')
        ax.set(title=cohort,xlabel='Supported measured throughput (%)',ylabel='All-issued violation bounds (%)')
    axes[0,0].legend(fontsize=6)
    for ext in ['png','pdf']:
        fig.savefig(ROOT/f'results/figures/fig8_marur.{ext}',dpi=300)
    plt.close(fig)


if __name__=='__main__':
    main()
