"""Verify data-exploring.md Cypher queries against the Aircraft Digital Twin graph.

Reads Neo4j credentials from lab_setup/.env and runs read-only verification
queries from Lab_2_Databricks_ETL_Neo4j/data-exploring.md. Covers Graph Schema,
Aircraft Topology, Flight Operations, Maintenance Events, Component Removals,
and Multi-Hop Patterns.

Usage:
    cd lab_setup/verify
    uv sync
    uv run verify-data-exploring
"""

import time
from pathlib import Path

import typer
from neo4j import GraphDatabase
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.table import Table

# lab_setup/.env is three levels up from this file (src/verify_data_exploring/main.py)
_ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"

app = typer.Typer(add_completion=False)
console = Console()


class Settings(BaseSettings):
    neo4j_uri: str
    neo4j_username: str = "neo4j"
    neo4j_password: str

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# ---------------------------------------------------------------------------
# Query definitions — sourced from Lab_2_Databricks_ETL_Neo4j/data-exploring.md
# ---------------------------------------------------------------------------

QUERIES: list[dict] = [
    # ── Graph Schema ──────────────────────────────────────────────────────────
    {
        "section": "Graph Schema",
        "name": "Node labels and counts",
        "min_rows": 1,
        "cypher": """\
MATCH (n)
RETURN labels(n)[0] AS Label, count(n) AS Count
ORDER BY Count DESC""",
    },
    {
        "section": "Graph Schema",
        "name": "Count relationship types",
        "min_rows": 1,
        "cypher": """\
MATCH ()-[r]->()
RETURN type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC""",
    },
    # ── Aircraft Topology ─────────────────────────────────────────────────────
    {
        "section": "Aircraft Topology",
        "name": "One aircraft's full hierarchy",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})-[:HAS_SYSTEM]->(s:System)-[:HAS_COMPONENT]->(c:Component)
RETURN a.tail_number AS Aircraft, s.name AS System, c.name AS Component
LIMIT 10""",
    },
    {
        "section": "Aircraft Topology",
        "name": "System and component breakdown (tabular)",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})-[:HAS_SYSTEM]->(s:System)
OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(c:Component)
RETURN a.tail_number AS Aircraft,
       s.type AS SystemType,
       s.name AS System,
       count(c) AS ComponentCount,
       collect(c.name) AS Components
ORDER BY s.type, s.name""",
    },
    {
        "section": "Aircraft Topology",
        "name": "Fleet breakdown by manufacturer and model",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)
RETURN a.manufacturer AS Manufacturer,
       a.model AS Model,
       count(a) AS Count,
       collect(DISTINCT a.operator) AS Operators
ORDER BY Manufacturer, Model""",
    },
    {
        "section": "Aircraft Topology",
        "name": "Systems and sensors per aircraft",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)
WITH a, count(DISTINCT s) AS SystemCount
MATCH (a)-[:HAS_SYSTEM]->(s2:System)-[:HAS_SENSOR]->(sn:Sensor)
RETURN a.tail_number AS TailNumber,
       a.model AS Model,
       SystemCount,
       count(DISTINCT sn) AS SensorCount
ORDER BY SensorCount DESC""",
    },
    # ── Flight Operations ─────────────────────────────────────────────────────
    {
        "section": "Flight Operations",
        "name": "Recent flights for one aircraft",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})-[:OPERATES_FLIGHT]->(f:Flight)
WHERE f.scheduled_departure IS NOT NULL
RETURN f.flight_number AS Flight,
       f.origin AS Origin,
       f.destination AS Destination,
       f.scheduled_departure AS Departure,
       f.scheduled_arrival AS Arrival
ORDER BY f.scheduled_departure DESC
LIMIT 10""",
    },
    {
        "section": "Flight Operations",
        "name": "Busiest routes by flight count",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:DEPARTS_FROM]->(dep:Airport),
      (f)-[:ARRIVES_AT]->(arr:Airport)
RETURN dep.iata AS Origin,
       arr.iata AS Destination,
       count(f) AS Flights
ORDER BY Flights DESC
LIMIT 15""",
    },
    {
        "section": "Flight Operations",
        "name": "Airports with the most departures",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:DEPARTS_FROM]->(a:Airport)
RETURN a.iata AS IATA,
       a.name AS Airport,
       a.city AS City,
       count(f) AS Departures
ORDER BY Departures DESC
LIMIT 10""",
    },
    {
        "section": "Flight Operations",
        "name": "Flights that experienced delays",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:HAS_DELAY]->(d:Delay)
WHERE d.minutes IS NOT NULL
RETURN f.flight_number AS Flight,
       f.origin AS Origin,
       f.destination AS Destination,
       d.cause AS DelayCause,
       d.minutes AS DelayMinutes
ORDER BY d.minutes DESC
LIMIT 20""",
    },
    {
        "section": "Flight Operations",
        "name": "Delay causes ranked by total minutes lost",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:HAS_DELAY]->(d:Delay)
WHERE d.minutes IS NOT NULL
RETURN d.cause AS Cause,
       count(d) AS Occurrences,
       sum(d.minutes) AS TotalMinutes,
       avg(d.minutes) AS AvgMinutes
ORDER BY TotalMinutes DESC""",
    },
    # ── Maintenance Events ────────────────────────────────────────────────────
    {
        "section": "Maintenance Events",
        "name": "All maintenance events with severity",
        "min_rows": 1,
        "cypher": """\
MATCH (c:Component)-[:HAS_EVENT]->(m:MaintenanceEvent)
RETURN m.severity AS Severity,
       count(m) AS EventCount,
       collect(DISTINCT m.fault)[..5] AS SampleFaults
ORDER BY EventCount DESC""",
    },
    {
        "section": "Maintenance Events",
        "name": "Maintenance events on one aircraft, newest first",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(a:Aircraft {tail_number: 'N10082'})
WHERE m.reported_at IS NOT NULL
RETURN m.event_id AS EventID,
       m.fault AS Fault,
       m.severity AS Severity,
       m.corrective_action AS Action,
       m.reported_at AS ReportedAt
ORDER BY m.reported_at DESC""",
    },
    {
        "section": "Maintenance Events",
        "name": "Systems with the most maintenance events",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent)-[:AFFECTS_SYSTEM]->(s:System)
RETURN s.type AS SystemType,
       s.name AS SystemName,
       count(m) AS Events,
       collect(DISTINCT m.severity) AS Severities
ORDER BY Events DESC
LIMIT 10""",
    },
    {
        "section": "Maintenance Events",
        "name": "Full maintenance context: component → event → system → aircraft",
        "min_rows": 1,
        "cypher": """\
MATCH (c:Component)-[:HAS_EVENT]->(m:MaintenanceEvent)-[:AFFECTS_SYSTEM]->(s:System)<-[:HAS_SYSTEM]-(a:Aircraft)
WHERE m.severity = 'CRITICAL'
RETURN a.tail_number AS Aircraft,
       a.model AS Model,
       s.type AS System,
       c.name AS Component,
       m.fault AS Fault,
       m.reported_at AS ReportedAt
ORDER BY m.reported_at DESC""",
    },
    # ── Component Removals ────────────────────────────────────────────────────
    {
        "section": "Component Removals",
        "name": "All removals with reason and cost",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_REMOVAL]->(r:Removal)
WHERE r.removal_date IS NOT NULL
RETURN a.tail_number AS Aircraft,
       r.removal_id AS RemovalID,
       r.reason AS Reason,
       r.removal_date AS Date,
       r.tsn AS TimeOnWing,
       r.csn AS CyclesAtRemoval
ORDER BY r.removal_date DESC
LIMIT 20""",
    },
    {
        "section": "Component Removals",
        "name": "Which component was removed",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_REMOVAL]->(r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
WHERE r.removal_date IS NOT NULL
RETURN a.tail_number AS Aircraft,
       c.type AS ComponentType,
       c.name AS Component,
       r.reason AS Reason,
       r.tsn AS HoursOnWing,
       r.csn AS Cycles,
       r.removal_date AS Date
ORDER BY r.removal_date DESC""",
    },
    {
        "section": "Component Removals",
        "name": "Components removed most frequently",
        "min_rows": 1,
        "cypher": """\
MATCH (r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
RETURN c.type AS ComponentType,
       c.name AS Component,
       count(r) AS Removals
ORDER BY Removals DESC
LIMIT 10""",
    },
    # ── Multi-Hop Patterns ────────────────────────────────────────────────────
    {
        "section": "Multi-Hop Patterns",
        "name": "Aircraft with maintenance events and maintenance delays",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:OPERATES_FLIGHT]->(f:Flight)-[:HAS_DELAY]->(d:Delay),
      (m:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(a)
WHERE d.cause = 'Maintenance'
RETURN a.tail_number AS Aircraft,
       count(DISTINCT f) AS DelayedFlights,
       count(DISTINCT m) AS MaintenanceEvents,
       sum(d.minutes) AS TotalDelayMinutes
ORDER BY TotalDelayMinutes DESC
LIMIT 10""",
    },
    {
        "section": "Multi-Hop Patterns",
        "name": "Sensor-to-aircraft chain",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)-[:HAS_SENSOR]->(sn:Sensor)
WHERE sn.type IS NOT NULL
RETURN a.tail_number AS Aircraft,
       s.type AS SystemType,
       sn.type AS SensorType,
       sn.name AS SensorName,
       sn.unit AS Unit
ORDER BY a.tail_number, s.type, sn.type
LIMIT 30""",
    },
    {
        "section": "Multi-Hop Patterns",
        "name": "Aircraft that use the same airport as origin and destination (round-trip)",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:OPERATES_FLIGHT]->(f1:Flight)-[:DEPARTS_FROM]->(ap:Airport),
      (a)-[:OPERATES_FLIGHT]->(f2:Flight)-[:ARRIVES_AT]->(ap)
WHERE f1.flight_id <> f2.flight_id
RETURN a.tail_number AS Aircraft,
       ap.iata AS HubAirport,
       count(DISTINCT f1) AS DepartureFlights,
       count(DISTINCT f2) AS ArrivalFlights
ORDER BY DepartureFlights DESC
LIMIT 10""",
    },
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@app.command()
def verify() -> None:
    """Run all data-exploring verification queries against the Aircraft Digital Twin graph."""
    try:
        settings = Settings()
    except Exception as e:
        console.print(f"[red]Failed to load settings from {_ENV_FILE}: {e}[/red]")
        raise typer.Exit(1) from e

    console.rule("[bold]Data Exploring Verification — Aircraft Digital Twin Graph[/bold]")
    console.print(f"Neo4j URI: {settings.neo4j_uri}")
    console.print(f"Env file:  {_ENV_FILE}")
    console.print()

    try:
        t0 = time.time()
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        driver.verify_connectivity()
        console.print(f"Connected in {time.time() - t0:.2f}s\n")
    except Exception as e:
        console.print(f"[red]Connection failed: {e}[/red]")
        raise typer.Exit(1) from e

    results: list[tuple[str, bool, str]] = []
    current_section: str | None = None
    t_start = time.time()

    for i, q in enumerate(QUERIES, 1):
        if q["section"] != current_section:
            current_section = q["section"]
            console.rule(f"[cyan]{current_section}[/cyan]")

        console.print(f"  [{i}/{len(QUERIES)}] {q['name']}")

        try:
            records, _, _ = driver.execute_query(q["cypher"])
            rows = [dict(r) for r in records]
            row_count = len(rows)

            if rows:
                columns = list(rows[0].keys())
                table = Table(*columns, show_header=True, header_style="bold", box=None, pad_edge=False)
                for row in rows[:5]:
                    table.add_row(*[str(row[c]) for c in columns])
                console.print(table)
                if row_count > 5:
                    console.print(f"    ... ({row_count - 5} more rows)")
            else:
                console.print("    (no rows returned)")

            passed = row_count >= q["min_rows"]
            detail = f"rows={row_count}"
            if not passed:
                detail += f", expected>={q['min_rows']}"
            results.append((q["name"], passed, detail))
            status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
            console.print(f"    {status}  {detail}\n")

        except Exception as e:
            results.append((q["name"], False, f"error: {e}"))
            console.print(f"    [red]FAIL[/red]  error: {e}\n")

    elapsed = time.time() - t_start
    driver.close()

    _print_summary(results, elapsed)

    failed = sum(1 for _, p, _ in results if not p)
    if failed > 0:
        raise typer.Exit(1)


def _print_summary(results: list[tuple[str, bool, str]], elapsed: float) -> None:
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)

    console.rule("[bold]SUMMARY[/bold]")
    for name, p, detail in results:
        color = "green" if p else "red"
        status = "PASS" if p else "FAIL"
        console.print(f"  [{color}][{status}][/{color}] {name}  — {detail}")

    console.print()
    console.print(f"Total: {len(results)}  Passed: {passed}  Failed: {failed}  ({elapsed:.2f}s)")
    console.rule()

    if failed == 0:
        console.print("[bold green]SUCCESS[/bold green]")
    else:
        console.print("[bold red]FAILED[/bold red]")


if __name__ == "__main__":
    app()
