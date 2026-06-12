"""Automated version of 02_gds_louvain_maintenance.ipynb for cluster execution.

Builds the fault co-occurrence projection, runs Louvain community detection
(stats, stream, write), then validates the results with PASS/FAIL assertions.
The fault_community property written to Aircraft nodes persists; the in-memory
projection is dropped at the end.

Requires the Lab 2 base data (run_lab2_01.py) to be loaded first. The Delta
sensor-profile check additionally requires the sensor Delta tables to exist.

Usage:
    ./upload.sh run_lab2_02.py && ./submit.sh run_lab2_02.py
"""

import argparse
import sys

from neo4j import GraphDatabase

PROJECTION = "fault-network"


def main():
    parser = argparse.ArgumentParser(
        description="Lab 2 Notebook 02: GDS Louvain Community Detection"
    )
    parser.add_argument("--neo4j-uri", required=True, help="Neo4j Aura URI")
    parser.add_argument("--neo4j-username", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo4j-password", required=True, help="Neo4j password")
    parser.add_argument("--neo4j-database", default="neo4j", help="Neo4j database name")
    parser.add_argument(
        "--data-path",
        default="/Volumes/databricks-neo4j-workshop/aircraft/raw_data",
        help="(unused, accepted for submit.sh compatibility)",
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

    spark = SparkSession.builder.getOrCreate()

    print("=" * 60)
    print("Lab 2 Notebook 02: GDS Louvain Community Detection")
    print("=" * 60)
    print(f"Neo4j URI:    {args.neo4j_uri}")
    print(f"Catalog:      {args.catalog}.{args.schema}")
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

    def spark_query(cypher):
        return (spark.read
            .format("org.neo4j.spark.DataSource")
            .option("query", cypher)
            .load())

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

        # ── Maintenance data present ─────────────────────────────────────────

        fault_dist = run_query(driver, """
            MATCH (m:MaintenanceEvent)
            RETURN m.fault AS fault_type, count(*) AS occurrences
            ORDER BY occurrences DESC
        """)
        record("Fault distribution", len(fault_dist) > 0, f"fault_types={len(fault_dist)}")

        # ── Build projection ─────────────────────────────────────────────────

        run_query(driver, f"CALL gds.graph.drop('{PROJECTION}', false) YIELD graphName")

        proj = run_query(driver, """
            MATCH (a1:Aircraft)-[:HAS_SYSTEM]->(:System)-[:HAS_COMPONENT]->(:Component)
                  -[:HAS_EVENT]->(m1:MaintenanceEvent)
            MATCH (a2:Aircraft)-[:HAS_SYSTEM]->(:System)-[:HAS_COMPONENT]->(:Component)
                  -[:HAS_EVENT]->(m2:MaintenanceEvent)
            WHERE elementId(a1) < elementId(a2) AND m1.fault = m2.fault
            WITH a1, a2, count(DISTINCT m1.fault) AS shared_faults
            RETURN gds.graph.project(
                'fault-network',
                a1,
                a2,
                {
                    sourceNodeLabels: labels(a1),
                    targetNodeLabels: labels(a2),
                    relationshipType: 'SHARES_FAULT',
                    relationshipProperties: {weight: shared_faults}
                },
                {undirectedRelationshipTypes: ['SHARES_FAULT']}
            )
        """)[0]
        node_count = proj["nodeCount"]
        rel_count = proj["relationshipCount"]
        print(f"  Projection: {node_count} nodes, {rel_count} relationships")
        record("Build fault-network projection",
               node_count > 0 and rel_count > 0,
               f"nodes={node_count}, rels={rel_count}")

        # ── Louvain stats ────────────────────────────────────────────────────

        stats = run_query(driver, f"""
            CALL gds.louvain.stats('{PROJECTION}', {{relationshipWeightProperty: 'weight'}})
            YIELD communityCount, modularity, ranLevels
        """)[0]
        print(f"  Communities={stats['communityCount']}, "
              f"modularity={round(stats['modularity'], 4)}, levels={stats['ranLevels']}")
        record("Louvain stats", stats["communityCount"] >= 1,
               f"communities={stats['communityCount']}, "
               f"modularity={round(stats['modularity'], 4)}")

        # ── Louvain stream ───────────────────────────────────────────────────

        stream = run_query(driver, f"""
            CALL gds.louvain.stream('{PROJECTION}', {{relationshipWeightProperty: 'weight'}})
            YIELD nodeId, communityId
            RETURN gds.util.asNode(nodeId).tail_number AS aircraft, communityId
            ORDER BY communityId, aircraft
        """)
        record("Louvain stream", len(stream) == node_count,
               f"rows={len(stream)}, expected={node_count}")

        # ── Louvain write ────────────────────────────────────────────────────

        write = run_query(driver, f"""
            CALL gds.louvain.write('{PROJECTION}', {{
                writeProperty: 'fault_community',
                relationshipWeightProperty: 'weight'
            }})
            YIELD communityCount, modularity, nodePropertiesWritten
        """)[0]
        record("Louvain write", write["nodePropertiesWritten"] == node_count,
               f"written={write['nodePropertiesWritten']}, expected={node_count}")

        # ── Verify persisted property ────────────────────────────────────────

        persisted = run_query(driver, """
            MATCH (a:Aircraft) WHERE a.fault_community IS NOT NULL
            RETURN count(a) AS c
        """)[0]["c"]
        record("fault_community persisted", persisted == node_count,
               f"aircraft_with_community={persisted}, expected={node_count}")

        # ── Spark connector read-back ────────────────────────────────────────

        try:
            community_df = spark_query("""
                MATCH (a:Aircraft) WHERE a.fault_community IS NOT NULL
                RETURN a.aircraft_id AS aircraft_id, a.tail_number AS tail_number,
                       a.fault_community AS fault_community
            """)
            spark_count = community_df.count()
            community_df.orderBy("fault_community", "tail_number").show(truncate=False)
            record("Spark connector read communities", spark_count == persisted,
                   f"rows={spark_count}, expected={persisted}")
        except Exception as e:
            record("Spark connector read communities", False, f"error: {e}")

        # ── Delta sensor profile per community (optional) ────────────────────

        try:
            community_df.createOrReplaceTempView("aircraft_communities")
            sensor_by_community = spark.sql(f"""
                SELECT ac.fault_community, sen.type AS sensor_type,
                       round(AVG(r.value), 2) AS avg_value,
                       count(DISTINCT ac.aircraft_id) AS aircraft_in_community
                FROM `{args.catalog}`.`{args.schema}`.sensor_readings r
                JOIN `{args.catalog}`.`{args.schema}`.sensors sen ON r.sensor_id = sen.sensor_id
                JOIN `{args.catalog}`.`{args.schema}`.systems s ON sen.system_id = s.system_id
                JOIN aircraft_communities ac ON s.aircraft_id = ac.aircraft_id
                GROUP BY ac.fault_community, sen.type
                ORDER BY ac.fault_community, sen.type
            """)
            sensor_rows = sensor_by_community.count()
            sensor_by_community.show(truncate=False)
            record("Delta sensor profile per community", sensor_rows > 0,
                   f"rows={sensor_rows}")
        except Exception as e:
            record("Delta sensor profile per community", False, f"error: {e}")

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
