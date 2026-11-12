"""Describe lag transitions and fixed-nominal trace influence without refitting models."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.loader import extract_sessions_8224890, load_raw_8224890, load_14073311_ookla
from src.data.splits import create_experiment_splits

OUT = ROOT / "results/exploratory/sirhan_external"


def transitions(label, lag, outcome):
    lag, outcome = np.asarray(lag), np.asarray(outcome)
    change = outcome - lag
    near_zero = outcome <= .001
    fall = change <= -10
    return dict(setting=label, n=len(change), pearson=np.corrcoef(lag, outcome)[0, 1],
                spearman=pd.Series(lag).corr(pd.Series(outcome),method="spearman"),
                mae=np.abs(change).mean(), near_zero=near_zero.mean(), fall=fall.mean(),
                rise=(change >= 10).mean(), near_zero_after_high=(near_zero & fall).sum())


def transition_audit():
    irish = pd.read_parquet(ROOT / "data/raw/sirhan-external-work/features.parquet",
                            columns=["dl_lag1", "y"])
    rows = [transitions("Ireland", irish.dl_lag1, irish.y)]
    _, earlier = extract_sessions_8224890(load_raw_8224890())
    later = load_14073311_ookla()
    source = earlier[earlier.operator == "Op1"]
    targets = [source, later[later.operator=="Op1"], earlier[earlier.operator=="Op2"],
               later[later.operator=="Op2"]]
    for i, target in enumerate(targets):
        split = create_experiment_splits(source, target, "within_domain" if i==0 else "transfer", [10])
        test = split.target_test
        rows.append(transitions(f"E{i}", test.y_lag1, test.target_y))
    pd.DataFrame(rows).to_csv(OUT / "lag_transitions.csv", index=False)


def paired_gain(frame):
    totals = frame.groupby(["seed","method"])[["delivered","observed"]].sum()
    if len(totals)!=60 or (totals.observed<=0).any():
        raise ValueError("Each exclusion needs positive throughput for both methods on all 30 splits")
    utility = (totals.delivered/totals.observed).unstack()
    return 100*(utility.persistence-utility["global"])


def influence_audit():
    totals = pd.read_csv(OUT / "fixed_trace_totals.csv")
    paired = totals[totals.method.isin(["global","persistence"])]
    delivered = paired.pivot(index=["trace_id","seed"],columns="method",values="delivered")
    observed = paired[paired.method=="global"].set_index(["trace_id","seed"]).observed
    trace = paired.drop_duplicates("trace_id").set_index("trace_id")[["app","mobility","observed","n"]].copy()
    if (paired.groupby("trace_id")["observed"].nunique()>1).any():
        raise ValueError("Trace throughput changed across appearances")
    differences = 100*(delivered.persistence-delivered["global"])/observed
    trace["mean_gain_pp"] = differences.groupby("trace_id").mean()
    trace["test_appearances"] = differences.groupby("trace_id").size()
    trace["omit_gain_pp"] = [paired_gain(paired[paired.trace_id!=t]).mean() for t in trace.index]
    trace.sort_index().to_csv(OUT / "trace_influence.csv")
    downloads = trace.app.str.lower().eq("download")
    top = trace[downloads].nlargest(5,"observed").index
    if len(top)!=5:
        raise ValueError("Expected at least five download traces")
    exclusions = {"All": [], "OmitTop5": top, "OmitDownloads": trace[downloads].index}
    results = []
    for label, ids in exclusions.items():
        retained = paired[~paired.trace_id.isin(ids)]
        gains = paired_gain(retained)
        counts = retained.groupby(["seed","method"])[["violations","n"]].sum()
        risk = (counts.violations/counts.n).unstack()
        results.append(dict(sample=label, excluded=len(ids), mean_gain_pp=gains.mean(),
                            positive_splits=(gains>0).sum(),tree_v=risk["global"].mean(),
                            persistence_v=risk.persistence.mean()))
    pd.DataFrame(results).to_csv(OUT / "trace_exclusions.csv", index=False)


if __name__=="__main__":
    transition_audit()
    influence_audit()
