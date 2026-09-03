# Databricks notebook source
# MAGIC %md
# MAGIC # Generate mock bus journeys
# MAGIC Creates deterministic POC data using the shared application contract. Re-running with the same seed produces the same operational characteristics; dates are relative to the run date.

# COMMAND ----------

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "bus_operations")
dbutils.widgets.text("table", "bus_journeys")
dbutils.widgets.text("row_count", "3000")
dbutils.widgets.text("seed", "20260902")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
table = dbutils.widgets.get("table")
row_count = int(dbutils.widgets.get("row_count"))
seed = int(dbutils.widgets.get("seed"))

import re

identifier = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
if not all(identifier.fullmatch(value) for value in (catalog, schema, table)):
    raise ValueError("Catalog, schema, and table must be simple SQL identifiers")
if not 1000 <= row_count <= 5000:
    raise ValueError("row_count must be between 1,000 and 5,000")

# COMMAND ----------

import random
from datetime import date, datetime, time, timedelta
from pyspark.sql.types import DateType, DoubleType, IntegerType, StringType, StructField, StructType, TimestampType

routes = ["11A", "11C", "16", "45", "50", "51", "74", "87", "97"]
depots = ["Birmingham Central", "Coventry", "Perry Barr", "Walsall", "West Bromwich"]
rng = random.Random(seed)
today = date.today()
route_delay_bias = {route: index * 0.7 for index, route in enumerate(routes)}
rows = []

for index in range(row_count):
    route = rng.choice(routes)
    depot = rng.choice(depots)
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
    rows.append((
        f"JNY-{journey_date:%Y%m%d}-{index + 1:05d}", f"BUS-{rng.randint(1001, 1290)}", route, depot,
        journey_date, scheduled_departure, None if cancelled else scheduled_departure + timedelta(minutes=departure_lag),
        scheduled_arrival, None if cancelled else scheduled_arrival + timedelta(minutes=delay), delay, status,
        0 if cancelled else rng.randint(3, 78), "Electric" if rng.random() < 0.35 else "Diesel", distance,
    ))

journey_schema = StructType([
    StructField("journey_id", StringType(), False), StructField("bus_id", StringType(), False),
    StructField("route_number", StringType(), False), StructField("depot", StringType(), False),
    StructField("journey_date", DateType(), False), StructField("scheduled_departure", TimestampType(), False),
    StructField("actual_departure", TimestampType(), True), StructField("scheduled_arrival", TimestampType(), False),
    StructField("actual_arrival", TimestampType(), True), StructField("delay_minutes", IntegerType(), False),
    StructField("journey_status", StringType(), False), StructField("passenger_count", IntegerType(), False),
    StructField("vehicle_type", StringType(), False), StructField("distance_miles", DoubleType(), False),
])
journeys = spark.createDataFrame(rows, journey_schema)

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
full_table = f"`{catalog}`.`{schema}`.`{table}`"
(journeys.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(full_table))

# COMMAND ----------

written = spark.table(full_table)
assert written.count() == row_count
assert written.select("journey_id").distinct().count() == row_count
assert written.filter("journey_status NOT IN ('On Time', 'Delayed', 'Cancelled')").count() == 0
assert written.filter("journey_status = 'Cancelled' AND (actual_departure IS NOT NULL OR actual_arrival IS NOT NULL OR passenger_count != 0)").count() == 0
display(written.groupBy("journey_status").count().orderBy("journey_status"))
print(f"Created {row_count:,} journeys in {catalog}.{schema}.{table}")
