#!/usr/bin/env python3
"""The one definition of this workshop's Databricks objects.

Uploaded to ``/voc/scripts`` beside the hooks and invoked by
``workspace_init.sh``. One definition rather than two, because the alternative
is a Vocareum copy and an instructor copy of the same eight table definitions,
and two copies of a Genie comment drift silently: a Genie space with a stale
column comment answers plausibly rather than correctly, which is the hardest
class of workshop failure to notice in a room of thirty people.

What it replaces. The previous route was ``dbacademy.py``, a vendored and
locally patched SDK wrapper installed by ``pip3 install databricks-sdk`` at the
top of a hook. Three things ruled it out and only one is about speed. It writes
``voccustomdata.txt`` itself, which puts a second writer on the one channel a
hook failure travels through. PEP 668 refuses the install outright on a managed
host, and this hook failing empties the catalog for every student later placed
in the workspace. And the local patches made it a fork nobody was maintaining.
What is left is four call shapes against endpoints ``voclab.py`` already speaks.

Why it imports ``voclab``. Both files land in ``/voc/scripts``, so the import is
a lookup in the directory this program is already running from. Taking
``Workspace``, ``ApiError`` and the output helpers from there rather than
restating them means one HTTP retry policy rather than two drifting copies, and
the retry policy is the part most worth not writing twice: it separates a 429,
which is safe to retry, from a 500 on a create, which is how one workspace ends
up with two DLT pipelines. The cost is that those names become a contract the
package owes its courses, which is stated here rather than assumed.

The output contract is ``voclab.py``'s, unchanged. Narration to **stderr**, so
it interleaves with ``voc_log``. ``key=value`` lines on **stdout**, keys from
``[a-z0-9_]``. On failure an ``error_code`` and a ``message`` and a non-zero
exit, which the hook hands to ``voc_fail``. This program writes neither
``voccustomdata.txt`` nor ``$VOC_IPC_DATA_FILE``; the calling hook does, from
those variables, and both files stay single-writer.

Standard library only, against Python 3.9, for the same reason ``voclab.py`` is.

Exit codes: ``0`` ok, ``1`` a failure carrying an ``error_code``.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

EXIT_OK = 0
EXIT_FAILED = 1


def _import_voclab():
    """Find the lab runtime, whether this runs in Vocareum or on a laptop.

    In Vocareum both files sit in ``/voc/scripts`` and the sibling import wins.
    Off it, ``voclab.py`` is package data inside ``dbx-vocareum-tools``, which
    this repository declares as a dev dependency, so the installed package is
    where to look. Locating the module is the only thing that differs between
    the two; everything below runs identically under both, which is the property
    that makes one definition worth having.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import voclab

        return voclab
    except ImportError:
        pass

    try:
        from dbx_vocareum_tools.labruntime import RUNTIME_DIR
    except ImportError:
        raise SystemExit(
            "voclab.py is not beside this file and dbx-vocareum-tools is not "
            "installed, so there is no lab runtime to build on. In Vocareum "
            "the two are uploaded to /voc/scripts together; on a laptop, run "
            "this through `uv run` from the repository root."
        ) from None
    sys.path.insert(0, str(RUNTIME_DIR))
    import voclab

    return voclab


voclab = _import_voclab()


# --- What this workshop is made of -------------------------------------------
#
# Read from the environment with the defaults the DLT notebook carries, and
# forwarded into the pipeline configuration below, so an override here cannot
# desync from the notebook that reads the same four names.

CATALOG = os.environ.get("WORKSHOP_CATALOG", "databricks-neo4j-workshop")
VOLUME_SCHEMA = os.environ.get("WORKSHOP_VOLUME_SCHEMA", "aircraft")
VOLUME_NAME = os.environ.get("WORKSHOP_VOLUME_NAME", "raw_data")
LAKEHOUSE_SCHEMA = os.environ.get("WORKSHOP_LAKEHOUSE_SCHEMA", "aircraft")

# Bronze and silver land here, so a participant browsing Catalog, or picking
# tables for a Genie space, sees the eight gold tables and nothing else.
PIPELINE_SCHEMA = os.environ.get("WORKSHOP_PIPELINE_SCHEMA", "aircraft_pipeline")

VOLUME_PATH = f"/Volumes/{CATALOG}/{VOLUME_SCHEMA}/{VOLUME_NAME}"

# Where the catalog's managed tables physically go, and the one value here read
# under its course.env name rather than a WORKSHOP_ one. It is a property of the
# account the course is deployed into, not of the workshop, so it belongs beside
# the other per-deployment values a course states rather than in this file.
#
# Measured 2026-08-08 and the reason this exists at all: the account this course
# runs on has Databricks Default Storage enabled, which leaves the metastore with
# no storage_root, and a bare CREATE CATALOG there fails with
# "[INVALID_STATE] Metastore storage root URL does not exist". Naming a location
# inside an external location the metastore holds succeeds. Naming one inside
# Databricks-managed storage does not, and refuses with "Please use the UI",
# which a hook can never satisfy.
#
# Empty rather than unset when absent, because the value is spliced into SQL and
# the statement without it has to be exactly the statement that was there before.
# An account whose metastore does carry a storage_root needs no value here.
CATALOG_MANAGED_LOCATION = os.environ.get(
    "VOC_COURSE_CATALOG_MANAGED_LOCATION", ""
).strip()

PIPELINE_NAME = "Fleet Digital Twin ETL"
DLT_NOTEBOOK_WORKSPACE_PATH = "/Shared/workshop/dlt_fleet_etl"

# The eight gold tables, in the order a reader meets them: the fleet, what is on
# it, what it did, then the two summaries Lab 4 asks Genie about.
GOLD_TABLES = (
    "aircraft",
    "systems",
    "sensors",
    "sensor_readings",
    "flights",
    "maintenance_events",
    "fleet_readiness",
    "sensor_health",
)

# Lab 5 names. Stated here for the same reason every other name is: the notebook
# that logs the agent, the notebook that queries the endpoint, and any admin
# script that cleans up after a cohort all have to agree, and a name written
# three times drifts. The schema is the one of these this file creates, in
# infrastructure_statements below, because a model cannot be registered into a
# schema that is not there. The model, the endpoint and the secret scope are
# created by Lab 5 in a participant's notebook, reading their names from here.
#
# Registered under the workshop catalog so a teardown of the catalog takes the
# model with it, in the pipeline schema's sibling rather than the gold schema so
# a participant browsing gold tables for a Genie space still sees eight.
AGENT_SCHEMA = os.environ.get("WORKSHOP_AGENT_SCHEMA", "agents")
AGENT_MODEL_NAME = "fleet_ops_assistant"
AGENT_MODEL_FULL_NAME = f"{CATALOG}.{AGENT_SCHEMA}.{AGENT_MODEL_NAME}"

# Serving endpoint names are account-unique, not catalog-scoped, so a shared
# workspace needs one per participant. Lab 5 suffixes this with the participant's
# identifier rather than using it bare.
AGENT_ENDPOINT_PREFIX = "fleet-ops-assistant"

# Where Lab 5 puts the Neo4j password so the deployed endpoint, which runs as a
# service principal and not as the notebook user, can read it. Same per-
# participant caveat as the endpoint: scope names are workspace-unique.
AGENT_SECRET_SCOPE_PREFIX = "fleet-ops"
AGENT_SECRET_KEY_NEO4J_URI = "neo4j-uri"
AGENT_SECRET_KEY_NEO4J_USERNAME = "neo4j-username"
AGENT_SECRET_KEY_NEO4J_PASSWORD = "neo4j-password"

# The model behind the supervisor's routing decision, and behind GraphRAG answer
# generation in Lab 3. One name so the two cannot diverge.
SUPERVISOR_LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"

# The embedding endpoint Lab 3 writes maintenanceChunkEmbeddings with and Lab 5
# reads it back with. Changing this invalidates every stored vector, because a
# 1024-dimension index says nothing about which model produced the numbers in it.
EMBEDDING_ENDPOINT = "databricks-bge-large-en"
EMBEDDING_DIMENSIONS = 1024

# Where the courseware is, singular. This used to be two lists of candidate
# paths, written while it was still an open question whether the upload could
# address anything but a flat folder. It is no longer open. Measured 2026-08-07
# against part 5664556 and recorded in dbx-vocareum's docs/vocareum-api.md,
# "Nesting, measured 2026-08-07": an archive member carrying a directory prefix
# uploads and lands at that exact path, while a nested ``target`` is refused
# with a 400. So ``lab/courseware/`` travels inside the same archive as the
# hooks and arrives under /voc/scripts with its layout intact.
#
# /voc/scripts rather than /voc/private, deliberately. It is the only directory
# measured to exist on the machine a hook actually runs on: a live session
# sourced /voc/scripts/voclib.sh from there. Whether /voc/private is even
# mounted on that machine has never been measured, and the file listing that
# shows it is Vocareum's content store rather than the hook's filesystem.
#
# A candidate list was the worse alternative for a reason worth stating: a
# search finds the courseware at the first path that happens to hold a CSV, so
# a half-finished deployment and a correct one both report success, and the
# record cannot say which one ran.
COURSEWARE_DIR = "/voc/scripts/courseware"
DATA_DIR = f"{COURSEWARE_DIR}/aircraft_digital_twin_data"
DATA_DIR_VAR = "WORKSHOP_DATA_DIR"

DLT_NOTEBOOK = f"{COURSEWARE_DIR}/dlt_fleet_etl.py"
DLT_NOTEBOOK_VAR = "WORKSHOP_DLT_NOTEBOOK"

# Lab 3 reads the maintenance manuals out of the volume by name. A run that
# uploaded every CSV and no manual produces a workshop that provisions cleanly
# and breaks two labs in, so their absence is a failure rather than a warning.
DATA_GLOBS = ("*.csv", "MAINTENANCE_*.md")

STATEMENT_WAIT = "50s"
STATEMENT_POLL_SECONDS = 5
STATEMENT_TIMEOUT_SECONDS = 300
STATEMENT_RUNNING = ("PENDING", "RUNNING")
PIPELINE_POLL_SECONDS = 15
PIPELINE_TIMEOUT_SECONDS = 900
PIPELINE_DONE = frozenset({"COMPLETED"})
PIPELINE_FAILED = frozenset({"FAILED", "CANCELED"})

STATEMENTS_PATH = "/api/2.0/sql/statements"
PIPELINES_PATH = "/api/2.0/pipelines"
WORKSPACE_IMPORT_PATH = "/api/2.0/workspace/import"
WORKSPACE_MKDIRS_PATH = "/api/2.0/workspace/mkdirs"
FILES_PATH = "/api/2.0/fs/files"

# Two group names for two APIs, and they are not interchangeable. ``account
# users`` is the account-level group every Vocareum user lands in; ``users`` is
# the workspace-local one.
#
# Unity Catalog resolves account-level groups, so every GRANT statement below
# goes to ``account users`` and all of them succeeded, measured 2026-08-08 in
# workspace 7474646059936391: 11 infrastructure grants and 26 Genie grants, with
# the required ones fatal, so a failure could not have gone unnoticed.
#
# The workspace permissions API does not resolve them. The same run answered
# ``HTTP 404 RESOURCE_DOES_NOT_EXIST: Principal: GroupName(account users) does
# not exist`` and fell through to ``users``, which took the grant. Trying both
# was the earlier hedge against not knowing which one existed. Now it is known,
# and the hedge only buys a refusal in every transcript from here on, so this
# list names the one the API accepts.
PARTICIPANT_GROUPS = ("users",)
GRANTEE = "`account users`"


# --- The declarative half ----------------------------------------------------


def infrastructure_statements() -> list[tuple[str, str, bool]]:
    """The catalog, four schemas, the volume, and the grants that reach them.

    Each entry is ``(description, sql, required)``. ``required`` is not
    decoration. The version this replaces logged every failure and carried on,
    which is how a run reports success against a catalog that was never created
    and thirty students arrive to an empty Catalog browser. So everything a
    later step reads is required, and every statement here is read by a later
    step. The tuple keeps its third field because ``run_statements`` is shared
    with ``genie_statements``, not because anything below may be refused.

    Every grant here is a read. ``USE_CATALOG``, ``USE_SCHEMA``, ``READ_VOLUME``,
    and the ``SELECT`` grants in ``genie_statements``, and nothing else. No lab
    writes to this catalog: Labs 2 and 3 read the volume and the gold tables and
    write their results to the participant's own Aura instance, and Lab 4 Part A
    builds a Genie space, which needs ``SELECT`` and no more. Keep it that way.
    A ``GRANT CREATE CONNECTION ON METASTORE TO account users`` used to sit at
    the end of this list, so that whoever built the Lab 4 Part B MCP connection
    by hand could do it without metastore admin. It was removed on 2026-08-08:
    thirty students held a metastore-wide create privilege for a step none of
    them perform, since Part B verifies a connection an administrator already
    made.

    Do not put it back. That privilege is now granted once per account to the
    one administrator who needs it, by Step 0 of
    ``workshop-setup/MCP-MANUAL-SETUP.md``, which also records who owns the
    metastore and why. It belongs there rather than here for two reasons: a
    grant on the metastore outlives every workspace this hook builds, so running
    it per workspace init only repeats it; and this function runs as
    ``vocareum-sp``, which owns the metastore, so anything it grants on the
    metastore succeeds regardless of whether it should.
    """
    catalog = f"`{CATALOG}`"
    volume = f"{catalog}.`{VOLUME_SCHEMA}`.`{VOLUME_NAME}`"
    create_catalog = f"CREATE CATALOG IF NOT EXISTS {catalog}"
    if CATALOG_MANAGED_LOCATION:
        create_catalog += f" MANAGED LOCATION '{CATALOG_MANAGED_LOCATION}'"
    return [
        ("catalog", create_catalog, True),
        (
            "grant use catalog",
            f"GRANT USE_CATALOG ON CATALOG {catalog} TO {GRANTEE}",
            True,
        ),
        (
            "volume schema",
            f"CREATE SCHEMA IF NOT EXISTS {catalog}.`{VOLUME_SCHEMA}`",
            True,
        ),
        (
            "grant use volume schema",
            f"GRANT USE_SCHEMA ON SCHEMA {catalog}.`{VOLUME_SCHEMA}` TO {GRANTEE}",
            True,
        ),
        ("volume", f"CREATE VOLUME IF NOT EXISTS {volume}", True),
        (
            "grant read volume",
            f"GRANT READ_VOLUME ON VOLUME {volume} TO {GRANTEE}",
            True,
        ),
        (
            "lakehouse schema",
            f"CREATE SCHEMA IF NOT EXISTS {catalog}.`{LAKEHOUSE_SCHEMA}`",
            True,
        ),
        (
            "grant use lakehouse schema",
            f"GRANT USE_SCHEMA ON SCHEMA {catalog}.`{LAKEHOUSE_SCHEMA}` TO {GRANTEE}",
            True,
        ),
        (
            "pipeline schema",
            f"CREATE SCHEMA IF NOT EXISTS {catalog}.`{PIPELINE_SCHEMA}`",
            True,
        ),
        (
            "grant use pipeline schema",
            f"GRANT USE_SCHEMA ON SCHEMA {catalog}.`{PIPELINE_SCHEMA}` TO {GRANTEE}",
            True,
        ),
        (
            "agent schema",
            f"CREATE SCHEMA IF NOT EXISTS {catalog}.`{AGENT_SCHEMA}`",
            True,
        ),
        (
            "grant use agent schema",
            f"GRANT USE_SCHEMA ON SCHEMA {catalog}.`{AGENT_SCHEMA}` TO {GRANTEE}",
            True,
        ),
    ]


TABLE_COMMENTS = (
    ("aircraft", "Fleet of aircraft with tail numbers, models, and operators"),
    ("systems", "Aircraft systems including engines, avionics, and hydraulics"),
    ("sensors", "Sensors installed on aircraft systems"),
    (
        "sensor_readings",
        (
            "Sensor readings at 4-hour intervals over 90 days (2024-07-01 to "
            "2024-09-28), 155,520 rows across 288 sensors"
        ),
    ),
    (
        "flights",
        "Flight operations with aircraft, route, schedule, and total delay minutes",
    ),
    ("maintenance_events", "Maintenance events with fault details and severity"),
    ("fleet_readiness", "Per-aircraft fleet readiness with mission status"),
    ("sensor_health", "Per-sensor health summary with anomaly detection"),
)

COLUMN_COMMENTS = (
    ("aircraft", "tail_number", "Aircraft registration/tail number (e.g., N10000)"),
    ("aircraft", "model", "Aircraft model (e.g., B737-800, A320-200)"),
    ("aircraft", "operator", "Airline operator name"),
    ("systems", "type", "System type (Engine, Avionics, Hydraulics)"),
    ("sensors", "type", "Sensor type: EGT, Vibration, N1Speed, FuelFlow"),
    ("sensor_readings", "sensor_id", "Foreign key to sensors table"),
    (
        "sensor_readings",
        "timestamp",
        "Reading timestamp (4-hour intervals, 6 readings per sensor per day)",
    ),
    ("sensor_readings", "value", "Sensor reading value in the sensor unit"),
    (
        "fleet_readiness",
        "readiness_status",
        "MISSION READY, DEGRADED, or NOT MISSION READY",
    ),
    (
        "sensor_health",
        "health_status",
        "NORMAL, WARNING, or ANOMALY based on 2-sigma deviation",
    ),
)


def genie_statements() -> list[tuple[str, str, bool]]:
    """The comments Genie reads, and the grants that let a participant see them.

    These comments are the reason a SQL warehouse is provisioned at all. Lab 4
    asks a Genie space questions in English, and a space with no table or column
    comments answers plausibly rather than correctly. So a comment that did not
    land is a failure here rather than the warning it used to be.

    Only the eight gold tables are granted. Bronze and silver stay in
    ``PIPELINE_SCHEMA`` without SELECT, deliberately, so the schema a
    participant browses holds the eight tables the labs talk about.
    """
    target = f"`{CATALOG}`.`{LAKEHOUSE_SCHEMA}`"
    statements = []
    for table, comment in TABLE_COMMENTS:
        statements.append(
            (
                f"comment on {table}",
                f"COMMENT ON TABLE {target}.{table} IS '{comment}'",
                True,
            )
        )
    for table, column, comment in COLUMN_COMMENTS:
        statements.append(
            (
                f"comment on {table}.{column}",
                f"COMMENT ON COLUMN {target}.{table}.{column} IS '{comment}'",
                True,
            )
        )
    for table in GOLD_TABLES:
        statements.append(
            (
                f"grant select on {table}",
                f"GRANT SELECT ON TABLE {target}.{table} TO {GRANTEE}",
                True,
            )
        )
    return statements


def pipeline_settings(notebook_path: str) -> dict:
    """The DLT pipeline body.

    ``schema`` rather than the deprecated ``target``. That is what puts the
    pipeline in the default publishing mode, which is what lets the notebook
    publish gold into ``LAKEHOUSE_SCHEMA`` while bronze and silver stay in
    ``PIPELINE_SCHEMA``. A pipeline created with ``target`` cannot publish to a
    second schema at all, which is why an existing one is reported by name below
    rather than silently reused as though it were equivalent.

    Serverless, so nothing waits on a cluster to boot before the ETL starts, and
    non-continuous, because this runs once per workspace and the data is static
    for the rest of the class.
    """
    return {
        "name": PIPELINE_NAME,
        "catalog": CATALOG,
        "schema": PIPELINE_SCHEMA,
        "serverless": True,
        "continuous": False,
        "channel": "CURRENT",
        "libraries": [{"notebook": {"path": notebook_path}}],
        "configuration": {
            "pipelines.applyChangesPreviewEnabled": "true",
            "WORKSHOP_CATALOG": CATALOG,
            "WORKSHOP_VOLUME_SCHEMA": VOLUME_SCHEMA,
            "WORKSHOP_VOLUME_NAME": VOLUME_NAME,
            "WORKSHOP_LAKEHOUSE_SCHEMA": LAKEHOUSE_SCHEMA,
        },
    }


# --- The four call shapes ----------------------------------------------------


def execute_sql(workspace, warehouse_id: str, statement: str) -> None:
    """Run one statement and wait for it, or raise naming what failed.

    The API takes a ``wait_timeout`` and answers inline when the statement
    finishes inside it, so most of these return on the first call and the poll
    below is for the few that do not. ``CREATE CATALOG`` on a cold serverless
    warehouse is the one that reliably does not.

    Not marked idempotent for retry purposes, even though every statement here
    is written to be re-runnable. A 500 from this endpoint says nothing about
    whether the statement ran, and the wait below is the wait, not the retry.
    """
    response = workspace.call(
        "POST",
        STATEMENTS_PATH,
        {
            "statement": statement,
            "warehouse_id": warehouse_id,
            "wait_timeout": STATEMENT_WAIT,
        },
    )
    excerpt = voclab.single_line(statement[:120])
    deadline = time.monotonic() + STATEMENT_TIMEOUT_SECONDS

    while True:
        status = response.get("status") or {}
        state = status.get("state") or "UNKNOWN"
        if state == "SUCCEEDED":
            return
        if state not in STATEMENT_RUNNING:
            detail = (status.get("error") or {}).get("message")
            reason = voclab.single_line(detail or f"no reason given, state {state}")
            raise voclab.VoclabError("SQL_FAILED", f"{excerpt} failed: {reason}")
        if time.monotonic() > deadline:
            raise voclab.VoclabError(
                "SQL_TIMEOUT",
                f"{excerpt} was still {state} after {STATEMENT_TIMEOUT_SECONDS}s.",
            )
        statement_id = response.get("statement_id")
        time.sleep(STATEMENT_POLL_SECONDS)
        response = workspace.call(
            "GET", f"{STATEMENTS_PATH}/{statement_id}", idempotent=True
        )


def run_statements(
    workspace,
    warehouse_id: str,
    statements: list[tuple[str, str, bool]],
    label: str,
) -> list[str]:
    """Run a list of statements, returning the descriptions that were refused.

    A required statement that fails raises, naming which one in ``fields`` so
    the record says where the run stopped. An optional one is returned instead,
    because something that was asked for and refused is worth a field even when
    it is not worth failing over.
    """
    skipped = []
    total = len(statements)
    for index, (description, statement, required) in enumerate(statements, start=1):
        voclab.log(f"{label} {index}/{total}: {description}")
        try:
            execute_sql(workspace, warehouse_id, statement)
        except (voclab.VoclabError, voclab.ApiError) as error:
            detail = voclab.single_line(str(error))
            if required:
                raise voclab.VoclabError(
                    "SQL_FAILED",
                    f"{label} ({description}) failed: {detail}",
                    {f"{label}_failed_at": description},
                ) from error
            voclab.log(f"  refused, and not required: {detail}")
            skipped.append(description)
    return skipped


def put_file(workspace, remote_path: str, payload: bytes) -> None:
    """Upload one file into a Unity Catalog volume.

    The only call here that is not JSON in and JSON out, which is why it does
    not go through ``Workspace.call``: the Files API takes the bytes as the
    body. It reuses the same host and bearer token, so there is still one
    credential and one place it comes from.
    """
    quoted = urllib.parse.quote(remote_path)
    request = urllib.request.Request(
        f"{workspace.host}{FILES_PATH}{quoted}?overwrite=true",
        data=payload,
        headers={
            "Authorization": f"Bearer {workspace.token}",
            "Content-Type": "application/octet-stream",
            "User-Agent": voclab.USER_AGENT,
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=voclab.HTTP_TIMEOUT_SECONDS
        ) as response:
            response.read()
    except urllib.error.HTTPError as error:
        detail = voclab.api_detail(str(error.code), voclab.read_error_body(error))
        raise voclab.VoclabError(
            "VOLUME_UPLOAD_FAILED", f"PUT {remote_path} failed: {detail}"
        ) from error
    except (urllib.error.URLError, OSError) as error:
        raise voclab.VoclabError(
            "VOLUME_UPLOAD_FAILED",
            f"PUT {remote_path} could not reach {workspace.host}: {error}",
        ) from error


def import_notebook(workspace, local_path: Path, remote_path: str) -> None:
    """Put the DLT notebook where the pipeline can name it.

    ``overwrite`` is true here, unlike the student notebook import in
    ``voclab.py``, and the difference is deliberate. That one preserves a
    student's own edits across a ``stop``. This one lives in ``/Shared``, nobody
    edits it, and the current definition winning is what keeps the pipeline from
    running last deployment's ETL.
    """
    parent = remote_path.rsplit("/", 1)[0]
    if parent:
        workspace.call("POST", WORKSPACE_MKDIRS_PATH, {"path": parent}, idempotent=True)
    workspace.call(
        "POST",
        WORKSPACE_IMPORT_PATH,
        {
            "path": remote_path,
            "content": base64.b64encode(local_path.read_bytes()).decode("ascii"),
            "format": "SOURCE",
            "language": "PYTHON",
            "overwrite": True,
        },
        idempotent=True,
    )


def find_pipeline(workspace, name: str) -> dict:
    """The pipeline with this name, or an empty dict.

    Name is the idempotency key, the same as it is for the cluster, the
    warehouse and the instance pool, and for the same reason: a ``pipeline_id``
    is minted by one workspace and Vocareum creates a workspace per part, so an
    ID recorded in a course's config is wrong everywhere but where it was
    written. Paged, because ``pipelines/list`` pages.
    """
    token = None
    while True:
        path = PIPELINES_PATH
        if token:
            path = f"{path}?page_token={urllib.parse.quote(token)}"
        payload = workspace.call("GET", path, idempotent=True)
        for pipeline in payload.get("statuses") or []:
            if pipeline.get("name") == name:
                return pipeline
        token = payload.get("next_page_token")
        if not token:
            return {}


def start_and_wait(workspace, pipeline_id: str) -> str:
    """Trigger a full refresh and wait for it, returning the terminal state."""
    workspace.call(
        "POST", f"{PIPELINES_PATH}/{pipeline_id}/updates", {"full_refresh": True}
    )
    deadline = time.monotonic() + PIPELINE_TIMEOUT_SECONDS

    while True:
        payload = workspace.call(
            "GET", f"{PIPELINES_PATH}/{pipeline_id}", idempotent=True
        )
        updates = payload.get("latest_updates") or []
        state = (updates[0].get("state") if updates else "") or "UNKNOWN"
        voclab.log(f"  pipeline {payload.get('state')}, update {state}")
        if state in PIPELINE_DONE:
            return state
        if state in PIPELINE_FAILED:
            raise voclab.VoclabError(
                "PIPELINE_FAILED",
                f"The {PIPELINE_NAME} pipeline finished as {state}. Its event "
                f"log in the workspace names the table that failed.",
                {"pipeline_id": pipeline_id},
            )
        if time.monotonic() > deadline:
            raise voclab.VoclabError(
                "PIPELINE_TIMEOUT",
                f"The {PIPELINE_NAME} pipeline was still {state} after "
                f"{PIPELINE_TIMEOUT_SECONDS}s.",
                {"pipeline_id": pipeline_id},
            )
        time.sleep(PIPELINE_POLL_SECONDS)


# --- Finding what the courseware unpacked to ---------------------------------


def resolve_data_dir() -> Path:
    """Return the courseware data directory, or fail naming the one place it is.

    One path rather than a search. ``lab/courseware/aircraft_digital_twin_data``
    goes up in the same hash-verified archive as the hooks, so if it is not at
    :data:`DATA_DIR` the deployment is wrong and that is what the record should
    say. The override exists for a laptop run against a checkout, not as a
    fallback: a fallback is how a run provisions from a directory nobody meant
    and reports success.
    """
    override = (os.environ.get(DATA_DIR_VAR) or "").strip()
    path = Path(override or DATA_DIR)
    if path.is_dir() and any(path.glob("*.csv")):
        return path
    raise voclab.VoclabError(
        "MISSING_COURSEWARE",
        f"{path} does not hold the workshop CSVs. They travel in the lab "
        f"archive as courseware/aircraft_digital_twin_data, so re-run "
        f"dbx-vocareum-upload, or set {DATA_DIR_VAR} to point elsewhere.",
    )


def resolve_dlt_notebook() -> Path:
    """Return the DLT notebook, on the same reasoning as the data directory."""
    override = (os.environ.get(DLT_NOTEBOOK_VAR) or "").strip()
    path = Path(override or DLT_NOTEBOOK)
    if path.is_file():
        return path
    raise voclab.VoclabError(
        "MISSING_DLT_NOTEBOOK",
        f"{path} is not there. dlt_fleet_etl.py travels in the lab archive as "
        f"courseware/dlt_fleet_etl.py, so re-run dbx-vocareum-upload, or set "
        f"{DLT_NOTEBOOK_VAR} to point elsewhere.",
    )


def data_files(data_dir: Path) -> list[Path]:
    """Everything the volume has to hold: the CSVs, then the manuals.

    A missing manual is a failure rather than the warning it used to be. Lab 3
    loads them out of the volume by name, so a run that uploaded 22 CSVs and no
    manual provisions cleanly and breaks two labs later.
    """
    found = []
    for pattern in DATA_GLOBS:
        matched = sorted(data_dir.glob(pattern))
        if not matched:
            raise voclab.VoclabError(
                "MISSING_COURSEWARE",
                f"{data_dir} holds no {pattern}, so the volume would come up "
                f"without files the labs read out of it.",
            )
        found.extend(matched)
    return found


# --- The stages --------------------------------------------------------------


def resolve_warehouse_id(workspace, args: argparse.Namespace) -> str:
    """The warehouse to run SQL on, found by name, the key everything else uses.

    ``voclab.py warehouse-ensure`` has already created it from
    ``workspace_init.sh`` by the time this runs, so this looks it up rather than
    creating a second one. Absent is a failure rather than a fallback onto
    whatever warehouse happens to be running, because "whatever is running" is
    how a class's DDL lands on an unrelated team's warehouse.
    """
    name = voclab.resolve_course_value(
        getattr(args, "warehouse_name", None), voclab.WAREHOUSE_NAME_VAR
    )
    if not name:
        raise voclab.VoclabError(
            "MISSING_WAREHOUSE_NAME",
            f"No warehouse name was given and {voclab.WAREHOUSE_NAME_VAR} is "
            f"unset, so there is nothing to run SQL on. course.env is where "
            f"that name is set, and workspace_init.sh creates it from there.",
        )
    warehouse = voclab.find_warehouse(workspace, name)
    if not warehouse:
        raise voclab.VoclabError(
            "MISSING_WAREHOUSE",
            f"No SQL warehouse named {name} exists in this workspace. It is "
            f"created by voclab.py warehouse-ensure from workspace_init.sh, so "
            f"this means that step did not run or did not succeed.",
        )
    return warehouse["id"]


def provision_infrastructure(workspace, warehouse_id: str) -> dict:
    voclab.log("creating the catalog, the four schemas and the volume")
    # The return value is discarded because every statement in this stage is
    # required, so a refusal raises rather than lands in the list. The stage used
    # to report an ``infrastructure_refused`` field for the one optional grant;
    # that grant is gone and no reader ever consumed the field.
    run_statements(
        workspace, warehouse_id, infrastructure_statements(), "infrastructure"
    )
    return {
        "catalog": CATALOG,
        "volume_path": VOLUME_PATH,
    }


def provision_data(workspace) -> dict:
    data_dir = resolve_data_dir()
    files = data_files(data_dir)
    total = len(files)
    voclab.log(f"uploading {total} files from {data_dir} to {VOLUME_PATH}")
    for index, path in enumerate(files, start=1):
        voclab.log(f"  {index}/{total}: {path.name}")
        put_file(workspace, f"{VOLUME_PATH}/{path.name}", path.read_bytes())
    return {"data_dir": str(data_dir), "data_files_uploaded": total}


def grant_pipeline_view(workspace, pipeline_id: str) -> str:
    """Let participants watch the pipeline whose output they are about to read.

    Recorded rather than fatal. The tables are what the labs need and they are
    granted separately; being able to open the pipeline page is worth having and
    is not worth failing a whole workspace over.
    """
    granted = []
    for group in PARTICIPANT_GROUPS:
        try:
            workspace.call(
                "PATCH",
                f"/api/2.0/permissions/pipelines/{pipeline_id}",
                {
                    "access_control_list": [
                        {"group_name": group, "permission_level": "CAN_VIEW"}
                    ]
                },
                idempotent=True,
            )
            granted.append(group)
        except voclab.ApiError as error:
            detail = voclab.single_line(str(error))
            voclab.log(f"  CAN_VIEW to '{group}' refused: {detail}")
    return ", ".join(granted) if granted else "nobody"


def provision_pipeline(workspace) -> dict:
    notebook = resolve_dlt_notebook()
    voclab.log(f"importing {notebook} to {DLT_NOTEBOOK_WORKSPACE_PATH}")
    import_notebook(workspace, notebook, DLT_NOTEBOOK_WORKSPACE_PATH)

    existing = find_pipeline(workspace, PIPELINE_NAME)
    if existing:
        pipeline_id = existing["pipeline_id"]
        action = "found"
        voclab.log(
            f"the {PIPELINE_NAME} pipeline already exists ({pipeline_id}). If it "
            f"was created with the legacy target field it cannot publish gold to "
            f"a second schema; delete it and run this again."
        )
    else:
        created = workspace.call(
            "POST", PIPELINES_PATH, pipeline_settings(DLT_NOTEBOOK_WORKSPACE_PATH)
        )
        pipeline_id = created["pipeline_id"]
        action = "created"
        voclab.log(f"created the {PIPELINE_NAME} pipeline ({pipeline_id})")

    visible_to = grant_pipeline_view(workspace, pipeline_id)
    voclab.log("starting a full refresh; this is the several minutes of the run")
    state = start_and_wait(workspace, pipeline_id)
    return {
        "pipeline_id": pipeline_id,
        "pipeline_action": action,
        "pipeline_state": state,
        "pipeline_visible_to": visible_to,
    }


def provision_genie(workspace, warehouse_id: str) -> dict:
    voclab.log("adding the Genie comments and granting the gold tables")
    run_statements(workspace, warehouse_id, genie_statements(), "genie")
    return {"gold_tables": len(GOLD_TABLES), "genie_comments": "applied"}


def provision(workspace, args: argparse.Namespace) -> dict:
    """Everything, in the order each stage needs the one before it.

    The order is not a preference. The volume has to exist before a file can go
    in it, the data has to be there before the pipeline can read it, and a gold
    table has to exist before a comment can be attached to it.
    """
    warehouse_id = resolve_warehouse_id(workspace, args)
    fields = {"warehouse_id": warehouse_id}
    fields.update(provision_infrastructure(workspace, warehouse_id))
    fields.update(provision_data(workspace))
    fields.update(provision_pipeline(workspace))
    fields.update(provision_genie(workspace, warehouse_id))
    return fields


def run(args: argparse.Namespace) -> dict:
    """Dispatch one stage."""
    workspace = voclab.build_workspace(args)
    if args.command == "provision":
        return provision(workspace, args)
    if args.command == "upload-data":
        return provision_data(workspace)
    if args.command == "pipeline":
        return provision_pipeline(workspace)

    # The two that need a warehouse and nothing else.
    warehouse_id = resolve_warehouse_id(workspace, args)
    fields = {"warehouse_id": warehouse_id}
    if args.command == "infrastructure":
        fields.update(provision_infrastructure(workspace, warehouse_id))
    else:
        fields.update(provision_genie(workspace, warehouse_id))
    return fields


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="workshop.py",
        description=(
            "Provision this workshop's Databricks objects: the catalog and "
            "volume, the courseware data, the DLT pipeline, and the comments "
            "and grants a Genie space reads."
        ),
    )
    parser.add_argument(
        "--host", help="Workspace URL. Defaults to VOC_DB_WORKSPACE_URL."
    )
    parser.add_argument("--token", help="Bearer token. Defaults to VOC_DB_API_TOKEN.")
    parser.add_argument(
        "--warehouse-name",
        help=(
            "The SQL warehouse to run statements on. Defaults to "
            "VOC_COURSE_WAREHOUSE_NAME, which is what created it."
        ),
    )
    # Every stage is separately runnable because the pipeline stage takes
    # several minutes, and a deployer debugging the Genie comments should not
    # have to re-run the ETL to reach them.
    parser.add_argument(
        "command",
        choices=("provision", "infrastructure", "upload-data", "pipeline", "genie"),
        nargs="?",
        default="provision",
        help="Which stage to run. Default is provision, which runs them all.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. See the module docstring for the output contract."""
    args = parse_args(argv)
    try:
        voclab.emit(run(args))
        return EXIT_OK
    except voclab.VoclabError as error:
        voclab.emit(dict(error.fields, error_code=error.code, message=error.message))
        return EXIT_FAILED
    except voclab.ApiError as error:
        voclab.emit(
            {"error_code": "API_ERROR", "message": voclab.single_line(str(error))}
        )
        return EXIT_FAILED
    except Exception as error:
        # Broad on purpose, for the same reason voclab.py's is. A traceback that
        # exits non-zero having emitted nothing produces a lab that failed for
        # no stated reason, which is the exact thing voc_fail exists to prevent.
        # The traceback still goes to stderr, where the console log keeps it.
        traceback.print_exc()
        voclab.emit(
            {
                "error_code": "UNEXPECTED_ERROR",
                "message": f"{type(error).__name__}: {error}",
            }
        )
        return EXIT_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
