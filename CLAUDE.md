# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


## Response style

- **Condensed:** No preamble, no throat clearing. Only what is necessary.
- **Bullets:** Use `**term:** description` form.
- **Small words, short sentences, short paragraphs.** If a big word is unavoidable, define it right after.
- **Report shape:** what you did, whether it worked, what to do now.
- **Decisions:** 2 options max, the context needed to pick fast, and which one you would take.
- **Exactness:** Keep paths and commands verbatim.
- 
## Project Overview

A hands-on workshop teaching production-ready AI agents combining **Neo4j graph databases** with **Databricks AI/ML**. Demonstrates a dual-database architecture for aircraft digital twins where Neo4j handles relationship-rich data (topology, maintenance, flights) and Databricks Lakehouse handles high-volume time-series sensor telemetry.

The workshop builds toward a **LangGraph supervisor agent** in Lab 5 that routes questions across three tools: a Genie space for sensor analytics in SQL, Cypher over the participant's own Aura instance, and GraphRAG retrieval over maintenance manuals. Lab 6 then gives that agent memory in Neo4j. Lab 4 Part B is an instructor demo, not a participant exercise: the instructor builds a no-code Supervisor Agent in Databricks Agent Bricks over Neo4j MCP against their own demo instance, and participants watch.

## Build & Run Commands

All Python tools use `uv` for package management and `hatchling` as build backend. Python 3.11+ required.

### populate_aircraft_db (Neo4j data loading CLI)
```bash
cd workshop-setup/populate_aircraft_db
uv sync                                     # embeddings work out of the box
uv run populate-aircraft-db setup           # Load CSV data + enrich (chunking, embeddings, entity extraction)
uv run populate-aircraft-db setup --skip-extraction   # same, minus the extractor LLM. No OpenAI or Anthropic key
uv run populate-aircraft-db verify         # Print node/relationship counts
uv run populate-aircraft-db clean          # Delete all data
uv run populate-aircraft-db samples        # Run showcase Cypher queries
```

`--extra anthropic` is the one remaining extra, required when
`LLM_PROVIDER=anthropic`. Embeddings have no extra and no provider setting: they
always call the `databricks-bge-large-en` serving endpoint, whose client
`mlflow-skinny` is a base dependency. That makes Databricks credentials a
prerequisite for every `setup` and `enrich`, including `--skip-extraction`. Set
`DATABRICKS_CONFIG_PROFILE` or `DATABRICKS_HOST`/`DATABRICKS_TOKEN` in `.env`.

### Databricks provisioning
`lab/workshop.py` is the one definition of this course's Databricks objects: the
catalog, the four schemas, the volume, the courseware, the `Fleet Digital Twin
ETL` pipeline and the comments a Genie space reads. Vocareum's
`workspace_init.sh` calls it, and so does anything else that needs those names.
```bash
uv run python lab/workshop.py provision   # or infrastructure | upload-data | pipeline | genie
```

### Admin scripts (non-Vocareum workspaces)
The two jobs `workshop.py` and `voclab.py` do not cover. Both read every object
name from `lab/workshop.py`; neither defines anything.
```bash
uv run python workshop-setup/auto_scripts/sync_notebooks.py   # lab notebooks -> /Shared
uv run python workshop-setup/auto_scripts/teardown.py --yes   # delete the catalog and all of it
```

### verify (Neo4j verification CLIs)
One package, `verify-gds`, exposing three commands. Each connects to Aura and
replays a lab's queries against the graph.
```bash
cd workshop-setup/verify
uv sync
uv run verify-lab2                         # Lab 2 verification queries
uv run verify-data-exploring               # Data exploration queries
uv run verify-gds                          # GDS queries
uv run verify-gds --skip-nb04              # Skip feature computation
```

## Architecture

### Two Independent CLI Tools
Each under `workshop-setup/` is a standalone Python package with its own `pyproject.toml`, `.env`, and Typer CLI:

- **`populate_aircraft_db/`** — Loads aircraft CSV data into Neo4j Aura, runs GraphRAG enrichment (doc chunking, embeddings via BGE-large, entity extraction via SimpleKGPipeline)
- **`verify/`**: Verifies Neo4j data loaded correctly. Distributed as `verify-gds`, with one command per lab: `verify-lab2`, `verify-data-exploring`, `verify-gds`

`workshop-setup/auto_scripts/` is not one of them. It is two plain scripts with no
package and no dependencies of its own, run from the repository root's
environment. See `workshop-setup/auto_scripts/README.md`.

### Dual-Database Strategy
- **Neo4j**: `(Aircraft)-[:HAS_SYSTEM]->(System)-[:HAS_COMPONENT]->(Component)`, plus Sensors, Flights, Delays, MaintenanceEvents
- **Databricks**: Delta tables for `sensor_readings` (~155K rows), `sensors`, `systems`, `aircraft`
- Aircraft/Systems/Sensors exist in **both** databases as join points

### Multi-Agent Architecture (Lab 4 Part B, instructor demo)
```
User Question → Supervisor Agent (Agent Bricks)
  ├→ Genie space → Databricks Lakehouse (natural language → SQL)
  └→ Neo4j MCP Agent → Neo4j Aura (LangGraph + MCP tools: get_neo4j_schema, read_neo4j_cypher)
```

The Neo4j MCP connection uses OAuth2 M2M auth via a Unity Catalog HTTP connection to an external MCP server. It lives only in the instructor's demo workspace, and participants never create or use one. Instructor preparation: `workshop-setup/neo4j_mcp_connection/` and `MCP-MANUAL-SETUP.md`.

### Lab Progression
Lab 1 (Neo4j Aura setup + Cypher intro) → Lab 2 (ETL via Spark Connector notebooks) → Lab 3 (GraphRAG semantic search over maintenance manuals) → Lab 4 Part A (Genie space over lakehouse telemetry, the participant path) with Part B (Neo4j MCP + Agent Bricks Supervisor Agent) shown alongside it as an instructor demo → Lab 5 (LangGraph agent over Genie, the participant's own Aura instance, and the Lab 3 retrievers, deployed to Model Serving) → Lab 6 (Neo4j agent memory)

Labs 5 and 6 are both on disk:

- `Lab_5_LangGraph_Agent/` holds `01_langgraph_agent.ipynb`, `tools.py`, `agent.py` and `README.md`. `tools.py` builds the three nodes and carries the supervisor prompt. `agent.py` wraps the same graph as an MLflow `ResponsesAgent` for Model Serving, reading its credentials from environment variables rather than `dbutils`
- `Lab_6_Agent_Memory/` holds `01_agent_memory.ipynb`, `02_instructor_demos.ipynb`, `memory.py` and `README.md`. It adds a `recall` node before the supervisor and a `remember` node after it, leaving the three tools untouched, and redeploys the same Model Serving endpoint Lab 5 creates rather than a second one. `memory.py` imports from both `Lab_3_Semantic_Search/data_utils.py` and `Lab_5_LangGraph_Agent/tools.py`, so the three lab folders have to stay siblings

`expand.md` is the plan those labs were built from. It is a record of intent, not
a description of what shipped, so read the labs' own files first.

## Configuration

Each tool reads from `.env` files (see `.env.example` in each directory). Key variables:
- **Neo4j**: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- **LLM**: `LLM_PROVIDER` (openai/anthropic), `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- **Embeddings**: no provider setting. Always the `databricks-bge-large-en` serving endpoint at 1024 dimensions, reached with the `DATABRICKS_*` credentials below. `DATABRICKS_EMBEDDING_MODEL` renames the endpoint and is the only knob
- **Databricks**: `DATABRICKS_PROFILE`, `DATABRICKS_ACCOUNT_ID`, `CATALOG_NAME`

All config uses Pydantic `BaseSettings` with `SecretStr` for passwords.

## Code Conventions

- **Typer** for all CLIs with **Rich** for colored output/tables
- Batch processing with `BATCH_SIZE=1000` for Neo4j data loading
- Context managers for Neo4j driver lifecycle
- Full type hints on public signatures
- Ruff linting with rules: E, W, F, I, B, C4, UP, SIM
- `lab/workshop.py` is standard library only, against Python 3.9: it runs on the Vocareum host, where no `pip install` belongs on a hook's critical path. `workshop-setup/auto_scripts/` follows the same rule so it can import it

## Key Reference Files

- `workshop-setup/README.md` — Main admin setup guide with troubleshooting
- `workshop-setup/populate_aircraft_db/DATA_GENERATOR.md` — Data generator guide and complete schema reference (all 23 CSVs, dual-DB strategy, query patterns)
- `workshop-setup/auto_scripts/README.md` — the two admin scripts, and what took over every job the retired `databricks-setup` CLI did
