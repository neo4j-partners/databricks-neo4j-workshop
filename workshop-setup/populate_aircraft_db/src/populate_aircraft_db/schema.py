"""Constraint and index definitions for the Aircraft Digital Twin graph."""

from __future__ import annotations

from neo4j import Driver

# (label, property) pairs — one uniqueness constraint each.
CONSTRAINTS: list[tuple[str, str]] = [
    ("Aircraft", "aircraft_id"),
    ("System", "system_id"),
    ("Component", "component_id"),
    ("Sensor", "sensor_id"),
    ("Airport", "airport_id"),
    ("Flight", "flight_id"),
    ("Delay", "delay_id"),
    ("MaintenanceEvent", "event_id"),
    ("Removal", "removal_id"),
    ("Document", "documentId"),
    # OperatingLimit means the 20 canonical rows of nodes_operating_limits.csv
    # and nothing else, so it is keyed on the limit_id that CSV assigns. This is
    # the same constraint Lab 2's notebook creates. It is absent from
    # EXTRACTION_CONSTRAINTS below and therefore never dropped: extraction now
    # writes ExtractedLimit, so it cannot collide with these rows and the
    # constraint can stay up for the whole run.
    ("OperatingLimit", "limit_id"),
]

# (label, property) pairs — property indexes for common lookups.
INDEXES: list[tuple[str, str]] = [
    ("MaintenanceEvent", "severity"),
    ("Flight", "aircraft_id"),
    ("Removal", "aircraft_id"),
]

# (index_name, label, [properties]) — fulltext indexes for sample queries.
FULLTEXT_INDEXES: list[tuple[str, str, list[str]]] = [
    ("maintenance_search", "MaintenanceEvent", ["fault", "corrective_action"]),
    ("delay_search", "Delay", ["cause"]),
    ("component_search", "Component", ["name", "type"]),
    ("document_search", "Document", ["title", "aircraftType"]),
]

# Constraints for entity types created by the enrichment phase of `setup`.
# SimpleKGPipeline deduplicates on the `name` property. Limits extracted from
# the manuals land on ExtractedLimit, which keeps them clear of the canonical
# OperatingLimit rows above.
EXTRACTION_CONSTRAINTS: list[tuple[str, str]] = [
    ("AircraftModel", "name"),
    ("SystemReference", "name"),
    ("ComponentReference", "name"),
    ("Fault", "name"),
    ("MaintenanceProcedure", "name"),
    ("ExtractedLimit", "name"),
]


def _quote_identifier(identifier: str) -> str:
    """Quote a Neo4j schema identifier."""
    return f"`{identifier.replace('`', '``')}`"


def create_constraints(driver: Driver, database: str) -> None:
    """Create uniqueness constraints (idempotent)."""
    for label, prop in CONSTRAINTS:
        driver.execute_query(
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE",
            database_=database,
        )
        print(f"  [OK] Constraint: {label}.{prop}")


def create_indexes(driver: Driver, database: str) -> None:
    """Create property indexes (idempotent)."""
    for label, prop in INDEXES:
        index_name = f"idx_{label.lower()}_{prop.lower()}"
        driver.execute_query(
            f"CREATE INDEX {index_name} IF NOT EXISTS FOR (n:{label}) ON (n.{prop})",
            database_=database,
        )
        print(f"  [OK] Index: {label}.{prop}")


def create_fulltext_indexes(driver: Driver, database: str) -> None:
    """Create fulltext indexes for sample demo queries (idempotent)."""
    for name, label, props in FULLTEXT_INDEXES:
        props_clause = ", ".join(f"n.{p}" for p in props)
        driver.execute_query(
            f"CREATE FULLTEXT INDEX {name} IF NOT EXISTS "
            f"FOR (n:{label}) ON EACH [{props_clause}]",
            database_=database,
        )
        print(f"  [OK] Fulltext index: {name} on {label}({', '.join(props)})")


def create_extraction_constraints(driver: Driver, database: str) -> None:
    """Create uniqueness constraints for extracted entity types (idempotent)."""
    for label, prop in EXTRACTION_CONSTRAINTS:
        driver.execute_query(
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE",
            database_=database,
        )
        print(f"  [OK] Constraint: {label}.{prop}")


def drop_extraction_constraints(driver: Driver, database: str) -> None:
    """Drop extracted-entity uniqueness constraints before SimpleKGPipeline runs.

    Still required. The pipeline's writer issues `CREATE` for every entity
    mention it finds, one node per mention, and collapses the duplicates only
    afterward during entity resolution. A `name` uniqueness constraint would
    therefore fail partway through the write, before the duplicates are gone.

    EXTRACTION_CONSTRAINTS no longer lists OperatingLimit, so this only touches
    labels the pipeline actually writes. The canonical OperatingLimit constraint
    on `limit_id` stays up for the whole run. That is a real guarantee rather
    than an accident of the extracted nodes lacking `limit_id`: a node property
    uniqueness constraint is not enforced against nodes that lack the property,
    so leaving the constraint up would not have caught a collision on `name`.
    Keeping the two populations under separate labels is what settles it.
    """
    for label, prop in EXTRACTION_CONSTRAINTS:
        records, _, _ = driver.execute_query(
            """
            SHOW CONSTRAINTS
            YIELD name, type, labelsOrTypes, properties
            WHERE type = 'UNIQUENESS'
              AND labelsOrTypes = [$label]
              AND properties = [$property]
            RETURN name
            """,
            label=label,
            property=prop,
            database_=database,
        )
        for record in records:
            driver.execute_query(
                f"DROP CONSTRAINT {_quote_identifier(record['name'])} IF EXISTS",
                database_=database,
            )
            print(f"  [OK] Dropped constraint: {label}.{prop}")


def create_embedding_indexes(driver: Driver, database: str, dimensions: int) -> None:
    """Create vector and fulltext indexes for Chunk embeddings (idempotent).

    Imports neo4j_graphrag lazily so that other commands don't require it.
    """
    from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index

    create_vector_index(
        driver,
        name="maintenanceChunkEmbeddings",
        label="Chunk",
        embedding_property="embedding",
        dimensions=dimensions,
        similarity_fn="cosine",
        neo4j_database=database,
    )
    print("  [OK] Vector index: maintenanceChunkEmbeddings")

    create_fulltext_index(
        driver,
        name="maintenanceChunkText",
        label="Chunk",
        node_properties=["text"],
        neo4j_database=database,
    )
    print("  [OK] Fulltext index: maintenanceChunkText")


def build_extraction_schema():
    """Build a GraphSchema for SimpleKGPipeline entity extraction.

    Extracts model-level manual knowledge into labels that do not collide with
    the operational graph loaded from CSV.  Entity names are qualified with the
    aircraft type where appropriate so entity resolution stays model-scoped.
    """
    from neo4j_graphrag.experimental.components.schema import (
        ConstraintType,
        GraphConstraintType,
        GraphSchema,
        NodeType,
        Pattern,
        PropertyType,
        RelationshipType,
    )

    node_types = [
        NodeType(
            label="AircraftModel",
            description="An aircraft model covered by a maintenance manual.",
            properties=[
                PropertyType(
                    name="name",
                    type="STRING",
                    description="Aircraft model, e.g. A320-200, A321neo, B737-800.",
                ),
                PropertyType(
                    name="manufacturer",
                    type="STRING",
                    description="Aircraft manufacturer when stated.",
                ),
            ],
            additional_properties=False,
        ),
        NodeType(
            label="SystemReference",
            description="A manual-described aircraft system or subsystem.",
            properties=[
                PropertyType(
                    name="name",
                    type="STRING",
                    description="System name qualified by aircraft type.",
                ),
                PropertyType(
                    name="systemType",
                    type="STRING",
                    description="System category, e.g. Engine, Avionics, Hydraulics.",
                ),
                PropertyType(
                    name="aircraftType",
                    type="STRING",
                    description="Aircraft model from document context.",
                ),
            ],
            additional_properties=False,
        ),
        NodeType(
            label="ComponentReference",
            description="A component, part, sensor, or LRU described in a manual.",
            properties=[
                PropertyType(
                    name="name",
                    type="STRING",
                    description="Component name qualified by aircraft type.",
                ),
                PropertyType(
                    name="componentType",
                    type="STRING",
                    description="Generic component or part type.",
                ),
                PropertyType(
                    name="partNumber",
                    type="STRING",
                    description="Part number when explicitly stated.",
                ),
                PropertyType(
                    name="aircraftType",
                    type="STRING",
                    description="Aircraft model from document context.",
                ),
            ],
            additional_properties=False,
        ),
        NodeType(
            label="Fault",
            description="A fault, warning, symptom, or failure condition.",
            properties=[
                PropertyType(
                    name="name",
                    type="STRING",
                    description="Fault name qualified by aircraft type.",
                ),
                PropertyType(
                    name="faultCode",
                    type="STRING",
                    description="Fault or message code when explicitly stated.",
                ),
                PropertyType(
                    name="severity",
                    type="STRING",
                    description="Severity or urgency when stated.",
                ),
                PropertyType(
                    name="aircraftType",
                    type="STRING",
                    description="Aircraft model from document context.",
                ),
            ],
            additional_properties=False,
        ),
        NodeType(
            label="MaintenanceProcedure",
            description="A maintenance, inspection, removal, or troubleshooting action.",
            properties=[
                PropertyType(
                    name="name",
                    type="STRING",
                    description="Procedure name qualified by aircraft type.",
                ),
                PropertyType(
                    name="procedureType",
                    type="STRING",
                    description=(
                        "Inspection, troubleshooting, removal, replacement, "
                        "test, or reset."
                    ),
                ),
                PropertyType(
                    name="interval",
                    type="STRING",
                    description="Maintenance interval when explicitly stated.",
                ),
                PropertyType(
                    name="aircraftType",
                    type="STRING",
                    description="Aircraft model from document context.",
                ),
            ],
            additional_properties=False,
        ),
        NodeType(
            label="ExtractedLimit",
            description=(
                "An operating parameter limit stated in a maintenance manual. "
                "Distinct from the canonical OperatingLimit rows loaded from CSV."
            ),
            properties=[
                PropertyType(
                    name="name",
                    type="STRING",
                    description=(
                        "Unique identifier combining parameter and aircraft type, "
                        "e.g. 'EGT - A320-200', 'N1Speed - B737-800'. "
                        "Always append ' - <aircraft type>'."
                    ),
                ),
                PropertyType(
                    name="parameterName",
                    type="STRING",
                    description=(
                        "Base parameter name matching sensor type, e.g. EGT, "
                        "Vibration, N1Speed, FuelFlow"
                    ),
                ),
                PropertyType(name="unit", type="STRING", description="Unit of measurement"),
                PropertyType(
                    name="regime",
                    type="STRING",
                    description="Operating regime, e.g. takeoff, cruise",
                ),
                PropertyType(name="minValue", type="STRING", description="Minimum value"),
                PropertyType(name="maxValue", type="STRING", description="Maximum value"),
                PropertyType(
                    name="aircraftType",
                    type="STRING",
                    description="Aircraft type, e.g. A320-200",
                ),
            ],
            additional_properties=False,
        ),
    ]
    relationship_types = [
        RelationshipType(label="HAS_SYSTEM"),
        RelationshipType(label="HAS_COMPONENT"),
        RelationshipType(label="HAS_FAULT"),
        RelationshipType(label="HAS_PROCEDURE"),
        RelationshipType(label="HAS_LIMIT"),
        RelationshipType(label="CORRECTED_BY"),
    ]
    patterns = [
        Pattern(
            source="AircraftModel",
            relationship="HAS_SYSTEM",
            target="SystemReference",
        ),
        Pattern(
            source="SystemReference",
            relationship="HAS_COMPONENT",
            target="ComponentReference",
        ),
        Pattern(source="SystemReference", relationship="HAS_FAULT", target="Fault"),
        Pattern(source="ComponentReference", relationship="HAS_FAULT", target="Fault"),
        Pattern(
            source="SystemReference",
            relationship="HAS_PROCEDURE",
            target="MaintenanceProcedure",
        ),
        Pattern(
            source="ComponentReference",
            relationship="HAS_PROCEDURE",
            target="MaintenanceProcedure",
        ),
        Pattern(source="Fault", relationship="CORRECTED_BY", target="MaintenanceProcedure"),
        Pattern(source="SystemReference", relationship="HAS_LIMIT", target="ExtractedLimit"),
        Pattern(
            source="ComponentReference",
            relationship="HAS_LIMIT",
            target="ExtractedLimit",
        ),
    ]
    constraints = [
        ConstraintType(
            type=GraphConstraintType.EXISTENCE,
            node_type=label,
            property_names=("name",),
            relationship_type=None,
        )
        for label in (
            "AircraftModel",
            "SystemReference",
            "ComponentReference",
            "Fault",
            "MaintenanceProcedure",
            "ExtractedLimit",
        )
    ]

    return GraphSchema(
        node_types=tuple(node_types),
        relationship_types=tuple(relationship_types),
        patterns=tuple(patterns),
        constraints=tuple(constraints),
        additional_node_types=False,
        additional_relationship_types=False,
        additional_patterns=False,
    )
