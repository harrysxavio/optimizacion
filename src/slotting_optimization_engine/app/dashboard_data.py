"""Reusable data loading and summary helpers for the technical Streamlit app.

This module intentionally keeps Streamlit out of the data layer. The UI imports
these pure helpers to inspect Phase 1 processed outputs without owning business
logic or feature calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from slotting_optimization_engine.config.project_paths import DATA_PROCESSED_DIR
from slotting_optimization_engine.domain.constants import (
    Features,
    Locations,
    Skus,
    Zones,
)

EXPECTED_OUTPUT_FILES: dict[str, str] = {
    "SKU features": "slotting_features.parquet",
    "Location utilization": "location_utilization.csv",
    "Zone utilization": "zone_utilization.csv",
    "Slotting diagnostics": "slotting_diagnostics.csv",
    "Location diagnostics": "location_diagnostics.csv",
    "Zone diagnostics": "zone_diagnostics.csv",
    "Category diagnostics": "category_diagnostics.csv",
    "Diagnostic summary": "diagnostic_summary.csv",
}

PREREQUISITE_COMMANDS: tuple[str, ...] = (
    "python scripts/generate_sample_data.py",
    "python scripts/run_data_validation.py",
    "python scripts/build_features.py",
    "python scripts/run_diagnostics.py",
)


@dataclass(frozen=True)
class DatasetStatus:
    """Availability and shape metadata for one processed output."""

    name: str
    path: Path
    exists: bool
    row_count: int | None = None
    column_count: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class DashboardData:
    """Loaded Phase 1 outputs plus their availability metadata."""

    sku_features: pd.DataFrame | None
    location_utilization: pd.DataFrame | None
    zone_utilization: pd.DataFrame | None
    slotting_diagnostics: pd.DataFrame | None
    location_diagnostics: pd.DataFrame | None
    zone_diagnostics: pd.DataFrame | None
    category_diagnostics: pd.DataFrame | None
    diagnostic_summary: pd.DataFrame | None
    statuses: tuple[DatasetStatus, ...]


def _load_dataframe(path: Path) -> pd.DataFrame:
    """Load a supported processed output by extension."""
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)

    raise ValueError(f"Unsupported dashboard input format: {path.suffix}")


def inspect_processed_output(name: str, path: Path) -> tuple[DatasetStatus, pd.DataFrame | None]:
    """Return availability metadata and a dataframe for a processed output.

    Missing or unreadable files are represented as status objects instead of
    exceptions so the technical UI can guide the analyst toward regeneration.
    """
    if not path.exists():
        return DatasetStatus(name=name, path=path, exists=False), None

    try:
        dataframe = _load_dataframe(path)
    except Exception as exc:  # pragma: no cover - exact parser errors vary by backend
        return DatasetStatus(name=name, path=path, exists=True, error=str(exc)), None

    return (
        DatasetStatus(
            name=name,
            path=path,
            exists=True,
            row_count=len(dataframe),
            column_count=len(dataframe.columns),
        ),
        dataframe,
    )


def load_dashboard_data(processed_dir: Path | None = None) -> DashboardData:
    """Load all Phase 1 outputs expected by the Streamlit inspection app."""
    base_dir = processed_dir or DATA_PROCESSED_DIR

    loaded: dict[str, pd.DataFrame | None] = {}
    statuses: list[DatasetStatus] = []

    for name, filename in EXPECTED_OUTPUT_FILES.items():
        status, dataframe = inspect_processed_output(name, base_dir / filename)
        statuses.append(status)
        loaded[name] = dataframe

    return DashboardData(
        sku_features=loaded["SKU features"],
        location_utilization=loaded["Location utilization"],
        zone_utilization=loaded["Zone utilization"],
        slotting_diagnostics=loaded["Slotting diagnostics"],
        location_diagnostics=loaded["Location diagnostics"],
        zone_diagnostics=loaded["Zone diagnostics"],
        category_diagnostics=loaded["Category diagnostics"],
        diagnostic_summary=loaded["Diagnostic summary"],
        statuses=tuple(statuses),
    )


def missing_outputs(statuses: tuple[DatasetStatus, ...]) -> tuple[DatasetStatus, ...]:
    """Return files that are missing or failed to load."""
    return tuple(status for status in statuses if not status.exists or status.error)


def status_table(statuses: tuple[DatasetStatus, ...]) -> pd.DataFrame:
    """Convert statuses into a UI-friendly table."""
    rows = [
        {
            "dataset": status.name,
            "available": "Yes" if status.exists and not status.error else "No",
            "rows": status.row_count,
            "columns": status.column_count,
            "path": str(status.path),
            "error": status.error or "",
        }
        for status in statuses
    ]
    return pd.DataFrame(rows)


def compute_kpis(data: DashboardData) -> dict[str, int | float | None]:
    """Compute high-level inspection KPIs from already-built Phase 1 outputs."""
    sku_features = data.sku_features
    location_util = data.location_utilization
    zone_util = data.zone_utilization

    sku_count = _unique_or_len(sku_features, Skus.SKU_ID)
    zone_count = _unique_or_len(zone_util, Zones.ZONE_ID)
    location_count = _unique_or_len(location_util, Locations.LOCATION_ID)

    avg_utilization = None
    if location_util is not None:
        util_columns = [
            column
            for column in (Features.VOLUME_UTIL_PCT, Features.WEIGHT_UTIL_PCT)
            if column in location_util.columns
        ]
        if util_columns:
            avg_utilization = float(location_util[util_columns].mean(axis=1).mean())

    over_capacity_locations = None
    if location_util is not None and "over_capacity" in location_util.columns:
        over_capacity_locations = int(location_util["over_capacity"].fillna(False).sum())
    elif zone_util is not None and "over_capacity_location_count" in zone_util.columns:
        over_capacity_locations = int(zone_util["over_capacity_location_count"].fillna(0).sum())

    return {
        "sku_count": sku_count,
        "zone_count": zone_count,
        "location_count": location_count,
        "avg_utilization_pct": avg_utilization,
        "over_capacity_locations": over_capacity_locations,
    }


def preview_table(dataframe: pd.DataFrame | None, rows: int = 25) -> pd.DataFrame:
    """Return a bounded preview copy for UI display."""
    if dataframe is None:
        return pd.DataFrame()
    return dataframe.head(rows).copy()


def zone_chart_data(zone_utilization: pd.DataFrame | None) -> pd.DataFrame:
    """Return zone utilization columns suitable for Streamlit native charts."""
    if zone_utilization is None or Zones.ZONE_ID not in zone_utilization.columns:
        return pd.DataFrame()

    available_columns = [
        column
        for column in ("avg_volume_util_pct", "avg_weight_util_pct")
        if column in zone_utilization.columns
    ]
    if not available_columns:
        return pd.DataFrame()

    return zone_utilization.set_index(Zones.ZONE_ID)[available_columns]


def location_chart_data(location_utilization: pd.DataFrame | None, rows: int = 25) -> pd.DataFrame:
    """Return top utilized locations suitable for Streamlit native charts."""
    if location_utilization is None or Locations.LOCATION_ID not in location_utilization.columns:
        return pd.DataFrame()

    available_columns = [
        column
        for column in (Features.VOLUME_UTIL_PCT, Features.WEIGHT_UTIL_PCT)
        if column in location_utilization.columns
    ]
    if not available_columns:
        return pd.DataFrame()

    chart_data = location_utilization.copy()
    chart_data["avg_utilization_pct"] = chart_data[available_columns].mean(axis=1)
    chart_data = chart_data.sort_values("avg_utilization_pct", ascending=False).head(rows)
    return chart_data.set_index(Locations.LOCATION_ID)[available_columns]


def _unique_or_len(dataframe: pd.DataFrame | None, column: str) -> int | None:
    if dataframe is None:
        return None
    if column in dataframe.columns:
        return int(dataframe[column].nunique())
    return len(dataframe)
