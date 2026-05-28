"""
Synthetic data generation for slotting optimization.

Generates six internally consistent datasets:
    - skus:      Product master with categories, dimensions, rotation classes.
    - zones:     Logical warehouse zones with capacities and distances.
    - locations: Physical storage locations linked to zones.
    - inventory: Current stock levels by SKU and location.
    - orders:    Synthetic demand order headers.
    - order_lines: Line items within orders.

Trade-off: Synthetic data follows controlled distributions that produce
"interesting" slotting scenarios (mix of fast/slow movers, varied zone
priorities, near-full locations). Real warehouse data would be messier —
feature thresholds will need calibration against real data.

Determinism: All generation uses numpy.random.Generator with a configurable
seed (default 42). Tests can set seed=42 for fully reproducible results.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from slotting_optimization_engine.domain.constants import (
    DEFAULT_LOCATIONS_PER_ZONE,
    DEFAULT_ORDER_COUNT,
    DEFAULT_ORDER_LINES_PER_ORDER_AVG,
    DEFAULT_SKU_COUNT,
    DEFAULT_ZONE_COUNT,
    SYNTHETIC_SEED,
    Inventory,
    Locations,
    OrderLines,
    Orders,
    SalesChannel,
    Skus,
    Zones,
)


@dataclass
class GenerationConfig:
    """Configurable parameters for synthetic data generation.

    Attributes:
        n_skus:              Number of SKU master records.
        n_zones:             Number of warehouse zones.
        locations_per_zone:  Physical locations per zone.
        n_orders:            Number of order headers.
        avg_lines_per_order: Average order lines per order (Poisson lambda).
        seed:                Random seed for deterministic output.
    """
    n_skus: int = DEFAULT_SKU_COUNT
    n_zones: int = DEFAULT_ZONE_COUNT
    locations_per_zone: int = DEFAULT_LOCATIONS_PER_ZONE
    n_orders: int = DEFAULT_ORDER_COUNT
    avg_lines_per_order: int = DEFAULT_ORDER_LINES_PER_ORDER_AVG
    seed: int = SYNTHETIC_SEED


class SyntheticDataGenerator:
    """Generates all synthetic datasets for the slotting engine.

    Usage::

        gen = SyntheticDataGenerator(GenerationConfig(seed=42))
        data = gen.generate_all()
        data["skus"].head()

    The generator guarantees internal consistency: inventory SKUs reference
    existing SKUs, locations reference real zones, order lines reference
    valid orders and SKUs.
    """

    def __init__(self, config: GenerationConfig | None = None):
        self.config = config or GenerationConfig()
        self._rng = np.random.default_rng(self.config.seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_all(self) -> dict[str, pd.DataFrame]:
        """Generate all six datasets in dependency order."""
        skus = self._generate_skus()
        zones = self._generate_zones()
        locations = self._generate_locations(zones)
        inventory = self._generate_inventory(skus, locations)
        orders = self._generate_orders()
        order_lines = self._generate_order_lines(orders, skus)

        return {
            "skus": skus,
            "zones": zones,
            "locations": locations,
            "inventory": inventory,
            "orders": orders,
            "order_lines": order_lines,
        }

    # ------------------------------------------------------------------
    # SKU master
    # ------------------------------------------------------------------

    def _generate_skus(self) -> pd.DataFrame:
        """Generate SKU master data.

        Distribution assumptions:
        - 20 % A (fast), 30 % B, 30 % C, 20 % D (slow).
        - Volumes and weights follow log-normal distributions to simulate
          the order-of-magnitude variety found in real multi-category DCs.
        """
        n = self.config.n_skus

        categories = ["Electronics", "Clothing", "Home & Garden", "Sports",
                       "Food & Beverage"]
        subcategories_map = {
            "Electronics": ["Smartphones", "Laptops", "Accessories", "Audio"],
            "Clothing":     ["Men", "Women", "Kids", "Footwear"],
            "Home & Garden":["Furniture", "Decor", "Tools", "Outdoor"],
            "Sports":       ["Fitness", "Team Sports", "Outdoor", "Swimming"],
            "Food & Beverage": ["Snacks", "Beverages", "Pantry", "Fresh"],
        }

        cat_indices = self._rng.integers(0, len(categories), size=n)
        sku_categories = [categories[i] for i in cat_indices]
        sku_subcategories = [
            self._rng.choice(subcategories_map[categories[ci]])
            for ci in cat_indices
        ]

        # Rotation: A=20%, B=30%, C=30%, D=20% (rough Pareto shape)
        rotation_classes = self._rng.choice(
            ["A", "B", "C", "D"], size=n, p=[0.20, 0.30, 0.30, 0.20],
        )

        # Avg daily demand: A >> B > C >> D
        demand_base = {"A": 100.0, "B": 40.0, "C": 15.0, "D": 3.0}
        avg_daily_demand = [
            max(0.1, demand_base[rc] * self._rng.lognormal(0, 0.5))
            for rc in rotation_classes
        ]

        # Physical dimensions — log-normal produces realistic variety
        unit_volume = np.maximum(
            0.01, self._rng.lognormal(mean=3.0, sigma=1.5, size=n),
        )
        unit_weight = np.maximum(
            0.01, self._rng.lognormal(mean=1.0, sigma=1.2, size=n),
        )

        return pd.DataFrame({
            Skus.SKU_ID:          [f"SKU-{i:05d}" for i in range(1, n + 1)],
            Skus.CATEGORY:        sku_categories,
            Skus.SUBCATEGORY:     sku_subcategories,
            Skus.UNIT_VOLUME:     np.round(unit_volume, 2),
            Skus.UNIT_WEIGHT:     np.round(unit_weight, 3),
            Skus.ROTATION_CLASS:  rotation_classes.tolist(),
            Skus.AVG_DAILY_DEMAND: np.round(avg_daily_demand, 1),
        })

    # ------------------------------------------------------------------
    # Zones
    # ------------------------------------------------------------------

    def _generate_zones(self) -> pd.DataFrame:
        """Generate warehouse zone definitions.

        Priority 1 = closest to dispatch. Premium picking zones have smaller
        capacity (expensive space), while reserve/bulk zones have larger
        capacity but are farther from dispatch.
        """
        n = self.config.n_zones

        # Cycle zone types to support arbitrary counts
        base_types = ["picking", "picking", "picking",
                       "reserve", "reserve", "reserve", "reserve",
                       "bulk", "bulk", "cross_dock"]
        zone_types = (base_types * (n // len(base_types) + 1))[:n]

        zone_ids = [f"Z-{i:02d}" for i in range(1, n + 1)]
        priority = list(range(1, n + 1))

        # Distance increases with priority level (higher number = farther)
        distance = [10.0 + (p - 1) * 15.0 for p in priority]

        # Capacity inversely proportional to priority (premium = smaller)
        max_vol = [max(500.0, 5000.0 - (p - 1) * 400.0) for p in priority]
        max_wt  = [max(200.0, 2000.0 - (p - 1) * 150.0) for p in priority]

        return pd.DataFrame({
            Zones.ZONE_ID:              zone_ids,
            Zones.ZONE_TYPE:            zone_types,
            Zones.PRIORITY_LEVEL:       priority,
            Zones.DISTANCE_TO_DISPATCH: distance,
            Zones.MAX_VOLUME_CAPACITY:  max_vol,
            Zones.MAX_WEIGHT_CAPACITY:  max_wt,
        })

    # ------------------------------------------------------------------
    # Locations
    # ------------------------------------------------------------------

    def _generate_locations(self, zones: pd.DataFrame) -> pd.DataFrame:
        """Generate physical storage locations linked to zones.

        Each zone gets ``locations_per_zone`` locations. Location capacities
        are proportional to the parent zone's capacity per-location, with
        +/- 20% random variation to simulate real variability.
        """
        records: list[dict] = []
        loc_idx = 0

        for _, zone in zones.iterrows():
            for _ in range(self.config.locations_per_zone):
                aisle = chr(65 + loc_idx // 10)   # A, B, C …
                rack  = f"R-{loc_idx % 10 + 1}"
                level = f"L-{int(self._rng.integers(1, 5))}"
                loc_idx += 1

                dz = self.config.locations_per_zone
                vol_cap = max(
                    100.0,
                    zone[Zones.MAX_VOLUME_CAPACITY] / dz
                    * self._rng.uniform(0.8, 1.2),
                )
                wt_cap = max(
                    50.0,
                    zone[Zones.MAX_WEIGHT_CAPACITY] / dz
                    * self._rng.uniform(0.8, 1.2),
                )

                records.append({
                    Locations.LOCATION_ID:       f"LOC-{loc_idx:06d}",
                    Locations.ZONE_ID:           str(zone[Zones.ZONE_ID]),
                    Locations.AISLE:             aisle,
                    Locations.RACK:              str(rack),
                    Locations.LEVEL:             str(level),
                    Locations.MAX_VOLUME_CAPACITY: round(vol_cap, 1),
                    Locations.MAX_WEIGHT_CAPACITY: round(wt_cap, 1),
                })

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    def _generate_inventory(
        self, skus: pd.DataFrame, locations: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate inventory snapshot.

        Business rules / assumptions:
        - Each active location holds 1-4 SKUs.
        - ~10 % of locations are empty (realistic for a DC).
        - Stock-on-hand covers roughly 1-30 days of avg daily demand.
        - Occupied volume/weight = units * SKU unit dimensions.
        """
        records: list[dict] = []
        sku_ids = skus[Skus.SKU_ID].tolist()
        loc_ids = locations[Locations.LOCATION_ID].tolist()

        sku_dims = skus.set_index(Skus.SKU_ID)[[Skus.UNIT_VOLUME,
                                                  Skus.UNIT_WEIGHT]]

        # 90 % of locations receive inventory
        active_locs = loc_ids[:int(len(loc_ids) * 0.9)]

        for loc in active_locs:
            n_skus = int(self._rng.integers(1, 5))
            chosen = self._rng.choice(
                sku_ids, size=min(n_skus, len(sku_ids)), replace=False,
            )

            for sku in chosen:
                unit_vol = sku_dims.loc[sku, Skus.UNIT_VOLUME]
                unit_wt  = sku_dims.loc[sku, Skus.UNIT_WEIGHT]

                demand_val = skus.loc[
                    skus[Skus.SKU_ID] == sku, Skus.AVG_DAILY_DEMAND
                ].values
                avg_demand = demand_val[0] if len(demand_val) else 1.0

                units = max(1, int(self._rng.exponential(scale=avg_demand * 7)))

                records.append({
                    Inventory.SKU_ID:          sku,
                    Inventory.LOCATION_ID:     loc,
                    Inventory.UNITS_ON_HAND:   units,
                    Inventory.OCCUPIED_VOLUME: round(units * unit_vol, 2),
                    Inventory.OCCUPIED_WEIGHT: round(units * unit_wt, 3),
                })

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def _generate_orders(self) -> pd.DataFrame:
        """Generate synthetic order headers.

        Orders span a 90-day window (Jan-Mar 2026).
        Channel mix: online ~50 %, retail ~30 %, wholesale ~20 %.
        """
        n = self.config.n_orders
        start = pd.Timestamp("2026-01-01")
        end   = pd.Timestamp("2026-03-31")
        date_span = (end - start).days

        order_dates = [
            start + pd.Timedelta(days=int(d))
            for d in self._rng.integers(0, date_span + 1, size=n)
        ]

        channels = self._rng.choice(
            [c.value for c in SalesChannel],
            size=n, p=[0.5, 0.3, 0.2],
        )

        return pd.DataFrame({
            Orders.ORDER_ID:   [f"ORD-{i:07d}" for i in range(1, n + 1)],
            Orders.ORDER_DATE: order_dates,
            Orders.CHANNEL:    channels.tolist(),
        })

    # ------------------------------------------------------------------
    # Order lines
    # ------------------------------------------------------------------

    def _generate_order_lines(
        self, orders: pd.DataFrame, skus: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate order line items.

        Business assumption: High-rotation SKUs appear in more orders.
        Weighted sampling: A-class SKUs are ~4× more likely than D-class.

        Each order has 1-10 lines (Poisson with avg_lines_per_order mean,
        clamped to [1, 10]).
        """
        sku_ids = skus[Skus.SKU_ID].tolist()

        rotation_map = dict(zip(
            skus[Skus.SKU_ID].tolist(),
            skus[Skus.ROTATION_CLASS].tolist(),
        ))

        # Sampling weights: A=4, B=3, C=2, D=1
        wmap = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0}
        weights = np.array([wmap.get(rotation_map[s], 1.0) for s in sku_ids],
                           dtype=float)
        weights /= weights.sum()

        records: list[dict] = []
        for oid in orders[Orders.ORDER_ID]:
            n_lines = min(10, max(1,
                                  int(self._rng.poisson(
                                      self.config.avg_lines_per_order))))

            chosen = self._rng.choice(sku_ids, size=n_lines, p=weights,
                                      replace=True)
            for sku in chosen:
                qty = max(1, int(self._rng.exponential(scale=2.5)))
                records.append({
                    OrderLines.ORDER_ID: oid,
                    OrderLines.SKU_ID:   sku,
                    OrderLines.QUANTITY: qty,
                })

        return pd.DataFrame(records)


# ===========================================================================
# Convenience function
# ===========================================================================

def generate_all_datasets(
    config: GenerationConfig | None = None,
) -> dict[str, pd.DataFrame]:
    """One-call convenience wrapper around SyntheticDataGenerator."""
    return SyntheticDataGenerator(config).generate_all()
