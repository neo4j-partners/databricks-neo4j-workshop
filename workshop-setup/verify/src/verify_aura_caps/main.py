"""Measure whether an AuraDB Free instance tolerates the Lab 3 plus Lab 6 schema.

Lab 6's memory library creates 33 indexes and 12 constraints on first connect, on
top of whatever Lab 3 already left behind. If AuraDB Free caps below the combined
total, Lab 6 fails for every participant in the room at once. Nothing in the
repository measures that, and a multi-database Professional instance is not
evidence.

Two commands, in the order you should run them:

    check   Read-only. Counts what the instance already carries and says whether
            Lab 6's 33 + 12 would fit under a stated ceiling. Safe anywhere.

    probe   Creates Lab 6's shape against a throwaway label, one object at a
            time, until something fails or the whole set lands. Drops every
            object it created, whether it succeeded or not. Point it at a
            fresh Free instance, never at one carrying a participant's graph.

Usage:
    cd workshop-setup/verify
    uv sync
    uv run verify-aura-caps check
    uv run verify-aura-caps probe
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

import typer
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.table import Table

# workshop-setup/.env is three levels up from this file (src/verify_aura_caps/main.py)
_ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"

# What Lab_6_Agent_Memory/memory.py installs on first connect. Sourced from
# memory.py:599 and Lab_6_Agent_Memory/README.md:361.
LAB6_INDEXES = 33
LAB6_CONSTRAINTS = 12
LAB6_VECTOR_INDEXES = 6

# The throwaway label every probe object hangs off. Nothing in the workshop
# graph uses it, so a probe cannot collide with participant data.
PROBE_LABEL = "__AuraCapProbe"
PROBE_PREFIX = "aura_cap_probe_"

# Dimension of databricks-bge-large-en, the model Lab 3 and Lab 6 both embed with.
EMBEDDING_DIMENSIONS = 1024

app = typer.Typer(add_completion=False, help=__doc__)
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


@dataclass
class Inventory:
    """What an instance carries right now."""

    database: str
    indexes: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    vector_indexes: list[str] = field(default_factory=list)


def home_database(driver: Driver) -> str:
    """Return the instance's home database name.

    Never assume "neo4j". An Aura instance can carry a differently named home
    database, and both `SHOW DATABASES` and `verify_connectivity` succeed on one
    where the first real query against "neo4j" fails.
    """
    records, _, _ = driver.execute_query("SHOW DATABASES YIELD name, home, type")
    for record in records:
        if record["home"] and record["type"] != "system":
            return record["name"]
    for record in records:
        if record["type"] != "system":
            return record["name"]
    raise RuntimeError("SHOW DATABASES returned no non-system database")


def read_inventory(driver: Driver, database: str) -> Inventory:
    """Count indexes and constraints without changing anything."""
    inventory = Inventory(database=database)

    records, _, _ = driver.execute_query(
        "SHOW INDEXES YIELD name, type", database_=database
    )
    for record in records:
        inventory.indexes.append(record["name"])
        if record["type"] == "VECTOR":
            inventory.vector_indexes.append(record["name"])

    records, _, _ = driver.execute_query("SHOW CONSTRAINTS YIELD name", database_=database)
    inventory.constraints = [record["name"] for record in records]

    return inventory


def _print_inventory(inventory: Inventory) -> None:
    table = Table(title=f"Current schema on `{inventory.database}`")
    table.add_column("Object", style="cyan")
    table.add_column("Count", justify="right")
    table.add_row("Indexes (all types)", str(len(inventory.indexes)))
    table.add_row("  of which vector", str(len(inventory.vector_indexes)))
    table.add_row("Constraints", str(len(inventory.constraints)))
    console.print(table)


@app.command()
def check(
    ceiling_indexes: int = typer.Option(
        0,
        "--ceiling-indexes",
        help="Documented index cap to test against. 0 means unknown, so only report.",
    ),
    ceiling_constraints: int = typer.Option(
        0,
        "--ceiling-constraints",
        help="Documented constraint cap to test against. 0 means unknown.",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="List every object by name."),
) -> None:
    """Report what the instance carries and what Lab 6 would add. Read-only."""
    settings = Settings()
    with GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_username, settings.neo4j_password)
    ) as driver:
        driver.verify_connectivity()
        database = home_database(driver)
        inventory = read_inventory(driver, database)

    _print_inventory(inventory)

    if verbose:
        for title, names in (
            ("Indexes", inventory.indexes),
            ("Constraints", inventory.constraints),
        ):
            console.print(f"\n[bold]{title}[/bold]")
            for name in sorted(names):
                console.print(f"  {name}")

    projected_indexes = len(inventory.indexes) + LAB6_INDEXES
    projected_constraints = len(inventory.constraints) + LAB6_CONSTRAINTS

    console.print(
        f"\nAfter Lab 6: [bold]{projected_indexes}[/bold] indexes, "
        f"[bold]{projected_constraints}[/bold] constraints "
        f"(Lab 6 adds {LAB6_INDEXES} and {LAB6_CONSTRAINTS})."
    )

    if not ceiling_indexes and not ceiling_constraints:
        console.print(
            "\n[yellow]No ceiling given, so this is a count and not a verdict.[/yellow] "
            "Run `probe` against a fresh Free instance to measure the real limit."
        )
        return

    over = False
    if ceiling_indexes and projected_indexes > ceiling_indexes:
        console.print(
            f"[red]Over the index ceiling:[/red] {projected_indexes} > {ceiling_indexes}"
        )
        over = True
    if ceiling_constraints and projected_constraints > ceiling_constraints:
        console.print(
            f"[red]Over the constraint ceiling:[/red] "
            f"{projected_constraints} > {ceiling_constraints}"
        )
        over = True

    if over:
        raise typer.Exit(code=1)
    console.print("[green]Fits under the stated ceilings.[/green]")


def _probe_statements() -> list[tuple[str, str, str]]:
    """Build Lab 6's shape as (kind, name, cypher), in creation order.

    Constraints first, because a uniqueness constraint creates its own backing
    index and so is the object most likely to trip a cap. Vector indexes last,
    because they are the ones Free is most likely to limit separately.
    """
    statements: list[tuple[str, str, str]] = []

    for i in range(LAB6_CONSTRAINTS):
        name = f"{PROBE_PREFIX}constraint_{i:02d}"
        statements.append(
            (
                "constraint",
                name,
                f"CREATE CONSTRAINT {name} IF NOT EXISTS "
                f"FOR (n:{PROBE_LABEL}) REQUIRE n.c{i:02d} IS UNIQUE",
            )
        )

    range_count = LAB6_INDEXES - LAB6_VECTOR_INDEXES
    for i in range(range_count):
        name = f"{PROBE_PREFIX}range_{i:02d}"
        statements.append(
            (
                "index",
                name,
                f"CREATE INDEX {name} IF NOT EXISTS FOR (n:{PROBE_LABEL}) ON (n.r{i:02d})",
            )
        )

    for i in range(LAB6_VECTOR_INDEXES):
        name = f"{PROBE_PREFIX}vector_{i:02d}"
        statements.append(
            (
                "vector index",
                name,
                f"CREATE VECTOR INDEX {name} IF NOT EXISTS "
                f"FOR (n:{PROBE_LABEL}) ON (n.v{i:02d}) "
                f"OPTIONS {{indexConfig: {{"
                f"`vector.dimensions`: {EMBEDDING_DIMENSIONS}, "
                f"`vector.similarity_function`: 'cosine'}}}}",
            )
        )

    return statements


def _drop_probe_objects(driver: Driver, database: str) -> int:
    """Drop every object this script created. Safe to call twice."""
    dropped = 0

    records, _, _ = driver.execute_query("SHOW CONSTRAINTS YIELD name", database_=database)
    for record in records:
        if record["name"].startswith(PROBE_PREFIX):
            driver.execute_query(f"DROP CONSTRAINT {record['name']}", database_=database)
            dropped += 1

    records, _, _ = driver.execute_query("SHOW INDEXES YIELD name", database_=database)
    for record in records:
        if record["name"].startswith(PROBE_PREFIX):
            driver.execute_query(f"DROP INDEX {record['name']}", database_=database)
            dropped += 1

    return dropped


@app.command()
def probe(
    yes: bool = typer.Option(
        False, "--yes", help="Skip the confirmation. Required for non-interactive runs."
    ),
) -> None:
    """Create Lab 6's shape one object at a time, then roll every one of them back.

    Point this at a fresh AuraDB Free instance. It writes schema, so it is not
    safe against an instance carrying a participant's graph.
    """
    settings = Settings()

    console.print(
        f"[yellow]This creates up to {LAB6_CONSTRAINTS} constraints and "
        f"{LAB6_INDEXES} indexes on `{settings.neo4j_uri}` and then drops them.[/yellow]"
    )
    if not yes and not typer.confirm("Continue?"):
        raise typer.Exit(code=1)

    with GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_username, settings.neo4j_password)
    ) as driver:
        driver.verify_connectivity()
        database = home_database(driver)
        before = read_inventory(driver, database)
        _print_inventory(before)

        created = 0
        failure: tuple[str, str, Neo4jError] | None = None
        try:
            for kind, name, cypher in _probe_statements():
                try:
                    driver.execute_query(cypher, database_=database)
                except Neo4jError as exc:
                    failure = (kind, name, exc)
                    break
                created += 1
                console.print(f"  [green]ok[/green] {kind} {name}")
        finally:
            dropped = _drop_probe_objects(driver, database)
            after = read_inventory(driver, database)

    console.print(f"\nCreated {created}, dropped {dropped} on the way out.")

    if after.indexes != before.indexes or after.constraints != before.constraints:
        console.print(
            "[red]Rollback did not return the instance to its starting schema.[/red] "
            f"Look for objects named `{PROBE_PREFIX}*` and drop them by hand."
        )
        raise typer.Exit(code=2)

    if failure is None:
        console.print(
            f"\n[green]PASS.[/green] All {LAB6_CONSTRAINTS} constraints and "
            f"{LAB6_INDEXES} indexes landed on top of "
            f"{len(before.indexes)} existing indexes and "
            f"{len(before.constraints)} existing constraints. "
            "Lab 6 fits on this tier."
        )
        return

    kind, name, exc = failure
    console.print(
        f"\n[red]NO-GO.[/red] Failed creating {kind} `{name}` after {created} objects.\n"
        f"  {exc.code}: {exc.message}"
    )
    raise typer.Exit(code=1)


def main() -> None:
    try:
        app()
    except Neo4jError as exc:
        console.print(f"[red]Neo4j error:[/red] {exc.code}: {exc.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
