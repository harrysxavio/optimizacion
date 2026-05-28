"""Tests for Phase 4 scenario/model comparison."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from slotting_optimization_engine.scenarios.comparison import (
    SCENARIO_NOTE,
    ScenarioConfig,
    build_default_scenarios,
    build_scenario_action_mix,
    build_scenario_comparison,
    build_scenario_summary,
    load_scenario_inputs,
    save_scenario_outputs,
)

PROJ_ROOT = Path(__file__).resolve().parent.parent.parent


def test_default_scenarios_include_expected_lenses() -> None:
    scenarios = build_default_scenarios(top_n=3)

    assert [scenario.name for scenario in scenarios] == [
        "baseline",
        "demand_first",
        "capacity_first",
        "balanced_review",
    ]
    assert all(scenario.top_n == 3 for scenario in scenarios)


def test_scenario_comparison_applies_weights_and_sorting() -> None:
    scenarios = [
        ScenarioConfig(
            name="capacity_first",
            description="test capacity emphasis",
            top_n=2,
            action_weights={"review_zone_capacity_pressure": 2.0},
            entity_type_weights={"zone": 1.5},
        )
    ]

    comparison = build_scenario_comparison(_minimal_scores(), scenarios)

    assert comparison["scenario"].eq("capacity_first").all()
    assert comparison.iloc[0]["entity_type"] == "zone"
    assert comparison.iloc[0]["candidate_action"] == "review_zone_capacity_pressure"
    assert comparison.iloc[0]["scenario_weighted_score"] == 180.0
    assert comparison["scenario_rank"].tolist() == [1, 2]
    assert comparison["scenario_note"].eq(SCENARIO_NOTE).all()


def test_action_mix_and_summary_return_comparable_metrics() -> None:
    scenarios = build_default_scenarios(top_n=2)
    comparison = build_scenario_comparison(_minimal_scores(), scenarios)

    action_mix = build_scenario_action_mix(comparison)
    summary = build_scenario_summary(comparison, scenarios)

    assert set(action_mix["scenario"]) == {scenario.name for scenario in scenarios}
    assert action_mix["selected_share"].between(0, 1).all()
    assert set(summary["scenario"]) == {scenario.name for scenario in scenarios}
    assert summary["selected_count"].eq(2).all()
    assert summary["scenario_note"].eq(SCENARIO_NOTE).all()


def test_load_scenario_inputs_reports_missing_phase_3_outputs(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="run_scoring.py"):
        load_scenario_inputs(tmp_path)


def test_save_scenario_outputs_writes_expected_csv_files(tmp_path) -> None:
    scenarios = build_default_scenarios(top_n=2)
    comparison = build_scenario_comparison(_minimal_scores(), scenarios)
    action_mix = build_scenario_action_mix(comparison)
    summary = build_scenario_summary(comparison, scenarios)

    paths = save_scenario_outputs({
        "comparison": comparison,
        "action_mix": action_mix,
        "summary": summary,
    }, tmp_path)

    assert paths["comparison"].name == "scenario_comparison.csv"
    assert paths["action_mix"].name == "scenario_action_mix.csv"
    assert paths["summary"].name == "scenario_summary.csv"
    assert all(path.is_file() for path in paths.values())


def test_run_scenarios_script_is_importable() -> None:
    spec = importlib.util.spec_from_file_location(
        "run_scenarios", PROJ_ROOT / "scripts" / "run_scenarios.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert callable(module.main)


def _minimal_scores() -> pd.DataFrame:
    return pd.DataFrame({
        "entity_type": ["sku", "sku", "zone", "sku"],
        "entity_id": ["SKU-1", "SKU-2", "Z-1", "SKU-3"],
        "candidate_action": [
            "review_high_demand_far_sku",
            "review_slow_mover_in_premium_zone",
            "review_zone_capacity_pressure",
            "review_high_demand_far_sku",
        ],
        "opportunity_score": [100.0, 70.0, 60.0, 30.0],
        "priority": ["high", "high", "medium", "low"],
        "rank": [1, 2, 3, 4],
        "reason": ["reason"] * 4,
        "business_rule_state": ["inferred / pending confirmation"] * 4,
    })
