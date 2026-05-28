"""Tests for pure dashboard helper functions used by the Streamlit UI."""

from pathlib import Path

import pandas as pd

from slotting_optimization_engine.app.dashboard_data import (
    DashboardData,
    compute_kpis,
    inspect_processed_output,
    location_chart_data,
    missing_outputs,
    preview_table,
    status_table,
    zone_chart_data,
)
from slotting_optimization_engine.domain.constants import Features, Locations, Skus, Zones


def test_inspect_processed_output_reports_missing_file(tmp_path: Path) -> None:
    status, dataframe = inspect_processed_output("SKU features", tmp_path / "missing.parquet")

    assert not status.exists
    assert status.row_count is None
    assert dataframe is None


def test_compute_kpis_from_loaded_outputs() -> None:
    data = DashboardData(
        sku_features=pd.DataFrame({Skus.SKU_ID: ["SKU-1", "SKU-2"]}),
        location_utilization=pd.DataFrame({
            Locations.LOCATION_ID: ["L-1", "L-2", "L-3"],
            Features.VOLUME_UTIL_PCT: [50.0, 80.0, 100.0],
            Features.WEIGHT_UTIL_PCT: [40.0, 70.0, 90.0],
            "over_capacity": [False, True, False],
        }),
        zone_utilization=pd.DataFrame({Zones.ZONE_ID: ["Z-1", "Z-2"]}),
        slotting_diagnostics=None,
        location_diagnostics=None,
        zone_diagnostics=None,
        category_diagnostics=None,
        diagnostic_summary=None,
        statuses=(),
    )

    kpis = compute_kpis(data)

    assert kpis["sku_count"] == 2
    assert kpis["zone_count"] == 2
    assert kpis["location_count"] == 3
    assert kpis["avg_utilization_pct"] == 71.66666666666667
    assert kpis["over_capacity_locations"] == 1


def test_missing_outputs_and_status_table() -> None:
    missing_status, _ = inspect_processed_output("Zones", Path("does-not-exist.csv"))

    assert missing_outputs((missing_status,)) == (missing_status,)

    table = status_table((missing_status,))

    assert table.loc[0, "dataset"] == "Zones"
    assert table.loc[0, "disponible"] == "❌ No"


def test_preview_table_returns_bounded_copy() -> None:
    dataframe = pd.DataFrame({"value": [1, 2, 3]})

    preview = preview_table(dataframe, rows=2)


    assert list(preview["value"]) == [1, 2]
    assert preview is not dataframe


def test_chart_helpers_return_expected_indexes() -> None:
    zone_chart = zone_chart_data(pd.DataFrame({
        Zones.ZONE_ID: ["Z-1"],
        "avg_volume_util_pct": [55.0],
        "avg_weight_util_pct": [45.0],
    }))
    location_chart = location_chart_data(pd.DataFrame({
        Locations.LOCATION_ID: ["L-1", "L-2"],
        Features.VOLUME_UTIL_PCT: [30.0, 90.0],
        Features.WEIGHT_UTIL_PCT: [20.0, 70.0],
    }))

    assert list(zone_chart.index) == ["Z-1"]
    assert list(location_chart.index) == ["L-2", "L-1"]
