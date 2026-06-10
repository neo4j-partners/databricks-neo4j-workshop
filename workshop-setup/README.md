# Lab Admin Setup Guide

**Purpose:** Instructions for workshop administrators to prepare the Databricks environment before participants arrive.

---

## Quick Start: Load CSVs and Lakehouse Tables Only

To upload the CSV data and create the lakehouse Delta tables without running the full provisioning (cluster creation, library installs), use the `load_lakehouse_data.py` script. This runs only the data portion of `databricks-setup setup`.

**Prerequisites:** The catalog, schema, and volume must already exist (see [Step 1](#step-1-create-unity-catalog-and-volume-ui)). The script does not create them. Authenticate the Databricks CLI and configure `workshop-setup/.env` (see [Prerequisites](#prerequisites)).

```bash
cd workshop-setup/auto_scripts
uv sync
uv run python load_lakehouse_data.py
```

The script:

1. Uploads the CSVs from `aircraft_digital_twin_data_v2/` to the Unity Catalog volume.
2. Creates the `aircraft`, `systems`, `sensors`, and `sensor_readings` Delta tables via the Statement Execution API.
3. Prints the per-table row counts so you can confirm the load.

The script does not upload the GraphRAG maintenance manuals (the `MAINTENANCE_*.md` files live in `aircraft_digital_twin_data/`, not the v2 folder). Upload them separately if you are running Lab 3.

For the full administrator setup, continue with the checklist below.

---

## Pre-Workshop Checklist

Complete these steps before the workshop begins:

- [ ] Create Unity Catalog, Schema, and Volume (Step 1 — UI required)
- [ ] Run `databricks-setup setup` to upload data and create tables (Step 2)
- [ ] Test the complete workflow
- [ ] Document connection details for participants

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

If you have multiple Databricks profiles configured, set `DATABRICKS_PROFILE` in `.env` (see Step 2.1), or export for ad-hoc CLI commands:

```bash
export DATABRICKS_CONFIG_PROFILE=<your-profile-name>
```

### Python and uv

The CLI requires Python 3.11+ and [uv](https://docs.astral.sh/uv/):

```bash
cd workshop-setup/auto_scripts && uv sync
```

### Databricks Resources

The following resources must exist before running `databricks-setup`. See details below for setup instructions.

| Resource | Name | Created In |
|----------|------|------------|
| Unity Catalog | `databricks-neo4j-workshop` | [Step 1.1](#11-create-a-catalog) |
| Schema | `lab-schema` | [Step 1.2](#12-create-a-schema) |
| Volume | `lab-volume` | [Step 1.3](#13-create-the-volume) |

---


## Why Catalog Creation Is Manual

Newer Databricks workspaces use **Default Storage**, which blocks programmatic catalog creation via CLI, REST API, and SQL — all return the same error. Only the UI has the special handling to assign Default Storage to a new catalog. Once the catalog exists, everything else (schema, volume, compute, data upload, and table creation) is automated by `databricks-setup`. 

---

## Step 1: Create Unity Catalog and Volume (UI)

Create the catalog, schema, and volume through the Databricks UI.

### 1.1 Create a Catalog

1. Navigate to **Data** > **Catalogs** in the Databricks workspace
2. Click **Create Catalog**
3. Name it `databricks-neo4j-workshop` (or similar)
4. Select the appropriate metastore
5. Click **Create**

### 1.2 Create a Schema

1. Within the catalog, click **Create Schema**
2. Name it `lab-schema`
3. Click **Create**

### 1.3 Create the Volume

1. Navigate to the schema created above
2. Click **Create** > **Volume**
3. Configure:
   - **Name:** `lab-volume`
   - **Volume type:** Managed
4. Click **Create**

**Resulting path:** `/Volumes/databricks-neo4j-workshop/lab-schema/lab-volume/`

### 1.4 Verify Creation (CLI)

Confirm the catalog, schema, and volume exist with one command:

```bash
databricks volumes read databricks-neo4j-workshop.lab-schema.lab-volume
```

This returns volume metadata if successful, or an error if any component is missing.

---

## Step 2: Automated Setup

The `databricks-setup` CLI (in `auto_scripts/`) handles everything after catalog creation. It runs two sequential tracks:

- **Track A:** Creates/starts an admin cluster and installs libraries (Neo4j Spark Connector + Python packages)
- **Track B:** Uploads data files, notebooks, and creates Delta Lake tables via SQL Warehouse

### 2.1 Configure Environment

Copy the example environment file and customize:

```bash
cp workshop-setup/.env.example workshop-setup/.env
```

Edit `.env` and set at minimum:

```bash
# Databricks CLI profile (optional - uses default if empty)
DATABRICKS_PROFILE=""
```

For the full list of configuration options, see the [auto_scripts README](auto_scripts/README.md#configuration).

### 2.2 Run Setup

```bash
cd workshop-setup/auto_scripts
uv run databricks-setup setup
```

All configuration is loaded from `workshop-setup/.env` — there are no CLI arguments.

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

For configuration details (environment variables, cluster defaults, cloud provider options), see the [auto_scripts README](auto_scripts/README.md#configuration).

---

### Manual Setup (UI Alternative)

If you prefer to set up the data through the Databricks UI instead of using `databricks-setup`, see the complete step-by-step guide in **[MANUAL_SETUP.md](docs/MANUAL_SETUP.md)**.

---

## Step 3: Prepare Participant Instructions

Create a handout or slide with:

### Connection Information

| Resource | Value |
|----------|-------|
| Databricks Workspace URL | `https://your-workspace.cloud.databricks.com` |
| Data Volume Path | `/Volumes/databricks-neo4j-workshop/lab-schema/lab-volume/` |
| Shared Notebook Folder | `/Shared/databricks-neo4j-workshop/` |

### Quick Start Instructions

1. Sign in to Databricks with your workshop credentials
2. Navigate to Compute and verify the workshop cluster is running
3. Open **Workspace** > **Shared** > **databricks-neo4j-workshop** to find the lab notebooks
4. Enter your Neo4j credentials from Lab 1
5. Run all cells (Shift+Enter or Run All)
6. Verify the counts in the output cells

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

### Common Issues

**"Spark Connector not found" error**
- Verify the participant's cluster is in Dedicated (Single User) mode
- Check library installation status on the cluster
- Restart the cluster after adding the library

**"Connection refused" to Neo4j**
- Verify URI format: `neo4j+s://` for Aura
- Check participant's Neo4j instance is running
- Verify credentials are correct

**"Path does not exist" for Volume**
- Verify Volume path matches notebook configuration
- Check files were uploaded successfully
- Confirm participant has access to the catalog

**Duplicate nodes on re-run**
- The notebook uses Overwrite mode which should handle this
- If issues persist, have participants run cleanup query:
  ```cypher
  MATCH (n) DETACH DELETE n
  ```

**Genie not generating correct SQL**
- Ensure table comments are added (handled by `databricks-setup` CLI)
- Verify table relationships are configured in the Genie Space
- Add more sample questions to guide the model

**Lakehouse table creation fails**
- Ensure CSV files are uploaded to the Volume first
- Check file paths match exactly
- Verify the SQL Warehouse has access to the Volume

---

## CLI Command Reference

```
databricks-setup setup                         # Create admin cluster, upload data, create tables
databricks-setup cleanup [--yes]               # Delete data, tables, and catalog
databricks-setup sync                          # Upload/sync workshop notebooks to workspace
```

---

## File Inventory

For the full file inventory with sizes, record counts, and sensor data details, see **[MANUAL_SETUP.md](docs/MANUAL_SETUP.md#file-inventory)**.

The setup CLI uploads **25 files** to the Volume:
- **22 CSV files** from `aircraft_digital_twin_data/` (nodes and relationships for Labs 2 and 3)
- **3 Markdown files** (maintenance manuals for Lab 3: A320, A321neo, B737)

---

## Cost Considerations

- **Clusters:** The setup creates a single-node admin cluster (m5.large by default)
- **Auto-termination:** Set to 30 minutes by default to avoid idle costs
- **Storage:** Volume storage for CSV files is negligible (~25 MB total)
- **Delta Lake:** The lakehouse tables add minimal storage overhead
- **Genie:** Genie queries consume compute resources; monitor usage during workshop

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

## Contact

For issues during workshop setup, contact the workshop organizers or refer to:
- [Neo4j Spark Connector Documentation](https://neo4j.com/docs/spark/current/)
- [Databricks Unity Catalog Documentation](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
- [Databricks Genie Documentation](https://docs.databricks.com/en/genie/index.html)
