# Graph on Databricks: Field Enablement Agenda

* **Intro to Graph: Finding Patterns in Connected Data**: How relationships and network structure surface unique insights about connected data.

* **Graph Algorithms: From Connected Data to Analytical Features**: How algorithms for centrality, community detection, and similarity turn connected data into measurable, reusable features.

* **Graph-Enriched Lakehouse Architecture**: A dual-engine strategy using Neo4j for network traversal and the Lakehouse for scale. Graph-derived features are written back to Delta tables to augment existing records with graph context for analytics and AI.

* **Neo4j and Databricks Integration Patterns**: Spark Connector and MCP-based integration patterns for moving graph results into the Lakehouse and exposing them to agents.

* **GraphRAG and Graph-Enriched Search**: Integration of vector embeddings with graph traversal enables multi-hop queries by combining semantic similarity with graph structure.

* **Agentic GraphRAG: Combining Genie and Neo4j**: A supervisor that routes across Genie for SQL analytics, Cypher for graph traversal, and GraphRAG for documentation, unifying Lakehouse and graph data in one agent. Built in LangGraph against the participant's own graph, and with no code using Agent Bricks and a governed MCP connection.

* **Deploying the Agent**: Logging the agent to Unity Catalog and serving it as an endpoint that authenticates as a service principal rather than as the notebook user. The step that separates a notebook demo from a product.

* **Agent Memory as a Graph**: Storing what the agent learns in the same database as the domain data, so a single traversal can cross from conversation history into fleet maintenance history and answer questions neither graph could answer alone.
