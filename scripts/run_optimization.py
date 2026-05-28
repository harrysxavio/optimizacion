#!/usr/bin/env python3
"""Run Phase 5 controlled mathematical optimization prototype."""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from slotting_optimization_engine.optimization.assignment import (  # noqa: E402
    AssignmentConfig,
    build_optimization_outputs,
    load_optimization_inputs,
    save_optimization_outputs,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Step 1: Loading Phase 3/4 outputs and synthetic dimensions ...")
    inputs = load_optimization_inputs()
    for name, dataframe in inputs.items():
        logger.info("  Loaded %s: %d rows", name, len(dataframe))

    logger.info("Step 2: Building Phase 5 SKU-to-zone assignment prototype ...")
    config = AssignmentConfig()
    outputs = build_optimization_outputs(inputs, config=config)
    logger.info("  Built assignments: %d", len(outputs["assignments"]))
    logger.info("  Built cost matrix rows: %d", len(outputs["cost_matrix"]))
    logger.info("  Solver method: %s", outputs["assignments"]["solver_method"].iloc[0])

    logger.info("Step 3: Saving optimization outputs to data/processed/ ...")
    paths = save_optimization_outputs(outputs)
    for name, path in paths.items():
        logger.info("  Saved %s -> %s", name, path)

    logger.info("Done - Phase 5 controlled optimization prototype complete.")


if __name__ == "__main__":
    main()
