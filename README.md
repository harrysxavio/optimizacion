# Introducción en español

`slotting-optimization-engine` es un motor modular en Python para entender y mejorar, de forma gradual, el **slotting** de un centro de distribución.

En simple: **slotting** significa decidir dónde conviene ubicar cada SKU dentro del depósito. No es solo “poner productos en estanterías”; una mala ubicación puede aumentar caminatas, congestionar zonas, ocupar espacios premium con productos lentos o dejar SKUs de alta demanda lejos del despacho.

## Qué problema ayuda a mirar

Hoy el proyecto ordena el análisis, no reemplaza al equipo operativo. Toma datos sintéticos de SKUs, ubicaciones, zonas, inventario y pedidos, y los transforma en señales para responder preguntas como estas:

| Pregunta | Ejemplo de señal actual |
|---|---|
| ¿Qué SKUs de alta demanda están lejos o en zonas poco prioritarias? | `review_high_demand_far_sku` |
| ¿Qué slow movers ocupan zonas premium? | `review_slow_mover_in_premium_zone` |
| ¿Qué zonas muestran presión de capacidad? | `review_zone_capacity_pressure` |
| ¿Cómo cambian las prioridades si miro primero demanda, capacidad o balance general? | Comparación de escenarios Phase 4 |

## Qué puede hacer hoy, hasta Phase 4

| Fase | Qué hace | Qué produce |
|---|---|---|
| Phase 1 | Genera datos sintéticos, valida contratos y construye features | Tablas de SKUs, demanda, utilización y features |
| Phase 1.5 | Muestra una UI técnica mínima en Streamlit | Inspección visual de outputs procesados |
| Phase 2 | Detecta diagnósticos descriptivos | Flags por SKU, ubicación, zona y categoría |
| Phase 3 | Prioriza oportunidades para revisión humana | Scores y cola de revisión |
| Phase 4 | Compara lentes analíticos what-if | Ranking comparativo por escenario/modelo simple |

## Qué NO deberías decidir a ciegas

- No muevas SKUs automáticamente usando estos CSV.
- No trates un score alto como una orden operativa.
- No interpretes los escenarios como solución óptima.
- No cambies layout, dotación o capacidad sin validar con operación real.
- No uses estos pesos como política de negocio hasta confirmarlos con expertos.

Los datos actuales son sintéticos y los umbrales/pesos están marcados como `inferred / pending confirmation`. Eso es DELIBERADO: sirve para aprender y auditar la lógica antes de convertirla en decisión de negocio.

## Uso paso a paso

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

python scripts/generate_sample_data.py
python scripts/run_data_validation.py
python scripts/build_features.py
python scripts/run_diagnostics.py
python scripts/run_scoring.py
python scripts/run_scenarios.py

python -m ruff check src tests scripts
python -m pytest -v
```

## Qué hace cada comando

| Comando | Explicación simple |
|---|---|
| `generate_sample_data.py` | Crea datos sintéticos reproducibles para practicar sin tocar datos reales |
| `run_data_validation.py` | Revisa que IDs, claves, tipos y reglas mínimas estén bien |
| `build_features.py` | Calcula demanda, utilización y señales analíticas base |
| `run_diagnostics.py` | Marca problemas descriptivos, como capacidad o mala ubicación relativa |
| `run_scoring.py` | Ordena oportunidades para revisión humana con pesos transparentes |
| `run_scenarios.py` | Compara escenarios analíticos: baseline, demanda primero, capacidad primero y revisión balanceada |

## Outputs principales

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
- `data/processed/scenario_comparison.csv`
- `data/processed/scenario_action_mix.csv`
- `data/processed/scenario_summary.csv`

## Cómo leer los outputs de Phase 4

| Archivo | Cómo leerlo |
|---|---|
| `scenario_comparison.csv` | Top N por escenario con ranking recalculado según el lente analítico |
| `scenario_action_mix.csv` | Cuánta mezcla de acciones aparece en cada escenario |
| `scenario_summary.csv` | Métricas comparables: score promedio, high priority, foco SKU/zona y cobertura de acciones |

## Posibles usos actuales

- Preparar una conversación con operación sobre dónde revisar primero.
- Comparar si el backlog se ve distinto cuando priorizás demanda o capacidad.
- Documentar supuestos antes de pedir datos reales.
- Diseñar una futura fase de optimización con mejores requisitos.

## Posibilidades futuras

Las fases futuras podrían agregar optimización matemática, simulación operativa, conectores WMS/ERP, autenticación, despliegue y una app de negocio. Eso todavía NO está implementado.

Caveat clave: Phase 4 compara modelos/lentes simples sobre scores existentes. No calcula ubicaciones destino, no resuelve un modelo de optimización y no ejecuta movimientos de SKUs.

# Slotting Optimization Engine

A modular Python engine for slotting optimization in high-volume e-commerce and retail distribution centers. Built in controlled phases, it evolves from descriptive analytics toward prescriptive optimization.

## Current scope

**Phase 0 completed** — project skeleton, architecture, base documentation, and configuration established.
**Phase 1 completed** — synthetic data pipeline, validation, and feature builder.  
**Phase 1.5 completed** — minimal technical Streamlit front for inspecting processed outputs.  
**Phase 2 completed** — descriptive advanced slotting diagnostics and diagnostic output files.  
**Phase 3 completed** — transparent scoring/prioritization queue from Phase 2 diagnostics.  
**Phase 4 completed** — analytical scenario/model comparison from Phase 3 scores.

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
│       ├── scenarios/                 # Analytical scenario comparison (Phase 4)
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

## Phase 4 scenario/model comparison

Run Phase 4 after Phase 3 scoring outputs exist:

```powershell
python scripts/run_scenarios.py
```

Scenario outputs compare transparent analytical lenses such as `baseline`, `demand_first`, `capacity_first`, and `balanced_review`. They are what-if review summaries only; they do not calculate optimal moves, target locations, solver decisions, simulation results, or automatic SKU movement instructions.

Expected outputs:

- `data/processed/scenario_comparison.csv`
- `data/processed/scenario_action_mix.csv`
- `data/processed/scenario_summary.csv`

## Output structure

After running Phase 1, Phase 2, Phase 3, and Phase 4 scripts:

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
    ├── scoring_summary.csv                 # Phase 3 scoring metrics/config notes
    ├── scenario_comparison.csv             # Phase 4 top-N scenario comparison rows
    ├── scenario_action_mix.csv             # Phase 4 action mix by scenario
    └── scenario_summary.csv                # Phase 4 scenario-level metrics
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
| `docs/phase_notes/phase_4_scenarios.md` | Phase 4 scenario/model comparison rules, outputs, and evidence |
| `docs/phase_logs/phase_0_terminal_log.md` | Phase 0 terminal commands and results |
| `docs/phase_logs/phase_1_terminal_log.md` | Phase 1 terminal commands and results |
| `docs/phase_logs/phase_1_5_terminal_log.md` | Phase 1.5 terminal commands and results |
| `docs/phase_logs/phase_2_terminal_log.md` | Phase 2 terminal commands and results |
| `docs/phase_logs/phase_3_terminal_log.md` | Phase 3 terminal commands and results |
| `docs/phase_logs/phase_4_terminal_log.md` | Phase 4 terminal commands and results |
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
- Phase 4: Scenario/model comparison — completed as analytical what-if comparison only
- Phase 5: Mathematical optimization
- Phase 6: Operational simulation
- Phase 7: Production-ready application

See `docs/roadmap.md` for detailed status.
