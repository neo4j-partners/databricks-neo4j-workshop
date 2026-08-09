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

# GraphRAG Retriever Patterns

Vector, Vector Cypher, and Text2Cypher over the Aircraft Digital Twin

---

## From Knowledge Graph to Answers

- **Entities:** aircraft, systems, components, sensors, maintenance events
- **Relationships:** HAS_SYSTEM, HAS_COMPONENT, HAS_EVENT, OPERATES_FLIGHT
- **Embeddings:** vector representations for semantic search
- **Chunks:** text passages from maintenance manuals

**The question:** how do you retrieve the right information from this graph to answer what a participant asks.

<!--
Structured entities, relationships, and embedded text chunks are all in the
same graph. A retriever decides which of that content answers a given
question, and does it without the presenter writing custom code per question.
-->

---

## What Is a Retriever?

A **retriever** searches the knowledge graph and returns relevant information.

| Retriever | What It Does |
|---|---|
| **Vector** | Semantic similarity search across text chunks |
| **Vector Cypher** | Semantic search plus graph traversal for relationships |
| **Text2Cypher** | Natural language to Cypher for precise facts |

All three feed the same **GraphRAG** pipeline: retriever finds context, LLM generates the answer.

<!--
Three patterns, three jobs: meaning, meaning plus structure, exact facts.
The retriever's job stops at finding context. An LLM turns that context into
an answer, which is what the GraphRAG class does later in this deck.
-->

---

## Vector Retriever

The simplest retriever. Finds content by meaning, not keywords.

1. **Convert** the question to an embedding
2. **Search** the vector index for similar chunk embeddings
3. **Return** the most semantically similar chunks

```python
from neo4j_graphrag.retrievers import VectorRetriever

vector_retriever = VectorRetriever(
    driver=driver,
    index_name='maintenanceChunkEmbeddings',
    embedder=embedder,
    return_properties=['text']
)

results = vector_retriever.search(
    query_text="What maintenance procedures apply to engine bearing wear?",
    top_k=5
)
for record in results.records:
    print(f"Score: {record['score']:.4f}, Text: {record['text'][:200]}...")
```

<!--
"Engine bearing wear" finds content about "turbine component degradation"
even without exact word matches. Driver connects to Neo4j, index name points
at the stored embeddings, embedder turns the question into a vector. Each
result carries the chunk text and a similarity score.
-->

---

## Similarity Scores and top_k

| Score Range | Interpretation |
|---|---|
| 0.95-1.0 | Extremely similar, near-exact match |
| 0.90-0.95 | Highly relevant |
| 0.85-0.90 | Relevant |
| 0.80-0.85 | Moderately relevant |
| < 0.80 | Weak relevance |

| top_k | Trade-off |
|---|---|
| 1-3 | Fastest, most relevant only |
| 5-10 | Balanced coverage |
| 15-20 | Maximum coverage, may include less relevant results |

**Rule of thumb:** start with `top_k=5`, adjust based on results.

<!--
Higher scores mean stronger semantic matches. top_k controls how many
chunks come back. Five is a reasonable default for most maintenance
questions, then tune from what the results look like.
-->

---

## Vector Retriever: Best For and Limitations

**Best for:**
- "What causes hydraulic system failures?"
- "Describe bearing wear in turbine engines"
- Conceptual, exploratory questions

**Limitation:** returns text chunks only, no entity relationships, no structured data, no traversal.

Example: "What maintenance events affect Aircraft N10001?" Vector search returns chunks about maintenance in general, not necessarily N10001, missing the structured `HAS_EVENT` relationships that name that aircraft.

<!--
Vector search is exploratory and blind to graph structure. Entity-specific
and relationship-heavy questions need the next retriever.
-->

---

## Vector Cypher Retriever

**Vector Retriever:** text chunks only.
**Vector Cypher Retriever:** text chunks plus related entities from graph traversal.

**Two-step process:**
1. **Vector search**, semantic, identical to Vector Retriever
2. **Cypher traversal**, structural: from each matched chunk, gather related entities and relationships

This is the retriever Lab 3 and Lab 5 both build on. Master this one.

<!--
This is the most important retriever in the workshop. Lab 3 builds it, Lab
5's supervisor agent calls it as a tool. Nothing new happens in step one,
it is the same vector search as before. Step two is what makes this
retriever different: a Cypher query runs on every matched chunk.
-->

---

## Creating a Vector Cypher Retriever

```python
from neo4j_graphrag.retrievers import VectorCypherRetriever

system_context_query = """
WITH node
// From the matched chunk to its manual, to the aircraft that manual applies to
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)-[:APPLIES_TO]->(a:Aircraft)
MATCH (a)-[:HAS_SYSTEM]->(s:System)
// OPTIONAL so systems with no components still appear
OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(comp:Component)

WITH node, doc, a, s, comp
RETURN doc.aircraftType AS aircraft_type,
       a.tail_number AS aircraft,
       COLLECT(DISTINCT s.name)[0..3] AS systems,
       COLLECT(DISTINCT comp.name)[0..3] AS components,
       node.text AS context
"""

retriever = VectorCypherRetriever(
    driver=driver,
    index_name='maintenanceChunkEmbeddings',
    embedder=embedder,
    retrieval_query=system_context_query
)
```

<!--
Verbatim from Lab 3 notebook 02. Same driver, index, and embedder as
VectorRetriever, plus one new argument: retrieval_query. The library runs the
vector search automatically and hands this query `node` and `score`.
Everything after is plain Cypher: reach the manual, cross APPLIES_TO to the
aircraft, then collect its systems and components. Cypher comments use two
forward slashes.
-->

---

## Why OPTIONAL MATCH Matters

**Without OPTIONAL MATCH:**
```cypher
MATCH (s:System)-[:HAS_COMPONENT]->(comp:Component)
```
Drops any system that has no components attached, and the chunk with it.

**With OPTIONAL MATCH:**
```cypher
OPTIONAL MATCH (s:System)-[:HAS_COMPONENT]->(comp:Component)
```
Keeps every system; the components list comes back empty when none exist.

Use `OPTIONAL MATCH` whenever the surrounding node should appear in results even when the relationship is missing.

<!--
A plain MATCH here filters the whole row out, so a chunk about a system with
no components recorded never reaches the LLM at all. The retrieval query runs
per matched chunk, so one missing relationship silently loses a result.
-->

---

## The Chunk as Anchor

Graph traversal can only start from what vector search finds.

**Example problem:**
- Question: "What maintenance events affect Aircraft N10001?"
- Vector search finds: chunks about maintenance procedures in general, not N10001-specific
- Traversal: reaches the components those chunks mention
- Result: may not include components actually on N10001

If the question names a specific entity, use Text2Cypher, or make sure the question surfaces chunks that mention that entity.

<!--
This is the key limitation to internalize. Vector Cypher enriches what the
vector search surfaces, it does not search the whole graph. Weak vector
matches mean weak traversal, no matter how good the Cypher is.
-->

---

## Vector Cypher Retriever: Best For

- Content and related entities in the same answer
- Questions that involve relationships
- Traversing from relevant content to connected data

**Example questions:**
- "Which components have bearing wear, and what aircraft are they on?"
- "What maintenance events affect engines mentioned in these manuals?"
- "Which aircraft systems link to the faults described in these documents?"

<!--
Anything needing both the passage and the entities it names points here.
Purely conceptual questions are cheaper with Vector alone; precise counts
or lookups are more reliable with Text2Cypher.
-->

---

## Text2Cypher Retriever: How It Works

**The problem:** some questions need precise facts, not semantic search.

1. User asks a question in natural language
2. LLM generates a Cypher query from the question and the schema
3. Query executes against the graph
4. Precise, structured results return

**Example:**
Question: "How many critical maintenance events does aircraft N10001 have?"
Generated: `MATCH (a:Aircraft {tail_number:'N10001'})-[:HAS_SYSTEM]->()-[:HAS_COMPONENT]->()-[:HAS_EVENT]->(e:MaintenanceEvent {severity:'CRITICAL'}) RETURN count(e)`
Result: `7`

<!--
No embeddings involved. The LLM reads the graph schema, writes Cypher
directly from the question, and the query runs like any other Cypher query.
-->

---

## Creating a Text2Cypher Retriever

```python
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.schema import get_schema

# Schema tells the LLM what's queryable
schema = get_schema(driver)

text2cypher_retriever = Text2CypherRetriever(
    driver=driver,
    llm=llm,                    # LLM for Cypher generation
    neo4j_schema=schema         # Graph structure
)
```

**The schema is critical.** With it, the LLM knows exactly which node labels, properties, and relationships exist. Without it, the LLM guesses, and often invents properties that do not exist.

<!--
get_schema pulls the actual node labels, property types, and relationship
patterns from the live graph. That schema string keeps the generated Cypher
grounded in what the graph actually contains.
-->

---

## Text2Cypher: Best For, Limitations, Security

**Best for:** precise facts, counts, lists, specific entities, aggregations. Example: "List all components removed from the hydraulics system."

**Limitations:** questions must map to the schema. "What's the sentiment about this fault?" fails, there is no sentiment property. Generated Cypher can carry syntax errors or inefficient patterns; validate before trusting it.

**Security:** Text2Cypher executes LLM-generated queries.
- **Use read-only credentials**
- **Validate queries** for DELETE, DROP, and other write operations
- **Enforce LIMIT clauses**, log generated queries for review

<!--
Text2Cypher writes exact queries, and that power is the risk: an
LLM-generated query runs against your database. Read-only credentials and
query validation are not optional in production.
-->

---

## The GraphRAG Class

Retrievers find context. The **GraphRAG** class combines a retriever with an LLM to produce a grounded answer in one call.

```python
from neo4j_graphrag.generation import GraphRAG

rag = GraphRAG(
    retriever=vector_retriever,   # any retriever type
    llm=llm
)

response = rag.search(
    query_text="What maintenance procedures apply to engine bearing wear?",
    retriever_config={"top_k": 5}
)
print(response.answer)
```

Swap `vector_retriever` for `vector_cypher_retriever` or `text2cypher_retriever` to change the retrieval strategy without touching any other code.

<!--
This closes the loop: the retriever finds context, GraphRAG hands that
context to the LLM, and the LLM generates the answer. The retriever type is
a swap-in argument, nothing else changes.
-->

---

## External Vector Stores: Databricks Vector Search

GraphRAG's vector store is pluggable. If a team already uses **Databricks Vector Search**, vectors stay in the Lakehouse while Neo4j supplies graph context.

```python
from neo4j_graphrag.retrievers import ExternalRetriever

retriever = ExternalRetriever(
    driver=driver,
    id_property="chunkId",
    external_embedder=databricks_embedder,
    fetcher=databricks_vector_search_fetcher
)
```

| Vector Store | How It Works |
|---|---|
| **Neo4j, built-in** | Vectors and graph in one database, simplest setup |
| **Databricks Vector Search** | Vectors stay in the Lakehouse alongside Delta tables |

The external store runs the similarity search and returns matching IDs. Neo4j resolves those IDs to nodes and traverses the graph.

<!--
The graph context is the value-add regardless of where the vectors live.
Teams already invested in Databricks Vector Search keep their existing
embeddings pipeline and still get graph enrichment.
-->

---

## From Retrievers to Agent Tools

> "Which engines are showing abnormal EGT readings, what maintenance history do those aircraft have, and what does the maintenance manual say to do about high EGT?"

- **Abnormal EGT readings:** Genie Agent over Lakehouse sensor telemetry. EGT is Exhaust Gas Temperature
- **Maintenance history:** Vector Cypher Retriever, traversing from aircraft to their maintenance events
- **What the manual says:** Vector Retriever, semantic search over manual chunks

The Lab 5 supervisor agent wraps each retriever as a tool and routes each part of the question to the one that answers it.

<!--
This single question needs all three retrieval patterns plus Genie. No one
tool answers it alone. The next deck covers how the supervisor decides
which tool to call for which clause, and stitches the answers together.
-->

---

## Choosing the Right Retriever

| Question Pattern | Best Retriever | Why |
|---|---|---|
| "What causes...", "Describe..." | Vector | Semantic, conceptual content |
| "Which [entities] are affected by..." | Vector Cypher | Content plus related entities |
| "How many...", "List all..." | Text2Cypher | Precise counts and lookups |
| Content plus relationships | Vector Cypher | Chunk as anchor, then traverse |
| Facts, counts, aggregations | Text2Cypher | Direct graph query, no ambiguity |

Ask: content or facts? Do I need related entities? Is this about relationships? The answers point at one retriever.

<!--
Keep this table on hand while building Lab 3 and Lab 5. Most real
questions lean toward one retriever clearly; the hero question from the
previous slide is the exception that needs all three.
-->

---

## Summary

- **Vector Retriever:** semantic similarity across chunks, the foundation
- **Vector Cypher Retriever:** chunk as anchor, traverses to entities and relationships, the retriever Lab 3 and Lab 5 depend on
- **Text2Cypher Retriever:** natural language to exact Cypher, for facts and counts
- **GraphRAG class** wraps any retriever with an LLM for a grounded answer
- **External vector stores**, like Databricks Vector Search, can replace the built-in index without changing the graph traversal

Each retriever becomes an agent tool. The supervisor decides which one, or which combination, answers a given question.

<!--
Three patterns, one pipeline. The next deck covers the LangGraph supervisor
that routes questions across these retrievers, Genie, and the participant's
own Aura instance.
-->
