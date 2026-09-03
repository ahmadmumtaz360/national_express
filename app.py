"""Streamlit entry point for the Bus Operations Monitor Databricks App."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

overview, network, exceptions = st.tabs(["Overview", "Network performance", "Service exceptions"])
with overview:
    left, right = st.columns([1.55, 1])
    daily = daily_performance(filtered)
    trend = make_subplots(specs=[[{"secondary_y": True}]])
    trend.add_trace(go.Scatter(x=daily["journey_date"], y=daily["journeys"], name="Journeys", mode="lines+markers",
                               line=dict(color="#7CC4FA", width=2), marker=dict(size=5)), secondary_y=False)
    trend.add_trace(go.Scatter(x=daily["journey_date"], y=daily["average_delay"], name="Average delay", mode="lines+markers",
                               line=dict(color=BLUE, width=3), marker=dict(size=6)), secondary_y=True)
    trend.update_layout(title="Journeys and delays over time")
    trend.update_xaxes(title_text="Operating date")
    trend.update_yaxes(title_text="Journeys", secondary_y=False)
    trend.update_yaxes(title_text="Average delay (min)", secondary_y=True, showgrid=False)
    left.plotly_chart(polish_chart(trend), use_container_width=True)
    status_counts = filtered["journey_status"].value_counts().reindex(["On Time","Delayed","Cancelled"], fill_value=0)
    donut = go.Figure(go.Pie(labels=status_counts.index, values=status_counts.values, hole=.68, marker_colors=[GREEN,AMBER,RED],
                             textinfo="percent", hovertemplate="%{label}: %{value:,}<extra></extra>"))
    donut.update_layout(title="Journey status mix", annotations=[dict(text=f"{len(filtered):,}<br><span style='font-size:11px'>journeys</span>", x=.5,y=.5,showarrow=False,font_size=20)])
    donut = polish_chart(donut)
    donut.update_layout(legend=dict(orientation="h", yanchor="top", y=-.02, xanchor="center", x=.5))
    right.plotly_chart(donut, use_container_width=True)
    routes_data = route_performance(filtered).head(10).sort_values("average_delay")
    route_chart = px.bar(routes_data, x="average_delay", y="route_number", orientation="h", title="Routes requiring attention",
                         labels={"average_delay":"Average delay (minutes)","route_number":"Route"}, color="average_delay",
                         color_continuous_scale=[[0,CYAN],[1,RED]])
    route_chart.update_layout(coloraxis_showscale=False)
    st.plotly_chart(polish_chart(route_chart, 410), use_container_width=True)

with network:
    depot = depot_performance(filtered)
    depot_chart = px.bar(depot, x="depot", y="on_time_pct", color="average_delay", text_auto=".1f", title="Performance by depot",
                         labels={"on_time_pct":"On-time journeys (%)","average_delay":"Avg delay","depot":"Depot"}, color_continuous_scale="RdYlGn_r")
    depot_chart.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
    st.plotly_chart(polish_chart(depot_chart, 420), use_container_width=True)
    col1, col2 = st.columns(2)
    vehicle = filtered.groupby("vehicle_type", as_index=False).agg(journeys=("journey_id","count"), average_delay=("delay_minutes","mean"))
    vehicle_chart = px.bar(vehicle, x="vehicle_type", y="journeys", color="vehicle_type", title="Fleet mix", text_auto=True,
                           color_discrete_map={"Electric":CYAN,"Diesel":NAVY})
    vehicle_chart.update_layout(showlegend=False)
    col1.plotly_chart(polish_chart(vehicle_chart, 340), use_container_width=True)
    volume_chart = px.area(daily, x="journey_date", y="journeys", title="Journey volume",
                           labels={"journeys":"Journeys","journey_date":"Operating date"}, color_discrete_sequence=[CYAN])
    col2.plotly_chart(polish_chart(volume_chart, 340), use_container_width=True)

with exceptions:
    st.markdown('<div class="section-title">Most delayed journeys</div>', unsafe_allow_html=True)
    columns = ["journey_id","bus_id","route_number","depot","journey_date","scheduled_departure","actual_departure","delay_minutes","journey_status","passenger_count","vehicle_type"]
    exceptions_data = filtered.sort_values("delay_minutes", ascending=False)[columns].head(100)
    st.dataframe(exceptions_data, hide_index=True, use_container_width=True, column_config={
        "journey_id":"Journey","bus_id":"Bus","route_number":"Route",
        "journey_date":st.column_config.DateColumn("Date",format="DD MMM YYYY"),
        "scheduled_departure":st.column_config.DatetimeColumn("Scheduled",format="HH:mm"),
        "actual_departure":st.column_config.DatetimeColumn("Actual",format="HH:mm"),
        "delay_minutes":st.column_config.NumberColumn("Delay",format="%d min"),
        "passenger_count":st.column_config.NumberColumn("Passengers",format="%d")})
    st.download_button("Download exceptions CSV", exceptions_data.to_csv(index=False).encode("utf-8"),
                       file_name=f"journey_exceptions_{datetime.now():%Y%m%d}.csv", mime="text/csv")

st.caption("NX Operations Control · Proof-of-concept using synthetic operational data · Not for live service decisions")
