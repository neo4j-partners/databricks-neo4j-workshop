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
publishes eight, and the symptom was a Genie Agent that answered plausibly
rather than correctly, which is the hardest class of workshop failure to notice
in a room of thirty people. Provisioning the workshop by hand alongside the
hooks does not produce a spare. It produces a second catalog whose tables
disagree with the notebooks the participants are running.

---

## What creates what

| Object | Created by | Called from |
|--------|-----------|-------------|
| SQL warehouse `shared_warehouse` | `voclab.py warehouse-ensure` | `lab/workspace_init.sh` |
| Catalog `databricks-neo4j-workshop`, the `aircraft`, `aircraft_pipeline` and `agents` schemas, the `raw_data` volume, and the eight grants that reach them, six reads plus `CREATE MODEL` and `CREATE TABLE` on `agents` for Lab 5 | `workshop.provision_infrastructure` | `lab/workspace_init.sh`, through `voc_python workshop.py provision` |
| The 29 courseware files in the volume, 23 CSVs, 5 maintenance manuals and the `neo4j-agent-memory` wheel Lab 6 installs | `workshop.provision_data` | same |
| `/Shared/workshop/dlt_fleet_etl` and the `Fleet Digital Twin ETL` pipeline, run to completion | `workshop.provision_pipeline` | same |
| The eight gold tables in `aircraft` | published by that pipeline | same |
| 8 table comments, 10 column comments and 8 `SELECT` grants | `workshop.provision_genie` | same |
| The per-student cluster and its thirteen libraries | `voclab.py cluster-ensure` | `lab/lab_setup.sh` to pre-warm, `lab/user_setup.sh` to guarantee |
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

**The gate checks that objects exist, not what is inside them.** `expected.json`
names the volume; nothing asserts the volume's 29 files. So a workspace whose
volume holds no CSVs and no wheel still exits `0`. The gate is a check on
provisioning having run, not on it having finished correctly. Until that
changes, confirm the volume contents by hand, or trust
`workshop.provision_data`, which does fail loudly on a missing file. The wheel
is the sharpest case, and it has its own section below.

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

- **The instructor's demo instance for Lab 4 Part B.** Part B is a demo the
  instructor runs, and the MCP server behind it points at an instance the
  instructor loads before class. Part A queries Unity Catalog and touches no
  graph at all, so no participant reads this instance and none needs credentials
  for it.
- **A participant who fell behind.** `--skip-extraction` chunks, embeds and
  indexes the maintenance manual without an extractor LLM, so no OpenAI or
  Anthropic key is needed. It creates no `ExtractedLimit` nodes and none of the
  other extracted entities. The 20 canonical `OperatingLimit` nodes load from CSV
  either way, so the `limit_retriever` cell in Lab 3 notebook 02 still has a
  chain to traverse.

Embeddings have no provider setting. The loader always calls the same
`databricks-bge-large-en` endpoint Lab 3 calls, so vectors written by the loader
and vectors written by the notebooks come from one model. A bare `uv sync`
installs everything that path needs, but the loader does need Databricks
credentials, on the `--skip-extraction` path too. Set `DATABRICKS_CONFIG_PROFILE`
or the host/token pair in `.env`.

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
for a step only an administrator performs. Part B is a demo participants watch,
so they never touch the connection and never needed it. Every grant
`provision_infrastructure` makes is now a read.

The administrator does not get `CREATE CONNECTION` by signing in, and being an
account admin does not confer it, because the metastore is owned by the
`vocareum-sp` service principal rather than by a person. It is granted once per
account, and **Step 0 of [MCP-MANUAL-SETUP.md](MCP-MANUAL-SETUP.md)** is where
that statement lives. The grant is on the metastore, an account-level object, so
it survives the workspaces being torn down between cohorts.

Lab 4 Part B is an instructor demo, so this whole section is instructor
preparation. The participant labs, including the Lab 5 LangGraph agent and the
Lab 6 memory agent, reach Neo4j with the Python driver against each
participant's own instance and need none of this.

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

**The runtime is injected from the installed package, not from this
repository.** `dbx-vocareum-upload` puts its own `voclab.py` and `voclib.sh`
into every archive, and `uv.lock` pins which version that is. So a fix made in
`dbx-vocareum` does not arrive by pulling this repository. Resync first, or the
upload ships the old runtime and hash-verifies it cleanly:

```bash
uv lock --upgrade-package dbx-vocareum-tools && uv sync
```

`pyproject.toml` names the dependency as `git+https://...` with no tag and no
rev, so it tracks the branch and the lock is the only pin. There is no version
to bump.

---

### The `neo4j-agent-memory` wheel

Lab 6 needs a build of `neo4j-agent-memory` that does not exist on PyPI, so the
course ships one. This is the only build artifact the repository carries, and
the only piece of the courseware that is not either data or a notebook.

| | |
|---|---|
| Committed at | `lab/courseware/wheels/neo4j_agent_memory-0.5.1.dev1+mentions-py3-none-any.whl` |
| Reaches the volume by | `workshop.provision_data`, called from `lab/workspace_init.sh` |
| Lands at | `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/` |
| Installed on the cluster by | `VOC_COURSE_LIBRARIES` in `lab/course.env`, as `whl:` plus a separate `pypi:httpx>=0.27.0` |
| Built from | the `mentions` branch of [`neo4j-partners/agent-memory`](https://github.com/neo4j-partners/agent-memory), `uv build --wheel` |

**Why a fork.** Released `0.5.0` silently drops `MENTIONS` edges on the
automatic extraction path, which is the edge Lab 6's headline query walks. The
fix exists on that branch and nowhere else yet. The branch bumps the version to
`0.5.1.dev1+mentions`, so `pip list` tells a patched install from an unpatched
one at a glance.

**Why a wheel rather than `git+https`.** It is byte-identical for every
participant, installs with no clone and no build at cluster start, and is the
same artifact Lab 6 hands to Model Serving. The `git+` form would make every
cluster in the class clone and build the package while a student waits.

**Why `httpx` is a separate entry.** A wheel carries no extras. The library's
`[nams]` extra contains exactly one thing, `httpx>=0.27.0`, and the bolt path
imports it transitively, so without it `MemoryClient.connect()` fails with
`ModuleNotFoundError: No module named 'httpx'` at connect time rather than at
import time, in front of the participant.

**Why `wheels/` is its own directory.** `courseware/aircraft_digital_twin_data/`
is a symlink to the data generator's committed output. A build artifact parked
there is one `populate-aircraft-db generate` away from being clobbered, and that
failure would not name itself. `wheels/` is the course's, like
`dlt_fleet_etl.py` beside it, and nothing regenerates it.

**Rebuilding it.** Manual, and rare. Build from the branch, drop the new file
in, delete the old one, and update the path in `VOC_COURSE_LIBRARIES`. The
filename carries the version, so the two must move together:

```bash
cd <checkout of neo4j-partners/agent-memory>   # branch: mentions
uv build --wheel
cp dist/neo4j_agent_memory-*.whl <this repo>/lab/courseware/wheels/
```

`workshop.provision_data` uploads every `*.whl` it finds and fails the whole
provision if the directory is missing or empty, rather than warning. A volume
without the wheel does not break one lab: it breaks the library install on
every cluster in the class, at cluster start, with the student waiting.

**One trap for Lab 6, and it is unmeasured.** `0.5.1.dev1+mentions` is a PEP 440
local version segment and resolves from nowhere. MLflow's inferred requirements
will emit `neo4j-agent-memory==0.5.1.dev1+mentions` into the logged model, which
the serving build container cannot install. So the logged model cannot be left
to inference here.

The option to try first is `mlflow.models.utils.add_libraries_to_model(<model-uri>)`,
which copies the wheel into the model artifact, so the build container installs
from the artifact and never resolves the name at all.

Naming the volume path in `pip_requirements` looks like the simpler fix and
probably is not one: the serving build container does not mount `/Volumes`, so
a `/Volumes/...` requirement has nothing to read. That is reasoning, not a
measurement. **Whoever reaches this first should record what actually happened
here**, because it is the least-verified claim in the memory documentation and
it sits on the critical path for the Lab 6 endpoint.

The measurements behind all of the above are in
[`../worklog/memory-spike.md`](../worklog/memory-spike.md).

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
lands on `Lab_1_Aura_Setup/01_create_aura_instance` in their own folder with their cluster
already building. Nothing has to be handed out.

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
restart it after adding the library. The libraries take about six minutes to
reach `INSTALLED` after the cluster reaches `RUNNING`, which is what
`lab_setup.sh` pre-warming buys back. That figure was measured when the list
held eleven entries and now holds thirteen; the two added are a local wheel and
a small pure-Python package, so treat six minutes as a floor rather than a
number to quote at a student.

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
before adding sample questions to the agent.

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

The wheel is the exception to "live data lives here". It is committed under
`lab/courseware/wheels/` rather than in this directory, for the reason given in
[The `neo4j-agent-memory` wheel](#the-neo4j-agent-memory-wheel) above.

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
