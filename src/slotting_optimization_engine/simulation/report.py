"""
Phase 6 — Simulation report builder.

Compiles all simulation results (travel, workload, throughput) into
structured CSV outputs and a summary table.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from slotting_optimization_engine.config.project_paths import DATA_PROCESSED_DIR
from slotting_optimization_engine.simulation.config import SIMULATION_CAVEAT


def build_simulation_report(
    travel_result: dict,
    workload_result: dict,
    throughput_result: dict,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Compile all simulation results into output DataFrames.

    Parameters
    ----------
    travel_result : dict
        Output from ``simulate_travel()``.
    workload_result : dict
        Output from ``simulate_workload()``.
    throughput_result : dict
        Output from ``estimate_throughput()``.
    output_dir : Path | None
        Directory to write CSVs (default: ``DATA_PROCESSED_DIR``).

    Returns
    -------
    dict with keys:
        * ``simulation_summary`` — top-level metrics in a tall table
        * ``travel_aggregate``   — travel metrics as a tall table
        * ``zone_detail``        — per-zone pick counts (pre / post)
        * ``throughput_scenarios`` — throughput scenario comparison
        * ``travel_order_detail`` — top-N per-order detail
    """
    # ── Summary: flatten key metrics into a tall DataFrame ───────────────
    travel_agg = travel_result.get("aggregate", {})
    workload_agg = workload_result.get("aggregate", {})
    throughput_agg = throughput_result.get("aggregate", {})

    summary_rows: list[dict[str, object]] = [
        ("total_orders_simulated", travel_agg.get("total_orders_simulated")),
        ("total_current_distance_m", travel_agg.get("total_current_distance_m")),
        ("total_optimized_distance_m", travel_agg.get("total_optimized_distance_m")),
        ("total_distance_saved_m", travel_agg.get("total_distance_saved_m")),
        ("total_time_saved_s", travel_agg.get("total_time_saved_s")),
        ("avg_distance_per_order_current", travel_agg.get("avg_distance_per_order_current")),
        ("avg_distance_per_order_optimized", travel_agg.get("avg_distance_per_order_optimized")),
        ("avg_improvement_pct", travel_agg.get("avg_improvement_pct")),
        ("orders_with_improvement", travel_agg.get("orders_with_improvement")),
        ("gini_coefficient_before", workload_agg.get("gini_coefficient_before")),
        ("gini_coefficient_after", workload_agg.get("gini_coefficient_after")),
        ("gini_change", workload_agg.get("gini_change")),
        ("balance_improved", workload_agg.get("balance_improved")),
        ("total_picks_current", workload_agg.get("total_picks_current")),
        ("total_picks_optimized", workload_agg.get("total_picks_optimized")),
        ("orders_per_shift_current", throughput_agg.get("orders_per_shift_current")),
        ("orders_per_shift_optimized", throughput_agg.get("orders_per_shift_optimized")),
        ("throughput_gain_pct", throughput_agg.get("throughput_gain_pct")),
        ("recommended_scenario", throughput_agg.get("recommended_scenario")),
    ]

    summary = pd.DataFrame(
        {"metric": [r[0] for r in summary_rows], "value": [r[1] for r in summary_rows]}
    )
    summary["assumption_state"] = "inferred / pending confirmation"
    summary["simulation_caveat"] = SIMULATION_CAVEAT

    # ── Travel aggregate as tall table ───────────────────────────────────
    travel_tall = pd.DataFrame(
        {"metric": list(travel_agg.keys()), "value": list(travel_agg.values())}
    )

    # ── Zone detail ──────────────────────────────────────────────────────
    zone_detail = workload_result.get("zone_detail")
    if zone_detail is not None and isinstance(zone_detail, pd.DataFrame):
        zone_detail = zone_detail.copy()
        zone_detail["assumption_state"] = "inferred / pending confirmation"
        zone_detail["simulation_caveat"] = SIMULATION_CAVEAT

    # ── Throughput scenario table ────────────────────────────────────────
    throughput_table = throughput_result.get("scenario_table")
    if isinstance(throughput_table, pd.DataFrame) and not throughput_table.empty:
        throughput_table = throughput_table.copy()

    # ── Top-N order detail ────────────────────────────────────────────────
    order_detail = travel_result.get("order_detail")
    if isinstance(order_detail, pd.DataFrame) and not order_detail.empty:
        order_detail = order_detail.head(100).copy()
        order_detail["assumption_state"] = "inferred / pending confirmation"
        order_detail["simulation_caveat"] = SIMULATION_CAVEAT

    return {
        "simulation_summary": summary,
        "travel_aggregate": travel_tall,
        "zone_detail": zone_detail,
        "throughput_scenarios": throughput_table,
        "travel_order_detail": order_detail,
    }


def save_simulation_outputs(
    reports: dict[str, pd.DataFrame | None],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Save simulation output DataFrames to CSV files.

    Parameters
    ----------
    reports : dict
        Output from ``build_simulation_report()``.
    output_dir : Path | None
        Directory (default ``DATA_PROCESSED_DIR``).

    Returns
    -------
    dict mapping report keys to their saved file paths.
    """
    output_dir = output_dir or DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    name_map = {
        "simulation_summary": "simulation_summary.csv",
        "travel_aggregate": "simulation_travel_aggregate.csv",
        "zone_detail": "simulation_zone_impact.csv",
        "throughput_scenarios": "simulation_throughput_scenarios.csv",
        "travel_order_detail": "simulation_order_detail.csv",
    }

    paths: dict[str, Path] = {}
    for key, filename in name_map.items():
        df = reports.get(key)
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            path = output_dir / filename
            df.to_csv(path, index=False)
            paths[key] = path
    return paths
