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

A sensor reading says an engine is running hot. Only the parts, aircraft and manuals behind it say what to do about it.

---

## The Stakes

An airline is putting GenAI agents into workflows where a wrong answer grounds an aircraft or, worse, lets one fly that should not:

- **Dispatch decisions**: whether an aircraft on the ground is cleared to fly today
- **Airworthiness**: safety findings missed or misread against the maintenance record
- **Compliance and audit**: maintenance actions that must be traceable back to the manual that required them

Every one of these needs two things at once: what the sensors read, and what the part those readings came from is attached to. An answer that cannot be explained cannot be used.

---

## Why LLMs Alone Fall Short

- **Hallucination**: an LLM generates the statistically probable answer, not the verified one, and will describe a maintenance action that never happened just as confidently as one that did
- **Knowledge cutoff**: it has no access to this fleet's telemetry, maintenance records, or manuals, no matter how recently it was trained
- **Relationship blindness**: it cannot connect a sensor reading to the system it belongs to, or a fault to every other aircraft that shares the same component

Retrieval closes the first two gaps. Only a graph closes the third.

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

A knowledge graph stores the fleet as records plus the links between them: this sensor sits on that engine, that engine on this aircraft, this repair closed that finding.

- **Connected, verifiable facts**, not pattern-matched chunks
- **Traversal on top of similarity**: fleet context vectors cannot reach
- **Traceable**: every answer walks back through the relationships behind it
- **Fewer tokens**: only the facts the answer needs, not everything that looked similar
- **Governed retrieval**: permissions live in the same graph as the facts

The agent answers from evidence the graph can defend, not a guess about what a manual probably says.

---

## The Evidence

The UK's National Innovation Centre for Data ran 510 complex questions, some needing hundreds of steps. Neo4j sponsored the study, NICD ran it.

- **80% more truthful**: 63 vs 35 on a measure that penalizes hallucination
- **Over 2x precision and recall**: .38 vs .18, .35 vs .15
- **Half the refusals**: vector-only attempted 28.9% of questions, GraphRAG 65.3%
- **Fewer tokens per correct answer**: sections fetched, not whole documents
- **No ontology project**: built from the titles, sections and links the docs had

An agent that declines two questions in three is as unusable as one that guesses.

<small>Source: [Independent study: GraphRAG makes AI agents 80% more truthful](https://neo4j.com/blog/agentic-ai/study-graphrag-ai-agents-80-percent-more-truthful/), Neo4j</small>

<!--
Full NICD report: neo4j.com/whitepapers/nicd-reducing-hallucinations-graphrag/

Two points to land in the room:

The refusal number is the one that changes minds. Vector-only RAG mostly fails
by declining, not by lying, so teams who have only measured hallucination rate
think their system is fine. Ask how useful an assistant is that shrugs at two
out of three real questions.

The last bullet answers the objection that always comes: "a graph means a
six-month data modeling project." NICD hand-engineered nothing. That is the
same thing Lab 3 does to the maintenance manuals in about an hour.
-->

---

## The Proof: The Hero Question

> Which engines are showing abnormal EGT readings, what maintenance history do those aircraft have, and what does the maintenance manual say to do about high EGT?

Answering this needs three stores at once. One of them is the graph: the fleet stored as records plus the links between them, so an engine knows which aircraft it hangs off and which repairs it has seen.

- **Telemetry** for the EGT, Exhaust Gas Temperature, readings themselves, in the Databricks Lakehouse
- **The graph** for the maintenance history behind each aircraft
- **The manuals** for the procedure, retrieved by GraphRAG

No single store answers it. The agent has to route across all three and combine what comes back.

---

## What We Are Building Today

By the end of the workshop, you will have built and deployed exactly this:

- A **LangGraph supervisor agent** routing across a Genie Agent, Cypher over your own Neo4j Aura instance, and GraphRAG retrieval over maintenance manuals
- Deployed to **Databricks Model Serving** for production hosting
- Extended with **persistent memory**, written back into the same Neo4j graph as the Aircraft Digital Twin
- Built end to end on your own Aura instance, not a shared demo

The demo you are about to see is the artifact you will build.

---

## Neo4j + Databricks Partnership

- **Joint focus**: grounding enterprise AI agents in verified data to reduce hallucinations
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
