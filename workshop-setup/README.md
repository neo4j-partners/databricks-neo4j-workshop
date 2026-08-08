# Workshop setup

**Purpose:** what provisions this workshop, what is still done by hand, and
where each piece lives.

The Databricks side is provisioned by the Vocareum lifecycle hooks in `lab/`.
Nothing in this directory creates a catalog, a schema, a volume, a table, a
pipeline or a grant. `lab/workshop.py` is the course's one definition of those
objects and the hooks call it.

Read that as an instruction rather than a description. A second copy of the
table definitions is how this repository already broke once: the retired copy
under `auto_scripts/` defined four gold tables where the current definition
publishes eight, and the symptom was a Genie space that answered plausibly
rather than correctly, which is the hardest class of workshop failure to notice
in a room of thirty people. Provisioning the workshop by hand alongside the
hooks does not produce a spare. It produces a second catalog whose tables
disagree with the notebooks the participants are running.

---

## What creates what

| Object | Created by | Called from |
|--------|-----------|-------------|
| SQL warehouse `shared_warehouse` | `voclab.py warehouse-ensure` | `lab/workspace_init.sh` |
| Catalog `databricks-neo4j-workshop`, the `aircraft`, `aircraft_pipeline` and `agents` schemas, the `raw_data` volume, and the ten grants that reach them | `workshop.provision_infrastructure` | `lab/workspace_init.sh`, through `voc_python workshop.py provision` |
| The 29 courseware files in the volume, 23 CSVs, 5 maintenance manuals and the `neo4j-agent-memory` wheel Lab 6 installs | `workshop.provision_data` | same |
| `/Shared/workshop/dlt_fleet_etl` and the `Fleet Digital Twin ETL` pipeline, run to completion | `workshop.provision_pipeline` | same |
| The eight gold tables in `aircraft` | published by that pipeline | same |
| 8 table comments, 10 column comments and 8 `SELECT` grants | `workshop.provision_genie` | same |
| The per-student cluster and its eleven libraries | `voclab.py cluster-ensure` | `lab/lab_setup.sh` to pre-warm, `lab/user_setup.sh` to guarantee |
| The lab notebooks in the student's own workspace folder | `voclab.py notebook-import` | `lab/user_setup.sh`, from `VOC_COURSE_NOTEBOOKS` in `lab/course.env` |
| Reclaiming anything billable when a session ends | `lab/lab_end.sh` | Vocareum, on stop or terminate |

Names, sizes, runtimes and the library list all come from `lab/course.env`. That
file is the one place a course states its values, and it travels to
`/voc/scripts` with the hooks. Changing a name here and not there is the drift
this arrangement exists to prevent.

To check that a workspace holds everything the course names, run the ship gate
from the repository root:

```bash
uv run dbx-vocareum-diagnose --expect expected.json
```

Exit `0` means every object in `expected.json` is present. Exit `3` names the
ones that are not. Run it after the DLT pipeline finishes rather than during: the
eight gold tables are the pipeline's output, so a gate run against a live update
reports a failure that resolves itself.

---

## What is still manual, and why

### Neo4j Aura

Nothing automates the graph side, and nothing can from here. Neo4j runs in Aura
and the lab connects out to it over Bolt, so no workspace resource hosts a
database and Vocareum's cleanup cannot reach one. `dbx-vocareum/docs/neo4j-aura.md`
has the full account of that decision and what follows from it.

Participants create their own free Aura instance in Lab 1 and load it themselves
with the Lab 2 ETL notebooks and the Lab 3 embedding notebooks. That is the
lab, not a setup step somebody skipped.

Two administrator cases need an instance loaded ahead of time, and both use the
`populate_aircraft_db` CLI in this directory:

- **The Lab 4 reference instance.** Lab 4 queries one administrator-managed
  instance rather than a participant's, so every participant gets the full graph
  no matter how far they got in Lab 2.
- **A participant who fell behind.** `--skip-extraction` chunks, embeds and
  indexes the maintenance manual without an extractor LLM, so no OpenAI or
  Anthropic key is needed. It does not create the `OperatingLimit` nodes that the
  `limit_retriever` cell in Lab 3 notebook 02 queries.

`EMBEDDING_PROVIDER=databricks` calls the same `databricks-bge-large-en`
endpoint Lab 3 calls, so vectors written by the loader and vectors written by the
notebooks come from one model. Install it with `uv sync --extra databricks`.

### The Neo4j MCP connection, for Lab 4 Part B only

The Unity Catalog HTTP connection to the external Neo4j MCP server is created by
hand in the Databricks UI. See [MCP-MANUAL-SETUP.md](MCP-MANUAL-SETUP.md) and
`neo4j_mcp_connection/`. It stays manual because it carries an OAuth client
secret issued by an AWS AgentCore deployment that lives outside this repository,
and because the `Is MCP connection` flag is a UI affordance some workspaces do
not surface at all.

The privilege is manual too. `workshop.py` used to grant
`CREATE CONNECTION ON METASTORE` to `account users`; that was removed on
2026-08-08, because it gave every participant a metastore-wide create privilege
for a step only an administrator performs. Part B has participants verify a
connection an administrator already made, so they never needed it. Every grant
`provision_infrastructure` makes is now a read.

The administrator does not get `CREATE CONNECTION` by signing in, and being an
account admin does not confer it, because the metastore is owned by the
`vocareum-sp` service principal rather than by a person. It is granted once per
account, and **Step 0 of [MCP-MANUAL-SETUP.md](MCP-MANUAL-SETUP.md)** is where
that statement lives. The grant is on the metastore, an account-level object, so
it survives the workspaces being torn down between cohorts.

Lab 4 Part B is optional. The required labs, including the Lab 5 LangGraph
agent, reach Neo4j with the Python driver against each participant's own
instance and need none of this.

### The storage that backs the catalog

The Databricks account this course deploys into has Default Storage enabled, so
its metastore carries no storage root and a bare `CREATE CATALOG` fails there.
The course brings its own: an S3 bucket, an IAM role, a Unity Catalog storage
credential and an external location, all built once by hand in the course
owner's AWS account. `VOC_COURSE_CATALOG_MANAGED_LOCATION` in `lab/course.env`
names the path, and `workshop.py` appends it to `CREATE CATALOG` as a
`MANAGED LOCATION` clause. The full chain and its policy documents are in
`dbx-vocareum/setup-workshop-v2.md` under "The AWS side".

Leave that variable empty on an account whose metastore has a storage root of
its own, and `workshop.py` emits the plain statement instead.

### Deploying a change

`lab/` reaches Vocareum through one hash-verified upload from the repository
root:

```bash
uv run dbx-vocareum-upload lab/ --dry-run   # show the archive, send nothing
uv run dbx-vocareum-upload lab/             # upload and verify
```

Exit `3` means a hash mismatch. Do not start a lab against it. Redeploying does
not re-run `workspace_init.sh`, which Vocareum fires once per workspace; the
`Rerun Init` button on the Vocareum admin Workspaces page is the only way to
trigger it again. Admin-side instructions live in
[`vocareum/SETUP_GUIDE.md`](../vocareum/SETUP_GUIDE.md).

---

## Running the workshop outside Vocareum

An instructor provisioning a Databricks workspace by hand runs the same
definition rather than a second one. `lab/workshop.py` locates its runtime
inside the installed `dbx-vocareum-tools` package when it is not sitting in
`/voc/scripts`, so it runs from a laptop unchanged:

```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=dapi...
export WORKSHOP_DATA_DIR=workshop-setup/aircraft_digital_twin_data
export WORKSHOP_DLT_NOTEBOOK=lab/courseware/dlt_fleet_etl.py

uv run python lab/workshop.py provision --warehouse-name "<an existing warehouse>"
```

The warehouse is looked up by name and never created here, because "whatever
warehouse happens to be running" is how a class's DDL lands on an unrelated
team's compute. Every stage is separately runnable, `infrastructure`,
`upload-data`, `pipeline` and `genie`, so debugging the Genie comments does not
mean re-running the ETL to reach them.

Two jobs the hooks do not cover outside Vocareum, both in `auto_scripts/`:

- **`sync_notebooks.py`** publishes the lab notebooks to
  `/Shared/databricks-neo4j-workshop`, overwriting. `notebook-import` is not a
  substitute: it targets `/Users/<email>` and skips a file that is already there,
  which is what preserves a student's work across a stop.
- **`teardown.py`** deletes the catalog, its schemas, the volume, the pipeline
  and the shared notebook tree. Nothing else deletes anything.

Both read every object name from `lab/workshop.py`. See
[auto_scripts/README.md](auto_scripts/README.md).

The classic cluster is the remaining gap. Labs 2 and 3 need one because the
Neo4j Spark Connector is a Maven library and serverless compute cannot install
it. Under Vocareum `cluster-ensure` builds it per student from
`VOC_COURSE_SPARK_VERSION`, `VOC_COURSE_NODE_TYPE` and `VOC_COURSE_LIBRARIES`.
On a hand-provisioned workspace an instructor creates it in the UI with those
same three values, read out of `lab/course.env` rather than copied into a second
file here.

---

## What the participants need told

Under Vocareum, `user_setup.sh` writes the landing page into
`$VOC_IPC_DATA_FILE` and Vocareum redirects the browser there, so a participant
lands on `00_cluster_smoke_test` in their own folder with their cluster already
building. Nothing has to be handed out.

On a hand-provisioned workspace, a handout or slide carries:

| Resource | Value |
|----------|-------|
| Databricks workspace URL | `https://your-workspace.cloud.databricks.com` |
| Data volume path | `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/` |
| Shared notebook folder | `/Shared/databricks-neo4j-workshop/` |

Participants sign in, check that the workshop cluster is running, open the
shared folder, enter their Neo4j credentials from Lab 1, and run the notebooks.

---

## Troubleshooting

**"Spark Connector not found"**
The cluster has to be in Dedicated (single user) access mode; shared modes are
not supported by the connector. Check the library status on the cluster, and
restart it after adding the library. The eleven libraries take about six minutes
to reach `INSTALLED` after the cluster reaches `RUNNING`, which is what
`lab_setup.sh` pre-warming buys back.

**"Connection refused" to Neo4j**
Aura is TLS only, so the URI is `neo4j+s://`, and `bolt://` fails in the
handshake rather than as a bad password. Check that the participant's instance
is running and that the credentials are the ones Aura issued at creation.

**"Path does not exist" for the volume**
Run the ship gate. If the volume is absent, `workspace_init.sh` did not finish,
and the `Init Exit Status` link on the Vocareum admin Workspaces page opens the
hook's full transcript. Read its last line rather than the exit number: a hook
that ended in `voc_fail` has been observed reported as `Init Exit Status: 0`.

**The catalog is empty and the student still got a cluster and a notebook**
Those come from `user_setup.sh`, which does not depend on `workspace_init.sh`.
An empty catalog with a working student session means the workspace hook failed
or never ran against that workspace.

**Duplicate nodes on re-run**
The Lab 2 ETL writes in overwrite mode. If duplicates persist, participants can
clear the graph with `MATCH (n) DETACH DELETE n`.

**Genie answers plausibly rather than correctly**
The table and column comments are what it grounds against, and
`provision_genie` applies them. Confirm the eight gold tables carry comments
before adding sample questions to the space.

**Gold tables missing after a clean provision**
They are the DLT pipeline's output. `workshop.py` waits on the update to a 900
second timeout, so a hook that returned has already settled, but a gate or a
browse run alongside a live update sees them absent.

---

## What is in this directory

| Path | What it is |
|------|-----------|
| `aircraft_digital_twin_data/` | The dataset, 23 CSVs and 5 maintenance manuals. Live data: `lab/courseware/` symlinks it and the upload follows the link, so it ships to Vocareum from here. |
| `auto_scripts/` | `sync_notebooks.py` and `teardown.py`, the two jobs nothing else covers, plus the import seam that reaches `lab/workshop.py`. |
| `populate_aircraft_db/` | The Neo4j loader and the generator that produced the dataset. Manual, for the reasons above. |
| `neo4j_mcp_connection/` | Supporting notebook for the Lab 4 Part B MCP connection. Manual. |
| `verify/` | Read-only Cypher verification for the Lab 2 and GDS query sets. Development tooling, run against a loaded Aura instance. |
| `notebook_validation/` | Upload-and-submit harness that runs the lab notebooks as Databricks jobs. Development tooling. |
| `docs/` | Reference material. `MANUAL_SETUP.md` is the file inventory and expected counts. `EXAMPLE_QUERIES.md` is the Aura Agent question set. |
| `MCP-MANUAL-SETUP.md` | The one Databricks-side procedure still done by hand. |

---

## Cost

The values are in `lab/course.env` rather than restated here, and these are what
they currently say:

- **Per-student cluster:** `i3.xlarge`, single node, auto-terminating after 90
  minutes. Measured rather than chosen: the Vocareum `.cfg` asked for
  `m5.large` and never got it.
- **SQL warehouse:** `2X-Small`, auto-stopping after 10 minutes. One per
  workspace, not one per student, because the Statement Execution API needs a
  warehouse id and a course that runs SQL needs it once.
- **DLT pipeline:** serverless, one full refresh per workspace initialization.
- **Storage:** about 25 MB of CSVs and manuals in the volume, plus the bronze,
  silver and gold Delta tables the pipeline writes.

An instance pool is a separate, deliberate cost. `dbx-vocareum-pool --create
--min-idle N` holds N booted machines until somebody deletes the pool, and
nothing automatic ever does.

---

## Reference

- [Neo4j Spark Connector](https://neo4j.com/docs/spark/current/)
- [Databricks Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
- [Databricks Genie](https://docs.databricks.com/en/genie/index.html)
