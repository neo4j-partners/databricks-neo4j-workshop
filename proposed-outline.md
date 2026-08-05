# Proposed Workshop Outline

A condensed proposal for restructuring the Neo4j and Databricks workshop. The goal is to focus on the core value proposition of Neo4j, building AI agents powered by knowledge graphs, and streamline the setup process. The new flow: why this matters, what you'll build, then walk through building it, ending with a clear next step for attendees.


## 1. Workshop Overview and What We're Building

Attendees hear the business story first, unplanned component failures grounding aircraft and delaying flights, then watch a live demo of the finished Fleet Ops Assistant. Every setup step afterward is progress toward a destination they have already seen.

- Open with the pain: fleet data is fragmented, and relationship questions like "which component failures caused flight delays" are painful in SQL alone.
- Frame the technical problem: LLMs hallucinate, and vector search cannot traverse relationships. These create answers that sound confident but are wrong, and blind spots on multi-hop questions that require following chains from component to maintenance event to flight delay. Grounding the agent in a knowledge graph addresses both.
- Introduce the pattern: a dual-database architecture where Neo4j owns relationships and the Databricks Lakehouse owns time-series telemetry at scale.
- Live demo the finished Fleet Ops Assistant from a pre-provisioned instructor environment: one question answered by Genie over Lakehouse telemetry, one by the Neo4j MCP agent over the graph, one compound question that needs both.
- Show the finished architecture slide so participants can see the end solution.
- Anchor the session on one memorable question the system can answer: "Which component failures caused flight delays, and are those components showing abnormal sensor trends elsewhere in the fleet?" By Lab 4, attendees ask it in plain English and get a real answer.

## 2. Lab 1: Neo4j Aura Setup

Simplified Aura setup with no extra steps. Attendees walk through the Aura free trial sign-up directly, which cuts setup time and gets everyone to a running graph database fast.

- Sign up for the Aura free trial in the browser.
- Create the free instance and save the connection URI and credentials for use in later labs.
- Quick Cypher orientation: run a few starter queries to get comfortable with nodes and relationships.
- Position the lab as the on-ramp: about 20 minutes, and every later lab connects to this instance.

## 3. Lab 2: Databricks ETL to Neo4j

Load the Aircraft Digital Twin dataset into Neo4j using the Spark Connector. Framed as "loading the data the agent you just saw queried" so the DBA work has a visible purpose.

- Run the ETL notebook to move aircraft, systems, components, sensors, flights, and maintenance events from Delta tables into Neo4j.
- Verify the loaded graph with sample Cypher queries: component hierarchies, maintenance history, delay tracing.
- Explore the dual-database split: telemetry stays in the Lakehouse, relationships live in the graph, and Aircraft, Systems, and Sensors exist in both as join points.
- About 45 minutes, with a "where this fits" callout tying the lab back to the opening demo.

## 4. Lab 3: Semantic Search and GraphRAG

Add the AI retrieval layer over maintenance documentation: chunk the manuals, generate embeddings, and build GraphRAG retrievers that combine vector similarity with graph traversal.

- Chunk the maintenance manual and generate embeddings with Databricks BGE-large.
- Create the Neo4j vector index and run semantic searches over the chunks.
- Build GraphRAG retrievers that start from a semantic hit and traverse the graph for connected context: components, faults, corrective actions.
- Compare plain vector search against graph-enriched retrieval to show why the graph matters.
- About 45 minutes.

## 5. Lab 4: Compound AI Agents

The payoff. Attendees build the same Fleet Ops Assistant they saw in the opening demo: a Genie space for sensor analytics plus a Neo4j MCP agent for graph queries, unified under an Agent Bricks Supervisor Agent.

- Create a Genie space for natural language SQL over the sensor telemetry tables.
- Connect the Neo4j MCP agent so the system can run Cypher over the knowledge graph.
- Assemble the Supervisor Agent in Agent Bricks to route questions to the right backend.
- Ask the anchor question from the opening and watch their own build answer it.
- About 75 minutes.

## 6. Close: Call to Action

Close by turning what attendees built into their next step. Talk through other potential use cases tailored to the audience, share customer proof, and make one clear ask so attendees leave ready to book a conversation about their own data.

- Make one clear ask: book a scoping session with an AE or SE, with a QR code on the final slide.
- Run a short exit survey with a qualifying question about graph use cases, and route interested attendees to the account team.
