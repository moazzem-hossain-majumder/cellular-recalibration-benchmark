"""Audit tests for locked Path A PACER results and untouched cohort invariants."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validate_pacer import verify_lock_and_artifacts


def test_pacer_locked_study_audit_passes():
    report = verify_lock_and_artifacts()
    assert report['preregistration_lock_verified'] is True
    assert report['prospective_trips_collected'] == 0
    assert report['theorem1_mean_excess_checks']['all_within_bound'] is True
    assert report['physical_clusters']['untouched_heldout'] >= 20
    assert report['physical_clusters']['retrospective'] == 16
