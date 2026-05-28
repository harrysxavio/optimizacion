"""
Phase 6 — Throughput estimation.

Estimates how the travel-time savings from Phase 5 optimisation could
translate into increased order throughput (orders per hour) under three
scenarios: optimistic, balanced / moderate, and conservative.

All estimates are based on *inferred* assumptions and MUST be validated
against real operational data.
"""

from __future__ import annotations

import pandas as pd

from slotting_optimization_engine.simulation.config import (
    SIMULATION_CAVEAT,
    SimulationConfig,
)

# ── Scenario labels ──────────────────────────────────────────────────────────

OPTIMISTIC = "optimistic"
BALANCED = "balanced"
CONSERVATIVE = "conservative"
SCENARIOS = [OPTIMISTIC, BALANCED, CONSERVATIVE]

_MULT_KEY = {
    OPTIMISTIC: "optimistic_throughput_mult",
    BALANCED: "balanced_throughput_mult",
    CONSERVATIVE: "conservative_throughput_mult",
}


def estimate_throughput(
    travel_result: dict[str, object],
    config: SimulationConfig | None = None,
) -> dict[str, pd.DataFrame | dict[str, float | int]]:
    """Estimate throughput impact from travel-time savings.

    Parameters
    ----------
    travel_result : dict
        Output from ``simulate_travel()`` — must contain an ``aggregate``
        sub-dict with at least ``total_time_saved_s`` and
        ``travel_overhead_factor``.
    config : SimulationConfig | None
        Simulation parameters (scenario multipliers, shift length).

    Returns
    -------
    dict with keys:
        * ``scenario_table``  — pd.DataFrame with one row per scenario
        * ``aggregate``       — dict of recommended (balanced) metrics
    """
    config = config or SimulationConfig()
    agg = travel_result.get("aggregate", {})
    if not isinstance(agg, dict):
        raise ValueError("travel_result['aggregate'] must be a dict.")

    time_saved_s = float(agg.get("total_time_saved_s", 0.0))
    total_orders = int(agg.get("total_orders_simulated", 0))

    if total_orders <= 0:
        return {
            "scenario_table": pd.DataFrame(),
            "aggregate": {
                "note": "No orders to simulate.",
                "assumption_state": config.assumption_state,
                "simulation_caveat": SIMULATION_CAVEAT,
            },
        }

    # Baseline: current time spent per order (travel + pick)
    seconds_per_shift_productive = config.seconds_per_shift * config.productive_utilization_pct

    # Simulate current orders/hour capacity
    # Current measurement: we know total travel time for the simulated orders
    # Estimate how many orders could be picked in one shift
    avg_travel_per_order_s = (
        time_saved_s / total_orders  # approximate — assumes saved time is representative
    )

    # Baseline pick rate: how many orders could we process now?
    # For this, we need to estimate total pick time per order
    avg_pick_time_per_order_s = _estimate_pick_time_per_order(
        agg, config
    )
    avg_total_time_per_order_current = avg_travel_per_order_s + avg_pick_time_per_order_s

    if avg_total_time_per_order_current <= 0:
        return {
            "scenario_table": pd.DataFrame(),
            "aggregate": {
                "note": ("Estimated per-order time is zero or negative — "
                      "cannot estimate throughput."),
                "assumption_state": config.assumption_state,
                "simulation_caveat": SIMULATION_CAVEAT,
            },
        }

    orders_per_shift_current = seconds_per_shift_productive / avg_total_time_per_order_current

    # Scenario rows
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        mult = getattr(config, _MULT_KEY[scenario])
        # The multiplier represents the % improvement in throughput
        # If we save X% travel time, we can process Y% more orders
        # Simple model: throughput scales inversely with time per order
        time_reduction_pct = (
            time_saved_s / (time_saved_s + avg_pick_time_per_order_s * total_orders)
            if (time_saved_s + avg_pick_time_per_order_s * total_orders) > 0
            else 0.0
        )
        # Apply the scenario multiplier to the base time reduction
        effective_reduction = time_reduction_pct * mult
        if effective_reduction < 1:
            orders_per_shift_optimized = orders_per_shift_current / (1 - effective_reduction)
        else:
            orders_per_shift_optimized = orders_per_shift_current * 2  # cap at 2x

        rows.append({
            "scenario": scenario,
            "multiplier": mult,
            "orders_per_shift_current": round(orders_per_shift_current, 1),
            "orders_per_shift_optimized": round(orders_per_shift_optimized, 1),
            "throughput_gain_pct": round(
                ((orders_per_shift_optimized / orders_per_shift_current) - 1) * 100, 2
            ),
            "assumption_state": config.assumption_state,
            "simulation_caveat": SIMULATION_CAVEAT,
        })

    scenario_table = pd.DataFrame(rows)

    # The balanced scenario is the recommended estimate
    balanced_row = rows[1] if len(rows) > 1 else rows[0]  # type: ignore[assignment]

    return {
        "scenario_table": scenario_table,
        "aggregate": {
            "recommended_scenario": BALANCED,
            "orders_per_shift_current": balanced_row["orders_per_shift_current"],  # type: ignore[index]
            "orders_per_shift_optimized": balanced_row["orders_per_shift_optimized"],  # type: ignore[index]
            "throughput_gain_pct": balanced_row["throughput_gain_pct"],  # type: ignore[index]
            "productive_seconds_per_shift": seconds_per_shift_productive,
            "avg_travel_time_per_order_s": round(avg_travel_per_order_s, 2),
            "avg_pick_time_per_order_s": round(avg_pick_time_per_order_s, 2),
            "total_time_saved_s": round(time_saved_s, 2),
            "assumption_state": config.assumption_state,
            "simulation_caveat": SIMULATION_CAVEAT,
        },
    }


def _estimate_pick_time_per_order(
    aggregate: dict[str, object],
    config: SimulationConfig,
) -> float:
    """Estimate average pick time per order based on config.

    Uses ``config.pick_time_per_sku_s`` multiplied by a default of
    5 SKUs per order (matching the synthetic data generator).
    """
    _ = aggregate  # kept for future use with real SKU-count data
    return float(config.pick_time_per_sku_s) * 5
