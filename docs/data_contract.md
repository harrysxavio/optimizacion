# Data Contract — Slotting Optimization Engine

**Status:** FINALISED — Phase 2 diagnostics added.  
**Purpose:** Define data entities, fields, validation rules, file formats, and diagnostic output schemas.  
**Last updated:** 2026-05-27

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

---

## 7. Open questions (resolved)

| Question | Resolution |
|----------|-----------|
| Location capacity units | Absolute values (cm³/kg), utilisation expressed as percentage |
| Synthetic dataset sizes | Configurable via `GenerationConfig`; defaults: 500 SKUs, 10 zones, 200 locations, 2000 orders |
| Multi-tenant (multiple DCs) | Deferred — single DC model for Phase 1 |
| Feature drop tolerance | Zero tolerance — build_all_features asserts row-count preservation |
| Validation library choice | Pandera primary + explicit fallback (two-tier strategy) |
