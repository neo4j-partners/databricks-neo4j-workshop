"""Upload workshop CSVs to the UC volume and create the lakehouse Delta tables.

Runs only the data portion of `databricks-setup setup` (Track B, minus the
notebook upload): finds the SQL warehouse, uploads CSVs from
aircraft_digital_twin_data/ to the Unity Catalog volume, then creates the
`aircraft`, `systems`, `sensors`, and `sensor_readings` Delta tables via the
Statement Execution API.

Config is read from workshop-setup/.env, the same as the full setup command.

Run from the auto_scripts directory:

    uv run python load_lakehouse_data.py
"""

from __future__ import annotations

from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import Disposition, Format

from databricks_setup.config import Config, VolumeConfig
from databricks_setup.data_upload import upload_data_files, verify_upload
from databricks_setup.lakehouse_tables import create_lakehouse_tables, get_verification_sql
from databricks_setup.log import log
from databricks_setup.utils import print_header
from databricks_setup.warehouse import get_or_start_warehouse

DATA_DIR = Path(__file__).resolve().parent.parent / "aircraft_digital_twin_data"


def print_table_counts(
    client: WorkspaceClient,
    warehouse_id: str,
    volume_config: VolumeConfig,
) -> None:
    """Run the verification query and print the actual per-table row counts.

    ``create_lakehouse_tables`` runs the same query but discards the result
    rows, so this re-runs it and prints the data the user actually cares about.
    """
    print_header("Lakehouse Table Row Counts")

    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=get_verification_sql(volume_config),
        wait_timeout="50s",
        disposition=Disposition.INLINE,
        format=Format.JSON_ARRAY,
    )

    rows = response.result.data_array if response.result else None
    if not rows:
        log("[yellow]No row-count data returned.[/yellow]")
        return

    for table_name, row_count in rows:
        log(f"  {table_name:<18} {int(row_count):>12,}")


def main() -> None:
    """Upload CSVs to the volume and create the lakehouse tables."""
    config = Config.load()
    config.data.data_dir = DATA_DIR
    client = config.prepare()

    warehouse_id = get_or_start_warehouse(client, config.warehouse)

    upload_data_files(client, config.data, config.volume)
    verify_upload(client, config.volume)

    create_lakehouse_tables(
        client,
        warehouse_id,
        config.volume,
        config.warehouse.timeout_seconds,
    )

    print_table_counts(client, warehouse_id, config.volume)


if __name__ == "__main__":
    main()
