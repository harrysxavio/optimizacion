# Phase 1 — Synthetic Data Pipeline and Feature Builder

**Phase:** 1  
**Status:** Complete  
**Implementer:** AI-assisted (SDD Apply executor)  
**Date:** 2026-05-27

---

## 1. What was implemented

The complete Phase 1 data pipeline:

- Synthetic data generation for all six core datasets (SKUs, zones, locations, inventory, orders, order lines).
- Data loading from CSV with configurable path resolution.
- Two-tier data validation (pandera schemas → explicit pandas-based fallback).
- Analytical feature construction (demand, picking frequency, utilisation, distance indicators, alignment score).
- CLI scripts to orchestrate generation, validation, and feature building.
- Unit tests for all modules.
- Data governance documentation (`docs/data/`).

Graphify context was used before Phase 1 implementation to visualise code relationships and identify which modules were touched by Phase 0. Graphify confirmed the Phase 0 structure before Phase 1 edits began.

---

## 2. Files created

### Source modules

| File | Purpose |
|------|---------|
| `src/slotting_optimization_engine/domain/constants.py` | Column name constants, enums, and default configuration |
| `src/slotting_optimization_engine/data/generator.py` | `SyntheticDataGenerator` — generates all six datasets |
| `src/slotting_optimization_engine/data/loading.py` | CSV loading with optional validation |
| `src/slotting_optimization_engine/data/validation.py` | Two-tier validation: pandera schemas + explicit fallback |
| `src/slotting_optimization_engine/features/builder.py` | Feature construction: demand, utilisation, alignment |

### Scripts

| File | Purpose |
|------|---------|
| `scripts/generate_sample_data.py` | CLI entrypoint for data generation |
| `scripts/run_data_validation.py` | CLI entrypoint for validation |
| `scripts/build_features.py` | CLI entrypoint for feature building |

### Tests

| File | Purpose |
|------|---------|
| `tests/unit/test_data_generator.py` | ~25 tests for generator integrity, FK consistency, determinism |
| `tests/unit/test_data_validation.py` | ~15 tests for validation pass/fail scenarios |
| `tests/unit/test_data_loading.py` | 4 tests for CSV roundtrip and error handling |
| `tests/unit/test_feature_builder.py` | ~15 tests for feature correctness and output formats |

### Documentation

| File | Purpose |
|------|---------|
| `docs/data/README.md` | Data documentation overview |
| `docs/data/dataset-index.md` | Complete dataset index with schemas and lineage |
| `docs/data/business-knowledge.md` | Business rules and domain knowledge |
| `docs/data/query-log.md` | Record of data operations |
| `docs/data/synthetic/cleaning-log.md` | Synthetic data cleaning events |
| `docs/data/synthetic/learnings.md` | Reusable technical patterns and gotchas |
| `docs/phase_notes/phase_1_data_pipeline.md` | This file |
| `docs/phase_logs/phase_1_terminal_log.md` | Terminal log for Phase 1 commands |

---

## 3. What each file is for

### `domain/constants.py`

Centralises all column name constants (as grouped classes: `Skus`, `Zones`, `Locations`, `Inventory`, `Orders`, `OrderLines`, `Features`), enums (`RotationClass`, `ZoneType`, `SalesChannel`), default generation parameters, and file names. Imported by all data and feature modules — no magic strings.

### `data/generator.py`

`SyntheticDataGenerator` produces six internally consistent datasets:

- **SKUs**: 500 (default) with categories, log-normal volumes/weights, rotation class distribution (20/30/30/20).
- **Zones**: 10 (default) with types, priority levels, capacities inversely proportional to priority.
- **Locations**: 20 per zone with capacity variation.
- **Inventory**: SKU-location assignments with 10% empty locations, stock-based demand coverage.
- **Orders**: 2,000 (default) over 90-day window, three channels.
- **Order Lines**: Weighted towards high-rotation SKUs, Poisson-distributed lines per order.

All generation is deterministic via `numpy.random.default_rng(seed=42)`.

### `data/validation.py`

Two-tier validation:

- **Tier 1 (pandera)**: `DataFrameModel` schemas with field constraints (non-null, unique, gt/ge, isin). Uses `coerce=True, strict=False`.
- **Tier 2 (fallback)**: Explicit pandas functions that reproduce the same rules. Activated when pandera import fails.

All validators return lists of error strings. `validate_all_datasets` automatically resolves FK dependencies.

### `data/loading.py`

`load_dataset` reads a single CSV by entity name. `load_all_datasets` loads in dependency order so FK validation works. Both accept `validate=True` to run validation on load.

### `features/builder.py`

Seven feature builders:

1. `build_demand_by_sku` — Total quantity + order count per SKU.
2. `build_sku_footprint` — Total occupied volume/weight per SKU.
3. `build_location_utilization` — Volume/weight % per location (capped at 100%, over-capacity flagged).
4. `build_zone_utilization` — Aggregated zone-level stats.
5. `build_distance_indicators` — Distance-to-dispatch and priority per SKU-location pair.
6. `build_alignment_score` — ⚠️ **Non-prescriptive** heuristic flagging high-demand SKUs in close locations.
7. `build_all_features` — Orchestrates all builders and merges into a wide feature table.

---

## 4. How the flow works

```text
scripts/generate_sample_data.py
         │
         ▼
  SyntheticDataGenerator
         │
         ├── data/synthetic/skus.csv
         ├── data/synthetic/zones.csv
         ├── data/synthetic/locations.csv
         ├── data/synthetic/inventory.csv
         ├── data/synthetic/orders.csv
         └── data/synthetic/order_lines.csv
         │
         ▼
scripts/run_data_validation.py
         │
         ▼
  loading.load_all_datasets()
         │
         ▼
  validation.validate_all_datasets()
         │  (pandera schemas / explicit fallback)
         │
         ▼
scripts/build_features.py
         │
         ▼
  loading.load_all_datasets(validate=True)
         │
         ▼
  features.builder.build_all_features()
         │
         ├── data/processed/slotting_features.parquet
         ├── data/processed/location_utilization.csv
         └── data/processed/zone_utilization.csv
```

---

## 5. Main functions / classes

### Data generation

| Class/Method | Responsibility |
|---|---|
| `GenerationConfig` | Dataclass holding generation parameters |
| `SyntheticDataGenerator.__init__` | Seeds RNG, stores config |
| `SyntheticDataGenerator.generate_all()` | Returns dict of 6 DataFrames |
| `generate_all_datasets()` | Convenience wrapper |

### Data loading

| Function | Responsibility |
|---|---|
| `load_dataset(entity, directory, validate)` | Load single CSV, optionally validate |
| `load_all_datasets(directory, validate)` | Load all 6 in FK-safe order |

### Data validation

| Function | Responsibility |
|---|---|
| `validate_dataset(entity, df, **fks)` | Dispatch to pandera or explicit validator |
| `validate_all_datasets(datasets)` | Validate all 6 with FK resolution |
| `format_validation_report(results)` | Pretty-print validation results |

### Feature building

| Function | Responsibility |
|---|---|
| `build_demand_by_sku(order_lines)` | Demand and order count aggregation |
| `build_sku_footprint(inventory)` | Volume/weight per SKU |
| `build_location_utilization(inventory, locations)` | Location utilisation % |
| `build_zone_utilization(loc_util, locations, zones)` | Zone-level utilisation |
| `build_distance_indicators(inventory, locations, zones)` | Distance/priority for SKU-location |
| `build_alignment_score(demand, skus, distance)` | ⚠️ Non-prescriptive alignment heuristic |
| `build_all_features(datasets)` | Orchestrator — returns 3 DataFrames |
| `save_features(outputs, output_dir)` | Save to parquet/CSV |

---

## 6. Technical decisions

| Decision | Choice | Trade-off |
|---|---|---|
| Validation strategy | Pandera primary + explicit fallback | Ensures validation works regardless of pandera compatibility |
| Data exchange format | CSV for source, Parquet for features | CSV is human-readable; Parquet is typed and faster for analytics |
| Log-normal distributions | Realistic physical dimensions | Adds complexity vs uniform distribution |
| 10% empty locations | Simulates realistic DC | May under/over-estimate utilisation for small datasets |
| Utilisation capping at 100% | Better UX for reporting | Raw overage data preserved in over_capacity flag |
| Alignment score as heuristic | Non-prescriptive by design | Must not be used for automated decisions without review |
| `pyarrow` dependency added | Required for Parquet output | Adds ~15MB to install |

---

## 7. Assumptions

- All Phase 1 data is synthetic — threshold and distributions must be recalibrated with real data.
- Volumes are in cubic centimeters, weights in kilograms.
- Single distribution center model (no multi-DC logic).
- Daily batch processing (no streaming).
- Pandera 0.31.x is compatible with the installed pandas version. If not, the explicit fallback handles validation transparently.

---

## 8. Remaining limitations

- No real WMS/ERP data connectors (deferred to Phase 7).
- No advanced slotting diagnostics (Phase 2).
- No prescriptive scoring or recommendations (Phase 3).
- Alignment score is heuristic and non-prescriptive — needs calibration.
- No Streamlit front-end for visual inspection (Phase 1.5).
- No scenario comparison or what-if modelling (Phase 4).
- No mathematical optimisation (Phase 5).
- No operational simulation (Phase 6).

---

## 9. What is missing for the next phase

Phase 1.5 requires:

- Streamlit entrypoint (`src/slotting_optimization_engine/app/streamlit_app.py`).
- Basic dataset summary views.
- Basic utilisation, demand, and rotation visuals.
- Clear error messages when required data files do not exist.
- Phase 1.5 documentation and terminal log.

Dependencies for Phase 1.5: `pip install -e ".[streamlit]"`.

---

## 10. How to run related scripts

```powershell
# Generate synthetic data (must be first)
python scripts/generate_sample_data.py

# Validate generated data
python scripts/run_data_validation.py

# Build analytical features (includes validation)
python scripts/build_features.py

# Run all tests
pytest -v

# Lint check
python -m ruff check src tests scripts
```

---

## 11. Expected output

After running all scripts:

- **`data/synthetic/`**: 6 CSV files with synthetic data.
- **`data/processed/`**: 1 Parquet + 2 CSV files with analytical features.
- **Console**: Info-level logging showing row counts and validation results.
- **Tests**: All tests passing.

---

## 12. Common errors

| Error | Likely cause | Resolution |
|---|---|---|
| `FileNotFoundError: Dataset file not found` | `generate_sample_data.py` not run yet | Run `python scripts/generate_sample_data.py` |
| `ModuleNotFoundError: slotting_optimization_engine` | Package not installed | Run `pip install -e ".[dev]"` |
| `pandera.errors.SchemaError` | Data violates contract | Check dataset contents; run with `validate=False` for debugging |
| Parquet-related ImportError | `pyarrow` not installed | Run `pip install "pyarrow>=10"` |

---

## 13. How to resolve common errors

See table above. The most common fix sequence:
1. `pip install -e ".[dev]"` (install package).
2. `python scripts/generate_sample_data.py` (generate data).
3. `python scripts/run_data_validation.py` (validate).
4. `python scripts/build_features.py` (build features).

---

## 14. Tests covering the phase

| Test class | File | What it verifies |
|---|---|---|
| `TestSyntheticDataGenerator` | `test_data_generator.py` | Column presence, row counts, FK integrity, determinism, valid domains |
| `TestValidateSkus` | `test_data_validation.py` | SKU validation pass/fail (nulls, duplicates, zero values, invalid classes) |
| `TestValidateZones` | `test_data_validation.py` | Zone validation pass/fail |
| `TestValidateLocations` | `test_data_validation.py` | Location validation + FK to zones |
| `TestValidateInventory` | `test_data_validation.py` | Inventory validation + FKs to SKUs/locations |
| `TestValidateOrders` | `test_data_validation.py` | Orders validation |
| `TestValidateOrderLines` | `test_data_validation.py` | Order lines validation + FK checks |
| `TestValidateAll` | `test_data_validation.py` | Multi-dataset validation + report format |
| `TestLoadDataset` | `test_data_loading.py` | CSV roundtrip, error handling |
| `TestDemandBySku` | `test_feature_builder.py` | Demand aggregation |
| `TestSkuFootprint` | `test_feature_builder.py` | Volume/weight footprint |
| `TestLocationUtilization` | `test_feature_builder.py` | Location utilisation range |
| `TestZoneUtilization` | `test_feature_builder.py` | Zone aggregation |
| `TestAlignmentScore` | `test_feature_builder.py` | Alignment score range and columns |
| `TestBuildAllFeatures` | `test_feature_builder.py` | Full pipeline: row counts, output files, non-null features |

Total: ~60 tests across 4 test files.

---

## 15. Evidence that the phase works

- All tests pass (see `docs/phase_logs/phase_1_terminal_log.md` for results).
- Synthetic data generates 6 consistent CSV files with referential integrity.
- Validation detects nulls, duplicates, zero/negative values, and FK violations.
- Feature builder produces 3 output files with correct row counts and no silent drops.
- Ruff lint passes for `src`, `tests`, and `scripts`.
- Graphify was used before implementation to verify Phase 0 code relationships.

Phase 1 is ready for Manager verification.
