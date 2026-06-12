"""Automated version of 04_gds_pagerank_airports.ipynb for cluster execution.

Projects the airport route network, runs PageRank and Betweenness centrality
(stream + write), reads the scores back through the Spark connector, correlates
centrality against maintenance-caused delays, and validates with PASS/FAIL
assertions. The projection is dropped at the end; the pagerank_score and
betweenness_score properties persist on Airport nodes.

Requires the Lab 2 base data (run_lab2_01.py) to be loaded first.

Usage:
    ./upload.sh run_lab2_04.py && ./submit.sh run_lab2_04.py
"""

import argparse
import sys

from neo4j import GraphDatabase

PROJECTION = "airport-routes"


def _unwrap_projection(row):
    """The Cypher aggregation form ``RETURN gds.graph.project(...)`` returns a
    single column keyed by the expression text, whose value is the result map.
    Unwrap it to that inner map so callers can read nodeCount/relationshipCount.
    """
    if len(row) == 1:
        (value,) = row.values()
        if isinstance(value, dict) and "nodeCount" in value:
            return value
    return row


def main():
    parser = argparse.ArgumentParser(description="Lab 2 Notebook 04: GDS PageRank Airports")
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
    from pyspark.sql.functions import corr

    spark = SparkSession.builder.getOrCreate()

    print("=" * 60)
    print("Lab 2 Notebook 04: GDS PageRank Airports")
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

        # ── Route data present ───────────────────────────────────────────────

        routes = run_query(driver, """
            MATCH (f:Flight)-[:DEPARTS_FROM]->(dep:Airport)
            MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
            RETURN count(*) AS flight_legs
        """)[0]["flight_legs"]
        record("Flight route data present", routes > 0, f"flight_legs={routes}")

        # ── Build projection ─────────────────────────────────────────────────

        run_query(driver, f"CALL gds.graph.drop('{PROJECTION}', false) YIELD graphName")

        proj = run_query(driver, """
            MATCH (dep:Airport)<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(arr:Airport)
            WITH dep, arr, count(f) AS flight_count
            RETURN gds.graph.project(
                'airport-routes',
                dep,
                arr,
                {
                    sourceNodeLabels: ['Airport'],
                    targetNodeLabels: ['Airport'],
                    relationshipType: 'FLIES_TO',
                    relationshipProperties: {weight: flight_count}
                },
                {undirectedRelationshipTypes: ['FLIES_TO']}
            )
        """)[0]
        proj = _unwrap_projection(proj)
        node_count = proj["nodeCount"]
        rel_count = proj["relationshipCount"]
        print(f"  Projection: {node_count} airports, {rel_count} routes")
        record("Build airport-routes projection",
               node_count > 0 and rel_count > 0,
               f"airports={node_count}, routes={rel_count}")

        # ── PageRank stream ──────────────────────────────────────────────────

        pagerank = run_query(driver, """
            CALL gds.pageRank.stream('airport-routes', {
                maxIterations: 20,
                dampingFactor: 0.85,
                relationshipWeightProperty: 'weight'
            })
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).iata AS iata, round(score, 4) AS pagerank_score
            ORDER BY pagerank_score DESC
        """)
        record("PageRank stream", len(pagerank) == node_count,
               f"rows={len(pagerank)}, expected={node_count}")

        # ── Betweenness stream ───────────────────────────────────────────────

        betweenness = run_query(driver, """
            CALL gds.betweenness.stream('airport-routes')
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).iata AS iata, round(score, 2) AS betweenness_score
            ORDER BY betweenness_score DESC
        """)
        record("Betweenness stream", len(betweenness) == node_count,
               f"rows={len(betweenness)}, expected={node_count}")

        # ── Write scores ─────────────────────────────────────────────────────

        pr_write = run_query(driver, """
            CALL gds.pageRank.write('airport-routes', {
                writeProperty: 'pagerank_score',
                maxIterations: 20,
                relationshipWeightProperty: 'weight'
            })
            YIELD nodePropertiesWritten
        """)[0]
        record("PageRank write", pr_write["nodePropertiesWritten"] == node_count,
               f"written={pr_write['nodePropertiesWritten']}, expected={node_count}")

        bt_write = run_query(driver, """
            CALL gds.betweenness.write('airport-routes', {writeProperty: 'betweenness_score'})
            YIELD nodePropertiesWritten
        """)[0]
        record("Betweenness write", bt_write["nodePropertiesWritten"] == node_count,
               f"written={bt_write['nodePropertiesWritten']}, expected={node_count}")

        # ── Spark connector read-back + correlation ──────────────────────────

        try:
            centrality_df = spark_query("""
                MATCH (ap:Airport) WHERE ap.pagerank_score IS NOT NULL
                RETURN ap.iata AS iata, ap.city AS city,
                       ap.pagerank_score AS pagerank_score,
                       ap.betweenness_score AS betweenness_score
            """)
            centrality_df.createOrReplaceTempView("airport_centrality")
            centrality_count = centrality_df.count()
            centrality_df.orderBy("pagerank_score", ascending=False).show(truncate=False)
            record("Spark connector read centrality", centrality_count == node_count,
                   f"rows={centrality_count}, expected={node_count}")

            delay_by_airport = spark_query("""
                MATCH (f:Flight)-[:DEPARTS_FROM]->(ap:Airport)
                OPTIONAL MATCH (f)-[:HAS_DELAY]->(d:Delay)
                RETURN ap.iata AS iata,
                       count(DISTINCT f) AS total_flights,
                       count(CASE WHEN d.cause = 'Maintenance' THEN 1 END) AS maintenance_delays
            """)
            delay_by_airport.createOrReplaceTempView("airport_delays")

            correlation = spark.sql("""
                SELECT ac.iata,
                       round(ac.pagerank_score, 4) AS pagerank,
                       ad.total_flights,
                       round(100.0 * ad.maintenance_delays / NULLIF(ad.total_flights, 0), 1)
                           AS maint_delay_pct
                FROM airport_centrality ac
                JOIN airport_delays ad ON ac.iata = ad.iata
            """)
            pearson = correlation.select(
                corr("pagerank", "maint_delay_pct").alias("pearson_r")
            ).collect()[0]["pearson_r"]
            print(f"  Pearson(PageRank, maintenance delay %) = "
                  f"{round(pearson, 4) if pearson is not None else None}")
            record("Centrality/delay correlation computed", correlation.count() > 0,
                   f"airports={correlation.count()}, pearson="
                   f"{round(pearson, 4) if pearson is not None else 'n/a'}")
        except Exception as e:
            record("Spark connector read centrality", False, f"error: {e}")

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
