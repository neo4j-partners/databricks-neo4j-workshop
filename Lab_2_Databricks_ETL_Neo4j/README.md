# Lab 2: Databricks ETL to Neo4j

Load aircraft data from Databricks into Neo4j using the Spark Connector.

> **Infrastructure:** This lab uses the Vocareum lab environment for the Databricks workspace setup and notebook execution.

**Duration:** ~45 minutes for the core notebook, plus optional extra time for the Graph Data Science notebook

---

## Core Notebook

The core flow is a single notebook:

| Notebook | Description | Required For |
|----------|-------------|--------------|
| [`01_aircraft_etl_to_neo4j.ipynb`](01_aircraft_etl_to_neo4j.ipynb) | Guided walkthrough that teaches the Spark Connector mechanics while loading the complete canonical dataset: Aircraft, Systems, Components, Sensors, Airports, Flights, Delays, Maintenance Events, and Removals. Clears the database first (`CLEAR_DATABASE = True`) | **Labs 3, 5, 6** |

> **Important:** Run this notebook before proceeding. It teaches how the Spark Connector works while clearing the database and loading the full canonical dataset, so its output is what Labs 3, 5, and 6 depend on.

---

## Optional: Graph Data Science Notebook

One optional notebook applies a Neo4j Graph Data Science algorithm to the loaded graph. It requires notebook 01 to have been run first and requires the Neo4j Graph Data Science plugin. A `gds.version()` check cell is included so you can confirm GDS is available on your instance.

| Notebook | Algorithm | What It Does |
|----------|-----------|--------------|
| [`02_gds_knn_aircraft.ipynb`](02_gds_knn_aircraft.ipynb) | kNN | Builds per-aircraft feature vectors from both Databricks sensor telemetry and Neo4j maintenance data, then writes `SIMILAR_PROFILE` relationships between the three most similar peer aircraft |

> **Going deeper:** Three additional GDS notebooks covering Louvain community detection, PageRank centrality, and Node Similarity are in [Appendix A](../Appendix_A_GDS_Graph_Analytics/).

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

After notebook 01 completes, Neo4j holds the full Aircraft Digital Twin graph: the fleet with its systems, components, and sensors, plus flights, delays, maintenance events, and removals. The sensor readings stay in Databricks Delta tables. For the full schema reference, including exact row counts, see [DATA_GENERATOR.md](../workshop-setup/populate_aircraft_db/DATA_GENERATOR.md).

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
| [Appendix A — gds-exploring.md](../Appendix_A_GDS_Graph_Analytics/gds-exploring.md) | Companion queries for GDS notebooks: inspect projections, re-run individual algorithm steps, and explore written results |

---

## Next Steps

After completing this lab:
- Continue to [Lab 3 - Semantic Search](../Lab_3_Semantic_Search) to add GraphRAG capabilities over maintenance documentation
- Continue to [Lab 4 - Compound AI Agents](../Lab_4_Compound_AI_Agents) to build a Genie space over the lakehouse telemetry in Part A. Part B, which adds a Supervisor Agent over Neo4j MCP, is optional and advanced
- Continue to Lab 5 to build a LangGraph agent over Genie, your own Aura instance, and the Lab 3 retrievers, then Lab 6 to give that agent memory in Neo4j
- The data you loaded will be queried by AI agents in later labs

---

## Help

- Ask your instructor for assistance
- Check the [Neo4j Spark Connector docs](https://neo4j.com/docs/spark/current/)
- Review the [Cypher Query Language reference](https://neo4j.com/docs/cypher-manual/current/)
