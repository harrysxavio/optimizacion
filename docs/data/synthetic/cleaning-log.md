# Cleaning Log — Synthetic Data

**Source:** `data/synthetic/`  
**Last updated:** 2026-05-27

---

## 2026-05-27 — Initial generation

**Event:** First generation of all six synthetic datasets.

**Generator:** `SyntheticDataGenerator` (seed=42, default config).

**Output files:** `skus.csv`, `zones.csv`, `locations.csv`, `inventory.csv`, `orders.csv`, `order_lines.csv` → `data/synthetic/`.

**Validation result:** All datasets passed validation (pandera schemas + explicit checks). See `docs/phase_logs/phase_1_terminal_log.md`.

**Issues found:** None at generation time. The generator guarantees:
- Non-null required fields
- Unique primary keys
- Positive capacities and dimensions
- Valid FK references (inventory SKUs exist in SKU master, locations exist in zones, etc.)

**Resolution:** No cleaning required.

**Status:** ✅ Clean

---

## Inferred cleaning rules

| Rule | State | Reason |
|------|-------|--------|
| Generated data is clean by construction — no nulls, no orphan FKs | `technical pattern` | Generator enforces consistency |
| 10% of locations intentionally empty | `technical pattern` | Simulates realistic DC layout |
| Non-prescriptive alignment score must be clearly documented as such | `technical pattern` | Avoids misinterpretation |
