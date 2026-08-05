# Neo4j + Databricks Workshop

## Build AI Agents and Knowledge Graphs

Welcome to the hands-on workshop. You will build an AI system that answers natural language questions about a commercial aviation fleet, routing each question to whichever backend can answer it best: Neo4j for relationship questions, Databricks for sensor trend questions.

Full lab instructions live on the workshop site:
**https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/index.html**

---

## Lab Progression

| Lab | Topic | Where you work | Instructions |
|-----|-------|----------------|--------------|
| **Lab 1** | Neo4j Aura Setup | Browser (Aura console) | [Lab 1](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab1.html) |
| **Lab 2** | Databricks ETL to Neo4j | Notebook in this workspace | [Lab 2](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab2.html) |
| **Lab 3** | Semantic Search / GraphRAG | Notebooks in this workspace | [Lab 3](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab3.html) |
| **Lab 4** | Compound AI Agents | Databricks UI (Genie + Agent Bricks) | [Lab 4](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab4.html) |

Labs 1 and 4 are browser and UI work, so they have no notebooks. Follow the links above for those.

---

## Architecture

**Dual Database Strategy:**
- **Databricks Lakehouse** — time-series sensor telemetry, roughly 155K readings across 90 days
- **Neo4j Aura** — graph relationships: aircraft topology, components, sensors, maintenance events, flights, delays, airports

**Multi-Agent Supervisor (Lab 4):**
- User question → Agent Bricks Supervisor
  - → **Genie Agent** (sensor analytics via SQL)
  - → **Neo4j MCP Agent** (graph queries via Cypher)

---

## Notebooks in This Workspace

Your Databricks home folder contains:

```
Lab_2_Databricks_ETL_Neo4j/
  01_aircraft_etl_to_neo4j.ipynb     <- start here
Lab_3_Semantic_Search/
  01_data_and_embeddings.ipynb
  02_graphrag_retrievers.ipynb
  03_hybrid_retrievers.ipynb
  data_utils.py
```

Run them in order. Lab 3 depends on the graph that Lab 2 loads.

---

## Getting Started

1. Open the Databricks workspace (left pane)
2. Complete [Lab 1](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab1.html) to create your Neo4j Aura instance and save your credentials
3. Navigate to **Lab_2_Databricks_ETL_Neo4j** → `01_aircraft_etl_to_neo4j`
4. Attach to your assigned cluster
5. Follow the notebook instructions

## Neo4j Credentials

You create your own Neo4j Aura free trial instance in Lab 1 and download the credentials file there. Enter those values in the **Configuration** cell at the top of each notebook:

```python
NEO4J_URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_password_here"
```

Lab 4 does not use your personal Aura instance. It queries a shared reference instance through the Neo4j MCP connection that the instructor has already configured.

## Shared Lakehouse Data

The sensor telemetry and fleet tables are already loaded for you in Unity Catalog:

- Catalog: `databricks-neo4j-workshop`
- Schema: `aircraft`
- Raw files: `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/`

## Need Help?

- Raise your hand for instructor assistance
- Each lab page on the workshop site has a troubleshooting section
