from datetime import date

import pandas as pd

from analytics import build_insight, calculate_kpis, depot_performance


def sample_frame():
    return pd.DataFrame([
        {"journey_id": "1", "route_number": "51", "depot": "A", "journey_date": date(2026, 9, 1), "journey_status": "Delayed", "delay_minutes": 12, "passenger_count": 20},
        {"journey_id": "2", "route_number": "50", "depot": "A", "journey_date": date(2026, 9, 1), "journey_status": "On Time", "delay_minutes": 0, "passenger_count": 10},
        {"journey_id": "3", "route_number": "51", "depot": "B", "journey_date": date(2026, 9, 1), "journey_status": "Cancelled", "delay_minutes": 0, "passenger_count": 0},
        {"journey_id": "4", "route_number": "50", "depot": "B", "journey_date": date(2026, 8, 31), "journey_status": "Delayed", "delay_minutes": 8, "passenger_count": 15},
    ])


def test_kpis_include_all_statuses():
    kpis = calculate_kpis(sample_frame())
    assert kpis.total_journeys == 4
    assert (kpis.on_time_pct, kpis.delayed_pct, kpis.cancelled_pct) == (25.0, 50.0, 25.0)
    assert kpis.average_delay == 5.0
    assert kpis.total_passengers == 45


def test_insight_uses_latest_visible_date():
    assert build_insight(sample_frame()) == "Route 51 has the worst average delay on 01 Sep 2026 at 6.0 minutes."


def test_depot_on_time_rate_is_calculated_per_depot():
    depot = depot_performance(sample_frame()).set_index("depot")
    assert depot.loc["A", "on_time_pct"] == 50.0
    assert depot.loc["B", "on_time_pct"] == 0.0


def test_empty_kpis_and_insight():
    empty = sample_frame().iloc[0:0]
    assert calculate_kpis(empty).total_journeys == 0
    assert build_insight(empty) == "No journeys match the selected filters."
