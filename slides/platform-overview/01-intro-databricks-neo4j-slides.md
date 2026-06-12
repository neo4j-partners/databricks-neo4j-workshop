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

# Building the Intelligence Platform

Data Intelligence Meets Graph Intelligence

---

## Databricks & Neo4j: Better Together

- Databricks-Certified Neo4j Spark Connector
- Bi-directional, scalable data pipelines
- Effortless Databricks + Neo4j Agent integration
- Accelerate Innovation with GraphRAG
- Graph Analytics Unlock Hidden Patterns at Scale

<!--
Databricks and Neo4j have an official technology partnership. The
Spark Connector is Databricks-certified and provides the primary
bridge for moving data between the lakehouse and the graph in both
directions.

This slide previews the four value pillars the rest of the deck
walks through: data pipelines, graph analytics, GraphRAG retrieval,
and agent integration.
-->

---

## Data Intelligence Meets Graph Intelligence

- **Databricks (Data Intelligence Platform):** structured, semi-structured, unstructured data at scale
- **Neo4j (Graph Intelligence Platform):** connections between entities, explicit and traversable

<!--
Databricks is the Data Intelligence Platform. It governs and analyzes
structured, semi-structured, and unstructured data at scale.

Neo4j is the Graph Intelligence Platform. It makes connections between
entities explicit and traversable.

This slide sets up the framing for the rest of the deck. The next two
slides break down what each platform actually does.
-->

---

## Databricks: The Data Intelligence Platform

- **Aggregates** transactions, sensor streams, clickstreams
- **Governs** documents, images, unstructured files
- **Databricks SQL** at petabyte scale, real-time streaming, data science
- **Unity Catalog** (unified governance across data and AI), **Delta Lake** (open lakehouse storage), **Lakebase** (integrated OLTP)
- **Mosaic AI** (agent systems), **AI/BI Genie** (conversational analytics), **Agent Bricks** (agent control plane)

<!--
Databricks handles structured, semi-structured, and unstructured data.
It aggregates transactions and sensor streams, governs documents and
images through Unity Catalog, runs SQL against Delta Lake at petabyte
scale, and supports ML pipelines from feature engineering through
model serving. Schema enforcement, ACID transactions, and time travel
provide the foundation.
-->

---

## Neo4j: The Graph Intelligence Platform

- **Traverses** supply chains, fraud networks, knowledge graphs
- **Cypher** pattern matching on nodes and relationships
- **Multi-hop traversal** and path finding in milliseconds
- **Graph Data Science** (graph algorithms), **AuraDB** (managed database), **GraphRAG** (graph-enhanced retrieval), **Aura Agent** (agent creation from knowledge graphs)

<!--
Neo4j makes connections between entities explicit and traversable.
Cypher is the query language for graph databases, operating over nodes
and relationships. Multi-hop traversals that would require complex
recursive SQL run in milliseconds. Pattern matching across connection
topologies reveals structures invisible in flat tables.
-->

---

## The Medallion Architecture

- **Bronze:** raw data lands from cloud storage; no transformation
- **Silver:** cleaned, typed, governed tables; the Spark Connector reads from here
- **Gold:** business-ready outputs enriched by graph insights (fraud alerts, risk scores, ML features)
- **Bidirectional flow:** data flows forward through the layers, graph insights flow back

<!--
The Medallion Architecture is how Databricks organizes data
through progressive refinement. Bronze is the raw landing zone:
files arrive from cloud storage with no transformation. Silver
is the general curation layer: schema enforcement, type casting,
column renaming. Customer_ID becomes account_id, Txn_Amount
becomes amount. Silver tables are governed and ready for
downstream consumers, including the Spark Connector writing to
Neo4j.

Gold is where all intelligence converges. Graph algorithm results
(cycle detection, PageRank, community scores) write back to Delta
as columns in Gold tables. These join with operational data that
never left the lakehouse to produce fraud alerts, risk scores,
and ML feature tables for case management.

Data flows forward through the layers, graph insights flow back.
Silver feeds the graph, Gold captures what the graph discovers.
This bidirectional flow is where data intelligence and graph
intelligence compound each other's value.
-->

---

## Building the Intelligence Platform

- **ELT Data Pipeline:** Governed Delta tables projected into graph nodes and relationships
- **Knowledge Graph Construction:** Unstructured docs enriched into embeddings and extracted entities
- **Data Analytics:** Graph insights written back to Gold tables for dashboards and ML
- **GraphRAG Retrieval/Agent:** Agents query both platforms through vector search, Cypher, and SQL

<!--
Four stages connect Databricks to Neo4j, each building on the
Medallion Architecture. The Data Pipeline takes curated Silver
tables and batch-loads them as graph nodes and relationships via
the Spark Connector. Knowledge Graph Construction uses the
neo4j-graphrag-python Knowledge Graph Builder (SimpleKGPipeline)
to chunk regulatory and AML policy documents, generate embeddings,
extract entities, and write them back into Neo4j. Data Analytics
combines graph insights written back to Gold Delta tables with
lakehouse data for dashboards, reports, and ML features, queried
through Unity Catalog JDBC for governed cross-system joins.
GraphRAG Retrieval combines vector search with graph traversal
via the VectorCypherRetriever, exposed as MCP tools so
investigation agents can query the graph and the lakehouse
together.
-->

---

## The Intelligence Platform — Data Flow

![Intelligence Platform Data Flow](../databricks-in-depth/intelligence-platform-flow.png)

<!--
The same four stages visualized as a data flow. Stages 1-2 flow
left to right (Databricks to Neo4j): Silver tables through the
Spark Connector become graph nodes; unstructured docs through the
KG Builder become embeddings and entities. Stage 3 reverses: graph
insights flow back to Gold tables. Stage 4 spans both: the
multi-agent supervisor routes to Genie (SQL) and the Neo4j MCP
agent (Cypher).
-->

---

## Neo4j Connection Patterns by Platform Stage

- **Data Pipeline:** Neo4j Spark Connector (batch writes)
- **Knowledge Graph Construction:** neo4j-graphrag-python (uses Neo4j Python driver)
- **Data Analytics:** Spark Connector (Graph Data Science reads) + Unity Catalog JDBC (governed SQL, BI tools)
- **GraphRAG Retrieval/Agent:** Neo4j MCP Server + Python driver + Aura Agent

<!--
Each platform stage uses a different connector optimized for its
workload. The Data Pipeline uses the Spark Connector for batch
DataFrame writes into Neo4j. This is the primary path for bulk
loading structured data.

Knowledge Graph Construction uses the Neo4j Python driver directly,
not the Spark Connector. The SimpleKGPipeline from
neo4j-graphrag-python handles chunking, LLM-based entity
extraction, and embedding generation, none of which are Spark
operations.

Data Analytics uses both connectors. The Spark Connector provides
first-class GDS integration: invoke PageRank, community detection,
and other graph algorithms directly, get results as DataFrames for
ML features and Gold Delta tables. Neo4j's docs position this as
a "graph co-processor" in existing Spark ML workflows. Unity
Catalog JDBC adds the governed SQL layer: register Neo4j as a
JDBC connection, query graph data via SQL translated to Cypher,
join graph results with Delta tables, and connect BI tools like
Power BI and Tableau through standard JDBC.

GraphRAG Retrieval uses the Neo4j MCP Server to expose schema
inspection and read-only Cypher as agent tools. The Python driver
powers the VectorCypherRetriever underneath, combining vector
search with graph traversal in a single query.
-->

---

# Two Data Models, Two Query Languages

How rows and columns work together with nodes and relationships

---

## Financial Fraud as a Working Example

- **The use case:** money laundering through circular transfers across account chains
- **Each transfer looks legitimate.** The cycle reveals the fraud
- **Why graph:** `(ACC-1001)-[:REGISTERED_AT]->(742 Evergreen)-[:REGISTERED_AT]-(ACC-2047)` is one traversal, not a self-join
- **The question:** "which accounts share an address with a flagged account?" is a single hop in the graph

<!--
We'll use financial fraud to walk through each pipeline stage.
Money laundering moves funds through chains of accounts and back
to the origin. Each individual transfer looks legitimate in
isolation. The circular pattern is only visible when you follow
the connections.

This is where graph structure pays off. Detecting A transferred
to B transferred to C transferred back to A is a single Cypher
pattern match. In SQL, the same detection requires complex nested joins
that self-join the transactions table at each hop, with explicit
visited-node tracking to prevent infinite loops. The graph
represents the cycle directly; the table has to reconstruct it.
-->

---

## Fraud Ring — Dual Database Architecture

![Fraud Ring Dual Database Architecture](../databricks-in-depth/fraud-ring-dual-architecture.png)

---

## Neo4j Graph Components

- Graphs model the real world as **nodes** (entities) and **relationships** (connections)
- `(parentheses)` are nodes, `[:brackets]` are relationships

```
(:Account)-[:TRANSFERRED_TO {amount, timestamp, channel}]->(:Account)
```

Each Account node carries properties (account_id, customer_name, status). Each TRANSFERRED_TO relationship carries transaction details (amount, timestamp, channel).

---

## Data Intelligence, Graph Intelligence, or Both?

- **SQL:** total transfer volume by account — a single GROUP BY aggregation
- **Cypher:** accounts within three hops of a flagged account — a single traversal query

Most investigations need **both**

| Question | Platform |
|---|---|
| Total transfer volume by account | Databricks (SQL aggregation) |
| Accounts within three hops of a flagged account | Neo4j (graph traversal) |
| Find the fraud ring, compute its total volume | Both |

<!--
Each question maps to the platform built to answer it. SQL is
built for aggregation: totals, averages, counts. Cypher is built
for traversal: following connections across multiple hops.

The third row shows why you need both: Neo4j detects the fraud
ring through cycle traversal, Databricks computes transfer totals
for the identified accounts. Neither platform can answer that
question alone.
-->

---

## From the Lakehouse to the Graph

- **Most data stays in Delta:** aggregates, metrics, logs, documents
- **Rows become nodes:** account columns become node properties
- **Foreign keys become relationships:** `account.address_id` → `(:Account)-[:REGISTERED_AT]->(:Address)`
- **Mapping tables become relationships:** `account_devices` rows become `[:USED_DEVICE]` edges with properties
- **Shared attributes become shared nodes:** two accounts with the same SSN connect through one `(:SSN)` node
- **Self-referential columns become chains:** `from_account` → `to_account` becomes `(:Account)-[:TRANSFERRED_TO]->(:Account)`

<!--
Not everything moves to the graph. Aggregates, metrics, logs, and
documents stay in Delta where they belong. Only the subset with
connection patterns worth traversing projects into Neo4j. The
lakehouse remains the system of record; the graph is a projection
of the connections that matter.

Rows become nodes: a row in the accounts table becomes an Account
node, with columns like account_id, customer_name, and status as
node properties.

Foreign keys become relationships. A column like
account.address_id pointing to addresses.id becomes a
REGISTERED_AT relationship. This is the most straightforward
mapping: one-hop lookups that SQL also handles well.

Mapping tables dissolve into relationships. A junction table like
account_devices doesn't become nodes. Each row becomes a
USED_DEVICE relationship with first_seen and last_seen as
relationship properties. The mapping table disappears entirely.

Shared attribute values surface implicit connections. Two accounts
sharing the same SSN have no foreign key between them. Discovering
that link in the lakehouse requires a self-join. In the graph, SSN
becomes a shared node and both accounts connect to it, making the
hidden connection explicit and traversable.

Self-referential columns become relationship chains. from_account
and to_account in the transactions table point to two entities in
the same table. In the graph this becomes a TRANSFERRED_TO
relationship. Chains of these are natural traversals in the graph
but require complex nested joins in SQL.

The value compounds as you move down the list. Foreign keys are
simple one-hop lookups. Mapping tables eliminate multi-table joins.
Shared attributes reveal hidden networks. Self-referential chains
replace complex nested joins. The further down you go, the more the
graph pays off relative to SQL.
-->

---

# ELT: Lakehouse to Graph

---

## From Raw Data to Governed Delta Tables

- **Cloud storage** lands raw files (S3, ADLS Gen2, GCS)
- **Databricks** processes data into Delta tables via Jobs, Notebooks, or Spark Declarative Pipelines
- **Delta Lake** enforces schema and rejects bad data at ingestion
- **Delta tables** become the interchange format for the Spark Connector

<!--
Raw data lands in cloud storage: S3, Azure Data Lake Storage Gen2, or
GCS. This is the unprocessed landing zone, not a governed catalog yet.

Databricks processes that raw data into Delta tables. The processing
layer is Jobs, Notebooks, or Spark Declarative Pipelines (formerly
Delta Live Tables). Auto Loader can incrementally detect and process
new files as they arrive.

Delta Lake provides the governance layer: schema enforcement catches
malformed account IDs and invalid amounts here, not during the graph
load. Column renaming happens at this stage too. Customer_ID becomes
account_id, Txn_Amount becomes amount, so graph properties are clean
without extra transformation downstream.

Time travel enables recovery from bad loads. If a pipeline run
corrupts data, you roll back to the previous version rather than
re-ingesting from scratch.

The key point: Delta tables are the interchange format. The Neo4j
Spark Connector reads from these governed tables. Everything upstream
of this slide is Databricks territory. Everything downstream is the
Spark Connector projecting connections into the graph.
-->

---

## The Neo4j Spark Connector

- **Officially supported bridge** between Databricks and Neo4j
- **Databricks → Neo4j:** Turn Lakehouse rows into graph nodes and relationships
- **Neo4j → Databricks:** Pull graph data back into DataFrames for analytics or ML
- **Supports batch and incremental** loading patterns

---

## Loading the Graph

- **Node properties from columns:** account_id, customer_name, status become properties on each Account node
- **Nodes first:** Account rows become Account nodes via batched upserts
- **Relationships second:** the connector matches nodes by property values, creates `TRANSFERRED_TO` edges
- **Properties on the relationship:** amount, timestamp, channel stored directly on the edge

<!--
Each row in the accounts Delta table becomes an Account node.
Batched upserts create if new or update if existing, so the load
is idempotent. Relationships come second because both endpoints
must exist before the connector can match them.

The connector matches existing Account nodes by property values
and creates TRANSFERRED_TO connections between them. Transaction
details ride on the relationship itself: amount, timestamp, and
channel are stored directly on the edge. No separate edge table,
no foreign key resolution at query time.
-->

---

## Design Decision: Relationship Types vs. Properties

- **Type per connection:** `:TRANSFERRED_TO`, `:SHARED_DEVICE`, indexed lookups, faster traversal
- **Generic with property:** `:CONNECTED {type: "transfer"}`, simpler schema, slower property filters
- **Choose type per connection** when traversals follow specific connection types
- **Directional relationships:** bidirectional flows require writing in both directions

<!--
The fraud example uses a single relationship type (TRANSFERRED_TO)
with transaction details as properties. In other domains you may
face the choice between multiple relationship types or a generic
type with a property.

Type per connection means each kind of link gets its own
relationship type. Neo4j indexes relationship types, so type-based
lookups are fast. The tradeoff is a larger type vocabulary to
manage.

Generic with property uses a single relationship type and
distinguishes via a property value. Simpler schema, but property
filters are slower than type lookups at query time.

Default to type per connection when your traversals need to follow
specific connection types. Neo4j relationships are directional, so
bidirectional flows like transfers require writing in both
directions.
-->

---

## Validation Through Spark Reads

- **Node counts** match source row counts
- **Relationship counts** fall within expected ranges for transaction volume
- **High-connectivity nodes** reflect known patterns from source data

<!--
The connector reads from Neo4j just as easily as it writes. Cypher
results come back as standard DataFrames, so validation runs in
the same Spark environment that built the graph.

Three checks cover the common failure modes. Node counts should
match source row counts exactly. Relationship counts should fall
within expected ranges for the transaction volume. High-connectivity
nodes should reflect known characteristics from the source data,
like high-volume accounts with expected transfer counts.

If counts don't match, the most common causes are failed node loads
or key value mismatches between DataFrame columns and node
properties. The connector silently drops relationships when the
MATCH clause can't find the target node.
-->

---

## Graph Insights Flow Back to the Lakehouse

- **Cycle Detection:** fraud ring flags in the alerts table
- **PageRank:** risk scores for investigation prioritization
- **Community Detection:** fraud ring groupings via Louvain
- **Degree Centrality:** counterparty counts as ML features

<!--
Graph intelligence flows back as standard DataFrames. Graph-derived
metrics become columns in Delta Gold tables, available for
dashboards, ML features, and downstream analytics.

Cycle detection identifies accounts involved in circular
transaction chains and writes a flag to the fraud alerts table.
PageRank scores influential accounts based on transaction flow
patterns, producing a risk-scoring column for investigation
prioritization. Louvain community detection clusters tightly
connected accounts into groups for fraud ring identification.
Degree centrality counts how many counterparties an account
transacts with, feeding fraud-prediction ML models.

Once in Delta Lake, these insights join with operational data
like account histories that never left the lakehouse. This is
the Gold layer in action: graph intelligence enriching data
intelligence.
-->

---

## Foundation for Data Intelligence Meets Graph Intelligence

- **The Medallion Architecture is built.** Data intelligence and graph intelligence are connected
- **Bronze:** raw data landed from cloud storage
- **Silver:** cleaned, governed tables fed the Spark Connector
- **Gold:** graph insights flowing back as fraud alerts, risk scores, ML features

**Next:** enriching the graph with unstructured knowledge through Knowledge Graph Construction

<!--
We've walked through the full data pipeline. Raw data landed in
Bronze, got cleaned and governed in Silver, and the Spark
Connector projected connection data into Neo4j. Graph algorithm
results flow back as columns in Gold tables: fraud alerts, risk
scores, ML features.

That's the initial Medallion Architecture end to end. Delta Lake
governs the data, Neo4j reveals the connections, and the Spark
Connector bridges both directions.

So far we've only loaded structured, tabular data. The foundation
handles rows and columns well, but the graph can hold more than
that. The next stage adds unstructured knowledge: AML policy
documents, maintenance manuals, regulatory text. Knowledge Graph
Construction chunks those documents, extracts entities, generates
embeddings, and writes them into the graph. That's where we're
headed next.
-->

---

## Appendix: Implementation Details

---

## Debugging: When Relationships Fail to Create

If relationships fail to create, the MATCH clauses aren't finding nodes. Two common causes:

1. **The node load failed** and the target Account doesn't exist
2. **Key values don't match** between the DataFrame column and the node property

The connector doesn't surface which case applies. If a match fails because no Account node has an `account_id` matching the DataFrame value, that relationship row **silently drops**.

**Checking manually is required.** Compare the node properties in Neo4j against the relationship DataFrame values to identify mismatches.

---

## Appendix: Graph vs. SQL Decision Framework

---

## When to Query the Graph vs. Stay in the Lakehouse

**Stay in SQL / Databricks when:**

- The question is about aggregation: totals, averages, counts, distributions
- The data fits naturally in rows and columns with no recursive joins
- You need full-table scans over billions of records (Spark's distributed engine is built for this)
- The answer lives in a single table or a small number of predictable joins

**Move to Cypher / Neo4j when:**

- The question involves connections between entities — "who is connected to whom?"
- You need variable-length traversal — following chains where the depth isn't known in advance
- The join count would be three or more self-joins against the same table
- You need real-time path finding or pattern matching against a connection topology
- The query shape changes based on what you find (exploratory traversal)

**The rule of thumb:** if you're counting things, stay in SQL. If you're following connections, move to the graph.

---

## Decision Table: SQL vs. Cypher

| Signal | Stay in SQL | Move to Cypher |
|--------|-------------|----------------|
| Number of hops | 1–2 fixed joins | 3+ or variable depth |
| Query shape | Known at design time | Depends on the data encountered |
| Result type | Aggregated numbers | Paths, subgraphs, connected components |
| Latency requirement | Batch is fine | Sub-second for interactive investigation |
| Data volume per query | Millions of rows scanned | Thousands of entities traversed |

---

## Appendix: Cypher vs. SQL Side-by-Side

---

## The Same Question, Two Languages

**Question:** Find all accounts within three hops of a known fraudulent account (account-1234) through shared devices or addresses.

**SQL (Databricks):**

```sql
WITH hop1 AS (
    SELECT DISTINCT ad2.account_id
    FROM account_devices ad1
    JOIN account_devices ad2
      ON ad1.device_id = ad2.device_id AND ad1.account_id != ad2.account_id
    WHERE ad1.account_id = 'account-1234'
    UNION
    SELECT DISTINCT aa2.account_id
    FROM account_addresses aa1
    JOIN account_addresses aa2
      ON aa1.address_id = aa2.address_id AND aa1.account_id != aa2.account_id
    WHERE aa1.account_id = 'account-1234'
),
hop2 AS (
    SELECT DISTINCT ad2.account_id
    FROM hop1 h JOIN account_devices ad1 ON h.account_id = ad1.account_id
    JOIN account_devices ad2
      ON ad1.device_id = ad2.device_id AND ad1.account_id != ad2.account_id
    UNION
    SELECT DISTINCT aa2.account_id
    FROM hop1 h JOIN account_addresses aa1 ON h.account_id = aa1.account_id
    JOIN account_addresses aa2
      ON aa1.address_id = aa2.address_id AND aa1.account_id != aa2.account_id
),
hop3 AS (
    SELECT DISTINCT ad2.account_id
    FROM hop2 h JOIN account_devices ad1 ON h.account_id = ad1.account_id
    JOIN account_devices ad2
      ON ad1.device_id = ad2.device_id AND ad1.account_id != ad2.account_id
    UNION
    SELECT DISTINCT aa2.account_id
    FROM hop2 h JOIN account_addresses aa1 ON h.account_id = aa1.account_id
    JOIN account_addresses aa2
      ON aa1.address_id = aa2.address_id AND aa1.account_id != aa2.account_id
)
SELECT account_id FROM hop1 UNION
SELECT account_id FROM hop2 UNION
SELECT account_id FROM hop3;
```

---

## The Same Question in Cypher

**Cypher (Neo4j):**

```cypher
MATCH (flagged:Account {account_id: 'account-1234'})
      -[:USED_DEVICE|REGISTERED_AT*1..3]-
      (connected:Account)
WHERE connected <> flagged
RETURN DISTINCT connected.account_id
```

The SQL version requires manually coding each hop as a separate CTE with explicit joins across two link tables. Adding a fourth hop means another CTE block. The Cypher version expresses the same traversal in three lines, and changing `*1..3` to `*1..5` extends the search with no structural change.

---

## Appendix: Schema Shift — Fraud Edition

---

## From Transaction Tables to a Fraud Graph

In the lakehouse, fraud data lives across several tables:

| Delta Table | Columns |
|-------------|---------|
| `accounts` | account_id, customer_name, ssn, opened_date, status |
| `transactions` | txn_id, from_account, to_account, amount, timestamp, channel |
| `devices` | device_id, fingerprint, ip_address |
| `account_devices` | account_id, device_id, first_seen, last_seen |
| `addresses` | address_id, street, city, state, zip |
| `account_addresses` | account_id, address_id, address_type |

In the graph, these become:

```
(:Account {account_id, customer_name, opened_date, status})
(:Device {device_id, fingerprint, ip_address})
(:Address {street, city, state, zip})
(:SSN {value})

(account)-[:TRANSFERRED_TO {amount, timestamp, channel}]->(account)
(account)-[:USED_DEVICE {first_seen, last_seen}]->(device)
(account)-[:REGISTERED_AT {address_type}]->(address)
(account)-[:HAS_SSN]->(ssn)
```

---

## Modeling Decisions That Matter

- **Shared attributes become nodes, not properties** — SSN as a column hides shared identities; SSN as a node makes the connection explicit without a self-join
- **Transactions become relationships with properties** — amount, timestamp, and channel ride on `TRANSFERRED_TO` directly, no foreign key resolution at query time
- **Temporal properties stay on relationships** — timestamps on `USED_DEVICE` and `TRANSFERRED_TO` enable time-windowed queries without a separate time-dimension table
- **Only connection-relevant data enters the graph** — columns like `marketing_opt_in` stay in Delta Lake; columns like `status` and `opened_date` stay on nodes because they filter fraud queries

---

## Appendix: Other Fraud Patterns the Graph Enables

---

## Synthetic Identity Fraud

- Fraudsters combine a real SSN with a fake name and address to fabricate identities
- Multiple synthetic identities share fragments — same SSN, device fingerprint, or mailing address — creating a hidden network
- In the graph, every shared attribute is an explicit connection; community detection surfaces clusters without predefined queries

```cypher
MATCH (a1:Account)-[:HAS_SSN|USED_DEVICE|REGISTERED_AT]->(shared)
      <-[:HAS_SSN|USED_DEVICE|REGISTERED_AT]-(a2:Account)
WHERE a1 <> a2
WITH a1, a2, COUNT(DISTINCT shared) AS shared_identifiers
WHERE shared_identifiers >= 2
RETURN a1.account_id, a2.account_id, shared_identifiers
ORDER BY shared_identifiers DESC
```

---

## First-Party Fraud Rings

- A coordinated group opens accounts, builds credit history, maxes out credit lines simultaneously, and disappears
- Each individual account looks legitimate in isolation — the ring is only visible through shared connections
- Community detection algorithms (Louvain, Label Propagation) identify tightly connected clusters in the shared-attribute graph

**Operational flow:** Ingest in Delta (Bronze/Silver) → Load to Neo4j via Spark Connector → Run community detection → Write community assignments back to Gold tables for case management

---

## Bust-Out Fraud

- A fraudster opens an account, makes small purchases and on-time payments for months, then rapidly maxes out and vanishes
- The behavioral shift is visible as a change in transaction velocity and amounts over time
- Combined with shared-attribute connections, the graph reveals **coordinated** bust-outs across multiple accounts

```cypher
MATCH (a:Account)-[recent:PURCHASED]->(m:Merchant)
WHERE recent.timestamp > datetime() - duration('P30D')
WITH a, COUNT(recent) AS txn_30d, SUM(recent.amount) AS spend_30d
MATCH (a)-[hist:PURCHASED]->(m:Merchant)
WHERE hist.timestamp > datetime() - duration('P180D')
  AND hist.timestamp <= datetime() - duration('P30D')
WITH a, txn_30d, spend_30d,
     COUNT(hist) AS txn_prior, SUM(hist.amount) AS spend_prior
WHERE spend_30d > spend_prior * 2
RETURN a.account_id, spend_30d, spend_prior
ORDER BY spend_30d DESC
```
