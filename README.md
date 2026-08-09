# Hands-On Workshop: Neo4j and Databricks

**Everything you need to run this workshop is on the site: https://neo4j-partners.github.io/databricks-neo4j-workshop**

Build an AI agent that answers natural language questions about a commercial aviation fleet, over two databases at once. Neo4j Aura holds the fleet's relationships and its maintenance manuals, the Databricks Lakehouse holds the sensor telemetry, and a supervisor you write in LangGraph routes each question to whichever can answer it. Lab 6 then puts the agent's memory in the graph beside the fleet data.

Start at the [Workshop Overview](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/workshop-overview.html), then work through the labs in order.

## The labs

| Lab | Notebooks | Time |
|-----|-----------|------|
| 1. Neo4j Aura Setup | [`Lab_1_Aura_Setup`](./Lab_1_Aura_Setup) | 20 min |
| 2. Databricks ETL to Neo4j | [`Lab_2_Databricks_ETL_Neo4j`](./Lab_2_Databricks_ETL_Neo4j) | 45 min |
| 3. Semantic Search with GraphRAG | [`Lab_3_Semantic_Search`](./Lab_3_Semantic_Search) | 45 min |
| 4 Part A. Genie Space | [`04_genie_agent.ipynb`](./Lab_4_Compound_AI_Agents/04_genie_agent.ipynb) | 30 min |
| 4 Part B. No-code Supervisor | [`PART_B.md`](./Lab_4_Compound_AI_Agents/PART_B.md), an instructor demo you watch | 10 min |
| 5. LangGraph Agent | [`Lab_5_LangGraph_Agent`](./Lab_5_LangGraph_Agent) | 90 min |
| 6. Agent Memory | [`Lab_6_Agent_Memory`](./Lab_6_Agent_Memory) | 75 min |
| Appendix A. GDS Graph Analytics, optional | [`Appendix_A_GDS_Graph_Analytics`](./Appendix_A_GDS_Graph_Analytics) | 45 min |

Each lab's steps live in its notebooks. The site carries the concepts behind them.

## For instructors and administrators

| What | Where |
|---|---|
| Workspace and data provisioning | [`workshop-setup/README.md`](./workshop-setup/README.md) |
| The dataset and its full schema | [`workshop-setup/populate_aircraft_db/DATA_GENERATOR.md`](./workshop-setup/populate_aircraft_db/DATA_GENERATOR.md) |
| Slide decks | [`slides/`](./slides) |
| The site itself | [`site/README.md`](./site/README.md) |

## Feedback

Open an issue on the [GitHub repository](https://github.com/neo4j-partners/databricks-neo4j-workshop/issues).
