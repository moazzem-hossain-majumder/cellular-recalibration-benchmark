"""Count actual source, pooled and pattern-specific fallback assignments on test rows."""
from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.loader import load_raw_8224890,extract_sessions_8224890,load_14073311_ookla
from src.data.splits import create_experiment_splits


def main():
    _, early = extract_sessions_8224890(load_raw_8224890())
    later = load_14073311_ookla()
    source = early[early.operator=='Op1']
    records = []
    for i,target in enumerate([source,later[later.operator=='Op1'],early[early.operator=='Op2'],later[later.operator=='Op2']]):
        budgets = [0,1,2,5,8,9,10,15]
        split = create_experiment_splits(source,target,'within_domain' if i==0 else 'transfer',budgets)
        pool = split.target_calib_pool.sort_values('t_start')
        assert pool.session_id.is_unique and pool.t_end.max() <= split.target_test.t_start.min()
        for k in budgets:
            if k>len(pool):
                continue
            for g,n in split.target_test.group_id.value_counts().items():
                count = int((pool.iloc[:k].group_id==g).sum())
                route = 'group' if count>=9 else 'pooled' if k>=9 else 'source'
                records.append(dict(regime=f'E{i}',k=k,group=g,prefix_count=count,test_rows=n,route=route))
    pd.DataFrame(records).to_csv(ROOT/'results/diagnostics/group_support.csv',index=False)
    metrics = pd.read_csv(ROOT/'results/metrics/calibration_budget_results.csv')
    fig,ax = plt.subplots(figsize=(6.6,3.2),layout='constrained')
    for reg,b in metrics[metrics.method=='Global_Conformal'].groupby('regime'):
        ax.plot(b.budget_K,100*b.zero_bound_fraction,marker='o',label=reg[:2])
    ax.set(xlabel='Target calibration sessions',ylabel='Forecasts with a zero lower bound (%)',
           ylim=(-3,103),xticks=[0,1,2,5,8,9,10,15])
    ax.legend(ncols=4,frameon=False)
    for ext in ['pdf','png']:
        fig.savefig(ROOT/f'results/figures/fig6_zero_bounds.{ext}',dpi=300)
    plt.close(fig)


if __name__=='__main__':
    main()
