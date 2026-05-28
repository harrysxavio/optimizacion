#!/usr/bin/env python3
"""Run Phase 4 scenario/model comparison and save outputs to data/processed."""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from slotting_optimization_engine.scenarios.comparison import (  # noqa: E402
    build_default_scenarios,
    build_scenario_action_mix,
    build_scenario_comparison,
    build_scenario_summary,
    load_scenario_inputs,
    save_scenario_outputs,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Step 1: Loading Phase 3 scoring outputs ...")
    inputs = load_scenario_inputs()
    for name, dataframe in inputs.items():
        logger.info("  Loaded %s: %d rows", name, len(dataframe))

    logger.info("Step 2: Building Phase 4 analytical scenario comparisons ...")
    scenarios = build_default_scenarios()
    scenario_comparison = build_scenario_comparison(inputs["opportunity_scores"], scenarios)
    scenario_action_mix = build_scenario_action_mix(scenario_comparison)
    scenario_summary = build_scenario_summary(scenario_comparison, scenarios)
    logger.info("  Compared scenarios: %d", len(scenarios))
    logger.info("  Built selected comparison rows: %d", len(scenario_comparison))

    logger.info("Step 3: Saving scenario outputs to data/processed/ ...")
    paths = save_scenario_outputs({
        "comparison": scenario_comparison,
        "action_mix": scenario_action_mix,
        "summary": scenario_summary,
    })
    for name, path in paths.items():
        logger.info("  Saved %s -> %s", name, path)

    logger.info("Done - Phase 4 scenario/model comparison complete.")


if __name__ == "__main__":
    main()
