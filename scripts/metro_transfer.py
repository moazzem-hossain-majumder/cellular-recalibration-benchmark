"""Same interval endpoint on bus and metro, with shared calendar cutoffs."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.validate_clock_and_network import BUS,URL,OUT,route_pairs
from src.evaluation.conformal import compute_conformal_quantile


def run():
    bus = route_pairs(BUS,URL,json.loads((OUT/'dataset_manifest.json').read_text())['norway_files'])
    metro = route_pairs(BUS.parent/'oslo-metro',URL.replace('bus.ljansbakken-oslo','metro.kalbakken-jernbanetorget'),
                        json.loads((OUT/'metro_manifest.json').read_text()))
    train_end = pd.Timestamp('2010-10-01',tz='UTC')
    test_start = pd.Timestamp('2011-01-30',tz='UTC')
    test = metro[metro.time>=test_start]
    records = []
    for training,frame in [('Bus',bus),('Metro',metro)]:
        train = frame[frame.end<train_end]
        model = HistGradientBoostingRegressor(max_iter=100,max_depth=5,learning_rate=.05,random_state=42)
        inputs = ['lag','lag2']
        model.fit(train[inputs],train.y)
        point = model.predict(test[inputs])
        for calibration,stream in [('Bus',bus),('Metro',metro)]:
            prefix = stream[(stream.time>=train_end)&(stream.end<test_start)].head(10)
            assert len(prefix)==10
            q = compute_conformal_quantile(model.predict(prefix[inputs])-prefix.y.to_numpy())
            lower = np.maximum(0,point-q)
            records.append(dict(training=training,calibration=calibration,test='Metro',k=10,
                n=len(test),test_dates=test.time.dt.date.nunique(),test_logs=test.trace.nunique(),
                train_rows=len(train),train_dates=train.time.dt.date.nunique(),q=q,mae=np.mean(abs(point-test.y)),
                v=(lower>test.y).mean(),u=np.minimum(lower,test.y).sum()/test.y.sum()))
    pd.DataFrame(records).to_csv(OUT/'metro_transfer.csv',index=False)


if __name__=='__main__':
    run()
