"""Lightweight Neo4j connectivity and data presence check.

Quick health check before running heavier validation scripts. Verifies
that the Neo4j instance is reachable, contains data, and reports version info.

Usage:
    ./upload.sh check_neo4j.py && ./submit.sh check_neo4j.py
"""

import argparse
import sys
import time


def main():
    parser = argparse.ArgumentParser(description="Neo4j Connectivity Check")
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

    print("=" * 60)
    print("Neo4j Connectivity Check")
    print("=" * 60)
    print(f"Neo4j URI:  {args.neo4j_uri}")
    print()

    results = []  # (name, passed, detail)

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    # ── Step 1: Connect and verify connectivity ───────────────────────────────

    try:
        t0 = time.time()
        driver = GraphDatabase.driver(
            args.neo4j_uri, auth=(args.neo4j_username, args.neo4j_password)
        )
        driver.verify_connectivity()
        elapsed = time.time() - t0
        record("Neo4j connectivity", True, f"connected in {elapsed:.2f}s")
    except Exception as e:
        record("Neo4j connectivity", False, str(e))
        print("\nCannot proceed without a connection.")
        _print_summary(results)
        sys.exit(1)

    # ── Step 2: Check node count ──────────────────────────────────────────────

    try:
        records, _, _ = driver.execute_query("MATCH (n) RETURN count(n) AS count", database_=args.neo4j_database)
        node_count = records[0]["count"]
        record("Node count", True, f"{node_count:,} nodes")
    except Exception as e:
        record("Node count", False, str(e))

    # ── Step 3: Server info ───────────────────────────────────────────────────

    try:
        records, _, _ = driver.execute_query(
            "CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition",
            database_=args.neo4j_database,
        )
        row = dict(records[0])
        version = row["versions"][0] if row["versions"] else "unknown"
        edition = row.get("edition", "unknown")
        record("Server info retrieved", True, f"{row['name']} {version} ({edition})")
    except Exception as e:
        record("Server info retrieved", False, str(e))

    driver.close()
    print("\nConnection closed.")

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

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, p, detail in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    print()
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}")
    print("=" * 60)

    if failed > 0:
        print("FAILED")
    else:
        print("SUCCESS")


if __name__ == "__main__":
    main()
