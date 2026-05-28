"""
data — Data generation, loading, validation, and transformation.

Phase 1 implements:
    - Synthetic data generation (SKUs, zones, locations, inventory, orders).
    - Data loading from CSV/Parquet into pandas DataFrames.
    - Contract validation using pandera schemas.

Future phases may add:
    - Real WMS/ERP data connectors.
    - Incremental and streaming ingestion.
"""
