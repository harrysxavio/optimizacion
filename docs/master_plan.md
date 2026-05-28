# Master Plan — slotting-optimization-engine

**Project:** `slotting-optimization-engine`  
**Plan version:** `v0.2.0`  
**Last updated:** 2026-05-27  
**Status:** Phase 0, Phase 0-D, Phase 1, Phase 1-D, Phase 1.5, and Phase 1.5-D completed.  
**Scope of this update:** Phase 1.5 technical Streamlit front and Phase 1.5-D documentation.

---

## 1. Objective

Build, in controlled phases, a modular and production-evolvable Python engine for slotting optimization in a high-volume e-commerce/retail distribution center.

The long-term system should move beyond descriptive SQL/BI indicators and become an analytical-prescriptive engine able to:

- Diagnose SKU-location misalignment.
- Identify overused and underused zones.
- Detect high-demand SKUs located far from priority areas.
- Detect low-rotation SKUs occupying premium zones.
- Analyze category grouping quality.
- Evaluate location density, volume usage, weight usage, and capacity.
- Recommend zone resizing opportunities.
- Compare alternative slotting scenarios.
- Estimate operational impact.
- Prepare the base for mathematical optimization.

---

## 2. Business context

The project models a high-volume retail/e-commerce distribution center, similar in operational complexity to marketplaces or large omnichannel retailers.

The future engine must reason about:

- SKUs and categories.
- Physical locations.
- Storage zones.
- Volume, weight, and capacity restrictions.
- Demand variability.
- Fill rate.
- Rotation and picking frequency.
- Product affinity.
- Operational impact of SKU prioritization.
- Logical layout quality.

The first delivery must create a clean technical foundation, not the final optimizer.

---

## 3. Current scope

Only the following phases are in scope for the first implementation cycle:

| Phase | Name | Scope status | Implementation status |
|---|---|---|---|
| 0 | Design, architecture, initial configuration, base documentation | In scope | Completed |
| 0-D | Documentation, explanation, and traceability for Phase 0 | In scope | Completed |
| 1 | Synthetic data, loading, validation, transformation, initial feature builder | In scope | Completed |
| 1-D | Documentation, explanation, and traceability for Phase 1 | In scope | Completed |
| 1.5 | Minimal technical Streamlit front | In scope | Completed |
| 1.5-D | Documentation, explanation, and traceability for Phase 1.5 | In scope | Completed |

Phase 0 (design, architecture, base docs) and Phase 0-D (documentation and traceability) have been completed. No functional implementation beyond project structure and configuration was performed.

---

## 4. Future scope

The following capabilities are intentionally deferred and must not be implemented during the first cycle except as clearly marked future stubs or folders:

| Future phase | Capability | Status |
|---|---|---|
| 2 | Advanced slotting diagnostics | Future |
| 3 | Prescriptive scoring and prioritization | Future |
| 4 | Scenario/model comparison | Future |
| 5 | Mathematical optimization | Future |
| 6 | Operational simulation | Future |
| 7 | Production-ready application | Future |

Deferred capabilities include advanced recommendations, real optimization, simulation, production deployment, authentication, real WMS/ERP integrations, and final business UX.

---

## 5. Guiding principles

| Principle | Decision |
|---|---|
| Controlled scope | Implement only Phases 0, 1, and 1.5 in the first cycle. |
| Modular architecture | Keep data, domain, features, diagnostics, optimization, simulation, reporting, and app concerns separated. |
| Production evolution | Start simple, but avoid structures that block future production hardening. |
| Traceability | Every relevant decision must update this master plan. |
| Testability | Functional phases must include tests or explicit verification evidence. |
| Documentation-first phase closure | No phase is complete until its documentation and logs are updated. |
| No hidden business logic in UI | Streamlit must call reusable modules instead of owning core business rules. |
| Prescriptive-ready design | Even early descriptive features should prepare future diagnostics and optimization. |

---

## 6. Proposed project structure

```text
slotting-optimization-engine/
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
├── docs/
│   ├── master_plan.md
│   ├── architecture_sdd.md
│   ├── data_contract.md
│   ├── roadmap.md
│   ├── phase_notes/
│   │   ├── phase_0_design_and_setup.md
│   │   ├── phase_1_data_pipeline.md
│   │   └── phase_1_5_streamlit_front.md
│   └── phase_logs/
│       ├── phase_0_terminal_log.md
│       ├── phase_1_terminal_log.md
│       └── phase_1_5_terminal_log.md
├── scripts/
│   ├── generate_sample_data.py
│   ├── run_data_validation.py
│   └── build_features.py
├── src/
│   └── slotting_optimization_engine/
│       ├── __init__.py
│       ├── config/
│       ├── data/
│       ├── domain/
│       ├── features/
│       ├── diagnostics/
│       ├── optimization/
│       ├── simulation/
│       ├── reporting/
│       └── app/
├── tests/
│   ├── unit/
│   └── integration/
└── notebooks/
```

Folders for future phases may exist as placeholders, but they must be clearly marked as future work and must not contain advanced logic during the first cycle.

---

## 7. Initial architecture direction

```text
Synthetic/raw data
        ↓
Data loading
        ↓
Data contract validation
        ↓
Data transformation
        ↓
Feature builder
        ↓
Analytical dataset
        ↓
Technical Streamlit inspection UI
        ↓
Future diagnostics, scenarios, optimization, simulation, recommendations
```

### Main modules

| Module | Purpose | Current-cycle responsibility |
|---|---|---|
| `config` | Central configuration | Paths, constants, environment-safe defaults. |
| `domain` | Business/domain concepts | SKU, zone, location concepts and future domain rules. |
| `data` | Data generation, loading, validation | Synthetic data and contract validation. |
| `features` | Analytical feature construction | Initial demand, rotation, utilization, and density features. |
| `diagnostics` | Slotting diagnostics | Future stub only in first cycle. |
| `optimization` | Mathematical optimization | Future stub only in first cycle. |
| `simulation` | Operational simulation | Future stub only in first cycle. |
| `reporting` | Outputs and summaries | Basic reusable summaries if needed. |
| `app` | Streamlit technical UI | Minimal visual inspection front. |

---

## 8. Technical decisions

| Area | Decision | Reason | Status |
|---|---|---|---|
| Language | Python 3.11+ | Strong ecosystem for data, optimization, apps, and testing. | Proposed |
| Packaging | `pyproject.toml` | Modern Python project standard. | Proposed |
| Dataframes | pandas | Simple, familiar, enough for the first cycle. | Proposed |
| Validation | pandera and/or pydantic | Explicit contracts prevent silent bad data. Final choice to confirm in Phase 0. | Proposed |
| Testing | pytest | Simple and widely adopted. | Proposed |
| UI | Streamlit | Fast technical front for validating the tool visually. | Proposed |
| Lint/format | ruff | Lightweight quality gate; pytest `assert` syntax is allowed only under `tests/**/*.py` via `S101` per-file ignore. | Implemented in Phase 0 |
| Future optimization | OR-Tools, Pyomo, scipy candidates | Solver choice must wait until optimization requirements are clearer. | Deferred |

Any change to these decisions must update this file and the affected documentation.

---

## 9. Data scope for Phase 1

### Synthetic datasets

| Dataset | Description |
|---|---|
| `skus` | Product/SKU master data. |
| `zones` | Logical warehouse zones. |
| `locations` | Physical storage locations linked to zones. |
| `inventory` | Current inventory by SKU and location. |
| `orders` | Synthetic demand header data. |
| `order_lines` | Synthetic order lines for demand and picking frequency. |

### Initial fields

| Entity | Candidate fields |
|---|---|
| SKU | `sku_id`, `category`, `subcategory`, `unit_volume`, `unit_weight`, `rotation_class`, `avg_daily_demand`. |
| Zone | `zone_id`, `zone_type`, `priority_level`, `distance_to_dispatch`, `max_volume_capacity`, `max_weight_capacity`. |
| Location | `location_id`, `zone_id`, `aisle`, `rack`, `level`, `max_volume_capacity`, `max_weight_capacity`. |
| Inventory | `sku_id`, `location_id`, `units_on_hand`, `occupied_volume`, `occupied_weight`. |
| Orders | `order_id`, `order_date`, `channel`. |
| Order lines | `order_id`, `sku_id`, `quantity`. |

### Initial features

- Demand by SKU.
- Picking frequency by SKU.
- SKU volume and weight footprint.
- Location capacity utilization.
- Zone capacity utilization.
- Basic rotation classification.
- Relative distance indicators.
- Preliminary alignment indicators, only if explicitly marked as initial and non-prescriptive.

---

## 10. Data validation rules

Minimum validations for Phase 1:

- Required IDs must not be null.
- Master keys must be unique where expected.
- Capacities must be greater than zero.
- SKU volume and weight must be greater than zero.
- Inventory quantities must be non-negative.
- Inventory SKUs must exist in the SKU master.
- Inventory locations must exist in the location master.
- Locations must reference valid zones.
- Order lines must reference valid orders and SKUs.
- Generated feature outputs must not silently drop critical records.

These rules are documented in `docs/data_contract.md` and enforced by the
two-tier validation system in `src/slotting_optimization_engine/data/validation.py`.

**Validation implementation:** Two-tier strategy — pandera DataFrameModel schemas
(Tier 1) with explicit pandas-based fallback (Tier 2) when pandera is unavailable.
This ensures validation never silently degrades.

---

## 11. Phase plan

### Phase 0 — Design, architecture, setup, documentation base

**Goal:** Create the initial project skeleton and foundational documentation.

**Expected deliverables:**

- Base folder structure.
- `README.md`.
- `pyproject.toml`.
- `.gitignore`.
- `.env.example`.
- `docs/master_plan.md`.
- `docs/architecture_sdd.md`.
- `docs/data_contract.md`.
- `docs/roadmap.md`.
- `docs/phase_notes/phase_0_design_and_setup.md`.
- `docs/phase_logs/phase_0_terminal_log.md`.

**Acceptance criteria:**

- Project structure exists.
- Base docs exist.
- Setup commands are documented.
- Phase 0 log records commands and outcomes.
- No advanced future logic is implemented.

### Phase 0-D — Documentation and traceability

**Goal:** Explain what was created, why, how to run it, and what remains pending.

**Required updates:**

- `docs/master_plan.md`
- `README.md`
- `docs/architecture_sdd.md`
- `docs/phase_notes/phase_0_design_and_setup.md`
- `docs/phase_logs/phase_0_terminal_log.md`

### Phase 1 — Synthetic data pipeline and feature builder

**Goal:** Generate, load, validate, transform, and build initial analytical features from synthetic data.

**Expected deliverables:**

- `scripts/generate_sample_data.py`
- `scripts/run_data_validation.py`
- `scripts/build_features.py`
- Data modules under `src/slotting_optimization_engine/data/`.
- Feature modules under `src/slotting_optimization_engine/features/`.
- Unit tests for core functions.
- Processed feature output in `data/processed/`.

**Acceptance criteria:**

- Synthetic data generation works.
- Validation detects basic data contract failures.
- Feature builder produces expected outputs.
- Tests pass or limitations are documented.
- Documentation and logs are updated.

### Phase 1-D — Documentation and traceability

**Required updates:**

- `docs/master_plan.md`
- `README.md`
- `docs/data_contract.md`
- `docs/phase_notes/phase_1_data_pipeline.md`
- `docs/phase_logs/phase_1_terminal_log.md`

### Phase 1.5 — Minimal technical Streamlit front

**Goal:** Provide a simple visual interface to inspect synthetic and processed data.

**Expected deliverables:**

- Streamlit entrypoint, preferably `src/slotting_optimization_engine/app/streamlit_app.py`.
- Basic dataset summary views.
- Basic utilization, demand, and rotation visuals.
- Clear error messages when required data files do not exist.
- Reusable functions outside the Streamlit script where possible.
- Lightweight design system documentation for the technical UI.

**Acceptance criteria:**

- Streamlit app is implemented; runtime launch requires optional `streamlit` dependency.
- App displays processed data or tells the user how to generate it.
- UI does not contain core business logic.
- Documentation and logs are updated.

### Phase 1.5-D — Documentation and traceability

**Required updates:**

- `docs/master_plan.md`
- `README.md`
- `docs/phase_notes/phase_1_5_streamlit_front.md`
- `docs/phase_logs/phase_1_5_terminal_log.md`
- `docs/architecture_sdd.md`
- `docs/roadmap.md`
- `docs/DESIGN.md`

---

## 12. Required phase-note template

Every file under `docs/phase_notes/` must include:

1. What was implemented.
2. What files were created.
3. What each file is for.
4. How the flow works.
5. Main functions/classes.
6. Technical decisions.
7. Assumptions.
8. Remaining limitations.
9. What is missing for the next phase.
10. How to run related scripts.
11. Expected output.
12. Common errors.
13. How to resolve common errors.
14. Tests covering the phase.
15. Evidence that the phase works.

---

## 13. Terminal log standard

Terminal logs must be stored under `docs/phase_logs/`.

Required format:

````markdown
# Phase X Terminal Log

## Command

```bash
<command>
```

## Result

<result>

## Errors

<errors or "No errors">

## Resolution

<resolution or "No resolution required">

## Final Status

<final status>
````

If a command cannot be executed, the log must explicitly say so.

### Current log status

| Log | Status |
|---|---|
| `docs/phase_logs/phase_0_terminal_log.md` | Created. Phase 0 setup and structure tests were executed and recorded. |
| `docs/phase_logs/phase_1_terminal_log.md` | Created. Phase 1 generation, validation, feature build, lint, and tests were executed and recorded. |
| `docs/phase_logs/phase_1_5_terminal_log.md` | Created. Phase 1.5 feature build, lint, tests, smoke import, Streamlit dependency check, and Graphify commands were recorded. |

---

## 14. Planned commands

These commands describe the standard project workflow. Phase 0, Phase 1, and Phase 1.5 verification commands were executed and recorded in their phase logs.

### Environment setup

```bash
python -m venv .venv
pip install -e ".[dev]"
```

PowerShell activation example:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Generate synthetic data

```bash
python scripts/generate_sample_data.py
```

### Validate data

```bash
python scripts/run_data_validation.py
```

### Build features

```bash
python scripts/build_features.py
```

### Run tests

```bash
pytest
```

### Run technical Streamlit front

```bash
streamlit run src/slotting_optimization_engine/app/streamlit_app.py
```

---

## 15. Mandatory traceability rules

If any relevant decision changes, update the required documents before marking a phase complete.

| Change type | Required updates |
|---|---|
| Folder structure | `docs/master_plan.md`, `docs/architecture_sdd.md`, related phase note |
| Library choice | `docs/master_plan.md`, `README.md`, related phase note |
| Script name | `docs/master_plan.md`, `README.md`, related phase note |
| Data contract | `docs/master_plan.md`, `docs/data_contract.md`, related phase note |
| Execution flow | `docs/master_plan.md`, `README.md`, related phase note |
| Validation criterion | `docs/master_plan.md`, `docs/data_contract.md`, related phase note |
| Phase scope | `docs/master_plan.md`, `docs/roadmap.md`, related phase note |
| How to run the project | `docs/master_plan.md`, `README.md`, related phase log |

No phase can be considered complete if `docs/master_plan.md` is outdated.

---

## 16. Code comment rules

The implementation must include clear, useful, moderate comments.

Comments should explain:

- Why a function exists.
- What business rule a validation represents.
- What future phase a piece of code prepares.
- What trade-off is being accepted.
- What operational assumption is being used.
- What must evolve later.

Comments should avoid:

- Restating obvious code.
- Noise without technical or business value.
- Outdated explanations.

The code should be understandable to someone learning Python without sacrificing good engineering practices.

---

## 17. Documentation references

| Document | Purpose | Status |
|---|---|---|
| `docs/master_plan.md` | Living project guide and traceability source | Updated (Phase 1.5) |
| `README.md` | Project usage and quick start | Updated (Phase 1.5) |
| `docs/architecture_sdd.md` | Technical architecture and SDD decisions | Updated (Phase 1.5) |
| `docs/data_contract.md` | Data entities, fields, validations, assumptions | Updated (Phase 1 — finalised) |
| `docs/roadmap.md` | Detailed project roadmap | Updated (Phase 1.5) |
| `docs/phase_notes/phase_0_design_and_setup.md` | Phase 0 explanation and evidence | Created (Phase 0) |
| `docs/phase_notes/phase_1_data_pipeline.md` | Phase 1 explanation and evidence | Created (Phase 1) |
| `docs/phase_notes/phase_1_5_streamlit_front.md` | Phase 1.5 explanation and evidence | Created (Phase 1.5) |
| `docs/DESIGN.md` | Lightweight technical UI design system | Created (Phase 1.5) |
| `docs/data/README.md` | Data documentation overview | Created (Phase 1) |
| `docs/data/dataset-index.md` | All datasets with schemas and lineage | Created (Phase 1) |
| `docs/data/business-knowledge.md` | Business rules and domain knowledge | Created (Phase 1) |
| `docs/data/query-log.md` | Data operations record | Created (Phase 1) |
| `docs/data/synthetic/cleaning-log.md` | Synthetic data cleaning events | Created (Phase 1) |
| `docs/data/synthetic/learnings.md` | Technical patterns and gotchas | Created (Phase 1) |

---

## 18. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Building too much too early | High | Keep strict phase gates and defer advanced work. |
| Weak data contracts | High | Define and test data validation early. |
| Unrealistic synthetic data | Medium | Document assumptions and improve data generation iteratively. |
| Streamlit accumulating business logic | Medium/High | Keep logic in reusable modules under `src/`. |
| Descriptive-only solution | Medium | Design features to support future prescriptive analysis. |
| Premature solver choice | Medium | Defer optimization library selection until Phase 5 requirements are clear. |
| Missing phase evidence | High | Require terminal logs, tests, docs, and master plan updates before phase closure. |
| Overengineering | Medium | Add only what supports Phases 0, 1, and 1.5 now. |

---

## 19. Scope changes

| Date | Version | Change | Reason | Impact |
|---|---|---|---|---|
| 2026-05-27 | v0.1.0-plan-only | Created master plan only, without executing implementation commands | User requested a plan in Markdown and explicitly said not to execute | Establishes the project roadmap and traceability contract |
| 2026-05-27 | v0.1.0 | Implemented Phase 0 and Phase 0-D: project structure, pyproject.toml, .gitignore, .env.example, src package with all subpackages, config/project_paths.py, unit tests, docs (architecture, data contract, roadmap, phase notes, terminal log) | User approved master plan and requested Phase 0 implementation | Delivers the complete project skeleton and foundational documentation |
| 2026-05-27 | v0.1.1 | Added Ruff verification to Phase 0 and documented the test-only `S101` exception for pytest assertions | Manager verification found lint issues after the initial Phase 0 apply | Phase 0 now passes both structure tests and lint checks |
| 2026-05-27 | v0.2.0 | Implemented Phase 1 and Phase 1-D: synthetic data generator, validation, loading, feature builder, scripts, tests, data governance docs, terminal log | User requested Phase 1 implementation after Phase 0 was verified | Delivers the complete Phase 1 data pipeline with 6 synthetic datasets and 7 feature builders |
| 2026-05-27 | v0.3.0 | Implemented Phase 1.5 and Phase 1.5-D: technical Streamlit front, dashboard helpers, UI design system, tests, docs, terminal log, and Graphify update/query evidence | User requested only Phase 1.5 after Phase 1 was completed and verified | Delivers a minimal descriptive UI for inspecting Phase 1 processed outputs without adding diagnostics, optimization, simulation, auth, or deployment |

---

## 20. Next steps

1. Manager verification of Phase 1.5 implementation, docs, and logs.
2. Install optional Streamlit dependency with `pip install -e ".[streamlit]"` if runtime UI launch is required locally.
3. Launch `streamlit run src/slotting_optimization_engine/app/streamlit_app.py` for manual browser inspection.
4. Keep Phase 2 limited to advanced diagnostics only after Phase 1.5 is accepted.

---

## 21. Current delivery status

| Item | Status |
|---|---|---|
| Master plan Markdown file | Updated through Phase 1.5 |
| Project code | Created — Phase 1 data pipeline and Phase 1.5 technical UI complete |
| Project commands | Phase 1.5 verification commands executed and recorded |
| Phase 0 implementation | Completed |
| Phase 0-D documentation | Completed |
| Phase 1 implementation | Completed |
| Phase 1-D documentation | Completed |
| Phase 1.5 implementation | Completed |
| Phase 1.5-D documentation | Completed |
| Terminal logs | Created — Phase 0, Phase 1, and Phase 1.5 |

---

## 22. Phase completion rule

A phase can only be marked complete when all of the following exist:

- Relevant code/configuration, if applicable.
- Tests or documented verification evidence.
- Terminal log for the phase.
- Phase note under `docs/phase_notes/`.
- Updated `docs/master_plan.md`.
- Updated related documents affected by architecture, data, execution, or scope changes.

If any item is missing, the phase remains pending or partial.
