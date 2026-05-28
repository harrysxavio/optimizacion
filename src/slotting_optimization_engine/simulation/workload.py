"""
Phase 6 — Zone workload and balance simulation.

Counts the number of picks (order lines) per warehouse zone under the
CURRENT placement vs. the Phase 5 OPTIMISED assignment, and computes a
simple balance metric (Gini-simulated coefficient) to show how evenly
workload is distributed across zones.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from slotting_optimization_engine.domain.constants import (
    Inventory,
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
from slotting_optimization_engine.simulation.travel import (
    _CURRENT_ZONE,
    _OPT_ZONE,
)

_ZONE_PICKS_CURR = "picks_current"
_ZONE_PICKS_OPT = "picks_optimized"
_PICK_CHANGE = "pick_change"
_PICK_CHANGE_PCT = "pick_change_pct"
_BALANCE_BEFORE = "balance_before"
_BALANCE_AFTER = "balance_after"


def gini_coefficient(values: pd.Series) -> float:
    """Compute a normalised Gini coefficient (0 = perfect equality, 1 = monopoly).

    This is a simplified implementation that treats each zone's pick count
    as an "income" value.  Lower Gini = more balanced workload across zones.
    """
    values = values.astype(float)
    if values.sum() <= 0 or len(values) < 2:
        return 0.0
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    cumsum = np.cumsum(sorted_vals)
    return float((2 * np.sum((np.arange(1, n + 1)) * sorted_vals) / (n * cumsum[-1])) - (n + 1) / n)


def simulate_workload(
    order_lines: pd.DataFrame,
    zones: pd.DataFrame,
    sku_current: pd.DataFrame,
    sku_optimized: pd.DataFrame | None = None,
    config: SimulationConfig | None = None,
) -> dict[str, pd.DataFrame | dict[str, float | int]]:
    """Run the zone workload simulation.

    Parameters
    ----------
    order_lines : pd.DataFrame
        Synthetic order lines with ``order_id`` and ``sku_id``.
    zones : pd.DataFrame
        Zone master with ``zone_id``.
    sku_current : pd.DataFrame
        Current SKU → zone mapping from ``build_sku_current_zone()``.
    sku_optimized : pd.DataFrame | None
        Phase 5 SKU → optimised zone mapping.
    config : SimulationConfig | None
        Unused in this module (kept for API consistency).

    Returns
    -------
    dict with keys:
        * ``zone_detail``   — per-zone pick counts before / after
        * ``aggregate``     — dict of balance metrics
    """
    _ = config  # kept for API consistency

    # ── Current picks per zone ───────────────────────────────────────────
    picks_current = (
        order_lines
        .merge(sku_current[[Inventory.SKU_ID, _CURRENT_ZONE]], on=Skus.SKU_ID, how="left")
        .groupby(_CURRENT_ZONE, as_index=False)
        .size()
        .rename(columns={_CURRENT_ZONE: Zones.ZONE_ID, "size": _ZONE_PICKS_CURR})
    )

    # ── Optimised picks per zone ─────────────────────────────────────────
    result: dict[str, object] = {"zone_detail": None, "aggregate": {}}

    if sku_optimized is not None and not sku_optimized.empty:
        picks_optimized = (
            order_lines
            .merge(sku_optimized[[Skus.SKU_ID, _OPT_ZONE]], on=Skus.SKU_ID, how="left")
            .groupby(_OPT_ZONE, as_index=False)
            .size()
            .rename(columns={_OPT_ZONE: Zones.ZONE_ID, "size": _ZONE_PICKS_OPT})
        )

        # Combine into zone detail
        detail = picks_current.merge(
            picks_optimized, on=Zones.ZONE_ID, how="outer"
        ).fillna(0)

        detail[_ZONE_PICKS_CURR] = detail[_ZONE_PICKS_CURR].astype(int)
        detail[_ZONE_PICKS_OPT] = detail[_ZONE_PICKS_OPT].astype(int)
        detail[_PICK_CHANGE] = detail[_ZONE_PICKS_OPT] - detail[_ZONE_PICKS_CURR]
        detail[_PICK_CHANGE_PCT] = np.where(
            detail[_ZONE_PICKS_CURR] > 0,
            (detail[_PICK_CHANGE] / detail[_ZONE_PICKS_CURR] * 100).round(2),
            np.nan,
        )
        detail = detail.sort_values(_PICK_CHANGE, ascending=False).reset_index(drop=True)

        # Balance metrics
        gini_before = gini_coefficient(detail[_ZONE_PICKS_CURR])
        gini_after = gini_coefficient(detail[_ZONE_PICKS_OPT])
        total_picks_current = int(detail[_ZONE_PICKS_CURR].sum())
        total_picks_optimized = int(detail[_ZONE_PICKS_OPT].sum())
        zones_with_change = int((detail[_PICK_CHANGE] != 0).sum())

        result["zone_detail"] = detail
        result["aggregate"] = {
            "total_zones": len(detail),
            "total_picks_current": total_picks_current,
            "total_picks_optimized": total_picks_optimized,
            "zones_with_pick_change": zones_with_change,
            "gini_coefficient_before": round(gini_before, 4),
            "gini_coefficient_after": round(gini_after, 4),
            "gini_change": round(gini_after - gini_before, 4),
            "balance_improved": gini_after < gini_before,
            "assumption_state": "inferred / pending confirmation",
            "simulation_caveat": SIMULATION_CAVEAT,
        }
    else:
        # Current-state only
        picks_current = picks_current.sort_values(_ZONE_PICKS_CURR, ascending=False)
        gini_before = gini_coefficient(picks_current[_ZONE_PICKS_CURR])
        result["zone_detail"] = picks_current
        result["aggregate"] = {
            "total_zones": len(picks_current),
            "total_picks_current": int(picks_current[_ZONE_PICKS_CURR].sum()),
            "gini_coefficient_before": round(gini_before, 4),
            "note": "No Phase 5 optimized assignments available — current-state only.",
            "assumption_state": "inferred / pending confirmation",
            "simulation_caveat": SIMULATION_CAVEAT,
        }

    return result  # type: ignore[return-value]


# ── Scenario C pluggable wrapper ─────────────────────────────────────────────


class WorkloadScenario(SimulationScenario):
    """Pluggable scenario that estimates zone workload balance impact."""

    @property
    def name(self) -> str:
        return "workload"

    @property
    def description(self) -> str:
        return (
            "Estima la carga de picks por zona antes y después de la "
            "optimización, y mide el balance con el coeficiente Gini."
        )

    def run(self, context: SimulationContext) -> dict[str, Any]:
        return simulate_workload(
            order_lines=context.order_lines,
            zones=context.zones,
            sku_current=context.sku_current_zone,
            sku_optimized=context.sku_optimized_zone,
            config=context.config,
        )
