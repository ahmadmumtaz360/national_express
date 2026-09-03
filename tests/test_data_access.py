import data_access


def test_unconfigured_environment_uses_synthetic_fallback(monkeypatch):
    monkeypatch.delenv("LOCAL_DATA_PATH", raising=False)
    monkeypatch.delenv("DATABRICKS_WAREHOUSE_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_TABLE_NAME", raising=False)

    frame = data_access.load_journeys()

    assert len(frame) == 3000
    assert frame["journey_id"].is_unique


def test_partial_databricks_configuration_is_rejected(monkeypatch):
    monkeypatch.delenv("LOCAL_DATA_PATH", raising=False)
    monkeypatch.setenv("DATABRICKS_WAREHOUSE_ID", "warehouse")
    monkeypatch.delenv("DATABRICKS_TABLE_NAME", raising=False)

    try:
        data_access.load_journeys()
    except data_access.DataConfigurationError as exc:
        assert "configured together" in str(exc)
    else:
        raise AssertionError("Expected partial Databricks configuration to fail")
