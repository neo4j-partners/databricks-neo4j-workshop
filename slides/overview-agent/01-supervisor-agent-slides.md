---
marp: true
theme: default
paginate: true
---

<style>
section {
  --marp-auto-scaling-code: false;
}

li {
  opacity: 1 !important;
  animation: none !important;
  visibility: visible !important;
}

/* Disable all fragment animations */
.marp-fragment {
  opacity: 1 !important;
  visibility: visible !important;
}

ul > li,
ol > li {
  opacity: 1 !important;
}
</style>

# The Supervisor Agent and Deployment

One supervisor, three tools, one endpoint that answers for someone else

---

## Why a Single Retriever Is Not Enough

- **Vector, vector-Cypher, Text2Cypher:** three retrieval patterns, one shape of question each
- **Users do not name a pattern.** They ask questions:
  - "What causes turbine bearing wear?"
  - "How many critical maintenance events are in the database?"
  - "Which aircraft have engines with components that had recent faults?"
- One retriever answers one shape of question. Real questions do not arrive sorted by shape.

---

## What Is an Agent: Components and Tools

An agent wraps retrievers in a reasoning loop, with four parts:

| Component | What It Does |
|---|---|
| **Perception** | Reads the question, the history, the tool descriptions |
| **Reasoning** | Decides which tool fits the question |
| **Action** | Calls a tool: a function the agent can invoke |
| **Response** | Returns a grounded answer in natural language |

Retrievers become tools. The agent matches a question to a tool description, not to a retriever's name.

---

## The ReAct Loop

**ReAct**: Reason, then Act, then Observe, then Respond, or loop again.

```
1. Receive: "How many critical events does Engine #1 on N10001 have?"
2. Reason: this asks for a count
3. Act: call the database query tool
4. Observe: result = 7
5. Respond: "Engine #1 on N10001 has 7 critical maintenance events."
```

Complex questions cycle more than once. The supervisor ahead is this same loop, run over three stores instead of one.

---

## What Lab 5 Assembles

- **Lab 2** gave you a fleet graph: aircraft, systems, components, flights, maintenance history, in your own Aura instance
- **Lab 3** gave you the manuals: chunked, embedded, with a retriever that walks out from a matched passage
- **Lab 4** gave you a Genie Agent: natural language to SQL over the Lakehouse telemetry
- **None of the three answers a real question alone.** This lab builds what decides which one to reach for

<!--
Nothing here is new data, and the routing decision is the hard
part. Lab 4's compound agent demo built this from a form in Agent
Bricks; this lab writes it in code, with the rule visible.
-->

---

## The Shape of the Agent

![Supervisor routing to a Genie node, a Cypher node and a GraphRAG node](../../site/modules/ROOT/images/lab5-agent-topology.svg)

Nothing in this graph writes to Neo4j.

<!--
Five nodes and one decision. The supervisor picks a tool or picks
synthesize. Every tool reports back to the supervisor rather than
answering. Synthesize ends the run.

Point at the arrows coming back up from the tools. That is the
slide's only real content, and the next slides unpack it.
-->

---

## The Three Tools, and the Loop That Calls Them

- **`genie_node`:** SQL over Delta telemetry, through the Genie Agent. The only tool that can see a reading
- **`cypher_node`:** text to Cypher over your own Aura instance, read-only, one retry with the error carried back to the model
- **`graphrag_node`:** a `VectorCypherRetriever` over the Lab 3 manual chunks, with a Cypher tail run from each hit
- **Every tool edge points back to the supervisor.** It sees the result and can pick again, so one question can reach two stores
- **The decision returns as JSON**, constrained by a schema, not read out of prose

<!--
The Sensor nodes carry no reading values, by design from Lab 2:
timestamped values at that volume belong in Delta. That single fact
is why every measurement question routes to Genie.

A supervisor with a loop back to itself will call the same tool
three times if nothing stops it, because calling again always feels
safer than answering. MAX_TOOL_CALLS is the backstop, not the rule;
the prompt's stopping instruction is the rule. ROUTE_SCHEMA
constrains the reply to a next field and a reason field. No code
reads reason, but a model that has to write down why it picked a
tool picks better.
-->

---

## Wiring the Graph

```python
builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("genie_node", genie_node)
builder.add_node("cypher_node", cypher_node)
builder.add_node("graphrag_node", graphrag_node)
builder.add_node("synthesize", synthesize_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route_from_supervisor, {...})

for tool_name in ("genie_node", "cypher_node", "graphrag_node"):
    builder.add_edge(tool_name, "supervisor")

builder.add_edge("synthesize", END)
```

State is a `TypedDict`: `question`, `route`, `trace`, `findings`, `answer`.

<!--
About thirty lines, and not the interesting part of the lab. Show
it, then move on. Each node is a plain callable that takes the
state and returns the part that changed. trace is the ordered list
of tools called, the record the routing measurement reads later.
-->

---

## The Pair the Model Gets Wrong, and Where to Route It

**`cypher_node` and `graphrag_node` both end in a Neo4j traversal.**

```cypher
WITH node
OPTIONAL MATCH (previous:Chunk)-[:NEXT_CHUNK]->(node)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(following:Chunk)
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)-[:APPLIES_TO]->(a:Aircraft)-[:HAS_SYSTEM]->(s:System)
```

That is the GraphRAG tail. Neither the neighboring passage nor the aircraft a manual applies to is in the embedding; both are one hop away.

**Describing tools by what they do at the end cannot tell these two apart.** Route on where the question starts instead:

| Question | Route | Why |
|---|---|---|
| "What maintenance events did N10004 have?" | `cypher_node` | N10004 is a node |
| "What is the procedure for an EGT exceedance?" | `graphrag_node` | A phrase in a manual, not a node |
| "How do I troubleshoot engine vibration?" | `graphrag_node` | A procedure lives in the text |

<!--
This is the central problem of the lab. The Cypher tail is exactly
what makes graphrag_node worth having, and also what makes routing
hard. That is the concrete answer to what GraphRAG adds to vector
search, and why Lab 3 came before this one.

The reframing is the lesson: stop describing what the tool does,
describe what the question looks like when it arrives. The example
pairs are how a routing prompt gets tuned: take a question that
went to the wrong tool, work out which sentence should have caught
it, add the pair, rerun the measurement.
-->

---

## Two Prompt Rules, Each Bought with a Measured Failure

**The wiring is thirty lines. The prompt is the lab.**

**Rule One, the direction rule.** An `AFFECTS_AIRCRAFT` arrow written backwards matched nothing and returned zero rows with no error, on an aircraft that has maintenance events.

```cypher
// Wrong: arrow points away from the named noun, matches nothing
(:Aircraft {tail_number: 'N10004'})-[:AFFECTS_AIRCRAFT]->(:MaintenanceEvent)
// Right: the arrow runs FROM the event TO the thing affected
(:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(:Aircraft {tail_number: 'N10004'})
```

**Rule Two, never substitute a limit for a measurement.** Asked for the aircraft with the highest average vibration, `cypher_node` answered with an `OperatingLimit.maxValue`: a shared ceiling, not a reading. The rule: for any measured-value question, return exactly

```cypher
RETURN 'The graph holds no sensor readings.' AS cannot_answer
```

so the supervisor routes to `genie_node` instead of ending on a confident, wrong number.

<!--
Zero rows with no error is the worst failure mode a text-to-Cypher
tool has: the query is valid, the database is healthy, and the
answer is confidently empty. The fix was nine lines of schema text
in the prompt, not an undirected pattern; an undirected match would
have shipped a habit Lab 1 spends its time arguing against.

OperatingLimit is a good trap because it is well-formed data, never
empty, always nearby. The rule does not say "be careful"; it gives
the exact string to return, which the synthesis prompt can
recognize and carry through instead of papering over.
-->

---

## Measured Routing

Twelve questions, four per tool, scored on the first tool the supervisor chose.

| Slice | Accuracy |
|---|---|
| Overall | 12/12 (100%) |
| `genie_node` questions | 4/4 (100%) |
| `cypher_node` questions | 4/4 (100%) |
| `graphrag_node` questions | 4/4 (100%) |
| **`cypher_node` vs `graphrag_node` alone** | **8/8 (100%)** |

Recorded 2026-08-08 from a full run of `01_langgraph_agent.ipynb`, against `SUPERVISOR_PROMPT` as it stands today. These numbers go stale the moment someone edits the prompt.

<!--
The last row is the one that matters. Both tools end in a graph
traversal, so that pair is where a weak routing prompt fails
first. Say the caveat out loud: a routing number without a date
and a prompt version is decoration. Section 9 of the notebook
reproduces it, and participants should rerun it after editing
anything.
-->

---

## The Anchor Question

> Which engines are showing abnormal EGT readings, what maintenance history do those aircraft have, and what does the maintenance manual say to do about high EGT?

**Routed `genie_node`, then `cypher_node`, then `graphrag_node`, in a single pass.**

1. **Genie** named the engines carrying abnormal EGT
2. **The graph** returned the maintenance history for those aircraft, including a bearing wear fault with its corrective action
3. **The manual** closed with the guidance for high EGT: trend data for margin degradation, oil spectrographic analysis, fuel filter differential pressure, and a borescope of the HPT nozzle and blades

One question, three tools, one answer. **No single store can answer it.**

<!--
This is the demo the whole workshop builds toward. Run it live if
the room has a working agent, and show the route line before the
answer.

The supervisor was not told to use three tools. It worked the
sequence out from the question, one call at a time, with each
result in front of it when it chose the next.

The order is the natural one and the prompt suggests it: telemetry
finds which aircraft the readings point at, the graph returns that
aircraft's history, the manual returns the procedure.
-->

---

## Degradation: Two Tools Are Still an Agent

- **`VectorCypherRetriever` raises when its index is missing.** Building it eagerly would turn a skipped Lab 3 into a failure cells before the agent exists
- **The builder checks first.** No `maintenanceChunkEmbeddings` index means `graphrag_node` becomes a node that explains its own absence
- **The notebook drops it from `available_tools`,** and the routing schema's enum narrows to the tools that actually exist
- **The graph still compiles and still answers** from telemetry and the fleet graph. Running Lab 3 notebook 01 brings the third tool back with no other change

<!--
An agent whose tool set is discovered at build time degrades; an
agent whose tool set is assumed at import time fails. Narrowing the
enum is the part worth copying: a better guard than checking the
model's answer afterward, because the model cannot name a tool it
was never offered.
-->

---

## Why a Bolt Driver Rather Than MCP

- **The Lab 4 demo reached Neo4j through an MCP server** registered as a Unity Catalog HTTP connection: the right shape for a governed, shared, admin-managed instance
- **It is the wrong shape for a classroom.** The connection is an admin object, and the OAuth2 credential behind it belongs to whoever owns the server
- **Your instance is yours.** Your password is in the secret scope Lab 3 wrote, and the Neo4j Python driver opens a Bolt session against it in one line
- **The governance story pays when the graph is shared.** It costs more than it returns when the graph has exactly one user

<!--
Do not present this as MCP being wrong; that demo's architecture is
correct for the problem it solves. The question is who else reads
the graph. Credentials note: on the normal path, no plaintext
password is typed anywhere in Lab 5. The driver helper reads the
scope, uses the values, and drops them.
-->

---

## Deploying the Agent: What Actually Changes

- **A notebook demo runs with your permissions.** It works because you happen to have them
- **An endpoint runs as its own identity**, a service principal Model Serving creates, starting with access to nothing
- **Every resource it touches has to be granted to that identity explicitly.** That is the whole line between a notebook that works and a product that works for someone else

| Question a reviewer asks | Where the answer lives |
|---|---|
| What can it reach? | Only what is declared at log time, in `build_resources` |
| Where do secrets live? | A secret scope, referenced, never copied |
| What is auditable? | A Unity Catalog model version and an MLflow trace per request |

<!--
This is the thesis: nothing about the agent's logic changes when it
is deployed, only who is asking. In the notebook, every call runs
as the participant. On the endpoint, every call runs as a principal
created for the endpoint, granted nothing by default.

Put the reviewer table early on purpose. It is the slide a reviewer
would ask you to build, and the rest of this section is that table
expanded.
-->

---

## The Wrapper: MLflow `ResponsesAgent`

The graph is not served directly. It is wrapped.

```python
class FleetOpsAgent(ResponsesAgent):
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse: ...
    def predict_stream(self, request: ResponsesAgentRequest) -> Iterator[...]: ...

AGENT = FleetOpsAgent()
set_model(AGENT)
```

- **A compiled graph is an object in memory**, holding an open driver and a live session
- **`ResponsesAgent`** is the interface Model Serving speaks: one request in, output items out
- **`set_model(AGENT)`** makes the file the model rather than a library beside it

<!--
A LangGraph object cannot be handed to Model Serving; it has to be
rebuilt from nothing on a machine nobody logged into. predict_stream
exists so a streaming client still works, even though every node
here returns a whole finding at the end. Connections open on the
first request, not at load time: a container that fails on load
restarts and fails again with the reason buried in build logs; one
that fails on first request answers with the reason.
-->

---

## Register to Unity Catalog

```python
mlflow.set_registry_uri("databricks-uc")

logged = mlflow.pyfunc.log_model(
    name="agent",
    python_model="agent.py",             # models-from-code, not a pickle
    code_paths=["tools.py", "../Lab_3_Semantic_Search/data_utils.py"],
    model_config=MODEL_CONFIG,           # everything that is not a credential
    resources=RESOURCES,                 # everything the endpoint may reach
    pip_requirements=PIP_REQUIREMENTS,   # pinned, not inferred
    registered_model_name=UC_MODEL_NAME,
)
```

- **The agent becomes a versioned, governed artifact**, with a three-part Unity Catalog name
- **`python_model="agent.py"` stores the source file.** A reviewer can read exactly what will run
- **Pin the requirements.** An inferred one can carry a local version segment nothing can resolve

<!--
Models-from-code matters for review as well as reliability: the
artifact contains agent.py and tools.py as source, nothing had to
survive being serialized. Inferred requirements read the notebook's
own environment; a cluster carrying the Lab 6 memory wheel produces
an unresolvable requirement, and the container fails to build about
fifteen minutes after you stopped watching.
-->

---

## Resources vs Credentials

Databricks objects are declared and granted. Everything else is a credential, and travels as a reference.

```python
RESOURCES = [
    DatabricksGenieSpace(genie_space_id=...),
    DatabricksSQLWarehouse(warehouse_id=...),      # a Genie grant is not a warehouse grant
    DatabricksTable(table_name=...),
    DatabricksServingEndpoint(endpoint_name=...),  # the LLM and the embedding model
]

ENVIRONMENT_VARS = {
    "NEO4J_URI":      "{{secrets/<scope>/neo4j-uri}}",
    "NEO4J_PASSWORD": "{{secrets/<scope>/neo4j-password}}",
}
```

**The trap:** a model logged with the Genie Agent but not its warehouse deploys and routes cleanly. Every sensor question then fails, `not authorized to use or monitor this SQL Endpoint`.

<!--
Aura is not a Databricks object; it cannot be granted, so it has to
travel as an environment variable. dbutils does not exist in a
serving container: notebook 01 reads the password with
dbutils.secrets.get, and that call cannot exist in the served
agent, which is why agent.py reads os.environ instead. The control
plane resolves the reference when the endpoint starts, so the
password is never in the notebook, MLflow, or the endpoint's own
configuration.

The warehouse omission fails late and quietly: not at deploy, not
at routing. The endpoint comes up healthy, graph and manual
questions work, and only telemetry breaks, naming a component the
participant never explicitly configured.
-->

---

## Deploy, Then Score

```python
mlflow.set_experiment(f"/Users/{CURRENT_USER}/{ENDPOINT_NAME}")

deployment = agents.deploy(
    UC_MODEL_NAME, MODEL_VERSION,
    endpoint_name=ENDPOINT_NAME,
    environment_vars=ENVIRONMENT_VARS,
    scale_to_zero=True,
)
```

`agents.deploy` creates the endpoint, attaches the version, applies the environment block, and grants the declared resources. A first deploy takes roughly sixteen minutes; the call returns in under one.

```python
results = mlflow.genai.evaluate(
    data=EVAL_PAIRS,
    predict_fn=predict_fn,        # calls the endpoint, not a notebook copy
    scorers=[routing, Correctness(), RelevanceToQuery()],
)
```

**Low `Correctness` with `routing` at 1.0 is a prompt or data problem. Low `routing` is a supervisor problem.**

<!--
Set the experiment before deploying, or the endpoint works and
produces no traces. scale_to_zero means the first question after a
quiet period is slow, not a failure.

routing is a plain Python function comparing expected tools against
the trace: no judge needed for something the trace already states.
predict_fn calls the deployed endpoint with the serving principal's
permissions, which is the whole point of evaluating after
deployment rather than before.
-->

---

## The Names Are a Contract

```python
UC_MODEL_NAME = "databricks-neo4j-workshop.agents.fleet_ops_assistant"
AGENT_ENDPOINT_PREFIX = "fleet-ops-assistant"
```

- **Constants in `agent.py`**, not strings a participant types
- **Lab 6 redeploys *this* endpoint** with memory added, rather than standing up a second one. Renaming either breaks Lab 6
- **A registered model name is scoped to its catalog**, so it is the same for everyone
- **A serving endpoint name is unique across the account**, so it carries the participant's slug, taken from the same secret scope the credentials come from

<!--
Two derivations of who the participant is could drift; one cannot,
which is why the endpoint name and the credentials both trace back
to the same secret scope. Serving endpoint names are limited to
sixty-three characters, so the slug is truncated to fit. The
practical instruction for the room: do not rename these. Lab 6
calls the same function with the same scope and expects the same
endpoint back.
-->

---

## Summary

- **One supervisor, three tool nodes**, over Delta telemetry, your own graph, and the Lab 3 manual chunks, looping back to itself until every part of a question has an answer against it
- **`cypher_node` and `graphrag_node` are adjacent** because GraphRAG has a Cypher tail. Route on where the question starts, not on what a tool does at the end
- **Two prompt rules, each bought with a measured failure:** a backwards arrow that returned zero rows silently, and a limit returned as a measurement
- **Deployed, the graph becomes an endpoint** with its own identity: resources declared and granted, credentials referenced, the model logged as readable source
- **That endpoint is a building block, too:** registered as a serving endpoint, it is what an Agent Bricks Supervisor can route to alongside a Genie Agent with no orchestration code, the same shape Lab 4's instructor demo showed over MCP

<!--
If one thing survives the day, make it the routing reframing:
describe the question, not the tool. The deployed endpoint is not
the end of the story either. Because it is a Unity Catalog model
behind a served endpoint, anything that can call an endpoint,
including a no-code Agent Bricks Supervisor, can compose it with
other agents the same way this lab composed three tools.
-->
