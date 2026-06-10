"""Verify Lab 2 Cypher queries against the Aircraft Digital Twin graph.

Reads Neo4j credentials from lab_setup/.env and runs read-only verification
queries from Lab_2_Databricks_ETL_Neo4j/SAMPLE_QUERIES.md. Covers Schema,
Aircraft Topology, Components and Systems, Sensors, Maintenance, Flights and
Delays, Airports and Routes, Component Removals, and Cross-Domain Analysis.

Usage:
    cd lab_setup/verify
    uv sync
    uv run verify-lab2
"""

import sys
import time
from pathlib import Path

import typer
from neo4j import GraphDatabase
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.table import Table

# lab_setup/.env is three levels up from this file (src/verify_lab2/main.py)
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
# Query definitions — sourced from Lab_2_Databricks_ETL_Neo4j/SAMPLE_QUERIES.md
# ---------------------------------------------------------------------------

QUERIES: list[dict] = [
    # ── Schema ───────────────────────────────────────────────────────────────
    {
        "section": "Schema",
        "name": "Count all nodes and relationships",
        "min_rows": 1,
        "cypher": """\
MATCH (n)
RETURN labels(n)[0] AS Label, count(n) AS Count
ORDER BY Count DESC""",
    },
    # ── Aircraft Topology ─────────────────────────────────────────────────────
    {
        "section": "Aircraft Topology",
        "name": "See one aircraft's complete hierarchy",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})-[r1:HAS_SYSTEM]->(s:System)-[r2:HAS_COMPONENT]->(c:Component)
RETURN a.tail_number AS Aircraft, s.name AS System, c.name AS Component
LIMIT 10""",
    },
    {
        "section": "Aircraft Topology",
        "name": "Aircraft hierarchy (tabular view)",
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
        "section": "Aircraft Topology",
        "name": "Compare aircraft by operator",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)
RETURN a.operator AS Operator, count(a) AS Count""",
    },
    {
        "section": "Aircraft Topology",
        "name": "Fleet by manufacturer",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)
RETURN a.manufacturer AS Manufacturer,
       count(a) AS AircraftCount,
       collect(DISTINCT a.model) AS Models
ORDER BY AircraftCount DESC""",
    },
    {
        "section": "Aircraft Topology",
        "name": "Aircraft detail card",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})
OPTIONAL MATCH (a)-[:HAS_SYSTEM]->(s:System)
OPTIONAL MATCH (a)-[:OPERATES_FLIGHT]->(f:Flight)
OPTIONAL MATCH (a)-[:HAS_REMOVAL]->(r:Removal)
RETURN a.tail_number AS TailNumber,
       a.model AS Model,
       a.manufacturer AS Manufacturer,
       a.operator AS Operator,
       count(DISTINCT s) AS Systems,
       count(DISTINCT f) AS Flights,
       count(DISTINCT r) AS Removals""",
    },
    # ── Components and Systems ────────────────────────────────────────────────
    {
        "section": "Components and Systems",
        "name": "Component distribution",
        "min_rows": 1,
        "cypher": """\
MATCH (c:Component)
RETURN c.type AS ComponentType, count(c) AS Count
ORDER BY Count DESC""",
    },
    {
        "section": "Components and Systems",
        "name": "Find all engine components",
        "min_rows": 1,
        "cypher": """\
MATCH (s:System {type: 'Engine'})-[:HAS_COMPONENT]->(c:Component)
RETURN c.type AS ComponentType, count(c) AS Count
ORDER BY Count DESC""",
    },
    {
        "section": "Components and Systems",
        "name": "System types and their component types",
        "min_rows": 1,
        "cypher": """\
MATCH (s:System)-[:HAS_COMPONENT]->(c:Component)
RETURN s.type AS SystemType,
       collect(DISTINCT c.type) AS ComponentTypes,
       count(c) AS TotalComponents
ORDER BY TotalComponents DESC""",
    },
    {
        "section": "Components and Systems",
        "name": "Systems with the most components",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)-[:HAS_COMPONENT]->(c:Component)
RETURN a.tail_number AS Aircraft,
       s.name AS System,
       s.type AS SystemType,
       count(c) AS ComponentCount
ORDER BY ComponentCount DESC
LIMIT 10""",
    },
    # ── Sensors ───────────────────────────────────────────────────────────────
    {
        "section": "Sensors",
        "name": "Sensor types and measurement units",
        "min_rows": 1,
        "cypher": """\
MATCH (sn:Sensor)
RETURN sn.type AS SensorType,
       sn.unit AS Unit,
       count(sn) AS Count
ORDER BY Count DESC""",
    },
    {
        "section": "Sensors",
        "name": "Sensors on a specific aircraft",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})-[:HAS_SYSTEM]->(s:System)-[:HAS_SENSOR]->(sn:Sensor)
WHERE s.type IS NOT NULL AND sn.type IS NOT NULL
RETURN s.name AS System,
       s.type AS SystemType,
       sn.name AS Sensor,
       sn.type AS SensorType,
       sn.unit AS Unit
ORDER BY s.type, sn.type""",
    },
    {
        "section": "Sensors",
        "name": "Systems by sensor density",
        "min_rows": 1,
        "cypher": """\
MATCH (s:System)-[:HAS_SENSOR]->(sn:Sensor)
WITH s.type AS SystemType, count(sn) AS SensorCount
RETURN SystemType, SensorCount
ORDER BY SensorCount DESC""",
    },
    {
        "section": "Sensors",
        "name": "Engine systems by aircraft model",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System {type: 'Engine'})
RETURN a.model AS Model,
       a.manufacturer AS Manufacturer,
       collect(DISTINCT s.name)[0] AS EngineType,
       count(s) AS EngineSystems
ORDER BY Model""",
    },
    # ── Maintenance ───────────────────────────────────────────────────────────
    {
        "section": "Maintenance",
        "name": "Find aircraft with critical maintenance issues",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)-[:HAS_COMPONENT]->(c:Component)-[:HAS_EVENT]->(m:MaintenanceEvent)
WHERE m.severity = 'CRITICAL' AND m.reported_at IS NOT NULL
RETURN a.tail_number, s.name, c.name, m.fault, m.reported_at
ORDER BY m.reported_at DESC
LIMIT 10""",
    },
    {
        "section": "Maintenance",
        "name": "Maintenance events by severity",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent)
RETURN m.severity AS Severity, count(m) AS Count
ORDER BY Count DESC""",
    },
    {
        "section": "Maintenance",
        "name": "Most common faults",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent)
WHERE m.fault IS NOT NULL
RETURN m.fault AS Fault,
       m.severity AS Severity,
       count(m) AS Occurrences
ORDER BY Occurrences DESC
LIMIT 15""",
    },
    {
        "section": "Maintenance",
        "name": "Aircraft ranked by maintenance burden",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(a:Aircraft)
RETURN a.tail_number AS Aircraft,
       a.model AS Model,
       count(m) AS TotalEvents,
       count(CASE WHEN m.severity = 'CRITICAL' THEN 1 END) AS CriticalEvents
ORDER BY TotalEvents DESC""",
    },
    {
        "section": "Maintenance",
        "name": "Corrective actions for critical faults",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent)
WHERE m.severity = 'CRITICAL'
  AND m.corrective_action IS NOT NULL
  AND m.reported_at IS NOT NULL
RETURN m.fault AS Fault,
       m.corrective_action AS CorrectiveAction,
       m.reported_at AS ReportedAt
ORDER BY m.reported_at DESC
LIMIT 10""",
    },
    {
        "section": "Maintenance",
        "name": "Systems with the most maintenance events",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent)-[:AFFECTS_SYSTEM]->(s:System)
RETURN s.type AS SystemType,
       count(m) AS Events,
       count(CASE WHEN m.severity = 'CRITICAL' THEN 1 END) AS Critical,
       count(CASE WHEN m.severity = 'WARNING' THEN 1 END) AS Warning
ORDER BY Events DESC""",
    },
    # ── Flights and Delays ────────────────────────────────────────────────────
    {
        "section": "Flights and Delays",
        "name": "Analyze flight delays by cause",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:HAS_DELAY]->(d:Delay)
RETURN d.cause AS Cause,
       count(*) AS Count,
       avg(d.minutes) AS AvgMinutes,
       max(d.minutes) AS MaxMinutes,
       sum(d.minutes) AS TotalMinutes
ORDER BY Count DESC""",
    },
    {
        "section": "Flights and Delays",
        "name": "Flights by operator",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)
RETURN f.operator AS Operator, count(f) AS FlightCount
ORDER BY FlightCount DESC""",
    },
    {
        "section": "Flights and Delays",
        "name": "Flights for a specific aircraft",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})-[:OPERATES_FLIGHT]->(f:Flight)
WHERE f.scheduled_departure IS NOT NULL
OPTIONAL MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
OPTIONAL MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
RETURN f.flight_number AS Flight,
       dep.iata AS Origin,
       arr.iata AS Destination,
       f.scheduled_departure AS Departure,
       f.scheduled_arrival AS Arrival
ORDER BY f.scheduled_departure""",
    },
    {
        "section": "Flights and Delays",
        "name": "Most delayed flights",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:OPERATES_FLIGHT]->(f:Flight)-[:HAS_DELAY]->(d:Delay)
WHERE d.minutes IS NOT NULL
RETURN a.tail_number AS Aircraft,
       f.flight_number AS Flight,
       d.cause AS DelayCause,
       d.minutes AS DelayMinutes
ORDER BY d.minutes DESC
LIMIT 10""",
    },
    {
        "section": "Flights and Delays",
        "name": "Aircraft with the most total delay",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:OPERATES_FLIGHT]->(f:Flight)-[:HAS_DELAY]->(d:Delay)
RETURN a.tail_number AS Aircraft,
       a.model AS Model,
       count(d) AS DelayCount,
       sum(d.minutes) AS TotalDelayMinutes
ORDER BY TotalDelayMinutes DESC""",
    },
    # ── Airports and Routes ───────────────────────────────────────────────────
    {
        "section": "Airports and Routes",
        "name": "Airports in the dataset",
        "min_rows": 1,
        "cypher": """\
MATCH (ap:Airport)
WHERE ap.country IS NOT NULL AND ap.city IS NOT NULL
RETURN ap.iata AS IATA, ap.name AS Name, ap.city AS City, ap.country AS Country
ORDER BY ap.country, ap.city""",
    },
    {
        "section": "Airports and Routes",
        "name": "Busiest airports by departures",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:DEPARTS_FROM]->(ap:Airport)
RETURN ap.iata AS Airport,
       ap.name AS Name,
       count(f) AS Departures
ORDER BY Departures DESC
LIMIT 10""",
    },
    {
        "section": "Airports and Routes",
        "name": "Airport-to-airport route frequency",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:DEPARTS_FROM]->(dep:Airport)
MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
RETURN dep.iata AS Origin,
       arr.iata AS Destination,
       count(f) AS FlightCount
ORDER BY FlightCount DESC
LIMIT 15""",
    },
    {
        "section": "Airports and Routes",
        "name": "Airports with the most delays",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:HAS_DELAY]->(d:Delay)
MATCH (f)-[:DEPARTS_FROM]->(ap:Airport)
RETURN ap.iata AS Airport,
       ap.name AS Name,
       count(d) AS DelayedFlights,
       sum(d.minutes) AS TotalDelayMinutes,
       avg(d.minutes) AS AvgDelayMinutes
ORDER BY TotalDelayMinutes DESC
LIMIT 10""",
    },
    # ── Component Removals ────────────────────────────────────────────────────
    {
        "section": "Component Removals",
        "name": "Find component removal history",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_REMOVAL]->(r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
WHERE r.removal_date IS NOT NULL
RETURN a.tail_number, c.name, r.reason, r.removal_date, r.tsn, r.csn
ORDER BY r.removal_date DESC
LIMIT 20""",
    },
    {
        "section": "Component Removals",
        "name": "Removals by reason",
        "min_rows": 1,
        "cypher": """\
MATCH (r:Removal)
WHERE r.reason IS NOT NULL
RETURN r.reason AS Reason, count(r) AS Count
ORDER BY Count DESC""",
    },
    {
        "section": "Component Removals",
        "name": "Aircraft with the most removals",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_REMOVAL]->(r:Removal)
RETURN a.tail_number AS Aircraft,
       a.model AS Model,
       count(r) AS Removals,
       avg(r.tsn) AS AvgTimeSinceNew,
       avg(r.csn) AS AvgCyclesSinceNew
ORDER BY Removals DESC""",
    },
    {
        "section": "Component Removals",
        "name": "Which components get removed most often",
        "min_rows": 1,
        "cypher": """\
MATCH (r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
RETURN c.type AS ComponentType,
       c.name AS ComponentName,
       count(r) AS TimesRemoved
ORDER BY TimesRemoved DESC
LIMIT 15""",
    },
    # ── Cross-Domain Analysis ─────────────────────────────────────────────────
    {
        "section": "Cross-Domain Analysis",
        "name": "Aircraft with both critical maintenance and delays",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent {severity: 'CRITICAL'})-[:AFFECTS_AIRCRAFT]->(a:Aircraft)
WITH a, count(m) AS CriticalEvents
MATCH (a)-[:OPERATES_FLIGHT]->(f:Flight)-[:HAS_DELAY]->(d:Delay)
RETURN a.tail_number AS Aircraft,
       a.model AS Model,
       CriticalEvents,
       count(d) AS DelayedFlights,
       sum(d.minutes) AS TotalDelayMinutes
ORDER BY CriticalEvents DESC""",
    },
    {
        "section": "Cross-Domain Analysis",
        "name": "Maintenance history for removed components",
        "min_rows": 1,
        "cypher": """\
MATCH (r:Removal)-[:REMOVED_COMPONENT]->(c:Component)-[:HAS_EVENT]->(m:MaintenanceEvent)
WHERE r.removal_date IS NOT NULL
RETURN c.name AS Component,
       c.type AS ComponentType,
       r.reason AS RemovalReason,
       r.removal_date AS RemovedOn,
       m.fault AS PriorFault,
       m.severity AS FaultSeverity,
       m.reported_at AS FaultReportedAt
ORDER BY r.removal_date DESC
LIMIT 20""",
    },
    {
        "section": "Cross-Domain Analysis",
        "name": "Full aircraft profile: systems, maintenance, flights, removals",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})
OPTIONAL MATCH (a)-[:HAS_SYSTEM]->(s:System)
WITH a, count(s) AS SystemCount
OPTIONAL MATCH (a)-[:OPERATES_FLIGHT]->(f:Flight)
WITH a, SystemCount, count(f) AS FlightCount
OPTIONAL MATCH (a)-[:HAS_REMOVAL]->(r:Removal)
WITH a, SystemCount, FlightCount, count(r) AS RemovalCount
OPTIONAL MATCH (m:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(a)
RETURN a.tail_number AS TailNumber,
       a.model AS Model,
       a.operator AS Operator,
       SystemCount,
       FlightCount,
       RemovalCount,
       count(m) AS MaintenanceEvents""",
    },
    {
        "section": "Cross-Domain Analysis",
        "name": "Airports serving delayed aircraft with critical maintenance",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent {severity: 'CRITICAL'})-[:AFFECTS_AIRCRAFT]->(a:Aircraft)
WITH DISTINCT a
MATCH (a)-[:OPERATES_FLIGHT]->(f:Flight)-[:DEPARTS_FROM]->(ap:Airport)
WHERE EXISTS { (f)-[:HAS_DELAY]->(:Delay) }
RETURN ap.iata AS Airport,
       ap.name AS AirportName,
       count(DISTINCT a) AS AffectedAircraft,
       count(f) AS DelayedFlights
ORDER BY DelayedFlights DESC""",
    },
    {
        "section": "Cross-Domain Analysis",
        "name": "Route delay analysis with maintenance correlation",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:DEPARTS_FROM]->(dep:Airport)
MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
OPTIONAL MATCH (f)-[:HAS_DELAY]->(d:Delay)
MATCH (a:Aircraft)-[:OPERATES_FLIGHT]->(f)
OPTIONAL MATCH (me:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(a)
WHERE me.severity = 'CRITICAL'
WITH dep.iata AS Origin,
     arr.iata AS Destination,
     count(DISTINCT f) AS Flights,
     count(DISTINCT d) AS Delays,
     count(DISTINCT me) AS CriticalEvents
WHERE Flights > 1
RETURN Origin,
       Destination,
       Flights,
       Delays,
       CriticalEvents
ORDER BY Delays DESC
LIMIT 15""",
    },
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@app.command()
def verify() -> None:
    """Run all Lab 2 verification queries against the Aircraft Digital Twin graph."""
    try:
        settings = Settings()
    except Exception as e:
        console.print(f"[red]Failed to load settings from {_ENV_FILE}: {e}[/red]")
        raise typer.Exit(1) from e

    console.rule("[bold]Lab 2 Verification — Aircraft Digital Twin Graph[/bold]")
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
