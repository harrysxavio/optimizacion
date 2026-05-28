"""
Phase 6 — Simulation configuration and documented assumptions.

Every assumption is explicitly stated and marked as
``inferred / pending confirmation`` so that business users must review
and validate them before treating simulation outputs as operational
estimates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from slotting_optimization_engine.scoring.prioritization import BUSINESS_RULE_STATE

SIMULATION_CAVEAT: str = (
    "Phase 6 operational simulation prototype on synthetic data with "
    "inferred assumptions; not a certified warehouse engineering model, "
    "not a labour standard, and not a replacement for time-and-motion studies."
)


@dataclass(frozen=True)
class SimulationConfig:
    """Inferred parameters and assumptions for Phase 6 simulation.

    All values are *inferred / pending confirmation* — they are reasonable
    defaults for a synthetic-data prototype but MUST be calibrated against
    real warehouse data before operational use.
    """

    # ── Travel assumptions ──────────────────────────────────────────────
    picker_speed_m_per_s: float = 1.0
    """Average picker walking speed (m/s) including minor delays.

    Typical DC walking speed ranges from 0.8–1.2 m/s depending on aisle
    width, congestion, and equipment (cart vs. pallet jack). 1.0 m/s is a
    conservative mid-point for an unloaded picker on a straight aisle.
    """

    pick_time_per_sku_s: float = 5.0
    """Time to physically pick one SKU unit (reach, scan, place).

    Does NOT include travel time — that is modelled separately. Real
    pick times vary by SKU size, weight, packaging, and whether the
    picker uses voice, RF scanner, or pick-to-light. 5 s is a plausible
    average for small-to-medium e-commerce items.
    """

    travel_overhead_factor: float = 1.3
    """Multiplier accounting for indirect travel (aisle entry, back-tracking).

    Straight-line zone-to-dispatch distance under-estimates real walk
    paths by roughly 20–40 % depending on layout. 1.3 is a middle-ground
    assumption for a typical rectangular warehouse with parallel aisles.
    """

    # ── Shift / volume assumptions ──────────────────────────────────────
    seconds_per_shift: int = 28_800
    """8-hour shift in seconds (8 × 3 600)."""

    productive_utilization_pct: float = 0.80
    """Fraction of shift spent on productive picking (vs. breaks, meetings).

    Industry benchmarks range from 75–90 % for standard shifts. 80 % is
    a typical planning value.
    """

    # ── Throughput scenario multipliers ────────────────────────────────
    optimistic_throughput_mult: float = 1.15
    """Best-case throughput multiplier from optimisation (15 % uplift)."""

    balanced_throughput_mult: float = 1.08
    """Balanced-case throughput multiplier (8 % uplift)."""

    conservative_throughput_mult: float = 1.03
    """Conservative / worst-case throughput multiplier (3 % uplift)."""

    # ── Top-N settings for detail output ────────────────────────────────
    top_n_orders_detail: int = 20
    """Number of highest-impact orders to include in the order detail CSV."""

    top_n_skus_detail: int = 20
    """Number of highest-impact SKUs to include in the SKU detail CSV."""

    # ── State metadata ──────────────────────────────────────────────────
    assumption_state: str = BUSINESS_RULE_STATE
    simulation_caveat: str = SIMULATION_CAVEAT

    # ── Human-readable labels for each assumption ───────────────────────
    ASSUMPTION_DESCRIPTIONS: ClassVar[dict[str, str]] = {
        "picker_speed_m_per_s": (
            "Velocidad media del picker caminando (m/s). Rango típico "
            "0.8–1.2. 1.0 es un punto medio conservador."
        ),
        "pick_time_per_sku_s": (
            "Tiempo físico de pick por SKU (alcanzar, escanear, colocar). "
            "5 s es un promedio plausible para e-commerce liviano."
        ),
        "travel_overhead_factor": (
            "Factor de ajuste por distancia indirecta (pasillos, retrocesos). "
            "1.3 = +30 % sobre distancia lineal a despacho."
        ),
        "seconds_per_shift": "Duración del turno en segundos (8 h = 28 800 s).",
        "productive_utilization_pct": (
            "Fracción del turno dedicada a picking productivo (vs. pausas, "
            "reuniones). 80 % es un valor de planificación típico."
        ),
        "optimistic_throughput_mult": (
            "Multiplicador de throughput en escenario optimista (15 % de mejora)."
        ),
        "balanced_throughput_mult": (
            "Multiplicador de throughput en escenario balanceado (8 % de mejora)."
        ),
        "conservative_throughput_mult": (
            "Multiplicador de throughput en escenario conservador (3 % de mejora)."
        ),
    }
