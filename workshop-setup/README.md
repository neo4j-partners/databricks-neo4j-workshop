# Lab Admin Setup Guide

**Purpose:** Instructions for workshop administrators to prepare the Databricks environment before participants arrive.

---

## Pre-Workshop Checklist

Complete these steps before the workshop begins:

- [ ] Create the Unity Catalog catalog (Step 1, UI required)
- [ ] Run the `workshop_setup.ipynb` notebook to provision everything else (Step 2)
- [ ] Test the complete workflow
- [ ] Document connection details for participants

---

## Step 1: Create the Catalog (UI, Required)

### Why Catalog Creation Is Manual

Newer Databricks workspaces use **Default Storage**, which blocks programmatic catalog creation via CLI, REST API, and SQL. All return the same error. Only the UI has the special handling to assign Default Storage to a new catalog. Once the catalog exists, everything else (schema, volume, compute, data download, and table creation) is handled by the setup notebook.

### Create the Catalog

1. Navigate to **Data** > **Catalogs** in the Databricks workspace
2. Click **Create Catalog**
3. Name it `databricks-neo4j-workshop` (or similar)
4. Select the appropriate metastore
5. Click **Create**

The schema (`aircraft`) and volume (`raw_data`) are created by the setup notebook in Step 2; you do not need to create them in the UI.

---

## Step 2: Run the Setup Notebook

The notebook [`workshop_setup.ipynb`](workshop_setup.ipynb) provisions everything after catalog creation. Run it top to bottom as an admin preparing a shared workspace, or as a participant self-serving in your own workspace or Free Edition account.

### Get the notebook into the workspace

Either:

- **Import it**: in the workspace, go to **Workspace** > **Import** and upload `workshop-setup/workshop_setup.ipynb`, or
- **Clone the repo as a Git folder** and open the notebook from `workshop-setup/`.

### What it does

1. **Classic compute cluster and libraries**: UI steps to create the cluster Labs 2 and 3 need (the Neo4j Spark Connector is a Maven library, which serverless compute cannot install), plus an optional cell that automates it with the Databricks SDK.
2. **Catalog, schema, and volume**: creates the schema and volume under the catalog from Step 1. If you used a different catalog name, change the `CATALOG` constant in the notebook.
3. **Workshop data**: downloads the 22 CSVs and 5 maintenance manuals from the public GitHub repo straight into the volume.
4. **Lakehouse tables**: creates the four Delta tables (`aircraft`, `systems`, `sensors`, `sensor_readings`) with Genie-friendly table and column comments, then verifies row counts.
5. **SQL warehouse check**: confirms a SQL warehouse exists for the labs and Genie.

All cells are idempotent, so the notebook is safe to re-run.

**Free Edition note:** Free Edition provides serverless compute only and cannot create classic clusters, so the cluster step needs a standard workspace. The rest of the notebook runs fine on Free Edition.

---

## Alternative Setup Paths

- **CLI automation**: the `databricks-setup` CLI in `auto_scripts/` automates cluster creation, data upload, and table creation from your laptop. See **[docs/automated-setup-guide.md](docs/automated-setup-guide.md)**.
- **Full UI walkthrough**: to set everything up through the Databricks UI step by step, see **[docs/MANUAL_SETUP.md](docs/MANUAL_SETUP.md)**.

---

## Step 3: Prepare Participant Instructions

Create a handout or slide with:

### Connection Information

| Resource | Value |
|----------|-------|
| Databricks Workspace URL | `https://your-workspace.cloud.databricks.com` |
| Data Volume Path | `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/` |
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
- Ensure table comments are added (handled by the setup notebook)
- Verify table relationships are configured in the Genie Space
- Add more sample questions to guide the model

**Lakehouse table creation fails**
- Ensure CSV files are uploaded to the Volume first
- Check file paths match exactly
- Verify the SQL Warehouse has access to the Volume

---

## File Inventory

For the full file inventory with sizes, record counts, and sensor data details, see **[MANUAL_SETUP.md](docs/MANUAL_SETUP.md#file-inventory)**.

The setup notebook downloads **27 files** into the Volume:
- **22 CSV files** from `aircraft_digital_twin_data/` (nodes and relationships for Labs 2 and 3)
- **5 Markdown files** (maintenance manuals for Lab 3: A220, A320, A321neo, B737, E190)

---

## Cost Considerations

- **Clusters:** The setup creates a single-node admin cluster (m5.large by default)
- **Auto-termination:** Set to 30 minutes by default to avoid idle costs
- **Storage:** Volume storage for CSV files is negligible (~25 MB total)
- **Delta Lake:** The lakehouse tables add minimal storage overhead
- **Genie:** Genie queries consume compute resources; monitor usage during workshop

---

## Contact

For issues during workshop setup, contact the workshop organizers or refer to:
- [Neo4j Spark Connector Documentation](https://neo4j.com/docs/spark/current/)
- [Databricks Unity Catalog Documentation](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
- [Databricks Genie Documentation](https://docs.databricks.com/en/genie/index.html)
