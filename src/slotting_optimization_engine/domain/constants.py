"""
Domain constants, enums, and schema field names for the slotting domain.

Centralises all column names, enum values, and default configuration so that
data, feature, and validation modules reference a single source of truth
instead of scattering raw strings across the codebase.
"""

from __future__ import annotations

from enum import StrEnum

# ===========================================================================
# Schema column names — one group per dataset
# ===========================================================================
# Each class collects the column-name constants for its entity. Using classes
# rather than module-level constants reduces import noise and groups related
# names for discoverability.
# ===========================================================================


class Skus:
    """Column names for the SKU master dataset."""
    SKU_ID = "sku_id"
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    UNIT_VOLUME = "unit_volume"
    UNIT_WEIGHT = "unit_weight"
    ROTATION_CLASS = "rotation_class"
    AVG_DAILY_DEMAND = "avg_daily_demand"


class Zones:
    """Column names for the warehouse zones dataset."""
    ZONE_ID = "zone_id"
    ZONE_TYPE = "zone_type"
    PRIORITY_LEVEL = "priority_level"
    DISTANCE_TO_DISPATCH = "distance_to_dispatch"
    MAX_VOLUME_CAPACITY = "max_volume_capacity"
    MAX_WEIGHT_CAPACITY = "max_weight_capacity"


class Locations:
    """Column names for the physical locations dataset."""
    LOCATION_ID = "location_id"
    ZONE_ID = "zone_id"
    AISLE = "aisle"
    RACK = "rack"
    LEVEL = "level"
    MAX_VOLUME_CAPACITY = "max_volume_capacity"
    MAX_WEIGHT_CAPACITY = "max_weight_capacity"


class Inventory:
    """Column names for the inventory snapshot dataset."""
    SKU_ID = "sku_id"
    LOCATION_ID = "location_id"
    UNITS_ON_HAND = "units_on_hand"
    OCCUPIED_VOLUME = "occupied_volume"
    OCCUPIED_WEIGHT = "occupied_weight"


class Orders:
    """Column names for the synthetic orders header dataset."""
    ORDER_ID = "order_id"
    ORDER_DATE = "order_date"
    CHANNEL = "channel"


class OrderLines:
    """Column names for the synthetic order lines dataset."""
    ORDER_ID = "order_id"
    SKU_ID = "sku_id"
    QUANTITY = "quantity"


# ===========================================================================
# Feature output column names
# ===========================================================================


class Features:
    """Column names for derived analytical features."""
    TOTAL_DEMAND = "total_demand"
    ORDER_COUNT = "order_count"
    TOTAL_VOLUME = "total_volume"
    TOTAL_WEIGHT = "total_weight"
    VOLUME_UTIL_PCT = "volume_utilization_pct"
    WEIGHT_UTIL_PCT = "weight_utilization_pct"
    SKU_COUNT_IN_LOC = "sku_count_in_location"
    ALIGNMENT_FLAG = "alignment_flag"
    ALIGNMENT_SCORE = "alignment_score"


# ===========================================================================
# Enums
# ===========================================================================


class RotationClass(StrEnum):
    """ABC-style rotation classification.

    A = very high rotation (fast movers)
    B = high rotation
    C = medium rotation
    D = low rotation (slow movers)

    Business assumption: In a typical DC, ~20% of SKUs drive ~80% of
    demand (Pareto). The generator distribution reflects this.
    """
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class ZoneType(StrEnum):
    """Warehouse zone type classification.

    - picking: Fast-access area for order picking (highest priority).
    - reserve: Bulk storage for replenishment (medium priority).
    - cross_dock: Temporary staging for cross-docked goods.
    - bulk: Long-term bulk storage (lowest priority).
    """
    PICKING = "picking"
    RESERVE = "reserve"
    CROSS_DOCK = "cross_dock"
    BULK = "bulk"


class SalesChannel(StrEnum):
    """Sales channel for synthetic orders."""
    ONLINE = "online"
    RETAIL = "retail"
    WHOLESALE = "wholesale"


# ===========================================================================
# Default generation parameters
# ===========================================================================

SYNTHETIC_SEED: int = 42
"""Default random seed for deterministic synthetic data."""

DEFAULT_SKU_COUNT: int = 500
DEFAULT_ZONE_COUNT: int = 10
DEFAULT_LOCATIONS_PER_ZONE: int = 20
DEFAULT_ORDER_COUNT: int = 2000
DEFAULT_ORDER_LINES_PER_ORDER_AVG: int = 5

# ===========================================================================
# File names
# ===========================================================================

DATASET_FILES: dict[str, str] = {
    "skus": "skus.csv",
    "zones": "zones.csv",
    "locations": "locations.csv",
    "inventory": "inventory.csv",
    "orders": "orders.csv",
    "order_lines": "order_lines.csv",
}

FEATURES_FILE: str = "slotting_features.parquet"
FEATURES_SUMMARY_FILE: str = "slotting_feature_summary.csv"
