"""
Test project package structure and import paths.

Verifies that Phase 0 delivered a valid Python package that can be
imported, and that the expected directory structure exists. This is
a sanity check — it catches missing __init__.py files, path issues,
and broken imports early.
"""

from pathlib import Path

import pytest

# The project root is four levels up from this test file.
PROJ_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Packages that must be importable
# ---------------------------------------------------------------------------

REQUIRED_PACKAGES = [
    "slotting_optimization_engine",
    "slotting_optimization_engine.config",
    "slotting_optimization_engine.data",
    "slotting_optimization_engine.domain",
    "slotting_optimization_engine.features",
    "slotting_optimization_engine.diagnostics",
    "slotting_optimization_engine.optimization",
    "slotting_optimization_engine.simulation",
    "slotting_optimization_engine.reporting",
    "slotting_optimization_engine.app",
]

REQUIRED_DIRECTORIES = [
    "src/slotting_optimization_engine",
    "src/slotting_optimization_engine/config",
    "src/slotting_optimization_engine/data",
    "src/slotting_optimization_engine/domain",
    "src/slotting_optimization_engine/features",
    "src/slotting_optimization_engine/diagnostics",
    "src/slotting_optimization_engine/optimization",
    "src/slotting_optimization_engine/simulation",
    "src/slotting_optimization_engine/reporting",
    "src/slotting_optimization_engine/app",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
    "data/synthetic",
    "docs",
    "docs/phase_notes",
    "docs/phase_logs",
    "scripts",
    "notebooks",
]

REQUIRED_FILES = [
    "README.md",
    "pyproject.toml",
    ".gitignore",
    ".env.example",
    "docs/master_plan.md",
    "docs/architecture_sdd.md",
    "docs/data_contract.md",
    "docs/roadmap.md",
    "docs/phase_notes/phase_0_design_and_setup.md",
    "docs/phase_notes/phase_1_5_streamlit_front.md",
    "docs/phase_logs/phase_0_terminal_log.md",
    "docs/phase_logs/phase_1_5_terminal_log.md",
    "docs/DESIGN.md",
    "src/slotting_optimization_engine/__init__.py",
    "src/slotting_optimization_engine/config/__init__.py",
    "src/slotting_optimization_engine/config/project_paths.py",
    "src/slotting_optimization_engine/data/__init__.py",
    "src/slotting_optimization_engine/data/generator.py",
    "src/slotting_optimization_engine/data/loading.py",
    "src/slotting_optimization_engine/data/validation.py",
    "src/slotting_optimization_engine/domain/__init__.py",
    "src/slotting_optimization_engine/domain/constants.py",
    "src/slotting_optimization_engine/features/__init__.py",
    "src/slotting_optimization_engine/features/builder.py",
    "src/slotting_optimization_engine/diagnostics/__init__.py",
    "src/slotting_optimization_engine/optimization/__init__.py",
    "src/slotting_optimization_engine/simulation/__init__.py",
    "src/slotting_optimization_engine/reporting/__init__.py",
    "src/slotting_optimization_engine/app/__init__.py",
    "src/slotting_optimization_engine/app/dashboard_data.py",
    "src/slotting_optimization_engine/app/streamlit_app.py",
    "scripts/generate_sample_data.py",
    "scripts/run_data_validation.py",
    "scripts/build_features.py",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/unit/test_project_structure.py",
    "tests/unit/test_data_generator.py",
    "tests/unit/test_data_validation.py",
    "tests/unit/test_data_loading.py",
    "tests/unit/test_feature_builder.py",
    "tests/unit/test_dashboard_data.py",
    "tests/integration/__init__.py",
]


class TestProjectStructure:
    """Verify the Phase 0 project skeleton is in place."""

    @pytest.mark.parametrize("package_name", REQUIRED_PACKAGES)
    def test_required_packages_importable(self, package_name: str) -> None:
        """All expected subpackages must be importable."""
        __import__(package_name)

    @pytest.mark.parametrize("dir_relpath", REQUIRED_DIRECTORIES)
    def test_required_directories_exist(self, dir_relpath: str) -> None:
        """All expected directories must exist on disk."""
        path = PROJ_ROOT / dir_relpath
        assert path.is_dir(), f"Expected directory does not exist: {path}"

    @pytest.mark.parametrize("file_relpath", REQUIRED_FILES)
    def test_required_files_exist(self, file_relpath: str) -> None:
        """All expected files must exist on disk."""
        path = PROJ_ROOT / file_relpath
        assert path.is_file(), f"Expected file does not exist: {path}"

    def test_config_paths_resolve(self) -> None:
        """project_paths module must resolve paths without error."""
        from slotting_optimization_engine.config.project_paths import (  # noqa: F811  # noqa: F401
            DATA_DIR,
            DATA_PROCESSED_DIR,
            DATA_RAW_DIR,
            DATA_SYNTHETIC_DIR,
            PROJ_ROOT,
        )

        # These assertions protect the next phases from writing generated data
        # into an unexpected location because of a broken project-root lookup.
        assert PROJ_ROOT.exists()
        assert DATA_DIR.exists()
        assert DATA_RAW_DIR.exists()
        assert DATA_PROCESSED_DIR.exists()
        assert DATA_SYNTHETIC_DIR.exists()
