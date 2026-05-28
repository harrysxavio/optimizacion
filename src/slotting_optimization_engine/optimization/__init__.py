"""Controlled mathematical optimization prototypes."""

from slotting_optimization_engine.optimization.assignment import (
    OPTIMIZATION_CAVEAT,
    AssignmentConfig,
    build_assignment_cost_matrix,
    build_optimization_outputs,
    build_optimization_summary,
    load_optimization_inputs,
    save_optimization_outputs,
    select_candidate_skus,
    solve_assignment,
)

__all__ = [
    "OPTIMIZATION_CAVEAT",
    "AssignmentConfig",
    "build_assignment_cost_matrix",
    "build_optimization_outputs",
    "build_optimization_summary",
    "load_optimization_inputs",
    "save_optimization_outputs",
    "select_candidate_skus",
    "solve_assignment",
]
