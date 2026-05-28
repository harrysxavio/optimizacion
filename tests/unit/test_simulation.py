"""Unit tests for Phase 6 simulation modules."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from slotting_optimization_engine.simulation.config import (
    SIMULATION_CAVEAT,
    SimulationConfig,
)
from slotting_optimization_engine.simulation.report import (
    build_simulation_report,
    save_simulation_outputs,
)
from slotting_optimization_engine.simulation.throughput import estimate_throughput
from slotting_optimization_engine.simulation.travel import (
    build_sku_current_zone,
    build_sku_optimized_zone,
    simulate_travel,
)
from slotting_optimization_engine.simulation.workload import (
    gini_coefficient,
    simulate_workload,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_zones() -> pd.DataFrame:
    return pd.DataFrame({
        "zone_id": ["Z1", "Z2", "Z3"],
        "zone_type": ["picking", "reserve", "bulk"],
        "priority_level": [1, 2, 3],
        "distance_to_dispatch": [10.0, 50.0, 100.0],
        "max_volume_capacity": [1000, 5000, 10000],
        "max_weight_capacity": [5000, 20000, 50000],
    })


@pytest.fixture
def sample_locations() -> pd.DataFrame:
    return pd.DataFrame({
        "location_id": ["L1", "L2", "L3", "L4"],
        "zone_id": ["Z1", "Z1", "Z2", "Z3"],
        "aisle": ["A1", "A1", "B1", "C1"],
        "rack": ["R1", "R2", "R3", "R4"],
        "level": [1, 2, 1, 1],
        "max_volume_capacity": [100, 100, 200, 500],
        "max_weight_capacity": [500, 500, 1000, 2500],
    })


@pytest.fixture
def sample_inventory() -> pd.DataFrame:
    return pd.DataFrame({
        "sku_id": ["S1", "S2", "S3", "S1", "S4"],
        "location_id": ["L1", "L2", "L3", "L2", "L4"],
        "units_on_hand": [10, 20, 30, 5, 40],
        "occupied_volume": [1.0, 2.0, 3.0, 0.5, 4.0],
        "occupied_weight": [0.5, 1.0, 1.5, 0.25, 2.0],
    })


@pytest.fixture
def sample_order_lines() -> pd.DataFrame:
    return pd.DataFrame({
        "order_id": ["O1", "O1", "O1", "O2", "O2", "O3"],
        "sku_id": ["S1", "S2", "S3", "S1", "S4", "S2"],
        "quantity": [1, 2, 1, 3, 1, 2],
    })


@pytest.fixture
def sample_optimization_assignments() -> pd.DataFrame:
    return pd.DataFrame({
        "assignment_rank": [1, 2, 3, 4],
        "sku_id": ["S1", "S2", "S3", "S4"],
        "target_zone_id": ["Z1", "Z1", "Z2", "Z1"],
        "target_zone_slot": ["Z1-1", "Z1-2", "Z2-1", "Z1-3"],
        "candidate_action": ["move", "move", "move", "move"],
        "opportunity_score": [90, 80, 70, 60],
        "assignment_cost": [0.1, 0.2, 0.3, 0.4],
        "solver_method": ["greedy_fallback"] * 4,
    })


# ── SimulationConfig tests ──────────────────────────────────────────────


class TestSimulationConfig:
    def test_defaults_are_frozen(self):
        config = SimulationConfig()
        with pytest.raises(AttributeError):
            config.picker_speed_m_per_s = 2.0  # type: ignore[misc]

    def test_caveat_constant(self):
        assert "not a certified warehouse engineering model" in SIMULATION_CAVEAT

    def test_assumption_descriptions_exist(self):
        assert len(SimulationConfig.ASSUMPTION_DESCRIPTIONS) >= 8


# ── Travel simulator tests ──────────────────────────────────────────────


class TestBuildSkuCurrentZone:
    def test_returns_primary_zone(self, sample_locations, sample_inventory):
        result = build_sku_current_zone(sample_inventory, sample_locations)
        assert "sku_id" in result.columns
        assert "current_zone_id" in result.columns

        # S1 has 10 units in L1 (Z1) and 5 in L2 (Z1) -> Z1
        s1 = result[result["sku_id"] == "S1"]
        assert len(s1) == 1
        assert s1.iloc[0]["current_zone_id"] == "Z1"

    def test_all_skus_represented(self, sample_locations, sample_inventory):
        result = build_sku_current_zone(sample_inventory, sample_locations)
        assert set(result["sku_id"]) == {"S1", "S2", "S3", "S4"}


class TestBuildSkuOptimizedZone:
    def test_returns_optimized_zone(self, sample_optimization_assignments):
        result = build_sku_optimized_zone(sample_optimization_assignments)
        assert "sku_id" in result.columns
        assert "optimized_zone_id" in result.columns
        assert len(result) == 4

    def test_deduplicates_skus(self):
        dupes = pd.DataFrame({
            "sku_id": ["S1", "S1", "S2"],
            "target_zone_id": ["Z1", "Z2", "Z1"],
            "assignment_cost": [0.1, 0.2, 0.3],
        })
        result = build_sku_optimized_zone(dupes)
        assert len(result) == 2


class TestSimulateTravel:
    def test_returns_expected_keys(self, sample_zones, sample_order_lines,
                                   sample_locations, sample_inventory,
                                   sample_optimization_assignments):
        sku_current = build_sku_current_zone(sample_inventory, sample_locations)
        sku_opt = build_sku_optimized_zone(sample_optimization_assignments)

        result = simulate_travel(sample_order_lines, sample_zones, sku_current, sku_opt)
        assert "order_detail" in result
        assert "aggregate" in result

    def test_aggregate_has_expected_metrics(self, sample_zones, sample_order_lines,
                                            sample_locations, sample_inventory,
                                            sample_optimization_assignments):
        sku_current = build_sku_current_zone(sample_inventory, sample_locations)
        sku_opt = build_sku_optimized_zone(sample_optimization_assignments)

        result = simulate_travel(sample_order_lines, sample_zones, sku_current, sku_opt)
        agg = result["aggregate"]
        assert agg["total_orders_simulated"] == 3
        assert agg["total_distance_saved_m"] >= 0
        assert agg["avg_improvement_pct"] >= 0
        assert agg["assumption_state"] == "inferred / pending confirmation"

    def test_no_optimization_still_works(self, sample_zones, sample_order_lines,
                                         sample_locations, sample_inventory):
        sku_current = build_sku_current_zone(sample_inventory, sample_locations)
        result = simulate_travel(sample_order_lines, sample_zones, sku_current)
        assert "aggregate" in result
        assert "total_orders_simulated" in result["aggregate"]

    def test_distances_non_negative(self, sample_zones, sample_order_lines,
                                    sample_locations, sample_inventory,
                                    sample_optimization_assignments):
        sku_current = build_sku_current_zone(sample_inventory, sample_locations)
        sku_opt = build_sku_optimized_zone(sample_optimization_assignments)
        result = simulate_travel(sample_order_lines, sample_zones, sku_current, sku_opt)
        detail = result["order_detail"]
        assert (detail["distance_saved_m"] >= 0).all()


# ── Workload simulator tests ────────────────────────────────────────────


class TestGiniCoefficient:
    def test_perfect_equality(self):
        assert gini_coefficient(pd.Series([10, 10, 10])) == 0.0

    def test_extreme_inequality(self):
        # Gini( [100, 0, 0] ) = 2/3 ≈ 0.667 — textbook result
        gini = gini_coefficient(pd.Series([100, 0, 0]))
        assert gini == pytest.approx(2 / 3, rel=1e-3)

    def test_single_zone(self):
        assert gini_coefficient(pd.Series([50])) == 0.0

    def test_empty_or_zero(self):
        assert gini_coefficient(pd.Series([])) == 0.0
        assert gini_coefficient(pd.Series([0, 0, 0])) == 0.0


class TestSimulateWorkload:
    def test_returns_expected_keys(self, sample_zones, sample_order_lines,
                                   sample_locations, sample_inventory,
                                   sample_optimization_assignments):
        sku_current = build_sku_current_zone(sample_inventory, sample_locations)
        sku_opt = build_sku_optimized_zone(sample_optimization_assignments)

        result = simulate_workload(sample_order_lines, sample_zones, sku_current, sku_opt)
        assert "zone_detail" in result
        assert "aggregate" in result

    def test_pick_counts_align(self, sample_zones, sample_order_lines,
                               sample_locations, sample_inventory,
                               sample_optimization_assignments):
        sku_current = build_sku_current_zone(sample_inventory, sample_locations)
        sku_opt = build_sku_optimized_zone(sample_optimization_assignments)

        result = simulate_workload(sample_order_lines, sample_zones, sku_current, sku_opt)
        agg = result["aggregate"]
        # Total picks should equal number of order lines
        assert agg["total_picks_current"] == len(sample_order_lines)
        assert agg["total_picks_optimized"] == len(sample_order_lines)

    def test_no_optimization_returns_current_only(self, sample_zones, sample_order_lines,
                                                  sample_locations, sample_inventory):
        sku_current = build_sku_current_zone(sample_inventory, sample_locations)
        result = simulate_workload(sample_order_lines, sample_zones, sku_current)
        assert "note" in result["aggregate"]

    def test_gini_between_0_and_1(self, sample_zones, sample_order_lines,
                                  sample_locations, sample_inventory,
                                  sample_optimization_assignments):
        sku_current = build_sku_current_zone(sample_inventory, sample_locations)
        sku_opt = build_sku_optimized_zone(sample_optimization_assignments)

        result = simulate_workload(sample_order_lines, sample_zones, sku_current, sku_opt)
        assert 0 <= result["aggregate"]["gini_coefficient_before"] <= 1
        assert 0 <= result["aggregate"]["gini_coefficient_after"] <= 1


# ── Throughput tests ────────────────────────────────────────────────────


class TestEstimateThroughput:
    def test_returns_expected_keys(self):
        travel_result = {
            "aggregate": {
                "total_time_saved_s": 5000,
                "total_orders_simulated": 1000,
                "travel_overhead_factor": 1.3,
            }
        }
        result = estimate_throughput(travel_result)
        assert "scenario_table" in result
        assert "aggregate" in result

    def test_three_scenarios(self):
        travel_result = {
            "aggregate": {
                "total_time_saved_s": 5000,
                "total_orders_simulated": 1000,
            }
        }
        result = estimate_throughput(travel_result)
        table = result["scenario_table"]
        assert len(table) == 3
        assert set(table["scenario"]) == {"optimistic", "balanced", "conservative"}

    def test_no_orders_returns_note(self):
        travel_result = {"aggregate": {"total_time_saved_s": 0, "total_orders_simulated": 0}}
        result = estimate_throughput(travel_result)
        assert "note" in result["aggregate"]

    def test_throughput_gains_positive(self):
        travel_result = {
            "aggregate": {
                "total_time_saved_s": 5000,
                "total_orders_simulated": 1000,
            }
        }
        result = estimate_throughput(travel_result)
        table = result["scenario_table"]
        assert (table["throughput_gain_pct"] >= 0).all()

    def test_optimistic_greater_than_conservative(self):
        travel_result = {
            "aggregate": {
                "total_time_saved_s": 5000,
                "total_orders_simulated": 1000,
            }
        }
        result = estimate_throughput(travel_result)
        table = result["scenario_table"]
        opt = table[table["scenario"] == "optimistic"]["throughput_gain_pct"].iloc[0]
        con = table[table["scenario"] == "conservative"]["throughput_gain_pct"].iloc[0]
        assert opt >= con

    def test_bad_aggregate_raises(self):
        with pytest.raises(ValueError):
            estimate_throughput({"aggregate": "not_a_dict"})


# ── Report tests ────────────────────────────────────────────────────────


def _make_travel_result() -> dict:
    return {
        "aggregate": {
            "total_orders_simulated": 100,
            "total_current_distance_m": 50000,
            "total_optimized_distance_m": 45000,
            "total_distance_saved_m": 5000,
            "total_time_saved_s": 5000,
            "avg_distance_per_order_current": 500,
            "avg_distance_per_order_optimized": 450,
            "avg_improvement_pct": 10.0,
            "orders_with_improvement": 80,
            "travel_overhead_factor": 1.3,
            "assumption_state": "inferred / pending confirmation",
            "simulation_caveat": SIMULATION_CAVEAT,
        },
        "order_detail": pd.DataFrame({
            "order_id": ["O1", "O2"],
            "order_distance_current": [100, 200],
            "order_distance_optimized": [90, 180],
            "distance_saved_m": [10, 20],
            "time_saved_s": [13, 26],
            "distance_improvement_pct": [10.0, 10.0],
        }),
    }


def _make_workload_result() -> dict:
    return {
        "aggregate": {
            "total_zones": 5,
            "total_picks_current": 500,
            "total_picks_optimized": 500,
            "zones_with_pick_change": 3,
            "gini_coefficient_before": 0.35,
            "gini_coefficient_after": 0.28,
            "gini_change": -0.07,
            "balance_improved": True,
            "assumption_state": "inferred / pending confirmation",
            "simulation_caveat": SIMULATION_CAVEAT,
        },
        "zone_detail": pd.DataFrame({
            "zone_id": ["Z1", "Z2", "Z3"],
            "picks_current": [200, 150, 150],
            "picks_optimized": [150, 200, 150],
            "pick_change": [-50, 50, 0],
        }),
    }


def _make_throughput_result() -> dict:
    return {
        "aggregate": {
            "recommended_scenario": "balanced",
            "orders_per_shift_current": 1000,
            "orders_per_shift_optimized": 1080,
            "throughput_gain_pct": 8.0,
            "productive_seconds_per_shift": 23040,
            "avg_travel_time_per_order_s": 50,
            "avg_pick_time_per_order_s": 25,
            "total_time_saved_s": 5000,
            "assumption_state": "inferred / pending confirmation",
            "simulation_caveat": SIMULATION_CAVEAT,
        },
        "scenario_table": pd.DataFrame({
            "scenario": ["optimistic", "balanced", "conservative"],
            "multiplier": [1.15, 1.08, 1.03],
            "orders_per_shift_current": [1000, 1000, 1000],
            "orders_per_shift_optimized": [1150, 1080, 1030],
            "throughput_gain_pct": [15.0, 8.0, 3.0],
        }),
    }


class TestBuildSimulationReport:
    def test_returns_expected_keys(self):
        reports = build_simulation_report(
            _make_travel_result(),
            _make_workload_result(),
            _make_throughput_result(),
        )
        assert "simulation_summary" in reports
        assert "travel_aggregate" in reports
        assert "zone_detail" in reports
        assert "throughput_scenarios" in reports
        assert "travel_order_detail" in reports

    def test_summary_has_expected_metrics(self):
        reports = build_simulation_report(
            _make_travel_result(),
            _make_workload_result(),
            _make_throughput_result(),
        )
        summary = reports["simulation_summary"]
        assert isinstance(summary, pd.DataFrame)
        assert len(summary) >= 10
        assert "assumption_state" in summary.columns
        assert "simulation_caveat" in summary.columns

    def test_caveat_present(self):
        reports = build_simulation_report(
            _make_travel_result(),
            _make_workload_result(),
            _make_throughput_result(),
        )
        summary = reports["simulation_summary"]
        assert summary["simulation_caveat"].iloc[0] == SIMULATION_CAVEAT


class TestSaveSimulationOutputs:
    def test_saves_csv_files(self, tmp_path):
        reports = build_simulation_report(
            _make_travel_result(),
            _make_workload_result(),
            _make_throughput_result(),
        )
        paths = save_simulation_outputs(reports, output_dir=tmp_path)
        assert len(paths) >= 3  # at least summary, travel, zone
        for path in paths.values():
            assert Path(path).is_file()

    def test_empty_report_does_not_save(self, tmp_path):
        paths = save_simulation_outputs({}, output_dir=tmp_path)
        assert len(paths) == 0


class TestSimulationScriptImportable:
    def test_script_is_importable(self):
        # Verify the simulation CLI script can be imported without errors

        root = Path(__file__).resolve().parent.parent.parent
        script_path = root / "scripts" / "run_simulation.py"
        assert script_path.is_file()

        # Just check it parses correctly
        import ast
        with open(script_path) as f:
            tree = ast.parse(f.read())
        assert isinstance(tree, ast.Module)
