"""End-to-end automated reproduction pipeline for the research benchmark."""
import os
import sys
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_step(step_num: int, title: str, cmd: list):
    print('\n' + '='*75)
    print(f'STEP {step_num}: {title}')
    print('='*75)
    t0 = time.time()
    result = subprocess.run([sys.executable] + cmd, cwd=ROOT)
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f'ERROR: Step {step_num} failed with return code {result.returncode}')
        sys.exit(result.returncode)
    print(f'Step {step_num} completed successfully in {elapsed:.2f}s.')

def main():
    print('='*75)
    print('CELLULAR THROUGHPUT BENCHMARK: FULL REPRODUCIBILITY PIPELINE')
    print('='*75)
    total_start = time.time()
    
    # Step 1: Verify data integrity and acquisition manifest
    run_step(1, 'Verify Raw Datasets and Pinned Cryptographic Checksums',
             ['scripts/download_data.py', '--verify-only'])
             
    # Step 2: Run unit and causality test suite
    run_step(2, 'Run Unit and Leakage Integrity Test Suite',
             ['-m', 'pytest', 'tests/'])
             
    # Step 3: Run full experimental benchmark and generate figures & tables
    run_step(3, 'Execute Point Predictors, Transfer Regimes, and Conformal Calibration',
             ['src/experiments/runner.py'])
             
    # Step 4: Run ablation studies, sensitivity, CS-CP, and SLA analyses
    run_step(4, 'Execute Fallback Sensitivity, Pareto Frontiers, CS-CP, and SLA Economic Analysis',
             ['src/experiments/ablations.py'])
             
    # Step 5: Build interactive web dashboard
    run_step(5, 'Build Standalone Interactive Web Dashboard',
             ['scripts/build_web_demo.py'])
             
    total_time = time.time() - total_start
    print('\n' + '='*75)
    print(f'PIPELINE COMPLETE: All steps reproduced in {total_time:.2f}s.')
    print(f'Artifacts available in: {ROOT / "results"} and {ROOT / "paper"}')
    print('='*75)

if __name__ == '__main__':
    main()

