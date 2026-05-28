"""
features — Analytical feature construction for slotting analysis.

Transforms raw data into derived features used by diagnostics,
prescriptive scoring, and optimization modules.

Phase 1 features:
    - Demand by SKU.
    - Picking frequency.
    - Volume and weight footprint.
    - Location and zone capacity utilisation.
    - Rotation classification.
    - Relative distance indicators.

These features are designed with future prescriptive use in mind,
avoiding dead-end aggregations that would need a full rewrite later.
"""
