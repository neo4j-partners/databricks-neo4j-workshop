# Similarity

Similarity algorithms compare nodes by the neighborhoods or features they share and write relationships encoding that similarity back to the graph. Node Similarity uses Jaccard overlap on shared neighbors; kNN uses numerical feature vectors. In the aircraft use case, similarity surfaces aircraft that fail in the same ways, enabling maintenance knowledge to transfer across fleet segments or aircraft models.

## Notebook

| Notebook | Algorithm | What It Does |
|----------|-----------|--------------|
| [`05_gds_node_similarity_aircraft.ipynb`](05_gds_node_similarity_aircraft.ipynb) | Node Similarity (Jaccard) | Builds a bipartite Aircraft-FaultType graph, computes Jaccard overlap between aircraft fault portfolios, and writes `SIMILAR_FAULT_PROFILE` relationships between aircraft that share fault types |

## Relationship to Lab 2

The kNN similarity notebook (`02_gds_knn_aircraft.ipynb` in Lab 2) uses numerical feature vectors derived from both Databricks sensor telemetry and Neo4j maintenance data. This appendix notebook uses structural overlap on fault types instead, producing a complementary view. The comparison queries at the end of notebook 05 assume the Lab 2 kNN notebook has already run and the `SIMILAR_PROFILE` relationships exist.

## When to Use This

Node Similarity is the right choice when similarity should be defined by shared connections rather than numerical closeness. It requires no feature engineering, making it fast to set up and easy to explain to a business audience.

## Prerequisites

- Lab 2 notebook 01 completed
- Lab 2 notebook 02 (`02_gds_knn_aircraft.ipynb`) completed, for the comparison queries
- Neo4j GDS plugin available on your Aura instance (verify with `CALL gds.version()`)
