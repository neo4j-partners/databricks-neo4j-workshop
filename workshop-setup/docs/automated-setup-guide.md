# databricks-setup CLI Guide

**Purpose:** Reference for the `databricks-setup` CLI in `auto_scripts/`, the laptop-driven companion to the [setup notebook](../workshop_setup.ipynb).

The notebook is the primary way to provision the Databricks side: it creates the schema and volume, downloads the data, and builds the lakehouse tables. The CLI exists for the jobs the notebook does not do:

- **`sync`** uploads the Lab 2, Lab 3, and MCP notebooks into the workspace. The setup notebook never touches these, so this is the usual way to get the lab notebooks in front of participants.
- **`cleanup`** tears the whole environment down: lakehouse tables, volume, schema, catalog, and the notebook folder.
- **`load_lakehouse_data.py`** reloads just the CSVs and Delta tables from your laptop, handy when you do not want to open a notebook.

Full `setup` is also available as a laptop alternative to running the notebook; see [Full setup](#full-setup-alternative-to-the-notebook) at the end.

The catalog must already exist before running any of these. Catalog creation is UI-only on Default Storage workspaces; see [Step 1 in the main README](../README.md#step-1-create-the-catalog-ui-required).

---

## Prerequisites

### Databricks CLI authentication

Authenticate the Databricks CLI with your user account:

```bash
databricks auth login --host <your-workspace-url>
```

This opens a browser for OAuth login. After authenticating, verify you are logged in as your user, not a service principal:

```bash
databricks current-user me
```

You should see your email address in the output.

#### Using a named profile

If you have multiple Databricks profiles configured, set `DATABRICKS_PROFILE` in `.env` (see [Configure environment](#configure-environment)), or export for ad-hoc CLI commands:

```bash
export DATABRICKS_CONFIG_PROFILE=<your-profile-name>
```

### Python and uv

The CLI requires Python 3.11+ and [uv](https://docs.astral.sh/uv/):

```bash
cd workshop-setup/auto_scripts && uv sync
```

### Configure environment

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

### Databricks resources

These must exist before running the CLI:

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

## Command reference

```
databricks-setup sync                          # Upload/sync the lab notebooks to the workspace
databricks-setup cleanup [--yes]               # Delete tables, volume, schema, catalog, notebooks
databricks-setup setup                         # Full provisioning (alternative to the notebook)
```

All configuration is loaded from `workshop-setup/.env`; there are no CLI arguments.

---

## `sync`: upload the lab notebooks

The setup notebook provisions data and tables but does not upload the notebooks participants run. `sync` does:

```bash
cd workshop-setup/auto_scripts
uv run databricks-setup sync
```

It uploads the Lab 2, Lab 3, and MCP notebooks to `/Shared/databricks-neo4j-workshop/`. The `neo4j_mcp_connection` folder is deleted first to avoid stale artifacts, then re-uploaded cleanly. Cloning the repo as a Git folder is the alternative if you would rather not use the CLI.

---

## `cleanup`: tear everything down

Removes everything the workshop created: lakehouse tables, volume, schemas, catalog, and the notebook folder. Each step is idempotent, so it is safe to re-run if a previous run stopped partway.

```bash
cd workshop-setup/auto_scripts

# Interactive confirmation
uv run databricks-setup cleanup

# Skip confirmation
uv run databricks-setup cleanup --yes
```

This permanently deletes the catalog and all its contents, so the confirmation prompt is there on purpose.

---

## Quick load: CSVs and lakehouse tables only

To upload the CSV data and create the lakehouse Delta tables without the full provisioning, run `load_lakehouse_data.py`. This is the data portion of `setup` (Track B) minus the notebook upload.

**Prerequisites:** The catalog, schema, and volume must already exist. The script does not create them.

```bash
cd workshop-setup/auto_scripts
uv run python load_lakehouse_data.py
```

The script:

1. Uploads the CSVs and the `MAINTENANCE_*.md` manuals from `aircraft_digital_twin_data/` to the Unity Catalog volume.
2. Creates the `aircraft`, `systems`, `sensors`, and `sensor_readings` Delta tables via the Statement Execution API.
3. Prints the per-table row counts so you can confirm the load.

---

## Full setup (alternative to the notebook)

`setup` provisions the same things the [setup notebook](../workshop_setup.ipynb) does, driven from your laptop instead of from a notebook cell. Reach for it when you are scripting environment creation outside the workspace; otherwise the notebook is the simpler path.

```bash
cd workshop-setup/auto_scripts
uv run databricks-setup setup
```

It runs two tracks sequentially:

**Track A, admin cluster and libraries:**
1. Creates or reuses a dedicated admin Spark cluster.
2. Waits for the cluster to reach RUNNING state.
3. Installs the Neo4j Spark Connector and Python packages.

**Track B, data upload and lakehouse tables:**
1. Finds the configured SQL Warehouse.
2. Uploads CSV and Markdown data files to the volume.
3. Uploads workshop notebooks to the shared workspace folder.
4. Creates Delta Lake tables via the Statement Execution API.

All operations are idempotent, so the command is safe to re-run. For configuration details such as environment variables, cluster defaults, and cloud provider options, see the [auto_scripts README](../auto_scripts/README.md#configuration).

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
