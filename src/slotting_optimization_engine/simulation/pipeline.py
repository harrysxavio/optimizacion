"""
Phase 6 — Scenario C: Reusable simulation pipeline framework.

Provides the abstract base class for pluggable simulation scenarios,
a shared context dataclass, and a pipeline that executes scenarios
in dependency order.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from slotting_optimization_engine.simulation.config import SimulationConfig


@dataclass
class SimulationContext:
    """Shared context passed between pipeline scenarios.

    All loaded DataFrames are stored here so each scenario can access
    whatever it needs without reloading data.
    """

    # ── Loaded input DataFrames ───────────────────────────────────────────
    orders: pd.DataFrame | None = None
    order_lines: pd.DataFrame | None = None
    zones: pd.DataFrame | None = None
    locations: pd.DataFrame | None = None
    inventory: pd.DataFrame | None = None
    optimization_assignments: pd.DataFrame | None = None

    # ── SKU→zone mappings (built once) ───────────────────────────────────
    sku_current_zone: pd.DataFrame | None = None
    sku_optimized_zone: pd.DataFrame | None = None

    # ── Simulation config ─────────────────────────────────────────────────
    config: SimulationConfig = field(default_factory=SimulationConfig)

    # ── Accumulated results from previous scenarios ───────────────────────
    # Each scenario stores its result dict under its name so downstream
    # scenarios (e.g. Throughput → depends on Travel) can reference them.
    results: dict[str, Any] = field(default_factory=dict)

    def get_result(self, scenario_name: str) -> dict[str, Any] | None:
        """Get the result dict from a previously-run scenario."""
        return self.results.get(scenario_name)


class SimulationScenario(ABC):
    """Abstract base for a pluggable simulation scenario.

    Subclasses must define ``name`` (unique identifier) and implement
    ``run(context)`` which reads from the shared context and returns
    a dict with keys like ``"aggregate"``, ``"order_detail"``, etc.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique scenario name (used in CLI --scenarios and registry)."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what this scenario estimates."""
        return ""

    @abstractmethod
    def run(self, context: SimulationContext) -> dict[str, Any]:
        """Execute this scenario against the shared context.

        Parameters
        ----------
        context : SimulationContext
            Shared data and previous scenario results.

        Returns
        -------
        dict
            Scenario-specific results (structure varies by scenario).
        """
        ...


class SimulationPipeline:
    """Orchestrates a sequence of SimulationScenario executions.

    Usage::

        pipeline = SimulationPipeline(scenarios=["travel", "workload", "throughput"])
        results = pipeline.run(context)
    """

    def __init__(
        self,
        scenarios: list[str],
        registry: dict[str, type[SimulationScenario]] | None = None,
    ):
        self._scenario_names = list(scenarios)
        self._registry = registry or {}

    @property
    def scenario_names(self) -> list[str]:
        return list(self._scenario_names)

    def run(self, context: SimulationContext) -> dict[str, Any]:
        """Run every scenario in order, feeding results into the context.

        Returns
        -------
        dict mapping each scenario name to its result dict.
        """
        results: dict[str, Any] = {}
        for name in self._scenario_names:
            cls = self._registry.get(name)
            if cls is None:
                raise ValueError(
                    f"Unknown scenario '{name}'. "
                    f"Available: {sorted(self._registry)}"
                )
            scenario = cls()
            outcome = scenario.run(context)
            context.results[name] = outcome
            results[name] = outcome
        return results
