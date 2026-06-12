[Workshop Site](https://neo4j-partners.github.io/databricks-neo4j-workshop)

# Hands-On Workshop: Neo4j and Databricks

## What You Will Build

By the end of this workshop you will have a working AI system that answers natural language questions about a commercial aviation fleet. Ask it a question and a Supervisor Agent decides which of two specialized backends can best answer it: Neo4j for relationship questions and Databricks for sensor trend questions.

The system answers two fundamentally different kinds of questions:

- **Relationship questions** such as "Which components have had critical failures, and which flights did those failures delay?" are best answered by traversing a graph.
- **Time-series analytics questions** such as "How have engine temperature readings trended over the last 90 days?" are best answered by running SQL over columnar data.

A single database handles one kind well but not both. This workshop shows how to pair Neo4j and Databricks so each handles the workload it is built for, then connect them through a shared AI layer.

The dataset is an Aircraft Digital Twin: a simulated aviation fleet with real structure. Aircraft have systems and components. Components generate sensor readings and accumulate maintenance events. Aircraft operate flights between airports, and those flights can have delays tied to specific component failures. The combination gives you a realistic, richly connected dataset that exercises both the graph and the analytics platform.

---

## Workshop Architecture

The end-to-end architecture routes each user question to the backend best suited to answer it:

- **Supervisor Agent** (Databricks Agent Bricks): receives user questions and decides which specialized agent to call
- **Genie Agent**: handles sensor telemetry analytics using natural language SQL over Unity Catalog tables
- **Neo4j MCP Agent**: handles graph-powered queries over the knowledge graph using the Model Context Protocol
- **Neo4j Aura**: the graph database storing aircraft relationships, maintenance history, and flight operations
- **Databricks**: provides notebooks, model serving, and vector search

![Workshop Architecture Overview](images/lab-architecture-overview.png)

## Dual Database Architecture

The workshop is built on a dual database architecture that assigns each workload to the platform best suited for it:

- **Databricks Lakehouse** handles high-volume time-series sensor telemetry, optimized for aggregations, trend analysis, and statistical queries over columnar data.
- **Neo4j Aura** stores the richly connected relational data: aircraft topology, component hierarchies, maintenance events, flights, and airport routes, traversing multi-hop relationships natively without expensive JOINs.

![Dual Database Architecture](images/dual-database-architecture.png)

---

## Overview

Participants work through lab exercises in Databricks and Neo4j Aura, using Databricks as the notebook environment for ETL, multi-agent orchestration, and semantic search.

### Data Overview

The workshop uses a comprehensive **Aircraft Digital Twin** dataset that models a complete aviation fleet over 90 operational days. The data is split across two platforms, each chosen for the workload it handles best:

- **Databricks Lakehouse** stores the **time-series sensor telemetry**, roughly 155K readings across 90 days. Columnar storage and SQL make the Lakehouse ideal for aggregations, trend analysis, and statistical comparisons over large volumes of timestamped data.
- **Neo4j Aura** stores the **richly connected relational data**: aircraft topology, component hierarchies, maintenance events, flights, delays, and airport routes. A graph database handles multi-hop relationship traversals natively, avoiding the expensive JOINs a tabular database would require for queries like "Which components caused flight delays?"

Together the dataset includes:

- **Aircraft** with tail numbers, models, and operators
- **Systems** (Engines, Avionics, Hydraulics)
- **Components** (Turbines, Compressors, Pumps, etc.)
- **Sensors** with monitoring metadata
- **Sensor Readings** (telemetry every 4 hours over 90 days)
- **Flights** with departure/arrival information
- **Maintenance Events** with fault severity and corrective actions
- **Airports** in the route network

### Key Technologies

| Technology | Purpose |
|------------|---------|
| **Neo4j Aura** | Graph database for storing aircraft relationships |
| **Databricks** | Notebooks, Unity Catalog |
| **AI/BI Genie** | Natural language analytics over Unity Catalog tables |
| **Agent Bricks: Supervisor Agent** | No-code multi-agent supervisor combining multiple data sources |
| **GraphRAG** | Graph-enhanced retrieval combining vector search with graph traversal |
| **Neo4j Spark Connector** | ETL from Databricks to Neo4j |
| **Model Context Protocol (MCP)** | Standard for connecting AI models to data sources |

---

## Workshop Structure

### Phase 1: Setup

*Get connected to all workshop resources.*

| Lab | Description | Time |
|-----|-------------|------|
| [Lab 1 - Neo4j Aura Setup](./Lab_1_Aura_Setup) | Create an Aura free trial, save credentials, learn Cypher basics | 20 min |

---

### Phase 2: Databricks ETL & Semantic Search

*Load aircraft data into Neo4j, then add semantic search capabilities: chunk maintenance documentation, generate vector embeddings, and build GraphRAG retrievers.*

| Lab | Description | Time |
|-----|-------------|------|
| [Lab 2 - Databricks ETL to Neo4j](./Lab_2_Databricks_ETL_Neo4j) | Load Aircraft Digital Twin data into Neo4j using the Spark Connector | 45 min |
| [Lab 3 - Semantic Search](./Lab_3_Semantic_Search) | Load maintenance manual, generate embeddings, build GraphRAG retrievers | 45 min |

---

### Phase 3: Multi-Agent Analytics

*Build a multi-agent supervisor that combines the Databricks Lakehouse with the Neo4j knowledge graph.*

| Lab | Description | Time |
|-----|-------------|------|
| [Lab 4 - Compound AI Agents](./Lab_4_Compound_AI_Agents) | Build a Supervisor Agent combining Genie space (sensor analytics) + Neo4j MCP (graph queries) | 75 min |

---

## Prerequisites

- **Laptop** with a modern web browser
- **Network Access** to Databricks and Neo4j Aura
- Neo4j Aura free trial account (created in Lab 1)
- Databricks workspace with Model Serving enabled
- No local software installation required

---

## Knowledge Graph Schema

The knowledge graph models a commercial aviation fleet as a connected network of physical things, operational events, and documentation.

- **Aircraft and their physical structure.** Each aircraft has a tail number, model, and operator. An aircraft contains three main systems: Engines, Avionics, and Hydraulics. Each system contains multiple components. Engines hold turbines and compressors; hydraulic systems hold pumps and actuators. Every component is monitored by one or more sensors that record health and performance readings.

- **Maintenance history.** When a component develops a fault, a maintenance event is recorded against that component. Each event captures the fault description, its severity, the corrective action taken, and when it was reported. Some components are physically removed and replaced, creating a removal record linked to the maintenance event that triggered it.

- **Flight operations.** Aircraft operate flights between airports. Each flight has a flight number, departure airport, and arrival airport. A flight can have one or more delays, and each delay records its cause and duration in minutes. Delays can be traced back through the graph to the specific component failure that caused them.

- **Maintenance documentation.** Technical maintenance manuals are stored as documents and broken into overlapping chunks for semantic search. Each chunk carries a vector embedding so the system can retrieve relevant passages using natural language queries. Chunks link back to their source document and chain to adjacent chunks for context.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Graph Database | Neo4j Aura |
| Embeddings | Databricks BGE-large (databricks-bge-large-en) |
| LLM | Databricks Llama 3.3 70B |
| Vector Search | Neo4j Vector Index |
| Multi-Agent | Databricks Agent Bricks: Supervisor Agent |
| ETL | Neo4j Spark Connector |

## Configuration

Each notebook has a **Configuration** cell at the top where you enter your Neo4j credentials:

```python
NEO4J_URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_password_here"
```

Databricks notebooks use Foundation Model APIs, which handle authentication automatically when running in Databricks.

## Resources

### Neo4j
- [Neo4j Aura Documentation](https://neo4j.com/docs/aura/)
- [neo4j-graphrag Python Library](https://neo4j.com/docs/neo4j-graphrag-python/)
- [Neo4j MCP Server](https://github.com/neo4j/mcp)
- [Neo4j Spark Connector](https://neo4j.com/docs/spark/current/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

### Databricks
- [Foundation Model APIs](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/)
- [AI/BI Genie](https://docs.databricks.com/aws/en/genie/)
- [Agent Bricks: Supervisor Agent](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor)
- [Databricks Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/)

## Feedback

We appreciate your feedback! Please open an issue on the [GitHub repository](https://github.com/neo4j-partners/databricks-neo4j-workshop/issues) for bugs, suggestions, or comments.
