# Overview Section: Narrative Arc

Sets up the rest of the slide deck by motivating graph feature engineering.

1. **The Dual Architecture for This Use Case** — Databricks holds analytics + documents, Neo4j holds the relationship graph. A graph data pipeline links customers to profiles, enabling GraphRAG search.

2. **Graph-Enriched Retrieval** — How the pipeline works: Spark Connector builds the graph, KG construction adds documents, GraphRAG traverses from text into operational data. Includes graphrag-retrieval-flow.png.

3. **The GraphRAG Gap** — Semantic search finds customers by risk profile, but only 3 of 103 have documents. The other 100 are invisible to retrieval even though the graph holds their structural data.

4. **What's Missing: Structural Similarity** — The 100 unlabeled customers have the same topology (accounts, positions, stocks) as the labeled 3. Similar portfolios likely mean similar risk profiles. We need a way to measure that.

5. **The Solution: Graph Feature Engineering** — Group customers by the structure of their connections. GDS turns topology into numbers (community IDs, centrality, embeddings). A classifier trained on the 3 labeled customers predicts labels for the remaining 100.

Then into Foundations (Features/Classifiers vocabulary, Example table) → GDS algorithms → Bi-directional loop → Scaling.
