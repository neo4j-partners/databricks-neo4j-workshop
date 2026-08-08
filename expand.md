# Proposal: Restructure Labs 4 through 6 for an Extended Advanced Workshop

A proposal to make Lab 4 Part B optional, add a LangGraph lab that connects the Genie space to the participant's own Aura instance, and add a memory lab. The result is a longer workshop where every required lab builds on the graph the participant loaded themselves.

**This document supersedes `proposed-outline.md` and `workshop-improve.md`.** Both of those propose restructures that end at Lab 4, and both predate the decision to add Labs 5 and 6. Where they conflict with this document, this document wins. Their still-valid parts, the "lead with the why" opening and the live demo of the finished agent before Lab 1, are carried into the Suggested Day Structure below. Each gets a superseded banner rather than deletion, since the reasoning in them is worth keeping.

---

## Status

Last updated 2026-08-08.

| Track | Where it is |
|---|---|
| **A. Engineering** | Phase 0 catch-up loader **done and verified against a live Aura instance.** Phase 1 starting |
| **B. Memory research** | Memory spike in flight, running in parallel with Phase 1. Nothing here has been measured yet |
| **C. Content and infra** | Repository documentation complete. The Lab 5 architecture diagram, the Antora site in `site/`, the slides in `slides/`, and the Vocareum courseware bundle are deferred by decision rather than outstanding |

**Done**

- The `databricks` embedding provider, the `--skip-extraction` flag, and every documentation and naming change in the Concrete Changes list below except the diagram.
- Verified end to end on 2026-08-08: `populate-aircraft-db setup --skip-extraction` with `EMBEDDING_PROVIDER=databricks` took an empty Aura instance to a complete graph in **4 minutes 23 seconds** with no OpenAI or Anthropic key present. Result: 155,520 Readings, 14,543 Flights, 5,541 Delays, 612 Components, 290 Chunks, 288 Sensors, 286 MaintenanceEvents, 144 Systems, 57 Removals, 40 Airports, 36 Aircraft, 5 Documents. All 290 chunk embeddings at 1024 dimensions. `maintenanceChunkEmbeddings` ONLINE and returning results. Lexical graph identical in shape to the `SimpleKGPipeline` output: `FROM_DOCUMENT` 290, `NEXT_CHUNK` 285, `APPLIES_TO` 36 cross-links to Aircraft, and both `Document` and `Chunk` carrying the `__KGBuilder__` label the library writes.

- **Idempotency confirmed.** A second full run over the already-loaded instance finished in 4 minutes 9 seconds and left node counts unchanged at 177,362 with chunks still at 290, so nothing duplicated. It also reports `[OK] Verification passed.` with zero warnings now that the extraction checks stand down when extraction was skipped, and states in one line that they were not verified.
- Embedder drift measured and **retired**. The loader path and the Lab 3 path return cosine 1.0000000000 on the same text, because both now call the same Foundation Model endpoint through the same client. A `data_utils.py` query embedding against loader-written vectors returns the right chunks at 0.85.
- Four open questions settled on 2026-08-08: the development instance split, `VectorCypherRetriever` for `graphrag_node`, the memory spike running in parallel with Phase 1, and deterministic `OperatingLimit` loading. Each is recorded in place below.

**Development instances**

Two Aura instances, one per track, so neither track's writes show up in the other's tests.

| Instance | Track | Credentials |
|---|---|---|
| `f024ea61` | A. Lab 5 development, already loaded | `workshop-setup/.env` |
| `1a2c98cc` | B. Memory spike | `workshop-setup/.env.memory` |

Instance `f024ea61` is reset with `populate-aircraft-db clean` and reloaded whenever a test needs a clean graph.

**Next**

Phase 1 and the memory spike are both in flight. Phase 1 builds the three Lab 5 tools against the already-loaded `f024ea61`; the spike measures the headline memory demo against `1a2c98cc`.

One Phase 0 item can still invalidate the Lab 5 plan on its own: whether the loader runs from a serverless notebook cell. It does not block Phase 1, which builds against an already-loaded instance.

The spike's go/no-go now lands after Lab 5 is underway. That is survivable because Lab 5 does not depend on memory. A no-go costs Lab 6 and nothing before it, and the recorded fallback stays "hold Lab 6 and ship Labs 4 and 5 alone."

Labs 5 and 6 get written before anything that describes them. The Vocareum courseware bundle, the Antora site in `site/`, and the slides in `slides/` are rewritten afterward, in one pass against what shipped. See Sequencing under the Implementation Plan.

**Known state, not bugs**

- `vocareum/courseware/data/Lab_3_Semantic_Search/` holds tracked copies of the three Lab 3 notebooks and `data_utils.py`. They were byte-identical to the top-level `Lab_3_Semantic_Search/` files until the 2026-08-08 secret-scope change, which touched only the top-level copies. The two now diverge. `lab/` uses symlinks to the top-level directories, so that path picks the change up on its own. The `vocareum/courseware/data/` path does not, because it is a copy. `neo4j-databricks-workshop.dbc` and `neo4j-databricks-workshop.dat` are binary bundles of the same files and need rebuilding at the same time. The divergence is deliberate: the bundle gets resynced once, in Phase 4, after the lab content has stopped moving, rather than after every edit.
- The Antora site in `site/` and the slides in `slides/` still end the workshop at Lab 4, and both are deferred to Phase 5 for the same reason. Until that pass lands, a push to `main` publishes a site that contradicts the repository READMEs.

---

## The Problem

Labs 1, 2, and 3 all connect to the participant's personal Aura instance through the same configuration cell:

```python
NEO4J_URI = ""       # e.g., "neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = ""  # Your password from Lab 1
```

Lab 4 Part B is the only place in the workshop that breaks this pattern. It routes graph questions through an administrator-managed external MCP server pointed at a shared Reference Aura Instance, and the lab says so explicitly:

> You do not need data in your personal Aura instance for this lab.

Everything the participant built in Labs 1 through 3 goes unused at the exact moment the workshop is supposed to pay off. They load a fleet graph in Lab 2, build vector indexes and GraphRAG retrievers over it in Lab 3, then watch an agent answer questions against somebody else's database. The GraphRAG work from Lab 3 is never wired into the agent at all.

The fix is to add a required lab that points an agent at the graph the participant built, and to reposition Part B as the optional no-code path rather than the main line. Part B stays where it is and keeps working. It stops being the only ending the workshop has.

---

## Recommended Structure

| Lab | Content | Neo4j target | Time | Status |
|---|---|---|---|---|
| 1 | Aura setup and Cypher basics | Personal | 20 min | Required |
| 2 | Databricks ETL to Neo4j via Spark Connector | Personal | 45 min | Required |
| 3 | Semantic search and GraphRAG retrievers | Personal | 45 min | Required |
| 4 Part A | Genie space over Lakehouse telemetry | none | 30 min | Required |
| 4 Part B | Agent Bricks no-code supervisor over MCP | Reference | 45 min | **Optional, advanced** |
| **5** | **LangGraph agent over Genie plus their own Aura** | **Personal** | **90 min** | **Required** |
| **6** | **Neo4j agent memory** | **Personal** | **75 min** | **Required** |
| App. A | GDS graph analytics | Personal | optional | Optional |

Roughly five hours of required lab time, which supports a full-day advanced format with lecture and breaks. Part B adds 45 minutes for audiences that want the no-code path.

The column that matters is the third one. On the required path every lab reads and writes the same database, and each lab's output is the next lab's input. Lab 2 loads the fleet, Lab 3 adds documentation and vector indexes to it, Lab 5 builds an agent that queries both, and Lab 6 writes the agent's memory back into it.

---

## Lab 4: Part A Required, Part B Optional

Leave both parts where they are. `Lab_4_Compound_AI_Agents/` keeps its name, its README, `PART_A.md`, and `PART_B.md`. Two edits to the README:

**Mark Part B optional and advanced.** It becomes the no-code path for audiences that want to see Agent Bricks Multi-Agent Supervisor as a product, and the centrally-governed MCP path for audiences asking how this looks in production. Both are real reasons to run it. Neither is a reason to make it the only ending. Add a note that Part B queries the shared Reference Aura Instance rather than the participant's own, so participants understand why it works without their Lab 2 data.

**Reframe the Part A closing.** Right now Part A ends by pointing at Part B. It should end by naming what Genie cannot do: Genie answers "what was the average EGT" and cannot answer "which component failure delayed which flight," because that question is a traversal. Then offer both continuations. Lab 5 for the code path against your own graph, Part B for the no-code path against the reference graph.

## Lab 5: The LangGraph Agent

The lab the workshop has been building toward. A supervisor routing across three tools, all of them the participant's own work.

```
                       ┌──────────────┐
      question ───────▶│  supervisor  │◀───────────┐
                       └──────┬───────┘            │
              ┌───────────────┼───────────────┐    │
              ▼               ▼               ▼    │
      ┌───────────────┐ ┌───────────┐ ┌────────────┴──┐
      │  genie_node   │ │cypher_node│ │ graphrag_node │
      │   (Lab 4)     │ │  (Lab 2)  │ │    (Lab 3)    │
      └───────┬───────┘ └─────┬─────┘ └───────┬───────┘
              │               │               │
              ▼               ▼               ▼
      Unity Catalog      Neo4j Aura      Neo4j vector
        telemetry      (your instance)   index (yours)
              └───────────────┼───────────────┘
                              ▼
                        ┌───────────┐
                        │ synthesize│──▶ answer
                        └───────────┘
```

Three tools rather than two makes the routing lesson much better than Lab 4 Part B's. The supervisor now distinguishes three genuinely different retrieval modes:

| Question | Route | Why |
|---|---|---|
| "Average EGT on N10000 over 30 days" | Genie | Aggregation over 155K timestamped rows |
| "Which component failures delayed flights" | Cypher | Multi-hop traversal |
| "What does the manual say about EGT exceedance" | GraphRAG | Semantic similarity over manual chunks |
| "Engines with abnormal EGT, their maintenance history, and the relevant procedure" | All three | The anchor question, finally answerable end to end |

**Connection approach.** The `cypher_node` and `graphrag_node` use the Neo4j Python driver and `neo4j-graphrag` directly, with the same three credentials from the Lab 1 configuration cell. The `graphrag_node` is close to a straight lift of the `VectorCypherRetriever` already built in Lab 3 notebook 02, so it costs almost no new code and it finally connects Lab 3 to the agent. It reads the `maintenanceChunkEmbeddings` vector index and must embed queries with `databricks-bge-large-en`, matching `Lab_3_Semantic_Search/data_utils.py`.

Lab 3 notebook 03 builds hybrid retrieval over the `maintenanceChunkText` fulltext index and is marked optional. The `graphrag_node` therefore uses vector similarity rather than hybrid search to find the starting chunks. Hybrid becomes an exercise inside Lab 5 for anyone who ran notebook 03, never a dependency.

**`graphrag_node` uses `VectorCypherRetriever`, not a plain vector retriever.** The Cypher tail that runs after the vector hit is the part that makes this GraphRAG rather than vector search, so a vector-only node would demonstrate the least interesting half of Lab 3. This puts `graphrag_node` and `cypher_node` closer together than a clean tool boundary would like, since both end in a traversal, so the supervisor prompt has to distinguish them explicitly: `cypher_node` for questions that start from a named entity, `graphrag_node` for questions that start from language in the manuals. Routing accuracy between those two tools is the specific thing Phase 1's completion criteria must measure.

**Supervisor model.** Use `databricks-meta-llama-3-3-70b-instruct`, already the `DEFAULT_LLM_MODEL` in `Lab_3_Semantic_Search/data_utils.py:35`. One model endpoint across Labs 3 and 5 means one thing to check for availability in a new workspace. The endpoint name belongs in `lab/workshop.py` alongside the other object names.

Routing across three tools is a harder job than anything Lab 3 asks of this model, so treat the choice as provisional rather than locked. Declare it as one named constant in `agent.py` and never inline it. Phase 1 measures routing accuracy on the eval set; if the model misroutes the anchor question or confuses the Cypher and GraphRAG tools, swap the constant to a stronger tool-calling endpoint such as `databricks-claude-sonnet-4-5` and record the second endpoint as a workspace prerequisite. Start with one endpoint, keep the escape hatch to two.

**Deployment and auth.** Required, not optional. Deploying an agent that authenticates as a service principal is the lesson that separates a notebook demo from a product, and it is the question participants ask anyway. Two credentials, not one, and they fail in different ways:

| Credential | Mechanism | Risk |
|---|---|---|
| Aura password for `cypher_node` and `graphrag_node` | Databricks secret scope, injected as an environment variable at deploy time | Low. Fails loudly at connection time |
| Genie space and model endpoint access for `genie_node` | Resources declared at log time so deployment provisions a short-lived credential for the serving principal | Higher. The endpoint deploys fine and Genie calls fail at request time with an authorization error |

The Genie path is the more likely deployment failure, because the notebook runs as the participant while the endpoint runs as a service principal, and Genie also requires access to the underlying Unity Catalog tables rather than to the space alone. Phase 2 verifies this by calling the deployed endpoint, not by checking that deployment succeeded.

Budget 10 minutes of Lab 5 for credential handling, and budget wait time for the deploy itself. Phase 2 measures how long a cold deploy takes so the lab can name the number instead of leaving participants watching a spinner.

**Structure.** Split into two notebooks so the halfway point is a working agent:

- `01_langgraph_agent.ipynb`: build the three tools, wire the supervisor, run the test questions in-notebook.
- `02_deploy_and_evaluate.ipynb`: wrap in `ResponsesAgent`, log to Unity Catalog, deploy, evaluate with MLflow against a fixed question set.

## Lab 6: Agent Memory

Memory writes go to the participant's Aura instance, which is where their domain graph already lives. That single fact is what makes this lab worth building, because memory nodes and fleet nodes end up in one database and can be traversed together.

Use [`neo4j-agent-memory`](https://github.com/neo4j-labs/agent-memory) on the self-hosted bolt path. `client.schema.adopt_existing_graph(...)` adopts the fleet graph as long-term memory, so remembered entities resolve to the real `Aircraft` and `Component` nodes from Lab 2 rather than creating parallel copies. Add `recall` and `remember` nodes on either side of the Lab 5 supervisor.

Demonstrations, in order of how well each answers "why does this need a graph". **Hands-on** means the participant writes and runs it. **Demo** means the notebook ships it complete and the participant runs the cell and reads the output, with the instructor talking over it.

| Demo | What it shows | Include |
|---|---|---|
| Memory joined to fleet data in one traversal | Which components three or more technicians asked about this week, and whether those are the ones actually failing. One Cypher across the conversation graph and the fleet graph | Hands-on, headline |
| Reasoning reuse, measured | Successful Cypher and SQL replayed as few-shot exemplars. Run the eval set with memory off then on, compare tool calls, retries, tokens, latency, accuracy | Hands-on |
| Cross-session continuity | "Any vibration trends on that aircraft?" resolves after a restart | Hands-on |
| Correction with temporal invalidation | Correct an EGT redline, then traverse to what the agent used to believe and when it stopped | Demo |
| Learned preferences | Role and fleet scope stored once, applied silently to later sessions including the generated SQL | Demo |
| Shift handoff | Investigation findings attach to the component and a different technician picks them up | Demo |
| Routing memory | The supervisor learns which tool answered similar questions, improving on the static prompt from Lab 5 | Demo |
| Proactive briefing | Remembered interests joined to fresh telemetry on session start | Optional |
| GDS over the memory graph | Attention hotspots across the organization, written back to Delta. Ties in Appendix A | Stretch |

Three hands-on demos in 75 minutes leaves roughly 20 minutes each including setup, which is honest. Nine hands-on demos in 75 minutes was not. The four marked Demo still get built and still get airtime; they cost the participant a cell run rather than a build, so they are cheap to keep and cheap to skip when the room is running late.

The headline demo is the reason to do this in Neo4j rather than any memory product, and it only works because memory and fleet data are in one database. Under the old structure they were in two.

---

## What Happens to Part B and MCP

**Part B stays in place, marked optional.** It teaches Agent Bricks Multi-Agent Supervisor as a no-code product, which is a genuine Databricks selling point and takes 45 minutes to reach a working system. Nothing about it changes except its position on the required path. An instructor can also demo it in 10 minutes to make the no-code versus code contrast explicit without spending the full 45.

**All MCP material stays, marked advanced and forward-looking.** MCP appears in the agenda, in the Key Technologies table, in the architecture diagrams, and across `workshop-setup/neo4j_mcp_connection/` and `MCP-MANUAL-SETUP.md`. None of it needs to move. What changes is how it is framed: MCP is the direction this integration is heading and the pattern for centrally-governed agent access to Neo4j, presented as an advanced section rather than as the mechanism every participant must use to finish the workshop.

Three places it lives:

1. **Lab 4 Part B**, unchanged, as the Unity Catalog HTTP connection pattern with OAuth2 M2M against a hosted MCP server. The production shape.
2. **A future section in Lab 5**, sketched but not required in the first release, that runs `mcp-neo4j-cypher` as a local process against the participant's own Aura and swaps the `cypher_node` implementation to call it. Same agent, same answers, different transport. This is the version that teaches MCP as an abstraction rather than as a hosting problem, and it is worth building once Lab 5 is stable.
3. **`workshop-setup/`**, unchanged, as the admin path for anyone provisioning the connection.

**Admin setup cost is unchanged for now.** Keeping Part B alive means keeping the AgentCore deployment, the OAuth2 M2M credentials, the Unity Catalog connection, and the loaded reference instance alive with it. That cost was previously on the critical path for every delivery. It now sits behind an optional lab, so a broken MCP connection stops being a workshop-stopping failure at 9am. It becomes a section the instructor skips.

---

## The Cost, and How to Cover It

Under the current structure, Lab 4 Part B is a safety net. A participant who never finishes Lab 2 still gets a working agent, because the agent queries somebody else's fully loaded database. Part B survives this proposal and can still play that role, but it is no longer where the workshop ends, so Labs 2 and 3 become load-bearing for Labs 5 and 6.

Three mitigations, in order of importance:

**A catch-up cell at the top of Lab 5.** One cell that brings the participant's Aura instance to the state Labs 2 and 3 would have left it in, idempotently. Anyone behind runs it and continues. This is the single most important item in the whole proposal to get right, because without it the restructure trades a narrative problem for a completion problem.

Reuse `workshop-setup/populate_aircraft_db` rather than writing a new loader. `uv run populate-aircraft-db setup` already loads the CSVs, chunks the manual, generates embeddings, and creates the indexes, and `loader.py` already checks for the index named `maintenanceChunkEmbeddings`, which is the same name Lab 3 notebook 01 creates. The tool targets Lab 3's schema today. Rebuilding would mean reproducing that schema by hand and maintaining two loaders that must agree forever.

Two changes were required before it could be reused. **Both are done and verified.**

**Add a `databricks` embedding provider.** `config.py` currently offers `bge`, which runs `BAAI/bge-large-en-v1.5` locally through sentence-transformers, and `openai`. Lab 3 uses the `databricks-bge-large-en` Foundation Model endpoint. Same model, same 1024 dimensions, two different serving paths. Vectors from the two paths should be close, and "should be close" is not good enough for a vector index that `graphrag_node` queries. Adding a third provider that calls the same endpoint Lab 3 uses removes the question entirely and drops the sentence-transformers dependency from the serverless path.

**Add a flag to skip entity extraction.** The `setup` command also runs `SimpleKGPipeline` entity extraction, which needs an LLM API key and is not something Lab 5 depends on. The catch-up path needs CSVs, chunks, embeddings, and indexes. Nothing else.

This was written as a small change and it was not one. `SimpleKGPipeline` builds chunking, embedding, and extraction as one object with no seam between them, and the index creation the catch-up path exists for runs after it, so a flag that wraps the call would also skip the index. What shipped instead assembles the library's own components minus the extractor, and puts the branch inside the enrich step so index creation and cross-linking still run on both paths. Everything else in Lab 3, and all three Lab 5 tools, work against the resulting graph.

Skipping the extractor did leave one gap, and it is being closed at the source rather than documented as a limitation. No extractor meant no `OperatingLimit` nodes, so Lab 3 notebook 02's `limit_retriever` cell had nothing to return on a catch-up graph. The fix: the operating limits are extracted from the five maintenance manuals once, into a checked-in CSV, and the loader writes `OperatingLimit` nodes and `HAS_LIMIT` edges from it like any other node CSV. Deterministic, no LLM, no key. The catch-up path then produces the same graph the extraction path does for this entity type. In progress; tracked as a Phase 0 item.

**A documented fallback to the reference instance.** Keep the reference instance credentials available as an override for anyone whose Aura instance is broken or expired. Changing three variables in a configuration cell restores the old behavior. Cheap insurance that costs one paragraph of documentation.

**A Lab 3 fallback for the GraphRAG node.** The `graphrag_node` needs the vector index from Lab 3 notebook 01. If a participant skipped it, the agent should degrade to two tools with a clear message rather than failing at import time.

---

## Suggested Day Structure

| Segment | Time |
|---|---|
| Opening: the problem, the architecture, live demo of the finished agent | 30 min |
| Lab 1: Aura setup | 20 min |
| Lecture: graph data modeling and integration patterns | 30 min |
| Lab 2: Databricks ETL to Neo4j | 45 min |
| Break | 15 min |
| Lecture: GraphRAG, vector search plus traversal | 25 min |
| Lab 3: Semantic search and GraphRAG | 45 min |
| Lunch | 45 min |
| Lab 4 Part A: Genie space | 30 min |
| Lecture: agent architectures and the supervisor pattern, including MCP | 25 min |
| Lab 5: LangGraph agent | 90 min |
| Break | 15 min |
| Lecture: agent memory, and why it is a graph problem | 20 min |
| Lab 6: Agent memory | 75 min |
| Close: what to build next, call to action | 20 min |

About seven and a half hours including breaks. Lab 4 Part B and Appendix A are take-home, with a 10 minute instructor demo of Part B folded into the agent architectures lecture so the no-code path and the MCP pattern both get airtime.

For audiences that cannot commit to a full day, the same material splits: Labs 1 through 4 as a half-day foundation, where Part B is a reasonable ending on its own, and Labs 5 and 6 as a half-day advanced session for participants who completed the first.

The split is not free. A half-day advanced session is a different room on a different day, and Aura Free instances pause after three days of inactivity and are deleted after 30. Whatever a participant loaded in the foundation session may be gone, paused, or forgotten by the time the advanced session starts, and the Lab 5 catch-up cell only helps someone who reaches Lab 5 in the same workspace with the same credentials. Making the split actually work needs a second catch-up path at the top of Lab 6, plus a way for a returning participant to get back to a running instance with the right data. That is real work and it is not the first work. It lands as **Phase 5**, after the full-day path is proven. Until Phase 5 ships, the full day is the supported format and the split is best effort.

---

## Concrete Changes

**New**

```
Lab_5_LangGraph_Agent/
├── README.md
├── 01_langgraph_agent.ipynb      # Three tools, supervisor, in-notebook testing
├── 02_deploy_and_evaluate.ipynb  # ResponsesAgent, secret scope, deploy, MLflow eval
├── agent.py                      # Graph definition, logged as the MLflow model
├── tools.py                      # genie, cypher, graphrag tool construction
└── eval/questions.jsonl

Lab_6_Agent_Memory/
├── README.md
├── 01_memory_setup.ipynb         # Memory client, adopt existing graph, recall/remember nodes
├── 02_memory_demos.ipynb         # The demonstration set
├── memory.py
└── eval/run_memory_eval.py       # Memory off versus on comparison
```

**Moved**

Nothing. `Lab_4_Compound_AI_Agents/` keeps its name, both parts, and all MCP material.

**Edited**

- `Lab_4_Compound_AI_Agents/README.md`: mark Part B optional and advanced, note that it queries the Reference Aura Instance, and offer Lab 5 as the other continuation.
- `Lab_4_Compound_AI_Agents/PART_A.md`: rewrite the closing handoff to point at both Lab 5 and Part B.
- `Lab_4_Compound_AI_Agents/PART_B.md`: add an optional-section banner at the top. No content changes.
- `README.md` and `agenda.md`: new lab list, the extended-day framing, and MCP described as the advanced and forward-looking integration pattern rather than the required one.
- `Lab_3_Semantic_Search/README.md`: note that notebook 01 is now required rather than foundational, since Lab 5 depends on the `maintenanceChunkEmbeddings` index. Notebook 03 stays optional.
- `workshop-setup/populate_aircraft_db/src/populate_aircraft_db/config.py`: add a `databricks` embedding provider calling `databricks-bge-large-en`.
- `workshop-setup/populate_aircraft_db/src/populate_aircraft_db/main.py`: add a flag to skip entity extraction for the catch-up path.
- `workshop-setup/populate_aircraft_db`: a checked-in CSV of operating limits extracted from the five maintenance manuals, plus loader code that writes `OperatingLimit` nodes and `HAS_LIMIT` edges from it like any other node CSV. This takes the one entity type Lab 3 notebook 02 queries directly off the LLM extraction path, so `limit_retriever` returns results on a catch-up graph.
- `lab/workshop.py`: names for the Lab 5 model, serving endpoint, secret scope, and the `databricks-meta-llama-3-3-70b-instruct` supervisor endpoint. It also creates the `agents` schema that holds the registered Lab 5 model, with a `USE_SCHEMA` grant to the participant grantee.
- `Lab_3_Semantic_Search/01_data_and_embeddings.ipynb`: the one place a participant types Neo4j credentials. It writes them to a per-participant secret scope, then reads them back from that scope for its own connection. Notebooks 02 and 03 read from the scope and carry no plaintext password. See Open Decision 1, now resolved.
- `workshop-setup/README.md`: mark external MCP provisioning as required only for Lab 4 Part B.
- `images/lab-architecture-overview.*`: add a Lab 5 variant drawn against the participant's own Aura with three tools. Keep the existing diagram for Part B. **Deferred to Phase 5.** The shipped PNG currently shows the Part B MCP topology, which is now the optional path, and both the root README and the Lab 4 README display it. Drawing it before Lab 5 is built means drawing an architecture nobody has run.
- `vocareum/courseware/`: resync `data/Lab_3_Semantic_Search/` from the top-level lab directories and rebuild `neo4j-databricks-workshop.dbc` and `neo4j-databricks-workshop.dat`. **Deferred to Phase 4.** These are copies rather than symlinks, so they already diverge from the top-level files after the 2026-08-08 secret-scope change. Resyncing once after the lab content stops moving costs one pass. Resyncing after every edit costs one pass per edit.
- `site/`: the Antora source tree that `.github/workflows/deploy-antora.yml` builds and publishes on every push to `main`. It carries its own navigation, its own lab tables, and its own copy of the architecture diagram, all of which still end the workshop at Lab 4. Roughly 30 stale lines across 9 `.adoc` files. Two of them are the exact claims this restructure exists to remove: `site/modules/ROOT/pages/lab4-instructions.adoc:16` still says "You do not need data in your personal Aura instance for this lab," and `site/modules/ROOT/pages/lab4-instructions.adoc:552` still says "You have completed the workshop." **Deferred to Phase 5**, rewritten in one pass once Labs 5 and 6 have landed. The risk of waiting, stated plainly: until that pass, a push to `main` publishes a site that contradicts the repository READMEs.
- `slides/`: `slides/platform-overview/01-workshop-over.md:126-143` still lists the MCP infrastructure as required shared provisioning, and the slides still describe the old shared-versus-personal Aura split. **Deferred to Phase 5** for the same reason as the site, and rewritten in the same pass.
- `proposed-outline.md` and `workshop-improve.md`: add a superseded banner at the top of each pointing here. No content changes, since the reasoning is still worth reading.

---

## Open Decisions

1. ~~Whether provisioning creates one secret scope per participant or the workshop shares one scope with per-user keys.~~ **Resolved 2026-08-08: neither. The participant creates their own scope, in Lab 3 notebook 01.**

   Credentials are typed once, in the notebook that already asks for them, and written to a scope named `fleet-ops-<user-slug>`. Notebooks 02 and 03 read from it, and Lab 5 reads from it. This is strictly better than provisioning, for three reasons: it removes the secret scope from `lab/workspace_init.sh` and `lab/lab_end.sh` entirely, it removes the Phase 0 question of whether a Vocareum hook can create scopes, and no participant's Aura password is ever visible to another.

   Four things the implementation has to get right:
   - **Scope names are workspace-unique, not per-user.** A literal name means the first participant wins and the other 29 write into their scope. The name is derived from `current_user()`.
   - **Guard the placeholder.** A participant who re-runs the cell after clearing it would otherwise overwrite a working password with `your-password-here`. The write refuses when the field is empty or unchanged.
   - **The served endpoint reads secrets differently from the notebook.** In the notebook `dbutils.secrets.get` works because the participant owns the scope. The deployed endpoint runs as a service principal, and secret scopes are not in the automatic-passthrough resource list. The working pattern is an endpoint environment variable, `{"NEO4J_PASSWORD": "{{secrets/<scope>/<key>}}"}`, set at deploy time, with READ granted to the endpoint's principal. **Unmeasured.** Phase 2 settles it before Lab 5 notebook 02 is written.
   - **`dbutils.secrets.get` redacts on print.** A participant debugging by printing the URI sees `[REDACTED]` and reads it as a bug. One sentence of lab text prevents the support question.

   Lab 5 gets the same scope-creation block, commented out by default, above a note saying to run it only if Lab 3 was skipped. Lab 5 is not a place to type a password. It is a place to recover if you arrived without one.
2. Whether `databricks-meta-llama-3-3-70b-instruct` routes three tools well enough. Phase 1 decides it on measured routing accuracy, not on preference. The fallback is a second endpoint.
3. When the local MCP section lands in Lab 5. Proposed as a future section rather than first release, since it is the part most likely to behave differently on serverless compute and Lab 5 should ship without waiting on it.
4. How long Part B stays maintained. It is optional now, so a break is survivable, but it still requires a live AgentCore server, valid OAuth2 M2M credentials, and a loaded reference instance. Worth setting a review date rather than deciding today.

---

## Implementation Plan

### Goal

A participant can finish Lab 6 having used only the Aura instance they created in Lab 1, with Lab 4 Part B and all MCP material intact and marked optional.

### Sequencing

Write the new labs first. Lab 5, then Lab 6. Only after they land does anything downstream get rewritten: the Vocareum courseware bundle, the Antora site in `site/`, and the slides in `slides/`. Those three surfaces describe the course, so rewriting them before the course exists means writing them twice, once against a proposal and once against what shipped.

Order: Lab 5, then Lab 6, then the courseware bundle in Phase 4, then the site and the slides together in Phase 5.

### Assumptions

- The Unity Catalog volume holds everything the catch-up loader needs, including the maintenance manual that Lab 3 notebook 01 chunks.
- Aura Free capacity covers the fleet graph, the manual chunks with embeddings, and one participant's memory graph together. To be measured in Phase 0, not assumed past it.
- Databricks serverless notebooks can open a bolt connection to Aura. Lab 2 already relies on this, so it is established rather than assumed.
- Whether `neo4j-agent-memory` accepts Databricks Foundation Model endpoints for its embedding and LLM providers is a hypothesis, not a fact. Phase 0 settles it.
- Whether a `uv` package installs and runs from a serverless notebook cell is unverified. If it does not, the fallback is to call `populate_aircraft_db` as a job on classic compute, or to vendor its loader module into the notebook. The embedding provider fix matters either way.
- ~~Vocareum participants may lack permission to create their own secret scope.~~ Retired by Open Decision 1. The participant creates their own scope from Lab 3 notebook 01, which the workshop already asks them to run. If it turns out they cannot, that surfaces in Lab 3 during the Phase 4 dry run rather than in a provisioning hook at 9am.
- A workspace can host one Model Serving endpoint per participant at class size. Deployment is required, so this stops being a nice-to-have and becomes a hard prerequisite. Phase 0 checks the quota, Phase 4 proves it at scale.
- `neo4j-agent-memory` is a `neo4j-labs` project with a pre-1.0 API surface. Assume it moves under us.

### Locked Decisions

| Decision | Reasoning | Dropped |
|---|---|---|
| LangGraph for Lab 5 | Genie, MCP, and MLflow integrations already exist on Databricks, and the supervisor pattern maps onto what participants configured in Part B | OpenAI Agents SDK, Pydantic AI, bare `ResponsesAgent` tool loop |
| Direct bolt driver for the Lab 5 Neo4j tools | Same three credentials as Labs 1 through 3, no per-participant server to host | Per-participant MCP server, shared MCP for the required path |
| `neo4j-agent-memory` on the self-hosted bolt path | Memory lands in the participant's own graph, so `adopt_existing_graph` can link memory to real fleet nodes | Hosted NAMS backend, which stores memory outside their Aura and breaks the headline demo |
| Part B and all MCP material stay in place | Part B is a genuine Databricks selling point and a working safety net; MCP is where the integration is heading | Deleting Part B, moving it to an appendix, removing MCP references |
| Reuse `populate_aircraft_db` as the catch-up loader | It already produces Lab 3's schema and index names, so one code path stays correct instead of two agreeing by luck | Writing a fresh Spark Connector loader |
| `graphrag_node` uses `VectorCypherRetriever` | The Cypher tail after the vector hit is what makes the node GraphRAG rather than vector search, so a vector-only node would demonstrate the least interesting half of Lab 3. The cost is that it sits close to `cypher_node`, which the supervisor prompt handles explicitly and Phase 1 measures | vector-only retrieval, a plain `VectorRetriever` with no Cypher tail |
| One embedding path, `databricks-bge-large-en` | The loader and Lab 3 must write vectors the same way or `graphrag_node` returns nonsense against the shared index | Leaving the loader on local sentence-transformers and hoping the vectors match |
| `databricks-meta-llama-3-3-70b-instruct` as the supervisor model | Already the Lab 3 default, so one endpoint to verify per workspace. Declared as one constant so Phase 1 can swap it on measured routing accuracy | GPT OSS 120B from the Part B Playground steps, a second endpoint to depend on |
| Model Serving deployment is required, not optional | Deploying an agent that authenticates as a service principal is the lesson that separates a notebook demo from a product, and it is the question every participant asks. Making it optional means most of the room skips the only part that teaches production auth | Instructor-demo-only deployment, take-home deployment |
| This document supersedes `proposed-outline.md` and `workshop-improve.md` | Three live planning documents with three different endings drift within a week. One document owns the plan | Keeping all three current, merging all three into one file |

### Deliberately Not Doing

- Rewriting Labs 1, 2, or 3. Lab 3 gets two changes and no more: a README note that notebook 01 is now required, and credential handling moved onto a secret scope. The lesson content in all three notebooks is untouched.
- Building the local `mcp-neo4j-cypher` section in Lab 5. Sketched as a future section so Lab 5 ships without waiting on serverless subprocess behavior.
- Hardening memory for production. Multi-tenancy, PII handling, and retention policy each get a callout in Lab 6, not an exercise.
- Redesigning the Genie space. Part A is already good and is not part of this work.
- Touching Vocareum provisioning beyond the new object names in `lab/workshop.py`. The per-participant secret scope was going to land in `lab/workspace_init.sh` and `lab/lab_end.sh`. Open Decision 1 moved it into Lab 3 notebook 01 instead, so the hooks are untouched.

### Phases

**Phase 0: Prove the risky parts.** Status: In progress. The loader is done and verified. The memory spike is running now, in parallel with Phase 1 rather than ahead of it, against its own Aura instance `1a2c98cc`.

The two items that can invalidate the plan. Everything after this is known-feasible engineering.

- [x] Add a `databricks` embedding provider to `populate_aircraft_db/config.py` calling `databricks-bge-large-en`. Verified returning 1024 dimensions
- [x] Add a flag to skip `SimpleKGPipeline` entity extraction. Shipped as `--skip-extraction` on both `setup` and `enrich`. It bypasses `SimpleKGPipeline` and assembles the library's own `FixedSizeSplitter`, `TextChunkEmbedder`, `LexicalGraphBuilder`, and `Neo4jWriter`, so the Document and Chunk nodes are the ones the full path writes. It does not write `OperatingLimit` nodes and `HAS_LIMIT` edges, which the next item moves out of extraction and onto a CSV
- [ ] Write `OperatingLimit` nodes and `HAS_LIMIT` edges deterministically. Extract the limits from the five maintenance manuals into a checked-in CSV, and have the loader write it like any other node CSV, so the catch-up path and the extraction path produce the same graph for this entity type. No LLM and no API key on the catch-up path
  - [ ] Verified by running the `limit_retriever` cell from Lab 3 notebook 02 against a graph loaded with `--skip-extraction` and getting results. A successful load is not the criterion; a non-empty `limit_retriever` result is
- [ ] Confirm `populate_aircraft_db` installs and runs from a serverless notebook cell, or pick the job or vendored fallback
- [x] Loader takes an empty Aura instance to a complete fleet graph plus Document and Chunk nodes, embeddings, and the `maintenanceChunkEmbeddings` index. Verified 2026-08-08 against an empty instance. Counts and timing in the Status section above
- [x] Prove no embedder drift. **Cosine 1.0000000000 on both test strings**, measured 2026-08-08 by embedding the same text through `populate_aircraft_db.pipeline.DatabricksEmbeddings` and `Lab_3_Semantic_Search/data_utils.DatabricksEmbeddings` in one process. Not close, identical. Both call `mlflow.deployments` against `databricks-bge-large-en` with the same request body, so there is one serving path rather than two. The drift risk is gone rather than mitigated
- [x] Query the vector index with a `data_utils.py` query embedding against loader-written vectors and confirm the top hits are relevant. Verified: "What is the procedure for an EGT exceedance?" returned EGT overheat and engine troubleshooting chunks at 0.8488, 0.8462, and 0.8335
- [x] Measure loader wall-clock time. 4 minutes 23 seconds for the full load including 290 embedded chunks. Comfortably in-lab, so the pre-generated-embeddings fallback is not needed
- [ ] Measure Aura Free storage after a full load
- [ ] Spike the headline memory demo standalone: write memory against a loaded instance, run one Cypher joining conversation memory to maintenance history, judge the answer
- [ ] Confirm which embedding and LLM providers `neo4j-agent-memory` accepts on Databricks
- [ ] Pin `neo4j-agent-memory` to an exact version and record it (see the research note below)
- [x] ~~Confirm whether Vocareum participants can create a secret scope~~ **Retired by Open Decision 1.** The participant creates their own scope in Lab 3 notebook 01, so no hook creates one and the permission question does not arise
- [ ] Check the workspace Model Serving endpoint quota against the largest expected class size

Completion criteria: the loader runs twice in a row without duplicating data, cross-path cosine similarity is high enough that retrieval quality is unchanged, and the memory spike either returns a good answer or is recorded as a no-go for Lab 6.

Note: generating embeddings for the manual chunks is the slow part and may push the loader past a comfortable in-lab runtime. If it does, pre-generate embeddings into the Unity Catalog volume and have the loader write them rather than compute them.

**Research note: pin `neo4j-agent-memory`.** It is a `neo4j-labs` project, which means a pre-1.0 API and no compatibility promise. A workshop notebook that installs the latest version can break between the dry run and delivery day without a single line of our code changing, and it breaks in a room, live. Before Phase 3 starts, answer four things and write the answers into `Lab_6_Agent_Memory/README.md`:

- **Exact version.** Pin it in the notebook `%pip install` line, not a floor and not a range. Record the resolved version and the commit it came from.
- **API surface we depend on.** List the specific calls Lab 6 uses, starting with `client.schema.adopt_existing_graph(...)`, and note whether each is documented or read off the source. Undocumented calls are the ones that move.
- **Neo4j version floor.** Confirm the pinned version works on the Neo4j version Aura Free actually serves, not on the version the README assumes.
- **Owner and cadence.** Who maintains it, how often it releases, and whether a Neo4j-internal contact can warn us before a breaking change. That contact is worth more than the pin.

If the pinned version cannot be made to work on Aura Free, that is a Phase 0 no-go for Lab 6 and it surfaces here rather than in Phase 3. Set a re-check date at the same time as the Part B review date, so both external dependencies get looked at together rather than each being remembered separately.

**Phase 1: Lab 5 core agent.** Status: Starting. Builds against the loaded Aura instance `f024ea61`, credentials in `workshop-setup/.env`

- [ ] `genie_node` bound to the Part A Genie space
- [ ] `cypher_node` against a personal Aura instance over bolt
- [ ] `graphrag_node` built on `VectorCypherRetriever`, lifted from the Lab 3 notebook 02 work, embedding queries with `databricks-bge-large-en`. The Cypher tail stays: it is what makes this GraphRAG rather than vector search
- [ ] Supervisor prompt distinguishes `cypher_node` from `graphrag_node` explicitly, since both end in a traversal and the boundary between them is the one the model is most likely to get wrong
- [ ] Supervisor node on `databricks-meta-llama-3-3-70b-instruct`, routing across all three, with the Part B routing prompt as the starting point
- [ ] `graphrag_node` degrades to a clear message rather than failing at import when the vector index is absent
- [ ] Optional hybrid retrieval exercise for participants who ran Lab 3 notebook 03
- [ ] Credentials read from the `fleet-ops-<user-slug>` secret scope Lab 3 notebook 01 created. No plaintext password anywhere in Lab 5
- [ ] A scope-creation block, **commented out by default**, above a note saying to run it only if Lab 3 was skipped. It is the recovery path, not the normal path
- [ ] `01_langgraph_agent.ipynb` runs the anchor question end to end across all three tools

Completion criteria: the anchor question about abnormal EGT, maintenance history, and the relevant manual procedure returns a correct answer in-notebook, and each of the four routing cases lands on the expected tool. Report `cypher_node` versus `graphrag_node` routing accuracy as its own number rather than folding it into an overall score, because `VectorCypherRetriever` makes those two tools adjacent and that pair is where misrouting will show up first.

**Phase 2: Lab 5 ships, deployment included.** Status: Pending

Deployment is required, so this phase is not done when the notebook is written. It is done when a deployed endpoint answers questions as a service principal.

- [ ] `ResponsesAgent` wrapper with MLflow autologging
- [ ] Aura password sourced from the Lab 3 secret scope rather than a notebook literal
- [ ] **Measure how the serving principal reads that scope.** The notebook path works because the participant owns the scope. The endpoint does not. Expected fix is an endpoint environment variable, `{"NEO4J_PASSWORD": "{{secrets/<scope>/<key>}}"}`, plus READ for the endpoint's principal. Unmeasured, and it is the credential most likely to fail silently until the first request
- [ ] Genie space and model endpoint declared as resources at log time so the serving principal gets a credential
- [ ] Serving principal confirmed to have access to the Unity Catalog tables behind the Genie space, not just to the space
- [ ] Logged to Unity Catalog and deployed to Model Serving
- [ ] **Call the deployed endpoint with one question per tool** and confirm all three answer. Genie is the one that fails here, not Neo4j
- [ ] **Call the deployed endpoint with the anchor question** and confirm it routes across all three tools end to end
- [ ] **Time a cold deploy** from `log_model` to a serving endpoint that answers, so the lab can tell participants how long to wait instead of leaving them guessing
- [ ] **Deploy a second endpoint as a different workspace user** and confirm both stay healthy. Proves per-participant deployment before Phase 4 proves it at class size
- [ ] Failure mode documented: what a participant sees when the Genie credential is missing, and the one thing to check
- [ ] MLflow evaluation against the fixed question set, run against the deployed endpoint rather than the in-notebook graph
- [ ] `02_deploy_and_evaluate.ipynb` and `Lab_5_LangGraph_Agent/README.md` complete

Completion criteria: the deployed endpoint answers one question per tool and the anchor question when called as the serving principal rather than as the notebook user, two endpoints coexist under different users, and the evaluation baseline for Lab 6 comes from the deployed endpoint. A successful deploy is not the criterion. A successful Genie call through the endpoint is.

**Phase 3: Lab 6 memory.** Status: Pending, gated on the Phase 0 spike

- [ ] Memory client configured against the participant's Aura, with `adopt_existing_graph` resolving to real fleet nodes
- [ ] `recall` and `remember` nodes added around the Lab 5 supervisor
- [ ] `neo4j-agent-memory` pinned to the exact version chosen in Phase 0
- [ ] The three hands-on demos: fleet-joined traversal, reasoning reuse, cross-session continuity
- [ ] Memory off versus on evaluation harness reusing the Phase 2 baseline
- [ ] The four instructor demos, shipped complete as runnable cells: correction with invalidation, learned preferences, shift handoff, routing memory
- [ ] Each hands-on demo timed individually against its share of the 75 minutes

Completion criteria: the headline traversal returns a good answer, the memory comparison shows a measurable difference in tool calls, tokens, or accuracy, and the three hands-on demos fit inside 75 minutes measured rather than estimated.

**Phase 4: Delivery readiness.** Status: Pending. Owner: Ryan.

Ryan runs the dry run personally, on a fresh Vocareum-shaped workspace user and a fresh Aura instance. Not a development workspace and not an account with leftover state, because the failures worth catching are the ones that only happen to someone starting clean.

- [ ] Full dry run of Labs 1 through 6 on a fresh Aura instance and a fresh workspace user
- [ ] Catch-up loader exercised from a deliberately incomplete Lab 2 state
- [ ] Reference instance fallback verified as a three-variable override
- [ ] Model Serving deployment exercised at class size, or the quota confirmed sufficient for it
- [ ] Part B still works, with its optional banner in place
- [ ] **Resync the Vocareum courseware bundle.** `vocareum/courseware/data/Lab_3_Semantic_Search/` holds copies, not symlinks, of the three Lab 3 notebooks and `data_utils.py`, and they diverged from the top-level files when the 2026-08-08 secret-scope change landed on the top-level copies alone. `lab/` symlinks the top-level directories and needs nothing. Rebuild `neo4j-databricks-workshop.dbc` and `neo4j-databricks-workshop.dat` in the same pass, since both are binary bundles of the same files. Done once, here, after the lab content has stopped moving
- [ ] Timings recorded against the suggested day structure, per lab and per Lab 6 demo

Completion criteria: Ryan completes the required path start to finish without intervening as the instructor, and the recorded timings either match the suggested day structure or the structure is corrected to match them.

**Phase 5: The half-day split.** Status: Pending, after Phase 4

Everything above assumes one continuous day. This phase makes the two-half-day format supported rather than best effort. It is last because it only matters once the full-day path is proven, and because its main deliverable is a second catch-up path that has no reason to exist until the first one works.

- [ ] **The Lab 5 architecture diagram.** A variant of `images/lab-architecture-overview.*` drawn against the participant's own Aura with three tools, keeping the existing one for Part B. Deferred to here because it should be drawn from the architecture that shipped rather than the one that was proposed, and because the current PNG being wrong costs a slide, not a lab
- [ ] **Rewrite the Antora site in `site/`.** Its own navigation, its own lab tables, and its own copy of the architecture diagram all still end the workshop at Lab 4. Roughly 30 stale lines across 9 `.adoc` files, including `site/modules/ROOT/pages/lab4-instructions.adoc:16`, "You do not need data in your personal Aura instance for this lab," and `site/modules/ROOT/pages/lab4-instructions.adoc:552`, "You have completed the workshop." `.github/workflows/deploy-antora.yml` publishes on every push to `main`, so until this pass lands the published site contradicts the repository READMEs. One pass, after Labs 5 and 6 have landed
- [ ] **Rewrite the slides in `slides/`.** `slides/platform-overview/01-workshop-over.md:126-143` still lists the MCP infrastructure as required shared provisioning, and the slides still describe the old shared-versus-personal Aura split. Same pass as the site, same reason for waiting
- [ ] Catch-up cell at the top of Lab 6 that brings a returning participant to end-of-Lab-5 state: fleet graph, Lab 3 artifacts, and a working Lab 5 agent. Reuses the Lab 5 catch-up cell and adds the agent
- [ ] Written guidance for resuming a paused Aura Free instance, and what to do when it was deleted rather than paused
- [ ] Confirm whether the Lab 5 serving endpoint survives between sessions or must be redeployed, and document whichever it is
- [ ] Confirm the participant's secret scope and Genie space access survive the gap
- [ ] A between-sessions note for participants: what to leave running, what will pause, and what to do the morning of the advanced session
- [ ] Foundation-session ending that stands on its own, since Lab 4 Part B is now the half-day close
- [ ] Dry run of the advanced half-day alone, starting from a deliberately cold state at least three days old

Completion criteria: someone who did the foundation session, walked away for a week, and let their Aura instance pause can start the advanced session and reach the Lab 6 headline demo without instructor help.

### What Runs in Parallel

Three tracks. Track C started immediately and its repository documentation work is done. What is left in Track C is deferred by decision rather than blocked: the courseware bundle in Phase 4, the site, the slides, and the Lab 5 diagram in Phase 5. Each of those describes the course, so each waits until the course has stopped moving.

| Track | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---|---|---|---|---|---|---|
| **A. Engineering** | Catch-up loader | Three tools plus supervisor | Deploy and evaluate | Memory nodes and demos | Dry run | Lab 6 catch-up cell |
| **B. Memory research** | Headline demo spike, provider check, version pin | Spike continues, in parallel with Phase 1 | idle | joins Track A | Dry run | idle |
| **C. Content and infra** | Lab 4 banners, Part A handoff, superseded banners **(done)** | Repo docs, `agenda.md`, `lab/workshop.py` **(done)** | Eval question set | Lab 6 README | Timing capture, Vocareum courseware resync | Lab 5 architecture diagram, Antora site, slides, between-sessions guidance |

What actually blocks what:

- The catch-up loader does not block building the Lab 5 tools. Build the tools against an already-loaded instance. The loader is a prerequisite for participants, not for development.
- The memory spike does not block Lab 5 at all. It needs a loaded graph and nothing else, so it runs alongside the entire Lab 5 build and delivers its go/no-go before Lab 6 starts. That is the settled order: the spike runs in parallel with Phase 1, not ahead of it. The consequence is that a no-go arrives after Lab 5 is underway, which costs nothing already built, because Lab 5 does not depend on memory. The fallback stays "hold Lab 6 and ship Labs 4 and 5 alone."
- The Track C work that was independent of code is done. What remains waits on the labs rather than on code: the courseware bundle, the site, and the slides all describe the course, so each gets rewritten once, after Labs 5 and 6 land.
- The Lab 5 eval question set can be written on day one. It is a list of questions and expected routes.
- Only Phase 3 has a hard dependency on Phase 1, because the memory nodes attach to the Lab 5 supervisor.
- Phase 5 depends on Phase 4, not on Phase 3. Its catch-up cell has to reproduce a state Phase 4 has confirmed is reachable, so building it earlier means building it against a moving target.

Parallelism caveat, now resolved: Tracks A and B both write to Aura, and the memory spike puts memory nodes into a graph the loader tests are trying to keep clean. Two tracks writing to one graph is how a loader test starts failing for a reason that has nothing to do with the loader. The separation now exists. Track A works against `f024ea61`, already loaded, credentials in `workshop-setup/.env`, reset with `populate-aircraft-db clean` and reloaded whenever a test needs a clean graph. Track B works against `1a2c98cc`, credentials in `workshop-setup/.env.memory`. With one person doing all three tracks, the tracks still collapse to sequential in wall-clock terms, but neither track can corrupt the other's evidence.

### If Phase 0 Fails

- ~~Loader too slow~~: **measured at 4 minutes 23 seconds, so this one did not happen.** The fallbacks stay written down in case the serverless path is slower than the laptop path: pre-generate embeddings into the volume, or split the loader so the fleet graph loads in-lab and the Lab 3 artifacts load only for participants who skipped Lab 3.
- ~~Embedder drift confirmed between the two paths~~: **measured at cosine 1.0, so this one did not happen either.** The rule it implied still stands and is now cheap to keep: one writer, one reader, one model, named once as `EMBEDDING_ENDPOINT` in `lab/workshop.py`.
- `populate_aircraft_db` will not run on serverless: vendor its loader module into the catch-up notebook. The embedding provider fix carries over unchanged, and the schema and index names stay identical.
- Aura Free too small: move memory to a second free instance and accept losing the fleet-joined traversal demo, or drop Lab 6 to the take-home path.
- Memory spike returns a weak answer: hold Lab 6 and ship Labs 4 and 5 alone. That is already a large improvement, and it is the majority of the value in this proposal.
