# Data Documentation — Slotting Optimization Engine

This directory contains all data-related documentation for the project.

## Structure

```
docs/data/
├── README.md                 # This file — data doc overview
├── dataset-index.md          # All datasets in the project
├── business-knowledge.md     # Business rules, assumptions, KPIs
├── query-log.md              # Historical record of data queries/commands
└── synthetic/
    ├── cleaning-log.md       # Cleaning and validation events
    └── learnings.md          # Reusable patterns and technical learnings
```

## Sources

| Source | Type | Status | Documentation |
|--------|------|--------|---------------|
| `data/synthetic/` | Generated CSV datasets | Active (Phase 1) | `dataset-index.md` |
| `data/processed/` | Derived feature outputs | Active (Phase 1) | `dataset-index.md` |

## Key files

- **`dataset-index.md`** — Complete index of every dataset, its schema, row counts, and lineage.
- **`business-knowledge.md`** — Business rules, domain definitions, and KPIs with state tracking.
- **`query-log.md`** — Record of SQL/data commands executed, for reproducibility.
- **`synthetic/cleaning-log.md`** — Event log of data cleaning and validation runs.
- **`synthetic/learnings.md`** — Technical patterns and learnings from working with synthetic data.
