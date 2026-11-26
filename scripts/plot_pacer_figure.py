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
    """Keep legacy fig9_pacer refreshed with neutral 'heldout_public' domain labels."""
    plt.rcParams.update({'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8})
    sm = (
        seeds.groupby(['domain', 'cohort', 'model', 'cap_new'], as_index=False)
        .agg(mean_excess=('selective_excess_upper', 'mean'), bound=('theorem1_bound', 'first'))
    )
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.45), dpi=300)
    for dom, label, marker, color in [
        ('heldout_public', 'Held-out public archives (4 cohorts)', 'o', '#1f77b4'),
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
        (summ['domain'] == 'heldout_public')
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


def plot_main_fig0_pipeline_flow() -> None:
    """Compact end-to-end study pipeline distinguishing design, frozen scoring, accounting, and audit."""
    import matplotlib.patches as patches

    plt.rcParams.update({'font.size': 7.2})
    fig, ax = plt.subplots(figsize=(7.2, 1.55), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 22)
    ax.axis('off')

    boxes = [
        (1.0, 4.0, 17.0, 14.0, '#eef4fb', '#2b5c8f', '1. Source Training', 'Rome Op1 (2021)\n57 source rows\nFrozen HistGBM'),
        (21.0, 4.0, 18.0, 14.0, '#fff4e6', '#b85d19', '2. Design & Replay', 'Retrospective (16 dates)\n3 campaigns; MARUR\nfailure -> PACER specs'),
        (42.0, 4.0, 19.0, 14.0, '#f3f0fa', '#5c3c92', '3. Frozen Scoring', 'Held-out (26 dates)\n3 camp; SHA-256 locked\n(prior access, not blind)'),
        (64.0, 4.0, 17.5, 14.0, '#eaf7ee', '#246b3a', '4. Ledger & Prop. 1', 'R=AR+, Qnew, [lo,hi]\nPool vs Eq, G_eff / k\n5 Reversal Conditions'),
        (84.5, 4.0, 14.5, 14.0, '#fdf0f0', '#9e2a2b', '5. Audit & Outputs', 'Single-factor flips\nPareto (R+hi, U)\naudit_policy.py'),
    ]
    for x0, y0, w, h, fc, ec, title, body in boxes:
        rect = patches.FancyBboxPatch(
            (x0, y0), w, h, boxstyle='round,pad=0.4,rounding_size=0.8',
            facecolor=fc, edgecolor=ec, linewidth=1.1,
        )
        ax.add_patch(rect)
        ax.text(x0 + w / 2.0, y0 + h - 2.3, title, ha='center', va='top', fontsize=7.0, fontweight='bold', color=ec)
        ax.text(x0 + w / 2.0, y0 + 5.2, body, ha='center', va='center', fontsize=6.1, color='#222222', linespacing=1.25)

    for x_start, x_end in [(18.4, 20.6), (39.4, 41.6), (61.4, 63.6), (81.9, 84.1)]:
        ax.annotate('', xy=(x_end, 11.0), xytext=(x_start, 11.0),
                    arrowprops=dict(arrowstyle='->', color='#333333', lw=1.1))

    ax.text(39.5, 1.3, 'Frozen Protocol Boundary (no held-out tuning)', ha='center', va='center', fontsize=6.2, style='italic', color='#5c3c92')
    ax.text(81.5, 1.3, 'Post-hoc Exploratory Checks Only', ha='center', va='center', fontsize=6.2, style='italic', color='#9e2a2b')
    fig.tight_layout(pad=0.2)
    _save_both(fig, 'main_fig0_pipeline_flow')


def plot_main_fig4_ablation_pareto() -> None:
    """Centerpiece 2-panel graphic: (a) Single-factor reversal rates, (b) Risk-Utility Pareto frontier."""
    plt.rcParams.update({'font.size': 7.3, 'axes.titlesize': 8.0, 'axes.labelsize': 7.3})
    abl = pd.read_csv(ROOT / 'results/exploratory/sensitivity/single_factor_ablation.csv')
    par = pd.read_csv(ROOT / 'results/exploratory/sensitivity/risk_utility_pareto.csv')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.75), dpi=300)

    # Panel (a): Single-factor flip/indeterminacy rates across immutable saved comparisons
    short_lbl = {
        'R_vs_Rplus_SLA': '1a. R->R+ SLA (400)',
        'R_vs_Rplus_Rank': '1b. R->R+ Rank (400)',
        'Cap_vs_Qnew_All': '2. Cnew!=Qnew (400)',
        'Missing_Bounds_Overlap': '3. [lo,hi] Overlap (285)',
        'Pooling_Weight_Rplus': '4. Pool!=Eq Sign (120)',
        'Campaign_Clustering_Donner': '5. Donner DEFF Flip (5)',
    }
    abl_p = abl.copy()
    abl_p['short'] = abl_p['factor'].map(short_lbl)
    y = np.arange(len(abl_p))[::-1]
    cols = ['#d62728', '#ff7f0e', '#8c564b', '#9467bd', '#1f77b4', '#2ca02c']
    ax1.barh(y, abl_p['pct_affected'], color=cols, alpha=0.88, height=0.62, edgecolor='#222222', linewidth=0.4)
    for yi, r in zip(y, abl_p.itertuples()):
        ax1.text(r.pct_affected + 1.5, yi, f'{r.pct_affected:.1f}% ({r.n_affected}/{r.n_total})', va='center', fontsize=6.2, color='#111111')
    ax1.set_yticks(y)
    ax1.set_yticklabels(abl_p['short'], fontsize=6.6)
    ax1.set_xlim(0, 82)
    ax1.set_xlabel('Evaluated Comparisons Reversed / Ambiguous (%)')
    ax1.set_title('(a) Single-Factor Accounting Reversal Rates')
    ax1.grid(True, axis='x', alpha=0.25, linewidth=0.5)

    # Panel (b): Risk-Utility Pareto (Supported U vs Cond Upper Risk R+^hi, 10-cohort mean)
    prim = par[par['source'] == 'HistGBM_Recorded_10Coh'].copy()
    alsw = par[(par['source'] == 'HistGBM_AlphaSweep_10Coh') & (par['cap_new'] == 10)].copy()

    # Operating curves across nominal alpha in {0.05, 0.10, 0.20} at C_new=10
    for pol, col, ls in [('Periodic', '#7f7f7f', '--'), ('MARUR', '#ff7f0e', ':'), ('PACER', '#1f77b4', '-.')]:
        sub_a = alsw[alsw['policy'] == pol].sort_values('alpha')
        ax2.plot(sub_a['supported_u_pp'], sub_a['cond_risk_hi_pp'], linestyle=ls, color=col, linewidth=0.95, alpha=0.75, label=f'{pol} a-sweep')

    markers = {0: 'D', 10: 'o', 40: 's'}
    pcolors = {'Frozen': '#333333', 'Periodic': '#666666', 'MARUR': '#ff7f0e', 'PACER': '#1f77b4', 'ACI': '#2ca02c', 'Early': '#9467bd', 'DecayingOGD': '#d62728'}
    for r in prim.itertuples():
        lbl = f"{r.policy} C={r.cap_new}" if r.policy in ('Frozen', 'Periodic', 'MARUR', 'PACER') and r.cap_new in (0, 10) else None
        ax2.scatter(r.supported_u_pp, r.cond_risk_hi_pp, marker=markers[r.cap_new], s=32, color=pcolors.get(r.policy, '#444444'), edgecolor='#111111', linewidth=0.4, zorder=4)

    ann = [
        ('Frozen', 0, (4, -8)),
        ('Periodic', 10, (5, -7)),
        ('Periodic', 40, (5, -7)),
        ('ACI', 40, (-30, -3)),
        ('MARUR', 10, (-34, 4)),
        ('PACER', 40, (-18, 7)),
        ('Early', 40, (-14, 7)),
        ('DecayingOGD', 10, (-28, -9)),
    ]
    lut = prim.set_index(['policy', 'cap_new'])
    for pol, cap, (dx, dy) in ann:
        row = lut.loc[(pol, cap)]
        short_p = 'OGD' if pol == 'DecayingOGD' else ('Per' if pol == 'Periodic' else ('Frz' if pol == 'Frozen' else pol))
        txt = f'{short_p}{cap}' if cap > 0 else 'Frz0'
        ax2.annotate(txt, (row['supported_u_pp'], row['cond_risk_hi_pp']), xytext=(dx, dy), textcoords='offset points', fontsize=6.0)

    ax2.axhline(10.0, color='#2ca02c', linestyle='--', linewidth=0.9)
    ax2.text(0.18, 11.4, 'Target alpha = 10% (unmet)', fontsize=6.0, color='#246b3a', ha='left')
    ax2.text(1.75, 21.0, 'Matched (Q, A):\n3/100 wins vs Per', fontsize=6.0, bbox=dict(boxstyle='round,pad=0.25', fc='#fffbe6', ec='#b59b00', lw=0.6))
    ax2.set_xlim(0.0, 6.2)
    ax2.set_ylim(5.0, 58.0)
    ax2.set_xlabel('Mean Supported Throughput $U$ (%)')
    ax2.set_ylabel('Mean Cond. Upper Risk $R_+^{\\mathrm{hi}}$ (%)')
    ax2.set_title('(b) Risk-Utility Trade-Off (Circles C=10, Sq C=40)')
    ax2.legend(loc='lower right', fontsize=5.8, frameon=True)
    ax2.grid(True, alpha=0.25, linewidth=0.5)

    fig.tight_layout()
    _save_both(fig, 'main_fig4_ablation_pareto')


def main() -> None:
    seeds = pd.read_csv(ROOT / 'results/pacer/pacer_seed_sensitivity.csv')
    summ = pd.read_csv(ROOT / 'results/pacer/pacer_summary.csv')
    plot_main_fig0_pipeline_flow()
    plot_main_fig1_summary(summ)
    plot_main_fig2_pacer_breakdown(summ)
    plot_main_fig3_theorem1_bounds(seeds)
    plot_main_fig4_ablation_pareto()
    plot_legacy_fig9(seeds, summ)


if __name__ == '__main__':
    main()
