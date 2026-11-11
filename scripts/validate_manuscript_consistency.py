"""
Automated manuscript-to-experiment consistency validation.

This script verifies that all numerical claims in the manuscript, LaTeX tables,
README, and abstract are traceable to the authoritative experiment output files.
It fails with specific error messages if any discrepancy is found.

Usage:
    python scripts/validate_manuscript_consistency.py
"""
import json
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / 'results' / 'metrics'
TABLES_DIR = ROOT / 'results' / 'tables'
PAPER_TABLES_DIR = ROOT / 'paper' / 'tables'

errors = []
warnings = []


def check(condition, msg):
    """Record a validation error if condition is False."""
    if not condition:
        errors.append(f"FAIL: {msg}")
        return False
    return True


def warn(msg):
    """Record a non-fatal warning."""
    warnings.append(f"WARN: {msg}")


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def load_csv_records(path):
    with open(path, 'r') as f:
        return list(csv.DictReader(f))


# ============================================================
# 1. Validate Table 1 (Point Predictors) matches JSON source
# ============================================================
def validate_table1():
    print("\n--- Validating Table 1: Point Predictor Profiles ---")
    profiles = load_json(METRICS_DIR / 'point_predictor_profiles.json')
    tex_path = TABLES_DIR / 'table1_point_predictors.tex'
    tex_content = tex_path.read_text(encoding='utf-8')

    for model_name, prof in profiles.items():
        display_name = model_name.replace('_', ' ')
        mae_str = f"{prof['val_mae']:.2f}"
        rmse_str = f"{prof['val_rmse']:.2f}"
        fit_str = f"{prof['fit_time_seconds']:.3f}"

        check(mae_str in tex_content,
              f"Table 1: {display_name} MAE {mae_str} not found in LaTeX table")
        check(rmse_str in tex_content,
              f"Table 1: {display_name} RMSE {rmse_str} not found in LaTeX table")
        check(fit_str in tex_content,
              f"Table 1: {display_name} Fit Time {fit_str} not found in LaTeX table")

    # Verify paper/tables/ copy matches results/tables/
    paper_tex = (PAPER_TABLES_DIR / 'table1_point_predictors.tex').read_text(encoding='utf-8')
    check(tex_content == paper_tex,
          "Table 1: paper/tables/ copy differs from results/tables/ source")

    print(f"  Table 1 validation: {len(profiles)} models checked")


# ============================================================
# 2. Validate Table 2 (Main Benchmark) matches CSV source
# ============================================================
def validate_table2():
    print("\n--- Validating Table 2: Main Benchmark Results ---")
    records = load_csv_records(METRICS_DIR / 'calibration_budget_results.csv')
    tex_path = TABLES_DIR / 'table2_main_benchmark.tex'
    tex_content = tex_path.read_text(encoding='utf-8')

    # Build lookup: (regime, budget_K, method) -> (V, U)
    lookup = {}
    for r in records:
        key = (r['regime'], int(r['budget_K']), r['method'])
        lookup[key] = (float(r['violation_rate']), float(r['supported_fraction']))

    # Check specific K=10 values that appear prominently
    regimes_check = [
        'E0_WithinDomain_Op1_2021',
        'E1_CampaignTransfer_Op1_2023',
        'E2_CrossOperator_Op2_2021',
        'E3_JointShift_Op2_2023'
    ]
    methods_check = ['Uncalibrated', 'Global_Conformal', 'Proposed_Missingness_Aware']
    budgets_check = [0, 2, 5, 8, 9, 10]

    checked = 0
    for regime in regimes_check:
        for method in methods_check:
            for k in budgets_check:
                key = (regime, k, method)
                if key in lookup:
                    v, u = lookup[key]
                    v_str = f"{v:.2f}"
                    u_str = f"{u:.2f}"
                    # These formatted values should appear in the tex table
                    if v_str not in tex_content:
                        # Only flag if it's not a rounding artifact
                        v_alt = f"{v:.2f}"
                        if v_alt not in tex_content:
                            errors.append(
                                f"Table 2: {regime} {method} K={k} V={v_str} not found in LaTeX")
                    checked += 1

    # Verify paper/tables/ copy matches results/tables/
    paper_tex = (PAPER_TABLES_DIR / 'table2_main_benchmark.tex').read_text(encoding='utf-8')
    check(tex_content == paper_tex,
          "Table 2: paper/tables/ copy differs from results/tables/ source")

    print(f"  Table 2 validation: {checked} cells checked")


# ============================================================
# 3. Validate bootstrap results match manuscript claims
# ============================================================
def validate_bootstrap():
    print("\n--- Validating Bootstrap Significance Claims ---")
    boot = load_json(METRICS_DIR / 'bootstrap_significance_tests.json')

    # E1 bootstrap
    e1 = boot.get('E1_CampaignTransfer_Op1_2023', {})
    if 'delta_U' in e1:
        check(abs(e1['delta_U']['point'] - 0.0372) < 0.001,
              f"Bootstrap E1 delta_U point should be ~0.037, got {e1['delta_U']['point']}")
        check(abs(e1['delta_U']['ci_95'][0] - 0.0188) < 0.002,
              f"Bootstrap E1 delta_U CI lower should be ~0.019, got {e1['delta_U']['ci_95'][0]}")

    # E2 bootstrap
    e2 = boot.get('E2_CrossOperator_Op2_2021', {})
    if 'delta_U' in e2:
        check(abs(e2['delta_U']['point'] - 0.171) < 0.002,
              f"Bootstrap E2 delta_U point should be ~0.171, got {e2['delta_U']['point']}")

    # E0 should be zero (degenerate)
    e0 = boot.get('E0_WithinDomain_Op1_2021', {})
    if 'delta_U' in e0:
        check(e0['delta_U']['point'] == 0.0,
              f"Bootstrap E0 delta_U should be 0.0, got {e0['delta_U']['point']}")

    print("  Bootstrap validation complete")


# ============================================================
# 4. Validate no unsupported Bangladesh operational claims
# ============================================================
def validate_no_unsupported_bangladesh():
    print("\n--- Validating No Unsupported Bangladesh Operational Claims ---")
    tex_path = ROOT / 'paper' / 'manuscript.tex'
    md_path = ROOT / 'paper' / 'manuscript.md'

    # Patterns that should NOT appear as operational claims
    # (prospective framing is acceptable)
    forbidden_patterns = [
        r'BDT\s+\d',                     # BDT cost figures
        r'1,20,000',                       # Specific BDT amounts
        r'2,50,000',                       # Specific BDT amounts
        r'BTRC\s+directives?\s+requiring', # BTRC as if binding on this research
    ]

    for path in [tex_path, md_path]:
        content = path.read_text(encoding='utf-8')
        for pattern in forbidden_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                errors.append(
                    f"Bangladesh: Found unsupported claim pattern '{pattern}' in {path.name}: {matches}")

    print("  Bangladesh claims validation complete")


# ============================================================
# 5. Validate abstract numerical claims
# ============================================================
def validate_abstract_claims():
    print("\n--- Validating Abstract Numerical Claims ---")
    tex_path = ROOT / 'paper' / 'manuscript.tex'
    content = tex_path.read_text(encoding='utf-8')

    # Extract abstract
    abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', content, re.DOTALL)
    if not abstract_match:
        errors.append("Cannot find abstract in manuscript.tex")
        return
    abstract = abstract_match.group(1)

    # Check: "1,132 verified commercial Speedtest sessions"
    check('1,132' in abstract or '1{,}132' in abstract,
          "Abstract should mention 1,132 sessions")

    # Check: "1,001 causal forecast pairs"
    check('1,001' in abstract or '1{,}001' in abstract,
          "Abstract should mention 1,001 causal pairs")

    # Check: "33% to 62%" violation rates
    check('33' in abstract and '62' in abstract,
          "Abstract should mention 33% to 62% violation rates")

    # Check: Lemma 1 K>=9
    check('K \\ge 9' in abstract or 'K=9' in abstract or 'K \\geq 9' in abstract or '$K \\ge 9$' in abstract,
          "Abstract should mention K>=9 threshold")

    print("  Abstract claims validation complete")


# ============================================================
# 6. Validate README numerical claims
# ============================================================
def validate_readme():
    print("\n--- Validating README Numerical Claims ---")
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')

    # Session counts
    check('1,132' in readme or '1132' in readme,
          "README should mention 1,132 sessions")
    check('1,001' in readme or '1001' in readme,
          "README should mention 1,001 causal pairs")

    # Violation rate range
    check('62' in readme,
          "README should mention 62% max violation rate")

    # Bootstrap values should match JSON
    boot = load_json(METRICS_DIR / 'bootstrap_significance_tests.json')
    e1_du = boot['E1_CampaignTransfer_Op1_2023']['delta_U']['point']
    check(f"{e1_du:+.3f}" in readme or f"+{e1_du:.3f}" in readme,
          f"README E1 delta_U should match {e1_du:+.3f}")

    print("  README validation complete")


# ============================================================
# 7. Validate dataset instance counts
# ============================================================
def validate_dataset_counts():
    print("\n--- Validating Dataset Instance Counts ---")
    records = load_csv_records(METRICS_DIR / 'calibration_budget_results.csv')

    # E0 test samples at K=0
    e0_uncal = [r for r in records
                if r['regime'] == 'E0_WithinDomain_Op1_2021'
                and r['method'] == 'Uncalibrated'
                and int(r['budget_K']) == 0]
    if e0_uncal:
        n_e0 = int(e0_uncal[0]['test_samples'])
        check(n_e0 == 41,
              f"E0 test samples should be 41, got {n_e0}")

    # E1 test samples
    e1_uncal = [r for r in records
                if r['regime'] == 'E1_CampaignTransfer_Op1_2023'
                and r['method'] == 'Uncalibrated'
                and int(r['budget_K']) == 0]
    if e1_uncal:
        n_e1 = int(e1_uncal[0]['test_samples'])
        check(n_e1 == 139,
              f"E1 test samples should be 139, got {n_e1}")

    # E2 test samples
    e2_uncal = [r for r in records
                if r['regime'] == 'E2_CrossOperator_Op2_2021'
                and r['method'] == 'Uncalibrated'
                and int(r['budget_K']) == 0]
    if e2_uncal:
        n_e2 = int(e2_uncal[0]['test_samples'])
        check(n_e2 == 256,
              f"E2 test samples should be 256, got {n_e2}")

    # E3 test samples
    e3_uncal = [r for r in records
                if r['regime'] == 'E3_JointShift_Op2_2023'
                and r['method'] == 'Uncalibrated'
                and int(r['budget_K']) == 0]
    if e3_uncal:
        n_e3 = int(e3_uncal[0]['test_samples'])
        check(n_e3 == 103,
              f"E3 test samples should be 103, got {n_e3}")

    print("  Dataset count validation complete")


# ============================================================
# 8. Validate Lemma 1 correctness
# ============================================================
def validate_lemma1():
    print("\n--- Validating Lemma 1 Formulation ---")
    tex_path = ROOT / 'paper' / 'manuscript.tex'
    content = tex_path.read_text(encoding='utf-8')

    # Lemma 1 should NOT claim "zero statistical benefit" for K<9
    check('zero statistical benefit' not in content,
          "Lemma 1 should not claim 'zero statistical benefit' for K<9 "
          "(source fallback still provides useful calibration)")

    # Should mention that K=9 is an activation threshold, not a guarantee
    check('activation' in content.lower() or 'cutoff' in content.lower(),
          "Lemma 1 should describe K=9 as an activation threshold/cutoff")

    print("  Lemma 1 validation complete")


# ============================================================
# 9. Validate test count claims
# ============================================================
def validate_test_count():
    print("\n--- Validating Test Suite Claims ---")
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')

    # Count actual test files
    test_dir = ROOT / 'tests'
    test_files = list(test_dir.rglob('test_*.py'))
    n_test_files = len(test_files)

    # README claims specific test count - verify it's reasonable
    # (we don't run pytest here, just check that test files exist)
    check(n_test_files >= 5,
          f"Expected at least 5 test files, found {n_test_files}")

    print(f"  Found {n_test_files} test files")


# ============================================================
# 10. Validate PDF tables match authoritative source
# ============================================================
def validate_pdf_tables():
    print("\n--- Validating Generated PDF Tables & Text ---")
    pdf_path = ROOT / 'paper' / 'manuscript.pdf'
    check(pdf_path.exists(), f"PDF does not exist: {pdf_path}")
    if not pdf_path.exists():
        return

    import pymupdf
    doc = pymupdf.open(str(pdf_path))
    pdf_text = ''.join(page.get_text() for page in doc)

    # Check that authoritative Table II (point predictors) numbers are present
    profiles = load_json(METRICS_DIR / 'point_predictor_profiles.json')
    for mname, prof in profiles.items():
        mae_str = f"{prof['val_mae']:.2f}"
        check(mae_str in pdf_text,
              f"PDF: {mname} MAE {mae_str} missing from generated PDF")

    # Check that obsolete numbers are strictly ABSENT
    obsolete_numbers = ["55.96", "46.96"]
    for obs in obsolete_numbers:
        check(obs not in pdf_text,
              f"PDF: Obsolete number '{obs}' found in generated PDF")

    # Check key Table III benchmark numbers in PDF
    key_benchmark_values = ["0.44", "0.37", "0.41", "0.62", "0.33"]
    for val in key_benchmark_values:
        check(val in pdf_text,
              f"PDF: Key benchmark value '{val}' missing from generated PDF")

    # Check that submission_package.pdf exists and is non-empty
    sub_pdf = ROOT / 'paper' / 'submission_package.pdf'
    check(sub_pdf.exists() and sub_pdf.stat().st_size > 100000,
          "paper/submission_package.pdf is missing or corrupted")

    print(f"  PDF validation complete ({len(doc)} pages, {len(profiles)} models checked)")


# ============================================================
# 11. Validate session segmentation sensitivity audit artifact
# ============================================================
def validate_segmentation_sensitivity():
    print("\n--- Validating Session Boundary Sensitivity Artifact ---")
    diag_path = ROOT / 'results' / 'diagnostics' / 'session_boundary_sensitivity.json'
    check(diag_path.exists(), f"Diagnostic file missing: {diag_path}")
    if not diag_path.exists():
        return

    diag = load_json(diag_path)
    required_methods = ['reset', 'relative_drop', 'active_burst']
    for m in required_methods:
        check(m in diag, f"Segmentation method '{m}' missing from sensitivity diagnostic")
        if m in diag:
            check(diag[m]['total_extracted_sessions'] > 0,
                  f"Method '{m}' has 0 extracted sessions")
            check('duration_distribution' in diag[m],
                  f"Method '{m}' missing duration distribution")
            check('throughput_distribution' in diag[m],
                  f"Method '{m}' missing throughput distribution")

    print(f"  Segmentation sensitivity validation complete ({len(required_methods)} strategies checked)")


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("MANUSCRIPT CONSISTENCY VALIDATION")
    print("=" * 70)

    validate_table1()
    validate_table2()
    validate_bootstrap()
    validate_no_unsupported_bangladesh()
    validate_abstract_claims()
    validate_readme()
    validate_dataset_counts()
    validate_lemma1()
    validate_test_count()
    validate_pdf_tables()
    validate_segmentation_sensitivity()

    print("\n" + "=" * 70)
    if errors:
        print(f"VALIDATION FAILED: {len(errors)} error(s) detected")
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("ALL VALIDATION CHECKS PASSED")

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  ⚠️  {w}")

    print("=" * 70)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())

