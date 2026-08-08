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


# Neo4j and Databricks Workshop

Build AI Agents and Knowledge Graphs with Neo4j and Databricks

---

## What You'll Build

- **Load** aircraft fleet data into a Neo4j knowledge graph using the Spark Connector
- **Add** semantic search with vector embeddings and GraphRAG retrievers
- **Query** sensor telemetry in natural language with a Databricks Genie space
- **Build** a LangGraph supervisor that routes across Genie, Cypher over your own graph, and GraphRAG
- **Give** that agent memory stored in the same graph as the fleet data
- **Watch** the instructor build the same routing with no code in Agent Bricks over a governed Neo4j MCP connection
- **Create** a no-code Aura Agent with Cypher Templates, Text2Cypher, and Similarity Search

---

## What Is a Digital Twin?

A **digital twin** is a virtual representation of a physical system — its structure, state, and behavior modeled in data.

For an aircraft fleet this means capturing:
- **Topology**: Aircraft, systems, components, and sensors and how they connect
- **Operations**: Flights, routes, delays
- **Maintenance**: Events, faults, component removals, corrective actions
- **Documentation**: Maintenance manuals, procedures, operating limits

---

## Why Knowledge Graphs for Digital Twins?

Digital twins are fundamentally about **relationships** — a component belongs to a system, a system belongs to an aircraft, a fault affects a component, a removal follows a maintenance event.

**Knowledge graphs model this naturally:**
- Entities become **nodes** with properties
- Connections become **relationships** with types and properties
- Multi-hop traversals are native — no expensive JOINs
- The graph *is* the twin — query it, reason over it, extend it

Tabular databases can store the same data, but answering "Which components caused flight delays?" requires chaining multiple JOINs across many tables. In a graph, it's a single traversal.

---

<style scoped>
section { font-size: 95%; }
</style>

## The Aircraft Digital Twin Dataset

The workshop uses a comprehensive dataset modeling a complete aviation fleet over 90 operational days:

| Entity | Count | Description |
|--------|-------|-------------|
| Aircraft | 20 | Tail numbers, models, operators |
| Systems | 80 | Engines, Avionics, Hydraulics per aircraft |
| Components | 320 | Turbines, Compressors, Pumps |
| Sensors | 160 | Monitoring metadata |
| Sensor Readings | 345,600+ | Hourly telemetry over 90 days |
| Flights | 800 | Departure/arrival information |
| Maintenance Events | 300 | Fault severity and corrective actions |
| Airports | 12 | Route network |

---

## Dual Database Architecture

The data is split across two platforms, each chosen for the workload it handles best:

**Databricks Lakehouse** — Time-series sensor telemetry
- 345,600+ hourly readings across 90 days
- Columnar storage and SQL for aggregations, trend analysis, statistical comparisons

**Neo4j Aura** — Richly connected relational data
- Aircraft topology, component hierarchies, maintenance events, flights, delays, airport routes
- Native multi-hop traversals without expensive JOINs

A multi-agent supervisor routes questions to the right database automatically.

---

![bg contain](../../images/dual-database-architecture.svg)

---

<style scoped>
section { font-size: 95%; }
</style>

## Workshop Infrastructure: Shared Resources

Shared resources are pre-configured by administrators so participants can focus on the labs:

| Resource | Description |
|----------|-------------|
| **Databricks Data & Tables** | CSV files in Unity Catalog Volume and pre-created Lakehouse tables |
| **Instructor Demo Aura Instance** | Fully populated Neo4j database behind the Lab 4 Part B demo. Participants never connect to it |
| **Neo4j MCP Server** | External MCP server against the demo instance, used only in the Part B demo |
| **Databricks MCP Connection** | That MCP server registered in Unity Catalog, in the instructor's workspace |

---

## Workshop Infrastructure: Personal Resources

Each participant gets their own environment to work in:

| Resource | Description |
|----------|-------------|
| **Personal Aura Instance** | Your own Neo4j database, created in Lab 1 and used by every required lab after it |
| **Databricks Workspace** | Clone notebooks and run them on a shared cluster to build your graph and agents |

**Every required lab uses your own instance.** Lab 2 loads the fleet into it, Lab 3 adds the maintenance manual and vector indexes, Lab 5 queries it, and Lab 6 writes agent memory back to it. A broken load shows up in the next lab, which is the point.

**Lab 4 Part B is an instructor demo** against a separate instance. You need no credential, no MCP connection, and no setup for it.

---

![bg contain](../../images/workshop-infrastructure.svg)
