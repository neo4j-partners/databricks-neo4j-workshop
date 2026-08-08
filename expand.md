# Proposal: Restructure Labs 4 through 6 for an Extended Advanced Workshop

A proposal to make Lab 4 Part B optional, add a LangGraph lab that connects the Genie space to the participant's own Aura instance, and add a memory lab. The result is a longer workshop where every required lab builds on the graph the participant loaded themselves.

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

Lab 3 notebook 03 builds hybrid retrieval over the `maintenanceChunkText` fulltext index and is marked optional. The `graphrag_node` therefore uses vector retrieval only. Hybrid becomes an exercise inside Lab 5 for anyone who ran notebook 03, never a dependency.

**Supervisor model.** Use `databricks-meta-llama-3-3-70b-instruct`, already the `DEFAULT_LLM_MODEL` in `Lab_3_Semantic_Search/data_utils.py`. One model endpoint across Labs 3 and 5 means one thing to check for availability in a new workspace. The endpoint name belongs in `lab/workshop.py` alongside the other object names.

**Deployment and auth.** Two credentials, not one, and they fail in different ways:

| Credential | Mechanism | Risk |
|---|---|---|
| Aura password for `cypher_node` and `graphrag_node` | Databricks secret scope, injected as an environment variable at deploy time | Low. Fails loudly at connection time |
| Genie space and model endpoint access for `genie_node` | Resources declared at log time so deployment provisions a short-lived credential for the serving principal | Higher. The endpoint deploys fine and Genie calls fail at request time with an authorization error |

The Genie path is the more likely deployment failure, because the notebook runs as the participant while the endpoint runs as a service principal, and Genie also requires access to the underlying Unity Catalog tables rather than to the space alone. Phase 2 verifies this by calling the deployed endpoint, not by checking that deployment succeeded.

Credential handling for a deployed agent is worth 10 minutes of an advanced workshop and is the natural answer to the question participants ask anyway.

**Structure.** Split into two notebooks so the halfway point is a working agent:

- `01_langgraph_agent.ipynb`: build the three tools, wire the supervisor, run the test questions in-notebook.
- `02_deploy_and_evaluate.ipynb`: wrap in `ResponsesAgent`, log to Unity Catalog, deploy, evaluate with MLflow against a fixed question set.

## Lab 6: Agent Memory

Memory writes go to the participant's Aura instance, which is where their domain graph already lives. That single fact is what makes this lab worth building, because memory nodes and fleet nodes end up in one database and can be traversed together.

Use [`neo4j-agent-memory`](https://github.com/neo4j-labs/agent-memory) on the self-hosted bolt path. `client.schema.adopt_existing_graph(...)` adopts the fleet graph as long-term memory, so remembered entities resolve to the real `Aircraft` and `Component` nodes from Lab 2 rather than creating parallel copies. Add `recall` and `remember` nodes on either side of the Lab 5 supervisor.

Demonstrations, in order of how well each answers "why does this need a graph":

| Demo | What it shows | Include |
|---|---|---|
| Memory joined to fleet data in one traversal | Which components three or more technicians asked about this week, and whether those are the ones actually failing. One Cypher across the conversation graph and the fleet graph | Required, headline |
| Reasoning reuse, measured | Successful Cypher and SQL replayed as few-shot exemplars. Run the eval set with memory off then on, compare tool calls, retries, tokens, latency, accuracy | Required |
| Correction with temporal invalidation | Correct an EGT redline, then traverse to what the agent used to believe and when it stopped | Required |
| Cross-session continuity | "Any vibration trends on that aircraft?" resolves after a restart | Required |
| Learned preferences | Role and fleet scope stored once, applied silently to later sessions including the generated SQL | Required |
| Shift handoff | Investigation findings attach to the component and a different technician picks them up | Recommended |
| Routing memory | The supervisor learns which tool answered similar questions, improving on the static prompt from Lab 5 | Recommended |
| Proactive briefing | Remembered interests joined to fresh telemetry on session start | Optional |
| GDS over the memory graph | Attention hotspots across the organization, written back to Delta. Ties in Appendix A | Stretch |

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

Two changes are required before it can be reused:

**Add a `databricks` embedding provider.** `config.py` currently offers `bge`, which runs `BAAI/bge-large-en-v1.5` locally through sentence-transformers, and `openai`. Lab 3 uses the `databricks-bge-large-en` Foundation Model endpoint. Same model, same 1024 dimensions, two different serving paths. Vectors from the two paths should be close, and "should be close" is not good enough for a vector index that `graphrag_node` queries. Adding a third provider that calls the same endpoint Lab 3 uses removes the question entirely and drops the sentence-transformers dependency from the serverless path.

**Add a flag to skip entity extraction.** The `setup` command also runs `SimpleKGPipeline` entity extraction, which needs an LLM API key and is not something Lab 5 depends on. The catch-up path needs CSVs, chunks, embeddings, and indexes. Nothing else.

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

For audiences that cannot commit to a full day, the same material splits cleanly: Labs 1 through 4 as a half-day foundation, where Part B is a reasonable ending on its own, and Labs 5 and 6 as a half-day advanced session for participants who completed the first.

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
- `lab/workshop.py`: names for the Lab 5 model, serving endpoint, secret scope, and the `databricks-meta-llama-3-3-70b-instruct` supervisor endpoint.
- `lab/workspace_init.sh` and `lab/lab_end.sh`: create and clean up the per-participant secret scope, following the pattern already used for the MCP credentials.
- `workshop-setup/README.md`: mark external MCP provisioning as required only for Lab 4 Part B.
- `images/lab-architecture-overview.*`: add a Lab 5 variant drawn against the participant's own Aura with three tools. Keep the existing diagram for Part B.

---

## Open Decisions

1. Whether provisioning creates one secret scope per participant or the workshop shares one scope with per-user keys. Shared is less to provision and leaks every participant's Aura password to every participant.
2. Whether Lab 5 deployment to Model Serving is required or optional. It is the right lesson and it is also the most likely place for a room of 30 people to hit a workspace limit. If optional, the in-notebook path still needs the Genie credential to work as the participant, which it does.
3. When the local MCP section lands in Lab 5. Proposed as a future section rather than first release, since it is the part most likely to behave differently on serverless compute and Lab 5 should ship without waiting on it.
4. How long Part B stays maintained. It is optional now, so a break is survivable, but it still requires a live AgentCore server, valid OAuth2 M2M credentials, and a loaded reference instance. Worth setting a review date rather than deciding today.

---

## Implementation Plan

### Goal

A participant can finish Lab 6 having used only the Aura instance they created in Lab 1, with Lab 4 Part B and all MCP material intact and marked optional.

### Assumptions

- The Unity Catalog volume holds everything the catch-up loader needs, including the maintenance manual that Lab 3 notebook 01 chunks.
- Aura Free capacity covers the fleet graph, the manual chunks with embeddings, and one participant's memory graph together. To be measured in Phase 0, not assumed past it.
- Databricks serverless notebooks can open a bolt connection to Aura. Lab 2 already relies on this, so it is established rather than assumed.
- Whether `neo4j-agent-memory` accepts Databricks Foundation Model endpoints for its embedding and LLM providers is a hypothesis, not a fact. Phase 0 settles it.
- Whether a `uv` package installs and runs from a serverless notebook cell is unverified. If it does not, the fallback is to call `populate_aircraft_db` as a job on classic compute, or to vendor its loader module into the notebook. The embedding provider fix matters either way.
- Vocareum participants may lack permission to create their own secret scope. `lab/lab_end.sh` and `vocareum/SETUP_GUIDE.md` show scopes being created by provisioning rather than by users, so plan for provisioning to create one scope per participant.

### Locked Decisions

| Decision | Reasoning | Dropped |
|---|---|---|
| LangGraph for Lab 5 | Genie, MCP, and MLflow integrations already exist on Databricks, and the supervisor pattern maps onto what participants configured in Part B | OpenAI Agents SDK, Pydantic AI, bare `ResponsesAgent` tool loop |
| Direct bolt driver for the Lab 5 Neo4j tools | Same three credentials as Labs 1 through 3, no per-participant server to host | Per-participant MCP server, shared MCP for the required path |
| `neo4j-agent-memory` on the self-hosted bolt path | Memory lands in the participant's own graph, so `adopt_existing_graph` can link memory to real fleet nodes | Hosted NAMS backend, which stores memory outside their Aura and breaks the headline demo |
| Part B and all MCP material stay in place | Part B is a genuine Databricks selling point and a working safety net; MCP is where the integration is heading | Deleting Part B, moving it to an appendix, removing MCP references |
| Reuse `populate_aircraft_db` as the catch-up loader | It already produces Lab 3's schema and index names, so one code path stays correct instead of two agreeing by luck | Writing a fresh Spark Connector loader |
| One embedding path, `databricks-bge-large-en` | The loader and Lab 3 must write vectors the same way or `graphrag_node` returns nonsense against the shared index | Leaving the loader on local sentence-transformers and hoping the vectors match |
| `databricks-meta-llama-3-3-70b-instruct` as the supervisor model | Already the Lab 3 default, so one endpoint to verify per workspace | GPT OSS 120B from the Part B Playground steps, a second endpoint to depend on |

### Deliberately Not Doing

- Rewriting Labs 1, 2, or 3. Lab 3's README gets one note about notebook 01 becoming required. Nothing else changes.
- Building the local `mcp-neo4j-cypher` section in Lab 5. Sketched as a future section so Lab 5 ships without waiting on serverless subprocess behavior.
- Hardening memory for production. Multi-tenancy, PII handling, and retention policy each get a callout in Lab 6, not an exercise.
- Redesigning the Genie space. Part A is already good and is not part of this work.
- Touching Vocareum provisioning beyond adding the new object names to `lab/workshop.py`.

### Phases

**Phase 0: Prove the risky parts.** Status: Pending

The two items that can invalidate the plan. Everything after this is known-feasible engineering.

- [ ] Add a `databricks` embedding provider to `populate_aircraft_db/config.py` calling `databricks-bge-large-en`
- [ ] Add a flag to skip `SimpleKGPipeline` entity extraction
- [ ] Confirm `populate_aircraft_db` installs and runs from a serverless notebook cell, or pick the job or vendored fallback
- [ ] Loader takes an empty Aura instance to a complete fleet graph plus Document and Chunk nodes, embeddings, and the `maintenanceChunkEmbeddings` index
- [ ] Prove no embedder drift: embed the same chunk text through the loader path and through `Lab_3_Semantic_Search/data_utils.py`, compare cosine similarity
- [ ] Query the vector index with a `data_utils.py` query embedding against loader-written vectors and confirm the top hits are relevant
- [ ] Measure loader wall-clock time and Aura Free storage after a full load
- [ ] Spike the headline memory demo standalone: write memory against a loaded instance, run one Cypher joining conversation memory to maintenance history, judge the answer
- [ ] Confirm which embedding and LLM providers `neo4j-agent-memory` accepts on Databricks
- [ ] Confirm whether Vocareum participants can create a secret scope, or whether provisioning must create one per user

Completion criteria: the loader runs twice in a row without duplicating data, cross-path cosine similarity is high enough that retrieval quality is unchanged, and the memory spike either returns a good answer or is recorded as a no-go for Lab 6.

Note: generating embeddings for the manual chunks is the slow part and may push the loader past a comfortable in-lab runtime. If it does, pre-generate embeddings into the Unity Catalog volume and have the loader write them rather than compute them.

**Phase 1: Lab 5 core agent.** Status: Pending

- [ ] `genie_node` bound to the Part A Genie space
- [ ] `cypher_node` against a personal Aura instance over bolt
- [ ] `graphrag_node` lifted from the Lab 3 `VectorCypherRetriever` work, embedding queries with `databricks-bge-large-en`, vector retrieval only
- [ ] Supervisor node on `databricks-meta-llama-3-3-70b-instruct`, routing across all three, with the Part B routing prompt as the starting point
- [ ] `graphrag_node` degrades to a clear message rather than failing at import when the vector index is absent
- [ ] Optional hybrid retrieval exercise for participants who ran Lab 3 notebook 03
- [ ] `01_langgraph_agent.ipynb` runs the anchor question end to end across all three tools

Completion criteria: the anchor question about abnormal EGT, maintenance history, and the relevant manual procedure returns a correct answer in-notebook, and each of the four routing cases lands on the expected tool.

**Phase 2: Lab 5 ships.** Status: Pending

- [ ] `ResponsesAgent` wrapper with MLflow autologging
- [ ] Aura password sourced from a Databricks secret scope rather than a notebook literal
- [ ] Genie space and model endpoint declared as resources at log time so the serving principal gets a credential
- [ ] Serving principal confirmed to have access to the Unity Catalog tables behind the Genie space, not just to the space
- [ ] Logged to Unity Catalog and deployed to Model Serving
- [ ] MLflow evaluation against the fixed question set
- [ ] `02_deploy_and_evaluate.ipynb` and `Lab_5_LangGraph_Agent/README.md` complete

Completion criteria: the deployed endpoint answers one question per tool when called as the serving principal rather than as the notebook user, and the evaluation run produces a baseline the Lab 6 memory comparison can be measured against. A successful deploy is not the criterion. A successful Genie call through the endpoint is.

**Phase 3: Lab 6 memory.** Status: Pending, gated on the Phase 0 spike

- [ ] Memory client configured against the participant's Aura, with `adopt_existing_graph` resolving to real fleet nodes
- [ ] `recall` and `remember` nodes added around the Lab 5 supervisor
- [ ] The five required demos: fleet-joined traversal, reasoning reuse, correction with invalidation, cross-session continuity, learned preferences
- [ ] Memory off versus on evaluation harness reusing the Phase 2 baseline
- [ ] The two recommended demos, shift handoff and routing memory, if time allows

Completion criteria: the headline traversal returns a good answer, and the memory comparison shows a measurable difference in tool calls, tokens, or accuracy.

**Phase 4: Delivery readiness.** Status: Pending

- [ ] Full dry run of Labs 1 through 6 on a fresh Aura instance and a fresh workspace user
- [ ] Catch-up loader exercised from a deliberately incomplete Lab 2 state
- [ ] Reference instance fallback verified as a three-variable override
- [ ] Part B still works, with its optional banner in place
- [ ] Timings recorded against the suggested day structure

Completion criteria: one person completes the required path start to finish without the instructor intervening.

### What Runs in Parallel

Three tracks. Track C is independent of all code and can start immediately.

| Track | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|---|
| **A. Engineering** | Catch-up loader | Three tools plus supervisor | Deploy and evaluate | Memory nodes and demos | Dry run |
| **B. Memory research** | Headline demo spike, provider check | idle | idle | joins Track A | Dry run |
| **C. Content and infra** | Lab 4 banners and Part A handoff | Repo docs, `agenda.md`, `lab/workshop.py` | Lab 5 architecture diagram, eval question set | Lab 6 README | Timing capture |

What actually blocks what:

- The catch-up loader does not block building the Lab 5 tools. Build the tools against an already-loaded instance. The loader is a prerequisite for participants, not for development.
- The memory spike does not block Lab 5 at all. It needs a loaded graph and nothing else, so it runs alongside the entire Lab 5 build and delivers its go/no-go before Lab 6 starts.
- The whole of Track C is documentation and naming. None of it waits on code.
- The Lab 5 eval question set can be written on day one. It is a list of questions and expected routes.
- Only Phase 3 has a hard dependency on Phase 1, because the memory nodes attach to the Lab 5 supervisor.

Parallelism caveat: Tracks A and B both write to Aura, and the memory spike puts memory nodes into a graph the loader tests are trying to keep clean. Give each track its own Aura instance. With one person doing all three tracks, the tracks collapse to sequential and Phase 0 is still the right starting point.

### If Phase 0 Fails

- Loader too slow: pre-generate embeddings into the volume, or split the loader so the fleet graph loads in-lab and the Lab 3 artifacts load only for participants who skipped Lab 3.
- Embedder drift confirmed between the two paths: rebuild the vector index from the loader's own embeddings so one writer owns the index, and have `graphrag_node` embed through the same provider. One writer, one reader, one model.
- `populate_aircraft_db` will not run on serverless: vendor its loader module into the catch-up notebook. The embedding provider fix carries over unchanged, and the schema and index names stay identical.
- Aura Free too small: move memory to a second free instance and accept losing the fleet-joined traversal demo, or drop Lab 6 to the take-home path.
- Memory spike returns a weak answer: hold Lab 6 and ship Labs 4 and 5 alone. That is already a large improvement, and it is the majority of the value in this proposal.
