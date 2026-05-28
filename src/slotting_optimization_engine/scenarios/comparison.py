"""Phase 4 scenario/model comparison for transparent what-if evaluation.

The functions in this module compare alternative analytical lenses over Phase 3
scores. They do not solve an optimization model, choose target locations, or
produce executable movement plans.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

from slotting_optimization_engine.config.project_paths import DATA_PROCESSED_DIR
from slotting_optimization_engine.scoring.prioritization import BUSINESS_RULE_STATE

SCENARIO_NOTE = (
    "Analytical what-if comparison only; not mathematical optimization, not a solver "
    "output, and not an executable SKU movement plan."
)

PRIORITY_MULTIPLIERS = {
    "high": 1.25,
    "medium": 1.0,
    "low": 0.75,
}


@dataclass(frozen=True)
class ScenarioConfig:
    """Inferred comparison lens for ranking already-scored opportunities."""

    name: str
    description: str
    top_n: int = 50
    score_weight: float = 1.0
    priority_weight: float = 0.0
    action_weights: dict[str, float] = field(default_factory=dict)
    entity_type_weights: dict[str, float] = field(default_factory=dict)
    assumption_state: str = BUSINESS_RULE_STATE


def build_default_scenarios(top_n: int = 50) -> list[ScenarioConfig]:
    """Return the default Phase 4 analytical comparison lenses."""
    return [
        ScenarioConfig(
            name="baseline",
            description="Phase 3 score order without extra emphasis.",
            top_n=top_n,
        ),
        ScenarioConfig(
            name="demand_first",
            description="Emphasizes high-demand SKUs with distance or priority concerns.",
            top_n=top_n,
            action_weights={"review_high_demand_far_sku": 1.35},
            entity_type_weights={"sku": 1.05},
        ),
        ScenarioConfig(
            name="capacity_first",
            description="Emphasizes zones with capacity or premium-zone pressure.",
            top_n=top_n,
            action_weights={"review_zone_capacity_pressure": 1.4},
            entity_type_weights={"zone": 1.25},
        ),
        ScenarioConfig(
            name="balanced_review",
            description="Balances score, priority label, SKU issues, and zone pressure.",
            top_n=top_n,
            priority_weight=8.0,
            action_weights={
                "review_high_demand_far_sku": 1.1,
                "review_slow_mover_in_premium_zone": 1.1,
                "review_zone_capacity_pressure": 1.1,
            },
        ),
    ]


def load_scenario_inputs(processed_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Load Phase 3 outputs and optional Phase 2 diagnostics for scenario comparison."""
    processed_dir = processed_dir or DATA_PROCESSED_DIR
    required_files = {
        "opportunity_scores": processed_dir / "slotting_opportunity_scores.csv",
        "priority_queue": processed_dir / "priority_recommendation_queue.csv",
        "scoring_summary": processed_dir / "scoring_summary.csv",
    }
    missing = [str(path) for path in required_files.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing Phase 3 scoring output(s): "
            + ", ".join(missing)
            + ". Run `python scripts/run_scoring.py` first."
        )

    inputs = {name: pd.read_csv(path) for name, path in required_files.items()}
    diagnostic_summary_path = processed_dir / "diagnostic_summary.csv"
    if diagnostic_summary_path.is_file():
        inputs["diagnostic_summary"] = pd.read_csv(diagnostic_summary_path)
    return inputs


def build_scenario_comparison(
    opportunity_scores: pd.DataFrame,
    scenarios: list[ScenarioConfig] | None = None,
) -> pd.DataFrame:
    """Build one selected top-N comparison row per scenario and candidate item."""
    scenarios = scenarios or build_default_scenarios()
    scored = _validate_opportunity_scores(opportunity_scores)
    frames = [_rank_for_scenario(scored, scenario) for scenario in scenarios]
    return pd.concat(frames, ignore_index=True)


def build_scenario_action_mix(scenario_comparison: pd.DataFrame) -> pd.DataFrame:
    """Summarize selected candidate-action coverage per scenario."""
    if scenario_comparison.empty:
        return pd.DataFrame()

    grouped = scenario_comparison.groupby(["scenario", "candidate_action"], as_index=False).agg(
        selected_count=("entity_id", "count"),
        total_weighted_opportunity=("scenario_weighted_score", "sum"),
        average_opportunity_score=("opportunity_score", "mean"),
        high_priority_count=("priority", lambda values: int((values == "high").sum())),
    )
    totals = scenario_comparison.groupby("scenario")["entity_id"].count().rename("scenario_total")
    grouped = grouped.merge(totals, on="scenario", how="left")
    grouped["selected_share"] = (grouped["selected_count"] / grouped["scenario_total"]).round(4)
    grouped["total_weighted_opportunity"] = grouped["total_weighted_opportunity"].round(2)
    grouped["average_opportunity_score"] = grouped["average_opportunity_score"].round(2)
    grouped["assumption_state"] = BUSINESS_RULE_STATE
    grouped["scenario_note"] = SCENARIO_NOTE
    return grouped[
        [
            "scenario",
            "candidate_action",
            "selected_count",
            "selected_share",
            "high_priority_count",
            "average_opportunity_score",
            "total_weighted_opportunity",
            "assumption_state",
            "scenario_note",
        ]
    ].sort_values(["scenario", "selected_count", "candidate_action"], ascending=[True, False, True])


def build_scenario_summary(
    scenario_comparison: pd.DataFrame,
    scenarios: list[ScenarioConfig] | None = None,
) -> pd.DataFrame:
    """Build scenario-level comparable metrics."""
    scenarios = scenarios or build_default_scenarios()
    scenario_lookup = {scenario.name: scenario for scenario in scenarios}
    rows: list[dict[str, object]] = []
    for scenario_name, frame in scenario_comparison.groupby("scenario", sort=False):
        scenario = scenario_lookup.get(scenario_name)
        rows.append({
            "scenario": scenario_name,
            "description": scenario.description if scenario else "Custom scenario lens.",
            "selected_count": len(frame),
            "top_n": int(frame["scenario_top_n"].iloc[0]),
            "total_weighted_opportunity": round(float(frame["scenario_weighted_score"].sum()), 2),
            "average_opportunity_score": round(float(frame["opportunity_score"].mean()), 2),
            "average_scenario_score": round(float(frame["scenario_weighted_score"].mean()), 2),
            "high_priority_count": int((frame["priority"] == "high").sum()),
            "sku_selected_count": int((frame["entity_type"] == "sku").sum()),
            "zone_selected_count": int((frame["entity_type"] == "zone").sum()),
            "candidate_action_coverage": int(frame["candidate_action"].nunique()),
            "dominant_candidate_action": _mode_or_empty(frame["candidate_action"]),
            "assumption_state": BUSINESS_RULE_STATE,
            "scenario_note": SCENARIO_NOTE,
            "config_snapshot": _config_snapshot(scenario) if scenario else "custom scenario",
        })
    return pd.DataFrame(rows)


def save_scenario_outputs(
    scenario_outputs: dict[str, pd.DataFrame],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Save scenario comparison outputs as CSV files in ``data/processed``."""
    output_dir = output_dir or DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_names = {
        "comparison": "scenario_comparison.csv",
        "action_mix": "scenario_action_mix.csv",
        "summary": "scenario_summary.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in output_names.items():
        path = output_dir / filename
        scenario_outputs[key].to_csv(path, index=False)
        paths[key] = path
    return paths


def _rank_for_scenario(scores: pd.DataFrame, scenario: ScenarioConfig) -> pd.DataFrame:
    frame = scores.copy()
    action_multiplier = frame["candidate_action"].map(scenario.action_weights).fillna(1.0)
    entity_multiplier = frame["entity_type"].map(scenario.entity_type_weights).fillna(1.0)
    priority_bonus = (
        frame["priority"].map(PRIORITY_MULTIPLIERS).fillna(1.0) * scenario.priority_weight
    )
    frame["scenario_weighted_score"] = (
        frame["opportunity_score"] * scenario.score_weight * action_multiplier * entity_multiplier
        + priority_bonus
    ).round(2)
    frame = frame.sort_values(
        [
            "scenario_weighted_score",
            "opportunity_score",
            "entity_type",
            "entity_id",
            "candidate_action",
        ],
        ascending=[False, False, True, True, True],
    ).head(scenario.top_n)
    frame = frame.reset_index(drop=True)
    frame.insert(0, "scenario_rank", range(1, len(frame) + 1))
    frame.insert(0, "scenario", scenario.name)
    frame["scenario_description"] = scenario.description
    frame["scenario_top_n"] = scenario.top_n
    frame["scenario_assumption_state"] = scenario.assumption_state
    frame["scenario_note"] = SCENARIO_NOTE
    return frame[
        [
            "scenario",
            "scenario_rank",
            "scenario_weighted_score",
            "scenario_description",
            "scenario_top_n",
            "entity_type",
            "entity_id",
            "candidate_action",
            "priority",
            "opportunity_score",
            "rank",
            "reason",
            "business_rule_state",
            "scenario_assumption_state",
            "scenario_note",
        ]
    ]


def _validate_opportunity_scores(opportunity_scores: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        "entity_type",
        "entity_id",
        "candidate_action",
        "opportunity_score",
        "priority",
        "rank",
        "reason",
        "business_rule_state",
    }
    missing = sorted(required_columns.difference(opportunity_scores.columns))
    if missing:
        raise ValueError("Missing required opportunity score column(s): " + ", ".join(missing))
    frame = opportunity_scores.copy()
    frame["opportunity_score"] = pd.to_numeric(
        frame["opportunity_score"], errors="coerce"
    ).fillna(0.0)
    return frame


def _mode_or_empty(values: pd.Series) -> str:
    mode = values.mode()
    if mode.empty:
        return ""
    return str(mode.iloc[0])


def _config_snapshot(scenario: ScenarioConfig | None) -> str:
    if scenario is None:
        return ""
    values = asdict(scenario)
    return "; ".join(f"{key}={value}" for key, value in values.items())
