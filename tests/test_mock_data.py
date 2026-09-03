from mock_data import generate_mock_journeys


def test_generator_contract_and_business_rules():
    frame = generate_mock_journeys(1000, seed=7)
    assert len(frame) == 1000
    assert frame["journey_id"].is_unique
    assert set(frame["journey_status"]) <= {"On Time", "Delayed", "Cancelled"}
    assert set(frame["vehicle_type"]) == {"Diesel", "Electric"}
    cancelled = frame[frame["journey_status"] == "Cancelled"]
    assert cancelled["actual_departure"].isna().all()
    assert cancelled["actual_arrival"].isna().all()
    assert cancelled["passenger_count"].eq(0).all()
    assert frame.loc[frame["journey_status"] != "Delayed", "delay_minutes"].eq(0).all()
