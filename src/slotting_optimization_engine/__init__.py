"""
slotting-optimization-engine — Modular slotting optimization for distribution centers.

This package provides the analytical and prescriptive foundation for
slotting optimization in high-volume e-commerce / retail DCs.

Architecture layout:
    config/       — Central configuration and path resolution.
    data/         — Data generation, loading, and contract validation.
    domain/       — Business domain concepts (SKU, zone, location).
    features/     — Analytical feature construction.
    diagnostics/  — Slotting diagnostics (future — placeholder stub).
    optimization/ — Mathematical optimization (future — placeholder stub).
    simulation/   — Operational simulation (future — placeholder stub).
    reporting/    — Outputs and summaries.
    app/          — Streamlit technical UI (Phase 1.5 — placeholder stub).
"""

__version__ = "0.1.0"
