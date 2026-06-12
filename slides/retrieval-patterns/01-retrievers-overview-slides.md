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


# Neo4j GraphRAG Retrievers Overview

---

## From Knowledge Graph to Answers

You have a knowledge graph with:
- **Entities**: Aircraft, systems, components, sensors, maintenance events
- **Relationships**: HAS_SYSTEM, HAS_COMPONENT, HAS_EVENT, OPERATES_FLIGHT
- **Embeddings**: Vector representations for semantic search

**The question**: How do you *retrieve* the right information to answer user questions?

---

## What is a Retriever?

A **retriever** searches your knowledge graph and returns relevant information.

**Three retrieval patterns:**

| Retriever | What It Does |
|-----------|--------------|
| **Vector** | Semantic similarity search across text chunks |
| **Vector Cypher** | Semantic search + graph traversal for relationships |
| **Text2Cypher** | Natural language → Cypher query for precise facts |

Each pattern excels at different question types.

---

## Retrieval to Answer: How GraphRAG Works

Retrievers work with the **GraphRAG** class, which combines retrieval with LLM generation:

```
User Question
    ↓
Retriever finds relevant context
    ↓
Context passed to LLM
    ↓
LLM generates grounded answer
```

The retriever's job is finding the right context. The LLM's job is generating a coherent answer from that context.

---

## Vector Retriever

**How it works:**
- Converts your question to an embedding
- Finds chunks with similar embeddings
- Returns semantically related content

**Best for:**
- "What causes hydraulic pressure loss?"
- "Describe common turbine faults"
- Conceptual, exploratory questions

**Limitation:** Returns text chunks only—no entity relationships.

---

## Vector Cypher Retriever

**How it works:**
- Vector search finds relevant chunks
- Custom Cypher query traverses from chunks to related entities
- Returns content + structured data

**Best for:**
- "Which aircraft have components with critical maintenance events?"
- "What maintenance procedures apply to engines with bearing wear?"
- Questions needing both content and relationships

**Key insight:** The chunk is the anchor—you traverse from what vector search finds.

---

## Text2Cypher Retriever

**How it works:**
- LLM converts natural language to Cypher
- Query executes against the graph
- Returns precise, structured results

**Best for:**
- "How many critical maintenance events are there?"
- "List all components removed from aircraft N10001"
- Counts, lists, specific lookups

**Limitation:** Question must map to graph schema.

---

## Choosing the Right Retriever

| Question Pattern | Best Retriever |
|-----------------|----------------|
| "What is...", "Tell me about..." | Vector |
| "Which [entities] are affected by..." | Vector Cypher |
| "How many...", "List all..." | Text2Cypher |
| Content about topics | Vector |
| Content + relationships | Vector Cypher |
| Facts, counts, aggregations | Text2Cypher |

---

## The Decision Framework

**Ask yourself:**

1. **Am I looking for content or facts?**
   - Content → Vector or Vector Cypher
   - Facts → Text2Cypher

2. **Do I need related entities?**
   - No → Vector
   - Yes → Vector Cypher

3. **Is this about relationships?**
   - Traversals → Vector Cypher or Text2Cypher
   - Semantic → Vector

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

Swap `vector_retriever` for `vector_cypher_retriever` or `text2cypher_retriever` to change the retrieval strategy without changing any other code.

---

## External Vector Stores: Databricks Vector Search

GraphRAG's vector store is pluggable. If your team already uses **Databricks Vector Search**, vectors can stay in the Lakehouse while Neo4j provides graph context.

```python
from neo4j_graphrag.retrievers import ExternalRetriever

retriever = ExternalRetriever(
    driver=driver,
    id_property="chunkId",
    external_embedder=databricks_embedder,
    fetcher=databricks_vector_search_fetcher
)
```

**How it works:** Databricks Vector Search runs the similarity search and returns chunk IDs. Neo4j resolves those IDs to nodes and traverses the graph for context. Each system does what it does best.

---

## Summary

In this lesson, you learned:

- **Retrievers** search and return relevant information from your knowledge graph
- **Vector Retriever**: Semantic similarity search across chunks
- **Vector Cypher Retriever**: Semantic search + graph traversal
- **Text2Cypher Retriever**: Natural language to precise database queries
- **GraphRAG class**: Wraps any retriever with an LLM for end-to-end question answering
- **External vector stores**: Databricks Vector Search can replace the built-in vector index
- **Each retriever excels at different question types.** Choosing the right one matters.

**Next:** Deep dive into each retriever type.
