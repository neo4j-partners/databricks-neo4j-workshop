# Lab 3 - Semantic Search for Aircraft Maintenance

In this lab, you'll add semantic search capabilities to your aircraft knowledge graph. Building on the aircraft topology loaded in Lab 2, you'll create a Document-Chunk structure for the A320-200 Maintenance Manual and enable AI-powered retrieval of maintenance procedures.

> **Infrastructure:** This lab uses your **personal** Aura instance. You'll load maintenance manual chunks and generate embeddings into the graph you built in Lab 2.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 2** (Databricks ETL) to load the aircraft graph (Aircraft, System, Component nodes)
- Neo4j Aura credentials from Lab 1 (URI, username, password)
- Running in a **Databricks notebook environment** (for Foundation Model API access)
- **Maintenance manual** already uploaded to the Unity Catalog Volume (pre-loaded by workshop administrators)

## Running Graph Queries

After building the data pipeline in notebook 01, continue with notebooks 02 and 03.

Connect directly to Neo4j Aura using the Python driver and `neo4j-graphrag` library. Uses `VectorRetriever`, `VectorCypherRetriever`, and `GraphRAG` to combine vector search with LLM-generated answers.

**Run:** `01` → `02` → `03` (optional)

## Lab Overview

The notebooks are numbered 01-03 and build on the aircraft graph you loaded in Lab 2.

> **Notebook 01 is required, not just foundational.** It creates the `maintenanceChunkEmbeddings` vector index, and Lab 5's `graphrag_node` queries that index by name. Skip notebook 01 and the Lab 5 agent drops to two tools. Notebook 03 stays optional: Lab 5 uses vector retrieval only, and hybrid retrieval is an exercise there rather than a dependency.

### 01_data_and_embeddings.ipynb - Data Preparation (Required)
Build the foundation for semantic search over maintenance documentation:
- Understand the Document -> Chunk graph structure
- Load the A320-200 Maintenance Manual into Neo4j
- Create Document and Chunk nodes with relationships
- Generate embeddings using Databricks Foundation Model APIs (BGE-large)
- Create vector and fulltext indexes in Neo4j
- Perform similarity search to find relevant maintenance procedures

### 02_graphrag_retrievers.ipynb - Retrieval Strategies
Learn retrieval patterns from simple to graph-enhanced:
- Set up a VectorRetriever using Neo4j's vector index
- Use GraphRAG to combine vector search with LLM-generated answers
- Create custom Cypher queries with VectorCypherRetriever
- Connect maintenance documentation to your aircraft topology
- Compare standard vs. graph-enhanced retrieval results

### 03_hybrid_retrievers.ipynb - Hybrid Search (Optional)
Combine vector similarity with keyword-based fulltext search for more robust retrieval:
- Use HybridRetriever and HybridCypherRetriever to blend vector and keyword results
- Compare hybrid retrieval against pure vector search

## Configuration

Each notebook has a Configuration cell where you enter your Neo4j credentials:

```python
NEO4J_URI = ""  # e.g., "neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = ""  # Your password from Lab 1
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
7. Continue to **notebook 02** to build GraphRAG retrievers

## Files

| File | Description |
|------|-------------|
| `01_data_and_embeddings.ipynb` | Data loading and embedding generation |
| `02_graphrag_retrievers.ipynb` | Retrieval strategies and GraphRAG |
| `03_hybrid_retrievers.ipynb` | Hybrid search combining vector + keyword retrieval (Optional) |
| `data_utils.py` | Utility functions for Neo4j and Databricks |
| `README.md` | This file |

**Note:** The `MAINTENANCE_A320.md` file must be uploaded to the Unity Catalog Volume before running the notebooks.

## Next Steps

Congratulations! You've completed the Semantic Search lab. You can now combine vector search with graph traversal to build powerful GraphRAG retrievers.

Copy and paste queries from the [Sample Queries](SAMPLE_QUERIES.md) page to explore the Document-Chunk structure and fulltext search in the Neo4j Query Workspace.

> **Note:** Vector similarity search is not included in the sample queries because it requires embedding the query text with the same model used to generate the stored embeddings (Databricks BGE-large). The notebooks handle this automatically via the Databricks Foundation Model APIs. See notebooks 02 and 03 for hands-on semantic search examples.

When you're ready, continue to [Lab 4 Part A](../Lab_4_Compound_AI_Agents/PART_A.md) to build the Genie space over sensor telemetry. The retrievers you just built become the `graphrag_node` tool in [Lab 5](../Lab_5_LangGraph_Agent), where a supervisor routes between them, Genie, and direct Cypher.
