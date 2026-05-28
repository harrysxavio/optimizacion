# Master Plan — slotting-optimization-engine

**Project:** `slotting-optimization-engine`  
**Plan version:** `v0.8.0`  
**Last updated:** 2026-05-28  
**Status:** Phase 0, Phase 0-D, Phase 1, Phase 1-D, Phase 1.5, Phase 1.5-D, Phase 2, Phase 2-D, Phase 3, Phase 3-D, Phase 4, Phase 4-D, Phase 5, Phase 5-D, Phase 6, and Phase 6-D completed.  
**Scope of this update:** Phase 6 operational impact simulation (Scenario B: travel, workload, throughput), documentation, tests, terminal log, Graphify update evidence, README flow diagram, and master plan update to v0.8.0.

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
| 2 | Advanced slotting diagnostics | In scope | Completed |
| 2-D | Documentation, explanation, and traceability for Phase 2 | In scope | Completed |
| 3 | Prescriptive scoring and prioritization | In scope | Completed as review prioritization only |
| 3-D | Documentation, explanation, and traceability for Phase 3 | In scope | Completed |
| 4 | Scenario/model comparison | In scope | Completed as analytical what-if comparison only |
| 4-D | Documentation, explanation, and traceability for Phase 4 | In scope | Completed |
| 5 | Mathematical optimization | In scope | Completed as controlled SKU-to-zone prototype only |
| 5-D | Documentation, explanation, and traceability for Phase 5 | In scope | Completed |
| 6 | Operational simulation | In scope | Completed — all 3 scenarios (A/B/C) done. A = distance-only, B = full operational impact, C = reusable pipeline framework |
| 6-D | Documentation, explanation, and traceability for Phase 6 | In scope | Completed |

Phases 0 through 6-D have been completed. Phase 5 is a controlled mathematical assignment prototype only; Phase 6 is an operational impact simulation (all 3 scenarios: A distance-only, B full impact, C reusable pipeline) with inferred assumptions on synthetic data. Auth, deploy, production UX, real WMS/ERP integration, location-level feasibility guarantees, and automatic SKU move execution are still deferred.

---

## 4. Future scope

The following capabilities are intentionally deferred and must not be implemented during the first cycle except as clearly marked future stubs or folders:

| Future phase | Capability | Status |
|---|---|---|
| 7 | Production-ready application | Future |

Deferred capabilities include warehouse-grade optimization, warehouse-grade simulation, production deployment, authentication, real WMS/ERP integrations, final business UX, and automatic SKU move execution.

---

## 5. Guiding principles

| Principle | Decision |
|---|---|
| Controlled scope | Implement only the currently requested phase; Phase 5 is zone-level optimization only, not simulation or execution. |
| Modular architecture | Keep data, domain, features, diagnostics, scoring, scenarios, optimization, simulation, reporting, and app concerns separated. |
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
│       ├── scoring/
│       ├── scenarios/
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
Diagnostics, scoring, scenario comparison, and controlled optimization, then future simulation and recommendations
```

### Main modules

| Module | Purpose | Current-cycle responsibility |
|---|---|---|
| `config` | Central configuration | Paths, constants, environment-safe defaults. |
| `domain` | Business/domain concepts | SKU, zone, location concepts and future domain rules. |
| `data` | Data generation, loading, validation | Synthetic data and contract validation. |
| `features` | Analytical feature construction | Initial demand, rotation, utilization, and density features. |
| `diagnostics` | Slotting diagnostics | Descriptive diagnostic flags and CSV outputs. |
| `scoring` | Prioritization scoring | Action-level review scores and queue from diagnostic outputs. |
| `scenarios` | Scenario/model comparison | Analytical what-if comparison lenses over Phase 3 scoring outputs. |
| `optimization` | Mathematical optimization | Controlled Phase 5 SKU-to-zone assignment prototype; no physical move execution. |
| `simulation` | Operational simulation | Phase 6 travel, workload, and throughput simulation; Scenario C reusable framework deferred. |
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
| Phase 5 optimization | SciPy `linear_sum_assignment` with deterministic greedy fallback | Small transparent assignment prototype; method is recorded in outputs. | Implemented in Phase 5 |

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

### Phase 2 — Advanced slotting diagnostics

**Goal:** Produce descriptive slotting quality diagnostics from Phase 1 outputs without creating recommendations, prescriptive scores, scenarios, optimization, simulation, auth, deploy, or a final business app.

**Expected deliverables:**

- `src/slotting_optimization_engine/diagnostics/rules.py`
- `scripts/run_diagnostics.py`
- CSV diagnostic outputs under `data/processed/`
- Unit tests for diagnostic functions and practical script behavior
- Low-risk dashboard availability/preview support only

**Acceptance criteria:**

- Detect high-demand SKUs with long-distance or low-priority placement.
- Detect low-demand/slow-rotation SKUs occupying premium zones.
- Detect overutilized and underutilized zones/locations.
- Detect category spread/misgrouping indicators when fields exist.
- Detect capacity/density concerns using utilization outputs.
- Mark all thresholds/business rules as `inferred / pending confirmation`.
- Keep outputs descriptive and non-prescriptive.

### Phase 2-D — Documentation and traceability

**Required updates:**

- `docs/master_plan.md`
- `README.md`
- `docs/data_contract.md`
- `docs/data/dataset-index.md`
- `docs/data/business-knowledge.md`
- `docs/data/query-log.md`
- `docs/data/synthetic/learnings.md`
- `docs/phase_notes/phase_2_diagnostics.md`
- `docs/phase_logs/phase_2_terminal_log.md`
- `docs/architecture_sdd.md`
- `docs/roadmap.md`

### Phase 3 — Scoring and prioritization

**Goal:** Produce transparent prioritization scores and a sorted review queue from Phase 2 diagnostic outputs without creating mathematical optimization, target slot recommendations, scenario comparison, simulation, auth, deploy, or a final business app.

**Expected deliverables:**

- `src/slotting_optimization_engine/scoring/__init__.py`
- `src/slotting_optimization_engine/scoring/prioritization.py`
- `scripts/run_scoring.py`
- `data/processed/slotting_opportunity_scores.csv`
- `data/processed/priority_recommendation_queue.csv`
- `data/processed/scoring_summary.csv`
- Unit tests for score range, priority assignment, queue sorting, missing inputs, and output writing
- Documentation updates and Phase 3 terminal log

**Acceptance criteria:**

- Read Phase 2 diagnostic CSVs from `data/processed/`.
- Use a dataclass config with transparent weights.
- Mark every scoring weight/rule as `inferred / pending confirmation`.
- Emit candidate action labels such as `review_high_demand_far_sku`, `review_slow_mover_in_premium_zone`, and `review_zone_capacity_pressure`.
- Keep scoring as review prioritization only, not optimal move recommendation.
- Avoid heavy dependencies and use pandas only.

### Phase 3-D — Documentation and traceability

**Required updates:**

- `README.md`
- `docs/master_plan.md`
- `docs/data_contract.md`
- `docs/data/dataset-index.md`
- `docs/data/business-knowledge.md`
- `docs/data/query-log.md`
- `docs/data/synthetic/learnings.md`
- `docs/phase_notes/phase_3_scoring.md`
- `docs/phase_logs/phase_3_terminal_log.md`
- `docs/architecture_sdd.md`
- `docs/roadmap.md`

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
| `docs/phase_logs/phase_2_terminal_log.md` | Created. Phase 2 diagnostics, lint, tests, and Graphify commands were recorded. |
| `docs/phase_logs/phase_3_terminal_log.md` | Created. Phase 3 diagnostics, scoring, lint, tests, and Graphify commands were recorded. |

---

## 14. Planned commands

These commands describe the standard project workflow. Phase 0 through Phase 5 verification commands were executed and recorded in their phase logs.

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

### Run descriptive diagnostics

```bash
python scripts/run_diagnostics.py
```

### Run scoring/prioritization

```bash
python scripts/run_scoring.py
```

### Run scenario comparison

```bash
python scripts/run_scenarios.py
```

### Run controlled optimization prototype

```bash
python scripts/run_optimization.py
```

### Run operational simulation

```bash
python scripts/run_simulation.py

# Dry run (load data only, no simulation)
python scripts/run_simulation.py --dry-run
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
| `docs/master_plan.md` | Living project guide and traceability source | Updated (Phase 5) |
| `README.md` | Project usage, tools table, and quick start | Updated (Phase 5) |
| `docs/architecture_sdd.md` | Technical architecture and SDD decisions | Updated (Phase 5) |
| `docs/data_contract.md` | Data entities, fields, validations, assumptions, diagnostic/scoring/scenario/optimization schemas | Updated (Phase 5) |
| `docs/roadmap.md` | Detailed project roadmap | Updated (Phase 5) |
| `docs/phase_notes/phase_0_design_and_setup.md` | Phase 0 explanation and evidence | Created (Phase 0) |
| `docs/phase_notes/phase_1_data_pipeline.md` | Phase 1 explanation and evidence | Created (Phase 1) |
| `docs/phase_notes/phase_1_5_streamlit_front.md` | Phase 1.5 explanation and evidence | Created (Phase 1.5) |
| `docs/phase_notes/phase_2_diagnostics.md` | Phase 2 explanation and evidence | Created (Phase 2) |
| `docs/phase_notes/phase_3_scoring.md` | Phase 3 explanation and evidence | Created (Phase 3) |
| `docs/phase_notes/phase_4_scenarios.md` | Phase 4 explanation and evidence | Created (Phase 4) |
| `docs/phase_notes/phase_5_optimization.md` | Phase 5 explanation and evidence | Created (Phase 5) |
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
| Prototype mistaken for execution plan | High | Repeat caveats in outputs/docs; Phase 5 has no automatic SKU moves and no location-level guarantee. Phase 6 is not a certified engineering model. |
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
| 2026-05-27 | v0.4.0 | Implemented Phase 2 and Phase 2-D: descriptive diagnostics module, CLI, diagnostic CSV outputs, tests, data governance docs, terminal log, and Graphify update/query evidence | User requested only Phase 2 advanced slotting diagnostics and explicitly excluded prescriptive/optimization phases | Delivers descriptive diagnostic outputs while keeping Phase 3+ capabilities deferred |
| 2026-05-27 | v0.5.0 | Implemented Phase 3: transparent scoring/prioritization module, CLI, scoring CSV outputs, tests, Spanish README intro, data governance docs, terminal log, and Graphify update/query evidence | User requested only Phase 3 scoring/prioritization and explicitly excluded Phase 4+ | Delivers a human-review priority queue while keeping scenario comparison, mathematical optimization, and simulation deferred |
| 2026-05-28 | v0.6.0 | Implemented Phase 4 and Phase 4-D: scenario comparison module, CLI, scenario CSV outputs, tests, Spanish README expansion, data governance docs, terminal log, and Graphify update/query evidence | User requested only scenario/model comparison and explicitly excluded Phase 5+ optimization, solver, simulation, auth, deploy, and automatic SKU move execution | Delivers analytical what-if comparison while keeping mathematical optimization and simulation deferred |
| 2026-05-28 | v0.7.0 | Implemented Phase 5 and Phase 5-D: controlled assignment optimization module, CLI, optimization CSV outputs, tests, README tools table, data governance docs, terminal log, and Graphify update/query evidence | User requested only Phase 5 controlled mathematical optimization and explicitly excluded Phase 6 simulation, auth, deploy, real WMS/ERP integration, final app, and automatic SKU moves | Delivers a bounded SKU-to-zone optimization prototype while keeping execution, location feasibility, and simulation deferred |
| 2026-05-28 | v0.8.0 | Implemented Phase 6 and Phase 6-D: operational impact simulation (Scenario B), simulation modules, CLI, 5 CSV outputs, 38 new tests, phase note, terminal log, Graphify update, and README/master_plan/roadmap/data docs updated | User requested Phase 6 Scenario B (operational impact) first, followed by Scenario C and Scenario A | Delivers an operational impact simulation prototype with inferred assumptions; not a certified warehouse engineering model |

---

## 20. Next steps

1. Manager/user review of Phase 6 implementation, docs, logs, and Graphify update/query evidence.
2. Review inferred thresholds, scoring weights, scenario weights, optimization weights, simulation assumptions, and top-N settings with business users before treating outputs as operating policy.
3. Review Phase 6 documentation, beginner's guide, and verify all 3 scenarios produce expected outputs.

---

## 21. Current delivery status

| Item | Status |
|---|---|---|
| Master plan Markdown file | Updated through Phase 6 |
| Project code | Created — Phase 1 data pipeline, Phase 1.5 technical UI, Phase 2 diagnostics, Phase 3 scoring, Phase 4 scenarios, Phase 5 optimization, and Phase 6 simulation complete |
| Project commands | Phase 5 verification commands executed and recorded |
| Phase 0 implementation | Completed |
| Phase 0-D documentation | Completed |
| Phase 1 implementation | Completed |
| Phase 1-D documentation | Completed |
| Phase 1.5 implementation | Completed |
| Phase 1.5-D documentation | Completed |
| Phase 2 implementation | Completed |
| Phase 2-D documentation | Completed |
| Phase 3 implementation | Completed |
| Phase 3-D documentation | Completed |
| Phase 4 implementation | Completed |
| Phase 4-D documentation | Completed |
| Phase 5 implementation | Completed |
| Phase 5-D documentation | Completed |
| Phase 6 implementation | Completed |
| Phase 6-D documentation | Completed |
| Terminal logs | Created — Phase 0, Phase 1, Phase 1.5, Phase 2, Phase 3, Phase 4, Phase 5, and Phase 6 |

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
