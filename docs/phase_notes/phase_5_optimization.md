# Phase 5 — Controlled Mathematical Optimization Prototype

## Goal

Phase 5 adds a small, bounded SKU-to-zone assignment prototype over synthetic data. It uses Phase 3 priority signals, Phase 4 scenario context, Phase 2 diagnostics, and synthetic SKU/zone dimensions to produce transparent analytical recommendations.

## Scope

| Area | Decision |
|---|---|
| Candidate entity | Top-N SKU rows from `priority_recommendation_queue.csv` |
| Target entity | Warehouse zones expanded into simple logical `target_zone_slot` values |
| Objective | Minimize inferred weighted cost from demand/access fit, capacity pressure, opportunity score, and scenario context |
| Solver | SciPy `linear_sum_assignment` if importable; deterministic greedy fallback otherwise |
| Outputs | `optimization_assignments.csv`, `optimization_summary.csv`, `optimization_cost_matrix.csv` |
| Caveat | Prototype only; no physical move execution and no guaranteed feasible location slot |

## Files Added Or Updated

| File | Purpose |
|---|---|
| `src/slotting_optimization_engine/optimization/assignment.py` | Phase 5 input loading, cost matrix, solver/fallback, summaries, CSV saves |
| `src/slotting_optimization_engine/optimization/__init__.py` | Public optimization exports |
| `scripts/run_optimization.py` | CLI entrypoint for Phase 5 outputs |
| `tests/unit/test_optimization_assignment.py` | Unit tests for costs, shape, determinism, missing inputs, saves, and method field |
| `tests/unit/test_project_structure.py` | Required file expectations updated |
| `README.md` | Phase 5 usage, tools table, outputs, and caveats |
| `docs/data_contract.md` | Optimization output schemas |
| `docs/data/*.md` | Dataset index, business knowledge, query log, and learnings updated |

## Data Flow

```text
priority_recommendation_queue.csv
slotting_diagnostics.csv
zone_diagnostics.csv
scenario_comparison.csv
skus.csv / zones.csv
        |
        v
load_optimization_inputs()
        |
        v
select_candidate_skus()
        |
        v
build_assignment_cost_matrix()
        |
        v
solve_assignment()
        |
        v
optimization_assignments.csv
optimization_summary.csv
optimization_cost_matrix.csv
```

## Assumptions

| Assumption | State |
|---|---|
| Top-N SKU candidates are enough for the prototype | `inferred / pending confirmation` |
| Demand should favor closer/higher-priority zones | `inferred / pending confirmation` |
| Slow/lower-demand SKUs can tolerate less premium access | `inferred / pending confirmation` |
| Zone utilization is a proxy for capacity pressure | `inferred / pending confirmation` |
| Logical zone slots are acceptable for a prototype | `technical pattern` |

## Explicit Non-Goals

- No Phase 6 simulation engine.
- No auth, deploy, production app, or WMS/ERP integration.
- No automatic execution of SKU moves.
- No guarantee of location-level physical feasibility.
- No warehouse-grade optimizer claim.

## Graphify

Manager ran Graphify before implementation:

```powershell
graphify query "For Phase 5 mathematical optimization, what modules and outputs should connect to scenarios, scoring, diagnostics, domain constants, tests, README, and docs?" --budget 2200
```

Graphify was used as a hint source only. Source files and current CSV schemas were verified directly before implementation. After implementation, `graphify update .` and a UTF-8 Phase 5 relationship query were run and recorded in `docs/phase_logs/phase_5_terminal_log.md`.

## Verification

Verification commands are recorded in `docs/phase_logs/phase_5_terminal_log.md`:

- `python scripts/run_optimization.py`
- `python -m ruff check src tests scripts`
- `python -m pytest -v`
- `graphify update .`
- UTF-8 Graphify Phase 5 relationship query

## Streamlit

Streamlit was not updated. Phase 5 is core optimization logic plus documentation; adding UI would expand scope and risk confusion between analytical prototype output and executable operational recommendations.
