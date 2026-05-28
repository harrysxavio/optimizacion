"""
Tests for data loading from CSV files.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from slotting_optimization_engine.data.generator import (
    GenerationConfig,
    SyntheticDataGenerator,
)
from slotting_optimization_engine.data.loading import (
    load_all_datasets,
    load_dataset,
)
from slotting_optimization_engine.domain.constants import (
    DATASET_FILES,
    Orders,
    Skus,
)


class TestLoadDataset:
    """Tests for loading individual datasets."""

    def test_load_all_roundtrip(self, tmp_synthetic_dir: Path) -> None:
        """Write → read back → compare."""
        gen = SyntheticDataGenerator(GenerationConfig(
            n_skus=20, n_zones=2, locations_per_zone=5,
            n_orders=30, seed=42,
        ))
        original = gen.generate_all()

        # Write to temp dir
        for entity, filename in DATASET_FILES.items():
            original[entity].to_csv(tmp_synthetic_dir / filename, index=False)

        # Read back (no validation to avoid fixture errors)
        datasets = load_all_datasets(directory=tmp_synthetic_dir, validate=False)
        assert set(datasets.keys()) == set(original.keys())

        for key in original:
            pd.testing.assert_frame_equal(datasets[key], original[key])

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_dataset("skus", directory=tmp_path, validate=False)

    def test_load_unknown_entity_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Unknown entity"):
            load_dataset("nonexistent", directory=tmp_path, validate=False)

    def test_load_with_validation(
        self, tmp_synthetic_dir: Path, valid_datasets: dict,
    ) -> None:
        """Loading with validation passes on clean data."""
        for entity, filename in DATASET_FILES.items():
            valid_datasets[entity].to_csv(
                tmp_synthetic_dir / filename, index=False,
            )

        datasets = load_all_datasets(directory=tmp_synthetic_dir, validate=True)
        assert len(datasets) == 6


# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture
def tmp_synthetic_dir(tmp_path: Path) -> Path:
    synthetic = tmp_path / "synthetic"
    synthetic.mkdir(parents=True, exist_ok=True)
    return synthetic


@pytest.fixture
def valid_datasets() -> dict[str, pd.DataFrame]:
    """Small valid datasets for loading tests."""
    from slotting_optimization_engine.domain.constants import (
        Inventory,
        Locations,
        OrderLines,
        Zones,
    )

    skus = pd.DataFrame({
        Skus.SKU_ID: ["SKU-001", "SKU-002"],
        Skus.CATEGORY: ["A", "B"],
        Skus.SUBCATEGORY: ["X", "Y"],
        Skus.UNIT_VOLUME: [100.0, 200.0],
        Skus.UNIT_WEIGHT: [0.5, 1.0],
        Skus.ROTATION_CLASS: ["A", "B"],
        Skus.AVG_DAILY_DEMAND: [50.0, 20.0],
    })
    zones = pd.DataFrame({
        Zones.ZONE_ID: ["Z-01", "Z-02"],
        Zones.ZONE_TYPE: ["picking", "reserve"],
        Zones.PRIORITY_LEVEL: [1, 2],
        Zones.DISTANCE_TO_DISPATCH: [10.0, 25.0],
        Zones.MAX_VOLUME_CAPACITY: [5000.0, 10000.0],
        Zones.MAX_WEIGHT_CAPACITY: [2000.0, 4000.0],
    })
    locs = pd.DataFrame({
        Locations.LOCATION_ID: ["LOC-001", "LOC-002"],
        Locations.ZONE_ID: ["Z-01", "Z-02"],
        Locations.AISLE: ["A", "B"],
        Locations.RACK: ["R-1", "R-1"],
        Locations.LEVEL: ["L-1", "L-2"],
        Locations.MAX_VOLUME_CAPACITY: [500.0, 1000.0],
        Locations.MAX_WEIGHT_CAPACITY: [200.0, 400.0],
    })
    inv = pd.DataFrame({
        Inventory.SKU_ID: ["SKU-001", "SKU-002"],
        Inventory.LOCATION_ID: ["LOC-001", "LOC-002"],
        Inventory.UNITS_ON_HAND: [100, 50],
        Inventory.OCCUPIED_VOLUME: [10000.0, 10000.0],
        Inventory.OCCUPIED_WEIGHT: [50.0, 50.0],
    })
    orders = pd.DataFrame({
        Orders.ORDER_ID: ["ORD-001", "ORD-002"],
        Orders.ORDER_DATE: pd.to_datetime(["2026-01-15", "2026-02-20"]),
        Orders.CHANNEL: ["online", "retail"],
    })
    ol = pd.DataFrame({
        OrderLines.ORDER_ID: ["ORD-001", "ORD-002"],
        OrderLines.SKU_ID: ["SKU-001", "SKU-002"],
        OrderLines.QUANTITY: [2, 1],
    })
    return {
        "skus": skus, "zones": zones, "locations": locs,
        "inventory": inv, "orders": orders, "order_lines": ol,
    }
