"""
Workshop Data Setup — uploads CSVs to UC volumes and creates a DLT pipeline
for bronze→silver→gold medallion architecture ETL.

Designed to run inside Vocareum's workspace_init flow or standalone.
Uses only the Databricks SDK.

Usage:
  # Called from workspace_init (pass WorkspaceClient)
  from workshop_data_setup import setup_workshop_data
  setup_workshop_data(workspace_client=w, warehouse_id=warehouse_id)
"""

import base64
import logging
import os
import sys
import time
from pathlib import Path

from databricks.sdk.service.iam import AccessControlRequest, PermissionLevel

logger = logging.getLogger("workshop_data_setup")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    logger.addHandler(handler)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CATALOG = os.getenv("WORKSHOP_CATALOG", "databricks-neo4j-workshop")
VOLUME_SCHEMA = os.getenv("WORKSHOP_VOLUME_SCHEMA", "lab-schema")
VOLUME_NAME = os.getenv("WORKSHOP_VOLUME_NAME", "lab-volume")
LAKEHOUSE_SCHEMA = os.getenv("WORKSHOP_LAKEHOUSE_SCHEMA", "lakehouse")

DATA_DIR = os.getenv(
    "WORKSHOP_DATA_DIR",
    "/voc/private/courseware/aircraft_digital_twin_data",
)

DLT_NOTEBOOK_SOURCE = os.getenv(
    "DLT_NOTEBOOK_PATH",
    "/voc/private/courseware/dlt_fleet_etl.py",
)

VOLUMES_PATH = f"/Volumes/{CATALOG}/{VOLUME_SCHEMA}/{VOLUME_NAME}"
DLT_NOTEBOOK_WORKSPACE_PATH = "/Shared/workshop/dlt_fleet_etl"
PIPELINE_NAME = "Fleet Digital Twin ETL"


# ---------------------------------------------------------------------------
# Infrastructure SQL
# ---------------------------------------------------------------------------

def get_infrastructure_sql() -> list[tuple[str, str]]:
    """Return (description, sql) for catalog/schema/volume creation."""
    return [
        ("Creating catalog", f"CREATE CATALOG IF NOT EXISTS `{CATALOG}`"),
        ("Granting USE CATALOG", f"GRANT USE_CATALOG ON CATALOG `{CATALOG}` TO `account users`"),
        ("Creating volume schema", f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{VOLUME_SCHEMA}`"),
        ("Granting USE SCHEMA on volume schema", f"GRANT USE_SCHEMA ON SCHEMA `{CATALOG}`.`{VOLUME_SCHEMA}` TO `account users`"),
        ("Creating volume", f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`{VOLUME_SCHEMA}`.`{VOLUME_NAME}`"),
        ("Granting READ VOLUME", f"GRANT READ_VOLUME ON VOLUME `{CATALOG}`.`{VOLUME_SCHEMA}`.`{VOLUME_NAME}` TO `account users`"),
        ("Creating lakehouse schema", f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{LAKEHOUSE_SCHEMA}`"),
        ("Granting USE SCHEMA on lakehouse", f"GRANT USE_SCHEMA ON SCHEMA `{CATALOG}`.`{LAKEHOUSE_SCHEMA}` TO `account users`"),
        ("Granting CREATE CONNECTION", "GRANT CREATE CONNECTION ON METASTORE TO `account users`"),
    ]


def get_post_pipeline_sql() -> list[str]:
    """Return SQL for comments + grants to run after DLT pipeline completes."""
    target = f"`{CATALOG}`.`{LAKEHOUSE_SCHEMA}`"
    return [
        # Table comments for Genie
        f"COMMENT ON TABLE {target}.aircraft IS 'Fleet of aircraft with tail numbers, models, and operators'",
        f"COMMENT ON TABLE {target}.systems IS 'Aircraft systems including engines, avionics, and hydraulics'",
        f"COMMENT ON TABLE {target}.sensors IS 'Sensors installed on aircraft systems'",
        f"COMMENT ON TABLE {target}.sensor_readings IS 'Hourly sensor readings over 90 days (July-September 2024)'",
        f"COMMENT ON TABLE {target}.flights IS 'Flight operations with aircraft, route, schedule, and total delay minutes'",
        f"COMMENT ON TABLE {target}.maintenance_events IS 'Maintenance events with fault details and severity'",
        f"COMMENT ON TABLE {target}.fleet_readiness IS 'Per-aircraft fleet readiness with mission status'",
        f"COMMENT ON TABLE {target}.sensor_health IS 'Per-sensor health summary with anomaly detection'",
        # Column comments for Genie
        f"COMMENT ON COLUMN {target}.aircraft.tail_number IS 'Aircraft registration/tail number (e.g., N95040A)'",
        f"COMMENT ON COLUMN {target}.aircraft.model IS 'Aircraft model (e.g., B737-800, A320-200)'",
        f"COMMENT ON COLUMN {target}.aircraft.operator IS 'Airline operator name'",
        f"COMMENT ON COLUMN {target}.systems.system_type IS 'System type (Engine, Avionics, Hydraulics)'",
        f"COMMENT ON COLUMN {target}.sensors.sensor_type IS 'Sensor type: EGT, Vibration, N1Speed, FuelFlow'",
        f"COMMENT ON COLUMN {target}.sensor_readings.sensor_id IS 'Foreign key to sensors table'",
        f"COMMENT ON COLUMN {target}.sensor_readings.timestamp IS 'Reading timestamp (hourly intervals)'",
        f"COMMENT ON COLUMN {target}.sensor_readings.value IS 'Sensor reading value in the sensor unit'",
        f"COMMENT ON COLUMN {target}.fleet_readiness.readiness_status IS 'MISSION READY, DEGRADED, or NOT MISSION READY'",
        f"COMMENT ON COLUMN {target}.sensor_health.health_status IS 'NORMAL, WARNING, or ANOMALY based on 2-sigma deviation'",
        # Grants — gold tables
        f"GRANT SELECT ON TABLE {target}.aircraft TO `account users`",
        f"GRANT SELECT ON TABLE {target}.systems TO `account users`",
        f"GRANT SELECT ON TABLE {target}.sensors TO `account users`",
        f"GRANT SELECT ON TABLE {target}.sensor_readings TO `account users`",
        f"GRANT SELECT ON TABLE {target}.flights TO `account users`",
        f"GRANT SELECT ON TABLE {target}.maintenance_events TO `account users`",
        f"GRANT SELECT ON TABLE {target}.fleet_readiness TO `account users`",
        f"GRANT SELECT ON TABLE {target}.sensor_health TO `account users`",
    ]


# ---------------------------------------------------------------------------
# Upload logic
# ---------------------------------------------------------------------------

def upload_csv_files(workspace_client, data_dir: str) -> int:
    """Upload CSV files from local filesystem to UC volume."""
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return 0

    csv_files = sorted(data_path.glob("*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {data_dir}")
        return 0

    logger.info(f"Uploading {len(csv_files)} CSV files to {VOLUMES_PATH}")
    uploaded = 0

    for f in csv_files:
        target = f"{VOLUMES_PATH}/{f.name}"
        logger.info(f"  [{uploaded + 1}/{len(csv_files)}] {f.name}")
        t0 = time.monotonic()
        with open(f, "rb") as fd:
            workspace_client.files.upload(target, fd, overwrite=True)
        elapsed = time.monotonic() - t0
        uploaded += 1
        logger.info(f"    Done ({elapsed:.1f}s)")

    logger.info(f"Uploaded {uploaded} files")
    return uploaded


def upload_dlt_notebook(workspace_client) -> str:
    """Upload the DLT pipeline notebook to the workspace."""
    source_path = DLT_NOTEBOOK_SOURCE

    if not os.path.exists(source_path):
        logger.error(f"DLT notebook not found at {source_path}")
        raise FileNotFoundError(f"DLT notebook not found: {source_path}")

    with open(source_path, "r") as f:
        content = f.read()

    # Import as PYTHON notebook via workspace API
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    # Ensure parent directory exists
    parent = "/".join(DLT_NOTEBOOK_WORKSPACE_PATH.rsplit("/", 1)[:-1])
    try:
        workspace_client.workspace.mkdirs(parent)
    except Exception:
        pass

    from databricks.sdk.service.workspace import ImportFormat, Language
    workspace_client.workspace.import_(
        path=DLT_NOTEBOOK_WORKSPACE_PATH,
        content=encoded,
        format=ImportFormat.SOURCE,
        language=Language.PYTHON,
        overwrite=True,
    )

    logger.info(f"Uploaded DLT notebook to {DLT_NOTEBOOK_WORKSPACE_PATH}")
    return DLT_NOTEBOOK_WORKSPACE_PATH


# ---------------------------------------------------------------------------
# DLT Pipeline creation
# ---------------------------------------------------------------------------

def create_dlt_pipeline(workspace_client) -> str:
    """Create and start a DLT pipeline for the fleet ETL."""
    from databricks.sdk.service.pipelines import PipelineLibrary, NotebookLibrary

    # Check if pipeline already exists
    for p in workspace_client.pipelines.list_pipelines():
        if p.name == PIPELINE_NAME:
            logger.info(f"Pipeline '{PIPELINE_NAME}' already exists (id={p.pipeline_id})")
            return p.pipeline_id

    response = workspace_client.pipelines.create(
        name=PIPELINE_NAME,
        catalog=CATALOG,
        target=LAKEHOUSE_SCHEMA,
        serverless=True,
        continuous=False,
        channel="CURRENT",
        libraries=[
            PipelineLibrary(
                notebook=NotebookLibrary(path=DLT_NOTEBOOK_WORKSPACE_PATH)
            )
        ],
        configuration={
            "pipelines.applyChangesPreviewEnabled": "true",
        },
    )

    pipeline_id = response.pipeline_id
    logger.info(f"Created DLT pipeline '{PIPELINE_NAME}' (id={pipeline_id})")

    # Grant CAN_VIEW to all users so participants can see the pipeline
    for group in ["users", "account users"]:
        try:
            workspace_client.permissions.update(
                request_object_type="pipelines",
                request_object_id=pipeline_id,
                access_control_list=[
                    AccessControlRequest(
                        group_name=group,
                        permission_level=PermissionLevel.CAN_VIEW,
                    )
                ],
            )
            logger.info(f"Granted CAN_VIEW on pipeline to '{group}'")
        except Exception as e:
            logger.warning(f"Failed to grant CAN_VIEW to '{group}' (non-fatal): {e}")

    return pipeline_id


def start_and_wait_pipeline(workspace_client, pipeline_id: str, timeout: int = 600):
    """Trigger a pipeline update and wait for completion."""
    logger.info(f"Starting pipeline {pipeline_id}...")
    workspace_client.pipelines.start_update(pipeline_id=pipeline_id, full_refresh=True)

    # Wait for pipeline to complete
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        pipeline = workspace_client.pipelines.get(pipeline_id=pipeline_id)
        state = pipeline.state
        latest = pipeline.latest_updates[0] if pipeline.latest_updates else None
        update_state = latest.state if latest else "UNKNOWN"

        logger.info(f"  Pipeline state: {state}, update: {update_state}")

        if str(update_state) in ("COMPLETED", "UpdateStateInfoState.COMPLETED"):
            logger.info("Pipeline completed successfully!")
            return True
        elif str(update_state) in ("FAILED", "CANCELED", "UpdateStateInfoState.FAILED", "UpdateStateInfoState.CANCELED"):
            logger.error(f"Pipeline failed with state: {update_state}")
            return False

        time.sleep(15)

    logger.error(f"Pipeline timed out after {timeout}s")
    return False


# ---------------------------------------------------------------------------
# SQL execution
# ---------------------------------------------------------------------------

def execute_sql(workspace_client, warehouse_id: str, sql: str):
    """Execute a SQL statement via Statement Execution API."""
    from databricks.sdk.service.sql import StatementState

    logger.debug(f"Executing: {sql[:120]}...")

    response = workspace_client.statement_execution.execute_statement(
        statement=sql,
        warehouse_id=warehouse_id,
        wait_timeout="50s",
    )

    while response.status.state == StatementState.PENDING:
        time.sleep(5)
        response = workspace_client.statement_execution.get_statement(
            statement_id=response.statement_id
        )

    if response.status.state != StatementState.SUCCEEDED:
        error_msg = response.status.error.message if response.status.error else "Unknown error"
        raise RuntimeError(f"SQL failed: {error_msg}")

    return response


# ---------------------------------------------------------------------------
# Main setup function
# ---------------------------------------------------------------------------

def setup_workshop_data(
    workspace_client=None,
    warehouse_id: str = None,
    data_dir: str = None,
    skip_upload: bool = False,
):
    """
    Complete workshop data setup:
    1. Create catalog, schemas, volume
    2. Upload CSVs to UC volume
    3. Upload DLT notebook + create and run pipeline
    4. Add Genie-friendly comments + grant permissions
    """
    if workspace_client is None:
        from databricks.sdk import WorkspaceClient
        workspace_client = WorkspaceClient()

    if data_dir is None:
        data_dir = DATA_DIR

    # Find a warehouse if not provided
    if warehouse_id is None:
        logger.info("Finding SQL warehouse...")
        from databricks.sdk.service.sql import State as WhState
        for wh in workspace_client.warehouses.list():
            if wh.state in [WhState.RUNNING, WhState.STARTING]:
                warehouse_id = wh.id
                logger.info(f"Using warehouse: {wh.name} ({wh.id})")
                break
        else:
            for wh in workspace_client.warehouses.list():
                if wh.state not in [WhState.DELETED, WhState.DELETING]:
                    logger.info(f"Starting warehouse: {wh.name}")
                    workspace_client.warehouses.start(wh.id)
                    warehouse_id = wh.id
                    time.sleep(30)
                    break
            else:
                raise RuntimeError("No SQL warehouse found")

    # Step 1: Create catalog, schemas, volume
    logger.info("=" * 60)
    logger.info("STEP 1: Creating catalog, schemas, and volume")
    logger.info("=" * 60)

    for desc, sql_stmt in get_infrastructure_sql():
        logger.info(f"  {desc}...")
        try:
            execute_sql(workspace_client, warehouse_id, sql_stmt)
            logger.info(f"    Done.")
        except RuntimeError as e:
            logger.error(f"    FAILED: {e}")

    # Step 2: Upload CSVs
    if not skip_upload:
        logger.info("=" * 60)
        logger.info("STEP 2: Uploading CSV data files")
        logger.info("=" * 60)
        upload_csv_files(workspace_client, data_dir)
    else:
        logger.info("Skipping CSV upload (skip_upload=True)")

    # Step 3: Upload DLT notebook and create pipeline
    logger.info("=" * 60)
    logger.info("STEP 3: Creating DLT pipeline (Bronze → Silver → Gold)")
    logger.info("=" * 60)

    upload_dlt_notebook(workspace_client)
    pipeline_id = create_dlt_pipeline(workspace_client)
    success = start_and_wait_pipeline(workspace_client, pipeline_id)

    if not success:
        logger.warning("DLT pipeline did not complete — comments/grants may fail")

    # Step 4: Comments + permissions (on gold tables)
    logger.info("=" * 60)
    logger.info("STEP 4: Adding Genie comments and granting permissions")
    logger.info("=" * 60)

    for sql in get_post_pipeline_sql():
        try:
            execute_sql(workspace_client, warehouse_id, sql)
        except RuntimeError as e:
            logger.warning(f"  Comment/grant failed (non-fatal): {e}")

    logger.info("=" * 60)
    logger.info("Workshop data setup complete!")
    logger.info(f"  Catalog:     {CATALOG}")
    logger.info(f"  Volume:      {VOLUMES_PATH}")
    logger.info(f"  Pipeline:    {PIPELINE_NAME} (id={pipeline_id})")
    logger.info(f"  Gold tables: {CATALOG}.{LAKEHOUSE_SCHEMA}.*")
    logger.info(f"    aircraft, systems, sensors, sensor_readings")
    logger.info(f"    flights, maintenance_events")
    logger.info(f"    fleet_readiness, sensor_health")
    logger.info("=" * 60)


if __name__ == "__main__":
    setup_workshop_data()
