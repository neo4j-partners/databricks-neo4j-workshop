# Community Detection

Community detection algorithms find natural clusters in a graph by maximizing connections within groups and minimizing connections between them. In the aircraft use case, communities reveal which aircraft share failure patterns, enabling coordinated maintenance decisions across a fleet segment rather than treating each aircraft in isolation.

## Notebook

| Notebook | Algorithm | What It Does |
|----------|-----------|--------------|
| [`02_gds_louvain_maintenance.ipynb`](02_gds_louvain_maintenance.ipynb) | Louvain | Builds a co-occurrence graph where Aircraft nodes are connected by shared fault types, runs Louvain to detect risk communities, and writes a `fault_community` integer property back to each Aircraft node |

## When to Use This

Louvain is a good starting point for community detection: it scales well, requires no predefined number of clusters, and produces hierarchical results you can inspect at multiple resolutions. Use it when you want to segment a population by shared behavior rather than by attributes stored in the nodes themselves.

## Prerequisites

- Lab 2 notebook 01 completed
- Neo4j GDS plugin available on your Aura instance (verify with `CALL gds.version()`)
