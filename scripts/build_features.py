#!/usr/bin/env python3
"""
Load validated synthetic data, build analytical features, and save to
``data/processed/``.

Usage::

    python scripts/build_features.py

Output files:

    - ``data/processed/slotting_features.parquet``
    - ``data/processed/location_utilization.csv``
    - ``data/processed/zone_utilization.csv``
"""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from slotting_optimization_engine.data.loading import load_all_datasets
from slotting_optimization_engine.features.builder import (
    build_all_features,
    save_features,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Step 1: Loading datasets ...")
    datasets = load_all_datasets(validate=True)

    for name, df in datasets.items():
        logger.info("  Loaded %s: %d rows, %d cols", name, len(df), len(df.columns))

    logger.info("Step 2: Building features ...")
    feature_outputs = build_all_features(datasets)

    for name, df in feature_outputs.items():
        logger.info("  Built %s: %d rows, %d cols", name, len(df), len(df.columns))

    logger.info("Step 3: Saving to data/processed/ ...")
    paths = save_features(feature_outputs)

    for name, path in paths.items():
        logger.info("  Saved %s → %s", name, path)

    logger.info("Done — feature pipeline complete.")


if __name__ == "__main__":
    main()
