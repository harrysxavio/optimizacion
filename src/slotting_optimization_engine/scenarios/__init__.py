"""Scenario/model comparison helpers for analytical slotting what-if review."""

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

__all__ = [
    "SCENARIO_NOTE",
    "ScenarioConfig",
    "build_default_scenarios",
    "build_scenario_action_mix",
    "build_scenario_comparison",
    "build_scenario_summary",
    "load_scenario_inputs",
    "save_scenario_outputs",
]
