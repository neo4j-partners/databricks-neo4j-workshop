"""Profile the Lab 2 load process to find where the time goes.

Runs the same load as run_lab2_01.py but instruments every step with
wall-clock timing, measures fixed overheads (driver round trip, Spark
connector round trip, CSV read), verifies index health before loading,
and A/B tests the Flight node load (the largest node file) across write
strategies: MERGE vs CREATE, serial vs parallel partitions.

Destructive: clears the database in full mode, or deletes Flight nodes
and their relationships in --flights-only mode.

Usage:
    ./upload.sh profile_lab2_load.py && ./submit.sh profile_lab2_load.py

submit.sh only injects credentials; the extra flags below require a
manual job submit (or a temporary edit to submit.sh):
    --flights-only    baselines + Flight A/B variants only (skips the
                      full load; keeps the rest of the graph intact)
    --batch-size N    connector batch size for all writes (default 20000)
"""

import argparse
import sys
import time
from contextlib import contextmanager


def main():
    parser = argparse.ArgumentParser(description="Profile the Lab 2 load process")
    parser.add_argument("--neo4j-uri", required=True, help="Neo4j Aura URI")
    parser.add_argument("--neo4j-username", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo4j-password", required=True, help="Neo4j password")
    parser.add_argument("--neo4j-database", default="neo4j", help="Neo4j database name")
    parser.add_argument(
        "--data-path",
        default="/Volumes/databricks-neo4j-workshop/aircraft/raw_data",
        help="Unity Catalog Volume path containing CSV data files",
    )
    parser.add_argument(
        "--flights-only",
        action="store_true",
        help="Run only baselines and Flight A/B variants (skips the full load)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=20000, help="Connector batch size for all writes"
    )
    parser.add_argument("--mcp-endpoint", default="", help="(unused)")
    parser.add_argument("--mcp-api-key", default="", help="(unused)")
    parser.add_argument("--mcp-path", default="", help="(unused)")
    args = parser.parse_args()

    from neo4j import GraphDatabase
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col

    spark = SparkSession.builder.getOrCreate()

    spark.conf.set("neo4j.url", args.neo4j_uri)
    spark.conf.set("neo4j.authentication.basic.username", args.neo4j_username)
    spark.conf.set("neo4j.authentication.basic.password", args.neo4j_password)
    spark.conf.set("neo4j.database", args.neo4j_database)

    driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_username, args.neo4j_password))

    print("=" * 70)
    print("Lab 2 Load Profiler")
    print("=" * 70)
    print(f"Neo4j URI:    {args.neo4j_uri}")
    print(f"Data Path:    {args.data_path}")
    print(f"Batch size:   {args.batch_size}")
    print(f"Mode:         {'flights-only' if args.flights_only else 'full load'}")
    print(f"Spark:        {spark.version}")
    print()

    timings = []  # (step, seconds, rows)
    results = []  # (name, passed, detail)

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    @contextmanager
    def timed(step, rows=None):
        start = time.perf_counter()
        yield
        elapsed = time.perf_counter() - start
        timings.append((step, elapsed, rows))
        rate = f", {rows / elapsed:,.0f} rows/s" if rows and elapsed > 0 else ""
        print(f"  [TIME] {step}: {elapsed:.1f}s{rate}")

    # ── Helpers: plain Neo4j driver (no Spark overhead) ───────────────────────

    def cypher(query):
        """Run a query via the Neo4j driver and return its records."""
        records, _, _ = driver.execute_query(query, database_=args.neo4j_database)
        return records

    def delete_label(label):
        """Delete all nodes with a label in batches; returns nodes deleted."""
        total = 0
        while True:
            deleted = cypher(
                f"MATCH (n:{label}) WITH n LIMIT 10000 DETACH DELETE n RETURN count(*) AS c"
            )[0]["c"]
            total += deleted
            if deleted == 0:
                return total

    # ── Helpers: Spark connector (the path the notebook uses) ────────────────

    def read_csv(filename):
        return spark.read.option("header", "true").csv(f"{args.data_path}/{filename}")

    def run_cypher(query):
        return spark.read.format("org.neo4j.spark.DataSource").option("query", query).load()

    def run_script(script):
        # The connector's read sessions reject DDL ("Writing in read access
        # mode not allowed"), so schema statements go through the driver.
        for statement in script.split(";"):
            if statement.strip():
                cypher(statement)

    def write_nodes(df, label, mode, partitions, node_key=None):
        """Write nodes with an explicit strategy so variants can be compared.

        mode="Overwrite" generates MERGE on node_key; mode="Append" generates
        plain CREATE. partitions controls how many concurrent transactions
        write to Neo4j.
        """
        writer = (
            df.repartition(partitions)
            .write.format("org.neo4j.spark.DataSource")
            .mode(mode)
            .option("labels", f":{label}")
            .option("batch.size", args.batch_size)
        )
        if mode == "Overwrite":
            writer = writer.option("node.keys", node_key)
        writer.save()

    def write_relationships(df, rel_type, source_label, source_key, target_label, target_key):
        """Write relationships exactly as the notebook does (serial, keys strategy)."""
        (
            df.coalesce(1)
            .write.format("org.neo4j.spark.DataSource")
            .mode("Overwrite")
            .option("relationship", rel_type)
            .option("relationship.save.strategy", "keys")
            .option("relationship.source.labels", f":{source_label}")
            .option("relationship.source.node.keys", source_key)
            .option("relationship.target.labels", f":{target_label}")
            .option("relationship.target.node.keys", target_key)
            .option("batch.size", args.batch_size)
            .save()
        )

    # ── Section 1: Overhead baselines ─────────────────────────────────────────

    print("--- Baselines " + "-" * 56)

    # Driver round trip: pure network + Neo4j latency, no Spark involved.
    rtts = []
    for _ in range(5):
        t0 = time.perf_counter()
        cypher("RETURN 1")
        rtts.append(time.perf_counter() - t0)
    avg_driver = sum(rtts) / len(rtts)
    print(f"  Driver RETURN 1 x5: min {min(rtts) * 1000:.0f}ms, avg {avg_driver * 1000:.0f}ms")
    timings.append(("baseline: driver RETURN 1 (avg of 5)", avg_driver, None))

    # Connector round trip: the same query through spark.read. The difference
    # vs the driver baseline is the fixed Spark job + connector overhead that
    # every notebook cell pays regardless of data volume.
    rtts = []
    for i in range(3):
        t0 = time.perf_counter()
        run_cypher(f"RETURN 1 AS x // ping {i}").collect()
        rtts.append(time.perf_counter() - t0)
    avg_connector = sum(rtts) / len(rtts)
    print(f"  Connector RETURN 1 x3: min {min(rtts):.1f}s, avg {avg_connector:.1f}s")
    timings.append(("baseline: connector RETURN 1 (avg of 3)", avg_connector, None))

    # CSV scan: Spark-only cost of reading the largest node file, no Neo4j.
    with timed("baseline: scan nodes_flights.csv (Spark only)"):
        raw_flight_rows = read_csv("nodes_flights.csv").count()
    print(f"  nodes_flights.csv rows: {raw_flight_rows:,}")

    # ── Section 2: Prepare database ───────────────────────────────────────────

    print("\n--- Prepare database " + "-" * 49)

    if args.flights_only:
        print("  Skipping full clear (--flights-only)")
    else:
        with timed("clear database"):
            while True:
                deleted = cypher(
                    "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n RETURN count(*) AS c"
                )[0]["c"]
                if deleted == 0:
                    break
        remaining = cypher("MATCH (n) RETURN count(n) AS c")[0]["c"]
        record("Clear database", remaining == 0, f"remaining={remaining}")

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
    with timed("constraints and indexes (via driver)"):
        run_script(";\n".join(constraints + indexes))

    # A still-populating index silently turns every keyed lookup into a label
    # scan, which is the classic hidden cause of slow relationship loads.
    with timed("await indexes online"):
        try:
            cypher("CALL db.awaitIndexes(300)")
        except Exception as e:
            print(f"  db.awaitIndexes unavailable ({e}); relying on SHOW INDEXES check")
    index_rows = cypher(
        "SHOW INDEXES YIELD name, state, populationPercent RETURN name, state, populationPercent"
    )
    offline = [r for r in index_rows if r["state"] != "ONLINE"]
    for r in offline:
        print(f"  index {r['name']}: {r['state']} ({r['populationPercent']}%)")
    record("All indexes ONLINE", not offline, f"{len(index_rows)} indexes, {len(offline)} offline")

    # ── Section 3: Flight node A/B variants ───────────────────────────────────

    print("\n--- Flight node A/B variants " + "-" * 41)

    flights_df = read_csv("nodes_flights.csv").withColumnRenamed(":ID(Flight)", "flight_id")
    flights_df.persist()
    flight_rows = flights_df.count()  # materialize the cache so variants skip the CSV scan

    variants = [
        ("merge serial (old notebook)", "Overwrite", 1),
        ("merge parallel x4", "Overwrite", 4),
        ("create serial", "Append", 1),
        ("create parallel x4 (new notebook)", "Append", 4),
    ]

    for name, mode, partitions in variants:
        deleted = delete_label("Flight")
        print(f"  (deleted {deleted:,} existing Flight nodes)")
        with timed(f"flights: {name}", rows=flight_rows):
            write_nodes(flights_df, "Flight", mode, partitions, node_key="flight_id")
        actual = cypher("MATCH (n:Flight) RETURN count(n) AS c")[0]["c"]
        record(f"Flight count after '{name}'", actual == flight_rows,
               f"expected={flight_rows}, actual={actual}")

    flights_df.unpersist()

    # ── Section 4: Full instrumented load ─────────────────────────────────────

    if args.flights_only:
        print("\nSkipping full load (--flights-only)")
    else:
        # The last variant left Flight nodes loaded; reload them in the full
        # pass so its timing is measured under the same conditions as the rest.
        delete_label("Flight")

        def load_nodes(df, label):
            rows = df.count()
            with timed(f"nodes: {label}", rows=rows):
                write_nodes(df, label, "Append", 4)
            return rows

        def load_rels(df, rel_type, source_label, source_key, target_label, target_key):
            rows = df.count()
            with timed(f"rels: {rel_type}", rows=rows):
                write_relationships(df, rel_type, source_label, source_key,
                                    target_label, target_key)
            return rows

        print("\n--- Full load: nodes " + "-" * 49)
        expected_nodes = {}

        df = read_csv("nodes_aircraft.csv").withColumnRenamed(":ID(Aircraft)", "aircraft_id")
        expected_nodes["Aircraft"] = load_nodes(df, "Aircraft")

        df = read_csv("nodes_systems.csv").withColumnRenamed(":ID(System)", "system_id")
        expected_nodes["System"] = load_nodes(df, "System")

        df = read_csv("nodes_components.csv").withColumnRenamed(":ID(Component)", "component_id")
        expected_nodes["Component"] = load_nodes(df, "Component")

        df = read_csv("nodes_sensors.csv").withColumnRenamed(":ID(Sensor)", "sensor_id")
        expected_nodes["Sensor"] = load_nodes(df, "Sensor")

        df = (read_csv("nodes_airports.csv")
            .withColumnRenamed(":ID(Airport)", "airport_id")
            .withColumn("lat", col("lat").cast("double"))
            .withColumn("lon", col("lon").cast("double")))
        expected_nodes["Airport"] = load_nodes(df, "Airport")

        df = read_csv("nodes_flights.csv").withColumnRenamed(":ID(Flight)", "flight_id")
        expected_nodes["Flight"] = load_nodes(df, "Flight")

        df = (read_csv("nodes_delays.csv")
            .withColumnRenamed(":ID(Delay)", "delay_id")
            .withColumn("minutes", col("minutes").cast("integer")))
        expected_nodes["Delay"] = load_nodes(df, "Delay")

        df = read_csv("nodes_maintenance.csv").withColumnRenamed(":ID(MaintenanceEvent)", "event_id")
        expected_nodes["MaintenanceEvent"] = load_nodes(df, "MaintenanceEvent")

        df = (read_csv("nodes_removals.csv")
            .withColumnRenamed(":ID(RemovalEvent)", "removal_id")
            .withColumnRenamed("RMV_REA_TX", "reason")
            .withColumnRenamed("time_since_install", "tsn")
            .withColumnRenamed("flight_cycles_at_removal", "csn")
            .withColumn("tsn", col("tsn").cast("double"))
            .withColumn("csn", col("csn").cast("integer")))
        expected_nodes["Removal"] = load_nodes(df, "Removal")

        print("\n--- Full load: relationships " + "-" * 41)
        expected_rels = {}

        rel_specs = [
            ("rels_aircraft_system.csv", "HAS_SYSTEM",
             "Aircraft", ":START_ID(Aircraft)", "aircraft_id",
             "System", ":END_ID(System)", "system_id"),
            ("rels_system_component.csv", "HAS_COMPONENT",
             "System", ":START_ID(System)", "system_id",
             "Component", ":END_ID(Component)", "component_id"),
            ("rels_system_sensor.csv", "HAS_SENSOR",
             "System", ":START_ID(System)", "system_id",
             "Sensor", ":END_ID(Sensor)", "sensor_id"),
            ("rels_component_event.csv", "HAS_EVENT",
             "Component", ":START_ID(Component)", "component_id",
             "MaintenanceEvent", ":END_ID(MaintenanceEvent)", "event_id"),
            ("rels_aircraft_flight.csv", "OPERATES_FLIGHT",
             "Aircraft", ":START_ID(Aircraft)", "aircraft_id",
             "Flight", ":END_ID(Flight)", "flight_id"),
            ("rels_flight_departure.csv", "DEPARTS_FROM",
             "Flight", ":START_ID(Flight)", "flight_id",
             "Airport", ":END_ID(Airport)", "airport_id"),
            ("rels_flight_arrival.csv", "ARRIVES_AT",
             "Flight", ":START_ID(Flight)", "flight_id",
             "Airport", ":END_ID(Airport)", "airport_id"),
            ("rels_flight_delay.csv", "HAS_DELAY",
             "Flight", ":START_ID(Flight)", "flight_id",
             "Delay", ":END_ID(Delay)", "delay_id"),
            ("rels_event_system.csv", "AFFECTS_SYSTEM",
             "MaintenanceEvent", ":START_ID(MaintenanceEvent)", "event_id",
             "System", ":END_ID(System)", "system_id"),
            ("rels_event_aircraft.csv", "AFFECTS_AIRCRAFT",
             "MaintenanceEvent", ":START_ID(MaintenanceEvent)", "event_id",
             "Aircraft", ":END_ID(Aircraft)", "aircraft_id"),
            ("rels_aircraft_removal.csv", "HAS_REMOVAL",
             "Aircraft", ":START_ID(Aircraft)", "aircraft_id",
             "Removal", ":END_ID(RemovalEvent)", "removal_id"),
        ]
        for (filename, rel_type,
             src_label, src_col, src_key,
             tgt_label, tgt_col, tgt_key) in rel_specs:
            df = (read_csv(filename)
                .withColumnRenamed(src_col, src_key)
                .withColumnRenamed(tgt_col, tgt_key))
            expected_rels[rel_type] = load_rels(df, rel_type, src_label, src_key,
                                                tgt_label, tgt_key)

        # REMOVED_COMPONENT flips direction (Removal is the source node), so it
        # does not fit the spec table above.
        df = (read_csv("rels_component_removal.csv")
            .withColumnRenamed(":START_ID(Component)", "component_id")
            .withColumnRenamed(":END_ID(RemovalEvent)", "removal_id"))
        expected_rels["REMOVED_COMPONENT"] = load_rels(
            df, "REMOVED_COMPONENT", "Removal", "removal_id", "Component", "component_id")

        print("\n--- Full load: count verification " + "-" * 36)
        for label, expected in expected_nodes.items():
            actual = cypher(f"MATCH (n:{label}) RETURN count(n) AS c")[0]["c"]
            record(f"Node count: {label}", actual == expected,
                   f"expected={expected}, actual={actual}")
        for rel_type, expected in expected_rels.items():
            actual = cypher(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS c")[0]["c"]
            record(f"Rel count: {rel_type}", actual == expected,
                   f"expected={expected}, actual={actual}")

    # ── Timing report ─────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("TIMING REPORT (slowest first)")
    print("=" * 70)
    print(f"{'STEP':<48} {'SECONDS':>8} {'ROWS':>8} {'ROWS/S':>8}")
    for step, secs, rows in sorted(timings, key=lambda t: t[1], reverse=True):
        rows_str = f"{rows:,}" if rows else "-"
        rate_str = f"{rows / secs:,.0f}" if rows and secs > 0 else "-"
        print(f"{step:<48} {secs:>8.1f} {rows_str:>8} {rate_str:>8}")

    print()
    print(f"Fixed overhead per connector call (Spark job + round trip): ~{avg_connector:.1f}s")
    print(f"Pure Neo4j round trip (driver):                             ~{avg_driver * 1000:.0f}ms")
    print("Steps whose total time is close to the connector baseline are")
    print("overhead-bound (Spark job startup), not Neo4j-bound.")

    # ── Summary ───────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    for name, p, detail in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    print()
    print(f"Total: {len(results)}  Passed: {passed}  Failed: {failed}")
    print("=" * 70)

    driver.close()

    if failed > 0:
        print("FAILED")
        sys.exit(1)
    print("SUCCESS")


if __name__ == "__main__":
    main()
