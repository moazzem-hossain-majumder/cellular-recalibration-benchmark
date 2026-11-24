"""Regenerate Figure 4 from saved multi-alpha results; include every observed risk."""
import json
from pathlib import Path
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
FIGURES_DIR=ROOT/'results/figures'

def plot(frontier_data):
    # Plot Figure 4: Pareto Risk-Utility Frontiers across alpha
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    
    # 4a: Empirical Violation V vs Nominal Alpha (Calibration Curve)
    reg_colors = {'E0_WithinDomain': '#1f77b4', 'E1_CampaignTransfer': '#ff7f0e',
                  'E2_CrossOperator': '#2ca02c', 'E3_JointShift': '#d62728'}
    
    axes[0].plot([0, 0.35], [0, 0.35], 'k--', alpha=0.7, label='Nominal reference ($V=\\alpha$)')
    for reg, col in reg_colors.items():
        sub = frontier_data[reg]
        axes[0].plot(sub['alphas'], sub['proposed']['V'], '-o', color=col, label=f"{reg.split('_')[0]} (Proposed)")
        
    axes[0].set_title('(a) Calibration Reliability: Empirical $V$ vs Nominal $\\alpha$')
    axes[0].set_xlabel('Nominal Risk Level ($\\alpha$)')
    axes[0].set_ylabel('Empirical Violation Rate ($V$)')
    axes[0].set_xlim(0, 0.32)
    axes[0].set_ylim(-0.02, max(0.35, 1.10*max(max(v['proposed']['V']) for v in frontier_data.values())))
    axes[0].grid(True, linestyle='--', alpha=0.5)
    axes[0].legend(loc='upper left', frameon=True)
    
    # 4b: Risk-Utility Pareto Tradeoff: U vs V
    for reg, col in reg_colors.items():
        sub = frontier_data[reg]
        axes[1].plot(sub['proposed']['V'], sub['proposed']['U'], '-s', color=col, label=f"{reg.split('_')[0]}")
        for i, a in enumerate(sub['alphas']):
            if a in [0.01, 0.05, 0.10, 0.20]:
                axes[1].annotate(f'$\\alpha$={a}', (sub['proposed']['V'][i], sub['proposed']['U'][i]),
                                 fontsize=7, xytext=(3, 3), textcoords='offset points')
                                 
    axes[1].set_title('(b) Risk-Utility Pareto Frontier ($U$ vs Empirical $V$)')
    axes[1].set_xlabel('Empirical Violation Rate ($V$)')
    axes[1].set_ylabel('Supported-Rate Fraction ($U$)')
    axes[1].set_ylim(-0.02, 0.45)
    axes[1].grid(True, linestyle='--', alpha=0.5)
    axes[1].legend(loc='lower right', frameon=True)
    
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / 'fig4_pareto_frontier.pdf', bbox_inches='tight')
    fig.savefig(FIGURES_DIR / 'fig4_pareto_frontier.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {FIGURES_DIR / "fig4_pareto_frontier.pdf"}')

if __name__=='__main__':
    plot(json.loads((ROOT/'results/metrics/multi_alpha_frontier.json').read_text()))
