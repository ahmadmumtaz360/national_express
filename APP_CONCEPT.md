# Bus Operations Monitor — Concept Guide

## Overview

The Bus Operations Monitor is a proof of concept showing how a bus company could monitor daily operational performance before connecting real National Express or WMCA data.

The application turns journey-level records into management KPIs, operational charts, filters, alerts, and journey details.

## High-level data flow

```text
Synthetic bus journeys
        ↓
Databricks Delta table
        ↓
Bus Operations Monitor
        ↓
KPIs, filters, charts, insights, and delayed-journey details
```

## Why build this application?

Bus operators run thousands of journeys. Operations managers need quick answers to questions such as:

- How many journeys operated?
- How many were on time, delayed, or cancelled?
- Which routes and depots are performing badly?
- How many passengers were affected?
- Are delays improving or getting worse?
- Which individual journeys require investigation?

The dashboard provides one place to answer these questions.

## Synthetic data

Synthetic data is fake but realistic test data. It allows the application to be developed and demonstrated without waiting for access to confidential operational systems.

The included generator creates approximately 3,000 journeys with the following information:

- Journey ID
- Bus ID
- Route number
- Depot
- Journey date
- Scheduled departure
- Actual departure
- Scheduled arrival
- Actual arrival
- Delay minutes
- Journey status: On Time, Delayed, or Cancelled
- Passenger count
- Vehicle type: Diesel or Electric
- Distance in miles

## Headline KPIs

### Total journeys

The number of journeys included in the current filters.

### On time

The percentage of selected journeys classified as on time.

### Delayed

The percentage of selected journeys classified as delayed.

### Cancelled

The percentage of selected journeys that did not operate.

### Average delay

The mean delay in minutes across the selected journeys.

### Total passengers

The estimated number of passengers carried by the selected journeys.

For example, if the dashboard reports **51.8% on time**, approximately 52 of every 100 journeys met the on-time definition.

## Filters

Every KPI, chart, insight, and table can be filtered by:

- Date range
- Route
- Depot
- Vehicle type

For example:

```text
Depot: Coventry
Vehicle type: Electric
Date: Last seven days
```

The dashboard would then show only electric journeys operated by Coventry depot during that period.

## Dashboard views

### Routes requiring attention

Shows the routes with the highest average delay.

### Journeys and delays over time

Shows daily journey volume and average delay. Separate axes keep both measures readable.

### Journey status mix

Compares the proportion of on-time, delayed, and cancelled journeys.

### Performance by depot

Compares on-time performance and average delay across operating depots.

### Fleet mix

Shows the number of journeys operated by diesel and electric vehicles.

### Most delayed journeys

Lists the exact journeys with the largest delays, including their buses, routes, depots, scheduled and actual times, passenger counts, and vehicle types.

The table can also be downloaded as a CSV file for further investigation.

## Operational insight

The insight section converts the data into a short management statement, for example:

> Route 74 has the worst average delay on 3 September at 9.2 minutes.

This helps users identify the most important current issue without manually examining every chart.

## Application architecture

The dashboard UI, analytics logic, and data-access logic are separated.

```text
Data source
    ↓
data_access.py
    ↓
Standard journey data contract
    ↓
analytics.py
    ↓
app.py dashboard
```

The main components are:

- `notebooks/01_generate_mock_bus_journeys.py` creates the synthetic data in Databricks.
- `data_access.py` reads either a Databricks table, a local CSV, or the synthetic preview data.
- `analytics.py` calculates KPIs, route performance, depot performance, daily trends, and insights.
- `app.py` presents the Streamlit interface.
- `app.yaml` defines how the Databricks App starts and receives its resources.

## Replacing mock data with real operational data

The application is designed around a stable journey data contract.

```text
Current POC:
Synthetic generator → journey table → dashboard

Future production:
WMCA/National Express feed → journey table → dashboard
```

Real operational data should be transformed into the same columns and data types expected by the application. Once that compatibility layer exists, the dashboard can use the real source without rebuilding its KPIs, filters, charts, or tables.

A curated Delta table or compatibility view would normally sit between the raw operational feed and the application.

## Current delivery status

The repository includes:

- Synthetic journey-data generator
- Databricks notebook that creates a Delta table
- Streamlit dashboard
- Databricks SQL data-access layer
- Databricks App configuration
- Automated analytics and data-contract tests
- README with setup and deployment instructions
- Streamlit Cloud demonstration version

## Streamlit Cloud versus Databricks deployment

The public demonstration is hosted on Streamlit Cloud. Because that environment does not have Databricks credentials or Databricks App resources, it generates the synthetic data in memory.

For a complete Databricks deployment:

1. Run the supplied notebook in Databricks.
2. Create the Unity Catalog Delta table.
3. Create a Databricks App.
4. Add a SQL warehouse resource with **Can use** permission.
5. Add the journey table as a resource with **Select** permission.
6. Deploy the same application code.

The resulting app would be hosted in Databricks and read data stored in Databricks through the app service principal.

## Future opportunities

Once the POC is connected to real data, it could be extended with:

- Live service disruption monitoring
- Delay and cancellation forecasting
- Route-level reliability targets
- Depot and driver shift analysis
- Passenger-impact estimates
- Electric-vehicle range and charging analysis
- Repeated-delay hotspot detection
- Automated alerts for operations teams
- Historical comparisons and service-level reporting

## Manager-ready explanation

> This POC demonstrates an operational control dashboard that converts journey-level bus data into reliability KPIs, route and depot analysis, delay trends, and actionable alerts. We are currently using synthetic data, but the data layer is designed so it can later be replaced by real WMCA or National Express feeds without rebuilding the dashboard.
