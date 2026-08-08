#!/usr/bin/env python3
"""Publish the lab notebooks into ``/Shared`` for a non-Vocareum workshop.

This is one of the two jobs the retired ``databricks_setup`` CLI did that
nothing else covers. Everything else it did is now either ``lab/workshop.py``
(the catalog, the schemas, the volume, the courseware, the tables and the Genie
comments) or ``voclab.py`` in ``dbx-vocareum-tools`` (the cluster, the
libraries, the warehouse, and the per-student notebook import).

Why this is not ``voclab.py notebook-import``. That command targets
``/Users/<email>``, imports one course-named notebook, and **skips** a file that
is already there so a student's edits survive a ``stop``. This targets
``/Shared``, imports the whole lab set across six folders, and **overwrites**,
because nobody edits ``/Shared`` and the current definition winning is the point
of running it. Two different objects with two different rules, not two copies of
one.

Why the file list lives here. ``VOC_COURSE_NOTEBOOKS`` in ``lab/course.env``
names what each *student* gets on their own cluster, which is the smoke test and
nothing else. The instructor-facing ``/Shared`` tree is a different set with a
different folder layout, so stating it here duplicates no definition.

The output contract is ``lab/workshop.py``'s, which is ``voclab.py``'s:
narration to **stderr**, ``key=value`` lines on **stdout**.

Credentials come from ``voclab.build_workspace``: ``--host`` and ``--token``
first, then ``VOC_DB_WORKSPACE_URL`` / ``VOC_DB_API_TOKEN``, then
``DATABRICKS_HOST`` / ``DATABRICKS_TOKEN``. There is no ``.databrickscfg``
profile support, deliberately: one credential resolved in one place, the same
one the Vocareum hooks use.

Exit codes: ``0`` ok, ``1`` a failure carrying an ``error_code``.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import traceback
import urllib.parse
from pathlib import Path

from workshop_module import REPO_ROOT, import_workshop

workshop = import_workshop()
voclab = workshop.voclab

EXIT_OK = 0
EXIT_FAILED = 1

WORKSPACE_MKDIRS_PATH = "/api/2.0/workspace/mkdirs"
WORKSPACE_IMPORT_PATH = "/api/2.0/workspace/import"
WORKSPACE_DELETE_PATH = "/api/2.0/workspace/delete"
WORKSPACE_LIST_PATH = "/api/2.0/workspace/list"

# The participant-facing tree. Distinct from ``workshop.DLT_NOTEBOOK_WORKSPACE_PATH``
# (``/Shared/workshop/dlt_fleet_etl``), which is the pipeline's source and is
# owned by ``workshop.py``. Nothing may be added here that ``workshop.py``
# already names.
SHARED_FOLDER = os.environ.get(
    "WORKSHOP_SHARED_FOLDER", "/Shared/databricks-neo4j-workshop"
)

# (repository directory, files, workspace subfolder). Appendix A keeps its
# per-topic subfolders so the workspace layout matches the repository and the
# appendix README that describes it.
NOTEBOOKS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "Lab_2_Databricks_ETL_Neo4j",
        ("01_aircraft_etl_to_neo4j.ipynb", "02_gds_knn_aircraft.ipynb"),
        "Lab_2_Databricks_ETL_Neo4j",
    ),
    (
        "Lab_3_Semantic_Search",
        (
            "01_data_and_embeddings.ipynb",
            "02_graphrag_retrievers.ipynb",
            "03_hybrid_retrievers.ipynb",
            "data_utils.py",
        ),
        "Lab_3_Semantic_Search",
    ),
    (
        "Appendix_A_GDS_Graph_Analytics/centrality",
        ("04_gds_pagerank_airports.ipynb",),
        "Appendix_A_GDS_Graph_Analytics/centrality",
    ),
    (
        "Appendix_A_GDS_Graph_Analytics/community_detection",
        ("02_gds_louvain_maintenance.ipynb",),
        "Appendix_A_GDS_Graph_Analytics/community_detection",
    ),
    (
        "Appendix_A_GDS_Graph_Analytics/similarity",
        ("05_gds_node_similarity_aircraft.ipynb",),
        "Appendix_A_GDS_Graph_Analytics/similarity",
    ),
    (
        "workshop-setup/neo4j_mcp_connection",
        ("mcp-set-flag.ipynb",),
        "neo4j_mcp_connection",
    ),
)

# Overwriting an ``.ipynb`` in place leaves the previous run's outputs and
# metadata behind in this one folder, which is the one participants are told to
# read a flag out of. Deleting first is cheaper than explaining a stale flag.
DELETE_BEFORE_UPLOAD = frozenset({"neo4j_mcp_connection"})


def upload_files() -> list[tuple[Path, str]]:
    """Return ``(local file, workspace subfolder)`` for everything to publish.

    A missing file is a failure rather than a skip. The list above is what the
    workshop is, so a checkout that cannot supply it should say so here rather
    than publish a partial tree that looks complete in the workspace.
    """
    found: list[tuple[Path, str]] = []
    for directory, names, subfolder in NOTEBOOKS:
        for name in names:
            local = REPO_ROOT / directory / name
            if not local.is_file():
                raise voclab.VoclabError(
                    "MISSING_NOTEBOOK",
                    f"{local} is not there, so {SHARED_FOLDER} would come up "
                    f"missing a notebook a lab walks through.",
                )
            found.append((local, subfolder))
    return found


def import_one(workspace, local_path: Path, remote_path: str) -> None:
    """Import one file, choosing the format from its suffix.

    ``.ipynb`` goes up as ``JUPYTER`` and carries its own language; a ``.py``
    helper goes up as ``SOURCE``, which requires the language be stated. Sending
    a notebook as ``SOURCE`` succeeds and produces a workspace file full of JSON,
    which is why this branches rather than picking one.
    """
    body: dict = {
        "path": remote_path,
        "content": base64.b64encode(local_path.read_bytes()).decode("ascii"),
        "overwrite": True,
    }
    if local_path.suffix == ".ipynb":
        body["format"] = "JUPYTER"
    else:
        body["format"] = "SOURCE"
        body["language"] = "PYTHON"
    workspace.call("POST", WORKSPACE_IMPORT_PATH, body, idempotent=True)


def delete_folder(workspace, path: str) -> bool:
    """Delete a workspace folder and everything under it. True if one was there.

    Absent is the goal state, so a folder that was never created is success.
    """
    try:
        workspace.call(
            "POST",
            WORKSPACE_DELETE_PATH,
            {"path": path, "recursive": True},
            idempotent=True,
        )
    except voclab.ApiError as error:
        if voclab.names_error_code(error, voclab.NOT_FOUND_ERROR_CODE):
            return False
        raise
    return True


def list_folder(workspace, path: str) -> list[str]:
    """Workspace paths directly under ``path``, or an empty list if it is absent."""
    quoted = urllib.parse.quote(path)
    try:
        payload = workspace.call(
            "GET", f"{WORKSPACE_LIST_PATH}?path={quoted}", idempotent=True
        )
    except voclab.ApiError as error:
        if voclab.names_error_code(error, voclab.NOT_FOUND_ERROR_CODE):
            return []
        raise
    entries = payload.get("objects") or []
    return [entry["path"] for entry in entries if entry.get("path")]


def sync(workspace) -> dict:
    """Publish every notebook and report how many the workspace then holds."""
    files = upload_files()
    subfolders = sorted({subfolder for _, subfolder in files})

    for subfolder in subfolders:
        if subfolder in DELETE_BEFORE_UPLOAD:
            target = f"{SHARED_FOLDER}/{subfolder}"
            if delete_folder(workspace, target):
                voclab.log(f"removed {target} so it re-imports clean")

    for subfolder in subfolders:
        workspace.call(
            "POST",
            WORKSPACE_MKDIRS_PATH,
            {"path": f"{SHARED_FOLDER}/{subfolder}"},
            idempotent=True,
        )

    total = len(files)
    voclab.log(f"importing {total} files into {SHARED_FOLDER}")
    for index, (local_path, subfolder) in enumerate(files, start=1):
        remote_path = f"{SHARED_FOLDER}/{subfolder}/{local_path.stem}"
        voclab.log(f"  {index}/{total}: {subfolder}/{local_path.name}")
        import_one(workspace, local_path, remote_path)

    present = 0
    for subfolder in subfolders:
        present += len(list_folder(workspace, f"{SHARED_FOLDER}/{subfolder}"))

    return {
        "shared_folder": SHARED_FOLDER,
        "notebooks_uploaded": total,
        "notebooks_present": present,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sync_notebooks.py",
        description=(
            "Publish this workshop's lab notebooks into the shared workspace "
            "folder participants read them from."
        ),
    )
    parser.add_argument(
        "--host", help="Workspace URL. Defaults to DATABRICKS_HOST."
    )
    parser.add_argument("--token", help="Bearer token. Defaults to DATABRICKS_TOKEN.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        voclab.emit(sync(voclab.build_workspace(args)))
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
        # Broad for the same reason ``workshop.py``'s is: a traceback that exits
        # non-zero having emitted nothing leaves a run that failed for no stated
        # reason. The traceback still reaches stderr.
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
