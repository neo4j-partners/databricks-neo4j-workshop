# Slides Organization

## Key Topics Summary

* **Databricks + Neo4j Dual-Database Architecture**: Why the two platforms complement each other. Databricks handles large-scale tabular analytics and ML; Neo4j handles relationship traversal and pattern matching. Together they cover questions that neither can answer alone. Covered in: `platform-overview/02-databricks-neo4j-integration-slides.md`, `platform-overview/03-intro-databricks-neo4j-slides.md`, `platform-overview/01-workshop-overview-slides.md`

* **Neo4j Graph Fundamentals**: Nodes, relationships, and properties as the building blocks of a property graph. Cypher as the query language for pattern matching. Why multi-hop traversals are faster in a graph than in SQL with recursive joins. Covered in: `platform-overview/02-databricks-neo4j-integration-slides.md`, `platform-overview/04-neo4j-aura-overview-slides.md`

* **Neo4j Aura**: The fully managed cloud version of Neo4j, available on AWS, GCP, and Azure. Includes tools for querying, visual exploration, and dashboards. The product also ships Aura Agents for no-code conversational interfaces, which is a product fact and not workshop content: no deck covers it. Covered in: `platform-overview/04-neo4j-aura-overview-slides.md` for the query, Explore, and Dashboards tools

* **Medallion Architecture**: Databricks data organization pattern with three layers. Bronze holds raw data. Silver holds cleaned, governed tables. Gold holds analytics-ready outputs enriched by graph insights. Covered in: `platform-overview/03-intro-databricks-neo4j-slides.md`

* **Neo4j Spark Connector**: The official bidirectional bridge between Databricks Delta tables and Neo4j. Rows become nodes; foreign keys become relationships. Also reads graph data back into DataFrames for analytics and ML. Covered in: `platform-overview/02-databricks-neo4j-integration-slides.md`, `platform-overview/03-intro-databricks-neo4j-slides.md`

* **LLM Limitations**: Three core problems with using LLMs alone for enterprise data. Hallucination produces confident but wrong answers. Knowledge cutoff means the model cannot access private or recent data. Relationship blindness means the model cannot reason across connected information. Covered in: `genai-foundations/02-genai-and-limitations-slides.md`, `agents/02-power-of-graphrag-slides.md`

* **Traditional RAG**: Retrieval-Augmented Generation as the baseline approach to grounding LLM responses. Documents are split into chunks, embedded as vectors, and retrieved by semantic similarity. Covered in: `genai-foundations/03-traditional-rag-slides.md`

* **Context ROT**: The finding that too much irrelevant context degrades LLM accuracy. Similarity search retrieves related but not necessarily relevant chunks, filling the context window with noise. Covered in: `genai-foundations/04-context-and-rag-slides.md`

* **GraphRAG**: Graph-enhanced retrieval that combines vector similarity search with graph traversal. Vector search finds the most relevant chunks; graph traversal follows extracted entities and relationships from those chunks to gather richer, structured context. Covered across: `platform-overview/02-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md`, `genai-foundations/04-context-and-rag-slides.md`, `graph-ml/03-graph-enrichment-slides.md`

* **Knowledge Graph Construction**: The pipeline for turning unstructured documents into a structured graph. Steps are: chunk documents, embed chunks, extract entities with an LLM, resolve duplicate entities, and cross-link to the operational graph. Covered in: `background/kg-construction/05-building-knowledge-graphs-slides.md`, `agents/02-power-of-graphrag-slides.md`

* **SimpleKGPipeline**: The `neo4j-graphrag-python` library class that orchestrates the full knowledge graph construction pipeline. Accepts schema, LLM, embedder, and text splitter configuration. Covered in: `background/kg-construction/05-building-knowledge-graphs-slides.md`, `background/kg-construction/06-schema-design-slides.md`

* **Schema Design**: Defining which node types, relationship types, and valid patterns to extract from documents. Three modes: user-provided for production, extracted for exploration, free for initial discovery. Covered in: `background/kg-construction/06-schema-design-slides.md`

* **Chunking Strategies**: How document splitting affects both entity extraction quality and retrieval precision. Larger chunks give the LLM more context for extraction; smaller chunks give retrieval more precision. Chunk overlap preserves context at boundaries. Covered in: `kg-construction/07-chunking-slides.md`

* **Entity Resolution**: Merging duplicate nodes that represent the same real-world entity extracted under different names. Strategies include upstream normalization via prompt engineering, canonical reference lists, and post-processing fuzzy or semantic resolvers. Covered in: `background/kg-construction/08-entity-resolution-slides.md`

* **Vectors and Embeddings**: Numerical representations of text meaning as high-dimensional vectors. Similar meanings produce similar vectors, enabling semantic search. Neo4j stores embeddings as node properties and indexes them for fast similarity queries. Covered in: `kg-construction/09-vectors-slides.md`

* **Vector Retriever**: The simplest GraphRAG retriever. Converts a question to an embedding and returns the most semantically similar chunks from the vector index. Best for exploratory, conceptual questions. Covered in: `retrieval-patterns/02-vector-retriever-slides.md`

* **Vector Cypher Retriever**: Combines vector similarity search with a custom Cypher traversal. Vector search finds relevant chunks; the Cypher query traverses from those chunks to related entities and relationships in the graph. Best for questions that need both content and structured data. Covered in: `retrieval-patterns/03-vector-cypher-retriever-slides.md`

* **Text2Cypher Retriever**: An LLM converts a natural language question directly into a Cypher query, which executes against the graph and returns precise structured results. Best for counts, lists, and entity-specific facts. Covered in: `retrieval-patterns/04-text2cypher-retriever-slides.md`

* **ReAct Pattern and Agents**: The Reasoning and Acting loop that AI agents follow: receive a question, reason about which tool fits, execute the tool, observe the result, respond. Retrievers become tools agents can select automatically based on question type. Covered in: `agents/01-from-retrievers-to-agents-slides.md`

* **Genie Agent**: Databricks' natural language to SQL system. Translates plain English questions into governed SQL queries against Delta Lake tables registered in Unity Catalog. One of two specialized agents in the multi-agent architecture. Covered in: `platform-overview/02-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md`

* **Neo4j MCP Server**: Exposes Neo4j as agent tools via the Model Context Protocol. Tools include schema discovery, read-only Cypher execution, and GDS procedure listing. Allows any agent framework to query the graph without pre-built integrations. Covered in: `platform-overview/02-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md`

* **Multi-Agent Supervisor**: A coordinator agent that routes questions to specialized agents based on the nature of the question. Numbers and trends go to Genie; relationships and structure go to the Neo4j MCP agent; questions that need both get decomposed and sent to each. Covered in: `platform-overview/02-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md`, `agents/03-langgraph-supervisor-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md`

* **LangGraph Supervisor Agent**: The Lab 5 agent written in code rather than assembled from a form. One supervisor node loops over three tools: a Genie node for Lakehouse telemetry, a Cypher node against the participant's own Aura instance, and a GraphRAG node over the maintenance manuals. Routing is a loop rather than a one-shot decision, and the deck works through the prompt rules that stop the model routing on the wrong signal. Covered in: `agents/03-langgraph-supervisor-slides.md`

* **Deploying the Agent**: What changes when the notebook graph becomes a Model Serving endpoint. The endpoint runs as its own service principal rather than with the author's permissions, the graph is wrapped as an MLflow `ResponsesAgent`, the model is registered to Unity Catalog, and reachable Databricks objects are declared as resources while secrets stay credential references. Covered in: `agents/04-deploy-the-agent-slides.md`

* **Agent Memory**: Lab 6 gives the deployed agent memory in Neo4j, adding a `recall` node before the supervisor and a `remember` node after it, and redeploying the same endpoint. Memory is three layers on one graph, short term, long term and reasoning, and it is routing context for the supervisor rather than a fourth tool. Superseding rather than deleting keeps a wrong answer auditable. The payoff is adoption: stamping `:Entity` onto the Lab 2 `Aircraft` nodes makes a remembered aircraft the fleet node, so one traversal crosses both halves. Covered in: `agents/05-agent-memory-slides.md`

* **Graph Data Science (GDS)**: Neo4j's library of 65+ graph algorithms organized into centrality, community detection, similarity, pathfinding, and node embedding categories. Algorithms run on in-memory graph projections and results write back to the database as node properties. Covered in: `graph-ml/03-graph-enrichment-slides.md`

* **Graph Feature Engineering**: Using GDS algorithms to generate ML features from graph topology. FastRP produces node embedding vectors. PageRank scores influence. Louvain assigns community membership. These features combine with tabular data in a feature table for classifier training. Covered in: `graph-ml/03-graph-enrichment-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md`

* **MLflow Experiment Tracking**: Used to compare classifiers trained with tabular features alone against classifiers trained with graph features added. Quantifies the accuracy lift that graph topology contributes over flat table data. Covered in: `graph-ml/03-graph-enrichment-slides.md`

* **Agentic Graph Enrichment**: A cyclic pipeline where agents compare graph contents against unstructured documents to detect missing relationships, propose enrichments with confidence scores, validate against the existing schema, and write approved relationships back to the graph. Each cycle changes what algorithms compute and what the next cycle discovers. Covered in: `graph-ml/04-future-graph-enrichment-slides.md`

* **Incremental Sync with Change Data Feed**: Keeping Neo4j and Databricks aligned without full reloads. Delta Lake's Change Data Feed captures only changed rows; a Spark Structured Streaming job pushes deltas to Neo4j via the Spark Connector. Costs stay proportional to change volume. Covered in: `graph-ml/03-graph-enrichment-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md`

* **Neo4j as a Semantic Map**: Syncing Unity Catalog metadata into Neo4j so business concepts connect to physical tables and columns as a traversable graph. Improves data discovery and boosts text-to-SQL accuracy by giving agents structured domain context. Covered in: `platform-overview/02-databricks-neo4j-integration-slides.md`

* **Authorization Sync**: Patterns for aligning access privileges between Unity Catalog and Neo4j when both systems hold overlapping data. Four approaches: shared identity provider, shared IdP plus a semantic map, UC as source of truth pushing to Neo4j, and Neo4j as source of truth pushing to UC. Covered in: `background/governance/auth-sync-slides.md`

* **Aircraft Digital Twin**: The workshop's running use case. A multi-model aircraft fleet modeled in both Neo4j and Databricks, with topology and maintenance in Neo4j and time-series sensor telemetry in Databricks. Illustrates the dual-database pattern with real query examples. Covered in: `platform-overview/01-workshop-overview-slides.md`, `platform-overview/02-databricks-neo4j-integration-slides.md`

* **Financial Fraud Detection**: The secondary running use case in the deeper technical decks. Money laundering through circular account transfers illustrates why graph traversal outperforms recursive SQL for multi-hop connection queries. Covered in: `platform-overview/03-intro-databricks-neo4j-slides.md`, `background/governance/auth-sync-slides.md`

---

## Phased Plan: Reorganize Slides by Topic

### What

Reorganize the slide files from their current delivery-context folders into topic-based folders so it is clear what content exists, which version is canonical for each topic, and what is redundant or missing.

### Why

Right now the folder names reflect who gave the talk, not what is in the slides. The same topic (GraphRAG, the multi-agent supervisor, the Spark Connector) is explained in three or four separate files. There is no single place to look up a topic, and it is unclear which version to use when building a new deck.

### Scope

All `.md` slide files under `slides/`. Does not touch images, node_modules, or the docs reference documents.

### Deliberately Not Doing

- Not changing slide content yet. This plan only moves and labels files.
- Not building any new slides to fill gaps. Gaps get noted, not fixed.
- Not changing the Marp format or theme.

---

### Phase 1: Label Every File

**Status: Complete.** See the File Inventory section below.

**Goal:** Every slide file has a written label stating its topic cluster, audience level, and primary use case example.

- Read each slide file and write a one-line label for it: topic cluster, depth level (overview / practitioner / deep dive), and which use case it uses (aircraft, fraud, portfolio, generic).
- Record the labels in a simple table in this file under a new section called "File Inventory."
- Flag any file that does not fit cleanly into one topic cluster.

**Done when:** Every non-empty `.md` slide file under `slides/` (excluding `node_modules/`) has a row in the File Inventory table.

---

### Phase 2: Decide the Target Folder Structure

**Status: Complete.** See the Target Structure section below.

**Goal:** A confirmed list of topic folders with a one-line description of what belongs in each.

- Using the labels from Phase 1 and the seven topic clusters listed below, draft a proposed folder layout.
- For each topic cluster, name one file that should be the canonical reference for that topic. Where there are multiple files on the same topic, pick one.
- Write the proposed structure in this file under a new section called "Target Structure."

**Topic clusters to work from:**
1. Platform overview (why Databricks + Neo4j, dual-database architecture)
2. GenAI foundations (LLM limitations, traditional RAG, Context ROT)
3. Knowledge graph construction (chunking, schema, entity resolution, vectors)
4. Retrieval patterns (Vector, Vector Cypher, Text2Cypher retrievers)
5. Agents and multi-agent systems (Genie, MCP, supervisor, ReAct)
6. Graph ML and enrichment (GDS, feature engineering, enrichment loop)
7. Governance and integration (auth sync, JDBC federation, semantic map)

**Done when:** The Target Structure section lists every proposed folder with its canonical file and lists which existing files are redundant for that folder.

---

### Phase 3: Consolidate Redundant Files

**Status: Complete.** SUMMARY.md marked redundant. All five multi-cluster files reviewed; no content merging needed.

**Goal:** Each topic has exactly one canonical slide file. Redundant files are either merged into the canonical file or marked for deletion.

- For each topic with more than one file, compare the versions side by side. Identify any content in the non-canonical versions that is not in the canonical version.
- If unique content exists in a non-canonical file, move that content into the canonical file.
- If a non-canonical file has nothing unique, mark it for deletion.
- Do not delete files yet. Add a `# REDUNDANT - merge complete` comment at the top of files marked for removal.

**Done when:** Every topic cluster has a single canonical file. No unique content remains in files marked redundant.

**Findings:**

| File | Action | Reason |
|------|--------|--------|
| `overview-databricks-neo4j/SUMMARY.md` (deleted in Phase 4, no current path) | Marked redundant | Every section is covered by `platform-overview/02-databricks-neo4j-integration-slides.md`, which has additional appendix content. Nothing unique in SUMMARY.md. |
| `platform-overview/03-intro-databricks-neo4j-slides.md` | No action | Canonical for platform-overview (fraud lens). Cross-cluster governance content (JDBC) is not covered by auth-sync-slides; stays in file. |
| `agents/02-power-of-graphrag-slides.md` | No action | Canonical for agents. LLM limitations intro is two slides, fully covered by `genai-foundations/02-genai-and-limitations-slides.md`. No merge needed. |
| `graph-ml/04-future-graph-enrichment-slides.md` | No action | Canonical for graph ML. Agents content is application-specific to enrichment; not a duplicate of any agents canonical. |
| `platform-overview/02-databricks-neo4j-integration-slides.md` | No action | Canonical for platform-overview (aircraft lens). Cross-cluster content (semantic map, JDBC, MCP overview) is complementary to dedicated canonicals, not duplicative. |

---

### Phase 4: Move Files into Topic Folders

**Status: Complete**

**Goal:** Files live under topic-named folders matching the Target Structure from Phase 2.

- Create the topic folders.
- Move each canonical file into its target folder.
- Update the README to reflect the new folder names and what belongs in each.
- Delete files marked redundant in Phase 3.

**Done when:** The folder structure matches the Target Structure. No slide files remain in the old delivery-context folders. The README describes the new layout.

---

### Phase 5: Walk Through and Validate

**Status: Complete**

**Goal:** Confirm the reorganized slides tell a coherent story and nothing important was lost.

- Read through the canonical file for each topic cluster in the order listed in Phase 2.
- Check that each file can stand alone without assuming the reader has seen a previous deck.
- Note any topic from the Key Topics Summary above that no file covers adequately. Record these as gaps.
- Write a short "what is missing" list in this file.

**Done when:** Every topic cluster has been reviewed. Gaps are written down. No content from the original files has been silently lost.

---

#### Coverage Check

Every topic from the Key Topics Summary has at least one canonical file that covers it. No topic was silently lost during the reorganization.

| Topic | Covered In |
|-------|-----------|
| Dual-database architecture | `platform-overview/01-workshop-overview-slides.md`, `platform-overview/02-databricks-neo4j-integration-slides.md`, `platform-overview/03-intro-databricks-neo4j-slides.md` |
| Neo4j graph fundamentals (nodes, Cypher) | `platform-overview/02-databricks-neo4j-integration-slides.md`, `platform-overview/03-intro-databricks-neo4j-slides.md` |
| Neo4j Aura | `platform-overview/04-neo4j-aura-overview-slides.md` |
| Medallion Architecture | `platform-overview/03-intro-databricks-neo4j-slides.md` |
| Neo4j Spark Connector | `platform-overview/02-databricks-neo4j-integration-slides.md` (appendix), `platform-overview/03-intro-databricks-neo4j-slides.md` |
| LLM limitations | `genai-foundations/02-genai-and-limitations-slides.md`, `agents/02-power-of-graphrag-slides.md` |
| Traditional RAG | `genai-foundations/03-traditional-rag-slides.md` |
| Context ROT | `genai-foundations/04-context-and-rag-slides.md` |
| GraphRAG | `platform-overview/02-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md`, `genai-foundations/04-context-and-rag-slides.md`, `graph-ml/03-graph-enrichment-slides.md` |
| Knowledge graph construction | `background/kg-construction/05-building-knowledge-graphs-slides.md` (Background), `agents/02-power-of-graphrag-slides.md` |
| SimpleKGPipeline | `background/kg-construction/05-building-knowledge-graphs-slides.md` (Background), `background/kg-construction/06-schema-design-slides.md` (Background) |
| Schema design | `background/kg-construction/06-schema-design-slides.md` (Background) |
| Chunking strategies | `kg-construction/07-chunking-slides.md` |
| Entity resolution | `background/kg-construction/08-entity-resolution-slides.md` (Background) |
| Vectors and embeddings | `kg-construction/09-vectors-slides.md` |
| Vector Retriever | `retrieval-patterns/02-vector-retriever-slides.md` |
| Vector Cypher Retriever | `retrieval-patterns/03-vector-cypher-retriever-slides.md` |
| Text2Cypher Retriever | `retrieval-patterns/04-text2cypher-retriever-slides.md` |
| ReAct pattern and agents | `agents/01-from-retrievers-to-agents-slides.md` |
| Genie Agent | `platform-overview/02-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md`, `agents/03-langgraph-supervisor-slides.md` (as a tool node) |
| Neo4j MCP Server | `platform-overview/02-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md` |
| Multi-agent supervisor | `platform-overview/02-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md`, `agents/03-langgraph-supervisor-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md` |
| LangGraph supervisor agent | `agents/03-langgraph-supervisor-slides.md` |
| Agent deployment to Model Serving | `agents/04-deploy-the-agent-slides.md` |
| Agent memory | `agents/05-agent-memory-slides.md` |
| Graph Data Science (GDS) | `platform-overview/04-neo4j-aura-overview-slides.md` (brief), `graph-ml/03-graph-enrichment-slides.md` |
| Graph feature engineering | `graph-ml/03-graph-enrichment-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md` |
| MLflow experiment tracking | `graph-ml/03-graph-enrichment-slides.md` |
| Agentic graph enrichment | `graph-ml/04-future-graph-enrichment-slides.md` |
| Incremental sync with Change Data Feed | `graph-ml/03-graph-enrichment-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md` |
| Neo4j as semantic map | `platform-overview/02-databricks-neo4j-integration-slides.md`, `background/governance/auth-sync-slides.md` (Background) |
| Authorization sync | `background/governance/auth-sync-slides.md` (Background) |
| Aircraft digital twin | `platform-overview/01-workshop-overview-slides.md`, `platform-overview/02-databricks-neo4j-integration-slides.md` |
| Financial fraud detection | `platform-overview/03-intro-databricks-neo4j-slides.md`, `background/governance/auth-sync-slides.md` (Background) |

---

#### Issues Found Per Cluster

**platform-overview/**

1. **Stale title in `platform-overview/04-neo4j-aura-overview-slides.md`**: RESOLVED in Phase 6. The first content slide read `# GraphRAG Agent Blueprint with AWS` on a deck about Neo4j Aura tools. It now reads `# Neo4j Aura: Cloud Graph Database`.

2. **Four files share the `01-` prefix**: STILL OPEN. `platform-overview/02-databricks-neo4j-integration-slides.md`, `platform-overview/03-intro-databricks-neo4j-slides.md`, `platform-overview/04-neo4j-aura-overview-slides.md`, and `platform-overview/01-workshop-overview-slides.md` all sort together. No clear primary file for the cluster.

**genai-foundations/**

3. **Sequence assumptions in `genai-foundations/03-traditional-rag-slides.md`**: RESOLVED in Phase 6. The opening no longer says "Remember the LLM limitations we discussed"; the slide now restates the three limitations in full, so the deck stands alone.

4. **Sequence assumption in `genai-foundations/04-context-and-rag-slides.md`**: RESOLVED in Phase 6. The opening no longer says "We've seen how RAG provides context to LLMs"; it now restates what traditional RAG does before naming its limits.

**retrieval-patterns/**

5. **Use case mismatch across all four files**: RESOLVED in Phase 6. All four files used a finance and investment use case (Companies, RiskFactors, AssetManagers, Apple, BlackRock). All four now use the aircraft digital twin, matching the rest of the workshop.

**agents/**

6. **Stale "Next" pointer in `agents/01-from-retrievers-to-agents-slides.md`**: RESOLVED in Phase 6. The final summary slide read "Next: Learn about the Microsoft Agent Framework." No mention of a Microsoft Agent Framework remains anywhere under `slides/`.

7. **Numeric sort order inverts logical order**: RESOLVED in Phase 6. The ReAct fundamentals deck was renamed from `08-from-retrievers-to-agents-slides.md` to `agents/01-from-retrievers-to-agents-slides.md`, so directory order now matches teaching order: 01 ReAct fundamentals, 02 Genie and MCP and supervisor, 03 LangGraph supervisor, 04 deployment.

8. **Use case mismatch with other agents content**: PARTLY RESOLVED. `agents/01-from-retrievers-to-agents-slides.md` now uses the aircraft digital twin. `agents/02-power-of-graphrag-slides.md` still uses financial fraud, which does not match the aircraft use case of the surrounding decks. `agents/03` and `agents/04` both use aircraft.

**graph-ml/**

9. **Webinar recap slides**: RESOLVED in Phase 6. Both files opened with a "Partnership Overview and Recap" section listing joint customers. No such slides remain in either file.

10. **Content overlap on incremental sync**: STILL OPEN. Both `graph-ml/03-graph-enrichment-slides.md` and `graph-ml/04-future-graph-enrichment-slides.md` cover Change Data Feed and the bi-directional loop pattern with similar slides. The overlap is moderate, not a duplication problem, but a reader studying both files will encounter the same material twice.

11. **Use case mismatch with the workshop**: STILL OPEN. Both `graph-ml/` files use the portfolio and asset manager use case rather than the aircraft digital twin. These are deep-dive decks rather than workshop lab decks, so the mismatch is less disruptive than it was in `retrieval-patterns/`.

---

#### What Is Missing

Gaps confirmed from Phase 2 and newly identified in this review:

**Confirmed gaps from Phase 2:**
- No standalone introduction to JDBC federation as a topic. `background/governance/auth-sync-slides.md` opens with a JDBC federation status update but it is a partner/internal briefing, not a teaching deck, and it now sits on the Background track rather than the workshop path.
- Databricks Vector Search as an external vector store option. CLOSED in Phase 6: `retrieval-patterns/01-retrievers-overview-slides.md` now carries an "External Vector Stores: Databricks Vector Search" slide.
- Genie Agent setup and configuration steps. Still a gap. Covered in workshop notebooks, not in slides.

**New gaps identified in Phase 5:**
- No slide covering the `GraphRAG` orchestration class from `neo4j-graphrag-python`. CLOSED in Phase 6: `retrieval-patterns/01-retrievers-overview-slides.md` now carries a "The GraphRAG Class" slide.
- No slide on LangGraph or any other agent framework. CLOSED: `agents/03-langgraph-supervisor-slides.md` builds the Lab 5 supervisor in LangGraph, and `agents/04-deploy-the-agent-slides.md` takes the same graph to a Model Serving endpoint.

- No agent memory deck. CLOSED: `agents/05-agent-memory-slides.md` covers Lab 6 in nine slides, from the stateless Lab 5 agent through the three memory layers, superseding, and the adoption payoff.

**Gaps as of the current file layout:**
- None outstanding in the agents cluster.

**What is not a gap:** Aura Agents. The feature is out of scope for this workshop and no deck should cover it. The `graph-ml/` portfolio use case is a coherence issue, not a content gap: the concepts are fully covered and only the example domain differs.

---

## File Inventory

Phase 1 complete. Every `.md` file under `slides/` (excluding `node_modules/` and this file) has a row below with its format, topic cluster, depth level, and primary use case. Files marked with * span more than one cluster.

**Format:** Marp = presentation slide deck | Reference = participant reference doc, no Marp | Outline = planning or narrative arc, not a deliverable slide deck | Admin = README or meta doc

**Depth:** overview | practitioner | deep dive | n/a (not applicable)

**Track:** Workshop = on the workshop delivery path | Background = kept and maintained, moved off the workshop path under `background/` | n/a (not a deck)

| File | Format | Track | Topic Cluster | Depth | Use Case | Notes |
|------|--------|-------|---------------|-------|----------|-------|
| `README.md` | Admin | n/a | meta | n/a | n/a | Build and usage instructions for the slides directory. Not a slide file. |
| `platform-overview/03-intro-databricks-neo4j-slides.md` | Marp | Workshop | platform overview * | deep dive | fraud | * Also covers governance (Spark Connector, bidirectional data flow) and knowledge graph construction (graph modeling decisions). Fraud and portfolio lens; distinct from the aircraft angle of other platform files. |
| `agents/02-power-of-graphrag-slides.md` | Marp | Workshop | agents and multi-agent systems * | deep dive | fraud | * Also covers GenAI foundations (LLM limitations). Most detailed treatment of Genie, Neo4j MCP, and the multi-agent supervisor. Use case corrected from aircraft to fraud: the worked example is regulations, thresholds, and account transfers. |
| `graph-ml/03-graph-enrichment-slides.md` | Marp | Workshop | graph ML and enrichment | deep dive | portfolio | GDS algorithms, feature engineering, MLflow lift comparison, bidirectional data loop, incremental sync with Change Data Feed. |
| `graph-ml/04-future-graph-enrichment-slides.md` | Marp | Workshop | graph ML and enrichment * | deep dive | portfolio | * Also covers agents (agentic enrichment loop, multi-agent supervisor for gap detection). Overlaps with 03 on incremental sync. |
| `background/governance/auth-sync-slides.md` | Marp | Background | governance and integration | deep dive | generic | Unique content: four authorization sync patterns between Unity Catalog and Neo4j, plus the semantic map data model, plus the JDBC federation status update it opens with. No substantial overlap with other files. Partner and internal briefing rather than a teaching deck, which is why it sits on the Background track. |
| `docs/slides.md` | Outline | n/a | graph ML and enrichment | n/a | portfolio | Deleted 2026-08-09, no current path. Was a 15-line narrative arc for the graph enrichment decks, already realized in `graph-ml/03-graph-enrichment-slides.md`. Never a deliverable slide file. |
| `docs/building-knowledge-graphs.md` | Reference | n/a | knowledge graph construction | practitioner | aircraft | Deleted 2026-08-09, no current path. Was 79% verbatim duplicate of the five KG construction decks now at `background/kg-construction/05`, `06`, `08` and `kg-construction/07`, `09`. No unique content. |
| `docs/overview-and-genai-foundations.md` | Reference | n/a | GenAI foundations * | overview / practitioner | aircraft | Deleted 2026-08-09, no current path. Was 74% verbatim duplicate of `platform-overview/01-workshop-overview-slides.md` and `genai-foundations/02`, `03`, `04`, and had drifted: it still carried the "Hourly-scale" telemetry error after the deck was corrected. |
| `platform-overview/02-databricks-neo4j-integration-slides.md` | Marp | Workshop | platform overview * | overview | aircraft | * Also covers agents (MCP, multi-agent supervisor) and governance (semantic map, JDBC federation). Most complete single-file overview of the full partnership. |
| `overview-databricks-neo4j/SUMMARY.md` | Reference | n/a | platform overview | overview | aircraft | Deleted in Phase 4, no current path. Was a condensed plain-text summary of `platform-overview/02-databricks-neo4j-integration-slides.md`. No unique content. |
| `platform-overview/04-neo4j-aura-overview-slides.md` | Marp | Workshop | platform overview | overview | generic | Neo4j Aura managed cloud: what Aura is, why a graph database, the value of Aura for GenAI, graph analytics in Explore, and the three tools (Query Workspace, Explore, Dashboards). Description corrected: the deck carries no Aura Agents content. No substantial overlap with other files. |
| `platform-overview/01-workshop-overview-slides.md` | Marp | Workshop | platform overview | overview | aircraft | Workshop opener: digital twin definition, the dataset's entity types, dual-database architecture, shared vs personal infrastructure. Distinct role as the workshop entry point. |
| `genai-foundations/02-genai-and-limitations-slides.md` | Marp | Workshop | GenAI foundations | overview | generic | LLM strengths and three core limitations (hallucination, knowledge cutoff, relationship blindness). Clean standalone file. |
| `genai-foundations/03-traditional-rag-slides.md` | Marp | Workshop | GenAI foundations | overview | generic | RAG motivation, embeddings as smart librarian analogy, retrieval flow. Clean standalone file. |
| `genai-foundations/04-context-and-rag-slides.md` | Marp | Workshop | GenAI foundations | practitioner | aircraft | Context ROT, questions RAG cannot answer, GraphRAG solution with three retrieval patterns. Bridges GenAI foundations to knowledge graph construction. |
| `background/kg-construction/05-building-knowledge-graphs-slides.md` | Marp | Background | knowledge graph construction | practitioner | aircraft | neo4j-graphrag package, SimpleKGPipeline, aircraft digital twin graph structure. Entry point for the KG construction sequence when that sequence is taught in full. |
| `background/kg-construction/06-schema-design-slides.md` | Marp | Background | knowledge graph construction | practitioner | aircraft | Three schema modes, node type definitions, relationship patterns, workshop schema table. |
| `kg-construction/07-chunking-slides.md` | Marp | Workshop | knowledge graph construction | practitioner | generic | Chunk size trade-off, FixedSizeSplitter parameters, typical size ranges, evaluation Cypher queries. |
| `background/kg-construction/08-entity-resolution-slides.md` | Marp | Background | knowledge graph construction | practitioner | aircraft | Duplicate entity problem, three resolution strategies, FuzzyMatchResolver example. |
| `kg-construction/09-vectors-slides.md` | Marp | Workshop | knowledge graph construction | practitioner | generic | Embeddings definition, cosine similarity, storing vectors in Neo4j, combining with graph traversal. |
| `retrieval-patterns/01-retrievers-overview-slides.md` | Marp | Workshop | retrieval patterns | practitioner | aircraft | Three retriever types, the `GraphRAG` orchestration class, Databricks Vector Search as an external store, decision framework table. |
| `retrieval-patterns/02-vector-retriever-slides.md` | Marp | Workshop | retrieval patterns | practitioner | aircraft | VectorRetriever creation, similarity score ranges, top_k parameter, limitations. |
| `retrieval-patterns/03-vector-cypher-retriever-slides.md` | Marp | Workshop | retrieval patterns | practitioner | aircraft | Two-step vector + Cypher process, retrieval_query with OPTIONAL MATCH, chunk as anchor concept. |
| `retrieval-patterns/04-text2cypher-retriever-slides.md` | Marp | Workshop | retrieval patterns | practitioner | aircraft | Text2CypherRetriever, schema role, security considerations, generated query quality. |
| `agents/01-from-retrievers-to-agents-slides.md` | Marp | Workshop | agents and multi-agent systems | practitioner | aircraft | Four agent components, tools, ReAct pattern, multi-tool example. Bridges the retrieval patterns cluster to agents. |
| `agents/03-langgraph-supervisor-slides.md` | Marp | Workshop | agents and multi-agent systems | practitioner | aircraft | The Lab 5 supervisor in LangGraph. What the earlier labs supply, the shape of the graph, the three tool nodes (Genie, Cypher over the participant's own Aura instance, GraphRAG over the manuals), routing as a loop rather than a one-shot decision, the two prompt rules that fix the routing failures, measured routing, and why the Cypher node uses a Bolt driver rather than MCP. |
| `agents/04-deploy-the-agent-slides.md` | Marp | Workshop | agents and multi-agent systems | practitioner | aircraft | Taking the same graph to Model Serving. What changes when the endpoint runs as its own service principal, the MLflow `ResponsesAgent` wrapper, registering to Unity Catalog, declaring resources against referencing credentials, deploy and wait, scoring the deployed endpoint, and why the object names are a contract Lab 6 depends on. |
| `agents/05-agent-memory-slides.md` | Marp | Workshop | agents and multi-agent systems | practitioner | aircraft | Lab 6 agent memory in Neo4j. Nine slides: why the Lab 5 agent is stateless, why a longer prompt or a vector store does not fix it, the three memory layers (short term, long term, reasoning), the reasoning-trace query that is the thesis, superseding rather than deleting so a wrong answer stays auditable, hot-path against background writes, the `recall` and `remember` nodes added around an unchanged supervisor, the adoption payoff where fleet ranking and conversation ranking disagree, and why memory belongs on the side where the joins are. |

**Multi-cluster files (flagged for review in Phase 3):**

- `platform-overview/03-intro-databricks-neo4j-slides.md`: platform overview + governance and integration + knowledge graph construction
- `agents/02-power-of-graphrag-slides.md`: agents and multi-agent systems + GenAI foundations
- `graph-ml/04-future-graph-enrichment-slides.md`: graph ML and enrichment + agents and multi-agent systems
- `platform-overview/02-databricks-neo4j-integration-slides.md`: platform overview + agents and multi-agent systems + governance and integration

---

## Target Structure

Phase 2 complete. Proposed topic-based folder layout with canonical files named per cluster and a list of redundant files. The layout below has been updated to match what is on disk now: the governance deck and three of the five KG construction decks moved under `background/`, and three agent decks were added.

### Folder Layout

```
slides/
  platform-overview/        Workshop  (why Databricks + Neo4j, dual-database architecture, Neo4j Aura)
  genai-foundations/        Workshop  (LLM limitations, traditional RAG, Context ROT)
  kg-construction/          Workshop  (chunking, vectors)
  retrieval-patterns/       Workshop  (Vector, Vector Cypher, Text2Cypher retrievers)
  agents/                   Workshop  (ReAct, Genie, MCP, LangGraph supervisor, deployment)
  graph-ml/                 Workshop  (GDS, feature engineering, enrichment loop, MLflow)
  background/
    governance/             Background  (authorization sync, semantic map, JDBC federation)
    kg-construction/        Background  (SimpleKGPipeline, schema design, entity resolution)
  docs/                     Not built  (long-form participant reference docs and one outline, not Marp)
  images/                   Not built  (shared image assets)
  aircraft/                 Not built  (diagram sources: .excalidraw and .svg)
  databricks-in-depth/      Not built  (diagram sources: .excalidraw and .svg)
  README.md                 Not built  (build and usage instructions)
  organize.md               Not built  (this file)
```

### Canonical Files per Cluster

| Cluster | Track | File | Role |
|---------|-------|------|------|
| platform-overview | Workshop | `platform-overview/02-databricks-neo4j-integration-slides.md` | Most complete overview of the full partnership: dual-database, Spark Connector, GraphRAG, MCP, semantic map, and multi-agent routing. Primary file for webinars and conference talks. |
| platform-overview | Workshop | `platform-overview/01-workshop-overview-slides.md` | Workshop entry point with digital twin definition, the dataset's entity types, and shared vs personal infrastructure. Serves a different role than the file above; keep separately. |
| platform-overview | Workshop | `platform-overview/04-neo4j-aura-overview-slides.md` | Unique focus on the managed cloud product: what Aura is, the value of Aura for GenAI, graph analytics in Explore, and the Query Workspace, Explore, and Dashboards tools. No overlap with other platform files; keep separately. |
| platform-overview | Workshop | `platform-overview/03-intro-databricks-neo4j-slides.md` | Deeper engineering perspective through fraud and portfolio lens. Assign to platform-overview/ for now; spans multiple clusters, flag for potential split in a future phase. |
| GenAI foundations | Workshop | `genai-foundations/02-genai-and-limitations-slides.md` | Standalone LLM limitations treatment. |
| GenAI foundations | Workshop | `genai-foundations/03-traditional-rag-slides.md` | Standalone traditional RAG introduction. |
| GenAI foundations | Workshop | `genai-foundations/04-context-and-rag-slides.md` | Context ROT and the case for GraphRAG. Bridges GenAI foundations to knowledge graph construction. |
| knowledge graph construction | Background | `background/kg-construction/05-building-knowledge-graphs-slides.md` | Entry point for the KG construction sequence: neo4j-graphrag package, SimpleKGPipeline. |
| knowledge graph construction | Background | `background/kg-construction/06-schema-design-slides.md` | Schema design. |
| knowledge graph construction | Workshop | `kg-construction/07-chunking-slides.md` | Chunking strategies. |
| knowledge graph construction | Background | `background/kg-construction/08-entity-resolution-slides.md` | Entity resolution. |
| knowledge graph construction | Workshop | `kg-construction/09-vectors-slides.md` | Vectors and embeddings. |
| retrieval patterns | Workshop | `retrieval-patterns/01-retrievers-overview-slides.md` | Retriever overview, the `GraphRAG` class, external vector stores, and the decision framework. Entry point for the retrieval sequence. |
| retrieval patterns | Workshop | `retrieval-patterns/02-vector-retriever-slides.md` | Vector Retriever. |
| retrieval patterns | Workshop | `retrieval-patterns/03-vector-cypher-retriever-slides.md` | Vector Cypher Retriever. |
| retrieval patterns | Workshop | `retrieval-patterns/04-text2cypher-retriever-slides.md` | Text2Cypher Retriever. |
| agents and multi-agent systems | Workshop | `agents/01-from-retrievers-to-agents-slides.md` | ReAct pattern and agent fundamentals. Entry point for the agents cluster. |
| agents and multi-agent systems | Workshop | `agents/02-power-of-graphrag-slides.md` | Genie, Neo4j MCP, and the multi-agent supervisor. Most detailed conceptual treatment. Spans GenAI foundations but the agent architecture is the primary content. |
| agents and multi-agent systems | Workshop | `agents/03-langgraph-supervisor-slides.md` | The Lab 5 supervisor written in LangGraph: three tool nodes, routing as a loop, the prompt rules that make routing correct, and why the Cypher node uses a Bolt driver rather than MCP. |
| agents and multi-agent systems | Workshop | `agents/04-deploy-the-agent-slides.md` | The same graph on Model Serving: service principal identity, the MLflow `ResponsesAgent` wrapper, Unity Catalog registration, resources against credentials, and scoring the deployed endpoint. |
| agents and multi-agent systems | Workshop | `agents/05-agent-memory-slides.md` | Lab 6 agent memory: the three memory layers on one graph, superseding rather than deleting, `recall` and `remember` around an unchanged supervisor, and the adoption payoff that makes a remembered aircraft the fleet node. |
| graph ML and enrichment | Workshop | `graph-ml/03-graph-enrichment-slides.md` | GDS algorithms, graph feature engineering, MLflow lift comparison, bidirectional data loop. |
| graph ML and enrichment | Workshop | `graph-ml/04-future-graph-enrichment-slides.md` | Agentic enrichment loop, confidence scoring, ontology validation. Spans agents cluster but graph ML is the primary content. |
| governance and integration | Background | `background/governance/auth-sync-slides.md` | Four authorization sync patterns. Unique content; no overlap with other files. |

### Redundant Files

| File | Redundant Because | Proposed Action |
|------|-------------------|-----------------|
| `overview-databricks-neo4j/SUMMARY.md` | Condensed plain-text version of `platform-overview/02-databricks-neo4j-integration-slides.md`. No unique content. | Marked for deletion in Phase 3, deleted in Phase 4. No current path. |
| `databricks-in-depth/slides.md` | Narrative arc planning document, not a deliverable slide deck. No slide content to preserve. | Moved to `docs/slides.md` in Phase 4; not a candidate for a topic folder. |

**Reference docs, deleted 2026-08-09.** `docs/` held three long-form markdown files that were never built and never linked from anywhere except audit records. Measured against the decks, `building-knowledge-graphs.md` was 79% verbatim duplicate of the five KG construction decks and `overview-and-genai-foundations.md` was 74% verbatim duplicate of `platform-overview/01-workshop-overview-slides.md` plus the three `genai-foundations` decks. The residual was reworded prose and an obsolete provider list, not new material. `slides.md` was a 15-line planning outline for the graph-ml narrative arc, already realized in `graph-ml/03-graph-enrichment-slides.md`. They had also drifted: `overview-and-genai-foundations.md` still carried the "Hourly-scale" telemetry error after the deck was corrected. Recoverable with `git show d7faca2:slides/docs/<file>`.

### Gaps Identified in Phase 2

No dedicated slide file exists for:
- JDBC federation and SQL-to-Cypher translation (mentioned in `platform-overview/02-databricks-neo4j-integration-slides.md` but not developed as standalone slides)
- Databricks Vector Search as a pluggable external vector store (mentioned in one slide, not developed). Closed in Phase 6, see the What Is Missing section
- Genie Agent setup and configuration steps (covered in workshop notebooks, not in slides)

These are content gaps to address in a future content phase, not part of the reorganization.

---

---

### Phase 6: Fix Issues and Fill Gaps

**Status: Complete**

**Goal:** Address the 10 issues and 6 gaps documented in Phase 5.

**Fixing:**
- Stale title slide in `platform-overview/04-neo4j-aura-overview-slides.md`
- Stale "Next: Microsoft Agent Framework" pointer in the from-retrievers-to-agents deck
- Sequence-dependent openings in `genai-foundations/03-traditional-rag-slides.md` and `genai-foundations/04-context-and-rag-slides.md`
- Use case mismatch in all four `retrieval-patterns/` files and the from-retrievers-to-agents deck (finance to aircraft)
- Sort order in `agents/` by renaming `08-from-retrievers-to-agents-slides.md` to `agents/01-from-retrievers-to-agents-slides.md`
- Webinar partnership recap slides in `graph-ml/03-graph-enrichment-slides.md` and `graph-ml/04-future-graph-enrichment-slides.md`
- Gap: add `GraphRAG` class slides to `retrieval-patterns/01-retrievers-overview-slides.md`
- Gap: add Databricks Vector Search slide to `retrieval-patterns/01-retrievers-overview-slides.md`

**Not fixing:**
- Four `01-` prefix files in `platform-overview/`: naming, not content; renaming would break history and links
- Content overlap on incremental sync in `graph-ml/`: editorial decision deferred
- JDBC federation standalone intro: content already covered in `background/governance/auth-sync-slides.md`
- Genie Agent setup/configuration: covered in workshop notebooks, not slides

**Superseded by later work:** the "no LangGraph slides" gap was later closed by `agents/03-langgraph-supervisor-slides.md` and `agents/04-deploy-the-agent-slides.md`, which were written after this phase.

**Done when:** All items above marked complete. No new content errors introduced.

---

### Phase 7: Reorganize into Eight Decks

**Status: Complete, 2026-08-09.**

**Goal:** Replace the seventeen workshop slide files with eight decks that follow the run of show, one deck per folder, one file per deck.

#### Progress

| Step | Status | Result |
|------|--------|--------|
| Shelve three decks under `background/` | Done | `git mv` of `agents/02`, `graph-ml/03`, `graph-ml/04`. Image depth fixed with an extra `..` in both graph-ml decks |
| Write the eight decks | Done | 2,517 lines total, 121 slides. Written by eight parallel agents, one per deck |
| Verify frontmatter | Done | All eight match the template byte for byte |
| Verify no em dashes | Done | Zero across all eight |
| Delete the seventeen consumed files | Done | 4,631 lines removed. `platform-overview/`, `genai-foundations/`, `kg-construction/`, `retrieval-patterns/` and `agents/` are gone |
| Stage `spark-connector-virtual-graph.png` | Done | Tracked, lands in deck 2 |
| Update `build-slides.sh` | Done | `WORKSHOP_TOPICS` is the eight `overview-*` names in run-of-show order. `copy_assets` now mirrors `slides/aircraft/` |
| Update `slides/README.md` | Done | Slide Decks section is a run-of-show table with the lab each deck pairs with |
| Rewire the site | Done | 16 wrappers deleted, 8 written, `slides-agent-memory.adoc` repointed and retitled, 3 shelved wrappers repointed to `background/` paths, Slides section of `site/nav.adoc` rewritten as a flat numbered list |
| Build verification | Done | 15 decks built, 8 workshop and 7 background. Every image reference in the built HTML resolves to a file under `attachments/`. Zero broken links |
| Quality and flow review | Done | Eight decks read end to end. Six fixes applied, listed below. Rebuilt and re-verified after |

**Deck sizes as shipped:**

| # | Deck | Lines | Slides |
|---|------|-------|--------|
| 1 | `overview-business-story/01-business-case-slides.md` | 162 | 9 |
| 2 | `overview-architecture/01-architecture-roadmap-slides.md` | 387 | 16 |
| 3 | `overview-knowledge-graph/01-knowledge-graph-foundations-slides.md` | 337 | 19 |
| 4 | `overview-graphrag/01-graphrag-foundations-slides.md` | 259 | 15 |
| 5 | `overview-retrievers/01-retriever-patterns-slides.md` | 452 | 18 |
| 6 | `overview-agent/01-supervisor-agent-slides.md` | 340 | 18 |
| 7 | `overview-agent-memory/01-agent-memory-slides.md` | 299 | 13 |
| 8 | `overview-mcp/01-mcp-agent-bricks-slides.md` | 285 | 13 |

#### Review pass, 2026-08-09

Mechanical checks passed with no changes: no financial-domain vocabulary anywhere in the eight decks, no em dashes, no litotes, no throat-clearing openers, all code fences balanced, all frontmatter identical.

Six content fixes applied:

| Deck | Problem | Fix |
|------|---------|-----|
| 5 Retrievers | The `retrieval_query` example was invented. It used SQL-style `--` Cypher comments and a `DESCRIBES` relationship that does not exist in the graph | Replaced with `system_context_query`, verbatim from `Lab_3_Semantic_Search/02_graphrag_retrievers.ipynb`. The following slide's `OPTIONAL MATCH` example was rewritten to match it |
| 5 Retrievers | Text2Cypher example used `{tailNumber:'N10001'}` | Corrected to `tail_number`, the real property name |
| 1 Business Case | Slide 8 pointed forward to deck 4 for depth on LLM limits; deck 4's own notes pointed back to deck 1 for the same thing | Deck 1 keeps the depth and ends on how retrieval and the graph close each gap. Deck 4's notes now name the deck rather than a number and mark the slide as a one-line recall |
| 1 Business Case | "Why LLMs Alone Fall Short" sat after the hero question, breaking the argument | Moved directly after "The Stakes", so the deck runs stakes, why the model alone fails, why vectors alone fail, then GraphRAG |
| 3 Knowledge Graph | The SQL versus Cypher pair read as an apology for the Databricks schema | Reframed as an escalation: state what the question needs, show what SQL reaches, then run the real question in Cypher. Also fixed a question written with a period and dropped the explanatory parentheses in the language labels |
| 7 Agent Memory | Instructor note cited "the GenAI foundations deck", a name Phase 7 retired | Now cites the GraphRAG Foundations deck, which is where Context Rot lives |

**Open, needs a decision:** `site/modules/ROOT/images/dual-database-architecture.svg` has stale figures baked into it, 345,600+ readings, 160 sensors, 80 systems, 20 aircraft. The committed CSVs hold 155,520 readings, 288 sensors, 144 systems, 36 aircraft, and deck 2's own instructor note says roughly 155,000. The file is a shared site asset used outside the slides, so it was left alone.

**Deviations from plan, recorded:**

- **Line counts ran above target.** The plan estimated about 1,890 lines; the decks ship at 2,517. The gap is code blocks and tables, which condense less than prose. Decks 2, 5 and 6 carry the overage.
- **The three-hop SQL versus Cypher contrast changed question.** The Databricks side has four gold tables in a fixed linear join chain and no junction table, so the fraud deck's variable-depth reachability question has no SQL answer on the real schema. Deck 3 substitutes a self-join on shared sensor type as what SQL reaches, then runs the real variable-depth question in Cypher.
- **`list-gds-procedures` dropped from the MCP tools slide.** The deployment this repo documents in `MCP-MANUAL-SETUP.md` exposes two tools, `get_neo4j_schema` and `read_neo4j_cypher`. The source slide listed a third that does not exist here.
- **The semantic map argument was dropped from deck 8.** Syncing Unity Catalog metadata into Neo4j is a different feature from the two-agent supervisor demo Lab 4 Part B actually runs.
- **`fraud-ring-dual-architecture.svg` stays fraud-flavored.** No new deck references it. It survives only in `background/governance/auth-sync-slides.md`, which is shelved.
- **`intelligence-platform-flow.svg` is orphaned.** Nothing referenced it before this phase either.

Phase 7 supersedes the Target Structure and Canonical Files tables above. Those describe the six-folder layout this phase replaces.

#### Why

Measured against the sibling workshop at `/Users/ryanknight/projects/aws/neo4j-bedrock-graphrag-workshop/slides`, which runs eight decks totalling 1,876 lines:

- **Deck count and size:** seventeen workshop files here, 126 to 956 lines each. Four of them share an `01-` prefix and sort together.
- **Deck names:** `02-databricks-neo4j-integration` names a file. `The Business Case for GraphRAG` names what the audience gets.
- **Opening:** the sibling opens on the cost of a wrong answer, then hero questions, then a live demo of the finished build. This workshop opens on "What You'll Build".
- **Hero question:** the sibling repeats the same two questions in decks 1, 3, and 6. The anchor question here appears once, at `agents/03-langgraph-supervisor-slides.md:330`.
- **Use case:** the sibling uses SEC 10-K throughout. This workshop uses aircraft on the path, fraud in two decks, and portfolio in two more.
- **Graph introduction:** the sibling has a dedicated Knowledge Graph Foundations deck covering nodes, Cypher, and the schema before any GraphRAG. This workshop has none. Graph basics are spread across `platform-overview/02`, `03`, and `04`.

#### The Eight Decks

Folder convention is `overview-<topic>/01-<topic>-slides.md`, one file per folder. This retires the `01-` prefix collision and the numeric sort problem recorded as issues 2 and 7 in Phase 5.

| # | Deck | Built from |
|---|------|-----------|
| 1 | **The Business Case for GraphRAG** | New. Plus `genai-foundations/02`, `agents/02:36`, `platform-overview/01` What You'll Build |
| 2 | **Workshop Architecture and Roadmap** | `platform-overview/01` + `02`, plus salvage items 1, 2, 3, 6 |
| 3 | **Knowledge Graph Foundations** | New. Plus `platform-overview/04` whole, `02` appendix, salvage items 4 and 5 |
| 4 | **GraphRAG Foundations** | `genai-foundations/03` + `04`, `kg-construction/09` + `07`, `agents/02:55` to `:174` |
| 5 | **GraphRAG Retriever Patterns** | `retrieval-patterns/01` to `04` merged, 787 lines to about 290 |
| 6 | **The Supervisor Agent and Deployment** | `agents/01` + `03` + `04` |
| 7 | **Agent Memory with Neo4j** | `agents/05`, trimmed 539 to about 280 |
| 8 | **Neo4j MCP and Agent Bricks** | `agents/02:218` to `:383`, reframed as the Lab 4 Part B instructor demo |

**Hero question.** The anchor question at `agents/03:330`, on abnormal EGT readings routed through Genie, then the graph, then the manual, becomes the hero question. It opens deck 1 and recurs in decks 5, 6, and 8.

**Opening demo.** Deck 1 closes on a single "Opening Demo" slide carrying instructor notes in an HTML comment. Building the deck requires no live endpoint.

#### Deleted

One file, `platform-overview/03-intro-databricks-neo4j-slides.md`. 762 lines, 38 slides. Six slides are salvaged first, listed below. The remaining 32 are the fraud use case, the ELT walkthrough, and four appendices.

Fifteen files are consumed rather than deleted. Their paths go away and their content moves into a new deck: `platform-overview/01`, `02`, `04`; `genai-foundations/02`, `03`, `04`; `kg-construction/07`, `09`; `retrieval-patterns/01` to `04`; `agents/01`, `03`, `04`, `05`.

#### Salvage Manifest

Lift these six out of `platform-overview/03` before it goes.

| Source | Lands |
|--------|-------|
| `03:111` The Medallion Architecture | Deck 2, one slide, rebuilt |
| `03:168` The Intelligence Platform Data Flow, plus `spark-connector-virtual-graph.png` | Deck 2, full bleed |
| `03:200` Neo4j Connection Patterns by Platform Stage | Deck 2, verbatim |
| `03:432` Design Decision: Relationship Types vs. Properties | Deck 3, verbatim |
| `03:605` and `03:654` The Same Question, Two Languages | Deck 3, converted to aircraft |
| `03:286` and `03:589` Data Intelligence, Graph Intelligence, or Both, plus the Decision Table | Deck 2 |

The sixth item was added during review. The SQL versus Cypher decision table covering hop count, query shape, result type, latency, and volume exists nowhere else in the repository, so deleting the deck would lose it silently.

The fifth item is a three-hop `USED_DEVICE|REGISTERED_AT*1..3` traversal set against a four-CTE SQL block. The aircraft rewrite needs a variable-depth path over the real Lab 2 schema, along the lines of every aircraft within three hops of the component that failed on a given tail number, through shared systems and maintenance events. Check the join tables against the loaded graph before writing the SQL.

#### Shelved

Three files move to `background/` unchanged, off the build path. Shelving keeps them readable, so decks 1, 4, and 8 copy slides out of `agents/02` rather than inheriting them.

| File | Destination |
|------|-------------|
| `agents/02-power-of-graphrag-slides.md` | `background/agents/` |
| `graph-ml/03-graph-enrichment-slides.md` | `background/graph-ml/` |
| `graph-ml/04-future-graph-enrichment-slides.md` | `background/graph-ml/` |

This closes Phase 5 issues 8, 10, and 11, all three of which were use case or overlap problems in decks that no longer sit on the workshop path.

#### How `agents/02` Splits

| Slide | Goes to |
|-------|---------|
| `36` Why Agents? LLM Limitations in the Enterprise | Deck 1. One-line recap in deck 4 |
| `55` Embeddings and Vector Search | Deck 4 |
| `83` From Documents to Searchable Chunks | Deck 4 |
| `112` From Chunks to Graph Structure | Deck 4 |
| `145` What the Knowledge Graph Contains | Deck 4 |
| `174` GraphRAG: Graph-Enriched Retrieval | Deck 4 |
| `218` Beyond GraphRAG: Reaching the Lakehouse | Deck 8 |
| `241` Specialized Agents for Different Data Structures | Deck 8 |
| `267` Databricks Genie: Natural Language to SQL | Deck 8 |
| `300` Neo4j Graph Agent: Natural Language to Cypher | Deck 8 |
| `326` How the Graph Agent Reaches Neo4j | Deck 8 |
| `355` Neo4j MCP Tools | Deck 8, verbatim, already use case neutral |
| `383` Multi-Agent Supervisor: Routing to the Right Platform | Deck 8 |
| `408` The Intelligence Platform Is Active | Dropped. Closing slide for a deck that no longer exists |

The deck 4 block is AML flavored. Slide `145` draws `(:Regulation) (:Threshold) (:Procedure)` cross-linked to `(:Account)-[:TRANSFERRED_TO]->(:Account)`. The aircraft target is already established at `agents/03:153`: `(:Document)-[:APPLIES_TO]->(:Aircraft)-[:HAS_SYSTEM]->(:System)` beneath the same Chunk and NEXT_CHUNK layer. Same diagram shape, mechanical swap. Deck 8 slides `267` through `383` are platform mechanics rather than use case and carry over with light edits. Slides `218` and `241` are the fraud-framed pair.

#### Unused Assets to Adopt

`slides/aircraft/` holds six SVGs that no deck references today. Deck 3 needed diagrams drawn, and five of them already exist in the right use case.

| Asset | Lands |
|-------|-------|
| `aircraft-digital-twin-property-graph.svg` | Deck 3, the nodes and relationships slide |
| `knowledge-graph-structure.svg` | Deck 3, the schema slide |
| `step1-flat-tables-foreign-keys.svg`, `step2-spark-connector-mapping.svg`, `step3-connected-graph.svg` | Deck 3, a three-slide tables-become-graphs sequence |
| `graphrag-retrieval-flow.svg` | Deck 4, replacing the portfolio version both `graph-ml/` decks use |

`databricks-in-depth/spark-connector-virtual-graph.png` is untracked and needs a `git add`. It shows the Virtual Graph and composite graphs, which no lab builds, so deck 2 should frame it as where the pattern goes in production rather than as workshop architecture.

#### Loss Audit

Every slide in the deleted deck, and where it went.

| Dropped from `platform-overview/03` | Verdict |
|---|---|
| Better Together, Data Intelligence Meets Graph Intelligence, the two platform slides | Covered. `platform-overview/02` carries "Why Combine" and "What Each Platform Brings", both bound for deck 2 |
| Building the Intelligence Platform, line 142 | Covered by the deck 2 architecture slide |
| ELT: Lakehouse to Graph, Raw Data to Governed Delta, The Neo4j Spark Connector, Loading the Graph, Validation Through Spark Reads | Covered. The `platform-overview/02` appendix carries "Tables Become Graphs" and "The Neo4j Spark Connector", both bound for deck 3. The load and validate code is Lab 2 notebook material |
| Graph Insights Flow Back to the Lakehouse | Covered by `graph-ml/03` and `04`, which are shelved rather than deleted |
| Financial fraud: working example, fraud ring, graph components, transaction tables to fraud graph, synthetic identity, first-party rings, bust-out | Dropped deliberately. This is the use case mismatch being removed |
| Debugging: When Relationships Fail to Create | Dropped. Lab 2 troubleshooting belongs in the site docs, not a deck |
| Decision framework appendices, lines 568 and 589 | Rescued by salvage item 6 |

Image check: both images the deleted deck references survive. `spark-connector-virtual-graph.png` moves to deck 2, and `fraud-ring-dual-architecture.svg` is still referenced at `background/governance/auth-sync-slides.md:183`. No orphans.

Final tally: 21 slide files in, 8 workshop decks and 7 background decks out. One file deleted, 32 of its 38 slides dropped on purpose.

#### Build and Docs Changes

- **`build-slides.sh`:** `WORKSHOP_TOPICS` becomes the eight `overview-*` folder names. `background` gains `agents/` and `graph-ml/` subdirectories, which Marp already recurses into. `copy_assets` gains `slides/aircraft/`, which no deck reaches today.
- **Deck depth:** the shelved `graph-ml/` decks emit one directory deeper once under `background/`, so their `../databricks-in-depth/` reference needs a third dot segment. See the depth note at the top of `build-slides.sh`.
- **`README.md`:** the Slide Decks section is rewritten to list the eight decks in run of show order with a one-line description each.
- **Gallery:** the sibling workshop generates `build/index.html` from a deck list in `scripts/build-slides.mjs` holding a title and description per deck. That gallery is the artifact this reorganization is modeled on. Adding one here is optional and out of scope for Phase 7, since this repository publishes through Antora instead.

**Done when:** Eight `overview-*` folders exist with one deck each, `platform-overview/03` is deleted with all six salvage items placed, the three shelved files sit under `background/`, `build-slides.sh` and `README.md` match the new layout, and every deck builds with no broken image links.

---

## Ways to Further Organize the Slides

### 1. By Audience and Delivery Context

The decks currently mix workshop instruction, webinar content, and deep technical reference. Tagging each file by its intended delivery context would help clarify what gets used when:

- **Workshop labs**: `platform-overview/`, `genai-foundations/`, `kg-construction/`, `retrieval-patterns/`, `agents/`
- **Webinar / conference talks**: `platform-overview/03-intro-databricks-neo4j-slides.md`, `agents/02-power-of-graphrag-slides.md`, `graph-ml/03-graph-enrichment-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md`
- **Internal / partner deep dives**: `background/governance/auth-sync-slides.md`
- **Background, kept but off the workshop path**: `background/kg-construction/05-building-knowledge-graphs-slides.md`, `background/kg-construction/06-schema-design-slides.md`, `background/kg-construction/08-entity-resolution-slides.md`

The `background/` folder is this idea already partly acted on: the decks under it are maintained but not delivered in the workshop run.

### 2. By Topic Cluster

A natural grouping by subject area:

| Cluster | Files |
|---------|-------|
| Data Engineering | `platform-overview/03-intro-databricks-neo4j-slides.md`, Medallion Architecture, Spark Connector, incremental sync |
| GenAI Foundations | `genai-foundations/02-genai-and-limitations-slides.md`, `genai-foundations/03-traditional-rag-slides.md`, `genai-foundations/04-context-and-rag-slides.md` |
| Knowledge Graph Construction | `background/kg-construction/05-building-knowledge-graphs-slides.md`, `background/kg-construction/06-schema-design-slides.md`, `kg-construction/07-chunking-slides.md`, `background/kg-construction/08-entity-resolution-slides.md`, `kg-construction/09-vectors-slides.md` |
| Retrieval and Agents | `retrieval-patterns/01`-`04`, `agents/01-from-retrievers-to-agents-slides.md` |
| Multi-Agent Architecture | `agents/02-power-of-graphrag-slides.md`, `agents/03-langgraph-supervisor-slides.md`, `agents/04-deploy-the-agent-slides.md`, `platform-overview/02-databricks-neo4j-integration-slides.md` (agent sections) |
| Graph ML and Feature Engineering | `graph-ml/03-graph-enrichment-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md` |
| Governance | `background/governance/auth-sync-slides.md` |

### 3. By Depth Level

- **Level 1 (conceptual)**: `platform-overview/02-databricks-neo4j-integration-slides.md`, `platform-overview/01-workshop-overview-slides.md`, `platform-overview/04-neo4j-aura-overview-slides.md`, `genai-foundations/02-genai-and-limitations-slides.md`
- **Level 2 (practitioner)**: `genai-foundations/03`, `04`, `kg-construction/`, `background/kg-construction/`, `retrieval-patterns/`, `agents/01`, `agents/03`, `agents/04`
- **Level 3 (technical deep dive)**: `platform-overview/03-intro-databricks-neo4j-slides.md`, `agents/02-power-of-graphrag-slides.md`, `graph-ml/03`, `graph-ml/04`, `background/governance/auth-sync-slides.md`

### 4. Redundancy Audit

Several topics appear in multiple decks with slightly different framing. A redundancy pass would identify which version to keep as the canonical source and which to remove or consolidate:

- GraphRAG: covered in `agents/02-power-of-graphrag-slides.md`, `genai-foundations/04-context-and-rag-slides.md`, `platform-overview/02-databricks-neo4j-integration-slides.md`
- Multi-agent supervisor: covered in `agents/02-power-of-graphrag-slides.md`, `agents/03-langgraph-supervisor-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md`, `platform-overview/02-databricks-neo4j-integration-slides.md`
- Spark Connector: covered in `platform-overview/03-intro-databricks-neo4j-slides.md`, `graph-ml/03-graph-enrichment-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md`, `platform-overview/02-databricks-neo4j-integration-slides.md`
- Graph feature engineering enrichment loop: overlaps between `graph-ml/03-graph-enrichment-slides.md` and `graph-ml/04-future-graph-enrichment-slides.md`

### 5. Sequential Story Arc

The decks do not currently share a single narrative spine. Mapping them to a learning path would reveal gaps and ordering issues:

```
Why graphs? → What is Neo4j Aura? → Why LLMs fail alone? → Traditional RAG →
Context ROT → GraphRAG solution → Building KGs → Schema → Chunking →
Entity Resolution → Vectors → Retrievers → Agents → Multi-agent systems →
LangGraph supervisor → Deployment → Agent memory →
Graph ML → Enrichment loops → Authorization
```

Building KGs, Schema, Entity Resolution and Authorization now sit under `background/`, so the workshop run skips them and the spine above is the full-library arc rather than the delivered one. Agent memory has no deck yet.

Checking whether any slide deck assumes knowledge not yet introduced would identify sequencing problems.

### 6. Use Case Coverage

The current decks use three use cases: aircraft digital twins across the workshop path, financial fraud in `platform-overview/03-intro-databricks-neo4j-slides.md` and `agents/02-power-of-graphrag-slides.md`, and portfolios and asset managers in both `graph-ml/` decks. Mapping which topics are demonstrated with which use case, and which topics have no concrete example, would surface gaps where a worked example would help.
