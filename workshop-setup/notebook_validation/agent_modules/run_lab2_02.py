"""Automated version of 02_load_neo4j_full.ipynb for cluster execution.

Converts the interactive notebook into a standalone Python script that can be
uploaded and run on a Databricks cluster via spark_python_task. Loads the
complete Aircraft Digital Twin dataset into Neo4j, then runs verification
queries with PASS/FAIL assertions.

Usage:
    ./upload.sh run_lab2_02.py && ./submit.sh run_lab2_02.py
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Lab 2 Notebook 02: Full Data Load to Neo4j")
    parser.add_argument("--neo4j-uri", required=True, help="Neo4j Aura URI")
    parser.add_argument("--neo4j-username", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo4j-password", required=True, help="Neo4j password")
    parser.add_argument(
        "--data-path",
        default="/Volumes/databricks-neo4j-workshop/aircraft/raw_data",
        help="Unity Catalog Volume path containing CSV data files",
    )
    parser.add_argument("--skip-clear", action="store_true", help="Skip database clearing")
    parser.add_argument("--mcp-endpoint", default="", help="(unused)")
    parser.add_argument("--mcp-api-key", default="", help="(unused)")
    parser.add_argument("--mcp-path", default="", help="(unused)")
    args = parser.parse_args()

    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col

    spark = SparkSession.builder.getOrCreate()

    print("=" * 60)
    print("Lab 2 Notebook 02: Full Data Load to Neo4j")
    print("=" * 60)
    print(f"Neo4j URI:    {args.neo4j_uri}")
    print(f"Data Path:    {args.data_path}")
    print(f"Clear DB:     {not args.skip_clear}")
    print(f"Spark:        {spark.version}")
    print()

    # ── Configure Neo4j Spark Connector ──────────────────────────────────────

    spark.conf.set("neo4j.url", args.neo4j_uri)
    spark.conf.set("neo4j.authentication.basic.username", args.neo4j_username)
    spark.conf.set("neo4j.authentication.basic.password", args.neo4j_password)
    spark.conf.set("neo4j.database", "neo4j")

    BATCH_SIZE = 20000
    results = []  # (name, passed, detail)

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    # ── Helper Functions (from notebook) ─────────────────────────────────────

    def read_csv(filename):
        """Read a CSV file from the Unity Catalog Volume."""
        return spark.read.option("header", "true").csv(f"{args.data_path}/{filename}")

    def write_nodes(df, label, id_column):
        """Write a DataFrame as nodes to Neo4j."""
        (df.write
         .format("org.neo4j.spark.DataSource")
         .mode("Overwrite")
         .option("labels", f":{label}")
         .option("node.keys", id_column)
         .option("batch.size", BATCH_SIZE)
         .save())
        count = df.count()
        print(f"  Wrote {count} {label} nodes")
        return count

    def write_relationships(df, rel_type, source_label, source_key, target_label, target_key):
        """Write relationships to Neo4j using keys strategy."""
        (df.coalesce(1)
         .write
         .format("org.neo4j.spark.DataSource")
         .mode("Overwrite")
         .option("relationship", rel_type)
         .option("relationship.save.strategy", "keys")
         .option("relationship.source.labels", f":{source_label}")
         .option("relationship.source.node.keys", source_key)
         .option("relationship.target.labels", f":{target_label}")
         .option("relationship.target.node.keys", target_key)
         .option("batch.size", BATCH_SIZE)
         .save())
        count = df.count()
        print(f"  Wrote {count} {rel_type} relationships")
        return count

    def run_cypher(query):
        """Execute a Cypher query and return results as DataFrame."""
        return (spark.read
            .format("org.neo4j.spark.DataSource")
            .option("query", query)
            .load())

    def run_script(script):
        """Execute a Cypher script (DDL operations like constraints)."""
        return (spark.read
            .format("org.neo4j.spark.DataSource")
            .option("script", script)
            .option("query", "RETURN 1 AS done")
            .load())

    # ── Section 1: Clear Database ────────────────────────────────────────────

    if not args.skip_clear:
        print("Clearing database...")
        MAX_CLEAR_PASSES = 20
        for pass_num in range(1, MAX_CLEAR_PASSES + 1):
            # Delete batch via script, count via query — combined in one read.
            # No IN TRANSACTIONS (works in explicit tx). Comment busts Spark cache.
            result = (spark.read
                .format("org.neo4j.spark.DataSource")
                .option("script",
                    "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n")
                .option("query",
                    f"MATCH (n) RETURN count(n) AS remaining // pass {pass_num}")
                .load())
            remaining = result.collect()[0]["remaining"]
            print(f"  Clear pass {pass_num}: {remaining} nodes remaining")
            if remaining == 0:
                break
        record("Clear database", remaining == 0, f"remaining={remaining}")
    else:
        print("Skipping database clear (--skip-clear)")

    # ── Section 2: Create Constraints and Indexes ────────────────────────────

    print("\nCreating constraints and indexes...")

    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Aircraft) REQUIRE n.aircraft_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:System) REQUIRE n.system_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Component) REQUIRE n.component_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Sensor) REQUIRE n.sensor_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Airport) REQUIRE n.airport_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Flight) REQUIRE n.flight_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Delay) REQUIRE n.delay_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:MaintenanceEvent) REQUIRE n.event_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Removal) REQUIRE n.removal_id IS UNIQUE",
    ]

    indexes = [
        "CREATE INDEX idx_maintenanceevent_severity IF NOT EXISTS "
        "FOR (n:MaintenanceEvent) ON (n.severity)",
        "CREATE INDEX idx_flight_aircraft_id IF NOT EXISTS FOR (n:Flight) ON (n.aircraft_id)",
        "CREATE INDEX idx_removal_aircraft_id IF NOT EXISTS FOR (n:Removal) ON (n.aircraft_id)",
    ]

    run_script(";\n".join(constraints + indexes))
    record("Constraints and indexes", True)

    # ── Section 3: Load Nodes ────────────────────────────────────────────────

    print("\nLoading nodes...")
    expected_nodes = {}

    # Aircraft
    df = read_csv("nodes_aircraft.csv").withColumnRenamed(":ID(Aircraft)", "aircraft_id")
    expected_nodes["Aircraft"] = write_nodes(df, "Aircraft", "aircraft_id")

    # System
    df = read_csv("nodes_systems.csv").withColumnRenamed(":ID(System)", "system_id")
    expected_nodes["System"] = write_nodes(df, "System", "system_id")

    # Component
    df = read_csv("nodes_components.csv").withColumnRenamed(":ID(Component)", "component_id")
    expected_nodes["Component"] = write_nodes(df, "Component", "component_id")

    # Sensor
    df = read_csv("nodes_sensors.csv").withColumnRenamed(":ID(Sensor)", "sensor_id")
    expected_nodes["Sensor"] = write_nodes(df, "Sensor", "sensor_id")

    # Airport
    df = (read_csv("nodes_airports.csv")
        .withColumnRenamed(":ID(Airport)", "airport_id")
        .withColumn("lat", col("lat").cast("double"))
        .withColumn("lon", col("lon").cast("double")))
    expected_nodes["Airport"] = write_nodes(df, "Airport", "airport_id")

    # Flight
    df = read_csv("nodes_flights.csv").withColumnRenamed(":ID(Flight)", "flight_id")
    expected_nodes["Flight"] = write_nodes(df, "Flight", "flight_id")

    # Delay
    df = (read_csv("nodes_delays.csv")
        .withColumnRenamed(":ID(Delay)", "delay_id")
        .withColumn("minutes", col("minutes").cast("integer")))
    expected_nodes["Delay"] = write_nodes(df, "Delay", "delay_id")

    # MaintenanceEvent
    df = read_csv("nodes_maintenance.csv").withColumnRenamed(":ID(MaintenanceEvent)", "event_id")
    expected_nodes["MaintenanceEvent"] = write_nodes(df, "MaintenanceEvent", "event_id")

    # Removal
    df = (read_csv("nodes_removals.csv")
        .withColumnRenamed(":ID(RemovalEvent)", "removal_id")
        .withColumnRenamed("RMV_REA_TX", "reason")
        .withColumnRenamed("time_since_install", "tsn")
        .withColumnRenamed("flight_cycles_at_removal", "csn")
        .withColumn("tsn", col("tsn").cast("double"))
        .withColumn("csn", col("csn").cast("integer")))
    expected_nodes["Removal"] = write_nodes(df, "Removal", "removal_id")

    # ── Section 4: Load Relationships ────────────────────────────────────────

    print("\nLoading relationships...")
    expected_rels = {}

    # HAS_SYSTEM
    df = (read_csv("rels_aircraft_system.csv")
        .withColumnRenamed(":START_ID(Aircraft)", "aircraft_id")
        .withColumnRenamed(":END_ID(System)", "system_id"))
    expected_rels["HAS_SYSTEM"] = write_relationships(
        df, "HAS_SYSTEM", "Aircraft", "aircraft_id", "System", "system_id")

    # HAS_COMPONENT
    df = (read_csv("rels_system_component.csv")
        .withColumnRenamed(":START_ID(System)", "system_id")
        .withColumnRenamed(":END_ID(Component)", "component_id"))
    expected_rels["HAS_COMPONENT"] = write_relationships(
        df, "HAS_COMPONENT", "System", "system_id", "Component", "component_id")

    # HAS_SENSOR
    df = (read_csv("rels_system_sensor.csv")
        .withColumnRenamed(":START_ID(System)", "system_id")
        .withColumnRenamed(":END_ID(Sensor)", "sensor_id"))
    expected_rels["HAS_SENSOR"] = write_relationships(
        df, "HAS_SENSOR", "System", "system_id", "Sensor", "sensor_id")

    # HAS_EVENT
    df = (read_csv("rels_component_event.csv")
        .withColumnRenamed(":START_ID(Component)", "component_id")
        .withColumnRenamed(":END_ID(MaintenanceEvent)", "event_id"))
    expected_rels["HAS_EVENT"] = write_relationships(
        df, "HAS_EVENT", "Component", "component_id", "MaintenanceEvent", "event_id")

    # OPERATES_FLIGHT
    df = (read_csv("rels_aircraft_flight.csv")
        .withColumnRenamed(":START_ID(Aircraft)", "aircraft_id")
        .withColumnRenamed(":END_ID(Flight)", "flight_id"))
    expected_rels["OPERATES_FLIGHT"] = write_relationships(
        df, "OPERATES_FLIGHT", "Aircraft", "aircraft_id", "Flight", "flight_id")

    # DEPARTS_FROM
    df = (read_csv("rels_flight_departure.csv")
        .withColumnRenamed(":START_ID(Flight)", "flight_id")
        .withColumnRenamed(":END_ID(Airport)", "airport_id"))
    expected_rels["DEPARTS_FROM"] = write_relationships(
        df, "DEPARTS_FROM", "Flight", "flight_id", "Airport", "airport_id")

    # ARRIVES_AT
    df = (read_csv("rels_flight_arrival.csv")
        .withColumnRenamed(":START_ID(Flight)", "flight_id")
        .withColumnRenamed(":END_ID(Airport)", "airport_id"))
    expected_rels["ARRIVES_AT"] = write_relationships(
        df, "ARRIVES_AT", "Flight", "flight_id", "Airport", "airport_id")

    # HAS_DELAY
    df = (read_csv("rels_flight_delay.csv")
        .withColumnRenamed(":START_ID(Flight)", "flight_id")
        .withColumnRenamed(":END_ID(Delay)", "delay_id"))
    expected_rels["HAS_DELAY"] = write_relationships(
        df, "HAS_DELAY", "Flight", "flight_id", "Delay", "delay_id")

    # AFFECTS_SYSTEM
    df = (read_csv("rels_event_system.csv")
        .withColumnRenamed(":START_ID(MaintenanceEvent)", "event_id")
        .withColumnRenamed(":END_ID(System)", "system_id"))
    expected_rels["AFFECTS_SYSTEM"] = write_relationships(
        df, "AFFECTS_SYSTEM", "MaintenanceEvent", "event_id", "System", "system_id")

    # AFFECTS_AIRCRAFT
    df = (read_csv("rels_event_aircraft.csv")
        .withColumnRenamed(":START_ID(MaintenanceEvent)", "event_id")
        .withColumnRenamed(":END_ID(Aircraft)", "aircraft_id"))
    expected_rels["AFFECTS_AIRCRAFT"] = write_relationships(
        df, "AFFECTS_AIRCRAFT", "MaintenanceEvent", "event_id", "Aircraft", "aircraft_id")

    # HAS_REMOVAL
    df = (read_csv("rels_aircraft_removal.csv")
        .withColumnRenamed(":START_ID(Aircraft)", "aircraft_id")
        .withColumnRenamed(":END_ID(RemovalEvent)", "removal_id"))
    expected_rels["HAS_REMOVAL"] = write_relationships(
        df, "HAS_REMOVAL", "Aircraft", "aircraft_id", "Removal", "removal_id")

    # REMOVED_COMPONENT
    df = (read_csv("rels_component_removal.csv")
        .withColumnRenamed(":START_ID(Component)", "component_id")
        .withColumnRenamed(":END_ID(RemovalEvent)", "removal_id"))
    expected_rels["REMOVED_COMPONENT"] = write_relationships(
        df, "REMOVED_COMPONENT", "Removal", "removal_id", "Component", "component_id")

    # ── Section 5: Verification ──────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    # -- Verify node counts ------------------------------------------------

    print("\nNode counts:")
    node_result = run_cypher("""
        CALL () {
            MATCH (n:Aircraft) RETURN 'Aircraft' AS label, count(n) AS count
            UNION ALL
            MATCH (n:System) RETURN 'System' AS label, count(n) AS count
            UNION ALL
            MATCH (n:Component) RETURN 'Component' AS label, count(n) AS count
            UNION ALL
            MATCH (n:Sensor) RETURN 'Sensor' AS label, count(n) AS count
            UNION ALL
            MATCH (n:Airport) RETURN 'Airport' AS label, count(n) AS count
            UNION ALL
            MATCH (n:Flight) RETURN 'Flight' AS label, count(n) AS count
            UNION ALL
            MATCH (n:Delay) RETURN 'Delay' AS label, count(n) AS count
            UNION ALL
            MATCH (n:MaintenanceEvent) RETURN 'MaintenanceEvent' AS label, count(n) AS count
            UNION ALL
            MATCH (n:Removal) RETURN 'Removal' AS label, count(n) AS count
        }
        RETURN label, count
        ORDER BY count DESC
    """)
    node_result.show(truncate=False)

    neo4j_nodes = {row["label"]: row["count"] for row in node_result.collect()}
    for label, expected in expected_nodes.items():
        actual = neo4j_nodes.get(label, 0)
        record(f"Node count: {label}", actual == expected,
               f"expected={expected}, actual={actual}")

    # -- Verify relationship counts ----------------------------------------

    print("\nRelationship counts:")
    rel_result = run_cypher("""
        MATCH ()-[r]->()
        RETURN type(r) AS rel_type, count(*) AS count
        ORDER BY count DESC
    """)
    rel_result.show(truncate=False)

    neo4j_rels = {row["rel_type"]: row["count"] for row in rel_result.collect()}
    for rel_type, expected in expected_rels.items():
        actual = neo4j_rels.get(rel_type, 0)
        record(f"Rel count: {rel_type}", actual == expected,
               f"expected={expected}, actual={actual}")

    # -- Verification queries ----------------------------------------------

    print("\nVerification queries:")

    # Critical maintenance
    critical = run_cypher("""
        CALL {
            MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)-[:HAS_COMPONENT]->(c:Component)
                  -[:HAS_EVENT]->(m:MaintenanceEvent)
            WHERE m.severity = 'CRITICAL' AND m.reported_at IS NOT NULL
            RETURN a.tail_number AS TailNumber, s.name AS System, c.name AS Component,
                   m.fault AS Fault, m.reported_at AS ReportedAt
            ORDER BY m.reported_at DESC
            LIMIT 10
        }
        RETURN TailNumber, System, Component, Fault, ReportedAt
    """)
    critical.show(truncate=False)
    record("Critical maintenance query", critical.count() > 0,
           f"rows={critical.count()}")

    # Flight delays by cause
    delays = run_cypher("""
        CALL {
            MATCH (f:Flight)-[:HAS_DELAY]->(d:Delay)
            RETURN d.cause AS Cause, count(*) AS Count, avg(d.minutes) AS AvgMinutes
            ORDER BY Count DESC
        }
        RETURN Cause, Count, AvgMinutes
    """)
    delays.show(truncate=False)
    record("Flight delays query", delays.count() > 0,
           f"rows={delays.count()}")

    # Component removal history
    removals = run_cypher("""
        CALL {
            MATCH (a:Aircraft)-[:HAS_REMOVAL]->(r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
            WHERE r.removal_date IS NOT NULL
            RETURN a.tail_number AS TailNumber, c.name AS Component, r.reason AS Reason,
                   r.removal_date AS RemovalDate
            ORDER BY r.removal_date DESC
            LIMIT 20
        }
        RETURN TailNumber, Component, Reason, RemovalDate
    """)
    removals.show(truncate=False)
    record("Component removal query", removals.count() > 0,
           f"rows={removals.count()}")

    # Aircraft hierarchy for N10000
    hierarchy = run_cypher("""
        CALL {
            MATCH (a:Aircraft {tail_number: 'N10000'})-[:HAS_SYSTEM]->(s:System)
                  -[:HAS_COMPONENT]->(c:Component)
            WHERE s.type IS NOT NULL AND s.name IS NOT NULL AND c.name IS NOT NULL
            RETURN a.tail_number AS Aircraft, s.name AS System, s.type AS SystemType,
                   c.name AS Component, c.type AS ComponentType
            ORDER BY s.type, s.name, c.name
        }
        RETURN Aircraft, System, SystemType, Component, ComponentType
    """)
    hierarchy.show(truncate=False)
    record("Aircraft hierarchy query", hierarchy.count() > 0,
           f"rows={hierarchy.count()}")

    # ── Summary ──────────────────────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)

    for name, p, detail in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    print()
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}")
    print("=" * 60)

    if failed > 0:
        print("FAILED")
        sys.exit(1)
    else:
        print("SUCCESS")


if __name__ == "__main__":
    main()
