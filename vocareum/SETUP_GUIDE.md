# Vocareum Setup Guide: Neo4j + Databricks Workshop

## Prerequisites

- Vocareum access (request via http://go/vocareum-lab-development)
- Access to the appropriate Vocareum org (GenAI for Serverless)
- Join **#field-driven-labs-vocareum** on Slack for help

## Step 1: Clone a Template

1. Log into Vocareum (https://labs.vocareum.com)
2. Find an existing Databricks lab template in **DB Field Driven Enablement Labs**
3. Click **Clone** → **Clone by Copy**
4. Set Course Name: `Neo4j + Databricks Workshop`
5. Select Organization: **GenAI** (for serverless support)
6. Leave all other fields default, click Clone

## Step 2: Course Settings

On the Vocareum home page → click **Settings** for your course:

| Setting | Value |
|---------|-------|
| Course Name | Neo4j + Databricks Workshop |
| Start Date | Workshop start date |
| End Date | Workshop end date + 1 day buffer |
| LTI | **Disabled** (for direct enrollment) |
| Course Feedback | Enabled |

## Step 3: Lab Settings (Assignment/Part)

Click **Assignments** → click on the Part → configure:

| Setting | Value |
|---------|-------|
| Part Name | Neo4j Databricks Lab |
| Lab Type | **Databricks** |
| Users per workspace | 25 |
| Session Length | **240** minutes |
| End Lab Behavior | **Terminate resources** |
| Timer | **Enabled** |
| Readme Button | **Enabled** |

## Step 4: Upload Files

Click **Configure Workspace** → **Files** in the Assignment tab.

### Complete File Mapping

Upload from `vocareum/` in this repo to Vocareum filesystem:

| Local file | Upload to | Purpose |
|------------|-----------|---------|
| `courseware/neo4j-databricks-workshop.cfg` | `/voc/private/courseware/` | Course config: cluster spec, entry notebook, default catalog |
| `courseware/neo4j-databricks-workshop.dat` | `/voc/private/courseware/` | Lab notebooks. The `.dat` extension prevents Vocareum auto-extract |
| `courseware/aircraft_digital_twin_data.zip` | `/voc/private/courseware/` | Workshop data, 2.1 MB, 27 files. The init script also accepts `.dat` or a pre-extracted folder |
| `scripts/workspace_init.sh` | `/voc/scripts/` | Shell wrapper |
| `scripts/user_setup.sh` | `/voc/scripts/` | Shell wrapper |
| `scripts/lab_setup.sh` | `/voc/scripts/` | Shell wrapper |
| `scripts/lab_end.sh` | `/voc/scripts/` | Shell wrapper |
| `scripts/python/workspace_init.py` | `/voc/scripts/python/` | Workspace init logic |
| `scripts/python/user_setup.py` | `/voc/scripts/python/` | Per-user setup |
| `scripts/python/lab_setup.py` | `/voc/scripts/python/` | Lab resume |
| `scripts/python/lab_end.py` | `/voc/scripts/python/` | Resource cleanup |
| `scripts/python/workshop_data_setup.py` | `/voc/scripts/python/` | Data staging + DLT pipeline setup |
| `courseware/dlt_fleet_etl.py` | `/voc/private/courseware/` | DLT notebook (bronze → silver → gold) |
| `docs/README.md` | `/voc/docs/` | Iframe instructions shown to participants |

**Note:** Upload `scripts/python/dbacademy.py` to `/voc/scripts/python/`. This is a patched version that fixes `delta_sharing_recipient_token_lifetime` and adds a `self.w` None guard. If the template already has one, **overwrite it** with ours.

`courseware/neo4j-databricks-workshop.dbc` is the same archive as the `.dat` file. Keep it for direct Databricks import during testing. Vocareum uses the `.dat` copy.

### What Is in the Data Zip

`aircraft_digital_twin_data.zip` contains 27 files under a single `aircraft_digital_twin_data/` folder:

- **22 CSVs**: 10 node exports and 12 relationship exports
- **5 maintenance manuals**: `MAINTENANCE_A220.md`, `MAINTENANCE_A320.md`, `MAINTENANCE_A321neo.md`, `MAINTENANCE_B737.md`, `MAINTENANCE_E190.md`

The manuals are required. Lab 3 notebook 01 reads `MAINTENANCE_A320.md` from the Unity Catalog volume, and it fails if the manuals are absent.

Dataset volumes:

| Entity | Rows |
|--------|------|
| Aircraft | 36 |
| Airports | 40 |
| Systems | 144 |
| Components | 612 |
| Sensors | 288 |
| Flights | 14,543 |
| Delays | 5,541 |
| Maintenance events | 286 |
| Removals | 57 |
| Sensor readings | 155,520 |

Sensor readings cover July 1, 2024 through September 28, 2024, at 4-hour intervals. That is 540 timestamps across 90 days for each of the 288 sensors.

### What Is in the Notebook Bundle

`neo4j-databricks-workshop.dat` contains 5 files:

```
Lab_2_Databricks_ETL_Neo4j/
  01_aircraft_etl_to_neo4j.ipynb     <- entry notebook
Lab_3_Semantic_Search/
  01_data_and_embeddings.ipynb
  02_graphrag_retrievers.ipynb
  03_hybrid_retrievers.ipynb
  data_utils.py
```

The Graph Data Science notebooks are deliberately excluded. `Lab_2_Databricks_ETL_Neo4j/02_gds_knn_aircraft.ipynb` and everything under `Appendix_A_GDS_Graph_Analytics/` require AuraDB Professional, and Vocareum participants use Aura Free.

Labs 1 and 4 have no notebooks. Their instructions live on the published workshop site, which `docs/README.md` links to:
`https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/`

### Rebuilding the Bundle and the Data Zip

Both uploaded artifacts are generated from the main workshop, not authored by hand. Regenerate them whenever the labs or the dataset change, otherwise Vocareum silently drifts from the workshop that everyone else runs.

`vocareum/courseware/data/` is the staging directory for the bundle. It is a checked-in mirror of the lab notebooks, and it is not uploaded to Vocareum directly.

Run from the repository root:

```bash
# 1. Refresh the staged notebooks from the main labs
cp Lab_2_Databricks_ETL_Neo4j/01_aircraft_etl_to_neo4j.ipynb \
   vocareum/courseware/data/Lab_2_Databricks_ETL_Neo4j/
cp Lab_3_Semantic_Search/0[123]_*.ipynb Lab_3_Semantic_Search/data_utils.py \
   vocareum/courseware/data/Lab_3_Semantic_Search/

# 2. Rebuild the bundle (.dbc is a byte-identical copy of .dat)
cd vocareum/courseware/data
rm -f ../neo4j-databricks-workshop.dat ../neo4j-databricks-workshop.dbc
zip -q -r -X ../neo4j-databricks-workshop.dat \
    Lab_2_Databricks_ETL_Neo4j Lab_3_Semantic_Search \
    -x '*.DS_Store' -x '*__pycache__*'
cp ../neo4j-databricks-workshop.dat ../neo4j-databricks-workshop.dbc
cd ../../..

# 3. Rebuild the data zip from the canonical dataset
rm -rf /tmp/vocdata && mkdir -p /tmp/vocdata/aircraft_digital_twin_data
cp workshop-setup/aircraft_digital_twin_data/*.csv \
   workshop-setup/aircraft_digital_twin_data/*.md \
   /tmp/vocdata/aircraft_digital_twin_data/
(cd /tmp/vocdata && zip -q -r -X aircraft_digital_twin_data.zip aircraft_digital_twin_data)
cp /tmp/vocdata/aircraft_digital_twin_data.zip vocareum/courseware/
```

Verify before uploading. Both commands should report no differences:

```bash
# Bundle matches the main labs
unzip -q -o vocareum/courseware/neo4j-databricks-workshop.dat -d /tmp/datcheck
diff -r /tmp/datcheck vocareum/courseware/data

# Data zip matches the canonical dataset
unzip -q -o vocareum/courseware/aircraft_digital_twin_data.zip -d /tmp/zipcheck
diff -r /tmp/zipcheck/aircraft_digital_twin_data workshop-setup/aircraft_digital_twin_data
```

`-X` strips extra file attributes so the archive is reproducible. Exclude `__pycache__`, which otherwise ships a stale compiled `data_utils`.

## What Happens Automatically

### On Workspace Init (`workspace_init.py`)
1. **dbacademy** creates the metastore, the default catalog `databricks-neo4j-workshop`, and a shared warehouse
2. The script locates the data, extracting `aircraft_digital_twin_data.dat` or `.zip` if a pre-extracted folder is absent
3. **workshop_data_setup.py** then:
   - Creates the catalog, the `aircraft` schema, and the `raw_data` volume
   - Uploads 22 CSVs and 5 maintenance manuals to `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/`
   - Uploads the DLT notebook to `/Shared/workshop/dlt_fleet_etl`
   - Creates and full-refreshes a **serverless DLT pipeline** named `Fleet Digital Twin ETL`:
     - **Bronze**: raw CSV ingestion, 10 node tables and 12 relationship tables
     - **Silver**: cleaned, typed, validated entities with DQ expectations
     - **Gold**: analytics-ready tables enriched with joins and aggregations
   - Adds Genie-friendly table and column comments
   - Grants SELECT on the gold tables and USE on the catalog, schema, and volume to `account users`
   - Grants CREATE CONNECTION on the metastore to `account users`

#### Where the pipeline tables land

Bronze and silver tables publish to a separate schema, `aircraft_pipeline`. Only the 8 gold tables land in `databricks-neo4j-workshop.aircraft`, which keeps the schema participants browse free of intermediate tables.

| Gold table | Used by |
|------------|---------|
| `aircraft` | Lab 4 Genie space |
| `systems` | Lab 4 Genie space |
| `sensors` | Lab 4 Genie space |
| `sensor_readings` | Lab 4 Genie space |
| `flights` | Reference and exploration |
| `maintenance_events` | Reference and exploration |
| `fleet_readiness` | Reference and exploration |
| `sensor_health` | Reference and exploration |

The Lab 4 Genie space needs only the first four. The other four are available for participants who want to explore further.

The gold `systems` and `sensors` tables use the column names `type` and `name`. They previously used `system_type`, `system_name`, `sensor_type`, and `sensor_name`. The current names match the `auto_scripts` tables used outside Vocareum and the Genie instructions in Lab 4 Part A.

### On User Setup (`user_setup.py`)
- Creates a per-user single-node cluster from the spec in `neo4j-databricks-workshop.cfg`: DBR `17.3.x-cpu-ml-scala2.13`, node type `m5.large`, 120-minute auto-termination
- Installs the Neo4j Spark Connector plus 10 PyPI packages on that cluster
- Creates a per-user schema for scratch work
- Creates a working volume in the ops schema
- Imports the lab notebooks to the user's home folder
- Returns a redirect URL to the entry notebook, `Lab_2_Databricks_ETL_Neo4j/01_aircraft_etl_to_neo4j`

The PyPI packages are `neo4j==6.2.0`, `databricks-agents>=1.11.0`, `langgraph==1.2.4`, `langchain-openai==1.3.0`, `pydantic==2.13.4`, `langchain-core>=1.4.6`, `databricks-langchain>=0.20.0`, `neo4j-graphrag>=1.17.0`, `beautifulsoup4>=4.15.0`, and `sentence_transformers`. Lab 2 and Lab 3 raise `ImportError` without them, so do not strip the library list when editing the cfg.

### On Lab Resume (`lab_setup.py`)
- Starts the user's cluster and warehouse if stopped
- Returns the redirect URL

### On Lab End (`lab_end.py`)
- Terminates the user's cluster
- Stops the user's warehouse
- Drops the user catalog and schema
- Cleans up metadata

## Manual Pre-Workshop Steps

### A. Neo4j Aura

Two separate Aura instances are involved.

**Participant instances.** Each participant creates their own Aura Free instance during Lab 1 and uses it for Labs 2 and 3. No pre-provisioning needed.

**Reference instance.** Lab 4 does not use participant instances. It queries a single administrator-managed **Reference Aura Instance** through the Neo4j MCP connection. Load it with the complete dataset before the workshop using `workshop-setup/populate_aircraft_db`:

```bash
cd workshop-setup/populate_aircraft_db
uv sync
uv run populate-aircraft-db setup
uv run populate-aircraft-db verify
```

Point that tool's `.env` at the reference instance, not at a participant instance. Using a shared reference instance means every participant gets the full graph in Lab 4 regardless of how far they got in Lab 2.

### B. Neo4j MCP Server + UC Connection (Lab 4)

Lab 4 Part B needs a Unity Catalog HTTP connection named `neo4j_agentcore_mcp` that points at a Neo4j MCP server backed by the reference Aura instance. Participants only verify and use the connection. They never create it.

**Step B1: Deploy the Neo4j MCP server**

The MCP server deployment tooling is **not in this repo**. `workshop-setup/neo4j_mcp_connection/` contains only `mcp-set-flag.ipynb` and a README. Earlier versions of this guide told the admin to run `aws-starter neo4j-agentcore-mcp-server` from that directory. There is no such directory and no such script here.

Deploy the server from the separate `neo4j-agentcore-mcp-server` project, which runs the MCP server behind an AWS AgentCore Gateway with Cognito M2M auth. Its `./deploy.sh credentials` step writes `.mcp-credentials.json` with the values the connection needs:

| `.mcp-credentials.json` key | Used for |
|------------------------------|----------|
| `gateway_url` | Split into **Host** and **Base path** |
| `client_id` | Client ID |
| `client_secret` | Client secret |
| `scope` | OAuth scope |
| `token_url` | Token endpoint |

Point the server's Neo4j connection settings at the reference Aura instance from Step A.

If you do not have access to that deployment project, ask the workshop owner for an existing gateway URL and credential set. The connection can be created against a gateway someone else already runs.

**Step B2: Create the UC HTTP connection**

Follow `workshop-setup/MCP-MANUAL-SETUP.md`. It is the authoritative walkthrough and covers the UI wizard field by field. The parts that matter for Vocareum:

- **Connection name:** `neo4j_agentcore_mcp`. Lab 4 Part B, the published Lab 4 page, and `MCP-MANUAL-SETUP.md` all use exactly this name.
- **Connection type:** `HTTP`
- **Auth type:** **OAuth Machine to Machine**
- **Host:** scheme and domain from `gateway_url`, with no path, starting with `https://`
- **Base path:** `/mcp`. Leaving this at the default `/` produces a URL ending in `:443/` and every call fails.

Optionally store the credentials in a Databricks secret scope first and reference them from SQL instead of typing them into the wizard:

```bash
export DATABRICKS_HOST="https://dbc-xxxxx.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."

databricks secrets create-scope mcp-neo4j-secrets

echo -n "https://<gateway-host>.gateway.bedrock-agentcore.<region>.amazonaws.com" \
  | databricks secrets put-secret mcp-neo4j-secrets gateway_host
echo -n "<client_id>"     | databricks secrets put-secret mcp-neo4j-secrets client_id
echo -n "<client_secret>" | databricks secrets put-secret mcp-neo4j-secrets client_secret
echo -n "https://<cognito-domain>/oauth2/token" \
  | databricks secrets put-secret mcp-neo4j-secrets token_endpoint
echo -n "<scope>"         | databricks secrets put-secret mcp-neo4j-secrets oauth_scope
```

```sql
CREATE CONNECTION IF NOT EXISTS neo4j_agentcore_mcp TYPE HTTP
OPTIONS (
  host secret('mcp-neo4j-secrets', 'gateway_host'),
  base_path '/mcp',
  client_id secret('mcp-neo4j-secrets', 'client_id'),
  client_secret secret('mcp-neo4j-secrets', 'client_secret'),
  oauth_scope secret('mcp-neo4j-secrets', 'oauth_scope'),
  token_endpoint secret('mcp-neo4j-secrets', 'token_endpoint')
);
```

**Step B3: Enable the MCP flag**

1. Go to **Catalog** > **External Data** > **Connections**
2. Find `neo4j_agentcore_mcp` and click **Edit**
3. Check **Is MCP connection**
4. Click **Update**

Some workspaces do not surface that checkbox. If yours does not, run `workshop-setup/neo4j_mcp_connection/mcp-set-flag.ipynb` on a cluster. Set `CONNECTION_NAME` to `neo4j_agentcore_mcp` and paste the client secret into `CLIENT_SECRET`. The notebook re-sends the existing options with `is_mcp_connection: "true"`.

**Step B4: Grant access to all participants**

```sql
GRANT USE CONNECTION ON CONNECTION neo4j_agentcore_mcp TO `account users`;
```

Without this grant, participants hit a permission error in Lab 4 Part B when the supervisor calls the MCP subagent.

**Step B5: Verify the connection**

```sql
SELECT http_request(
  conn => 'neo4j_agentcore_mcp',
  method => 'POST',
  path => '',
  headers => map('Content-Type', 'application/json'),
  json => '{"jsonrpc":"2.0","method":"tools/list","id":1}'
) AS response;
```

The response should list two tools. AgentCore prefixes them, so expect `neo4j-mcp-server-target___get_neo4j_schema` and `neo4j-mcp-server-target___read_neo4j_cypher`.

### C. Genie Space (Lab 4)

**Participants create their own Genie space.** Lab 4 Part A walks each participant through creating a space named `Aircraft Sensor Analyst [YOUR_INITIALS]` over `databricks-neo4j-workshop.aircraft`, using the tables `sensor_readings`, `sensors`, `systems`, and `aircraft`. Part B then attaches that space to the participant's own supervisor agent as the `sensor_data_agent` subagent. Do not pre-create a single shared space. Each participant needs their own so they can edit its instructions.

The admin's job is to make sure participants can succeed at Part A:

1. Confirm the four gold tables exist and are readable:

   ```sql
   SELECT * FROM `databricks-neo4j-workshop`.aircraft.aircraft LIMIT 5;
   ```

2. Confirm the table and column comments were applied by workspace init. Genie relies on them.
3. Confirm a **Serverless SQL Warehouse** is running and visible to participants. Part A step 2.3 asks them to select one as the Genie default warehouse.
4. Confirm the workspace has Agent Bricks and Genie enabled.

## Step 5: Test

1. Click **Student View** in Vocareum to launch a test lab
2. Verify workspace init completes with no errors in the logs
3. Verify the volume has 27 files, including the 5 `MAINTENANCE_*.md` manuals:
   `ls /Volumes/databricks-neo4j-workshop/aircraft/raw_data/`
4. Verify the DLT pipeline `Fleet Digital Twin ETL` reached COMPLETED
5. Verify the 8 gold tables exist in `databricks-neo4j-workshop.aircraft` and that bronze and silver landed in `aircraft_pipeline`
6. Verify row counts. This should return 155,520:

   ```sql
   SELECT COUNT(*) FROM `databricks-neo4j-workshop`.aircraft.sensor_readings;
   ```

7. Verify `systems` and `sensors` expose `type` and `name` columns
8. Verify the notebooks load in the user's home folder, 5 files across two folders
9. Verify the cluster starts on DBR 17.3 ML and that `import neo4j`, `import neo4j_graphrag`, and `import langgraph` all succeed
10. Run Lab 2 notebook 01 end to end against a test Aura instance
11. Run Lab 3 notebook 01, which confirms the maintenance manual is readable from the volume
12. Run the MCP `tools/list` check from Step B5

## Step 6: Enroll Participants

For direct enrollment (LTI disabled):
- See "Running Workshops on Vocareum" in the Vocareum docs
- Share the enrollment link with participants

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `self.w` is None | `VOC_DB_WORKSPACE_URL` or `VOC_DB_API_TOKEN` not set | Vocareum provisioning failed. Check the workspace exists |
| `delta_sharing_recipient_token_lifetime_in_seconds` = 0 | Databricks no longer allows infinite token lifetime | Patch the dbacademy.py line to use `86400` |
| `Root storage credential does not exist` | Metastore exists but the credential was deleted | Delete the metastore and re-run init |
| `Permission assignment APIs not available` | Workspace not using identity federation | Use workspace-level SCIM instead of account-level |
| `WARNING: No CSV files found` in init logs | The zip was not uploaded, or was uploaded under a different name | Confirm `aircraft_digital_twin_data.zip` or `.dat` is in `/voc/private/courseware/` |
| Data upload fails | Volume does not exist yet | Ensure the catalog, schema, and volume SQL runs before the upload step |
| Lab 3 notebook 01 fails reading the manual | The manuals were not staged to the volume | Re-run `upload_data_files`. An old zip with CSVs only causes this |
| `ImportError` in Lab 2 or Lab 3 | Cluster libraries missing | Check the `libraries` list in `neo4j-databricks-workshop.cfg` has the Maven connector and all 10 PyPI packages, then restart the cluster |
| `ClassNotFoundException` on `org.neo4j.spark` | Scala version mismatch | The connector must be the `_2.13` build to match DBR 17.3 on Scala 2.13 |
| Genie generates SQL against `system_type` or `sensor_type` | Stale column names | Gold `systems` and `sensors` use `type` and `name`. Reload the Part A instructions text |
| MCP connection not listed as an MCP server | The MCP flag is false | Complete Step B3, or run `mcp-set-flag.ipynb` if the checkbox is missing |
| MCP calls fail with a `:443/` URL | Base path defaulted to `/` | Edit the connection and set **Base path** to `/mcp` |
| Participant sees permission denied on the MCP subagent | Missing grant | Run the `GRANT USE CONNECTION` from Step B4 |

## Workspace Details

| Resource | Details |
|----------|---------|
| Workspace | Vocareum-provisioned (auto) |
| Catalog | `databricks-neo4j-workshop` |
| Volume | `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/` |
| Volume contents | 22 CSVs + 5 maintenance manuals |
| Gold schema | `databricks-neo4j-workshop.aircraft` |
| Bronze/silver schema | `databricks-neo4j-workshop.aircraft_pipeline` |
| Gold tables | `aircraft`, `systems`, `sensors`, `sensor_readings`, `flights`, `maintenance_events`, `fleet_readiness`, `sensor_health` |
| Genie tables (Lab 4) | `aircraft`, `systems`, `sensors`, `sensor_readings` |
| DLT pipeline | `Fleet Digital Twin ETL`, serverless, triggered, full refresh on init |
| Cluster | Single-node `m5.large`, DBR `17.3.x-cpu-ml-scala2.13`, 120-minute auto-termination |
| Spark Connector | `org.neo4j:neo4j-connector-apache-spark_2.13:5.4.3_for_spark_3` |
| Cluster PyPI libraries | 10 packages, see the User Setup section |
| MCP connection | `neo4j_agentcore_mcp`, HTTP, OAuth M2M, base path `/mcp` |
| Entry notebook | `Lab_2_Databricks_ETL_Neo4j/01_aircraft_etl_to_neo4j` |
| Session Length | 4 hours |
