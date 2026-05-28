"""
Phase 6 — Scenario C: Scenario registry.

Maps scenario names to their classes so the CLI and pipeline can
resolve scenarios by string identifier without hard-coding imports.
"""

from __future__ import annotations

from slotting_optimization_engine.simulation.pipeline import SimulationScenario
from slotting_optimization_engine.simulation.throughput import ThroughputScenario
from slotting_optimization_engine.simulation.travel import TravelScenario
from slotting_optimization_engine.simulation.workload import WorkloadScenario

# ── Built-in registry ────────────────────────────────────────────────────────

BUILTIN_SCENARIOS: dict[str, type[SimulationScenario]] = {
    "travel": TravelScenario,
    "workload": WorkloadScenario,
    "throughput": ThroughputScenario,
}

# ── ALL_SCENARIOS constant — used by CLI --list-scenarios ────────────────────

ALL_SCENARIOS: dict[str, str] = {
    name: cls().description
    for name, cls in BUILTIN_SCENARIOS.items()
}
