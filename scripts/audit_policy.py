"""CLI tool to audit cellular throughput recalibration ledgers."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.audit.recalibration_audit import audit_ledger


def _format_text(report: dict) -> str:
    lines = ['=== Empirical Recalibration Accounting Audit ===']
    for pol, s in report['policies'].items():
        u_str = f"{100*s['supported_throughput_U']:.2f}%" if pd.notna(s['supported_throughput_U']) else 'N/A'
        lines.append(
            f"[{pol}] G={s['clusters']} N={s['eligible_ticks']} M={s['positive_offers']} "
            f"A={100*s['offer_frequency_A']:.2f}% R+=[{100*s['conditional_risk_lo']:.2f}%, {100*s['conditional_risk_hi']:.2f}%] "
            f"R_all=[{100*s['all_issued_risk_lo']:.2f}%, {100*s['all_issued_risk_hi']:.2f}%] "
            f"U={u_str} Q_new={s['realized_queries']} id_err={s['r_identity_max_abs_err']:.2e}"
        )
        for w in s['warnings']:
            lines.append(f"  WARNING ({pol}): {w}")
    for c in report['comparisons']:
        lines.append(
            f"[Paired {c['candidate']} - {c['reference']}] G={c['clusters']} (active={c['joint_active_clusters']}) "
            f"Eq dU={c['equal_cluster_du_pp']:+.2f} pp (SD={c['between_cluster_sd_pp']:.2f}, 95% t-CI [{c['t_du_ci95_pp'][0]:+.2f}, {c['t_du_ci95_pp'][1]:+.2f}], MDE80={c['mde80_du_pp']:.2f} pp) | "
            f"Pool dU={c['pooled_du_pp']:+.2f} pp (boot [{c['boot_du_ci95_pp'][0]:+.2f}, {c['boot_du_ci95_pp'][1]:+.2f}]) | "
            f"Pool dR+hi={c['pooled_dpos_hi_pp']:+.2f} pp (boot [{c['boot_dpos_hi_ci95_pp'][0]:+.2f}, {c['boot_dpos_hi_ci95_pp'][1]:+.2f}]) vs Eq dR+hi={c['equal_cluster_dpos_hi_pp']:+.2f} pp"
        )
        if c['tost_p_values']:
            tost_str = ', '.join(f'{k}: p={v:.4f}' for k, v in c['tost_p_values'].items())
            lines.append(f"  TOST equivalence p-values: {tost_str}")
        for w in c['warnings']:
            lines.append(f"  WARNING ({c['candidate']} vs {c['reference']}): {w}")
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Audit cellular recalibration policy ledgers.')
    parser.add_argument('csv_path', type=Path, help='Path to cluster-summary or tick-level ledger CSV(.gz).')
    parser.add_argument('--reference', default=None, help='Reference policy name for paired contrasts.')
    parser.add_argument('--min-clusters', type=int, default=20, help='Minimum physical clusters before warning.')
    parser.add_argument('--alpha', type=float, default=0.10, help='Nominal target risk level.')
    parser.add_argument('--n-boot', type=int, default=2000, help='Cluster bootstrap resamples.')
    parser.add_argument('--seed', type=int, default=42, help='Bootstrap RNG seed.')
    parser.add_argument('--json', action='store_true', help='Output JSON report instead of human-readable text.')
    args = parser.parse_args(argv)

    frame = pd.read_csv(args.csv_path)
    report = audit_ledger(
        frame,
        reference=args.reference,
        min_clusters=args.min_clusters,
        alpha=args.alpha,
        n_boot=args.n_boot,
        seed=args.seed,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format_text(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
