# Roadmap — Slotting Optimization Engine

**Last updated:** 2026-05-28

---

## Phase overview

| Phase | Name | Status | Description |
|---|---|---|---|
| 0 | Design, architecture, initial config, base docs | ✅ **Completed** | Project skeleton, `pyproject.toml`, structure, documentation |
| 0-D | Phase 0 documentation & traceability | ✅ **Completed** | Architecture, data contract, roadmap, phase notes, logs |
| 1 | Data pipeline — synthetic data, validation, transformation, features | ✅ **Completed** | Synthetic data generation, two-tier validation, feature builder |
| 1-D | Phase 1 documentation & traceability | ✅ **Completed** | Phase notes, logs, contract updates, data governance docs |
| 1.5 | Minimal Streamlit technical front-end | ✅ **Completed** | Dataset inspection, KPIs, basic visualisations |
| 1.5-D | Phase 1.5 documentation & traceability | ✅ **Completed** | Phase notes, logs, README, architecture, design docs |
| 2 | Advanced slotting diagnostics | ✅ **Completed** | Descriptive SKU placement, zone, location, category, and capacity diagnostics |
| 2-D | Phase 2 documentation & traceability | ✅ **Completed** | Phase notes, logs, contracts, data governance docs, Graphify evidence |
| 3 | Prescriptive scoring and prioritisation | ✅ **Completed** | Transparent review-prioritization scores from Phase 2 diagnostics |
| 4 | Scenario/model comparison | ✅ **Completed** | Analytical what-if comparison of Phase 3 ranking lenses; no solver or move execution |
| 4-D | Phase 4 documentation & traceability | ✅ **Completed** | Phase note, terminal log, data contract, governance docs, Graphify evidence |
| 5 | Mathematical optimisation | ✅ **Completed** | Controlled SKU-to-zone assignment prototype; no execution or location-level feasibility guarantee |
| 5-D | Phase 5 documentation & traceability | ✅ **Completed** | Phase note, terminal log, data contract, governance docs, README tools table, Graphify evidence |
| 6 | Operational simulation | 🔜 Future | Labour modelling, travel time, throughput estimation |
| 7 | Production-ready application | 🔜 Future | Auth, CI/CD, deployment, WMS/ERP connectors |

## Current phase details

### Phase 0 — Complete

- [x] Base folder structure
- [x] `README.md` with project overview, setup, and docs map
- [x] `pyproject.toml` with Python 3.11+ and minimal dependencies
- [x] `.gitignore` and `.env.example`
- [x] `src/slotting_optimization_engine/` package with all subpackages
- [x] `config/project_paths.py` with central path resolution
- [x] `tests/unit/test_project_structure.py` for import/directory verification
- [x] `docs/architecture_sdd.md` documenting architecture and decisions
- [x] `docs/data_contract.md` (preliminary Phase 1 entities and rules)
- [x] `docs/roadmap.md` (this file)
- [x] `docs/phase_notes/phase_0_design_and_setup.md`
- [x] `docs/phase_logs/phase_0_terminal_log.md`
- [x] `docs/master_plan.md` updated

### Phase 1 — Complete

- [x] `src/slotting_optimization_engine/domain/constants.py` — Column name constants, enums, config defaults
- [x] `src/slotting_optimization_engine/data/generator.py` — `SyntheticDataGenerator` class
- [x] `src/slotting_optimization_engine/data/validation.py` — Two-tier validation (pandera + explicit fallback)
- [x] `src/slotting_optimization_engine/data/loading.py` — CSV loading with optional validation
- [x] `src/slotting_optimization_engine/features/builder.py` — Feature construction (demand, utilisation, alignment)
- [x] `scripts/generate_sample_data.py` — CLI entrypoint
- [x] `scripts/run_data_validation.py` — CLI entrypoint
- [x] `scripts/build_features.py` — CLI entrypoint
- [x] `tests/unit/test_data_generator.py` — ~25 generator tests
- [x] `tests/unit/test_data_validation.py` — ~15 validation tests
- [x] `tests/unit/test_data_loading.py` — 4 loading tests
- [x] `tests/unit/test_feature_builder.py` — ~15 feature tests
- [x] `docs/data/README.md` — Data documentation overview
- [x] `docs/data/dataset-index.md` — Complete dataset index
- [x] `docs/data/business-knowledge.md` — Business rules and KPIs
- [x] `docs/data/query-log.md` — Data operations record
- [x] `docs/data/synthetic/cleaning-log.md` — Cleaning events
- [x] `docs/data/synthetic/learnings.md` — Technical patterns
- [x] `docs/data_contract.md` — Finalised with actual fields and validations
- [x] `docs/phase_notes/phase_1_data_pipeline.md` — Phase 1 explanation and evidence
- [x] `docs/phase_logs/phase_1_terminal_log.md` — Terminal log
- [x] `docs/master_plan.md` — Updated with Phase 1 completion
- [x] `README.md` — Updated with execution commands

### Phase 1.5 — Complete

- [x] `src/slotting_optimization_engine/app/dashboard_data.py` — Pure helpers for loading processed outputs, availability status, KPIs, previews, and chart-ready tables
- [x] `src/slotting_optimization_engine/app/streamlit_app.py` — Minimal technical Streamlit inspection UI
- [x] `docs/DESIGN.md` — Lightweight operational/control-tower design system
- [x] `tests/unit/test_dashboard_data.py` — Unit tests for pure dashboard helpers
- [x] `tests/unit/test_project_structure.py` — Updated structure expectations
- [x] `README.md` — Streamlit command and prerequisite outputs
- [x] `docs/architecture_sdd.md` — Updated app architecture responsibilities
- [x] `docs/phase_notes/phase_1_5_streamlit_front.md` — Phase note and evidence
- [x] `docs/phase_logs/phase_1_5_terminal_log.md` — Terminal log with verification and Graphify use
- [x] `docs/master_plan.md` — Updated with Phase 1.5 completion

### Phase 2 — Complete

- [x] `src/slotting_optimization_engine/diagnostics/rules.py` — Descriptive diagnostic rules and CSV output writer
- [x] `scripts/run_diagnostics.py` — CLI entrypoint for Phase 2 outputs
- [x] `data/processed/slotting_diagnostics.csv` — SKU-level descriptive diagnostic flags
- [x] `data/processed/location_diagnostics.csv` — Location utilization, density, and category-mix diagnostics
- [x] `data/processed/zone_diagnostics.csv` — Zone utilization and premium-zone slow-mover diagnostics
- [x] `data/processed/category_diagnostics.csv` — Category spread and grouping indicators
- [x] `data/processed/diagnostic_summary.csv` — Summary counts and threshold notes
- [x] `tests/unit/test_diagnostics_rules.py` — Unit and script-level missing-input tests
- [x] `tests/unit/test_project_structure.py` — Updated required files
- [x] `src/slotting_optimization_engine/app/dashboard_data.py` — Low-risk diagnostic output availability support
- [x] `src/slotting_optimization_engine/app/streamlit_app.py` — Diagnostic summary preview only
- [x] `docs/phase_notes/phase_2_diagnostics.md` — Phase 2 decisions and evidence
- [x] `docs/phase_logs/phase_2_terminal_log.md` — Terminal log with verification and Graphify use

### Phase 3 — Complete

- [x] `src/slotting_optimization_engine/scoring/__init__.py` — Scoring package exports
- [x] `src/slotting_optimization_engine/scoring/prioritization.py` — Dataclass scoring config, action scores, priority queue, summary, and output writer
- [x] `scripts/run_scoring.py` — CLI entrypoint for Phase 3 outputs
- [x] `data/processed/slotting_opportunity_scores.csv` — Action-level prioritization scores
- [x] `data/processed/priority_recommendation_queue.csv` — Sorted human-review queue
- [x] `data/processed/scoring_summary.csv` — Summary metrics and inferred config snapshot
- [x] `tests/unit/test_scoring_prioritization.py` — Score range, priority labels, queue sorting, missing inputs, output saving, script import
- [x] `tests/unit/test_project_structure.py` — Updated required Phase 3 files
- [x] `docs/phase_notes/phase_3_scoring.md` — Phase 3 decisions and evidence
- [x] `docs/phase_logs/phase_3_terminal_log.md` — Terminal log with verification and Graphify use

### Phase 4 — Complete

- [x] `src/slotting_optimization_engine/scenarios/__init__.py` — Scenario package exports
- [x] `src/slotting_optimization_engine/scenarios/comparison.py` — Dataclass scenario lenses, top-N comparison, action mix, summary, and output writer
- [x] `scripts/run_scenarios.py` — CLI entrypoint for Phase 4 outputs
- [x] `data/processed/scenario_comparison.csv` — Top-N analytical comparison rows by scenario
- [x] `data/processed/scenario_action_mix.csv` — Candidate-action mix by scenario
- [x] `data/processed/scenario_summary.csv` — Scenario-level comparable metrics and assumptions
- [x] `tests/unit/test_scenario_comparison.py` — Scenario config, sorting/weights, missing inputs, output saving, and script import tests
- [x] `tests/unit/test_project_structure.py` — Updated required Phase 4 files
- [x] `docs/phase_notes/phase_4_scenarios.md` — Phase 4 decisions and evidence
- [x] `docs/phase_logs/phase_4_terminal_log.md` — Terminal log with verification and Graphify use

### Phase 5 — Complete

- [x] `src/slotting_optimization_engine/optimization/__init__.py` — Optimization package exports
- [x] `src/slotting_optimization_engine/optimization/assignment.py` — Cost matrix, solver/fallback assignment, summary, and output writer
- [x] `scripts/run_optimization.py` — CLI entrypoint for Phase 5 outputs
- [x] `data/processed/optimization_assignments.csv` — Controlled SKU-to-zone assignment rows
- [x] `data/processed/optimization_summary.csv` — Method, selected SKU count, zone usage, and cost metrics
- [x] `data/processed/optimization_cost_matrix.csv` — Transparent SKU-zone-slot cost matrix
- [x] `tests/unit/test_optimization_assignment.py` — Cost matrix, shape, deterministic fallback, missing inputs, saving, method field, script import
- [x] `tests/unit/test_project_structure.py` — Updated required Phase 5 files
- [x] `docs/phase_notes/phase_5_optimization.md` — Phase 5 decisions and evidence
- [x] `docs/phase_logs/phase_5_terminal_log.md` — Terminal log with verification and Graphify use

## Legend

| Symbol | Meaning |
|---|---|
| ✅ **Completed** | Done and verified |
| 🔲 Pending | Planned but not started |
| 🔜 Future | Defined but deferred beyond the first cycle |
