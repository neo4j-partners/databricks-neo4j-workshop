# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A hands-on workshop teaching production-ready AI agents combining **Neo4j graph databases** with **Databricks AI/ML**. Demonstrates a dual-database architecture for aircraft digital twins where Neo4j handles relationship-rich data (topology, maintenance, flights) and Databricks Lakehouse handles high-volume time-series sensor telemetry.

The workshop culminates in a **Supervisor Agent** (Databricks Agent Bricks) that routes questions to specialized agents: a Genie space (sensor analytics via SQL) and Neo4j MCP (graph relationships via Cypher).

## Build & Run Commands

All Python tools use `uv` for package management and `hatchling` as build backend. Python 3.11+ required.

### populate_aircraft_db (Neo4j data loading CLI)
```bash
cd workshop-setup/populate_aircraft_db
uv sync                                    # Install dependencies
uv run populate-aircraft-db setup           # Load CSV data + enrich (chunking, embeddings, entity extraction)
uv run populate-aircraft-db verify         # Print node/relationship counts
uv run populate-aircraft-db clean          # Delete all data
uv run populate-aircraft-db samples        # Run showcase Cypher queries
```

### databricks_setup (Admin workspace provisioning CLI)
```bash
cd workshop-setup/auto_scripts
uv sync
uv run databricks-setup setup             # Full setup (cluster, data, tables)
uv run databricks-setup cleanup            # Tear down
uv run databricks-setup sync               # Upload/sync workshop notebooks
```

### verify_labs (Neo4j verification CLI)
```bash
cd workshop-setup/verify_labs
uv sync
uv run verify-labs check                   # Connectivity test
uv run verify-labs lab2                    # All Lab 2 verification queries
uv run verify-labs lab2 --notebook 01      # Notebook 1 only
```

### Linting (auto_scripts only)
```bash
cd workshop-setup/auto_scripts
uv run ruff check .                        # Lint (rules: E, W, F, I, B, C4, UP, SIM)
uv run mypy src/                           # Type checking (strict mode)
```

## Architecture

### Three Independent CLI Tools
Each under `workshop-setup/` is a standalone Python package with its own `pyproject.toml`, `.env`, and Typer CLI:

- **`populate_aircraft_db/`** — Loads aircraft CSV data into Neo4j Aura, runs GraphRAG enrichment (doc chunking, embeddings via BGE-large, entity extraction via SimpleKGPipeline)
- **`auto_scripts/`** (databricks_setup) — Automates Databricks workspace provisioning: cluster creation, Spark Connector install, Delta table creation
- **`verify_labs/`** — Verifies Neo4j data loaded correctly in Lab 2

### Dual-Database Strategy
- **Neo4j**: `(Aircraft)-[:HAS_SYSTEM]->(System)-[:HAS_COMPONENT]->(Component)`, plus Sensors, Flights, Delays, MaintenanceEvents
- **Databricks**: Delta tables for `sensor_readings` (~155K rows), `sensors`, `systems`, `aircraft`
- Aircraft/Systems/Sensors exist in **both** databases as join points

### Multi-Agent Architecture (Lab 4)
```
User Question → Supervisor Agent (Agent Bricks)
  ├→ Genie space → Databricks Lakehouse (natural language → SQL)
  └→ Neo4j MCP Agent → Neo4j Aura (LangGraph + MCP tools: get-schema, read-cypher)
```

The MCP agent (`workshop-setup/neo4j_mcp_connection/neo4j_mcp_agent.py`) uses OAuth2 M2M auth via Unity Catalog HTTP connection to an external MCP server.

### Lab Progression
Lab 1 (Neo4j Aura setup + Cypher intro) → Lab 2 (ETL via Spark Connector notebooks) → Lab 3 (GraphRAG semantic search over maintenance manuals) → Lab 4 (compound AI agents: Genie space + Supervisor Agent)

## Configuration

Each tool reads from `.env` files (see `.env.example` in each directory). Key variables:
- **Neo4j**: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- **LLM**: `LLM_PROVIDER` (openai/anthropic/azure), `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- **Databricks**: `DATABRICKS_PROFILE`, `DATABRICKS_ACCOUNT_ID`, `CATALOG_NAME`

All config uses Pydantic `BaseSettings` with `SecretStr` for passwords.

## Code Conventions

- **Typer** for all CLIs with **Rich** for colored output/tables
- Batch processing with `BATCH_SIZE=1000` for Neo4j data loading
- Context managers for Neo4j driver lifecycle
- Full type hints; `mypy --strict` enforced in auto_scripts
- Ruff linting with rules: E, W, F, I, B, C4, UP, SIM

## Key Reference Files

- `workshop-setup/README.md` — Main admin setup guide with troubleshooting
- `workshop-setup/populate_aircraft_db/DATA_GENERATOR.md` — Data generator guide and complete schema reference (all 22 CSVs, dual-DB strategy, query patterns)
- `workshop-setup/auto_scripts/README.md` — Databricks CLI reference with all config options
