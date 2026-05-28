"""Data loading, templates, validation, and recommendations for the Streamlit Panel de Control.

This module keeps Streamlit out of the data layer. Pure pandas helpers for:
- Loading processed outputs from all 6 phases
- Generating downloadable CSV templates for user uploads
- Validating uploaded files against schema contracts
- Computing KPIs and human-readable recommendations
"""

from __future__ import annotations

import io
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from slotting_optimization_engine.config.project_paths import DATA_PROCESSED_DIR
from slotting_optimization_engine.domain.constants import (
    Features,
    Inventory,
    Locations,
    OrderLines,
    Orders,
    Skus,
    Zones,
)

# ===========================================================================
# Expected output files — all 6 phases
# ===========================================================================

EXPECTED_OUTPUT_FILES_PHASE_1_2: dict[str, str] = {
    "Slotting features": "slotting_features.parquet",
    "Location utilization": "location_utilization.csv",
    "Zone utilization": "zone_utilization.csv",
    "Slotting diagnostics": "slotting_diagnostics.csv",
    "Location diagnostics": "location_diagnostics.csv",
    "Zone diagnostics": "zone_diagnostics.csv",
    "Category diagnostics": "category_diagnostics.csv",
    "Diagnostic summary": "diagnostic_summary.csv",
}

EXPECTED_OUTPUT_FILES_PHASE_3_6: dict[str, str] = {
    "Opportunity scores": "slotting_opportunity_scores.csv",
    "Priority queue": "priority_recommendation_queue.csv",
    "Scoring summary": "scoring_summary.csv",
    "Scenario comparison": "scenario_comparison.csv",
    "Scenario action mix": "scenario_action_mix.csv",
    "Scenario summary": "scenario_summary.csv",
    "Optimization assignments": "optimization_assignments.csv",
    "Optimization summary": "optimization_summary.csv",
    "Optimization cost matrix": "optimization_cost_matrix.csv",
    "Simulation summary": "simulation_summary.csv",
    "Travel aggregate": "simulation_travel_aggregate.csv",
    "Zone impact": "simulation_zone_impact.csv",
    "Throughput scenarios": "simulation_throughput_scenarios.csv",
    "Order detail": "simulation_order_detail.csv",
}

ALL_EXPECTED_FILES: dict[str, str] = {
    **EXPECTED_OUTPUT_FILES_PHASE_1_2,
    **EXPECTED_OUTPUT_FILES_PHASE_3_6,
}

# Group by phase for UI organisation
PHASE_GROUPS: dict[str, dict[str, str]] = {
    "1": {
        "Slotting features": "slotting_features.parquet",
        "Location utilization": "location_utilization.csv",
        "Zone utilization": "zone_utilization.csv",
    },
    "2": {
        "Slotting diagnostics": "slotting_diagnostics.csv",
        "Location diagnostics": "location_diagnostics.csv",
        "Zone diagnostics": "zone_diagnostics.csv",
        "Category diagnostics": "category_diagnostics.csv",
        "Diagnostic summary": "diagnostic_summary.csv",
    },
    "3": {
        "Opportunity scores": "slotting_opportunity_scores.csv",
        "Priority queue": "priority_recommendation_queue.csv",
        "Scoring summary": "scoring_summary.csv",
    },
    "4": {
        "Scenario comparison": "scenario_comparison.csv",
        "Scenario action mix": "scenario_action_mix.csv",
        "Scenario summary": "scenario_summary.csv",
    },
    "5": {
        "Optimization assignments": "optimization_assignments.csv",
        "Optimization summary": "optimization_summary.csv",
        "Optimization cost matrix": "optimization_cost_matrix.csv",
    },
    "6": {
        "Simulation summary": "simulation_summary.csv",
        "Travel aggregate": "simulation_travel_aggregate.csv",
        "Zone impact": "simulation_zone_impact.csv",
        "Throughput scenarios": "simulation_throughput_scenarios.csv",
        "Order detail": "simulation_order_detail.csv",
    },
}

# ===========================================================================
# Script execution — map phase → script path
# ===========================================================================

SCRIPTS_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent / "scripts"

PHASE_SCRIPTS: dict[str, Path] = {
    "1": SCRIPTS_DIR / "build_features.py",
    "2": SCRIPTS_DIR / "run_diagnostics.py",
    "3": SCRIPTS_DIR / "run_scoring.py",
    "4": SCRIPTS_DIR / "run_scenarios.py",
    "5": SCRIPTS_DIR / "run_optimization.py",
    "6": SCRIPTS_DIR / "run_simulation.py",
}


def run_phase_script(phase: str) -> tuple[bool, str]:
    """Execute a phase script and return (success, output_or_error)."""
    script = PHASE_SCRIPTS.get(phase)
    if script is None:
        return False, f"Fase {phase} no tiene script asociado."
    if not script.exists():
        return False, f"Script no encontrado: {script}"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            return True, result.stdout[-2000:] if result.stdout else "✅ Ejecutado correctamente."
        return False, (result.stderr or result.stdout or "Error desconocido")[-2000:]
    except subprocess.TimeoutExpired:
        return False, "⏱️ Tiempo de ejecución excedido (10 min)."
    except Exception as exc:
        return False, f"Error al ejecutar: {exc}"


# ===========================================================================
# Overview indicators — traffic-light status per phase
# ===========================================================================


@dataclass
class PhaseIndicator:
    """Status indicator for one phase in the overview dashboard."""

    phase: str
    label: str
    status: str          # "ok" | "warning" | "error" | "missing"
    status_emoji: str    # "🟢" | "🟡" | "🔴" | "⚪"
    metrics: list[tuple[str, str | int | float | None]]
    message: str
    recommendations: list[str]


def compute_overview_indicators(data: FullDashboardData) -> list[PhaseIndicator]:
    """Compute traffic-light indicators for all 6 phases."""
    indicators: list[PhaseIndicator] = []

    all_status_map = {s.name: s for s in data.statuses}

    # ── Phase 1 — Features ─────────────────────────────────────────
    p1_files = list(PHASE_GROUPS["1"].keys())
    p1_missing = [n for n in p1_files if not (all_status_map.get(n) and all_status_map[n].exists)]
    p1_ok = len(p1_missing) == 0
    sku_f = data.sku_features
    sku_count = len(sku_f) if sku_f is not None else 0
    indicators.append(PhaseIndicator(
        phase="1", label="Features (Fase 1)",
        status="ok" if p1_ok else "missing",
        status_emoji="🟢" if p1_ok else "🔴",
        metrics=[("SKUs procesados", f"{sku_count:,}")] if sku_f is not None else [],
        message="Datos base cargados correctamente." if p1_ok else f"Faltan: {', '.join(p1_missing)}.",
        recommendations=["✅ Base de datos lista para diagnóstico."] if p1_ok else ["⚠️ Ejecutá Fase 1 para generar datos base."],
    ))

    # ── Phase 2 — Diagnostics ─────────────────────────────────────
    p2_files = list(PHASE_GROUPS["2"].keys())
    p2_missing = [n for n in p2_files if not (all_status_map.get(n) and all_status_map[n].exists)]
    p2_ok = len(p2_missing) == 0
    diag = data.diagnostic_summary
    total_flags = int(diag["flag_count"].sum()) if diag is not None and "flag_count" in diag.columns else 0
    diag_recs = generate_diagnostics_recommendations(
        data.diagnostic_summary, data.slotting_diagnostics, data.zone_diagnostics,
    )
    indicators.append(PhaseIndicator(
        phase="2", label="Diagnóstico (Fase 2)",
        status="warning" if total_flags > 0 else "ok" if p2_ok else "missing",
        status_emoji="🟡" if total_flags > 0 else "🟢" if p2_ok else "🔴",
        metrics=[("Flags detectados", total_flags)] if diag is not None else [],
        message=f"Diagnóstico completo. {total_flags} flag(s) de oportunidad." if p2_ok
                else f"Faltan: {', '.join(p2_missing)}.",
        recommendations=diag_recs if p2_ok else ["⚠️ Ejecutá Fase 2 para diagnosticar slotting."],
    ))

    # ── Phase 3 — Scoring ─────────────────────────────────────────
    p3_files = list(PHASE_GROUPS["3"].keys())
    p3_missing = [n for n in p3_files if not (all_status_map.get(n) and all_status_map[n].exists)]
    p3_ok = len(p3_missing) == 0
    pq = data.priority_queue
    top_score = None
    top_entity = None
    if pq is not None and not pq.empty:
        row = pq.iloc[0]
        if "opportunity_score" in row.index:
            top_score = float(row["opportunity_score"])
            top_entity = str(row.get("entity_id", "N/A"))
    scoring_recs = generate_scoring_recommendations(data.priority_queue, data.scoring_summary)
    indicators.append(PhaseIndicator(
        phase="3", label="Scoring (Fase 3)",
        status="ok" if p3_ok and top_score is not None else "warning" if p3_ok else "missing",
        status_emoji="🟢" if p3_ok and top_score is not None else "🟡" if p3_ok else "🔴",
        metrics=[
            ("Top score", f"{top_score:.1f}" if top_score is not None else "—"),
            ("Top SKU", top_entity or "—"),
        ] if p3_ok else [],
        message=f"Scoring completado. Prioridad máxima: {top_entity} (score {top_score:.1f})." if top_score is not None
                else "Datos de scoring disponibles." if p3_ok
                else f"Faltan: {', '.join(p3_missing)}.",
        recommendations=scoring_recs if p3_ok else ["⚠️ Ejecutá Fase 3 para scoring de oportunidades."],
    ))

    # ── Phase 4 — Scenarios ───────────────────────────────────────
    p4_files = list(PHASE_GROUPS["4"].keys())
    p4_missing = [n for n in p4_files if not (all_status_map.get(n) and all_status_map[n].exists)]
    p4_ok = len(p4_missing) == 0
    sc = data.scenario_summary
    scenario_count = len(sc) if sc is not None else 0
    scenarios_recs = generate_scenario_recommendations(data.scenario_summary, data.scenario_comparison)
    indicators.append(PhaseIndicator(
        phase="4", label="Escenarios (Fase 4)",
        status="ok" if p4_ok and scenario_count > 0 else "missing",
        status_emoji="🟢" if p4_ok and scenario_count > 0 else "🔴",
        metrics=[("Escenarios evaluados", scenario_count)] if sc is not None else [],
        message=f"{scenario_count} escenario(s) comparados." if scenario_count > 0
                else "Datos de escenarios disponibles." if p4_ok
                else f"Faltan: {', '.join(p4_missing)}.",
        recommendations=scenarios_recs if p4_ok else ["⚠️ Ejecutá Fase 4 para comparar escenarios."],
    ))

    # ── Phase 5 — Optimization ────────────────────────────────────
    p5_files = list(PHASE_GROUPS["5"].keys())
    p5_missing = [n for n in p5_files if not (all_status_map.get(n) and all_status_map[n].exists)]
    p5_ok = len(p5_missing) == 0
    opt_assignments = data.optimization_assignments
    opt_count = len(opt_assignments) if opt_assignments is not None else 0

    opt_method = "—"
    opt_sku_count = "—"
    if data.optimization_summary is not None and not data.optimization_summary.empty:
        opt_md = dict(zip(data.optimization_summary["metric"], data.optimization_summary["value"]))
        opt_method = str(opt_md.get("solver_method", "desconocido"))
        opt_sku_count = str(opt_md.get("selected_skus", "—"))
    optim_recs = generate_optimization_recommendations(data.optimization_summary, data.optimization_assignments)
    indicators.append(PhaseIndicator(
        phase="5", label="Optimización (Fase 5)",
        status="ok" if p5_ok else "missing",
        status_emoji="🟢" if p5_ok else "🔴",
        metrics=[("Método", opt_method), ("SKUs asignados", opt_sku_count)] if p5_ok else [],
        message=f"Optimización ejecutada con método '{opt_method}' para {opt_sku_count} SKU(s)." if p5_ok
                else f"Faltan: {', '.join(p5_missing)}.",
        recommendations=optim_recs if p5_ok else ["⚠️ Ejecutá Fase 5 para generar asignaciones optimizadas."],
    ))

    # ── Phase 6 — Simulation ──────────────────────────────────────
    p6_files = list(PHASE_GROUPS["6"].keys())
    p6_missing = [n for n in p6_files if not (all_status_map.get(n) and all_status_map[n].exists)]
    p6_ok = len(p6_missing) == 0
    sim = data.simulation_summary
    sim_recs = generate_simulation_recommendations(data.simulation_summary)
    improvement_pct = None
    gini_val = None
    if sim is not None and not sim.empty and "metric" in sim.columns:
        sim_md = dict(zip(sim["metric"], sim["value"]))
        # Map actual simulation metric names
        for metric_key in ["avg_improvement_pct", "travel_distance_improvement_pct", "improvement_pct"]:
            v = sim_md.get(metric_key)
            if v is not None:
                try:
                    improvement_pct = f"{float(v):.1f}%"
                except (ValueError, TypeError):
                    improvement_pct = str(v)
                break
        for gini_key in ["gini_coefficient_after", "gini_coefficient", "gini_change"]:
            v = sim_md.get(gini_key)
            if v is not None and not (isinstance(v, float) and pd.isna(v)):
                try:
                    gini_val = f"{float(v):.4f}"
                except (ValueError, TypeError):
                    gini_val = str(v)
                break
    elif sim is not None and not sim.empty:
        # Fallback: wide format
        row = sim.iloc[0]
        for col in sim.columns:
            if "improvement" in col.lower() or "reduction" in col.lower():
                try:
                    improvement_pct = f"{float(row[col]):.1f}%"
                except (ValueError, TypeError):
                    pass
    indicators.append(PhaseIndicator(
        phase="6", label="Simulación (Fase 6)",
        status="ok" if p6_ok else "missing",
        status_emoji="🟢" if p6_ok else "🔴",
        metrics=[("Mejora viaje", improvement_pct or "—")] + ([("Gini", gini_val)] if gini_val else []),
        message=f"Simulación completada. Mejora estimada: {improvement_pct}." if improvement_pct
                else "Simulación disponible." if p6_ok
                else f"Faltan: {', '.join(p6_missing)}.",
        recommendations=sim_recs if p6_ok else ["⚠️ Ejecutá Fase 6 para simular el impacto operativo."],
    ))

    return indicators


# ===========================================================================
# Dataset template definitions for user uploads
# ===========================================================================

# Column name → friendly type hint for UI validation messages
TYPE_HINTS: dict[str, str] = {
    "text": "Texto",
    "number": "Número (decimal)",
    "integer": "Número entero",
    "date": "Fecha (YYYY-MM-DD)",
}

ColumnDef = dict[str, str]  # {column_name: type_hint}


TEMPLATES: dict[str, dict[str, Any]] = {
    "skus": {
        "label": "Catálogo de SKUs",
        "description": "Lista maestra de todos los productos. Cada fila = un SKU.",
        "columns": {
            Skus.SKU_ID: "text",
            Skus.CATEGORY: "text",
            Skus.SUBCATEGORY: "text",
            Skus.UNIT_VOLUME: "number",
            Skus.UNIT_WEIGHT: "number",
            Skus.ROTATION_CLASS: "text",
            Skus.AVG_DAILY_DEMAND: "number",
        },
        "example": {
            Skus.SKU_ID: "SKU-001",
            Skus.CATEGORY: "Electrónicos",
            Skus.SUBCATEGORY: "Accesorios",
            Skus.UNIT_VOLUME: 0.5,
            Skus.UNIT_WEIGHT: 0.2,
            Skus.ROTATION_CLASS: "A",
            Skus.AVG_DAILY_DEMAND: 45.0,
        },
    },
    "zones": {
        "label": "Zonas del depósito",
        "description": "Áreas del depósito con distancia a despacho y capacidad.",
        "columns": {
            Zones.ZONE_ID: "text",
            Zones.ZONE_TYPE: "text",
            Zones.PRIORITY_LEVEL: "integer",
            Zones.DISTANCE_TO_DISPATCH: "number",
            Zones.MAX_VOLUME_CAPACITY: "number",
            Zones.MAX_WEIGHT_CAPACITY: "number",
        },
        "example": {
            Zones.ZONE_ID: "Z-01",
            Zones.ZONE_TYPE: "picking",
            Zones.PRIORITY_LEVEL: 1,
            Zones.DISTANCE_TO_DISPATCH: 120.0,
            Zones.MAX_VOLUME_CAPACITY: 1000.0,
            Zones.MAX_WEIGHT_CAPACITY: 5000.0,
        },
    },
    "locations": {
        "label": "Ubicaciones (estanterías)",
        "description": "Ubicaciones físicas dentro de cada zona.",
        "columns": {
            Locations.LOCATION_ID: "text",
            Locations.ZONE_ID: "text",
            Locations.AISLE: "text",
            Locations.RACK: "text",
            Locations.LEVEL: "text",
            Locations.MAX_VOLUME_CAPACITY: "number",
            Locations.MAX_WEIGHT_CAPACITY: "number",
        },
        "example": {
            Locations.LOCATION_ID: "LOC-000001",
            Locations.ZONE_ID: "Z-01",
            Locations.AISLE: "A",
            Locations.RACK: "01",
            Locations.LEVEL: "1",
            Locations.MAX_VOLUME_CAPACITY: 2.0,
            Locations.MAX_WEIGHT_CAPACITY: 500.0,
        },
    },
    "inventory": {
        "label": "Inventario",
        "description": "Stock actual. Cada fila = un SKU en una ubicación.",
        "columns": {
            Inventory.SKU_ID: "text",
            Inventory.LOCATION_ID: "text",
            Inventory.UNITS_ON_HAND: "integer",
            Inventory.OCCUPIED_VOLUME: "number",
            Inventory.OCCUPIED_WEIGHT: "number",
        },
        "example": {
            Inventory.SKU_ID: "SKU-001",
            Inventory.LOCATION_ID: "LOC-000001",
            Inventory.UNITS_ON_HAND: 50,
            Inventory.OCCUPIED_VOLUME: 0.5,
            Inventory.OCCUPIED_WEIGHT: 0.2,
        },
    },
    "orders": {
        "label": "Pedidos (cabecera)",
        "description": "Encabezados de pedidos. Cada fila = una orden.",
        "columns": {
            Orders.ORDER_ID: "text",
            Orders.ORDER_DATE: "text",
            Orders.CHANNEL: "text",
        },
        "example": {
            Orders.ORDER_ID: "ORD-00001",
            Orders.ORDER_DATE: "2025-01-15",
            Orders.CHANNEL: "online",
        },
    },
    "order_lines": {
        "label": "Líneas de pedido",
        "description": "Detalle de cada pedido. Cada fila = un SKU en una orden.",
        "columns": {
            OrderLines.ORDER_ID: "text",
            OrderLines.SKU_ID: "text",
            OrderLines.QUANTITY: "integer",
        },
        "example": {
            OrderLines.ORDER_ID: "ORD-00001",
            OrderLines.SKU_ID: "SKU-001",
            OrderLines.QUANTITY: 2,
        },
    },
}

TEMPLATE_DATASET_KEYS: list[str] = [
    "skus",
    "zones",
    "locations",
    "inventory",
    "orders",
    "order_lines",
]

# ===========================================================================
# Data classes
# ===========================================================================


@dataclass(frozen=True)
class DatasetStatus:
    """Availability and shape metadata for one processed output."""

    name: str
    filename: str
    exists: bool
    row_count: int | None = None
    column_count: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating an uploaded CSV against its expected schema."""

    is_valid: bool
    errors: list[str]
    warnings: list[str] = field(default_factory=list)
    row_count: int = 0
    column_count: int = 0


@dataclass(frozen=True)
class DashboardData:
    """Loaded processed outputs from Phase 1-2 plus availability metadata."""

    sku_features: pd.DataFrame | None
    location_utilization: pd.DataFrame | None
    zone_utilization: pd.DataFrame | None
    slotting_diagnostics: pd.DataFrame | None
    location_diagnostics: pd.DataFrame | None
    zone_diagnostics: pd.DataFrame | None
    category_diagnostics: pd.DataFrame | None
    diagnostic_summary: pd.DataFrame | None
    statuses: tuple[DatasetStatus, ...]


@dataclass(frozen=True)
class FullDashboardData:
    """Loaded processed outputs from all 6 phases plus availability."""

    # Phase 1-2
    sku_features: pd.DataFrame | None
    location_utilization: pd.DataFrame | None
    zone_utilization: pd.DataFrame | None
    slotting_diagnostics: pd.DataFrame | None
    location_diagnostics: pd.DataFrame | None
    zone_diagnostics: pd.DataFrame | None
    category_diagnostics: pd.DataFrame | None
    diagnostic_summary: pd.DataFrame | None
    # Phase 3
    opportunity_scores: pd.DataFrame | None
    priority_queue: pd.DataFrame | None
    scoring_summary: pd.DataFrame | None
    # Phase 4
    scenario_comparison: pd.DataFrame | None
    scenario_action_mix: pd.DataFrame | None
    scenario_summary: pd.DataFrame | None
    # Phase 5
    optimization_assignments: pd.DataFrame | None
    optimization_summary: pd.DataFrame | None
    optimization_cost_matrix: pd.DataFrame | None
    # Phase 6
    simulation_summary: pd.DataFrame | None
    travel_aggregate: pd.DataFrame | None
    zone_impact: pd.DataFrame | None
    throughput_scenarios: pd.DataFrame | None
    order_detail: pd.DataFrame | None
    # Metadata
    statuses: tuple[DatasetStatus, ...]


def compute_kpis(data: DashboardData) -> dict[str, int | float | None]:
    """Compute high-level inspection KPIs from Phase 1 outputs."""
    sku_features = data.sku_features
    location_util = data.location_utilization
    zone_util = data.zone_utilization

    sku_count = _unique_or_len(sku_features, Skus.SKU_ID)
    zone_count = _unique_or_len(zone_util, Zones.ZONE_ID)
    location_count = _unique_or_len(location_util, Locations.LOCATION_ID)

    avg_utilization = None
    if location_util is not None:
        util_columns = [
            col
            for col in (Features.VOLUME_UTIL_PCT, Features.WEIGHT_UTIL_PCT)
            if col in location_util.columns
        ]
        if util_columns:
            avg_utilization = float(location_util[util_columns].mean(axis=1).mean())

    over_capacity_locations = None
    if location_util is not None and "over_capacity" in location_util.columns:
        over_capacity_locations = int(location_util["over_capacity"].fillna(False).sum())
    elif zone_util is not None and "over_capacity_location_count" in zone_util.columns:
        over_capacity_locations = int(zone_util["over_capacity_location_count"].fillna(0).sum())

    return {
        "sku_count": sku_count,
        "zone_count": zone_count,
        "location_count": location_count,
        "avg_utilization_pct": avg_utilization,
        "over_capacity_locations": over_capacity_locations,
    }


# ===========================================================================
# Template generation
# ===========================================================================


def generate_template_df(dataset_key: str) -> pd.DataFrame:
    """Return a DataFrame with the correct columns and one example row."""
    template = TEMPLATES.get(dataset_key)
    if template is None:
        return pd.DataFrame()

    df = pd.DataFrame([template["example"]])
    # Ensure column order matches template
    df = df[list(template["columns"].keys())]
    return df


def get_template_csv(dataset_key: str) -> str:
    """Return the template as a CSV string for download."""
    df = generate_template_df(dataset_key)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# ===========================================================================
# Upload validation
# ===========================================================================


def validate_uploaded_csv(
    uploaded_file,
    dataset_key: str,
    extra_data: dict[str, pd.DataFrame] | None = None,
) -> ValidationResult:
    """Validate an uploaded CSV file against the expected template schema.

    Parameters
    ----------
    uploaded_file : Streamlit UploadedFile
        The file uploaded by the user.
    dataset_key : str
        One of TEMPLATE_DATASET_KEYS (skus, zones, …).
    extra_data : dict[str, pd.DataFrame] | None
        Previously validated datasets for referential integrity checks.

    Returns
    -------
    ValidationResult with errors and warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if uploaded_file is None:
        return ValidationResult(is_valid=False, errors=["No se recibió ningún archivo."])

    template = TEMPLATES.get(dataset_key)
    if template is None:
        return ValidationResult(is_valid=False, errors=[f"Dataset desconocido: {dataset_key}"])

    expected_columns: dict[str, str] = template["columns"]

    try:
        df = pd.read_csv(uploaded_file)
    except Exception as exc:
        return ValidationResult(
            is_valid=False,
            errors=[f"No se pudo leer el CSV: {exc}"],
        )

    # Check not empty
    if df.empty:
        errors.append("El archivo CSV está vacío.")

    # Check required columns
    required = list(expected_columns.keys())
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        errors.append(
            f"Faltan columnas requeridas: {', '.join(missing_cols)}. "
            f"Requeridas: {', '.join(required)}"
        )

    # Extra columns (warning)
    extra_cols = [c for c in df.columns if c not in required]
    if extra_cols:
        warnings.append(
            f"Columnas adicionales no esperadas: {', '.join(extra_cols)}. Serán ignoradas."
        )

    # Check nulls in required columns
    for col in required:
        if col in df.columns and df[col].isna().any():
            null_count = int(df[col].isna().sum())
            msg = f"La columna '{col}' tiene {null_count} valor(es) nulo(s)."
            errors.append(msg)

    # Check types (soft validation, non-blocking → warning)
    for col, type_hint in expected_columns.items():
        if col not in df.columns or df[col].isna().all():
            continue
        if type_hint == "number":
            non_numeric = pd.to_numeric(df[col], errors="coerce").isna().sum()
            if non_numeric > 0:
                msg = f"La columna '{col}' debería ser numérica pero tiene {non_numeric} valor(es) no numéricos."  # noqa: E501
                warnings.append(msg)
        elif type_hint == "integer":
            clean = pd.to_numeric(df[col], errors="coerce")
            non_integer = clean.dropna()[clean.dropna() % 1 != 0]
            if len(non_integer) > 0:
                msg = f"La columna '{col}' debería ser entera pero tiene {len(non_integer)} valor(es) decimal(es)."  # noqa: E501
                warnings.append(msg)

    # Referential integrity
    if extra_data:
        if dataset_key == "inventory" and Inventory.SKU_ID in df.columns:
            sku_ids = (
                set(extra_data["skus"][Skus.SKU_ID])
                if "skus" in extra_data and not extra_data["skus"].empty
                else set()
            )
            missing_refs = set(df[Inventory.SKU_ID].unique()) - sku_ids
            if missing_refs and sku_ids:
                errors.append(
                    f"{len(missing_refs)} SKU(s) en inventario no existen en el catálogo de SKUs."
                )
        if dataset_key == "order_lines" and OrderLines.SKU_ID in df.columns:
            sku_ids = (
                set(extra_data["skus"][Skus.SKU_ID])
                if "skus" in extra_data and not extra_data["skus"].empty
                else set()
            )
            missing_refs = set(df[OrderLines.SKU_ID].unique()) - sku_ids
            if missing_refs and sku_ids:
                msg = f"{len(missing_refs)} SKU(s) en líneas de pedido no existen en el catálogo de SKUs."  # noqa: E501
                warnings.append(msg)

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        row_count=len(df),
        column_count=len(df.columns),
    )


# ===========================================================================
# Loading helpers
# ===========================================================================


def _load_dataframe(path: Path) -> pd.DataFrame:
    """Load a supported processed output by extension."""
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path, dtype_backend="numpy_nullable")
    raise ValueError(f"Formato no soportado: {path.suffix}")


def inspect_processed_output(name: str, path: Path) -> tuple[DatasetStatus, pd.DataFrame | None]:
    """Return availability metadata and a dataframe for a processed output."""
    if not path.exists():
        return DatasetStatus(name=name, filename=path.name, exists=False), None
    try:
        dataframe = _load_dataframe(path)
    except Exception as exc:
        return (
            DatasetStatus(name=name, filename=path.name, exists=True, error=str(exc)),
            None,
        )
    return (
        DatasetStatus(
            name=name,
            filename=path.name,
            exists=True,
            row_count=len(dataframe),
            column_count=len(dataframe.columns),
        ),
        dataframe,
    )


def load_dashboard_data(processed_dir: Path | None = None) -> DashboardData:
    """Load Phase 1-2 outputs."""
    base_dir = processed_dir or DATA_PROCESSED_DIR
    loaded: dict[str, pd.DataFrame | None] = {}
    statuses: list[DatasetStatus] = []
    for name, filename in EXPECTED_OUTPUT_FILES_PHASE_1_2.items():
        status, dataframe = inspect_processed_output(name, base_dir / filename)
        statuses.append(status)
        loaded[name] = dataframe
    return DashboardData(
        sku_features=loaded["Slotting features"],
        location_utilization=loaded["Location utilization"],
        zone_utilization=loaded["Zone utilization"],
        slotting_diagnostics=loaded["Slotting diagnostics"],
        location_diagnostics=loaded["Location diagnostics"],
        zone_diagnostics=loaded["Zone diagnostics"],
        category_diagnostics=loaded["Category diagnostics"],
        diagnostic_summary=loaded["Diagnostic summary"],
        statuses=tuple(statuses),
    )


def load_full_dashboard_data(processed_dir: Path | None = None) -> FullDashboardData:
    """Load processed outputs from all 6 phases."""
    base_dir = processed_dir or DATA_PROCESSED_DIR
    loaded: dict[str, pd.DataFrame | None] = {}
    statuses: list[DatasetStatus] = []
    for name, filename in ALL_EXPECTED_FILES.items():
        status, dataframe = inspect_processed_output(name, base_dir / filename)
        statuses.append(status)
        loaded[name] = dataframe
    return FullDashboardData(
        # Phase 1-2
        sku_features=loaded.get("Slotting features"),
        location_utilization=loaded.get("Location utilization"),
        zone_utilization=loaded.get("Zone utilization"),
        slotting_diagnostics=loaded.get("Slotting diagnostics"),
        location_diagnostics=loaded.get("Location diagnostics"),
        zone_diagnostics=loaded.get("Zone diagnostics"),
        category_diagnostics=loaded.get("Category diagnostics"),
        diagnostic_summary=loaded.get("Diagnostic summary"),
        # Phase 3
        opportunity_scores=loaded.get("Opportunity scores"),
        priority_queue=loaded.get("Priority queue"),
        scoring_summary=loaded.get("Scoring summary"),
        # Phase 4
        scenario_comparison=loaded.get("Scenario comparison"),
        scenario_action_mix=loaded.get("Scenario action mix"),
        scenario_summary=loaded.get("Scenario summary"),
        # Phase 5
        optimization_assignments=loaded.get("Optimization assignments"),
        optimization_summary=loaded.get("Optimization summary"),
        optimization_cost_matrix=loaded.get("Optimization cost matrix"),
        # Phase 6
        simulation_summary=loaded.get("Simulation summary"),
        travel_aggregate=loaded.get("Travel aggregate"),
        zone_impact=loaded.get("Zone impact"),
        throughput_scenarios=loaded.get("Throughput scenarios"),
        order_detail=loaded.get("Order detail"),
        statuses=tuple(statuses),
    )


def status_table(statuses: tuple[DatasetStatus, ...]) -> pd.DataFrame:
    """Convert statuses into a UI-friendly table (no path column)."""
    rows = [
        {
            "dataset": s.name,
            "disponible": "✅ Sí" if s.exists and not s.error else "❌ No",
            "filas": s.row_count or 0,
            "columnas": s.column_count or 0,
            "error": s.error or "",
        }
        for s in statuses
    ]
    return pd.DataFrame(rows)


def missing_outputs(statuses: tuple[DatasetStatus, ...]) -> tuple[DatasetStatus, ...]:
    """Return files that are missing or failed to load."""
    return tuple(s for s in statuses if not s.exists or s.error)


# ===========================================================================
# Chart data helpers
# ===========================================================================


def zone_chart_data(zone_utilization: pd.DataFrame | None) -> pd.DataFrame:
    """Return zone utilization columns suitable for Streamlit native charts."""
    if zone_utilization is None or Zones.ZONE_ID not in zone_utilization.columns:
        return pd.DataFrame()
    available = [
        col
        for col in ("avg_volume_util_pct", "avg_weight_util_pct")
        if col in zone_utilization.columns
    ]
    if not available:
        return pd.DataFrame()
    return zone_utilization.set_index(Zones.ZONE_ID)[available]


def location_chart_data(location_utilization: pd.DataFrame | None, rows: int = 25) -> pd.DataFrame:
    """Return top utilized locations suitable for Streamlit native charts."""
    if location_utilization is None or Locations.LOCATION_ID not in location_utilization.columns:
        return pd.DataFrame()
    available = [
        col
        for col in (Features.VOLUME_UTIL_PCT, Features.WEIGHT_UTIL_PCT)
        if col in location_utilization.columns
    ]
    if not available:
        return pd.DataFrame()
    chart = location_utilization.copy()
    chart["promedio"] = chart[available].mean(axis=1)
    chart = chart.sort_values("promedio", ascending=False).head(rows)
    return chart.set_index(Locations.LOCATION_ID)[available]


def preview_table(dataframe: pd.DataFrame | None, rows: int = 25) -> pd.DataFrame:
    """Return a bounded preview copy for UI display."""
    if dataframe is None:
        return pd.DataFrame()
    return dataframe.head(rows).copy()


# ===========================================================================
# Recommendations
# ===========================================================================


def generate_health_signal(kpis: dict) -> tuple[str, str]:
    """Return (emoji_status, message) with overall health assessment."""
    if kpis.get("over_capacity_locations") and kpis["over_capacity_locations"] > 0:
        return (
            "🔴",
            f"Se detectaron {kpis['over_capacity_locations']} ubicaciones sobrecapacidad.",
        )
    return ("🟢", "Sin alertas críticas de capacidad.")


def generate_diagnostics_recommendations(
    diagnostic_summary: pd.DataFrame | None,
    slotting_diagnostics: pd.DataFrame | None,
    zone_diagnostics: pd.DataFrame | None,
) -> list[str]:
    """Generate human-readable insights from Phase 2 diagnostics."""
    tips: list[str] = []

    if diagnostic_summary is not None and not diagnostic_summary.empty:
        total = (
            diagnostic_summary["flag_count"].sum()
            if "flag_count" in diagnostic_summary.columns
            else 0
        )
        if total > 0:
            msg = f"🔍 Se encontraron {int(total)} flags diagnósticos en total. Revisá las tablas abajo para detalles."  # noqa: E501
            tips.append(msg)

    if slotting_diagnostics is not None and not slotting_diagnostics.empty:
        if "candidate_action" in slotting_diagnostics.columns:
            high_demand_far = len(
                slotting_diagnostics[
                    slotting_diagnostics["candidate_action"]
                    .str.contains("high_demand_far", case=False, na=False)
                ]
            )
            if high_demand_far > 0:
                msg = f"📦 {high_demand_far} SKU(s) de alta demanda están lejos del despacho. Son candidatos prioritarios para reubicación."  # noqa: E501
                tips.append(msg)
            slow_in_premium = len(
                slotting_diagnostics[
                    slotting_diagnostics["candidate_action"]
                    .str.contains("slow_mover_in_premium", case=False, na=False)
                ]
            )
            if slow_in_premium > 0:
                msg = f"🐌 {slow_in_premium} SKU(s) de movimiento lento ocupan zonas premium. Revisá si conviene moverlos a zonas de menor prioridad."  # noqa: E501
                tips.append(msg)

    if zone_diagnostics is not None and not zone_diagnostics.empty:
        over_cap = (
            zone_diagnostics[zone_diagnostics.get("over_capacity_location_count", 0) > 0]
            if "over_capacity_location_count" in zone_diagnostics.columns
            else pd.DataFrame()
        )
        if not over_cap.empty:
            zones_str = ", ".join(over_cap[Zones.ZONE_ID].astype(str).unique())
            tips.append(f"⚠️ Zonas con sobrecapacidad: {zones_str}. Considerá redistribuir carga.")

    if not tips:
        tips.append("✅ No se detectaron problemas significativos en los diagnósticos.")

    return tips


def generate_scoring_recommendations(
    priority_queue: pd.DataFrame | None,
    scoring_summary: pd.DataFrame | None,
) -> list[str]:
    """Generate insights from Phase 3 scoring."""
    tips: list[str] = []
    if priority_queue is not None and not priority_queue.empty:
        top_sku = priority_queue.iloc[0]
        score_col = "opportunity_score"
        if score_col in top_sku.index:
            entity = top_sku.get("entity_id", "N/A")
            score_val = top_sku[score_col]
            msg = f"🥇 La prioridad más alta es '{entity}' con score {score_val:.1f}. Revisá este caso primero."  # noqa: E501
            tips.append(msg)
            # Count high-priority items
            high_count = len(priority_queue[priority_queue[score_col] >= 80]) if score_col in priority_queue.columns else 0
            if high_count > 1:
                tips.append(f"🎯 {high_count} SKU(s) tienen score >= 80. Son candidatos prioritarios para reubicación inmediata.")
    if scoring_summary is not None and not scoring_summary.empty:
        if "metric" in scoring_summary.columns:
            sc_md = dict(zip(scoring_summary["metric"], scoring_summary["value"]))
            avg_score = sc_md.get("average_opportunity_score", None)
            if avg_score is not None:
                try:
                    tips.append(f"📊 Score promedio global: {float(avg_score):.1f}.")
                except (ValueError, TypeError):
                    pass
        elif "score_summary" in scoring_summary.columns:
            tips.append(f"📊 Resumen de scoring disponible con {len(scoring_summary)} métrica(s).")
    if not tips:
        tips.append("ℹ️ Ejecutá Phase 3 (run_scoring.py) para generar la cola de prioridad.")
    return tips


def generate_scenario_recommendations(
    scenario_summary: pd.DataFrame | None,
    scenario_comparison: pd.DataFrame | None,
) -> list[str]:
    """Generate insights from Phase 4 scenario comparison."""
    tips: list[str] = []
    if scenario_summary is not None and not scenario_summary.empty:
        if "scenario" in scenario_summary.columns:
            scenarios = scenario_summary["scenario"].tolist()
            tips.append(f"🔄 {len(scenarios)} escenarios comparados: {', '.join(scenarios)}.")
    if not tips:
        tips.append("ℹ️ Ejecutá Phase 4 (run_scenarios.py) para comparar escenarios analíticos.")
    return tips


def generate_optimization_recommendations(
    optimization_summary: pd.DataFrame | None,
    optimization_assignments: pd.DataFrame | None,
) -> list[str]:
    """Generate insights from Phase 5 optimization."""
    tips: list[str] = []
    if optimization_summary is not None and not optimization_summary.empty:
        if "metric" in optimization_summary.columns:
            opt_md = dict(zip(optimization_summary["metric"], optimization_summary["value"]))
            method = str(opt_md.get("solver_method", "desconocido"))
            sku_count = str(opt_md.get("selected_skus", "?"))
            total_cost = opt_md.get("total_assignment_cost", None)
            cost_str = f"{float(total_cost):.2f}" if total_cost is not None else "—"
            tips.append(f"⚙️ Optimización ejecutada con método '{method}' para {sku_count} SKU(s). Costo total: {cost_str}.")
        else:
            row = optimization_summary.iloc[0]
            method = (
                optimization_summary.iloc[0].get("method", "desconocido")
                if "method" in optimization_summary.columns
                else "desconocido"
            )
            sku_count = (
                optimization_summary.iloc[0].get("sku_count", "?")
                if "sku_count" in optimization_summary.columns
                else "?"
            )
            tips.append(f"⚙️ Optimización ejecutada con método '{method}' para {sku_count} SKU(s).")
    if optimization_assignments is not None and not optimization_assignments.empty:
        zone_col = next(
            (
                c
                for c in ["target_zone", "target_zone_id", "assigned_zone", "zone_id"]
                if c in optimization_assignments.columns
            ),
            None,
        )
        if zone_col:
            zone_counts = optimization_assignments[zone_col].value_counts()
            for zone, count in zone_counts.items():
                tips.append(f"📍 {int(count)} SKU(s) asignados a {zone}.")
    if not tips:
        tips.append("ℹ️ Ejecutá Phase 5 (run_optimization.py) para generar asignaciones.")
    return tips


def generate_simulation_recommendations(
    simulation_summary: pd.DataFrame | None,
) -> list[str]:
    """Generate insights from Phase 6 simulation."""
    tips: list[str] = []
    if simulation_summary is not None and not simulation_summary.empty:
        if "metric" in simulation_summary.columns:
            sim_md = dict(zip(simulation_summary["metric"], simulation_summary["value"]))
            # Map actual metric names from simulation output
            metric_map = {
                "avg_improvement_pct": ("📉 Mejora distancia promedio", "{:.1f}%"),
                "total_distance_saved_m": ("📏 Distancia total ahorrada", "{:,.0f} m"),
                "gini_coefficient_after": ("⚖️ Coeficiente Gini (después)", "{:.4f}"),
                "throughput_gain_pct": ("🚚 Ganancia de throughput", "{:.1f}%"),
                "avg_distance_per_order_current": ("📏 Distancia promedio actual", "{:,.0f} m"),
                "avg_distance_per_order_optimized": ("📏 Distancia promedio optimizada", "{:,.0f} m"),
                "total_time_saved_s": ("⏱️ Tiempo total ahorrado", "{:,.0f} s"),
            }
            for metric_name, (label, fmt) in metric_map.items():
                val = sim_md.get(metric_name)
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    try:
                        tips.append(f"{label}: {fmt.format(float(val))}")
                    except (ValueError, TypeError):
                        tips.append(f"{label}: {val}")
        else:
            row = simulation_summary.iloc[0]
            for col_pct in [
                c
                for c in simulation_summary.columns
                if "improvement" in c.lower() or "reduction" in c.lower() or "saving" in c.lower()
            ]:
                val = row.get(col_pct)
                if val is not None:
                    try:
                        tips.append(f"📉 {col_pct.replace('_', ' ').title()}: {float(val):.1f}%")
                    except (ValueError, TypeError):
                        pass
            for col_gini in [c for c in simulation_summary.columns if "gini" in c.lower()]:
                val = row.get(col_gini)
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    try:
                        tips.append(f"⚖️ {col_gini.replace('_', ' ').title()}: {float(val):.4f}")
                    except (ValueError, TypeError):
                        pass
    if not tips:
        tips.append("ℹ️ Ejecutá Phase 6 (run_simulation.py) para generar la simulación operativa.")
    return tips


def _unique_or_len(dataframe: pd.DataFrame | None, column: str) -> int | None:
    if dataframe is None:
        return None
    if column in dataframe.columns:
        return int(dataframe[column].nunique())
    return len(dataframe)
