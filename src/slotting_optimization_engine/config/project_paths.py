"""
project_paths — Central path resolution for data, scripts, and output directories.

Why a central paths module:
    - Prevents scattered hard-coded paths and the "working directory surprises"
      that plague data projects.
    - All modules reference PROJ_ROOT and derive their paths from it.
    - Environment variables can override defaults (useful in CI or containers).

Design decision:
    Uses pathlib.Path throughout instead of os.path for consistent,
    cross-platform path handling. No lazy-evaluation tricks — resolve eagerly
    so import order doesn't matter.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root detection
# ---------------------------------------------------------------------------
# Strategy: try env var first (lets CI or containerised runs override),
# then walk up from this file's location to find the project directory.
# The project root is defined as the directory containing pyproject.toml.
# ---------------------------------------------------------------------------

_env_root = os.getenv("PROJECT_ROOT")
if _env_root:
    PROJ_ROOT = Path(_env_root).resolve(strict=True)
else:
    # This file lives at src/slotting_optimization_engine/config/project_paths.py
    # Walking up 4 levels reaches the project root.
    PROJ_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ---------------------------------------------------------------------------
# Derived paths
# ---------------------------------------------------------------------------
# Each data subdirectory has its own path constant. Keeping them explicit
# rather than computing on every call makes it easy to add overrides per
# environment later.
# ---------------------------------------------------------------------------

DATA_DIR = PROJ_ROOT / "data"
DATA_RAW_DIR = Path(os.getenv("DATA_RAW_DIR", str(DATA_DIR / "raw")))
DATA_PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", str(DATA_DIR / "processed")))
DATA_SYNTHETIC_DIR = Path(os.getenv("DATA_SYNTHETIC_DIR", str(DATA_DIR / "synthetic")))

SRC_DIR = PROJ_ROOT / "src"
SCRIPTS_DIR = PROJ_ROOT / "scripts"
TESTS_DIR = PROJ_ROOT / "tests"
NOTEBOOKS_DIR = PROJ_ROOT / "notebooks"

# ---------------------------------------------------------------------------
# Ensures that essential data directories exist at import time.
# This is safe because we're only creating tracked placeholders, not
# generated/cached files. If the dirs can't be created, we want to fail fast.
# ---------------------------------------------------------------------------

ESSENTIAL_DIRS = [
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_SYNTHETIC_DIR,
]

for _d in ESSENTIAL_DIRS:
    _d.mkdir(parents=True, exist_ok=True)
