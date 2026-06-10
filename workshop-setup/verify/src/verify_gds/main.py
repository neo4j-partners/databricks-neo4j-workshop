"""Verify GDS Cypher queries against the Aircraft Digital Twin graph.

Loads Neo4j credentials from lab_setup/.env and runs every query from
gds-exploring.md in order: GDS version check, kNN (Notebook 04),
PageRank/Betweenness (Notebook 05), Node Similarity (Notebook 06),
and cross-algorithm queries.

Usage:
    cd lab_setup/verify
    uv sync
    uv run verify-gds
"""

import sys
import time
from pathlib import Path

import typer
from neo4j import GraphDatabase
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.table import Table

from verify_gds.nb04_features import compute_and_write_features

# lab_setup/.env — four levels up from src/verify_gds/main.py
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
# Queries — copied verbatim from gds-exploring.md.
# Multi-statement blocks are split into individual entries.
# min_rows=0 means the query is allowed to return no rows (e.g. empty fleet).
# ---------------------------------------------------------------------------

QUERIES: list[dict] = [
    # ── GDS Version and Projection Inventory ─────────────────────────────────
    {
        "section": "GDS Version and Projection Inventory",
        "name": "Check the GDS version",
        "min_rows": 1,
        "cypher": "RETURN gds.version() AS version",
    },
    {
        "section": "GDS Version and Projection Inventory",
        "name": "List active in-memory projections",
        "min_rows": 0,
        "cypher": """\
CALL gds.graph.list()
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount""",
    },
    # ── Notebook 04 — kNN Aircraft Similarity ─────────────────────────────────
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Verify feature properties landed on Aircraft nodes",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)
WHERE a.avg_egt_norm IS NOT NULL
RETURN a.tail_number                          AS TailNumber,
       round(a.avg_egt_norm, 3)               AS AvgEGT,
       round(a.stddev_vibration_norm, 3)      AS StddevVibration,
       round(a.avg_fuel_flow_norm, 3)         AS AvgFuelFlow,
       round(a.total_events_norm, 3)          AS TotalEvents,
       round(a.critical_events_norm, 3)       AS CriticalEvents
ORDER BY a.tail_number
LIMIT 10""",
    },
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Drop aircraft-profiles projection (pre-create)",
        "min_rows": 0,
        "cypher": "CALL gds.graph.drop('aircraft-profiles', false) YIELD graphName",
    },
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Project Aircraft nodes for kNN",
        "min_rows": 1,
        "cypher": """\
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
YIELD graphName, nodeCount, relationshipCount""",
    },
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Stream kNN similarity pairs",
        "min_rows": 1,
        "cypher": """\
CALL gds.knn.stream('aircraft-profiles', {
    topK: 3,
    nodeProperties: [
        'avg_egt_norm', 'stddev_egt_norm',
        'avg_vibration_norm', 'stddev_vibration_norm',
        'avg_fuel_flow_norm',
        'total_events_norm', 'critical_events_norm'
    ],
    similarityCutoff: 0.4,
    randomSeed: 42,
    concurrency: 1
})
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).tail_number AS Aircraft,
       gds.util.asNode(node1).model       AS Model,
       gds.util.asNode(node2).tail_number AS PeerAircraft,
       gds.util.asNode(node2).model       AS PeerModel,
       round(similarity, 4)               AS SimilarityScore
ORDER BY Aircraft, SimilarityScore DESC""",
    },
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Write SIMILAR_PROFILE relationships",
        "min_rows": 1,
        "cypher": """\
CALL gds.knn.write('aircraft-profiles', {
    topK: 3,
    writeRelationshipType: 'SIMILAR_PROFILE',
    writeProperty: 'similarity_score',
    nodeProperties: [
        'avg_egt_norm', 'stddev_egt_norm',
        'avg_vibration_norm', 'stddev_vibration_norm',
        'avg_fuel_flow_norm',
        'total_events_norm', 'critical_events_norm'
    ],
    randomSeed: 42,
    concurrency: 1
})
YIELD relationshipsWritten, nodesCompared""",
    },
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Visualize the full similarity network",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[r:SIMILAR_PROFILE]->(peer:Aircraft)
RETURN a, r, peer""",
    },
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Top kNN pairs by similarity score",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[r:SIMILAR_PROFILE]->(peer:Aircraft)
WHERE r.similarity_score IS NOT NULL
RETURN a.tail_number   AS Aircraft,
       a.model         AS Model,
       peer.tail_number AS Peer,
       peer.model       AS PeerModel,
       round(r.similarity_score, 4) AS Similarity
ORDER BY Similarity DESC
LIMIT 10""",
    },
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Cross-model similarity — peers across model boundaries",
        "min_rows": 0,
        "cypher": """\
MATCH (a:Aircraft)-[r:SIMILAR_PROFILE]->(peer:Aircraft)
WHERE a.model <> peer.model
  AND r.similarity_score IS NOT NULL
RETURN a.tail_number   AS Aircraft,
       a.model         AS Model,
       peer.tail_number AS Peer,
       peer.model       AS PeerModel,
       round(r.similarity_score, 4) AS Similarity
ORDER BY Similarity DESC""",
    },
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Peer alert: who to inspect when N10000 flags an anomaly?",
        "min_rows": 0,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})-[r:SIMILAR_PROFILE]->(peer:Aircraft)
WHERE r.similarity_score IS NOT NULL
RETURN peer.tail_number AS PeerTail,
       peer.model       AS PeerModel,
       peer.operator    AS PeerOperator,
       round(r.similarity_score, 4) AS Similarity
ORDER BY Similarity DESC""",
    },
    {
        "section": "Notebook 04 — kNN Aircraft Similarity",
        "name": "Drop aircraft-profiles projection (cleanup)",
        "min_rows": 0,
        "cypher": "CALL gds.graph.drop('aircraft-profiles', false) YIELD graphName",
    },
    # ── Notebook 05 — PageRank and Betweenness ────────────────────────────────
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Explore airport traffic before projecting",
        "min_rows": 1,
        "cypher": """\
MATCH (f:Flight)-[:DEPARTS_FROM]->(ap:Airport)
WITH ap, count(f) AS Departures
OPTIONAL MATCH (f2:Flight)-[:ARRIVES_AT]->(ap)
RETURN ap.iata     AS IATA,
       ap.city     AS City,
       Departures,
       count(f2)   AS Arrivals
ORDER BY Departures DESC""",
    },
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Top routes by flight frequency",
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
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Drop airport-routes projection (pre-create)",
        "min_rows": 0,
        "cypher": "CALL gds.graph.drop('airport-routes', false) YIELD graphName",
    },
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Build the weighted airport route projection (Cypher aggregation)",
        "min_rows": 1,
        "cypher": """\
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
)""",
    },
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Stream PageRank — which airports are most influential?",
        "min_rows": 1,
        "cypher": """\
CALL gds.pageRank.stream('airport-routes', {
    maxIterations: 20,
    dampingFactor: 0.85,
    relationshipWeightProperty: 'weight'
})
YIELD nodeId, score
WHERE score > 0
RETURN gds.util.asNode(nodeId).iata AS IATA,
       gds.util.asNode(nodeId).city AS City,
       round(score, 4)              AS PageRank
ORDER BY PageRank DESC""",
    },
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Stream Louvain — which airports cluster together?",
        "min_rows": 1,
        "cypher": """\
CALL gds.louvain.stream('airport-routes', {
    relationshipWeightProperty: 'weight'
})
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).iata AS IATA,
       gds.util.asNode(nodeId).city AS City,
       communityId                  AS Community
ORDER BY Community, IATA""",
    },
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Write PageRank scores to Airport nodes",
        "min_rows": 1,
        "cypher": """\
CALL gds.pageRank.write('airport-routes', {
    writeProperty: 'pagerank_score',
    maxIterations: 20,
    relationshipWeightProperty: 'weight'
})
YIELD nodePropertiesWritten""",
    },
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Write Louvain community to Airport nodes",
        "min_rows": 1,
        "cypher": """\
CALL gds.louvain.write('airport-routes', {
    writeProperty: 'community_id',
    relationshipWeightProperty: 'weight'
})
YIELD communityCount, nodePropertiesWritten""",
    },
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Airports ranked by PageRank with community (after write)",
        "min_rows": 1,
        "cypher": """\
MATCH (ap:Airport)
WHERE ap.pagerank_score IS NOT NULL
RETURN ap.iata                     AS IATA,
       ap.city                     AS City,
       round(ap.pagerank_score, 4) AS PageRank,
       ap.community_id             AS Community
ORDER BY PageRank DESC""",
    },
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Community membership — which airports cluster together?",
        "min_rows": 1,
        "cypher": """\
MATCH (ap:Airport)
WHERE ap.community_id IS NOT NULL
RETURN ap.community_id                  AS Community,
       count(ap)                        AS Airports,
       collect(ap.iata)                 AS Members,
       round(avg(ap.pagerank_score), 4) AS AvgPageRank
ORDER BY Airports DESC""",
    },
    {
        "section": "Notebook 05 — PageRank and Louvain",
        "name": "Maintenance delays departing from the top PageRank airport",
        "min_rows": 0,
        "cypher": """\
MATCH (ap:Airport)
WHERE ap.pagerank_score IS NOT NULL
WITH ap ORDER BY ap.pagerank_score DESC LIMIT 1
MATCH (ap)<-[:DEPARTS_FROM]-(f:Flight)-[:HAS_DELAY]->(d:Delay {cause: 'Maintenance'})
RETURN ap.iata         AS Airport,
       ap.city         AS City,
       f.flight_number AS Flight,
       d.minutes       AS DelayMinutes
ORDER BY DelayMinutes DESC
LIMIT 20""",
    },
    # ── Notebook 06 — Node Similarity ─────────────────────────────────────────
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Explore fault type vocabulary",
        "min_rows": 1,
        "cypher": """\
MATCH (m:MaintenanceEvent)
WITH m.fault + '_' + m.severity AS FaultKey,
     m.fault                    AS Fault,
     m.severity                 AS Severity
RETURN FaultKey, Fault, Severity, count(*) AS Occurrences
ORDER BY Occurrences DESC""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Fault type diversity per aircraft",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(:System)-[:HAS_COMPONENT]->(:Component)
      -[:HAS_EVENT]->(m:MaintenanceEvent)
RETURN a.tail_number                                          AS Aircraft,
       a.model                                               AS Model,
       count(DISTINCT m.fault + '_' + m.severity)            AS DistinctFaultTypes,
       count(m)                                              AS TotalEvents
ORDER BY DistinctFaultTypes DESC""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Create FaultType nodes (graph enrichment step)",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(:System)-[:HAS_COMPONENT]->(:Component)
      -[:HAS_EVENT]->(m:MaintenanceEvent)
WITH a,
     m.fault + '_' + m.severity AS fault_key,
     m.fault                    AS fault_name,
     m.severity                 AS severity
MERGE (ft:FaultType {key: fault_key})
    ON CREATE SET ft.fault = fault_name, ft.severity = severity
MERGE (a)-[:EXPERIENCED_FAULT]->(ft)
RETURN count(DISTINCT ft) AS FaultTypeNodes,
       count(DISTINCT a)  AS AircraftConnected""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Verify the bipartite structure",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[:EXPERIENCED_FAULT]->(ft:FaultType)
RETURN a.tail_number AS Aircraft,
       count(ft)     AS FaultTypes,
       collect(ft.key)[..5] AS SampleFaults
ORDER BY FaultTypes DESC
LIMIT 10""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Drop aircraft-faulttype projection (pre-create)",
        "min_rows": 0,
        "cypher": "CALL gds.graph.drop('aircraft-faulttype', false) YIELD graphName",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Project the bipartite Aircraft-FaultType graph",
        "min_rows": 1,
        "cypher": """\
CALL gds.graph.project(
    'aircraft-faulttype',
    ['Aircraft', 'FaultType'],
    {EXPERIENCED_FAULT: {orientation: 'NATURAL'}}
)
YIELD graphName, nodeCount, relationshipCount""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Stream Node Similarity — top Jaccard pairs",
        "min_rows": 1,
        "cypher": """\
CALL gds.nodeSimilarity.stream('aircraft-faulttype', {
    topK: 5,
    similarityCutoff: 0.2
})
YIELD node1, node2, similarity
WHERE gds.util.asNode(node1):Aircraft
  AND gds.util.asNode(node2):Aircraft
RETURN gds.util.asNode(node1).tail_number AS AircraftA,
       gds.util.asNode(node1).model       AS ModelA,
       gds.util.asNode(node2).tail_number AS AircraftB,
       gds.util.asNode(node2).model       AS ModelB,
       round(similarity, 4)               AS JaccardSimilarity
ORDER BY JaccardSimilarity DESC
LIMIT 20""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Write SIMILAR_FAULT_PROFILE relationships",
        "min_rows": 1,
        "cypher": """\
CALL gds.nodeSimilarity.write('aircraft-faulttype', {
    topK: 5,
    similarityCutoff: 0.2,
    writeRelationshipType: 'SIMILAR_FAULT_PROFILE',
    writeProperty: 'jaccard_score'
})
YIELD nodesCompared, relationshipsWritten""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Most similar aircraft pairs by Jaccard score (after write)",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[r:SIMILAR_FAULT_PROFILE]->(b:Aircraft)
WHERE r.jaccard_score IS NOT NULL
RETURN a.tail_number        AS Aircraft,
       a.model              AS Model,
       b.tail_number        AS Peer,
       b.model              AS PeerModel,
       round(r.jaccard_score, 4) AS JaccardScore
ORDER BY JaccardScore DESC
LIMIT 15""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Cross-model fault profile similarity",
        "min_rows": 0,
        "cypher": """\
MATCH (a:Aircraft)-[r:SIMILAR_FAULT_PROFILE]->(b:Aircraft)
WHERE a.model <> b.model
  AND r.jaccard_score IS NOT NULL
RETURN a.tail_number        AS Aircraft,
       a.model              AS Model,
       b.tail_number        AS Peer,
       b.model              AS PeerModel,
       round(r.jaccard_score, 4) AS JaccardScore
ORDER BY JaccardScore DESC""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Visualize the fault profile similarity network",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft)-[r:SIMILAR_FAULT_PROFILE]->(b:Aircraft)
RETURN a, r, b""",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Drop aircraft-faulttype projection (cleanup)",
        "min_rows": 0,
        "cypher": "CALL gds.graph.drop('aircraft-faulttype', false) YIELD graphName",
    },
    {
        "section": "Notebook 06 — Node Similarity",
        "name": "Clean up FaultType scaffolding (preserves SIMILAR_FAULT_PROFILE)",
        "min_rows": 0,
        "cypher": "MATCH (ft:FaultType) DETACH DELETE ft",
    },
    # ── Cross-Algorithm Queries ────────────────────────────────────────────────
    {
        "section": "Cross-Algorithm Queries",
        "name": "Compare kNN peers vs fault-profile peers for N10000",
        "min_rows": 1,
        "cypher": """\
MATCH (a:Aircraft {tail_number: 'N10000'})
CALL (a) {
  OPTIONAL MATCH (a)-[r:SIMILAR_FAULT_PROFILE]->(peer:Aircraft)
  RETURN collect({tail: peer.tail_number, jaccard: round(r.jaccard_score, 4)}) AS FaultProfilePeers
}
CALL (a) {
  OPTIONAL MATCH (a)-[r:SIMILAR_PROFILE]->(peer:Aircraft)
  RETURN collect({tail: peer.tail_number, knn: round(r.similarity_score, 4)}) AS KNNPeers
}
RETURN FaultProfilePeers, KNNPeers""",
    },
    {
        "section": "Cross-Algorithm Queries",
        "name": "Aircraft that appear as peers in both similarity algorithms",
        "min_rows": 0,
        "cypher": """\
MATCH (a:Aircraft)-[:SIMILAR_FAULT_PROFILE]->(peer:Aircraft)
MATCH (a)-[:SIMILAR_PROFILE]->(peer)
RETURN a.tail_number   AS Aircraft,
       peer.tail_number AS Peer,
       a.model          AS Model,
       peer.model       AS PeerModel
ORDER BY Aircraft""",
    },
    {
        "section": "Cross-Algorithm Queries",
        "name": "Busiest airports by PageRank that also have high maintenance delay rates",
        "min_rows": 1,
        "cypher": """\
MATCH (ap:Airport)
WHERE ap.pagerank_score IS NOT NULL
WITH ap ORDER BY ap.pagerank_score DESC LIMIT 10
MATCH (ap)<-[:DEPARTS_FROM]-(f:Flight)
OPTIONAL MATCH (f)-[:HAS_DELAY]->(d:Delay {cause: 'Maintenance'})
RETURN ap.iata                                       AS IATA,
       ap.city                                       AS City,
       round(ap.pagerank_score, 4)                   AS PageRank,
       ap.community_id                               AS Community,
       count(DISTINCT f)                             AS TotalFlights,
       count(d)                                      AS MaintenanceDelays,
       round(100.0 * count(d) / count(DISTINCT f), 1) AS MaintenanceDelayPct
ORDER BY PageRank DESC""",
    },
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@app.command()
def verify(
    skip_nb04: bool = typer.Option(False, "--skip-nb04", help="Skip feature computation (use if *_norm props already exist)"),
) -> None:
    """Run all GDS queries from gds-exploring.md against the Aircraft Digital Twin graph."""
    try:
        settings = Settings()
    except Exception as e:
        console.print(f"[red]Failed to load settings from {_ENV_FILE}: {e}[/red]")
        raise typer.Exit(1) from e

    console.rule("[bold]GDS Verification — Aircraft Digital Twin Graph[/bold]")
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

    if not skip_nb04:
        compute_and_write_features(driver)
        console.print()

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
                preview = rows[:5]
                table = Table(
                    *columns,
                    show_header=True,
                    header_style="bold",
                    box=None,
                    pad_edge=False,
                )
                for row in preview:
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
    console.print("[bold green]SUCCESS[/bold green]" if failed == 0 else "[bold red]FAILED[/bold red]")


if __name__ == "__main__":
    app()
