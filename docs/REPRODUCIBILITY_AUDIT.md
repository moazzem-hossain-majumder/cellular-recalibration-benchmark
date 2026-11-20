# Reproducibility audit

## Executed independent working-copy reproduction

A filesystem snapshot of the pre-MARUR repository at base commit a50c114ed2a5cffcb3a624c7b3ca7b63693c9159 was created in a separate temporary directory. Raw public archives and publisher files were copied; mutable Irish work products and extracted Rome traces were regenerated. The full scripts/reproduce_all.py process completed with exit code 0, including paper generation, consistency validation and 71 tests. This used the existing installed Python 3.11 environment. It verifies execution isolation and reconstruction from cached raw inputs. It does not test a newly provisioned operating system or fresh dependency resolution.

The machine-readable receipt includes every stage and its actual timestamps. The snapshot excludes the later MARUR implementation, which has its own execution receipt and checks. [Isolated baseline receipt](../results/runs/isolated_baseline_reproduction.json)

The earlier read-only audit recorded successful hosted runs 44692057773 and 44692043287 at the baseline SHA. Those hosted jobs precede the current local edits. [Baseline Actions run](https://github.com/moazzem-hossain-majumder/cellular-recalibration-benchmark/actions/runs/44692057773)

## Packaging and licensing

The package metadata previously advertised Apache-2.0 without a matching repository LICENSE. That unsupported declaration was removed. The author must choose and supply a code license before distributing a licensed software release. No license was selected on the author's behalf.

The previous discovery rule produced top-level modules such as data and models while source imports use src.data and src.models. Discovery now includes src and src.* explicitly. Verify installation from an isolated target to ensure imports resolve outside the checkout.

Rome releases identify CC BY 4.0. NUWiNS identifies CC0. The Irish repository has GPL-3.0 but the separately downloaded production archive's data terms need care. Norwegian source pages provide citation instructions without an explicit raw-data license. Preserve attribution, link acquisition sources, and distribute code plus hashes and instructions; avoid including raw archives in the submission ZIP. See EXTERNAL_DATA_PROVENANCE.md and EXTERNAL_VALIDATION_PLAN.md for per-release distinctions.

## Reproduction procedure

Use Python 3.11 and requirements.txt with constraints-research.txt. Install a platform-appropriate PyTorch wheel and Tectonic, or set the TECTONIC executable path. Run scripts/reproduce_all.py from an isolated checkout. Archive results/runs/execution.json and the JUnit report. The manifest is generated after the final artifacts and verified with scripts/generate_experiment_manifest.py --verify. Text hashes normalize line endings; raw source bytes retain exact acquisition hashes.

MARUR needs the existing frozen point forecasts, full Rome raw clock inputs, and prior US/Irish ledgers. scripts/run_marur.py regenerates the complete scheduled roster and controller outputs. The sequential actions, responses and opportunities are saved separately. Configured query budgets are distinct from measured labels and from uncharged lag-telemetry feedback.
## MARUR stage verification and package import

The later isolated run reproduced actions.csv.gz, responses.csv.gz, opportunities.csv.gz, dates.csv and both paired-contrast files exactly. All 576 summary rows also matched after excluding elapsed-time measurements. The isolated stage independently validated 160,032 actions and 5,960 response events. This extends the completed baseline pipeline without claiming a fresh full run of every unchanged benchmark stage after the new code was added. [Isolated MARUR receipt](../results/runs/isolated_marur_reproduction.json)

The corrected wheel was installed with no dependencies into a temporary target, and src.evaluation.marur imported successfully while the process working directory was outside the checkout. That demonstrates the package namespace fix in the existing research environment.

Final local validation passed all 78 tests, including seven MARUR causality, timing, missing-response and scheduled-roster tests. The revised manuscript contains 14 tables and eight figures; the combined cover letter and manuscript PDF has 15 pages. The new results table and figure were visually inspected for layout and legibility.
