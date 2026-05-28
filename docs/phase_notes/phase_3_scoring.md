# Phase 3 — Scoring and Prioritization

## 1. What was implemented

Phase 3 adds transparent scoring and prioritization on top of Phase 2 diagnostic outputs.

The implementation reads diagnostic CSVs from `data/processed/`, creates action-level review scores, builds a sorted priority queue, and saves a scoring summary. It does not solve an optimization model, select target locations, recommend optimal SKU moves, compare scenarios, or simulate operations.

## 2. Files created

- `src/slotting_optimization_engine/scoring/__init__.py`
- `src/slotting_optimization_engine/scoring/prioritization.py`
- `scripts/run_scoring.py`
- `tests/unit/test_scoring_prioritization.py`
- `docs/phase_notes/phase_3_scoring.md`
- `docs/phase_logs/phase_3_terminal_log.md`

## 3. What each file is for

- `scoring/__init__.py` exposes Phase 3 scoring functions and config.
- `scoring/prioritization.py` owns the dataclass config, diagnostic input loading, opportunity score generation, queue generation, summary generation, and CSV output writing.
- `scripts/run_scoring.py` is the CLI entrypoint for Phase 3.
- `tests/unit/test_scoring_prioritization.py` verifies score range, priority labels, queue sorting, missing input errors, output saving, and script importability.
- `phase_3_scoring.md` documents the phase.
- `phase_3_terminal_log.md` records execution evidence.

## 4. How the flow works

```text
Phase 2 diagnostic CSVs
        │
        ▼
load_diagnostic_inputs()
        │
        ▼
build_slotting_opportunity_scores()
        │
        ├── review_high_demand_far_sku
        ├── review_slow_mover_in_premium_zone
        └── review_zone_capacity_pressure
        │
        ▼
build_priority_queue()
        │
        ▼
build_scoring_summary()
        │
        ▼
save_scoring_outputs()
```

## 5. Main functions/classes

- `ScoringConfig`: frozen dataclass with inferred weights and thresholds.
- `load_diagnostic_inputs`: loads required Phase 2 outputs and reports missing files clearly.
- `build_slotting_opportunity_scores`: creates one row per entity/action candidate.
- `build_priority_queue`: filters and sorts review candidates by descending score.
- `build_scoring_summary`: records scoring counts, priority counts, score statistics, and config snapshot.
- `save_scoring_outputs`: writes the three Phase 3 CSV outputs.

## 6. Technical decisions

- Use pandas only; no new heavy dependencies.
- Keep weights in a dataclass so assumptions are visible and testable.
- Copy `inferred / pending confirmation` into outputs and docs.
- Use `review_*` action labels to avoid implying approved operational movement.
- Score to a 0-100 range for easy analyst interpretation.

## 7. Assumptions

- Phase 2 diagnostics already exist in `data/processed/`.
- Phase 2 diagnostic flags are valid descriptive inputs.
- Weight values are inferred from synthetic data behavior and are not confirmed business policy.
- Priority labels are review labels, not service-level commitments.

## 8. Remaining limitations

- No mathematical optimization.
- No target slot recommendation.
- No scenario comparison.
- No operational simulation.
- No real WMS/ERP data.
- No business-confirmed scoring weights.

## 9. What is missing for the next phase

Phase 4 may introduce scenario/model comparison only if explicitly requested. Phase 5 optimization, Phase 6 simulation, and Phase 7 production readiness remain deferred.

## 10. How to run related scripts

```powershell
python scripts/run_diagnostics.py
python scripts/run_scoring.py
```

## 11. Expected output

- `data/processed/slotting_opportunity_scores.csv`
- `data/processed/priority_recommendation_queue.csv`
- `data/processed/scoring_summary.csv`

## 12. Common errors

Missing Phase 2 outputs:

```text
Missing Phase 2 diagnostic output(s): ... Run `python scripts/run_diagnostics.py` first.
```

## 13. How to resolve common errors

Run the prerequisite diagnostics script:

```powershell
python scripts/run_diagnostics.py
python scripts/run_scoring.py
```

## 14. Tests covering the phase

- `tests/unit/test_scoring_prioritization.py`
- `tests/unit/test_project_structure.py`

## 15. Evidence that the phase works

Evidence is recorded in `docs/phase_logs/phase_3_terminal_log.md`.
