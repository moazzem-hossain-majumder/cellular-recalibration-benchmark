"""Compare empirical selection and an independent-offer exact-binomial benchmark."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.clock_frontier import OUT,metrics


def upper(errors,offers,alpha):
    if offers==0 or errors==offers:
        return 1.
    return float(beta.ppf(1-alpha,errors+1,offers-errors))


def main():
    ticks=pd.read_csv(OUT/'ticks.csv',float_precision='round_trip')
    validation_rows=[]
    test_rows=[]
    for regime,group in ticks.groupby('regime'):
        pre=group[group.partition=='calibration'].sort_values(['time','trace'])
        fit=pre[(pre.date==pre.date.min()) & pre.y.notna()].head(10)
        val=pre[pre.date>pre.date.min()]
        test=group[group.partition=='test']
        assert len(fit)==10 and fit.end.max()<=val.time.min() and val.end.max()<=test.time.min()
        def evaluate(frame,model,scale):
            point=frame[model]
            q=(fit[model]-fit.y).max()
            return metrics(frame.y,point,np.maximum(0,point-q)*scale)
        candidates=[]
        for model in ['Persistence','HistGBM']:
            for scale in [.25,.5,1.]:
                stats=evaluate(val,model,scale)
                errors=stats['violations']+stats['unresolved']
                n=stats['positive']
                ceiling=upper(errors,n,.05/6)
                eligible=stats['positive_rate']>=.1 and stats['u']>=.05
                candidates.append(dict(regime=regime,model=model,scale=scale,upper=ceiling,
                    empirical=eligible and n>0 and 10*errors<=n,
                    exact=eligible and ceiling<=.1,**stats))
        validation_rows.extend(candidates)
        for role in ['empirical','exact','Persistence','HistGBM']:
            if role in ['empirical','exact']:
                options=[r for r in candidates if r[role]]
                winner=max(options,key=lambda r:r['u']) if options else None
                model,scale=(winner['model'],winner['scale']) if winner else ('None',0.)
            else:
                model,scale=role,1.
            stats=evaluate(test,model if model!='None' else 'Persistence',scale)
            if model=='None':
                stats['mae']=np.nan
            test_rows.append(dict(regime=regime,role=role,model=model,scale=scale,**stats))
    pd.DataFrame(validation_rows).to_csv(OUT/'positive_offer_validation.csv',index=False)
    pd.DataFrame(test_rows).to_csv(OUT/'positive_offer_test.csv',index=False)


if __name__=='__main__':
    main()
