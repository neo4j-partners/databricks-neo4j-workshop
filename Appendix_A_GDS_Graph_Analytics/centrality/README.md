# Centrality

Centrality algorithms score nodes by their structural importance in a network. PageRank measures influence through incoming connections; Betweenness Centrality identifies nodes that act as bridges between parts of the graph. In the aircraft use case, these scores reveal which airports anchor the route network and which connectors, if disrupted by maintenance delays, would fragment the most routes.

## Notebook

| Notebook | Algorithms | What It Does |
|----------|------------|--------------|
| [`04_gds_pagerank_airports.ipynb`](04_gds_pagerank_airports.ipynb) | PageRank, Betweenness Centrality | Projects the weighted airport route network, runs both algorithms, writes `pagerank_score` and `betweenness_score` back to Airport nodes, and joins with Databricks to correlate centrality with maintenance-caused delays |

## When to Use This

Use centrality when you need to rank nodes by network position rather than by a property they already carry. The cross-database join in this notebook (Neo4j centrality scores + Databricks delay data) also demonstrates a practical pattern for combining graph-derived features with tabular analytics.

## Prerequisites

- Lab 2 notebook 01 completed
- Neo4j GDS plugin available on your Aura instance (verify with `CALL gds.version()`)
