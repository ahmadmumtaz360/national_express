"""Streamlit entry point for the Bus Operations Monitor Databricks App."""

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import build_insight, calculate_kpis, daily_performance, depot_performance, route_performance
from data_access import load_journeys

st.set_page_config(page_title="Bus Operations Monitor", page_icon="🚌", layout="wide")
st.title("Bus Operations Monitor")
st.caption("Operational journey performance · synthetic proof-of-concept data")


@st.cache_data(ttl=300, show_spinner="Loading journey data…")
def get_data() -> pd.DataFrame:
    return load_journeys()


try:
    journeys = get_data()
except Exception as exc:
    st.error(f"The journey dataset could not be loaded: {exc}")
    st.stop()

with st.sidebar:
    st.header("Filters")
    min_date, max_date = min(journeys["journey_date"]), max(journeys["journey_date"])
    selected_dates = st.date_input("Journey date", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    routes = st.multiselect("Route", sorted(journeys["route_number"].astype(str).unique()))
    depots = st.multiselect("Depot", sorted(journeys["depot"].unique()))
    vehicles = st.multiselect("Vehicle type", sorted(journeys["vehicle_type"].unique()))

filtered = journeys.copy()
if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    filtered = filtered[filtered["journey_date"].between(selected_dates[0], selected_dates[1])]
if routes:
    filtered = filtered[filtered["route_number"].astype(str).isin(routes)]
if depots:
    filtered = filtered[filtered["depot"].isin(depots)]
if vehicles:
    filtered = filtered[filtered["vehicle_type"].isin(vehicles)]

st.info(f"💡 {build_insight(filtered)}")
kpis = calculate_kpis(filtered)
cards = st.columns(6)
for card, label, value in zip(cards, ["Total journeys", "On time", "Delayed", "Cancelled", "Average delay", "Passengers"],
                              [f"{kpis.total_journeys:,}", f"{kpis.on_time_pct:.1f}%", f"{kpis.delayed_pct:.1f}%", f"{kpis.cancelled_pct:.1f}%", f"{kpis.average_delay:.1f} min", f"{kpis.total_passengers:,}"]):
    card.metric(label, value)

if filtered.empty:
    st.warning("No journeys match the selected filters.")
    st.stop()

left, right = st.columns(2)
routes_data = route_performance(filtered).head(10).sort_values("average_delay")
left.plotly_chart(px.bar(routes_data, x="average_delay", y="route_number", orientation="h", title="Routes with worst average delays", labels={"average_delay": "Average delay (minutes)", "route_number": "Route"}), use_container_width=True)
daily = daily_performance(filtered)
right.plotly_chart(px.line(daily, x="journey_date", y=["journeys", "average_delay"], markers=True, title="Journeys and delays over time", labels={"value": "Value", "journey_date": "Date", "variable": "Measure"}), use_container_width=True)
depot = depot_performance(filtered)
st.plotly_chart(px.bar(depot, x="depot", y="on_time_pct", color="average_delay", title="Performance by depot", labels={"on_time_pct": "On-time journeys (%)", "average_delay": "Avg delay"}, color_continuous_scale="RdYlGn_r"), use_container_width=True)

st.subheader("Most delayed journeys")
columns = ["journey_id", "bus_id", "route_number", "depot", "journey_date", "scheduled_departure", "actual_departure", "delay_minutes", "journey_status", "passenger_count", "vehicle_type"]
st.dataframe(filtered.sort_values("delay_minutes", ascending=False)[columns].head(25), hide_index=True, use_container_width=True)
