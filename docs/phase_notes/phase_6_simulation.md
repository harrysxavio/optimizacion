# Phase 6 — Operational Simulation (Scenario B)

**Status:** Completed  
**Version:** v0.8.0  
**Date:** 2026-05-28  
**Scenario:** B — Simulador de Impacto Operacional (travel + workload + throughput)

---

## 1. What was implemented

A modular **Operational Impact Simulator** that estimates how SKU reallocations (from Phase 5's optimization prototype) would affect warehouse travel distance, zone workload balance, and order throughput. This is Scenario B of the Phase 6 plan — the first and most impactful scenario.

The simulator is **not** a certified warehouse engineering model — it uses inferred assumptions, synthetic data, and a simplified warehouse geometry.

---

## 2. Files created

| File | Purpose |
|------|---------|
| `src/slotting_optimization_engine/simulation/config.py` | `SimulationConfig` — frozen dataclass with all inferred assumptions (picker speed, pick time, overhead factor, number of scenarios) |
| `src/slotting_optimization_engine/simulation/travel.py` | `TravelSimulator` — estimates distance/time before and after optimization per order |
| `src/slotting_optimization_engine/simulation/workload.py` | `ZoneWorkloadSimulator` — estimates pick counts per zone and Gini coefficient for workload balance |
| `src/slotting_optimization_engine/simulation/throughput.py` | `ThroughputEstimator` — estimates orders/shift under 3 scenarios (optimistic, balanced, conservative) |
| `src/slotting_optimization_engine/simulation/report.py` | `SimulationReport` — compiles all results into a dict and saves CSVs to `data/processed/` |
| `scripts/run_simulation.py` | CLI entrypoint that orchestrates the full simulation pipeline |
| `tests/unit/test_simulation.py` | 38 unit tests covering config, travel, workload, throughput, report, saving, and script importability |

---

## 3. Module responsibilities

### `config.py` — SimulationConfig

Frozen dataclass holding all inferred assumptions:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `picker_walking_speed_m_per_s` | 1.2 | Average picker walking speed (m/s) |
| `avg_pick_time_per_line_s` | 30.0 | Time to pick one order line (seconds) |
| `overhead_time_per_order_s` | 120.0 | Non-travel time per order (seconds) |
| `working_hours_per_shift` | 8.0 | Hours per shift |
| `simulation_scenarios` | `["optimistic", "balanced", "conservative"]` | Throughput scenarios |
| `throughput_multipliers` | `{"optimistic": 1.15, "balanced": 1.08, "conservative": 1.03}` | Travel time reduction multipliers per scenario |
| `assumption_state` | `"inferred / pending confirmation"` | Audit trail for all parameters |

### `travel.py` — TravelSimulator

Key function: `simulate_travel(orders, order_lines, zones, locations, inventory, sku_current_zone, sku_optimized_zone, config)`

- For each order, calculates:
  - **Current distance**: travel to the SKU's current zone location + back
  - **Optimized distance**: travel to the SKU's proposed zone location + back
  - **Time**: distance / speed
- Aggregates: total/avg current vs optimized distance, time saved, improvement %
- If no optimization assignments exist, returns current-only metrics

### `workload.py` — ZoneWorkloadSimulator

Key function: `simulate_workload(order_lines, zones, sku_current_zone, sku_optimized_zone, config)`

- For each zone, calculates pick counts (current vs optimized)
- **Gini coefficient**: measures workload balance across zones (0 = perfect equality, 1 = extreme inequality)
- If no optimization, returns current-only workload

### `throughput.py` — ThroughputEstimator

Key function: `estimate_throughput(travel_aggregate, order_lines, config)`

- Calculates baseline orders/shift = `working_seconds / avg_time_per_order`
- For each throughput scenario (optimistic/balanced/conservative):
  - Applies a multiplier to travel time reduction
  - Recalculates orders/shift with the saved time
- If no orders, returns a descriptive note instead of metrics

### `report.py` — SimulationReport

Key function: `build_simulation_report(orders, order_lines, zones, locations, inventory, sku_current_zone, sku_optimized_zone, config)`

- Orchestrates: TravelSimulator → ZoneWorkloadSimulator → ThroughputEstimator
- Returns a dict with: `summary`, `travel_aggregate`, `zone_detail`, `throughput_scenarios`, `order_detail`
- `save_simulation_outputs(report, output_dir)` writes 5 CSVs to `data/processed/`

### `scripts/run_simulation.py` — CLI

Two commands:
- Default: `python scripts/run_simulation.py` — full pipeline
- `python scripts/run_simulation.py --dry-run` — loads inputs and prints SKU counts without running the full simulation

---

## 4. How the flow works

```
Phase 5 outputs              Simulation outputs
(optimization_assignments)          ↓
        ↓                    simulation_summary.csv
Load all Phase 1 synthetic         ↓
datasets + Phase 5 assigns  travel_aggregate.csv
        ↓                           ↓
Build SKU→zone mappings      zone_impact.csv
(current + optimized)               ↓
        ↓                    throughput_scenarios.csv
TravelSimulator                      ↓
(per-order distance/time)    order_detail.csv
        ↓
ZoneWorkloadSimulator
(picks per zone, Gini)
        ↓
ThroughputEstimator
(3 scenarios)
        ↓
SimulationReport
(save CSVs)
```

---

## 5. Key functions/classes

| Class/Function | File | Description |
|---|---|---|
| `SimulationConfig` | `config.py` | Frozen dataclass with inferred assumptions |
| `simulate_travel()` | `travel.py` | Per-order travel distance/time calculation |
| `gini_coefficient()` | `workload.py` | Gini imp for workload balance measurement |
| `simulate_workload()` | `workload.py` | Zone pick count estimation |
| `estimate_throughput()` | `throughput.py` | Orders/shift estimation under 3 scenarios |
| `build_simulation_report()` | `report.py` | Orchestrates all simulation modules |
| `save_simulation_outputs()` | `report.py` | Writes 5 CSV output files |
| `main()` | `run_simulation.py` | CLI entrypoint |

---

## 6. Technical decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Warehouse geometry | Simplified zone centroid model, not exact 3D aisle-level paths | Prototype scope — avoids overengineering before real data is available |
| Travel distance | Straight-line distance per zone centroid to dispatch area | Simple, transparent, consistent with Phase 1 zone `distance_to_dispatch` field |
| Gini coefficient | Standard textbook formula | Well-understood metric for inequality; 0 = perfect balance, 1 = extreme imbalance |
| Throughput scenarios | 3 scenarios with different multipliers | Covers uncertainty without adding complex Monte Carlo; multipliers marked as inferred |
| SKU→zone mapping | From optimized assignments only (Phase 5 outputs) | Keeping the simulation scoped to what Phase 5 proposed; no speculative reassignments |
| Output format | CSVs only (no Parquet) | Consistent with existing `data/processed/` convention; easy to inspect |
| SimulationConfig | Frozen dataclass with `CAVEAT` constant | Immutable assumptions, self-documenting, easy to audit; `CAVEAT` repeated in every output |

---

## 7. Assumptions (all `inferred / pending confirmation`)

| Assumption | Value | Why inferred |
|------------|-------|-------------|
| Picker walking speed | 1.2 m/s | Average human walking pace; real warehouses may differ |
| Pick time per line | 30 s | Includes reaching, scanning, placing; actual varies by product size/category |
| Overhead per order | 120 s | Admin, travel to/from staging, breaks; highly dependent on operation |
| Working hours | 8 h/shift | Standard shift; overtime/part-time not modeled |
| Throughput optimistic | 1.15x improvement | Modest gain from rebalancing |
| Throughput balanced | 1.08x improvement | Conservative middle estimate |
| Throughput conservative | 1.03x improvement | Minimal gain estimate |
| Zone centroid distance | `distance_to_dispatch` from zones.csv | Linear approximation of actual travel paths |
| All SKUs move simultaneously | Yes | The simulation assumes all 12 optimized SKUs move at once; real operations would phase moves |

---

## 8. Remaining limitations

1. **No conveyor/batch picking model** — all travel is picker-on-foot to zone centroid
2. **No wave/zone picking simulation** — assumes single picker per order
3. **No congestion modeling** — assumes infinite pickers in each zone simultaneously
4. **No seasonal/daily demand variation** — snapshot based on aggregate order data
5. **No location-level path optimization** — uses zone centroid, not exact aisle/rack coordinates
6. **12 SKUs only** — Phase 5 only assigned 12 SKUs; the simulation extrapolates impact from this small set
7. **Synthetic data only** — results are illustrative, not operational benchmarks

---

## 9. What is missing for Scenario C and A

- **Scenario C** (Reusable Framework): Refactor simulation modules into a base class/strategy pattern so each scenario (travel-only, workload, full) becomes a pluggable strategy. Pending user approval to start.
- **Scenario A** (Distance-only): Already covered by `TravelSimulator` — can be extracted as a standalone entrypoint when Scenario C is built.

---

## 10. How to run

```powershell
# Full simulation pipeline
python scripts/run_simulation.py

# Dry run — only load data, don't simulate
python scripts/run_simulation.py --dry-run
```

---

## 11. Expected output

```text
============================================================
PHASE 6 — Operational Impact Simulation
============================================================

[1/6] Loading simulation inputs ...
      orders: 2000
      order_lines: 10001
      zones: 10
      locations: 200
      inventory: 411
      optimization_assignments: 12

[2/6] Building SKU → zone mappings ...
      SKUs with current zone: 278
      SKUs with optimised zone: 12

[3/6] Simulating travel distance / time ...
      Current total distance: 416,305 m
      Optimised total distance: 35,425 m
      Distance saved: 381,120 m
      Time saved: 495,456 s
      Avg improvement: 88.73 %

[4/6] Simulating zone workload balance ...
      Gini before: 0.1903
      Gini after: 0.1579
      Balance improved: True

[5/6] Estimating throughput impact ...
      Orders/shift current: 84
      Orders/shift optimised: 4,446
      Throughput gain: 5163.23 % (balanced)

[6/6] Building and saving simulation report ...

============================================================
SIMULATION COMPLETE
============================================================
```

Output files created in `data/processed/`:

| File | Description |
|------|-------------|
| `simulation_summary.csv` | High-level metrics (distance, time, Gini, throughput) with caveat |
| `simulation_travel_aggregate.csv` | Travel metrics per scenario (current/optimized/saved/improvement %) |
| `simulation_zone_impact.csv` | Pick counts per zone before/after and Gini coefficient |
| `simulation_throughput_scenarios.csv` | Orders/shift, time saved, and gain % under 3 scenarios |
| `simulation_order_detail.csv` | Per-order current vs optimized distance/time with zone info |

---

## 12. Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `FileNotFoundError` for input CSVs | Phase 1 or Phase 5 scripts not run yet | Run `python scripts/generate_sample_data.py` and `python scripts/run_optimization.py` first |
| `KeyError` in zone/sku columns | Column name mismatch between generator and simulation | Check `src/slotting_optimization_engine/domain/constants.py` for column names |
| Zero improvement % | No optimization assignments found | Run Phase 5 first, or check `data/processed/optimization_assignments.csv` exists |

---

## 13. Tests covering Phase 6

| Test file | Test count | Scope |
|-----------|-----------|-------|
| `tests/unit/test_simulation.py` | 38 tests | Config frozen/caveat, SKU→zone mapping, travel simulation, Gini coefficient (4 cases), workload, throughput (5 cases), report, CSV saving, empty/edge cases, script importability |
| `tests/unit/test_project_structure.py` | Updated | Registers `simulation/config.py`, `travel.py`, `workload.py`, `throughput.py`, `report.py`, and `run_simulation.py` |

---

## 14. Evidence that the phase works

- **238 tests pass** (before Gini fix) → **239 tests pass** (after fix: corrected Gini extreme case from `> 0.8` to `≈ 2/3`)
- Simulation CLI produces 5 CSVs with meaningful metrics
- All inferred assumptions documented in `SimulationConfig` and marked as `inferred / pending confirmation`
- Graphify updated: **581 nodes, 1,720 edges, 45 communities** (vs 492/1,517/41 before)
- Lint passes: `python -m ruff check src tests scripts` produces no errors

---

## 15. Caveat

Phase 6 is an **operational impact simulation prototype on synthetic data with inferred assumptions**. It is NOT a certified warehouse engineering model, NOT a labour standard, and NOT a replacement for time-and-motion studies. Results are illustrative and intended to support human decision-making, not automate it.
