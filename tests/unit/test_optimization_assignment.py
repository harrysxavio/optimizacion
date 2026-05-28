"""Tests for Phase 5 controlled optimization assignment prototype."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from slotting_optimization_engine.optimization.assignment import (
    OPTIMIZATION_CAVEAT,
    AssignmentConfig,
    build_assignment_cost_matrix,
    build_optimization_outputs,
    load_optimization_inputs,
    save_optimization_outputs,
    select_candidate_skus,
    solve_assignment,
)

PROJ_ROOT = Path(__file__).resolve().parent.parent.parent


def test_cost_matrix_contains_all_sku_zone_slot_pairs() -> None:
    config = AssignmentConfig(top_n_skus=2, max_slots_per_zone=2)
    candidates = select_candidate_skus(_priority_queue(), config)

    cost_matrix = build_assignment_cost_matrix(
        candidates=candidates,
        skus=_skus(),
        zones=_zones(),
        slotting_diagnostics=_slotting_diagnostics(),
        zone_diagnostics=_zone_diagnostics(),
        scenario_comparison=_scenario_comparison(),
        config=config,
    )

    assert set(cost_matrix["sku_id"]) == {"SKU-1", "SKU-2"}
    assert cost_matrix["target_zone_slot"].nunique() >= 2
    assert cost_matrix["assignment_cost"].between(0, 1).all()
    assert cost_matrix["optimization_caveat"].eq(OPTIMIZATION_CAVEAT).all()


def test_assignment_shape_is_one_zone_per_selected_sku() -> None:
    outputs = build_optimization_outputs(
        _inputs(), AssignmentConfig(top_n_skus=2), force_fallback=True
    )

    assignments = outputs["assignments"]

    assert len(assignments) == 2
    assert assignments["sku_id"].is_unique
    assert assignments["target_zone_id"].notna().all()
    assert assignments["solver_method"].eq("greedy_fallback").all()


def test_assignment_is_deterministic_with_fallback() -> None:
    outputs_a = build_optimization_outputs(
        _inputs(), AssignmentConfig(top_n_skus=2), force_fallback=True
    )
    outputs_b = build_optimization_outputs(
        _inputs(), AssignmentConfig(top_n_skus=2), force_fallback=True
    )

    pd.testing.assert_frame_equal(outputs_a["assignments"], outputs_b["assignments"])


def test_load_optimization_inputs_reports_missing_phase_outputs(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="run_scenarios.py"):
        load_optimization_inputs(processed_dir=tmp_path, synthetic_dir=tmp_path)


def test_save_optimization_outputs_writes_expected_csv_files(tmp_path) -> None:
    outputs = build_optimization_outputs(
        _inputs(), AssignmentConfig(top_n_skus=2), force_fallback=True
    )

    paths = save_optimization_outputs(outputs, tmp_path)

    assert paths["assignments"].name == "optimization_assignments.csv"
    assert paths["summary"].name == "optimization_summary.csv"
    assert paths["cost_matrix"].name == "optimization_cost_matrix.csv"
    assert all(path.is_file() for path in paths.values())


def test_solver_method_is_recorded_for_fallback() -> None:
    cost_matrix = build_assignment_cost_matrix(
        candidates=select_candidate_skus(_priority_queue(), AssignmentConfig(top_n_skus=2)),
        skus=_skus(),
        zones=_zones(),
        slotting_diagnostics=_slotting_diagnostics(),
        zone_diagnostics=_zone_diagnostics(),
        scenario_comparison=None,
    )

    assignments = solve_assignment(cost_matrix, force_fallback=True)

    assert assignments["solver_method"].eq("greedy_fallback").all()


def test_run_optimization_script_is_importable() -> None:
    spec = importlib.util.spec_from_file_location(
        "run_optimization", PROJ_ROOT / "scripts" / "run_optimization.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert callable(module.main)


def _inputs() -> dict[str, pd.DataFrame]:
    return {
        "priority_queue": _priority_queue(),
        "slotting_diagnostics": _slotting_diagnostics(),
        "zone_diagnostics": _zone_diagnostics(),
        "skus": _skus(),
        "zones": _zones(),
        "scenario_comparison": _scenario_comparison(),
    }


def _priority_queue() -> pd.DataFrame:
    return pd.DataFrame({
        "queue_position": [1, 2, 3],
        "priority": ["high", "high", "medium"],
        "opportunity_score": [95.0, 80.0, 70.0],
        "entity_type": ["sku", "sku", "zone"],
        "entity_id": ["SKU-1", "SKU-2", "Z-1"],
        "candidate_action": [
            "review_high_demand_far_sku",
            "review_slow_mover_in_premium_zone",
            "review_zone_capacity_pressure",
        ],
        "reason": ["reason"] * 3,
        "business_rule_state": ["inferred / pending confirmation"] * 3,
        "scoring_note": ["note"] * 3,
    })


def _skus() -> pd.DataFrame:
    return pd.DataFrame({
        "sku_id": ["SKU-1", "SKU-2"],
        "category": ["A", "B"],
        "subcategory": ["A1", "B1"],
        "unit_volume": [1.0, 2.0],
        "unit_weight": [1.0, 2.0],
        "rotation_class": ["A", "D"],
        "avg_daily_demand": [100.0, 10.0],
    })


def _zones() -> pd.DataFrame:
    return pd.DataFrame({
        "zone_id": ["Z-1", "Z-2"],
        "zone_type": ["picking", "bulk"],
        "priority_level": [1, 5],
        "distance_to_dispatch": [10.0, 100.0],
        "max_volume_capacity": [100.0, 100.0],
        "max_weight_capacity": [100.0, 100.0],
    })


def _slotting_diagnostics() -> pd.DataFrame:
    return pd.DataFrame({
        "sku_id": ["SKU-1", "SKU-2"],
        "total_demand": [100.0, 10.0],
        "diagnostic_count": [1, 1],
        "min_priority_level": [5, 1],
        "distance_to_dispatch": [100.0, 10.0],
    })


def _zone_diagnostics() -> pd.DataFrame:
    return pd.DataFrame({
        "zone_id": ["Z-1", "Z-2"],
        "avg_utilization_pct": [50.0, 20.0],
        "overutilized_zone_flag": [False, False],
    })


def _scenario_comparison() -> pd.DataFrame:
    return pd.DataFrame({
        "scenario": ["baseline", "baseline"],
        "entity_type": ["sku", "sku"],
        "entity_id": ["SKU-1", "SKU-2"],
        "scenario_weighted_score": [95.0, 80.0],
    })
