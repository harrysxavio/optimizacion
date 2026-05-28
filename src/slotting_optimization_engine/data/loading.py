"""
Data loading from CSV files into pandas DataFrames.

All paths are resolved through ``config.project_paths`` so that file
locations are centralised and overridable via environment variables.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from slotting_optimization_engine.config.project_paths import DATA_SYNTHETIC_DIR
from slotting_optimization_engine.data.validation import validate_dataset
from slotting_optimization_engine.domain.constants import DATASET_FILES, Orders


def load_dataset(
    entity: str,
    directory: Path | None = None,
    validate: bool = True,
    **fks: pd.DataFrame,
) -> pd.DataFrame:
    """Load a single dataset from CSV and optionally validate it.

    Parameters
    ----------
    entity : str
        One of ``"skus"``, ``"zones"``, ``"locations"``, ``"inventory"``,
        ``"orders"``, ``"order_lines"``.
    directory : Path or None
        Directory containing the CSV file. Defaults to ``DATA_SYNTHETIC_DIR``.
    validate : bool
        If True, run validation after loading and raise on errors.
    **fks : pd.DataFrame
        Foreign-key DataFrames forwarded to the validation function.

    Returns
    -------
    pd.DataFrame
        The loaded dataset.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If validation is enabled and errors are found.
    """
    directory = directory or DATA_SYNTHETIC_DIR
    filename = DATASET_FILES.get(entity)
    if filename is None:
        msg = f"Unknown entity '{entity}'. Valid: {list(DATASET_FILES)}"
        raise ValueError(msg)

    filepath = directory / filename
    if not filepath.is_file():
        raise FileNotFoundError(
            f"Dataset file not found: {filepath}\n"
            f"Run ``python scripts/generate_sample_data.py`` first."
        )

    # Parse order_date as datetime when loading orders
    parse_dates = [Orders.ORDER_DATE] if entity == "orders" else None
    df = pd.read_csv(filepath, parse_dates=parse_dates)

    if validate:
        errors = validate_dataset(entity, df, **fks)
        if errors:
            raise ValueError(
                f"Validation failed for '{entity}' ({len(errors)} error(s)):\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

    return df


def load_all_datasets(
    directory: Path | None = None,
    validate: bool = True,
) -> dict[str, pd.DataFrame]:
    """Load all six synthetic datasets.

    Returns a dict mapping entity names to DataFrames. Datasets are loaded
    in dependency order so FK validation can reference already-loaded tables.
    """
    directory = directory or DATA_SYNTHETIC_DIR
    datasets: dict[str, pd.DataFrame] = {}

    # Order matters: parents before children for FK validation
    load_order = ["skus", "zones", "locations", "inventory",
                   "orders", "order_lines"]

    for entity in load_order:
        # Build FK params from already-loaded datasets
        fk_params: dict = {}
        if entity == "locations":
            fk_params["zones_df"] = datasets.get("zones")
        elif entity == "inventory":
            fk_params["skus_df"] = datasets.get("skus")
            fk_params["locs_df"] = datasets.get("locations")
        elif entity == "order_lines":
            fk_params["orders_df"] = datasets.get("orders")
            fk_params["skus_df"] = datasets.get("skus")

        datasets[entity] = load_dataset(
            entity, directory=directory, validate=validate, **fk_params,
        )

    return datasets
