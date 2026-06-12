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

### Step 5b: Run the Lab 2 GDS notebooks (additive)

Builds the in-memory projections and runs the four GDS algorithms from notebooks `02`–`05`, validating each with PASS/FAIL checks. These are additive to the base Lab 2 data: each writes properties or relationships to Neo4j, then drops its in-memory projection at the end. Run them after Step 4 (data loaded):

```bash
./submit.sh run_lab2_02.py    # Louvain community detection → fault_community on Aircraft
./submit.sh run_lab2_03.py    # kNN aircraft similarity → SIMILAR_PROFILE relationships
./submit.sh run_lab2_04.py    # PageRank + Betweenness → pagerank_score, betweenness_score on Airport
./submit.sh run_lab2_05.py    # Node Similarity → SIMILAR_FAULT_PROFILE relationships
```

> Requires the Aura instance to have GDS available (each script checks `gds.version()` and fails fast if not). `run_lab2_02.py` and `run_lab2_03.py` additionally read the sensor Delta tables; `run_lab2_03.py` also reads `nodes_maintenance.csv` from the Volume. `run_lab2_05.py` creates temporary `FaultType` nodes and removes them on completion.

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

## Profiling the Lab 2 Load

When the Lab 2 load is slow, `profile_lab2_load.py` shows where the time goes. It runs the same load as `run_lab2_01.py` but times every step (clear, constraints, each node and relationship load), measures fixed overheads (Neo4j driver round trip vs Spark connector round trip vs CSV scan), verifies all indexes are ONLINE before loading, and A/B tests the Flight node load (the largest node file) across four write strategies: MERGE vs CREATE, serial vs 4 parallel partitions. It ends with a timing report sorted slowest-first.

```bash
./upload.sh profile_lab2_load.py
./submit.sh profile_lab2_load.py
```

> **Destructive**: clears the database like `run_lab2_01.py`. With `--flights-only` it skips the full load and only deletes/reloads Flight nodes (faster iteration on the A/B variants), but `submit.sh` does not inject extra flags — submit manually or edit `submit.sh` to pass them. `--batch-size N` changes the connector batch size for all writes.

Reading the report: steps whose total time is close to the "connector RETURN 1" baseline are dominated by fixed Spark job overhead, not Neo4j write throughput. The Flight A/B rows show directly what MERGE vs CREATE and serial vs parallel cost on your cluster and Aura instance.

## Scripts Reference

| Script | Purpose | Destructive | Needs Spark |
|--------|---------|-------------|-------------|
| `test_hello.py` | Cluster smoke test (Python, Spark, Connector) | No | Yes |
| `check_neo4j.py` | Neo4j connectivity and data presence check | No | No |
| `run_lab2_01.py` | Load Lab 2 data + validate (19 checks) | **Yes** — clears DB | Yes |
| `profile_lab2_load.py` | Profile the Lab 2 load: per-step timings, overhead baselines, Flight A/B write strategies | **Yes** — clears DB (Flight nodes only with `--flights-only`) | Yes |
| `verify_lab2.py` | Read-only Lab 2 verification (13 queries) | No | No |
| `run_lab2_02.py` | GDS Louvain community detection (notebook 02) + validate | Additive — writes `fault_community`, drops projection | Yes |
| `run_lab2_03.py` | GDS kNN aircraft similarity (notebook 03) + validate | Additive — writes `*_norm` + `SIMILAR_PROFILE`, drops projection | Yes |
| `run_lab2_04.py` | GDS PageRank + Betweenness (notebook 04) + validate | Additive — writes `pagerank_score`/`betweenness_score`, drops projection | Yes |
| `run_lab2_05.py` | GDS Node Similarity (notebook 05) + validate | Additive — writes `SIMILAR_FAULT_PROFILE`, removes temp `FaultType` nodes | Yes |
| `recreate_lakehouse_tables.py` | One-off admin fix: rebuild aircraft/systems/sensors Delta tables so key columns are `aircraft_id`/`system_id`/`sensor_id` (not raw `:ID(...)` headers) | **Yes** — drops + recreates 3 dimension tables | Yes |
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
