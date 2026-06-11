"""CLI entry point for populate-aircraft-db."""

from __future__ import annotations

import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal

import typer
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from .config import Settings
from .generator.cli import generate as generate_cmd
from .generator.cli import validate as validate_csv_cmd
from .loader import clear_database, load_nodes, load_relationships, verify
from .schema import (
    create_constraints,
    create_embedding_indexes,
    create_extraction_constraints,
    create_fulltext_indexes,
    create_indexes,
    drop_extraction_constraints,
)

app = typer.Typer(
    name="populate-aircraft-db",
    help="Generate the Aircraft Digital Twin dataset and load it into a Neo4j Aura instance.",
    add_completion=False,
    pretty_exceptions_show_locals=False,
)

# Dataset generation commands (no Neo4j connection required)
app.command("generate")(generate_cmd)
app.command("validate-csv")(validate_csv_cmd)


def _fmt_elapsed(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


@contextmanager
def _connect(settings: Settings) -> Generator[Driver, None, None]:
    """Create a Neo4j driver, verify connectivity, and close on exit."""
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password.get_secret_value()),
    )
    try:
        driver.verify_connectivity()
    except (ServiceUnavailable, OSError) as exc:
        driver.close()
        print(f"[FAIL] Cannot connect to {settings.neo4j_uri}")
        print(f"       {exc}")
        print("\nCheck that the Neo4j instance is running and reachable.")
        sys.exit(1)
    try:
        print("[OK] Connected.\n")
        yield driver
    finally:
        driver.close()


# ---------------------------------------------------------------------------
# LLM credential resolution
# ---------------------------------------------------------------------------


@dataclass
class _LLMCredentials:
    provider: Literal["openai", "anthropic"]
    openai_key: str | None
    anthropic_key: str | None
    llm_model: str
    llm_max_tokens: int
    embedding_provider: Literal["bge", "openai"]
    embedding_model: str
    embedding_dims: int


def _resolve_llm_credentials(settings: Settings) -> _LLMCredentials:
    """Validate and resolve LLM credentials from settings. Raises typer.BadParameter on failure."""
    provider = settings.llm_provider
    embedding_provider = settings.embedding_provider
    openai_key = None
    anthropic_key = None

    # OpenAI is needed for extraction (llm_provider=openai) and/or embeddings
    # (embedding_provider=openai). The default BGE embedder runs locally and
    # needs no API key.
    if provider == "openai" or embedding_provider == "openai":
        if settings.openai_api_key is None:
            usage = (
                "extraction" if provider == "openai" else "embeddings"
            )
            raise typer.BadParameter(
                f"OPENAI_API_KEY is required for {usage} when using OpenAI. "
                "Set it in .env or as an env var."
            )
        openai_key = settings.openai_api_key.get_secret_value()

    if provider == "openai":
        llm_model = settings.openai_extraction_model
        llm_max_tokens = settings.openai_extraction_max_completion_tokens
    elif provider == "anthropic":
        if settings.anthropic_api_key is None:
            raise typer.BadParameter(
                "ANTHROPIC_API_KEY is required when using Anthropic. "
                "Set it in .env or as an env var."
            )
        anthropic_key = settings.anthropic_api_key.get_secret_value()
        llm_model = settings.anthropic_extraction_model
        llm_max_tokens = settings.anthropic_extraction_max_tokens
    else:
        raise typer.BadParameter(
            f"Unknown provider: {provider!r}. Use 'openai' or 'anthropic'."
        )

    return _LLMCredentials(
        provider=provider,
        openai_key=openai_key,
        anthropic_key=anthropic_key,
        llm_model=llm_model,
        llm_max_tokens=llm_max_tokens,
        embedding_provider=embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_dims=settings.embedding_dimensions,
    )


# ---------------------------------------------------------------------------
# Enrichment helper
# ---------------------------------------------------------------------------


def _run_enrich(driver: Driver, settings: Settings, creds: _LLMCredentials) -> None:
    """Run the enrichment pipeline: chunk, embed, extract entities, and link."""
    from .pipeline import (
        clear_enrichment_data,
        link_to_existing_graph,
        process_all_documents,
        validate_enrichment,
    )

    print("Clearing existing enrichment data (safe re-run)...")
    clear_enrichment_data(driver)
    print()

    print("Dropping extraction constraints for pipeline write phase...")
    drop_extraction_constraints(driver)
    print()

    if settings.enrich_sample_size:
        print(
            f"Running SimpleKGPipeline (LLM: {creds.provider}/{creds.llm_model}, "
            f"max_tokens={creds.llm_max_tokens}, "
            f"sample_size={settings.enrich_sample_size} chunks/doc)..."
        )
    else:
        print(
            f"Running SimpleKGPipeline (LLM: {creds.provider}/{creds.llm_model}, "
            f"max_tokens={creds.llm_max_tokens})..."
        )

    process_all_documents(
        driver,
        settings.document_dir,
        provider=creds.provider,
        openai_api_key=creds.openai_key,
        anthropic_api_key=creds.anthropic_key,
        llm_model=creds.llm_model,
        llm_max_tokens=creds.llm_max_tokens,
        embedding_provider=creds.embedding_provider,
        embedding_model=creds.embedding_model,
        embedding_dimensions=creds.embedding_dims,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        enrich_sample_size=settings.enrich_sample_size,
    )

    print("\nCreating extraction constraints (post entity-resolution)...")
    create_extraction_constraints(driver)

    print("\nCreating embedding indexes...")
    create_embedding_indexes(driver, creds.embedding_dims)

    print("\nLinking to existing graph...")
    link_to_existing_graph(driver)

    validate_enrichment(driver)


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


@app.command("setup")
def setup_cmd() -> None:
    """Load CSV data into Neo4j and run GraphRAG enrichment in a single pass."""
    settings = Settings()  # type: ignore[call-arg]

    # Validate LLM credentials early, before any Neo4j work.
    creds = _resolve_llm_credentials(settings)

    start = time.monotonic()

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        print("Creating constraints...")
        create_constraints(driver)
        print("\nCreating indexes...")
        create_indexes(driver)
        print("\nCreating fulltext indexes...")
        create_fulltext_indexes(driver)
        print()

        load_nodes(driver, settings.data_dir)
        print()
        load_relationships(driver, settings.data_dir)
        print()

        try:
            _run_enrich(driver, settings, creds)
        except Exception as exc:
            print(f"\n[FAIL] Enrichment failed: {exc}")
            print("CSV data was loaded successfully. Fix the issue and re-run:")
            print("  uv run populate-aircraft-db setup")
            raise typer.Exit(code=1) from exc

        verify(
            driver,
            expected_embedding_dimensions=settings.embedding_dimensions,
        )

    elapsed = time.monotonic() - start
    print(f"\nDone in {_fmt_elapsed(elapsed)}.")


@app.command("verify")
def verify_cmd(
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit with a nonzero status when verification warnings are found.",
    ),
) -> None:
    """Run comprehensive graph verification (read-only)."""
    settings = Settings()  # type: ignore[call-arg]

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        passed = verify(
            driver,
            expected_embedding_dimensions=settings.embedding_dimensions,
            strict=strict,
        )

    if strict and not passed:
        raise typer.Exit(code=1)


@app.command("clean")
def clean_cmd() -> None:
    """Clear all nodes and relationships from the database."""
    settings = Settings()  # type: ignore[call-arg]

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        clear_database(driver)

    print("\nDone.")


@app.command("clean-enrichment")
def clean_enrichment_cmd() -> None:
    """Clear enrichment data (Documents, Chunks, extracted entities) while preserving the operational graph."""
    from .pipeline import clear_enrichment_data

    settings = Settings()  # type: ignore[call-arg]

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        clear_enrichment_data(driver)

    print("\nDone.")


@app.command("load-operational")
def load_operational_cmd() -> None:
    """Load only CSV operational data and relink existing enrichment."""
    from .pipeline import link_to_existing_graph, validate_enrichment

    settings = Settings()  # type: ignore[call-arg]

    start = time.monotonic()

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        print("Creating constraints...")
        create_constraints(driver)
        print("\nCreating indexes...")
        create_indexes(driver)
        print("\nCreating fulltext indexes...")
        create_fulltext_indexes(driver)
        print()

        load_nodes(driver, settings.data_dir)
        print()
        load_relationships(driver, settings.data_dir)
        print()

        print("Linking existing enrichment to operational graph...")
        link_to_existing_graph(driver)

        validate_enrichment(driver)

    elapsed = time.monotonic() - start
    print(f"\nDone in {_fmt_elapsed(elapsed)}.")


@app.command("enrich")
def enrich_cmd() -> None:
    """Run GraphRAG enrichment against an already-loaded operational graph."""
    settings = Settings()  # type: ignore[call-arg]
    creds = _resolve_llm_credentials(settings)

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        _run_enrich(driver, settings, creds)

    print("\nDone.")


@app.command("debug-extract")
def debug_extract_cmd(
    document: str = typer.Option(
        "MAINTENANCE_A321neo.md",
        "--document",
        "-d",
        help="Maintenance manual filename in DOCUMENT_DIR.",
    ),
    chunks: str = typer.Option(
        "3,5,6,7,9,10,11,12,13,15,16",
        "--chunks",
        "-c",
        help="Comma-separated chunk indexes to send to the extractor.",
    ),
) -> None:
    """Validate extractor output for selected chunks without writing to Neo4j."""
    from .pipeline import debug_extract_chunks

    settings = Settings()  # type: ignore[call-arg]
    creds = _resolve_llm_credentials(settings)
    try:
        chunk_indexes = [int(index.strip()) for index in chunks.split(",") if index.strip()]
    except ValueError as exc:
        raise typer.BadParameter("--chunks must be a comma-separated list of integers") from exc

    try:
        passed = debug_extract_chunks(
            settings.document_dir,
            filename=document,
            chunk_indexes=chunk_indexes,
            provider=creds.provider,
            openai_api_key=creds.openai_key,
            anthropic_api_key=creds.anthropic_key,
            llm_model=creds.llm_model,
            llm_max_tokens=creds.llm_max_tokens,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    except ImportError as exc:
        print(f"[FAIL] {exc}")
        if creds.provider == "anthropic":
            print("Install Anthropic support with: uv sync --extra anthropic")
        raise typer.Exit(code=1) from exc
    if not passed:
        raise typer.Exit(code=1)


@app.command("samples")
def samples_cmd() -> None:
    """Run sample queries showcasing the knowledge graph (read-only)."""
    from .samples import run_all_samples

    settings = Settings()  # type: ignore[call-arg]

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        run_all_samples(driver, sample_size=settings.sample_size)


@app.command("agent-samples")
def agent_samples_cmd() -> None:
    """Simulate the Neo4j Aura Agent: send natural language questions to the LLM,
    generate Cypher or vector searches, execute them, and display results."""
    from .agent_samples import run_agent_samples

    settings = Settings()  # type: ignore[call-arg]
    creds = _resolve_llm_credentials(settings)

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        run_agent_samples(
            driver,
            provider=creds.provider,
            openai_key=creds.openai_key,
            anthropic_key=creds.anthropic_key,
            llm_model=creds.llm_model,
            embedding_provider=creds.embedding_provider,
            embedding_model=creds.embedding_model,
            embedding_dimensions=creds.embedding_dims,
            sample_size=settings.sample_size,
        )


if __name__ == "__main__":
    app()
