"""Master reproduction entry point executing full data verification, tests, and benchmarks."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.reproduce_experiments import main

if __name__ == '__main__':
    main()

