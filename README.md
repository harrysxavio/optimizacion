# Introducción en español

`slotting-optimization-engine` es un motor modular en Python para analizar la calidad del slotting de un centro de distribución: qué SKU está ubicado en qué zona, qué tan demandado es, cuánto espacio usa y qué señales merecen revisión operativa.

El problema que resuelve hoy es ordenar el trabajo analítico: transforma datos sintéticos de SKUs, ubicaciones, zonas, inventario y pedidos en features, diagnósticos descriptivos y una cola de priorización para revisar oportunidades de slotting. Esto ayuda a detectar casos como SKUs de alta demanda lejos del despacho, slow movers ocupando zonas premium y zonas con presión de capacidad.

Lo que puede hacer hoy:

- Generar datos sintéticos reproducibles.
- Validar contratos de datos.
- Construir features de demanda, utilización y alineación inicial.
- Mostrar una UI técnica mínima en Streamlit para inspección.
- Generar diagnósticos descriptivos de slotting, ubicación, zona y categoría.
- Generar scoring de priorización Phase 3 con pesos transparentes e inferidos.

Lo que todavía NO hace:

- No calcula una solución óptima de slotting.
- No recomienda movimientos óptimos SKU→ubicación.
- No ejecuta simulación operativa ni comparación de escenarios.
- No usa datos reales de WMS/ERP.
- No tiene autenticación, despliegue productivo ni UX final de negocio.

Uso paso a paso:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

python scripts/generate_sample_data.py
python scripts/run_data_validation.py
python scripts/build_features.py
python scripts/run_diagnostics.py
python scripts/run_scoring.py

python -m ruff check src tests scripts
python -m pytest -v
```

Outputs principales:

- `data/processed/slotting_features.parquet`
- `data/processed/location_utilization.csv`
- `data/processed/zone_utilization.csv`
- `data/processed/slotting_diagnostics.csv`
- `data/processed/location_diagnostics.csv`
- `data/processed/zone_diagnostics.csv`
- `data/processed/category_diagnostics.csv`
- `data/processed/diagnostic_summary.csv`
- `data/processed/slotting_opportunity_scores.csv`
- `data/processed/priority_recommendation_queue.csv`
- `data/processed/scoring_summary.csv`

Caveats importantes: los datos actuales son sintéticos y los umbrales/pesos de scoring están marcados como `inferred / pending confirmation`. El scoring es una priorización para revisión humana, no una optimización matemática ni una recomendación automática de movimientos.

# Slotting Optimization Engine

A modular Python engine for slotting optimization in high-volume e-commerce and retail distribution centers. Built in controlled phases, it evolves from descriptive analytics toward prescriptive optimization.

## Current scope

**Phase 0 completed** — project skeleton, architecture, base documentation, and configuration established.
**Phase 1 completed** — synthetic data pipeline, validation, and feature builder.  
**Phase 1.5 completed** — minimal technical Streamlit front for inspecting processed outputs.  
**Phase 2 completed** — descriptive advanced slotting diagnostics and diagnostic output files.  
**Phase 3 completed** — transparent scoring/prioritization queue from Phase 2 diagnostics.

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
│       ├── scoring/                   # Prioritization scoring (Phase 3)
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

## Phase 3 scoring/prioritization

Run Phase 3 scoring after Phase 2 diagnostic outputs exist:

```powershell
python scripts/run_scoring.py
```

Scoring outputs prioritize review work only. They do not calculate optimal moves, target locations, solver decisions, simulation results, or business-approved recommendations. All weights are transparent and marked as `inferred / pending confirmation`.

Expected outputs:

- `data/processed/slotting_opportunity_scores.csv`
- `data/processed/priority_recommendation_queue.csv`
- `data/processed/scoring_summary.csv`

## Output structure

After running Phase 1, Phase 2, and Phase 3 scripts:

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
    ├── diagnostic_summary.csv      # Metric summary of diagnostic counts
    ├── slotting_opportunity_scores.csv     # Action-level prioritization scores
    ├── priority_recommendation_queue.csv   # Sorted review queue
    └── scoring_summary.csv                 # Phase 3 scoring metrics/config notes
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
| `docs/phase_notes/phase_3_scoring.md` | Phase 3 scoring rules, outputs, and evidence |
| `docs/phase_logs/phase_0_terminal_log.md` | Phase 0 terminal commands and results |
| `docs/phase_logs/phase_1_terminal_log.md` | Phase 1 terminal commands and results |
| `docs/phase_logs/phase_1_5_terminal_log.md` | Phase 1.5 terminal commands and results |
| `docs/phase_logs/phase_2_terminal_log.md` | Phase 2 terminal commands and results |
| `docs/phase_logs/phase_3_terminal_log.md` | Phase 3 terminal commands and results |
| `docs/DESIGN.md` | Lightweight technical UI design system |
| `docs/data/README.md` | Data documentation overview |
| `docs/data/dataset-index.md` | All datasets with schemas and lineage |
| `docs/data/business-knowledge.md` | Business rules and domain knowledge |
| `docs/data/query-log.md` | Data operations record |
| `docs/data/synthetic/cleaning-log.md` | Synthetic data cleaning events |
| `docs/data/synthetic/learnings.md` | Technical patterns and gotchas |

## Future phases

Advanced capabilities are intentionally deferred and will not appear in early implementations:

- Phase 3: Prescriptive scoring and prioritization — completed as review prioritization only
- Phase 4: Scenario/model comparison
- Phase 5: Mathematical optimization
- Phase 6: Operational simulation
- Phase 7: Production-ready application

See `docs/roadmap.md` for detailed status.
