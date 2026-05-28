# Business Knowledge — Slotting Optimization Engine

**Last updated:** 2026-05-28  
**Status:** Active (Phase 5)

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
| Phase 3 prioritization weights are inferred and only order review work | `inferred / pending confirmation` |
| Candidate action labels identify review themes, not approved operational moves | `technical pattern` |
| `review_high_demand_far_sku` flags high-demand SKUs with distance/priority concern for review | `inferred / pending confirmation` |
| `review_slow_mover_in_premium_zone` flags low-demand or slow-rotation SKUs occupying premium access for review | `inferred / pending confirmation` |
| `review_zone_capacity_pressure` flags zones with utilization or premium-zone pressure for review | `inferred / pending confirmation` |
| Phase 4 `baseline` scenario preserves Phase 3 score ordering for comparison | `inferred / pending confirmation` |
| Phase 4 `demand_first` scenario gives extra analytical weight to high-demand far-SKU review labels | `inferred / pending confirmation` |
| Phase 4 `capacity_first` scenario gives extra analytical weight to zone capacity pressure labels | `inferred / pending confirmation` |
| Phase 4 `balanced_review` scenario adds a small priority-label bonus and moderate action emphasis | `inferred / pending confirmation` |
| Scenario outputs are what-if comparison summaries, not optimized plans or movement instructions | `technical pattern` |
| Phase 5 selects top-N SKU candidates from the Phase 3 priority queue for a bounded assignment prototype | `inferred / pending confirmation` |
| Phase 5 cost combines demand, zone distance/priority, capacity pressure, opportunity score, and scenario context | `inferred / pending confirmation` |
| Phase 5 target zone slots are logical solver slots, not confirmed physical locations | `technical pattern` |
| Phase 5 assignments are analytical recommendations only and must not execute SKU moves | `technical pattern` |

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
| Opportunity score | 0-100 inferred review-prioritization score | `scoring.prioritization.build_slotting_opportunity_scores` |
| Priority queue position | Sorted rank for human review queue | `scoring.prioritization.build_priority_queue` |
| Scenario weighted score | Reweighted Phase 3 opportunity score for within-scenario comparison only | `scenarios.comparison.build_scenario_comparison` |
| Candidate action coverage | Count of distinct review action labels selected by a scenario | `scenarios.comparison.build_scenario_summary` |
| Assignment cost | Weighted cost minimized by the Phase 5 prototype | `optimization.assignment.build_assignment_cost_matrix` |
| Solver method | Records whether SciPy or deterministic fallback produced the assignment | `optimization.assignment.solve_assignment` |

---

## Data quality notes

- All Phase 1 data is synthetic with controlled distributions.
- Nulls are only expected in optional fields (subcategory, rack, level, channel).
- Referential integrity is enforced by the generator (no orphaned FKs in clean runs).
- Feature outputs assert row-count preservation against source SKU master.
