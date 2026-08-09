"""CLI entry point for populate-aircraft-db."""

from __future__ import annotations

import os
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
from .loader import (
    clear_database,
    load_nodes,
    load_operating_limits,
    load_relationships,
    verify,
)
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
    embedding_model: str
    embedding_dims: int


def _export_databricks_env(settings: Settings) -> None:
    """Publish Databricks credentials from .env into the process environment.

    pydantic-settings reads .env into a Settings object and stops there, but the
    MLflow deployments client the embedder uses only reads os.environ. Without
    this bridge a host and token sitting in .env look configured and are not.
    Only keys the user actually set are written, so an ambient environment (a
    Databricks notebook, an already-exported token) still wins when .env is
    silent.
    """
    if settings.databricks_host:
        os.environ["DATABRICKS_HOST"] = settings.databricks_host
    if settings.databricks_token:
        os.environ["DATABRICKS_TOKEN"] = settings.databricks_token.get_secret_value()
    if settings.databricks_config_profile:
        os.environ["DATABRICKS_CONFIG_PROFILE"] = settings.databricks_config_profile


def _resolve_llm_credentials(
    settings: Settings,
    *,
    skip_extraction: bool = False,
) -> _LLMCredentials:
    """Validate and resolve LLM credentials from settings. Raises typer.BadParameter on failure.

    With *skip_extraction* set, no LLM runs, so no LLM key is required. That is
    the point of the flag: the catch-up path needs chunks, embeddings, and an
    index, and demanding an OpenAI or Anthropic key to produce them would put an
    external account on the critical path of a lab.
    """
    provider = settings.llm_provider
    openai_key = None
    anthropic_key = None

    # OpenAI is needed for extraction only (llm_provider=openai). Embeddings
    # never need it: the Databricks embedder authenticates through the
    # workspace.
    if provider == "openai" and not skip_extraction:
        if settings.openai_api_key is None:
            raise typer.BadParameter(
                "OPENAI_API_KEY is required for extraction when using OpenAI. "
                "Set it in .env or as an env var."
            )
        openai_key = settings.openai_api_key.get_secret_value()

    if provider == "openai":
        llm_model = settings.openai_extraction_model
        llm_max_tokens = settings.openai_extraction_max_completion_tokens
    elif provider == "anthropic":
        if settings.anthropic_api_key is None and not skip_extraction:
            raise typer.BadParameter(
                "ANTHROPIC_API_KEY is required when using Anthropic. "
                "Set it in .env or as an env var."
            )
        if settings.anthropic_api_key is not None:
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
        embedding_model=settings.embedding_model,
        embedding_dims=settings.embedding_dimensions,
    )


# ---------------------------------------------------------------------------
# Enrichment helper
# ---------------------------------------------------------------------------


def _run_enrich(
    driver: Driver,
    settings: Settings,
    creds: _LLMCredentials,
    *,
    skip_extraction: bool = False,
) -> None:
    """Run the enrichment pipeline: chunk, embed, extract entities, and link.

    With *skip_extraction* the entity half is left out and only the Document,
    Chunk, embedding, and index half runs. The extraction constraints are left
    alone too, since nothing will be written that needs resolving.
    """
    from .pipeline import (
        clear_enrichment_data,
        link_to_existing_graph,
        process_all_documents,
        process_all_documents_lexical_only,
        validate_enrichment,
    )

    print("Clearing existing enrichment data (safe re-run)...")
    clear_enrichment_data(driver, settings.neo4j_database)
    print()

    sample_note = (
        f", sample_size={settings.enrich_sample_size} chunks/doc"
        if settings.enrich_sample_size
        else ""
    )

    if skip_extraction:
        print(
            f"Chunking and embedding, no entity extraction "
            f"(embeddings: {creds.embedding_model}{sample_note})..."
        )
        process_all_documents_lexical_only(
            driver,
            settings.neo4j_database,
            settings.document_dir,
            embedding_model=creds.embedding_model,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            enrich_sample_size=settings.enrich_sample_size,
        )
    else:
        print("Dropping extraction constraints for pipeline write phase...")
        drop_extraction_constraints(driver, settings.neo4j_database)
        print()

        print(
            f"Running SimpleKGPipeline (LLM: {creds.provider}/{creds.llm_model}, "
            f"max_tokens={creds.llm_max_tokens}{sample_note})..."
        )

        process_all_documents(
            driver,
            settings.neo4j_database,
            settings.document_dir,
            provider=creds.provider,
            openai_api_key=creds.openai_key,
            anthropic_api_key=creds.anthropic_key,
            llm_model=creds.llm_model,
            llm_max_tokens=creds.llm_max_tokens,
            embedding_model=creds.embedding_model,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            enrich_sample_size=settings.enrich_sample_size,
        )

        print("\nCreating extraction constraints (post entity-resolution)...")
        create_extraction_constraints(driver, settings.neo4j_database)

    print("\nCreating embedding indexes...")
    create_embedding_indexes(driver, settings.neo4j_database, creds.embedding_dims)

    print()
    load_operating_limits(driver, settings.neo4j_database, settings.data_dir)

    print("\nLinking to existing graph...")
    link_to_existing_graph(driver, settings.neo4j_database)

    validate_enrichment(
        driver, settings.neo4j_database, skip_extraction=skip_extraction
    )


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


_SKIP_EXTRACTION_HELP = (
    "Chunk and embed the manuals but skip LLM entity extraction. Needs no "
    "OpenAI or Anthropic key. Leaves out ExtractedLimit and the other extracted "
    "entities. The canonical OperatingLimit nodes load from CSV either way, so "
    "Lab 3 notebook 02's operating-limit retriever still has a chain to "
    "traverse. Everything vector search needs is still written."
)


@app.command("setup")
def setup_cmd(
    skip_extraction: bool = typer.Option(
        False,
        "--skip-extraction",
        help=_SKIP_EXTRACTION_HELP,
    ),
) -> None:
    """Load CSV data into Neo4j and run GraphRAG enrichment in a single pass."""
    settings = Settings()  # type: ignore[call-arg]
    _export_databricks_env(settings)

    # Validate LLM credentials early, before any Neo4j work.
    creds = _resolve_llm_credentials(settings, skip_extraction=skip_extraction)

    start = time.monotonic()

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        print("Creating constraints...")
        create_constraints(driver, settings.neo4j_database)
        print("\nCreating indexes...")
        create_indexes(driver, settings.neo4j_database)
        print("\nCreating fulltext indexes...")
        create_fulltext_indexes(driver, settings.neo4j_database)
        print()

        load_nodes(driver, settings.neo4j_database, settings.data_dir)
        print()
        load_relationships(driver, settings.neo4j_database, settings.data_dir)
        print()

        try:
            _run_enrich(driver, settings, creds, skip_extraction=skip_extraction)
        except Exception as exc:
            print(f"\n[FAIL] Enrichment failed: {exc}")
            print("CSV data was loaded successfully. Fix the issue and re-run:")
            print("  uv run populate-aircraft-db setup")
            raise typer.Exit(code=1) from exc

        verify(
            driver,
            settings.neo4j_database,
            expected_embedding_dimensions=settings.embedding_dimensions,
            skip_extraction=skip_extraction,
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
            settings.neo4j_database,
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
        clear_database(driver, settings.neo4j_database)

    print("\nDone.")


@app.command("clean-enrichment")
def clean_enrichment_cmd() -> None:
    """Clear enrichment data (Documents, Chunks, extracted entities) while preserving the operational graph."""
    from .pipeline import clear_enrichment_data

    settings = Settings()  # type: ignore[call-arg]

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        clear_enrichment_data(driver, settings.neo4j_database)

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
        create_constraints(driver, settings.neo4j_database)
        print("\nCreating indexes...")
        create_indexes(driver, settings.neo4j_database)
        print("\nCreating fulltext indexes...")
        create_fulltext_indexes(driver, settings.neo4j_database)
        print()

        load_nodes(driver, settings.neo4j_database, settings.data_dir)
        print()
        load_relationships(driver, settings.neo4j_database, settings.data_dir)
        print()
        load_operating_limits(driver, settings.neo4j_database, settings.data_dir)
        print()

        print("Linking existing enrichment to operational graph...")
        link_to_existing_graph(driver, settings.neo4j_database)

        validate_enrichment(driver, settings.neo4j_database)

    elapsed = time.monotonic() - start
    print(f"\nDone in {_fmt_elapsed(elapsed)}.")


@app.command("enrich")
def enrich_cmd(
    skip_extraction: bool = typer.Option(
        False,
        "--skip-extraction",
        help=_SKIP_EXTRACTION_HELP,
    ),
) -> None:
    """Run GraphRAG enrichment against an already-loaded operational graph."""
    settings = Settings()  # type: ignore[call-arg]
    _export_databricks_env(settings)
    creds = _resolve_llm_credentials(settings, skip_extraction=skip_extraction)

    print(f"Connecting to {settings.neo4j_uri}...")
    with _connect(settings) as driver:
        _run_enrich(driver, settings, creds, skip_extraction=skip_extraction)

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
        run_all_samples(
            driver, settings.neo4j_database, sample_size=settings.sample_size
        )


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
            settings.neo4j_database,
            provider=creds.provider,
            openai_key=creds.openai_key,
            anthropic_key=creds.anthropic_key,
            llm_model=creds.llm_model,
            embedding_model=creds.embedding_model,
            sample_size=settings.sample_size,
        )


if __name__ == "__main__":
    app()
