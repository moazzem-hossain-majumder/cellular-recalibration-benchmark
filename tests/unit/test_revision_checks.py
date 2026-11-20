import pandas as pd
from scripts.select_clock_policy import select
from scripts.generate_experiment_manifest import digest


def test_selection_counts_missing_positives_and_resolves_ties():
    rows = pd.DataFrame([
        (0, 10, 0, 0, 0.0, 0),
        (1, 10, 1, 1, 0.9, 9),
        (2, 10, 0, 1, 0.5, 10),
        (3, 10, 0, 1, 0.5, 9),
        (4, 10, 0, 1, 0.5, 9),
    ], columns=['order', 'issued', 'violations', 'unresolved', 'u', 'k'])
    assert select(rows)['order'] == 3
    assert select(rows.iloc[:2])['order'] == 0


def test_manifest_handles_checkout_line_endings(tmp_path):
    for extension, same in [('md', True), ('pdf', False)]:
        file = tmp_path / f'example.{extension}'
        file.write_bytes(b'a\nb')
        original = digest(file)
        file.write_bytes(b'a\r\nb')
        assert (digest(file) == original) == same
