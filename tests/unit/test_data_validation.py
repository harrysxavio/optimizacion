"""
Tests for data validation — both pandera (if available) and explicit fallback.
"""

from __future__ import annotations

import pandas as pd
import pytest

from slotting_optimization_engine.data.validation import (
    format_validation_report,
    validate_all_datasets,
    validate_dataset,
)
from slotting_optimization_engine.domain.constants import (
    Inventory,
    Locations,
    OrderLines,
    Orders,
    Skus,
    Zones,
)


class TestValidateSkus:
    """SKU validation tests."""

    def test_valid_skus_passes(self, valid_skus: pd.DataFrame) -> None:
        errors = validate_dataset("skus", valid_skus)
        assert errors == [], f"Expected clean validation, got: {errors}"

    def test_null_sku_id_fails(self, valid_skus: pd.DataFrame) -> None:
        df = valid_skus.copy()
        df.loc[0, Skus.SKU_ID] = None
        errors = validate_dataset("skus", df)
        assert len(errors) > 0

    def test_duplicate_sku_id_fails(self, valid_skus: pd.DataFrame) -> None:
        df = valid_skus.copy()
        df.loc[1, Skus.SKU_ID] = df.loc[0, Skus.SKU_ID]
        errors = validate_dataset("skus", df)
        assert len(errors) > 0

    def test_zero_volume_fails(self, valid_skus: pd.DataFrame) -> None:
        df = valid_skus.copy()
        df.loc[0, Skus.UNIT_VOLUME] = 0.0
        errors = validate_dataset("skus", df)
        assert len(errors) > 0

    def test_negative_weight_fails(self, valid_skus: pd.DataFrame) -> None:
        df = valid_skus.copy()
        df.loc[0, Skus.UNIT_WEIGHT] = -1.0
        errors = validate_dataset("skus", df)
        assert len(errors) > 0

    def test_invalid_rotation_class_fails(self, valid_skus: pd.DataFrame) -> None:
        df = valid_skus.copy()
        df.loc[0, Skus.ROTATION_CLASS] = "E"
        errors = validate_dataset("skus", df)
        assert len(errors) > 0

    def test_missing_required_column_fails(self, valid_skus: pd.DataFrame) -> None:
        df = valid_skus.drop(columns=[Skus.CATEGORY])
        errors = validate_dataset("skus", df)
        assert len(errors) > 0


class TestValidateZones:
    """Zone validation tests."""

    def test_valid_zones_passes(self, valid_zones: pd.DataFrame) -> None:
        errors = validate_dataset("zones", valid_zones)
        assert errors == []

    def test_zero_capacity_fails(self, valid_zones: pd.DataFrame) -> None:
        df = valid_zones.copy()
        df.loc[0, Zones.MAX_VOLUME_CAPACITY] = 0.0
        errors = validate_dataset("zones", df)
        assert len(errors) > 0

    def test_null_zone_id_fails(self, valid_zones: pd.DataFrame) -> None:
        df = valid_zones.copy()
        df.loc[0, Zones.ZONE_ID] = None
        errors = validate_dataset("zones", df)
        assert len(errors) > 0


class TestValidateLocations:
    """Location validation tests."""

    def test_valid_locations_passes(
        self, valid_locations: pd.DataFrame, valid_zones: pd.DataFrame,
    ) -> None:
        errors = validate_dataset("locations", valid_locations,
                                   zones_df=valid_zones)
        assert errors == []

    def test_invalid_zone_ref_fails(
        self, valid_locations: pd.DataFrame, valid_zones: pd.DataFrame,
    ) -> None:
        df = valid_locations.copy()
        df.loc[0, Locations.ZONE_ID] = "NONEXISTENT"
        errors = validate_dataset("locations", df, zones_df=valid_zones)
        assert len(errors) > 0


class TestValidateInventory:
    """Inventory validation tests."""

    def test_valid_inventory_passes(
        self, valid_inventory: pd.DataFrame,
        valid_skus: pd.DataFrame, valid_locations: pd.DataFrame,
    ) -> None:
        errors = validate_dataset("inventory", valid_inventory,
                                   skus_df=valid_skus, locs_df=valid_locations)
        assert errors == []

    def test_negative_units_fails(
        self, valid_inventory: pd.DataFrame,
        valid_skus: pd.DataFrame, valid_locations: pd.DataFrame,
    ) -> None:
        df = valid_inventory.copy()
        df.loc[0, Inventory.UNITS_ON_HAND] = -5
        errors = validate_dataset("inventory", df,
                                   skus_df=valid_skus, locs_df=valid_locations)
        assert len(errors) > 0


class TestValidateOrders:
    """Order validation tests."""

    def test_valid_orders_passes(self, valid_orders: pd.DataFrame) -> None:
        errors = validate_dataset("orders", valid_orders)
        assert errors == []

    def test_null_order_id_fails(self, valid_orders: pd.DataFrame) -> None:
        df = valid_orders.copy()
        df.loc[0, Orders.ORDER_ID] = None
        errors = validate_dataset("orders", df)
        assert len(errors) > 0


class TestValidateOrderLines:
    """Order line validation tests."""

    def test_valid_order_lines_passes(
        self, valid_order_lines: pd.DataFrame,
        valid_orders: pd.DataFrame, valid_skus: pd.DataFrame,
    ) -> None:
        errors = validate_dataset("order_lines", valid_order_lines,
                                   orders_df=valid_orders, skus_df=valid_skus)
        assert errors == []

    def test_invalid_order_ref_fails(
        self, valid_order_lines: pd.DataFrame,
        valid_orders: pd.DataFrame, valid_skus: pd.DataFrame,
    ) -> None:
        df = valid_order_lines.copy()
        df.loc[0, OrderLines.ORDER_ID] = "ORD-NONEXISTENT"
        errors = validate_dataset("order_lines", df,
                                   orders_df=valid_orders, skus_df=valid_skus)
        assert len(errors) > 0

    def test_zero_quantity_fails(
        self, valid_order_lines: pd.DataFrame,
        valid_orders: pd.DataFrame, valid_skus: pd.DataFrame,
    ) -> None:
        df = valid_order_lines.copy()
        df.loc[0, OrderLines.QUANTITY] = 0
        errors = validate_dataset("order_lines", df,
                                   orders_df=valid_orders, skus_df=valid_skus)
        assert len(errors) > 0


class TestValidateAll:
    """Integration-style tests for validate_all_datasets."""

    def test_all_valid_passes(
        self, valid_datasets: dict[str, pd.DataFrame],
    ) -> None:
        results = validate_all_datasets(valid_datasets)
        failures = {e: errs for e, errs in results.items() if errs}
        assert not failures, f"Validation errors: {failures}"

    def test_report_format(self, valid_datasets: dict[str, pd.DataFrame]) -> None:
        results = validate_all_datasets(valid_datasets)
        report = format_validation_report(results)
        assert "PASSED" in report
        assert "6 passed" in report or "5 passed" in report


# =====================================================================
# Fixtures — small valid datasets for validation tests
# =====================================================================


@pytest.fixture
def valid_skus() -> pd.DataFrame:
    return pd.DataFrame({
        Skus.SKU_ID: ["SKU-001", "SKU-002", "SKU-003"],
        Skus.CATEGORY: ["Electronics", "Clothing", "Sports"],
        Skus.SUBCATEGORY: ["Audio", "Men", "Fitness"],
        Skus.UNIT_VOLUME: [100.0, 500.0, 50.0],
        Skus.UNIT_WEIGHT: [0.5, 0.3, 1.2],
        Skus.ROTATION_CLASS: ["A", "B", "C"],
        Skus.AVG_DAILY_DEMAND: [50.0, 20.0, 5.0],
    })


@pytest.fixture
def valid_zones() -> pd.DataFrame:
    return pd.DataFrame({
        Zones.ZONE_ID: ["Z-01", "Z-02"],
        Zones.ZONE_TYPE: ["picking", "reserve"],
        Zones.PRIORITY_LEVEL: [1, 2],
        Zones.DISTANCE_TO_DISPATCH: [10.0, 25.0],
        Zones.MAX_VOLUME_CAPACITY: [5000.0, 10000.0],
        Zones.MAX_WEIGHT_CAPACITY: [2000.0, 4000.0],
    })


@pytest.fixture
def valid_locations(valid_zones: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        Locations.LOCATION_ID: ["LOC-001", "LOC-002", "LOC-003"],
        Locations.ZONE_ID: ["Z-01", "Z-01", "Z-02"],
        Locations.AISLE: ["A", "A", "B"],
        Locations.RACK: ["R-1", "R-2", "R-1"],
        Locations.LEVEL: ["L-1", "L-2", "L-1"],
        Locations.MAX_VOLUME_CAPACITY: [500.0, 500.0, 1000.0],
        Locations.MAX_WEIGHT_CAPACITY: [200.0, 200.0, 400.0],
    })


@pytest.fixture
def valid_inventory(
    valid_skus: pd.DataFrame, valid_locations: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame({
        Inventory.SKU_ID: ["SKU-001", "SKU-002", "SKU-003"],
        Inventory.LOCATION_ID: ["LOC-001", "LOC-002", "LOC-003"],
        Inventory.UNITS_ON_HAND: [100, 50, 20],
        Inventory.OCCUPIED_VOLUME: [10000.0, 25000.0, 1000.0],
        Inventory.OCCUPIED_WEIGHT: [50.0, 15.0, 24.0],
    })


@pytest.fixture
def valid_orders() -> pd.DataFrame:
    return pd.DataFrame({
        Orders.ORDER_ID: ["ORD-001", "ORD-002"],
        Orders.ORDER_DATE: pd.to_datetime(["2026-01-15", "2026-02-20"]),
        Orders.CHANNEL: ["online", "retail"],
    })


@pytest.fixture
def valid_order_lines(
    valid_orders: pd.DataFrame, valid_skus: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame({
        OrderLines.ORDER_ID: ["ORD-001", "ORD-001", "ORD-002"],
        OrderLines.SKU_ID: ["SKU-001", "SKU-002", "SKU-003"],
        OrderLines.QUANTITY: [2, 1, 5],
    })


@pytest.fixture
def valid_datasets(
    valid_skus: pd.DataFrame,
    valid_zones: pd.DataFrame,
    valid_locations: pd.DataFrame,
    valid_inventory: pd.DataFrame,
    valid_orders: pd.DataFrame,
    valid_order_lines: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    return {
        "skus": valid_skus,
        "zones": valid_zones,
        "locations": valid_locations,
        "inventory": valid_inventory,
        "orders": valid_orders,
        "order_lines": valid_order_lines,
    }
