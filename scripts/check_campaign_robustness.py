"""Equal-date sensitivity for frozen-model comparisons and playback assumptions."""
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/external_validation'


def main():
    rome=pd.read_csv(ROOT/'results/clock_histgbm/per_date.csv')
    rows=[]
    for r in rome[(rome.policy=='Global') & (rome.k==10)].itertuples():
        rows.append(dict(cohort=r.regime,date=r.date,model=r.model,issued=r.issued,scored=r.scored,
            positive=r.positive,positive_scored=r.positive_scored,errors=r.violations,unresolved=r.unresolved,
            support=r.delivered_sum,observed=r.observed_sum))
    for file in ['drive3_forecasts.csv','ireland_drive_ticks.csv']:
        d=pd.read_csv(OUT/file)
        d=d[(d.partition=='test') & d.y_lag1.notna()]
        if 'carrier' not in d:
            d['carrier']='Ireland'
        for (cohort,date),g in d.groupby(['carrier','date']):
            for model in ['Tree','Persistence']:
                lower=g[model+'_lower'];pos=lower>0
                rows.append(dict(cohort=cohort,date=date,model='HistGBM' if model=='Tree' else model,
                    issued=len(g),scored=g.y.count(),positive=pos.sum(),positive_scored=(pos & g.y.notna()).sum(),
                    errors=(lower>g.y).sum(),unresolved=(pos & g.y.isna()).sum(),
                    support=np.minimum(lower,g.y).sum(),observed=g.y.sum()))
    d=pd.DataFrame(rows)
    d['positive_risk']=d.errors/d.positive_scored.replace(0,np.nan)
    d['issued_low']=d.errors/d.issued
    d['issued_high']=(d.errors+d.unresolved)/d.issued
    d['utility']=d.support/d.observed.replace(0,np.nan)
    d.to_csv(OUT/'cross_campaign_dates.csv',index=False)
    summaries=[]
    for (cohort,model),g in d.groupby(['cohort','model']):
        for omitted in ['none',*g.date]:
            kept=g if omitted=='none' else g[g.date!=omitted]
            summaries.append(dict(cohort=cohort,model=model,omit_date=omitted,dates=len(kept),
                positive_dates=int((kept.positive>0).sum()),
                equal_date_low=kept.issued_low.mean(),equal_date_high=kept.issued_high.mean(),
                equal_date_utility=kept.utility.mean(),pooled_low=kept.errors.sum()/kept.issued.sum()))
    pd.DataFrame(summaries).to_csv(OUT/'cross_campaign_date_sensitivity.csv',index=False)
    d=pd.read_csv(OUT/'playback_sensitivity.csv.gz')
    keys=['segment_s','request_delay_s','date','policy']
    g=d.groupby(keys).agg(stall=('stall_s','sum'),post=('post_start_s','sum'),media=('media_mbit','sum'),
                         segments=('segments','sum'),no_start=('segments',lambda x:(x==0).sum())).reset_index()
    g['risk']=g.stall/g.post.replace(0,np.nan)
    g['bitrate']=g.media/(g.segment_s*g.segments.replace(0,np.nan))
    g.to_csv(OUT/'playback_sensitivity_dates.csv',index=False)
    rows=[]
    for (segment,delay),b in g.groupby(['segment_s','request_delay_s']):
        pairs=b.pivot(index='date',columns='policy',values=['risk','bitrate'])
        rows.append(dict(segment_s=segment,request_delay_s=delay,dates=len(pairs),
            lower_stall_dates=int((pairs.risk.TreeLower<pairs.risk.Tree).sum()),
            lower_bitrate_dates=int((pairs.bitrate.TreeLower<pairs.bitrate.Tree).sum()),
            median_stall_delta=(pairs.risk.TreeLower-pairs.risk.Tree).median(),
            median_bitrate_delta=(pairs.bitrate.TreeLower-pairs.bitrate.Tree).median()))
    pd.DataFrame(rows).to_csv(OUT/'playback_sensitivity_summary.csv',index=False)


if __name__=='__main__':
    main()
