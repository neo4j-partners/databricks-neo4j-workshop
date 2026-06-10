# Databricks Setup CLI

A modular Python CLI tool for setting up and cleaning up Databricks environments for the Neo4j workshop.

For full usage instructions, configuration options, and examples, see the main [Lab Admin Setup Guide](../README.md#step-2-automated-setup).

## Quick Start

```bash
cd lab_setup/auto_scripts
uv sync

# Set up environment
uv run databricks-setup setup

# Tear down everything except the compute cluster
uv run databricks-setup cleanup
```

## Commands

### `setup`

Runs two tracks sequentially:

```
databricks-setup setup
├── Track A: Admin Cluster + Libraries
│   ├── Create or reuse dedicated admin Spark cluster
│   ├── Wait for cluster to reach RUNNING state
│   └── Install Neo4j Spark Connector + Python packages
│
├── Track B: Data + Lakehouse Tables
│   ├── Find SQL Warehouse
│   ├── Upload CSV files to Unity Catalog volume
│   ├── Upload workshop notebooks to shared workspace folder
│   ├── Verify upload
│   └── Create Delta Lake tables via Statement Execution API
│
└── Report results
```

```bash
uv run databricks-setup setup
```

All configuration is loaded from `lab_setup/.env` — see [Configuration](#configuration) below.

### `cleanup`

Deletes notebooks, lakehouse tables, volume, schemas, and catalog.

```bash
# Interactive confirmation prompt
uv run databricks-setup cleanup

# Skip confirmation
uv run databricks-setup cleanup --yes
```

## Configuration

Copy the example environment file and customize:

```bash
cp lab_setup/.env.example lab_setup/.env
```

Edit `.env` and set at minimum:

```bash
# Databricks CLI profile (optional - uses default if empty)
DATABRICKS_PROFILE=""
```

### All options

| Variable | Description | Default |
|----------|-------------|---------|
| `CATALOG_NAME` | Unity Catalog name | `databricks-neo4j-workshop` |
| `VOLUME_SCHEMA` | Schema for the data volume | `lab-schema` |
| `VOLUME_NAME` | Volume name for CSV data upload | `lab-volume` |
| `LAKEHOUSE_SCHEMA` | Schema for lakehouse Delta tables | `lakehouse` |
| `WAREHOUSE_NAME` | SQL Warehouse name (for lakehouse tables) | `Starter Warehouse` |
| `WAREHOUSE_TIMEOUT` | SQL statement timeout (seconds) | `600` |
| `DATABRICKS_PROFILE` | CLI profile from ~/.databrickscfg | Default |
| `CLUSTER_NAME` | Cluster name to create or reuse | `Small Spark 4.0` |
| `USER_EMAIL` | Cluster owner email | Auto-detected |
| `SPARK_VERSION` | Databricks Runtime version | `17.3.x-cpu-ml-scala2.13` |
| `AUTOTERMINATION_MINUTES` | Cluster auto-shutdown | `30` |
| `RUNTIME_ENGINE` | `STANDARD` or `PHOTON` | `STANDARD` |
| `NODE_TYPE` | Instance type for cluster nodes | `m5.large` |

### Cluster defaults

| Setting | Value |
|---------|-------|
| Runtime | 17.3 LTS ML (Spark 4.0.0, Scala 2.13) |
| Photon | Disabled (workshop data is small; Photon only benefits >100GB workloads) |
| Node type | `m5.large` (8 GB, 2 cores). Override via `NODE_TYPE` env var. |
| Workers | 0 (single node) |
| Access mode | Dedicated (Single User) |
| Auto-terminate | 30 minutes |

To change defaults, edit `.env`.

## Project Structure

```
auto_scripts/
├── pyproject.toml              # Project config, dependencies
├── uv.lock                     # Locked dependencies
├── README.md
└── src/databricks_setup/
    ├── __init__.py
    ├── main.py                 # Typer CLI entry point (setup + cleanup)
    ├── config.py               # Configuration dataclasses
    ├── models.py               # Shared domain models (SqlStep, SqlResult, etc.)
    ├── log.py                  # Dual-output logging (terminal + timestamped log file)
    ├── utils.py                # Polling, client helpers
    ├── cluster.py              # Cluster creation/management
    ├── libraries.py            # Library installation
    ├── data_upload.py          # Volume file upload
    ├── warehouse.py            # SQL Warehouse management + SQL execution
    ├── lakehouse_tables.py     # Lakehouse SQL definitions + creation
    └── cleanup.py              # Teardown logic (schemas, volume, catalog)
```

## Development

```bash
# Install with dev dependencies
uv sync

# Run linter
uv run ruff check src/

# Run type checker
uv run mypy src/

# Auto-fix linting issues
uv run ruff check --fix src/
```
