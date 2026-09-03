# Bus Operations Monitor

A Databricks App proof of concept for monitoring bus journey performance. It reads a stable journey contract from a Unity Catalog Delta table, provides operational filters and KPIs, and keeps the UI independent from data generation so mock data can later be replaced with real WMCA/National Express data.

## Included

- `notebooks/01_generate_mock_bus_journeys.py` creates 3,000 deterministic synthetic journeys in a managed Delta table.
- `app.py` provides KPIs, filters, charts, a delayed-journey table, and a generated insight.
- `data_access.py` isolates the Databricks read layer.
- `analytics.py` contains framework-independent, tested calculations.
- `scripts/generate_local_data.py` supports development without a workspace.

## Data contract

| Column | Type | Notes |
|---|---|---|
| `journey_id` | string | Stable journey identifier |
| `bus_id` | string | Vehicle/fleet identifier |
| `route_number` | string | Route identifier |
| `depot` | string | Operating depot |
| `journey_date` | date | Local operating date |
| `scheduled_departure` | timestamp | Scheduled local time |
| `actual_departure` | timestamp, nullable | Null when cancelled |
| `scheduled_arrival` | timestamp | Scheduled local time |
| `actual_arrival` | timestamp, nullable | Null when cancelled |
| `delay_minutes` | integer | Arrival delay; zero for on-time/cancelled journeys |
| `journey_status` | string | `On Time`, `Delayed`, or `Cancelled` |
| `passenger_count` | integer | Zero for cancelled journeys |
| `vehicle_type` | string | `Diesel` or `Electric` |
| `distance_miles` | double | Planned route distance |

## Create data in Databricks

1. Open `notebooks/01_generate_mock_bus_journeys.py` as a Databricks notebook and attach Unity Catalog-enabled compute.
2. Set the `catalog`, `schema`, `table`, `row_count`, and `seed` widgets if needed.
3. Run all cells. The default destination is `main.bus_operations.bus_journeys`; the final cell validates it.

The notebook uses an explicit schema and overwrites only the configured table.

## Deploy the app

1. Create a Databricks App from this repository/workspace folder.
2. Add a **SQL warehouse** resource with key `sql-warehouse` and **Can use** permission.
3. Add the generated Unity Catalog table as a **table** resource with key `bus-journeys` and **Select** permission.
4. Deploy. `app.yaml` maps both resources to environment variables; no credentials or workspace IDs are committed.

The app service principal also needs `USE CATALOG` and `USE SCHEMA` on the table's parents. The app reads at most 100,000 rows per refresh. For a much larger real dataset, push filters and aggregation into `data_access.py`.

## Run locally

```powershell
python -m pip install -r requirements-dev.txt
python scripts/generate_local_data.py
$env:LOCAL_DATA_PATH = "data/mock_bus_journeys.csv"
streamlit run app.py
```

Alternatively, configure a Databricks CLI profile and set `DATABRICKS_WAREHOUSE_ID` and `DATABRICKS_TABLE_NAME` before running Streamlit.

## Test

```powershell
python -m pytest
```

## Replace mock data later

Transform the real feed into the contract above—preferably a curated Delta table or compatibility view—then point the app's `bus-journeys` table resource at it. `app.py` and `analytics.py` remain unchanged.
