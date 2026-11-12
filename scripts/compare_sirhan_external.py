"""Run Sirhan's archived 30-seed benchmark with an additional paired scoring hook.

Usage: python scripts/compare_sirhan_external.py PATH_TO_MENDELEY_V1_ZIP
Requires the Raca 5G-production-dataset.zip in data/raw/ucc-external/.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from zipfile import ZipFile

import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/raw/sirhan-external-work"
OUT = ROOT / "results/exploratory/sirhan_external"
PINS = {
    "load_data.py":"4ee4726b3bcd3b269b91347a1a401411766189e5783023106ce0a856557729a4",
    "features.py":"43a685f2a525961d9410307bf06b8268cc9364325bc0569a7112da0f333ba71c",
    "run_multiseed_fast_30.py":"ac29e84566ecb63d4fe55399b6af5a25dfca00643b791d504aaacc6948f52746",
}


def evaluate_paired(seed, cal, test):
    """Use the released lag feature for each method, with no extra telemetry."""
    rows = []
    trace_totals = []
    y = test.y.to_numpy()
    for name in ("global", "minimum", "persistence"):
        def point(frame):
            tree = frame.pred.to_numpy()
            lag = frame.dl_lag1.to_numpy()
            if name == "global":
                return tree
            if name == "persistence":
                return lag
            return np.minimum(np.maximum(tree, 0), lag)
        scores = point(cal) - cal.y.to_numpy()
        pt = point(test)
        for beta in np.linspace(.01,.20,20):
            rank = min(len(scores),int(np.ceil((len(scores)+1)*(1-beta))))
            q = np.partition(scores,rank-1)[rank-1]
            lower = np.maximum(0,pt-q)
            if np.isclose(beta, .10):
                detail = test[["trace_id", "app", "mobility"]].copy()
                detail = detail.assign(n=1, observed=y, delivered=np.minimum(lower,y),
                                       violations=(lower>y).astype(int), abs_error=np.abs(pt-y))
                totals = detail.groupby(["trace_id","app","mobility"],as_index=False).sum()
                trace_totals.append(totals.assign(seed=seed,method=name))
            rows.append(dict(seed=seed,method=name,beta=beta,n=len(y),
                             V=float((lower>y).mean()),U=float(np.minimum(lower,y).sum()/y.sum())))
    pd.DataFrame(rows).to_csv(CACHE/f"curve_{seed}.csv",index=False)
    pd.concat(trace_totals).to_csv(CACHE/f"trace_fixed_{seed}.csv",index=False)


def main():
    CACHE.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    raw = ROOT/"data/raw/ucc-external/5G-production-dataset.zip"
    raw_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
    if raw_hash != "abc729d696b5e0ba34a9c6ed35a851f2868d2b5071be5efb8a49691c23bb1a9b":
        raise ValueError("Unexpected raw archive")
    with ZipFile(raw) as archive:
        for name in archive.namelist():
            if name.startswith("5G-production-dataset/") and name.endswith(".csv"):
                dest = (CACHE/name).resolve()
                if not dest.is_relative_to(CACHE):
                    raise ValueError(name)
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(archive.read(name))
    baseline_one, baseline_two = [], []
    with ZipFile(sys.argv[1]) as archive:
        for script,expected in PINS.items():
            path, = [n for n in archive.namelist() if n.endswith("/"+script)]
            source = archive.read(path)
            if hashlib.sha256(source).hexdigest()!=expected:
                raise ValueError(f"Unexpected archived source: {script}")
            code = source.decode().replace("/home/claude/artifacts",CACHE.as_posix())
            code = code.replace("/home/claude/data/5G-production-dataset",(CACHE/"5G-production-dataset").as_posix())
            if script != "run_multiseed_fast_30.py":
                exec(compile(code,path,"exec"),{"__name__":"__main__"})
                continue
            marker = "    # ---------- TWO-SIDED"
            assert code.count(marker)==1
            code = code.replace(marker,"    evaluate_paired(seed, cal, te)\n"+marker)
            ns = {"__name__":"archived_benchmark","evaluate_paired":evaluate_paired}
            exec(compile(code,path,"exec"),ns)
            for seed in range(30):
                two,one = ns["run_seed"](seed)
                baseline_one.extend(one)
                baseline_two.extend(two)
                print(f"Finished trace split {seed+1}/30",flush=True)
    baseline = pd.DataFrame(baseline_one)
    baseline.to_csv(OUT/"archived_one_sided.csv",index=False)
    pd.DataFrame(baseline_two).to_csv(OUT/"archived_two_sided.csv",index=False)
    curve = pd.concat([pd.read_csv(CACHE/f"curve_{i}.csv",float_precision="round_trip") for i in range(30)])
    curve.to_csv(OUT/"decision_curves.csv",index=False)
    pd.concat([pd.read_csv(CACHE/f"trace_fixed_{i}.csv",float_precision="round_trip")
               for i in range(30)]).to_csv(OUT/"fixed_trace_totals.csv",index=False)
    records=[]
    for (seed,method), b in curve.groupby(["seed","method"]):
        for budget in (.02,.05,.10):
            u = b.loc[b.V<=budget,"U"].max()
            if method=="global":
                ref = baseline[(baseline.seed==seed)&(baseline.method=="OS_global")].iloc[0]
                np.testing.assert_allclose(u,ref[f"util@{budget:.2f}"],equal_nan=True)
            records.append(dict(seed=seed,method=method,budget=budget,U=u))
    frontier=pd.DataFrame(records)
    frontier.to_csv(OUT/"matched_frontier.csv",index=False)
    print(frontier.groupby(["budget","method"]).U.agg(["mean","count"]))
    metadata=dict(raw_sha256=raw_hash,source_sha256=PINS,python=platform.python_version(),
                  sklearn=sklearn.__version__,numpy=np.__version__,pandas=pd.__version__,
                  threads=os.environ.get("OMP_NUM_THREADS"))
    (OUT/"run.json").write_text(json.dumps(metadata,indent=2))


if __name__=="__main__":
    main()
