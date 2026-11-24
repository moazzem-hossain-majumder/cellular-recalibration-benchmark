"""Render Fig. 9: Theorem 1 verification and untouched-archive PACER trade-offs."""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    plt.rcParams.update({'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8})
    seeds = pd.read_csv(ROOT / 'results/pacer/pacer_seed_sensitivity.csv')
    summ = pd.read_csv(ROOT / 'results/pacer/pacer_summary.csv')

    sm = (
        seeds.groupby(['domain', 'cohort', 'model', 'cap_new'], as_index=False)
        .agg(mean_excess=('selective_excess_upper', 'mean'), bound=('theorem1_bound', 'first'))
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.45), dpi=300)

    # Panel A: Theorem 1 empirical mean selective excess vs proved finite-sample bound across all 40 cells
    for dom, label, marker, color in [
        ('untouched_heldout', 'Untouched held-out (4 cohorts)', 'o', '#1f77b4'),
        ('retrospective', 'Retrospective (6 cohorts)', 's', '#d62728'),
    ]:
        sub = sm[sm['domain'] == dom]
        ax1.scatter(sub['bound'], sub['mean_excess'], label=label, marker=marker, s=30, alpha=0.85, color=color)

    lim = max(float(sm['bound'].max()) * 1.05, 0.72)
    xs = np.linspace(0.0, lim, 100)
    ax1.plot(xs, xs, '--', color='#333333', linewidth=1.0, label='Theorem 1 upper bound ($y=x$)')
    ax1.axhline(0.0, color='#888888', linewidth=0.7, linestyle=':')
    ax1.set_xlim(0.12, lim)
    ax1.set_ylim(-0.08, 0.25)
    ax1.set_xlabel('Theorem 1 Upper Bound')
    ax1.set_ylabel(r'Mean Selective Excess $A(R_+^{\mathrm{hi}}-\alpha)$')
    ax1.set_title('(a) Theorem 1 Across All 40 Cohort-Model-Cap Cells')
    ax1.legend(loc='upper left', fontsize=6.5, frameon=True)
    ax1.grid(True, alpha=0.25, linewidth=0.5)

    # Panel B: Untouched held-out HistGBM conditional risk vs service frequency across policies (cap=10 & 40)
    u = summ[
        (summ['domain'] == 'untouched_heldout')
        & (summ['model'] == 'HistGBM')
        & (summ['scenario'] == 'Recorded')
        & (summ['cap_new'].isin([10, 40]))
        & (summ['policy'].isin(['Periodic', 'MARUR', 'PACER']))
    ].copy()
    cohorts = ['Ireland_Static', 'Oslo_Commute', 'Rome_Capacity_Op1', 'Rome_Capacity_Op2']
    short_names = ['Ireland\nStatic', 'Oslo\nCommute', 'RomeCap\nOp1', 'RomeCap\nOp2']
    x = np.arange(len(cohorts))
    width = 0.25
    colors = {'Periodic': '#7f7f7f', 'MARUR': '#ff7f0e', 'PACER': '#1f77b4'}

    c10 = u[u['cap_new'] == 10].set_index(['cohort', 'policy'])
    for i, pol in enumerate(['Periodic', 'MARUR', 'PACER']):
        vals = [100.0 * float(c10.loc[(c, pol), 'positive_high']) for c in cohorts]
        ax2.bar(x + (i - 1) * width, vals, width=width * 0.92, label=f'{pol} ($C=10$)', color=colors[pol], alpha=0.88)

    ax2.axhline(10.0, color='#2ca02c', linestyle='--', linewidth=1.0, label='10% target')
    ax2.set_xticks(x)
    ax2.set_xticklabels(short_names, fontsize=7)
    ax2.set_ylabel('Positive-Offer Upper Risk $R_+^{\mathrm{hi}}$ (%)')
    ax2.set_title('(b) Untouched Archives ($C_{\\mathrm{new}}=10$, HistGBM)')
    ax2.set_ylim(0, 72)
    ax2.legend(loc='upper left', fontsize=6.5, ncol=2, frameon=True)
    ax2.grid(True, axis='y', alpha=0.25, linewidth=0.5)

    fig.tight_layout()
    out_res = ROOT / 'results/figures/fig9_pacer.pdf'
    out_res_png = ROOT / 'results/figures/fig9_pacer.png'
    out_pap = ROOT / 'paper/figures/fig9_pacer.pdf'
    out_pap_png = ROOT / 'paper/figures/fig9_pacer.png'
    out_res.parent.mkdir(parents=True, exist_ok=True)
    out_pap.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_res, bbox_inches='tight')
    fig.savefig(out_res_png, dpi=300, bbox_inches='tight')
    plt.close(fig)
    shutil.copy2(out_res, out_pap)
    shutil.copy2(out_res_png, out_pap_png)
    print('Saved:', out_res, 'and', out_res_png)


if __name__ == '__main__':
    main()
