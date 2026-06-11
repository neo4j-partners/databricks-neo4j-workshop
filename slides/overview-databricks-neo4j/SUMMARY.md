# Databricks + Neo4j: The Better Together Value

## What the Graph Looks Like

- Graphs naturally model the real world
- Data in Neo4j lives as **nodes** (entities/nouns) and **relationships** (how they connect)
- In the diagram: `(parentheses)` are nodes, `[:brackets]` are relationships

```
(Aircraft) -[:HAS_SYSTEM]-> (System) -[:HAS_COMPONENT]-> (Component)
     |
     |--[:OPERATED_FLIGHT]-> (Flight) -[:DEPARTED_FROM]-> (Airport)
                                |
                                |--[:HAD_DELAY]-> (Delay)
```

Every node and relationship can carry properties (names, dates, measurements), so the graph is rich with context — not just connections.

---

## Why Combine Databricks and Neo4j?

- Databricks and Neo4j solve **different problems well**
- **Databricks** excels at large volumes of structured data — aggregations, time-series analysis, and ML over tables
- **Neo4j** excels at understanding **how things connect** — following chains of relationships, finding patterns, and answering questions about structure
- Most real-world problems have both: numbers that need crunching **and** relationships that need navigating

---

## Building a Knowledge Graph from Lakehouse Data

1. **Store your raw data** in Databricks — CSVs, Delta tables, whatever you have
2. **Use the Neo4j Connector** to write that data into Neo4j as nodes and relationships
3. **Not all data moves** — only the subset that fits a graph model (entities and relationships) is extracted
4. **Query the graph** to answer relationship-heavy questions that tables struggle with

**Example:** An aircraft fleet dataset becomes a connected graph where you can naturally ask "which components were on aircraft that had delays after a specific type of maintenance?" — a question that would require many table joins but is a simple graph traversal.

---

## GraphRAG: Smarter Document Search

- **GraphRAG** combines document search with graph context to give AI better answers
- Break documents into chunks, generate embeddings, store chunks in Neo4j linked to the graph
- When someone searches for "how to troubleshoot engine vibration," the system finds relevant text **and** knows which aircraft and components are involved

| Approach | What You Get |
|----------|-------------|
| **Vector search alone** | "Here are text chunks about engine vibration" |
| **GraphRAG** | "Here are text chunks about engine vibration, **plus** the affected aircraft, their maintenance history, and related component data" |

---

## Flexible Vector Store Options

- GraphRAG's vector store is **pluggable** — you are not locked into a single vector database
- **Neo4j** (built-in) — vectors and graph in one database, simplest setup
- **Databricks Vector Search** — keep vectors in your Lakehouse alongside your Delta tables
- **The key insight:** Graph context is the value-add — regardless of where your vectors live

---

## Three Ways to Retrieve Knowledge

- **Vector Search** — find the most relevant text by meaning
- **Graph-Enhanced Search** — find relevant text, then follow graph connections
- **Hybrid Search** — combine meaning-based and keyword-based search for domain-specific terms and fault codes

---

## Neo4j in Unity Catalog: Federated Queries via JDBC

- Neo4j registered as a **JDBC connection in Unity Catalog**
- The driver **automatically translates SQL into Cypher** — users write SQL, Neo4j executes it as a graph query
- **Unified governance** — graph data under the same UC access controls and lineage
- **Federated queries** — combine graph relationships and Lakehouse metrics in a single SQL statement
- **Genie-ready** — materialized graph data powers natural language analytics without Cypher knowledge

---

## Neo4j as an MCP Server

- **Model Context Protocol (MCP)** is an open standard that lets AI agents use external tools
- Neo4j MCP server exposes: **get the schema** and **run read queries**
- An AI agent on Databricks can **explore and query Neo4j on its own** — no pre-built integrations needed

---

## The Data Discovery Problem

- Enterprise lakehouses grow fast — **hundreds of schemas, thousands of tables**
- Analysts spend more time finding and understanding data than analyzing it
- AI agents can write SQL, but struggle to know **which table to query** or **what a column means**
- The graph can fill this gap: a **semantic layer** that maps business meaning onto physical data

---

## Building a Semantic Layer

- **Sync Unity Catalog metadata into Neo4j**: catalogs, schemas, tables, columns as a connected graph
- Layer on **domain knowledge**: business concepts mapped to physical assets, metric definitions, authoritative sources
- Neo4j makes these connections **traversable** — follow paths from business concepts to tables, metrics to sources

---

## Neo4j as a Semantic Layer

- Analysts discover data faster through **business concepts** instead of hunting through schemas
- Agents use **GraphRAG patterns on metadata** — semantic search for a business concept, then traverse to find related schemas, tables, and columns
- Text-to-SQL accuracy jumps when agents understand the domain
- **Complementary to Unity Catalog**: UC governs access and lineage, the graph adds **meaning and connections**

---

## Multi-Agent Analytics

- Data lives in **both** platforms — build specialized AI agents for each
- Create **focused agents** that each do one thing well
- A **supervisor** routes questions to the right agent automatically
- The end user asks a question in plain English — the system figures out where to go

---

## The Genie Space Agent

- Lives entirely in Databricks, built using **Genie Space**
- Answers questions about sensor readings and telemetry — anything in Lakehouse tables
- Translates natural language into SQL

---

## The Neo4j MCP Agent

- Connects to Neo4j through the **MCP server** registered in Unity Catalog
- Answers questions about relationships, structure, and operational history
- Discovers the graph schema through MCP, then generates and runs Cypher queries

---

## The Supervisor: Bringing It Together

```
                User Question
                     |
                     v
            ┌─── Supervisor ───┐
            |                  |
            v                  v
    Genie Space Agent    Neo4j MCP Agent
    (Lakehouse / SQL)    (Graph / Cypher)
```

- **Numbers and trends** → Genie Space Agent
- **Relationships and structure** → Neo4j MCP Agent
- **Both needed** → Calls each agent in sequence, then combines the answers

---

## Multi-Agent Routing in Action

- **"What is the average EGT for engine AC5?"** → Genie agent (numeric aggregation over sensor data)
- **"Which components were serviced on aircraft N10000?"** → Neo4j agent (relationship traversal)
- **"Find aircraft with high vibration readings and show their maintenance history"** → Both agents in sequence, supervisor synthesizes a combined answer

No Cypher or SQL knowledge required from the end user.

---

## Alternative Architecture: Agent as a Serving Endpoint

- Deploy the Neo4j agent as a **Databricks Model Serving endpoint** instead of connecting via MCP at the supervisor level
- Package with MLflow, register in Unity Catalog, deploy as an always-available API
- **Key difference:** The agent's connection to Neo4j is baked into the deployment, giving the agent more control over how it queries the graph

---

## Combining the Deployed Agent with Genie

```
                User Question
                     |
                     v
        ┌─── Supervisor Agent ───┐
        |           (no code)          |
        v                              v
Neo4j Agent Endpoint          Genie Space Agent
(deployed via MLflow)         (Lakehouse / SQL)
```

- Adding or swapping agents is a **UI operation**, not a code change
- The supervisor uses the LLM to understand intent and route — no hand-written routing rules
- Built-in **tracing and feedback collection** through the Databricks Review App

---

## What Each Platform Brings

| | Databricks | Neo4j |
|---|-----------|-------|
| **Stores** | Tables and files | Nodes and relationships |
| **Answers** | "How much?" and "How often?" | "How is this connected?" and "What is affected?" |
| **AI capability** | Foundation Models, Genie | Vector indexes, GraphRAG, MCP |
| **Strength** | Scale, aggregation, ML | Relationships, traversal, pattern matching |

---

## Summary

- The **Neo4j Connector** moves data between the Lakehouse and the Knowledge Graph
- **Lakehouse data becomes a graph** — making implicit relationships explicit and queryable
- **Neo4j as an MCP server** gives AI agents direct access to the knowledge graph
- **Multi-agent systems** route questions to the right platform automatically
- **GraphRAG** combines document search with graph context for smarter AI answers

Together, you get the analytical power of the Lakehouse **and** the relationship intelligence of the graph — connected, not siloed.
