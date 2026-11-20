"""Exploratory earlier-date selection, with zero as an explicit abstention candidate."""
from pathlib import Path
import sys
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.clock_frontier import OUT,calibrate,metrics


def select(validation):
    # Full-precision empirical ceiling; ties use smaller K and then candidate order.
    eligible = validation[10*(validation.violations+validation.unresolved)<=validation.issued]
    return eligible.sort_values(['u','k','order'],ascending=[False,True,True]).iloc[0]


def main():
    ticks = pd.read_csv(OUT/'ticks.csv',float_precision='round_trip')
    rows,heldout = [],[]
    for regime,b in ticks.groupby('regime'):
        pool = b[b.partition=='calibration'].sort_values(['time','trace'])
        first = pool.date.min()
        fit = pool[(pool.date==first)&pool.y.notna()]
        validation = pool[pool.date!=first]
        test = b[b.partition=='test']
        assert fit.end.max() <= validation.time.min() and validation.end.max() <= test.time.min()
        settings = [('Zero','None',0)]
        settings.extend((m,rule,k) for k in [9,10,15,20] if k<=len(fit)
                        for m in ['Persistence','HistGBM'] for rule in ['Global','Grouped'])
        def forecast(frame,model,rule,k):
            if model=='Zero':
                return np.zeros(len(frame)),np.zeros(len(frame))
            _,lower = calibrate(fit.head(k),frame,model,0,rule=='Grouped')
            return frame[model],lower
        candidates=[]
        for order,(model,rule,k) in enumerate(settings):
            pt,lo = forecast(validation,model,rule,k)
            candidates.append(dict(regime=regime,model=model,policy=rule,k=k,order=order,
                                   validation_dates=validation.date.nunique(),
                                   **metrics(validation.y,pt,lo)))
        winner=select(pd.DataFrame(candidates))
        rows.extend(candidates)
        for role,(model,rule,k) in [('Selected',(winner.model,winner.policy,int(winner.k))),
                                    ('FixedTree',('HistGBM','Global',10)),
                                    ('FixedLag',('Persistence','Global',10))]:
            pt,lo=forecast(test,model,rule,k)
            heldout.append(dict(regime=regime,role=role,model=model,policy=rule,k=k,
                                fit_date=first,validation_labels=int(validation.y.count()),
                                **metrics(test.y,pt,lo)))
    pd.DataFrame(rows).to_csv(OUT/'selection_validation.csv',index=False)
    pd.DataFrame(heldout).to_csv(OUT/'selection_test.csv',index=False)


if __name__=='__main__':
    main()
