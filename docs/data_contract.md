# Data Contract — Slotting Optimization Engine

**Status:** FINALISED — Phase 6 simulation outputs added.  
**Purpose:** Define data entities, fields, validation rules, file formats, diagnostic output schemas, scoring output schemas, scenario output schemas, optimization output schemas, and simulation output schemas.  
**Last updated:** 2026-05-28

---

## 1. Entities

### 1.1 SKU (`skus` — `data/synthetic/skus.csv`)

Product master data.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `sku_id` | string | Yes | PK, unique, not null | Unique SKU identifier |
| `category` | string | Yes | Not null | Product category |
| `subcategory` | string | No | Nullable | Product subcategory |
| `unit_volume` | float | Yes | > 0 | Volume per unit (cm³) |
| `unit_weight` | float | Yes | > 0 | Weight per unit (kg) |
| `rotation_class` | string | Yes | Must be A/B/C/D | Rotation classification |
| `avg_daily_demand` | float | Yes | >= 0 | Average daily demand (units) |

### 1.2 Zone (`zones` — `data/synthetic/zones.csv`)

Logical warehouse zone.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `zone_id` | string | Yes | PK, unique, not null | Unique zone identifier |
| `zone_type` | string | Yes | Not null | Zone type (picking, reserve, bulk, cross_dock) |
| `priority_level` | integer | Yes | >= 1 | Lower = closer to dispatch (1 = highest) |
| `distance_to_dispatch` | float | Yes | >= 0 | Relative distance to dispatch area |
| `max_volume_capacity` | float | Yes | > 0 | Maximum volume capacity |
| `max_weight_capacity` | float | Yes | > 0 | Maximum weight capacity |

### 1.3 Location (`locations` — `data/synthetic/locations.csv`)

Physical storage location.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `location_id` | string | Yes | PK, unique, not null | Unique location identifier |
| `zone_id` | string | Yes | FK → `zones.zone_id`, not null | Parent zone |
| `aisle` | string | Yes | Not null | Aisle identifier |
| `rack` | string | No | Nullable | Rack identifier |
| `level` | string | No | Nullable | Level within rack |
| `max_volume_capacity` | float | Yes | > 0 | Maximum volume for this location |
| `max_weight_capacity` | float | Yes | > 0 | Maximum weight for this location |

### 1.4 Inventory (`inventory` — `data/synthetic/inventory.csv`)

Current inventory snapshot.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `sku_id` | string | Yes | FK → `skus.sku_id`, not null | SKU in storage |
| `location_id` | string | Yes | FK → `locations.location_id`, not null | Storage location |
| `units_on_hand` | integer | Yes | >= 0 | Current units stored |
| `occupied_volume` | float | Yes | >= 0 | Volume currently used |
| `occupied_weight` | float | Yes | >= 0 | Weight currently used |

### 1.5 Orders (`orders` — `data/synthetic/orders.csv`)

Order header data (synthetic demand).

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `order_id` | string | Yes | PK, unique, not null | Unique order identifier |
| `order_date` | date | Yes | Not null | Order date |
| `channel` | string | No | Nullable | Sales channel (online, retail, wholesale) |

### 1.6 Order Lines (`order_lines` — `data/synthetic/order_lines.csv`)

Line items within orders.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `order_id` | string | Yes | FK → `orders.order_id`, not null | Parent order |
| `sku_id` | string | Yes | FK → `skus.sku_id`, not null | Ordered SKU |
| `quantity` | integer | Yes | > 0 | Quantity ordered |

---

## 2. Validation rules

### 2.1 Mandatory checks

| Rule | Applies to | Validation method |
|------|-----------|-------------------|
| Required fields must not be null | All entities | pandera `nullable=False` or explicit `notna()` check |
| Primary keys must be unique | `skus.sku_id`, `zones.zone_id`, `locations.location_id`, `orders.order_id` | pandera `unique=True` or explicit `duplicated()` check |
| Capacities > 0 | `zones.max_volume_capacity`, `zones.max_weight_capacity`, `locations.max_volume_capacity`, `locations.max_weight_capacity` | pandera `gt=0` or explicit `<= 0` check |
| SKU volume/weight > 0 | `skus.unit_volume`, `skus.unit_weight` | pandera `gt=0` or explicit `<= 0` check |
| Inventory >= 0 | `inventory.units_on_hand`, `inventory.occupied_volume`, `inventory.occupied_weight` | pandera `ge=0` or explicit `< 0` check |
| Rotation class valid | `skus.rotation_class` | pandera `isin=["A","B","C","D"]` or explicit `~isin()` check |
| Quantity > 0 | `order_lines.quantity` | pandera `gt=0` or explicit `<= 0` check |

### 2.2 Referential integrity

| Rule | Applies to | Validation method |
|------|-----------|-------------------|
| `inventory.sku_id` must reference a valid `skus.sku_id` | `inventory` → `skus` | Explicit `isin()` check against SKU master |
| `inventory.location_id` must reference a valid `locations.location_id` | `inventory` → `locations` | Explicit `isin()` check against location master |
| `locations.zone_id` must reference a valid `zones.zone_id` | `locations` → `zones` | Explicit `isin()` check against zones |
| `order_lines.order_id` must reference a valid `orders.order_id` | `order_lines` → `orders` | Explicit `isin()` check against orders |
| `order_lines.sku_id` must reference a valid `skus.sku_id` | `order_lines` → `skus` | Explicit `isin()` check against SKU master |

### 2.3 Feature output checks

| Rule | Applies to | Validation method |
|------|-----------|-------------------|
| Feature outputs must not silently drop critical records | All feature transforms | Assert `len(features) == len(skus)` in `build_all_features` |
| Aggregations must preserve referential integrity | Derived datasets | FK checks during `load_all_datasets(validate=True)` |

---

## 3. Validation implementation

Validation uses a **two-tier strategy**:

1. **Tier 1 (pandera)**: `DataFrameModel` schemas with field-level constraints (`nullable`, `unique`, `gt`, `ge`, `isin`). Pandera 0.31.x is compatible with pandas 3.0.3 and Python 3.13.5.
2. **Tier 2 (explicit fallback)**: If pandera import fails, validation falls back to explicit pandas functions (`notna()`, `duplicated()`, comparison operators) that reproduce the same rules.

All validation functions are in `src/slotting_optimization_engine/data/validation.py`.

---

## 4. File formats

| Dataset | Format | Location | Compressed |
|---------|--------|----------|------------|
| All synthetic source data | CSV | `data/synthetic/*.csv` | No |
| Slotting features | Parquet | `data/processed/slotting_features.parquet` | Yes (built-in) |
| Location/zone utilisation | CSV | `data/processed/*.csv` | No |
| Diagnostic outputs | CSV | `data/processed/*_diagnostics.csv`, `diagnostic_summary.csv` | No |
| Scoring outputs | CSV | `data/processed/slotting_opportunity_scores.csv`, `priority_recommendation_queue.csv`, `scoring_summary.csv` | No |
| Scenario outputs | CSV | `data/processed/scenario_comparison.csv`, `scenario_action_mix.csv`, `scenario_summary.csv` | No |
| Optimization outputs | CSV | `data/processed/optimization_assignments.csv`, `optimization_summary.csv`, `optimization_cost_matrix.csv` | No |
| Simulation outputs | CSV | `data/processed/simulation_summary.csv`, `simulation_travel_aggregate.csv`, `simulation_zone_impact.csv`, `simulation_throughput_scenarios.csv`, `simulation_order_detail.csv` | No |

---

## 5. Phase 2 diagnostic output schemas

All diagnostic thresholds are `inferred / pending confirmation`. Outputs are descriptive only and do not contain recommended moves, scores for prioritization, optimization decisions, or simulation results.

### 5.1 Slotting Diagnostics (`slotting_diagnostics.csv`)

| Field | Description |
|-------|-------------|
| `sku_id`, `category`, `rotation_class` | SKU identifiers and taxonomy copied from Phase 1 features |
| `total_demand`, `order_count` | Phase 1 demand features |
| `location_count`, `zone_count` | Count of current SKU placements from validated synthetic inventory/location context |
| `distance_to_dispatch`, `priority_level`, `min_priority_level` | Current placement distance/priority evidence |
| `high_demand_threshold`, `low_demand_threshold`, `long_distance_threshold` | Inferred threshold values used for flags |
| `is_high_demand`, `is_low_demand_or_rotation` | Demand/rotation classification indicators |
| `has_long_distance_placement`, `has_low_priority_placement`, `occupies_premium_zone` | Placement condition flags |
| `high_demand_poor_placement_flag` | Descriptive flag for high demand SKUs in long-distance or low-priority placements |
| `low_demand_premium_zone_flag` | Descriptive flag for low-demand/slow-rotation SKUs occupying premium zones |
| `diagnostic_count`, `diagnostic_severity` | Count and label for number of triggered descriptive flags |
| `business_rule_state` | Always `inferred / pending confirmation` for Phase 2 |

### 5.2 Location Diagnostics (`location_diagnostics.csv`)

Includes Phase 1 location utilization fields plus `category_count`, `assigned_sku_count`, `total_location_demand`, `avg_utilization_pct`, `overutilized_flag`, `underutilized_flag`, `density_concern_flag`, `category_mix_flag`, `diagnostic_count`, and `business_rule_state`.

### 5.3 Zone Diagnostics (`zone_diagnostics.csv`)

Includes Phase 1 zone utilization fields plus `assigned_sku_count`, `low_demand_sku_count`, `slow_rotation_sku_count`, `avg_utilization_pct`, `overutilized_zone_flag`, `underutilized_zone_flag`, `premium_zone_slow_mover_flag`, and `business_rule_state`.

### 5.4 Category Diagnostics (`category_diagnostics.csv`)

| Field | Description |
|-------|-------------|
| `category` | SKU category |
| `zone_count`, `location_count`, `sku_count` | Spread and placement counts |
| `total_demand` | Demand represented by category placements |
| `top_zone_sku_share` | Share of category SKUs in the most represented zone |
| `category_spread_flag` | Category spans at least the inferred zone-count threshold |
| `category_misgrouping_indicator` | Category is spread and lacks dominant-zone concentration |
| `business_rule_state` | `inferred / pending confirmation` |

### 5.5 Diagnostic Summary (`diagnostic_summary.csv`)

One row per diagnostic metric with `metric`, `value`, `business_rule_state`, and `threshold_note`.

---

## 6. Assumptions

1. **Synthetic data only**: Phase 1 uses generated data that follows known distributions. Real data is not available.
2. **CSV as exchange format**: Source data is stored and loaded from CSV files. Parquet is used for feature outputs.
3. **Daily batch processing**: The pipeline assumes daily data snapshots, not real-time streaming.
4. **Single DC model**: The initial engine models a single distribution center.
5. **Metric units**: Volume in cubic centimeters; weight in kilograms.
6. **Deterministic generation**: All synthetic data is reproducible with seed=42.
7. **Diagnostic thresholds pending confirmation**: Phase 2 uses simple quantile and utilization thresholds for review only.
8. **Scoring weights pending confirmation**: Phase 3 weights are transparent, inferred, and not approved business policy.
9. **Scenario lenses pending confirmation**: Phase 4 scenario weights and top-N settings are analytical assumptions, not operating policy.
10. **Optimization weights pending confirmation**: Phase 5 costs and zone-slot limits are inferred and must not be treated as approved warehouse policy.
11. **Simulation assumptions pending confirmation**: Phase 6 parameters (picker speed 1.2 m/s, pick time 30 s, overhead 120 s, throughput multipliers 1.03/1.08/1.15) are inferred and not certified warehouse standards.

---

## 7. Phase 3 scoring output schemas

All Phase 3 scoring outputs are `inferred / pending confirmation`. They prioritize human review and do not contain optimal moves, target slots, scenario comparisons, solver output, or simulation results.

### 7.1 Slotting Opportunity Scores (`slotting_opportunity_scores.csv`)

| Field | Description |
|-------|-------------|
| `entity_type` | Scored entity type, currently `sku` or `zone` |
| `entity_id` | SKU or zone identifier |
| `candidate_action` | Review label such as `review_high_demand_far_sku`, `review_slow_mover_in_premium_zone`, or `review_zone_capacity_pressure` |
| `opportunity_score` | Prioritization score clipped to 0-100 |
| `reason` | Human-readable explanation of the diagnostic signal |
| `priority` | `high`, `medium`, or `low` from inferred score thresholds |
| `rank` | Descending rank by score |
| `business_rule_state` | Always `inferred / pending confirmation` for Phase 3 |
| `scoring_note` | Explicit non-optimization caveat |

### 7.2 Priority Recommendation Queue (`priority_recommendation_queue.csv`)

Sorted review queue for opportunities with score >= configured queue threshold. Despite the filename, recommendations are candidate review actions only, not optimal movement instructions.

| Field | Description |
|-------|-------------|
| `queue_position` | 1-based sorted queue position |
| `priority` | Priority label |
| `opportunity_score` | 0-100 prioritization score |
| `entity_type`, `entity_id` | Entity under review |
| `candidate_action` | Candidate review action label |
| `reason` | Diagnostic/scoring explanation |
| `business_rule_state` | `inferred / pending confirmation` |
| `scoring_note` | Non-optimization caveat |

### 7.3 Scoring Summary (`scoring_summary.csv`)

One row per scoring metric with `metric`, `value`, `business_rule_state`, `scoring_note`, and `config_snapshot`. The config snapshot records every inferred weight and threshold.

---

## 8. Phase 4 scenario output schemas

All Phase 4 scenario outputs are `inferred / pending confirmation`. They compare analytical lenses over Phase 3 scores and do not contain optimal moves, target slots, solver output, simulation results, or executable movement plans.

### 8.1 Scenario Comparison (`scenario_comparison.csv`)

Top-N selected rows per scenario/model variant.

| Field | Description |
|-------|-------------|
| `scenario` | Scenario lens name, e.g. `baseline`, `demand_first`, `capacity_first`, `balanced_review` |
| `scenario_rank` | 1-based rank within that scenario lens |
| `scenario_weighted_score` | Reweighted score used for within-scenario comparison only |
| `scenario_description` | Human-readable scenario assumption summary |
| `scenario_top_n` | Number of selected rows requested for the scenario |
| `entity_type`, `entity_id` | Entity under analytical review, currently SKU or zone |
| `candidate_action` | Candidate review action inherited from Phase 3 |
| `priority`, `opportunity_score`, `rank`, `reason` | Phase 3 score context copied for traceability |
| `business_rule_state` | Phase 3 assumption state |
| `scenario_assumption_state` | Phase 4 scenario assumption state, currently `inferred / pending confirmation` |
| `scenario_note` | Explicit caveat that this is analytical what-if comparison only |

### 8.2 Scenario Action Mix (`scenario_action_mix.csv`)

One row per scenario/action combination with selected count, share, high-priority count, average opportunity score, total weighted opportunity, assumption state, and scenario caveat.

### 8.3 Scenario Summary (`scenario_summary.csv`)

One row per scenario with selected count, top-N, total weighted opportunity, average scores, high-priority count, SKU/zone emphasis counts, candidate-action coverage, dominant action, assumption state, scenario caveat, and config snapshot.

---

## 9. Phase 5 optimization output schemas

All Phase 5 optimization outputs are `inferred / pending confirmation`. They are a controlled mathematical prototype over synthetic data and do not contain executable move tasks, WMS/ERP integrations, simulation results, or guaranteed feasible physical locations.

### 9.1 Optimization Assignments (`optimization_assignments.csv`)

One row per selected SKU assignment to a target zone slot.

| Field | Description |
|-------|-------------|
| `assignment_rank` | 1-based order returned by the assignment method |
| `sku_id` | Selected SKU from the Phase 3 priority queue |
| `target_zone_id` | Candidate target zone, not a physical location |
| `target_zone_slot` | Logical expanded zone slot used only to allow rectangular assignment |
| `candidate_action`, `opportunity_score` | Phase 3 review context copied for traceability |
| `total_demand`, `rotation_class` | SKU demand/rotation context |
| `zone_priority_level`, `zone_distance_to_dispatch`, `zone_capacity_pressure` | Zone cost drivers |
| `scenario_weighted_score` | Best available Phase 4 scenario context for the SKU |
| `assignment_cost` | Transparent weighted minimization cost; lower is preferred by the prototype |
| `solver_method` | `scipy_linear_sum_assignment` or `greedy_fallback` |
| `assumption_state` | Always `inferred / pending confirmation` for Phase 5 |
| `optimization_caveat` | Explicit prototype/no-execution/no-location-feasibility caveat |
| `config_snapshot` | Inferred weights and limits used for the run |

### 9.2 Optimization Summary (`optimization_summary.csv`)

One row per metric: selected SKUs, assigned rows, candidate zone slots, target zones used, average assignment cost, total assignment cost, solver method, assumption state, caveat, and config snapshot.

### 9.3 Optimization Cost Matrix (`optimization_cost_matrix.csv`)

One row per SKU-zone-slot candidate pair with the same cost driver fields used by the assignment output. This table exists for auditability and explains why the prototype selected a lower-cost pairing.

---

## 10. Phase 6 simulation output schemas

All Phase 6 simulation outputs are `inferred / pending confirmation`. They are an operational impact prototype over synthetic data and do not replace certified warehouse engineering models, labour standards, or time-and-motion studies.

### 10.1 Simulation Summary (`simulation_summary.csv`)

| Field | Description |
|-------|-------------|
| `metric` | Metric name: run_timestamp, dataset_description, total_skus, total_orders, total_order_lines, total_zones, total_locations, total_inventory_records, optimized_sku_count, current_total_distance_m, optimized_total_distance_m, distance_saved_m, current_total_time_s, optimized_total_time_s, time_saved_s, avg_improvement_pct, gini_current, gini_optimized, balance_improved, orders_per_shift_current, orders_per_shift_optimized, throughput_gain_pct, assumption_state |
| `value` | Metric value |
| `note` | Optional caveat or description |

### 10.2 Simulation Travel Aggregate (`simulation_travel_aggregate.csv`)

| Field | Description |
|-------|-------------|
| `scenario` | Always `current_vs_optimized` |
| `current_total_distance_m` | Sum of travel distance across all orders using current SKU zones |
| `optimized_total_distance_m` | Sum of travel distance using optimized SKU zones (from Phase 5) |
| `distance_saved_m` | Difference (current - optimized) |
| `current_total_time_s` | Sum of travel time (distance / speed) across all orders |
| `optimized_total_time_s` | Optimized travel time |
| `time_saved_s` | Difference (current - optimized) |
| `avg_improvement_pct` | Average per-order improvement percentage |

### 10.3 Simulation Zone Impact (`simulation_zone_impact.csv`)

| Field | Description |
|-------|-------------|
| `zone_id` | Zone identifier |
| `zone_type` | Zone classification |
| `priority_level` | Priority level (1 = highest) |
| `current_pick_count` | Number of picks in this zone under current assignment |
| `optimized_pick_count` | Number of picks under optimized assignment |
| `pick_change` | Change in pick count (optimized - current) |
| `pick_change_pct` | Percentage change |
| `gini_coefficient_current` | Gini across all zones (current) — 0 = perfect equality |
| `gini_coefficient_optimized` | Gini across all zones (optimized) |

### 10.4 Simulation Throughput Scenarios (`simulation_throughput_scenarios.csv`)

| Field | Description |
|-------|-------------|
| `scenario` | Scenario name: `optimistic`, `balanced`, or `conservative` |
| `total_time_saved_s` | Total travel time saved from the travel simulation |
| `time_saved_with_multiplier_s` | Time saved × scenario throughput multiplier |
| `orders_per_shift_before` | Estimated orders per shift without optimization |
| `orders_per_shift_after` | Estimated orders per shift with optimization under this scenario |
| `throughput_gain_pct` | Percentage gain in orders per shift |
| `throughput_multiplier` | The multiplier applied (1.15, 1.08, or 1.03) |
| `note` | Scenario description and caveat |

### 10.5 Simulation Order Detail (`simulation_order_detail.csv`)

| Field | Description |
|-------|-------------|
| `order_id` | Order identifier |
| `line_count` | Number of order lines in this order |
| `current_distance_m` | Current travel distance for this order |
| `optimized_distance_m` | Optimized travel distance for this order |
| `distance_saved_m` | Difference |
| `current_time_s` | Current travel time |
| `optimized_time_s` | Optimized travel time |
| `time_saved_s` | Difference |
| `current_zone_ids` | Pipe-delimited list of current zone IDs visited |
| `optimized_zone_ids` | Pipe-delimited list of optimized zone IDs visited |

### 10.6 Caveat column

Every simulation output includes an `assumption_state` column set to `inferred / pending confirmation`.

---

## 11. Open questions (resolved)

| Question | Resolution |
|----------|-----------|
| Location capacity units | Absolute values (cm³/kg), utilisation expressed as percentage |
| Synthetic dataset sizes | Configurable via `GenerationConfig`; defaults: 500 SKUs, 10 zones, 200 locations, 2000 orders |
| Multi-tenant (multiple DCs) | Deferred — single DC model for Phase 1 |
| Feature drop tolerance | Zero tolerance — build_all_features asserts row-count preservation |
| Validation library choice | Pandera primary + explicit fallback (two-tier strategy) |
