"""
Tests for the feature builder module.
"""

from __future__ import annotations

import pandas as pd
import pytest

from slotting_optimization_engine.data.generator import (
    GenerationConfig,
    SyntheticDataGenerator,
)
from slotting_optimization_engine.domain.constants import (
    Features,
    Inventory,
    Locations,
    Skus,
    Zones,
)
from slotting_optimization_engine.features.builder import (
    build_alignment_score,
    build_all_features,
    build_demand_by_sku,
    build_distance_indicators,
    build_location_utilization,
    build_sku_footprint,
    build_zone_utilization,
    save_features,
)


@pytest.fixture(scope="class")
def small_datasets() -> dict[str, pd.DataFrame]:
    """Generate small deterministic dataset once for feature tests."""
    config = GenerationConfig(
        n_skus=30,
        n_zones=3,
        locations_per_zone=4,
        n_orders=50,
        avg_lines_per_order=3,
        seed=42,
    )
    return SyntheticDataGenerator(config).generate_all()


class TestDemandBySku:
    """Tests for demand aggregation."""

    def test_output_columns(self, small_datasets) -> None:
        demand = build_demand_by_sku(small_datasets["order_lines"])
        assert Skus.SKU_ID in demand.columns
        assert Features.TOTAL_DEMAND in demand.columns
        assert Features.ORDER_COUNT in demand.columns

    def test_demand_non_negative(self, small_datasets) -> None:
        demand = build_demand_by_sku(small_datasets["order_lines"])
        assert (demand[Features.TOTAL_DEMAND] >= 0).all()
        assert (demand[Features.ORDER_COUNT] >= 0).all()

    def test_skus_without_orders_excluded(self, small_datasets) -> None:
        """Not every SKU appears in orders — that's expected."""
        demand = build_demand_by_sku(small_datasets["order_lines"])
        skus_with_orders = set(demand[Skus.SKU_ID])
        all_skus = set(small_datasets["skus"][Skus.SKU_ID])
        # Some SKUs may be missing from orders (not all are picked)
        assert skus_with_orders.issubset(all_skus)


class TestSkuFootprint:
    """Tests for volume/weight footprint."""

    def test_output_columns(self, small_datasets) -> None:
        fp = build_sku_footprint(small_datasets["inventory"])
        assert Skus.SKU_ID in fp.columns
        assert Features.TOTAL_VOLUME in fp.columns
        assert Features.TOTAL_WEIGHT in fp.columns

    def test_footprint_non_negative(self, small_datasets) -> None:
        fp = build_sku_footprint(small_datasets["inventory"])
        assert (fp[Features.TOTAL_VOLUME] >= 0).all()
        assert (fp[Features.TOTAL_WEIGHT] >= 0).all()


class TestLocationUtilization:
    """Tests for location utilisation."""

    def test_output_columns(self, small_datasets) -> None:
        util = build_location_utilization(
            small_datasets["inventory"], small_datasets["locations"],
        )
        assert Locations.LOCATION_ID in util.columns
        assert Features.VOLUME_UTIL_PCT in util.columns
        assert Features.WEIGHT_UTIL_PCT in util.columns
        assert Features.SKU_COUNT_IN_LOC in util.columns

    def test_utilization_between_0_and_100(self, small_datasets) -> None:
        util = build_location_utilization(
            small_datasets["inventory"], small_datasets["locations"],
        )
        assert (util[Features.VOLUME_UTIL_PCT] >= 0).all()
        assert (util[Features.VOLUME_UTIL_PCT] <= 100).all()
        assert (util[Features.WEIGHT_UTIL_PCT] >= 0).all()
        assert (util[Features.WEIGHT_UTIL_PCT] <= 100).all()

    def test_some_locations_empty(self, small_datasets) -> None:
        """~10% of locations have no inventory → zero utilisation."""
        util = build_location_utilization(
            small_datasets["inventory"], small_datasets["locations"],
        )
        assert (util[Features.VOLUME_UTIL_PCT] == 0).any()


class TestZoneUtilization:
    """Tests for zone utilisation."""

    def test_output_columns(self, small_datasets) -> None:
        loc_util = build_location_utilization(
            small_datasets["inventory"], small_datasets["locations"],
        )
        zone_util = build_zone_utilization(
            loc_util, small_datasets["locations"], small_datasets["zones"],
        )
        assert Zones.ZONE_ID in zone_util.columns
        assert "avg_volume_util_pct" in zone_util.columns
        assert "avg_weight_util_pct" in zone_util.columns
        assert "location_count" in zone_util.columns

    def test_all_zones_represented(self, small_datasets) -> None:
        loc_util = build_location_utilization(
            small_datasets["inventory"], small_datasets["locations"],
        )
        zone_util = build_zone_utilization(
            loc_util, small_datasets["locations"], small_datasets["zones"],
        )
        all_zones = set(small_datasets["zones"][Zones.ZONE_ID])
        result_zones = set(zone_util[Zones.ZONE_ID])
        assert result_zones == all_zones


class TestDistanceIndicators:
    """Tests for distance/priority indicators."""

    def test_output_columns(self, small_datasets) -> None:
        dist = build_distance_indicators(
            small_datasets["inventory"],
            small_datasets["locations"],
            small_datasets["zones"],
        )
        assert Inventory.SKU_ID in dist.columns
        assert Inventory.LOCATION_ID in dist.columns
        assert Locations.ZONE_ID in dist.columns
        assert Zones.DISTANCE_TO_DISPATCH in dist.columns
        assert Zones.PRIORITY_LEVEL in dist.columns


class TestAlignmentScore:
    """Tests for the preliminary alignment score."""

    def test_output_columns(self, small_datasets) -> None:
        from slotting_optimization_engine.features.builder import (
            build_demand_by_sku,
            build_distance_indicators,
        )
        demand = build_demand_by_sku(small_datasets["order_lines"])
        dist = build_distance_indicators(
            small_datasets["inventory"],
            small_datasets["locations"],
            small_datasets["zones"],
        )
        aligned = build_alignment_score(
            demand, small_datasets["skus"], dist,
        )
        assert Features.ALIGNMENT_FLAG in aligned.columns
        assert Features.ALIGNMENT_SCORE in aligned.columns

    def test_score_in_0_1_range(self, small_datasets) -> None:
        demand = build_demand_by_sku(small_datasets["order_lines"])
        dist = build_distance_indicators(
            small_datasets["inventory"],
            small_datasets["locations"],
            small_datasets["zones"],
        )
        aligned = build_alignment_score(
            demand, small_datasets["skus"], dist,
        )
        assert (aligned[Features.ALIGNMENT_SCORE] >= 0).all()
        assert (aligned[Features.ALIGNMENT_SCORE] <= 1).all()


class TestBuildAllFeatures:
    """Integration tests for the full feature pipeline."""

    def test_output_keys(self, small_datasets) -> None:
        outputs = build_all_features(small_datasets)
        assert "features" in outputs
        assert "location_utilization" in outputs
        assert "zone_utilization" in outputs

    def test_feature_row_count(self, small_datasets) -> None:
        """All SKUs must be represented (no silent drops)."""
        outputs = build_all_features(small_datasets)
        n_skus = len(small_datasets["skus"])
        assert len(outputs["features"]) == n_skus, (
            f"Feature table has {len(outputs['features'])} rows, "
            f"expected {n_skus}"
        )

    def test_zone_util_row_count(self, small_datasets) -> None:
        outputs = build_all_features(small_datasets)
        n_zones = len(small_datasets["zones"])
        assert len(outputs["zone_utilization"]) == n_zones

    def test_save_features(self, small_datasets, tmp_path) -> None:
        outputs = build_all_features(small_datasets)
        paths = save_features(outputs, output_dir=tmp_path)
        assert len(paths) == 3
        for p in paths.values():
            assert p.is_file(), f"Output file not found: {p}"

    def test_all_features_non_null(self, small_datasets) -> None:
        outputs = build_all_features(small_datasets)
        feat = outputs["features"]
        assert feat[Skus.SKU_ID].notna().all()
        assert feat[Features.ALIGNMENT_SCORE].notna().all()
