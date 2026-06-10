"""Main entry point for Databricks environment setup and cleanup.

Provides CLI interface for setting up data and tearing down workshop resources.
"""

from __future__ import annotations

import time
import traceback
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from databricks.sdk import WorkspaceClient

from .cleanup import run_cleanup
from .cluster import get_or_create_cluster, wait_for_cluster_running
from .config import Config, SetupResult
from .data_upload import upload_data_files, verify_upload
from .lakehouse_tables import create_lakehouse_tables
from .libraries import ensure_libraries_installed
from .log import Level, close_log_file, init_log_file, log, log_to_file
from .notebooks import upload_notebooks, verify_notebook_upload
from .utils import print_header
from .warehouse import get_or_start_warehouse

app = typer.Typer(
    name="databricks-setup",
    help="Setup and cleanup Databricks environment for Neo4j workshop.",
    add_completion=False,
)


# ---------------------------------------------------------------------------
# setup
# ---------------------------------------------------------------------------

@app.command()
def setup() -> None:
    """Set up Databricks environment for the Neo4j workshop.

    Runs two tracks sequentially:

      Track A: Create/start admin cluster and install libraries.

      Track B: Upload data files and create lakehouse tables via SQL Warehouse.

    All configuration is loaded from lab_setup/.env.
    """
    log_path = init_log_file()
    log(f"[dim]Log file: {log_path}[/dim]")

    start = time.monotonic()
    try:
        _run_setup()
        elapsed = time.monotonic() - start
        log(f"[green]Total elapsed time: {_fmt_elapsed(elapsed)}[/green]")
    except Exception as e:
        elapsed = time.monotonic() - start
        log(f"[red]Error: {e}[/red]", level=Level.ERROR)
        log_to_file(traceback.format_exc(), level=Level.ERROR)
        log(f"[dim]Failed after {_fmt_elapsed(elapsed)}[/dim]")
        raise typer.Exit(code=1) from None
    finally:
        close_log_file()


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------

@app.command()
def cleanup(
    yes: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Delete notebooks, lakehouse tables, volume, schemas, and catalog.

    Removes everything created by the setup command.  Each step is idempotent.

    All configuration is loaded from lab_setup/.env.
    """
    log_path = init_log_file()
    log(f"[dim]Log file: {log_path}[/dim]")
    start = time.monotonic()
    try:
        _run_cleanup(yes=yes)
        elapsed = time.monotonic() - start
        log(f"[green]Total elapsed time: {_fmt_elapsed(elapsed)}[/green]")
    except Exception as e:
        elapsed = time.monotonic() - start
        log(f"[red]Error: {e}[/red]", level=Level.ERROR)
        log_to_file(traceback.format_exc(), level=Level.ERROR)
        log(f"[dim]Failed after {_fmt_elapsed(elapsed)}[/dim]")
        raise typer.Exit(code=1) from None
    finally:
        close_log_file()


# ---------------------------------------------------------------------------
# sync
# ---------------------------------------------------------------------------

@app.command()
def sync() -> None:
    """Sync workshop notebooks to the Databricks workspace.

    Uploads all lab notebooks.  The neo4j_mcp_connection folder is deleted
    first to avoid stale artifacts, then re-uploaded cleanly.
    """
    log_path = init_log_file()
    log(f"[dim]Log file: {log_path}[/dim]")

    start = time.monotonic()
    try:
        _run_sync()
        elapsed = time.monotonic() - start
        log(f"[green]Total elapsed time: {_fmt_elapsed(elapsed)}[/green]")
    except Exception as e:
        elapsed = time.monotonic() - start
        log(f"[red]Error: {e}[/red]", level=Level.ERROR)
        log_to_file(traceback.format_exc(), level=Level.ERROR)
        log(f"[dim]Failed after {_fmt_elapsed(elapsed)}[/dim]")
        raise typer.Exit(code=1) from None
    finally:
        close_log_file()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_elapsed(seconds: float) -> str:
    """Format elapsed seconds as a human-readable string."""
    m, s = divmod(int(seconds), 60)
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


# ---------------------------------------------------------------------------
# setup orchestration
# ---------------------------------------------------------------------------

def _run_sync() -> None:
    """Load config, upload notebooks, and verify."""
    config = Config.load()
    client = config.prepare()

    print_header("Sync Notebooks")
    log(f"  Target: {config.notebook.workspace_folder}")

    upload_notebooks(client, config.notebook)
    verify_notebook_upload(client, config.notebook)

    log()
    log("[green]Notebook sync complete.[/green]")


def _run_setup() -> None:
    """Load config, run Tracks A and B, and print results."""
    config = Config.load()
    client = config.prepare()

    _print_config_summary(config)

    result = SetupResult()

    # Track A: Admin Cluster
    result.cluster_ok = _setup_admin_cluster(client, config)

    # Track B: Data Upload + Lakehouse Tables
    print_header("Track B: Data Upload + Lakehouse Tables")
    warehouse_id = get_or_start_warehouse(client, config.warehouse)
    upload_data_files(client, config.data, config.volume)
    verify_upload(client, config.volume)

    try:
        upload_notebooks(client, config.notebook)
        verify_notebook_upload(client, config.notebook)
    except Exception as e:
        log(f"[red]Notebook upload failed: {e}[/red]")
        result.notebooks_ok = False

    result.tables_ok = create_lakehouse_tables(
        client,
        warehouse_id,
        config.volume,
        config.warehouse.timeout_seconds,
    )

    _print_summary(result, config)


def _setup_admin_cluster(client: WorkspaceClient, config: Config) -> bool:
    """Create/start the admin cluster and install libraries (Track A).

    The cluster is created in Single User (dedicated) mode, assigned to the
    admin user running the setup.

    Returns:
        True if the cluster is running with libraries installed, False on error.
    """
    print_header("Track A: Admin Cluster")

    if not config.user_email:
        log("[red]Cannot create admin cluster: user email not resolved.[/red]")
        return False

    try:
        cluster_id = get_or_create_cluster(client, config.cluster, config.user_email)
        wait_for_cluster_running(client, cluster_id)
        ensure_libraries_installed(client, cluster_id, config.library)
    except Exception as e:
        log(f"[red]Admin cluster setup failed: {e}[/red]")
        log_to_file(traceback.format_exc(), level=Level.ERROR)
        return False

    return True


# ---------------------------------------------------------------------------
# cleanup orchestration
# ---------------------------------------------------------------------------

def _run_cleanup(*, yes: bool) -> None:
    """Load config, confirm, and run cleanup."""
    config = Config.load()
    client = config.prepare()
    warehouse_id = get_or_start_warehouse(client, config.warehouse)

    _print_cleanup_target(config)

    if not yes:
        typer.confirm("Proceed with cleanup?", abort=True)

    run_cleanup(
        client, warehouse_id, config.volume, config.warehouse.timeout_seconds,
        notebook_config=config.notebook,
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _print_config_summary(config: Config) -> None:
    """Print configuration overview before running tracks."""
    print_header("Databricks Environment Setup")

    if config.user_email:
        log(f"User:       {config.user_email}")
    log(f"Cluster:    {config.cluster.name}")
    log(f"Warehouse:  {config.warehouse.name}")
    log(f"Volume:     {config.volume.full_path}")
    log(f"Lakehouse:  {config.volume.catalog}.{config.volume.lakehouse_schema}")
    log(f"Notebooks:  {config.notebook.workspace_folder}")

    log()


def _print_summary(result: SetupResult, config: Config) -> None:
    """Print final setup summary."""
    print_header("Setup Complete" if result.success else "Setup Completed with Errors")

    if result.cluster_ok:
        log(f"Cluster:      [green]{config.cluster.name}[/green]")
    else:
        log(f"Cluster:      [red]{config.cluster.name} — failed[/red]")
    log(f"Volume:       {config.volume.full_path}")
    log(f"Lakehouse:    {config.volume.catalog}.{config.volume.lakehouse_schema}")
    log(f"Notebooks:    {config.notebook.workspace_folder}")
    if not result.tables_ok:
        log("[red]Lakehouse table creation had errors.[/red]")
    if not result.notebooks_ok:
        log("[red]Notebook upload had errors.[/red]")


def _print_cleanup_target(config: Config) -> None:
    """Print what will be deleted."""
    print_header("Cleanup Target")
    log(f"Catalog:    {config.volume.catalog}")
    log(f"Schema:     {config.volume.catalog}.{config.volume.schema}")
    log(f"Volume:     {config.volume.full_path}")
    log(f"Lakehouse:  {config.volume.catalog}.{config.volume.lakehouse_schema}")
    log(f"Notebooks:  {config.notebook.workspace_folder}")
    log()
    log("[yellow]This will permanently delete the catalog and all its contents.[/yellow]")


if __name__ == "__main__":
    app()
