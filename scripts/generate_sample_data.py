#!/usr/bin/env python3
"""
Generate all six synthetic datasets and write them to ``data/synthetic/``.

Usage::

    python scripts/generate_sample_data.py

Optional overrides via environment variables:

- ``SKU_COUNT``: Number of SKUs to generate (default: 500).
- ``ZONE_COUNT``: Number of zones (default: 10).
- ``ORDER_COUNT``: Number of order headers (default: 2000).
- ``SEED``: Random seed for deterministic output (default: 42).

Output files in ``data/synthetic/``:

    - skus.csv
    - zones.csv
    - locations.csv
    - inventory.csv
    - orders.csv
    - order_lines.csv

Each file includes a comment header as the last row is a metadata row
containing generation parameters.
"""

from __future__ import annotations

import logging
import os
import sys

# Ensure the src package is on the path when running from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from slotting_optimization_engine.config.project_paths import DATA_SYNTHETIC_DIR
from slotting_optimization_engine.data.generator import (
    GenerationConfig,
    SyntheticDataGenerator,
)
from slotting_optimization_engine.domain.constants import DATASET_FILES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting synthetic data generation")

    # Read overrides from environment, falling back to defaults
    config = GenerationConfig(
        n_skus=int(os.getenv("SKU_COUNT", str(GenerationConfig.n_skus))),
        n_zones=int(os.getenv("ZONE_COUNT", str(GenerationConfig.n_zones))),
        n_orders=int(os.getenv("ORDER_COUNT", str(GenerationConfig.n_orders))),
        seed=int(os.getenv("SEED", str(GenerationConfig.seed))),
    )

    logger.info(
        "Config: %d SKUs, %d zones, %d orders, seed=%d",
        config.n_skus, config.n_zones, config.n_orders, config.seed,
    )

    # Generate
    generator = SyntheticDataGenerator(config)
    datasets = generator.generate_all()

    # Ensure output directory exists
    DATA_SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

    # Write CSV files
    for entity, filename in DATASET_FILES.items():
        filepath = DATA_SYNTHETIC_DIR / filename
        df = datasets[entity]
        df.to_csv(filepath, index=False)
        logger.info("  Wrote %s → %s (%d rows, %d cols)",
                     entity, filepath, len(df), len(df.columns))

    # Summary
    total_rows = sum(len(df) for df in datasets.values())
    logger.info("Done — %d total rows across %d datasets written to %s",
                 total_rows, len(datasets), DATA_SYNTHETIC_DIR)


if __name__ == "__main__":
    main()
