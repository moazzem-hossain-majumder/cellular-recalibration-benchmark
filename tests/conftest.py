"""Pytest configuration and test fixtures for unit and integration test suites."""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_822_PATH = ROOT / 'data' / 'raw' / '8224890' / 'Throughput Tests - Speedtest - Active Measurements.csv'
DATA_140_DIR = ROOT / 'data' / 'extracted' / '14073311' / 'Active Performance Dataset - 1' / 'Ookla Speedtests' / 'Op1 and Op2 - Italy'

RAW_DATA_AVAILABLE = DATA_822_PATH.exists() and DATA_140_DIR.exists()

skip_if_no_raw_data = pytest.mark.skipif(
    not RAW_DATA_AVAILABLE,
    reason="External raw Zenodo measurement archives not found on disk. Run scripts/download_data.py to obtain."
)

