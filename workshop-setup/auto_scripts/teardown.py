#!/usr/bin/env python3
"""Delete everything ``lab/workshop.py`` creates, plus the shared notebook tree.

The second of the two jobs the retired ``databricks_setup`` CLI did that nothing
else covers. Vocareum reclaims its own workspaces, so this exists for the
non-Vocareum case: a workspace an instructor provisioned by hand and wants back.

Every name it deletes is read from ``lab/workshop.py``. That is the whole design
of this file. The version it replaces held its own ``VolumeConfig`` with its own
copy of the catalog, schema and volume names, which meant a teardown could
silently miss what a differently-named provisioner had created. It also predated
the DLT pipeline, so it left ``aircraft_pipeline`` and the ``Fleet Digital Twin
ETL`` pipeline behind: dropping the gold schema under a pipeline that still
exists leaves the next provision run adopting a pipeline whose tables are gone.

Order is deliberate. The pipeline goes before the schemas it writes into, and
the catalog goes last with ``force`` so that anything the earlier steps could not
see is still reclaimed rather than left billing.

Output contract, credentials and exit codes are ``lab/workshop.py``'s. See
``sync_notebooks.py`` for the same note in full.
"""

from __future__ import annotations

import argparse
import sys
import traceback
import urllib.parse

from sync_notebooks import SHARED_FOLDER, delete_folder
from workshop_module import import_workshop

workshop = import_workshop()
voclab = workshop.voclab

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_REFUSED = 3

CATALOGS_PATH = "/api/2.1/unity-catalog/catalogs"
SCHEMAS_PATH = "/api/2.1/unity-catalog/schemas"
VOLUMES_PATH = "/api/2.1/unity-catalog/volumes"
WORKSPACE_DELETE_PATH = "/api/2.0/workspace/delete"

# ``aircraft`` is both the volume schema and the gold schema in this course, so
# the set collapses to two. Reading them from ``workshop`` rather than restating
# them is what keeps that true if the course ever splits them apart.
SCHEMAS = (
    workshop.PIPELINE_SCHEMA,
    workshop.LAKEHOUSE_SCHEMA,
    workshop.VOLUME_SCHEMA,
)


def _absent(error: voclab.ApiError) -> bool:
    """Whether a failed delete means the object was already gone.

    Unity Catalog and the workspace API do not agree on which code they return
    for a missing object, so both are matched. Everything else is re-raised: a
    permission failure reported as "already deleted" is how a teardown reports
    success over a catalog that is still there and still billing.
    """
    text = str(error)
    return voclab.NOT_FOUND_ERROR_CODE in text or "NOT_FOUND" in text


def delete_pipeline(workspace) -> str:
    """Delete the DLT pipeline by name, returning what happened.

    By name because a ``pipeline_id`` is minted per workspace, which is the same
    reason ``workshop.find_pipeline`` exists. Calling it rather than re-listing
    means one paging implementation, not two.
    """
    pipeline = workshop.find_pipeline(workspace, workshop.PIPELINE_NAME)
    if not pipeline:
        return "absent"
    pipeline_id = pipeline.get("pipeline_id") or ""
    voclab.log(f"deleting pipeline {workshop.PIPELINE_NAME} ({pipeline_id})")
    try:
        workspace.call(
            "DELETE", f"{workshop.PIPELINES_PATH}/{pipeline_id}", idempotent=True
        )
    except voclab.ApiError as error:
        if _absent(error):
            return "absent"
        raise
    return pipeline_id


def delete_volume(workspace) -> bool:
    """Delete the raw data volume. True if one was there."""
    full_name = f"{workshop.CATALOG}.{workshop.VOLUME_SCHEMA}.{workshop.VOLUME_NAME}"
    voclab.log(f"deleting volume {full_name}")
    try:
        workspace.call(
            "DELETE",
            f"{VOLUMES_PATH}/{urllib.parse.quote(full_name)}",
            idempotent=True,
        )
    except voclab.ApiError as error:
        if _absent(error):
            return False
        raise
    return True


def delete_schemas(workspace) -> list[str]:
    """Force-drop each schema, returning the ones that were there.

    ``force`` because a schema holding tables refuses a plain delete, and every
    table in these three was created by the provisioner this undoes. Deduplicated
    because the course currently points two of its three names at ``aircraft``.
    """
    dropped = []
    for schema in dict.fromkeys(SCHEMAS):
        full_name = f"{workshop.CATALOG}.{schema}"
        voclab.log(f"dropping schema {full_name}")
        try:
            workspace.call(
                "DELETE",
                f"{SCHEMAS_PATH}/{urllib.parse.quote(full_name)}?force=true",
                idempotent=True,
            )
        except voclab.ApiError as error:
            if _absent(error):
                continue
            raise
        dropped.append(schema)
    return dropped


def delete_catalog(workspace) -> bool:
    """Force-delete the catalog. True if one was there.

    Last and with ``force``, so that a schema the steps above could not see is
    still reclaimed. A catalog left behind is the one piece of this teardown that
    keeps costing money after the class is over.
    """
    voclab.log(f"deleting catalog {workshop.CATALOG}")
    try:
        workspace.call(
            "DELETE",
            f"{CATALOGS_PATH}/{urllib.parse.quote(workshop.CATALOG)}?force=true",
            idempotent=True,
        )
    except voclab.ApiError as error:
        if _absent(error):
            return False
        raise
    return True


def delete_dlt_notebook(workspace) -> bool:
    """Remove the pipeline's source notebook from ``/Shared``."""
    path = workshop.DLT_NOTEBOOK_WORKSPACE_PATH
    voclab.log(f"deleting {path}")
    try:
        workspace.call(
            "POST",
            WORKSPACE_DELETE_PATH,
            {"path": path, "recursive": False},
            idempotent=True,
        )
    except voclab.ApiError as error:
        if _absent(error):
            return False
        raise
    return True


def teardown(workspace) -> dict:
    """Run every step, in the order that leaves nothing depending on a deletion."""
    shared_gone = delete_folder(workspace, SHARED_FOLDER)
    if shared_gone:
        voclab.log(f"deleted {SHARED_FOLDER}")
    pipeline = delete_pipeline(workspace)
    notebook_gone = delete_dlt_notebook(workspace)
    volume_gone = delete_volume(workspace)
    schemas = delete_schemas(workspace)
    catalog_gone = delete_catalog(workspace)

    return {
        "shared_folder_deleted": "yes" if shared_gone else "absent",
        "pipeline_deleted": pipeline,
        "dlt_notebook_deleted": "yes" if notebook_gone else "absent",
        "volume_deleted": "yes" if volume_gone else "absent",
        "schemas_deleted": ", ".join(schemas) if schemas else "none",
        "catalog_deleted": "yes" if catalog_gone else "absent",
    }


def targets() -> list[str]:
    """What is about to be deleted, for the confirmation prompt."""
    return [
        f"workspace folder {SHARED_FOLDER}",
        f"workspace notebook {workshop.DLT_NOTEBOOK_WORKSPACE_PATH}",
        f"pipeline {workshop.PIPELINE_NAME}",
        f"volume {workshop.CATALOG}.{workshop.VOLUME_SCHEMA}.{workshop.VOLUME_NAME}",
        f"schemas {', '.join(dict.fromkeys(SCHEMAS))} in {workshop.CATALOG}",
        f"catalog {workshop.CATALOG} and everything left in it",
    ]


def confirm() -> bool:
    """Ask before deleting a catalog, unless there is nobody to ask.

    A non-interactive run without ``--yes`` refuses rather than proceeding.
    Defaulting to yes here would make a scripted invocation that forgot the flag
    delete a live class's catalog.
    """
    print("teardown.py will delete:", file=sys.stderr)
    for target in targets():
        print(f"  {target}", file=sys.stderr)
    if not sys.stdin.isatty():
        print(
            "teardown.py: stdin is not a terminal and --yes was not given.",
            file=sys.stderr,
        )
        return False
    return input("Proceed? Type yes to continue: ").strip().lower() == "yes"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="teardown.py",
        description=(
            "Delete this workshop's catalog, schemas, volume, DLT pipeline and "
            "shared notebooks from a workspace provisioned outside Vocareum."
        ),
    )
    parser.add_argument(
        "--host", help="Workspace URL. Defaults to DATABRICKS_HOST."
    )
    parser.add_argument("--token", help="Bearer token. Defaults to DATABRICKS_TOKEN.")
    parser.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.yes and not confirm():
        voclab.emit({"error_code": "REFUSED", "message": "Nothing was deleted."})
        return EXIT_REFUSED
    try:
        voclab.emit(teardown(voclab.build_workspace(args)))
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
        traceback.print_exc()
        voclab.emit(
            {
                "error_code": "UNEXPECTED_ERROR",
                "message": f"{type(error).__name__}: {error}",
            }
        )
        return EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
