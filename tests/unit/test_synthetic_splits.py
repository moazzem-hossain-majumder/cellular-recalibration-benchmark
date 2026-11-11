"""Synthetic unit tests for data splitting, chronological ordering, and budget handling."""
import pytest
import pandas as pd
import numpy as np
from src.data.splits import (
    create_experiment_splits,
    partition_by_chronological_days,
    generate_split_summary,
    DomainSplits
)

@pytest.mark.unit
def test_synthetic_e0_partitions_are_disjoint_and_budgets_are_explicit():
    """Exercise 5-way E0 chronological partitioning and unsupported budget K handling."""
    rows = []
    for day in range(10):
        rows.append({
            "session_id": day + 1,
            "date": f"2026-01-{day + 1:02d}",
            "t_start": pd.Timestamp("2026-01-01") + pd.Timedelta(days=day),
            "target_y": float(day + 1),
            "group_id": 2,
            "has_nr": 0,
        })
    frame = pd.DataFrame(rows)
    splits = create_experiment_splits(frame, frame, budgets=[0, 1, 2, 5, 8, 9, 10, 15], experiment_type="within_domain")

    parts = [splits.train, splits.val, splits.source_calib,
             splits.target_calib_pool, splits.target_test]
    for i, left in enumerate(parts):
        for right in parts[i + 1:]:
            assert set(left["session_id"]).isdisjoint(set(right["session_id"]))
            assert set(left["date"]).isdisjoint(set(right["date"]))

    assert splits.target_prefix_sessions[0] is not None
    assert splits.target_prefix_sessions[1] is not None
    assert splits.target_prefix_sessions[15] is None, "Budget K=15 must be None when fewer than 15 sessions exist."

@pytest.mark.unit
def test_transfer_domains_with_reused_local_session_ids_are_not_misclassified_as_e0():
    """Separate datasets can restart local session IDs at zero; must not trigger E0."""
    def make_frame(start_day, offset):
        rows = []
        for i in range(10):
            rows.append({
                "session_id": i,
                "date": f"2026-02-{start_day + i:02d}",
                "t_start": pd.Timestamp("2026-02-01") + pd.Timedelta(days=start_day + i),
                "target_y": float(offset + i),
                "group_id": 2,
                "has_nr": 0,
            })
        return pd.DataFrame(rows)
    source = make_frame(1, 10)
    target = make_frame(11, 100)
    splits = create_experiment_splits(source, target, budgets=[0, 1, 2, 5, 8, 9, 10, 15], experiment_type="transfer")
    assert len(splits.train) > 0
    assert len(splits.source_calib) > 0
    assert len(splits.target_calib_pool) > 0
    assert len(splits.target_test) > 0
    assert splits.target_prefix_sessions[15] is None

@pytest.mark.unit
def test_explicit_regime_and_within_domain_parameter():
    """Verify that passing regime='E0' or experiment_type='within_domain' enforces 5-way split."""
    rows = []
    for day in range(10):
        rows.append({
            "session_id": day + 1,
            "date": f"2026-01-{day + 1:02d}",
            "t_start": pd.Timestamp("2026-01-01") + pd.Timedelta(days=day),
            "target_y": float(day + 1),
            "group_id": 2,
            "has_nr": 0,
        })
    frame = pd.DataFrame(rows)
    frame_copy = frame.copy()
    
    splits = create_experiment_splits(frame, frame_copy, budgets=[0, 1, 2, 5], regime='E0_WithinDomain', experiment_type="within_domain")
    parts = [splits.train, splits.val, splits.source_calib, splits.target_calib_pool, splits.target_test]
    for i, left in enumerate(parts):
        for right in parts[i + 1:]:
            assert set(left["session_id"]).isdisjoint(set(right["session_id"]))
            assert set(left["date"]).isdisjoint(set(right["date"]))

@pytest.mark.unit
def test_generate_split_summary_structure():
    """Verify that generate_split_summary creates valid metadata with all required fields."""
    rows = []
    for day in range(8):
        rows.append({
            "session_id": day + 1,
            "date": f"2026-01-{day + 1:02d}",
            "t_start": pd.Timestamp("2026-01-01") + pd.Timedelta(days=day),
            "target_y": float(day * 10),
            "group_id": 2,
        })
    df = pd.DataFrame(rows)
    splits = create_experiment_splits(df, df, budgets=[0, 1, 5, 10], experiment_type="within_domain")
    summary = generate_split_summary(splits, "Synthetic_Test", "Test_001")
    
    assert summary["experiment_name"] == "Synthetic_Test"
    assert "train" in summary["partitions"]
    assert "target_test" in summary["partitions"]
    assert "budget_availability" in summary
    assert summary["budget_availability"]["1"]["available"] is True
    assert summary["budget_availability"]["10"]["available"] is False


@pytest.mark.unit
def test_create_experiment_splits_requires_experiment_type():
    """Verify that omitting or passing invalid experiment_type strictly raises ValueError."""
    rows = [{"session_id": 1, "date": "2026-01-01", "t_start": pd.Timestamp("2026-01-01"), "target_y": 10.0, "group_id": 1}]
    df = pd.DataFrame(rows)
    
    # Missing experiment_type raises TypeError or ValueError
    with pytest.raises((ValueError, TypeError)):
        create_experiment_splits(df, df)  # type: ignore
        
    # Invalid experiment_type raises ValueError
    with pytest.raises(ValueError, match="Invalid experiment_type"):
        create_experiment_splits(df, df, experiment_type="unsupported_regime")


