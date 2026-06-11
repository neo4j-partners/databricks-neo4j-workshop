# notebook_validation

Automated test suite for verifying the Aircraft Digital Twin workshop labs on a Databricks cluster. Replaces `verify_labs` with cluster-native validation that exercises the same code paths participants use.

## Prerequisites

- Databricks CLI configured with a profile (`databricks configure --profile <name>`)
- An all-purpose cluster with the Neo4j Spark Connector jar installed and Python 3.11+ (does not need to be running — scripts auto-start it if terminated)
- Neo4j Aura instance provisioned for the workshop

## Setup

```bash
cd workshop-setup/notebook_validation
cp .env.example .env
```

Edit `.env` with your values:

| Variable | Description |
|----------|-------------|
| `DATABRICKS_PROFILE` | CLI profile name |
| `DATABRICKS_CLUSTER_ID` | All-purpose cluster ID |
| `WORKSPACE_DIR` | Remote path for uploaded scripts (e.g., `/Workspace/Users/you@example.com/notebook_validation`) |
| `NEO4J_URI` | Neo4j Aura connection URI |
| `NEO4J_USERNAME` | Neo4j username (default: `neo4j`) |
| `NEO4J_PASSWORD` | Neo4j password |
| `DATA_PATH` | Unity Catalog Volume path (default: `/Volumes/databricks-neo4j-workshop/aircraft/raw_data`) |

## Full Validation Flow

### Step 1: Upload all scripts

```bash
./upload.sh --all
```

Verify the upload:

```bash
./validate.sh
```

### Step 2: Smoke test the cluster

Confirms Python, Spark, and the Neo4j Spark Connector are available:

```bash
./submit.sh test_hello.py
```

### Step 3: Neo4j connectivity check

Quick check that Neo4j is reachable and contains data:

```bash
./submit.sh check_neo4j.py
```

### Step 4: Load Lab 2 data

Clears the database, creates constraints/indexes, loads all 9 node types and 11 relationship types from CSV, then runs 19 PASS/FAIL checks:

```bash
./submit.sh run_lab2_01.py
```

> To skip the database clear: participants can pass `--skip-clear`, but `submit.sh` does not inject this flag by default.

### Step 5: Verify Lab 2 data (read-only)

Runs 13 read-only Cypher queries against the existing data without modifying anything. Use this to re-verify data at any point without reloading:

```bash
./submit.sh verify_lab2.py
```

### Step 6: Build and verify Lab 3 embedding pipeline

Loads the A320 maintenance manual, chunks it, generates embeddings, creates vector and fulltext indexes, then runs 16 PASS/FAIL checks:

```bash
./submit.sh run_lab3_01.py
```

> Requires `data_utils.py` on the cluster (included when you run `./upload.sh --all`).

### Step 7: Verify Lab 3 GraphRAG retrievers (read-only)

Read-only validation that the KG built in Step 6 supports the retriever patterns from `02_graphrag_retrievers.ipynb` (VectorRetriever, GraphRAG, VectorCypherRetriever, adjacent chunks, topology traversal, operating limits):

```bash
./submit.sh run_lab3_02.py
```

> Requires `data_utils.py` on the cluster and that `run_lab3_01.py` has already been run (KG + indexes must exist).

### Step 8: Verify Lab 3 Neo4j MCP server (read-only)

Confirms the Neo4j MCP server is reachable and returns expected data by calling the `get-schema` and `read-cypher` tools over HTTP JSON-RPC, mirroring `04_mcp_graph_queries.ipynb`:

```bash
./submit.sh run_lab3_04.py
```

> Uses only the Python standard library — no `data_utils.py` or Spark required.

## Scripts Reference

| Script | Purpose | Destructive | Needs Spark |
|--------|---------|-------------|-------------|
| `test_hello.py` | Cluster smoke test (Python, Spark, Connector) | No | Yes |
| `check_neo4j.py` | Neo4j connectivity and data presence check | No | No |
| `run_lab2_01.py` | Load Lab 2 data + validate (19 checks) | **Yes** — clears DB | Yes |
| `verify_lab2.py` | Read-only Lab 2 verification (13 queries) | No | No |
| `run_lab3_01.py` | Build Lab 3 embedding pipeline + validate (16 checks) | **Yes** — clears Document/Chunk nodes | No |
| `run_lab3_02.py` | Read-only validation of Lab 3 GraphRAG retriever patterns | No | No |
| `run_lab3_04.py` | Read-only verification of the Neo4j MCP server (get-schema, read-cypher) | No | No |
| `data_utils.py` | Shared utilities (embeddings, Neo4j connection, text splitting) | — | — |

## Shell Scripts

| Script | Purpose |
|--------|---------|
| `upload.sh` | Upload scripts to Databricks workspace |
| `submit.sh` | Check cluster, then submit a script as a one-time job run |
| `validate.sh` | Check cluster, then list remote workspace contents and verify uploads |
| `clean.sh` | Delete remote workspace and notebook_validation job runs |
| `cluster_utils.sh` | Shared helper — checks cluster state and auto-starts if terminated |

### upload.sh

```bash
./upload.sh                     # uploads test_hello.py (default)
./upload.sh run_lab2_01.py      # uploads a specific file
./upload.sh --all               # uploads all agent_modules/*.py files
```

### submit.sh

```bash
./submit.sh                     # runs test_hello.py (default)
./submit.sh verify_lab2.py      # runs a specific script
./submit.sh run_lab2_01.py --no-wait   # submit without waiting for completion
```

Neo4j credentials and `DATA_PATH` from `.env` are automatically injected as command-line arguments. The cluster is auto-started if terminated (polls up to 10 minutes).

### validate.sh

```bash
./validate.sh                   # list all remote files
./validate.sh run_lab2_01.py    # check if a specific file exists
```

### clean.sh

Deletes the remote workspace directory and all `notebook_validation:*` one-time job runs. Prompts for confirmation before proceeding.

```bash
./clean.sh              # clean workspace + job runs (with confirmation)
./clean.sh --workspace  # clean only remote workspace
./clean.sh --runs       # clean only job runs
./clean.sh --yes        # skip confirmation prompt
```

For a full reset and re-run:

```bash
./clean.sh --yes
./upload.sh --all
./submit.sh test_hello.py
```
