# Slotting Optimization Engine

A modular Python engine for slotting optimization in high-volume e-commerce and retail distribution centers. Built in controlled phases, it evolves from descriptive analytics toward prescriptive optimization.

## Current scope

**Phase 0 completed** — project skeleton, architecture, base documentation, and configuration established.
**Phase 1 completed** — synthetic data pipeline, validation, and feature builder.  
**Phase 1.5 completed** — minimal technical Streamlit front for inspecting processed outputs.  
**Phase 2 completed** — descriptive advanced slotting diagnostics and diagnostic output files.

## Project structure

```
slotting-optimization-engine/
├── README.md                          # This file
├── pyproject.toml                     # Package definition and dependencies
├── .gitignore
├── .env.example
├── data/
│   ├── raw/                           # Raw synthetic input data (Phase 1+)
│   ├── processed/                     # Transformed analytical datasets (Phase 1+)
│   └── synthetic/                     # Generated synthetic data (Phase 1+)
├── docs/
│   ├── master_plan.md                 # Living project guide and traceability
│   ├── architecture_sdd.md            # Technical architecture and design decisions
│   ├── data_contract.md               # Data entities, fields, and validation rules
│   ├── roadmap.md                     # Phase-by-phase project roadmap
│   ├── phase_notes/                   # Detailed phase documentation
│   └── phase_logs/                    # Terminal logs recording execution
├── scripts/                           # Phase 1+ CLI scripts
├── src/
│   └── slotting_optimization_engine/  # Main Python package
│       ├── config/                    # Central configuration and paths
│       ├── data/                      # Data generation, loading, validation
│       ├── domain/                    # Business domain concepts
│       ├── features/                  # Analytical feature construction
│       ├── diagnostics/               # Descriptive slotting diagnostics (Phase 2)
│       ├── optimization/              # Mathematical optimization (future stub)
│       ├── simulation/                # Operational simulation (future stub)
│       ├── reporting/                 # Outputs and summaries
│       └── app/                       # Streamlit technical UI (Phase 1.5)
├── tests/
│   ├── unit/                          # Unit tests
│   └── integration/                   # Integration tests (future)
└── notebooks/                         # Exploratory analysis notebooks
```

## Quick start (environment setup)

```powershell
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install package in development mode with dev dependencies
pip install -e ".[dev]"
```

## Phase 1 commands

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

## Phase 1.5 Streamlit front

Prerequisite outputs expected by the app:

- `data/processed/slotting_features.parquet`
- `data/processed/location_utilization.csv`
- `data/processed/zone_utilization.csv`

If those files are missing, regenerate Phase 1 outputs first:

```powershell
python scripts/generate_sample_data.py
python scripts/run_data_validation.py
python scripts/build_features.py
```

Install the optional Streamlit dependency and launch the technical front:

```powershell
pip install -e ".[streamlit]"
streamlit run src/slotting_optimization_engine/app/streamlit_app.py
```

The UI is descriptive only. The preliminary alignment score is shown as a non-prescriptive inspection signal, not as an optimization recommendation.

## Phase 2 diagnostics

Run Phase 2 diagnostics after Phase 1 processed outputs exist:

```powershell
python scripts/run_diagnostics.py
```

Diagnostic outputs are descriptive flags for analyst review only. Thresholds are inferred from the synthetic dataset and pending business confirmation.

Expected outputs:

- `data/processed/slotting_diagnostics.csv`
- `data/processed/location_diagnostics.csv`
- `data/processed/zone_diagnostics.csv`
- `data/processed/category_diagnostics.csv`
- `data/processed/diagnostic_summary.csv`

## Output structure

After running Phase 1 and Phase 2 scripts:

```
data/
├── synthetic/
│   ├── skus.csv              # 500 SKUs
│   ├── zones.csv             # 10 warehouse zones
│   ├── locations.csv         # 200 storage locations
│   ├── inventory.csv         # ~700 inventory records
│   ├── orders.csv            # 2,000 order headers
│   └── order_lines.csv       # ~10,000 order lines
└── processed/
    ├── slotting_features.parquet   # Wide feature table (one row per SKU)
    ├── location_utilization.csv    # Per-location utilisation %
    ├── zone_utilization.csv        # Per-zone utilisation summary
    ├── slotting_diagnostics.csv    # SKU-level descriptive diagnostic flags
    ├── location_diagnostics.csv    # Location utilization/density diagnostics
    ├── zone_diagnostics.csv        # Zone utilization and mix diagnostics
    ├── category_diagnostics.csv    # Category spread/grouping indicators
    └── diagnostic_summary.csv      # Metric summary of diagnostic counts
```

## Documentation map

| Document | Purpose |
|---|---|
| `docs/master_plan.md` | Living project guide, scope, decisions, and traceability |
| `docs/architecture_sdd.md` | Technical architecture, module responsibilities, data flow |
| `docs/data_contract.md` | Data entities, fields, validation rules (finalised) |
| `docs/roadmap.md` | Phases 0–7 with implementation status |
| `docs/phase_notes/phase_0_design_and_setup.md` | Phase 0 design decisions and evidence |
| `docs/phase_notes/phase_1_data_pipeline.md` | Phase 1 design decisions and evidence |
| `docs/phase_notes/phase_1_5_streamlit_front.md` | Phase 1.5 Streamlit front decisions and evidence |
| `docs/phase_notes/phase_2_diagnostics.md` | Phase 2 diagnostic rules, outputs, and evidence |
| `docs/phase_logs/phase_0_terminal_log.md` | Phase 0 terminal commands and results |
| `docs/phase_logs/phase_1_terminal_log.md` | Phase 1 terminal commands and results |
| `docs/phase_logs/phase_1_5_terminal_log.md` | Phase 1.5 terminal commands and results |
| `docs/phase_logs/phase_2_terminal_log.md` | Phase 2 terminal commands and results |
| `docs/DESIGN.md` | Lightweight technical UI design system |
| `docs/data/README.md` | Data documentation overview |
| `docs/data/dataset-index.md` | All datasets with schemas and lineage |
| `docs/data/business-knowledge.md` | Business rules and domain knowledge |
| `docs/data/query-log.md` | Data operations record |
| `docs/data/synthetic/cleaning-log.md` | Synthetic data cleaning events |
| `docs/data/synthetic/learnings.md` | Technical patterns and gotchas |

## Future phases

Advanced capabilities are intentionally deferred and will not appear in early implementations:

- Phase 3: Prescriptive scoring and prioritization
- Phase 4: Scenario/model comparison
- Phase 5: Mathematical optimization
- Phase 6: Operational simulation
- Phase 7: Production-ready application

See `docs/roadmap.md` for detailed status.
