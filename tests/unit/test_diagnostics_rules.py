"""Tests for Phase 2 descriptive diagnostic rules."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from slotting_optimization_engine.diagnostics.rules import (
    DiagnosticConfig,
    build_all_diagnostics,
    build_category_diagnostics,
    build_slotting_diagnostics,
    save_diagnostics,
)
from slotting_optimization_engine.domain.constants import (
    Features,
    Inventory,
    Locations,
    Skus,
    Zones,
)

PROJ_ROOT = Path(__file__).resolve().parent.parent.parent


def test_slotting_diagnostics_flags_high_demand_poor_placement() -> None:
    sku_features = pd.DataFrame({
        Skus.SKU_ID: ["S-1", "S-2"],
        Skus.CATEGORY: ["cat-a", "cat-b"],
        Skus.ROTATION_CLASS: ["A", "D"],
        Features.TOTAL_DEMAND: [100, 1],
        Features.ORDER_COUNT: [10, 1],
    })
    placement = pd.DataFrame({
        Skus.SKU_ID: ["S-1", "S-2"],
        Locations.LOCATION_ID: ["L-1", "L-2"],
        Zones.ZONE_ID: ["Z-9", "Z-1"],
        Zones.PRIORITY_LEVEL: [4, 1],
        Zones.DISTANCE_TO_DISPATCH: [90.0, 10.0],
    })

    diagnostics = build_slotting_diagnostics(
        sku_features,
        placement,
        DiagnosticConfig(high_demand_quantile=0.50, long_distance_quantile=0.50),
    )

    high_demand = diagnostics.loc[diagnostics[Skus.SKU_ID] == "S-1"].iloc[0]
    slow_premium = diagnostics.loc[diagnostics[Skus.SKU_ID] == "S-2"].iloc[0]
    assert bool(high_demand["high_demand_poor_placement_flag"])
    assert bool(slow_premium["low_demand_premium_zone_flag"])
    assert high_demand["business_rule_state"] == "inferred / pending confirmation"


def test_category_diagnostics_detects_spread_without_dominance() -> None:
    placement = pd.DataFrame({
        Skus.SKU_ID: ["S-1", "S-2", "S-3"],
        Locations.LOCATION_ID: ["L-1", "L-2", "L-3"],
        Zones.ZONE_ID: ["Z-1", "Z-2", "Z-3"],
        Zones.PRIORITY_LEVEL: [1, 2, 3],
        Zones.DISTANCE_TO_DISPATCH: [10.0, 20.0, 30.0],
    })
    sku_features = pd.DataFrame({
        Skus.SKU_ID: ["S-1", "S-2", "S-3"],
        Skus.CATEGORY: ["cat-a", "cat-a", "cat-a"],
        Features.TOTAL_DEMAND: [10, 10, 10],
    })

    diagnostics = build_category_diagnostics(
        placement,
        sku_features,
        DiagnosticConfig(category_spread_zone_min=3, category_dominance_max=0.60),
    )

    row = diagnostics.iloc[0]
    assert bool(row["category_spread_flag"])
    assert bool(row["category_misgrouping_indicator"])


def test_build_all_diagnostics_and_save_outputs(tmp_path) -> None:
    datasets = _minimal_datasets()
    sku_features = pd.DataFrame({
        Skus.SKU_ID: ["S-1", "S-2", "S-3"],
        Skus.CATEGORY: ["cat-a", "cat-a", "cat-b"],
        Skus.ROTATION_CLASS: ["A", "D", "C"],
        Features.TOTAL_DEMAND: [100, 2, 10],
        Features.ORDER_COUNT: [8, 1, 2],
    })
    location_utilization = pd.DataFrame({
        Locations.LOCATION_ID: ["L-1", "L-2", "L-3"],
        Features.VOLUME_UTIL_PCT: [90.0, 10.0, 50.0],
        Features.WEIGHT_UTIL_PCT: [80.0, 15.0, 40.0],
        Features.SKU_COUNT_IN_LOC: [3, 1, 1],
        "over_capacity": [False, False, False],
    })
    zone_utilization = pd.DataFrame({
        Zones.ZONE_ID: ["Z-1", "Z-2", "Z-3"],
        Zones.ZONE_TYPE: ["picking", "reserve", "bulk"],
        Zones.PRIORITY_LEVEL: [1, 2, 4],
        Zones.DISTANCE_TO_DISPATCH: [10.0, 30.0, 90.0],
        "avg_volume_util_pct": [90.0, 15.0, 45.0],
        "avg_weight_util_pct": [85.0, 10.0, 40.0],
        "location_count": [1, 1, 1],
        "over_capacity_location_count": [0, 0, 0],
    })

    outputs = build_all_diagnostics(
        sku_features,
        location_utilization,
        zone_utilization,
        datasets,
    )
    paths = save_diagnostics(outputs, tmp_path)

    assert set(outputs) == {
        "slotting_diagnostics",
        "location_diagnostics",
        "zone_diagnostics",
        "category_diagnostics",
        "diagnostic_summary",
    }
    assert all(path.is_file() for path in paths.values())


def test_run_diagnostics_reports_missing_processed_inputs(tmp_path) -> None:
    spec = importlib.util.spec_from_file_location(
        "run_diagnostics", PROJ_ROOT / "scripts" / "run_diagnostics.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with pytest.raises(FileNotFoundError, match="build_features.py"):
        module.load_processed_inputs(tmp_path)


def _minimal_datasets() -> dict[str, pd.DataFrame]:
    return {
        "inventory": pd.DataFrame({
            Inventory.SKU_ID: ["S-1", "S-2", "S-3"],
            Inventory.LOCATION_ID: ["L-3", "L-1", "L-2"],
        }),
        "locations": pd.DataFrame({
            Locations.LOCATION_ID: ["L-1", "L-2", "L-3"],
            Locations.ZONE_ID: ["Z-1", "Z-2", "Z-3"],
        }),
        "zones": pd.DataFrame({
            Zones.ZONE_ID: ["Z-1", "Z-2", "Z-3"],
            Zones.ZONE_TYPE: ["picking", "reserve", "bulk"],
            Zones.PRIORITY_LEVEL: [1, 2, 4],
            Zones.DISTANCE_TO_DISPATCH: [10.0, 30.0, 90.0],
        }),
    }
