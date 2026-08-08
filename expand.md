# Proposal: Restructure Labs 4 through 6 for an Extended Advanced Workshop

A proposal to make Lab 4 Part B optional, add a LangGraph lab that connects the Genie space to the participant's own Aura instance, and add a memory lab. The result is a longer workshop where every required lab builds on the graph the participant loaded themselves.

**This document supersedes `proposed-outline.md` and `workshop-improve.md`.** Both of those propose restructures that end at Lab 4, and both predate the decision to add Labs 5 and 6. Where they conflict with this document, this document wins. Their still-valid parts, the "lead with the why" opening and the live demo of the finished agent before Lab 1, are carried into the Suggested Day Structure below. Each gets a superseded banner rather than deletion, since the reasoning in them is worth keeping.

---

## Status

Last updated 2026-08-08.

| Track | Where it is |
|---|---|
| **A. Engineering** | Phase 0 catch-up loader **done and verified against a live Aura instance.** Phase 1 starting |
| **B. Memory research** | Phase 0 memory spike **done and measured against a live Aura instance. Verdict: GO, with three hard conditions.** Pin `neo4j-agent-memory==0.5.0` and install `httpx`, adopt `Aircraft` only, write with `extraction_mode="explicit"`. Full report in `worklog/memory-spike.md` |
| **C. Content and infra** | Repository documentation complete. Two documents that fall out of the AuraDB Free decision are in flight, `Lab_1_Aura_Setup/Aura_Free_Trial.md` and `Lab_2_Databricks_ETL_Neo4j/02_gds_knn_aircraft.ipynb`. The Lab 5 architecture diagram, the Antora site in `site/`, the slides in `slides/`, and the Vocareum courseware bundle are deferred by decision rather than outstanding |

**Done**

- The `databricks` embedding provider, the `--skip-extraction` flag, and every documentation and naming change in the Concrete Changes list below except the diagram.
- Verified end to end on 2026-08-08: `populate-aircraft-db setup --skip-extraction` with `EMBEDDING_PROVIDER=databricks` took an empty Aura instance to a complete graph in **4 minutes 23 seconds** with no OpenAI or Anthropic key present. Result: 155,520 Readings, 14,543 Flights, 5,541 Delays, 612 Components, 290 Chunks, 288 Sensors, 286 MaintenanceEvents, 144 Systems, 57 Removals, 40 Airports, 36 Aircraft, 5 Documents. All 290 chunk embeddings at 1024 dimensions. `maintenanceChunkEmbeddings` ONLINE and returning results. Lexical graph identical in shape to the `SimpleKGPipeline` output: `FROM_DOCUMENT` 290, `NEXT_CHUNK` 285, `APPLIES_TO` 36 cross-links to Aircraft, and both `Document` and `Chunk` carrying the `__KGBuilder__` label the library writes.

- **Idempotency confirmed.** A second full run over the already-loaded instance finished in 4 minutes 9 seconds and left node counts unchanged at 177,362 with chunks still at 290, so nothing duplicated. It also reports `[OK] Verification passed.` with zero warnings now that the extraction checks stand down when extraction was skipped, and states in one line that they were not verified.
- Embedder drift measured and **retired**. The loader path and the Lab 3 path return cosine 1.0000000000 on the same text, because both now call the same Foundation Model endpoint through the same client. A `data_utils.py` query embedding against loader-written vectors returns the right chunks at 0.85.
- Four open questions settled on 2026-08-08: the development instance split, `VectorCypherRetriever` for `graphrag_node`, the memory spike running in parallel with Phase 1, and deterministic `OperatingLimit` loading. Each is recorded in place below.

- **Deterministic `OperatingLimit` loading done and verified**, measured on `f024ea61`. `OperatingLimit` 20, matching the CSV row count exactly. `HAS_LIMIT` 288, one per sensor across 36 aircraft. Two consecutive full runs differ on zero of 44 metrics, so the CSV path is idempotent. The `limit_retriever` cell from Lab 3 notebook 02, run with the notebook's query and question verbatim against a `--skip-extraction` graph, returns populated results. `verify` reports zero warnings on the skip path.

- **Sensor unit strings normalized to the manual limit tables, done and verified on `f024ea61`.** `Sensor.unit` in `workshop-setup/aircraft_digital_twin_data/nodes_sensors.csv` now uses the same string as `OperatingLimit.unit` for the same physical quantity, so the two join on a plain string comparison. `EGT` moved from `C` to `°C` and `N1Speed` from `rpm` to `% RPM`. `Vibration` at `ips` and `FuelFlow` at `kg/s` were already correct. Measured after a reload: `WHERE s.unit = ol.unit` returns **288** and `WHERE s.unit <> ol.unit` returns **0**. Setup ran 4 minutes 35 seconds and exited 0, and Ruff reported 14 findings before the change and 14 after. `_SENSOR_TYPES` at `workshop-setup/populate_aircraft_db/src/populate_aircraft_db/generator/fleet.py:75` carries the same strings, so a regenerated fleet cannot reintroduce the old units. Documentation followed in `Lab_4_Compound_AI_Agents/PART_A.md`, `Lab_4_Compound_AI_Agents/PART_B.md`, `Lab_2_Databricks_ETL_Neo4j/data-exploring.md`, and `workshop-setup/docs/MANUAL_SETUP.md`.

- **Memory spike done, 2026-08-08, against `1a2c98cc`. Verdict GO with three hard conditions.** The headline demo works and is compelling, Databricks Foundation Model endpoints satisfy the library's provider Protocols with no library change, and the version is pinned at `neo4j-agent-memory==0.5.0`. The three conditions are pin 0.5.0 and install `httpx` explicitly, adopt `Aircraft` only, and write with `extraction_mode="explicit"`. Each is a Phase 3 checklist item below, and each is a silent failure rather than a loud one. Full report in `worklog/memory-spike.md`.

- **Aura node budget measured. The cap binds the admin reference instance, not participants.** What was measured is `f024ea61`, the admin reference instance loaded by `populate-aircraft-db setup`: **177,382 nodes, 88.7 percent of the 200,000 node cap**. 155,520 of those are `Reading` nodes. **Lab 2 loads no `Reading` nodes and never has**, so no participant graph resembles that figure. A participant who finishes Labs 1 through 3 holds about **21,613 nodes, 10.8 percent of the cap**, with roughly 178,000 nodes of headroom. Memory costs about 20 nodes per participant per session, so Lab 6 fits with room to spare. Nodes bind before relationships: 177,382 of 200,000 nodes is 88.7 percent, while 207,605 of 400,000 relationships is 51.9 percent, and `HAS_READING` alone is 74.9 percent of all relationships. **The class uses AuraDB Free, decided 2026-08-08, so the caps do apply.** They are 200,000 nodes and 400,000 relationships, confirmed current from `neo4j.com/cloud/platform/aura-graph-database/faq/`, fetched 2026-08-08. Open Decisions 5, 6, and 7 are all closed. Two items fall out of the tier decision, both now in flight rather than open: Lab 1's setup document points at the wrong button, and the Lab 2 GDS notebook does not run on Free. Full analysis in `worklog/aura-node-budget.md`.

**Development instances**

Two Aura instances, one per track, so neither track's writes show up in the other's tests.

| Instance | Track | Credentials |
|---|---|---|
| `f024ea61` | A. Lab 5 development, already loaded | `workshop-setup/.env` |
| `1a2c98cc` | B. Memory spike | `workshop-setup/.env.memory` |

Instance `f024ea61` is reset with `populate-aircraft-db clean` and reloaded whenever a test needs a clean graph.

**In flight, 2026-08-08**

Three items are being worked right now. None of them is verified, and none should be read as measured.

- **N1Speed reading values are absolute rpm while its operating limits are percentages.** The unit normalization exposed this rather than caused it. `nodes_readings.csv` N1Speed values run 2500.67 to 5282.73 with a mean of 4648, and the N1Speed `OperatingLimit` rows are 92, 100, and 104 percent. `Sensor.unit` and `OperatingLimit.unit` now agree as strings, so any query comparing a reading value against `ol.maxValue` for N1Speed compares rpm against percent and flags every sensor as exceeding. The root cause is data generation, not labeling: `n1_baseline` in `workshop-setup/populate_aircraft_db/src/populate_aircraft_db/generator/specs.py` is around 2600 for A220 and around 4700 for CFM and LEAP. Being fixed now.
- **`Lab_1_Aura_Setup/Aura_Free_Trial.md` is being rewritten to point at AuraDB Free.** It currently tells participants to click **Start 14-day free trial**, which provisions an AuraDB Professional Trial that expires mid-course.
- **`Lab_2_Databricks_ETL_Neo4j/02_gds_knn_aircraft.ipynb` is getting a note at the top.** Open Decision 7 is decided: the notebook stays, and the note says it cannot run on AuraDB Free and should be skipped unless the participant has their own AuraDB Professional instance.

**Next**

Phase 1 is in flight, building the three Lab 5 tools against the already-loaded `f024ea61`. The memory spike has landed its go/no-go ahead of schedule, so Lab 6 is unblocked and Phase 3 starts from measured numbers rather than hypotheses.

Two Phase 0 items can still invalidate parts of the plan. Whether the loader runs from a serverless notebook cell is one, and it does not block Phase 1, which builds against an already-loaded instance. Whether AuraDB Free tolerates 59 indexes and six vector indexes is the other, and it is the one remaining item that could still flip Lab 6 to no-go. The tier itself is settled: the class uses AuraDB Free, so the 200,000 node and 400,000 relationship caps apply.

The nearest thing to that list is the N1Speed magnitude fix in the In flight block above. It does not block Phase 1 either, since no Lab 5 tool compares a reading value against an operating limit, but it does have to land before any lab or demo asks whether a sensor is over its N1Speed limit.

Labs 5 and 6 get written before anything that describes them. The Vocareum courseware bundle, the Antora site in `site/`, and the slides in `slides/` are rewritten afterward, in one pass against what shipped. See Sequencing under the Implementation Plan.

**Known state, not bugs**

- `vocareum/courseware/data/Lab_3_Semantic_Search/` holds tracked copies of the three Lab 3 notebooks and `data_utils.py`. They were byte-identical to the top-level `Lab_3_Semantic_Search/` files until the 2026-08-08 secret-scope change, which touched only the top-level copies. The two now diverge. `lab/` uses symlinks to the top-level directories, so that path picks the change up on its own. The `vocareum/courseware/data/` path does not, because it is a copy. `neo4j-databricks-workshop.dbc` and `neo4j-databricks-workshop.dat` are binary bundles of the same files and need rebuilding at the same time. The divergence is deliberate: the bundle gets resynced once, in Phase 4, after the lab content has stopped moving, rather than after every edit.
- The Antora site in `site/` and the slides in `slides/` still end the workshop at Lab 4, and both are deferred to Phase 5 for the same reason. Until that pass lands, a push to `main` publishes a site that contradicts the repository READMEs.
- Two maintenance manuals contradict themselves on the N1Speed unit and were deliberately left alone during the unit normalization. `MAINTENANCE_A220.md:146` and `MAINTENANCE_E190.md:143` label N1Speed `rpm` in their sensor inventory tables, while their own limit tables at `MAINTENANCE_A220.md:286` and `MAINTENANCE_E190.md:270` say `% RPM` with percentage values. The limit tables win, and the data was normalized to them.
- Two stale figures in `workshop-setup/docs/MANUAL_SETUP.md` were also left alone. Line 135 gives an N1Speed typical range of 2000-3500 against an actual 2500-5283, and line 133 gives EGT 600-750 against an actual 616-731. The N1Speed row is worth correcting only after the magnitude fix in the In flight block lands, since that fix changes the numbers the row should carry.

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

Use [`neo4j-agent-memory`](https://github.com/neo4j-labs/agent-memory), pinned at `0.5.0`, on the self-hosted bolt path. `client.schema.adopt_existing_graph(...)` adopts the fleet graph as long-term memory, so remembered entities resolve to the real `Aircraft` nodes from Lab 2 rather than creating parallel copies. Add `recall` and `remember` nodes on either side of the Lab 5 supervisor.

**Adopt `Aircraft` only.** The spike measured `adopt_existing_graph` overwriting `type` unconditionally, so adopting `System`, `Component`, `Sensor`, or `Document` destroys the `type` values Lab 2 and Lab 4 filter on. Detail and the recovery cost are in the defect subsection below. The headline demo needs `Aircraft` and nothing else, so this costs the lab nothing.

Demonstrations, in order of how well each answers "why does this need a graph". **Hands-on** means the participant writes and runs it. **Demo** means the notebook ships it complete and the participant runs the cell and reads the output, with the instructor talking over it.

| Demo | What it shows | Include |
|---|---|---|
| Memory joined to fleet data in one traversal | Which aircraft two or more technicians asked about this week, and whether those are the ones actually failing. One Cypher across the conversation graph and the fleet graph | Hands-on, headline |
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

### The headline demo, measured

Built and run in the Phase 0 spike against `1a2c98cc`. Adoption of 36 `Aircraft` took 3.1 seconds and reported `migrated=36 already=0 skipped=0`. Five technicians, five sessions, ten messages. The joining Cypher binds `ac` in the memory half and reuses the same node in the fleet half, so there is no join key, no federation, and no second query. It runs in 0.6 to 0.7 seconds.

The result is a genuine "neither source alone" answer, and `N10011` is the reason it lands.

Fleet graph alone, ranked by criticality, puts `N10011` **last of six**:

```
N10004 events=23 critical=17
N10021 events=23 critical=16
N10020 events=22 critical=13
N10027 events=18 critical=13
N10000 events=18 critical=12
N10011 events=21 critical=11
```

Memory alone, ranked by attention, puts it **joint first**:

```
N10011 technicians=3 mentions=3
N10004 technicians=3 mentions=3
N10021 technicians=2 mentions=2
N10027 technicians=1 mentions=1
N10020 technicians=1 mentions=1
```

The joined query is the only one of the three that surfaces the point. Three technicians on three shifts each pulled the EGT trend on `N10011` independently, none of them knowing the others had, on an aircraft the severity model ranks at the bottom of the page. That contrast is the demo. The inverse reads well too: `N10020` and `N10027` carry 13 critical events each and one technician each has looked at them, which is the reverse alarm.

The warmup exercise is cross-session semantic recall. `client.short_term.search_messages("EGT margin trending down", limit=3)` returned the three `N10011` messages from three different technicians in three different sessions, with no shared vocabulary beyond "EGT", in 3.4 to 5.0 seconds. The vector search runs on `databricks-bge-large-en` embeddings through the adapter. Participants will see a Neo4j deprecation warning naming `db.index.vector.queryNodes`; it works on `5.27-aura`, and one sentence of lab text prevents the support question.

### Upstream defect in 0.5.0: automatic extraction silently drops `MENTIONS` edges

This is why condition three exists, and it would have sunk Lab 6 without ever printing an error.

In released 0.5.0, `_extract_and_link_entities` generates a `uuid4`, runs `MERGE (e:Entity {name, type})` whose `ON MATCH SET` never assigns `e.id`, discards the `RETURN e`, then links with `MATCH (e:Entity {id: $entity_id})` on the throwaway uuid. When the `MERGE` matches an existing node, that node keeps its own id, both `MATCH` clauses cannot bind, and the write is a no-op. No exception, no warning, no edge.

Two consequences. Every entity adopted from the fleet graph is unreachable from memory, because adoption gives `Aircraft` an id of `aircraft:N10004` and the uuid never matches it. Every repeat mention of any entity is lost, including entities the library created itself, so only the message that first creates an entity gets an edge. A ten-message auto-extraction run dropped all ten tail numbers. `MENTIONS` is the exact edge the headline query traverses.

**The workaround is `extraction_mode="explicit"` with `EntityRef`.** It routes through `_link_explicit_mentions`, which resolves by id, then by name and type, then by name, and returns the resolved id read back from the database, so the link lands on the adopted node. Verified at 10 of 10 tail numbers linked. It is also the better production pattern, since an agent normally knows which entities its tools touched and can pass them rather than pay an LLM to rediscover them, and it removes one LLM call per message from the lab's critical path.

**The upstream fix is one line:** read the id back from the `RETURN e` that `build_create_entity_query` already produces, and link with that instead of the uuid. Worth filing. Ryan already has 5 commits in that repository and William Lyon owns 373 of them, so the internal channel is open without an introduction. Tracked as a Phase 3 item.

**Related, and a second reason to prefer explicit mode: label collision.** Entities the library creates take a label derived from their type, so an entity of type `SYSTEM` becomes `:System:Entity` and `COMPONENT` becomes `:Component:Entity`, colliding with the fleet's own labels. During the auto-extraction run the `System` label count went from 144 to 148 and `Component` from 612 to 613, with names like `Engine`, `hydraulic`, and `turbine`. A `MATCH (s:System)` in Lab 2 or Lab 4 would then return conversational artifacts alongside real systems.

### Lab pacing, measured

Steady-state Databricks endpoint latency from a laptop, after warmup: **1.85 seconds per `databricks-bge-large-en` embedding call** and **1.84 seconds per short `databricks-meta-llama-3-3-70b-instruct` call**. Those set the floor.

That gives **5.6 seconds per message in explicit mode** and **9.2 seconds with automatic extraction**, so explicit mode saves about 3.6 seconds per message by skipping the extraction LLM call. First connect plus schema creation on an empty schema costs 22.4 seconds, once per database.

The consequence for lab design: a ten-message seed script takes about a minute and is fine, but participants must not write memory in a loop over dozens of messages in a notebook cell. Seed the conversation history in a setup step, or batch through `add_messages`. Phase 3 already requires timing each hands-on demo against its share of the 75 minutes, and these are the per-call numbers that timing has to add up from.

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

Skipping the extractor did leave one gap, and it is being closed at the source rather than documented as a limitation. No extractor meant no `OperatingLimit` nodes, so Lab 3 notebook 02's `limit_retriever` cell had nothing to return on a catch-up graph. The fix: the operating limits are extracted from the five maintenance manuals once, into a checked-in CSV, and the loader writes `OperatingLimit` nodes and `HAS_LIMIT` edges from it like any other node CSV. Deterministic, no LLM, no key. The catch-up path then produces the same graph the extraction path does for this entity type. **Done and verified on `f024ea61`:** `OperatingLimit` 20, matching the CSV row count, `HAS_LIMIT` 288, one per sensor across 36 aircraft, zero differences across all 44 metrics between two consecutive full runs, `verify` clean on the skip path, and the `limit_retriever` cell returning populated results when run with the notebook's own query and question.

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
├── README.md                     # Also holds the pinned-version research answers
├── 01_memory_setup.ipynb         # Memory client, adopt Aircraft only, recall/remember nodes
├── 02_memory_demos.ipynb         # The demonstration set
├── databricks_providers.py       # DatabricksEmbeddings, DatabricksLLM, ~130 lines, lab-provided
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
- `workshop-setup/aircraft_digital_twin_data/nodes_sensors.csv` and `workshop-setup/populate_aircraft_db/src/populate_aircraft_db/generator/fleet.py`: `Sensor.unit` normalized to the maintenance manual limit strings, `°C` and `% RPM`, so `Sensor.unit` and `OperatingLimit.unit` join. Done and verified. The unit strings that appear in `Lab_4_Compound_AI_Agents/PART_A.md`, `Lab_4_Compound_AI_Agents/PART_B.md`, `Lab_2_Databricks_ETL_Neo4j/data-exploring.md`, and `workshop-setup/docs/MANUAL_SETUP.md` were updated in the same pass.
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
5. ~~Whether Lab 2 should load fewer `Reading` nodes.~~ **Closed 2026-08-08: the question rested on a false premise. Lab 2 loads no `Reading` nodes.**

   `Lab_2_Databricks_ETL_Neo4j/01_aircraft_etl_to_neo4j.ipynb` loads nine node labels and twelve relationship types. `Reading` is not among them, the string "reading" appears zero times in that file, and `git log -S"nodes_readings" -- Lab_2_Databricks_ETL_Neo4j/` returns no commits. The only code that creates `Reading` nodes is `populate_aircraft_db setup`, the admin catch-up loader.

   The 177,382-node figure that framed this decision is the admin reference instance `f024ea61`, which carries 155,520 `Reading` nodes no participant has. A participant finishing Labs 1 through 3 holds about 21,613 nodes, 10.8 percent of the 200,000 cap, with roughly 178,000 nodes of headroom. There is no mid-lab cap risk, no recovery-path problem, and no Lab 2 content decision to make.

   A smaller recommendation survives, for a different reason: drop `Reading` and `HAS_READING` from `populate_aircraft_db`, because nothing in the workshop queries them. **Decided 2026-08-08, take Option A.** It is a Phase 0 checklist item below. Full analysis in `worklog/aura-node-budget.md`.
6. ~~Which Aura tier the class actually gets.~~ **Decided 2026-08-08: the class uses AuraDB Free. The 200,000 node and 400,000 relationship caps apply and every capacity number in this plan is measured against them.**

   Two shipped documents contradicted each other. `Lab_1_Aura_Setup/Aura_Free_Trial.md` instructs participants to click **"Start 14-day free trial"**, which per Neo4j's FAQ provisions an **AuraDB Professional Trial**, sized by RAM with no node cap. `Lab_2_Databricks_ETL_Neo4j/02_gds_knn_aircraft.ipynb` warns that GDS "is not included in the AuraDB Free tier, so this notebook will not run on a free instance." The GDS notebook was right about the tier. Lab 1's instructions are the wrong ones.

   The caps are comfortable on the required path. A participant finishing Labs 1 through 3 holds about 21,613 nodes, 10.8 percent of the cap, and memory adds about 20 nodes per session, so Lab 6 fits with roughly 178,000 nodes of headroom.

   Two consequences follow, both are work rather than questions, and both are in flight as of 2026-08-08:

   - `Lab_1_Aura_Setup/Aura_Free_Trial.md` must instruct participants to create an **AuraDB Free** instance rather than start the 14-day Professional trial. A participant who takes the trial button gets a different tier from the one every other document assumes, and it expires mid-course. Being rewritten now.
   - `Lab_2_Databricks_ETL_Neo4j/02_gds_knn_aircraft.ipynb` does not run on Free, by its own warning. Open Decision 7 settled what happens to it: the notebook stays, with a note at the top. Being added now.

   The Phase 0 item on whether the class tier tolerates 59 indexes and six vector indexes now has a named tier to test against: AuraDB Free.
7. ~~What happens to the Lab 2 GDS notebook on AuraDB Free.~~ **Decided 2026-08-08: `02_gds_knn_aircraft.ipynb` stays, with a note at the top.** The note says the notebook cannot run on AuraDB Free and should be skipped unless the participant has their own AuraDB Professional instance. Cutting it would delete working material for the audience that does have Professional, and the tier warning already in the notebook is the thing participants miss rather than the thing they lack. Being implemented 2026-08-08. Nothing in Labs 5 or 6 depends on it.

---

## Implementation Plan

### Goal

A participant can finish Lab 6 having used only the Aura instance they created in Lab 1, with Lab 4 Part B and all MCP material intact and marked optional.

### Sequencing

Write the new labs first. Lab 5, then Lab 6. Only after they land does anything downstream get rewritten: the Vocareum courseware bundle, the Antora site in `site/`, and the slides in `slides/`. Those three surfaces describe the course, so rewriting them before the course exists means writing them twice, once against a proposal and once against what shipped.

Order: Lab 5, then Lab 6, then the courseware bundle in Phase 4, then the site and the slides together in Phase 5.

### Assumptions

- The Unity Catalog volume holds everything the catch-up loader needs, including the maintenance manual that Lab 3 notebook 01 chunks.
- ~~Aura Free capacity covers the fleet graph, the manual chunks with embeddings, and one participant's memory graph together.~~ **Measured 2026-08-08, and capacity is not a constraint on the required path.** What was measured is the admin reference instance `f024ea61`, not a participant graph: 177,382 nodes, 88.7 percent of the 200,000 node cap, and 207,605 relationships, 51.9 percent of the 400,000 relationship cap. 155,520 of those nodes are `Reading` nodes that `populate-aircraft-db setup` writes, that Lab 2 does not load, and that no lab query reads. A participant after Labs 1 through 3 holds about 21,613 nodes, 10.8 percent of the cap, with roughly 178,000 nodes of headroom. Memory costs 1 node, 3.5 relationships, and about 20 properties per message, so ten messages added 20 nodes, which the headroom absorbs many times over. Storage is not a constraint either: `apoc.monitor.store()` is blocked on Aura, so bytes were estimated rather than read, and the dominant per-message cost is the 1024-element `Message.embedding` at roughly 8 KB, which puts a thirty-participant class at about 12 MB. The class uses AuraDB Free, so the 200,000 node cap does apply, and 10.8 percent of it is what the required path spends.
- Databricks serverless notebooks can open a bolt connection to Aura. Lab 2 already relies on this, so it is established rather than assumed.
- ~~Whether `neo4j-agent-memory` accepts Databricks Foundation Model endpoints for its embedding and LLM providers is a hypothesis, not a fact.~~ **Settled 2026-08-08, and it is a pass.** The library hard-codes no provider. `llm/protocol.py` defines `EmbeddingProvider`, `LLMProvider`, and `StructuredExtractor` as `@runtime_checkable` Protocols, and `MemorySettings.embedding` and `.llm` are typed `Any` with a validator that accepts any instance satisfying a Protocol. Nothing subclasses anything. About 130 lines of adapter binds Databricks Foundation Model endpoints through `mlflow.deployments`, verified live against `databricks-bge-large-en` and `databricks-meta-llama-3-3-70b-instruct`.
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
| Pin `neo4j-agent-memory==0.5.0`, install `httpx` alongside it, adopt `Aircraft` only, and write with `extraction_mode="explicit"` | The three conditions the Phase 0 spike attached to its GO. Each was measured, and each fails silently rather than loudly, so none of them can be left to a default | Floating the version, adopting every fleet label, relying on automatic LLM entity extraction |
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

**Phase 0: Prove the risky parts.** Status: In progress. The loader is done and verified. The memory spike ran against its own Aura instance `1a2c98cc` and came back GO with three conditions on 2026-08-08.

The two items that can invalidate the plan. Everything after this is known-feasible engineering.

- [x] Add a `databricks` embedding provider to `populate_aircraft_db/config.py` calling `databricks-bge-large-en`. Verified returning 1024 dimensions
- [x] Add a flag to skip `SimpleKGPipeline` entity extraction. Shipped as `--skip-extraction` on both `setup` and `enrich`. It bypasses `SimpleKGPipeline` and assembles the library's own `FixedSizeSplitter`, `TextChunkEmbedder`, `LexicalGraphBuilder`, and `Neo4jWriter`, so the Document and Chunk nodes are the ones the full path writes. It does not write `OperatingLimit` nodes and `HAS_LIMIT` edges, which the next item moves out of extraction and onto a CSV
- [x] Write `OperatingLimit` nodes and `HAS_LIMIT` edges deterministically. Shipped as a checked-in CSV the loader writes like any other node CSV. No LLM and no API key on the catch-up path. Measured on `f024ea61`: `OperatingLimit` 20, matching the CSV row count exactly, and `HAS_LIMIT` 288, one per sensor across 36 aircraft. Two consecutive full runs differ on zero of 44 metrics, and `verify` reports zero warnings on the skip path
  - [x] Verified by running the `limit_retriever` cell from Lab 3 notebook 02 against a graph loaded with `--skip-extraction` and getting results. **Run with the notebook's query and question verbatim, and it returns populated results.** A successful load was not the criterion; a non-empty `limit_retriever` result was
- [x] **Normalize `Sensor.unit` to the manual limit tables so it joins `OperatingLimit.unit`.** `EGT` from `C` to `°C` and `N1Speed` from `rpm` to `% RPM` in `workshop-setup/aircraft_digital_twin_data/nodes_sensors.csv`, with `_SENSOR_TYPES` at `workshop-setup/populate_aircraft_db/src/populate_aircraft_db/generator/fleet.py:75` changed to match so the generator cannot reintroduce the old strings. `Vibration` and `FuelFlow` were already correct. Verified on `f024ea61`: 288 sensors join on `s.unit = ol.unit` and 0 do not. Setup ran 4 minutes 35 seconds and exited 0, and Ruff was unchanged at 14 findings
- [ ] **Fix N1Speed reading magnitudes.** The readings are absolute rpm, 2500.67 to 5282.73 with a mean of 4648, and the N1Speed operating limits are percentages, 92, 100, and 104. Matching units as strings therefore made the mismatch worse rather than better: a comparison against `ol.maxValue` now looks valid and flags every sensor. The fix is in `workshop-setup/populate_aircraft_db/src/populate_aircraft_db/generator/specs.py`, where `n1_baseline` is around 2600 for A220 and around 4700 for CFM and LEAP. In flight 2026-08-08, unverified
- [ ] Confirm `populate_aircraft_db` installs and runs from a serverless notebook cell, or pick the job or vendored fallback
- [x] Loader takes an empty Aura instance to a complete fleet graph plus Document and Chunk nodes, embeddings, and the `maintenanceChunkEmbeddings` index. Verified 2026-08-08 against an empty instance. Counts and timing in the Status section above
- [x] Prove no embedder drift. **Cosine 1.0000000000 on both test strings**, measured 2026-08-08 by embedding the same text through `populate_aircraft_db.pipeline.DatabricksEmbeddings` and `Lab_3_Semantic_Search/data_utils.DatabricksEmbeddings` in one process. Not close, identical. Both call `mlflow.deployments` against `databricks-bge-large-en` with the same request body, so there is one serving path rather than two. The drift risk is gone rather than mitigated
- [x] Query the vector index with a `data_utils.py` query embedding against loader-written vectors and confirm the top hits are relevant. Verified: "What is the procedure for an EGT exceedance?" returned EGT overheat and engine troubleshooting chunks at 0.8488, 0.8462, and 0.8335
- [x] Measure loader wall-clock time. 4 minutes 23 seconds for the full load including 290 embedded chunks. Comfortably in-lab, so the pre-generated-embeddings fallback is not needed
- [x] Measure Aura storage after a full load. **The measurement is of the admin reference instance `f024ea61`, not of a participant graph, and neither nodes nor storage constrain the required path.** That instance holds 177,382 nodes, 88.7 percent of the 200,000 cap, and 207,605 relationships, 51.9 percent of the 400,000 cap, plus 764,474 properties, 59 indexes, and 24 constraints. 155,520 of the nodes are `Reading` nodes that `populate-aircraft-db setup` writes and Lab 2 does not load. A participant finishing Labs 1 through 3 holds about 21,613 nodes, 10.8 percent of the cap, with roughly 178,000 nodes of headroom. Memory adds 1 node, 3.5 relationships, and about 20 properties per message. Byte-level storage could not be read because `apoc.monitor.store()` is blocked on Aura, so it was estimated from the 1024-element `Message.embedding` at roughly 8 KB, putting a thirty-participant class at about 12 MB. Full breakdown in the Status section and `worklog/aura-node-budget.md`
- [ ] **Drop `Reading` and `HAS_READING` from `populate_aircraft_db`. Decided 2026-08-08, take Option A from `worklog/aura-node-budget.md`.** This is work to do, not an option to weigh. The reason is that nothing reads them, not the cap: fourteen files across five labs, the verifier, and the sample-query CLI were swept, and zero queries traverse `HAS_READING`. Lab 4's own Neo4j agent description omits `Reading` from "DATA AVAILABLE" and lists "Time-series sensor readings" under "DO NOT USE FOR", the Lab 5 routing table above sends the one reading question to Genie, and `HAS_READING` appears zero times in this document. The defect it fixes: an admin debugging a participant issue against the reference instance is debugging a graph 155,520 nodes larger than any participant has. Dropping them takes the reference instance from 177,382 to 21,862 nodes and from 207,605 to 52,085 relationships. Work is confined to `loader.py`, `schema.py`, `agent_samples.py`, and two `populate_aircraft_db` documents, about 75 minutes, with zero changes to Lab 2 notebooks, `nodes_readings.csv`, Lab 3, Lab 4, or the verifier. The runner-up option, per-sensor summary statistics as `Sensor` properties, lost because `gold_sensor_health` in `lab/courseware/dlt_fleet_etl.py` already publishes those exact statistics from the authoritative Delta table, so a Neo4j copy is a second answer that drifts. `setup` uses `MERGE`, so an in-place rerun leaves the existing `Reading` nodes in place; run `clean` first, or delete them in batched transactions
- [x] Spike the headline memory demo standalone. **It works, and it is compelling.** One Cypher binds `ac` in the memory half and reuses the same node in the fleet half, running in 0.6 to 0.7 seconds. The result: the fleet graph ranks `N10011` **last of six** on critical events at 21 events and 11 critical, while conversation memory ranks it **joint first** at 3 technicians and 3 mentions, because three technicians on three shifts each pulled its EGT trend independently and none of them knew the others had. Neither source alone produces that. Detail and the controls are under Lab 6 above
- [x] Confirm which embedding and LLM providers `neo4j-agent-memory` accepts on Databricks. **Settled, and it is a pass.** The library hard-codes no provider: `llm/protocol.py` defines `EmbeddingProvider`, `LLMProvider`, and `StructuredExtractor` as `@runtime_checkable` Protocols, and `MemorySettings.embedding` and `.llm` are typed `Any` with a validator accepting any Protocol instance. About 130 lines of adapter binds Databricks Foundation Model endpoints through `mlflow.deployments`, verified live against `databricks-bge-large-en` and `databricks-meta-llama-3-3-70b-instruct`. The library read 1024 dimensions off the adapter and created all six of its vector indexes at 1024 with COSINE similarity unprompted
- [x] Pin `neo4j-agent-memory` to an exact version and record it. **Pinned at `0.5.0`**, wheel uploaded 2026-05-30T23:23:11, tag `python-v0.5.0`, source commit `ece2e6ee1c594359381a7066ac05b2219ebf9cfb` by William Lyon. `requires-python >=3.10`. Neo4j server floor 5.20, stated in the project `README.md`, needed for vector indexes. The spike instance reported `5.27-aura`, enterprise, Cypher 5 and 25, comfortably above the floor. Answers to all four research-note questions are recorded below
- [x] ~~Confirm whether Vocareum participants can create a secret scope~~ **Retired by Open Decision 1.** The participant creates their own scope in Lab 3 notebook 01, so no hook creates one and the permission question does not arise
- [ ] Check the workspace Model Serving endpoint quota against the largest expected class size
- [ ] **Confirm AuraDB Free tolerates 59 indexes and six vector indexes.** The tier is decided, the spike instance's tier was never confirmed, and this is the one remaining item that can still flip Lab 6 to no-go. The library creates 33 indexes and 12 constraints on first connect, six of the 33 being vector indexes at 1024 dimensions, once per database rather than per participant, whether or not the lab uses reasoning traces or preferences. That is what takes the total to 59
- [ ] **Point `Lab_1_Aura_Setup/Aura_Free_Trial.md` at AuraDB Free.** It currently says to click **Start 14-day free trial**, which provisions an AuraDB Professional Trial that expires mid-course. In flight 2026-08-08
- [ ] **Note at the top of `Lab_2_Databricks_ETL_Neo4j/02_gds_knn_aircraft.ipynb` that it cannot run on AuraDB Free.** The notebook stays and is skipped unless the participant has their own AuraDB Professional instance. Open Decision 7, decided. In flight 2026-08-08
- [ ] **Test the `extraction_mode="explicit"` batch path.** The spike measured only the singular `add_message`. `add_messages` is what the seeding step will use, it embeds in batches through `embed_batch` and extracts afterward, and it is untested with explicit mentions

Completion criteria: the loader runs twice in a row without duplicating data, cross-path cosine similarity is high enough that retrieval quality is unchanged, and the memory spike either returns a good answer or is recorded as a no-go for Lab 6. The spike returned a good answer on 2026-08-08.

Note: generating embeddings for the manual chunks is the slow part and may push the loader past a comfortable in-lab runtime. If it does, pre-generate embeddings into the Unity Catalog volume and have the loader write them rather than compute them.

**Research note: pin `neo4j-agent-memory`. Answered 2026-08-08 by the Phase 0 spike.** It is a `neo4j-labs` project, which means a pre-1.0 API and no compatibility promise. A workshop notebook that installs the latest version can break between the dry run and delivery day without a single line of our code changing, and it breaks in a room, live. The four answers are recorded here because `Lab_6_Agent_Memory/README.md` does not exist yet. **Move this block into that README when Phase 3 creates it.**

- **Exact version.** `neo4j-agent-memory==0.5.0`, pinned in the notebook `%pip install` line, not a floor and not a range. Wheel uploaded 2026-05-30T23:23:11. Repository https://github.com/neo4j-labs/agent-memory, tag `python-v0.5.0`, source commit `ece2e6ee1c594359381a7066ac05b2219ebf9cfb`, 2026-05-30, William Lyon. `requires-python >=3.10`. **Install `httpx` alongside it.** See the Phase 3 checklist for why.
- **API surface we depend on.** Documented, from the README: `MemoryClient(settings, extractor=...)` as an async context manager, `MemorySettings(neo4j=, embedding=, llm=, schema_config=, extraction=)`, `Neo4jConfig`, `SchemaConfig`, `SchemaModel.CUSTOM`, `ExtractionConfig`, `ExtractorType.LLM`, `client.short_term.add_message(...)`, `client.short_term.search_messages(text, limit=)`, and `client.query.cypher(query, params)`. Documented in `docs/modules/ROOT/pages/how-to/adopt-existing-graph.adoc`: `client.schema.adopt_existing_graph(label_to_type=, name_property_per_label=)`, which also accepts `dry_run=True` and returns an `AdoptionReport` without writing. **Docstring only, so these are the ones that move:** `add_message(..., extraction_mode="explicit", explicit_mentions=[EntityRef(...)])` at `memory/short_term.py:661`, and `EntityRef` itself, which is not exported at package root and must be imported from `neo4j_agent_memory.schema.models`. **Undocumented, read off the source:** the `LLMEntityExtractor` constructor at `extraction/llm_extractor.py:140`, needed only if the lab wants a custom `extraction_prompt`, which `ExtractionConfig` does not expose. Use `client.query.cypher` from day one: `client.graph.execute_read` emits a deprecation warning naming v0.6.0 for removal.
- **Neo4j version floor.** 5.20, stated in the project `README.md` line 305, required for vector indexes. The spike instance reported `5.27-aura`, enterprise, Cypher 5 and 25, against Neo4j Python driver 6.2.0. The floor is met with room. The one Neo4j-side wrinkle is cosmetic: `search_messages` emits `db.index.vector.queryNodes is deprecated. It is replaced by SEARCH.` It works on 5.27-aura and participants will see the warning in notebook output.
- **Owner and cadence.** William Lyon authored 373 of the repository's commits and cut every tag, so he is the contact for a breaking-change warning. Ryan already has 5 commits in the repository, so the internal channel is open without an introduction. Other recent contributors: Prakriti Solankey, Andreas Berger, Tomaz Bratanic, kaustubh-darekar, muddybootscode. **The cadence is the risk, and it is concrete.** Thirteen PyPI releases between 2026-01-22 and 2026-05-30, about one every eleven days, and the series skipped 0.3 entirely, going 0.2.1 to 0.4.0 in thirteen days. `main` sits **38 commits ahead of the 0.5.0 tag**, among them `7b2f872 Generic backend-typed MemoryClient (agnostic Protocols + connect())`, which rewrites the exact Protocol surface the Databricks adapter binds to, plus six commits titled `Type-safety Phase 1` through `Phase 6` ending with mypy and ty blocking in CI. Expect the adapter to need work on the next release. **Pin, and stay pinned.** Treat any upgrade as a code change with its own test pass, not as a version bump.

The pinned version works on the Neo4j version Aura serves, so the Phase 0 no-go this note guarded against did not fire. Set a re-check date at the same time as the Part B review date, so both external dependencies get looked at together rather than each being remembered separately.

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

The first three items are the hard conditions the Phase 0 spike attached to its GO. Each one fails silently rather than loudly, which is why each is a checklist item rather than a note.

- [ ] **Pin `neo4j-agent-memory==0.5.0` and install `httpx` explicitly.** The bolt path imports httpx transitively: `MemoryClient.connect()` reaches `_connect_bolt`, which imports `neo4j_agent_memory.nams._unsupported`, which pulls in `nams/transport.py`, which does `import httpx`. httpx ships only in the `nams` extra, so a bare install fails with `ModuleNotFoundError: No module named 'httpx'` at `connect()` rather than at import, meaning it surfaces in front of participants
- [ ] **Adopt `Aircraft` only, and show the `dry_run=True` report first.** `adopt_existing_graph` runs `SET n.type = $type` unconditionally while guarding `id` and `name` with `coalesce`, so adopting `System`, `Component`, `Sensor`, or `Document` destroys the `type` values Lab 2 and Lab 4 filter on. `System.type` carries `Engine`, `Hydraulic`, `Fuel`, and `Landing Gear`; `Sensor.type` carries `EGT` and friends. This was hit live during the spike: adopting `Component` turned every `Component.type` from `Turbine` to `COMPONENT`, and recovery took a full `populate-aircraft-db load-operational` at 4 minutes 32 seconds. The lab text should say why, not just what
- [ ] **Write memory with `extraction_mode="explicit"` rather than the default auto extraction.** Auto extraction in 0.5.0 silently drops `MENTIONS` edges, which is the exact edge the headline query traverses. Explicit mode linked 10 of 10 and is the better production pattern anyway. Full detail in the defect subsection under Lab 6 above
- [ ] Memory client configured against the participant's Aura, with `adopt_existing_graph` resolving to real fleet `Aircraft` nodes
- [ ] `recall` and `remember` nodes added around the Lab 5 supervisor
- [ ] Ship `DatabricksEmbeddings` and `DatabricksLLM` as lab-provided code rather than as an exercise. Teaching the Protocol is a good five minutes; making participants write the structured-output retry loop is not. The loop is needed because Foundation Model endpoints do not enforce a JSON Schema server-side the way the OpenAI structured-output API does
- [ ] Import `EntityRef` from `neo4j_agent_memory.schema.models`, and use `client.query.cypher` rather than the deprecated `client.graph.execute_read`
- [ ] The three hands-on demos: fleet-joined traversal, reasoning reuse, cross-session continuity
- [ ] Memory off versus on evaluation harness reusing the Phase 2 baseline
- [ ] The four instructor demos, shipped complete as runnable cells: correction with invalidation, learned preferences, shift handoff, routing memory
- [ ] Seed conversation history in a setup step rather than in a participant-run loop, since a message costs 5.6 seconds in explicit mode
- [ ] Each hands-on demo timed individually against its share of the 75 minutes. The measured per-call floor is 1.85 seconds per embedding call and 1.84 seconds per short LLM call, giving 5.6 seconds per message in explicit mode and 9.2 seconds with auto extraction, plus 22.4 seconds for first connect and schema creation. Those are the numbers each demo's timing has to add up from
- [ ] **File the `MENTIONS` defect upstream.** The fix is one line: read the id back from the `RETURN e` that `build_create_entity_query` already produces, and link with that instead of the discarded uuid. Ryan has 5 commits in the repository already and William Lyon owns 373 of them, so the channel is open. Worth filing whether or not Lab 6 ships

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
- [ ] **Known oddity, conditional on how the loader is invoked.** During the memory spike, two background `populate-aircraft-db setup` runs exited without writing an exit line and produced empty log files, while loading the data correctly. Not root-caused. It matters only if a Vocareum hook ever runs the loader detached rather than in the foreground. If the dry run keeps the loader in the foreground, close this as not applicable

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
| **B. Memory research** | Headline demo spike, provider check, version pin **(done, GO)** | Aura tier check, explicit-mode batch path | idle | joins Track A | Dry run | idle |
| **C. Content and infra** | Lab 4 banners, Part A handoff, superseded banners **(done)**; sensor unit documentation **(done)**; Lab 1 tier fix and Lab 2 GDS note **(in flight)** | Repo docs, `agenda.md`, `lab/workshop.py` **(done)** | Eval question set | Lab 6 README | Timing capture, Vocareum courseware resync | Lab 5 architecture diagram, Antora site, slides, between-sessions guidance |

What actually blocks what:

- The catch-up loader does not block building the Lab 5 tools. Build the tools against an already-loaded instance. The loader is a prerequisite for participants, not for development.
- The memory spike did not block Lab 5 at all. It needed a loaded graph and nothing else, and it delivered its go/no-go before Lab 6 starts and before Lab 5 finished. **It came back GO with three conditions**, so the "hold Lab 6 and ship Labs 4 and 5 alone" fallback is not needed and stays written down only in case the remaining Aura tier check goes badly.
- The Track C work that was independent of code is done. What remains waits on the labs rather than on code: the courseware bundle, the site, and the slides all describe the course, so each gets rewritten once, after Labs 5 and 6 land.
- The Lab 5 eval question set can be written on day one. It is a list of questions and expected routes.
- Only Phase 3 has a hard dependency on Phase 1, because the memory nodes attach to the Lab 5 supervisor.
- Phase 5 depends on Phase 4, not on Phase 3. Its catch-up cell has to reproduce a state Phase 4 has confirmed is reachable, so building it earlier means building it against a moving target.

Parallelism caveat, now resolved: Tracks A and B both write to Aura, and the memory spike puts memory nodes into a graph the loader tests are trying to keep clean. Two tracks writing to one graph is how a loader test starts failing for a reason that has nothing to do with the loader. The separation now exists. Track A works against `f024ea61`, already loaded, credentials in `workshop-setup/.env`, reset with `populate-aircraft-db clean` and reloaded whenever a test needs a clean graph. Track B works against `1a2c98cc`, credentials in `workshop-setup/.env.memory`. With one person doing all three tracks, the tracks still collapse to sequential in wall-clock terms, but neither track can corrupt the other's evidence.

### If Phase 0 Fails

- ~~Loader too slow~~: **measured at 4 minutes 23 seconds, so this one did not happen.** The fallbacks stay written down in case the serverless path is slower than the laptop path: pre-generate embeddings into the volume, or split the loader so the fleet graph loads in-lab and the Lab 3 artifacts load only for participants who skipped Lab 3.
- ~~Embedder drift confirmed between the two paths~~: **measured at cosine 1.0, so this one did not happen either.** The rule it implied still stands and is now cheap to keep: one writer, one reader, one model, named once as `EMBEDDING_ENDPOINT` in `lab/workshop.py`.
- `populate_aircraft_db` will not run on serverless: vendor its loader module into the catch-up notebook. The embedding provider fix carries over unchanged, and the schema and index names stay identical.
- ~~Aura Free too small~~: **measured 2026-08-08, so this one did not happen either.** A participant after Labs 1 through 3 holds about 21,613 nodes, 10.8 percent of the 200,000 node cap, and memory costs about 20 nodes per participant per session against roughly 178,000 nodes of headroom. The 88.7 percent figure was the admin reference instance, which carries 155,520 `Reading` nodes Lab 2 never loads. The class uses AuraDB Free, so the cap is real and the measurement is against the right number. The fallbacks stay written down anyway: move memory to a second free instance and accept losing the fleet-joined traversal demo, or drop Lab 6 to the take-home path.
- ~~Memory spike returns a weak answer~~: **the spike returned GO with three conditions on 2026-08-08, so this one did not happen.** The fallback stays written down against the one item still open, whether AuraDB Free tolerates 59 indexes and six vector indexes: hold Lab 6 and ship Labs 4 and 5 alone. That is already a large improvement, and it is the majority of the value in this proposal.
