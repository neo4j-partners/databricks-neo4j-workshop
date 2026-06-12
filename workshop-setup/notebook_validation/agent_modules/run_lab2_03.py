"""Automated version of 03_gds_knn_aircraft.ipynb for cluster execution.

Engineers sensor + maintenance features in Spark, normalizes them, writes the
*_norm properties back to Aircraft nodes, projects the feature graph, runs kNN
to find similar aircraft, writes SIMILAR_PROFILE relationships, and validates
the result with PASS/FAIL assertions. The projection is dropped at the end;
the *_norm properties and SIMILAR_PROFILE relationships persist.

Requires the Lab 2 base data (run_lab2_01.py), the sensor Delta tables, and the
maintenance CSV in the Unity Catalog Volume.

Usage:
    ./upload.sh run_lab2_03.py && ./submit.sh run_lab2_03.py
"""

import argparse
import sys

from neo4j import GraphDatabase

PROJECTION = "aircraft-profiles"
FEATURE_COLS = [
    "avg_egt", "stddev_egt",
    "avg_vibration", "stddev_vibration",
    "avg_fuel_flow",
    "total_events", "critical_events",
]


def main():
    parser = argparse.ArgumentParser(description="Lab 2 Notebook 03: GDS kNN Aircraft Similarity")
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
        "--catalog", default="databricks-neo4j-workshop", help="Unity Catalog name"
    )
    parser.add_argument("--schema", default="aircraft", help="Schema with sensor tables")
    parser.add_argument("--mcp-endpoint", default="", help="(unused)")
    parser.add_argument("--mcp-api-key", default="", help="(unused)")
    parser.add_argument("--mcp-path", default="", help="(unused)")
    args = parser.parse_args()

    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, count, lit, when
    from pyspark.sql.functions import max as spark_max
    from pyspark.sql.functions import min as spark_min

    spark = SparkSession.builder.getOrCreate()

    print("=" * 60)
    print("Lab 2 Notebook 03: GDS kNN Aircraft Similarity")
    print("=" * 60)
    print(f"Neo4j URI:    {args.neo4j_uri}")
    print(f"Catalog:      {args.catalog}.{args.schema}")
    print(f"Data Path:    {args.data_path}")
    print(f"Spark:        {spark.version}")
    print()

    # ── Configure Neo4j Spark Connector ──────────────────────────────────────

    spark.conf.set("neo4j.url", args.neo4j_uri)
    spark.conf.set("neo4j.authentication.basic.username", args.neo4j_username)
    spark.conf.set("neo4j.authentication.basic.password", args.neo4j_password)
    spark.conf.set("neo4j.database", args.neo4j_database)

    results = []  # (name, passed, detail)

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    def neo4j_driver():
        return GraphDatabase.driver(
            args.neo4j_uri, auth=(args.neo4j_username, args.neo4j_password)
        )

    def run_query(driver, cypher, params=None):
        records, _, _ = driver.execute_query(cypher, params or {}, database_=args.neo4j_database)
        return [dict(r) for r in records]

    with neo4j_driver() as driver:
        # ── Connectivity + GDS availability ──────────────────────────────────

        try:
            driver.verify_connectivity()
            record("Neo4j connectivity", True)
        except Exception as e:
            record("Neo4j connectivity", False, f"error: {e}")
            _finish(results)

        try:
            version = run_query(driver, "RETURN gds.version() AS version")[0]["version"]
            record("GDS available", bool(version), f"version={version}")
        except Exception as e:
            record("GDS available", False, f"error: {e}")
            _finish(results)

        # ── Feature engineering: sensor stats from Delta ─────────────────────

        try:
            sensor_stats = spark.sql(f"""
                SELECT s.aircraft_id,
                       AVG(CASE WHEN sen.type = 'EGT' THEN r.value END) AS avg_egt,
                       STDDEV(CASE WHEN sen.type = 'EGT' THEN r.value END) AS stddev_egt,
                       AVG(CASE WHEN sen.type = 'Vibration' THEN r.value END) AS avg_vibration,
                       STDDEV(CASE WHEN sen.type = 'Vibration' THEN r.value END) AS stddev_vibration,
                       AVG(CASE WHEN sen.type = 'FuelFlow' THEN r.value END) AS avg_fuel_flow
                FROM `{args.catalog}`.`{args.schema}`.sensor_readings r
                JOIN `{args.catalog}`.`{args.schema}`.sensors sen ON r.sensor_id = sen.sensor_id
                JOIN `{args.catalog}`.`{args.schema}`.systems s ON sen.system_id = s.system_id
                GROUP BY s.aircraft_id
            """)
            sensor_count = sensor_stats.count()
            record("Sensor features from Delta", sensor_count > 0,
                   f"aircraft={sensor_count}")
        except Exception as e:
            record("Sensor features from Delta", False, f"error: {e}")
            _finish(results)

        # ── Maintenance features from CSV ────────────────────────────────────

        maintenance_df = (spark.read
            .option("header", "true")
            .csv(f"{args.data_path}/nodes_maintenance.csv")
            .withColumnRenamed(":ID(MaintenanceEvent)", "event_id"))
        maintenance_stats = (maintenance_df
            .groupBy("aircraft_id")
            .agg(
                count("*").alias("total_events"),
                count(when(col("severity") == "CRITICAL", True)).alias("critical_events"),
            ))
        maint_count = maintenance_stats.count()
        record("Maintenance features from CSV", maint_count > 0, f"aircraft={maint_count}")

        # ── Join + normalize ─────────────────────────────────────────────────

        features_df = sensor_stats.join(maintenance_stats, "aircraft_id", "left").fillna(0)

        def minmax_normalize(df, columns):
            result = df
            for c in columns:
                stats = df.agg(spark_min(c).alias("lo"), spark_max(c).alias("hi")).collect()[0]
                lo, hi = stats["lo"], stats["hi"]
                if hi > lo:
                    result = result.withColumn(f"{c}_norm", (col(c) - lo) / (hi - lo))
                else:
                    result = result.withColumn(f"{c}_norm", lit(0.0))
            return result

        features_norm = minmax_normalize(features_df, FEATURE_COLS)
        norm_cols = [f"{c}_norm" for c in FEATURE_COLS]
        feature_count = features_norm.count()
        record("Feature matrix built", feature_count > 0,
               f"aircraft={feature_count}, features={len(norm_cols)}")

        # ── Write features back to Aircraft nodes ────────────────────────────

        (features_norm
            .select(["aircraft_id"] + norm_cols)
            .write
            .format("org.neo4j.spark.DataSource")
            .mode("Overwrite")
            .option("labels", ":Aircraft")
            .option("node.keys", "aircraft_id")
            .save())

        written = run_query(driver, """
            MATCH (a:Aircraft) WHERE a.avg_egt_norm IS NOT NULL
            RETURN count(a) AS c
        """)[0]["c"]
        record("Feature properties written to Aircraft", written == feature_count,
               f"aircraft_with_features={written}, expected={feature_count}")

        # ── Build projection (node properties only) ──────────────────────────

        run_query(driver, f"CALL gds.graph.drop('{PROJECTION}', false) YIELD graphName")

        proj = run_query(driver, """
            CALL gds.graph.project(
                'aircraft-profiles',
                {
                    Aircraft: {
                        properties: [
                            'avg_egt_norm', 'stddev_egt_norm',
                            'avg_vibration_norm', 'stddev_vibration_norm',
                            'avg_fuel_flow_norm',
                            'total_events_norm', 'critical_events_norm'
                        ]
                    }
                },
                '*'
            )
            YIELD graphName, nodeCount, relationshipCount
        """)[0]
        print(f"  Projection: {proj['nodeCount']} nodes, {proj['relationshipCount']} relationships")
        record("Build aircraft-profiles projection", proj["nodeCount"] > 0,
               f"nodes={proj['nodeCount']}")

        # ── kNN stream ───────────────────────────────────────────────────────

        knn_props = [f"{c}_norm" for c in FEATURE_COLS]
        knn_stream = run_query(driver, """
            CALL gds.knn.stream('aircraft-profiles', {
                topK: 3,
                nodeProperties: $props,
                similarityCutoff: 0.4,
                randomSeed: 42,
                concurrency: 1
            })
            YIELD node1, node2, similarity
            RETURN gds.util.asNode(node1).tail_number AS aircraft,
                   gds.util.asNode(node2).tail_number AS peer,
                   round(similarity, 4) AS similarity
            ORDER BY aircraft, similarity DESC
        """, {"props": knn_props})
        record("kNN stream", len(knn_stream) > 0, f"pairs={len(knn_stream)}")

        # ── kNN write ────────────────────────────────────────────────────────

        write = run_query(driver, """
            CALL gds.knn.write('aircraft-profiles', {
                topK: 3,
                writeRelationshipType: 'SIMILAR_PROFILE',
                writeProperty: 'similarity_score',
                nodeProperties: $props,
                randomSeed: 42,
                concurrency: 1
            })
            YIELD relationshipsWritten, nodesCompared
        """, {"props": knn_props})[0]
        print(f"  Compared {write['nodesCompared']} aircraft, "
              f"wrote {write['relationshipsWritten']} relationships")
        record("kNN write", write["relationshipsWritten"] > 0,
               f"written={write['relationshipsWritten']}, compared={write['nodesCompared']}")

        # ── Verify relationships ─────────────────────────────────────────────

        verify = run_query(driver, """
            MATCH ()-[r:SIMILAR_PROFILE]-()
            RETURN count(r) AS relationship_count,
                   round(avg(r.similarity_score), 4) AS avg_similarity,
                   round(min(r.similarity_score), 4) AS min_similarity,
                   round(max(r.similarity_score), 4) AS max_similarity
        """)[0]
        print(f"  SIMILAR_PROFILE: {verify['relationship_count']} rels, "
              f"range {verify['min_similarity']}–{verify['max_similarity']}")
        record("SIMILAR_PROFILE relationships exist", verify["relationship_count"] > 0,
               f"count={verify['relationship_count']}")

        # ── Drop projection ──────────────────────────────────────────────────

        dropped = run_query(driver, f"CALL gds.graph.drop('{PROJECTION}', false) YIELD graphName")
        record("Drop projection", len(dropped) == 1)

    _finish(results)


def _finish(results):
    """Print the PASS/FAIL summary and exit (non-zero on any failure)."""
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
    print("SUCCESS")
    sys.exit(0)


if __name__ == "__main__":
    main()
