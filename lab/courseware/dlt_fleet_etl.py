# Databricks notebook source
# MAGIC %md
# MAGIC # Aircraft Fleet Digital Twin — DLT Pipeline
# MAGIC
# MAGIC **Medallion Architecture ETL** ingesting raw CSV sensor data from aircraft digital twins
# MAGIC into production-ready Delta tables for Genie Agent analytics and Neo4j graph integration.
# MAGIC
# MAGIC | Layer | Tables | Purpose |
# MAGIC |-------|--------|---------|
# MAGIC | **Bronze** | Raw CSV ingestion (11 node tables, 12 relationship tables) | Schema-on-read, preserve source fidelity |
# MAGIC | **Silver** | Cleaned + typed entities (aircraft, systems, sensors, readings, flights, maintenance) | Validated, deduplicated, proper types |
# MAGIC | **Gold** | Analytics-ready views (fleet_readiness, sensor_health, maintenance_summary) | Genie/BI/Agent consumption layer |
# MAGIC
# MAGIC Bronze and silver publish to the pipeline default schema (`aircraft_pipeline`).
# MAGIC Only the 8 gold tables are published into the participant-facing schema (`aircraft`).

# COMMAND ----------

import os

import dlt
from pyspark.sql.functions import (
    col, to_timestamp, trim, upper, when, lit, count, avg, max as spark_max,
    min as spark_min, sum as spark_sum, datediff, current_timestamp, expr,
    concat, round as spark_round, regexp_replace
)
from pyspark.sql.types import DoubleType, IntegerType

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _setting(key: str, default: str) -> str:
    """Resolve a workshop setting from pipeline configuration, then env vars, then default.

    workshop_data_setup.py reads the same keys from the environment and forwards
    them into the pipeline configuration, so an override cannot desync the two.
    """
    try:
        value = spark.conf.get(key)
    except Exception:
        value = None
    return value or os.getenv(key, default)


CATALOG = _setting("WORKSHOP_CATALOG", "databricks-neo4j-workshop")
VOLUME_SCHEMA = _setting("WORKSHOP_VOLUME_SCHEMA", "aircraft")
VOLUME_NAME = _setting("WORKSHOP_VOLUME_NAME", "raw_data")
VOLUME_PATH = f"/Volumes/{CATALOG}/{VOLUME_SCHEMA}/{VOLUME_NAME}"

# Bronze + silver land in the pipeline default schema. Only gold is published into
# the participant-facing schema, so Catalog and the Genie Agent show 8 tables
# instead of 40. The schema-qualified name resolves against the pipeline's
# default catalog.
GOLD_SCHEMA = _setting("WORKSHOP_LAKEHOUSE_SCHEMA", "aircraft")

# Enable column mapping for Neo4j CSV headers with special chars like :ID(Aircraft)
BRONZE_PROPS = {"delta.columnMapping.mode": "name"}

# ---------------------------------------------------------------------------
# BRONZE LAYER — Raw CSV ingestion, no transforms
# ---------------------------------------------------------------------------

# -- Node tables --

@dlt.table(
    name="bronze_aircraft",
    comment="Raw aircraft fleet data from CSV export",
    table_properties=BRONZE_PROPS
)
def bronze_aircraft():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_aircraft.csv")
    )

@dlt.table(
    name="bronze_systems",
    comment="Raw aircraft system data (engines, avionics, hydraulics)",
    table_properties=BRONZE_PROPS
)
def bronze_systems():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_systems.csv")
    )

@dlt.table(
    name="bronze_sensors",
    comment="Raw sensor metadata from aircraft systems",
    table_properties=BRONZE_PROPS
)
def bronze_sensors():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_sensors.csv")
    )

@dlt.table(
    name="bronze_readings",
    comment="Raw sensor telemetry readings (155,520 rows)",
    table_properties=BRONZE_PROPS
)
def bronze_readings():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_readings.csv")
    )

@dlt.table(
    name="bronze_flights",
    comment="Raw flight operations data",
    table_properties=BRONZE_PROPS
)
def bronze_flights():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_flights.csv")
    )

@dlt.table(
    name="bronze_maintenance",
    comment="Raw maintenance event records",
    table_properties=BRONZE_PROPS
)
def bronze_maintenance():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_maintenance.csv")
    )

@dlt.table(
    name="bronze_components",
    comment="Raw component data for aircraft systems",
    table_properties=BRONZE_PROPS
)
def bronze_components():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_components.csv")
    )

@dlt.table(
    name="bronze_airports",
    comment="Raw airport reference data",
    table_properties=BRONZE_PROPS
)
def bronze_airports():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_airports.csv")
    )

@dlt.table(
    name="bronze_delays",
    comment="Raw flight delay records",
    table_properties=BRONZE_PROPS
)
def bronze_delays():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_delays.csv")
    )

@dlt.table(
    name="bronze_removals",
    comment="Raw component removal events",
    table_properties=BRONZE_PROPS
)
def bronze_removals():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_removals.csv")
    )

@dlt.table(
    name="bronze_operating_limits",
    comment="Raw documented takeoff operating limits, transcribed from the maintenance manuals",
    table_properties=BRONZE_PROPS
)
def bronze_operating_limits():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(f"{VOLUME_PATH}/nodes_operating_limits.csv")
    )

# -- Relationship tables (useful for joins without Neo4j) --

@dlt.table(name="bronze_rel_aircraft_system", comment="Aircraft → System relationships", table_properties=BRONZE_PROPS)
def bronze_rel_aircraft_system():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_aircraft_system.csv")

@dlt.table(name="bronze_rel_system_sensor", comment="System → Sensor relationships", table_properties=BRONZE_PROPS)
def bronze_rel_system_sensor():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_system_sensor.csv")

@dlt.table(name="bronze_rel_system_component", comment="System → Component relationships", table_properties=BRONZE_PROPS)
def bronze_rel_system_component():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_system_component.csv")

@dlt.table(name="bronze_rel_aircraft_flight", comment="Aircraft → Flight relationships", table_properties=BRONZE_PROPS)
def bronze_rel_aircraft_flight():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_aircraft_flight.csv")

@dlt.table(name="bronze_rel_flight_departure", comment="Flight → Departure Airport", table_properties=BRONZE_PROPS)
def bronze_rel_flight_departure():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_flight_departure.csv")

@dlt.table(name="bronze_rel_flight_arrival", comment="Flight → Arrival Airport", table_properties=BRONZE_PROPS)
def bronze_rel_flight_arrival():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_flight_arrival.csv")

@dlt.table(name="bronze_rel_flight_delay", comment="Flight → Delay relationships", table_properties=BRONZE_PROPS)
def bronze_rel_flight_delay():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_flight_delay.csv")

@dlt.table(name="bronze_rel_component_event", comment="Component → Maintenance Event", table_properties=BRONZE_PROPS)
def bronze_rel_component_event():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_component_event.csv")

@dlt.table(name="bronze_rel_event_aircraft", comment="Maintenance Event → Aircraft", table_properties=BRONZE_PROPS)
def bronze_rel_event_aircraft():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_event_aircraft.csv")

@dlt.table(name="bronze_rel_event_system", comment="Maintenance Event → System", table_properties=BRONZE_PROPS)
def bronze_rel_event_system():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_event_system.csv")

@dlt.table(name="bronze_rel_aircraft_removal", comment="Aircraft → Removal Event", table_properties=BRONZE_PROPS)
def bronze_rel_aircraft_removal():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_aircraft_removal.csv")

@dlt.table(name="bronze_rel_component_removal", comment="Component → Removal Event", table_properties=BRONZE_PROPS)
def bronze_rel_component_removal():
    return spark.read.format("csv").option("header", "true").load(f"{VOLUME_PATH}/rels_component_removal.csv")

# ---------------------------------------------------------------------------
# SILVER LAYER — Cleaned, typed, validated
# ---------------------------------------------------------------------------

@dlt.table(
    name="silver_aircraft",
    comment="Fleet of aircraft with tail numbers, models, and operators"
)
@dlt.expect_or_drop("valid_tail_number", "tail_number IS NOT NULL")
@dlt.expect_or_drop("valid_aircraft_id", "aircraft_id IS NOT NULL")
def silver_aircraft():
    return (
        dlt.read("bronze_aircraft")
        .selectExpr(
            "`:ID(Aircraft)` as aircraft_id",
            "tail_number",
            "icao24",
            "model",
            "manufacturer",
            "operator"
        )
        .withColumn("tail_number", upper(trim(col("tail_number"))))
        .withColumn("model", trim(col("model")))
        .withColumn("manufacturer", trim(col("manufacturer")))
        .withColumn("operator", trim(col("operator")))
        .dropDuplicates(["aircraft_id"])
    )

@dlt.table(
    name="silver_systems",
    comment="Aircraft systems including engines, avionics, and hydraulics"
)
@dlt.expect_or_drop("valid_system_id", "system_id IS NOT NULL")
def silver_systems():
    return (
        dlt.read("bronze_systems")
        .selectExpr(
            "`:ID(System)` as system_id",
            "aircraft_id",
            "type as system_type",
            "name as system_name"
        )
        .withColumn("system_type", trim(col("system_type")))
        .withColumn("system_name", trim(col("system_name")))
        .dropDuplicates(["system_id"])
    )

@dlt.table(
    name="silver_sensors",
    comment="Sensors installed on aircraft systems measuring EGT, vibration, N1 speed, fuel flow. The unit column keeps the source's degree sign (e.g. °C) — Lab 2 loads this table into Neo4j, and the graph's value should be what the manuals print, matching OperatingLimit.unit. gold_sensors strips it to ASCII for Genie."
)
@dlt.expect_or_drop("valid_sensor_id", "sensor_id IS NOT NULL")
def silver_sensors():
    return (
        dlt.read("bronze_sensors")
        .selectExpr(
            "`:ID(Sensor)` as sensor_id",
            "system_id",
            "type as sensor_type",
            "name as sensor_name",
            "unit"
        )
        .withColumn("sensor_type", trim(col("sensor_type")))
        .dropDuplicates(["sensor_id"])
    )

@dlt.table(
    name="silver_sensor_readings",
    comment="Sensor readings at 4-hour intervals over 90 days (2024-07-01 to 2024-09-28). 155,520 time-series records (288 sensors x 540 readings).",
    partition_cols=["sensor_id"]
)
@dlt.expect_or_drop("valid_reading_id", "reading_id IS NOT NULL")
@dlt.expect_or_drop("valid_timestamp", "timestamp IS NOT NULL")
@dlt.expect_or_drop("valid_value", "value IS NOT NULL")
def silver_sensor_readings():
    return (
        dlt.read("bronze_readings")
        .select(
            col("reading_id"),
            col("sensor_id"),
            to_timestamp(col("ts")).alias("timestamp"),
            col("value").cast(DoubleType()).alias("value")
        )
        .dropDuplicates(["reading_id"])
    )

@dlt.table(
    name="silver_flights",
    comment="Flight operations with schedule, origin, destination, and delay information"
)
@dlt.expect_or_drop("valid_flight_id", "flight_id IS NOT NULL")
def silver_flights():
    dep = dlt.read("bronze_rel_flight_departure").selectExpr("`:START_ID(Flight)` as flight_id", "`:END_ID(Airport)` as origin_airport")
    arr = dlt.read("bronze_rel_flight_arrival").selectExpr("`:START_ID(Flight)` as flight_id", "`:END_ID(Airport)` as destination_airport")

    return (
        dlt.read("bronze_flights")
        .selectExpr(
            "`:ID(Flight)` as flight_id",
            "flight_number",
            "aircraft_id",
            "operator",
            "origin",
            "destination",
            "to_timestamp(scheduled_departure) as scheduled_departure",
            "to_timestamp(scheduled_arrival) as scheduled_arrival"
        )
        .join(dep, "flight_id", "left")
        .join(arr, "flight_id", "left")
        .dropDuplicates(["flight_id"])
    )

@dlt.table(
    name="silver_maintenance_events",
    comment="Maintenance events with fault details, severity, and corrective actions"
)
@dlt.expect_or_drop("valid_event_id", "event_id IS NOT NULL")
def silver_maintenance_events():
    return (
        dlt.read("bronze_maintenance")
        .selectExpr(
            "`:ID(MaintenanceEvent)` as event_id",
            "component_id",
            "system_id",
            "aircraft_id",
            "fault",
            "severity",
            "to_timestamp(reported_at) as reported_at",
            "corrective_action"
        )
        .withColumn("severity", upper(trim(col("severity"))))
        .dropDuplicates(["event_id"])
    )

@dlt.table(
    name="silver_components",
    comment="Aircraft components (fans, turbines, pumps, etc.) within systems"
)
def silver_components():
    return (
        dlt.read("bronze_components")
        .selectExpr(
            "`:ID(Component)` as component_id",
            "system_id",
            "type as component_type",
            "name as component_name"
        )
        .dropDuplicates(["component_id"])
    )

@dlt.table(
    name="silver_airports",
    comment="Airport reference data with coordinates"
)
def silver_airports():
    return (
        dlt.read("bronze_airports")
        .selectExpr(
            "`:ID(Airport)` as airport_id",
            "name as airport_name",
            "city",
            "country",
            "iata",
            "icao",
            "CAST(lat AS DOUBLE) as latitude",
            "CAST(lon AS DOUBLE) as longitude"
        )
    )

@dlt.table(
    name="silver_delays",
    comment="Flight delay records with cause and duration"
)
def silver_delays():
    # nodes_delays.csv has no flight_id — derive it from the Flight → Delay relationship.
    flight_delay = dlt.read("bronze_rel_flight_delay").selectExpr("`:START_ID(Flight)` as flight_id", "`:END_ID(Delay)` as delay_id")

    return (
        dlt.read("bronze_delays")
        .selectExpr(
            "`:ID(Delay)` as delay_id",
            "cause as delay_cause",
            "CAST(minutes AS INT) as delay_minutes"
        )
        .join(flight_delay, "delay_id", "left")
    )

@dlt.table(
    name="silver_removals",
    comment="Component removal events with maintenance details"
)
def silver_removals():
    return (
        dlt.read("bronze_removals")
        .selectExpr(
            "`:ID(RemovalEvent)` as removal_id",
            "RMV_TRK_NO as tracking_number",
            "RMV_REA_TX as removal_reason",
            "component_id",
            "aircraft_id",
            "to_timestamp(removal_date) as removal_date",
            "to_timestamp(installation_date) as installation_date",
            "work_order_number",
            "technician_id",
            "part_number",
            "serial_number",
            "CAST(time_since_install AS DOUBLE) as hours_since_install",
            "CAST(flight_hours_at_removal AS DOUBLE) as flight_hours_at_removal",
            "CAST(flight_cycles_at_removal AS INT) as flight_cycles_at_removal",
            "CAST(replacement_required AS BOOLEAN) as replacement_required",
            "CAST(shop_visit_required AS BOOLEAN) as shop_visit_required",
            "warranty_status",
            "removal_priority",
            "CAST(cost_estimate AS DOUBLE) as cost_estimate"
        )
    )

@dlt.table(
    name="silver_operating_limits",
    comment="Documented takeoff operating limits: 20 rows, four parameters across five aircraft models. Reference data for Lab 2's Neo4j graph, not gold — no BI consumer reads it, and it never joins to sensor_readings on unit, so it keeps the manuals' own degree sign, same as silver_sensors.unit."
)
@dlt.expect_or_drop("valid_limit_id", "limit_id IS NOT NULL")
def silver_operating_limits():
    return (
        dlt.read("bronze_operating_limits")
        .selectExpr(
            "`:ID(OperatingLimit)` as limit_id",
            "name",
            "parameterName",
            "unit",
            "regime",
            "CAST(minValue AS DOUBLE) as minValue",
            "CAST(maxValue AS DOUBLE) as maxValue",
            "aircraftType"
        )
        .dropDuplicates(["limit_id"])
    )

# ---------------------------------------------------------------------------
# GOLD LAYER — Analytics-ready tables for Genie / BI / Agents
#
# Gold tables are schema-qualified into GOLD_SCHEMA so they land in the
# participant-facing schema while bronze/silver stay in the pipeline schema.
# ---------------------------------------------------------------------------

@dlt.table(
    name=f"{GOLD_SCHEMA}.aircraft",
    comment="Fleet of aircraft with tail numbers, models, and operators. Join key for all fleet queries."
)
def gold_aircraft():
    """Production aircraft dimension table for Genie consumption."""
    return dlt.read("silver_aircraft")

@dlt.table(
    name=f"{GOLD_SCHEMA}.systems",
    comment="Aircraft systems including engines, avionics, and hydraulics. Each system belongs to one aircraft."
)
def gold_systems():
    """Production systems dimension with aircraft context."""
    aircraft = dlt.read("silver_aircraft").select("aircraft_id", "tail_number")
    return (
        dlt.read("silver_systems")
        .withColumnRenamed("system_type", "type")
        .withColumnRenamed("system_name", "name")
        .join(aircraft, "aircraft_id", "left")
    )

@dlt.table(
    name=f"{GOLD_SCHEMA}.sensors",
    comment="Sensors installed on aircraft systems. Types: EGT, Vibration, N1Speed, FuelFlow."
)
def gold_sensors():
    """Production sensor dimension with system + aircraft context.

    Strips the degree sign from ``unit`` (``°C`` -> ``C``). Genie generating SQL
    against this table does not reproduce that character: it writes
    ``unit = 'C'`` or ``LOWER(unit) = 'c'``, matches zero rows, and the agent
    above it then reports flatly that no engine shows an abnormal EGT. That
    answer is false. The same question with no unit filter finds over 4,980
    abnormal readings on one engine of N10000 alone. Stripping it here fixes
    that once, for Genie, without touching ``silver_sensors.unit``, which Lab 2
    loads into Neo4j and needs to keep the manuals' own spelling.
    """
    systems = dlt.read("silver_systems").select("system_id", "aircraft_id", "system_type", "system_name")
    aircraft = dlt.read("silver_aircraft").select("aircraft_id", "tail_number")
    return (
        dlt.read("silver_sensors")
        .withColumnRenamed("sensor_type", "type")
        .withColumnRenamed("sensor_name", "name")
        .withColumn("unit", trim(regexp_replace(col("unit"), "°", "")))
        .join(systems, "system_id", "left")
        .join(aircraft, "aircraft_id", "left")
    )

@dlt.table(
    name=f"{GOLD_SCHEMA}.sensor_readings",
    comment="Sensor readings at 4-hour intervals over 90 days (2024-07-01 to 2024-09-28), 155,520 rows across 288 sensors. Each sensor has 540 readings spaced 6 per day; there is no hourly granularity, so per-hour buckets are not meaningful. Partitioned by sensor_id for efficient time-series queries.",
    partition_cols=["sensor_id"]
)
def gold_sensor_readings():
    """Production sensor readings fact table."""
    return dlt.read("silver_sensor_readings")

@dlt.table(
    name=f"{GOLD_SCHEMA}.flights",
    comment="Flight operations with aircraft, route, schedule, and total delay minutes."
)
def gold_flights():
    """Enriched flight fact table with delay totals."""
    delays_agg = (
        dlt.read("silver_delays")
        .groupBy("flight_id")
        .agg(
            spark_sum("delay_minutes").alias("total_delay_minutes"),
            count("*").alias("delay_count")
        )
    )
    aircraft = dlt.read("silver_aircraft").select("aircraft_id", "tail_number")

    return (
        dlt.read("silver_flights")
        .join(delays_agg, "flight_id", "left")
        .join(aircraft, "aircraft_id", "left")
        .withColumn("total_delay_minutes", col("total_delay_minutes").cast(IntegerType()))
        .withColumn("delay_count", col("delay_count").cast(IntegerType()))
        .fillna({"total_delay_minutes": 0, "delay_count": 0})
    )

@dlt.table(
    name=f"{GOLD_SCHEMA}.maintenance_events",
    comment="Maintenance events enriched with aircraft tail number and system details. Severity: CRITICAL (141 events), MAJOR (77), MINOR (68)."
)
def gold_maintenance():
    """Maintenance events with full aircraft + system context."""
    aircraft = dlt.read("silver_aircraft").select("aircraft_id", "tail_number")
    systems = dlt.read("silver_systems").select("system_id", "system_type", "system_name")
    return (
        dlt.read("silver_maintenance_events")
        .join(aircraft, "aircraft_id", "left")
        .join(systems, "system_id", "left")
    )

@dlt.table(
    name=f"{GOLD_SCHEMA}.fleet_readiness",
    comment="Per-aircraft fleet readiness summary. Includes system count, sensor count, open critical maintenance, recent flights, and readiness status. Across the 36-aircraft fleet: 6 NOT MISSION READY, 12 DEGRADED, 18 MISSION READY."
)
def gold_fleet_readiness():
    """Mission-oriented fleet readiness view for command dashboards."""
    aircraft = dlt.read("silver_aircraft")

    sys_counts = (
        dlt.read("silver_systems")
        .groupBy("aircraft_id")
        .agg(count("*").alias("system_count"))
    )

    sensor_counts = (
        dlt.read("silver_sensors")
        .join(dlt.read("silver_systems").select("system_id", "aircraft_id"), "system_id")
        .groupBy("aircraft_id")
        .agg(count("*").alias("sensor_count"))
    )

    critical_mx = (
        dlt.read("silver_maintenance_events")
        .filter(col("severity") == "CRITICAL")
        .groupBy("aircraft_id")
        .agg(count("*").alias("critical_events"))
    )

    all_mx = (
        dlt.read("silver_maintenance_events")
        .groupBy("aircraft_id")
        .agg(
            count("*").alias("total_maintenance_events"),
            spark_max("reported_at").alias("last_maintenance_date")
        )
    )

    flight_stats = (
        dlt.read("silver_flights")
        .groupBy("aircraft_id")
        .agg(
            count("*").alias("total_flights"),
            spark_max("scheduled_departure").alias("last_flight_date")
        )
    )

    removal_stats = (
        dlt.read("silver_removals")
        .groupBy("aircraft_id")
        .agg(
            count("*").alias("total_removals"),
            spark_sum(when(col("replacement_required"), 1).otherwise(0)).alias("replacements_needed")
        )
    )

    return (
        aircraft
        .join(sys_counts, "aircraft_id", "left")
        .join(sensor_counts, "aircraft_id", "left")
        .join(critical_mx, "aircraft_id", "left")
        .join(all_mx, "aircraft_id", "left")
        .join(flight_stats, "aircraft_id", "left")
        .join(removal_stats, "aircraft_id", "left")
        .fillna({
            "system_count": 0, "sensor_count": 0,
            "critical_events": 0, "total_maintenance_events": 0,
            "total_flights": 0, "total_removals": 0, "replacements_needed": 0
        })
        # Thresholds tuned against the current dataset (286 maintenance events,
        # 141 of them CRITICAL, spread over 16 of the 36 aircraft). A simple
        # "any critical event" rule would mark 16 aircraft NOT MISSION READY and
        # never produce a DEGRADED aircraft.
        .withColumn("readiness_status",
            when(col("critical_events") >= 10, "NOT MISSION READY")
            .when(
                (col("critical_events") > 0)
                | (col("total_maintenance_events") >= 5)
                | (col("total_removals") >= 3),
                "DEGRADED"
            )
            .otherwise("MISSION READY")
        )
    )

@dlt.table(
    name=f"{GOLD_SCHEMA}.sensor_health",
    comment="Per-sensor descriptive statistics over the full 90-day window: reading count, average, min, max, standard deviation, 95th percentile, and the timestamp of the last reading, with system and tail number attached. Carries no health verdict. Whether a value is out of limits depends on the aircraft type and the flight regime, and no gold table joins readings to operating limits on that basis."
)
def gold_sensor_health():
    """Per-sensor descriptive statistics.

    Deliberately carries no ``health_status`` column. The rule that used to set
    one compared each sensor's p95 against its own ``avg + k*stddev``, which
    measures the shape of a distribution rather than the condition of a sensor.
    For anything near normal the p95 sits at about ``avg + 1.645*stddev``, so
    the ANOMALY branch at 2 sigma could never fire and the WARNING branch at 1
    sigma fired for almost everything: 284 WARNING, 4 NORMAL, 0 ANOMALY across
    all 288 sensors. No constant fixes that, because every sensor has roughly
    the same shape.

    A real verdict needs an outside reference, and the OperatingLimit rows are
    keyed on aircraft type, parameter and flight regime while a reading carries
    no regime. Picking one here would freeze an arbitrary choice into a gold
    table. That comparison belongs in the graph, which is where the limits live.
    """
    # unit stripped to ASCII here for the same reason gold_sensors strips it:
    # Genie writes `unit = 'C'`, not `unit = '°C'`. silver_sensors.unit keeps
    # the degree sign for Lab 2's Neo4j load, so every gold consumer strips it
    # itself rather than the other way around.
    sensors = dlt.read("silver_sensors").withColumn("unit", trim(regexp_replace(col("unit"), "°", "")))
    systems = dlt.read("silver_systems").select("system_id", "aircraft_id")
    aircraft = dlt.read("silver_aircraft").select("aircraft_id", "tail_number")

    stats = (
        dlt.read("silver_sensor_readings")
        .groupBy("sensor_id")
        .agg(
            count("*").alias("reading_count"),
            spark_round(avg("value"), 2).alias("avg_value"),
            spark_round(spark_min("value"), 2).alias("min_value"),
            spark_round(spark_max("value"), 2).alias("max_value"),
            spark_round(expr("stddev(value)"), 2).alias("stddev_value"),
            spark_max("timestamp").alias("last_reading_at"),
            spark_round(expr("percentile(value, 0.95)"), 2).alias("p95_value")
        )
    )

    return (
        sensors
        .join(stats, "sensor_id", "left")
        .join(systems, "system_id", "left")
        .join(aircraft, "aircraft_id", "left")
    )
