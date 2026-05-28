#!/usr/bin/env python3
"""Run Phase 2 descriptive diagnostics and save outputs to data/processed."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from slotting_optimization_engine.config.project_paths import DATA_PROCESSED_DIR
from slotting_optimization_engine.data.loading import load_all_datasets
from slotting_optimization_engine.diagnostics.rules import build_all_diagnostics, save_diagnostics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_processed_inputs(
    processed_dir: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load Phase 1 processed outputs required by diagnostics."""
    processed_dir = processed_dir or DATA_PROCESSED_DIR
    required = {
        "slotting features": processed_dir / "slotting_features.parquet",
        "location utilization": processed_dir / "location_utilization.csv",
        "zone utilization": processed_dir / "zone_utilization.csv",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing Phase 1 processed output(s): "
            + ", ".join(missing)
            + ". Run `python scripts/build_features.py` first."
        )

    return (
        pd.read_parquet(required["slotting features"]),
        pd.read_csv(required["location utilization"]),
        pd.read_csv(required["zone utilization"]),
    )


def main() -> None:
    logger.info("Step 1: Loading Phase 1 processed outputs ...")
    sku_features, location_utilization, zone_utilization = load_processed_inputs()
    logger.info("  Loaded slotting features: %d rows", len(sku_features))
    logger.info("  Loaded location utilization: %d rows", len(location_utilization))
    logger.info("  Loaded zone utilization: %d rows", len(zone_utilization))

    logger.info("Step 2: Loading validated synthetic source dimensions for placement context ...")
    datasets = load_all_datasets(validate=True)

    logger.info("Step 3: Building descriptive diagnostics ...")
    diagnostic_outputs = build_all_diagnostics(
        sku_features=sku_features,
        location_utilization=location_utilization,
        zone_utilization=zone_utilization,
        datasets=datasets,
    )
    for name, dataframe in diagnostic_outputs.items():
        logger.info("  Built %s: %d rows, %d cols", name, len(dataframe), len(dataframe.columns))

    logger.info("Step 4: Saving diagnostics to data/processed/ ...")
    paths = save_diagnostics(diagnostic_outputs)
    for name, path in paths.items():
        logger.info("  Saved %s -> %s", name, path)

    logger.info("Done - Phase 2 descriptive diagnostics complete.")


if __name__ == "__main__":
    main()
