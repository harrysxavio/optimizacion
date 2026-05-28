# Phase 4 — Scenario/Model Comparison

## 1. What was implemented

Phase 4 adds analytical scenario/model comparison over Phase 3 scoring outputs. It compares alternative what-if lenses (`baseline`, `demand_first`, `capacity_first`, `balanced_review`) without solving an optimization model, assigning target locations, simulating operations, or executing SKU moves.

## 2. Files created

| File | Purpose |
|---|---|
| `src/slotting_optimization_engine/scenarios/__init__.py` | Public exports for the scenario package |
| `src/slotting_optimization_engine/scenarios/comparison.py` | Scenario configs, ranking logic, action mix, summary, input loading, output saving |
| `scripts/run_scenarios.py` | CLI entrypoint for Phase 4 outputs |
| `tests/unit/test_scenario_comparison.py` | Unit tests for scenarios, sorting/weights, missing inputs, saves, and script import |
| `data/processed/scenario_comparison.csv` | Scenario-level top-N selected rows |
| `data/processed/scenario_action_mix.csv` | Action mix by scenario |
| `data/processed/scenario_summary.csv` | Scenario-level comparable metrics |

## 3. What each file is for

- `comparison.py` owns all reusable Phase 4 logic so the CLI remains thin.
- `run_scenarios.py` loads Phase 3 outputs, builds default scenarios, and saves CSV outputs.
- Tests protect behavior from drifting into hidden solver-like behavior.
- Output CSVs are review artifacts for analysts, not operational plans.

## 4. How the flow works

```text
Phase 3 scores and queue
        |
        v
load_scenario_inputs()
        |
        v
build_default_scenarios()
        |
        v
build_scenario_comparison()
        |
        +--> build_scenario_action_mix()
        +--> build_scenario_summary()
        |
        v
save_scenario_outputs()
```

## 5. Main functions/classes

| Function/class | Role |
|---|---|
| `ScenarioConfig` | Dataclass containing scenario assumptions, top-N, action weights, and entity weights |
| `build_default_scenarios` | Defines the four default Phase 4 comparison lenses |
| `load_scenario_inputs` | Reads required Phase 3 CSVs and optional Phase 2 diagnostic summary |
| `build_scenario_comparison` | Produces top-N selected rows per scenario |
| `build_scenario_action_mix` | Summarizes candidate-action mix per scenario |
| `build_scenario_summary` | Produces comparable scenario-level metrics |
| `save_scenario_outputs` | Writes the three Phase 4 CSV outputs |

## 6. Technical decisions

- Scenario comparison is implemented as pandas transformations only.
- `ScenarioConfig` keeps assumptions explicit and reviewable.
- All scenario assumptions remain `inferred / pending confirmation`.
- Every output includes a `scenario_note` stating that it is not optimization, solver output, or an executable movement plan.
- Streamlit was not updated because the user requested Phase 4 core comparison only; adding UI would be a separate surface and was not necessary for safe verification.

## 7. Assumptions

- `baseline` preserves Phase 3 ordering.
- `demand_first` emphasizes `review_high_demand_far_sku` and SKU entities.
- `capacity_first` emphasizes `review_zone_capacity_pressure` and zone entities.
- `balanced_review` adds moderate action emphasis and a priority-label bonus.
- Default `top_n=50` is inferred and pending business confirmation.

## 8. Remaining limitations

- No real WMS/ERP data.
- No solver, mathematical optimization, or target slot assignment.
- No simulation engine or operational labor/travel impact model.
- Scenario weights and top-N are not business-approved.
- Candidate actions remain review labels, not movement instructions.

## 9. What is missing for the next phase

- Phase 5 would need explicit optimization objectives, constraints, solver choice, feasible location/SKU movement rules, and business-approved weights.
- Any future UI exposure should clearly preserve the current caveats.

## 10. How to run related scripts

```powershell
python scripts/run_scenarios.py
```

If Phase 3 outputs are missing, run:

```powershell
python scripts/run_diagnostics.py
python scripts/run_scoring.py
python scripts/run_scenarios.py
```

## 11. Expected output

- `data/processed/scenario_comparison.csv`
- `data/processed/scenario_action_mix.csv`
- `data/processed/scenario_summary.csv`

## 12. Common errors

| Error | Cause |
|---|---|
| `Missing Phase 3 scoring output(s)` | `run_scenarios.py` was executed before Phase 3 outputs existed |
| Missing expected columns | A Phase 3 CSV schema changed without updating scenario comparison |

## 13. How to resolve common errors

- Regenerate diagnostics and scoring before scenarios.
- Update `comparison.py`, `docs/data_contract.md`, and tests if Phase 3 schemas intentionally change.

## 14. Tests covering the phase

- `tests/unit/test_scenario_comparison.py`
- `tests/unit/test_project_structure.py`

## 15. Evidence that the phase works

- `python scripts/run_scenarios.py` completed and wrote 200 comparison rows across 4 scenarios.
- `python -m ruff check src tests scripts` passed.
- `python -m pytest -v` passed.
- `graphify update .` and a UTF-8 Graphify query were run after the implementation.

## Graphify use

- Before implementation, Manager ran: `graphify query "For Phase 4 scenario and model comparison, what modules and outputs should connect to Phase 3 scoring, diagnostics, processed data, tests, README, and docs?" --budget 2200`.
- After implementation, Phase 4 ran `graphify update .` and a UTF-8 query to verify relationships.
