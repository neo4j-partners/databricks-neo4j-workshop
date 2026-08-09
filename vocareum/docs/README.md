# Neo4j + Databricks Workshop

## Build AI Agents and Knowledge Graphs

Welcome to the hands-on workshop. You will build an AI system that answers natural language questions about a commercial aviation fleet, routing each question to whichever backend can answer it best: Neo4j for relationship questions, Databricks for sensor trend questions.

Full lab instructions live on the workshop site:
**https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/index.html**

---

## Lab Progression

| Lab | Topic | Where you work | Instructions |
|-----|-------|----------------|--------------|
| **Lab 1** | Neo4j Aura Setup | Aura console, guided by a notebook | [Lab 1](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab1.html) |
| **Lab 2** | Databricks ETL to Neo4j | Notebook in this workspace | [Lab 2](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab2.html) |
| **Lab 3** | Semantic Search / GraphRAG | Notebooks in this workspace | [Lab 3](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab3.html) |
| **Lab 4** | Compound AI Agents | Genie and Agent Bricks, guided by a notebook | [Lab 4](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab4.html) |
| **Lab 5** | LangGraph Agent | Notebooks in this workspace | [Lab 5](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab5.html) |
| **Lab 6** | Agent Memory | Notebook in this workspace | `Lab_6_Agent_Memory/01_agent_memory.ipynb` |

Every lab has a notebook in your workspace, including Labs 1 and 4. Those two are browser work, so their notebooks carry the click-through steps as text beside the few cells you run. Work from the notebooks. The links above are the same instructions on the web. Lab 6 has no web page yet, so its notebook is the instructions.

---

## Architecture

**Dual Database Strategy:**
- **Databricks Lakehouse** — time-series sensor telemetry, hourly-scale readings across 90 days
- **Neo4j Aura** — graph relationships: aircraft topology, components, sensors, maintenance events, flights, delays, airports

**Supervisor Agent (Lab 5), the one you build:**
- User question → LangGraph supervisor
  - → **Genie node**, sensor analytics as SQL over the lakehouse
  - → **Cypher node**, graph queries against your own Aura instance
  - → **GraphRAG node**, retrieval over the maintenance manuals from Lab 3
- Deployed to Model Serving, then given memory in Lab 6

**Supervisor Agent (Lab 4 Part B), an instructor demo you watch:**
- User question → Agent Bricks Supervisor, built with no code
  - → **Genie Agent**, sensor analytics as SQL
  - → **Neo4j MCP Agent**, graph queries as Cypher

---

## Notebooks in This Workspace

Your Databricks home folder contains:

```
Lab_1_Aura_Setup/
  01_create_aura_instance.ipynb      <- start here
  02_credentials_and_cypher.ipynb
Lab_2_Databricks_ETL_Neo4j/
  01_aircraft_etl_to_neo4j.ipynb
Lab_3_Semantic_Search/
  01_data_and_embeddings.ipynb
  02_graphrag_retrievers.ipynb
  03_hybrid_retrievers.ipynb
  data_utils.py
Lab_4_Compound_AI_Agents/
  04_genie_agent.ipynb
Lab_5_LangGraph_Agent/
  01_langgraph_agent.ipynb
  02_deploy_and_evaluate.ipynb
  tools.py
  agent.py
Lab_6_Agent_Memory/
  01_agent_memory.ipynb
  02_instructor_demos.ipynb           <- the instructor drives this one
  memory.py
```

Run them in order. Lab 2 needs the Aura instance you create in Lab 1, Lab 3 needs the graph Lab 2 loads, Lab 5 needs the Genie space you create in Lab 4, and Lab 6 needs the agent and the Model Serving endpoint from Lab 5. Keep the lab folders as siblings. `memory.py` imports from `Lab_3_Semantic_Search/data_utils.py` and `Lab_5_LangGraph_Agent/tools.py`, so moving a folder breaks Lab 6.

---

## Getting Started

1. Open the Databricks workspace (left pane)
2. Open **Lab_1_Aura_Setup** → `01_create_aura_instance` and work through it in a browser tab to create your Neo4j Aura instance and download its credentials
3. Open `02_credentials_and_cypher` and attach it to your assigned cluster. It is the only notebook where you type your Neo4j password. Its connection test confirms the credentials reach Aura, and it stores them for every later lab
4. Continue lab by lab, attaching each notebook to the same cluster

## Neo4j Credentials

You create your own AuraDB Free instance in Lab 1 and download the credentials file there. AuraDB Free, not the 14-day trial the console offers first: the trial provisions AuraDB Professional and expires partway through this course.

You type those values once, in `Lab_1_Aura_Setup/02_credentials_and_cypher.ipynb`:

```python
NEO4J_URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_password_here"
```

That notebook writes them into a Databricks secret scope named `fleet-ops-<your user>`, and every notebook from Lab 2 on opens with a cell that reads the scope. There is nothing to paste again. If a later notebook stops with an error about a missing scope, go back and run Lab 1 notebook 02.

You never type a database name. Aura picks it, and on a Free instance it is often the instance ID rather than `neo4j`, so notebook 02 detects the real name off the connection and stores that too.

Lab 4 Part A does not use Neo4j at all. You build a Genie space over the lakehouse sensor tables. Part B is an instructor demo you watch rather than run, against the instructor's own workspace and Neo4j MCP connection, so there is nothing for you to configure there. Lab 5 goes back to your own Aura instance, the one you loaded in Lab 2. Lab 6 uses that same instance and is the first lab that writes to it, storing the agent's memory beside the fleet graph.

## Shared Lakehouse Data

The sensor telemetry and fleet tables are already loaded for you in Unity Catalog:

- Catalog: `databricks-neo4j-workshop`
- Schema: `aircraft`
- Raw files: `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/`

## Need Help?

- Raise your hand for instructor assistance
- Each lab page on the workshop site has a troubleshooting section
