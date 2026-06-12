# Lab 3: Sample Cypher Queries


Copy and paste these queries into the [Neo4j Aura Query interface](https://console.neo4j.io) to explore the GraphRAG data structures built in this lab — document chunking, text embeddings, entity extraction, fulltext indexes, and vector indexes.

These queries run against the structures created during Lab 3. They will not return results until the notebooks in this lab have been run.

All of these queries can also be run programmatically via:
```bash
cd workshop-setup/populate_aircraft_db
uv run populate-aircraft-db samples
```

## Cypher Concepts Used

| Concept | What It Does |
|---|---|
| `MATCH (n:Label)` | Find nodes by label — the starting point for most queries |
| `(a)-[:REL]->(b)` | Traverse a relationship between two nodes (direction matters) |
| `OPTIONAL MATCH` | Like a SQL LEFT JOIN — keeps the row even if the pattern has no match |
| `RETURN ... AS alias` | Project properties and rename columns |
| `WITH` | Pipes results between query parts — like a subquery boundary |
| `count()`, `collect()` | Aggregate functions — count rows or gather values into a list |
| `substring(str, start, len)` | Extract part of a string — handy for previewing long text |
| `ORDER BY ... DESC` | Sort results (ascending by default) |
| `LIMIT n` | Cap the number of returned rows |
| `CASE WHEN ... THEN ... END` | Conditional expressions — like SQL CASE |
| `EXISTS { pattern }` | Tests whether a graph pattern exists |
| `UNWIND` | Expands a list into individual rows |
| `db.index.fulltext.queryNodes()` | Run a keyword search against a named fulltext index |
| `db.index.vector.queryNodes()` | Run a vector similarity search against a named vector index |
| `CALL { ... }` | Subquery block — used to scope intermediate results or call procedures |

---

## Document-Chunk Structure

### View all documents and their chunk counts

```sql
MATCH (d:Document)
OPTIONAL MATCH (d)<-[:FROM_DOCUMENT]-(c:Chunk)
RETURN d.documentId AS DocumentId,
       d.title AS Title,
       d.aircraftType AS AircraftType,
       count(c) AS ChunkCount
```

> **Concepts**: `OPTIONAL MATCH` keeps documents even if they have no chunks yet. `count()` aggregates the matched chunks per document.

### Browse the first few chunks of a document

```sql
MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
WHERE c.index IS NOT NULL
RETURN c.index AS ChunkIndex,
       substring(c.text, 0, 120) AS Preview,
       d.documentId AS Document
ORDER BY c.index
LIMIT 10
```

> **Concepts**: `substring()` truncates long text for readable output. `WHERE c.index IS NOT NULL` filters nulls before sorting — always required when using `ORDER BY`.

### Walk the chunk chain

```sql
MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
WHERE c.index IS NOT NULL
OPTIONAL MATCH (c)-[:NEXT_CHUNK]->(next:Chunk)
RETURN c.index AS ChunkIndex,
       substring(c.text, 0, 80) AS Preview,
       next.index AS NextChunkIndex
ORDER BY c.index
LIMIT 10
```

> **Concepts**: `OPTIONAL MATCH` on `NEXT_CHUNK` keeps the last chunk in the chain (which has no successor). `WHERE c.index IS NOT NULL` ensures clean sorting. This shows the linked-list structure that preserves reading order.

### Find the first and last chunks

```sql
MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
WHERE c.index IS NOT NULL
  AND (NOT EXISTS { (:Chunk)-[:NEXT_CHUNK]->(c) }
       OR NOT EXISTS { (c)-[:NEXT_CHUNK]->(:Chunk) })
RETURN c.index AS ChunkIndex,
       CASE
         WHEN NOT EXISTS { (:Chunk)-[:NEXT_CHUNK]->(c) } THEN 'FIRST'
         ELSE 'LAST'
       END AS Position,
       substring(c.text, 0, 100) AS Preview
ORDER BY c.index
```

> **Concepts**: `EXISTS { pattern }` checks whether a pattern exists in the graph. Negating it finds chain endpoints — the first chunk has no incoming `NEXT_CHUNK`, the last has no outgoing.

---

## Extracted Entities

### View entities extracted from maintenance manuals

```sql
UNWIND ['OperatingLimit'] AS label
CALL (label) {
    MATCH (n) WHERE label IN labels(n)
    RETURN n.name AS name
    LIMIT 10
}
RETURN label AS entity_type, collect(name) AS samples
```

> **Concepts**: `UNWIND` expands a list of labels into rows. The `CALL` subquery scopes a `MATCH` per label. `collect()` re-aggregates the results. These entities were extracted via SimpleKGPipeline during the enrich step.

---

## Cross-Links: Knowledge Graph to Operational Graph

### Document to Aircraft

```sql
MATCH (d:Document)-[:APPLIES_TO]->(a:Aircraft)
RETURN d.title AS source, a.tail_number AS target
LIMIT 10
```

### Sensor to OperatingLimit

```sql
MATCH (s:Sensor)-[:HAS_LIMIT]->(ol:OperatingLimit)
RETURN s.sensor_id AS source, ol.name AS target
LIMIT 10
```

### Full provenance chain: OperatingLimit to Chunk to Document to Aircraft

```sql
MATCH (ol:OperatingLimit)-[:FROM_CHUNK]->(c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
      -[:APPLIES_TO]->(a:Aircraft)
RETURN ol.name AS source, substring(c.text, 0, 60) AS chunk,
       a.tail_number AS target
LIMIT 10
```

> **Concepts**: These cross-links connect the knowledge graph (extracted entities from maintenance manuals) back to the operational aircraft graph. The provenance chain traces an operating limit all the way back through its source chunk, document, and the aircraft it applies to.

---

## Fulltext Keyword Search

> **Prerequisite:** These queries require the `maintenanceChunkText` fulltext index.

### Search for a specific term

```sql
CALL db.index.fulltext.queryNodes('maintenanceChunkText', 'V2500')
YIELD node, score
RETURN score,
       node.index AS ChunkIndex,
       substring(node.text, 0, 200) AS Content
ORDER BY score DESC
LIMIT 5
```

> **Concepts**: `db.index.fulltext.queryNodes()` performs keyword search using Lucene scoring. Exact term matches rank highest. Unlike vector search, this finds chunks containing the literal string "V2500".

### Search with multiple keywords

```sql
CALL db.index.fulltext.queryNodes('maintenanceChunkText', 'hydraulic pressure contamination')
YIELD node, score
RETURN score,
       node.index AS ChunkIndex,
       substring(node.text, 0, 200) AS Content
ORDER BY score DESC
LIMIT 5
```

> **Concepts**: Multiple keywords are OR'd together by default — chunks matching more keywords score higher. This is useful for domain-specific terminology where exact terms matter.

---

## Vector Similarity Search

> **Prerequisite:** These queries require the `maintenanceChunkEmbeddings` vector index.

### Find similar chunks using stored embeddings

```sql
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
CALL db.index.vector.queryNodes(
    'maintenanceChunkEmbeddings', 6, seed.embedding
) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT 5
RETURN substring(seed.text, 0, 100) AS seed_text,
       score AS similarity,
       substring(node.text, 0, 100) AS match_text
```

> **Concepts**: Picks a random chunk and uses its embedding to find the most similar chunks via the vector index. No API key needed — reuses stored embeddings. `WHERE node <> seed` excludes the seed from its own results.

### Vector search with document context

```sql
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
CALL db.index.vector.queryNodes(
    'maintenanceChunkEmbeddings', 6, seed.embedding
) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT 5
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
RETURN substring(seed.text, 0, 80) AS seed_text,
       score AS similarity,
       doc.documentId AS doc_id,
       doc.aircraftType AS aircraft_type,
       node.index AS chunk_idx,
       substring(node.text, 0, 80) AS match_text
```

> **Concepts**: Enriches vector results by traversing `FROM_DOCUMENT` to include source document metadata. This mirrors the VectorCypherRetriever pattern from Lab 3.

### Adjacent chunk retrieval

```sql
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
CALL db.index.vector.queryNodes(
    'maintenanceChunkEmbeddings', 6, seed.embedding
) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT 5
OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(node)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
RETURN substring(seed.text, 0, 80) AS seed_text,
       score AS similarity,
       doc.documentId AS doc_id,
       node.index AS chunk_idx,
       prev.index AS prev_idx,
       next.index AS next_idx,
       substring(node.text, 0, 80) AS match_text
```

> **Concepts**: Combines vector search with `NEXT_CHUNK` traversal to retrieve surrounding context. The `OPTIONAL MATCH` on prev/next keeps chunks at chain boundaries. This is the adjacent-chunks pattern from Lab 3.

### Vector search connected to aircraft topology

```sql
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
CALL db.index.vector.queryNodes(
    'maintenanceChunkEmbeddings', 6, seed.embedding
) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT 5
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
CALL (node) {
    MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)
    WHERE
        (node.text CONTAINS 'Engine' AND s.name CONTAINS 'Engine') OR
        (node.text CONTAINS 'Avionics' AND s.name CONTAINS 'Avionics') OR
        (node.text CONTAINS 'Hydraulic' AND s.name CONTAINS 'Hydraulic')
    RETURN a.tail_number AS tail, s.name AS sys_name
    LIMIT 3
}
RETURN substring(seed.text, 0, 80) AS seed_text,
       score AS similarity,
       doc.documentId AS doc_id,
       node.index AS chunk_idx,
       tail AS aircraft,
       sys_name AS system,
       substring(node.text, 0, 60) AS match_text
```

> **Concepts**: The most advanced pattern — semantic search results are connected to the operational graph via a `CALL` subquery that matches chunk text to system names. This bridges the knowledge graph and the aircraft topology.

---

## Indexes and Schema

### Verify the fulltext index

```sql
SHOW INDEXES
YIELD name, type, labelsOrTypes, properties
WHERE type = 'FULLTEXT'
RETURN name, labelsOrTypes, properties
```

> **Concepts**: Filters to show only fulltext indexes. Confirms that the `maintenanceChunkText` index covers the `text` property on `Chunk` nodes.
