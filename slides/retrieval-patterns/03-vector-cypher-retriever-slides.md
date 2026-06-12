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


# Vector Cypher Retriever

---

## Beyond Basic Vector Search

**Vector Retriever:** Returns text chunks only.

**Vector Cypher Retriever:** Returns text chunks + related entities from graph traversal.

```
Query: "What maintenance issues affect aircraft components?"
    ↓
Vector Search: Find relevant chunks
    ↓
Graph Traversal: From chunks → Components → MaintenanceEvents → Aircraft
    ↓
Result: Content + structured entity data
```

---

## How It Works

**Two-step process:**

1. **Vector Search** (semantic)
   - Find chunks similar to your question
   - Same as Vector Retriever

2. **Cypher Traversal** (structural)
   - From each chunk, traverse the graph
   - Gather related entities and relationships
   - Return enriched context

**The combination:** Semantic relevance + graph intelligence.

---

## Creating a Vector Cypher Retriever

```python
from neo4j_graphrag.retrievers import VectorCypherRetriever

retrieval_query = """
MATCH (node)-[:FROM_DOCUMENT]-(doc:Document)-[:DESCRIBES]->(component:Component)
OPTIONAL MATCH (component)-[:HAS_EVENT]->(event:MaintenanceEvent)
WITH node, score, component, collect(event.fault)[0..20] AS faults
RETURN node.text AS text, score,
       {component: component.name, faults: faults} AS metadata
ORDER BY score DESC
"""

retriever = VectorCypherRetriever(
    driver=driver,
    index_name='maintenanceChunkEmbeddings',
    embedder=embedder,
    retrieval_query=retrieval_query
)
```

---

## Understanding the Retrieval Query

**The library provides automatically:**
```cypher
CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
YIELD node, score
-- Your query starts here with node and score --
```

**Your retrieval_query:**
- Receives `node` (matched chunk) and `score` (similarity)
- Traverses from node to related entities
- Returns enriched results

---

## Query Breakdown

```cypher
-- Traverse from chunk to the component it describes
MATCH (node)-[:FROM_DOCUMENT]-(doc:Document)-[:DESCRIBES]->(component:Component)

-- Get related maintenance events (OPTIONAL so components without events still appear)
OPTIONAL MATCH (component)-[:HAS_EVENT]->(event:MaintenanceEvent)

-- Aggregate faults, limit to 20
WITH node, score, component, collect(event.fault)[0..20] AS faults

-- Return chunk text + metadata
RETURN node.text AS text, score,
       {component: component.name, faults: faults} AS metadata
```

---

## Why OPTIONAL MATCH Matters

**Without OPTIONAL MATCH:**
```cypher
MATCH (company)-[:FACES_RISK]->(risk)
```
Only returns companies that *have* risk factors.

**With OPTIONAL MATCH:**
```cypher
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk)
```
Returns *all* companies; risks list is empty if none exist.

**Use OPTIONAL MATCH** for complete results.

---

## Best For

**Use Vector Cypher Retriever when:**

- You need content AND related entities
- Questions involve relationships
- You want to traverse from relevant content to connected data

**Example questions:**
- "Which components have bearing wear and what aircraft are they on?"
- "What maintenance events affect engines mentioned in these documents?"
- "Which aircraft systems are linked to the faults described in these manuals?"

---

## The Chunk as Anchor

**Critical concept:** You can only traverse from what vector search finds.

**Example problem:**
- Query: "What maintenance events affect Aircraft N10001?"
- Vector search finds: Chunks about "maintenance procedures" (not N10001-specific)
- Traversal: Goes to components mentioned in those chunks
- Result: May not include components on N10001

**Solution:** Ensure your question surfaces relevant chunks, or use Text2Cypher for entity-specific queries.

---

## When to Use Vector Cypher vs Text2Cypher

| Question Type | Best Retriever |
|---------------|----------------|
| Content + related entities | Vector Cypher |
| Specific entity facts | Text2Cypher |
| "What does [topic] affect?" | Vector Cypher |
| "How many [entities]?" | Text2Cypher |
| Semantic + relationships | Vector Cypher |
| Precise counts/lists | Text2Cypher |

---

## Summary

Vector Cypher Retriever combines semantic search with graph traversal:

- **Two-step process:** Vector search → Graph traversal
- **Custom Cypher query** defines what entities to gather
- **Returns:** Text chunks + structured metadata
- **Best for:** Questions needing content AND relationships
- **Key insight:** The chunk is the anchor for traversal

**Next:** Learn Text2Cypher for precise, entity-specific queries.
