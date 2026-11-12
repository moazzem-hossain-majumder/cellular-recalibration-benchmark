"""Select a ten-label forecasting rule on source development observations only."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.loader import extract_sessions_8224890, load_raw_8224890, load_14073311_ookla
from src.data.splits import create_experiment_splits
from src.models.baselines import HistGradientBoostingThroughputPredictor, PersistencePredictor
from src.evaluation.conformal import compute_conformal_quantile


def forecast(tree, rows, weight):
    return (1-weight)*tree.predict(rows) + weight*PersistencePredictor().predict(rows)


def evaluate(tree, calibration, test, weight, scale):
    if len(calibration) != 10 or calibration.t_end.max() > test.t_start.min():
        raise ValueError("Expected ten completed calibration sessions before scoring")
    pc = forecast(tree, calibration, weight)
    pt = forecast(tree, test, weight)
    yc = calibration.target_y.to_numpy()
    y = test.target_y.to_numpy()
    if scale == "log1p":
        q = compute_conformal_quantile(np.log1p(pc)-np.log1p(yc))
        lower = np.maximum(0, np.expm1(np.log1p(pt)-q))
    else:
        q = compute_conformal_quantile(pc-yc)
        lower = np.maximum(0, pt-q)
    if not np.isfinite(lower).all() or y.sum() <= 0:
        raise ValueError("Invalid bounds or throughput denominator")
    return dict(n=len(y), violations=int((lower>y).sum()), V=float((lower>y).mean()),
                U=float(np.minimum(lower,y).sum()/y.sum()))


def main():
    _, earlier = extract_sessions_8224890(load_raw_8224890())
    source = earlier[earlier.operator == "Op1"]
    dev = create_experiment_splits(source, source, "within_domain", [10])
    tree = HistGradientBoostingThroughputPredictor().fit(dev.train, dev.train.target_y.to_numpy())
    # Use post-fit source rows to mimic a ten-label calibration deployment.
    available = pd.concat([dev.val, dev.source_calib]).sort_values("t_start")
    calibration, scoring = available.iloc[:10], available.iloc[10:]
    candidates = []
    for weight in (0., .5, 1.):
        for scale in ("additive", "log1p"):
            candidates.append(dict(weight=weight, scale=scale,
                                   **evaluate(tree, calibration, scoring, weight, scale)))
    # Prefer higher supported throughput subject to the nominal empirical target.
    # If all fail, use lowest violations, then highest support. Stable order breaks ties.
    selected = min(candidates,key=lambda c:(max(0.,c["V"]-.10),-c["U"]))
    out = ROOT/"results/exploratory"
    out.mkdir(exist_ok=True)
    (out/"source_bound_selection.json").write_text(json.dumps(dict(
        source="Earlier Op1",train=len(dev.train),calibration=len(calibration),scoring=len(scoring),
        scoring_dates=scoring.date.unique().tolist(),candidates=candidates,selected=selected),indent=2))
    later = load_14073311_ookla()
    targets = [source,later[later.operator=="Op1"],earlier[earlier.operator=="Op2"],later[later.operator=="Op2"]]
    previous = pd.read_csv(out/"persistence_prefixes.csv")
    saved = pd.read_csv(ROOT/"results/diagnostics/test_forecasts.csv")
    results = []
    for i,target in enumerate(targets):
        regime = f"E{i}"
        split = create_experiment_splits(source,target,"within_domain" if i==0 else "transfer",[10])
        pool = split.target_calib_pool.sort_values("t_start")
        test = split.target_test
        check = saved[saved.regime.str.startswith(regime) & (saved.budget_K==10)]
        np.testing.assert_array_equal(test.session_id,check.session_id)
        np.testing.assert_allclose(test.target_y,check.target)
        for start in range(0,len(pool)-9,10):
            block = pool.iloc[start:start+10]
            for name,w,s in [("HistGBM",0.,"additive"),("Persistence",1.,"additive"),
                             ("Source-selected",selected["weight"],selected["scale"])]:
                metrics=evaluate(tree,block,test,w,s)
                if name!="Source-selected":
                    row=previous[(previous.regime==regime)&(previous.calibration_block==start//10+1)&(previous.model==name)].iloc[0]
                    np.testing.assert_allclose([metrics["V"],metrics["U"]],[row.violation,row.supported])
                results.append(dict(regime=regime,block=start//10+1,method=name,**metrics))
    frame=pd.DataFrame(results)
    frame.to_csv(out/"source_selected_bounds.csv",index=False)
    print(selected)
    print(frame[frame.block==1].to_string(index=False))
    print(frame.assign(meets=frame.V<=.10).groupby(["regime","method"]).agg(blocks=("V","size"),meets=("meets","sum"),median_U=("U","median")))


if __name__=="__main__":
    main()
