"""Read-only verification of Lab 2 data in Neo4j.

Runs all 13 Cypher verification queries (all from Notebook 01) against an
existing Neo4j instance without modifying any data. Use this to verify
Lab 2 data was loaded correctly without the destructive clear+reload of run_lab2_01.py.

Queries ported from verify_labs/src/verify_labs/lab2_queries.py.

Usage:
    ./upload.sh verify_lab2.py && ./submit.sh verify_lab2.py
"""

import argparse
import sys
import time

# ── Query definitions (from verify_labs lab2_queries.py) ──────────────────────

QUERIES = [
    # ── Core topology (Aircraft, System, Component) ───────────────────────────
    {
        "name": "Node counts by label",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(*) AS Count
ORDER BY NodeType""",
    },
    {
        "name": "Relationship counts by type",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH ()-[r]->()
RETURN type(r) AS RelType, count(*) AS Count
ORDER BY RelType""",
    },
    {
        "name": "Aircraft hierarchy for N10000",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})-[:HAS_SYSTEM]->(s:System)
WHERE s.type IS NOT NULL AND s.name IS NOT NULL
OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(c:Component)
RETURN a.tail_number AS Aircraft,
       a.model AS Model,
       s.name AS System,
       s.type AS SystemType,
       collect(c.name) AS Components
ORDER BY s.type, s.name""",
    },
    {
        "name": "Fleet by manufacturer",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)
RETURN a.manufacturer AS Manufacturer,
       count(a) AS AircraftCount,
       collect(a.model) AS Models
ORDER BY AircraftCount DESC""",
    },
    {
        "name": "Component distribution",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH (c:Component)
RETURN c.type AS ComponentType, count(c) AS Count
ORDER BY Count DESC""",
    },
    {
        "name": "Complete aircraft hierarchy",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})-[:HAS_SYSTEM]->(s:System)-[:HAS_COMPONENT]->(c:Component)
WHERE s.type IS NOT NULL AND s.name IS NOT NULL AND c.name IS NOT NULL
RETURN a.tail_number AS Aircraft, s.name AS System, s.type AS SystemType,
       c.name AS Component, c.type AS ComponentType
ORDER BY s.type, s.name, c.name""",
    },
    {
        "name": "Compare aircraft by operator",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)
RETURN a.operator AS Operator, count(a) AS Count""",
    },
    {
        "name": "Engine components",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH (s:System {type: 'Engine'})-[:HAS_COMPONENT]->(c:Component)
RETURN c.type AS ComponentType, count(c) AS Count
ORDER BY Count DESC""",
    },
    # ── Operational data (Sensors, Flights, Delays, Maintenance, Removals) ────
    {
        "name": "Comprehensive node counts",
        "notebook": "01",
        "min_rows": 9,
        "cypher": """\
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
ORDER BY count DESC""",
    },
    {
        "name": "Total relationship count",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH ()-[r]->() RETURN count(r) AS count""",
    },
    {
        "name": "Critical maintenance issues",
        "notebook": "01",
        "min_rows": 1,
        # NOTE: CSV data stores 'CRITICAL' (not 'Critical')
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)-[:HAS_COMPONENT]->(c:Component)-[:HAS_EVENT]->(m:MaintenanceEvent)
WHERE m.severity = 'CRITICAL' AND m.reported_at IS NOT NULL
RETURN a.tail_number AS TailNumber, s.name AS System, c.name AS Component,
       m.fault AS Fault, m.reported_at AS ReportedAt
ORDER BY m.reported_at DESC
LIMIT 10""",
    },
    {
        "name": "Flight delays by cause",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:HAS_DELAY]->(d:Delay)
RETURN d.cause AS Cause, count(*) AS Count, avg(d.minutes) AS AvgMinutes
ORDER BY Count DESC""",
    },
    {
        "name": "Component removal history",
        "notebook": "01",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_REMOVAL]->(r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
WHERE r.removal_date IS NOT NULL
RETURN a.tail_number AS TailNumber, c.name AS Component, r.reason AS Reason,
       r.removal_date AS RemovalDate, r.tsn AS TSN, r.csn AS CSN
ORDER BY r.removal_date DESC
LIMIT 20""",
    },
]


def main():
    parser = argparse.ArgumentParser(
        description="Lab 2 Read-Only Verification: 13 Cypher queries"
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

    from neo4j import GraphDatabase

    print("=" * 70)
    print("Lab 2 Read-Only Verification — 13 queries")
    print("=" * 70)
    print(f"Neo4j URI:  {args.neo4j_uri}")
    print()

    # ── Connect ───────────────────────────────────────────────────────────────

    try:
        t0 = time.time()
        driver = GraphDatabase.driver(
            args.neo4j_uri, auth=(args.neo4j_username, args.neo4j_password)
        )
        driver.verify_connectivity()
        print(f"Connected in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    print()

    results = []  # (name, passed, detail)

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    # ── Run queries ───────────────────────────────────────────────────────────

    current_notebook = None
    t_start = time.time()

    for i, q in enumerate(QUERIES, 1):
        # Print notebook section header on transition
        if q["notebook"] != current_notebook:
            current_notebook = q["notebook"]
            nb_queries = sum(1 for x in QUERIES if x["notebook"] == current_notebook)
            print(f"\n── Notebook {current_notebook} ({nb_queries} queries) " + "─" * 30)

        print(f"\n  Query {i}/{len(QUERIES)}: {q['name']}")

        try:
            records, _, _ = driver.execute_query(q["cypher"], database_=args.neo4j_database)
            rows = [dict(r) for r in records]
            row_count = len(rows)

            # Print first 5 rows
            if rows:
                columns = list(rows[0].keys())
                print(f"    {'  |  '.join(columns)}")
                for row in rows[:5]:
                    values = [str(row[c]) for c in columns]
                    print(f"    {'  |  '.join(values)}")
                if row_count > 5:
                    print(f"    ... ({row_count - 5} more rows)")
            else:
                print("    (no rows returned)")

            passed = row_count >= q["min_rows"]
            record(q["name"], passed, f"rows={row_count}, min={q['min_rows']}")

        except Exception as e:
            record(q["name"], False, f"error: {e}")

    elapsed = time.time() - t_start
    print(f"\nQueries completed in {elapsed:.2f}s")

    driver.close()
    print("Connection closed.")

    # ── Summary ───────────────────────────────────────────────────────────────

    _print_summary(results)

    failed = sum(1 for _, p, _ in results if not p)
    if failed > 0:
        sys.exit(1)


def _print_summary(results):
    """Print the PASS/FAIL summary table."""
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, p, detail in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    print()
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}")
    print("=" * 70)

    if failed > 0:
        print("FAILED")
    else:
        print("SUCCESS")


if __name__ == "__main__":
    main()
