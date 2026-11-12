"""Summarize the external benchmark, including feasibility and paired differences."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"results/exploratory/sirhan_external"


def main():
    frontier = pd.read_csv(OUT/"matched_frontier.csv")
    curves = pd.read_csv(OUT/"decision_curves.csv")
    assert len(curves)==30*3*20 and not curves.duplicated(["seed","method","beta"]).any()
    published = {0.02:0.331,0.05:0.472,0.10:0.569}
    lines = ["# External comparison on the Irish 5G traces","",
        "We ran the one-sided 30-seed experiment from Sirhan’s archived code on the public Raca et al. traces. "
        "The candidate takes the smaller of nonnegative tree throughput and the published dl_lag1 feature, then fits the same signed-error calibration rule. "
        "Persistence uses that lag alone. The target is next-row downlink Mbps. For target row t+1, dl_lag1 is the observation at t−1, the most recent throughput feature given to the published tree. "
        "All methods use identical calibration and test traces within each split. The Rome results informed the choice of candidate; the Irish results were first evaluated after fixing that choice.",
        "", "## Published one-sided frontier","",
        "Numbers below are percentages. For each seed the paper sweeps 20 nominal error levels from 0.01 to 0.20 and retains the largest supported fraction among settings satisfying the measured test violation budget. "
        "The mean excludes seeds without a feasible grid point. This is a retrospective frontier. Each method's feasible seed count is shown in parentheses.","",
        "| Budget | Published global | Rerun global | Minimum | Persistence | Paired minimum minus global (pp) | Minimum wins / jointly feasible |",
        "|---:|---:|---:|---:|---:|---:|---:|"]
    rows = []
    for b,pub in published.items():
        p = frontier[frontier.budget==b].pivot(index="seed",columns="method",values="U")
        assert len(p)==30
        delta = (p.minimum-p["global"]).dropna()
        def cell(name):
            return f"{100*p[name].mean():.2f} ({p[name].count()})"
        lines.append(f"| {b:.0%} | {100*pub:.1f} | {cell('global')} | {cell('minimum')} | {cell('persistence')} | {100*delta.mean():+.2f} | {(delta>0).sum()}/{len(delta)} |")
        rows.append(dict(budget=b,published_global=pub,rerun_global=p["global"].mean(),paired_gain=delta.mean(),paired_seeds=len(delta)))
    lines += ["","The independent persistence comparison on jointly feasible splits is:","",
              "| Budget | Persistence minus global (pp) | Persistence wins / jointly feasible |","|---:|---:|---:|"]
    for b in published:
        p = frontier[frontier.budget==b].pivot(index="seed",columns="method",values="U")
        delta = (p.persistence-p["global"]).dropna()
        lines.append(f"| {b:.0%} | {100*delta.mean():+.2f} | {(delta>0).sum()}/{len(delta)} |")
    lines += ["","## Fixed nominal error of 0.10","",
              "These settings are chosen before seeing test outcomes. Each seed uses its own calibration set. All 30 test splits contribute, including violations of the target.","",
              "| Method | Mean violation | Mean supported fraction | Splits meeting 10% |","|---|---:|---:|---:|"]
    fixed=curves[curves.beta.round(8)==.10]
    for name,g in fixed.groupby("method"):
        lines.append(f"| {name} | {g.V.mean():.2%} | {g.U.mean():.2%} | {(g.V<=.10).sum()}/30 |")
    lines += ["", "Seeds repartition the same 83 traces. Win counts describe paired split behavior and do not establish independence or population significance. This is an external test of the forecasting rule with the Irish paper’s feature and training protocol. It does not test a frozen Rome-trained model or a ten-session adaptation budget.",
              "", "## Reproduction","",
              "Use the [Mendeley V1 analysis archive](https://data.mendeley.com/datasets/ncbdm2c36d/1) and [Raca et al. data](https://github.com/uccmisl/5Gdataset/tree/306d92eba81cb4f1195d8b8eba625666a02a10ec). Place the data ZIP in data/raw/ucc-external and run scripts/compare_sirhan_external.py with the analysis ZIP as its argument, then scripts/report_sirhan_external.py. The wrapper pins all three upstream source files and the data archive by SHA-256, relocates paths and inserts a scoring hook that shares the fitted predictions. The upstream global frontier and independently scored global frontier are checked on every seed and budget. See the [paper, Table 4](https://www.mdpi.com/2673-8732/6/4/92), results/exploratory/sirhan_external/run.json for software versions and the accompanying CSVs for all seed results."]
    audit = pd.read_csv(OUT/"trace_influence.csv")
    exclusions = pd.read_csv(OUT/"trace_exclusions.csv").set_index("sample")
    lines.extend(["","## Influence at the fixed nominal level","",
        f"Across {len(audit)} leave-one-trace-out scoring runs the gain ranged from "
        f"{audit.omit_gain_pp.min():.2f} to {audit.omit_gain_pp.max():.2f} percentage points. "
        f"Across individual traces, {(audit.mean_gain_pp>0).sum()} had a positive mean gain "
        f"and the median gain was {audit.mean_gain_pp.median():.2f} points."])
    for label, description in [("OmitTop5","Removing the five downloads with the largest sum of measured rates"),
                               ("OmitDownloads","Removing all download traces")]:
        row = exclusions.loc[label]
        lines.extend(["",f"{description} yielded a {row.mean_gain_pp:.2f}-point gain. "
                      f"Mean violations were {100*row.tree_v:.2f}% for the tree and {100*row.persistence_v:.2f}% for persistence."])
    lines.extend(["","The exclusions affect scoring only. Rebuild the trace totals with the archived rerun, then run scripts/audit_external_traces.py before generating this report."])
    (ROOT/"docs/EXTERNAL_SIRHAN_COMPARISON.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    print(json.dumps(rows,indent=2))


if __name__=="__main__":
    main()
