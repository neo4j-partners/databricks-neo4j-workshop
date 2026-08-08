# Vocareum setup: Neo4j + Databricks workshop

The admin procedure for running this course on Vocareum lives in the `dbx-vocareum` tooling repository. It is not repeated here. A second copy of a procedure drifts, and this one already did: an older copy of the setup code defined 4 gold tables where the current one defines 8.

This page says what is in this directory, where to go for the procedure, and what the tooling does not cover.

The tooling repository is [neo4j-partners/dbx-vocareum](https://github.com/neo4j-partners/dbx-vocareum). This repository depends on it, declared in `pyproject.toml` as `dbx-vocareum-tools @ git+https://github.com/neo4j-partners/dbx-vocareum.git`.

Links below assume `dbx-vocareum` is checked out beside this repository.

## What is in this directory

| Path | What it is |
| --- | --- |
| `docs/README.md` | The participant-facing page Vocareum renders in the Readme panel. It links to the published workshop site and tells a student where to start. |

That is all of it. What a student is handed is named in `lab/course.env` at the repository root, and `dbx-vocareum-upload` sends it.

A `courseware/` directory sat here until 2026-08-08 holding the earlier manual upload procedure's assets: a `.dat` and a byte-identical `.dbc` archive, a course `.cfg`, a copy of the aircraft data zip, a second copy of `dlt_fleet_etl.py`, and copies of the Lab 2 and Lab 3 notebooks. Nothing read any of it. It was deleted rather than kept for reference, because a second copy of the notebooks is a second copy that drifts, and that one already had: its `data_utils.py` diverged from the top-level file at the 2026-08-08 secret-scope change.

Where each of those things lives now:

| Was in `courseware/` | Where it is now |
| --- | --- |
| `neo4j-databricks-workshop.cfg` library list | `VOC_COURSE_LIBRARIES` in `lab/course.env` |
| The `.dat` and `.dbc` archives, and the notebook copies under `data/` | `VOC_COURSE_NOTEBOOKS` in `lab/course.env` names what ships, and `dbx-vocareum-upload lab/` sends it |
| `dlt_fleet_etl.py` | `lab/courseware/dlt_fleet_etl.py`, which is the copy `lab/workshop.py` has always pointed at |
| `aircraft_digital_twin_data.zip` | Nothing replaces it. The files it held are tracked at `workshop-setup/aircraft_digital_twin_data/`, so a clone already has them and there is nothing to download. `workshop.py upload-data` uploads that directory to the volume file by file, and `lab/courseware/aircraft_digital_twin_data` symlinks it for the hook archive. Neither path ever reads a zip. |

## Where the admin procedure lives

| I want to | Read |
| --- | --- |
| Do any admin task, start to finish | [`dbx-vocareum/README.md`](../../dbx-vocareum/README.md) |
| Understand the four hooks and what each one is handed | [`dbx-vocareum/docs/databricks-labs.md`](../../dbx-vocareum/docs/databricks-labs.md) |
| Know what the service principal may do, and what a student may do | [`dbx-vocareum/docs/permissions.md`](../../dbx-vocareum/docs/permissions.md) |
| Get the lab up to Vocareum | [`dbx-vocareum/docs/deploying.md`](../../dbx-vocareum/docs/deploying.md) |
| Find out why a lab came up empty | [`dbx-vocareum/docs/diagnosing.md`](../../dbx-vocareum/docs/diagnosing.md) |
| Cut the wait a student spends on compute | [`dbx-vocareum/docs/pre-warm.md`](../../dbx-vocareum/docs/pre-warm.md) |
| Call the Vocareum REST API from code | [`dbx-vocareum/docs/vocareum-api.md`](../../dbx-vocareum/docs/vocareum-api.md) |
| Know where Neo4j runs, and why it is not inside the workspace | [`dbx-vocareum/docs/neo4j-aura.md`](../../dbx-vocareum/docs/neo4j-aura.md) |

`dbx-vocareum/docs/permissions.md` is the single source of truth for what each principal may do. Do not restate a permission result here.

## What this course owns

Three things belong to this course rather than to the tooling.

### `lab/` at the repository root

Four hooks, `workshop.py`, and `course.env`. Every value specific to this workshop lives in `course.env`: the cluster runtime and node type, the eleven libraries, the catalog name and its managed location, the notebook list, and the shared warehouse. Change a course value there. Do not change it in a hook, and do not change it in the tooling.

Vocareum runs four hooks by name and ignores anything else in `/voc/scripts`. Each one is a shell script this course owns, scaffolded once by `dbx-vocareum-init` and edited from then on.

- **`workspace_init.sh`: the workspace is built here, once.** It runs one time per workspace Vocareum creates, before any student exists. It ensures the SQL warehouse, then hands off to `voc_python workshop.py provision`, which creates the catalog with its managed location, both schemas, the volume, the uploaded data, the DLT pipeline, and the Genie comments and grants. Everything a class shares is built by this hook. Redeploying `/voc/scripts` does not re-run it. `Rerun Init` on the admin Workspaces page does.
- **`lab_setup.sh`: pre-warm, and it deliberately builds nothing.** It runs when Vocareum warms a lab ahead of a student. It reports the environment and stops there. No cluster is created, because the cluster name is derived from the student identity Vocareum mints at session start, so a cluster warmed here would carry a name the student's own session never looks for.
- **`user_setup.sh`: the student's session, and the only required hook.** It runs when a student clicks start. It calls `cluster-ensure` to create or restart the per-student cluster, then `notebook-import` to put the course's notebooks in the student's home folder, then writes the landing page into `$VOC_IPC_DATA_FILE`, which is what redirects the student's browser. It is the only hook that writes that file. A lab with no `user_setup.sh` starts successfully and does nothing.
- **`lab_end.sh`: reclaim whatever is still billing.** It runs on stop and on terminate, and it reads `VOC_END_LAB_BEHAVIOR` before deciding anything. On a stop the student's work is preserved for their next session, so the cluster is terminated and nothing is deleted. On a terminate the environment reverts, so the cluster is deleted outright. Notebooks are left alone in both cases. Anything billable that `user_setup.sh` created has to be reclaimed here, because Vocareum removes only what Vocareum created.

### `expected.json` at the repository root

The ship gate manifest. `uv run dbx-vocareum-diagnose --expect expected.json` reads it and fails when a named object is missing. It sits outside `lab/` on purpose, because everything under `lab/` is uploaded to `/voc/scripts` and this file is for whoever deploys rather than for the hooks.

### The manual pre-workshop steps

The hooks build the Databricks side. They do not build the Neo4j side or the Lab 4 agent wiring, and that is deliberate.

- **Participant Aura instances.** Each participant creates their own Aura Free instance in Lab 1. Nothing to pre-provision.
- **Reference Aura instance.** Lab 4 queries one administrator-managed instance instead of a participant's. Load it before the workshop with `workshop-setup/populate_aircraft_db`. A shared reference instance means every participant gets the full graph in Lab 4 no matter how far they got in Lab 2.
- **The `neo4j_agentcore_mcp` Unity Catalog connection.** Lab 4 Part B needs an HTTP connection to a Neo4j MCP server backed by the reference instance. `workshop-setup/MCP-MANUAL-SETUP.md` is the walkthrough. Participants verify and use the connection. They never create it.
- **Genie spaces.** Each participant creates their own in Lab 4 Part A. Do not pre-create a shared one, because each participant needs to edit their space's instructions.

## Setting up a new course

This workshop is one course. The tooling runs any number of them, and a second course does not copy this one. What follows is the shortest path from an empty repository to a lab a student can start. [`dbx-vocareum/docs/deploying.md`](../../dbx-vocareum/docs/deploying.md) has the same ground in full.

### 1. Declare the tooling as a dependency

In the new course's `pyproject.toml`:

```toml
[dependency-groups]
dev = [
  "dbx-vocareum-tools @ git+https://github.com/neo4j-partners/dbx-vocareum.git",
]
```

```bash
uv sync --group dev
```

The dev group, because nothing the course teaches imports it. It is the deployer's toolchain. A dependency rather than a copied folder, because then the shell and Python runtime the hooks call has exactly one owner and an upgrade is a version bump instead of a merge.

No revision is pinned in the declaration, so `uv.lock` holds whichever commit the default branch pointed at when the lock was written. Bump it whenever the tooling changes:

```bash
uv sync --group dev --upgrade-package dbx-vocareum-tools
```

This matters more than it looks. A fix inside the tooling's runtime changes no file in the course, so a course that redeploys without bumping uploads the old runtime and hash-verifies it successfully.

### 2. Scaffold the hooks

```bash
uv run dbx-vocareum-init lab/
```

That writes the four hooks, a `course.env` to fill in, and a README naming the rules the hooks depend on. From then on those files belong to the course. `--force` rewrites the hooks and never touches `course.env`, because `course.env` is the one file here holding values a human typed.

### 3. Fill in `lab/course.env`

Course values reach the hooks through this file and through nothing else. Every key is optional and every one has a default, so a course that names none of them still runs.

| Key | What it sets |
| --- | --- |
| `VOC_COURSE_SPARK_VERSION` | The cluster's Databricks runtime |
| `VOC_COURSE_NODE_TYPE` | The instance type the student's cluster runs on |
| `VOC_COURSE_AUTOTERMINATION_MINUTES` | How long an idle student cluster bills before it stops itself |
| `VOC_COURSE_LIBRARIES` | Libraries installed on the cluster, as `pypi:` and `maven:` entries |
| `VOC_COURSE_CATALOG` | The Unity Catalog catalog the course builds |
| `VOC_COURSE_NOTEBOOKS` | What the student is handed. A folder name, or a comma-separated list of files |
| `VOC_COURSE_WAREHOUSE_NAME`, `_SIZE`, `_AUTO_STOP_MINUTES` | The SQL warehouse `workspace_init.sh` ensures |

`VOC_COURSE_NOTEBOOKS` accepts paths, and the folder structure survives into the student's home folder. Naming `Lab_2/01_intro.ipynb` hands the student `Lab_2/01_intro`. The extension comes off, because a Databricks notebook object does not carry one.

### 4. Put the notebooks where the course names them

Anything under `lab/` is uploaded, so the notebooks either live there or are symlinked in from the rest of the repository. A symlink keeps one copy of each notebook rather than a second copy that drifts.

### 5. Write `expected.json`

The ship gate reads it. List what the course builds, by name:

```json
{
  "catalogs": ["my-course"],
  "schemas": ["my-course.data"],
  "volumes": ["my-course.data.raw"],
  "tables": ["my-course.data.readings"],
  "warehouses": ["shared_warehouse"],
  "pipelines": ["My ETL"],
  "workspace_paths": ["/Shared/my-course/etl"]
}
```

The manifest belongs to the course rather than to the tooling. The tooling knows how to ask whether a catalog named X exists. It must never know that X is this course's catalog, or the two have grown back together.

### 6. Add the course's own provisioning, if it needs any

A course that only hands out notebooks needs nothing here. A course that builds a catalog, tables or a pipeline writes its own Python and calls it from a hook:

```bash
voc_python workshop.py provision
```

The program prints `key=value` lines on stdout and narrates to stderr. Each key comes back to the hook as a shell variable prefixed with the program's name, so `workshop.py` answers as `$workshop_catalog`. Use the Python standard library only, against Python 3.9. There is no `pip install` on a hook's critical path: it is a round trip a student waits through and it fails outright on a locked-down host.

### 7. Deploy

Every call from a course repository needs `--env-file`, because the credentials live in the tooling repository and a course has no `.env` of its own.

```bash
export VOC_ENV=../dbx-vocareum/.env
uv run dbx-vocareum-upload lab/ --dry-run
uv run dbx-vocareum-upload lab/ --env-file "$VOC_ENV"
```

`--dry-run` reads no configuration at all, so it proves the archive and says nothing about credentials. Exit `0` means uploaded and hash-verified. **Exit `3` means hash mismatch. Stop, and do not start a lab against it.**

Upload the whole `lab/` directory every time, never the one file that changed. The hooks chain through `VOC_CUSTOM_DATA` and share one runtime, so a partial write leaves a lab built by one version and torn down by another.

### 8. Build the workspace, then check it

Uploading does not run `workspace_init.sh`. Press **Rerun Init** on the row for the workspace in the Vocareum admin Workspaces page. Then read the **`Init Exit Status`** text in the same row, which is a link to the hook's full transcript. Read the last line of the transcript and not the number beside it: the number showed `0` for a run that failed and exited 1.

```bash
uv run dbx-vocareum-diagnose --expect expected.json --env-file "$VOC_ENV"
```

Exit `0` is the ship signal. Exit `3` lists what is missing. If the course builds a pipeline, wait for its update to finish before believing a failure, because the pipeline's output tables are absent until it does and the gate passes minutes later with nothing changed.

### 9. Launch once as a student, from the web UI

The gate covers the workspace. It says nothing about what a student gets. Start the lab from the Vocareum web UI and confirm the cluster comes up and every notebook the course names is in the student's home folder.

**From the web UI rather than from the CLI,** because a hook that fails reports itself by redirecting the student's browser to a URL ending in `#voc-diag=<code>&script=<hook>`. That fragment is the only error channel a hook has. A launch started from the CLI throws it away. If the address bar carries no `#voc-diag=`, the hooks finished.

A session bills compute from the moment it starts, so end it when the check is done. A session started in the browser is ended in the browser: `dbx-vocareum-session --end` ends the session named in `.env`, which is a different student.
