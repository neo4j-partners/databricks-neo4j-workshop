# Plan: A Simple Workshop Setup Notebook

## Overview

This workshop teaches participants to build production-ready AI agents that combine a Neo4j graph database with the Databricks Lakehouse. The dataset is an aircraft digital twin: Neo4j holds the relationship-rich data such as aircraft topology, flights, and maintenance events, while Databricks Delta tables hold the high-volume sensor telemetry. The labs build up to a Supervisor Agent that routes questions to a Genie space for SQL analytics and to a Neo4j MCP agent for graph queries.

Today the Databricks side of the setup runs through a local Python CLI in `lab_setup/auto_scripts`. That tool requires a laptop with `uv`, a `.env` file, and Databricks SDK authentication, which makes it admin-only and fragile in a classroom. The goal is one self-contained Databricks notebook that anyone can import and run top to bottom: an admin provisioning a shared workspace, or a participant self-serving in their own workspace or Free Edition account.

The notebook will provision everything the labs need on the Databricks side: a classic compute cluster with the Neo4j Spark Connector and Python libraries, a Unity Catalog catalog, schemas, and volume, the workshop data downloaded from GitHub into the volume, and the four Delta lakehouse tables with Genie-friendly comments. Neo4j-side setup stays separate and is listed under "Other setup steps" below.

## Notebook structure, cell by cell

### Cell 1: Workshop overview (markdown)

- One short paragraph on the dual-database architecture: Neo4j for relationships, Databricks for sensor telemetry, with Aircraft, Systems, and Sensors existing in both as join points.
- One line per lab so participants see where setup fits: Lab 1 Neo4j Aura and Cypher, Lab 2 ETL with the Spark Connector, Lab 3 GraphRAG semantic search, Lab 4 Genie space and Supervisor Agent, Lab 5 Aura Agents.
- A "before you run this" checklist: workspace access, permission to create a catalog or the name of a shared catalog assigned by the instructor, a running SQL warehouse, and a Neo4j Aura instance with credentials for the later labs.

### Cell 2: Classic compute cluster and libraries (markdown plus optional code)

- Markdown walkthrough for creating the cluster in the UI:
  - Single-node classic compute, Dedicated (single-user) access mode.
  - Runtime `17.3.x-cpu-ml-scala2.13`, which is 17.3 LTS ML on Spark 4.0.
  - Node type `m5.large` on AWS or the equivalent 2-core, 8 GB type on Azure or GCP.
  - Auto-termination at 30 minutes.
- Markdown listing the libraries to install on the cluster:
  - Maven: `org.neo4j:neo4j-connector-apache-spark_2.13:5.3.10_for_spark_3`.
  - PyPI: `neo4j==6.0.2`, `databricks-agents>=1.2.0`, `langgraph==1.0.5`, `langchain-openai==1.1.2`, `pydantic==2.12.5`, `langchain-core>=1.2.0`, `databricks-langchain>=0.11.0`, `dspy>=3.0.4`, `neo4j-graphrag>=1.13.0`, `beautifulsoup4>=4.12.0`, `sentence_transformers`.
- An optional code cell that does the same thing with the Databricks SDK for admins who prefer automation: find or create the cluster by name, wait for it to reach RUNNING, install the libraries, and wait for them to report INSTALLED. Port this from `lab_setup/auto_scripts/src/databricks_setup/cluster.py` (`get_or_create_cluster`, `wait_for_cluster_running`) and `libraries.py` (`ensure_libraries_installed`, `wait_for_libraries`). Mark the cell clearly as optional so participants without cluster-create permission skip it.

### Cell 3: Catalog and schema setup (config plus SQL)

- A single configuration cell at the top using `dbutils.widgets` with these defaults, matching `config.py::VolumeConfig`:
  - Catalog: `databricks-neo4j-workshop`
  - Volume schema: `lab-schema`
  - Volume name: `lab-volume`
  - Lakehouse schema: `lakehouse`
- Participants in their own workspace keep the defaults; participants on a shared workspace prefix the catalog with their username; admins enter the shared catalog name once.
- SQL to create the objects, all idempotent:
  - `CREATE CATALOG IF NOT EXISTS`
  - `CREATE SCHEMA IF NOT EXISTS` for both the volume schema and the lakehouse schema
  - `CREATE VOLUME IF NOT EXISTS` for the data volume
- Note in the cell that catalog creation needs metastore privileges; if it fails, use a catalog an admin created for you.

### Cell 4: Download the data from GitHub (code)

- Data is published as a GitHub release asset because `nodes_readings.csv` in `lab_setup/aircraft_digital_twin_data_v2` is about 114 MB, over GitHub's 100 MB limit for regular repo files. A release asset allows up to 2 GB.
- The release zip contains the 22 v2 CSVs (10 node files, 12 relationship files) plus the 3 maintenance manuals (`MAINTENANCE_A320.md`, `MAINTENANCE_A321neo.md`, `MAINTENANCE_B737.md`) that Lab 3 needs. The manuals currently live in `lab_setup/aircraft_digital_twin_data`, not in v2, so the release packaging must pull them in.
- The cell mirrors the `data_loader.py` pattern from the `graph-on-databricks/aircraft-graphrag` project:
  - A `DATA_SOURCE` switch: `"github"` downloads the release zip with `urllib.request.urlopen`, `"volume"` assumes the files are already in the volume and skips the download. Re-runs are cheap.
  - Placeholder URL until the release exists: `https://github.com/<org>/databricks-neo4j-workshop/releases/download/<tag>/aircraft_digital_twin_data_v2.zip`
  - Download to local disk, extract, and copy every CSV and MD file into `/Volumes/<catalog>/<volume_schema>/<volume_name>/`.
- Finish with a file listing of the volume so participants confirm all 25 files landed.

### Cell 5: Lakehouse setup (SQL)

- Create the four Delta tables from the volume CSVs, reusing the DDL from `lab_setup/auto_scripts/src/databricks_setup/lakehouse_tables.py::get_table_creation_sql`:
  - `aircraft`, `systems`, `sensors`: `CREATE TABLE IF NOT EXISTS ... AS SELECT * FROM read_files('<volume>/nodes_*.csv', format => 'csv', header => 'true', inferSchema => 'true')` with `TBLPROPERTIES ('delta.columnMapping.mode' = 'name')`.
  - `sensor_readings`: same pattern but `PARTITIONED BY (sensor_id)` and selecting `reading_id`, `sensor_id`, `to_timestamp(ts) as timestamp`, `CAST(value AS DOUBLE) as value`.
- Apply the Genie table and column comments from `lakehouse_tables.py::get_comment_sql` so Lab 4's Genie space understands the model. There are 4 table comments and 15 column comments.
- End with the row-count verification query from `get_verification_sql`, a `UNION ALL` of `COUNT(*)` per table. The v1 counts are aircraft 20, systems 80, sensors 160, sensor_readings 345,600; the v2 dataset is roughly 5x larger for readings, so compute and document the v2 expected counts when building the notebook.

## Other setup steps not covered by this notebook

- **SQL warehouse**: the labs and Genie need a running warehouse. Free Edition and most workspaces ship with a Starter Warehouse; the notebook should only check it exists, not create one.
- **Neo4j Aura instance**: participants create a free Aura instance in Lab 1 and record the URI, username, and password. Store these in widgets or Databricks secrets for the Lab 2 and Lab 3 notebooks.
- **Neo4j data load**: the graph side is populated either by the Lab 2 ETL notebooks from the volume, or by the admin CLI `populate_aircraft_db` for the GraphRAG enrichment used in Lab 3.
- **Lab notebooks in the workspace**: today `databricks-setup sync` uploads the Lab 2, Lab 3, and MCP notebooks to `/Shared/databricks-neo4j-workshop`. Participants who clone the repo via Repos do not need this; admins provisioning a shared workspace still do.
- **Unity Catalog grants**: on a shared catalog, an admin must grant participants `USE CATALOG`, `USE SCHEMA`, `READ VOLUME`, and `SELECT` on the lakehouse tables. This stays an admin step outside the notebook.
- **Lab 4 components**: the Genie space over the lakehouse schema, the Unity Catalog HTTP connection to the Neo4j MCP server (`lab_setup/neo4j_mcp_connection/`), and the Supervisor Agent in Agent Bricks are created in Lab 4 itself, not in setup.
- **Verification**: `verify_labs` checks the Neo4j side after Lab 2; the notebook's own row-count query covers the Databricks side.

## Open items

- Publish the GitHub release with the v2 data zip, including the 3 maintenance manuals, and replace the placeholder URL.
- Compute the v2 expected row counts for the verification cell.
- Decide where the notebook lives in the repo. Suggested: `lab_setup/notebooks/00_workshop_setup.ipynb` so it sits with the rest of the setup tooling and can be added to the `sync` upload list.
