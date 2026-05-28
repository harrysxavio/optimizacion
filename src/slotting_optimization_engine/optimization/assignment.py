"""Phase 5 controlled SKU-to-zone assignment optimization prototype.

This module builds transparent assignment recommendations on synthetic data. It
does not execute moves, guarantee location-level feasibility, or replace
warehouse engineering review.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from slotting_optimization_engine.config.project_paths import DATA_PROCESSED_DIR, DATA_SYNTHETIC_DIR
from slotting_optimization_engine.domain.constants import Skus, Zones
from slotting_optimization_engine.scoring.prioritization import BUSINESS_RULE_STATE

OPTIMIZATION_CAVEAT = (
    "Prototype on synthetic data with inferred weights; no physical move execution, "
    "no guaranteed feasible location slot, and not a full warehouse-grade optimizer."
)


@dataclass(frozen=True)
class AssignmentConfig:
    """Inferred weights and limits for the Phase 5 prototype."""

    top_n_skus: int = 12
    max_slots_per_zone: int = 3
    demand_access_weight: float = 0.35
    slow_mover_access_weight: float = 0.15
    capacity_pressure_weight: float = 0.20
    opportunity_reward_weight: float = 0.20
    scenario_reward_weight: float = 0.10
    assumption_state: str = BUSINESS_RULE_STATE


def load_optimization_inputs(
    processed_dir: Path | None = None,
    synthetic_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Load Phase 3/4 outputs and synthetic dimensions needed by Phase 5."""
    processed_dir = processed_dir or DATA_PROCESSED_DIR
    synthetic_dir = synthetic_dir or DATA_SYNTHETIC_DIR
    required_files = {
        "priority_queue": processed_dir / "priority_recommendation_queue.csv",
        "slotting_diagnostics": processed_dir / "slotting_diagnostics.csv",
        "zone_diagnostics": processed_dir / "zone_diagnostics.csv",
        "skus": synthetic_dir / "skus.csv",
        "zones": synthetic_dir / "zones.csv",
    }
    missing = [str(path) for path in required_files.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing Phase 5 optimization input(s): "
            + ", ".join(missing)
            + ". Run Phase 1-4 commands through `python scripts/run_scenarios.py` first."
        )

    inputs = {name: pd.read_csv(path) for name, path in required_files.items()}
    scenario_path = processed_dir / "scenario_comparison.csv"
    if scenario_path.is_file():
        inputs["scenario_comparison"] = pd.read_csv(scenario_path)
    return inputs


def select_candidate_skus(
    priority_queue: pd.DataFrame,
    config: AssignmentConfig | None = None,
) -> pd.DataFrame:
    """Select top-N SKU candidates from the Phase 3 review queue."""
    config = config or AssignmentConfig()
    required = {
        "queue_position",
        "priority",
        "opportunity_score",
        "entity_type",
        "entity_id",
        "candidate_action",
        "reason",
    }
    missing = sorted(required.difference(priority_queue.columns))
    if missing:
        raise ValueError("Missing required priority queue column(s): " + ", ".join(missing))

    candidates = priority_queue[priority_queue["entity_type"].eq("sku")].copy()
    candidates["opportunity_score"] = pd.to_numeric(
        candidates["opportunity_score"], errors="coerce"
    ).fillna(0.0)
    candidates["queue_position"] = pd.to_numeric(
        candidates["queue_position"], errors="coerce"
    ).fillna(999999)
    return candidates.sort_values(
        ["opportunity_score", "queue_position", "entity_id"],
        ascending=[False, True, True],
    ).head(config.top_n_skus).reset_index(drop=True)


def build_assignment_cost_matrix(
    candidates: pd.DataFrame,
    skus: pd.DataFrame,
    zones: pd.DataFrame,
    slotting_diagnostics: pd.DataFrame,
    zone_diagnostics: pd.DataFrame,
    scenario_comparison: pd.DataFrame | None = None,
    config: AssignmentConfig | None = None,
) -> pd.DataFrame:
    """Build a transparent SKU-zone-slot cost matrix for assignment."""
    config = config or AssignmentConfig()
    sku_context = _build_sku_context(candidates, skus, slotting_diagnostics, scenario_comparison)
    zone_slots = _build_zone_slots(zones, zone_diagnostics, config)
    if sku_context.empty:
        raise ValueError("No SKU candidates available for optimization assignment.")
    if zone_slots.empty:
        raise ValueError("No target zone slots available for optimization assignment.")

    rows: list[dict[str, object]] = []
    for _, sku in sku_context.iterrows():
        for _, zone in zone_slots.iterrows():
            access_cost = _normalise_value(
                zone[Zones.DISTANCE_TO_DISPATCH], zone_slots[Zones.DISTANCE_TO_DISPATCH]
            )
            priority_cost = _normalise_value(
                zone[Zones.PRIORITY_LEVEL], zone_slots[Zones.PRIORITY_LEVEL]
            )
            zone_access_cost = (access_cost + priority_cost) / 2
            demand_norm = _ratio_to_max(sku["total_demand"], sku_context["total_demand"])
            opportunity_norm = float(sku["opportunity_score"]) / 100
            scenario_norm = _ratio_to_max(
                sku["scenario_weighted_score"], sku_context["scenario_weighted_score"]
            )
            capacity_pressure = float(zone["capacity_pressure"])
            cost = (
                config.demand_access_weight * demand_norm * zone_access_cost
                + config.slow_mover_access_weight * (1 - demand_norm) * (1 - zone_access_cost)
                + config.capacity_pressure_weight * capacity_pressure
                + config.opportunity_reward_weight * (1 - opportunity_norm)
                + config.scenario_reward_weight * (1 - scenario_norm)
            )
            rows.append({
                "sku_id": sku[Skus.SKU_ID],
                "target_zone_id": zone[Zones.ZONE_ID],
                "target_zone_slot": zone["target_zone_slot"],
                "candidate_action": sku["candidate_action"],
                "opportunity_score": round(float(sku["opportunity_score"]), 2),
                "total_demand": round(float(sku["total_demand"]), 2),
                "rotation_class": sku[Skus.ROTATION_CLASS],
                "zone_priority_level": int(zone[Zones.PRIORITY_LEVEL]),
                "zone_distance_to_dispatch": round(float(zone[Zones.DISTANCE_TO_DISPATCH]), 2),
                "zone_capacity_pressure": round(capacity_pressure, 4),
                "scenario_weighted_score": round(float(sku["scenario_weighted_score"]), 2),
                "assignment_cost": round(float(cost), 6),
                "assumption_state": config.assumption_state,
                "optimization_caveat": OPTIMIZATION_CAVEAT,
            })
    return pd.DataFrame(rows).sort_values(
        ["sku_id", "assignment_cost", "target_zone_id", "target_zone_slot"]
    ).reset_index(drop=True)


def solve_assignment(
    cost_matrix: pd.DataFrame,
    config: AssignmentConfig | None = None,
    force_fallback: bool = False,
) -> pd.DataFrame:
    """Assign each selected SKU to one target zone slot."""
    config = config or AssignmentConfig()
    _validate_cost_matrix(cost_matrix)
    matrix, sku_ids, slots = _pivot_costs(cost_matrix)
    method = "greedy_fallback"
    if not force_fallback:
        try:
            from scipy.optimize import linear_sum_assignment

            row_indexes, col_indexes = linear_sum_assignment(matrix)
            method = "scipy_linear_sum_assignment"
        except ImportError:
            row_indexes, col_indexes = _greedy_assignment(matrix)
    else:
        row_indexes, col_indexes = _greedy_assignment(matrix)

    lookup = cost_matrix.set_index(["sku_id", "target_zone_slot"])
    rows: list[dict[str, object]] = []
    assignment_pairs = zip(row_indexes, col_indexes)
    for assignment_rank, (row_index, col_index) in enumerate(assignment_pairs, start=1):
        sku_id = sku_ids[int(row_index)]
        slot = slots[int(col_index)]
        row = lookup.loc[(sku_id, slot)].to_dict()
        row["sku_id"] = sku_id
        row["target_zone_slot"] = slot
        row["assignment_rank"] = assignment_rank
        row["solver_method"] = method
        row["config_snapshot"] = _config_snapshot(config)
        rows.append(row)

    assignments = pd.DataFrame(rows)
    return assignments[
        [
            "assignment_rank",
            "sku_id",
            "target_zone_id",
            "target_zone_slot",
            "candidate_action",
            "opportunity_score",
            "total_demand",
            "rotation_class",
            "zone_priority_level",
            "zone_distance_to_dispatch",
            "zone_capacity_pressure",
            "scenario_weighted_score",
            "assignment_cost",
            "solver_method",
            "assumption_state",
            "optimization_caveat",
            "config_snapshot",
        ]
    ].sort_values(["assignment_rank", "sku_id"]).reset_index(drop=True)


def build_optimization_summary(
    assignments: pd.DataFrame,
    cost_matrix: pd.DataFrame,
    config: AssignmentConfig | None = None,
) -> pd.DataFrame:
    """Summarize Phase 5 optimization prototype outputs."""
    config = config or AssignmentConfig()
    rows = [
        ("selected_skus", int(assignments["sku_id"].nunique())),
        ("assigned_rows", len(assignments)),
        ("candidate_zone_slots", int(cost_matrix["target_zone_slot"].nunique())),
        ("target_zones_used", int(assignments["target_zone_id"].nunique())),
        ("average_assignment_cost", round(float(assignments["assignment_cost"].mean()), 6)),
        ("total_assignment_cost", round(float(assignments["assignment_cost"].sum()), 6)),
        ("solver_method", _mode_or_empty(assignments["solver_method"])),
    ]
    summary = pd.DataFrame({"metric": [row[0] for row in rows], "value": [row[1] for row in rows]})
    summary["assumption_state"] = config.assumption_state
    summary["optimization_caveat"] = OPTIMIZATION_CAVEAT
    summary["config_snapshot"] = _config_snapshot(config)
    return summary


def build_optimization_outputs(
    inputs: dict[str, pd.DataFrame],
    config: AssignmentConfig | None = None,
    force_fallback: bool = False,
) -> dict[str, pd.DataFrame]:
    """Build all Phase 5 optimization output tables."""
    config = config or AssignmentConfig()
    candidates = select_candidate_skus(inputs["priority_queue"], config)
    cost_matrix = build_assignment_cost_matrix(
        candidates=candidates,
        skus=inputs["skus"],
        zones=inputs["zones"],
        slotting_diagnostics=inputs["slotting_diagnostics"],
        zone_diagnostics=inputs["zone_diagnostics"],
        scenario_comparison=inputs.get("scenario_comparison"),
        config=config,
    )
    assignments = solve_assignment(cost_matrix, config=config, force_fallback=force_fallback)
    summary = build_optimization_summary(assignments, cost_matrix, config)
    return {"assignments": assignments, "summary": summary, "cost_matrix": cost_matrix}


def save_optimization_outputs(
    optimization_outputs: dict[str, pd.DataFrame],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Save Phase 5 optimization prototype outputs as CSV files."""
    output_dir = output_dir or DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_names = {
        "assignments": "optimization_assignments.csv",
        "summary": "optimization_summary.csv",
        "cost_matrix": "optimization_cost_matrix.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in output_names.items():
        path = output_dir / filename
        optimization_outputs[key].to_csv(path, index=False)
        paths[key] = path
    return paths


def _build_sku_context(
    candidates: pd.DataFrame,
    skus: pd.DataFrame,
    slotting_diagnostics: pd.DataFrame,
    scenario_comparison: pd.DataFrame | None,
) -> pd.DataFrame:
    scenario_scores = _scenario_scores(scenario_comparison)
    context = candidates.rename(columns={"entity_id": Skus.SKU_ID}).merge(
        skus[[Skus.SKU_ID, Skus.ROTATION_CLASS, Skus.AVG_DAILY_DEMAND]],
        on=Skus.SKU_ID,
        how="left",
    )
    diagnostic_columns = [
        Skus.SKU_ID,
        "total_demand",
        "diagnostic_count",
        "min_priority_level",
        "distance_to_dispatch",
    ]
    context = context.merge(
        slotting_diagnostics[diagnostic_columns], on=Skus.SKU_ID, how="left"
    ).merge(scenario_scores, on=Skus.SKU_ID, how="left")
    context["total_demand"] = pd.to_numeric(context["total_demand"], errors="coerce").fillna(
        context[Skus.AVG_DAILY_DEMAND]
    )
    context["scenario_weighted_score"] = pd.to_numeric(
        context["scenario_weighted_score"], errors="coerce"
    ).fillna(context["opportunity_score"])
    return context


def _scenario_scores(scenario_comparison: pd.DataFrame | None) -> pd.DataFrame:
    if scenario_comparison is None or scenario_comparison.empty:
        return pd.DataFrame(columns=[Skus.SKU_ID, "scenario_weighted_score"])
    required = {"entity_type", "entity_id", "scenario_weighted_score"}
    if not required.issubset(scenario_comparison.columns):
        return pd.DataFrame(columns=[Skus.SKU_ID, "scenario_weighted_score"])
    frame = scenario_comparison[scenario_comparison["entity_type"].eq("sku")].copy()
    frame["scenario_weighted_score"] = pd.to_numeric(
        frame["scenario_weighted_score"], errors="coerce"
    ).fillna(0.0)
    return frame.groupby("entity_id", as_index=False)["scenario_weighted_score"].max().rename(
        columns={"entity_id": Skus.SKU_ID}
    )


def _build_zone_slots(
    zones: pd.DataFrame,
    zone_diagnostics: pd.DataFrame,
    config: AssignmentConfig,
) -> pd.DataFrame:
    zone_context = zones.merge(
        zone_diagnostics[[Zones.ZONE_ID, "avg_utilization_pct", "overutilized_zone_flag"]],
        on=Zones.ZONE_ID,
        how="left",
    )
    zone_context["avg_utilization_pct"] = pd.to_numeric(
        zone_context["avg_utilization_pct"], errors="coerce"
    ).fillna(0.0)
    zone_context["capacity_pressure"] = (zone_context["avg_utilization_pct"] / 100).clip(0, 1)
    zone_context["capacity_slots"] = np.ceil(
        (1 - zone_context["capacity_pressure"]).clip(lower=0.05) * config.max_slots_per_zone
    ).astype(int)
    rows: list[dict[str, object]] = []
    for _, zone in zone_context.iterrows():
        for slot_number in range(1, int(zone["capacity_slots"]) + 1):
            row = zone.to_dict()
            row["target_zone_slot"] = f"{zone[Zones.ZONE_ID]}-{slot_number}"
            rows.append(row)
    return pd.DataFrame(rows)


def _pivot_costs(cost_matrix: pd.DataFrame) -> tuple[np.ndarray, list[str], list[str]]:
    pivot = cost_matrix.pivot(index="sku_id", columns="target_zone_slot", values="assignment_cost")
    pivot = pivot.sort_index(axis=0).sort_index(axis=1)
    values = pivot.to_numpy(dtype=float)
    if values.shape[1] < values.shape[0]:
        raise ValueError("Not enough target zone slots to assign each selected SKU.")
    return values, list(pivot.index), list(pivot.columns)


def _greedy_assignment(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    assignments: list[tuple[int, int]] = []
    used_rows: set[int] = set()
    used_cols: set[int] = set()
    candidates: list[tuple[float, int, int]] = []
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            candidates.append((float(matrix[row_index, col_index]), row_index, col_index))
    for _, row_index, col_index in sorted(candidates):
        if row_index in used_rows or col_index in used_cols:
            continue
        assignments.append((row_index, col_index))
        used_rows.add(row_index)
        used_cols.add(col_index)
        if len(assignments) == matrix.shape[0]:
            break
    rows = np.array([row for row, _ in assignments])
    cols = np.array([col for _, col in assignments])
    return rows, cols


def _validate_cost_matrix(cost_matrix: pd.DataFrame) -> None:
    required = {"sku_id", "target_zone_slot", "target_zone_id", "assignment_cost"}
    missing = sorted(required.difference(cost_matrix.columns))
    if missing:
        raise ValueError("Missing required cost matrix column(s): " + ", ".join(missing))


def _normalise_value(value: object, series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)
    minimum = float(numeric.min())
    maximum = float(numeric.max())
    if maximum == minimum:
        return 0.0
    return (float(value) - minimum) / (maximum - minimum)


def _ratio_to_max(value: object, series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)
    maximum = float(numeric.max())
    if maximum <= 0:
        return 0.0
    return min(max(float(value) / maximum, 0.0), 1.0)


def _mode_or_empty(values: pd.Series) -> str:
    mode = values.mode()
    if mode.empty:
        return ""
    return str(mode.iloc[0])


def _config_snapshot(config: AssignmentConfig) -> str:
    return "; ".join(f"{key}={value}" for key, value in asdict(config).items())
