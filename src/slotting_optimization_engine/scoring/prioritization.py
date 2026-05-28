"""Phase 3 transparent scoring for slotting opportunity prioritization.

This module ranks diagnostic findings for review. It is not mathematical
optimization, does not solve a move plan, and does not recommend optimal target
locations. All weights are inferred from Phase 2 diagnostics and remain pending
business confirmation.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from slotting_optimization_engine.config.project_paths import DATA_PROCESSED_DIR
from slotting_optimization_engine.domain.constants import Features, Skus, Zones

BUSINESS_RULE_STATE = "inferred / pending confirmation"
SCORING_NOTE = (
    "Prioritization score only; not mathematical optimization and not an optimal "
    "move recommendation. Weights are inferred/pending confirmation."
)


@dataclass(frozen=True)
class ScoringConfig:
    """Transparent inferred weights for prioritizing diagnostic review work."""

    high_demand_weight: float = 0.35
    distance_weight: float = 0.25
    poor_priority_weight: float = 0.15
    slow_mover_weight: float = 0.30
    premium_zone_weight: float = 0.25
    zone_capacity_weight: float = 0.40
    diagnostic_weight: float = 0.25
    high_priority_min_score: float = 70.0
    medium_priority_min_score: float = 40.0
    queue_min_score: float = 1.0
    weight_state: str = BUSINESS_RULE_STATE


def load_diagnostic_inputs(
    processed_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Load Phase 2 diagnostic CSV outputs required by scoring."""
    processed_dir = processed_dir or DATA_PROCESSED_DIR
    required_files = {
        "slotting": processed_dir / "slotting_diagnostics.csv",
        "location": processed_dir / "location_diagnostics.csv",
        "zone": processed_dir / "zone_diagnostics.csv",
        "category": processed_dir / "category_diagnostics.csv",
    }
    missing = [str(path) for path in required_files.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing Phase 2 diagnostic output(s): "
            + ", ".join(missing)
            + ". Run `python scripts/run_diagnostics.py` first."
        )

    diagnostics = {
        name: pd.read_csv(path)
        for name, path in required_files.items()
    }
    summary_path = processed_dir / "diagnostic_summary.csv"
    if summary_path.is_file():
        diagnostics["summary"] = pd.read_csv(summary_path)
    return diagnostics


def build_slotting_opportunity_scores(
    diagnostics: dict[str, pd.DataFrame],
    config: ScoringConfig | None = None,
) -> pd.DataFrame:
    """Build action-level opportunity scores from Phase 2 diagnostics."""
    config = config or ScoringConfig()
    score_frames = [
        _score_high_demand_far_skus(diagnostics["slotting"], config),
        _score_slow_movers_in_premium_zones(diagnostics["slotting"], config),
        _score_zone_capacity_pressure(diagnostics["zone"], config),
    ]
    scores = pd.concat(score_frames, ignore_index=True)
    scores["opportunity_score"] = scores["opportunity_score"].clip(lower=0, upper=100).round(2)
    scores["priority"] = scores["opportunity_score"].map(lambda score: _priority(score, config))
    scores["rank"] = scores["opportunity_score"].rank(method="first", ascending=False).astype(int)
    scores["business_rule_state"] = config.weight_state
    scores["scoring_note"] = SCORING_NOTE
    return scores.sort_values(
        ["opportunity_score", "entity_type", "entity_id", "candidate_action"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)


def build_priority_queue(
    opportunity_scores: pd.DataFrame,
    config: ScoringConfig | None = None,
) -> pd.DataFrame:
    """Return a sorted review queue for non-zero scoring opportunities."""
    config = config or ScoringConfig()
    queue = opportunity_scores[
        opportunity_scores["opportunity_score"] >= config.queue_min_score
    ].copy()
    queue = queue.sort_values(
        ["opportunity_score", "priority", "entity_type", "entity_id"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)
    queue["queue_position"] = range(1, len(queue) + 1)
    return queue[[
        "queue_position",
        "priority",
        "opportunity_score",
        "entity_type",
        "entity_id",
        "candidate_action",
        "reason",
        "business_rule_state",
        "scoring_note",
    ]]


def build_scoring_summary(
    opportunity_scores: pd.DataFrame,
    priority_queue: pd.DataFrame,
    config: ScoringConfig | None = None,
) -> pd.DataFrame:
    """Summarize Phase 3 scoring outputs and inferred scoring configuration."""
    config = config or ScoringConfig()
    rows = [
        ("total_scored_opportunities", len(opportunity_scores)),
        ("queued_opportunities", len(priority_queue)),
        ("high_priority_opportunities", int((opportunity_scores["priority"] == "high").sum())),
        ("medium_priority_opportunities", int((opportunity_scores["priority"] == "medium").sum())),
        ("low_priority_opportunities", int((opportunity_scores["priority"] == "low").sum())),
        ("max_opportunity_score", float(opportunity_scores["opportunity_score"].max())),
        ("mean_opportunity_score", float(opportunity_scores["opportunity_score"].mean())),
    ]
    summary = pd.DataFrame({
        "metric": [row[0] for row in rows],
        "value": [row[1] for row in rows],
    })
    summary["business_rule_state"] = config.weight_state
    summary["scoring_note"] = SCORING_NOTE
    summary["config_snapshot"] = _config_snapshot(config)
    return summary


def save_scoring_outputs(
    scoring_outputs: dict[str, pd.DataFrame],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Save scoring outputs as CSV files in ``data/processed``."""
    output_dir = output_dir or DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_names = {
        "opportunity_scores": "slotting_opportunity_scores.csv",
        "priority_queue": "priority_recommendation_queue.csv",
        "summary": "scoring_summary.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in output_names.items():
        path = output_dir / filename
        scoring_outputs[key].to_csv(path, index=False)
        paths[key] = path
    return paths


def _score_high_demand_far_skus(slotting: pd.DataFrame, config: ScoringConfig) -> pd.DataFrame:
    frame = slotting.copy()
    demand_component = _ratio_score(frame[Features.TOTAL_DEMAND], frame["high_demand_threshold"])
    distance_component = _ratio_score(
        frame[Zones.DISTANCE_TO_DISPATCH], frame["long_distance_threshold"]
    )
    priority_component = _ratio_score(frame[Zones.PRIORITY_LEVEL], 4.0)
    diagnostic_component = frame["high_demand_poor_placement_flag"].astype(float)
    score = 100 * (
        config.high_demand_weight * demand_component
        + config.distance_weight * distance_component
        + config.poor_priority_weight * priority_component
        + config.diagnostic_weight * diagnostic_component
    )
    return pd.DataFrame({
        "entity_type": "sku",
        "entity_id": frame[Skus.SKU_ID],
        "candidate_action": "review_high_demand_far_sku",
        "opportunity_score": score,
        "reason": _reason(
            "High-demand SKU with distance/zone-priority placement concern",
            frame["high_demand_poor_placement_flag"],
        ),
    })


def _score_slow_movers_in_premium_zones(
    slotting: pd.DataFrame,
    config: ScoringConfig,
) -> pd.DataFrame:
    frame = slotting.copy()
    slow_component = (
        frame["is_low_demand_or_rotation"].astype(float)
        + frame["low_demand_premium_zone_flag"].astype(float)
    ) / 2
    premium_component = 1 - _ratio_score(frame["min_priority_level"], 4.0)
    diagnostic_component = frame["diagnostic_count"].fillna(0).clip(upper=2) / 2
    score = 100 * (
        config.slow_mover_weight * slow_component
        + config.premium_zone_weight * premium_component
        + config.diagnostic_weight * diagnostic_component
    )
    return pd.DataFrame({
        "entity_type": "sku",
        "entity_id": frame[Skus.SKU_ID],
        "candidate_action": "review_slow_mover_in_premium_zone",
        "opportunity_score": score,
        "reason": _reason(
            "Slow/low-demand SKU may occupy premium access capacity",
            frame["low_demand_premium_zone_flag"],
        ),
    })


def _score_zone_capacity_pressure(zone: pd.DataFrame, config: ScoringConfig) -> pd.DataFrame:
    frame = zone.copy()
    utilization_component = _ratio_score(frame["avg_utilization_pct"], 100.0)
    capacity_component = frame["overutilized_zone_flag"].astype(float)
    diagnostic_component = (
        frame[["overutilized_zone_flag", "premium_zone_slow_mover_flag"]]
        .astype(float)
        .sum(axis=1)
        .clip(upper=2)
        / 2
    )
    score = 100 * (
        config.zone_capacity_weight * capacity_component
        + config.distance_weight * utilization_component
        + config.diagnostic_weight * diagnostic_component
    )
    return pd.DataFrame({
        "entity_type": "zone",
        "entity_id": frame[Zones.ZONE_ID],
        "candidate_action": "review_zone_capacity_pressure",
        "opportunity_score": score,
        "reason": _reason(
            "Zone utilization or premium-zone slow-mover pressure should be reviewed",
            frame["overutilized_zone_flag"] | frame["premium_zone_slow_mover_flag"],
        ),
    })


def _ratio_score(numerator: pd.Series, denominator: pd.Series | float) -> pd.Series:
    values = pd.to_numeric(numerator, errors="coerce").fillna(0).astype(float)
    if isinstance(denominator, pd.Series):
        base = pd.to_numeric(denominator, errors="coerce").replace(0, pd.NA).astype("Float64")
    else:
        base = float(denominator) if denominator else pd.NA
    ratio = (values / base).fillna(0).astype(float)
    return ratio.clip(lower=0, upper=1)


def _priority(score: float, config: ScoringConfig) -> str:
    if score >= config.high_priority_min_score:
        return "high"
    if score >= config.medium_priority_min_score:
        return "medium"
    return "low"


def _reason(prefix: str, flag: pd.Series) -> pd.Series:
    suffix = flag.map({True: "Phase 2 diagnostic flag is active", False: "supporting signal only"})
    return prefix + "; " + suffix


def _config_snapshot(config: ScoringConfig) -> str:
    items = asdict(config).items()
    return "; ".join(
        f"{_snake_to_label(key)}={value} ({BUSINESS_RULE_STATE})"
        for key, value in items
        if key != "weight_state"
    )


def _snake_to_label(value: str) -> str:
    return re.sub(r"_+", " ", value)
