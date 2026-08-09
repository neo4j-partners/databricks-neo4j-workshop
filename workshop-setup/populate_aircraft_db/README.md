# populate-aircraft-db

Standalone CLI tool that generates the Aircraft Digital Twin dataset and loads it into a Neo4j Aura instance. The `generate` command produces the synthetic CSV dataset with correlated sensor degradation. The `setup` command handles the full loading pipeline: CSV data loading, maintenance manual chunking, BGE-large embedding generation locally via sentence-transformers, and independently configured LLM-powered entity extraction with OpenAI or Anthropic via `neo4j-graphrag`'s `SimpleKGPipeline`.

**This is manual, and nothing automates it.** The Vocareum hooks in `lab/` build the Databricks side and reach nothing outside the workspace. Neo4j runs in Aura and the labs connect out to it over Bolt, so no workspace resource hosts a database, `workspace_init.sh` has nothing to create, and `lab_end.sh` has nothing to tear down. `dbx-vocareum/docs/neo4j-aura.md` records that decision and what follows from it. Participants load their own instance during Labs 2 and 3; this tool is for the two administrator cases, the instructor's demo instance behind Lab 4 Part B and a participant who fell behind. See `workshop-setup/README.md` for when each applies.

## Quick Start

```bash
cd workshop-setup/populate_aircraft_db

# Create .env with your Neo4j credentials (see .env.example)
cp .env.example .env
# Edit .env with your credentials

# Install and run
uv sync                              # BGE embeddings + OpenAI extraction
uv sync --extra anthropic            # include Anthropic extraction support
uv run populate-aircraft-db clean
uv run populate-aircraft-db setup
```

## Commands

| Command | Description |
|---------|-------------|
| `generate` | Generate the synthetic CSV dataset (fleet topology, sensor readings with degradation, maintenance events, flights, delays, removals). No Neo4j connection needed |
| `validate-csv` | Check referential integrity of generated CSV files. No Neo4j connection needed |
| `setup` | Load CSV data into Neo4j and run GraphRAG enrichment (chunking, embeddings, entity extraction, cross-linking) in a single pass. Safe to re-run — uses MERGE for CSV data and clears enrichment data before re-enriching. |
| `samples` | Run sample queries showcasing the knowledge graph (read-only, no API keys needed) |
| `verify` | Run comprehensive graph verification: counts, embeddings, indexes, constraints, vector search, cross-links, and orphan checks (read-only) |
| `clean` | Delete all nodes and relationships |
| `enrich` | Re-run manual GraphRAG enrichment against an already-loaded operational graph |
| `load-operational` | Load only CSV operational data and relink existing enrichment. No LLM calls |
| `clean-enrichment` | Delete enrichment data (Documents, Chunks, extracted entities) while preserving the operational graph |

All loading configuration is via `.env` — no command-line flags needed. The `generate` command takes flags instead (it reads nothing from `.env`).

### Regenerating the dataset

The committed dataset in `workshop-setup/aircraft_digital_twin_data/` was produced with:

```bash
uv run populate-aircraft-db generate --seed 42 --reading-interval 4
```

`--reading-interval 4` writes one reading every 4 hours (155,520 rows, ~11MB), keeping `nodes_readings.csv` small enough to commit. See **[DATA_GENERATOR.md](DATA_GENERATOR.md)** for the full guide: all options, controlling dataset size, regenerating only the readings file with `--readings-only`, and what gets generated.

### Typical full-load sequence

```bash
uv run populate-aircraft-db clean
uv run populate-aircraft-db setup     # uses LLM_PROVIDER from .env (default: openai)
uv run populate-aircraft-db verify --strict
uv run populate-aircraft-db enrich    # re-run manual enrichment only
uv run populate-aircraft-db samples   # run sample queries to explore the graph
```

If enrichment exists but operational labels like `Aircraft`, `System`,
`Component`, and `Sensor` are missing, repair that state without rerunning LLM
extraction:

```bash
uv run populate-aircraft-db load-operational
uv run populate-aircraft-db verify --strict
```

### Verification

`verify` is read-only. It checks:

- Operational and enrichment node counts
- Relationship counts by type
- Chunk embedding presence and dimensions
- Required vector/fulltext indexes and uniqueness constraints
- A vector search smoke test against `maintenanceChunkEmbeddings`
- Cross-links from manuals and extracted entities into the operational graph
- Common orphan patterns such as readings without sensors and documents without chunks

Use `--strict` in automation to fail the command when warnings are found:

```bash
uv run populate-aircraft-db verify --strict
```

## Configuration

Settings are loaded from a `.env` file in the project root or from environment variables.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEO4J_URI` | yes | - | Connection URI (e.g. `neo4j+s://...`) |
| `NEO4J_USERNAME` | no | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | yes | - | Neo4j password |
| `DATA_DIR` | no | `../aircraft_digital_twin_data` | CSV directory for operational graph loading |
| `DOCUMENT_DIR` | no | `../aircraft_digital_twin_data` | Maintenance manual directory for enrichment (same directory; CSVs and manuals live together) |
| `LLM_PROVIDER` | no | `openai` | LLM provider for entity extraction: `openai` or `anthropic` |
| `EMBEDDING_PROVIDER` | no | `bge` | Chunk embedding provider: `bge` (local sentence-transformers, no API key), `openai`, or `databricks` |
| `BGE_EMBEDDING_MODEL` | no | `BAAI/bge-large-en-v1.5` | BGE embedding model (used when `EMBEDDING_PROVIDER=bge`) |
| `BGE_EMBEDDING_DIMENSIONS` | no | `1024` | BGE embedding dimensions — matches the Lab 3 `maintenanceChunkEmbeddings` index |
| `OPENAI_API_KEY` | for setup (openai) | - | OpenAI API key. Required for extraction when `LLM_PROVIDER=openai` and for embeddings when `EMBEDDING_PROVIDER=openai` |
| `OPENAI_EMBEDDING_MODEL` | no | `text-embedding-3-small` | OpenAI embedding model (used when `EMBEDDING_PROVIDER=openai`) |
| `OPENAI_EMBEDDING_DIMENSIONS` | no | `1536` | OpenAI embedding dimensions (used when `EMBEDDING_PROVIDER=openai`) |
| `OPENAI_EXTRACTION_MODEL` | no | `gpt-5-mini` | Chat model for entity extraction (OpenAI) |
| `OPENAI_EXTRACTION_MAX_COMPLETION_TOKENS` | no | `8000` | OpenAI extraction output budget. Keep this high for GPT-5-family structured extraction |
| `ANTHROPIC_API_KEY` | for setup (anthropic) | - | Anthropic API key |
| `ANTHROPIC_EXTRACTION_MODEL` | no | `claude-sonnet-4-6` | Chat model for entity extraction (Anthropic) |
| `ANTHROPIC_EXTRACTION_MAX_TOKENS` | no | `8000` | Anthropic extraction output budget |
| `DATABRICKS_EMBEDDING_MODEL` | no | `databricks-bge-large-en` | Serving endpoint used when `EMBEDDING_PROVIDER=databricks` |
| `DATABRICKS_EMBEDDING_DIMENSIONS` | no | `1024` | Dimensions of that endpoint. Matches the Lab 3 index |
| `DATABRICKS_CONFIG_PROFILE` | no | - | Profile in `~/.databrickscfg` to authenticate with |
| `DATABRICKS_HOST` | no | - | Workspace URL, if not using a profile |
| `DATABRICKS_TOKEN` | no | - | Personal access token, if not using a profile |
| `CHUNK_SIZE` | no | `800` | Characters per chunk (setup) |
| `CHUNK_OVERLAP` | no | `100` | Overlap between chunks (setup) |
| `ENRICH_SAMPLE_SIZE` | no | `0` | Max chunks per document during setup (`0` = no limit) |
| `SAMPLE_SIZE` | no | `10` | Rows per section in the `samples` command |

### Embeddings vs extractor LLM

Chunk embeddings default to BGE-large (`BAAI/bge-large-en-v1.5`, 1024 dimensions), run locally via sentence-transformers with no API key. This matches the `databricks-bge-large-en` embeddings and the 1024-dim `maintenanceChunkEmbeddings` vector index used in Lab 3, so embeddings are compatible across the workshop. Entity extraction is controlled separately with `LLM_PROVIDER` and always needs an OpenAI or Anthropic API key.

To use the default BGE embeddings with Anthropic entity extraction (no OpenAI key needed):

```dotenv
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_EXTRACTION_MODEL=claude-sonnet-4-6
```

To opt back in to OpenAI embeddings (1536 dimensions — incompatible with the Lab 3 index dimensions):

```dotenv
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
```

To embed through the same Databricks Foundation Model endpoint the Lab 3 notebooks call, so the vectors this loader writes and the vectors a participant writes come from one model:

```dotenv
EMBEDDING_PROVIDER=databricks
DATABRICKS_CONFIG_PROFILE=DEFAULT
```

Install the extra it needs with `uv sync --extra databricks`. Inside a Databricks notebook, leave the host, token, and profile unset: authentication is already in the environment.

If `LLM_PROVIDER=openai` and you see repeated `LLM response has improper format` messages, keep `OPENAI_EXTRACTION_MAX_COMPLETION_TOKENS` at `8000` or higher. GPT-5-family models can spend part of that budget on structured-output reasoning before emitting the JSON graph.

### Loading without an extractor LLM

`setup` and `enrich` both accept `--skip-extraction`. It chunks the maintenance manuals, embeds the chunks, writes the Document and Chunk nodes, creates the `maintenanceChunkEmbeddings` vector index, and cross-links to the operational graph, all without calling an extractor. No OpenAI or Anthropic key is needed on this path.

```bash
uv run populate-aircraft-db setup --skip-extraction
```

The Document and Chunk nodes it writes are the same nodes the full path writes. What is missing is the extracted entities: no `ExtractedLimit` nodes, no `Fault` nodes, and none of their relationships. The 20 canonical `OperatingLimit` nodes load from CSV on this path too, and `link_to_existing_graph` still wires them to Sensors, so the `limit_retriever` cell in Lab 3 notebook 02 has a chain to traverse. Everything else in Lab 3, and all three tools in Lab 5, work against a graph loaded this way.

### Testing extractor settings

Use `debug-extract` to test the extractor on specific manual chunks without
writing to Neo4j or clearing enrichment data:

```bash
uv run populate-aircraft-db debug-extract \
  --document MAINTENANCE_A321neo.md \
  --chunks 3,5,6,7,9,10,11,12,13,15,16
```

The command uses the same `.env` settings as `setup` and reports whether each
chunk returns a valid graph. After the selected chunks pass, re-run enrichment:

```bash
uv run populate-aircraft-db enrich
```

If the debug chunks pass and enrichment was already generated, but cross-links
show `(none)` because the operational graph is missing, run:

```bash
uv run populate-aircraft-db load-operational
```

## What Gets Loaded

### Phase 1: Operational graph (from CSVs)

**9 node types:** Aircraft, System, Component, Sensor, Airport, Flight, Delay, MaintenanceEvent, Removal

**12 relationship types:** HAS_SYSTEM, HAS_COMPONENT, HAS_SENSOR, HAS_EVENT, OPERATES_FLIGHT, DEPARTS_FROM, ARRIVES_AT, HAS_DELAY, AFFECTS_SYSTEM, AFFECTS_AIRCRAFT, HAS_REMOVAL, REMOVED_COMPONENT

CSV files are read from `workshop-setup/aircraft_digital_twin_data/`.

The sensor readings file is not loaded into Neo4j. `nodes_readings.csv` holds
155,520 measurements, and the dual-database design puts every one of them in
the Databricks `sensor_readings` Delta table instead. `Sensor` nodes carry
metadata only, so a question about a measured value routes to Genie rather
than to Cypher.

The removal data includes tracking, work order, technician, part/serial,
warranty, priority, cost, installation, and shop-visit fields on `Removal`
nodes in addition to the existing component, aircraft, date, reason, TSN, and
cycle properties.

### Phase 2: Document chunks, embeddings, and manual knowledge

Uses `neo4j-graphrag`'s `SimpleKGPipeline` to process maintenance manuals from
`DOCUMENT_DIR` (A320-200, A321neo, B737-800, E190, A220-300 by default):

1. **Chunking**: Splits text into ~800-character chunks with overlap
2. **Embedding**: Generates BGE-large embeddings (local sentence-transformers, 1024 dimensions) stored on Chunk nodes
3. **Entity extraction**: Uses the configured extractor LLM to extract **AircraftModel**, **SystemReference**, **ComponentReference**, **Fault**, **MaintenanceProcedure**, and **ExtractedLimit** entities. Limits read out of the manuals get their own label so they never mix with the canonical **OperatingLimit** rows loaded from `nodes_operating_limits.csv`
4. **Entity resolution**: Deduplicates entities with matching `name` property (via APOC)
5. **Cross-linking**:
   - **Document → Aircraft** (APPLIES_TO) — links each manual to fleet aircraft by model
   - **AircraftModel → Aircraft** (DESCRIBES_MODEL) — links extracted model-level manual entities to fleet aircraft
   - **SystemReference/ComponentReference → System/Component** — links extracted manual references to matching operational graph nodes where names or types align
   - **Sensor → OperatingLimit** (HAS_LIMIT) — matches sensors to the canonical CSV operating limits by parameter name and aircraft type

Creates indexes:
- **Vector index:** `maintenanceChunkEmbeddings` on `Chunk.embedding`
- **Fulltext index:** `maintenanceChunkText` on `Chunk.text`

**Note:** Entity resolution requires APOC, which is available on Neo4j Aura by default.

## Known Issues

### Document `path` property

`SimpleKGPipeline` from `neo4j-graphrag` sets a default `path: "document.txt"` and `document_type: "inline_text"` on `Document` nodes when text is passed inline via `pipeline.run_async(text=...)`. To ensure Document nodes have a meaningful `path` value (e.g. `MAINTENANCE_A320.md`), we explicitly include `"path": meta.filename` in the `document_metadata` dict. Without this override, all Document nodes share the same generic `"document.txt"` path, which produces misleading results when agents query for document locations.
