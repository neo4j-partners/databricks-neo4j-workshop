# Lab 2: Databricks ETL to Neo4j

Load aircraft data from Databricks into Neo4j using the Spark Connector.

> **Infrastructure:** This lab uses the Vocareum lab environment for the Databricks workspace setup and notebook execution.

**Duration:** ~45 minutes for the core notebooks, plus optional extra time for the Graph Data Science notebooks

---

## Core Notebooks

The core flow is two notebooks:

| Notebook | Description | Required For |
|----------|-------------|--------------|
| [`01_aircraft_etl_to_neo4j.ipynb`](01_aircraft_etl_to_neo4j.ipynb) | Guided walkthrough that teaches the Spark Connector mechanics by loading Aircraft, System, and Component nodes | Learning the ETL pattern |
| [`02_load_neo4j_full.ipynb`](02_load_neo4j_full.ipynb) | Clears the database first (`CLEAR_DATABASE = True`), then loads the complete canonical dataset: Aircraft, Systems, Components, Sensors, Airports, Flights, Delays, Maintenance Events, and Removals | **Labs 3, 4** |

> **Important:** Run **both** notebooks before proceeding. Notebook 01 is the guided walkthrough that teaches how the Spark Connector works. Notebook 02 clears the database and loads the full canonical dataset, so its output is what Labs 3 and 4 depend on.

---

## Optional: Graph Data Science Notebooks

Four optional, more advanced notebooks apply Neo4j Graph Data Science (GDS) algorithms to the loaded graph. All four require notebook 02 to have been run first, and they require the Neo4j Graph Data Science plugin. Notebooks 03 and 04 include a `gds.version()` check cell you can use to confirm GDS is available on your instance.

| Notebook | Algorithm | What It Does |
|----------|-----------|--------------|
| [`03_gds_louvain_maintenance.ipynb`](03_gds_louvain_maintenance.ipynb) | Louvain | Community detection on maintenance events, grouping aircraft into risk communities based on shared fault patterns |
| [`04_gds_knn_aircraft.ipynb`](04_gds_knn_aircraft.ipynb) | kNN | Computes per-aircraft feature vectors from sensor and maintenance data, then writes `SIMILAR_PROFILE` relationships between similar aircraft |
| [`05_gds_pagerank_airports.ipynb`](05_gds_pagerank_airports.ipynb) | PageRank + Betweenness | Centrality analysis on the airport route network, writing `pagerank_score` and `betweenness_score` to Airport nodes |
| [`06_gds_node_similarity_aircraft.ipynb`](06_gds_node_similarity_aircraft.ipynb) | Node Similarity | Jaccard similarity over shared fault types, writing `SIMILAR_FAULT_PROFILE` relationships between aircraft |

> **Note:** Notebook 06's comparison queries assume notebook 04 has already run.

---

## Prerequisites

Before starting this lab, ensure you have:

- [ ] Neo4j Aura credentials from Lab 1 (URI, username, password)
- [ ] Vocareum lab environment access

---

## Instructions

Use the Vocareum lab setup to complete the Databricks workspace configuration and run the ETL notebooks.

---

## What You Loaded

After notebook 02 completes, Neo4j holds the full Aircraft Digital Twin graph: 36 aircraft, 144 systems, 612 components, 288 sensors, and roughly 14,500 flights with their delays, maintenance events, and removals. The 155,520 sensor readings stay in Databricks Delta tables. For the full schema reference, see [DATA_GENERATOR.md](../workshop-setup/populate_aircraft_db/DATA_GENERATOR.md).

---

## Troubleshooting

### "Connection refused" or timeout errors

- Verify your Neo4j URI starts with `neo4j+s://` (note the `+s`)
- Check your Neo4j Aura instance is running (green status in console)
- Confirm username and password are correct (no extra spaces)

### "Spark Connector not found" error

- Ensure you're using the workshop compute (not a personal compute)
- The cluster must be in **Dedicated (Single User)** access mode
- Try restarting the compute

### "Path does not exist" for data files

- Verify the DATA_PATH matches your workshop configuration
- Ask your instructor for the correct Volume path

### Duplicate nodes appearing

- The notebook uses Overwrite mode, so re-running should replace data
- If needed, clear your Neo4j database first:
  ```cypher
  MATCH (n) DETACH DELETE n
  ```

### Notebook cells failing

- Run cells in order from top to bottom
- Don't skip the configuration cells
- Check the error message for specific issues

---

## Key Concepts

This lab introduced Unity Catalog Volumes, where the workshop CSV files live, and the Neo4j Spark Connector, which writes Spark DataFrames into Neo4j as nodes and relationships.

---

## Explore Further

| File | Description |
|------|-------------|
| [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md) | Library of sample Cypher queries covering schema, aircraft topology, sensors, maintenance, flights, removals, and cross-domain analysis, with concept notes for each |
| [aura-explore.md](aura-explore.md) | Five progressive queries that build a graph visualization story in Aura Explore, from one aircraft out to its peer similarity network |
| [data-exploring.md](data-exploring.md) | Sample Cypher queries for creating nodes with `MERGE` and exploring the loaded dataset, from schema census to multi-hop patterns |
| [gds-exploring.md](gds-exploring.md) | Companion queries for the GDS notebooks: inspect projections, re-run individual algorithm steps, and explore the written results |

---

## Next Steps

After completing this lab:
- Continue to [Lab 3 - Semantic Search](../Lab_3_Semantic_Search) to add GraphRAG capabilities over maintenance documentation
- Continue to [Lab 4 - Compound AI Agents](../Lab_4_Compound_AI_Agents) to build a Supervisor Agent with Genie space and Neo4j MCP
- The data you loaded will be queried by AI agents in later labs

---

## Help

- Ask your instructor for assistance
- Check the [Neo4j Spark Connector docs](https://neo4j.com/docs/spark/current/)
- Review the [Cypher Query Language reference](https://neo4j.com/docs/cypher-manual/current/)
