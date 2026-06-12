# Vocareum Setup Guide — Neo4j + Databricks Workshop

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
| `courseware/neo4j-databricks-workshop.cfg` | `/voc/private/courseware/` | Course config |
| `courseware/neo4j-databricks-workshop.dat` | `/voc/private/courseware/` | Lab notebooks (`.dat` prevents Vocareum auto-extract) |
| `courseware/aircraft_digital_twin_data.zip` | `/voc/private/courseware/` | CSV data, 3.4MB (init script also accepts `.dat` or a pre-extracted folder) |
| `scripts/workspace_init.sh` | `/voc/scripts/` | Shell wrapper |
| `scripts/user_setup.sh` | `/voc/scripts/` | Shell wrapper |
| `scripts/lab_setup.sh` | `/voc/scripts/` | Shell wrapper |
| `scripts/lab_end.sh` | `/voc/scripts/` | Shell wrapper |
| `scripts/python/workspace_init.py` | `/voc/scripts/python/` | Workspace init logic |
| `scripts/python/user_setup.py` | `/voc/scripts/python/` | Per-user setup |
| `scripts/python/lab_setup.py` | `/voc/scripts/python/` | Lab resume |
| `scripts/python/lab_end.py` | `/voc/scripts/python/` | Resource cleanup |
| `scripts/python/workshop_data_setup.py` | `/voc/scripts/python/` | DLT pipeline setup |
| `courseware/dlt_fleet_etl.py` | `/voc/private/courseware/` | DLT notebook (bronze→silver→gold) |
| `docs/README.md` | `/voc/docs/` | Iframe instructions |

**Note:** Upload `scripts/python/dbacademy.py` to `/voc/scripts/python/`. This is a patched version (fixes `delta_sharing_recipient_token_lifetime` and `self.w` None guard). If the template already has one, **overwrite it** with ours.

## What Happens Automatically

### On Workspace Init (`workspace_init.py`)
1. **dbacademy** creates metastore, default catalog (`databricks-neo4j-workshop`), shared warehouse
2. **workshop_data_setup.py** then:
   - Creates catalog, schemas, and UC volume
   - Uploads 22 CSV files to `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/`
   - Uploads DLT notebook to `/Shared/workshop/dlt_fleet_etl`
   - Creates and runs a **serverless DLT pipeline** (`Fleet Digital Twin ETL`):
     - **Bronze**: Raw CSV ingestion (10 node tables + 12 relationship tables)
     - **Silver**: Cleaned, typed, validated entities with DQ expectations
     - **Gold**: Analytics-ready tables enriched with joins and aggregations
   - Gold tables: `aircraft`, `systems`, `sensors`, `sensor_readings`, `flights`, `maintenance_events`, `fleet_readiness`, `sensor_health`
   - Adds Genie-friendly column/table comments
   - Grants SELECT + USE to all users

### On User Setup (`user_setup.py`)
- Creates per-user cluster (i3.xlarge, DBR 16.4, Neo4j Spark Connector)
- Creates per-user schema for scratch work
- Creates working volume in ops schema
- Imports lab notebooks to user's home folder
- Returns redirect URL to entry notebook

### On Lab Resume (`lab_setup.py`)
- Starts user's cluster/warehouse if stopped
- Returns redirect URL

### On Lab End (`lab_end.py`)
- Terminates user's cluster
- Stops user's warehouse
- Drops user catalog/schema
- Cleans up metadata

## Manual Pre-Workshop Steps

### A. Neo4j Aura
Each participant creates their own Neo4j Aura instance during Lab 1. No pre-provisioning needed.

### B. Neo4j MCP Server + UC Connection (Lab 4)

The multi-agent supervisor in Lab 4 needs a Neo4j MCP server and a Unity Catalog HTTP connection. Since each participant creates their own Neo4j Aura instance (Lab 1), the MCP server must point to a **shared** Aura instance or be configured per-participant.

#### Option 1: Shared Neo4j Aura (Recommended for workshops)

Use a single pre-provisioned Aura instance that the instructor loads with data before the workshop.

**Step B1: Deploy the MCP server to AWS AgentCore**
```bash
cd workshop-setup/neo4j_mcp_connection/

# Deploy using aws-starter (see https://github.com/neo4j-partners/aws-starter)
aws-starter neo4j-agentcore-mcp-server

# This generates .mcp-credentials.json with OAuth2 credentials
```

**Step B2: Store OAuth2 secrets in the Vocareum workspace**

Values come from `neo4j-agentcore-mcp-server/.mcp-credentials.json`.
After workspace init completes and you have workspace access:

```bash
# Point at the Vocareum-provisioned workspace
export DATABRICKS_HOST="https://dbc-xxxxx.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."

# Create the secret scope
databricks secrets create-scope mcp-neo4j-secrets

# Store each credential (replace placeholders with values from .mcp-credentials.json)
echo -n "https://<gateway-host>.gateway.bedrock-agentcore.<region>.amazonaws.com" \
  | databricks secrets put-secret mcp-neo4j-secrets gateway_host
echo -n "<client_id>"    | databricks secrets put-secret mcp-neo4j-secrets client_id
echo -n "<client_secret>" | databricks secrets put-secret mcp-neo4j-secrets client_secret
echo -n "https://<cognito-domain>/oauth2/token" \
  | databricks secrets put-secret mcp-neo4j-secrets token_endpoint
echo -n "<scope>"        | databricks secrets put-secret mcp-neo4j-secrets oauth_scope
```

This creates a secret scope `mcp-neo4j-secrets` with keys: `gateway_host`, `client_id`, `client_secret`, `token_endpoint`, `oauth_scope`.

**Step B3: Create the UC HTTP connection**

Run this SQL in the workspace (via a notebook or SQL editor):
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

**Step B4: Enable MCP flag on the connection**

This step must be done in the UI:
1. Go to **Catalog** > **External Data** > **Connections**
2. Find `neo4j_agentcore_mcp` and click **Edit**
3. Check **Is MCP connection**
4. Click **Update**

**Step B5: Grant access to all users**
```sql
GRANT USE CONNECTION ON CONNECTION neo4j_agentcore_mcp TO `account users`;
```

#### Option 2: Per-participant MCP (Advanced)

If each participant needs their own MCP connection to their own Aura instance, they would follow `MCP-MANUAL-SETUP.md` themselves during Lab 4. This requires:
- Each participant deploys their own MCP server (not practical in a timed workshop)
- OR a shared MCP server that accepts a Neo4j URI as a parameter (not supported by the standard Neo4j MCP server)

For timed workshops, **Option 1 is strongly recommended**.

#### Verifying the MCP Connection

Test with this SQL after setup:
```sql
SELECT http_request(
  conn => 'neo4j_agentcore_mcp',
  method => 'POST',
  path => '',
  headers => map('Content-Type', 'application/json'),
  json => '{"jsonrpc":"2.0","method":"tools/list","id":1}'
) AS response;
```

### C. Genie Space (Lab 4)
Create a Genie Space pointed at `databricks-neo4j-workshop.aircraft` tables for the Genie Agent. This is a UI-only step done in the workspace after init.

1. Go to **Genie** in the workspace sidebar
2. Click **New** to create a Genie Space
3. Name: `Aircraft Fleet Analytics`
4. Add tables: `databricks-neo4j-workshop.aircraft.aircraft`, `systems`, `sensors`, `sensor_readings`
5. The tables already have Genie-friendly comments from workspace init
6. Copy the Genie Space ID (from the URL) — it's needed for the multi-agent supervisor config

## Step 5: Test

1. Click **Student View** in Vocareum to launch a test lab
2. Verify workspace initializes (check logs for errors)
3. Verify notebooks load in the workspace
4. Verify cluster starts with Neo4j Spark Connector
5. Verify Delta tables exist: `SELECT * FROM databricks-neo4j-workshop.aircraft.aircraft`
6. Run through Lab 2 notebook 1 end-to-end

## Step 6: Enroll Participants

For direct enrollment (LTI disabled):
- See "Running Workshops on Vocareum" in the Vocareum docs
- Share the enrollment link with participants

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `self.w` is None | `VOC_DB_WORKSPACE_URL` or `VOC_DB_API_TOKEN` not set | Vocareum provisioning failed — check workspace exists |
| `delta_sharing_recipient_token_lifetime_in_seconds` = 0 | Databricks no longer allows infinite token lifetime | Patch dbacademy.py line to use `86400` |
| `Root storage credential does not exist` | Metastore exists but credential was deleted | Delete metastore and re-run init |
| `Permission assignment APIs not available` | Workspace not using identity federation | Use workspace-level SCIM instead of account-level |
| CSV upload fails | Volume doesn't exist yet | Ensure catalog/schema/volume creation SQL runs first |

## Workspace Details

| Resource | Details |
|----------|---------|
| Workspace | Vocareum-provisioned (auto) |
| Catalog | `databricks-neo4j-workshop` |
| Volume | `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/` |
| Lakehouse Schema | `databricks-neo4j-workshop.aircraft` |
| Tables | `aircraft`, `systems`, `sensors`, `sensor_readings` |
| Cluster | Single-node i3.xlarge, DBR 16.4 |
| Spark Connector | `org.neo4j:neo4j-connector-apache-spark_2.12:5.4.3_for_spark_3` |
| Session Length | 4 hours |
