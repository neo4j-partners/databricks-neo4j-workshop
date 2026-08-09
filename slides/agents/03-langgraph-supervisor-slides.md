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


# The LangGraph Supervisor Agent

One supervisor, three tools, one question that needs all of them

---

## What Lab 5 Assembles

- **Lab 2 gave you a fleet graph:** aircraft, systems, components, flights, maintenance history, in your own Aura instance
- **Lab 3 gave you the manuals:** chunked, embedded, with a retriever that walks out from a matched passage
- **Lab 4 gave you a Genie Agent:** natural language to SQL over the Lakehouse telemetry
- **None of the three answers a real question on its own.** This lab builds the thing that decides which one to reach for

<!--
Nothing here is new data. Every store the agent touches was built
in an earlier lab. What is new is the routing decision, and that
decision turns out to be the hard part.

Lab 4's optional compound agent demo built the same routing
behaviour from a form in Agent Bricks. This lab writes it in code,
against the participant's own graph, with the routing rule visible
and editable.
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
slide's only real content, and the next two slides unpack it.
-->

---

## The Three Tools

- **`genie_node`:** SQL over the Delta telemetry, through your Genie Agent. Every measured value and every aggregate over measured values
- **`cypher_node`:** text to Cypher over your own Aura instance, run in a read transaction, with one retry that carries the error message back to the model
- **`graphrag_node`:** a `VectorCypherRetriever` over the Lab 3 manual chunks. Embed the question, take the closest chunks, then run a Cypher tail from each hit

**`genie_node` is the only tool that can see a reading.** The graph has `Sensor` nodes and no reading values on them, by design: timestamped values at that volume belong in Delta, where scanning them is cheap.

<!--
One line each, because the tools are not the interesting part.

The last bullet is load-bearing for everything that follows. Zero
Reading nodes in Neo4j is a design decision from Lab 2, and the
supervisor prompt leans on it to route every measurement question
to Genie.

The Cypher tail on graphrag_node is the reason the next few slides
exist, so flag it now and come back to it.
-->

---

## Routing Is a Loop, Not a One-Shot Decision

- **A router picks one tool and is done.** This supervisor sees what came back and gets to pick again
- **Every tool edge points back to the supervisor.** That edge is the entire difference between the two
- **So one question can reach two stores,** with each choice informed by the last result
- **The decision comes back as JSON,** constrained by a schema on the request rather than read out of prose the model wrote for a human
- **`MAX_TOOL_CALLS` is the backstop,** not the rule. The prompt tells the supervisor to call each tool at most once and to synthesize as soon as every part of the question has something against it

<!--
A supervisor with a loop back to itself will call the same tool
three times if nothing tells it not to, because calling a tool
again always feels safer than answering. The stopping rules in the
prompt are what prevent that; the call budget only catches the
case where the rules failed.

The structured output detail matters in practice: ROUTE_SCHEMA
constrains the reply to a next field and a reason field. No code
reads reason. It is in the schema because a model that has to
write down why it picked a tool picks better.
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

# Every tool reports back rather than answering.
for tool_name in ("genie_node", "cypher_node", "graphrag_node"):
    builder.add_edge(tool_name, "supervisor")

builder.add_edge("synthesize", END)
```

State is a `TypedDict`: `question`, `route`, `trace`, `findings`, `answer`.

<!--
About thirty lines, and this is not the interesting part of the
lab. Show it, then move on.

Each node is a plain callable that takes the state and returns the
part of it that changed. trace is the ordered list of tools called,
and it is the record the routing measurement reads later.
-->

---

## The Pair the Model Gets Wrong

**`cypher_node` and `graphrag_node` both end in a Neo4j traversal.**

```cypher
WITH node
OPTIONAL MATCH (previous:Chunk)-[:NEXT_CHUNK]->(node)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(following:Chunk)
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)-[:APPLIES_TO]->(a:Aircraft)-[:HAS_SYSTEM]->(s:System)
```

That is the GraphRAG tail. It walks sideways along `NEXT_CHUNK` so a procedure split across a chunk boundary arrives whole, and upward through the `Document` to the aircraft the manual applies to.

**A supervisor that describes its tools by what they do at the end cannot tell these two apart.** It sends manual questions to Cypher, where they return nothing, because manual text is not a property you can filter on.

<!--
This is the central problem of the lab. The Cypher tail is exactly
what makes graphrag_node worth having, and it is also what makes
the routing hard.

Neither the neighbouring passage nor the aircraft the manual applies
to is in the embedding. Both are one hop away in the graph. That is
the concrete answer to "what does GraphRAG add to vector search",
and it is why Lab 3 came before this one.
-->

---

## Route on Where the Question Starts

```
  Starts with a name you could put in a WHERE clause  -> cypher_node
  Starts with a phrase you would search a manual for  -> graphrag_node
```

| Question | Route | Why |
|---|---|---|
| "What maintenance events did N10004 have?" | `cypher_node` | N10004 is a node |
| "What is the procedure for an EGT exceedance?" | `graphrag_node` | A phrase in a manual, not a node |
| "What is the documented EGT limit for the A320-200?" | `cypher_node` | A `maxValue` on an `OperatingLimit` |
| "How do I troubleshoot engine vibration?" | `graphrag_node` | A procedure, so it lives in the text |

If the question names an entity and asks what a *document* says about it, the document is what is being asked for.

<!--
One reframing, and it is the lesson of the lab. Stop describing
what the tool does. Describe what the question looks like when it
arrives.

The example pairs are not decoration. They are how a routing prompt
gets tuned: take the question that went to the wrong tool, work out
which sentence should have caught it, add the pair, rerun the
measurement. Same loop you would use on a classifier.
-->

---

## Rule One: The Direction Rule

**The wiring is thirty lines. The prompt is the lab.** Two rules in it were each written to fix a measured failure.

**The failure.** An `AFFECTS_AIRCRAFT` arrow written backwards matched nothing and returned zero rows with **no error**, on an aircraft that has maintenance events. The tool reported that it found none.

```cypher
// Wrong. Points the arrow away from the named noun, matches nothing.
(:Aircraft {tail_number: 'N10004'})-[:AFFECTS_AIRCRAFT]->(:MaintenanceEvent)

// Right. The arrow runs FROM the event TO the thing affected.
(:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(:Aircraft {tail_number: 'N10004'})
```

A question naming an aircraft does not mean the arrow leaves the aircraft.

<!--
Zero rows with no error is the worst failure mode a text to Cypher
tool has. The query is valid. The database is healthy. The answer
is confidently empty, and nothing downstream can tell that it
happened.

Worth saying out loud: GRAPH_SCHEMA is not generated from the live
graph and should not be. A generated schema lists labels and
properties. It cannot tell you which arrow direction produced a
silent zero-row answer last Tuesday.

AFFECTS_AIRCRAFT and AFFECTS_SYSTEM both run from the
MaintenanceEvent to the thing affected. The model guessed the
direction from the shape of the question rather than from the
schema, because the schema had not told it.
-->

---

## Why We Fixed the Prompt, Not the Query

- **The obvious fix:** drop the arrow direction and let the pattern match either way. **Rejected**
- **It teaches a Cypher habit Lab 1 spends its time arguing against,** and it would make every traversal in the workshop quietly more expensive
- **The fix was nine lines of schema text** in the prompt, stating the direction and naming the failure it prevents
- **A wrong answer from a text-to-Cypher tool is usually a gap in what the model was told about the graph, not a flaw in the graph**

**A prompt rule with its bug attached is a lesson. The same rule without it is a wall of text nobody reads.**

<!--
This is the non-obvious call, and it is the one to take away.

The undirected pattern would have made the symptom go away in one
character. It would also have shipped an undirected traversal into
a workshop whose first lab explains why direction is how a graph
stays cheap. The bug was in the description, so the description
is where the fix went.
-->

---

## Rule Two: Never Substitute a Limit for a Measurement

**The failure.** Asked which aircraft had the highest average vibration, `cypher_node` answered with `maxValue` `3.0` from the `Vibration - B737-800` operating limit. That is a takeoff ceiling every B737-800 shares, transcribed from a manual. It is not a reading, it is not an average, and it is not that aircraft's.

**The rule.** For any question about a measured value, return exactly:

```cypher
RETURN 'The graph holds no sensor readings.' AS cannot_answer
```

**Why refusing is the useful behaviour.** The supervisor is still holding the question. A refusal routes it to `genie_node`, which can answer it. A plausible wrong number ends the conversation with a confident falsehood.

<!--
OperatingLimit is a good trap precisely because it is well-formed
data: the canonical limits, one per parameter per aircraft model,
never empty and never duplicated. The nearest number is always
available, which is what makes "return the nearest number" such an
attractive failure.

Note the shape of the rule. It does not say "be careful". It gives
the exact string to return, which is a thing the synthesis prompt
can then recognise and carry through instead of papering over.

The line the prompt draws: what a sensor observed is a measurement
and gets the refusal. What the fleet is held to, the ceiling, the
redline, the rated or permitted value, is a limit and is answered
from OperatingLimit.
-->

---

## Measured Routing

Twelve questions, four per tool, each scored on the **first** tool the supervisor chose.

| Slice | Accuracy |
|---|---|
| Overall | 12/12 (100%) |
| `genie_node` questions | 4/4 (100%) |
| `cypher_node` questions | 4/4 (100%) |
| `graphrag_node` questions | 4/4 (100%) |
| **`cypher_node` against `graphrag_node` alone** | **8/8 (100%)** |

Recorded 2026-08-08 from a full run of `01_langgraph_agent.ipynb`, against `SUPERVISOR_PROMPT` as it stands today. These numbers go stale when someone edits the prompt, and not before.

<!--
The last row is the one that matters. Both tools end in a graph
traversal, so that pair is where a weak routing prompt fails first.
Folding it into the overall average hides the one thing worth
knowing.

Say the caveat out loud rather than reading past it. A routing
number without a date and a prompt version is decoration. Section 9
of the notebook is what reproduces it, and participants should
re-run it after they edit anything.

One limitation: the test graph ran Lab 3 with entity extraction
switched off. The routing does not depend on the extracted labels,
but the run did not exercise them.
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

- **`VectorCypherRetriever` raises when its index is missing.** Building it eagerly would turn a skipped Lab 3 into a failure several cells before the agent exists
- **So the builder checks first.** No `maintenanceChunkEmbeddings` index means `graphrag_node` becomes a node that explains its own absence, marked unavailable
- **The notebook drops it from `available_tools`,** and the routing schema's enum narrows to the tools that actually exist
- **The graph still compiles, and the agent still answers** from telemetry and the fleet graph. Running Lab 3 notebook 01 brings the third tool back with no other change

<!--
A small piece of engineering with a general point behind it: an
agent whose tool set is discovered at build time degrades, and an
agent whose tool set is assumed at import time fails.

Narrowing the enum is the part worth copying. It is a better guard
than checking the model's answer afterwards, because the model
cannot name a tool it was never offered.
-->

---

## Why a Bolt Driver Rather Than MCP

- **The Lab 4 demo reached Neo4j through an MCP server** registered as a Unity Catalog HTTP connection. That is the right shape for a governed, shared, admin-managed instance
- **It is the wrong shape for a classroom.** The connection is an admin object, one per participant instance is not something a workshop can provision, and the OAuth2 credential behind it belongs to whoever owns the server
- **Your instance is yours.** Your password is in the secret scope Lab 3 wrote, and the Neo4j Python driver opens a Bolt session against it in one line
- **The governance story starts to pay when the graph is shared.** It costs more than it returns when the graph has exactly one user

<!--
Do not present this as MCP being wrong. That demo's architecture is
correct for the problem it solves. The question is who else is
reading the graph.

Credentials note while you are here: on the normal path no plaintext
password is typed anywhere in Lab 5. The driver helper reads the
scope, uses the values, and drops them, so nothing in the notebook
binds a password to a name.
-->

---

## Summary

- **One supervisor, three tool nodes,** over Delta telemetry, your own graph, and the Lab 3 manual chunks
- **Every tool returns to the supervisor.** That loop, not a single decision, is what lets one question reach three stores
- **`cypher_node` and `graphrag_node` are adjacent** because the GraphRAG retriever has a Cypher tail. Route on where the question *starts*, not on what a tool does at the end
- **Two prompt rules, each bought with a measured failure:** a backwards arrow that returned zero rows silently, and a limit returned as a measurement
- **The routing rules live in the prompt.** They are the part of this lab you will change first for your own domain

**Next:** logging the same graph to Unity Catalog and serving it as an endpoint that authenticates as a service principal.

<!--
If one thing survives the day, make it the routing reframing:
describe the question, not the tool.

The deployment deck picks up from here. The graph runs and routes
correctly; what is left is making it something other people can
call.
-->
