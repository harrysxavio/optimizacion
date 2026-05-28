"""Tests for Phase 3 scoring and prioritization."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from slotting_optimization_engine.domain.constants import Features, Skus, Zones
from slotting_optimization_engine.scoring.prioritization import (
    BUSINESS_RULE_STATE,
    ScoringConfig,
    build_priority_queue,
    build_scoring_summary,
    build_slotting_opportunity_scores,
    load_diagnostic_inputs,
    save_scoring_outputs,
)

PROJ_ROOT = Path(__file__).resolve().parent.parent.parent


def test_opportunity_scores_stay_in_zero_to_100_range() -> None:
    scores = build_slotting_opportunity_scores(_minimal_diagnostics())

    assert scores["opportunity_score"].between(0, 100).all()
    assert scores["business_rule_state"].eq(BUSINESS_RULE_STATE).all()
    assert set(scores["candidate_action"]) == {
        "review_high_demand_far_sku",
        "review_slow_mover_in_premium_zone",
        "review_zone_capacity_pressure",
    }


def test_priority_labels_include_high_medium_and_low() -> None:
    scores = build_slotting_opportunity_scores(
        _minimal_diagnostics(),
        ScoringConfig(high_priority_min_score=70.0, medium_priority_min_score=40.0),
    )

    assert {"high", "medium", "low"}.issubset(set(scores["priority"]))


def test_priority_queue_is_sorted_by_score_descending() -> None:
    scores = build_slotting_opportunity_scores(_minimal_diagnostics())
    queue = build_priority_queue(scores)

    assert queue["opportunity_score"].is_monotonic_decreasing
    assert queue["queue_position"].tolist() == list(range(1, len(queue) + 1))
    assert queue.iloc[0]["opportunity_score"] >= queue.iloc[-1]["opportunity_score"]


def test_load_diagnostic_inputs_reports_missing_phase_2_outputs(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="run_diagnostics.py"):
        load_diagnostic_inputs(tmp_path)


def test_save_scoring_outputs_writes_expected_csv_files(tmp_path) -> None:
    scores = build_slotting_opportunity_scores(_minimal_diagnostics())
    queue = build_priority_queue(scores)
    summary = build_scoring_summary(scores, queue)

    paths = save_scoring_outputs({
        "opportunity_scores": scores,
        "priority_queue": queue,
        "summary": summary,
    }, tmp_path)

    assert paths["opportunity_scores"].name == "slotting_opportunity_scores.csv"
    assert paths["priority_queue"].name == "priority_recommendation_queue.csv"
    assert paths["summary"].name == "scoring_summary.csv"
    assert all(path.is_file() for path in paths.values())


def test_run_scoring_script_is_importable() -> None:
    spec = importlib.util.spec_from_file_location(
        "run_scoring", PROJ_ROOT / "scripts" / "run_scoring.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert callable(module.main)


def _minimal_diagnostics() -> dict[str, pd.DataFrame]:
    slotting = pd.DataFrame({
        Skus.SKU_ID: ["S-fast", "S-slow", "S-neutral"],
        Skus.CATEGORY: ["cat-a", "cat-b", "cat-c"],
        Skus.ROTATION_CLASS: ["A", "D", "B"],
        Features.TOTAL_DEMAND: [100.0, 1.0, 30.0],
        Features.ORDER_COUNT: [10, 1, 3],
        "location_count": [1, 1, 1],
        "zone_count": [1, 1, 1],
        Zones.DISTANCE_TO_DISPATCH: [90.0, 10.0, 20.0],
        Zones.PRIORITY_LEVEL: [4.0, 1.0, 2.0],
        "min_priority_level": [4.0, 1.0, 2.0],
        "high_demand_threshold": [80.0, 80.0, 80.0],
        "low_demand_threshold": [10.0, 10.0, 10.0],
        "long_distance_threshold": [70.0, 70.0, 70.0],
        "is_high_demand": [True, False, False],
        "is_low_demand_or_rotation": [False, True, False],
        "has_long_distance_placement": [True, False, False],
        "has_low_priority_placement": [True, False, False],
        "occupies_premium_zone": [False, True, True],
        "high_demand_poor_placement_flag": [True, False, False],
        "low_demand_premium_zone_flag": [False, True, False],
        "diagnostic_count": [1, 1, 0],
        "diagnostic_severity": ["review", "review", "none"],
        "business_rule_state": [BUSINESS_RULE_STATE, BUSINESS_RULE_STATE, BUSINESS_RULE_STATE],
    })
    zone = pd.DataFrame({
        Zones.ZONE_ID: ["Z-full", "Z-empty"],
        Zones.ZONE_TYPE: ["picking", "bulk"],
        Zones.PRIORITY_LEVEL: [1, 4],
        Zones.DISTANCE_TO_DISPATCH: [10.0, 90.0],
        "avg_volume_util_pct": [95.0, 10.0],
        "avg_weight_util_pct": [85.0, 5.0],
        "location_count": [10, 10],
        "over_capacity_location_count": [1, 0],
        "assigned_sku_count": [30, 2],
        "low_demand_sku_count": [8, 0],
        "slow_rotation_sku_count": [8, 0],
        "avg_utilization_pct": [90.0, 7.5],
        "overutilized_zone_flag": [True, False],
        "underutilized_zone_flag": [False, True],
        "premium_zone_slow_mover_flag": [True, False],
        "business_rule_state": [BUSINESS_RULE_STATE, BUSINESS_RULE_STATE],
    })
    return {
        "slotting": slotting,
        "location": pd.DataFrame(),
        "zone": zone,
        "category": pd.DataFrame(),
    }
