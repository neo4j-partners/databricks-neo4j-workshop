# Lab 3 - Semantic Search for Aircraft Maintenance

In this lab, you'll add semantic search capabilities to your aircraft knowledge graph. Building on the aircraft topology loaded in Lab 2, you'll create a Document-Chunk structure for the A320-200 Maintenance Manual and enable AI-powered retrieval of maintenance procedures.

> **Infrastructure:** This lab uses your **personal** Aura instance. You'll load maintenance manual chunks and generate embeddings into the graph you built in Lab 2.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 2** (Databricks ETL) to load the aircraft graph (Aircraft, System, Component nodes)
- Neo4j Aura credentials from Lab 1 (URI, username, password)
- Running in a **Databricks notebook environment** (for Foundation Model API access)
- **Maintenance manual** already uploaded to the Unity Catalog Volume (pre-loaded by workshop administrators)

## Two Ways to Query the Graph

After building the data pipeline in notebook 01, you have two options for running graph queries. Choose based on your setup:

### Path A: Direct Neo4j Connection (Notebooks 02 + 03)

Connect directly to Neo4j Aura using the Python driver and `neo4j-graphrag` library. This path uses `VectorRetriever`, `VectorCypherRetriever`, and `GraphRAG` to combine vector search with LLM-generated answers.

**When to use:** You have Neo4j credentials and want to use the full `neo4j-graphrag` retriever abstractions with Databricks Foundation Model APIs for embeddings and LLM generation.

**Run:** `01` → `02` → `03` (optional)

### Path B: Neo4j MCP Server (Notebook 04)

> **Under construction:** Path B is currently unavailable. Notebook 04 is broken and being actively worked on. Follow Path A for now.

Query the same graph through a remote **MCP server** using the FastMCP client. Instead of connecting to Neo4j directly, your notebook talks to an MCP server that manages the database connection. You write explicit Cypher queries and send them via MCP's `read-cypher` tool.

**When to use:** You have MCP server credentials (endpoint URL + API key) and want to explore graph queries without direct database access. No Neo4j credentials or embedding model needed — uses fulltext search instead of vector search.

**Run:** `01` → `04`

### Key Differences

| | Direct Neo4j (Path A) | MCP Server (Path B) |
|---|---|---|
| **Connection** | `neo4j://` driver with DB credentials | HTTPS + API key to MCP server |
| **Search** | Vector similarity (embeddings) | Fulltext keyword search |
| **Dependencies** | `neo4j`, `neo4j-graphrag`, Databricks LLM/Embedder | `fastmcp` only |
| **Abstraction** | `VectorRetriever` / `VectorCypherRetriever` | Explicit Cypher via `read-cypher` tool |
| **LLM answers** | Yes (GraphRAG pipeline) | No (raw query results) |
| **Best for** | Application code, GraphRAG pipelines | AI agents, tool-calling, decoupled access |

## Lab Overview

The notebooks are numbered 01-04 and build on the aircraft graph you loaded in Lab 2.

### 01_data_and_embeddings.ipynb - Data Preparation (Required for both paths)
Build the foundation for semantic search over maintenance documentation:
- Understand the Document -> Chunk graph structure
- Load the A320-200 Maintenance Manual into Neo4j
- Create Document and Chunk nodes with relationships
- Generate embeddings using Databricks Foundation Model APIs (BGE-large)
- Create vector and fulltext indexes in Neo4j
- Perform similarity search to find relevant maintenance procedures

### 02_graphrag_retrievers.ipynb - Retrieval Strategies (Path A)
Learn retrieval patterns from simple to graph-enhanced:
- Set up a VectorRetriever using Neo4j's vector index
- Use GraphRAG to combine vector search with LLM-generated answers
- Create custom Cypher queries with VectorCypherRetriever
- Connect maintenance documentation to your aircraft topology
- Compare standard vs. graph-enhanced retrieval results

### 03_hybrid_retrievers.ipynb - Hybrid Search (Optional, Path A)
Combine vector similarity with keyword-based fulltext search for more robust retrieval:
- Use HybridRetriever and HybridCypherRetriever to blend vector and keyword results
- Compare hybrid retrieval against pure vector search

### 04_mcp_graph_queries.ipynb - MCP Graph Queries (Path B)
> **Under construction:** This notebook is currently broken and being actively worked on.

Query the knowledge graph through an MCP server:
- Connect to a remote MCP server using the FastMCP client
- Discover available tools and retrieve the graph schema
- Execute Cypher queries via MCP's `read-cypher` tool
- Replicate the same retrieval patterns from notebook 02 using fulltext search
- Understand how MCP decouples clients from database credentials

## Configuration

**Path A (Direct Neo4j):** Each notebook has a Configuration cell where you enter your Neo4j credentials:

```python
NEO4J_URI = ""  # e.g., "neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = ""  # Your password from Lab 1
```

**Path B (MCP Server):** Notebook 04 has a Configuration cell where you enter your MCP server details:

```python
MCP_ENDPOINT = ""  # e.g., "https://neo4jmcp-app-dev.example.com"
MCP_API_KEY = ""   # Your API key from the MCP_ACCESS config
```

The embedding and LLM models use Databricks Foundation Model APIs which are pre-deployed and require no additional configuration. When running in Databricks, the MLflow deployments client automatically handles authentication.

## Getting Started

1. Ensure Lab 2 is complete (aircraft topology loaded)
2. Verify the maintenance manual is uploaded to the Volume:
   ```
   /Volumes/databricks-neo4j-workshop/aircraft/raw_data/MAINTENANCE_A320.md
   ```
3. Upload the notebook files and `data_utils.py` to your Databricks workspace
4. Open `01_data_and_embeddings.ipynb`
5. Enter your Neo4j credentials in the Configuration cell
6. Run cells sequentially to load the maintenance manual and create embeddings
7. Continue to **notebook 02** (direct Neo4j) or **notebook 04** (MCP server)

## Files

| File | Description |
|------|-------------|
| `01_data_and_embeddings.ipynb` | Data loading and embedding generation |
| `02_graphrag_retrievers.ipynb` | Retrieval strategies and GraphRAG (Path A) |
| `03_hybrid_retrievers.ipynb` | Hybrid search combining vector + keyword retrieval (Optional) |
| `04_mcp_graph_queries.ipynb` | MCP-based graph queries (Path B, under construction) |
| `data_utils.py` | Utility functions for Neo4j and Databricks |
| `README.md` | This file |

**Note:** The `MAINTENANCE_A320.md` file must be uploaded to the Unity Catalog Volume before running the notebooks.

## Next Steps

Congratulations! You've completed the Semantic Search lab. You can now combine vector search with graph traversal to build powerful GraphRAG retrievers.

Copy and paste queries from the [Sample Queries](SAMPLE_QUERIES.md) page to explore the Document-Chunk structure and fulltext search in the Neo4j Query Workspace.

> **Note:** Vector similarity search is not included in the sample queries because it requires embedding the query text with the same model used to generate the stored embeddings (Databricks BGE-large). The notebooks handle this automatically via the Databricks Foundation Model APIs. See notebooks 02 and 03 for hands-on semantic search examples.

When you're ready, continue to [Lab 4 - Compound AI Agents](../Lab_4_Compound_AI_Agents) to build a Supervisor Agent that routes questions between a Genie space and Neo4j MCP.
