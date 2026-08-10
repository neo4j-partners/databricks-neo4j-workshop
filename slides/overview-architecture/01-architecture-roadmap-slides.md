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

# The Aircraft Digital Twin: Dataset and Setup

Aircraft Digital Twins with Neo4j and Databricks

---

## What You Will Build

- **Load** aircraft fleet data into a Neo4j knowledge graph using the Spark Connector
- **Add** semantic search with vector embeddings and GraphRAG retrievers
- **Query** sensor telemetry in natural language with a Databricks Genie Agent
- **Build** a LangGraph supervisor that routes across Genie, Cypher over your own graph, and GraphRAG
- **Give** that agent memory stored in the same graph as the Aircraft Digital Twin
- **Watch** the instructor build the same routing with no code in Agent Bricks over a governed Neo4j MCP connection

<!--
Lab 4 splits in two: Part A is the Genie Agent every participant
builds, Part B is an instructor demo participants only watch. Lab 5's
supervisor ties Genie, Cypher, and GraphRAG together, Lab 6 adds
memory.
-->

---

<style scoped>
section { font-size: 95%; }
</style>

## The Aircraft Digital Twin Dataset

The workshop models a multi-model aviation fleet over 90 operational days:

| Entity | Description |
|--------|-------------|
| Aircraft | Tail numbers, models, operators |
| Systems | Engines, Avionics, Hydraulics per aircraft |
| Components | Turbines, Compressors, Pumps |
| Sensors | Monitoring metadata |
| Sensor Readings | Telemetry every 4 hours over 90 days |
| Flights | Departure/arrival information |
| Maintenance Events | Fault severity and corrective actions |
| Airports | Route network |

<!--
Sensor Readings is the one entity that lives in Databricks, and it is
the highest-volume one by a wide margin. Every other row in this table
has a home in the graph.
-->

---

<style scoped>
section { font-size: 95%; }
</style>

## Workshop Infrastructure: Shared Resources

Shared resources are pre-configured by administrators so participants can focus on the labs.

| Resource | Description |
|----------|-------------|
| **Databricks Data & Tables** | CSV files in Unity Catalog Volume and pre-created Lakehouse tables |
| **Instructor Demo Aura Instance** | Fully populated Neo4j database behind the optional Lab 4 compound agent demo. Participants never connect to it |
| **Neo4j MCP Server** | External MCP server against the demo instance, used only in that optional demo |
| **Databricks MCP Connection** | That MCP server registered in Unity Catalog, in the instructor's workspace |

<!--
Everything here exists before Day 1. Participants never touch the
instructor's Aura instance, MCP server, or MCP connection.
-->

---

## Neo4j Aura

Neo4j Aura is a **fully managed cloud graph database service**. No infrastructure to maintain, automatic scaling with data and query volume, enterprise-grade security, deployed on AWS, GCP, or Azure.

This workshop runs on AuraDB Free.

<!-- Aura is the hosted product everything else builds on. The graph-versus-relational argument already landed twice in the What is a Knowledge Graph deck, so do not run it again here. This slide is the product and the tier you are about to sign up for. -->

---

<style scoped>
section { font-size: 24px; }
</style>

## Aura Developer Tools

**Query Workspace:** Cypher editor with syntax highlighting, auto-completion, saved query collections, and log forwarding to your cloud logging service.

**Explore:** visual, no-code graph exploration on an interactive canvas, no Cypher required.

**Dashboards:** low-code bar charts, line charts, geographic maps, and 3D graph visualizations for non-technical stakeholders.

**Graph Analytics:** Explore includes centrality and community detection. The full 65-plus algorithm library runs through Aura Graph Analytics serverless sessions. AuraDB Free carries none of it: the GDS notebooks here are take-home material, read now, run later on an instance with the plugin.

<!-- Query Workspace is where most lab time is spent. Be direct about the Free tier limit: no PageRank or community detection on this instance. -->

---

## Workshop Infrastructure: Personal Resources

Each participant gets their own environment to work in.

| Resource | Description |
|----------|-------------|
| **Personal Aura Instance** | Your own Neo4j database, created in Lab 1 and used by every required lab after it |
| **Databricks Workspace** | Clone notebooks and run them on a shared cluster to build your graph and agents |

**Every required lab uses your own instance.** Lab 2 loads the graph into it, Lab 3 adds the maintenance manual and vector indexes, Lab 5 queries it, and Lab 6 writes agent memory back to it. A broken load shows up in the next lab, which is the point.

**Lab 4's compound agent demo is optional** and runs against a separate instance. You need no credential, no MCP connection, and no setup for it.

<!--
Lab 4 Part B is an instructor demo, not something participants build.
Everything a participant builds runs against the personal Aura
instance created in Lab 1, and every lab after it depends on the one
before.
-->

---

![bg contain](../../images/workshop-infrastructure.svg)

<!--
Shared resources on one side, personal resources on the other. The
only line crossing from shared to personal is the instructor's demo,
and it runs one direction, instructor to audience.
-->

---

## Workshop Roadmap

**Part 1: Foundations, Labs 1 and 2**
- Lab 1: Provision your Aura instance, learn Cypher
- Lab 2: ETL from Databricks into the graph via the Spark Connector

**Part 2: Retrieval, Labs 3 and 4**
- Lab 3: GraphRAG semantic search over maintenance manuals
- Lab 4 Part A: Genie Agent over lakehouse telemetry
- Lab 4 Part B: **instructor demo**, Neo4j MCP and Agent Bricks supervisor, participants watch

**Part 3: The Supervisor Agent, Lab 5**
- Lab 5: LangGraph supervisor over Genie, Cypher, and GraphRAG, deployed to Model Serving

**Part 4: Agent Memory, Lab 6**
- Lab 6: Agent memory written back to Neo4j

<!--
Labs 1 through 3 build the graph and its retrieval layer. Lab 4 is
the split lab: Part A is required, Part B is instructor-only. Lab 5
brings the routing together in code. Lab 6 closes the loop by writing
back to the same graph that Lab 2 built.
-->
