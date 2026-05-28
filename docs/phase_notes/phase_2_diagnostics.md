# Phase 2 Notes — Advanced Slotting Diagnostics

## 1. What was implemented

Phase 2 adds descriptive advanced slotting diagnostics. It creates SKU, location, zone, category, and summary diagnostic CSV outputs from Phase 1 processed outputs, enriched with validated synthetic placement context when needed.

The phase does not implement prescriptive scoring, recommendations, scenario comparison, mathematical optimization, simulation, authentication, deployment, or a final business application.

## 2. What files were created

- `src/slotting_optimization_engine/diagnostics/rules.py`
- `scripts/run_diagnostics.py`
- `tests/unit/test_diagnostics_rules.py`
- `docs/phase_notes/phase_2_diagnostics.md`
- `docs/phase_logs/phase_2_terminal_log.md`
- `data/processed/slotting_diagnostics.csv`
- `data/processed/location_diagnostics.csv`
- `data/processed/zone_diagnostics.csv`
- `data/processed/category_diagnostics.csv`
- `data/processed/diagnostic_summary.csv`

## 3. What each file is for

- `diagnostics/rules.py` owns pure descriptive diagnostic builders, threshold config, and CSV saving.
- `run_diagnostics.py` loads Phase 1 processed outputs and validated synthetic context, then writes diagnostics to `data/processed/`.
- `test_diagnostics_rules.py` verifies diagnostic flags, category spread detection, output writing, and missing-input script behavior.
- Diagnostic CSV files are review artifacts for analysts and future Manager verification.
- This phase note records scope, assumptions, and evidence.
- The terminal log records commands, results, errors, and resolutions.

## 4. How the flow works

```text
data/processed/slotting_features.parquet
data/processed/location_utilization.csv
data/processed/zone_utilization.csv
        │
        ├── read by scripts/run_diagnostics.py
        │
data/synthetic/*.csv
        │
        └── read-only validated placement/category context
                │
                ▼
src/slotting_optimization_engine/diagnostics/rules.py
        │
        ├── build_slotting_diagnostics()
        ├── build_location_diagnostics()
        ├── build_zone_diagnostics()
        ├── build_category_diagnostics()
        └── build_diagnostic_summary()
                │
                ▼
data/processed/*diagnostics.csv
```

## 5. Main functions/classes

- `DiagnosticConfig`: inferred thresholds pending business confirmation.
- `build_all_diagnostics()`: orchestrates all pure diagnostic builders.
- `build_slotting_diagnostics()`: flags high-demand poor placement and low-demand/slow-rotation SKUs in premium zones.
- `build_location_diagnostics()`: flags overutilized, underutilized, dense, and mixed-category locations.
- `build_zone_diagnostics()`: flags overutilized/underutilized zones and premium-zone slow-mover presence.
- `build_category_diagnostics()`: flags category spread/misgrouping indicators when fields exist.
- `save_diagnostics()`: writes CSV outputs to `data/processed/`.
- `load_processed_inputs()`: script-level loader for required Phase 1 processed outputs.

## 6. Technical decisions

- Diagnostics live in `diagnostics/rules.py`, not in the UI.
- The CLI writes CSV outputs for easy review and data governance traceability.
- Thresholds are explicit in `DiagnosticConfig` and marked `inferred / pending confirmation`.
- The script reads synthetic source dimensions only to recover placement/category context not persisted in Phase 1 processed outputs.
- The Streamlit helper/UI update is intentionally low-risk: availability tracking and diagnostic summary preview only.
- No prescriptive recommendations or ranking scores were added.

## 7. Assumptions

- Phase 1 processed outputs already exist before running diagnostics.
- Synthetic data remains the only available source data.
- `priority_level <= 2` represents premium zones, pending confirmation.
- `priority_level >= 3` represents lower-priority placement, pending confirmation.
- High demand = top 20% by `total_demand`, low demand = bottom 20%, pending confirmation.
- Long-distance placement = top 25% by distance, pending confirmation.
- Overutilized = avg utilization >= 85%; underutilized = avg utilization <= 20%, pending confirmation.

## 8. Remaining limitations

- Phase 1 processed outputs do not persist full SKU-location placement context, so diagnostics read validated synthetic source tables as enrichment.
- Category misgrouping is an indicator only; it does not model product affinity or operational constraints.
- Thresholds are not calibrated against real warehouse operations.
- Diagnostic counts are not prescriptive scores and must not be used as move priorities.

## 9. What is missing for the next phase

- Business confirmation or adjustment of thresholds.
- Phase 3 prescriptive scoring, if explicitly requested later.
- Scenario comparison, mathematical optimization, simulation, auth, deploy, and final app UX remain deferred.

## 10. How to run related scripts

```powershell
python scripts/build_features.py
python scripts/run_diagnostics.py
python -m ruff check src tests scripts
python -m pytest -v
```

## 11. Expected output

- `slotting_diagnostics.csv`: SKU-level descriptive diagnostic flags.
- `location_diagnostics.csv`: location utilization, density, and category-mix diagnostics.
- `zone_diagnostics.csv`: zone utilization and premium-zone slow-mover diagnostics.
- `category_diagnostics.csv`: category spread and grouping indicators.
- `diagnostic_summary.csv`: metric counts with threshold notes.

## 12. Common errors

- Missing Phase 1 processed outputs: `run_diagnostics.py` raises a `FileNotFoundError` and asks to run `build_features.py`.
- Missing parquet support: `pyarrow` must be installed through project dependencies.
- Windows `UnicodeEncodeError` in Graphify query output: console encoding is not UTF-8.

## 13. How to resolve common errors

- Regenerate Phase 1 outputs with `python scripts/build_features.py`.
- Install project dependencies with `pip install -e ".[dev]"`.
- For Graphify on Windows PowerShell, set `$env:PYTHONIOENCODING='utf-8'` before the query.

## 14. Tests covering the phase

- `tests/unit/test_diagnostics_rules.py`
- Updated `tests/unit/test_project_structure.py`
- Updated `tests/unit/test_dashboard_data.py`

## 15. Evidence that the phase works

- Graphify was queried before implementation using the requested Phase 2 query; the first run hit a Windows encoding error and was rerun with UTF-8.
- `python scripts/run_diagnostics.py` produced all five diagnostic outputs in `data/processed/`.
- `python -m ruff check src tests scripts` passed after formatting fixes.
- `python -m pytest -v` was run after docs existed and passed.
- `graphify update .` and a post-phase UTF-8 Graphify query were run for updated relationship context.
