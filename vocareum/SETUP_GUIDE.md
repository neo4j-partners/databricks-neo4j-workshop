# Vocareum setup: Neo4j + Databricks workshop

The admin procedure for running this course on Vocareum lives in the `dbx-vocareum-utils` tooling repository. It is not repeated here. A second copy of a procedure drifts, and this one already did: an older copy of the setup code defined 4 gold tables where the current one defines 8.

This page says what is in this directory, where to go for the procedure, and what the tooling does not cover.

The tooling repository is [neo4j-partners/dbx-vocareum-utils](https://github.com/neo4j-partners/dbx-vocareum-utils). This repository depends on it, declared in `pyproject.toml` as `dbx-vocareum-tools @ git+https://github.com/neo4j-partners/dbx-vocareum-utils.git`.

Links below assume the tooling repository is cloned beside this repository under the folder name `dbx-vocareum`. A plain `git clone` of it creates `dbx-vocareum-utils`, so name the folder: `git clone https://github.com/neo4j-partners/dbx-vocareum-utils.git dbx-vocareum`.

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
| Know where Neo4j runs, and why it is not inside the workspace | [The manual pre-workshop steps](#the-manual-pre-workshop-steps), below |

`dbx-vocareum/docs/permissions.md` is the single source of truth for what each principal may do. Do not restate a permission result here.

## What this course owns

Three things belong to this course rather than to the tooling.

### `lab/` at the repository root

Four hooks, `workshop.py`, and `course.env`. Every value specific to this workshop lives in `course.env`: the cluster runtime and node type, the thirteen libraries, the catalog name and its managed location, the notebook list, and the shared warehouse. Change a course value there. Do not change it in a hook, and do not change it in the tooling.

Vocareum runs four hooks by name and ignores anything else in `/voc/scripts`. Each one is a shell script this course owns, scaffolded once by `dbx-vocareum-init` and edited from then on.

- **`workspace_init.sh`: the workspace is built here, once.** It runs one time per workspace Vocareum creates, before any student exists. It ensures the SQL warehouse, then hands off to `voc_python workshop.py provision`, which creates the catalog with its managed location, its schemas `aircraft` and `agents` plus `aircraft_pipeline_<workspace id>` and `aircraft_gold_<workspace id>`, the volume, the uploaded data, the DLT pipeline, and the Genie comments and grants. Everything a class shares is built by this hook. Redeploying `/voc/scripts` does not re-run it. `Rerun Init` on the admin Workspaces page does.
- **`lab_setup.sh`: pre-warm, and it deliberately builds nothing.** It runs when Vocareum warms a lab ahead of a student. It reports the environment and stops there. No cluster is created, because the cluster name is derived from the student identity Vocareum mints at session start, so a cluster warmed here would carry a name the student's own session never looks for.
- **`user_setup.sh`: the student's session, and the only required hook.** It runs when a student clicks start. It calls `cluster-ensure` to create or restart the per-student cluster, then `notebook-import` to put the course's notebooks in the student's home folder, then writes the landing page into `$VOC_IPC_DATA_FILE`, which is what redirects the student's browser. It is the only hook that writes that file. A lab with no `user_setup.sh` starts successfully and does nothing.
- **`lab_end.sh`: reclaim whatever is still billing.** It runs on stop and on terminate, and it reads `VOC_END_LAB_BEHAVIOR` before deciding anything. On a stop the student's work is preserved for their next session, so the cluster is terminated and nothing is deleted. On a terminate the environment reverts, so the cluster is deleted outright. Notebooks are left alone in both cases. Anything billable that `user_setup.sh` created has to be reclaimed here, because Vocareum removes only what Vocareum created.

### `expected.json` at the repository root

The ship gate manifest. `uv run dbx-vocareum-diagnose --expect expected.json` reads it and fails when a named object is missing. It sits outside `lab/` on purpose, because everything under `lab/` is uploaded to `/voc/scripts` and this file is for whoever deploys rather than for the hooks.

### The manual pre-workshop steps

The hooks build the Databricks side. They do not build the Neo4j side or the Lab 4 agent wiring, and that is deliberate.

- **Participant Aura instances.** Each participant creates their own Aura Free instance in Lab 1. Nothing to pre-provision.
- **The instructor's demo Aura instance.** Lab 4 Part A queries Unity Catalog and touches no graph. Part B is a demo the instructor runs, against an instance the instructor loads before class with `workshop-setup/populate_aircraft_db`. No participant reads that instance and none needs credentials for it.
- **The `neo4j_agentcore_mcp` Unity Catalog connection.** Part B needs an HTTP connection to a Neo4j MCP server pointed at the instructor's demo instance. `workshop-setup/MCP-MANUAL-SETUP.md` is the walkthrough. Participants watch the demo. They never create the connection and never call it.
- **Genie Agents.** Each participant creates their own in Lab 4 Part A. Do not pre-create a shared one, because each participant needs to edit their agent's instructions.

## Setting up a new course

This workshop is one course. The tooling runs any number of them, and a second course does not copy this one. [How a course goes live](../../dbx-vocareum/README.md#how-a-course-goes-live) in the `dbx-vocareum` README is the step-by-step procedure, from creating the course in Vocareum to rolling back a bad upload. [How the Neo4j workshop does it](../../dbx-vocareum/README.md#how-the-neo4j-workshop-does-it) in the same README uses this repository as its worked example.
