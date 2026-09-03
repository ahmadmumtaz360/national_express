"""Read the bus journey contract from Databricks or a local development file."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd

TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][\w-]*\.[A-Za-z_][\w-]*\.[A-Za-z_][\w-]*$")
DATE_COLUMNS = ["journey_date"]
TIMESTAMP_COLUMNS = ["scheduled_departure", "actual_departure", "scheduled_arrival", "actual_arrival"]


class DataConfigurationError(RuntimeError):
    """Raised when the app data source has not been configured safely."""


def _normalise_types(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in DATE_COLUMNS:
        result[column] = pd.to_datetime(result[column]).dt.date
    for column in TIMESTAMP_COLUMNS:
        result[column] = pd.to_datetime(result[column])
    return result


def load_journeys() -> pd.DataFrame:
    """Load journeys from a local file, Databricks, or the synthetic POC fallback."""
    local_path = os.getenv("LOCAL_DATA_PATH")
    if local_path:
        path = Path(local_path)
        if not path.is_file():
            raise DataConfigurationError(f"LOCAL_DATA_PATH does not exist: {path}")
        return _normalise_types(pd.read_csv(path))

    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    table_name = os.getenv("DATABRICKS_TABLE_NAME")
    if not warehouse_id and not table_name:
        from mock_data import generate_mock_journeys

        return generate_mock_journeys()
    if not warehouse_id or not table_name:
        raise DataConfigurationError(
            "DATABRICKS_WAREHOUSE_ID and DATABRICKS_TABLE_NAME must be configured together."
        )
    if not TABLE_NAME_PATTERN.fullmatch(table_name):
        raise DataConfigurationError("DATABRICKS_TABLE_NAME must be catalog.schema.table")
    quoted_table_name = ".".join(f"`{part}`" for part in table_name.split("."))

    from databricks import sql
    from databricks.sdk.core import Config

    cfg = Config()
    hostname = cfg.host.removeprefix("https://").removeprefix("http://")
    with sql.connect(
        server_hostname=hostname,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate,
        _use_arrow_native_complex_types=False,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {quoted_table_name} LIMIT 100000")
            frame = cursor.fetchall_arrow().to_pandas()
    return _normalise_types(frame)
