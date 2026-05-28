# Business Knowledge — Slotting Optimization Engine

**Last updated:** 2026-05-27  
**Status:** Active (Phase 2)

All rules are marked with their current state per the project governance policy.

---

## Domain concepts

### SKU Rotation Classes

| Class | Meaning | Typical % of SKUs | State |
|-------|---------|-------------------|-------|
| A | Very high rotation (fast movers) | ~20% | `technical pattern` |
| B | High rotation | ~30% | `technical pattern` |
| C | Medium rotation | ~30% | `technical pattern` |
| D | Low rotation (slow movers) | ~20% | `technical pattern` |

### Warehouse Zone Types

| Type | Purpose | Priority | State |
|------|---------|----------|-------|
| picking | Fast-access area for order picking | Highest | `technical pattern` |
| reserve | Bulk storage for replenishment | Medium | `technical pattern` |
| cross_dock | Temporary staging for cross-docked goods | Medium | `technical pattern` |
| bulk | Long-term storage | Lowest | `technical pattern` |

---

## Business Rules

### Inventory

| Rule | State |
|------|-------|
| Each active location can hold 1-4 SKUs | `inferred / pending confirmation` |
| ~10% of locations are typically empty | `inferred / pending confirmation` |
| Stock-on-hand covers roughly 1-30 days of avg daily demand | `inferred / pending confirmation` |
| Occupied volume/weight = units × SKU unit dimensions | `technical pattern` |

### Order Distribution

| Rule | State |
|------|-------|
| Online channel represents ~50% of orders | `inferred / pending confirmation` |
| Retail channel represents ~30% of orders | `inferred / pending confirmation` |
| Wholesale channel represents ~20% of orders | `inferred / pending confirmation` |
| High-rotation SKUs (class A) appear ~4× more often in orders than low-rotation (class D) | `inferred / pending confirmation` |
| Most orders contain 1-10 line items (Poisson-distributed) | `technical pattern` |

### Feature Heuristics

| Rule | State |
|------|-------|
| Alignment score thresholds (top 20% demand, median distance) are arbitrary and dataset-dependent | `inferred / pending confirmation` |
| ⚠️ Alignment score is NON-PRESCRIPTIVE — it flags patterns for human review, not automated decisions | `technical pattern` |
| Utilisation is capped at 100% for reporting; over-capacity is flagged separately | `technical pattern` |
| Phase 2 high-demand threshold uses the 80th percentile of `total_demand` | `inferred / pending confirmation` |
| Phase 2 low-demand threshold uses the 20th percentile of `total_demand` | `inferred / pending confirmation` |
| Phase 2 long-distance threshold uses the 75th percentile of placement distance | `inferred / pending confirmation` |
| Premium zones are priority level <= 2 for diagnostic review | `inferred / pending confirmation` |
| Low-priority placement is priority level >= 3 for diagnostic review | `inferred / pending confirmation` |
| Overutilized locations/zones are avg utilization >= 85%; underutilized are <= 20% | `inferred / pending confirmation` |

### Capacity and Utilisation

| Rule | State |
|------|-------|
| Premium zones (high priority, closer to dispatch) have smaller capacity | `inferred / pending confirmation` |
| Location capacity is proportional to zone capacity divided by locations per zone, ±20% | `inferred / pending confirmation` |

---

## Known KPIs (Phase 1 descriptive)

| KPI | Definition | Source |
|-----|-----------|--------|
| Total demand per SKU | Sum of quantities in order_lines | `features.builder.build_demand_by_sku` |
| Picking frequency per SKU | Count of distinct orders containing SKU | `features.builder.build_demand_by_sku` |
| Volume utilisation % | (occupied_volume / max_volume_capacity) × 100 | `features.builder.build_location_utilization` |
| Weight utilisation % | (occupied_weight / max_weight_capacity) × 100 | `features.builder.build_location_utilization` |
| SKU count per location | Distinct SKUs assigned to a location | `features.builder.build_location_utilization` |
| High-demand poor placement count | SKUs above inferred demand threshold with long-distance or low-priority placement | `diagnostics.rules.build_slotting_diagnostics` |
| Low-demand premium-zone count | Low-demand or slow-rotation SKUs occupying inferred premium zones | `diagnostics.rules.build_slotting_diagnostics` |
| Category spread indicator | Category spans multiple zones without dominant concentration | `diagnostics.rules.build_category_diagnostics` |

---

## Data quality notes

- All Phase 1 data is synthetic with controlled distributions.
- Nulls are only expected in optional fields (subcategory, rack, level, channel).
- Referential integrity is enforced by the generator (no orphaned FKs in clean runs).
- Feature outputs assert row-count preservation against source SKU master.
