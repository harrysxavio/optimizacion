"""Minimal technical Streamlit front for inspecting Phase 1 slotting outputs."""

from __future__ import annotations

import streamlit as st

from slotting_optimization_engine.app.dashboard_data import (
    PREREQUISITE_COMMANDS,
    compute_kpis,
    load_dashboard_data,
    location_chart_data,
    missing_outputs,
    preview_table,
    status_table,
    zone_chart_data,
)


def main() -> None:
    """Render the Streamlit technical inspection dashboard."""
    st.set_page_config(
        page_title="Slotting Control Tower",
        page_icon="📦",
        layout="wide",
    )
    _inject_control_tower_styles()

    data = load_dashboard_data()
    kpis = compute_kpis(data)
    unavailable = missing_outputs(data.statuses)

    st.title("Slotting Control Tower")
    st.caption(
        "Technical inspection front for processed slotting outputs. "
        "This view is descriptive only and does not generate recommendations."
    )

    st.info(
        "Alignment score is preliminary and non-prescriptive. It is a heuristic "
        "inspection signal only, not an operational instruction or optimization result.",
        icon="⚠️",
    )

    if unavailable:
        st.warning(
            "One or more processed outputs are missing or unreadable. Generate Phase 1 "
            "outputs with the commands below, then refresh this page.",
            icon="🧭",
        )
        st.code("\n".join(PREREQUISITE_COMMANDS), language="powershell")

    _render_kpis(kpis)

    st.subheader("Dataset availability")
    st.dataframe(status_table(data.statuses), use_container_width=True, hide_index=True)

    left, right = st.columns((1, 1), gap="large")
    with left:
        st.subheader("Zone utilization")
        zone_chart = zone_chart_data(data.zone_utilization)
        if zone_chart.empty:
            st.caption("Zone utilization chart unavailable until processed data is present.")
        else:
            st.bar_chart(zone_chart)
        st.dataframe(preview_table(data.zone_utilization), use_container_width=True)

    with right:
        st.subheader("Top utilized locations")
        location_chart = location_chart_data(data.location_utilization)
        if location_chart.empty:
            st.caption("Location utilization chart unavailable until processed data is present.")
        else:
            st.bar_chart(location_chart)
        st.dataframe(preview_table(data.location_utilization), use_container_width=True)

    st.subheader("SKU feature preview")
    st.caption("Bounded preview of the wide feature table generated in Phase 1.")
    st.dataframe(preview_table(data.sku_features, rows=50), use_container_width=True)

    st.subheader("Diagnostics availability")
    st.caption("Phase 2 diagnostic outputs are descriptive flags for analyst review only.")
    st.dataframe(preview_table(data.diagnostic_summary), use_container_width=True)


def _render_kpis(kpis: dict[str, int | float | None]) -> None:
    columns = st.columns(5)
    columns[0].metric("SKUs", _format_number(kpis["sku_count"]))
    columns[1].metric("Zones", _format_number(kpis["zone_count"]))
    columns[2].metric("Locations", _format_number(kpis["location_count"]))
    columns[3].metric("Avg utilization", _format_pct(kpis["avg_utilization_pct"]))
    columns[4].metric("Over-capacity locations", _format_number(kpis["over_capacity_locations"]))


def _format_number(value: int | float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}"


def _format_pct(value: int | float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.1f}%"


def _inject_control_tower_styles() -> None:
    st.markdown(
        """
        <style>
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
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
