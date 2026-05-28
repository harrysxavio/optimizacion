# Query Log — Slotting Optimization Engine

**Last updated:** 2026-05-28

Records of data operations executed against the project datasets.

---

## 2026-05-27 — Phase 1 data generation

**Action:** Generated all six synthetic datasets.

**Command:** `python scripts/generate_sample_data.py`

**Sources:** `data/synthetic/*.csv`

**Results:** See `docs/phase_logs/phase_1_terminal_log.md` for full output.

---

## 2026-05-27 — Phase 1 validation

**Action:** Validated all synthetic datasets against data contract.

**Command:** `python scripts/run_data_validation.py`

**Sources:** `data/synthetic/*.csv`

**Results:** See `docs/phase_logs/phase_1_terminal_log.md` for full output.

---

## 2026-05-27 — Phase 1 feature building

**Action:** Built analytical features from validated data.

**Command:** `python scripts/build_features.py`

**Sources:** `data/synthetic/*.csv` → `data/processed/*`

**Results:** See `docs/phase_logs/phase_1_terminal_log.md` for full output.

---

## 2026-05-27 — Phase 2 diagnostic generation

**Action:** Built descriptive slotting diagnostics from Phase 1 processed outputs and validated synthetic placement context.

**Command:** `python scripts/run_diagnostics.py`

**Sources:** `data/processed/slotting_features.parquet`, `data/processed/location_utilization.csv`, `data/processed/zone_utilization.csv`, and read-only `data/synthetic/*.csv` for placement/category context.

**Results:** Wrote `slotting_diagnostics.csv`, `location_diagnostics.csv`, `zone_diagnostics.csv`, `category_diagnostics.csv`, and `diagnostic_summary.csv` to `data/processed/`. See `docs/phase_logs/phase_2_terminal_log.md`.

---

## 2026-05-27 — Phase 3 scoring generation

**Action:** Built transparent prioritization scores and a sorted review queue from Phase 2 diagnostic outputs.

**Command:** `python scripts/run_scoring.py`

**Sources:** `data/processed/slotting_diagnostics.csv`, `location_diagnostics.csv`, `zone_diagnostics.csv`, `category_diagnostics.csv`, and optional `diagnostic_summary.csv`.

**Results:** Wrote `slotting_opportunity_scores.csv`, `priority_recommendation_queue.csv`, and `scoring_summary.csv` to `data/processed/`. See `docs/phase_logs/phase_3_terminal_log.md`.

---

## 2026-05-28 — Phase 4 scenario/model comparison

**Action:** Built analytical what-if scenario comparison outputs from Phase 3 scoring outputs.

**Command:** `python scripts/run_scenarios.py`

**Sources:** `data/processed/slotting_opportunity_scores.csv`, `priority_recommendation_queue.csv`, `scoring_summary.csv`, and optional `diagnostic_summary.csv`.

**Results:** Wrote `scenario_comparison.csv`, `scenario_action_mix.csv`, and `scenario_summary.csv` to `data/processed/`. See `docs/phase_logs/phase_4_terminal_log.md`.

---

## 2026-05-28 — Phase 5 controlled optimization prototype

**Action:** Built transparent SKU-to-zone assignment outputs from Phase 3 priority queue, Phase 4 scenario context, Phase 2 diagnostics, and validated synthetic SKU/zone dimensions.

**Command:** `python scripts/run_optimization.py`

**Sources:** `data/processed/priority_recommendation_queue.csv`, `slotting_diagnostics.csv`, `zone_diagnostics.csv`, optional `scenario_comparison.csv`, plus `data/synthetic/skus.csv` and `zones.csv`.

**Results:** Wrote `optimization_assignments.csv`, `optimization_summary.csv`, and `optimization_cost_matrix.csv` to `data/processed/`. The run recorded `greedy_fallback` because SciPy was not importable in the active environment despite being added to project dependencies. See `docs/phase_logs/phase_5_terminal_log.md`.
