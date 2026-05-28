"""Panel de Control de Slotting — Streamlit frontend completo.

7 pestañas que cubren todas las fases del proyecto con dashboards visuales,
indicadores con semáforos, paneles ejecutables, descarga de templates,
validación de uploads y ejecución de scripts desde la UI.
"""

from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from slotting_optimization_engine.app.dashboard_data import (
    DashboardData,
    EXPECTED_OUTPUT_FILES_PHASE_1_2,
    FullDashboardData,
    PHASE_GROUPS,
    TEMPLATES,
    TEMPLATE_DATASET_KEYS,
    compute_kpis,
    compute_overview_indicators,
    generate_diagnostics_recommendations,
    generate_health_signal,
    generate_optimization_recommendations,
    generate_scenario_recommendations,
    generate_scoring_recommendations,
    generate_simulation_recommendations,
    generate_template_df,
    get_template_csv,
    load_dashboard_data,
    load_full_dashboard_data,
    location_chart_data,
    run_phase_script,
    status_table,
    validate_uploaded_csv,
    zone_chart_data,
)

# ── Phase descriptions ──────────────────────────────────────────────────

PHASE_DESC: dict[str, str] = {
    "overview": (
        "**Panel de control global.** Indicadores clave de todas las fases del pipeline de slotting. "
        "Cada fase muestra su estado actual (✅ completo, ⚠️ alerta, ❌ pendiente), "
        "métricas principales y recomendaciones accionables."
    ),
    "diagnostics": (
        "**Diagnóstico de slotting (Fase 2).** Analiza la ubicación actual de cada SKU y detecta "
        "oportunidades de mejora: SKUs de alta demanda lejos del despacho, productos de movimiento "
        "lento en zonas premium, zonas con sobrecapacidad. Cada flag incluye una acción candidata."
    ),
    "scoring": (
        "**Scoring de oportunidades (Fase 3).** Cada SKU recibe un puntaje basado en demanda, "
        "distancia al despacho, rotación y restricciones de capacidad. La cola de prioridad "
        "ordena los SKUs por impacto potencial. **A mayor score, mayor beneficio al reubicar.**"
    ),
    "scenarios": (
        "**Comparación de escenarios (Fase 4).** Evalúa múltiples estrategias de slotting: "
        "ABC cross-dock, demanda ponderada, rotación pura. Cada escenario propone un mix de "
        "acciones (reubicar, intercambiar, mantener) con su impacto estimado."
    ),
    "optimization": (
        "**Asignación optimizada (Fase 5).** Algoritmo que maximiza el alineamiento SKU-ubicación "
        "respetando restricciones de capacidad, zona y tipo de producto. Genera asignaciones "
        "concretas y una matriz de costos para evaluar el impacto."
    ),
    "simulation": (
        "**Simulación operativa (Fase 6).** Modela el impacto de las asignaciones propuestas en "
        "métricas operativas: distancia total de viaje, congestión por zona, throughput y "
        "distribución de carga de trabajo (coeficiente Gini)."
    ),
}


# ── UI helpers ──────────────────────────────────────────────────────────


def _phase_status_card(indicator) -> None:
    """Render a single phase indicator card with traffic-light emoji."""
    with st.container(border=True):
        cols = st.columns([1, 5, 1])
        with cols[0]:
            st.markdown(f"<h2 style='margin:0; line-height:1'>{indicator.status_emoji}</h2>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"**{indicator.label}**")
            if indicator.metrics:
                metric_str = " · ".join(
                    f"{k}: **{v}**" for k, v in indicator.metrics if v is not None
                )
                st.caption(metric_str)
        with cols[2]:
            st.caption(indicator.status.upper())
        st.markdown(indicator.message)
        if indicator.recommendations and indicator.recommendations[0] != "✅ Base de datos lista para diagnóstico.":
            for r in indicator.recommendations[:2]:
                st.markdown(f"- {r}")


def _section_header(title: str, help_text: str | None = None) -> None:
    """Render a section header with optional info tooltip."""
    if help_text:
        col_h, col_info = st.columns([10, 1])
        with col_h:
            st.subheader(title)
        with col_info:
            st.markdown(
                f"<span title='{help_text}' style='cursor:help; font-size:1.2rem; "
                f"color:#566769;'>&#9432;</span>",
                unsafe_allow_html=True,
            )
    else:
        st.subheader(title)


# ── App ────────────────────────────────────────────────────────────────


def main() -> None:
    """Render the full multi-phase Slotting Control Panel."""
    st.set_page_config(
        page_title="Slotting Control Panel",
        page_icon="📦",
        layout="wide",
    )
    _inject_control_tower_styles()

    # ── Load data ──────────────────────────────────────────────────
    full_data = load_full_dashboard_data()
    all_statuses = full_data.statuses

    phase_1_2 = DashboardData(
        sku_features=full_data.sku_features,
        location_utilization=full_data.location_utilization,
        zone_utilization=full_data.zone_utilization,
        slotting_diagnostics=full_data.slotting_diagnostics,
        location_diagnostics=full_data.location_diagnostics,
        zone_diagnostics=full_data.zone_diagnostics,
        category_diagnostics=full_data.category_diagnostics,
        diagnostic_summary=full_data.diagnostic_summary,
        statuses=tuple(
            s for s in all_statuses
            if s.name in EXPECTED_OUTPUT_FILES_PHASE_1_2
        ),
    )

    kpis = compute_kpis(phase_1_2)
    indicators = compute_overview_indicators(full_data)

    # ── Header ────────────────────────────────────────────────────
    col_title, col_h = st.columns([5, 1])
    with col_title:
        st.title("📦 Slotting Control Panel")
        st.caption(
            "Pipeline completo de slotting — Fases 1 a 6. "
            "Panel ejecutivo con indicadores, diagnósticos y análisis."
        )
    with col_h:
        health_emoji, health_msg = generate_health_signal(kpis)
        st.metric("Estado general", health_emoji, help="Indicador de salud del sistema")

    # ── Tabs ──────────────────────────────────────────────────────
    tabs = st.tabs([
        "📊 Panel Global",
        "🔬 Diagnóstico",
        "📈 Scoring",
        "🔄 Escenarios",
        "⚙️ Optimización",
        "🎲 Simulación",
        "📋 Templates & Upload",
    ])

    tab_overview, tab_diag, tab_scoring, tab_scenarios, tab_optim, tab_sim, tab_tpl = tabs

    # ══════════════════════════════════════════════════════════════
    # TAB 1 — PANEL GLOBAL (Overview)
    # ══════════════════════════════════════════════════════════════
    with tab_overview:
        st.markdown(PHASE_DESC["overview"])

        # Health alert
        if "🔴" in health_emoji:
            st.error(health_msg, icon="🚨")
        elif "🟢" in health_emoji:
            st.success(health_msg, icon="✅")
        else:
            st.warning(health_msg, icon="⚠️")

        # ── KPI row ──────────────────────────────────────────────
        kpi_cols = st.columns(5)
        kpi_data = [
            ("SKUs", kpis.get("sku_count"), "{:,.0f}", ""),
            ("Zonas", kpis.get("zone_count"), "{:,.0f}", "Zonas del depósito configuradas"),
            ("Ubicaciones", kpis.get("location_count"), "{:,.0f}", "Ubicaciones físicas (estanterías)"),
            ("Utilización prom.", kpis.get("avg_utilization_pct"), "{:,.1f}%", "% de capacidad volumétrica utilizada en promedio"),
            ("Sobre capacidad", kpis.get("over_capacity_locations"), "{:,.0f}", "Ubicaciones que exceden su capacidad máxima"),
        ]
        for col, (label, val, fmt, help_text) in zip(kpi_cols, kpi_data):
            if val is None:
                col.metric(label, "—", help=help_text or None)
            else:
                col.metric(label, fmt.format(val), help=help_text or None)

        st.divider()

        # ── Phase indicator cards ─────────────────────────────────
        _section_header("Estado por fase", help_text="Cada fase del pipeline con su indicador de estado, métricas clave y recomendaciones.")

        row1 = st.columns(3)
        row2 = st.columns(3)
        for i, ind in enumerate(indicators):
            with (row1[i] if i < 3 else row2[i - 3]):
                _phase_status_card(ind)

        st.divider()

        # ── Collapsible charts ────────────────────────────────────
        with st.expander("📊 Ver gráficos de utilización", expanded=False):
            st.markdown(
                "<span title='Utilización volumétrica y de peso por zona y ubicación. "
                "Muestra qué zonas/ubicaciones están más cargadas.' "
                "style='cursor:help; font-size:0.9rem; color:#566769;'>&#9432; "
                "Gráficos de utilización — pasá el mouse sobre las barras para ver valores exactos.</span>",
                unsafe_allow_html=True,
            )
            chart_cols = st.columns(2)
            with chart_cols[0]:
                st.subheader("Utilización por zona")
                zc = zone_chart_data(full_data.zone_utilization)
                if zc.empty:
                    st.caption("Sin datos.")
                else:
                    st.bar_chart(zc)
            with chart_cols[1]:
                st.subheader("Top ubicaciones")
                lc = location_chart_data(full_data.location_utilization)
                if lc.empty:
                    st.caption("Sin datos.")
                else:
                    st.bar_chart(lc)

    # ══════════════════════════════════════════════════════════════
    # TAB 2 — DIAGNÓSTICO
    # ══════════════════════════════════════════════════════════════
    with tab_diag:
        st.markdown(PHASE_DESC["diagnostics"])

        diag_indicator = indicators[1]  # Phase 2
        st.info(diag_indicator.message, icon=diag_indicator.status_emoji)

        # ── Summary panel ─────────────────────────────────────────
        diag = full_data.diagnostic_summary
        sd = full_data.slotting_diagnostics
        zd = full_data.zone_diagnostics

        total_flags = 0
        if diag is not None and "flag_count" in diag.columns:
            total_flags = int(diag["flag_count"].sum())

        high_demand_far = 0
        slow_in_premium = 0
        if sd is not None and "candidate_action" in sd.columns:
            high_demand_far = int((sd["candidate_action"].str.contains("high_demand_far", case=False, na=False)).sum())
            slow_in_premium = int((sd["candidate_action"].str.contains("slow_mover_in_premium", case=False, na=False)).sum())

        over_cap_zones = 0
        if zd is not None and "over_capacity_location_count" in zd.columns:
            over_cap_zones = int((zd["over_capacity_location_count"] > 0).sum())

        sum_cols = st.columns(4)
        sum_cols[0].metric("🚩 Total flags", total_flags, help="Cantidad total de flags de diagnóstico en todos los SKUs")
        sum_cols[1].metric("📦 Alta demanda lejos", high_demand_far, help="SKUs de alta demanda ubicados lejos del despacho")
        sum_cols[2].metric("🐌 Lentos en premium", slow_in_premium, help="SKUs de movimiento lento en zonas premium")
        sum_cols[3].metric("⚠️ Zonas sobrecapacidad", over_cap_zones, help="Zonas con ubicaciones que exceden su capacidad")

        st.divider()

        # ── What each flag means ──────────────────────────────────
        _section_header("¿Qué significan estos flags?", help_text="Cada flag de diagnóstico representa una oportunidad de mejora en la asignación de SKUs a ubicaciones.")

        flag_meanings = {
            "📦 Alta demanda lejos del despacho": (
                "SKUs con alta rotación que están asignados a ubicaciones distantes de la zona de despacho. "
                "**Impacto:** aumenta el tiempo de picking y la distancia recorrida por los operarios. "
                "**Acción:** reubicar estos SKUs en zonas cercanas al despacho (prioridad baja = cerca)."
            ),
            "🐌 Lentos en zonas premium": (
                "SKUs de baja rotación ocupando ubicaciones cercanas al despacho (zonas premium). "
                "**Impacto:** desperdicio de espacio valioso que podrían usar SKUs de alta demanda. "
                "**Acción:** mover estos SKUs a zonas de menor prioridad."
            ),
            "⚠️ Zonas con sobrecapacidad": (
                "Zonas del depósito donde una o más ubicaciones exceden su capacidad volumétrica o de peso. "
                "**Impacto:** riesgo operativo y potencial daño a productos. "
                "**Acción:** redistribuir carga entre zonas o liberar espacio en las zonas afectadas."
            ),
        }
        for title, explanation in flag_meanings.items():
            with st.expander(title, expanded=False):
                st.markdown(explanation)

        st.divider()

        # ── Actionable recommendations ────────────────────────────
        diag_recs = generate_diagnostics_recommendations(diag, sd, zd)
        _section_header("🎯 Puntos de acción", help_text="Recomendaciones concretas basadas en los flags de diagnóstico.")

        for rec in diag_recs:
            emoji = "✅" if rec.startswith("✅") else "⚠️" if rec.startswith("⚠️") else "📌"
            st.markdown(f"{emoji} {rec}")

        st.divider()

        # ── Detail tables (collapsible) ───────────────────────────
        _section_header("📋 Tablas de detalle", help_text="Datos completos de diagnóstico para revisión analítica.")

        diag_sections = [
            ("Slotting diagnostics — flags por SKU", full_data.slotting_diagnostics, "Cada fila es un SKU con su flag de diagnóstico y acción candidata."),
            ("Location diagnostics — flags por ubicación", full_data.location_diagnostics, "Diagnóstico a nivel de ubicación física."),
            ("Zone diagnostics — flags por zona", full_data.zone_diagnostics, "Resumen por zona con conteo de ubicaciones sobrecapacidad."),
            ("Category diagnostics — flags por categoría", full_data.category_diagnostics, "Diagnóstico agregado por categoría de producto."),
            ("Diagnostic summary — resumen de flags", full_data.diagnostic_summary, "Conteo de flags por tipo y severidad."),
        ]
        for title, df, desc in diag_sections:
            with st.expander(f"{title}"):
                st.caption(desc)
                preview = df.head(100) if df is not None else None
                if preview is None or preview.empty:
                    st.caption("Sin datos.")
                else:
                    st.dataframe(preview, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 3 — SCORING
    # ══════════════════════════════════════════════════════════════
    with tab_scoring:
        st.markdown(PHASE_DESC["scoring"])

        sc_indicator = indicators[2]
        st.info(sc_indicator.message, icon=sc_indicator.status_emoji)

        # ── Key metrics ──────────────────────────────────────────
        pq = full_data.priority_queue
        ss = full_data.scoring_summary
        oscores = full_data.opportunity_scores

        total_scored = len(pq) if pq is not None else 0
        avg_score = None
        top_score = None
        top_sku = None
        if pq is not None and not pq.empty:
            if "opportunity_score" in pq.columns:
                avg_score = float(pq["opportunity_score"].mean())
                top_row = pq.iloc[0]
                top_score = float(top_row["opportunity_score"])
                top_sku = str(top_row.get("entity_id", pq.index[0]))

        score_cols = st.columns(4)
        score_cols[0].metric("🎯 SKUs evaluados", total_scored, help="Cantidad total de SKUs con puntaje de oportunidad")
        score_cols[1].metric("📊 Score promedio", f"{avg_score:.1f}" if avg_score is not None else "—", help="Puntaje de oportunidad promedio en todos los SKUs")
        score_cols[2].metric("🥇 Score máximo", f"{top_score:.1f}" if top_score is not None else "—", help="Mayor puntaje de oportunidad detectado")
        score_cols[3].metric("🔝 Top SKU", top_sku or "—", help="SKU con mayor prioridad de reubicación")

        st.divider()

        # ── How to read scoring ──────────────────────────────────
        _section_header("📖 Cómo interpretar el scoring", help_text="El scoring ordena los SKUs por beneficio potencial de reubicación.")

        with st.expander("¿Cómo se calcula el score?", expanded=False):
            st.markdown("""
            El score de oportunidad combina:
            1. **Demanda del SKU** — mayor demanda → mayor impacto al reubicar cerca del despacho
            2. **Distancia actual al despacho** — SKUs lejos tienen más potencial de mejora
            3. **Rotación** — SKUs de alta rotación se benefician más de estar cerca
            4. **Restricciones de capacidad** — si hay espacio disponible en zonas cercanas

            **Regla general:** SKUs con score > 80 son candidatos prioritarios para reubicación inmediata.
            """)

        st.divider()

        # ── Action points ────────────────────────────────────────
        scoring_recs = generate_scoring_recommendations(pq, ss)
        _section_header("🎯 Puntos de acción", help_text="Recomendaciones basadas en los scores de oportunidad.")
        for rec in scoring_recs:
            st.markdown(f"- {rec}")

        st.divider()

        # ── Detail tables ────────────────────────────────────────
        _section_header("📋 Tablas de detalle", help_text="Datos completos de scoring para revisión.")

        with st.expander("Priority queue — cola de prioridad", expanded=False):
            st.caption("SKUs ordenados por score de oportunidad descendente. Empezá por los primeros.")
            st.dataframe(pq.head(200) if pq is not None else None, use_container_width=True, hide_index=True)

        with st.expander("Scoring summary — resumen de scoring", expanded=False):
            st.dataframe(ss, use_container_width=True, hide_index=True)

        with st.expander("Opportunity scores — scores completos", expanded=False):
            st.dataframe(oscores.head(200) if oscores is not None else None, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 4 — ESCENARIOS
    # ══════════════════════════════════════════════════════════════
    with tab_scenarios:
        st.markdown(PHASE_DESC["scenarios"])

        sc_ind = indicators[3]
        st.info(sc_ind.message, icon=sc_ind.status_emoji)

        sc_comp = full_data.scenario_comparison
        sc_sum = full_data.scenario_summary
        sc_mix = full_data.scenario_action_mix

        # ── What each scenario means ─────────────────────────────
        _section_header("📖 ¿Qué significa cada escenario?", help_text="Cada escenario representa una estrategia diferente de slotting.")

        scenario_explanations = {
            "abc_crossdock": "🏭 **ABC Cross-dock:** Agrupa SKUs por rotación (ABC) cerca del despacho. Ideal para depósitos con alta rotación y cross-docking.",
            "weighted_demand": "📦 **Demanda ponderada:** Asigna prioridad según demanda diaria promedio × volumen. Balancea rotación y espacio ocupado.",
            "rotation_only": "🔄 **Rotación pura:** Solo considera rotación del SKU. Estrategia simple pero efectiva cuando el espacio no es restrictivo.",
        }
        if sc_sum is not None and not sc_sum.empty:
            for _, row in sc_sum.iterrows():
                name = str(row.get("scenario", "")).lower()
                if name in scenario_explanations:
                    st.info(scenario_explanations[name], icon="💡")
                elif "scenario" in sc_sum.columns:
                    st.info(f"💡 **{row['scenario']}** — Estrategia de slotting evaluada en la comparación.")

        st.divider()

        # ── Comparison table ─────────────────────────────────────
        _section_header("📊 Comparación de escenarios", help_text="Métricas clave de cada escenario para comparar su impacto.")

        if sc_comp is not None and not sc_comp.empty:
            st.dataframe(sc_comp, use_container_width=True, hide_index=True)
        else:
            st.caption("Sin datos de comparación.")

        st.divider()

        # ── Recommendations ──────────────────────────────────────
        scen_recs = generate_scenario_recommendations(sc_sum, sc_comp)
        _section_header("🎯 Recomendaciones", help_text="Basadas en la comparación de escenarios.")
        for rec in scen_recs:
            st.markdown(f"- {rec}")

        st.divider()

        # ── Detail tables ────────────────────────────────────────
        _section_header("📋 Detalle por escenario", help_text="Action mix propuesto para cada escenario.")

        with st.expander("Action mix por escenario", expanded=False):
            st.caption("Cantidad de SKUs a reubicar, intercambiar o mantener por escenario.")
            st.dataframe(sc_mix, use_container_width=True, hide_index=True)

        with st.expander("Resumen de escenarios", expanded=False):
            st.dataframe(sc_sum, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 5 — OPTIMIZACIÓN
    # ══════════════════════════════════════════════════════════════
    with tab_optim:
        st.markdown(PHASE_DESC["optimization"])

        opt_ind = indicators[4]
        st.info(opt_ind.message, icon=opt_ind.status_emoji)

        opt_sum = full_data.optimization_summary
        opt_assign = full_data.optimization_assignments
        opt_cost = full_data.optimization_cost_matrix

        # ── Key metrics ──────────────────────────────────────────
        opt_method = "—"
        opt_sku_count = "—"
        opt_total_cost = "—"
        opt_assigned = "—"
        if opt_sum is not None and not opt_sum.empty and "metric" in opt_sum.columns:
            opt_md = dict(zip(opt_sum["metric"], opt_sum["value"]))
            opt_method = str(opt_md.get("solver_method", opt_method))
            opt_sku_count = str(opt_md.get("selected_skus", opt_sku_count))
            opt_total_cost = f"{float(opt_md['total_assignment_cost']):,.2f}" if "total_assignment_cost" in opt_md else opt_total_cost
            opt_assigned = str(opt_md.get("assigned_rows", opt_assigned))

        opt_cols = st.columns(4)
        opt_cols[0].metric("⚙️ Método", opt_method, help="Algoritmo de optimización utilizado")
        opt_cols[1].metric("📦 SKUs asignados", opt_sku_count, help="Cantidad de SKUs con asignación optimizada")
        opt_cols[2].metric("💵 Costo total", opt_total_cost, help="Costo total estimado de las asignaciones")
        opt_cols[3].metric("📋 Total asignaciones", opt_assigned, help="Cantidad total de asignaciones generadas")

        st.divider()

        # ── How optimization works ───────────────────────────────
        _section_header("🔧 ¿Cómo funciona la optimización?", help_text="El algoritmo detrás de las asignaciones propuestas.")
        with st.expander("Ver explicación", expanded=False):
            st.markdown("""
            La optimización de slotting resuelve un **problema de asignación**:
            - **Objetivo:** maximizar el alignment score entre SKUs y ubicaciones
            - **Restricciones:** capacidad volumétrica, capacidad de peso, tipo de zona, compatibilidad producto-ubicación
            - **Método:** algoritmo greedy con constraints propagation (o el método configurado)
            - **Output:** para cada SKU, la ubicación óptima asignada y el costo asociado

            **La matriz de costos** permite visualizar el trade-off de asignar cada SKU a cada ubicación disponible.
            """)

        st.divider()

        # ── Recommendations ──────────────────────────────────────
        optim_recs = generate_optimization_recommendations(opt_sum, opt_assign)
        _section_header("🎯 Recomendaciones", help_text="Basadas en los resultados de optimización.")
        for rec in optim_recs:
            st.markdown(f"- {rec}")

        st.divider()

        # ── Detail tables ────────────────────────────────────────
        _section_header("📋 Tablas de detalle", help_text="Datos completos de optimización.")

        with st.expander("Asignaciones", expanded=False):
            st.caption("Cada fila es una asignación SKU → ubicación con su costo.")
            st.dataframe(opt_assign.head(500) if opt_assign is not None else None, use_container_width=True, hide_index=True)

        with st.expander("Resumen de optimización", expanded=False):
            st.dataframe(opt_sum, use_container_width=True, hide_index=True)

        with st.expander("Matriz de costos", expanded=False):
            st.caption("Costo de asignar cada SKU a cada ubicación. Filas = SKUs, columnas = ubicaciones.")
            st.dataframe(opt_cost.head(200) if opt_cost is not None else None, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 6 — SIMULACIÓN
    # ══════════════════════════════════════════════════════════════
    with tab_sim:
        st.markdown(PHASE_DESC["simulation"])

        sim_ind = indicators[5]
        st.info(sim_ind.message, icon=sim_ind.status_emoji)

        sim_sum = full_data.simulation_summary
        sim_travel = full_data.travel_aggregate
        sim_zone = full_data.zone_impact

        # ── Key metrics ──────────────────────────────────────────
        if sim_sum is not None and not sim_sum.empty:
            sim_cols = st.columns(4)
            if "metric" in sim_sum.columns:
                sim_md = dict(zip(sim_sum["metric"], sim_sum["value"]))
                # Map actual simulation metric names
                imp_val = None
                for k in ["avg_improvement_pct", "travel_distance_improvement_pct", "improvement_pct"]:
                    v = sim_md.get(k)
                    if v is not None and not pd.isna(v):
                        try: imp_val = f"{float(v):.1f}%"
                        except: imp_val = str(v)
                        break
                gini_val = None
                for k in ["gini_coefficient_after", "gini_coefficient", "gini_change"]:
                    v = sim_md.get(k)
                    if v is not None and not pd.isna(v):
                        try: gini_val = f"{float(v):.4f}"
                        except: gini_val = str(v)
                        break
                dist_saved = sim_md.get("total_distance_saved_m", None)
                if dist_saved is not None and not pd.isna(dist_saved):
                    try: dist_saved = f"{float(dist_saved):,.0f} m"
                    except: pass
                else:
                    dist_saved = None
                throughput = sim_md.get("throughput_gain_pct", None)
                if throughput is not None and not pd.isna(throughput):
                    try: throughput = f"{float(throughput):.1f}%"
                    except: pass
                else:
                    throughput = None

                sim_cols[0].metric("📉 Mejora distancia", imp_val or "—", help="Porcentaje de reducción en distancia de viaje promedio por orden")
                sim_cols[1].metric("⚖️ Gini", gini_val or "—", help="Coeficiente Gini después de la optimización (0 = equilibrio perfecto)")
                sim_cols[2].metric("📏 Distancia ahorrada", dist_saved or "—", help="Distancia total ahorrada en metros")
                sim_cols[3].metric("🚚 Throughput", throughput or "—", help="Ganancia de throughput estimada")
            else:
                # Fallback: wide format
                row = sim_sum.iloc[0]
                imp_cols = [c for c in sim_sum.columns if "improvement" in c.lower() or "reduction" in c.lower()]
                imp_val = float(row[imp_cols[0]]) if imp_cols else None
                sim_cols[0].metric("📉 Mejora viaje", f"{imp_val:.1f}%" if imp_val is not None else "—", help="Porcentaje de reducción en distancia total de viaje")
                sim_cols[1].metric("⚖️ Gini", "—")
                sim_cols[2].metric("📏 Distancia", "—")
                sim_cols[3].metric("🚚 Throughput", "—")

        st.divider()

        # ── Execute button ───────────────────────────────────────
        _section_header("▶️ Ejecutar simulación", help_text="Ejecuta el script de simulación (Fase 6) desde la UI.")

        sim_status = st.empty()
        sim_output = st.empty()

        if st.button("▶️ Ejecutar simulación ahora", type="primary", use_container_width=True, help="Ejecuta run_simulation.py y actualiza los resultados en esta página."):
            with st.spinner("Ejecutando simulación... esto puede tomar varios minutos."):
                sim_status.info("⏳ Ejecutando...")
                success, output = run_phase_script("6")
                if success:
                    sim_status.success("✅ Simulación completada exitosamente.")
                    sim_output.code(output[:3000], language="text")
                    st.caption("🔄 Refrescá la página para ver los nuevos resultados en los indicadores.")
                    st.button("🔄 Recargar página", on_click=st.rerun, type="secondary")
                else:
                    sim_status.error(f"❌ Error en la simulación.")
                    sim_output.code(output[:3000], language="text")

        st.divider()

        # ── What the simulation measures ─────────────────────────
        _section_header("📖 ¿Qué mide la simulación?", help_text="Métricas operativas que modela la simulación.")

        with st.expander("Ver explicación de métricas", expanded=False):
            st.markdown("""
            | Métrica | ¿Qué significa? |
            |---------|----------------|
            | **Distancia de viaje** | Distancia total que recorren los operarios para completar todos los pickings. Menor = más eficiente. |
            | **Coeficiente Gini** | Mide la concentración de carga de trabajo entre zonas. 0 = todas las zones tienen carga similar. 1 = una sola zona concentra todo. |
            | **Throughput** | Capacidad estimada de procesamiento (órdenes por hora o por turno). |
            | **Impacto por zona** | Cómo cambia la carga de trabajo en cada zona con las asignaciones propuestas. |
            | **Escenarios de throughput** | Proyecciones de capacidad bajo diferentes volúmenes de demanda. |
            """)

        st.divider()

        # ── Recommendations ──────────────────────────────────────
        sim_recs = generate_simulation_recommendations(sim_sum)
        _section_header("🎯 Recomendaciones", help_text="Basadas en los resultados de simulación.")
        for rec in sim_recs:
            st.markdown(f"- {rec}")

        st.divider()

        # ── Detail tables ────────────────────────────────────────
        _section_header("📋 Tablas de detalle", help_text="Datos completos de simulación.")

        sim_sections = [
            ("Resumen de simulación", sim_sum),
            ("Travel aggregate", sim_travel),
            ("Zone impact", sim_zone),
            ("Throughput scenarios", full_data.throughput_scenarios),
            ("Order detail", full_data.order_detail),
        ]
        for title, df in sim_sections:
            with st.expander(title, expanded=False):
                if df is not None and not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.caption("Sin datos.")

    # ══════════════════════════════════════════════════════════════
    # TAB 7 — TEMPLATES & UPLOAD
    # ══════════════════════════════════════════════════════════════
    with tab_tpl:
        st.markdown(
            "**Descargá templates CSV** con las columnas esperadas por cada dataset del sistema. "
            "Usalos como base para tus archivos de entrada. También podés **subir y validar** "
            "tus propios datos."
        )

        # ── Template downloads ──────────────────────────────────
        for key in TEMPLATE_DATASET_KEYS:
            tpl = TEMPLATES[key]
            cols = st.columns([2, 3, 1, 1])
            with cols[0]:
                st.markdown(f"**{tpl['label']}**")
            with cols[1]:
                st.caption(tpl["description"])
            with cols[2]:
                with st.expander("Ver columnas"):
                    for col_name, col_type in tpl["columns"].items():
                        st.markdown(f"- `{col_name}` ({col_type})")
            with cols[3]:
                csv_data = get_template_csv(key)
                st.download_button(
                    label="⬇ CSV",
                    data=csv_data,
                    file_name=f"template_{key}.csv",
                    mime="text/csv",
                    key=f"dl_{key}",
                )

        st.divider()

        # ── Upload & Validate ───────────────────────────────────
        st.subheader("Subir y validar datos")

        dataset_key = st.selectbox(
            "Seleccioná el tipo de dataset",
            options=TEMPLATE_DATASET_KEYS,
            format_func=lambda k: TEMPLATES[k]["label"],
            key="upload_dataset_select",
            help="Elegí a qué dataset corresponde el archivo que querés subir.",
        )

        uploaded_file = st.file_uploader(
            "Seleccioná un archivo CSV",
            type=["csv"],
            key="file_uploader",
            help="El archivo debe ser CSV con extensión .csv. Máximo 200 MB.",
        )

        if uploaded_file is not None:
            with st.spinner("Validando archivo…"):
                result = validate_uploaded_csv(uploaded_file, dataset_key)

            if result.is_valid:
                st.success(
                    f"✅ Archivo válido — {result.row_count} filas, "
                    f"{result.column_count} columnas."
                )
            else:
                st.error("❌ El archivo tiene errores de validación:")

            if result.errors:
                for err in result.errors:
                    st.warning(f"- {err}")

            if result.warnings:
                for warn in result.warnings:
                    st.info(f"ℹ️ {warn}")

            if result.is_valid:
                if st.checkbox(
                    "Usar estos datos para cálculos",
                    help="Al activarlo, los datos subidos reemplazarán las fuentes originales para el dataset seleccionado.",
                ):
                    st.session_state["validated_data"] = result
                    st.success("✅ Datos disponibles para la sesión actual.")

        # Status table for ALL phases
        st.divider()
        st.subheader("Estado completo — disponibles en disco")
        st.caption("Todos los datasets del pipeline con su estado de disponibilidad.")
        st.dataframe(
            status_table(all_statuses),
            use_container_width=True,
            hide_index=True,
        )


# ── Styles ─────────────────────────────────────────────────────────────


def _inject_control_tower_styles() -> None:
    st.markdown(
        """<style>
        .stApp {
            background: linear-gradient(180deg, #f4f7f8 0%, #eef3f3 100%);
            color: #172022;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #d7e0df;
            border-left: 4px solid #2f6f73;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            box-shadow: 0 8px 20px rgba(23, 32, 34, 0.06);
        }
        [data-testid="stMetricLabel"] {
            color: #566769;
            font-weight: 650;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #d7e0df;
            border-radius: 10px;
        }
        .st-emotion-cache-1avcm0n {
            background: #ffffff;
            border-radius: 10px;
            padding: 1rem;
            border: 1px solid #d7e0df;
        }
        </style>""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
