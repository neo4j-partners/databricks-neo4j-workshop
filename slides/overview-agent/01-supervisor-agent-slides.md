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

## What a Genie Agent Is

- **A Databricks-native agent over Unity Catalog tables**, built from a form in Lab 4 Part A
- **Domain knowledge, then SQL:** it reads table and column descriptions, not the schema alone
- **English in, governed SQL out.** Every generated query is read-only
- **Measurement questions only:** averages, trends, comparisons over `sensor_readings`
- **Here it is `genie_node`**, one tool among three, called by the supervisor rather than asked directly

<!-- Participants already built this one, so the slide is a reminder, not a lesson. The comments that carry the domain were written by the provisioning script, which is why the same Genie space answers the same way in thirty workspaces. It cannot see the graph or the manuals: that boundary is what makes routing a real decision. -->

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

1. **Receive:** "How many critical events does Engine #1 have?"
2. **Reason:** this asks for a count
3. **Act:** call the database query tool
4. **Observe:** the result comes back, seven
5. **Respond** in plain language, or loop again

Complex questions cycle more than once. The supervisor ahead is this same loop, run over three stores instead of one.

---

## Why a Single-Tool Agent Is Not Enough

- **Vector, vector-Cypher, Text2Cypher:** three retrieval patterns, each a tool an agent could hold, each answering one shape of question
- **Users do not name a pattern.** They ask "What causes turbine bearing wear?" or "Which aircraft have engines with components that had recent faults?"
- **One tool answers one shape of question.** An agent built around a single tool hits the same wall a single retriever does

---

## What Is a Supervisor Agent

- **An agent whose tools are other agents and retrievers**, not just functions
- **Same four parts, one level up:** perception reads the question, reasoning picks a tool, action calls it, response sees the result and decides: answer, or call another tool
- **It owns the routing decision, not the answer.** Each tool still does its own reasoning over its own store
- **Three tools here:** a Genie Agent over telemetry, a Cypher retriever over the graph, a GraphRAG retriever over the manuals
- **Get the routing wrong and a correct answer still comes from the wrong tool, or not at all**

<!-- This is the pattern this lab writes in code. Lab 4's demo built the same pattern from a form in Agent Bricks; the difference is not the concept, it is who is allowed to see the rule. -->

---

## The Shape of the Agent

![Supervisor routing to a Genie node, a Cypher node and a GraphRAG node](../../site/modules/ROOT/images/lab5-agent-topology.svg)

**A LangGraph graph, not a Neo4j one:** nodes are functions, edges are control flow.

Nothing here writes to Neo4j.

<!-- Five nodes, one decision: the supervisor picks a tool or picks synthesize. Every tool reports back rather than answering; point at those arrows, the slide's real content. Get the name collision out of the way here, on the picture, because the room has spent all day calling something else a graph. -->

---

## What Lab 5 Assembles

- **Lab 2** gave you a fleet graph: aircraft, systems, components, flights, maintenance history, in your own Aura instance
- **Lab 3** gave you the manuals: chunked, embedded, with a retriever that walks out from a matched passage
- **Lab 4** gave you a Genie Agent: natural language to SQL over the Lakehouse telemetry
- **None of the three answers a real question alone.** This lab builds what decides which one to reach for

<!-- Nothing here is new data, and the routing decision is the hard part. Lab 4's compound agent demo built this from a form in Agent Bricks; this lab writes it in code, with the rule visible. -->

---

## The Mosaic AI Services Labs 5 and 6 Use: The Models

**Every model call in both labs is a Databricks Foundation Model endpoint.**

- **Foundation Model APIs, pay per token:** `databricks-claude-sonnet-5` for the supervisor's routing, Cypher generation, and synthesis
- **`databricks-bge-large-en`** embeds the question `graphrag_node` searches with, the same endpoint Lab 3 wrote the index with
- **One client for both:** `mlflow.deployments.get_deploy_client("databricks")`
- **Structured outputs:** the endpoint itself enforces a JSON schema, so a route is read as a field, not out of prose
- **Genie:** `workspace_client.genie.start_conversation_and_wait` over the Lakehouse telemetry, wrapped as `genie_node`

<!-- No API keys anywhere in these labs: the workspace is the credential. Same embedding endpoint as Lab 3 is a hard requirement, because the vectors have to be comparable. Note there is no Vector Search index here; the vector indexes are Neo4j's, sized to this endpoint's 1024 dimensions. -->

---

## The Mosaic AI Services Labs 5 and 6 Use: Track and Register

**What turns a notebook object into something with a version number.**

- **MLflow tracing:** `mlflow.langchain.autolog` records a trace per request, in an experiment set before deploy
- **`ResponsesAgent`:** the MLflow interface Model Serving speaks, wrapped around the compiled graph
- **Unity Catalog Model Registry:** `mlflow.set_registry_uri("databricks-uc")`, registered into `databricks-neo4j-workshop.agents`
- **Agent Framework resources declared at log time:** `DatabricksServingEndpoint`, `DatabricksGenieSpace`, `DatabricksSQLWarehouse`, `DatabricksTable`
- **Databricks secrets and a Unity Catalog volume:** Neo4j credentials travel as a secret-scope reference, and the agent's dependencies load from the volume rather than PyPI

<!-- The resource list is the auth story: whatever is not declared here is not reachable from the endpoint. The volume matters in a locked-down workspace with no egress to PyPI. -->

---

## The Mosaic AI Services Labs 5 and 6 Use: Deploy and Score

**One call to serve it, one call to grade it.**

- **Mosaic AI Agent Framework:** `agents.deploy(...)` creates the Model Serving endpoint, attaches the version, applies the environment block, and grants the declared resources
- **What comes with it:** a service principal identity, inference tables written beside the model, and a Review App for feedback
- **Mosaic AI Agent Evaluation:** `mlflow.genai.evaluate` with `Correctness()`, `RelevanceToQuery()`, and a custom routing scorer, run against the deployed endpoint
- **Lab 6 adds no new service.** The same two Foundation Model endpoints do memory: BGE embeds every stored message, Claude extracts what is worth keeping
- **Lab 6 redeploys this endpoint**, rather than standing up a second one

<!-- Score the endpoint, not a notebook copy, so the deployed identity's permissions are what gets graded. Say plainly that Lab 6 introduces no new Databricks surface: the new machinery is all Neo4j. -->

---

## The Graph Tools, and the Loop That Calls Them

- **`cypher_node`:** text to Cypher over your own Aura instance, read-only, one retry with the error carried back to the model
- **`graphrag_node`:** a `VectorCypherRetriever` over the Lab 3 manual chunks, with a Cypher tail run from each hit
- **Every tool edge points back to the supervisor.** It sees the result and can pick again, so one question can reach two stores
- **The decision returns as JSON**, constrained by a schema, not read out of prose

<!-- No Reading nodes in Neo4j is a Lab 2 design choice, so every measurement question routes to the Genie Agent. MAX_TOOL_CALLS is the backstop; the prompt's stopping rule is what actually works. ROUTE_SCHEMA forces a reason field nobody reads, because writing one down sharpens the choice. -->

---

## What the Agent Carries Between Nodes

**The builder is thirty lines, and none of them are the interesting part.**

- **State is a `TypedDict`:** question, route, trace, findings, answer
- **Each node returns only what changed**, not a whole new state
- **`findings` accumulate**, so synthesize sees every tool's result at once
- **`trace` is the ordered list of tools called**, and the routing score reads it

<!-- The wiring is on the previous picture; this is the part that picture cannot show. Findings accumulating is why one question can reach two stores and still come back as one answer. -->

---

## The Anchor Question

> Which engines are showing abnormal EGT readings, what maintenance history do those aircraft have, and what does the maintenance manual say to do about high EGT?

**Routed `genie_node`, then `cypher_node`, then `graphrag_node`, in a single pass.**

1. **Genie** named the engines carrying abnormal EGT
2. **The graph** returned the maintenance history for those aircraft, including a bearing wear fault with its corrective action
3. **The manual** closed with the guidance for high EGT: trend data for margin degradation, oil spectrographic analysis, fuel filter differential pressure, and a borescope camera inspection of the HPT, the High-Pressure Turbine, nozzle and blades

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

## Deploying the Agent: What Actually Changes

- **A notebook demo runs with your permissions.** It works because you happen to have them
- **An endpoint runs as its own identity**, a service principal Model Serving creates, starting with access to nothing
- **Every resource it touches has to be granted to that identity explicitly.** That is the whole line between a notebook that works and a product that works for someone else

| Question a reviewer asks | Where the answer lives |
|---|---|
| What can it reach? | Only what is declared at log time, in `build_resources` |
| Where do secrets live? | A secret scope, referenced, never copied |
| What is auditable? | A Unity Catalog model version and an MLflow trace per request |

<!-- Nothing about the agent's logic changes, only who is asking. This reviewer table is the one to build early; the rest of this section expands it. -->

---

## The Wrapper: MLflow `ResponsesAgent`

**The graph is not served directly. It is wrapped.**

- **A compiled graph is an object in memory**, holding an open driver and a live session
- **`ResponsesAgent`** is the interface Model Serving speaks: one request in, output items out
- **Two methods to fill in:** one that answers, one that streams
- **`set_model`** makes the file itself the model, rather than a library beside it

<!-- A LangGraph object must be rebuilt from nothing on a machine no one logged into. Connections open on the first request, not at load, so a failure answers with its reason instead of hiding in build logs. -->

---

## Register to Unity Catalog: Resources vs Credentials

- **Logged as readable source**, not a pickle: `agent.py` ships as the model
- **Requirements are pinned**, not inferred from the notebook that happened to run
- **Databricks objects are declared and granted:** the Genie space, the SQL warehouse, the tables, the embedding endpoint. A Genie grant is not a warehouse grant
- **Everything else is a credential and travels as a reference:** the Neo4j password stays a secret-scope pointer
- **The trap:** declare the Genie space without its warehouse and it deploys cleanly, then every sensor question fails on authorization

<!-- Models-from-code means agent.py ships as source, not a pickle. Aura cannot be granted, so it travels as an environment variable resolved at startup; dbutils does not exist in a serving container, which is why agent.py reads os.environ instead. The warehouse omission fails late and quietly: healthy endpoint, broken telemetry only. -->

---

## Deploy, Then Score

- **One deploy call does four things:** creates the endpoint, attaches the version, applies the environment block, grants the declared resources
- **It returns in under a minute.** The endpoint is live in roughly sixteen
- **Set the MLflow experiment first**, or the endpoint runs with no traces to read
- **Score the endpoint, not a notebook copy:** a routing scorer, plus correctness and relevance
- **Low correctness with routing at 1.0** is a prompt or data problem. **Low routing** is a supervisor problem

<!-- Set the experiment before deploying, or the endpoint produces no traces. routing needs no judge; predict_fn scores the deployed endpoint's own permissions, not a notebook copy. -->

---

## The Names Are a Contract

- **The model name and the endpoint name are functions**, not strings a participant types
- **Both carry the participant's slug**, taken from the same secret scope the credentials come from
- **Endpoint names are unique across the account.** Model names carry the slug too, so thirty people are not writing versions into one model the first of them owns
- **Two write privileges pay for it:** create a model, and create tables, because every deploy writes inference tables beside the model
- **Renaming either breaks Lab 6**, which redeploys *this* endpoint with memory added rather than standing up a second one

<!-- Model name, endpoint name and credentials all trace to the same secret scope so they cannot drift. Do not rename these: Lab 6 expects the same model and endpoint back. -->

---

## Summary

- **One supervisor, three tool nodes**, over Delta telemetry, your own graph, and the Lab 3 manual chunks, looping back to itself until every part of a question has an answer against it
- **Route on where a question starts**, not on what a tool does at the end: two of the three tools finish in a graph traversal
- **Deployed, the graph becomes an endpoint** with its own identity: resources declared and granted, credentials referenced, the model logged as readable source
- **That endpoint is a building block, too:** registered as a serving endpoint, it is what an Agent Bricks Supervisor can route to alongside a Genie Agent with no orchestration code, the same shape Lab 4's instructor demo showed over MCP

<!-- If one thing survives the day: describe the question, not the tool. A no-code Agent Bricks Supervisor can compose this endpoint with other agents the same way the lab composed three tools. -->
