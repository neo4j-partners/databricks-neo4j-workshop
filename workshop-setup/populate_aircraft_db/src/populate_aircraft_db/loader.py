"""CSV reading, batched loading, database clearing, and verification."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from neo4j import Driver
from neo4j.exceptions import Neo4jError

BATCH_SIZE = 1000
OPERATIONAL_LABELS = [
    "Aircraft",
    "System",
    "Component",
    "Sensor",
    "Reading",
    "Airport",
    "Flight",
    "Delay",
    "MaintenanceEvent",
    "Removal",
]
ENRICHMENT_LABELS = [
    "Document",
    "Chunk",
    "AircraftModel",
    "SystemReference",
    "ComponentReference",
    "Fault",
    "MaintenanceProcedure",
    "OperatingLimit",
]
RELATIONSHIP_TYPES = [
    "HAS_SYSTEM",
    "HAS_COMPONENT",
    "HAS_SENSOR",
    "HAS_READING",
    "HAS_EVENT",
    "OPERATES_FLIGHT",
    "DEPARTS_FROM",
    "ARRIVES_AT",
    "HAS_DELAY",
    "AFFECTS_SYSTEM",
    "AFFECTS_AIRCRAFT",
    "HAS_REMOVAL",
    "REMOVED_COMPONENT",
    "FROM_DOCUMENT",
    "APPLIES_TO",
    "DESCRIBES_MODEL",
    "DESCRIBES_SYSTEM",
    "DESCRIBES_COMPONENT",
    "HAS_LIMIT",
]
REQUIRED_INDEXES = [
    "maintenanceChunkEmbeddings",
    "maintenanceChunkText",
]
REQUIRED_CONSTRAINTS = [
    ("Aircraft", "aircraft_id"),
    ("System", "system_id"),
    ("Component", "component_id"),
    ("Sensor", "sensor_id"),
    ("Reading", "reading_id"),
    ("Airport", "airport_id"),
    ("Flight", "flight_id"),
    ("Delay", "delay_id"),
    ("MaintenanceEvent", "event_id"),
    ("Removal", "removal_id"),
    ("Document", "documentId"),
    ("AircraftModel", "name"),
    ("SystemReference", "name"),
    ("ComponentReference", "name"),
    ("Fault", "name"),
    ("MaintenanceProcedure", "name"),
    ("OperatingLimit", "name"),
]

# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def read_csv(data_dir: Path, filename: str) -> list[dict[str, Any]]:
    """Read a CSV file and return a list of row dicts."""
    path = data_dir / filename
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _run_in_batches(driver: Driver, records: list[dict], query: str) -> None:
    """Execute a Cypher query over records in batches of BATCH_SIZE."""
    total = len(records)
    for i in range(0, total, BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        driver.execute_query(query, batch=batch)
        progress = min(i + BATCH_SIZE, total)
        print(f"  Progress: {progress}/{total} ({100 * progress // total}%)", end="\r")
    print()


# ---------------------------------------------------------------------------
# Node loading — matches notebook 02 Cypher exactly
# ---------------------------------------------------------------------------

_NODE_DEFINITIONS: list[tuple[str, str, str]] = [
    (
        "Aircraft",
        "nodes_aircraft.csv",
        """
        UNWIND $batch AS row
        MERGE (a:Aircraft {aircraft_id: row[':ID(Aircraft)']})
        SET a.tail_number = row['tail_number'],
            a.icao24 = row['icao24'],
            a.model = row['model'],
            a.manufacturer = row['manufacturer'],
            a.operator = row['operator']
        """,
    ),
    (
        "System",
        "nodes_systems.csv",
        """
        UNWIND $batch AS row
        MERGE (s:System {system_id: row[':ID(System)']})
        SET s.aircraft_id = row['aircraft_id'],
            s.type = row['type'],
            s.name = row['name']
        """,
    ),
    (
        "Component",
        "nodes_components.csv",
        """
        UNWIND $batch AS row
        MERGE (c:Component {component_id: row[':ID(Component)']})
        SET c.system_id = row['system_id'],
            c.type = row['type'],
            c.name = row['name']
        """,
    ),
    (
        "Sensor",
        "nodes_sensors.csv",
        """
        UNWIND $batch AS row
        MERGE (s:Sensor {sensor_id: row[':ID(Sensor)']})
        SET s.system_id = row['system_id'],
            s.type = row['type'],
            s.name = row['name'],
            s.unit = row['unit']
        """,
    ),
    (
        "Reading",
        "nodes_readings.csv",
        """
        UNWIND $batch AS row
        MERGE (r:Reading {reading_id: row['reading_id']})
        SET r.sensor_id = row['sensor_id'],
            r.timestamp = row['ts'],
            r.value = toFloat(row['value'])
        """,
    ),
    (
        "Airport",
        "nodes_airports.csv",
        """
        UNWIND $batch AS row
        MERGE (a:Airport {airport_id: row[':ID(Airport)']})
        SET a.name = row['name'],
            a.city = row['city'],
            a.country = row['country'],
            a.iata = row['iata'],
            a.icao = row['icao'],
            a.lat = toFloat(row['lat']),
            a.lon = toFloat(row['lon'])
        """,
    ),
    (
        "Flight",
        "nodes_flights.csv",
        """
        UNWIND $batch AS row
        MERGE (f:Flight {flight_id: row[':ID(Flight)']})
        SET f.flight_number = row['flight_number'],
            f.aircraft_id = row['aircraft_id'],
            f.operator = row['operator'],
            f.origin = row['origin'],
            f.destination = row['destination'],
            f.scheduled_departure = row['scheduled_departure'],
            f.scheduled_arrival = row['scheduled_arrival']
        """,
    ),
    (
        "Delay",
        "nodes_delays.csv",
        """
        UNWIND $batch AS row
        MERGE (d:Delay {delay_id: row[':ID(Delay)']})
        SET d.cause = row['cause'],
            d.minutes = toInteger(row['minutes'])
        """,
    ),
    (
        "MaintenanceEvent",
        "nodes_maintenance.csv",
        """
        UNWIND $batch AS row
        MERGE (m:MaintenanceEvent {event_id: row[':ID(MaintenanceEvent)']})
        SET m.component_id = row['component_id'],
            m.system_id = row['system_id'],
            m.aircraft_id = row['aircraft_id'],
            m.fault = row['fault'],
            m.severity = row['severity'],
            m.reported_at = row['reported_at'],
            m.corrective_action = row['corrective_action']
        """,
    ),
    (
        "Removal",
        "nodes_removals.csv",
        """
        UNWIND $batch AS row
        MERGE (r:Removal {removal_id: row[':ID(RemovalEvent)']})
        SET r.tracking_number = row['RMV_TRK_NO'],
            r.component_id = row['component_id'],
            r.aircraft_id = row['aircraft_id'],
            r.removal_date = row['removal_date'],
            r.reason = row['RMV_REA_TX'],
            r.work_order_number = row['work_order_number'],
            r.technician_id = row['technician_id'],
            r.part_number = row['part_number'],
            r.serial_number = row['serial_number'],
            r.tsn = toFloat(row['time_since_install']),
            r.flight_hours_at_removal = toFloat(row['flight_hours_at_removal']),
            r.csn = toInteger(row['flight_cycles_at_removal']),
            r.replacement_required = toBoolean(row['replacement_required']),
            r.shop_visit_required = toBoolean(row['shop_visit_required']),
            r.warranty_status = row['warranty_status'],
            r.removal_priority = row['removal_priority'],
            r.cost_estimate = toFloat(row['cost_estimate']),
            r.installation_date = row['installation_date']
        """,
    ),
]

# ---------------------------------------------------------------------------
# Relationship loading — matches notebook 02 Cypher exactly
# ---------------------------------------------------------------------------

_REL_DEFINITIONS: list[tuple[str, str, str]] = [
    (
        "HAS_SYSTEM",
        "rels_aircraft_system.csv",
        """
        UNWIND $batch AS row
        MATCH (a:Aircraft {aircraft_id: row[':START_ID(Aircraft)']})
        MATCH (s:System {system_id: row[':END_ID(System)']})
        MERGE (a)-[:HAS_SYSTEM]->(s)
        """,
    ),
    (
        "HAS_COMPONENT",
        "rels_system_component.csv",
        """
        UNWIND $batch AS row
        MATCH (s:System {system_id: row[':START_ID(System)']})
        MATCH (c:Component {component_id: row[':END_ID(Component)']})
        MERGE (s)-[:HAS_COMPONENT]->(c)
        """,
    ),
    (
        "HAS_SENSOR",
        "rels_system_sensor.csv",
        """
        UNWIND $batch AS row
        MATCH (s:System {system_id: row[':START_ID(System)']})
        MATCH (sn:Sensor {sensor_id: row[':END_ID(Sensor)']})
        MERGE (s)-[:HAS_SENSOR]->(sn)
        """,
    ),
    (
        "HAS_EVENT",
        "rels_component_event.csv",
        """
        UNWIND $batch AS row
        MATCH (c:Component {component_id: row[':START_ID(Component)']})
        MATCH (m:MaintenanceEvent {event_id: row[':END_ID(MaintenanceEvent)']})
        MERGE (c)-[:HAS_EVENT]->(m)
        """,
    ),
    (
        "HAS_READING",
        "nodes_readings.csv",
        """
        UNWIND $batch AS row
        MATCH (s:Sensor {sensor_id: row['sensor_id']})
        MATCH (r:Reading {reading_id: row['reading_id']})
        MERGE (s)-[:HAS_READING]->(r)
        """,
    ),
    (
        "OPERATES_FLIGHT",
        "rels_aircraft_flight.csv",
        """
        UNWIND $batch AS row
        MATCH (a:Aircraft {aircraft_id: row[':START_ID(Aircraft)']})
        MATCH (f:Flight {flight_id: row[':END_ID(Flight)']})
        MERGE (a)-[:OPERATES_FLIGHT]->(f)
        """,
    ),
    (
        "DEPARTS_FROM",
        "rels_flight_departure.csv",
        """
        UNWIND $batch AS row
        MATCH (f:Flight {flight_id: row[':START_ID(Flight)']})
        MATCH (a:Airport {airport_id: row[':END_ID(Airport)']})
        MERGE (f)-[:DEPARTS_FROM]->(a)
        """,
    ),
    (
        "ARRIVES_AT",
        "rels_flight_arrival.csv",
        """
        UNWIND $batch AS row
        MATCH (f:Flight {flight_id: row[':START_ID(Flight)']})
        MATCH (a:Airport {airport_id: row[':END_ID(Airport)']})
        MERGE (f)-[:ARRIVES_AT]->(a)
        """,
    ),
    (
        "HAS_DELAY",
        "rels_flight_delay.csv",
        """
        UNWIND $batch AS row
        MATCH (f:Flight {flight_id: row[':START_ID(Flight)']})
        MATCH (d:Delay {delay_id: row[':END_ID(Delay)']})
        MERGE (f)-[:HAS_DELAY]->(d)
        """,
    ),
    (
        "AFFECTS_SYSTEM",
        "rels_event_system.csv",
        """
        UNWIND $batch AS row
        MATCH (m:MaintenanceEvent {event_id: row[':START_ID(MaintenanceEvent)']})
        MATCH (s:System {system_id: row[':END_ID(System)']})
        MERGE (m)-[:AFFECTS_SYSTEM]->(s)
        """,
    ),
    (
        "AFFECTS_AIRCRAFT",
        "rels_event_aircraft.csv",
        """
        UNWIND $batch AS row
        MATCH (m:MaintenanceEvent {event_id: row[':START_ID(MaintenanceEvent)']})
        MATCH (a:Aircraft {aircraft_id: row[':END_ID(Aircraft)']})
        MERGE (m)-[:AFFECTS_AIRCRAFT]->(a)
        """,
    ),
    (
        "HAS_REMOVAL",
        "rels_aircraft_removal.csv",
        """
        UNWIND $batch AS row
        MATCH (a:Aircraft {aircraft_id: row[':START_ID(Aircraft)']})
        MATCH (r:Removal {removal_id: row[':END_ID(RemovalEvent)']})
        MERGE (a)-[:HAS_REMOVAL]->(r)
        """,
    ),
    (
        "REMOVED_COMPONENT",
        "rels_component_removal.csv",
        """
        UNWIND $batch AS row
        MATCH (r:Removal {removal_id: row[':END_ID(RemovalEvent)']})
        MATCH (c:Component {component_id: row[':START_ID(Component)']})
        MERGE (r)-[:REMOVED_COMPONENT]->(c)
        """,
    ),
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_nodes(driver: Driver, data_dir: Path) -> None:
    """Load all 10 node types from CSV files."""
    for label, filename, query in _NODE_DEFINITIONS:
        print(f"Loading {label} nodes...")
        records = read_csv(data_dir, filename)
        _run_in_batches(driver, records, query)
        print(f"  [OK] Loaded {len(records)} {label} nodes.")


def load_relationships(driver: Driver, data_dir: Path) -> None:
    """Load all 13 relationship types from CSV files."""
    for rel_type, filename, query in _REL_DEFINITIONS:
        print(f"Loading {rel_type} relationships...")
        records = read_csv(data_dir, filename)
        _run_in_batches(driver, records, query)
        print(f"  [OK] Loaded {len(records)} {rel_type} relationships.")


def clear_database(driver: Driver) -> None:
    """Delete all nodes and relationships in batches."""
    print("Clearing database...")
    deleted_total = 0
    while True:
        records, _, _ = driver.execute_query(
            "MATCH (n) WITH n LIMIT 500 DETACH DELETE n RETURN count(*) AS deleted"
        )
        count = records[0]["deleted"]
        deleted_total += count
        if count > 0:
            print(f"  Deleted {deleted_total} nodes so far...", end="\r")
        if count == 0:
            break
    print(f"\n  [OK] Database cleared ({deleted_total} nodes deleted).")


def _get_label_counts(driver: Driver) -> dict[str, int]:
    records, _, _ = driver.execute_query(
        """
        MATCH (n)
        UNWIND labels(n) AS label
        RETURN label, count(n) AS count
        """
    )
    return {record["label"]: record["count"] for record in records}


def _get_relationship_counts(driver: Driver) -> dict[str, int]:
    records, _, _ = driver.execute_query(
        """
        MATCH ()-[r]->()
        RETURN type(r) AS rel_type, count(r) AS count
        """
    )
    return {record["rel_type"]: record["count"] for record in records}


def _print_count_section(title: str, counts: dict[str, int]) -> None:
    print(f"\n{title}:")
    for name, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        print(f"  {name}: {count:,}")
    print("  ---------------------")
    print(f"  Total: {sum(counts.values()):,}")


def _has_constraint(
    constraint_rows: list[dict[str, Any]], label: str, property_name: str
) -> bool:
    return any(
        row["type"] == "UNIQUENESS"
        and row["labelsOrTypes"] == [label]
        and row["properties"] == [property_name]
        for row in constraint_rows
    )


def _warn_or_fail(
    failures: list[str],
    warnings: list[str],
    condition: bool,
    message: str,
    *,
    strict: bool,
) -> None:
    if condition:
        return
    if strict:
        failures.append(message)
    else:
        warnings.append(message)


def _verify_vector_search(
    driver: Driver,
    *,
    has_chunk_embeddings: bool,
    has_vector_index: bool,
) -> tuple[bool, str]:
    if not has_chunk_embeddings:
        return False, "no chunk embeddings found"
    if not has_vector_index:
        return False, "missing maintenanceChunkEmbeddings index"

    try:
        records, _, _ = driver.execute_query("""
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
            WITH c.embedding AS embedding
            LIMIT 1
            CALL db.index.vector.queryNodes(
                'maintenanceChunkEmbeddings',
                1,
                embedding
            )
            YIELD node, score
            RETURN count(node) AS count, max(score) AS score
        """)
    except Neo4jError as exc:
        return False, str(exc)

    count = records[0]["count"]
    score = records[0]["score"]
    if count < 1:
        return False, "vector query returned no rows"
    return True, f"{count} result(s), best score={score:.4f}"


def verify(
    driver: Driver,
    *,
    expected_embedding_dimensions: int = 1536,
    strict: bool = False,
) -> bool:
    """Print comprehensive graph verification and return whether it passed."""
    failures: list[str] = []
    warnings: list[str] = []

    label_counts = _get_label_counts(driver)
    relationship_counts = _get_relationship_counts(driver)
    operational_counts = {
        label: label_counts.get(label, 0) for label in OPERATIONAL_LABELS
    }
    enrichment_counts = {
        label: label_counts.get(label, 0) for label in ENRICHMENT_LABELS
    }
    rel_counts = {
        rel_type: relationship_counts.get(rel_type, 0)
        for rel_type in RELATIONSHIP_TYPES
    }

    print()
    print("=" * 60)
    print("Verification")
    print("=" * 60)
    _print_count_section("Operational Node Counts", operational_counts)
    _print_count_section("Enrichment Node Counts", enrichment_counts)
    _print_count_section("Relationship Counts", rel_counts)

    for label in OPERATIONAL_LABELS:
        _warn_or_fail(
            failures,
            warnings,
            operational_counts[label] > 0,
            f"{label} has no nodes",
            strict=strict,
        )

    for rel_type in RELATIONSHIP_TYPES[:13]:
        _warn_or_fail(
            failures,
            warnings,
            rel_counts[rel_type] > 0,
            f"{rel_type} has no relationships",
            strict=strict,
        )

    for label in ("Document", "Chunk", "AircraftModel", "OperatingLimit"):
        _warn_or_fail(
            failures,
            warnings,
            enrichment_counts[label] > 0,
            f"{label} has no enrichment nodes",
            strict=strict,
        )

    if enrichment_counts["Chunk"] > 0:
        embedding_records, _, _ = driver.execute_query(
            """
            MATCH (c:Chunk)
            RETURN count(c) AS chunks,
                   count(c.embedding) AS with_embedding,
                   count(CASE WHEN c.embedding IS NULL THEN 1 END) AS missing_embedding,
                   collect(DISTINCT size(c.embedding)) AS dimensions
            """
        )
        embedding_row = embedding_records[0]
        bad_dim_records, _, _ = driver.execute_query(
            """
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
              AND size(c.embedding) <> $expected_dimensions
            RETURN count(c) AS count
            """,
            expected_dimensions=expected_embedding_dimensions,
        )
        bad_dimensions = bad_dim_records[0]["count"]
    else:
        embedding_row = {
            "chunks": 0,
            "with_embedding": 0,
            "missing_embedding": 0,
            "dimensions": [],
        }
        bad_dimensions = 0
    dimensions = [dim for dim in embedding_row["dimensions"] if dim is not None]

    print("\nEmbedding Integrity:")
    print(f"  Chunks: {embedding_row['chunks']:,}")
    print(f"  With embeddings: {embedding_row['with_embedding']:,}")
    print(f"  Missing embeddings: {embedding_row['missing_embedding']:,}")
    print(f"  Dimensions found: {dimensions}")
    print(f"  Wrong-dimension embeddings: {bad_dimensions:,}")

    _warn_or_fail(
        failures,
        warnings,
        embedding_row["with_embedding"] > 0,
        "no chunk embeddings found",
        strict=strict,
    )
    _warn_or_fail(
        failures,
        warnings,
        embedding_row["missing_embedding"] == 0,
        "some chunks are missing embeddings",
        strict=strict,
    )
    _warn_or_fail(
        failures,
        warnings,
        bad_dimensions == 0,
        f"some embeddings do not have {expected_embedding_dimensions} dimensions",
        strict=strict,
    )

    index_rows, _, _ = driver.execute_query("""
        SHOW INDEXES
        YIELD name, type, state, labelsOrTypes, properties
        RETURN name, type, state, labelsOrTypes, properties
    """)
    index_by_name = {row["name"]: row for row in index_rows}

    print("\nRequired Indexes:")
    for name in REQUIRED_INDEXES:
        row = index_by_name.get(name)
        if row is None:
            print(f"  [MISSING] {name}")
            _warn_or_fail(
                failures,
                warnings,
                False,
                f"missing index {name}",
                strict=strict,
            )
            continue
        print(f"  [OK] {name}: {row['type']} {row['state']}")
        _warn_or_fail(
            failures,
            warnings,
            row["state"] == "ONLINE",
            f"index {name} is {row['state']}",
            strict=strict,
        )

    constraint_rows, _, _ = driver.execute_query("""
        SHOW CONSTRAINTS
        YIELD name, type, labelsOrTypes, properties
        RETURN name, type, labelsOrTypes, properties
    """)
    constraint_dicts = [dict(row) for row in constraint_rows]

    print("\nRequired Constraints:")
    for label, property_name in REQUIRED_CONSTRAINTS:
        exists = _has_constraint(constraint_dicts, label, property_name)
        status = "[OK]" if exists else "[MISSING]"
        print(f"  {status} {label}.{property_name}")
        _warn_or_fail(
            failures,
            warnings,
            exists,
            f"missing uniqueness constraint {label}.{property_name}",
            strict=strict,
        )

    vector_ok, vector_detail = _verify_vector_search(
        driver,
        has_chunk_embeddings=embedding_row["with_embedding"] > 0,
        has_vector_index="maintenanceChunkEmbeddings" in index_by_name,
    )
    print("\nVector Search Smoke Test:")
    print(f"  {'[OK]' if vector_ok else '[FAIL]'} {vector_detail}")
    _warn_or_fail(
        failures,
        warnings,
        vector_ok,
        f"vector search smoke test failed: {vector_detail}",
        strict=strict,
    )

    cross_link_checks = [
        ("Document -> Aircraft", rel_counts["APPLIES_TO"]),
        ("AircraftModel -> Aircraft", rel_counts["DESCRIBES_MODEL"]),
        ("SystemReference -> System", rel_counts["DESCRIBES_SYSTEM"]),
        ("Sensor -> OperatingLimit", rel_counts["HAS_LIMIT"]),
    ]
    print("\nCross-Link Checks:")
    for label, count in cross_link_checks:
        print(f"  {label}: {count:,}")
        _warn_or_fail(
            failures,
            warnings,
            count > 0,
            f"{label} has no links",
            strict=strict,
        )

    orphan_queries = [
        (
            "Readings without Sensor",
            "MATCH (r:Reading) WHERE NOT (r)<-[:HAS_READING]-(:Sensor) "
            "RETURN count(r) AS count",
            {"Reading", "Sensor"},
            {"HAS_READING"},
        ),
        (
            "Flights without Aircraft",
            "MATCH (f:Flight) WHERE NOT (f)<-[:OPERATES_FLIGHT]-(:Aircraft) "
            "RETURN count(f) AS count",
            {"Flight", "Aircraft"},
            {"OPERATES_FLIGHT"},
        ),
        (
            "Components without System",
            "MATCH (c:Component) WHERE NOT (c)<-[:HAS_COMPONENT]-(:System) "
            "RETURN count(c) AS count",
            {"Component", "System"},
            {"HAS_COMPONENT"},
        ),
        (
            "Sensors without Readings",
            "MATCH (s:Sensor) WHERE NOT (s)-[:HAS_READING]->(:Reading) "
            "RETURN count(s) AS count",
            {"Sensor", "Reading"},
            {"HAS_READING"},
        ),
        (
            "Documents without Chunks",
            "MATCH (d:Document) WHERE NOT (:Chunk)-[:FROM_DOCUMENT]->(d) "
            "RETURN count(d) AS count",
            {"Document", "Chunk"},
            {"FROM_DOCUMENT"},
        ),
    ]
    print("\nData Quality Checks:")
    existing_labels = set(label_counts)
    existing_relationships = set(relationship_counts)
    for label, query, required_labels, required_relationships in orphan_queries:
        if required_labels.issubset(existing_labels) and required_relationships.issubset(
            existing_relationships
        ):
            records, _, _ = driver.execute_query(query)
            count = records[0]["count"]
        else:
            count = 0
        print(f"  {label}: {count:,}")
        _warn_or_fail(
            failures,
            warnings,
            count == 0,
            f"{label}: {count:,}",
            strict=strict,
        )

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  [WARN] {warning}")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"  [FAIL] {failure}")
        print("=" * 60)
        return False

    if warnings:
        print("\n[OK] Verification completed with warnings.")
    else:
        print("\n[OK] Verification passed.")
    print("=" * 60)
    return True
