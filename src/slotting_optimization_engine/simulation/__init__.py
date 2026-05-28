"""
simulation — Operational simulation engine (Phase 6).

Simulates the operational impact of Phase 5 SKU-to-zone optimisation:
    - Travel distance and time comparison (before / after).
    - Zone workload balance simulation.
    - Throughput estimation under multiple scenarios.
"""

from __future__ import annotations

from slotting_optimization_engine.simulation.config import (
    SIMULATION_CAVEAT,
    SimulationConfig,
)
from slotting_optimization_engine.simulation.report import (
    build_simulation_report,
    save_simulation_outputs,
)
from slotting_optimization_engine.simulation.throughput import (
    estimate_throughput,
)
from slotting_optimization_engine.simulation.travel import (
    build_sku_current_zone,
    build_sku_optimized_zone,
    load_simulation_inputs,
    simulate_travel,
)
from slotting_optimization_engine.simulation.workload import (
    gini_coefficient,
    simulate_workload,
)

__all__ = [
    "SIMULATION_CAVEAT",
    "SimulationConfig",
    "build_sku_current_zone",
    "build_sku_optimized_zone",
    "build_simulation_report",
    "estimate_throughput",
    "gini_coefficient",
    "load_simulation_inputs",
    "save_simulation_outputs",
    "simulate_travel",
    "simulate_workload",
]
