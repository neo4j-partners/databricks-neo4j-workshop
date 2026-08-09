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

# The Business Case for GraphRAG

Why an AI agent flying a fleet needs to be grounded in a knowledge graph

---

## The Stakes

An airline is putting GenAI agents into workflows where a wrong answer grounds an aircraft or, worse, lets one fly that should not:

- **Dispatch decisions**: whether an aircraft on the ground is cleared to fly today
- **Airworthiness**: safety findings missed or misread against the maintenance record
- **Compliance and audit**: maintenance actions that must be traceable back to the manual that required them

An answer that cannot be explained cannot be used.

---

## The Problem Vectors Do Not Solve

Vector search finds text that is **similar**, but it cannot **traverse relationships**.

In a fleet, that gap hides exactly what matters:

- **The same component type failing** across different aircraft never surfaces from chunk similarity alone
- **A sensor reading** only means something once you know which system and which aircraft it hangs off
- **A manual procedure** that applies to one aircraft variant does not apply to another, and chunk similarity cannot tell them apart

Similar text is not the same as connected fact.

---

## The Shift to GraphRAG

GraphRAG grounds the agent in a knowledge graph:

- Retrieval returns **connected, verifiable facts**, not pattern-matched chunks
- Graph traversal adds fleet context on top of vector similarity
- Every answer **traces back** through the relationships that produced it

The agent answers from evidence the graph can defend, not from a statistical guess about what an engine manual probably says.

---

## Context Graphs and Decision Governance

An agent that routes across tools and answers over many turns needs a record of what it knew and when.

Lab 6 builds exactly that:

- A **recall node** reads what the graph already knows about an aircraft before the supervisor answers
- A **remember node** writes new facts back afterward
- Both writes land as **nodes and relationships** in the same graph that holds the fleet data, not a separate log a different team owns

Governance is not bolted on afterward. It lives in the same graph as the data.

---

## The Proof: The Hero Question

> Which engines are showing abnormal EGT readings, what maintenance history do those aircraft have, and what does the maintenance manual say to do about high EGT?

Answering this needs three stores at once:

- **Telemetry** for the EGT readings themselves, in the Databricks Lakehouse
- **The graph** for the maintenance history behind each aircraft
- **The manuals** for the procedure, retrieved by GraphRAG

No single store answers it. The agent has to route across all three and combine what comes back.

---

## What We Are Building Today

By the end of the workshop, you will have built and deployed exactly this:

- A **LangGraph supervisor agent** routing across a Genie Agent, Cypher over your own Neo4j Aura instance, and GraphRAG retrieval over maintenance manuals
- Deployed to **Databricks Model Serving** for production hosting
- Extended with **persistent memory**, written back into the same Neo4j graph as the fleet data
- Built end to end on your own Aura instance, not a shared demo

The demo you are about to see is the artifact you will build.

---

## Why LLMs Alone Fall Short

- **Hallucination**: an LLM generates the statistically probable answer, not the verified one, and will describe a maintenance action that never happened just as confidently as one that did
- **Knowledge cutoff**: it has no access to this fleet's telemetry, maintenance records, or manuals, no matter how recently it was trained
- **Relationship blindness**: it cannot connect a sensor reading to the system it belongs to, or a fault to every other aircraft that shares the same component

Deck 4 returns to each of these limitations in depth.

---

## Neo4j + Databricks Partnership

- **Joint focus**: grounding enterprise AI agents in verified data to reduce hallucinations
- **Spark Connector**: projects governed Delta tables directly into a Neo4j graph, the same pattern this workshop's own data pipeline uses
- **Neo4j MCP Server**: exposes schema discovery and read-only Cypher as standard agent tools, reachable from Databricks Agent Bricks and from any MCP-aware framework
- Neo4j and Databricks continue to deepen this integration across the agent and lakehouse stack

<!--
Instructor: replace the roadmap line with the current, approved Neo4j +
Databricks partnership talking points for your event. Keep any forward-looking
product claims to what has been publicly announced.
-->

---

## Opening Demo

See the finished build answer the hero question live.

<!--
Instructor run instructions:

Run the hero question live against the pre-deployed Lab 5 Model Serving
endpoint (deployed before the event, against the instructor's own Aura
instance loaded with the seed dataset):

"Which engines are showing abnormal EGT readings, what maintenance history do
those aircraft have, and what does the maintenance manual say to do about high
EGT?"

Show the agent's tool calls so the room sees routing happen across Genie, the
graph, and GraphRAG, not just the final answer.

Keep the endpoint live all day so attendees can hit it during breaks. Point
back to this demo from each lab: Lab 3 builds the retriever behind the manual
answer, Lab 5 builds the supervisor that routes the question, Lab 6 adds the
memory that lets it recall this conversation later.
-->
