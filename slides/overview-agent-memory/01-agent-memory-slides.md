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

# Agent Memory with Neo4j

How AI agents remember: conversations, durable facts, and their own reasoning, carried across sessions instead of lost when the context window closes.

---

## The Agent You Built Forgets Everything

- **Basic agents work well for simple, one-off questions**, but not for an ongoing dialog
- **Ask it about `N10013`.** Then ask "any maintenance events on that aircraft?" and it has no idea what *that* means
- **The core problem:** it has no memory of the question you just asked
- **Every new question starts from zero**, like meeting the agent for the first time

**"Most agents you build today have no memory at all."**

<!--
1.0 minute. Not a criticism of any particular agent. Being stateless is often the correct default until you decide otherwise on purpose.
-->

---

## Three Layers of Agent Memory

- **Short term memory**
  - Current context
  - Compression, relevancy
  - Integrate tool results
- **Long term memory**
  - Episodic
  - Semantic / structural
  - Procedural / instructional
- **Reasoning memory**
  - Tool call traces
  - Reasoning traces
  - Previous decisions

<!--
0.5 minutes. The taxonomy the rest of the deck is built on. Read the three headers, not every sub-bullet.
-->

---

## Short-Term Memory

Conversation history and session state with automatic entity extraction

- **Conversation storage.** Sessions and messages persisted as graph nodes with metadata
- **Multi-stage entity extraction.** Pipeline combining spaCy, GLiNER, and LLM extractors with configurable merge strategies
- **Entity resolution.** Multi-strategy dedup: exact, fuzzy, and semantic matching with type-aware resolution

```python
session = await memory.add_session("user_123")
await memory.add_message(session.id, role="user",
    content="Review Jessica's account")
```

<!--
1.0 minute. Three properties: sessions and messages are graph nodes, extraction is multi-stage, resolution is multi-strategy. The pipeline behind that middle bullet gets its own slide next.
-->

---

## Entity Extraction Pipeline

Turning raw message text into named entities the graph can store and connect

- **What it is.** Pulling people, organizations, locations, events, and objects out of raw conversation text
- **How it works.** Three extractors run in a cascade: a fast free tagger first, a stronger free tagger if that's not enough, then a paid LLM as a last resort
- **Why cascade.** Most text is easy, so most extraction stays fast and free; only the ambiguous cases pay for the slower, more accurate LLM call

<!--
1.0 minute. The pipeline diagram is next; this slide is the plain-language version of the same three ideas.
-->

---

![bg contain](../../site/modules/ROOT/images/lab6-entity-extraction-pipeline.svg)

<!--
1.0 minute. Walk the picture left to right, then down: cascade across the top, merge and clean-up below it. No title on purpose, same treatment as the closing graph image.
-->

---

## Long-Term Memory

Persistent knowledge graph of entities, relationships, and learned preferences

![w:880](../../site/modules/ROOT/images/lab6-long-term-memory.svg)

<!--
1.5 minutes. POLE+O on the left is the entity model; the five capabilities on the right are what that model buys you, chiefly the temporal relationships row, since a preference that can expire is what lets memory be corrected later without deleting the old belief.
-->

---

## Reasoning Memory

Decision traces, tool usage audits, and provenance — the layer that makes AI explainable

- **Tool call traces.** Every tool invocation, parameters, results — complete audit trail
- **Decision provenance.** Why did the agent choose this path? Causal chain fully recorded
- **Learning from experience.** Agent checks if it solved something similar before, reuses successful patterns
- **Compliance & debugging.** When something goes wrong, you can trace exactly what happened and why

<!--
1.0 minute. This is the layer a vector store has nowhere to put.
-->

---

## Why Graphs for Agent Memory?

- **Relationships are first-class.** Connections between entities, decisions, and events are the data, not an afterthought
- **Multi-hop traversal.** Follow chains: Customer → Account → Transaction → Decision → Policy → Employee
- **Structural similarity.** Graph embeddings (FastRP) find similar situations by network topology, not just text
- **Explainable decisions.** Full provenance chain: trace exactly how and why every decision was made
- **Cross-session knowledge.** Information learned in one conversation is available in all future interactions
- **Production ready.** Neo4j: ACID compliance, enterprise scale, proven technology

<!--
1.5 minutes. The thesis slide for the whole deck: every bullet above is a reason the graph, not a vector store, is where memory lives.
-->

---

![bg contain](../../site/modules/ROOT/images/lab6-memory-graph.svg)
