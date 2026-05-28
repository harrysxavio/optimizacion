"""
Tests for the synthetic data generator.
"""

from __future__ import annotations

from slotting_optimization_engine.data.generator import (
    GenerationConfig,
    SyntheticDataGenerator,
)
from slotting_optimization_engine.domain.constants import (
    Inventory,
    Locations,
    OrderLines,
    Orders,
    Skus,
    Zones,
)


class TestSyntheticDataGenerator:
    """Verify that the generator produces well-formed, consistent data."""

    @classmethod
    def setup_class(cls) -> None:
        """Generate a small dataset once for all tests (deterministic)."""
        config = GenerationConfig(
            n_skus=50,
            n_zones=3,
            locations_per_zone=5,
            n_orders=100,
            avg_lines_per_order=4,
            seed=42,
        )
        cls.gen = SyntheticDataGenerator(config)
        cls.data = cls.gen.generate_all()

    # -- Structural tests ------------------------------------------------

    def test_all_datasets_present(self) -> None:
        assert set(self.data.keys()) == {
            "skus", "zones", "locations", "inventory", "orders", "order_lines",
        }

    def test_skus_columns(self) -> None:
        expected = {
            Skus.SKU_ID, Skus.CATEGORY, Skus.SUBCATEGORY,
            Skus.UNIT_VOLUME, Skus.UNIT_WEIGHT,
            Skus.ROTATION_CLASS, Skus.AVG_DAILY_DEMAND,
        }
        assert set(self.data["skus"].columns) == expected

    def test_zones_columns(self) -> None:
        expected = {
            Zones.ZONE_ID, Zones.ZONE_TYPE, Zones.PRIORITY_LEVEL,
            Zones.DISTANCE_TO_DISPATCH,
            Zones.MAX_VOLUME_CAPACITY, Zones.MAX_WEIGHT_CAPACITY,
        }
        assert set(self.data["zones"].columns) == expected

    def test_locations_columns(self) -> None:
        expected = {
            Locations.LOCATION_ID, Locations.ZONE_ID,
            Locations.AISLE, Locations.RACK, Locations.LEVEL,
            Locations.MAX_VOLUME_CAPACITY, Locations.MAX_WEIGHT_CAPACITY,
        }
        assert set(self.data["locations"].columns) == expected

    def test_inventory_columns(self) -> None:
        expected = {
            Inventory.SKU_ID, Inventory.LOCATION_ID,
            Inventory.UNITS_ON_HAND,
            Inventory.OCCUPIED_VOLUME, Inventory.OCCUPIED_WEIGHT,
        }
        assert set(self.data["inventory"].columns) == expected

    def test_orders_columns(self) -> None:
        expected = {Orders.ORDER_ID, Orders.ORDER_DATE, Orders.CHANNEL}
        assert set(self.data["orders"].columns) == expected

    def test_order_lines_columns(self) -> None:
        expected = {
            OrderLines.ORDER_ID, OrderLines.SKU_ID, OrderLines.QUANTITY,
        }
        assert set(self.data["order_lines"].columns) == expected

    # -- Row count tests ------------------------------------------------

    def test_sku_count(self) -> None:
        assert len(self.data["skus"]) == 50

    def test_zone_count(self) -> None:
        assert len(self.data["zones"]) == 3

    def test_location_count(self) -> None:
        assert len(self.data["locations"]) == 3 * 5  # zones * locs_per_zone

    def test_order_count(self) -> None:
        assert len(self.data["orders"]) == 100

    def test_order_lines_have_rows(self) -> None:
        assert len(self.data["order_lines"]) > 0

    def test_inventory_have_rows(self) -> None:
        assert len(self.data["inventory"]) > 0

    # -- Data integrity ------------------------------------------------

    def test_skus_id_unique(self) -> None:
        assert self.data["skus"][Skus.SKU_ID].is_unique

    def test_zones_id_unique(self) -> None:
        assert self.data["zones"][Zones.ZONE_ID].is_unique

    def test_locations_id_unique(self) -> None:
        assert self.data["locations"][Locations.LOCATION_ID].is_unique

    def test_orders_id_unique(self) -> None:
        assert self.data["orders"][Orders.ORDER_ID].is_unique

    def test_no_null_sku_id(self) -> None:
        assert self.data["skus"][Skus.SKU_ID].notna().all()

    def test_no_null_zone_id(self) -> None:
        assert self.data["zones"][Zones.ZONE_ID].notna().all()

    def test_positive_volume(self) -> None:
        assert (self.data["skus"][Skus.UNIT_VOLUME] > 0).all()

    def test_positive_weight(self) -> None:
        assert (self.data["skus"][Skus.UNIT_WEIGHT] > 0).all()

    def test_non_negative_inventory(self) -> None:
        inv = self.data["inventory"]
        assert (inv[Inventory.UNITS_ON_HAND] >= 0).all()
        assert (inv[Inventory.OCCUPIED_VOLUME] >= 0).all()
        assert (inv[Inventory.OCCUPIED_WEIGHT] >= 0).all()

    # -- Referential integrity ------------------------------------------

    def test_inventory_skus_exist(self) -> None:
        valid_skus = set(self.data["skus"][Skus.SKU_ID])
        inv_skus = set(self.data["inventory"][Inventory.SKU_ID])
        assert inv_skus.issubset(valid_skus), (
            f"{inv_skus - valid_skus} not in SKU master"
        )

    def test_inventory_locations_exist(self) -> None:
        valid_locs = set(self.data["locations"][Locations.LOCATION_ID])
        inv_locs = set(self.data["inventory"][Inventory.LOCATION_ID])
        assert inv_locs.issubset(valid_locs), (
            f"{inv_locs - valid_locs} not in location master"
        )

    def test_locations_zones_exist(self) -> None:
        valid_zones = set(self.data["zones"][Zones.ZONE_ID])
        loc_zones = set(self.data["locations"][Locations.ZONE_ID])
        assert loc_zones.issubset(valid_zones)

    def test_order_lines_orders_exist(self) -> None:
        valid_orders = set(self.data["orders"][Orders.ORDER_ID])
        ol_orders = set(self.data["order_lines"][OrderLines.ORDER_ID])
        assert ol_orders.issubset(valid_orders)

    def test_order_lines_skus_exist(self) -> None:
        valid_skus = set(self.data["skus"][Skus.SKU_ID])
        ol_skus = set(self.data["order_lines"][OrderLines.SKU_ID])
        assert ol_skus.issubset(valid_skus)

    # -- Determinism ----------------------------------------------------

    def test_deterministic_output(self) -> None:
        """Same config + same seed must produce identical data."""
        config = GenerationConfig(
            n_skus=10, n_zones=2, locations_per_zone=3,
            n_orders=10, avg_lines_per_order=2, seed=42,
        )
        data_a = SyntheticDataGenerator(config).generate_all()
        data_b = SyntheticDataGenerator(config).generate_all()

        for key in data_a:
            assert data_a[key].equals(data_b[key]), (
                f"Dataset '{key}' differs between runs"
            )

    # -- Rotation class distribution ------------------------------------

    def test_rotation_classes_valid(self) -> None:
        valid = {"A", "B", "C", "D"}
        classes = set(self.data["skus"][Skus.ROTATION_CLASS])
        assert classes.issubset(valid)

    # -- Order channel distribution -------------------------------------

    def test_order_channels_valid(self) -> None:
        valid = {"online", "retail", "wholesale"}
        channels = set(self.data["orders"][Orders.CHANNEL].unique())
        assert channels.issubset(valid)
