#!/usr/bin/env python3
"""
Load synthetic data from ``data/synthetic/`` and run all validation checks.

Usage::

    python scripts/run_data_validation.py

On failure, prints a detailed validation report and exits with code 1.
"""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from slotting_optimization_engine.data.loading import load_all_datasets
from slotting_optimization_engine.data.validation import (
    format_validation_report,
    validate_all_datasets,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Loading datasets from data/synthetic/ ...")

    try:
        datasets = load_all_datasets(validate=False)
    except FileNotFoundError as exc:
        logger.error("Dataset file not found: %s", exc)
        logger.error("Run ``python scripts/generate_sample_data.py`` first.")
        sys.exit(1)

    logger.info("Loaded %d datasets. Running validation ...", len(datasets))

    results = validate_all_datasets(datasets)
    report = format_validation_report(results)

    print()
    print(report)
    print()

    # Check for failures
    failures = {e: errs for e, errs in results.items() if errs}
    if failures:
        logger.error("Validation FAILED for %d dataset(s)", len(failures))
        sys.exit(1)

    logger.info("All datasets passed validation.")


if __name__ == "__main__":
    main()
