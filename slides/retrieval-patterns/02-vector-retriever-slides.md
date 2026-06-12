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


# Vector Retriever

---

## What is a Vector Retriever?

The **simplest retriever**—finds content by meaning, not keywords.

**How it works:**
1. Convert your question to an embedding
2. Search vector index for similar chunk embeddings
3. Return the most semantically similar chunks

**Key insight:** "Engine bearing wear" finds content about "turbine component degradation" even without exact word matches.

---

## Creating a Vector Retriever

```python
from neo4j_graphrag.retrievers import VectorRetriever

vector_retriever = VectorRetriever(
    driver=driver,
    index_name='maintenanceChunkEmbeddings',
    embedder=embedder,
    return_properties=['text']
)
```

**Components:**
- **Driver**: Connection to Neo4j
- **Index**: Where embeddings are stored
- **Embedder**: Model that creates embeddings (e.g., OpenAI)

---

## Performing a Search

```python
query = "What maintenance procedures apply to engine bearing wear?"

results = vector_retriever.search(
    query_text=query,
    top_k=5
)

for record in results.records:
    print(f"Score: {record['score']:.4f}")
    print(f"Text: {record['text'][:200]}...")
```

**Each result includes:**
- **text**: The chunk content
- **score**: Similarity score (0-1, higher = more similar)

---

## Understanding Similarity Scores

| Score Range | Interpretation |
|-------------|----------------|
| 0.95-1.0 | Extremely similar (near-exact match) |
| 0.90-0.95 | Highly relevant |
| 0.85-0.90 | Relevant |
| 0.80-0.85 | Moderately relevant |
| < 0.80 | Weak relevance |

Higher scores indicate stronger semantic matches.

---

## Best For

**Use Vector Retriever when:**

- Finding conceptually similar content
- Questions like "What is...", "Tell me about...", "Explain..."
- Exploratory questions about topics
- When exact keywords don't match but meaning does

**Example questions:**
- "What causes hydraulic system failures?"
- "Describe bearing wear in turbine engines"
- "What maintenance actions address fuel flow issues?"

---

## Limitations

**Vector Retriever returns text only:**

- No entity relationships
- No structured data from the graph
- Can't aggregate across entities
- Can't traverse connections

**Example limitation:**
- Question: "What maintenance events affect Aircraft N10001?"
- Returns: Chunks about maintenance (may not be N10001-specific)
- Missing: Structured HAS_EVENT relationships for that aircraft

**When you need more:** Use Vector Cypher Retriever.

---

## The top_k Parameter

**Controls how many results to return:**

| top_k | Trade-off |
|-------|-----------|
| 1-3 | Fastest, most relevant only |
| 5-10 | Balanced coverage |
| 15-20 | Maximum coverage, may include less relevant |

**Rule of thumb:** Start with 5, adjust based on results.

---

## Summary

Vector Retriever is your foundation for semantic search:

- **Converts queries to embeddings** for meaning-based search
- **Returns semantically similar chunks** regardless of keywords
- **Best for** content questions, topic exploration
- **Limitation:** No graph relationships or structured data

**Next:** Learn how Vector Cypher Retriever adds graph intelligence.
