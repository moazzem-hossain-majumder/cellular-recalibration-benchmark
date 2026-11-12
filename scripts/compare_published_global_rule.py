"""Matched Rome adaptation of Sirhan (2026), Network 6(4), 92, one-sided global rule."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.loader import extract_sessions_8224890, load_raw_8224890, load_14073311_ookla
from src.data.splits import create_experiment_splits
from src.models.baselines import HistGradientBoostingThroughputPredictor, PersistencePredictor
from src.evaluation.conformal import GlobalConformalCalibrator


def main():
    _, earlier = extract_sessions_8224890(load_raw_8224890())
    source = earlier[earlier.operator == "Op1"]
    later = load_14073311_ookla()
    dev = create_experiment_splits(source,source,"within_domain",[10])
    tree = HistGradientBoostingThroughputPredictor().fit(dev.train,dev.train.target_y.to_numpy())
    persistence = PersistencePredictor()
    targets = [source,later[later.operator=="Op1"],earlier[earlier.operator=="Op2"],later[later.operator=="Op2"]]
    saved = pd.read_csv(ROOT/"results/diagnostics/test_forecasts.csv")
    previous = pd.read_csv(ROOT/"results/exploratory/persistence_prefixes.csv")
    records = []
    for i,target in enumerate(targets):
        regime = f"E{i}"
        split = create_experiment_splits(source,target,"within_domain" if i==0 else "transfer",[10])
        test = split.target_test
        pool = split.target_calib_pool.sort_values("t_start")
        assert pool.t_end.max() <= test.t_start.min()
        check = saved[(saved.regime.str.startswith(regime)) & (saved.budget_K==10)]
        np.testing.assert_array_equal(test.session_id,check.session_id)
        truth = test.target_y.to_numpy()
        np.testing.assert_allclose(truth,check.target)
        for j in range(0,len(pool)-9,10):
            block = pool.iloc[j:j+10]
            for method in ("tree","persistence","minimum"):
                def predict(frame):
                    if method=="tree":
                        return tree.predict(frame)
                    if method=="persistence":
                        return persistence.predict(frame)
                    return np.minimum(tree.predict(frame),persistence.predict(frame))
                calibration = GlobalConformalCalibrator(.1).fit(predict(block),block.target_y.to_numpy())
                lower,_ = calibration.predict_lower_bound(predict(test))
                assert np.isfinite(lower).all()
                v = float((lower>truth).mean())
                u = float(np.minimum(lower,truth).sum()/truth.sum())
                if method=="tree" and j==0:
                    np.testing.assert_allclose(lower,check.Global_Conformal)
                if method!="minimum":
                    label = "HistGBM" if method=="tree" else "Persistence"
                    ref = previous[(previous.regime==regime)&(previous.calibration_block==j//10+1)&(previous.model==label)].iloc[0]
                    np.testing.assert_allclose([v,u],[ref.violation,ref.supported])
                records.append(dict(regime=regime,block=j//10+1,method=method,n=len(test),violations=int((lower>truth).sum()),V=v,U=u))
    result=pd.DataFrame(records)
    result.to_csv(ROOT/"results/exploratory/published_global_comparison.csv",index=False)
    print(result[result.block==1].to_string(index=False))
    for reg,r in result.groupby("regime"):
        u=r.pivot(index="block",columns="method",values="U")
        v=r.pivot(index="block",columns="method",values="V")
        print(reg,len(v),"beats tree U while meeting risk:",int(((v.minimum<=.1)&(u.minimum>u.tree)).sum()),"risk passes:",int((v.minimum<=.1).sum()))


if __name__=="__main__":
    main()
