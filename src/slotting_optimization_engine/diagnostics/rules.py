"""Descriptive Phase 2 slotting diagnostics.

The thresholds below are inferred from the synthetic data model and are pending
business confirmation. They create inspection flags only; they do not prescribe
SKU moves, zone resizing, or any operational action.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from slotting_optimization_engine.config.project_paths import DATA_PROCESSED_DIR
from slotting_optimization_engine.domain.constants import (
    Features,
    Inventory,
    Locations,
    Skus,
    Zones,
)


@dataclass(frozen=True)
class DiagnosticConfig:
    """Simple inferred thresholds for descriptive diagnostics.

    All values are pending business confirmation. They are intentionally simple
    so analysts can review why a diagnostic row was flagged.
    """

    high_demand_quantile: float = 0.80
    low_demand_quantile: float = 0.20
    long_distance_quantile: float = 0.75
    premium_priority_max: int = 2
    low_priority_min: int = 3
    overutilized_pct: float = 85.0
    underutilized_pct: float = 20.0
    dense_location_sku_count: int = 3
    category_spread_zone_min: int = 3
    category_dominance_max: float = 0.60


def build_all_diagnostics(
    sku_features: pd.DataFrame,
    location_utilization: pd.DataFrame,
    zone_utilization: pd.DataFrame,
    datasets: dict[str, pd.DataFrame],
    config: DiagnosticConfig | None = None,
) -> dict[str, pd.DataFrame]:
    """Build every Phase 2 descriptive diagnostic output."""
    config = config or DiagnosticConfig()
    placement = _build_placement_table(
        datasets["inventory"], datasets["locations"], datasets["zones"]
    )

    slotting = build_slotting_diagnostics(sku_features, placement, config)
    location = build_location_diagnostics(location_utilization, placement, sku_features, config)
    zone = build_zone_diagnostics(zone_utilization, placement, sku_features, config)
    category = build_category_diagnostics(placement, sku_features, config)
    summary = build_diagnostic_summary(slotting, location, zone, category, config)

    return {
        "slotting_diagnostics": slotting,
        "location_diagnostics": location,
        "zone_diagnostics": zone,
        "category_diagnostics": category,
        "diagnostic_summary": summary,
    }


def build_slotting_diagnostics(
    sku_features: pd.DataFrame,
    placement: pd.DataFrame,
    config: DiagnosticConfig | None = None,
) -> pd.DataFrame:
    """Flag SKU placement diagnostics without recommending moves."""
    config = config or DiagnosticConfig()
    sku_placement = _sku_placement_summary(placement)
    diagnostics = sku_features.merge(sku_placement, on=Skus.SKU_ID, how="left")

    demand = diagnostics[Features.TOTAL_DEMAND].fillna(0)
    high_demand_threshold = float(demand.quantile(config.high_demand_quantile))
    low_demand_threshold = float(demand.quantile(config.low_demand_quantile))
    long_distance_threshold = _safe_quantile(
        diagnostics[Zones.DISTANCE_TO_DISPATCH], config.long_distance_quantile, fallback=0.0
    )

    diagnostics["high_demand_threshold"] = high_demand_threshold
    diagnostics["low_demand_threshold"] = low_demand_threshold
    diagnostics["long_distance_threshold"] = long_distance_threshold

    diagnostics["is_high_demand"] = demand >= high_demand_threshold
    diagnostics["is_low_demand_or_rotation"] = (
        (demand <= low_demand_threshold)
        | diagnostics[Skus.ROTATION_CLASS].isin(["C", "D"])
    )
    diagnostics["has_long_distance_placement"] = (
        diagnostics[Zones.DISTANCE_TO_DISPATCH].fillna(0) >= long_distance_threshold
    )
    diagnostics["has_low_priority_placement"] = (
        diagnostics[Zones.PRIORITY_LEVEL].fillna(config.low_priority_min) >= config.low_priority_min
    )
    diagnostics["occupies_premium_zone"] = (
        diagnostics["min_priority_level"].fillna(config.low_priority_min)
        <= config.premium_priority_max
    )
    diagnostics["high_demand_poor_placement_flag"] = (
        diagnostics["is_high_demand"]
        & (diagnostics["has_long_distance_placement"] | diagnostics["has_low_priority_placement"])
    )
    diagnostics["low_demand_premium_zone_flag"] = (
        diagnostics["is_low_demand_or_rotation"] & diagnostics["occupies_premium_zone"]
    )
    diagnostics["diagnostic_count"] = diagnostics[
        ["high_demand_poor_placement_flag", "low_demand_premium_zone_flag"]
    ].sum(axis=1)
    diagnostics["diagnostic_severity"] = diagnostics["diagnostic_count"].map(
        {0: "none", 1: "review", 2: "high_review"}
    )
    diagnostics["business_rule_state"] = "inferred / pending confirmation"

    return diagnostics[[
        Skus.SKU_ID,
        Skus.CATEGORY,
        Skus.ROTATION_CLASS,
        Features.TOTAL_DEMAND,
        Features.ORDER_COUNT,
        "location_count",
        "zone_count",
        Zones.DISTANCE_TO_DISPATCH,
        Zones.PRIORITY_LEVEL,
        "min_priority_level",
        "high_demand_threshold",
        "low_demand_threshold",
        "long_distance_threshold",
        "is_high_demand",
        "is_low_demand_or_rotation",
        "has_long_distance_placement",
        "has_low_priority_placement",
        "occupies_premium_zone",
        "high_demand_poor_placement_flag",
        "low_demand_premium_zone_flag",
        "diagnostic_count",
        "diagnostic_severity",
        "business_rule_state",
    ]]


def build_location_diagnostics(
    location_utilization: pd.DataFrame,
    placement: pd.DataFrame,
    sku_features: pd.DataFrame,
    config: DiagnosticConfig | None = None,
) -> pd.DataFrame:
    """Flag location utilization, density, and category-mix concerns."""
    config = config or DiagnosticConfig()
    enriched = placement.merge(
        sku_features[[Skus.SKU_ID, Skus.CATEGORY, Features.TOTAL_DEMAND]],
        on=Skus.SKU_ID,
        how="left",
        suffixes=("", "_feature"),
    )
    category_col = (
        f"{Skus.CATEGORY}_feature"
        if f"{Skus.CATEGORY}_feature" in enriched
        else Skus.CATEGORY
    )
    loc_mix = enriched.groupby(Locations.LOCATION_ID).agg(
        category_count=(category_col, "nunique"),
        assigned_sku_count=(Skus.SKU_ID, "nunique"),
        total_location_demand=(Features.TOTAL_DEMAND, "sum"),
    ).reset_index()

    diagnostics = location_utilization.merge(loc_mix, on=Locations.LOCATION_ID, how="left")
    for column in ["category_count", "assigned_sku_count", "total_location_demand"]:
        diagnostics[column] = diagnostics[column].fillna(0)
    diagnostics["avg_utilization_pct"] = diagnostics[
        [Features.VOLUME_UTIL_PCT, Features.WEIGHT_UTIL_PCT]
    ].mean(axis=1)
    over_capacity = (
        diagnostics["over_capacity"].fillna(False).astype(bool)
        if "over_capacity" in diagnostics
        else False
    )
    diagnostics["overutilized_flag"] = (
        diagnostics["avg_utilization_pct"] >= config.overutilized_pct
    ) | over_capacity
    diagnostics["underutilized_flag"] = (
        diagnostics["avg_utilization_pct"] <= config.underutilized_pct
    )
    diagnostics["density_concern_flag"] = (
        diagnostics[Features.SKU_COUNT_IN_LOC] >= config.dense_location_sku_count
    )
    diagnostics["category_mix_flag"] = diagnostics["category_count"] > 2
    diagnostics["diagnostic_count"] = diagnostics[
        ["overutilized_flag", "underutilized_flag", "density_concern_flag", "category_mix_flag"]
    ].sum(axis=1)
    diagnostics["business_rule_state"] = "inferred / pending confirmation"
    return diagnostics


def build_zone_diagnostics(
    zone_utilization: pd.DataFrame,
    placement: pd.DataFrame,
    sku_features: pd.DataFrame,
    config: DiagnosticConfig | None = None,
) -> pd.DataFrame:
    """Flag zone utilization and premium-zone demand mix diagnostics."""
    config = config or DiagnosticConfig()
    enriched = placement.merge(
        sku_features[[Skus.SKU_ID, Features.TOTAL_DEMAND, Skus.ROTATION_CLASS]],
        on=Skus.SKU_ID,
        how="left",
    )
    low_demand_threshold = _safe_quantile(
        enriched[Features.TOTAL_DEMAND], config.low_demand_quantile, 0.0
    )
    zone_mix = enriched.groupby(Zones.ZONE_ID).agg(
        assigned_sku_count=(Skus.SKU_ID, "nunique"),
        low_demand_sku_count=(
            Features.TOTAL_DEMAND,
            lambda s: int((s.fillna(0) <= low_demand_threshold).sum()),
        ),
        slow_rotation_sku_count=(Skus.ROTATION_CLASS, lambda s: int(s.isin(["C", "D"]).sum())),
    ).reset_index()
    diagnostics = zone_utilization.merge(zone_mix, on=Zones.ZONE_ID, how="left")
    for column in ["assigned_sku_count", "low_demand_sku_count", "slow_rotation_sku_count"]:
        diagnostics[column] = diagnostics[column].fillna(0).astype(int)
    diagnostics["avg_utilization_pct"] = diagnostics[
        ["avg_volume_util_pct", "avg_weight_util_pct"]
    ].mean(axis=1)
    diagnostics["overutilized_zone_flag"] = (
        (diagnostics["avg_utilization_pct"] >= config.overutilized_pct)
        | (diagnostics["over_capacity_location_count"].fillna(0) > 0)
    )
    diagnostics["underutilized_zone_flag"] = (
        diagnostics["avg_utilization_pct"] <= config.underutilized_pct
    )
    diagnostics["premium_zone_slow_mover_flag"] = (
        (diagnostics[Zones.PRIORITY_LEVEL] <= config.premium_priority_max)
        & ((diagnostics["low_demand_sku_count"] > 0) | (diagnostics["slow_rotation_sku_count"] > 0))
    )
    diagnostics["business_rule_state"] = "inferred / pending confirmation"
    return diagnostics


def build_category_diagnostics(
    placement: pd.DataFrame,
    sku_features: pd.DataFrame,
    config: DiagnosticConfig | None = None,
) -> pd.DataFrame:
    """Describe category spread and grouping concentration by zone."""
    config = config or DiagnosticConfig()
    enriched = placement.merge(
        sku_features[[Skus.SKU_ID, Skus.CATEGORY, Features.TOTAL_DEMAND]],
        on=Skus.SKU_ID,
        how="left",
        suffixes=("", "_feature"),
    )
    category_col = (
        f"{Skus.CATEGORY}_feature"
        if f"{Skus.CATEGORY}_feature" in enriched
        else Skus.CATEGORY
    )
    total_by_category = enriched.groupby(category_col)[Skus.SKU_ID].nunique().rename("sku_count")
    top_zone_share = (
        enriched.groupby([category_col, Zones.ZONE_ID])[Skus.SKU_ID]
        .nunique()
        .groupby(level=0)
        .max()
        .div(total_by_category)
        .rename("top_zone_sku_share")
    )
    diagnostics = enriched.groupby(category_col).agg(
        zone_count=(Zones.ZONE_ID, "nunique"),
        location_count=(Locations.LOCATION_ID, "nunique"),
        total_demand=(Features.TOTAL_DEMAND, "sum"),
    ).join(total_by_category).join(top_zone_share).reset_index()
    diagnostics = diagnostics.rename(columns={category_col: Skus.CATEGORY})
    diagnostics["category_spread_flag"] = (
        diagnostics["zone_count"] >= config.category_spread_zone_min
    )
    diagnostics["category_misgrouping_indicator"] = (
        diagnostics["category_spread_flag"]
        & (diagnostics["top_zone_sku_share"].fillna(0) <= config.category_dominance_max)
    )
    diagnostics["business_rule_state"] = "inferred / pending confirmation"
    return diagnostics


def build_diagnostic_summary(
    slotting: pd.DataFrame,
    location: pd.DataFrame,
    zone: pd.DataFrame,
    category: pd.DataFrame,
    config: DiagnosticConfig,
) -> pd.DataFrame:
    """Create a small one-row-per-metric diagnostic summary."""
    rows = [
        (
            "high_demand_poor_placement_skus",
            int(slotting["high_demand_poor_placement_flag"].sum()),
        ),
        (
            "low_demand_premium_zone_skus",
            int(slotting["low_demand_premium_zone_flag"].sum()),
        ),
        ("overutilized_locations", int(location["overutilized_flag"].sum())),
        ("underutilized_locations", int(location["underutilized_flag"].sum())),
        ("overutilized_zones", int(zone["overutilized_zone_flag"].sum())),
        ("underutilized_zones", int(zone["underutilized_zone_flag"].sum())),
        (
            "category_misgrouping_indicators",
            int(category["category_misgrouping_indicator"].sum()),
        ),
    ]
    return pd.DataFrame({
        "metric": [row[0] for row in rows],
        "value": [row[1] for row in rows],
        "business_rule_state": "inferred / pending confirmation",
        "threshold_note": _threshold_note(config),
    })


def save_diagnostics(
    diagnostic_outputs: dict[str, pd.DataFrame],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Save diagnostic outputs as CSV files in ``data/processed``."""
    output_dir = output_dir or DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    for name, dataframe in diagnostic_outputs.items():
        path = output_dir / f"{name}.csv"
        dataframe.to_csv(path, index=False)
        paths[name] = path
    return paths


def _build_placement_table(
    inventory: pd.DataFrame,
    locations: pd.DataFrame,
    zones: pd.DataFrame,
) -> pd.DataFrame:
    return inventory[[Inventory.SKU_ID, Inventory.LOCATION_ID]].merge(
        locations[[Locations.LOCATION_ID, Locations.ZONE_ID]],
        on=Locations.LOCATION_ID,
        how="left",
    ).merge(
        zones[[
            Zones.ZONE_ID,
            Zones.ZONE_TYPE,
            Zones.PRIORITY_LEVEL,
            Zones.DISTANCE_TO_DISPATCH,
        ]],
        on=Zones.ZONE_ID,
        how="left",
    )


def _sku_placement_summary(placement: pd.DataFrame) -> pd.DataFrame:
    return placement.groupby(Skus.SKU_ID).agg(
        location_count=(Locations.LOCATION_ID, "nunique"),
        zone_count=(Zones.ZONE_ID, "nunique"),
        distance_to_dispatch=(Zones.DISTANCE_TO_DISPATCH, "mean"),
        priority_level=(Zones.PRIORITY_LEVEL, "mean"),
        min_priority_level=(Zones.PRIORITY_LEVEL, "min"),
    ).reset_index()


def _safe_quantile(series: pd.Series, quantile: float, fallback: float) -> float:
    clean = series.dropna()
    if clean.empty:
        return fallback
    return float(clean.quantile(quantile))


def _threshold_note(config: DiagnosticConfig) -> str:
    return (
        "Thresholds inferred/pending confirmation: "
        f"high demand q{config.high_demand_quantile}, "
        f"low demand q{config.low_demand_quantile}, "
        f"long distance q{config.long_distance_quantile}, premium priority <= "
        f"{config.premium_priority_max}, overutilized >= {config.overutilized_pct}%, "
        f"underutilized <= {config.underutilized_pct}%."
    )
