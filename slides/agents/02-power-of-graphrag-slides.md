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

# Activating the Intelligence Platform with GraphRAG

Knowledge graph construction and graph-enriched retrieval

---

## Why Agents? LLM Limitations in the Enterprise

- **LLMs alone aren't enough:** they hallucinate, lack domain context, can't reach private data, and produce non-deterministic answers
- **Context rot:** model performance degrades as the context window fills with irrelevant or conflicting information

<!--
LLMs hallucinate, lack domain context, can't access private data,
and produce non-deterministic answers. These aren't edge cases —
they're the default behavior when you point a general-purpose
model at enterprise data.

This deck shows how GraphRAG and specialized agents address each
of these gaps. First we build a knowledge graph that gives the
model grounded context. Then we introduce agents that can reach
live data across both platforms.
-->

---

## Embeddings and Vector Search

- **First, encode the meaning:** embedding models read text and produce numerical representations that capture what the text means, not just what it says
- **"Engine overheating" and "thermal runaway in turbine"** produce similar representations because they mean similar things
- **This enables semantic similarity search:** given a question, find the stored text whose meaning is most similar
- **The next step:** split documents into chunks and embed each one so the entire corpus becomes searchable by meaning

<!--
Embeddings are the foundation that makes semantic retrieval
possible. An embedding model takes a piece of text and produces
a fixed-length numeric vector that encodes its meaning. Texts
with similar meaning produce vectors that are close together
in this high-dimensional space, even when they use completely
different words.

Vector search exploits this property. Given a query, you embed
it into the same space and find the stored vectors nearest to it.
This is fundamentally different from keyword search: you match
by meaning rather than by string overlap.

This is what makes RAG work. When a user asks a question, the
system embeds the question, searches for the closest chunks, and
feeds those chunks to the LLM as context. The next slide shows
how documents get prepared for this process.
-->

---

## From Documents to Searchable Chunks

- **Documents split into Chunk nodes** with raw text, linked to source via `FROM_DOCUMENT`
- **Chunks link to each other** via `NEXT_CHUNK` to preserve document order
- **Embedding models** convert chunk text into vectors that capture semantic meaning
- **"Circular transfer" matches "round-trip fund movement"** — same meaning, different words
- **Vector index** searches by semantic similarity, not keyword matching

<!--
The first half of Knowledge Graph Construction turns unstructured
documents into searchable graph nodes. Documents get split into
fixed-size pieces, typically 500 to 1000 characters, with overlap
so context isn't lost at boundaries. Each chunk becomes a Chunk
node storing the raw text as a property, linked back to its
Document node via FROM_DOCUMENT and to adjacent chunks via
NEXT_CHUNK.

An embedding model converts each chunk's text into a vector. Chunks
with similar meaning end up close together in vector space,
regardless of the exact words used. A vector index enables fast
similarity search: "circular transfer pattern" and "round-trip
fund movement" match by meaning even though they share no keywords.

At this point the graph has searchable text but no structure to
traverse. The next step adds that.
-->

---

## From Chunks to Graph Structure

- **An LLM reads each chunk** and extracts entities: regulations, thresholds, procedures
- **Entities become graph nodes** linked to source chunks via `FROM_CHUNK`
- **Entity resolution** deduplicates: same regulation in 5 chunks = 1 node, 5 links
- **Cross-linking** connects extracted entities to the existing operational graph

<!--
Chunks give you searchable text, but the graph needs structured
nodes to traverse. Entity extraction bridges that gap.

An LLM reads each chunk and identifies structured entities:
regulations, monetary thresholds, compliance procedures. These
become graph nodes with typed properties, linked back to the
chunks they were extracted from via FROM_CHUNK. That link is
provenance: you can always trace an entity back to the text it
came from.

Entity resolution handles deduplication. The same regulation
mentioned across five different chunks becomes one node with
five links, not five separate nodes. Cross-linking connects
extracted entities to the existing operational graph, so a
procedure that applies to a specific account type links directly
to those account nodes.

This is the "graph" half of GraphRAG. After vector search finds
relevant chunks, graph traversal follows the entities and
relationships surrounding those chunks to gather richer context.
Without entity extraction, there's nothing to traverse.
-->

---

## What the Knowledge Graph Contains

```
(:Document)--[:FROM_DOCUMENT]-->(:Chunk {text, embedding})--[:NEXT_CHUNK]-->(:Chunk)
                                         |
                                   [:FROM_CHUNK]
                                         |
                                         v
                          (:Regulation)  (:Threshold)  (:Procedure)
                                              |
                                        [:APPLIES_TO]
                                              v
                          (:Account)--[:TRANSFERRED_TO]-->(:Account)
```

<!--
This diagram shows the two layers of the knowledge graph and how
they connect. Documents become chunks with embeddings that feed a
vector index for semantic search. Entity extraction pulls structured
nodes from those chunks. Cross-linking connects extracted entities
to the operational transaction graph built by the data pipeline.

The top half is what Knowledge Graph Construction adds. The bottom
is what the Spark Connector built in the data pipeline. The
APPLIES_TO relationship bridges them.
-->

---

## GraphRAG: Graph-Enriched Retrieval

- **Data pipeline complete:** Spark Connector projected Delta tables into graph nodes and relationships
- **KG construction complete:** AML policy docs chunked, embedded, entity-extracted into the graph
- **The graph now holds** structured connections and regulatory knowledge
- **Search finds the starting points:** chunks closest in meaning to the question
- **Graph traversal enriches:** follows entities and relationships from those chunks
- **Agents receive richer context** than text search alone

<!--
The previous deck built the data pipeline: governed Delta tables
projected into Neo4j via the Spark Connector. That gave us account
nodes, transfer relationships, and shared-attribute connections.
The preceding slides walked through knowledge graph construction:
chunking, embedding, entity extraction, and cross-linking. The
graph is now enriched with both structured transaction data and
regulatory knowledge.

Vector or fulltext search finds the chunks most relevant to the
user's question. That's standard RAG. What GraphRAG adds is graph
traversal from those chunks through the entities and relationships
surrounding them.

When search returns a chunk about "enhanced due diligence for
high-value transfers," graph traversal follows the extracted
entities to find the specific regulations, thresholds, and
procedures connected to that chunk, plus any operational graph
nodes those entities link to. The agent receives all of this
as context, not just the chunk text.

This is why the entity extraction step matters. Without extracted
entities linked to chunks and cross-linked to the operational
graph, there's nothing for the graph traversal to follow. You'd
just have text search.
-->

---

# From Retrieval to Agents

Specialized agents for graph and lakehouse

---

## Beyond GraphRAG: Reaching the Lakehouse

- **GraphRAG reaches graph data:** grounded answers with entities and relationships from the knowledge graph
- **The lakehouse holds the rest:** transaction volumes, aggregations, trends in Delta tables
- **GraphRAG can't compute SQL:** "total transfer volume for this fraud ring?" lives in the lakehouse
- **To span both platforms,** we need more than retrieval

<!--
GraphRAG grounds LLM answers in retrieved content and enriches
them with graph context: entities, relationships, connected
chunks. This is a real improvement over plain text search.

But GraphRAG can only reach data in the graph. The fraud graph
holds account connections as TRANSFERRED_TO relationships, but
the full transaction ledger stays in Delta Lake. GraphRAG cannot
answer "what is the total transfer volume for accounts in this
fraud ring?" because that requires a SQL aggregation over rows
that never entered the graph. To answer questions that span both
platforms, we need agents.
-->

---

## Specialized Agents for Different Data Structures

- **Context window pollution:** two schemas, two query languages, and two sets of conventions in one prompt dilutes focus
- **Narrowed scope:** an agent that only knows about graph structure writes graph queries; an agent that knows about both starts mixing them up
- **Different reasoning patterns:** SQL thinks in rows, filters, and aggregations; Cypher thinks in paths, patterns, and traversals
- **Reliability:** a generalist agent produces queries that mix idioms, like trying a JOIN where a traversal belongs

<!--
GraphRAG handles graph retrieval. But the lakehouse needs its own
agent that speaks SQL, and the graph needs an agent that speaks
Cypher. Each platform has its own query language, schema
conventions, and structure. A single agent spread across both
can't maintain the focused context needed to generate reliable
queries against either.

When an agent only needs to reason about Delta tables, the schema
becomes a constraint that guides generation rather than a
suggestion it might ignore. Same for graph relationships. Focused
agents produce reliable queries by mastering one platform each.

The architecture: one agent per platform, a supervisor to
coordinate them. That's what we build next.
-->

---

## Databricks Genie: Natural Language to SQL

- **Compound AI system:** turns natural language into governed SQL
- **Purpose-built for tabular data:** optimized for SQL generation against rows and columns
- **Lakehouse and federated sources:** queries any data registered in Unity Catalog
- **Users ask in English:** "Total transfer volume for account-1234?" becomes SQL and executes
- **Read-only execution:** generated queries can never modify your data

<!--
Genie is not a single LLM. It's a compound AI system with multiple
interacting components specialized for natural language to SQL.

Genie queries any data registered in Unity Catalog: managed tables,
external tables, foreign tables from federated sources like
Snowflake, PostgreSQL, and BigQuery, plus views and materialized
views. Unity Catalog provides the metadata that makes Genie smart:
table names, column descriptions, primary/foreign key relationships.
Column-level context is intelligently filtered so only relevant
metadata reaches the model.

Domain experts configure Genie Spaces: curated sets of tables with
JOIN definitions, up to 100 plain-text instructions teaching domain
terminology and business rules, and example SQL queries that Genie
selects from when they match the user's question. When a response
matches a parameterized example query exactly, Genie marks it as
"Trusted" so users know the answer came from a verified path.

Every generated query is read-only, so Genie can never modify
your data.
-->

---

## Neo4j Graph Agent: Natural Language to Cypher

- **Graph-specialized agent:** turns natural language into Cypher traversals
- **Purpose-built for connected data:** optimized for paths, patterns, and multi-hop relationships
- **Schema-aware:** inspects every node label, relationship type, and property key before querying
- **Users ask in English:** "Which accounts are within three hops?" becomes a Cypher traversal
- **Read-only by default:** generated queries can never modify production data

<!--
Just as Genie is purpose-built for SQL against tabular data, this
agent is purpose-built for Cypher against connected data. It
understands graph patterns: paths, multi-hop traversals, cycle
detection, shared-attribute matching.

Because the agent knows that Account nodes connect through
TRANSFERRED_TO relationships, it writes precise traversals instead
of hallucinating table names or join conditions. The graph's
schema becomes a constraint that guides generation, not a
suggestion to ignore.

Every generated query is read-only, so the agent can never modify
production graph data.
-->

---

## How the Graph Agent Reaches Neo4j

- **MCP (Model Context Protocol):** exposes `get-schema`, `read-cypher`, and `list-gds-procedures` as agent tools
- **GraphRAG library:** retriever components for vector search, hybrid search, and graph-enriched retrieval over the knowledge graph
- **Agent memory:** graph-native memory that stores conversations, extracts entities, and captures reasoning traces across sessions
- **Python driver:** powers both libraries with direct Neo4j connectivity for queries, vector search, and transaction management
- **Agent context:** schema discovery + system prompt give the agent graph structure and domain knowledge

<!--
The agent accesses Neo4j through two paths. MCP exposes graph
intelligence as standard agent tools: get-schema for structure
discovery, read-cypher for query execution, and list-gds-procedures
for graph analytics when GDS is installed.

The Python driver provides a separate path for GraphRAG retrievers
like VectorCypherRetriever, which combines vector similarity search
with graph traversal in a single query.

Agent context comes from two sources working together. Schema
discovery via get-schema auto-inspects the graph structure using
APOC introspection so the agent knows every node label, relationship
type, and property key. The system prompt adds domain knowledge:
what a flagged account is, how fraud rings are structured, what
traversal depth is appropriate. Together they ensure the agent
queries against verified schema with domain-appropriate patterns.
-->

---

## Neo4j MCP Tools

- **`get-schema`:** APOC introspection, auto-discovers structure, token-efficient for LLMs
- **`read-cypher`:** read-only Cypher with parameterized inputs
- **`list-gds-procedures`:** discovers graph analytics (PageRank, community detection) when GDS is installed
- **Read-only mode:** `write-cypher` hidden entirely, agents can never modify production data

<!--
get-schema introspects the live database using APOC, sampling
nodes and relationships to discover the full graph structure.
The result is post-processed into a token-efficient JSON
representation optimized for LLM consumption: property types
without verbose metadata, relationships reduced to direction
and target labels, nulls and empties stripped.

read-cypher executes read-only Cypher statements with optional
parameterized inputs. In read-only mode, write-cypher is hidden
entirely so agents can never modify production data.

list-gds-procedures discovers available Graph Data Science
algorithms: centrality, community detection, similarity, path
finding. Only exposed when the GDS library is installed. This
lets agents run PageRank, community detection, and other
analytics directly.
-->

---

## Multi-Agent Supervisor: Routing to the Right Platform

A **supervisor agent** sits above both specialists and routes questions based on their nature.

```
                    User Question
                         |
                         v
                +--- Supervisor ---+
                |                  |
                v                  v
        Genie Space Agent    Neo4j MCP Agent
        (Lakehouse / SQL)    (Graph / Cypher)
```

<!--
The supervisor doesn't answer questions itself. It reads the
question, determines which data shape it targets, and routes to
the right specialist agent. If the question spans multiple data
shapes, it decomposes the question and sends sub-tasks to each
agent, then synthesizes a single answer.
-->

---

## The Intelligence Platform Is Active

- **Data layer (Deck 01):** governed Delta tables ↔ graph nodes via the Spark Connector
- **Knowledge layer:** unstructured docs → chunks, embeddings, entities in the graph
- **Retrieval layer:** vector search + graph traversal = GraphRAG
- **Agent layer:** Genie (SQL) + Neo4j MCP (Cypher), supervisor routes between them
- **Next:** hands-on labs — build the graph, configure agents, query both platforms

<!--
Deck 01 built the data foundation: Bronze landing, Silver
governance, Spark Connector projection into Neo4j, Gold tables
enriched with graph algorithm results.

This deck added three layers on top. Knowledge Graph Construction
turned unstructured AML policy documents into chunks with
embeddings and extracted entities cross-linked to the operational
graph. GraphRAG combines vector search with graph traversal so
agents receive richer context than text search alone. Specialized
agents master one platform each: Genie for SQL, the Neo4j MCP
agent for Cypher. A supervisor routes questions to the right
specialist and decomposes multi-source questions across both.

The full intelligence platform is now active: governed data,
enriched knowledge graph, semantic retrieval, and coordinated
agents. The hands-on labs let you build this yourself.
-->
