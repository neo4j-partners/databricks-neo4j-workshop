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


# Text2Cypher Retriever

---

## From Natural Language to Database Queries

**The problem:** Some questions need precise facts, not semantic search.

**Text2Cypher solution:**
1. User asks a question in natural language
2. LLM generates a Cypher query from the question
3. Query executes against the graph
4. Precise, structured results returned

**Example:**
- Question: "How many critical maintenance events does aircraft N10001 have?"
- Generated: `MATCH (a:Aircraft {tailNumber:'N10001'})-[:HAS_SYSTEM]->()-[:HAS_COMPONENT]->()-[:HAS_EVENT]->(e:MaintenanceEvent {severity:'CRITICAL'}) RETURN count(e)`
- Result: `7`

---

## How It Works

```
User: "Which components were removed from aircraft N10001?"
    ↓
[LLM + Schema] → Generate Cypher
    ↓
MATCH (a:Aircraft {tailNumber: 'N10001'})
      -[:HAS_SYSTEM]->()-[:HAS_COMPONENT]->(c:Component)
WHERE EXISTS { (c)-[:HAS_EVENT]->(:MaintenanceEvent {action: 'REMOVED'}) }
RETURN c.name
    ↓
[Execute Query]
    ↓
Result: High-pressure Turbine, Low-pressure Compressor, ...
```

---

## Creating a Text2Cypher Retriever

```python
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.schema import get_schema

# Schema tells LLM what's queryable
schema = get_schema(driver)

text2cypher_retriever = Text2CypherRetriever(
    driver=driver,
    llm=llm,                    # LLM for Cypher generation
    neo4j_schema=schema         # Graph structure
)
```

**The schema is critical:** Without it, the LLM guesses (often incorrectly).

---

## The Role of Schema

**Schema tells the LLM:**
```
Node properties:
  Aircraft {tailNumber: STRING, model: STRING}
  Component {name: STRING, type: STRING}
  MaintenanceEvent {fault: STRING, severity: STRING}

Relationships:
  (:Aircraft)-[:HAS_SYSTEM]->(:System)
  (:System)-[:HAS_COMPONENT]->(:Component)
  (:Component)-[:HAS_EVENT]->(:MaintenanceEvent)
```

**With schema:** LLM knows exactly what entities and relationships exist.
**Without schema:** LLM invents non-existent properties and relationships.

---

## Best For

**Use Text2Cypher when:**

- You need precise facts, counts, or lists
- Question is about specific entities
- Aggregations are needed
- Direct graph queries (no semantic search)

**Example questions:**
- "How many critical maintenance events does aircraft N10001 have?"
- "List all components removed from the hydraulics system"
- "Which aircraft has the most maintenance events?"
- "What is the average severity score per system?"

---

## Performing a Search

```python
query = "Which components were removed from aircraft N10001?"

results = text2cypher_retriever.search(query_text=query)

# Results contain:
# - The generated Cypher query
# - The query results
for record in results.records:
    print(record)
```

**Behind the scenes:** LLM analyzes your question, generates Cypher, executes it.

---

## Limitations

**Text2Cypher requires questions that map to schema:**

- Question: "What's the sentiment about AI regulation?"
- Problem: No "sentiment" property in schema
- Result: Cannot generate valid query

**Text2Cypher may struggle with:**
- Ambiguous questions
- Questions requiring interpretation
- Content that lives in text chunks (use Vector instead)

---

## Security Considerations

Text2Cypher executes LLM-generated queries. Important safeguards:

- **Use read-only credentials**: Prevent accidental data modification
- **Validate queries**: Check for dangerous operations (DELETE, DROP)
- **Limit results**: Ensure LIMIT clauses prevent unbounded returns
- **Monitor usage**: Log generated queries for review
- **Trust boundaries**: Don't expose to untrusted users

---

## Generated Query Quality

**LLMs may generate imperfect Cypher:**

- Syntax errors
- Deprecated syntax
- Non-existent properties
- Inefficient patterns

**Mitigation:**
- Use custom prompts to guide Cypher generation
- Validate generated queries
- Handle errors gracefully

---

## Comparing All Three Retrievers

| Question | Best Retriever | Why |
|----------|---------------|-----|
| "What causes turbine bearing wear?" | Vector | Semantic content |
| "Which aircraft have components with bearing faults?" | Vector Cypher | Content + entities |
| "How many critical events are on Engine #1?" | Text2Cypher | Precise count |
| "Describe hydraulic system failures" | Vector | Exploratory content |
| "List components removed from N10001" | Text2Cypher | Specific entity facts |

---

## Summary

Text2Cypher Retriever converts natural language to database queries:

- **LLM generates Cypher** from your question
- **Schema guides generation** for accuracy
- **Best for:** Facts, counts, lists, specific entities
- **Limitation:** Questions must map to graph schema

**You now know all three retrieval patterns:**
- Vector: Semantic content
- Vector Cypher: Content + relationships
- Text2Cypher: Precise facts

**Next:** Learn to build agents that choose the right retriever automatically.
