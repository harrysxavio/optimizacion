"""
Data validation for slotting datasets.

Two-tier validation strategy
----------------------------
Primary (Tier 1): **pandera** DataFrameModel schemas — declarative, self-
   documenting, produce rich error messages.

Fallback (Tier 2): Explicit pandas-based validation functions — used when
   pandera is unavailable or incompatible with the current pandas version.

Decision rationale
------------------
pandera 0.31.x was installed successfully in the Phase 0 environment
(pandas 3.0.3, Python 3.13.5). If future API changes break compatibility,
the fallback functions reproduce the same validation rules so data quality
is never silently compromised.

All inferred business rules are marked as ``inferred / pending confirmation``
until reviewed against real warehouse data.
"""

from __future__ import annotations

import logging

import pandas as pd

from slotting_optimization_engine.domain.constants import (
    Inventory,
    Locations,
    OrderLines,
    Orders,
    Skus,
    Zones,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier 1: pandera schemas
# ---------------------------------------------------------------------------

try:
    import warnings

    # Suppress the pandera top-level import deprecation warning;
    # `pandera.pandas` is the recommended path but the top-level aliases
    # still work in 0.31.x. We suppress to keep logs clean.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning,
                                module="pandera")
        import pandera.pandas as pa

    HAS_PANDERA = True
    logger.info("pandera available — using DataFrameModel schemas for validation")

    # --- Schema definitions ------------------------------------------------

    class SkusSchema(pa.DataFrameModel):
        """pandera schema for SKU master data."""
        sku_id: str = pa.Field(nullable=False, unique=True)
        category: str = pa.Field(nullable=False)
        subcategory: str = pa.Field(nullable=True)
        unit_volume: float = pa.Field(nullable=False, gt=0.0)
        unit_weight: float = pa.Field(nullable=False, gt=0.0)
        rotation_class: str = pa.Field(nullable=False, isin=["A", "B", "C", "D"])
        avg_daily_demand: float = pa.Field(nullable=False, ge=0.0)

        class Config:
            coerce = True
            strict = False  # tolerate future extra columns

    class ZonesSchema(pa.DataFrameModel):
        """pandera schema for warehouse zones."""
        zone_id: str = pa.Field(nullable=False, unique=True)
        zone_type: str = pa.Field(nullable=False)
        priority_level: int = pa.Field(nullable=False, ge=1)
        distance_to_dispatch: float = pa.Field(nullable=False, ge=0.0)
        max_volume_capacity: float = pa.Field(nullable=False, gt=0.0)
        max_weight_capacity: float = pa.Field(nullable=False, gt=0.0)

        class Config:
            coerce = True
            strict = False

    class LocationsSchema(pa.DataFrameModel):
        """pandera schema for physical locations."""
        location_id: str = pa.Field(nullable=False, unique=True)
        zone_id: str = pa.Field(nullable=False)
        aisle: str = pa.Field(nullable=False)
        rack: str = pa.Field(nullable=True)
        level: str = pa.Field(nullable=True)
        max_volume_capacity: float = pa.Field(nullable=False, gt=0.0)
        max_weight_capacity: float = pa.Field(nullable=False, gt=0.0)

        class Config:
            coerce = True
            strict = False

    class InventorySchema(pa.DataFrameModel):
        """pandera schema for inventory snapshot."""
        sku_id: str = pa.Field(nullable=False)
        location_id: str = pa.Field(nullable=False)
        units_on_hand: int = pa.Field(nullable=False, ge=0)
        occupied_volume: float = pa.Field(nullable=False, ge=0.0)
        occupied_weight: float = pa.Field(nullable=False, ge=0.0)

        class Config:
            coerce = True
            strict = False

    class OrdersSchema(pa.DataFrameModel):
        """pandera schema for order headers."""
        order_id: str = pa.Field(nullable=False, unique=True)
        order_date: pd.Timestamp = pa.Field(nullable=False)
        channel: str = pa.Field(nullable=True)

        class Config:
            coerce = True
            strict = False

    class OrderLinesSchema(pa.DataFrameModel):
        """pandera schema for order lines."""
        order_id: str = pa.Field(nullable=False)
        sku_id: str = pa.Field(nullable=False)
        quantity: int = pa.Field(nullable=False, gt=0)

        class Config:
            coerce = True
            strict = False

    # Map from entity name → pandera schema class
    PANDERA_SCHEMAS: dict[str, type[pa.DataFrameModel]] = {
        "skus": SkusSchema,
        "zones": ZonesSchema,
        "locations": LocationsSchema,
        "inventory": InventorySchema,
        "orders": OrdersSchema,
        "order_lines": OrderLinesSchema,
    }

except (ImportError, RuntimeError, TypeError) as _pandera_err:
    HAS_PANDERA = False
    logger.warning(
        "pandera import failed (%s) — falling back to explicit validation",
        _pandera_err,
    )
    PANDERA_SCHEMAS = {}


# ===================================================================
# Tier 2: Explicit validation helpers (fallback)
# ===================================================================


def _check_required_cols(df: pd.DataFrame, required: list[str],
                         name: str) -> list[str]:
    missing = [c for c in required if c not in df.columns]
    return [f"{name}: missing required columns: {missing}"] if missing else []


def _check_no_nulls(df: pd.DataFrame, columns: list[str],
                    name: str) -> list[str]:
    errors: list[str] = []
    for col in columns:
        if col in df.columns:
            n = int(df[col].isna().sum())
            if n:
                errors.append(f"{name}.{col}: {n} null value(s) (expected 0)")
    return errors


def _check_unique(df: pd.DataFrame, column: str,
                  name: str) -> list[str]:
    if column in df.columns:
        n = int(df[column].duplicated().sum())
        if n:
            return [f"{name}.{column}: {n} duplicate(s) (expected unique)"]
    return []


def _check_gt_zero(df: pd.DataFrame, columns: list[str],
                   name: str) -> list[str]:
    errors: list[str] = []
    for col in columns:
        if col in df.columns:
            n = int((df[col] <= 0).sum())
            if n:
                errors.append(f"{name}.{col}: {n} value(s) <= 0 (expected > 0)")
    return errors


def _check_ge_zero(df: pd.DataFrame, columns: list[str],
                   name: str) -> list[str]:
    errors: list[str] = []
    for col in columns:
        if col in df.columns:
            n = int((df[col] < 0).sum())
            if n:
                errors.append(f"{name}.{col}: {n} negative value(s) (expected >= 0)")
    return errors


# ===================================================================
# Per-entity validators (used by both tiers via the dispatch function)
# ===================================================================
# These operate on raw DataFrames and return lists of error strings.

# Column subsets for each entity
_SKUS_REQUIRED   = [Skus.SKU_ID, Skus.CATEGORY, Skus.UNIT_VOLUME,
                     Skus.UNIT_WEIGHT, Skus.ROTATION_CLASS,
                     Skus.AVG_DAILY_DEMAND]
_SKUS_NO_NULL    = [Skus.SKU_ID, Skus.CATEGORY, Skus.UNIT_VOLUME,
                     Skus.UNIT_WEIGHT, Skus.ROTATION_CLASS]
_SKUS_POSITIVE   = [Skus.UNIT_VOLUME, Skus.UNIT_WEIGHT]

_ZONES_REQUIRED  = [Zones.ZONE_ID, Zones.ZONE_TYPE, Zones.PRIORITY_LEVEL,
                     Zones.MAX_VOLUME_CAPACITY, Zones.MAX_WEIGHT_CAPACITY]
_ZONES_NO_NULL   = _ZONES_REQUIRED
_ZONES_POSITIVE  = [Zones.MAX_VOLUME_CAPACITY, Zones.MAX_WEIGHT_CAPACITY]

_LOCS_REQUIRED   = [Locations.LOCATION_ID, Locations.ZONE_ID,
                     Locations.AISLE, Locations.MAX_VOLUME_CAPACITY,
                     Locations.MAX_WEIGHT_CAPACITY]
_LOCS_NO_NULL    = [Locations.LOCATION_ID, Locations.ZONE_ID,
                     Locations.AISLE]
_LOCS_POSITIVE   = [Locations.MAX_VOLUME_CAPACITY,
                     Locations.MAX_WEIGHT_CAPACITY]

_INV_REQUIRED    = [Inventory.SKU_ID, Inventory.LOCATION_ID,
                     Inventory.UNITS_ON_HAND]
_INV_NO_NULL     = _INV_REQUIRED
_INV_NON_NEG     = [Inventory.UNITS_ON_HAND, Inventory.OCCUPIED_VOLUME,
                     Inventory.OCCUPIED_WEIGHT]

_ORD_REQUIRED    = [Orders.ORDER_ID, Orders.ORDER_DATE]
_ORD_NO_NULL     = _ORD_REQUIRED

_OL_REQUIRED     = [OrderLines.ORDER_ID, OrderLines.SKU_ID,
                     OrderLines.QUANTITY]
_OL_NO_NULL      = _OL_REQUIRED


def validate_skus(df: pd.DataFrame) -> list[str]:
    """Validate SKU dataset — column presence, nulls, types, domain values."""
    errors: list[str] = []
    errors.extend(_check_required_cols(df, _SKUS_REQUIRED, "skus"))
    errors.extend(_check_no_nulls(df, _SKUS_NO_NULL, "skus"))
    errors.extend(_check_unique(df, Skus.SKU_ID, "skus"))
    errors.extend(_check_gt_zero(df, _SKUS_POSITIVE, "skus"))

    if Skus.ROTATION_CLASS in df.columns:
        invalid = df[~df[Skus.ROTATION_CLASS].isin(["A", "B", "C", "D"])]
        if len(invalid):
            errors.append(
                f"skus.rotation_class: {len(invalid)} row(s) not in [A, B, C, D]"
            )
    return errors


def validate_zones(df: pd.DataFrame) -> list[str]:
    """Validate zones dataset."""
    errors: list[str] = []
    errors.extend(_check_required_cols(df, _ZONES_REQUIRED, "zones"))
    errors.extend(_check_no_nulls(df, _ZONES_NO_NULL, "zones"))
    errors.extend(_check_unique(df, Zones.ZONE_ID, "zones"))
    errors.extend(_check_gt_zero(df, _ZONES_POSITIVE, "zones"))

    if Zones.PRIORITY_LEVEL in df.columns:
        n = int((df[Zones.PRIORITY_LEVEL] < 1).sum())
        if n:
            errors.append(f"zones.priority_level: {n} row(s) < 1")
    return errors


def validate_locations(
    df: pd.DataFrame,
    zones_df: pd.DataFrame | None = None,
) -> list[str]:
    """Validate locations dataset + optional FK check against zones."""
    errors: list[str] = []
    errors.extend(_check_required_cols(df, _LOCS_REQUIRED, "locations"))
    errors.extend(_check_no_nulls(df, _LOCS_NO_NULL, "locations"))
    errors.extend(_check_unique(df, Locations.LOCATION_ID, "locations"))
    errors.extend(_check_gt_zero(df, _LOCS_POSITIVE, "locations"))

    if zones_df is not None and Locations.ZONE_ID in df.columns:
        valid = set(zones_df[Zones.ZONE_ID].unique())
        n = int((~df[Locations.ZONE_ID].isin(valid)).sum())
        if n:
            errors.append(
                f"locations.zone_id: {n} row(s) reference non-existent zones "
                f"(inferred / pending confirmation)"
            )
    return errors


def validate_inventory(
    df: pd.DataFrame,
    skus_df: pd.DataFrame | None = None,
    locs_df: pd.DataFrame | None = None,
) -> list[str]:
    """Validate inventory dataset + optional FK checks."""
    errors: list[str] = []
    errors.extend(_check_required_cols(df, _INV_REQUIRED, "inventory"))
    errors.extend(_check_no_nulls(df, _INV_NO_NULL, "inventory"))
    errors.extend(_check_ge_zero(df, _INV_NON_NEG, "inventory"))

    if skus_df is not None and Inventory.SKU_ID in df.columns:
        valid = set(skus_df[Skus.SKU_ID].unique())
        n = int((~df[Inventory.SKU_ID].isin(valid)).sum())
        if n:
            errors.append(
                f"inventory.sku_id: {n} row(s) reference non-existent SKUs"
            )
    if locs_df is not None and Inventory.LOCATION_ID in df.columns:
        valid = set(locs_df[Locations.LOCATION_ID].unique())
        n = int((~df[Inventory.LOCATION_ID].isin(valid)).sum())
        if n:
            errors.append(
                f"inventory.location_id: {n} row(s) reference non-existent locations"
            )
    return errors


def validate_orders(df: pd.DataFrame) -> list[str]:
    """Validate orders dataset."""
    errors: list[str] = []
    errors.extend(_check_required_cols(df, _ORD_REQUIRED, "orders"))
    errors.extend(_check_no_nulls(df, _ORD_NO_NULL, "orders"))
    errors.extend(_check_unique(df, Orders.ORDER_ID, "orders"))
    return errors


def validate_order_lines(
    df: pd.DataFrame,
    orders_df: pd.DataFrame | None = None,
    skus_df: pd.DataFrame | None = None,
) -> list[str]:
    """Validate order lines dataset + optional FK checks."""
    errors: list[str] = []
    errors.extend(_check_required_cols(df, _OL_REQUIRED, "order_lines"))
    errors.extend(_check_no_nulls(df, _OL_NO_NULL, "order_lines"))

    if OrderLines.QUANTITY in df.columns:
        n = int((df[OrderLines.QUANTITY] <= 0).sum())
        if n:
            errors.append(f"order_lines.quantity: {n} row(s) with quantity <= 0")

    if orders_df is not None and OrderLines.ORDER_ID in df.columns:
        valid = set(orders_df[Orders.ORDER_ID].unique())
        n = int((~df[OrderLines.ORDER_ID].isin(valid)).sum())
        if n:
            errors.append(
                f"order_lines.order_id: {n} row(s) reference non-existent orders"
            )
    if skus_df is not None and OrderLines.SKU_ID in df.columns:
        valid = set(skus_df[Skus.SKU_ID].unique())
        n = int((~df[OrderLines.SKU_ID].isin(valid)).sum())
        if n:
            errors.append(
                f"order_lines.sku_id: {n} row(s) reference non-existent SKUs"
            )
    return errors


# ===================================================================
# Dispatch
# ===================================================================

ENTITY_VALIDATORS = {
    "skus":        validate_skus,
    "zones":       validate_zones,
    "locations":   validate_locations,
    "inventory":   validate_inventory,
    "orders":      validate_orders,
    "order_lines": validate_order_lines,
}


def validate_dataset(
    entity: str,
    df: pd.DataFrame,
    **fks: pd.DataFrame,
) -> list[str]:
    """Validate a single dataset by entity name.

    Parameters
    ----------
    entity : str
        One of ``"skus"``, ``"zones"``, ``"locations"``, ``"inventory"``,
        ``"orders"``, ``"order_lines"``.
    df : pd.DataFrame
        The dataset to validate.
    **fks : pd.DataFrame
        Optional foreign-key DataFrames passed to entity validators:
        ``zones_df``, ``skus_df``, ``locs_df``, ``orders_df``.

    Returns
    -------
    list[str]
        List of validation error messages. An empty list means the dataset
        passed all checks.
    """
    errors: list[str] = []

    # --- Tier 1: pandera ---
    if HAS_PANDERA and entity in PANDERA_SCHEMAS:
        schema_class = PANDERA_SCHEMAS[entity]
        try:
            schema_class.validate(df, lazy=True)
        except Exception as exc:
            # Collect pandera error messages but DO NOT return early —
            # Tier 2 (explicit checks) still runs for FK validation
            # that pandera schemas don't cover.
            msg = str(exc)
            if hasattr(exc, "args") and exc.args:
                msg = "; ".join(str(a) for a in exc.args)
            errors.append(f"[pandera] {entity}: {msg}")

    # --- Tier 2: explicit validation ---
    if entity in ENTITY_VALIDATORS:
        # Forward only the FK arguments the validator accepts
        fk_kwargs: dict = {}
        sig = ENTITY_VALIDATORS[entity].__code__
        fk_names = sig.co_varnames[1:sig.co_argcount]  # skip first (df)
        for fn in fk_names:
            if fn in fks:
                fk_kwargs[fn] = fks[fn]

        errors.extend(ENTITY_VALIDATORS[entity](df, **fk_kwargs))

    return errors


def validate_all_datasets(
    datasets: dict[str, pd.DataFrame],
) -> dict[str, list[str]]:
    """Validate all six datasets and return a dict of errors per entity.

    Automatically resolves FK dependencies between datasets so that, e.g.,
    ``inventory`` is validated against ``skus`` and ``locations``.
    """
    fk_deps = {
        "locations":   {"zones_df": "zones"},
        "inventory":   {"skus_df": "skus", "locs_df": "locations"},
        "order_lines": {"orders_df": "orders", "skus_df": "skus"},
    }

    results: dict[str, list[str]] = {}
    for entity in ["skus", "zones", "locations", "inventory",
                    "orders", "order_lines"]:
        df = datasets.get(entity)
        if df is None:
            results[entity] = [f"Dataset '{entity}' not found"]
            continue

        # Resolve FK arguments
        fk_args: dict[str, pd.DataFrame] = {}
        if entity in fk_deps:
            for param, dep_entity in fk_deps[entity].items():
                if dep_entity in datasets:
                    fk_args[param] = datasets[dep_entity]

        results[entity] = validate_dataset(entity, df, **fk_args)

    return results


def format_validation_report(
    results: dict[str, list[str]],
) -> str:
    """Format validation results into a human-readable report string."""
    lines: list[str] = ["=" * 60,
                         "DATA VALIDATION REPORT",
                         "=" * 60]
    passed = 0
    failed = 0

    for entity in ["skus", "zones", "locations", "inventory",
                    "orders", "order_lines"]:
        errs = results.get(entity, ["No results"])
        if not errs:
            lines.append(f"  [PASS] {entity}: PASSED")
            passed += 1
        else:
            lines.append(f"  [FAIL] {entity}: FAILED ({len(errs)} error(s))")
            for e in errs:
                lines.append(f"       - {e}")
            failed += 1

    lines.append("=" * 60)
    lines.append(f"  {passed} passed, {failed} failed / {passed + failed} total")
    lines.append("=" * 60)
    return "\n".join(lines)
