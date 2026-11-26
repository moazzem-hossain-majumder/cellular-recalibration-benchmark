"""Render main-manuscript figures and locked Path A visual diagnostics.

Generates:
  1. main_fig1_policy_summary.pdf/.png: Three-panel joint summary across all 10 cohorts
     showing offer frequency A, positive-offer upper risk R_+^hi vs alpha=0.10, and
     supported throughput U for Frozen, Periodic, MARUR, and PACER (HistGBM, Recorded).
  2. main_fig2_pacer_breakdown.pdf/.png: Per-cohort and per-cap (C_new in {10, 40})
     conditional risk and utility breakdown comparing Periodic, MARUR, and PACER
     across held-out public archives and the 6-cohort retrospective mean.
  3. main_fig3_theorem1_bounds.pdf/.png: Theorem 1 bound B_1(K) versus trivial
     deterministic bound (1 - alpha)*A and observed 3-seed mean selective excess
     across all 40 cohort-model-cap cells, highlighting where B_1 < (1 - alpha)*A.
  4. fig9_pacer.pdf/.png: Legacy filename refreshed with neutral non-overstated labels.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _save_both(fig: plt.Figure, stem: str) -> None:
    res_pdf = ROOT / f'results/figures/{stem}.pdf'
    res_png = ROOT / f'results/figures/{stem}.png'
    pap_pdf = ROOT / f'paper/figures/{stem}.pdf'
    pap_png = ROOT / f'paper/figures/{stem}.png'
    res_pdf.parent.mkdir(parents=True, exist_ok=True)
    pap_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(res_pdf, bbox_inches='tight')
    fig.savefig(res_png, dpi=300, bbox_inches='tight')
    plt.close(fig)
    shutil.copy2(res_pdf, pap_pdf)
    shutil.copy2(res_png, pap_png)
    print(f'Saved: {res_pdf} and {res_png}')


def plot_main_fig1_summary(summ: pd.DataFrame) -> None:
    """Task 7 summary figure: offer frequency, conditional risk, and utility by policy & cohort."""
    plt.rcParams.update({'font.size': 7.5, 'axes.titlesize': 8.3, 'axes.labelsize': 7.5})
    cohorts = [
        'E1', 'E3', 'AT&T', 'T-Mobile', 'Verizon', 'Ireland',
        'Rome_Capacity_Op1', 'Rome_Capacity_Op2', 'Oslo_Commute', 'Ireland_Static',
    ]
    labels = [
        'E1\n(R)', 'E3\n(R)', 'AT&T\n(R)', 'T-Mob\n(R)', 'Ver\n(R)', 'Ire\n(R)',
        'RomeOp1\n(H)', 'RomeOp2\n(H)', 'Oslo\n(H)', 'IreStat\n(H)',
    ]
    sub = summ[
        (summ['model'] == 'HistGBM')
        & (summ['scenario'] == 'Recorded')
        & (summ['policy'].isin(['Frozen', 'Periodic', 'MARUR', 'PACER']))
    ].copy()

    series_specs = [
        ('Frozen', 0, 'Frozen (C=0)', '#4d4d4d'),
        ('Periodic', 10, 'Periodic (C=10)', '#8c8c8c'),
        ('MARUR', 10, 'MARUR (C=10)', '#ff7f0e'),
        ('PACER', 10, 'PACER (C=10)', '#1f77b4'),
        ('Periodic', 40, 'Periodic (C=40)', '#bdbdbd'),
        ('MARUR', 40, 'MARUR (C=40)', '#ffbb78'),
        ('PACER', 40, 'PACER (C=40)', '#aec7e8'),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(7.2, 5.4), dpi=300, sharex=True)
    x = np.arange(len(cohorts))
    width = 0.115
    offsets = (np.arange(len(series_specs)) - (len(series_specs) - 1) / 2.0) * width

    lut = sub.set_index(['cohort', 'policy', 'cap_new'])
    metrics_cfg = [
        ('positive_rate', 'Offer Freq. $A$ (%)', '(a) Positive-Offer Frequency Across All 10 Cohorts (R = Retrospective, H = Held-Out Public Archive)', 98.0, None),
        ('positive_high', 'Cond. Upper Risk (%)', '(b) Positive-Offer Upper Risk $R_+^{\\mathrm{hi}}$ vs. Nominal $\\alpha=10\\%$ Ceiling', 76.0, 10.0),
        ('u', 'Supported Rate $U$ (%)', '(c) Supported Measured Throughput $U$ (% of Observed Rate)', 25.0, None),
    ]

    for ax, (col, ylabel, title, ylim, ref_line) in zip(axes, metrics_cfg):
        for idx, (pol, cap, lbl, color) in enumerate(series_specs):
            vals = [100.0 * float(lut.loc[(c, pol, cap), col]) for c in cohorts]
            ax.bar(x + offsets[idx], vals, width=width * 0.92, label=lbl if ax is axes[0] else None, color=color, edgecolor='#222222', linewidth=0.25)
        ax.axvline(5.5, color='#555555', linestyle='--', linewidth=0.8)
        if ref_line is not None:
            ax.axhline(ref_line, color='#2ca02c', linestyle='--', linewidth=1.0, label='Target alpha = 10%' if ax is axes[1] else None)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, ylim)
        ax.set_title(title, loc='left', pad=4)
        ax.grid(True, axis='y', alpha=0.25, linewidth=0.5)

    handles, leg_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, leg_labels, loc='upper center', bbox_to_anchor=(0.52, 1.00), ncol=4, fontsize=6.6, frameon=True)
    axes[1].legend(loc='upper right', fontsize=6.6, frameon=True)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(labels, fontsize=7.0)
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.91])
    _save_both(fig, 'main_fig1_policy_summary')


def plot_main_fig2_pacer_breakdown(summ: pd.DataFrame) -> None:
    """Task 2a figure: Held-out per-cohort/cap breakdown + retrospective mean (C_new in {10, 40})."""
    plt.rcParams.update({'font.size': 7.5, 'axes.titlesize': 8.3, 'axes.labelsize': 7.5})
    u = summ[
        (summ['model'] == 'HistGBM')
        & (summ['scenario'] == 'Recorded')
        & (summ['cap_new'].isin([10, 40]))
        & (summ['policy'].isin(['Periodic', 'MARUR', 'PACER']))
    ].copy()

    groups = ['Ireland_Static', 'Oslo_Commute', 'Rome_Capacity_Op1', 'Rome_Capacity_Op2', 'RetroMean']
    glabels = ['Ireland\nStatic', 'Oslo\nCommute', 'RomeCap\nOp1', 'RomeCap\nOp2', 'Retro\nMean (6)']
    colors = {'Periodic': '#7f7f7f', 'MARUR': '#ff7f0e', 'PACER': '#1f77b4'}
    policies = ['Periodic', 'MARUR', 'PACER']

    def _val(cohort_key: str, pol: str, cap: int, metric: str) -> float:
        if cohort_key == 'RetroMean':
            sub = u[(u['domain'] == 'retrospective') & (u['policy'] == pol) & (u['cap_new'] == cap)]
            return 100.0 * float(sub[metric].mean())
        row = u[(u['cohort'] == cohort_key) & (u['policy'] == pol) & (u['cap_new'] == cap)].iloc[0]
        return 100.0 * float(row[metric])

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.85), dpi=300, sharey=True)
    x = np.arange(len(groups))
    w = 0.25

    for ax, cap, panel_title in [
        (axes[0], 10, '(a) Positive-Offer Upper Risk at $C_{\\mathrm{new}}=10$'),
        (axes[1], 40, '(b) Positive-Offer Upper Risk at $C_{\\mathrm{new}}=40$'),
    ]:
        for idx, pol in enumerate(policies):
            vals = [_val(g, pol, cap, 'positive_high') for g in groups]
            ax.bar(x + (idx - 1) * w, vals, width=w * 0.92, label=pol if ax is axes[0] else None, color=colors[pol], alpha=0.90)
        ax.axhline(10.0, color='#2ca02c', linestyle='--', linewidth=0.9, label='Nominal $\\alpha=10\\%$' if ax is axes[0] else None)
        ax.axvline(3.5, color='#555555', linestyle=':', linewidth=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(glabels, fontsize=7.0)
        ax.set_ylim(0, 68)
        ax.set_title(panel_title)
        ax.grid(True, axis='y', alpha=0.25, linewidth=0.5)

    axes[0].set_ylabel('Cond. Upper Risk $R_+^{\\mathrm{hi}}$ (%)')
    handles, leg_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, leg_labels, loc='upper center', bbox_to_anchor=(0.52, 1.00), ncol=4, fontsize=6.8, frameon=True)
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.89])
    _save_both(fig, 'main_fig2_pacer_breakdown')


def plot_main_fig3_theorem1_bounds(seeds: pd.DataFrame) -> None:
    """Task 3 figure: Compare Theorem 1 bound, trivial bound A*(1-alpha), and observed excess per cell."""
    plt.rcParams.update({'font.size': 7.5, 'axes.titlesize': 8.2, 'axes.labelsize': 7.5})
    sm = (
        seeds.groupby(['domain', 'cohort', 'model', 'cap_new'], as_index=False)
        .agg(
            mean_pos=('positive_rate', 'mean'),
            mean_excess=('selective_excess_upper', 'mean'),
            bound=('theorem1_bound', 'first'),
        )
    )
    sm['trivial'] = 0.90 * sm['mean_pos']
    sm['informative'] = sm['bound'] < sm['trivial']

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), dpi=300, sharey=True)
    for ax, cap, title in [
        (axes[0], 10, '(a) Budget $C_{\\mathrm{new}}=10$ ($B_1 \\in [0.68, 0.71]$; 1/20 Informative)'),
        (axes[1], 40, '(b) Budget $C_{\\mathrm{new}}=40$ ($B_1 \\in [0.18, 0.19]$; 3/20 Informative)'),
    ]:
        sub = sm[sm['cap_new'] == cap].copy()
        xs = np.linspace(0.0, 0.92, 100)
        ax.plot(xs, xs, ':', color='#555555', linewidth=1.0, label='Trivial ceiling $0.9A$')
        b_avg = float(sub['bound'].mean())
        ax.axhline(b_avg, color='#d62728', linestyle='--', linewidth=1.1, label=f'Mean Theorem 1 bound ({b_avg:.2f})')
        ax.fill_between([0, min(0.96, b_avg / 0.9)], [0, b_avg], [b_avg, b_avg], color='#ffdddd', alpha=0.30, label='Vacuous zone ($B_1 \\geq 0.9A$)' if cap == 10 else None)

        for mod, marker, col in [('HistGBM', 'o', '#1f77b4'), ('Persistence', '^', '#ff7f0e')]:
            ms = sub[sub['model'] == mod]
            ax.scatter(ms['mean_pos'], ms['mean_excess'], marker=marker, s=30, color=col, alpha=0.88, label=f'{mod} observed excess')

        for r in sub[sub['informative']].itertuples():
            short = r.cohort.replace('Ireland_Static', 'IreStat').replace('Oslo_Commute', 'Oslo')
            dx = -20 if short == 'IreStat' else -10
            ax.annotate(short, (r.mean_pos, r.mean_excess), xytext=(dx, 8), textcoords='offset points', fontsize=6.4, color='#111111')

        ax.axhline(0.0, color='#888888', linestyle=':', linewidth=0.6)
        ax.set_xlim(0.0, 0.96)
        ax.set_ylim(-0.07, 0.86)
        ax.set_xlabel('Mean Positive-Offer Frequency $A$')
        ax.set_title(title)
        ax.grid(True, alpha=0.25, linewidth=0.5)

    axes[0].set_ylabel('Selective Excess $A(R_+^{\\mathrm{hi}}-\\alpha)$ / Bound')
    axes[0].legend(loc='upper left', fontsize=6.1, frameon=True)
    fig.tight_layout()
    _save_both(fig, 'main_fig3_theorem1_bounds')


def plot_legacy_fig9(seeds: pd.DataFrame, summ: pd.DataFrame) -> None:
    """Keep legacy fig9_pacer refreshed without overstated 'Untouched' labels."""
    plt.rcParams.update({'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8})
    sm = (
        seeds.groupby(['domain', 'cohort', 'model', 'cap_new'], as_index=False)
        .agg(mean_excess=('selective_excess_upper', 'mean'), bound=('theorem1_bound', 'first'))
    )
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.45), dpi=300)
    for dom, label, marker, color in [
        ('untouched_heldout', 'Held-out public archives (4 cohorts)', 'o', '#1f77b4'),
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
    ax1.set_title('(a) Theorem 1 Bound vs. Excess (40 Cells)')
    ax1.legend(loc='upper left', fontsize=6.5, frameon=True)
    ax1.grid(True, alpha=0.25, linewidth=0.5)

    u = summ[
        (summ['domain'] == 'untouched_heldout')
        & (summ['model'] == 'HistGBM')
        & (summ['scenario'] == 'Recorded')
        & (summ['cap_new'] == 10)
        & (summ['policy'].isin(['Periodic', 'MARUR', 'PACER']))
    ].copy()
    cohorts = ['Ireland_Static', 'Oslo_Commute', 'Rome_Capacity_Op1', 'Rome_Capacity_Op2']
    short_names = ['Ireland\nStatic', 'Oslo\nCommute', 'RomeCap\nOp1', 'RomeCap\nOp2']
    x = np.arange(len(cohorts))
    width = 0.25
    colors = {'Periodic': '#7f7f7f', 'MARUR': '#ff7f0e', 'PACER': '#1f77b4'}
    c10 = u.set_index(['cohort', 'policy'])
    for i, pol in enumerate(['Periodic', 'MARUR', 'PACER']):
        vals = [100.0 * float(c10.loc[(c, pol), 'positive_high']) for c in cohorts]
        ax2.bar(x + (i - 1) * width, vals, width=width * 0.92, label=f'{pol} ($C=10$)', color=colors[pol], alpha=0.88)
    ax2.axhline(10.0, color='#2ca02c', linestyle='--', linewidth=1.0, label='10% target')
    ax2.set_xticks(x)
    ax2.set_xticklabels(short_names, fontsize=7)
    ax2.set_ylabel('Positive-Offer Upper Risk $R_+^{\\mathrm{hi}}$ (%)')
    ax2.set_title('(b) Held-Out Public Archives ($C_{\\mathrm{new}}=10$, HistGBM)')
    ax2.set_ylim(0, 72)
    ax2.legend(loc='upper left', fontsize=6.5, ncol=2, frameon=True)
    ax2.grid(True, axis='y', alpha=0.25, linewidth=0.5)
    fig.tight_layout()
    _save_both(fig, 'fig9_pacer')


def main() -> None:
    seeds = pd.read_csv(ROOT / 'results/pacer/pacer_seed_sensitivity.csv')
    summ = pd.read_csv(ROOT / 'results/pacer/pacer_summary.csv')
    plot_main_fig1_summary(summ)
    plot_main_fig2_pacer_breakdown(summ)
    plot_main_fig3_theorem1_bounds(seeds)
    plot_legacy_fig9(seeds, summ)


if __name__ == '__main__':
    main()
