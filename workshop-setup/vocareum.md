# Updating Vocareum When Labs Change

When you modify notebooks in the repo's `Lab_2_Databricks_ETL_Neo4j/` or `Lab_3_Semantic_Search/` directories, three additional locations must be updated before the changes reach workshop participants.

## What Lives Where

The repo maintains two copies of every lab notebook:

| Location | Purpose |
|----------|---------|
| `Lab_2_Databricks_ETL_Neo4j/*.ipynb` | Source of truth (repo root) |
| `Lab_3_Semantic_Search/*.ipynb` | Source of truth (repo root) |
| `vocareum/courseware/data/Lab_*/*.ipynb` | Staging copy used to build archives |
| `vocareum/courseware/neo4j-databricks-workshop.dbc` | Zip archive imported by Databricks |
| `vocareum/courseware/neo4j-databricks-workshop.dat` | Identical copy of `.dbc` (`.dat` extension prevents Vocareum from auto-extracting on upload) |

The `.dbc` and `.dat` files are byte-identical zip archives containing all notebooks and supporting files (`data_utils.py`). Databricks imports the `.dbc`; Vocareum uses the `.dat` for distribution.

## Step-by-Step Update Process

### 1. Edit the source notebook

Make your change in the repo root (e.g., `Lab_3_Semantic_Search/05_mcp_graph_queries.ipynb`).

### 2. Copy to the vocareum staging directory

```bash
# Copy the changed file(s)
cp Lab_3_Semantic_Search/05_mcp_graph_queries.ipynb \
   vocareum/courseware/data/Lab_3_Semantic_Search/05_mcp_graph_queries.ipynb
```

Or copy an entire lab directory if multiple files changed:

```bash
cp Lab_3_Semantic_Search/*.ipynb vocareum/courseware/data/Lab_3_Semantic_Search/
cp Lab_3_Semantic_Search/data_utils.py vocareum/courseware/data/Lab_3_Semantic_Search/
```

### 3. Rebuild the archive

```bash
cd vocareum/courseware/data
zip -r ../neo4j-databricks-workshop.dbc \
    Lab_2_Databricks_ETL_Neo4j/ \
    Lab_3_Semantic_Search/
cp ../neo4j-databricks-workshop.dbc ../neo4j-databricks-workshop.dat
```

The default `zip` command uses Deflate compression for files and Stored for directories, which matches the existing archive format.

### 4. Verify the archive

```bash
# List contents and compression method
unzip -v vocareum/courseware/neo4j-databricks-workshop.dbc

# Confirm .dbc and .dat are identical
diff vocareum/courseware/neo4j-databricks-workshop.dbc \
     vocareum/courseware/neo4j-databricks-workshop.dat
```

Check that:
- All expected files are present (directories use `Stored`, files use `Defl:N`)
- Only the files you changed have new timestamps and CRC-32 values
- File count matches (currently 9 files: 2 Lab 2 notebooks, 4 Lab 3 notebooks, `data_utils.py`, 2 directory entries)

### 5. Verify source parity

Confirm the vocareum staging copy matches the repo source:

```bash
for f in \
    Lab_2_Databricks_ETL_Neo4j/01_aircraft_etl_to_neo4j.ipynb \
    Lab_2_Databricks_ETL_Neo4j/02_load_neo4j_full.ipynb \
    Lab_3_Semantic_Search/03_data_and_embeddings.ipynb \
    Lab_3_Semantic_Search/04_graphrag_retrievers.ipynb \
    Lab_3_Semantic_Search/05_mcp_graph_queries.ipynb \
    Lab_3_Semantic_Search/06_hybrid_retrievers.ipynb \
    Lab_3_Semantic_Search/data_utils.py; do
    diff "$f" "vocareum/courseware/data/$f" > /dev/null 2>&1 \
        && echo "MATCH: $f" \
        || echo "DIFFER: $f"
done
```

Every file should show `MATCH`.

## Adding or Removing Notebooks

If you add a new notebook or remove an existing one:

1. Add/remove the file in both the repo root lab directory and `vocareum/courseware/data/Lab_*/`
2. Rebuild the archives (step 3 above) — `zip -r` captures the full directory contents
3. If the new notebook is the entry point, update `vocareum/courseware/neo4j-databricks-workshop.cfg`:

```json
{
  "content": {
    "src": "neo4j-databricks-workshop.dat",
    "entry": "Lab_2_Databricks_ETL_Neo4j/01_aircraft_etl_to_neo4j"
  }
}
```

The `entry` field controls which notebook opens first when a participant launches their workspace.

## Other Vocareum Artifacts

These files are independent of the lab notebooks and only need updating if their specific concerns change:

| File | When to update |
|------|---------------|
| `courseware/aircraft_digital_twin_data.zip` | CSV data schema changes |
| `courseware/dlt_fleet_etl.py` | DLT pipeline logic changes |
| `courseware/neo4j-databricks-workshop.cfg` | Cluster config, Spark version, entry notebook, or catalog name changes |
| `scripts/python/*.py` | Workspace provisioning, user setup, or teardown logic changes |
| `docs/README.md` | Student-facing instructions change |

## Upload to Vocareum

After rebuilding, upload the updated files to the Vocareum filesystem via **Configure Workspace > Files**:

| Local file | Upload to |
|------------|-----------|
| `courseware/neo4j-databricks-workshop.dbc` | `/voc/private/courseware/` |
| `courseware/neo4j-databricks-workshop.dat` | `/voc/private/courseware/` |

See `vocareum/SETUP_GUIDE.md` for the complete file mapping and first-time setup instructions.
