---
marp: true
theme: default
paginate: true
---

<style>
section {
  --marp-auto-scaling-code: false;
}

li {
  opacity: 1 !important;
  animation: none !important;
  visibility: visible !important;
}

/* Disable all fragment animations */
.marp-fragment {
  opacity: 1 !important;
  visibility: visible !important;
}

ul > li,
ol > li {
  opacity: 1 !important;
}
</style>

# Neo4j + Databricks

The dual-database architecture behind the aircraft digital twin

---

## Dual Database Architecture

The data splits across two platforms, each chosen for the workload it handles best.

**Databricks Lakehouse:** time-series sensor telemetry
- Readings every 4 hours across 90 days
- Columnar storage and SQL for aggregation, trend analysis, statistical comparison

**Neo4j Aura:** richly connected relational data
- Aircraft topology, component hierarchies, maintenance events, flights, delays, airport routes
- Native multi-hop traversal, no expensive joins

A multi-agent supervisor routes questions to the right database automatically.

<!--
Databricks owns the high-volume time series, a columnar workload.
Neo4j owns the connected data, a traversal workload. Lab 5's
supervisor decides, per question, which side to ask.
-->

---

![bg contain](../../site/modules/ROOT/images/dual-database-architecture.svg)

<!--
Databricks tables on one side, the Neo4j graph on the other, join
points where the same entity, aircraft, systems, sensors, exists in
both. The Spark Connector is the bridge between them.
-->

---

## What Each Platform Brings

Databricks scales tables. Neo4j scales connections. Most problems need both.

| | Databricks | Neo4j |
|---|-----------|-------|
| **Stores** | Tables and files | Nodes and relationships |
| **Answers** | How much, how often | How is this connected, what is affected |
| **AI capability** | Foundation Models, Genie | Vector indexes, GraphRAG, MCP |
| **Strength** | Scale, aggregation, ML | Relationships, traversal, pattern matching |

**The Spark Connector** moves data. **The Neo4j Custom JDBC Unity Catalog Connector** reads the graph as SQL without moving it. **MCP** lets agents query the graph directly. Together, the platforms stay connected at every layer.

<!--
Databricks excels at large volumes of data, aggregations, and machine
learning over tables. Neo4j excels at understanding how things
connect. Most real-world problems need both, which is the whole
premise of this workshop.

The same division of labor as a lookup table: scale on one side,
connections on the other, and three connectors keeping them in sync.
One copies, one reads in place, one hands the graph to an agent as a
tool.

Genie appears once, in the AI capability row. Do not explain it here.
Lab 4 Part A is where participants build one.
-->

---

## Neo4j Knowledge Layer

The graph is not just another store. It is the layer that makes enterprise data legible to an agent.

- **Ontologies:** the schema that tells an agent what an Aircraft is, what a Component is, and how they relate
- **Data:** entities and relationships, loaded from the governed tables in the lakehouse
- **Memory:** what the agent learned last time, written back as nodes and relationships, which is Lab 6

Embeddings come from a Databricks Foundation Model endpoint, `databricks-bge-large-en`, so the semantic layer is built on the same platform that holds the tables.

View on GitHub: https://github.com/neo4j/neo4j-graphrag-python

<!--
Three things live in one graph, and that is the point: the ontology,
the operational data, and the agent's own memory. Lab 2 loads the
data, Lab 3 adds the semantic layer over the manuals, Lab 6 adds
memory. Same database each time.

The embeddings line matters for the platform argument: nothing here
requires a third vendor. The model endpoint is Databricks.

Deck 5 owns what GraphRAG is. Do not explain retrieval here.
-->

---

## Data Intelligence, Graph Intelligence, or Both?

- **SQL:** total sensor readings per aircraft, a single GROUP BY aggregation
- **Cypher:** components within three hops of a flagged sensor, a single traversal query

Most questions need **both**.

| Question | Platform |
|---|---|
| Total sensor readings per aircraft | Databricks, SQL aggregation |
| Components within three hops of a flagged sensor | Neo4j, graph traversal |
| Find the affected aircraft, then total their flight hours | Both |

<!--
SQL is built for aggregation, Cypher for traversal. The third row is
why you need both: Neo4j finds the affected aircraft, Databricks
totals their flight hours. This is the same choice Lab 5's supervisor
makes automatically at runtime.

The heuristic, if anyone asks where the line falls:

  Number of hops        1-2 fixed joins stay in SQL; 3+ or variable
                        depth moves to Cypher
  Query shape           Known at design time stays in SQL; depends on
                        the data encountered moves to Cypher
  Result type           Aggregated numbers stay in SQL; paths,
                        subgraphs and connected components move to
                        Cypher
  Latency requirement   Batch is fine in SQL; sub-second interactive
                        investigation moves to Cypher
  Data volume per query Millions of rows scanned stays in SQL;
                        thousands of entities traversed moves to
                        Cypher
-->

---

## Three Tools, One Agent

The hero question from the opener needs three different kinds of retrieval.

- **Genie over Delta:** what did the sensors read. Columnar, high volume, aggregate. Lab 4 Part A
- **Cypher over Neo4j:** what is this part connected to, and what else does it touch. Connected, variable depth. Labs 1 and 2
- **GraphRAG over the manuals:** what does the procedure say. Text, retrieved by meaning. Lab 3

One supervisor routes the question to the right tool and combines what comes back. **Lab 5.**

<!--
A forward reference, not a spoiler. Do not explain the supervisor
here, deck 7 owns that. Do not re-ask the hero question either; the
room heard it in the opener and watched the demo answer it.

The point to land: the three-tool split is forced by the shape of the
data, not chosen for variety. Telemetry is columnar and huge.
Topology is connected. Procedure is text. No single store is good at
all three, which is why the architecture looks the way it does.

Everything before this slide is why the two platforms belong
together. This is what the combination buys.
-->

---

## The Medallion Architecture

- **Bronze:** raw data lands from cloud storage, no transformation
- **Silver:** cleaned, typed, governed tables; the Spark Connector reads from here
- **Gold:** business-ready outputs enriched by graph insights, for example maintenance alerts, component health scores, ML features
- **Bidirectional flow:** data flows forward through the layers, graph insights flow back

<!--
Bronze is the raw landing zone. Silver is schema enforcement and
column renaming, tail_number becomes aircraft_id, and it feeds the
Spark Connector. Gold is where graph algorithm results, component
criticality scores, community groupings, write back as columns
alongside operational data that never left the lakehouse. Silver
feeds the graph, Gold captures what the graph discovers.
-->

---

## Neo4j Spark Connector

The bi-directional bridge between the Databricks Lakehouse and a Neo4j knowledge graph.

- **Write** Lakehouse rows to Neo4j as nodes and relationships
- **Read** graph data back into Databricks as Spark DataFrames
- **Runs natively** inside Spark notebooks and workflows, no external service to stand up
- Batch-oriented, which is what bulk loading a graph wants

This is the connector Lab 2 runs on.

<!--
The one connector detail slide in the main line, because Lab 2 uses
it and nothing else here does. Keep it short: participants will see
the actual configuration in the Lab 2 notebooks.

The bi-directional point is the one worth landing. Most people
assume a one-way load. Reading back is what makes the GDS
write-back to Gold possible, which is the Data Analytics stage on the
next slide.
-->

---

<style scoped>
section { font-size: 25px; }
</style>

## Neo4j Connection Patterns by Platform Stage

- **Data Pipeline:** Neo4j Spark Connector, batch writes
- **Knowledge Graph Construction:** neo4j-graphrag-python, uses the Neo4j Python driver
- **Data Analytics:** Spark Connector for Graph Data Science reads and write-back to Gold
- **SQL Federation:** Neo4j Custom JDBC Unity Catalog Connector, SQL over the graph, joined with Delta in one query
  - Covered in full in the *Neo4j Connectors in Depth* background deck
- **GraphRAG Retrieval/Agent:** Neo4j MCP Server, Python driver, Aura Agent
  - Covered in the *Neo4j MCP and Agent Bricks* deck

Sample Projects: https://github.com/neo4j-partners/graph-on-databricks
NeoCarta, semantic layer for Databricks and more: https://github.com/neo4j-labs/neocarta

<!--
Each platform stage uses a different connector optimized for its
workload. The Data Pipeline uses the Spark Connector for batch
DataFrame writes into Neo4j. This is the primary path for bulk
loading structured data, and it is what Lab 2 does.

Knowledge Graph Construction uses the Neo4j Python driver directly,
not the Spark Connector. The SimpleKGPipeline from
neo4j-graphrag-python handles chunking, LLM-based entity extraction,
and embedding generation, none of which are Spark operations. This is
Lab 3.

Data Analytics uses the Spark Connector for its first-class GDS
integration: invoke PageRank, community detection, and other graph
algorithms directly, get results as DataFrames for ML features and
Gold Delta tables. Neo4j's docs position this as a "graph
co-processor" in existing Spark ML workflows.

SQL Federation moves nothing, and it is for the analyst who knows SQL
and has never written Cypher. The Neo4j Connectors in Depth
background deck covers it in full: no lab builds it.

GraphRAG Retrieval uses the Neo4j MCP Server to expose schema
inspection and read-only Cypher as agent tools. The Python driver
powers the retrievers underneath, combining vector search with graph
traversal in a single query. This is Lab 4 Part B and Lab 5.

This slide closes the deck as a map. Five stages, and the room now
knows which deck or lab covers each one.
-->
