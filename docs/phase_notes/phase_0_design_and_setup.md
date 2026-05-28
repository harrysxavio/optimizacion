# Phase 0 — Design, Architecture, and Setup

**Phase:** 0  
**Status:** Complete  
**Implementer:** AI-assisted (SDD Apply executor)  
**Date:** 2026-05-27

---

## 1. What was implemented

The complete Phase 0 project skeleton:

- Base directory structure as specified in `docs/master_plan.md`.
- Python package `slotting_optimization_engine` with all subpackages (some marked as future stubs).
- Central path configuration module.
- Base project configuration (`pyproject.toml`, `.gitignore`, `.env.example`).
- `README.md` with project overview, setup commands, and documentation map.
- Comprehensive documentation: architecture, data contract, roadmap.
- Phase 0 phase note and terminal log.
- Unit test verifying package structure.
- Updated `docs/master_plan.md` with Phase 0 completion status.

## 2. Files created

| File | Purpose |
|---|---|
| `README.md` | Project overview, setup, docs map |
| `pyproject.toml` | Python package definition, dependencies, tool config |
| `.gitignore` | Ignored files (Python, venv, data, IDE, OS) |
| `.env.example` | Environment variable template |
| `src/slotting_optimization_engine/__init__.py` | Package init with version and layout docstring |
| `src/slotting_optimization_engine/config/__init__.py` | Config package init |
| `src/slotting_optimization_engine/config/project_paths.py` | Central path resolution |
| `src/slotting_optimization_engine/data/__init__.py` | Data package (Phase 1 stub) |
| `src/slotting_optimization_engine/domain/__init__.py` | Domain package (Phase 1 stub) |
| `src/slotting_optimization_engine/features/__init__.py` | Features package (Phase 1 stub) |
| `src/slotting_optimization_engine/diagnostics/__init__.py` | Diagnostics package (Phase 2 stub) |
| `src/slotting_optimization_engine/optimization/__init__.py` | Optimization package (Phase 5 stub) |
| `src/slotting_optimization_engine/simulation/__init__.py` | Simulation package (Phase 6 stub) |
| `src/slotting_optimization_engine/reporting/__init__.py` | Reporting package (future stub) |
| `src/slotting_optimization_engine/app/__init__.py` | Streamlit app package (Phase 1.5 stub) |
| `tests/__init__.py` | Test package init |
| `tests/unit/__init__.py` | Unit test package init |
| `tests/unit/test_project_structure.py` | Structure and import verification tests |
| `tests/integration/__init__.py` | Integration test package (future stub) |
| `docs/architecture_sdd.md` | Technical architecture and decisions |
| `docs/data_contract.md` | Preliminary Phase 1 data contract |
| `docs/roadmap.md` | Phase-by-phase roadmap with status |
| `docs/phase_notes/phase_0_design_and_setup.md` | This file |
| `docs/phase_logs/phase_0_terminal_log.md` | Terminal commands and results |

## 3. What each file is for

Described in the "Files created" table above. Key architectural files:

- **`config/project_paths.py`**: Single source of truth for all filesystem paths. Prevents scattered hard-coded paths. Uses `pathlib.Path` for cross-platform support and allows env-var overrides.
- **`pyproject.toml`**: Modern Python packaging standard. Declares `pandas` and `pandera` as core deps, `pytest` and `ruff` as dev deps, `streamlit` as optional, and a test-only Ruff exception for pytest assertions.

## 4. How the flow works

Not applicable for Phase 0 — no execution flow exists yet. The architecture (see `docs/architecture_sdd.md`) defines the planned data flow for Phase 1.

## 5. Main functions / classes

- `config/project_paths.py` exposes `PROJ_ROOT`, `DATA_DIR`, `DATA_RAW_DIR`, `DATA_PROCESSED_DIR`, `DATA_SYNTHETIC_DIR`, etc. as module-level `Path` constants.
- `tests/unit/test_project_structure.py` contains `TestProjectStructure` with parametrised tests for imports, directories, and files.

## 6. Technical decisions

| Decision | Choice | Trade-off |
|---|---|---|
| Package manager | `pyproject.toml` + setuptools | Simpler than Poetry/PDM; no lock file in first cycle |
| Validation library | pandera | Best fit for pandas DataFrame validation; pulls pydantic as dependency |
| Streamlit as optional dep | `[streamlit]` extra | Core install remains lightweight; only Phase 1.5 needs it |
| Path resolution | Eager, with env-var override | Simple and predictable; no lazy evaluation complexity |
| Future stubs | Docstring-only `__init__.py` | Clearly marks deferred scope without polluting the namespace |
| Ruff `S101` in tests | Ignored only for `tests/**/*.py` | Pytest assertions are idiomatic; production code still keeps Bandit-style safety checks |

## 7. Assumptions

- Python 3.11+ is available (tested with 3.13.5).
- The package will be installed in editable mode (`pip install -e ".[dev]"`).
- Synthetic data in data/ directories is generated (Phase 1) and not committed to version control.
- The project root is identified by walking up from `config/project_paths.py`, or overridden via `PROJECT_ROOT` env var.

## 8. Remaining limitations

- No functional code exists beyond configuration and package structure.
- No data validation, generation, or transformation logic.
- No test for actual data correctness (only structure/imports).
- Path creation eagerly creates placeholder directories (safe side effect).

## 9. What is missing for the next phase

For Phase 1, the following must be created:

- `scripts/generate_sample_data.py` — synthetic data generator.
- `scripts/run_data_validation.py` — pandera validation runner.
- `scripts/build_features.py` — feature construction.
- Data modules under `src/slotting_optimization_engine/data/`.
- Feature modules under `src/slotting_optimization_engine/features/`.
- Domain models under `src/slotting_optimization_engine/domain/`.
- Unit tests for data and feature functions.
- Updated `docs/data_contract.md` with finalised schemas.

## 10. How to run related scripts

Phase 0 has no runnable scripts. Setup commands:

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install package with dev dependencies
pip install -e ".[dev]"

# Run structure tests
pytest tests/unit/test_project_structure.py -v

# Run lint checks
ruff check src/ tests/
```

## 11. Expected output

Running `pytest tests/unit/test_project_structure.py -v` should show all tests passing, verifying that:
- All required packages import correctly.
- All required directories exist.
- All required files exist.
- `config/project_paths.py` resolves paths without error.

## 12. Common errors

| Error | Likely cause | Resolution |
|---|---|---|
| `ModuleNotFoundError: No module named 'slotting_optimization_engine'` | Package not installed | Run `pip install -e ".[dev]"` from project root |
| Tests fail on directory paths | Wrong working directory | Run tests from project root or use `--rootdir` |
| ImportError in `project_paths.py` | Missing parent directory | Ensure `src/` layout is intact |

## 13. How to resolve common errors

See common errors table above. The most common fix is ensuring the package is installed in editable mode before running any code.

## 14. Tests covering the phase

| Test | File | What it verifies |
|---|---|---|
| `test_required_packages_importable` | `test_project_structure.py` | All 10 packages import correctly |
| `test_required_directories_exist` | `test_project_structure.py` | All 19 expected directories exist |
| `test_required_files_exist` | `test_project_structure.py` | All 25+ expected files exist |
| `test_config_paths_resolve` | `test_project_structure.py` | Path constants resolve to existing directories |

## 15. Evidence that the phase works

- All structure tests pass (see `docs/phase_logs/phase_0_terminal_log.md` for test results).
- Ruff lint passes for `src` and `tests` after the test-only `S101` configuration.
- The package `slotting_optimization_engine` and all 9 subpackages import successfully.
- `config/project_paths.py` resolves all paths without error.
- `docs/master_plan.md` is updated with Phase 0 completion status.
