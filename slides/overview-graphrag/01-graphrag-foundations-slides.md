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

# GraphRAG Foundations

From GenAI Limitations to Graph-Enriched Retrieval

<!-- The Business Case deck made the argument and Knowledge Graph Foundations built the graph. This one lays out the technique that makes the aircraft digital twin answerable in plain language, from LLM gaps through RAG to graph traversal. -->

---

## GenAI Limitations

Foundation models are powerful, but they have critical gaps:

- **Hallucination:** generate confident, incorrect answers
- **Knowledge cutoff:** training data has a fixed date, no access to this week's maintenance logs
- **Relationship blindness:** cannot traverse how an aircraft's systems, sensors, and maintenance events connect

These gaps matter when a technician needs a grounded, traceable answer, not a guess.

<!-- One-line recall of the Business Case deck, not a new argument. Say it fast. It exists to set up the next slide: something has to hand the model your data and its relationships at query time. -->

---

## What Is RAG?

**Retrieval-Augmented Generation** gives the LLM relevant context before it answers.

```
User Question
    ↓
Retrieve relevant chunks
    ↓
Pass chunks + question to LLM
    ↓
LLM generates a grounded answer
```

The LLM answers from retrieved evidence, not memory alone. Retrieval quality determines answer quality.

<!-- RAG fixes knowledge cutoff and hallucination by giving the model specific text at question time instead of relying on training memory. The open question is how you find the right text. -->

---

## Embeddings

An **embedding** is a list of numbers that represents the meaning of text, not just its words.

- "Bearing wear on Engine 1" and "turbine component degradation" produce similar vectors, because they describe related faults
- "Bearing wear on Engine 1" and "flight FL00123 departed JFK" produce vectors far apart
- The embedding model reads a chunk of text and outputs a fixed length vector

Embeddings power **semantic search**: matching on meaning rather than exact keywords.

![bg right:42% contain](../images/embeddings_visual.jpg)

<!-- This is the foundation. Once text becomes a vector, "similar meaning" becomes "nearby points," and finding relevant passages becomes a distance calculation, not a keyword match. -->

---

## Vector Search

Given a question, the system:

1. **Embeds the question** into a vector, using the same embedding model
2. **Compares** that vector against every stored chunk vector
3. **Returns** the passages closest in meaning, ranked by cosine similarity

Cosine similarity near 1.0 means very similar meaning; near 0.0 means unrelated.

Ask "what engine problems occurred" and the system finds chunks about bearing wear and overheat, even though neither chunk contains the words "engine problems."

![bg right:42% contain](../images/beyond_keywords.jpg)

<!-- The smart librarian idea: a catalog search for "dogs" misses a book about "canines." A librarian who has read every book finds it anyway, matching on what the book is about. -->

---

## Chunking

Maintenance manuals run to hundreds of pages. An LLM cannot process one in a single pass, so each manual is split into **chunks** before extraction and embedding.

Chunk size is a trade-off:

- **Larger chunks:** more context for entity extraction. "The engine" resolves to "CFM56-7B Engine 1" only when the surrounding text is visible
- **Smaller chunks:** more precise retrieval. A search returns the relevant paragraph, not the whole page

**Overlap** between consecutive chunks preserves context at the boundary, so a procedure split across two chunks does not get cut mid-step. A moderate size, 500 to 1000 characters, is a reasonable starting point for maintenance manuals.

<!-- A genuine two-sided trade-off, not a knob to maximize. Lab 3 fixes a specific chunk size for the maintenance manuals; this slide is why that number is not arbitrary. -->

---

## The Limit of Vector Search Alone

Vector search returns **isolated passages**:

- You get chunk text and a similarity score
- No information about *which aircraft* or *which system* the passage describes
- No connection to related maintenance events or sensor readings elsewhere in the corpus

"Here are chunks about bearing wear." But on which aircraft? Which engine? Is it still flying?

<!-- The hinge of the deck. Everything before explains how traditional RAG works; everything after explains what graph traversal adds, and why it is necessary rather than decorative. -->

---

## Context Rot

Even with context windows growing to hundreds of thousands of tokens, more context does not mean better answers.

**Context rot:** as the volume of retrieved context grows, model accuracy on questions about that context *decreases*. The signal gets diluted by noise.

The fix is not a bigger context window. It is **better retrieval**: finding precisely the right information, and nothing more.

[Source: Chroma Research, Context Rot]

![bg right:52% contain](../images/context_rot_hero_plot.png)

<!-- Dumping every loosely related chunk into the prompt can make the answer worse than a narrower, well targeted retrieval. That is the case for precision over breadth, which is what graph traversal adds. -->

---

## Questions Vector Search Alone Cannot Answer

| Question | Why It Fails |
|----------|---------------|
| Which aircraft have engines with critical maintenance events? | Requires traversing Aircraft to System to Component to Event |
| What components share the same fault type across the fleet? | Requires finding a shared pattern across aircraft, not one passage |
| Which flights were delayed by a specific maintenance issue? | Requires aggregation, not similarity |

These need *structured context* that preserves relationships, not just text that reads similarly.

<!-- Each is a one line Cypher traversal once the data is in the graph, and unanswerable by similarity search, which has no notion of a relationship at all. -->

---

## Enter GraphRAG

**GraphRAG** combines vector search with graph traversal.

| Approach | What You Get |
|----------|---------------|
| **Vector search alone** | "Here are chunks about engine bearing wear" |
| **GraphRAG** | "Here are chunks about engine bearing wear, on **Aircraft AC1001**, **Engine 1**, part of the **Propulsion System**" |

Graph connections turn an isolated passage into a **contextual, grounded answer**.

<!-- Same retrieval step, one more hop. The chunk search does not change; what changes is what happens after a chunk comes back. -->

---

## The Two-Layer Graph

```
(:Document)--[:FROM_DOCUMENT]-->(:Chunk {text, embedding})--[:NEXT_CHUNK]-->(:Chunk)
      |
[:APPLIES_TO]
      v
(:Aircraft)--[:HAS_SYSTEM]-->(:System)
```

The top layer is text: chunks with embeddings, linked to their source manual and to each other in reading order.

The bottom layer is structure: the aircraft and systems the manual describes, already built by the Lab 2 data pipeline.

`APPLIES_TO` is the bridge between them.

<!-- Two layers, built at two different times. The bottom layer is the operational graph the Spark Connector loaded in Lab 2. The top layer is what Lab 3 adds: manuals, chunked and embedded. APPLIES_TO connects them. -->

---

## How Graph-Enriched Retrieval Works

1. **Vector search** finds chunks whose meaning matches the question
2. **Graph traversal** follows relationships from each matched chunk:
   - `(Chunk)-[:FROM_DOCUMENT]->(Document)`: which manual?
   - `(Document)-[:APPLIES_TO]->(Aircraft)`: which aircraft?
   - `(Aircraft)-[:HAS_SYSTEM]->(System)`: which system?
   - `(Chunk)-[:NEXT_CHUNK]->(Chunk)`: what comes next, so a split procedure arrives whole
3. **LLM** receives chunk text plus the structured entity context

<!-- NEXT_CHUNK runs sideways, not up or down the layers. Chunk boundaries are arbitrary but procedures are not; a step cut mid-sentence needs its neighbor to read whole. -->

---

![bg contain](../aircraft/graphrag-retrieval-flow.svg)

<!-- The same traversal as the previous slide, drawn out. Walk it left to right: question, embedding, vector index, matched chunk, then the graph hops to document, aircraft, and system before it lands at the LLM. -->

---

## Worked Example

**Question:** "What maintenance issues affect the turbine on AC1001?"

1. **Vector search** finds chunks from AC1001's maintenance manual discussing turbine wear
2. **Graph traversal** follows connections:
   - `FROM_DOCUMENT` to the manual's Document node
   - `APPLIES_TO` to Aircraft AC1001
   - `HAS_SYSTEM` to the Propulsion System
3. **LLM answer** is grounded in the manual text *and* the verified aircraft and system it applies to

<!-- Without the graph hop, the answer is generic turbine advice from whichever manual scored highest. With it, the answer is scoped to AC1001, and the system it names is a fact from the graph, not a guess. -->

---

## Why Graph Context Matters

Without graph context, the LLM must **infer** structure from raw text:

- Which aircraft does this manual apply to?
- Is this the same engine flagged in the sensor data?
- Which other aircraft share this component and might be at risk?

With graph context, these are **verified facts** from the knowledge graph, not LLM guesses. The graph supplies the structured backbone; vector search supplies the relevant text.

<!-- The pitch in one sentence: vector search finds the text, the graph verifies what the text is about. Neither replaces the other. -->

---

## Retrieval Strategies Preview

GraphRAG is not one technique. It is a family of retrieval patterns.

- **Vector search:** find chunks whose meaning matches the question
- **Graph-enriched search:** vector search, then traverse to the aircraft, system, and neighboring chunks
- **Text2Cypher:** translate the question directly into a Cypher query against the graph

Next: how each pattern works in Neo4j, and when to reach for it.

<!-- The map for the next deck. Vector search and graph-enriched search are what we just covered. Text2Cypher is a different move: instead of finding text, it writes and runs a query. All three become concrete Neo4j retrievers next. -->
