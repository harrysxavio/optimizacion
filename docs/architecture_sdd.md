# Architecture — Slotting Optimization Engine

**Version:** 0.7.0  
**Status:** Phase 5 — Controlled mathematical optimization prototype implemented  
**Last updated:** 2026-05-28

---

## 1. Architectural overview

The engine follows a **modular layered architecture** designed for incremental evolution from descriptive analytics toward prescriptive optimization. Each module has a single responsibility and communicates through well-defined interfaces (Python function calls / class imports — no service bus or RPC in the first cycle).

### Guiding principles

- **Separation of concerns**: data, business logic, features, diagnostics, optimization, and UI are independent packages.
- **No business logic in the UI**: the Streamlit app (Phase 1.5) imports from `data`, `features`, and other modules — it never owns core rules.
- **Prescriptive‑ready design**: feature engineering prepares data structures that later phases can consume without a rewrite.
- **Explicit contracts**: pandera schemas and pydantic models validate data at module boundaries instead of relying on convention.
- **Production evolution**: the structure avoids patterns that would block future hardening (auth, config management, CI/CD).

---

## 2. Module responsibilities

| Module | Responsibility | Phase 0 status | Future scope |
|---|---|---|---|
| `config` | Central paths, environment variables, shared constants | Implemented | May add config file parsing, encryption, profile switching |
| `domain` | Business entities (SKU, Zone, Location, Inventory) | Placeholder stub | Pydantic models, domain services, business invariants |
| `data` | Generation, loading, validation | Placeholder stub | Synthetic data, pandera schemas, CSV/Parquet I/O |
| `features` | Derived analytical features | Placeholder stub | Demand, rotation, utilisation, distance indicators |
| `diagnostics` | Slotting quality diagnostics | Implemented in Phase 2 | Descriptive diagnostic flags; optimization remains deferred |
| `scoring` | Prioritization scoring | Implemented in Phase 3 | Transparent review queue from diagnostic signals; no optimal move recommendation |
| `scenarios` | Scenario/model comparison | Implemented in Phase 4 | Analytical what-if lenses over Phase 3 scores; no solver, target slots, simulation, or movement execution |
| `optimization` | Controlled mathematical optimization prototypes | Implemented in Phase 5 | Future full solver models, location-level feasibility, zone resizing, SKU relocation |
| `simulation` | Operational impact simulation | Placeholder stub (Phase 6) | Labour modelling, what-if scenarios |
| `reporting` | Output generation and summaries | Placeholder stub | PDF/Excel, BI exports |
| `app` | Streamlit technical front-end and pure dashboard helpers | Implemented in Phase 1.5 | Dataset inspection, basic visualisations; production UX remains future |

---

## 3. Data flow (implemented through Phase 5)

```text
Synthetic/raw data (CSV)
        │
        ▼
    ┌─────────────────────┐
    │   data/loading.py    │  reads CSV → pandas DataFrame
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  data/validation.py  │  pandera schema check
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │ data/transformation  │  cleaning, type casting
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │ features/builder.py  │  derived columns
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │   Analytical dataset │  (data/processed/)
    └─────────┬───────────┘
              │
        ┌──────┴───────────────┐
        ▼                      ▼
 diagnostics/rules.py    app/dashboard_data.py
 descriptive flags       pure loading/KPI helpers
        │                      │
        ▼                      ▼
  scoring/prioritization.py     app/streamlit_app.py
  prioritization scores         technical inspection UI
        │
        ▼
  scenarios/comparison.py
  analytical what-if lenses
        │
        ▼
  optimization/assignment.py
  controlled SKU-to-zone assignment
        │
        ▼
  data/processed/*
  score/queue/scenario/optimization CSVs
```

---

## 4. Key decisions

| Decision | Choice | Rationale |
|---|---|---|
| Packaging | `pyproject.toml` with setuptools | Modern Python standard; no extra build tooling needed |
| Package layout | `src/slotting_optimization_engine/` | Standard src-layout prevents accidental imports from the repo root |
| Path management | `config/project_paths.py` with pathlib | Centralises all paths; no scattered `os.path.join`; env-var overrides |
| Data validation | pandera (planned for Phase 1) | Dataframe-first validation; integrates naturally with pandas |
| Linting/format | ruff | Fast, comprehensive, replaces flake8 + isort + black. Pytest assertions are allowed only in tests through a scoped `S101` ignore. |
| UI framework | Streamlit (planned for Phase 1.5) | Fastest path to a visual interface for technical users |
| UI logic split | `dashboard_data.py` owns loading/status/KPI helpers; `streamlit_app.py` renders only | Keeps business and data inspection logic out of the Streamlit script |
| UI design system | `docs/DESIGN.md` | Documents the operational control-tower aesthetic and prevents arbitrary visual drift |
| Diagnostics scope | `diagnostics/rules.py` produces flags and evidence, not recommendations | Phase 2 must remain descriptive and avoid Phase 3 scoring/optimization behavior |
| Scoring scope | `scoring/prioritization.py` produces action-level review priorities only | Phase 3 ranks diagnostic signals but does not select optimal target locations or solve a move plan |
| Scoring weights | Dataclass config with transparent weights marked `inferred / pending confirmation` | Keeps business assumptions visible until confirmed by operations stakeholders |
| Scenario comparison scope | `scenarios/comparison.py` re-ranks Phase 3 scores under named analytical lenses | Phase 4 compares assumptions without optimization, simulation, target slot assignment, or automatic SKU move execution |
| Phase 5 solver | SciPy `linear_sum_assignment` if available, deterministic greedy fallback otherwise | Keeps the prototype small and transparent while recording the method used in outputs |
| Optimization scope | Zone-level SKU assignment only | Avoids pretending to guarantee physical slot feasibility or executable move plans before Phase 6+ requirements exist |

---

## 5. Testing strategy

| Layer | Tool | Scope | Phase |
|---|---|---|---|
| Unit tests | pytest | Individual functions, validation logic, feature calculations | Phase 0+ |
| Structure tests | pytest | Package imports, expected files/dirs | Phase 0 |
| Integration tests | pytest | Cross-module data pipeline | Phase 1+ |
| Manual verification | Streamlit inspection | Visual data quality check | Phase 1.5+ |
| CLI verification | `scripts/run_diagnostics.py` | Diagnostic output generation | Phase 2 |
| CLI verification | `scripts/run_scoring.py` | Scoring output generation | Phase 3 |
| CLI verification | `scripts/run_scenarios.py` | Scenario comparison output generation | Phase 4 |
| CLI verification | `scripts/run_optimization.py` | Controlled SKU-to-zone assignment output generation | Phase 5 |

### Phase 0 tests

- `test_project_structure.py` — verifies all packages import correctly and expected files/directories exist.

---

## 6. Deferred work

The following architectural items are intentionally deferred:

- **CI/CD pipeline**: No GitHub Actions, pre-commit hooks, or deployment config until Phase 7.
- **Logging framework**: Phase 0 uses print-level awareness only. Structured logging is deferred to Phase 3+.
- **Configuration file parsing**: Phase 0 uses env vars. YAML/TOML config files are deferred.
- **Dependency injection**: Not needed for the first cycle. If modules grow, consider simple DI in Phase 3+.
- **API layer**: No FastAPI/Flask in the first cycle. The Streamlit app is the only interface.
- **Database connectors**: All data in Phase 1 comes from CSV. Real WMS/ERP connectors are Phase 7.
- **Authentication/authorization**: Deferred to Phase 7.
- **Production application UX**: The app remains a technical inspection surface only; recommendations, scenario simulation, auth, and deployment remain deferred.
- **Advanced mathematical optimization**: Phase 5 is a bounded zone-level prototype only. Location-level feasibility, executable move plans, automatic movement execution, and simulation remain deferred.

---

## 7. Future architectural evolution

```text
Phase 0-1:  Descriptive analytics — synthetic data, features, inspection
                 │
                 ▼
Phase 2-3:  Diagnostics + prescriptive scoring
                 │
                 ▼
Phase 4-5:  Scenario comparison + mathematical optimization
                 │
                 ▼
Phase 6-7:  Simulation + production hardening
```
