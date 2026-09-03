"""Deterministic synthetic journey generation shared by local tooling and tests."""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

import pandas as pd

ROUTES = ["11A", "11C", "16", "45", "50", "51", "74", "87", "97"]
DEPOTS = ["Birmingham Central", "Coventry", "Perry Barr", "Walsall", "West Bromwich"]


def generate_mock_journeys(row_count: int = 3000, seed: int = 20260902) -> pd.DataFrame:
    if not 1000 <= row_count <= 5000:
        raise ValueError("row_count must be between 1,000 and 5,000")
    rng = random.Random(seed)
    today = date.today()
    route_delay_bias = {route: index * 0.7 for index, route in enumerate(ROUTES)}
    rows = []
    for index in range(row_count):
        route = rng.choice(ROUTES)
        depot = rng.choice(DEPOTS)
        journey_date = today - timedelta(days=rng.randrange(60))
        scheduled_departure = datetime.combine(journey_date, time(5)) + timedelta(minutes=rng.randrange(1080))
        distance = round(rng.uniform(4.0, 28.0), 1)
        scheduled_arrival = scheduled_departure + timedelta(minutes=round(distance * rng.uniform(2.2, 3.5)))
        cancelled = rng.random() < 0.035
        raw_delay = max(0, round(rng.gauss(2.0 + route_delay_bias[route], 5.0)))
        delayed = not cancelled and raw_delay >= 6
        status = "Cancelled" if cancelled else "Delayed" if delayed else "On Time"
        delay = raw_delay if delayed else 0
        departure_lag = max(0, delay + rng.randint(-3, 2))
        rows.append({
            "journey_id": f"JNY-{journey_date:%Y%m%d}-{index + 1:05d}",
            "bus_id": f"BUS-{rng.randint(1001, 1290)}", "route_number": route, "depot": depot,
            "journey_date": journey_date, "scheduled_departure": scheduled_departure,
            "actual_departure": None if cancelled else scheduled_departure + timedelta(minutes=departure_lag),
            "scheduled_arrival": scheduled_arrival,
            "actual_arrival": None if cancelled else scheduled_arrival + timedelta(minutes=delay),
            "delay_minutes": delay, "journey_status": status,
            "passenger_count": 0 if cancelled else rng.randint(3, 78),
            "vehicle_type": "Electric" if rng.random() < 0.35 else "Diesel", "distance_miles": distance,
        })
    return pd.DataFrame(rows)
