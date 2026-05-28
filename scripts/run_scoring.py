#!/usr/bin/env python3
"""Run Phase 3 scoring/prioritization and save outputs to data/processed."""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from slotting_optimization_engine.scoring.prioritization import (  # noqa: E402
    ScoringConfig,
    build_priority_queue,
    build_scoring_summary,
    build_slotting_opportunity_scores,
    load_diagnostic_inputs,
    save_scoring_outputs,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Step 1: Loading Phase 2 diagnostic outputs ...")
    diagnostics = load_diagnostic_inputs()
    for name, dataframe in diagnostics.items():
        logger.info("  Loaded %s diagnostics: %d rows", name, len(dataframe))

    logger.info("Step 2: Building Phase 3 prioritization scores ...")
    config = ScoringConfig()
    opportunity_scores = build_slotting_opportunity_scores(diagnostics, config)
    priority_queue = build_priority_queue(opportunity_scores, config)
    scoring_summary = build_scoring_summary(opportunity_scores, priority_queue, config)
    logger.info("  Built opportunity scores: %d rows", len(opportunity_scores))
    logger.info("  Built priority queue: %d rows", len(priority_queue))

    logger.info("Step 3: Saving scoring outputs to data/processed/ ...")
    paths = save_scoring_outputs({
        "opportunity_scores": opportunity_scores,
        "priority_queue": priority_queue,
        "summary": scoring_summary,
    })
    for name, path in paths.items():
        logger.info("  Saved %s -> %s", name, path)

    logger.info("Done - Phase 3 scoring/prioritization complete.")


if __name__ == "__main__":
    main()
