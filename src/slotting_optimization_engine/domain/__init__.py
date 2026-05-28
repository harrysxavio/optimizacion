"""
domain — Business domain concepts and value objects.

Captures the core warehouse ontology: SKUs, zones, locations, inventory,
and the rules that govern how they relate. Keeping domain logic separate
from data pipelines prevents business rules from leaking into infrastructure.

Phase 1 scope:
    - Basic dataclass/pydantic models for domain entities.
    - Validation rules (e.g., capacity must be positive).

Future phases may add:
    - Domain service objects for slotting rules.
    - Complex business invariants.
"""
