# Lab 6 modules

Developer documentation for the Python in this folder. **The lab itself is the
notebooks**, and the concepts are on the site:
[Lab 6: Agent Memory](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab6.html).

| File | What it is |
|---|---|
| `01_agent_memory.ipynb` | Adopt, seed, run the headline query, wire recall and remember, measure, redeploy |
| `02_instructor_demos.ipynb` | Four run-and-read demos. **Ships to every workspace**, and the instructor drives it. Not a participant exercise |
| `memory.py` | The Databricks adapters, the recall and remember nodes, the seed helper, and the headline Cypher |

There is no `memory_agent.py` on disk. Section 10 of notebook 01 writes it with
`%%writefile`, and that cell is the whole served model: `MemoryFleetOpsAgent`
subclasses Lab 5's `FleetOpsAgent` and overrides one method. Read the cell, not
the folder.

`memory.py` is lab-provided code rather than an exercise, for the same reason
`tools.py` is in Lab 5. Writing an async embedding adapter is not what anyone
came for.

## `memory.py`

| Name | What it does |
|---|---|
| `MemoryEmbeddings`, `MemoryLLM` | The two adapters that put `neo4j-agent-memory` on Databricks Foundation Model endpoints |
| `NotebookLoop`, `MemorySession` | A long-lived event loop, so an async client opened in one cell still works in the next |
| `adoption_dry_run`, `adopt_aircraft` | Adoption of the graph, with the guard rail that keeps it to `Aircraft` |
| `aircraft_mentions`, `seed_memory` | Explicit-mention writing, and the seeded shift history the demos read |
| `HEADLINE_QUERY`, `FLEET_ONLY_QUERY`, `MEMORY_ONLY_QUERY` | The query that crosses both halves, and its two controls |
| `build_recall_node`, `build_remember_node` | The two nodes either side of the Lab 5 supervisor |
| `build_memory_supervisor_node` | Lab 5's supervisor with `{recalled}` in its prompt and `resolved` in its reply |
| `MEMORY_SUPERVISOR_PROMPT`, `MEMORY_ROUTE_SCHEMA` | Lab 5's prompt and schema, each with one addition |
| `WHEEL_PATH`, `INSTALL_COMMAND`, `HTTPX_REQUIREMENT` | The pinned install, in one place |

The module imports `neo4j_agent_memory` lazily, inside the functions that need
it, so a notebook can import `memory.py` and print a useful message before the
`%pip install` cell has run. Keep it that way.

### Why the adapters are named `MemoryEmbeddings` and `MemoryLLM`

`DatabricksEmbeddings` and `DatabricksLLM` already exist, in
`Lab_3_Semantic_Search/data_utils.py`. Those implement neo4j-graphrag's
synchronous `Embedder` and `LLMInterface`. `neo4j-agent-memory` wants a
different thing: async Protocols, `embed` and `embed_one` on the embedder,
`complete` and `complete_structured` on the LLM. Two libraries, two sets of
Protocols, four classes, and the names have to differ or the second import
silently shadows the first.

`EMBEDDING_DIMENSIONS = 1024` is read off the adapter by the library, which
sizes every vector index it creates to match and re-validates on each later
connect. **Changing the embedding endpoint means dropping those indexes, not
editing a constant.**

### The event loop has to outlive the cell

`asyncio.run` per call opens and closes a loop each time. The Neo4j driver
inside the client binds to the loop that created it, so the next cell would get
a driver attached to a loop that no longer exists. `NotebookLoop` keeps one loop
on a background thread for the session, and `session.run(coro)` blocks on it.

### The adoption guard

`client.schema.adopt_existing_graph()` sets `n.type` unconditionally.
`DESTRUCTIVE_ADOPTION_LABELS` names the four labels whose `type` already means
something (`System`, `Component`, `Sensor`, `Document`), and
`_check_adoption_labels` refuses them before anything is written. Recovery from
adopting one of them is a full reload, measured at four and a half minutes.

`ADOPT_LABEL_TO_TYPE` is `Aircraft` alone, and `build_memory_settings` declares
one entity type, `AIRCRAFT`, for the matching reason: entities the library
creates take a label derived from their type, so `SYSTEM` becomes
`:System:Entity` and collides with the graph's own label.

`UNUSED_MEMORY_SUBSYSTEMS` names the four subsystems this lab never writes, and
the library then leaves their indexes and constraints off the instance. Index
count is the scarce resource on AuraDB Free, not node count.

### Why the wheel is pinned from a Unity Catalog volume

`neo4j-agent-memory` is a `neo4j-labs` project: pre-1.0, no compatibility
promise. `WHEEL_PATH` is built from the `mentions` branch of
<https://github.com/neo4j-partners/agent-memory>, checked into
`lab/courseware/wheels/`, and uploaded by `workshop.py provision-data`. Three
reasons, and each of them fails silently rather than loudly:

1. **Released 0.5.0 drops `MENTIONS` edges** on the automatic extraction path.
   `_extract_and_link_entities` links through `MATCH (e:Entity {id: $entity_id})`
   on a `uuid4` the `MERGE` never assigned, so every repeat mention and every
   adopted node is a no-op write. `MENTIONS` is the exact edge `HEADLINE_QUERY`
   walks. The fork reads the id back from the write and fixes it.
2. **A wheel carries no extras**, and the bolt path needs `httpx`. It is
   imported transitively by `MemoryClient.connect()`, so a bare install fails at
   connect time rather than at import time, in front of the room.
3. **The local version segment `+mentions` resolves from no index**, so anything
   pinning by version alone has to be handed the path. MLflow's inferred
   requirements are the case that matters, and Section 10 passes it.

The per-participant cluster installs the same path through
`VOC_COURSE_LIBRARIES` in `lab/course.env`, so the notebook's `%pip` line is a
safety net rather than the primary install. `workshop-setup/README.md`, section
"The `neo4j-agent-memory` wheel", is the operational account: how it is built,
how to rebuild it, and the Model Serving trap that follows.

**Treat any upgrade as a code change with its own test pass.** `main` already
carries a rewrite of the Protocol surface `MemoryEmbeddings` and `MemoryLLM`
bind to. William Lyon owns the upstream repository and is the contact for a
breaking-change warning.

### API surface that is likely to move

Documented and stable: `MemoryClient`, `MemorySettings`, `Neo4jConfig`,
`SchemaConfig`, `SchemaModel.CUSTOM`, `client.short_term.add_message`,
`client.short_term.search_messages`, `client.query.cypher`, and
`client.schema.adopt_existing_graph`.

**Docstring only, so these are the ones that move:** `extraction_mode="explicit"`
with `explicit_mentions=[EntityRef(...)]`, and `EntityRef` itself, which is not
exported at package root and has to come from
`neo4j_agent_memory.schema.models`.

Two more constraints worth knowing before editing anything. `add_messages_batch`
takes no `extraction_mode` and no `explicit_mentions`, which is why `seed_memory`
loops over the singular call. And `MemorySession.cypher()` is read-only by
design and rejects a write before the round trip, so notebook 02's cleanup cell
goes through a plain driver from `tools.open_driver_from_secrets` instead.

## Cross-lab imports, and why the folders must stay siblings

`memory.py` imports the embedder, the LLM helpers and the secret-scope helpers
from `../Lab_3_Semantic_Search/data_utils.py`, and the agent state, the routing
schema and the supervisor prompt from `../Lab_5_LangGraph_Agent/tools.py`. It
carries no copies of either.

**Keep `Lab_3_Semantic_Search`, `Lab_5_LangGraph_Agent` and
`Lab_6_Agent_Memory` as siblings**, in the repository and in the workspace, and
`ensure_labs_on_path()` resolves both on its own. Moving any one of them breaks
the other two.

`agent.py` is imported by the generated `memory_agent.py`, never by `memory.py`.
Importing it runs its `mlflow.models.set_model()` call, and a notebook that
imports `memory.py` should not be declaring itself a model, which is why
`ENV_CREDENTIAL_NAMES` is repeated here rather than imported.

## Measured results

The latency memory adds, and the argument about when it is worth paying, are on
the
[site page](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab6.html#what-memory-costs).
Section 9 of notebook 01 reproduces the comparison, and
`worklog/lab6-memory-defects.md` is the full run record, including the two
recall defects and the section-by-section timing behind the 75 minute budget.

**If you edit `MEMORY_SUPERVISOR_PROMPT` or `build_recall_node`, re-run Section
9 and read the answers, not just the score.** The failure mode here is a
confident answer about the wrong aircraft, and a substring test scored one of
those as a pass.
