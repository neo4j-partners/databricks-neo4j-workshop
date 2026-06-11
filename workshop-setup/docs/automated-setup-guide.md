# Automated Setup Guide (databricks-setup CLI)

**Purpose:** Set up the Databricks workshop environment from your laptop with the `databricks-setup` CLI in `auto_scripts/`, as an alternative to running the [setup notebook](../workshop_setup.ipynb).

The catalog must already exist before running the CLI. Catalog creation is UI-only on Default Storage workspaces; see [Step 1 in the main README](../README.md#step-1-create-the-catalog-ui-required).

---

## Quick Start: Load CSVs and Lakehouse Tables Only

To upload the CSV data and create the lakehouse Delta tables without running the full provisioning (cluster creation, library installs), use the `load_lakehouse_data.py` script. This runs only the data portion of `databricks-setup setup`.

**Prerequisites:** The catalog, schema, and volume must already exist. The script does not create them. Authenticate the Databricks CLI and configure `workshop-setup/.env` (see [Prerequisites](#prerequisites)).

```bash
cd workshop-setup/auto_scripts
uv sync
uv run python load_lakehouse_data.py
```

The script:

1. Uploads the CSVs and the `MAINTENANCE_*.md` manuals from `aircraft_digital_twin_data/` to the Unity Catalog volume.
2. Creates the `aircraft`, `systems`, `sensors`, and `sensor_readings` Delta tables via the Statement Execution API.
3. Prints the per-table row counts so you can confirm the load.

For the full automated setup, continue with the sections below.

---

## Prerequisites

### Databricks CLI Authentication

Before running any CLI commands, authenticate the Databricks CLI with your user account:

```bash
databricks auth login --host <your-workspace-url>
```

This opens a browser for OAuth login. After authenticating, verify you are logged in as your user (not a service principal):

```bash
databricks current-user me
```

You should see your email address in the output.

#### Using a Named Profile

If you have multiple Databricks profiles configured, set `DATABRICKS_PROFILE` in `.env` (see [Configure Environment](#configure-environment)), or export for ad-hoc CLI commands:

```bash
export DATABRICKS_CONFIG_PROFILE=<your-profile-name>
```

### Python and uv

The CLI requires Python 3.11+ and [uv](https://docs.astral.sh/uv/):

```bash
cd workshop-setup/auto_scripts && uv sync
```

### Databricks Resources

The following resources must exist before running `databricks-setup`:

| Resource | Name | Created In |
|----------|------|------------|
| Unity Catalog | `databricks-neo4j-workshop` | UI, see [main README Step 1](../README.md#step-1-create-the-catalog-ui-required) |
| Schema | `aircraft` | The setup notebook, or manually in the UI |
| Volume | `raw_data` | The setup notebook, or manually in the UI |

To create the schema and volume in the UI, see [MANUAL_SETUP.md](MANUAL_SETUP.md). Verify all three exist with one command:

```bash
databricks volumes read databricks-neo4j-workshop.aircraft.raw_data
```

This returns volume metadata if successful, or an error if any component is missing.

---

## Automated Setup

The `databricks-setup` CLI (in `auto_scripts/`) handles everything after catalog creation. It runs two sequential tracks:

- **Track A:** Creates/starts an admin cluster and installs libraries (Neo4j Spark Connector + Python packages)
- **Track B:** Uploads data files, notebooks, and creates Delta Lake tables via SQL Warehouse

### Configure Environment

Copy the example environment file and customize:

```bash
cp workshop-setup/.env.example workshop-setup/.env
```

Edit `.env` and set at minimum:

```bash
# Databricks CLI profile (optional - uses default if empty)
DATABRICKS_PROFILE=""
```

For the full list of configuration options, see the [auto_scripts README](../auto_scripts/README.md#configuration).

### Run Setup

```bash
cd workshop-setup/auto_scripts
uv run databricks-setup setup
```

All configuration is loaded from `workshop-setup/.env`; there are no CLI arguments.

### What it does

Runs two tracks sequentially:

**Track A — Admin Cluster + Libraries:**
1. Creates or reuses a dedicated admin Spark cluster
2. Waits for the cluster to reach RUNNING state
3. Installs Neo4j Spark Connector and Python packages

**Track B — Data Upload + Lakehouse Tables:**
1. Finds the configured SQL Warehouse
2. Uploads CSV and Markdown data files to the volume
3. Uploads workshop notebooks to the shared workspace folder
4. Creates Delta Lake tables via the Statement Execution API

All operations are idempotent — safe to re-run.

For configuration details (environment variables, cluster defaults, cloud provider options), see the [auto_scripts README](../auto_scripts/README.md#configuration).

---

## CLI Command Reference

```
databricks-setup setup                         # Create admin cluster, upload data, create tables
databricks-setup cleanup [--yes]               # Delete data, tables, and catalog
databricks-setup sync                          # Upload/sync workshop notebooks to workspace
```

---

## Cleanup

To tear down the data (lakehouse tables, volume, schemas, catalog, and notebook folder):

```bash
cd workshop-setup/auto_scripts

# Interactive confirmation
uv run databricks-setup cleanup

# Skip confirmation
uv run databricks-setup cleanup --yes
```

Each step is idempotent — safe to re-run if partially completed.

---

## Troubleshooting

### Authentication

If you see a UUID instead of your email when running `databricks current-user me`, your CLI may be configured with a service principal. Check for overriding environment variables:

```bash
env | grep -i DATABRICKS
```

If present, unset them for interactive use:

```bash
unset DATABRICKS_TOKEN
unset DATABRICKS_CLIENT_ID
unset DATABRICKS_CLIENT_SECRET
```

Then re-run `databricks auth login`.
