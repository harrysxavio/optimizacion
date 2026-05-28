"""
Phase 6 — Travel time and distance simulation.

Compares the estimated travel distance (and time) for the CURRENT SKU
placement against the Phase 5 OPTIMISED assignment.  Uses zone-level
``distance_to_dispatch`` as a proxy for travel distance per SKU pick,
aggregated across all synthetic orders.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from slotting_optimization_engine.config.project_paths import (
    DATA_PROCESSED_DIR,
    DATA_SYNTHETIC_DIR,
)
from slotting_optimization_engine.domain.constants import (
    Inventory,
    Locations,
    OrderLines,
    Skus,
    Zones,
)
from slotting_optimization_engine.simulation.config import (
    SIMULATION_CAVEAT,
    SimulationConfig,
)
from slotting_optimization_engine.simulation.pipeline import (
    SimulationContext,
    SimulationScenario,
)

# ── Column name helpers ──────────────────────────────────────────────────────

_CURRENT_ZONE = "current_zone_id"
_OPT_ZONE = "optimized_zone_id"
_CURR_DIST = "current_distance"
_OPT_DIST = "optimized_distance"
_ORDER_TOTAL_CURR = "order_distance_current"
_ORDER_TOTAL_OPT = "order_distance_optimized"
_DIST_SAVED = "distance_saved_m"
_TIME_SAVED = "time_saved_s"
_PCT_IMPROV = "distance_improvement_pct"


def load_simulation_inputs(
    processed_dir: Path | None = None,
    synthetic_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Load all inputs needed by the Phase 6 simulators.

    Returns
    -------
    dict with keys:
        * ``orders``        — synthetic order headers
        * ``order_lines``   — synthetic order lines (with SKUs)
        * ``zones``         — warehouse zones (includes ``distance_to_dispatch``)
        * ``locations``     — physical locations (maps location → zone)
        * ``inventory``     — current inventory (maps SKU → location)
        * ``optimization_assignments`` — Phase 5 assignments (SKU → target zone)
    """
    processed_dir = processed_dir or DATA_PROCESSED_DIR
    synthetic_dir = synthetic_dir or DATA_SYNTHETIC_DIR

    required = {
        "orders": synthetic_dir / "orders.csv",
        "order_lines": synthetic_dir / "order_lines.csv",
        "zones": synthetic_dir / "zones.csv",
        "locations": synthetic_dir / "locations.csv",
        "inventory": synthetic_dir / "inventory.csv",
        "optimization_assignments": processed_dir / "optimization_assignments.csv",
    }
    missing = [str(p) for p in required.values() if not p.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing Phase 6 simulation input(s): "
            + ", ".join(missing)
            + ". Run Phase 1 and Phase 5 commands first."
        )

    return {name: pd.read_csv(path) for name, path in required.items()}


def build_sku_current_zone(
    inventory: pd.DataFrame,
    locations: pd.DataFrame,
) -> pd.DataFrame:
    """Build the current SKU → zone mapping from inventory data.

    A SKU may be in multiple locations across different zones.  This function
    returns the **primary zone** (the one where the SKU has the most units).

    Returns
    -------
    pd.DataFrame with columns ``[sku_id, current_zone_id, units_in_zone]``.
    """
    sku_loc = inventory.merge(
        locations[[Locations.LOCATION_ID, Locations.ZONE_ID]],
        on=Locations.LOCATION_ID,
        how="left",
    )
    zone_counts = (
        sku_loc.groupby([Inventory.SKU_ID, Locations.ZONE_ID],
                        as_index=False)[Inventory.UNITS_ON_HAND]
        .sum()
    )
    # Keep the zone with the most units (primary zone)
    primary = zone_counts.loc[
        zone_counts.groupby(Inventory.SKU_ID)[Inventory.UNITS_ON_HAND].idxmax()
    ].rename(
        columns={Locations.ZONE_ID: _CURRENT_ZONE,
                 Inventory.UNITS_ON_HAND: "units_in_zone"}
    )
    return primary[[Inventory.SKU_ID, _CURRENT_ZONE, "units_in_zone"]]


def build_sku_optimized_zone(
    optimization_assignments: pd.DataFrame,
) -> pd.DataFrame:
    """Build the SKU → optimised zone mapping from Phase 5 assignments.

    Returns
    -------
    pd.DataFrame with columns ``[sku_id, optimized_zone_id]``.
    """
    return optimization_assignments[[Skus.SKU_ID, "target_zone_id"]].rename(
        columns={"target_zone_id": _OPT_ZONE}
    ).drop_duplicates(subset=[Skus.SKU_ID])


def simulate_travel(
    order_lines: pd.DataFrame,
    zones: pd.DataFrame,
    sku_current: pd.DataFrame,
    sku_optimized: pd.DataFrame | None = None,
    config: SimulationConfig | None = None,
) -> dict[str, pd.DataFrame | dict[str, float]]:
    """Run the travel-distance simulation.

    Parameters
    ----------
    order_lines : pd.DataFrame
        Synthetic order lines with ``order_id`` and ``sku_id``.
    zones : pd.DataFrame
        Zone master with ``zone_id`` and ``distance_to_dispatch``.
    sku_current : pd.DataFrame
        Current SKU → zone mapping from ``build_sku_current_zone()``.
    sku_optimized : pd.DataFrame | None
        Phase 5 SKU → optimised zone mapping.
        If ``None``, only the current-state metrics are computed.
    config : SimulationConfig | None
        Simulation parameters (speed, overhead).

    Returns
    -------
    dict with keys:
        * ``order_detail``  — per-order distance before / after
        * ``aggregate``     — dict of aggregate metrics
    """
    config = config or SimulationConfig()

    # Attach zone distance to each order line based on current placement
    ol_with_current = order_lines.merge(
        sku_current[[Inventory.SKU_ID, _CURRENT_ZONE]],
        on=Skus.SKU_ID,
        how="left",
    ).merge(
        zones[[Zones.ZONE_ID, Zones.DISTANCE_TO_DISPATCH]],
        left_on=_CURRENT_ZONE,
        right_on=Zones.ZONE_ID,
        how="left",
    ).rename(columns={Zones.DISTANCE_TO_DISPATCH: _CURR_DIST})

    # Aggregate per order: total current distance = sum of SKU distances
    order_current = (
        ol_with_current
        .groupby(OrderLines.ORDER_ID, as_index=False)[_CURR_DIST]
        .sum()
        .rename(columns={_CURR_DIST: _ORDER_TOTAL_CURR})
    )

    # ── Optimised side ───────────────────────────────────────────────────
    result: dict[str, object] = {"order_detail": None, "aggregate": {}}

    if sku_optimized is not None and not sku_optimized.empty:
        ol_with_opt = order_lines.merge(
            sku_optimized[[Skus.SKU_ID, _OPT_ZONE]],
            on=Skus.SKU_ID,
            how="left",
        ).merge(
            zones[[Zones.ZONE_ID, Zones.DISTANCE_TO_DISPATCH]],
            left_on=_OPT_ZONE,
            right_on=Zones.ZONE_ID,
            how="left",
        ).rename(columns={Zones.DISTANCE_TO_DISPATCH: _OPT_DIST})

        order_optimized = (
            ol_with_opt
            .groupby(OrderLines.ORDER_ID, as_index=False)[_OPT_DIST]
            .sum()
            .rename(columns={_OPT_DIST: _ORDER_TOTAL_OPT})
        )

        # Combine and compute deltas
        combined = order_current.merge(order_optimized, on=OrderLines.ORDER_ID, how="left")
        combined[_DIST_SAVED] = (
            combined[_ORDER_TOTAL_CURR] - combined[_ORDER_TOTAL_OPT]
        ).clip(lower=0.0)
        combined[_TIME_SAVED] = (
            combined[_DIST_SAVED]
            * config.travel_overhead_factor
            / config.picker_speed_m_per_s
        )
        combined[_PCT_IMPROV] = np.where(
            combined[_ORDER_TOTAL_CURR] > 0,
            (combined[_DIST_SAVED] / combined[_ORDER_TOTAL_CURR] * 100).round(2),
            0.0,
        )

        # ── Aggregate ────────────────────────────────────────────────────
        total_current_dist = combined[_ORDER_TOTAL_CURR].sum()
        total_optimized_dist = combined[_ORDER_TOTAL_OPT].sum()
        total_dist_saved = combined[_DIST_SAVED].sum()
        total_time_saved_s = combined[_TIME_SAVED].sum()
        avg_pct_improvement = float(combined[_PCT_IMPROV].mean())
        orders_improved = int((combined[_DIST_SAVED] > 0).sum())

        # Scenario breakdown for throughput estimator
        per_order_avg = combined[_ORDER_TOTAL_CURR].mean()
        per_order_avg_opt = combined[_ORDER_TOTAL_OPT].mean()

        result["order_detail"] = combined.sort_values(
            _DIST_SAVED, ascending=False
        ).reset_index(drop=True)

        result["aggregate"] = {
            "total_orders_simulated": len(combined),
            "total_current_distance_m": round(total_current_dist, 2),
            "total_optimized_distance_m": round(total_optimized_dist, 2),
            "total_distance_saved_m": round(total_dist_saved, 2),
            "total_time_saved_s": round(total_time_saved_s, 2),
            "avg_distance_per_order_current": round(per_order_avg, 2),
            "avg_distance_per_order_optimized": round(per_order_avg_opt, 2),
            "avg_improvement_pct": round(avg_pct_improvement, 2),
            "orders_with_improvement": orders_improved,
            "travel_overhead_factor": config.travel_overhead_factor,
            "assumption_state": config.assumption_state,
            "simulation_caveat": SIMULATION_CAVEAT,
        }
    else:
        result["order_detail"] = order_current
        result["aggregate"] = {
            "total_orders_simulated": len(order_current),
            "avg_distance_per_order_current": round(
                order_current[_ORDER_TOTAL_CURR].mean(), 2
            ),
            "total_current_distance_m": round(order_current[_ORDER_TOTAL_CURR].sum(), 2),
            "note": "No Phase 5 optimized assignments available — current-state only.",
            "assumption_state": config.assumption_state,
            "simulation_caveat": SIMULATION_CAVEAT,
        }

    return result  # type: ignore[return-value]


# ── Scenario C pluggable wrapper ─────────────────────────────────────────────


class TravelScenario(SimulationScenario):
    """Pluggable scenario that estimates travel distance/time impact."""

    @property
    def name(self) -> str:
        return "travel"

    @property
    def description(self) -> str:
        return (
            "Compara la distancia y tiempo de viaje actual vs. optimizado "
            "por orden, usando distancia a despacho por zona como proxy."
        )

    def run(self, context: SimulationContext) -> dict[str, Any]:
        return simulate_travel(
            order_lines=context.order_lines,
            zones=context.zones,
            sku_current=context.sku_current_zone,
            sku_optimized=context.sku_optimized_zone,
            config=context.config,
        )
