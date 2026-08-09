# Agent Memory: How Neo4j and the Ecosystem Explain It

Research scratch file. Sources fetched between 2026-08-07 and 2026-08-08.

---

## 1. The headline finding

Neo4j has **two taxonomies in circulation**, and they do not agree. Knowing which
one you are quoting matters.

**Taxonomy A, the 2025 LangGraph-derived one.** Alex Gilmore's `Modeling agent
memory` (March 2025) takes Harrison Chase's LangChain talk and re-models it in
Cypher. Short-term vs long-term; long-term splits into **semantic / episodic /
procedural**; **temporal** is a cross-cutting fourth that applies to any of the
three. Writing happens **in the hot path** or **in the background**. This is the
vocabulary most of the ecosystem shares, because it comes from the CoALA paper
by way of LangGraph.

**Taxonomy B, the 2026 Neo4j Labs one.** The `neo4j-agent-memory` library, the
Neo4j Agent Memory Service, and the `neo4j.com/labs/agent-memory` docs use
**short-term / long-term / reasoning**. Reasoning memory is pitched as the piece
everyone else skips: a record of the agent's own steps and tool calls, the "how
did we get there" layer that complements the "what we know" layer. Neo4j's own
glossary says the quiet part out loud:

> `neo4j-agent-memory` uses short-term / long-term, with reasoning memory as a
> third axis that doesn't fit either label cleanly.

The glossary also maps external terms inward: it says "episodic memory" in other
frameworks is closest to **short-term** memory here, which inverts the LangGraph
mapping where episodic memory is a species of long-term memory. Do not mix the
two decks.

For the workshop, Lab 6 is built on Taxonomy B, because it uses the
`neo4j-agent-memory` library directly. `client.short_term`, `client.long_term`,
`client.reasoning`.

---

## 2. Best sources

### Neo4j primary

| # | Source | Author / date | What it contributes |
|---|--------|---------------|---------------------|
| 1 | https://neo4j.com/blog/developer/modeling-agent-memory/ | Alex Gilmore, Senior AI Solutions Architect, Neo4j. March 20, 2025 | The canonical Neo4j take on the semantic / episodic / procedural / temporal taxonomy, with a concrete graph data model per type. Data models on GitHub at `a-s-g93/agentic-memory-article`. |
| 2 | https://neo4j.com/labs/agent-memory/explanation/memory-types/ | Neo4j Labs docs, 2026 | The three-layer model: short-term, long-term, reasoning. Identical across both backends. |
| 3 | https://neo4j.com/labs/agent-memory/glossary/ | Neo4j Labs docs, 2026 | The reconciliation table. Maps Neo4j's vocabulary to Zep, Cognee, Letta, and generic framework terms. The backbone of any "consolidated vocabulary" slide. |
| 4 | https://neo4j.com/labs/agent-memory/explanation/poleo-model/ | Neo4j Labs docs, 2026 | POLE+O as the default entity ontology: Person, Object, Location, Event, Organization. Borrowed from law enforcement and intelligence analysis. |
| 5 | https://neo4j.com/blog/developer/meet-lennys-memory-building-context-graphs-for-ai-agents/ | Neo4j Developer Blog, 2026 | Launch post for `neo4j-agent-memory`. Carries the unified schema and the provenance query that walks message to trace to step to tool call. |
| 6 | https://medium.com/neo4j/a-tour-of-the-neo4j-agent-memory-service-nams-0f2d535a4fdb | William Lyon, June 23, 2026 | The best single slide-source. Console walkthrough of NAMS: the three memory types in one graph picture, the observation/reflection compression pyramid, the entity-resolution cascade, per-workspace ontologies. Contains the line "vector stores give you recall; the graph gives you understanding." |
| 7 | https://github.com/neo4j-labs/agent-memory | Neo4j Labs, 2026 | The library Lab 6 actually uses. Three-column README table: per-session history / POLE+O knowledge graph / learn from past decisions. |
| 8 | https://neo4j.com/blog/agentic-ai/hands-on-with-context-graphs-and-neo4j/ | William Lyon, January 14, 2026 | The **State Clock vs Event Clock** framing, plus a full financial-services decision-trace model with `CAUSED` / `INFLUENCED` / `PRECEDENT_FOR`. Dual semantic + FastRP embeddings. |
| 9 | https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/ | Daniel Chalef, founder/CEO of Zep AI, March 24, 2025 | Neo4j hosting a competitor's explanation. Bi-temporal model, `t_valid` / `t_invalid`, "update or invalidate, but not discard," 300ms P95 hybrid retrieval, and the contrast with Microsoft GraphRAG's query-focused summarization. |
| 10 | https://www.youtube.com/watch?v=rnERHmj81VI | Going Meta S03E05, Neo4j Agent Memory | Live demo of the three memory types against an Aura instance. Good for lifting a demo script. |
| 11 | https://neo4j.com/videos/what-are-the-3-different-types-of-memory-on-an-agent/ | Neo4j video, 2026 | Two-minute version of the three-layer pitch. Shareable link for participants. |
| 12 | https://medium.com/neo4j/from-agent-memory-to-portable-skills-fb3daebaa261 | Neo4j Developer Blog, August 2026 | Where the story goes next: skill distillation from memory, provenance grounding, attestation. Good closing slide, weak teaching material. |

### Ecosystem

| # | Source | Author / date | What it contributes |
|---|--------|---------------|---------------------|
| 13 | https://docs.langchain.com/oss/python/concepts/memory | LangChain docs, current | The reference taxonomy everyone borrows. Thread-scoped short-term via **checkpointer**, cross-thread long-term via **store** with namespaces. The semantic/episodic/procedural table with human-vs-agent examples. **Profile vs collection**. **Hot path vs background**. Has the diagrams. |
| 14 | https://arxiv.org/html/2504.19413v1 | Mem0 paper, April 2025 | Two-phase pipeline: extraction then update. The **ADD / UPDATE / DELETE / NOOP** tool-call decision. `Mem0^g` adds a graph variant with conflict detection. |
| 15 | https://docs.mem0.ai/migration/oss-v2-to-v3 | Mem0 docs, current | Mem0 **removed** ADD/UPDATE/DELETE in v3 and went ADD-only, pushing contradiction handling into retrieval ranking. Graph memory is now a paid-platform feature only. A genuinely useful counterpoint slide. |
| 16 | https://www.letta.com/blog/agent-memory/ | Letta, current | The **operating system** analogy from MemGPT: core memory as RAM, recall memory as disk cache, archival memory as cold storage. The agent self-edits its own memory blocks via tool calls. |

Two sources I could not retrieve. Jason Koo's "Neo4j's Memory MCP Server for
Persistent AI Chat Memory" (Medium, August 6, 2025) exists but the slug resolves
to a 404 through Firecrawl; his LinkedIn post "Getting Started with Neo4j's
Memory MCP Server" points at a sub-7-minute video and is a workable substitute.
Tomaz Bratanic and Michael Hunger have not written a dedicated agent-memory post;
their memory-adjacent work is GraphRAG and knowledge-graph construction.

---

## 3. Consolidated vocabulary

### The layers

**Short-term memory.** The current conversation. Messages, turns, session
history. In LangGraph it is agent **state** persisted by a **checkpointer**,
scoped to a **thread**. In Neo4j Labs it is `(:User)-[:HAS_CONVERSATION]->
(:Conversation)-[:HAS_MESSAGE]->(:Message)`. Gilmore notes it is ephemeral and
often needs no external database at all, until token count becomes the problem.

**Long-term memory.** What survives the session. In LangGraph, JSON documents in
a **store** under a **namespace** and a **key**, searchable by embedding and by
content filter. In Neo4j Labs, a typed knowledge graph of entities, facts, and
preferences. The declarative "what we know" layer.

**Reasoning memory.** Neo4j-specific. Traces, steps, and tool calls captured per
agent task. The "how did we get there" layer. Enables trace similarity search so
a new question can retrieve the hindsight from an old one, and tool-call
statistics so you can see which tool keeps failing.

### The species of long-term memory (Taxonomy A)

**Semantic memory.** Facts about the world. Human analogy: things I learned in
school. Agent example: facts about a user. Gilmore recommends **hot-path**
writing, because stale facts get said out loud to the user.

**Episodic memory.** Remembered experiences. Human analogy: things I did. Agent
example: past question-and-Cypher pairs used as few-shot examples. Gilmore
recommends **background** writing gated on user feedback, so bad examples never
enter the pool.

**Procedural memory.** How to do something. Human analogy: riding a bike.
Agent example: the system prompt, tool descriptions, instructions. Updated by
reflection or meta-prompting: feed the agent its current prompt plus feedback and
let it rewrite itself. LangChain's definition is broader, model weights plus code
plus prompt, and notes that in practice only the prompt gets edited.

Gilmore's cleanest one-liner distinguishing the middle two: in Cypher
generation, **episodic memory recalls the explicit question-and-Cypher pairs;
procedural memory recalls how the Cypher gets generated.**

**Temporal memory.** How data changes over time. Cross-cutting. It applies to any
of the other three.

**Working memory.** Not a Neo4j term. It appears in the ecosystem as the
in-context scratchpad. Letta's **core memory** is the concrete version: a block
that always sits in the context window.

### The write path vocabulary

**Hot path.** Memory is written during the request, before the agent answers.
Immediately available, transparent to the user, costs latency, and forces the
agent to multitask between answering and remembering. ChatGPT's `save_memories`
tool is the reference implementation.

**Background.** Memory is written by an asynchronous worker. No latency in the
main path, cleaner separation, allows deduplication, at the cost of other threads
running on stale context. NAMS is fully background: the write returns
immediately and extraction, embedding, deduplication, and compression happen on
`extraction:jobs`, `observation:jobs`, and `reflection:jobs` queues. The
dashboard exposes **queue lag** as the health metric.

**Profile vs collection.** LangChain's framing for the shape of semantic memory.
A **profile** is a single continuously-updated document, easy to inject whole,
error-prone to update as it grows. A **collection** is many small documents,
higher recall, but shifts the difficulty to deletion, deduplication, and search.
The graph answer is that a knowledge graph is a collection with the relationships
kept, which restores the context a flat collection loses.

### Contradiction, decay, consolidation

**Bi-temporal model (Graphiti/Zep).** Two independent clocks. **Valid time** is
when the fact was true in the world. **Transaction time** is when the system
learned it. Four timestamps per edge: `valid_at`, `invalid_at`, `created_at`,
`expired_at`. When a new fact contradicts an old one, the old edge is
**invalidated, not deleted**. Chalef's phrasing: "update or invalidate, but not
discard." This makes point-in-time reconstruction possible, which is what an
audit needs.

**State Clock vs Event Clock (Lyon).** The same idea in slide-ready language.
The State Clock answers *what is true now*. The Event Clock answers *what
happened, when, and why*. A row in a table has only a State Clock. A graph can
carry both.

**Supersession (`neo4j-agent-memory`, and Lab 6).** A `SUPERSEDED_BY` edge from
old preference to new, plus a `valid_until` timestamp on the old one. Reads take
`active_only=True` or `as_of=<datetime>`. Nothing is deleted.

**ADD / UPDATE / DELETE / NOOP (Mem0 v2).** An LLM tool call decides the fate of
each extracted fact against the top-k similar existing memories. DELETE removes
memories that the new fact contradicts. Mem0 v3 **abandoned** this: extraction is
now a single ADD-only pass and contradiction is handled at retrieval time by
ranking. Worth showing as the honest counter-argument, since it says the diffing
step was not worth its LLM call.

**Consolidation / compression (NAMS).** A background worker rolls raw messages
into **observations**, 2 to 4 sentence summaries of a window of messages, each
traceable back to the exact messages it came from. Observations synthesize into a
single active **reflection**, the current best summary of the whole conversation.
One `GET /context` call returns all three tiers: reflection, recent observations,
recent raw messages. That is a ready-made layered prompt block.

**Entity resolution cascade (NAMS).** Type-strict, three stages. **Exact** match
on normalized names and aliases, then **fuzzy** (Levenshtein, Jaro-Winkler,
token-sort), then **semantic** on embeddings. High confidence auto-merges. Clear
non-matches become new nodes. The ambiguous middle band is written as a `SAME_AS`
edge marked `pending` and surfaced in a human-in-the-loop review queue.

### Why a graph, in their words

- **"Vector stores give you recall; the graph gives you understanding."** (Lyon,
  NAMS tour.) The strongest one-line version.
- **"Your 'memory' is just a pile of text chunks ranked by cosine similarity."**
  (Lyon, NAMS tour, describing the status quo.)
- **"Most agents you build today are amnesiacs."** (Lyon, NAMS tour, opening
  line.)
- The traversal argument: because short-term, long-term, and reasoning memory are
  one connected graph, you can walk from a tool call, to the entity it touched,
  to the message that first mentioned it. Three separate stores cannot do that.
- The contradiction argument: a vector store has no representation for "this used
  to be true." It has to delete, or return both and hope the LLM picks right.
- The token-cost argument: an LLM without memory fakes it by re-reading the whole
  conversation, so cost grows linearly with conversation length while quality
  degrades from distraction.
- **Context graph** is the current Neo4j umbrella term. A persistent, structured
  record of everything an agent knows and has done, sitting alongside the data it
  reasons over. Neo4j's thesis is that this is the next layer of AI
  infrastructure.

---

## 4. Graph data models

### Model 1: The unified three-layer graph (Neo4j Labs / NAMS)

The canonical picture. Green message nodes, orange entity nodes, purple reasoning
nodes, all in one graph.

```
(Conversation)-[:HAS_MESSAGE]->(Message)
(Message)-[:NEXT_MESSAGE]->(Message)
(Message)-[:MENTIONS]->(Entity)
(Entity)-[:WORKS_AT]->(Entity)
(Entity)-[:LOCATED_IN]->(Entity)
(ReasoningTrace)-[:INITIATED_BY]->(Message)
(ToolCall)-[:TRIGGERED_BY]->(Message)
```

Entities carry POLE+O typing and multiple labels:

```cypher
(:Entity:Person:Individual {
    id: "uuid", name: "John Smith", type: "PERSON", subtype: "INDIVIDUAL",
    canonical_name: "John Smith", description: "CEO of Acme Corp",
    confidence: 0.92, embedding: [0.1, 0.2, ...],
    created_at: datetime()
})
(:Message)-[:MENTIONS {confidence: 0.85, start_pos: 10, end_pos: 20}]->(:Entity)
```

The provenance query, the one that justifies reasoning memory:

```cypher
MATCH (m:Message {content: "What did Brian say about hiring?"})
      -[:TRIGGERED]->(t:ReasoningTrace)
      -[:HAS_STEP]->(s:ReasoningStep)
      -[:USED_TOOL]->(tc:ToolCall)
RETURN s.thought, tc.tool_name, tc.arguments, tc.result
```

Hybrid retrieval in one query: vector index, then a graph hop, then a property
filter.

```cypher
CALL db.index.vector.queryNodes('message_embedding', 10, $embedding)
YIELD node as m, score
MATCH (m)-[:MENTIONS]->(e:Entity {type: "PERSON"})
WHERE m.created_at > datetime() - duration('P7D')
RETURN m.content, e.name, score
```

### Model 2: Temporal semantic memory (Gilmore)

Two techniques, both worth showing.

1. Timestamps on the relationship. `(:User)-[:HAS_FRIEND {from, to}]->(:User)`
   records when a relationship started and ended.
2. Pull the mutable property out into its own node and version it. The `User`
   node keeps a single `HAS_CURRENT_DESCRIPTION` pointer to the newest version,
   and older versions chain backward with `PREVIOUS`.

```
(:User)-[:HAS_CURRENT_DESCRIPTION]->(:UserDescription {text, created})
(:UserDescription)-[:PREVIOUS]->(:UserDescription)
(:User)-[:HAS_FRIEND {since, until}]->(:User)
(:User)-[:ATTENDED]->(:Event)
```

The single-pointer trick is the practical part: retrieval stays a one-hop lookup
while history stays available for audit.

### Model 3: Temporal procedural memory (Gilmore)

The same versioning pattern applied to prompts.

```
(:Prompt {name: "text2cypher"})-[:HAS_CURRENT_SYSTEM_PROMPT]->(:SystemPromptDetails)
(:SystemPromptDetails)-[:PREVIOUS]->(:SystemPromptDetails)
(:Prompt)-[:HAS_CURRENT_USER_PROMPT]->(:UserPromptDetails)
(:UserPromptDetails)-[:PREVIOUS]->(:UserPromptDetails)
```

Retrieval strategy: fetch the current prompts at the start of every chat session,
so any improvement made since the last session takes effect. Reverting a bad
prompt is moving one relationship.

### Model 4: Episodic memory as few-shot store (Gilmore)

```
(:Question {text, embedding})-[:ANSWERED_BY]->(:CypherQuery {statement})
```

One `CypherQuery` can have many `Question` nodes attached, because different
wordings mean the same thing. Retrieval is a vector search over question
embeddings, then a one-hop traversal to the Cypher. Writes happen in the
background, gated on a positive user rating, so only examples that worked become
examples.

### Model 5: The decision trace / context graph (Lyon, financial services)

The most "enterprise" of the models, and the best argument for reasoning memory
in a regulated domain.

```
(:Decision)-[:CAUSED]->(:Decision)
(:Decision)-[:INFLUENCED]->(:Decision)
(:Decision)-[:PRECEDENT_FOR]->(:Decision)
(:Decision)-[:ABOUT]->(:Person|:Account|:Transaction)
(:Decision)-[:APPLIED_POLICY]->(:Policy)
(:Decision)-[:GRANTED_EXCEPTION]->(:Exception)
(:Decision)-[:TRIGGERED]->(:Escalation)
```

"Why was this account frozen?" is two lines:

```cypher
MATCH path = (freeze:Decision {id: $freeze_id})<-[:CAUSED*1..5]-(upstream)
RETURN path
```

Nodes carry two embeddings: `reasoning_embedding` from `text-embedding-3-small`
for semantic similarity, and `fastrp_embedding` from GDS FastRP for structural
similarity. Find decisions that *read* alike, and decisions that *sit in the same
shape of context*.

### Model 6: Lab 6's own model, for reference

What the workshop already builds. Worth putting on a slide next to Model 1 so
participants see that the lab is a real instance of the canonical picture.

```
(:User {identifier})-[:HAS_CONVERSATION]->(:Conversation {session_id})
(:Conversation)-[:HAS_MESSAGE]->(:Message {content, role})
(:Message)-[:MENTIONS]->(:Aircraft:Entity {tail_number, id, type, name})
(:Preference {category, preference, context, valid_until})-[:APPLIES_TO]->(:Aircraft)
(:Preference)-[:SUPERSEDED_BY]->(:Preference)
(:ReasoningTrace {task, outcome, success})-[:HAS_STEP]->(:ReasoningStep {thought, action, observation})
(:ReasoningStep)-[:USES_TOOL]->(:ToolCall {tool_name, status})
(:ReasoningStep)-[:TOUCHED]->(:Aircraft)
(:Tool {name, total_calls, successful_calls, failed_calls})
```

The join is the point. `Aircraft` nodes are **adopted**: the library adds
`:Entity` plus `id`/`type`/`name` onto the 36 aircraft nodes Lab 2 already
loaded, so a remembered aircraft *is* the fleet aircraft. Then one query spans
both halves:

```cypher
// 1. Conversation memory: which aircraft are technicians actually asking about
MATCH (u:User)-[:HAS_CONVERSATION]->(c:Conversation)-[:HAS_MESSAGE]->(m:Message)
      -[:MENTIONS]->(ac:Aircraft)
WITH ac, count(DISTINCT u) AS technicians,
     collect(DISTINCT u.identifier) AS who, count(DISTINCT m) AS mentions
WHERE technicians >= $min_technicians

// 2. Same node, fleet graph: what maintenance actually found
MATCH (ac)<-[:AFFECTS_AIRCRAFT]-(ev:MaintenanceEvent)-[:AFFECTS_SYSTEM]->(sys:System)
RETURN ac.tail_number AS aircraft, technicians, who AS asked_by, mentions,
       count(ev) AS events,
       count(CASE WHEN ev.severity = 'CRITICAL' THEN 1 END) AS critical,
       collect(DISTINCT sys.type)[0..4] AS systems
ORDER BY technicians DESC, critical DESC
```

The lab ships two controls that make the payoff measurable: a fleet-only query
that ranks N10011 last of six, and a memory-only query that ranks it joint first.
Neither half alone finds it. That is the demo.

---

## 5. How each adjacent project frames memory

**LangGraph.** Mechanism first, psychology second. Short-term memory *is* graph
state, persisted by a **checkpointer**, scoped to a **thread**. Long-term memory
is a **store**: JSON documents under a `namespace` tuple and a `key`, with vector
search and content filtering. The psychology layer (semantic/episodic/procedural)
is presented as a way to think, not as an API. The two axes that are genuinely
theirs are **profile vs collection** and **hot path vs background**. Both have
diagrams you can reuse.

**Zep / Graphiti.** Temporal-first. The pitch is that a knowledge graph without
time is a lie, because facts expire. Bi-temporal edges, invalidation instead of
deletion, hybrid retrieval combining semantic, BM25, and graph traversal, with a
300ms P95 target because memory sits in the request path. Explicitly contrasts
itself with Microsoft GraphRAG, which they characterize as batch,
query-focused summarization rather than incremental memory.

**Mem0.** Pipeline-first, and the most changeable. v2 was extraction plus an
LLM-decided ADD/UPDATE/DELETE/NOOP update phase against the top-10 similar
memories, with an optional Neo4j-backed graph variant. v3 dropped the update
phase to a single ADD-only pass and moved graph memory behind the paid platform.
The reason given is honest and worth quoting: the model should spend its capacity
understanding the input rather than diffing against existing state.

**Letta / MemGPT.** The **operating system** analogy, and the only project where
the *agent itself* is the memory manager. **Core memory** is a block always in
context, like RAM, holding persona and user facts, editable by the agent.
**Recall memory** is conversation history outside the window, like a disk cache,
searchable on demand. **Archival memory** is cold storage, written and queried by
tool call. The framing everyone borrows: treat the context window as a scarce
resource and page things in and out.

**Cognee.** Uses "memify" as its verb. Mentioned in Neo4j's glossary alignment
table.

**NAMS.** Managed service on top of the same model. Notable operational ideas a
data-engineering audience will recognize: queue lag as the freshness SLI,
human-in-the-loop review queues for both entity resolution and schema drift,
per-workspace ontologies with `strict` / `permissive` / `review` validation
modes, and immutable ontology revisions with an append-only audit trail.

---

## 6. Slide-worthy framings

**The amnesiac opener.** "Most agents you build today are amnesiacs. They run a
chain of reasoning, return an answer, and forget the whole thing the moment the
request ends."

**The pile of chunks.** "Your 'memory' is just a pile of text chunks ranked by
cosine similarity."

**Recall vs understanding.** "Vector stores give you recall; the graph gives you
understanding."

**The memory pyramid (NAMS).** Raw messages at the base, compressing upward into
observations, then into a single active reflection at the apex. A background
worker drives it; one context call returns all three tiers.

**The OS hierarchy (Letta).** Core memory = RAM, recall memory = disk cache,
archival memory = cold storage.

**Two clocks (Lyon).** State Clock answers *what is true now*. Event Clock
answers *what happened, when, and why*. A table has one clock; a graph has both.

**Write path vs read path (LangChain).** Hot path vs background on the write
side, retrieval on the read side. LangChain has the diagram.

**recall to act to remember.** The loop shape. In Lab 6 it is literally the graph
topology: `START -> recall -> supervisor -> {tools} -> synthesize -> remember -> END`.

**The three-color graph (NAMS Memory Browser).** Green conversation and message
nodes, orange POLE+O entities with typed relationships, purple agent steps and
tool calls, all in one force-directed picture. The single best image for
explaining that these are not three databases.

---

## 7. Suggested presentation flow, 15 to 20 minutes

Audience: data engineers and AI engineers who have already built GraphRAG
retrievers in Lab 3 and a LangGraph supervisor agent in Lab 5. Nine slides.

---

**Slide 1. The agent you just built is an amnesiac. (60 sec)**

Show the Lab 5 topology on screen: `START -> supervisor -> {genie, cypher,
graphrag} -> synthesize -> END`. Ask, "What does this agent know at the start of
question two?" Answer: exactly what it knew at the start of question one.

*Analogy:* a brilliant contractor who does great work and then has their memory
wiped every time they leave the hangar. You re-explain the aircraft every visit.

---

**Slide 2. The fake fix, and why it runs out. (90 sec)**

The usual patch is to stuff the transcript back into the context window. Three
failure modes, in order of when you hit them:

- **Cost.** Token spend grows linearly with conversation length.
- **Distraction.** Models degrade over long contexts even when the context fits.
- **Contradiction.** The transcript contains "the fault is on engine two" from
  Monday and "actually engine one" from Tuesday. Nothing in a flat transcript
  says which one is current.

*Beat:* Lyon's line. "You realize your 'memory' is just a pile of text chunks
ranked by cosine similarity."

---

**Slide 3. Three layers, one graph. (2 min, the anchor slide)**

The NAMS three-color picture: green conversation and messages, orange POLE+O
entities, purple reasoning steps and tool calls.

- **Short-term.** The conversation. What was said, by whom, in what order.
- **Long-term.** What we know. Entities, facts, preferences.
- **Reasoning.** How we got there. Traces, steps, tool calls.

Say the honest thing about vocabulary: other frameworks slice this as
semantic/episodic/procedural, from the LangGraph and CoALA lineage. Neo4j's own
glossary maps between them. Point at Alex Gilmore's post for that mapping and
move on. Do not spend three minutes on nomenclature.

*Analogy:* short-term is the shift log, long-term is the aircraft's permanent
record, reasoning is the mechanic's own notebook of what they tried and what
worked.

---

**Slide 4. Why a graph, in one query. (2 min)**

Put the traversal on screen: message, to the entity it mentions, to the tool call
that touched it, to the maintenance event on the same node.

The claim to land: **these are not three databases.** Because they are one graph,
you can walk from a tool call to the entity it touched to the message that first
mentioned it. Three separate stores, one for chat, one for facts, one for logs,
cannot do that join. Neither can a vector index, which returns similar text and
nothing about what connects it.

*Beat:* "Vector stores give you recall; the graph gives you understanding."

---

**Slide 5. Memory has to handle being wrong. (2 min)**

Three approaches, side by side, so the audience knows this is a design choice and
not a solved problem.

- **Delete and replace (Mem0 v2).** LLM picks ADD / UPDATE / DELETE / NOOP
  against the top-k similar memories. Simple, and destroys the audit trail. Mem0
  itself walked this back in v3 and went ADD-only.
- **Invalidate, never discard (Zep/Graphiti).** Bi-temporal edges, `valid_at`,
  `invalid_at`, `created_at`, `expired_at`. "Update or invalidate, but not
  discard."
- **Supersede (what Lab 6 does).** `(:Preference)-[:SUPERSEDED_BY]->(:Preference)`
  plus a `valid_until`. Reads take `active_only=True` or `as_of=<timestamp>`.

*Framing:* the **State Clock** answers what is true now. The **Event Clock**
answers what happened, when, and why. A row in a Delta table has one clock. This
graph has both.

*Demo beat, 45 seconds, from `02_instructor_demos.ipynb` Demo 1:* Monday's
preference says the fault is on engine two. Tuesday's correction says engine one,
borescope confirmed. Run `get_preferences_for(active_only=True)`, get engine one.
Run the same call with `as_of=BEFORE_CORRECTION`, get engine two. Nothing was
deleted. An auditor can reconstruct what the agent believed on any date.

---

**Slide 6. Where writes happen: hot path or background. (90 sec)**

The one operational decision this audience will actually have to make.

- **Hot path.** Write before you answer. Immediately available, transparent to
  the user, adds latency, and makes the agent multitask between answering and
  remembering.
- **Background.** Return immediately, extract and embed and deduplicate on a
  queue. No user-facing latency, cleaner separation, at the cost of staleness.

Gilmore's rule of thumb: semantic memory in the hot path, because saying a stale
fact out loud is the worst outcome. Episodic and procedural in the background,
gated on feedback, so bad examples never enter the pool.

*Data-engineering hook:* NAMS runs it fully in the background and exposes **queue
lag** on the dashboard. That is a freshness SLI. This room has built one before.

*Lab 6 note:* the lab writes in the hot path, one `remember` node, so
participants can see the effect inside a single notebook run.

---

**Slide 7. The loop: recall, act, remember. (2 min)**

The Lab 5 graph next to the Lab 6 graph.

```
Lab 5:  START -> supervisor -> {genie, cypher, graphrag} -> synthesize -> END
Lab 6:  START -> recall -> supervisor -> {genie, cypher, graphrag} -> synthesize -> remember -> END
```

Two nodes. The three tools are untouched. That is the whole architectural change.

- **`recall`** does one vector search over past `Message` nodes, across *all*
  sessions, not just the current one. Top 3, threshold 0.7. It prepends the
  result to the supervisor prompt with an explicit caveat: this tells you what
  people care about and what "that one" means. It does not tell you a
  measurement.
- **`remember`** writes the question and the answer back as `Message` nodes and
  links their `MENTIONS` edges to real `Aircraft` nodes.

*Beat, worth saying out loud:* recall runs **once per question**, not once per
tool call. Memory is context for routing, not a fourth tool.

---

**Slide 8. The payoff: memory joins the fleet graph. (3 min, the demo)**

The slide that makes the case, because it needs both halves and cannot be faked.

Adoption first, in one line: the memory library stamps `:Entity` onto the
`Aircraft` nodes Lab 2 already loaded. A remembered aircraft **is** the fleet
aircraft, the same node, not a foreign key.

Then run the three queries in order:

1. **Fleet only.** Rank aircraft by critical maintenance events. N10011 comes
   last of six. Nothing to see.
2. **Memory only.** Rank aircraft by how many distinct technicians asked about
   them. N10011 is joint first. Interesting, unexplained.
3. **Both, one query, one `ac` binding.** Four technicians keep asking about an
   aircraft whose maintenance record says it is fine. That divergence is the
   finding, and it exists in neither half alone.

*Analogy:* the maintenance log is what got written down. The conversation is what
the crew keeps worrying about. The gap between them is where the next incident
lives.

*Optional 30-second extra, Demo 2 from the instructor notebook:* a preference
scoped to an aircraft with `APPLIES_TO`, so the "EGT sensor reads five degrees
high on N10011" warning reaches **any** technician who touches that aircraft, not
only the one who discovered it. A user-keyed preferences table cannot express
that. The traversal starts at the aircraft.

---

**Slide 9. What you are actually building, and where it goes. (90 sec)**

Neo4j's name for this is a **context graph**: a persistent, structured record of
everything an agent knows and has done, sitting alongside the data it reasons
over.

Where this sits in the workshop's architecture, and worth saying explicitly to a
Databricks room:

- **Databricks** holds the telemetry. High volume, time-series, columnar.
  Millions of sensor readings.
- **Neo4j** holds the topology, the maintenance history, **and now the memory**.
  Relationship-rich, low volume, traversal-heavy.
- The agent's memory belongs on the side where the joins are, because the value
  of a memory is what it connects to.

Three things to take away:

- Memory is three layers, and **reasoning memory is the one most systems skip**.
- Memory must model **being wrong**, so supersede, do not delete.
- Memory that lives in the same graph as your domain data can be **joined** to
  it. That is the difference between remembering and understanding.

If they want the managed version, point at `neo4j.com/labs/agent-memory` and
`memory.neo4jlabs.com`. If they want to build it themselves, the four Cypher
patterns are in Lab 6.

---

### Timing

| Slide | Minutes | Cumulative |
|-------|---------|------------|
| 1. Amnesiac | 1.0 | 1.0 |
| 2. Fake fix | 1.5 | 2.5 |
| 3. Three layers | 2.0 | 4.5 |
| 4. Why a graph | 2.0 | 6.5 |
| 5. Being wrong + demo | 2.0 | 8.5 |
| 6. Hot path vs background | 1.5 | 10.0 |
| 7. recall/act/remember | 2.0 | 12.0 |
| 8. The payoff demo | 3.0 | 15.0 |
| 9. Wrap | 1.5 | 16.5 |

16.5 minutes of content, leaving 3 minutes of slack for questions inside a 20
minute slot. If you need to cut to 15, drop Slide 6 and fold hot-path vs
background into a single line on Slide 7. Never cut Slide 8.

---

## 8. Loose ends

- Jason Koo's Medium post on the memory MCP server is 404 through Firecrawl. His
  LinkedIn post "Getting Started with Neo4j's Memory MCP Server" and the
  associated sub-7-minute video are the usable substitute.
- The `mcp-neo4j-memory` server under `neo4j-contrib` is the older, simpler
  memory MCP, distinct from NAMS and from `neo4j-agent-memory`. Do not conflate
  the three when citing.
- Going Meta S03E05 is the best video source for lifting a live demo script if
  the Lab 6 demo needs a backup.
