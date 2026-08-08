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

**Connection approach.** The `cypher_node` and `graphrag_node` use the Neo4j Python driver and `neo4j-graphrag` directly, with the same three credentials from the Lab 1 configuration cell. The `graphrag_node` is close to a straight lift of the `VectorCypherRetriever` already built in Lab 3 notebook 02, so it costs almost no new code and it finally connects Lab 3 to the agent.

**Deployment.** Log the graph as an MLflow `ResponsesAgent`, then deploy to Model Serving with the Aura password supplied from a Databricks secret scope rather than a notebook literal. Credential handling for a deployed agent is a lesson worth 10 minutes of an advanced workshop, and it is the natural answer to the question participants will ask anyway.

**Structure.** Split into two notebooks so the halfway point is a working agent:

- `01_langgraph_agent.ipynb`: build the three tools, wire the supervisor, run the test questions in-notebook.
- `02_deploy_and_evaluate.ipynb`: wrap in `ResponsesAgent`, log to Unity Catalog, deploy, evaluate with MLflow against a fixed question set.

## Lab 6: Agent Memory

Unchanged from the previous draft in intent, and considerably simpler to build now. The infrastructure constraint that dominated the earlier proposal disappears: memory writes go to the participant's Aura instance, which is where their domain graph already lives.

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

**A catch-up cell at the top of Lab 5.** One cell that loads the complete fleet graph from the Unity Catalog volume into the participant's Aura instance, idempotently. It reuses the Spark Connector path from Lab 2 and should run in a couple of minutes. Anyone behind runs it and continues. This is the single most important item in the whole proposal to get right, because without it the restructure trades a narrative problem for a completion problem.

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
| Lab 4: Genie space | 30 min |
| Lecture: agent architectures and the supervisor pattern | 25 min |
| Lab 5: LangGraph agent | 90 min |
| Break | 15 min |
| Lecture: agent memory, and why it is a graph problem | 20 min |
| Lab 6: Agent memory | 75 min |
| Close: what to build next, call to action | 20 min |

About seven and a half hours including breaks. Appendix A and Appendix B are take-home.

For audiences that cannot commit to a full day, the same material splits cleanly: Labs 1 through 4 as a half-day foundation, Labs 5 and 6 as a half-day advanced session for participants who completed the first.

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

- `Lab_4_Compound_AI_Agents/PART_B.md` becomes `Appendix_B_Agent_Bricks/README.md`, with the reference instance and MCP connection notes intact.

**Edited**

- `Lab_4_Compound_AI_Agents/` renamed to `Lab_4_Genie_Space`, `PART_A.md` folded into `README.md`, closing section rewritten to hand off to Lab 5.
- `README.md` and `agenda.md`: new lab list and the extended-day framing.
- `Lab_3_Semantic_Search/README.md`: note that notebook 01 is now required rather than foundational, since Lab 5 depends on the vector index.
- `lab/workshop.py`: names for the Lab 5 model, serving endpoint, and secret scope.
- `workshop-setup/README.md`: external MCP setup moves to an optional section.
- `images/lab-architecture-overview.*`: redraw against the participant's own Aura, and add the third tool.

---

## Open Decisions

1. Whether the catch-up loader targets the Spark Connector path from Lab 2 or a lighter direct-driver load. The Spark path reuses code participants have seen; a driver load starts faster on serverless.
2. Whether Lab 5 deployment to Model Serving is required or optional. It is the right lesson and it is also the most likely place for a room of 30 people to hit a workspace limit.
3. Whether the local MCP section in Lab 5 ships in the first version or waits. It is the cleanest way to keep MCP in the story, and it is also the part most likely to behave differently on serverless compute.
4. Whether Appendix B stays maintained. Keeping it means keeping the AgentCore server and reference instance alive, which is exactly the operational cost this restructure was meant to shed.

---

## Recommendation

Do it, and sequence it in this order:

1. Write the catch-up loader and prove it takes a broken or empty Aura instance to a complete fleet graph in under three minutes. Everything else depends on this working.
2. Build the Lab 5 `cypher_node` and `graphrag_node` against a personal Aura instance and confirm the anchor question answers end to end across all three tools. That is the proof the restructure delivers what Part B never did.
3. Split Lab 4, move Part B to Appendix B, and ship Labs 4 and 5 as the new baseline.
4. Add Lab 6 once Lab 5 is stable, starting with the headline memory demo. If a single Cypher query joining conversation memory to maintenance history returns a good answer, the lab is worth building. If it does not, hold Lab 6 and ship the four-lab restructure on its own, which is already a large improvement.
