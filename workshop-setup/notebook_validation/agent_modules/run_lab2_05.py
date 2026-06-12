"""Automated version of 05_gds_node_similarity_aircraft.ipynb for cluster execution.

Builds a bipartite Aircraft-FaultType graph, runs Node Similarity (Jaccard) to
find aircraft with overlapping failure profiles, writes SIMILAR_FAULT_PROFILE
relationships, inspects cross-model pairs, and validates with PASS/FAIL
assertions. At the end the projection is dropped and the temporary FaultType
nodes are removed; the SIMILAR_FAULT_PROFILE relationships persist.

Requires the Lab 2 base data (run_lab2_01.py) to be loaded first.

Usage:
    ./upload.sh run_lab2_05.py && ./submit.sh run_lab2_05.py
"""

import argparse
import sys

from neo4j import GraphDatabase

PROJECTION = "aircraft-faulttype"


def main():
    parser = argparse.ArgumentParser(
        description="Lab 2 Notebook 05: GDS Node Similarity Aircraft"
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
    parser.add_argument("--mcp-endpoint", default="", help="(unused)")
    parser.add_argument("--mcp-api-key", default="", help="(unused)")
    parser.add_argument("--mcp-path", default="", help="(unused)")
    args = parser.parse_args()

    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col

    spark = SparkSession.builder.getOrCreate()

    print("=" * 60)
    print("Lab 2 Notebook 05: GDS Node Similarity Aircraft")
    print("=" * 60)
    print(f"Neo4j URI:    {args.neo4j_uri}")
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

        # ── Fault vocabulary present ─────────────────────────────────────────

        vocabulary = run_query(driver, """
            MATCH (m:MaintenanceEvent)
            WITH m.fault + '_' + m.severity AS fault_key
            RETURN count(DISTINCT fault_key) AS distinct_keys
        """)[0]["distinct_keys"]
        record("Fault vocabulary present", vocabulary > 0, f"distinct_keys={vocabulary}")

        # ── Create FaultType nodes + EXPERIENCED_FAULT relationships ─────────

        created = run_query(driver, """
            MATCH (a:Aircraft)-[:HAS_SYSTEM]->(:System)-[:HAS_COMPONENT]->(:Component)
                  -[:HAS_EVENT]->(m:MaintenanceEvent)
            WITH a, m.fault + '_' + m.severity AS fault_key,
                    m.fault AS fault_name, m.severity AS severity
            MERGE (ft:FaultType {key: fault_key})
                ON CREATE SET ft.fault = fault_name, ft.severity = severity
            MERGE (a)-[:EXPERIENCED_FAULT]->(ft)
            RETURN count(DISTINCT ft) AS fault_type_nodes, count(DISTINCT a) AS aircraft_connected
        """)[0]
        print(f"  FaultType nodes={created['fault_type_nodes']}, "
              f"aircraft connected={created['aircraft_connected']}")
        record("FaultType nodes created",
               created["fault_type_nodes"] > 0 and created["aircraft_connected"] > 0,
               f"fault_types={created['fault_type_nodes']}, "
               f"aircraft={created['aircraft_connected']}")

        # ── Build bipartite projection ───────────────────────────────────────

        run_query(driver, f"CALL gds.graph.drop('{PROJECTION}', false) YIELD graphName")

        proj = run_query(driver, """
            CALL gds.graph.project(
                'aircraft-faulttype',
                ['Aircraft', 'FaultType'],
                {EXPERIENCED_FAULT: {orientation: 'NATURAL'}}
            )
            YIELD graphName, nodeCount, relationshipCount
        """)[0]
        print(f"  Projection: {proj['nodeCount']} nodes, {proj['relationshipCount']} relationships")
        record("Build aircraft-faulttype projection",
               proj["nodeCount"] > 0 and proj["relationshipCount"] > 0,
               f"nodes={proj['nodeCount']}, rels={proj['relationshipCount']}")

        # ── Node Similarity stream (Aircraft-Aircraft pairs) ─────────────────

        similarity = run_query(driver, """
            CALL gds.nodeSimilarity.stream('aircraft-faulttype', {
                topK: 5,
                similarityCutoff: 0.2
            })
            YIELD node1, node2, similarity
            WHERE gds.util.asNode(node1):Aircraft AND gds.util.asNode(node2):Aircraft
            RETURN gds.util.asNode(node1).tail_number AS aircraft_a,
                   gds.util.asNode(node2).tail_number AS aircraft_b,
                   round(similarity, 4) AS jaccard
            ORDER BY jaccard DESC
            LIMIT 20
        """)
        record("Node Similarity stream", len(similarity) > 0, f"pairs={len(similarity)}")

        # ── Node Similarity write ────────────────────────────────────────────

        write = run_query(driver, """
            CALL gds.nodeSimilarity.write('aircraft-faulttype', {
                topK: 5,
                similarityCutoff: 0.2,
                writeRelationshipType: 'SIMILAR_FAULT_PROFILE',
                writeProperty: 'jaccard_score'
            })
            YIELD nodesCompared, relationshipsWritten
        """)[0]
        print(f"  Compared {write['nodesCompared']} nodes, "
              f"wrote {write['relationshipsWritten']} relationships")
        record("Node Similarity write", write["relationshipsWritten"] > 0,
               f"written={write['relationshipsWritten']}, compared={write['nodesCompared']}")

        # ── Verify relationships ─────────────────────────────────────────────

        rel_count = run_query(driver, """
            MATCH (:Aircraft)-[r:SIMILAR_FAULT_PROFILE]->(:Aircraft)
            RETURN count(r) AS c
        """)[0]["c"]
        record("SIMILAR_FAULT_PROFILE relationships exist", rel_count > 0,
               f"count={rel_count}")

        # ── Spark connector read-back + cross-model analysis ─────────────────

        try:
            similarity_df = spark_query("""
                MATCH (a:Aircraft)-[r:SIMILAR_FAULT_PROFILE]->(b:Aircraft)
                RETURN a.tail_number AS aircraft, a.model AS model,
                       b.tail_number AS peer, b.model AS peer_model,
                       round(r.jaccard_score, 4) AS jaccard_score
                ORDER BY aircraft, jaccard_score DESC
            """)
            df_count = similarity_df.count()
            cross_model = similarity_df.filter(col("model") != col("peer_model"))
            cross_count = cross_model.count()
            similarity_df.show(truncate=False)
            print(f"  Cross-model similar pairs: {cross_count}")
            record("Spark connector read similarity network", df_count == rel_count,
                   f"rows={df_count}, expected={rel_count}")
        except Exception as e:
            record("Spark connector read similarity network", False, f"error: {e}")

        # ── Cleanup: drop projection + remove temporary FaultType nodes ──────

        dropped = run_query(driver, f"CALL gds.graph.drop('{PROJECTION}', false) YIELD graphName")
        record("Drop projection", len(dropped) == 1)

        run_query(driver, "MATCH (ft:FaultType) DETACH DELETE ft")
        remaining = run_query(driver, "MATCH (ft:FaultType) RETURN count(ft) AS c")[0]["c"]
        record("FaultType nodes cleaned up", remaining == 0, f"remaining={remaining}")

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
