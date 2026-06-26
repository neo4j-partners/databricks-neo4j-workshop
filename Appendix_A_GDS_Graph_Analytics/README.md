# Appendix A: Graph Data Science Algorithms

Extended GDS notebooks for the Aircraft Digital Twin workshop. These go deeper on graph analytics than the main lab sequence requires, organized by algorithm family so you can pick what fits your audience or time budget.

All notebooks require Lab 2, notebook 01 (`01_aircraft_etl_to_neo4j.ipynb`), to have been run first. They also require the Neo4j Graph Data Science plugin on your Aura instance.

---

## Algorithm Families

| Folder | Family | Notebook | What It Does |
|--------|--------|----------|--------------|
| [`community_detection/`](community_detection/) | Community Detection | Louvain | Groups aircraft into risk communities based on shared fault patterns |
| [`centrality/`](centrality/) | Centrality | PageRank + Betweenness | Scores airports by network influence and identifies critical route connectors |
| [`similarity/`](similarity/) | Similarity | Node Similarity (Jaccard) | Finds aircraft that share overlapping fault portfolios across models |

The kNN similarity notebook lives in Lab 2 (`02_gds_knn_aircraft.ipynb`) rather than here because it bridges both Databricks sensor data and Neo4j maintenance data, making it central to the workshop's dual-database narrative. The Node Similarity notebook in this appendix extends that analysis; its comparison queries assume the Lab 2 kNN notebook has already run.

---

## Companion Reference

[`gds-exploring.md`](gds-exploring.md) contains Cypher queries for inspecting GDS projections, re-running individual algorithm steps, and exploring the properties and relationships written back to the graph by each notebook.

---

## Adding More Content

Drop new notebooks into the appropriate algorithm family subfolder. If a notebook spans more than one family, create a new subfolder rather than splitting it. Future appendix sections (Appendix B, C, etc.) follow the same top-level naming pattern.
