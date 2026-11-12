"""Rebuild and check the real-data study and its publication artifacts."""
import json
from datetime import datetime, timezone
import time
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def main():
    stages = []
    for args in [
        ['scripts/prepare_ookla_traces.py'], ['scripts/reproduce_experiments.py'],
        ['scripts/audit_data_quality.py'], ['scripts/audit_trace_filters.py'],
        ['scripts/audit_session_segmentation.py'], ['scripts/validate_session_boundaries.py'],
        ['scripts/audit_cluster_inference.py'], ['scripts/build_paper_html.py'],
        ['scripts/validate_manuscript_consistency.py'], ['-m','pytest','-ra','--junitxml=results/runs/final_tests.xml'],

    ]:
        start = datetime.now(timezone.utc).isoformat()
        tick = time.monotonic()
        result = subprocess.run([sys.executable,*args],cwd=ROOT)
        stages.append(dict(command=['python',*args],start_utc=start,end_utc=datetime.now(timezone.utc).isoformat(),seconds=round(time.monotonic()-tick,2),exit_code=result.returncode))
        (ROOT/'results/runs/execution.json').write_text(json.dumps(stages,indent=2)+'\n')
        result.check_returncode()
    subprocess.run([sys.executable,'scripts/generate_experiment_manifest.py'],cwd=ROOT,check=True)
if __name__=='__main__':
    main()
