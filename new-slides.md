## What Each Platform Brings

## Data Intelligence, Graph Intelligence, or Both?

## Neo4j Connection Patterns by Platform Stage  (rename Neo4j +Databricks Integration Patterns)

## Neo4j Spark Connector

## The Medallion Architecture

## Image - copy this image to this repo

/Users/ryanknight/projects/cloud-integration/databricks/new-slides/better-together/images/spark-connector-virtual-graph.png

## From the Lakehouse to the Graph

- **Rows become nodes**: aircraft columns become node properties
- **Foreign keys become relationships**: `system.aircraft_id` → `(:Aircraft)-[:HAS_SYSTEM]->(:System)`
- **Mapping tables become relationships**: `component_removals` rows become `[:REMOVED_FROM]` edges with properties
- **Shared attributes become shared nodes**: two aircraft at the same airport connect through one `(:Airport)` node
- **Self-referential columns become chains**: `origin_airport` → `destination_airport` becomes `(:Airport)<-[:DEPARTED_FROM]-(:Flight)-[:ARRIVED_AT]->(:Airport)`

## From Raw Data to Governed Delta Tables

- Cloud storage lands raw files (S3, ADLS Gen2, GCS)
- Databricks processes data into Delta tables via Jobs, Notebooks, or Spark Declarative Pipelines
- Delta Lake enforces schema and rejects bad data at ingestion
- Delta tables become the interchange format for the Spark Connector

##  Loading the Graph

- **Node properties from columns**: `aircraft_id`, `model`, `status` become properties on each `Aircraft` node
- **Nodes first**: Aircraft rows become `Aircraft` nodes via batched upserts
- **Relationships second**: the connector matches nodes by property values, creates `HAS_SYSTEM` edges
- **Properties on the relationship**: `removal_date`, `reason`, `shop` stored directly on the edge

##  Graph Insights Flow Back to the Lakehouse

- **Cycle Detection**: fraud ring flags in the alerts table
- **PageRank**: risk scores for investigation prioritization
- **Community Detection**: fraud ring groupings via Louvain
- **Degree Centrality**: counterparty counts as ML features

##Foundation for Data Intelligence Meets Graph Intelligence

- The Medallion Architecture is built. Data intelligence and graph intelligence are connected
- **Bronze**: raw data landed from cloud storage
- **Silver**: cleaned, governed tables fed the Spark Connector
- **Gold**: graph insights flowing back as fraud alerts, risk scores, ML features

## Neo4j Knowledge Layer

## Three Tools, One Agent
