"""Production-style Streamlit entry point for the Bus Operations Monitor."""

from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import build_insight, calculate_kpis, daily_performance, depot_performance, route_performance
from data_access import load_journeys

st.set_page_config(page_title="NX Operations Control", page_icon="🚌", layout="wide")
NAVY, BLUE, CYAN, GREEN, AMBER, RED = "#071A2B", "#0B65D8", "#20B8CD", "#18A875", "#F5A524", "#E5484D"

st.markdown("""
<style>
.stApp{background:var(--background-color);color:var(--text-color)}.block-container{padding-top:1.4rem;padding-bottom:3rem;max-width:1500px}
[data-testid="stSidebar"]{background:#071A2B}
[data-testid="stSidebar"] .stMarkdown,[data-testid="stSidebar"] [data-testid="stCaptionContainer"],[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{color:#F7FAFC!important}
[data-testid="stMetric"]{background:var(--secondary-background-color);border:1px solid rgba(128,128,128,.25);border-radius:14px;padding:1rem 1.05rem;box-shadow:0 3px 12px rgba(7,26,43,.05)}
[data-testid="stMetricLabel"]{color:var(--text-color);font-weight:600}[data-testid="stMetricValue"]{color:var(--text-color);font-weight:750}
div[data-testid="stPlotlyChart"]{background:var(--secondary-background-color);border:1px solid rgba(128,128,128,.25);border-radius:14px;padding:.35rem;box-shadow:0 3px 12px rgba(7,26,43,.04)}
[data-testid="stDataFrame"]{border:1px solid rgba(128,128,128,.25);border-radius:12px;overflow:hidden}
.brandbar{display:flex;align-items:center;justify-content:space-between;gap:1rem;background:linear-gradient(115deg,#071A2B 0%,#0C3254 70%,#0B65D8 100%);color:white;padding:1.35rem 1.5rem;border-radius:18px;margin-bottom:1rem;box-shadow:0 10px 30px rgba(7,26,43,.18)}
.brand-left{display:flex;align-items:center;gap:1rem}.brand-logo{width:54px;height:54px;border-radius:15px;background:#20B8CD;display:grid;place-items:center;color:#071A2B;font-size:25px;font-weight:900;box-shadow:inset 0 -4px 0 rgba(0,0,0,.12)}
.brand-title{font-size:1.55rem;font-weight:760;line-height:1.15}.brand-subtitle{color:#B9C9D8;font-size:.86rem;margin-top:.25rem}
.live-pill{white-space:nowrap;background:rgba(255,255,255,.11);border:1px solid rgba(255,255,255,.2);border-radius:999px;padding:.5rem .75rem;font-size:.78rem}
.live-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#32D583;margin-right:.4rem;box-shadow:0 0 0 4px rgba(50,213,131,.15)}
.insight{background:var(--secondary-background-color);border-left:4px solid #20B8CD;color:var(--text-color);border-radius:10px;padding:.85rem 1rem;margin:.35rem 0 1rem}
.kpi-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:.75rem;margin:.25rem 0 1rem}.kpi-card{background:var(--secondary-background-color);border:1px solid rgba(128,128,128,.25);border-radius:14px;padding:1rem;box-shadow:0 3px 12px rgba(7,26,43,.05);min-width:0}.kpi-label{color:var(--text-color);opacity:.7;font-size:.78rem;font-weight:650;white-space:nowrap}.kpi-value{color:var(--text-color);font-size:1.52rem;font-weight:780;line-height:1.25;margin:.28rem 0;white-space:nowrap}.kpi-note{color:var(--text-color);opacity:.58;font-size:.68rem}.kpi-card:nth-child(2){border-top:3px solid #18A875}.kpi-card:nth-child(3){border-top:3px solid #F5A524}.kpi-card:nth-child(4){border-top:3px solid #E5484D}
.section-title{color:var(--text-color);font-size:1.05rem;font-weight:720;margin:.5rem 0}.source-note{color:#AFC1D0;font-size:.75rem;line-height:1.45;padding-top:1rem}
.stTabs [data-baseweb="tab-list"]{gap:.4rem}.stTabs [data-baseweb="tab"]{background:var(--secondary-background-color);border-radius:9px;padding:.55rem 1rem;color:var(--text-color)!important;opacity:.75}.stTabs [aria-selected="true"]{color:#20B8CD!important;font-weight:700;opacity:1}
@media(prefers-color-scheme:light){
  .stApp{background:linear-gradient(145deg,#F2F6FA 0%,#FAFCFD 52%,#EEF5FA 100%)}
  .block-container{background:transparent}
  .insight{background:linear-gradient(90deg,#E4F6F9 0%,#F0F9FB 100%);border:1px solid #CDEAF0;border-left:4px solid #20B8CD;box-shadow:0 4px 14px rgba(25,77,103,.05)}
  .kpi-card{background:#FFFFFF;border-color:#D8E1E9;box-shadow:0 7px 20px rgba(19,52,75,.08)}
  .kpi-card:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(19,52,75,.12);transition:.18s ease}
  div[data-testid="stPlotlyChart"]{background:#FFFFFF;border-color:#D8E1E9;box-shadow:0 7px 22px rgba(19,52,75,.07)}
  .stTabs [data-baseweb="tab"]{background:#F7FAFC;border:1px solid #E1E8EF;color:#344054!important}
  .stTabs [aria-selected="true"]{background:#E8F7FA;color:#087F8C!important;border-color:#BFE8ED}
  [data-testid="stDataFrame"]{background:#FFFFFF;border-color:#D8E1E9;box-shadow:0 6px 18px rgba(19,52,75,.06)}
}
@media(max-width:1100px){.kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:700px){.brandbar{align-items:flex-start}.live-pill{display:none}.kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner="Loading operational data…")
def get_data() -> pd.DataFrame:
    return load_journeys()


def polish_chart(figure, height=365):
    figure.update_layout(height=height, margin=dict(l=20, r=20, t=58, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font=dict(family="Arial, sans-serif", size=12), title=dict(font=dict(size=16)),
                         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                         hoverlabel=dict(bgcolor=NAVY, font_color="white"))
    figure.update_xaxes(showgrid=False, linecolor="rgba(128,128,128,.3)")
    figure.update_yaxes(gridcolor="rgba(128,128,128,.22)", zeroline=False)
    return figure


try:
    journeys = get_data()
except Exception as exc:
    st.error(f"The journey dataset could not be loaded: {exc}")
    st.stop()

st.markdown(f"""
<div class="brandbar"><div class="brand-left"><div class="brand-logo">NX</div><div>
<div class="brand-title">Operations Control</div><div class="brand-subtitle">Network performance & journey reliability</div>
</div></div><div class="live-pill"><span class="live-dot"></span>Service monitor · refreshed {datetime.now():%H:%M}</div></div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🚌 Network filters")
    st.caption("Refine the operational view")
    min_date, max_date = min(journeys["journey_date"]), max(journeys["journey_date"])
    selected_dates = st.date_input("Operating period", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    routes = st.multiselect("Routes", sorted(journeys["route_number"].astype(str).unique()), placeholder="All routes")
    depots = st.multiselect("Depots", sorted(journeys["depot"].unique()), placeholder="All depots")
    vehicles = st.multiselect("Vehicle type", sorted(journeys["vehicle_type"].unique()), placeholder="All vehicles")
    st.markdown("---")
    st.markdown('<div class="source-note"><b>DATA SOURCE</b><br>Synthetic operations dataset<br>Refresh interval: 5 minutes</div>', unsafe_allow_html=True)

filtered = journeys.copy()
if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    filtered = filtered[filtered["journey_date"].between(selected_dates[0], selected_dates[1])]
if routes: filtered = filtered[filtered["route_number"].astype(str).isin(routes)]
if depots: filtered = filtered[filtered["depot"].isin(depots)]
if vehicles: filtered = filtered[filtered["vehicle_type"].isin(vehicles)]

st.markdown(f'<div class="insight"><b>Operational insight</b> &nbsp; {build_insight(filtered)}</div>', unsafe_allow_html=True)
kpis = calculate_kpis(filtered)
values = [("Total journeys", f"{kpis.total_journeys:,}", "Selected period"), ("On time", f"{kpis.on_time_pct:.1f}%", "Reliability"),
          ("Delayed", f"{kpis.delayed_pct:.1f}%", "Attention"), ("Cancelled", f"{kpis.cancelled_pct:.1f}%", "Service loss"),
          ("Average delay", f"{kpis.average_delay:.1f} min", "All journeys"), ("Passengers", f"{kpis.total_passengers:,}", "Estimated volume")]
cards_html = "".join(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>' for label, value, note in values)
st.markdown(f'<div class="kpi-grid">{cards_html}</div>', unsafe_allow_html=True)

if filtered.empty:
    st.warning("No journeys match the selected filters. Adjust the operating period or network filters.")
    st.stop()

overview, network, exceptions = st.tabs(["Overview", "Network performance", "Service exceptions"])
with overview:
    left, right = st.columns([1.55, 1])
    daily = daily_performance(filtered)
    trend = px.line(daily, x="journey_date", y="average_delay", markers=True, title="Average delay trend",
                    labels={"average_delay":"Average delay (min)","journey_date":"Operating date"}, color_discrete_sequence=[BLUE])
    trend.update_traces(line=dict(width=3), marker=dict(size=6))
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
    depot_chart = px.bar(depot, x="depot", y="on_time_pct", color="average_delay", text_auto=".1f", title="Depot reliability",
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
