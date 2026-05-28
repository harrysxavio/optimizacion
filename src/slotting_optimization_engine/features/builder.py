"""
Initial feature construction for slotting analysis.

Builds descriptive analytical features from validated synthetic data.
These features are designed to feed into future diagnostics (Phase 2) and
prescriptive scoring (Phase 3) without requiring a full pipeline rewrite.

⚠️  Phase 1 features are DESCRIPTIVE only. They identify patterns but do NOT
   prescribe actions. The alignment score is explicitly marked as
   **non-prescriptive** — it is a heuristic that must be reviewed and
   calibrated before any operational use.

Feature sets
------------
1. **Demand by SKU** — Total quantity ordered per SKU over the 90-day window.
2. **Picking frequency by SKU** — Number of distinct orders containing each SKU.
3. **Volume / weight footprint** — Total occupied volume and weight per SKU
   from the inventory snapshot.
4. **Location utilisation** — Volume and weight usage as a percentage of
   each location's capacity.
5. **Zone utilisation** — Rolled-up utilisation statistics per zone.
6. **Distance / priority indicators** — Distance-to-dispatch and priority
   level for each SKU's assigned locations.
7. **Preliminary alignment score** — Simple heuristic flagging whether
   high-demand SKUs are stored in high-priority zones. **Non-prescriptive**.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from slotting_optimization_engine.config.project_paths import DATA_PROCESSED_DIR
from slotting_optimization_engine.domain.constants import (
    Features,
    Inventory,
    Locations,
    OrderLines,
    Skus,
    Zones,
)


def build_demand_by_sku(
    order_lines: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate total demand and order count per SKU.

    Returns
    -------
    pd.DataFrame with columns: sku_id, total_demand, order_count.
    """
    demand = (
        order_lines
        .groupby(OrderLines.SKU_ID)
        .agg(
            total_demand=(OrderLines.QUANTITY, "sum"),
            order_count=(OrderLines.ORDER_ID, "nunique"),
        )
        .reset_index()
    )
    demand.columns = [Skus.SKU_ID, Features.TOTAL_DEMAND, Features.ORDER_COUNT]
    return demand


def build_sku_footprint(
    inventory: pd.DataFrame,
) -> pd.DataFrame:
    """Compute total occupied volume and weight per SKU.

    Returns
    -------
    pd.DataFrame with columns: sku_id, total_volume, total_weight.
    """
    footprint = (
        inventory
        .groupby(Inventory.SKU_ID)
        .agg(
            total_volume=(Inventory.OCCUPIED_VOLUME, "sum"),
            total_weight=(Inventory.OCCUPIED_WEIGHT, "sum"),
        )
        .reset_index()
    )
    footprint.columns = [Skus.SKU_ID, Features.TOTAL_VOLUME, Features.TOTAL_WEIGHT]
    return footprint


def build_location_utilization(
    inventory: pd.DataFrame,
    locations: pd.DataFrame,
) -> pd.DataFrame:
    """Compute volume and weight utilisation percentage per location.

    Business assumption: If occupied exceeds capacity (overstock), utilisation
    is capped at 100 % for reporting purposes. The raw overage information is
    preserved in a separate ``over_capacity`` flag for diagnostics.

    Returns
    -------
    pd.DataFrame with columns: location_id, volume_utilization_pct,
    weight_utilization_pct, sku_count_in_location, over_capacity.
    """
    # Aggregate inventory by location
    loc_usage = (
        inventory
        .groupby(Inventory.LOCATION_ID)
        .agg(
            total_volume=(Inventory.OCCUPIED_VOLUME, "sum"),
            total_weight=(Inventory.OCCUPIED_WEIGHT, "sum"),
            sku_count=(Inventory.SKU_ID, "nunique"),
        )
        .reset_index()
    )

    # Merge with location capacities
    merged = locations.merge(
        loc_usage,
        left_on=Locations.LOCATION_ID,
        right_on=Inventory.LOCATION_ID,
        how="left",
    )

    # Locations with no inventory get zero usage
    for col in ["total_volume", "total_weight", "sku_count"]:
        merged[col] = merged[col].fillna(0.0)

    # Utilisation percentages (capped at 100 % for reporting)
    merged[Features.VOLUME_UTIL_PCT] = np.clip(
        merged["total_volume"] / merged[Locations.MAX_VOLUME_CAPACITY] * 100,
        0, 100,
    )
    merged[Features.WEIGHT_UTIL_PCT] = np.clip(
        merged["total_weight"] / merged[Locations.MAX_WEIGHT_CAPACITY] * 100,
        0, 100,
    )
    merged[Features.SKU_COUNT_IN_LOC] = merged["sku_count"].astype(int)

    # Over-capacity flag for diagnostics (Phase 2+)
    merged["over_capacity"] = (
        (merged["total_volume"] > merged[Locations.MAX_VOLUME_CAPACITY])
        | (merged["total_weight"] > merged[Locations.MAX_WEIGHT_CAPACITY])
    )

    return merged[[
        Locations.LOCATION_ID,
        Features.VOLUME_UTIL_PCT,
        Features.WEIGHT_UTIL_PCT,
        Features.SKU_COUNT_IN_LOC,
        "over_capacity",
    ]]


def build_zone_utilization(
    location_util: pd.DataFrame,
    locations: pd.DataFrame,
    zones: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate location utilisation to zone level.

    Returns
    -------
    pd.DataFrame with columns: zone_id, avg_volume_util_pct,
    avg_weight_util_pct, location_count, over_capacity_location_count.
    """
    loc_with_zone = locations.merge(
        location_util,
        on=Locations.LOCATION_ID,
        how="left",
    )

    zone_stats = (
        loc_with_zone
        .groupby(Locations.ZONE_ID)
        .agg(
            avg_volume_util_pct=(Features.VOLUME_UTIL_PCT, "mean"),
            avg_weight_util_pct=(Features.WEIGHT_UTIL_PCT, "mean"),
            location_count=(Locations.LOCATION_ID, "count"),
            over_capacity_locations=("over_capacity", "sum"),
        )
        .reset_index()
    )

    # Merge zone metadata
    result = zones[[Zones.ZONE_ID, Zones.ZONE_TYPE, Zones.PRIORITY_LEVEL,
                     Zones.DISTANCE_TO_DISPATCH]].merge(
        zone_stats, on=Zones.ZONE_ID, how="left",
    )
    result["over_capacity_location_count"] = (
        result["over_capacity_locations"].fillna(0).astype(int)
    )
    result.drop(columns=["over_capacity_locations"], inplace=True)

    return result


def build_distance_indicators(
    inventory: pd.DataFrame,
    locations: pd.DataFrame,
    zones: pd.DataFrame,
) -> pd.DataFrame:
    """Attach distance-to-dispatch and priority level to each inventory record.

    Returns
    -------
    pd.DataFrame with columns: sku_id, location_id, zone_id,
    distance_to_dispatch, priority_level.
    """
    loc_zone = locations.merge(
        zones[[Zones.ZONE_ID, Zones.PRIORITY_LEVEL,
               Zones.DISTANCE_TO_DISPATCH]],
        on=Zones.ZONE_ID,
        how="left",
    )
    result = inventory[[Inventory.SKU_ID, Inventory.LOCATION_ID]].merge(
        loc_zone[[Locations.LOCATION_ID, Locations.ZONE_ID,
                   Zones.PRIORITY_LEVEL, Zones.DISTANCE_TO_DISPATCH]],
        on=Inventory.LOCATION_ID,
        how="left",
    )
    return result


def build_alignment_score(
    demand_by_sku: pd.DataFrame,
    skus: pd.DataFrame,
    distance_indicators: pd.DataFrame,
) -> pd.DataFrame:
    """Compute a preliminary alignment flag and score per SKU.

    **⚠️  Non-prescriptive.** This is a simple heuristic for inspection,
    NOT a production-ready recommendation. It must be reviewed and calibrated
    before any operational use.

    Logic
    -----
    - For each SKU, compute the average distance-to-dispatch of its locations.
    - If a high-demand SKU (top 20 % by total demand) has an average distance
      below the median, it is flagged as **aligned** (alignment_flag = True).
    - The alignment_score is normalised to [0, 1]:
        1 = highest-demand SKU in closest locations.
        0 = lowest-demand SKU in farthest locations.

    Caveats
    -------
    - Does not consider weight, cube utilisation, or product affinity.
    - Single-DC assumption; multi-DC would need distance normalisation.
    - Thresholds (top 20 %, median) are arbitrary and dataset-dependent.
    """
    # Per-SKU average distance
    sku_distance = (
        distance_indicators
        .groupby(Inventory.SKU_ID)
        .agg(avg_distance=(Zones.DISTANCE_TO_DISPATCH, "mean"))
        .reset_index()
    )

    # Merge demand and SKU data
    aligned = skus[[Skus.SKU_ID, Skus.AVG_DAILY_DEMAND,
                     Skus.ROTATION_CLASS]].merge(
        demand_by_sku, on=Skus.SKU_ID, how="left",
    ).merge(
        sku_distance, on=Inventory.SKU_ID, how="left",
    )

    # Fill NaN (SKUs with no demand or no location)
    aligned[Features.TOTAL_DEMAND] = aligned[Features.TOTAL_DEMAND].fillna(0)
    aligned["avg_distance"] = aligned["avg_distance"].fillna(
        aligned["avg_distance"].median()
        if not aligned["avg_distance"].isna().all() else 999.0,
    )

    # Thresholds
    demand_threshold = aligned[Features.TOTAL_DEMAND].quantile(0.80)
    distance_median = aligned["avg_distance"].median()

    aligned[Features.ALIGNMENT_FLAG] = (
        (aligned[Features.TOTAL_DEMAND] >= demand_threshold)
        & (aligned["avg_distance"] <= distance_median)
    )

    # Normalised alignment score [0, 1]
    max_demand = aligned[Features.TOTAL_DEMAND].max()
    min_dist = aligned["avg_distance"].min()
    max_dist = aligned["avg_distance"].max()

    if max_demand > 0 and max_dist > min_dist:
        demand_norm = aligned[Features.TOTAL_DEMAND] / max_demand
        distance_norm = 1 - (
            (aligned["avg_distance"] - min_dist) / (max_dist - min_dist)
        )
        aligned[Features.ALIGNMENT_SCORE] = (demand_norm + distance_norm) / 2
    else:
        aligned[Features.ALIGNMENT_SCORE] = 0.5  # neutral fallback

    return aligned[[
        Skus.SKU_ID, Skus.AVG_DAILY_DEMAND, Skus.ROTATION_CLASS,
        Features.TOTAL_DEMAND, Features.ORDER_COUNT,
        "avg_distance", Features.ALIGNMENT_FLAG, Features.ALIGNMENT_SCORE,
    ]]


def build_all_features(
    datasets: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Run all feature builders and return a dict of output DataFrames.

    Returns
    -------
    dict with keys:
        - ``"features"``: Wide-format feature table (one row per SKU).
        - ``"location_utilization"``: Per-location utilisation details.
        - ``"zone_utilization"``: Per-zone utilisation summary.
    """
    skus        = datasets["skus"]
    inventory   = datasets["inventory"]
    locations   = datasets["locations"]
    zones       = datasets["zones"]
    order_lines = datasets["order_lines"]

    demand_by_sku     = build_demand_by_sku(order_lines)
    sku_footprint     = build_sku_footprint(inventory)
    loc_util          = build_location_utilization(inventory, locations)
    zone_util         = build_zone_utilization(loc_util, locations, zones)
    dist_indicators   = build_distance_indicators(inventory, locations, zones)
    alignment         = build_alignment_score(demand_by_sku, skus, dist_indicators)

    # Wide feature table: one row per SKU with all features merged
    features = skus.merge(demand_by_sku, on=Skus.SKU_ID, how="left") \
                   .merge(sku_footprint, on=Skus.SKU_ID, how="left") \
                   .merge(
                       alignment[[Skus.SKU_ID, Features.ALIGNMENT_FLAG,
                                   Features.ALIGNMENT_SCORE]],
                       on=Skus.SKU_ID,
                       how="left",
                   )

    # Ensure no silent drops — check row count
    if len(features) != len(skus):
        raise ValueError(
            f"Feature table has {len(features)} rows but SKU master has "
            f"{len(skus)} — records were silently dropped."
        )

    # Fill NaN demand/footprint with 0 (SKUs with no orders or no inventory)
    for col in [Features.TOTAL_DEMAND, Features.ORDER_COUNT,
                Features.TOTAL_VOLUME, Features.TOTAL_WEIGHT]:
        if col in features.columns:
            features[col] = features[col].fillna(0)

    return {
        "features": features,
        "location_utilization": loc_util,
        "zone_utilization": zone_util,
    }


def save_features(
    feature_outputs: dict[str, pd.DataFrame],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Save feature DataFrames to ``data/processed/``.

    Parameters
    ----------
    feature_outputs : dict
        Output from ``build_all_features``.
    output_dir : Path or None
        Target directory. Defaults to ``DATA_PROCESSED_DIR``.

    Returns
    -------
    dict mapping output name to file path that was written.
    """
    output_dir = output_dir or DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}

    # Main feature table → Parquet (compact, typed, fast)
    fpath = output_dir / "slotting_features.parquet"
    feature_outputs["features"].to_parquet(fpath, index=False)
    paths["features"] = fpath

    # Location utilisation → CSV (easy to inspect)
    lpath = output_dir / "location_utilization.csv"
    feature_outputs["location_utilization"].to_csv(lpath, index=False)
    paths["location_utilization"] = lpath

    # Zone utilisation → CSV
    zpath = output_dir / "zone_utilization.csv"
    feature_outputs["zone_utilization"].to_csv(zpath, index=False)
    paths["zone_utilization"] = zpath

    return paths
