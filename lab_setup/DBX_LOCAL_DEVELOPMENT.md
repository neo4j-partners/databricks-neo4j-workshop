# Databricks Local Development and Remote Validation

Running notebook logic on a remote Databricks cluster from your local machine requires solving three problems: getting code and data onto the cluster, executing it without an interactive notebook session, and retrieving enough diagnostic output to debug failures. This guide captures the patterns and pitfalls discovered while building the `notebook_validation` framework for this project.

---

## The Core Workflow

The development loop has four stages: configure credentials, upload scripts, submit jobs, and inspect results. Each stage has its own failure modes, and the fastest path to productivity is running a smoke test through all four before attempting real work.

### 1. Configuration

Each tool directory maintains its own `.env` file. The `notebook_validation/.env` requires three credential sets:

```bash
# Databricks
DATABRICKS_PROFILE="azure-rk-knight"      # CLI profile name
DATABRICKS_CLUSTER_ID="1029-205109-abc"    # Existing all-purpose cluster
WORKSPACE_DIR="/Workspace/Users/you@example.com/notebook_validation"

# Neo4j
NEO4J_URI="neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="your-password"

# Data
DATA_PATH="/Volumes/your-catalog/lab-schema/lab-volume"
```

The `DATABRICKS_PROFILE` must match a profile configured via `databricks auth login`. The cluster must already exist and be startable. The `DATA_PATH` must reference the actual Unity Catalog name, which may differ from the default in notebook code (the project uses `aws-databricks-neo4j-workshop` on AWS and `azure-databricks-neo4j-workshop` on Azure, not the generic `databricks-neo4j-workshop` that appears in some templates).

### 2. Upload

The `upload.sh` script pushes Python files to the Databricks workspace using `databricks workspace import`:

```bash
./upload.sh test_hello.py       # Single file
./upload.sh --all               # All .py files in agent_modules/
```

Files land at `$WORKSPACE_DIR/agent_modules/<filename>`. The script creates the remote directory if it doesn't exist. Use `--all` when iterating on shared utilities like `data_utils.py` that other scripts import.

### 3. Submit

The `submit.sh` script creates a one-time job run on an existing cluster:

```bash
./submit.sh test_hello.py               # Run with default wait
./submit.sh run_lab2_02.py              # Run data load
./submit.sh run_lab2_02.py --no-wait    # Fire and forget
```

Neo4j credentials from `.env` are automatically injected as `--neo4j-uri`, `--neo4j-username`, `--neo4j-password` command-line arguments. Scripts that don't use `argparse` (like the smoke test) safely ignore them. The credentials are serialized through Python's `json.dumps` to handle special characters in passwords.

The job runs as a `spark_python_task` on the existing cluster, which means no startup wait. This is critical for fast iteration; job clusters add 5-10 minutes per submission.

### 4. Inspect Results

When a job fails, the CLI error message is rarely sufficient. Retrieve the actual output in two steps:

```bash
# Find the run
databricks jobs list-runs --profile azure-rk-knight --limit 3

# Get the task-level run ID
databricks jobs get-run <RUN_ID> --profile azure-rk-knight -o json

# Get stdout/stderr and error details
databricks jobs get-run-output <TASK_RUN_ID> --profile azure-rk-knight -o json
```

The parent run ID and the task run ID are different. `get-run` returns the parent; each task within it has its own `run_id` in the `tasks` array. `get-run-output` requires the task-level ID.

The JSON output has three useful fields: `error` (the exception message), `error_trace` (the full stack trace), and `logs` (stdout/stderr from the script). The `logs` field is the most valuable because it contains all `print()` output from the script, including any PASS/FAIL reporting.

---

## Smoke Testing

Always run the smoke test before submitting real work to a new cluster:

```bash
./upload.sh test_hello.py && ./submit.sh test_hello.py
```

The smoke test verifies three things: Python and Spark are available, the Neo4j Spark Connector jar is on the classpath, and job output is captured. A passing smoke test confirms the entire upload-submit-inspect pipeline works. A failing smoke test isolates the problem to infrastructure rather than script logic.

---

## Neo4j Spark Connector Constraints

The Neo4j Spark Connector translates between Spark DataFrames and Neo4j graph operations. It works well for bulk data loading but has specific constraints that surface when running Cypher queries through Spark.

### LIMIT and ORDER BY

The connector rejects `SKIP` and `LIMIT` at the end of a query with `IllegalArgumentException: SKIP/LIMIT are not allowed at the end of the query`. The connector attempts to push down pagination into its own batching logic and fails when it encounters Cypher-level pagination.

The fix is wrapping the query in a `CALL {}` subquery so the connector sees a simple `RETURN` at the outer level:

```python
# Fails
run_cypher("""
    MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)
    RETURN a.tail_number, s.name
    ORDER BY s.name
    LIMIT 10
""")

# Works
run_cypher("""
    CALL {
        MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)
        RETURN a.tail_number AS TailNumber, s.name AS SystemName
        ORDER BY s.name
        LIMIT 10
    }
    RETURN TailNumber, SystemName
""")
```

`ORDER BY` alone (without `LIMIT`) can also trigger pushdown issues. Wrap any query that uses ordering or pagination in a `CALL {}` subquery as a defensive measure.

### Transaction Modes and the `script` Option

The connector's `script` option runs Cypher statements before the main `query`. The script executes in a separate transaction context. However, `CALL { ... } IN TRANSACTIONS` requires an implicit (auto-commit) transaction and will fail with `DatabaseException: A query with 'CALL { ... } IN TRANSACTIONS' can only be executed in an implicit transaction` when the connector places it inside an explicit transaction.

This becomes an issue when calling `.collect()` on the resulting DataFrame, which changes how the connector manages the transaction lifecycle. The workaround is using simple write statements without `IN TRANSACTIONS`:

```python
# Fails when .collect() is called
result = (spark.read
    .format("org.neo4j.spark.DataSource")
    .option("script",
        "CALL { MATCH (n) WITH n LIMIT 10000 DETACH DELETE n } "
        "IN TRANSACTIONS OF 10000 ROWS")
    .option("query", "RETURN 1 AS done")
    .load())
result.collect()  # Triggers explicit transaction → error

# Works: no IN TRANSACTIONS clause
result = (spark.read
    .format("org.neo4j.spark.DataSource")
    .option("script", "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n")
    .option("query", "MATCH (n) RETURN count(n) AS remaining")
    .load())
remaining = result.collect()[0]["remaining"]
```

For databases under 10,000 nodes, `MATCH (n) WITH n LIMIT 10000 DETACH DELETE n` in a single transaction is fine. For larger databases, multiple passes with the loop pattern below are necessary.

### Spark DataFrame Caching in Loops

Spark caches DataFrame execution plans. When calling the same connector options in a loop (e.g., repeated delete-then-count passes), Spark may return cached results instead of re-executing the query against Neo4j. The delete appears to run once and all subsequent iterations see stale counts.

The fix is varying the query text per iteration with a Cypher comment, which forces Spark to treat each iteration as a distinct query plan:

```python
MAX_CLEAR_PASSES = 20
for pass_num in range(1, MAX_CLEAR_PASSES + 1):
    result = (spark.read
        .format("org.neo4j.spark.DataSource")
        .option("script",
            "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n")
        .option("query",
            f"MATCH (n) RETURN count(n) AS remaining // pass {pass_num}")
        .load())
    remaining = result.collect()[0]["remaining"]
    if remaining == 0:
        break
```

The `// pass {pass_num}` comment changes the query string on each iteration, defeating the cache. This pattern applies to any loop that re-executes Spark connector reads with identical options.

### Silent Relationship Drops

The connector's `keys` strategy for writing relationships uses `MATCH` semantics to find source and target nodes. If a node key referenced in the relationship DataFrame doesn't exist in Neo4j, the relationship is silently dropped. The `df.count()` reported by the write function reflects input rows, not successfully created relationships.

Always verify relationship counts in Neo4j after loading:

```python
# df.count() says 60, but Neo4j may have fewer
write_relationships(df, "REMOVED_COMPONENT", "Removal", "removal_id",
                    "Component", "component_id")

# Verify actual count
neo4j_count = run_cypher(
    "MATCH ()-[r:REMOVED_COMPONENT]->() RETURN count(r) AS count"
).collect()[0]["count"]
```

When counts diverge, the root cause is usually dangling foreign keys in the relationship CSV that reference node IDs absent from the node CSV.

---

## Uploading CSV Data to Volumes

When source CSV files change locally, they must be re-uploaded to the Unity Catalog Volume before re-running the load script:

```bash
databricks fs cp local_file.csv \
    "dbfs:/Volumes/your-catalog/lab-schema/lab-volume/local_file.csv" \
    --profile azure-rk-knight --overwrite
```

The `dbfs:` prefix is required even though Volumes are not technically DBFS paths. The `--overwrite` flag replaces the existing file. Without it, the upload fails if the file already exists.

---

## Column Renaming During Load

CSV column names from data generation tools often carry prefixes or abbreviations that make poor Neo4j property names. Rename columns in the Spark DataFrame before writing to Neo4j so that Cypher queries read naturally:

```python
df = (read_csv("nodes_removals.csv")
    .withColumnRenamed(":ID(RemovalEvent)", "removal_id")
    .withColumnRenamed("RMV_REA_TX", "reason")
    .withColumnRenamed("time_since_install", "tsn")
    .withColumnRenamed("flight_cycles_at_removal", "csn")
    .withColumn("tsn", col("tsn").cast("double"))
    .withColumn("csn", col("csn").cast("integer")))
```

This is a one-time decision that affects every downstream query. Renaming at load time is preferable to translating column names in every Cypher query or verification script.

---

## Post-Validation from the Local Machine

After the remote job succeeds, run the `verify-labs` CLI locally to confirm the data is queryable from outside the Databricks environment:

```bash
cd lab_setup/verify_labs
uv sync
uv run verify-labs check           # Connectivity + node count
uv run verify-labs lab2             # All Lab 2 queries
uv run verify-labs lab2 --notebook 02   # Notebook 02 queries only
```

The CLI connects directly to Neo4j Aura using credentials from `lab_setup/.env`. It runs the same verification queries that participants will encounter in the workshop notebooks. A passing remote job with a failing local verification indicates a data or schema problem that the Spark Connector masked (e.g., silent relationship drops or misnamed properties).

---

## Data Integrity Checks

Relationship CSVs can contain foreign keys that reference non-existent nodes. These are invisible during loading (the Spark Connector drops them silently) but surface as count mismatches during verification.

To check for dangling references locally before uploading:

```python
import csv

with open("nodes_components.csv") as f:
    valid_ids = {row[":ID(Component)"] for row in csv.DictReader(f)}

with open("rels_component_removal.csv") as f:
    for row in csv.DictReader(f):
        if row[":START_ID(Component)"] not in valid_ids:
            print(f"Dangling: {row[':START_ID(Component)']}")
```

Run this check whenever CSV data is regenerated. The cost of catching a dangling reference locally is seconds; the cost of discovering it through a failed remote job is minutes of upload-submit-inspect cycles.

---

## Neo4j Schema Operations and Auto-Commit Transactions

Schema operations in Neo4j (`CREATE INDEX`, `DROP INDEX`, `CREATE CONSTRAINT`) require auto-commit transactions. The Neo4j Python driver offers two execution paths, and they handle transactions differently.

`driver.execute_query()` runs statements inside managed transactions. For data operations (CRUD on nodes and relationships) this is correct and convenient. For schema operations, managed transactions silently succeed without actually creating the index. No error is raised, no exception is thrown, and `SHOW INDEXES` reveals nothing was created. This failure mode cost six debugging runs during Lab 3 validation development.

`session.run()` runs statements in auto-commit mode, which is what schema operations require. The result must be consumed before the session closes:

```python
# Fails silently — managed transaction, index never created
driver.execute_query("""
    CREATE VECTOR INDEX myIndex IF NOT EXISTS
    FOR (c:Chunk) ON (c.embedding)
    OPTIONS { indexConfig: { `vector.dimensions`: 1024, `vector.similarity_function`: 'cosine' } }
""")

# Works — auto-commit transaction
with driver.session() as session:
    result = session.run("""
        CREATE VECTOR INDEX myIndex IF NOT EXISTS
        FOR (c:Chunk) ON (c.embedding)
        OPTIONS { indexConfig: { `vector.dimensions`: 1024, `vector.similarity_function`: 'cosine' } }
    """)
    result.consume()
```

The `result.consume()` call is essential. Without it, the session may close before the server finishes processing the statement. The same pattern applies to `DROP INDEX ... IF EXISTS`.

The `neo4j-graphrag` library's `create_vector_index` and `create_fulltext_index` functions use `driver.execute_query()` internally, which means they silently fail for the same reason. Use raw Cypher via `session.run()` instead.

---

## Neo4j Index Equivalence

Neo4j enforces index uniqueness by label and property, not by name. Attempting to create a second index on the same label+property combination under a different name returns `An equivalent index already exists`, even with `IF NOT EXISTS`.

This surfaces when multiple tools create indexes on the same schema. For example, if `populate_aircraft_db` creates an index named `requirement_embeddings` on `Chunk.embedding`, then `run_lab3_03.py` attempts to create `maintenanceChunkEmbeddings` on the same `Chunk.embedding`. The second creation fails because Neo4j sees the label and property are already indexed.

Two approaches handle this:

**Clean database (recommended for validation).** Reset the Neo4j database before running the validation suite. This eliminates any pre-existing indexes and ensures the script creates exactly the indexes it expects. The validation workflow is: reset database, run Lab 2 (structural graph), run Lab 3 (semantic layer).

**Detect and reuse.** Query `SHOW INDEXES` after the creation attempt and find the actual index name covering the target label+property. The validation script does this as a fallback:

```python
actual_vector_idx = VECTOR_INDEX_NAME
with driver.session() as session:
    result = session.run("""
        SHOW INDEXES
        YIELD name, state, type, labelsOrTypes, properties
        WHERE type IN ['VECTOR', 'FULLTEXT']
        RETURN name, state, type, labelsOrTypes, properties
    """)
    for rec in result:
        labels = rec["labelsOrTypes"]
        props = rec["properties"]
        if "Chunk" in labels and "embedding" in props and rec["type"] == "VECTOR":
            actual_vector_idx = rec["name"]
```

The index name returned by `SHOW INDEXES` is the one that must be passed to `db.index.vector.queryNodes` and `db.index.fulltext.queryNodes` for search queries.

---

## Quick Reference

| Task | Command |
|------|---------|
| Upload all scripts | `./upload.sh --all` |
| Smoke test | `./upload.sh test_hello.py && ./submit.sh test_hello.py` |
| Run Lab 2 | `./submit.sh run_lab2_02.py` |
| Run Lab 3 | `./submit.sh run_lab3_03.py` |
| List recent runs | `databricks jobs list-runs --profile <profile> --limit 5` |
| Get run details | `databricks jobs get-run <RUN_ID> --profile <profile> -o json` |
| Get task output | `databricks jobs get-run-output <TASK_RUN_ID> --profile <profile> -o json` |
| Upload CSV to Volume | `databricks fs cp file.csv "dbfs:/Volumes/catalog/schema/volume/file.csv" --profile <profile> --overwrite` |
| Local Neo4j verify | `cd lab_setup/verify_labs && uv run verify-labs lab2` |
