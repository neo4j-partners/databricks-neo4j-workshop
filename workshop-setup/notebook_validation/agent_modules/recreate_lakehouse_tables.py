"""Recreate the aircraft/systems/sensors Delta tables with renamed ID columns.

One-off admin fix. The original tables were created with ``SELECT *`` which kept
the raw CSV headers (``:ID(Sensor)`` etc.) as column names. This drops and
rebuilds the three dimension tables so their keys are aircraft_id / system_id /
sensor_id, matching the SQL in notebooks 02 and 03 and the updated
auto_scripts/lakehouse_tables.py. sensor_readings already has a clean sensor_id
and is left untouched.

Usage:
    ./upload.sh recreate_lakehouse_tables.py && ./submit.sh recreate_lakehouse_tables.py
"""

import argparse
import sys

TBLPROPS = "TBLPROPERTIES ('delta.columnMapping.mode' = 'name')"

# (table, id header, id column) for the three dimension tables to rebuild.
TABLES = [
    ("aircraft", ":ID(Aircraft)", "aircraft_id", "nodes_aircraft.csv"),
    ("systems", ":ID(System)", "system_id", "nodes_systems.csv"),
    ("sensors", ":ID(Sensor)", "sensor_id", "nodes_sensors.csv"),
]


def main():
    parser = argparse.ArgumentParser(description="Recreate dimension tables with renamed ID columns")
    parser.add_argument("--catalog", default="databricks-neo4j-workshop", help="Unity Catalog name")
    parser.add_argument("--schema", default="aircraft", help="Schema holding the lakehouse tables")
    parser.add_argument(
        "--data-path",
        default="/Volumes/databricks-neo4j-workshop/aircraft/raw_data",
        help="Volume path containing the node CSVs",
    )
    # Accepted for submit.sh compatibility (unused here).
    parser.add_argument("--neo4j-uri", default="", help="(unused)")
    parser.add_argument("--neo4j-username", default="", help="(unused)")
    parser.add_argument("--neo4j-password", default="", help="(unused)")
    parser.add_argument("--neo4j-database", default="neo4j", help="(unused)")
    parser.add_argument("--mcp-endpoint", default="", help="(unused)")
    parser.add_argument("--mcp-api-key", default="", help="(unused)")
    parser.add_argument("--mcp-path", default="", help="(unused)")
    args = parser.parse_args()

    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    target = f"`{args.catalog}`.`{args.schema}`"

    print("=" * 60)
    print("Recreate dimension tables with renamed ID columns")
    print("=" * 60)
    print(f"Target:    {target}")
    print(f"Volume:    {args.data_path}")
    print()

    results = []  # (name, passed, detail)

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    def read_csv_expr(filename):
        return (
            f"read_files('{args.data_path}/{filename}', "
            "format => 'csv', header => 'true', inferSchema => 'true')"
        )

    for table, id_header, id_col, csv in TABLES:
        print(f"\nRebuilding {table} ({id_header} -> {id_col})...")
        spark.sql(f"DROP TABLE IF EXISTS {target}.{table}")
        spark.sql(f"""
            CREATE TABLE {target}.{table}
            {TBLPROPS}
            AS SELECT `{id_header}` AS {id_col}, * EXCEPT (`{id_header}`)
            FROM {read_csv_expr(csv)}
        """)
        cols = spark.sql(f"SELECT * FROM {target}.{table} LIMIT 0").columns
        renamed = id_col in cols and id_header not in cols
        row_count = spark.sql(f"SELECT count(*) AS c FROM {target}.{table}").collect()[0]["c"]
        print(f"  columns: {cols}")
        record(f"{table}: {id_col} present, raw header gone", renamed,
               f"rows={row_count}, cols={len(cols)}")

    # Re-apply the renamed column comments so Genie stays in sync.
    comments = [
        f"COMMENT ON COLUMN {target}.aircraft.aircraft_id IS 'Unique aircraft identifier'",
        f"COMMENT ON COLUMN {target}.systems.system_id IS 'Unique system identifier'",
        f"COMMENT ON COLUMN {target}.sensors.sensor_id IS 'Unique sensor identifier'",
    ]
    try:
        for statement in comments:
            spark.sql(statement)
        record("Re-applied ID column comments", True, f"{len(comments)} comments")
    except Exception as e:
        record("Re-applied ID column comments", False, f"error: {e}")

    # ── Summary ──────────────────────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    for name, p, detail in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    print()
    print(f"Total: {len(results)}  Passed: {passed}  Failed: {failed}")
    print("=" * 60)
    if failed > 0:
        print("FAILED")
        sys.exit(1)
    print("SUCCESS")


if __name__ == "__main__":
    main()
