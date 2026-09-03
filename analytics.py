"""Pure analytics functions shared by the UI and tests."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Kpis:
    total_journeys: int
    on_time_pct: float
    delayed_pct: float
    cancelled_pct: float
    average_delay: float
    total_passengers: int


def calculate_kpis(frame: pd.DataFrame) -> Kpis:
    total = len(frame)
    if total == 0:
        return Kpis(0, 0.0, 0.0, 0.0, 0.0, 0)
    status = frame["journey_status"]
    return Kpis(
        total, float(status.eq("On Time").mean() * 100),
        float(status.eq("Delayed").mean() * 100), float(status.eq("Cancelled").mean() * 100),
        float(frame["delay_minutes"].mean()), int(frame["passenger_count"].sum()),
    )


def route_performance(frame: pd.DataFrame) -> pd.DataFrame:
    return (frame.groupby("route_number", as_index=False)
            .agg(average_delay=("delay_minutes", "mean"), journeys=("journey_id", "count"))
            .sort_values(["average_delay", "journeys"], ascending=[False, False]))


def depot_performance(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby("depot", as_index=False).agg(
        journeys=("journey_id", "count"), average_delay=("delay_minutes", "mean"),
        delayed=("journey_status", lambda values: values.eq("Delayed").sum()),
        cancelled=("journey_status", lambda values: values.eq("Cancelled").sum()))
    rates = frame.assign(on_time=frame["journey_status"].eq("On Time")).groupby("depot")["on_time"].mean()
    grouped["on_time_pct"] = rates.reindex(grouped["depot"]).to_numpy() * 100
    return grouped.sort_values("average_delay", ascending=False)


def daily_performance(frame: pd.DataFrame) -> pd.DataFrame:
    return (frame.groupby("journey_date", as_index=False)
            .agg(journeys=("journey_id", "count"), average_delay=("delay_minutes", "mean"))
            .sort_values("journey_date"))


def build_insight(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "No journeys match the selected filters."
    latest_date = max(frame["journey_date"])
    worst = route_performance(frame[frame["journey_date"] == latest_date]).iloc[0]
    return (f"Route {worst['route_number']} has the worst average delay on "
            f"{latest_date:%d %b %Y} at {worst['average_delay']:.1f} minutes.")
