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

# Neo4j MCP and Agent Bricks

A no-code supervisor agent over sensor telemetry and the aircraft knowledge graph

<!--
This is Lab 4 Part B. It is an instructor demo, not a participant
exercise. The next slide states that plainly before anything else,
so nobody in the room thinks they need to build what follows.
-->

---

## Lab 4 Part B: An Instructor Demo

- **The instructor builds this, not you:** a Supervisor Agent in Databricks Agent Bricks, over Neo4j MCP
- **Against the instructor's own Aura instance:** loaded ahead of class with the full Aircraft Digital Twin
- **You watch, you don't build:** no MCP connection and no OAuth credential enter your workspace
- **Lab 5 is your path:** the same routing, in code, against the Aura instance you set up in Lab 1

<!--
Every participant already has their own Aura instance from Lab 1.
This demo does not touch it. The MCP connection lives only in the
instructor's demo workspace, set up ahead of time per
workshop-setup/MCP-MANUAL-SETUP.md. That setup needs a metastore
CREATE CONNECTION privilege participants do not hold and an OAuth
client secret from an AWS AgentCore deployment outside this repo.
Nothing here is meant to be reproduced live. Participants continue
straight to Lab 5.
-->

---

## Model Context Protocol: One Standard, Any Agent

- **MCP:** an open standard for how agents discover and call external tools
- **Without it:** every agent framework needs its own Neo4j client, its own auth, its own tool wiring
- **With it:** one server exposes tools once, any MCP-compatible agent connects
- **Agent Bricks speaks MCP natively:** register a server once as a Unity Catalog connection, any supervisor can use it

<!--
MCP separates three concerns: the agent, the server that exposes
tools, and the data source behind it. An agent asks the server what
tools exist, then calls them by name. Neither side needs the other's
internals. The payoff here: the Neo4j MCP server was built once, and
Agent Bricks uses it as a subagent with no custom orchestration code.
-->

---

## Beyond the Graph: Reaching the Lakehouse

- **The knowledge graph reaches graph data:** aircraft, systems, components, maintenance events, flights
- **The lakehouse holds the rest:** sensor telemetry such as EGT, Exhaust Gas Temperature, recorded every four hours over ninety days, in Delta tables
- **The graph can't compute SQL:** "average EGT for engine AC5 this month" lives in the lakehouse
- **Answering both halves needs more than one query engine**

<!--
The aircraft graph holds HAS_SYSTEM and HAS_COMPONENT relationships,
plus maintenance events and flights. It does not hold the raw
sensor_readings table, recorded every four hours over ninety days.
"Average EGT for engine AC5 this month" needs a SQL aggregation over
rows that never entered the graph. Spanning both platforms needs
agents, one per platform.
-->

---

## Specialized Agents for Different Data Structures

- **Context window pollution:** two schemas, two query languages in one prompt dilutes focus
- **Narrowed scope:** an agent that only knows sensor tables writes SQL, one that knows both starts mixing them up
- **Different reasoning patterns:** SQL thinks in rows and aggregations, Cypher thinks in paths and traversals
- **Reliability:** one agent per platform beats one generalist agent guessing at both

<!--
The lakehouse needs an agent that speaks SQL, the graph needs one
that speaks Cypher. A single agent spread across both cannot hold
the focused context needed for reliable queries against either. When
an agent reasons about one platform only, its schema becomes a
constraint that guides generation rather than a suggestion to
ignore. One agent per platform, a supervisor to coordinate them.
-->

---

## Neo4j MCP Tools

- **`get_neo4j_schema`:** reads labels, relationship types, and properties, token-efficient for the LLM
- **`read_neo4j_cypher`:** executes read-only Cypher, runs `EXPLAIN` first to block any write
- **Gateway-prefixed names:** the AgentCore Gateway exposes them as `neo4j-mcp-server-target___get_neo4j_schema` and `...___read_neo4j_cypher`
- **Read-only by design:** no write-capable tool exists in this deployment

<!--
get_neo4j_schema introspects the live graph and returns a compact
JSON structure: labels, relationship types, property keys, nothing
verbose. read_neo4j_cypher runs EXPLAIN on the query first to
confirm no write operation snuck in, then executes it. This
deployment exposes exactly these two tools. The Gateway prefix is
why the names look unusual in the tool list: it namespaces every
tool behind the target it proxies to.
-->

---

## Connecting to Neo4j: A Unity Catalog HTTP Connection

- **Connection type:** HTTP, named `neo4j_agentcore_mcp`, scoped to the metastore
- **Auth type:** OAuth Machine to Machine, Databricks exchanges a client ID and secret for a JWT and refreshes it automatically
- **What it points at:** an AWS AgentCore Gateway fronting the Neo4j MCP server, deployed outside this repository
- **Built once, by the instructor:** `CREATE CONNECTION` needs a metastore privilege participants do not hold

<!--
The Neo4j MCP server runs on AWS AgentCore behind a Cognito
machine-to-machine client-credentials flow. OAuth Machine to Machine
is the only Databricks auth type that fits: Dynamic Client
Registration expects the server to register clients on the fly, and
a static bearer token expires in about an hour with no refresh. This
is the one Databricks-side setup step in the whole workshop that
stays manual, carrying an OAuth client secret nothing in this repo
can read. Everything else gets built by lab/workshop.py.
-->

---

## The Genie Agent: Natural Language to SQL

- **Lives entirely in Databricks:** built in Lab 4 Part A, registered as `aircraft-genie`
- **Answers questions about telemetry:** anything in Unity Catalog tables, like `sensor_readings`
- **Domain knowledge, then SQL:** table descriptions and instructions turn English into governed SQL
- **Good at:** "average EGT for engine AC5 this month," "compare fuel flow between Boeing and Airbus aircraft"

<!--
Genie is the agent participants already built in Lab 4 Part A. It
reads table and column descriptions from Unity Catalog, applies
domain instructions about normal sensor ranges, and generates SQL
against sensor_readings, sensors, systems, and aircraft. Every
generated query is read-only.
-->

---

## The Neo4j MCP Agent: Natural Language to Cypher

- **Connects through the Unity Catalog connection:** discovers the graph schema via `get_neo4j_schema`
- **Answers questions about relationships:** aircraft, systems, components, maintenance events, flights
- **Schema first, then Cypher:** it writes and runs `read_neo4j_cypher` against the actual labels and types it found
- **Good at:** "which components were serviced on aircraft AC1001," "what maintenance events followed that flight"

<!--
This subagent has no baked-in knowledge of the graph. It calls
get_neo4j_schema first, sees the real labels and relationship types
like HAS_SYSTEM and HAS_COMPONENT, then writes Cypher against that
vocabulary instead of guessing. Every query runs through
read_neo4j_cypher, so it can only read.
-->

---

## Multi-Agent Supervisor: Routing to the Right Platform

```
                    User Question
                         |
                         v
                +--- Supervisor ---+
                |                  |
                v                  v
        Genie Agent          Neo4j MCP Agent
        (Lakehouse / SQL)    (Graph / Cypher)
```

- **Numbers and trends** go to the Genie agent
- **Relationships and structure** go to the Neo4j MCP agent
- **Both needed:** the supervisor calls each in turn, then combines the answers

<!--
The supervisor does not answer questions itself. It reads the
question, decides which data shape it targets, and routes to the
matching specialist. A question spanning both shapes gets
decomposed into sub-tasks for each agent, then synthesized into one
answer.
-->

---

## Routing in Action

- **"What is the average EGT for engine AC5?"** goes to the **Genie agent**, a numeric aggregation
- **"Which components were serviced on aircraft AC1001?"** goes to the **Neo4j MCP agent**, a relationship traversal
- **"Find aircraft with high EGT and show their maintenance history"** goes to **both agents in sequence**, then the supervisor combines the results

<!--
The first two questions are single-shape and route to one subagent
each. The third needs one agent's output as the other's input, so
the supervisor calls Genie first to identify qualifying aircraft,
then passes them to the Neo4j MCP agent. No SQL or Cypher knowledge
is required from the person asking.
-->

---

## The Hero Question: Where the Two-Agent Demo Stops

"Which engines are showing abnormal EGT readings, what maintenance history do those aircraft have, and what does the maintenance manual say to do about high EGT?"

- **Part one, abnormal EGT readings:** the Genie agent, SQL over `sensor_readings`
- **Part two, maintenance history for those aircraft:** the Neo4j MCP agent, Cypher traversal
- **Part three, what the manual says:** no subagent in this demo answers it

<!--
This is the workshop's hero question. Running it against this exact
demo shows where a two-agent supervisor runs out of road. This
supervisor has exactly two subagents, Genie and the Neo4j MCP agent,
so it answers the first two clauses well. The third clause needs the
GraphRAG retrievers built in Lab 3, which this demo never wires in
as a subagent. The gap is the point, not a flaw to patch here.
-->

---

## Building the Supervisor: No Code, One Page

- **One configuration page:** subagents on the left, instructions below them, a chat pane to test on the right
- **Add the Genie Agent:** pick the existing `aircraft-genie` agent by its id
- **Add the Neo4j MCP agent:** select the `neo4j_agentcore_mcp` connection as an external MCP server subagent
- **Write routing instructions:** plain-text description of what each subagent is good for, no orchestration code

<!--
Everything happens on one page in the Agent Bricks UI. Each
subagent gets a description the supervisor reads to decide who
handles a question, and the Instructions field carries the routing
policy in plain English. A sandboxed code execution tool comes
included with every supervisor, so it can compute over whatever the
subagents return, with no data access of its own.
-->

---

## Two Paths to the Same Shape

| | Agent Bricks Supervisor, this demo | Lab 5 LangGraph Agent |
|---|---|---|
| **Build method** | Configuration page, no code | Python graph in `tools.py` and `agent.py` |
| **Subagents** | Genie and the Neo4j MCP agent, two specialists | Genie, Cypher over your own Aura, and GraphRAG retrieval, three specialists |
| **Graph target** | The instructor's demo Aura instance | The Aura instance you set up in Lab 1 |
| **Hero question** | Answers the sensor and maintenance-history parts | Answers all three parts, including what the manual says |

<!--
Same shape, two ways to get there. Agent Bricks assembles a
supervisor from a form: fast to build and a clean way to show the
pattern before writing code. Lab 5 builds the identical shape in
LangGraph, with a third tool for manual retrieval, and deploys to
Model Serving as a ResponsesAgent that Lab 6 later gives memory. The
no-code path buys speed. The code path buys the full hero question
and a deployable endpoint.
-->
