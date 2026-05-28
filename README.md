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
| ¿Qué zona candidata sugiere un prototipo matemático para SKUs priorizados? | Asignación SKU→zona Phase 5, sin ejecución física |

## Qué puede hacer hoy, hasta Phase 5

| Fase | Qué hace | Qué produce |
|---|---|---|
| Phase 1 | Genera datos sintéticos, valida contratos y construye features | Tablas de SKUs, demanda, utilización y features |
| Phase 1.5 | Muestra una UI técnica mínima en Streamlit | Inspección visual de outputs procesados |
| Phase 2 | Detecta diagnósticos descriptivos | Flags por SKU, ubicación, zona y categoría |
| Phase 3 | Prioriza oportunidades para revisión humana | Scores y cola de revisión |
| Phase 4 | Compara lentes analíticos what-if | Ranking comparativo por escenario/modelo simple |
| Phase 5 | Calcula una asignación matemática controlada SKU→zona | CSV de asignaciones, resumen y matriz de costos |

---

## Diagramas de flujo por proceso

Para entender qué hace cada fase, mirá estos diagramas. Cada uno muestra **qué entra**, **qué se hace** y **qué sale**.

### Phase 1 — Generación de datos y features

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: DATOS Y FEATURES                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                           │
│  │  Generator   │  Genera 500 SKUs, 10 zonas, 200          │
│  │  (numpy)     │  ubicaciones, inventario, pedidos         │
│  └──────┬───────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                           │
│  │  Validator   │  Revisa contratos: IDs únicos, tipos,     │
│  │  (pandera)   │  claves foráneas, valores válidos         │
│  └──────┬───────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                           │
│  │  Loader      │  Lee CSVs validados y los convierte       │
│  │  (pandas)    │  en DataFrames listos para usar            │
│  └──────┬───────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                           │
│  │  Builder     │  Calcula demanda por SKU, utilización     │
│  │  (features)  │  por ubicación/zona, scores de alineación │
│  └──────┬───────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  OUTPUTS:                                             │   │
│  │  • slotting_features.parquet  (tabla amplia por SKU)  │   │
│  │  • location_utilization.csv   (utilización % por ubi) │   │
│  │  • zone_utilization.csv       (resumen por zona)      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Script: python scripts/generate_sample_data.py             │
│          python scripts/run_data_validation.py              │
│          python scripts/build_features.py                   │
└─────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Este paso crea un "mundo ficticio" de datos para practicar sin tocar información real. Los features son señales básicas como "¿cuánto se pide este SKU?" o "¿qué tan llenas están las zonas?".

---

### Phase 2 — Diagnósticos descriptivos

```
┌─────────────────────────────────────────────────────────────┐
│                   PHASE 2: DIAGNÓSTICOS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Entradas (de Phase 1):                                     │
│  • slotting_features.parquet                                │
│  • location_utilization.csv                                 │
│  • zone_utilization.csv                                     │
│                                                             │
│         ┌──────────────┐                                    │
│         │    Rules     │  Aplica reglas descriptivas:       │
│         │  (diagnostics│  "¿Este SKU de alta demanda está   │
│         │   rules.py)  │   lejos de la zona prioritaria?"   │
│         └──────┬───────┘  "¿Slow movers en zona premium?"  │
│                │        "¿Zona con capacidad al límite?"    │
│                │                                            │
│                ▼                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FLAGS POR:                                          │   │
│  │  • SKU (ubicación, demanda, patrón de movimiento)    │   │
│  │  • Ubicación (utilización, densidad)                 │   │
│  │  • Zona (capacidad, mezcla de categorías)            │   │
│  │  • Categoría (dispersión, dominancia)                 │   │
│  └──────┬───────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  OUTPUTS:                                            │   │
│  │  • slotting_diagnostics.csv    (1 fila por SKU)      │   │
│  │  • location_diagnostics.csv    (1 fila por ubicación)│   │
│  │  • zone_diagnostics.csv        (1 fila por zona)     │   │
│  │  • category_diagnostics.csv    (1 fila por categoría)│   │
│  │  • diagnostic_summary.csv      (conteo de problemas) │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Script: python scripts/run_diagnostics.py                  │
└─────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Phase 2 es como un "check-up" del depósito. No dice qué mover, solo marca qué se ve raro o merece atención. Los pesos están marcados como `inferred / pending confirmation` porque son supuestos, no reglas confirmadas.

---

### Phase 3 — Scoring y priorización

```
┌─────────────────────────────────────────────────────────────┐
│                PHASE 3: SCORING Y COLA                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Entradas (de Phase 2):                                     │
│  • slotting_diagnostics.csv                                 │
│  • zone_diagnostics.csv                                     │
│  • category_diagnostics.csv                                 │
│                                                             │
│         ┌──────────────┐                                    │
│         │   Scoring    │  Cruza señales de Phase 2 con      │
│         │  (scoring/   │  pesos transparentes:              │
│         │ prioritization  • Demanda: 30%                    │
│         │   .py)       │  • Distancia: 25%                  │
│         └──────┬───────┘  • Capacidad: 25%                  │
│                │        • Oportunidad: 20%                   │
│                │        (pesos inferidos, NO confirmados)   │
│                ▼                                            │
│         ┌──────────────┐                                    │
│         │  Priority    │  Ordena de mayor a menor score      │
│         │  Queue       │  y arma una cola para revisión      │
│         └──────┬───────┘  humana                            │
│                │                                            │
│                ▼                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  OUTPUTS:                                            │   │
│  │  • slotting_opportunity_scores.csv (1 fila/opción)   │   │
│  │  • priority_recommendation_queue.csv (top-N ordenado)│   │
│  │  • scoring_summary.csv (métricas y config)           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Script: python scripts/run_scoring.py                      │
└─────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Phase 3 arma una "lista de tareas ordenada" para que un humano sepa por dónde empezar a revisar. **No optimiza**, solo prioriza. Los pesos son supuestos que hay que confirmar con expertos del negocio.

---

### Phase 4 — Comparación de escenarios

```
┌─────────────────────────────────────────────────────────────┐
│              PHASE 4: ESCENARIOS WHAT-IF                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Entradas (de Phase 3):                                     │
│  • slotting_opportunity_scores.csv                          │
│  • priority_recommendation_queue.csv                        │
│                                                             │
│         ┌──────────────┐                                    │
│         │   Baseline   │  "Si no cambiamos nada, ¿cómo      │
│         │              │   se ve la prioridad?"              │
│         └──────┬───────┘                                    │
│                │                                            │
│         ┌──────┴───────┐                                    │
│         │  Demanda     │  "¿Qué pasa si priorizamos SKUs    │
│         │  primero     │  de alta demanda?"                 │
│         └──────┬───────┘                                    │
│                │                                            │
│         ┌──────┴───────┐                                    │
│         │  Capacidad   │  "¿Qué pasa si primero liberamos   │
│         │  primero     │  espacio en zonas llenas?"         │
│         └──────┬───────┘                                    │
│                │                                            │
│         ┌──────┴───────┐                                    │
│         │  Revisión    │  "¿Qué pasa si balanceamos ambos?" │
│         │  balanceada  │                                    │
│         └──────┬───────┘                                    │
│                │                                            │
│                ▼                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  COMPARA: score promedio, high priority, foco,       │   │
│  │  cobertura de acciones por escenario                 │   │
│  └──────┬───────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  OUTPUTS:                                            │   │
│  │  • scenario_comparison.csv   (top-N por escenario)   │   │
│  │  • scenario_action_mix.csv   (mezcla de acciones)    │   │
│  │  • scenario_summary.csv      (métricas comparables)  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Script: python scripts/run_scenarios.py                    │
└─────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Phase 4 es como mirar el mismo depósito desde 4 ángulos diferentes. No dice cuál es "el mejor", solo muestra qué cambia cuando cambian las prioridades. Útil para debates con el equipo operativo.

---

### Phase 5 — Asignación matemática controlada

```
┌─────────────────────────────────────────────────────────────┐
│            PHASE 5: ASIGNACIÓN SKU → ZONA                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Entradas:                                                  │
│  • priority_recommendation_queue.csv  (de Phase 3)          │
│  • slotting_diagnostics.csv           (de Phase 2)          │
│  • scenario_comparison.csv            (de Phase 4)          │
│  • skus.csv / zones.csv               (de Phase 1)          │
│                                                             │
│         ┌──────────────┐                                    │
│         │   Selector   │  Toma los top-N SKUs de la cola    │
│         │   (top-N)    │  de priorización                   │
│         └──────┬───────┘                                    │
│                │                                            │
│                ▼                                            │
│         ┌──────────────┐                                    │
│         │  Zone        │  Expande zonas en "slots lógicos"  │
│         │  Expander    │  (ej: zona A → slot A.1, A.2, A.3)│
│         └──────┬───────┘                                    │
│                │                                            │
│                ▼                                            │
│         ┌──────────────┐                                    │
│         │  Cost Matrix │  Calcula costo para cada par       │
│         │  Builder     │  SKU × zona_slot:                  │
│         └──────┬───────┘  • Demanda (peso alto)            │
│                │           • Distancia (penaliza lejanía)   │
│                │           • Capacidad (penaliza saturación) │
│                │           • Oportunidad (score de Phase 3)  │
│                │           • Contexto de escenario           │
│                │           (pesos inferidos, NO confirmados) │
│                ▼                                            │
│         ┌──────────────┐                                    │
│         │    Solver    │  Resuelve la asignación de menor   │
│         │              │  costo total:                      │
│         └──────┬───────┘                                    │
│                │                                            │
│     ┌──────────┴──────────┐                                 │
│     │                     │                                 │
│     ▼                     ▼                                 │
│ ┌────────┐        ┌──────────────┐                          │
│ │ SciPy  │        │   Greedy     │                          │
│ │ linear │        │  Fallback    │                          │
│ │ _sum_  │        │ (determi-    │                          │
│ │assign- │        │  nístico)    │                          │
│ │  ment  │        └──────┬───────┘                          │
│ └───┬────┘               │                                  │
│     │                    │                                  │
│     └──────────┬─────────┘                                  │
│                │                                            │
│                ▼                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  OUTPUTS:                                            │   │
│  │  • optimization_assignments.csv (1 assign por SKU)   │   │
│  │  • optimization_summary.csv     (método, costo, cant)│   │
│  │  • optimization_cost_matrix.csv (costo por combinac.)│   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ⚠️  PROTOTIPO: No ejecuta movimientos, no valida          │
│     factibilidad física, no conecta WMS/ERP.               │
│                                                             │
│  Script: python scripts/run_optimization.py                 │
└─────────────────────────────────────────────────────────────┘
```

**Qué aprendés:** Phase 5 es la primera vez que el motor "decide" algo, pero es una decisión **analítica**, no operativa. Asigna SKUs a zonas candidatas minimizando un costo matemático. **No es una orden de mover productos.** Si SciPy no está instalado, usa un fallback greedy determinístico (siempre da el mismo resultado).

---

### Flujo completo de las 5 fases

```
┌─────────────────────────────────────────────────────────────┐
│                  FLUJO COMPLETO                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ Phase 1 │───▶│ Phase 2 │───▶│ Phase 3 │                 │
│  │ Datos + │    │Diagnóst│    │ Scoring │                   │
│  │Features │    │   ics   │    │  Queue  │                  │
│  └─────────┘    └─────────┘    └────┬────┘                  │
│                                     │                       │
│                                     ▼                       │
│                              ┌─────────┐                    │
│                              │ Phase 4 │                    │
│                              │Escenarios│                   │
│                              └────┬────┘                    │
│                                   │                         │
│                                   ▼                         │
│                            ┌──────────┐                     │
│                            │ Phase 5  │                     │
│                            │Asignación│                     │
│                            └──────────┘                     │
│                                                             │
│  Cada fase produce archivos CSV que la siguiente consume.   │
│  No podés saltar fases: cada una necesita los outputs       │
│  de la anterior.                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Herramientas usadas por capa

| Capa explicada | Herramienta/librería | Qué hace en simple | Dónde aparece |
|---|---|---|---|
| Base del proyecto | Python | Lenguaje principal para construir el motor modular | `src/`, `scripts/`, `tests/` |
| Tablas y transformaciones | pandas | Lee CSV/Parquet y cruza SKUs, zonas, inventario, diagnósticos y scores | `data/loading.py`, `features/builder.py`, `diagnostics/`, `scoring/`, `scenarios/`, `optimization/` |
| Validación de datos | pandera | Define contratos de columnas, tipos y reglas; si falla, hay fallback explícito | `data/validation.py` |
| Cálculo numérico | numpy | Genera datos sintéticos reproducibles y ayuda con cálculos vectorizados | `data/generator.py`, `optimization/assignment.py` |
| Optimización matemática | scipy `linear_sum_assignment` | Resuelve la asignación rectangular de menor costo si SciPy está instalado | `optimization/assignment.py`; si no está disponible, usa fallback greedy documentado |
| UI técnica | Streamlit | Permite inspeccionar outputs procesados sin crear una app final de negocio | `app/streamlit_app.py` |
| Tests | pytest | Verifica generación, validación, features, diagnósticos, scoring, escenarios y optimización | `tests/unit/` |
| Lint/calidad | ruff | Revisa estilo, imports, errores simples y reglas de seguridad básicas | `python -m ruff check src tests scripts` |
| Mapa de relaciones | Graphify | Mantiene un grafo del proyecto para ver conexiones entre módulos, docs y outputs | `graphify-out/`, consultas registradas en `docs/phase_logs/` |
| Gobierno documental | Markdown docs/data governance | Deja trazabilidad humana: contratos, supuestos, logs, reglas inferidas y pendientes | `README.md`, `docs/`, `docs/data/` |

## Qué NO deberías decidir a ciegas

- No muevas SKUs automáticamente usando estos CSV.
- No trates un score alto como una orden operativa.
- No interpretes los escenarios ni la asignación Phase 5 como solución óptima operativa.
- No cambies layout, dotación o capacidad sin validar con operación real.
- No uses estos pesos como política de negocio hasta confirmarlos con expertos.
- No ejecutes movimientos de SKU automáticamente usando `optimization_assignments.csv`.

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
python scripts/run_optimization.py

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
| `run_optimization.py` | Construye una asignación matemática controlada SKU→zona; no ejecuta movimientos ni garantiza slot físico |

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
- `data/processed/optimization_assignments.csv`
- `data/processed/optimization_summary.csv`
- `data/processed/optimization_cost_matrix.csv`

## Cómo leer los outputs de Phase 4

| Archivo | Cómo leerlo |
|---|---|
| `scenario_comparison.csv` | Top N por escenario con ranking recalculado según el lente analítico |
| `scenario_action_mix.csv` | Cuánta mezcla de acciones aparece en cada escenario |
| `scenario_summary.csv` | Métricas comparables: score promedio, high priority, foco SKU/zona y cobertura de acciones |

## Cómo leer los outputs de Phase 5

| Archivo | Cómo leerlo |
|---|---|
| `optimization_assignments.csv` | Una asignación candidata SKU→zona/slot lógico para SKUs priorizados; es recomendación analítica, no orden de movimiento |
| `optimization_summary.csv` | Método usado (`scipy_linear_sum_assignment` o `greedy_fallback`), cantidad de SKUs, zonas usadas y costo total/promedio |
| `optimization_cost_matrix.csv` | Costos transparentes por combinación SKU-zona-slot, con demanda, distancia, prioridad, presión de capacidad y contexto de scoring |

Caveat clave: Phase 5 es un prototipo matemático acotado sobre datos sintéticos. No es un optimizador warehouse-grade, no valida factibilidad a nivel ubicación, no conecta WMS/ERP y no ejecuta movimientos.

## Posibles usos actuales

- Preparar una conversación con operación sobre dónde revisar primero.
- Comparar si el backlog se ve distinto cuando priorizás demanda o capacidad.
- Documentar supuestos antes de pedir datos reales.
- Diseñar una futura fase de optimización con mejores requisitos.

## Posibilidades futuras

Las fases futuras podrían agregar simulación operativa, conectores WMS/ERP, autenticación, despliegue y una app de negocio. Eso todavía NO está implementado.

Caveat clave: Phase 5 asigna SKUs a zonas candidatas con un modelo pequeño y transparente. No calcula ubicaciones físicas exactas, no garantiza capacidad real, no simula operación y no ejecuta movimientos de SKUs.

# Slotting Optimization Engine

A modular Python engine for slotting optimization in high-volume e-commerce and retail distribution centers. Built in controlled phases, it evolves from descriptive analytics toward prescriptive optimization.

## Current scope

**Phase 0 completed** — project skeleton, architecture, base documentation, and configuration established.
**Phase 1 completed** — synthetic data pipeline, validation, and feature builder.  
**Phase 1.5 completed** — minimal technical Streamlit front for inspecting processed outputs.  
**Phase 2 completed** — descriptive advanced slotting diagnostics and diagnostic output files.  
**Phase 3 completed** — transparent scoring/prioritization queue from Phase 2 diagnostics.  
**Phase 4 completed** — analytical scenario/model comparison from Phase 3 scores.  
**Phase 5 completed** — controlled mathematical SKU-to-zone assignment prototype; no execution or location-level feasibility guarantee.

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
│       ├── optimization/              # Controlled assignment optimization prototype (Phase 5)
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

## Phase 5 controlled optimization prototype

Run Phase 5 after Phase 4 scenario outputs exist:

```powershell
python scripts/run_optimization.py
```

Phase 5 builds a small SKU-to-zone assignment prototype using top-N SKU candidates from the Phase 3 queue, Phase 4 scenario context, diagnostics, and synthetic SKU/zone dimensions. If SciPy is installed, it uses `scipy.optimize.linear_sum_assignment`; otherwise it records a deterministic `greedy_fallback` method in the outputs.

Expected outputs:

- `data/processed/optimization_assignments.csv`
- `data/processed/optimization_summary.csv`
- `data/processed/optimization_cost_matrix.csv`

These outputs are analytical only. They are not WMS tasks, not automatic move instructions, and not guaranteed feasible at physical location level.

## Output structure

After running Phase 1 through Phase 5 scripts:

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
    ├── scenario_summary.csv                # Phase 4 scenario-level metrics
    ├── optimization_assignments.csv        # Phase 5 SKU-to-zone assignments
    ├── optimization_summary.csv            # Phase 5 method/cost summary
    └── optimization_cost_matrix.csv        # Phase 5 transparent cost matrix
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
| `docs/phase_notes/phase_5_optimization.md` | Phase 5 optimization prototype rules, outputs, caveats, and evidence |
| `docs/phase_logs/phase_0_terminal_log.md` | Phase 0 terminal commands and results |
| `docs/phase_logs/phase_1_terminal_log.md` | Phase 1 terminal commands and results |
| `docs/phase_logs/phase_1_5_terminal_log.md` | Phase 1.5 terminal commands and results |
| `docs/phase_logs/phase_2_terminal_log.md` | Phase 2 terminal commands and results |
| `docs/phase_logs/phase_3_terminal_log.md` | Phase 3 terminal commands and results |
| `docs/phase_logs/phase_4_terminal_log.md` | Phase 4 terminal commands and results |
| `docs/phase_logs/phase_5_terminal_log.md` | Phase 5 terminal commands and results |
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
- Phase 5: Mathematical optimization — completed as controlled SKU-to-zone prototype only
- Phase 6: Operational simulation
- Phase 7: Production-ready application

See `docs/roadmap.md` for detailed status.
