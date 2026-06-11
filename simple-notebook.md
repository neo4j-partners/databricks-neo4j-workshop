# Plan: A Simple Workshop Setup Notebook

## Overview

This workshop teaches participants to build production-ready AI agents that combine a Neo4j graph database with the Databricks Lakehouse. The dataset is an aircraft digital twin: Neo4j holds the relationship-rich data such as aircraft topology, flights, and maintenance events, while Databricks Delta tables hold the high-volume sensor telemetry. The labs build up to a Supervisor Agent that routes questions to a Genie space for SQL analytics and to a Neo4j MCP agent for graph queries.

Today the Databricks side of the setup runs through a local Python CLI in `workshop-setup/auto_scripts`. That tool requires a laptop with `uv`, a `.env` file, and Databricks SDK authentication, which makes it admin-only and fragile in a classroom. The goal is one self-contained Databricks notebook that anyone can import and run top to bottom: an admin provisioning a shared workspace, or a participant self-serving in their own workspace or Free Edition account.

The notebook will provision everything the labs need on the Databricks side: a classic compute cluster with the Neo4j Spark Connector and Python libraries, a Unity Catalog catalog, schemas, and volume, the workshop data downloaded from GitHub into the volume, and the four Delta lakehouse tables with Genie-friendly comments. Neo4j-side setup stays separate and is listed under "Other setup steps" below.

The notebook will be created in `workshop-setup/`, as `workshop-setup/notebooks/00_workshop_setup.ipynb`, so it sits with the rest of the setup tooling and can be added to the `sync` upload list.

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
  - Maven: `org.neo4j:neo4j-connector-apache-spark_2.13:5.4.3_for_spark_3`.
  - PyPI: `neo4j==6.2.0`, `databricks-agents>=1.11.0`, `langgraph==1.2.4`, `langchain-openai==1.3.0`, `pydantic==2.13.4`, `langchain-core>=1.4.6`, `databricks-langchain>=0.20.0`, `dspy>=3.2.1`, `neo4j-graphrag>=1.17.0`, `beautifulsoup4>=4.15.0`, `sentence_transformers`.
- An optional code cell that does the same thing with the Databricks SDK for admins who prefer automation: find or create the cluster by name, wait for it to reach RUNNING, install the libraries, and wait for them to report INSTALLED. Port this from `workshop-setup/auto_scripts/src/databricks_setup/cluster.py` (`get_or_create_cluster`, `wait_for_cluster_running`) and `libraries.py` (`ensure_libraries_installed`, `wait_for_libraries`). Mark the cell clearly as optional so participants without cluster-create permission skip it.

### Cell 3: Catalog and schema setup (markdown)

- Markdown documenting the Unity Catalog objects the workshop needs, with the default names matching `config.py::VolumeConfig`. One schema holds both the volume and the Delta tables, set as three constants in the notebook:
  - `CATALOG`: `databricks-neo4j-workshop`
  - `SCHEMA`: `aircraft`
  - `VOLUME`: `raw_data`
- Participants in their own workspace use the defaults; participants on a shared workspace prefix the catalog with their username; admins enter the shared catalog name once.
- Note that catalog creation needs metastore privileges; if it fails, use a catalog an admin created for you.

### Cell 4: Download the data from GitHub (code)

- The dataset is committed directly in the repo: `workshop-setup/aircraft_digital_twin_data/` holds the 22 CSVs (generated at a 4-hour reading interval, so `nodes_readings.csv` is ~11 MB and the whole directory ~13 MB) plus the 5 maintenance manuals Lab 3 needs. No release asset or zip is required.
- The cell mirrors the `data_loader.py` pattern from the `graph-on-databricks/aircraft-graphrag` project, which reads raw files straight from the public repo:
  - Base URL, pinned to a release tag so the workshop data cannot change mid-class: `https://raw.githubusercontent.com/neo4j-partners/databricks-neo4j-workshop/v1.2.0/workshop-setup/aircraft_digital_twin_data`
  - One-time admin step: create the `v1.2.0` tag on a commit that includes the regenerated `aircraft_digital_twin_data/` and push it. (The earlier `v1.0.0` and `v1.1.0` tags predate this 36-aircraft dataset.)
  - A hardcoded list of the 27 filenames; for each, fetch `f"{base}/{name}"` with `urllib.request.urlopen` and write the bytes to `/Volumes/<catalog>/<volume_schema>/<volume_name>/<name>`.
  - Skip files that already exist in the volume so re-runs are cheap.
- Finish with a file listing of the volume so participants confirm all 27 files landed.

### Cell 5: Lakehouse setup (SQL)

- Create the four Delta tables from the volume CSVs, reusing the DDL from `workshop-setup/auto_scripts/src/databricks_setup/lakehouse_tables.py::get_table_creation_sql`:
  - `aircraft`, `systems`, `sensors`: `CREATE TABLE IF NOT EXISTS ... AS SELECT * FROM read_files('<volume>/nodes_<table>.csv', format => 'csv', header => 'true', inferSchema => 'true')` with `TBLPROPERTIES ('delta.columnMapping.mode' = 'name')`. Each table reads its specific file (`nodes_aircraft.csv`, `nodes_systems.csv`, `nodes_sensors.csv`), never a glob, since the volume also holds the other 18 `nodes_*`/`rels_*` CSVs.
  - `sensor_readings`: same pattern but `PARTITIONED BY (sensor_id)` and selecting `reading_id`, `sensor_id`, `to_timestamp(ts) as timestamp`, `CAST(value AS DOUBLE) as value`.
- Apply the Genie table and column comments from `lakehouse_tables.py::get_comment_sql` so Lab 4's Genie space understands the model. There are 4 table comments and 15 column comments.
- End with the row-count verification query from `get_verification_sql`, a `UNION ALL` of `COUNT(*)` per table. Expected counts for the committed dataset: aircraft 100, systems 400, sensors 800, sensor_readings 432,000.

## Other setup steps not covered by this notebook

- **SQL warehouse**: the labs and Genie need a running warehouse. Free Edition and most workspaces ship with a Starter Warehouse; the notebook should only check it exists, not create one.
- **Neo4j Aura instance**: participants create a free Aura instance in Lab 1 and record the URI, username, and password. Store these in widgets or Databricks secrets for the Lab 2 and Lab 3 notebooks.
- **Neo4j data load**: the graph side is populated either by the Lab 2 ETL notebooks from the volume, or by the admin CLI `populate_aircraft_db` for the GraphRAG enrichment used in Lab 3.
- **Lab notebooks in the workspace**: today `databricks-setup sync` uploads the Lab 2, Lab 3, and MCP notebooks to `/Shared/databricks-neo4j-workshop`. Participants who clone the repo via Repos do not need this; admins provisioning a shared workspace still do.
- **Unity Catalog grants**: on a shared catalog, an admin must grant participants `USE CATALOG`, `USE SCHEMA`, `READ VOLUME`, and `SELECT` on the lakehouse tables. This stays an admin step outside the notebook.
- **Lab 4 components**: the Genie space over the lakehouse schema, the Unity Catalog HTTP connection to the Neo4j MCP server (`workshop-setup/neo4j_mcp_connection/`), and the Supervisor Agent in Agent Bricks are created in Lab 4 itself, not in setup.
- **Verification**: `verify_labs` checks the Neo4j side after Lab 2; the notebook's own row-count query covers the Databricks side.
