# Slides Organization

## Key Topics Summary

* **Databricks + Neo4j Dual-Database Architecture**: Why the two platforms complement each other. Databricks handles large-scale tabular analytics and ML; Neo4j handles relationship traversal and pattern matching. Together they cover questions that neither can answer alone. Covered in: `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md`, `databricks-in-depth/01-intro-databricks-neo4j-slides.md`, `overview-knowledge-graph/01-workshop-over.md`

* **Neo4j Graph Fundamentals**: Nodes, relationships, and properties as the building blocks of a property graph. Cypher as the query language for pattern matching. Why multi-hop traversals are faster in a graph than in SQL with recursive joins. Covered in: `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md`, `overview-knowledge-graph/01-neo4j-aura-overview-slides.md`

* **Neo4j Aura**: The fully managed cloud version of Neo4j, available on AWS, GCP, and Azure. Includes tools for querying, visual exploration, and dashboards, plus Aura Agents for no-code conversational interfaces. Covered in: `overview-knowledge-graph/01-neo4j-aura-overview-slides.md`

* **Medallion Architecture**: Databricks data organization pattern with three layers. Bronze holds raw data. Silver holds cleaned, governed tables. Gold holds analytics-ready outputs enriched by graph insights. Covered in: `databricks-in-depth/01-intro-databricks-neo4j-slides.md`

* **Neo4j Spark Connector**: The official bidirectional bridge between Databricks Delta tables and Neo4j. Rows become nodes; foreign keys become relationships. Also reads graph data back into DataFrames for analytics and ML. Covered in: `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md`, `databricks-in-depth/01-intro-databricks-neo4j-slides.md`

* **LLM Limitations**: Three core problems with using LLMs alone for enterprise data. Hallucination produces confident but wrong answers. Knowledge cutoff means the model cannot access private or recent data. Relationship blindness means the model cannot reason across connected information. Covered in: `overview-knowledge-graph/02-genai-and-limitations-slides.md`, `databricks-in-depth/02-power-of-graphrag-slides.md`

* **Traditional RAG**: Retrieval-Augmented Generation as the baseline approach to grounding LLM responses. Documents are split into chunks, embedded as vectors, and retrieved by semantic similarity. Covered in: `overview-knowledge-graph/03-traditional-rag-slides.md`

* **Context ROT**: The finding that too much irrelevant context degrades LLM accuracy. Similarity search retrieves related but not necessarily relevant chunks, filling the context window with noise. Covered in: `overview-knowledge-graph/04-context-and-rag-slides.md`

* **GraphRAG**: Graph-enhanced retrieval that combines vector similarity search with graph traversal. Vector search finds the most relevant chunks; graph traversal follows extracted entities and relationships from those chunks to gather richer, structured context. Covered across: `overview-databricks-neo4j/01-...`, `databricks-in-depth/02-power-of-graphrag-slides.md`, `overview-knowledge-graph/04-context-and-rag-slides.md`, `databricks-in-depth/03-graph-enrichment-slides.md`

* **Knowledge Graph Construction**: The pipeline for turning unstructured documents into a structured graph. Steps are: chunk documents, embed chunks, extract entities with an LLM, resolve duplicate entities, and cross-link to the operational graph. Covered in: `overview-knowledge-graph/05-building-knowledge-graphs-slides.md`, `databricks-in-depth/02-power-of-graphrag-slides.md`

* **SimpleKGPipeline**: The `neo4j-graphrag-python` library class that orchestrates the full knowledge graph construction pipeline. Accepts schema, LLM, embedder, and text splitter configuration. Covered in: `overview-knowledge-graph/05-building-knowledge-graphs-slides.md`, `overview-knowledge-graph/06-schema-design-slides.md`

* **Schema Design**: Defining which node types, relationship types, and valid patterns to extract from documents. Three modes: user-provided for production, extracted for exploration, free for initial discovery. Covered in: `overview-knowledge-graph/06-schema-design-slides.md`

* **Chunking Strategies**: How document splitting affects both entity extraction quality and retrieval precision. Larger chunks give the LLM more context for extraction; smaller chunks give retrieval more precision. Chunk overlap preserves context at boundaries. Covered in: `overview-knowledge-graph/07-chunking-slides.md`

* **Entity Resolution**: Merging duplicate nodes that represent the same real-world entity extracted under different names. Strategies include upstream normalization via prompt engineering, canonical reference lists, and post-processing fuzzy or semantic resolvers. Covered in: `overview-knowledge-graph/08-entity-resolution-slides.md`

* **Vectors and Embeddings**: Numerical representations of text meaning as high-dimensional vectors. Similar meanings produce similar vectors, enabling semantic search. Neo4j stores embeddings as node properties and indexes them for fast similarity queries. Covered in: `overview-knowledge-graph/09-vectors-slides.md`

* **Vector Retriever**: The simplest GraphRAG retriever. Converts a question to an embedding and returns the most semantically similar chunks from the vector index. Best for exploratory, conceptual questions. Covered in: `overview-retrievers/02-vector-retriever-slides.md`

* **Vector Cypher Retriever**: Combines vector similarity search with a custom Cypher traversal. Vector search finds relevant chunks; the Cypher query traverses from those chunks to related entities and relationships in the graph. Best for questions that need both content and structured data. Covered in: `overview-retrievers/03-vector-cypher-retriever-slides.md`

* **Text2Cypher Retriever**: An LLM converts a natural language question directly into a Cypher query, which executes against the graph and returns precise structured results. Best for counts, lists, and entity-specific facts. Covered in: `overview-retrievers/04-text2cypher-retriever-slides.md`

* **ReAct Pattern and Agents**: The Reasoning and Acting loop that AI agents follow: receive a question, reason about which tool fits, execute the tool, observe the result, respond. Retrievers become tools agents can select automatically based on question type. Covered in: `overview-retrievers/08-from-retrievers-to-agents-slides.md`

* **Genie Space**: Databricks' natural language to SQL system. Translates plain English questions into governed SQL queries against Delta Lake tables registered in Unity Catalog. One of two specialized agents in the multi-agent architecture. Covered in: `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md`, `databricks-in-depth/02-power-of-graphrag-slides.md`

* **Neo4j MCP Server**: Exposes Neo4j as agent tools via the Model Context Protocol. Tools include schema discovery, read-only Cypher execution, and GDS procedure listing. Allows any agent framework to query the graph without pre-built integrations. Covered in: `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md`, `databricks-in-depth/02-power-of-graphrag-slides.md`

* **Multi-Agent Supervisor**: A coordinator agent that routes questions to specialized agents based on the nature of the question. Numbers and trends go to Genie; relationships and structure go to the Neo4j MCP agent; questions that need both get decomposed and sent to each. Covered in: `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md`, `databricks-in-depth/02-power-of-graphrag-slides.md`, `databricks-in-depth/04-future-graph-enrichment-slides.md`

* **Graph Data Science (GDS)**: Neo4j's library of 65+ graph algorithms organized into centrality, community detection, similarity, pathfinding, and node embedding categories. Algorithms run on in-memory graph projections and results write back to the database as node properties. Covered in: `databricks-in-depth/03-graph-enrichment-slides.md`

* **Graph Feature Engineering**: Using GDS algorithms to generate ML features from graph topology. FastRP produces node embedding vectors. PageRank scores influence. Louvain assigns community membership. These features combine with tabular data in a feature table for classifier training. Covered in: `databricks-in-depth/03-graph-enrichment-slides.md`, `databricks-in-depth/04-future-graph-enrichment-slides.md`

* **MLflow Experiment Tracking**: Used to compare classifiers trained with tabular features alone against classifiers trained with graph features added. Quantifies the accuracy lift that graph topology contributes over flat table data. Covered in: `databricks-in-depth/03-graph-enrichment-slides.md`

* **Agentic Graph Enrichment**: A cyclic pipeline where agents compare graph contents against unstructured documents to detect missing relationships, propose enrichments with confidence scores, validate against the existing schema, and write approved relationships back to the graph. Each cycle changes what algorithms compute and what the next cycle discovers. Covered in: `databricks-in-depth/04-future-graph-enrichment-slides.md`

* **Incremental Sync with Change Data Feed**: Keeping Neo4j and Databricks aligned without full reloads. Delta Lake's Change Data Feed captures only changed rows; a Spark Structured Streaming job pushes deltas to Neo4j via the Spark Connector. Costs stay proportional to change volume. Covered in: `databricks-in-depth/03-graph-enrichment-slides.md`, `databricks-in-depth/04-future-graph-enrichment-slides.md`

* **Neo4j as a Semantic Layer**: Syncing Unity Catalog metadata into Neo4j so business concepts connect to physical tables and columns as a traversable graph. Improves data discovery and boosts text-to-SQL accuracy by giving agents structured domain context. Covered in: `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md`

* **Authorization Sync**: Patterns for aligning access privileges between Unity Catalog and Neo4j when both systems hold overlapping data. Four approaches: shared identity provider, shared IdP plus a semantic layer, UC as source of truth pushing to Neo4j, and Neo4j as source of truth pushing to UC. Covered in: `databricks-in-depth/auth-sync-slides.md`

* **Aircraft Digital Twin**: The workshop's running use case. A fleet of 20 aircraft modeled in both Neo4j and Databricks, with topology and maintenance in Neo4j and time-series sensor telemetry in Databricks. Illustrates the dual-database pattern with real query examples. Covered in: `overview-knowledge-graph/01-workshop-over.md`, `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md`

* **Financial Fraud Detection**: The secondary running use case in the deeper technical decks. Money laundering through circular account transfers illustrates why graph traversal outperforms recursive SQL for multi-hop connection queries. Covered in: `databricks-in-depth/01-intro-databricks-neo4j-slides.md`, `databricks-in-depth/auth-sync-slides.md`

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

**Status: Complete** — see File Inventory section below.

**Goal:** Every slide file has a written label stating its topic cluster, audience level, and primary use case example.

- Read each slide file and write a one-line label for it: topic cluster, depth level (overview / practitioner / deep dive), and which use case it uses (aircraft, fraud, portfolio, generic).
- Record the labels in a simple table in this file under a new section called "File Inventory."
- Flag any file that does not fit cleanly into one topic cluster.

**Done when:** Every non-empty `.md` slide file under `slides/` (excluding `node_modules/`) has a row in the File Inventory table.

---

### Phase 2: Decide the Target Folder Structure

**Status: Complete** — see Target Structure section below.

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
7. Governance and integration (auth sync, JDBC federation, semantic layer)

**Done when:** The Target Structure section lists every proposed folder with its canonical file and lists which existing files are redundant for that folder.

---

### Phase 3: Consolidate Redundant Files

**Status: Complete** — SUMMARY.md marked redundant. All five multi-cluster files reviewed; no content merging needed.

**Goal:** Each topic has exactly one canonical slide file. Redundant files are either merged into the canonical file or marked for deletion.

- For each topic with more than one file, compare the versions side by side. Identify any content in the non-canonical versions that is not in the canonical version.
- If unique content exists in a non-canonical file, move that content into the canonical file.
- If a non-canonical file has nothing unique, mark it for deletion.
- Do not delete files yet. Add a `# REDUNDANT - merge complete` comment at the top of files marked for removal.

**Done when:** Every topic cluster has a single canonical file. No unique content remains in files marked redundant.

**Findings:**

| File | Action | Reason |
|------|--------|--------|
| `overview-databricks-neo4j/SUMMARY.md` | Marked redundant | Every section is covered by `01-databricks-neo4j-integration-slides.md`, which has additional appendix content. Nothing unique in SUMMARY.md. |
| `databricks-in-depth/01-intro-databricks-neo4j-slides.md` | No action | Canonical for platform-overview (fraud lens). Cross-cluster governance content (JDBC) is not covered by auth-sync-slides; stays in file. |
| `databricks-in-depth/02-power-of-graphrag-slides.md` | No action | Canonical for agents. LLM limitations intro is two slides, fully covered by `overview-knowledge-graph/02-genai-and-limitations-slides.md`. No merge needed. |
| `databricks-in-depth/04-future-graph-enrichment-slides.md` | No action | Canonical for graph ML. Agents content is application-specific to enrichment; not a duplicate of any agents canonical. |
| `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md` | No action | Canonical for platform-overview (aircraft lens). Cross-cluster content (semantic layer, JDBC, MCP overview) is complementary to dedicated canonicals, not duplicative. |
| `docs/overview-and-genai-foundations.md` | No action | Reference doc kept as-is per Phase 2 decision. Different delivery format; content mirrored by Marp files. |

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
| Dual-database architecture | `platform-overview/01-workshop-over.md`, `01-databricks-neo4j-integration-slides.md`, `01-intro-databricks-neo4j-slides.md` |
| Neo4j graph fundamentals (nodes, Cypher) | `01-databricks-neo4j-integration-slides.md`, `01-intro-databricks-neo4j-slides.md` |
| Neo4j Aura | `01-neo4j-aura-overview-slides.md` |
| Medallion Architecture | `01-intro-databricks-neo4j-slides.md` |
| Neo4j Spark Connector | `01-databricks-neo4j-integration-slides.md` (appendix), `01-intro-databricks-neo4j-slides.md` |
| LLM limitations | `genai-foundations/02-genai-and-limitations-slides.md`, `agents/02-power-of-graphrag-slides.md` |
| Traditional RAG | `genai-foundations/03-traditional-rag-slides.md` |
| Context ROT | `genai-foundations/04-context-and-rag-slides.md` |
| GraphRAG | `01-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md`, `04-context-and-rag-slides.md`, `graph-ml/03-graph-enrichment-slides.md` |
| Knowledge graph construction | `kg-construction/05-building-knowledge-graphs-slides.md`, `agents/02-power-of-graphrag-slides.md` |
| SimpleKGPipeline | `kg-construction/05-building-knowledge-graphs-slides.md`, `06-schema-design-slides.md` |
| Schema design | `kg-construction/06-schema-design-slides.md` |
| Chunking strategies | `kg-construction/07-chunking-slides.md` |
| Entity resolution | `kg-construction/08-entity-resolution-slides.md` |
| Vectors and embeddings | `kg-construction/09-vectors-slides.md` |
| Vector Retriever | `retrieval-patterns/02-vector-retriever-slides.md` |
| Vector Cypher Retriever | `retrieval-patterns/03-vector-cypher-retriever-slides.md` |
| Text2Cypher Retriever | `retrieval-patterns/04-text2cypher-retriever-slides.md` |
| ReAct pattern and agents | `agents/08-from-retrievers-to-agents-slides.md` |
| Genie Space | `01-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md` |
| Neo4j MCP Server | `01-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md` |
| Multi-agent supervisor | `01-databricks-neo4j-integration-slides.md`, `agents/02-power-of-graphrag-slides.md`, `graph-ml/04-future-graph-enrichment-slides.md` |
| Graph Data Science (GDS) | `01-neo4j-aura-overview-slides.md` (brief), `graph-ml/03-graph-enrichment-slides.md` |
| Graph feature engineering | `graph-ml/03-graph-enrichment-slides.md`, `04-future-graph-enrichment-slides.md` |
| MLflow experiment tracking | `graph-ml/03-graph-enrichment-slides.md` |
| Agentic graph enrichment | `graph-ml/04-future-graph-enrichment-slides.md` |
| Incremental sync with Change Data Feed | `graph-ml/03-graph-enrichment-slides.md`, `04-future-graph-enrichment-slides.md` |
| Neo4j as semantic layer | `01-databricks-neo4j-integration-slides.md`, `governance/auth-sync-slides.md` |
| Authorization sync | `governance/auth-sync-slides.md` |
| Aircraft digital twin | `platform-overview/01-workshop-over.md`, `01-databricks-neo4j-integration-slides.md` |
| Financial fraud detection | `platform-overview/01-intro-databricks-neo4j-slides.md`, `governance/auth-sync-slides.md` |

---

#### Issues Found Per Cluster

**platform-overview/**

1. **Stale title in `01-neo4j-aura-overview-slides.md`**: The first content slide reads `# GraphRAG Agent Blueprint with AWS`. The content of the file is about Neo4j Aura tools, not AWS or GraphRAG agents. This title is a leftover from a previous version of the deck and will confuse readers.

2. **Four files share the `01-` prefix**: `01-databricks-neo4j-integration-slides.md`, `01-intro-databricks-neo4j-slides.md`, `01-neo4j-aura-overview-slides.md`, and `01-workshop-over.md` all sort together. No clear primary file for the cluster.

**genai-foundations/**

3. **Sequence assumptions in `03-traditional-rag-slides.md`**: The second slide opens with "Remember the LLM limitations we discussed:" This assumes the reader has already seen `02-genai-and-limitations-slides.md`. The file does not stand alone as written.

4. **Sequence assumption in `04-context-and-rag-slides.md`**: Opens with "We've seen how RAG provides context to LLMs:" Assumes the reader has seen `03-traditional-rag-slides.md`. Both issues are acceptable for workshop delivery but make the files harder to use independently.

**retrieval-patterns/**

5. **Use case mismatch across all four files**: All files in `retrieval-patterns/` use a finance and investment use case (Companies, RiskFactors, AssetManagers, Apple, BlackRock). The rest of the workshop uses the aircraft digital twin. A participant moving from `kg-construction/` to `retrieval-patterns/` encounters a complete change of domain without explanation.

**agents/**

6. **Stale "Next" pointer in `08-from-retrievers-to-agents-slides.md`**: The final summary slide reads "Next: Learn about the Microsoft Agent Framework." There is no Microsoft Agent Framework anywhere in the workshop materials. This pointer should be removed or updated to reference the multi-agent supervisor content.

7. **Numeric sort order inverts logical order**: `02-power-of-graphrag-slides.md` sorts before `08-from-retrievers-to-agents-slides.md` in a directory listing, but conceptually `08` (ReAct fundamentals) is the entry point and `02` (Genie, MCP, supervisor) is the follow-up.

8. **Use case mismatch with other agents content**: `08-from-retrievers-to-agents-slides.md` uses the finance use case. `02-power-of-graphrag-slides.md` uses fraud. Neither matches the aircraft digital twin used in the rest of the workshop.

**graph-ml/**

9. **Webinar recap slides**: Both files open with a "Partnership Overview and Recap" section listing joint customers (Gilead, iFord, Comcast, Ashley Furniture). These slides are appropriate for a live webinar audience needing context refreshed, but add noise when the files are read in a slide library context.

10. **Content overlap on incremental sync**: Both `03-graph-enrichment-slides.md` and `04-future-graph-enrichment-slides.md` cover Change Data Feed and the bi-directional loop pattern with similar slides. The overlap is moderate, not a duplication problem, but a reader studying both files will encounter the same material twice.

---

#### What Is Missing

Gaps confirmed from Phase 2 and newly identified in this review:

**Confirmed gaps from Phase 2:**
- No standalone introduction to JDBC federation as a topic. `governance/auth-sync-slides.md` opens with a JDBC federation status update but it is a partner/internal briefing, not a teaching deck.
- Databricks Vector Search as an external vector store option. Mentioned briefly in `01-databricks-neo4j-integration-slides.md` (one slide) but not developed.
- Genie Space setup and configuration steps. Covered in workshop notebooks, not in slides.

**New gaps identified in Phase 5:**
- No slide covering the `GraphRAG` orchestration class from `neo4j-graphrag-python`. The class is mentioned in `01-retrievers-overview-slides.md` with a diagram but not explained or demonstrated in code.
- No dedicated treatment of Aura Agents beyond the summary bullet in `01-neo4j-aura-overview-slides.md`. The feature has enough depth to warrant one or two focused slides.
- No slide on LangGraph or any other agent framework. The agents cluster explains the ReAct pattern and the Databricks-specific multi-agent architecture but does not discuss how to implement the Neo4j agent using a framework.

**What is not a gap:** The retrieval-patterns and agents/08 use case mismatch (finance vs. aircraft) is a coherence issue, not a content gap. The concepts are fully covered; the examples just use a different domain.

---

## File Inventory

Phase 1 complete. Every `.md` file under `slides/` (excluding `node_modules/` and this file) has a row below with its format, topic cluster, depth level, and primary use case. Files marked with * span more than one cluster.

**Format:** Marp = presentation slide deck | Reference = participant reference doc, no Marp | Outline = planning or narrative arc, not a deliverable slide deck | Admin = README or meta doc

**Depth:** overview | practitioner | deep dive | — (not applicable)

| File | Format | Topic Cluster | Depth | Use Case | Notes |
|------|--------|---------------|-------|----------|-------|
| `README.md` | Admin | meta | — | — | Build and usage instructions for the slides directory. Not a slide file. |
| `databricks-in-depth/01-intro-databricks-neo4j-slides.md` | Marp | platform overview * | deep dive | fraud | * Also covers governance (Spark Connector, bidirectional data flow) and knowledge graph construction (graph modeling decisions). Fraud and portfolio lens; distinct from the aircraft angle of other platform files. |
| `databricks-in-depth/02-power-of-graphrag-slides.md` | Marp | agents and multi-agent systems * | deep dive | aircraft | * Also covers GenAI foundations (LLM limitations). Most detailed treatment of Genie, Neo4j MCP, and the multi-agent supervisor. |
| `databricks-in-depth/03-graph-enrichment-slides.md` | Marp | graph ML and enrichment | deep dive | portfolio | GDS algorithms, feature engineering, MLflow lift comparison, bidirectional data loop, incremental sync with Change Data Feed. |
| `databricks-in-depth/04-future-graph-enrichment-slides.md` | Marp | graph ML and enrichment * | deep dive | portfolio | * Also covers agents (agentic enrichment loop, multi-agent supervisor for gap detection). Overlaps with 03 on incremental sync. |
| `databricks-in-depth/auth-sync-slides.md` | Marp | governance and integration | deep dive | generic | Unique content: four authorization sync patterns between Unity Catalog and Neo4j, plus the semantic layer data model. No substantial overlap with other files. |
| `databricks-in-depth/slides.md` | Outline | graph ML and enrichment | — | portfolio | Narrative arc and section flow notes for the graph enrichment portion of the databricks-in-depth deck. Not a deliverable slide file. |
| `docs/building-knowledge-graphs.md` | Reference | knowledge graph construction | practitioner | aircraft | Participant reference doc combining content from overview-knowledge-graph/05 through 09. Content is covered by those five Marp files; this serves a different delivery format. |
| `docs/overview-and-genai-foundations.md` | Reference | GenAI foundations * | overview / practitioner | aircraft | * Also covers platform overview (workshop overview, digital twin). Participant reference doc combining content from 01-workshop-over, 02, 03, and 04. Serves a different delivery format than those four Marp files. |
| `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md` | Marp | platform overview * | overview | aircraft | * Also covers agents (MCP, multi-agent supervisor) and governance (semantic layer, JDBC federation). Most complete single-file overview of the full partnership. |
| `overview-databricks-neo4j/SUMMARY.md` | Reference | platform overview | overview | aircraft | Condensed plain-text summary of 01-databricks-neo4j-integration-slides.md. No unique content. Redundant. |
| `overview-knowledge-graph/01-neo4j-aura-overview-slides.md` | Marp | platform overview | overview | generic | Neo4j Aura managed cloud: Explore tool, Query Workspace, Dashboards, Aura Agents for no-code GraphRAG. No substantial overlap with other files. |
| `overview-knowledge-graph/01-workshop-over.md` | Marp | platform overview | overview | aircraft | Workshop opener: digital twin definition, dataset stats, dual-database architecture, shared vs personal infrastructure. Distinct role as the workshop entry point. |
| `overview-knowledge-graph/02-genai-and-limitations-slides.md` | Marp | GenAI foundations | overview | generic | LLM strengths and three core limitations (hallucination, knowledge cutoff, relationship blindness). Clean standalone file. |
| `overview-knowledge-graph/03-traditional-rag-slides.md` | Marp | GenAI foundations | overview | generic | RAG motivation, embeddings as smart librarian analogy, retrieval flow. Clean standalone file. |
| `overview-knowledge-graph/04-context-and-rag-slides.md` | Marp | GenAI foundations | practitioner | aircraft | Context ROT, questions RAG cannot answer, GraphRAG solution with three retrieval patterns. Bridges GenAI foundations to knowledge graph construction. |
| `overview-knowledge-graph/05-building-knowledge-graphs-slides.md` | Marp | knowledge graph construction | practitioner | aircraft | neo4j-graphrag package, SimpleKGPipeline, aircraft digital twin graph structure. Entry point for the KG construction sequence. |
| `overview-knowledge-graph/06-schema-design-slides.md` | Marp | knowledge graph construction | practitioner | aircraft | Three schema modes, node type definitions, relationship patterns, workshop schema table. |
| `overview-knowledge-graph/07-chunking-slides.md` | Marp | knowledge graph construction | practitioner | generic | Chunk size trade-off, FixedSizeSplitter parameters, typical size ranges, evaluation Cypher queries. |
| `overview-knowledge-graph/08-entity-resolution-slides.md` | Marp | knowledge graph construction | practitioner | aircraft | Duplicate entity problem, three resolution strategies, FuzzyMatchResolver example. |
| `overview-knowledge-graph/09-vectors-slides.md` | Marp | knowledge graph construction | practitioner | generic | Embeddings definition, cosine similarity, storing vectors in Neo4j, combining with graph traversal. |
| `overview-retrievers/01-retrievers-overview-slides.md` | Marp | retrieval patterns | practitioner | aircraft | Three retriever types, GraphRAG class pipeline, decision framework table. |
| `overview-retrievers/02-vector-retriever-slides.md` | Marp | retrieval patterns | practitioner | aircraft | VectorRetriever creation, similarity score ranges, top_k parameter, limitations. |
| `overview-retrievers/03-vector-cypher-retriever-slides.md` | Marp | retrieval patterns | practitioner | aircraft | Two-step vector + Cypher process, retrieval_query with OPTIONAL MATCH, chunk as anchor concept. |
| `overview-retrievers/04-text2cypher-retriever-slides.md` | Marp | retrieval patterns | practitioner | aircraft | Text2CypherRetriever, schema role, security considerations, generated query quality. |
| `overview-retrievers/08-from-retrievers-to-agents-slides.md` | Marp | agents and multi-agent systems | practitioner | aircraft | Four agent components, tools, ReAct pattern, multi-tool example. Bridges the retrieval patterns cluster to agents. |

**Multi-cluster files (flagged for review in Phase 3):**

- `databricks-in-depth/01-intro-databricks-neo4j-slides.md`: platform overview + governance and integration + knowledge graph construction
- `databricks-in-depth/02-power-of-graphrag-slides.md`: agents and multi-agent systems + GenAI foundations
- `databricks-in-depth/04-future-graph-enrichment-slides.md`: graph ML and enrichment + agents and multi-agent systems
- `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md`: platform overview + agents and multi-agent systems + governance and integration
- `docs/overview-and-genai-foundations.md`: GenAI foundations + platform overview

---

## Target Structure

Phase 2 complete. Proposed topic-based folder layout with canonical files named per cluster and a list of redundant files.

### Proposed Folder Layout

```
slides/
  platform-overview/        (why Databricks + Neo4j, dual-database architecture, Neo4j Aura)
  genai-foundations/        (LLM limitations, traditional RAG, Context ROT)
  kg-construction/          (schema, chunking, entity resolution, vectors, SimpleKGPipeline)
  retrieval-patterns/       (Vector, Vector Cypher, Text2Cypher retrievers)
  agents/                   (ReAct, Genie, MCP, multi-agent supervisor)
  graph-ml/                 (GDS, feature engineering, enrichment loop, MLflow)
  governance/               (authorization sync, semantic layer, JDBC federation)
  docs/                     (keep as-is: participant reference docs, not Marp)
  README.md                 (update in Phase 4 to describe new layout)
  organize.md               (this file)
```

### Canonical Files per Cluster

| Cluster | File | Role |
|---------|------|------|
| platform-overview | `overview-databricks-neo4j/01-databricks-neo4j-integration-slides.md` | Most complete overview of the full partnership: dual-database, Spark Connector, GraphRAG, MCP, semantic layer, and multi-agent routing. Primary file for webinars and conference talks. |
| platform-overview | `overview-knowledge-graph/01-workshop-over.md` | Workshop entry point with digital twin definition, dataset stats, and shared vs personal infrastructure. Serves a different role than the file above; keep separately. |
| platform-overview | `overview-knowledge-graph/01-neo4j-aura-overview-slides.md` | Unique focus on the managed cloud product: Explore tool, Query Workspace, Dashboards, Aura Agents. No overlap with other platform files; keep separately. |
| platform-overview | `databricks-in-depth/01-intro-databricks-neo4j-slides.md` | Deeper engineering perspective through fraud and portfolio lens. Assign to platform-overview/ for now; spans multiple clusters, flag for potential split in a future phase. |
| GenAI foundations | `overview-knowledge-graph/02-genai-and-limitations-slides.md` | Standalone LLM limitations treatment. |
| GenAI foundations | `overview-knowledge-graph/03-traditional-rag-slides.md` | Standalone traditional RAG introduction. |
| GenAI foundations | `overview-knowledge-graph/04-context-and-rag-slides.md` | Context ROT and the case for GraphRAG. Bridges GenAI foundations to knowledge graph construction. |
| knowledge graph construction | `overview-knowledge-graph/05-building-knowledge-graphs-slides.md` | Entry point for the KG construction sequence: neo4j-graphrag package, SimpleKGPipeline. |
| knowledge graph construction | `overview-knowledge-graph/06-schema-design-slides.md` | Schema design. |
| knowledge graph construction | `overview-knowledge-graph/07-chunking-slides.md` | Chunking strategies. |
| knowledge graph construction | `overview-knowledge-graph/08-entity-resolution-slides.md` | Entity resolution. |
| knowledge graph construction | `overview-knowledge-graph/09-vectors-slides.md` | Vectors and embeddings. |
| retrieval patterns | `overview-retrievers/01-retrievers-overview-slides.md` | Retriever overview and decision framework. Entry point for the retrieval sequence. |
| retrieval patterns | `overview-retrievers/02-vector-retriever-slides.md` | Vector Retriever. |
| retrieval patterns | `overview-retrievers/03-vector-cypher-retriever-slides.md` | Vector Cypher Retriever. |
| retrieval patterns | `overview-retrievers/04-text2cypher-retriever-slides.md` | Text2Cypher Retriever. |
| agents and multi-agent systems | `overview-retrievers/08-from-retrievers-to-agents-slides.md` | ReAct pattern and agent fundamentals. Entry point for the agents cluster. |
| agents and multi-agent systems | `databricks-in-depth/02-power-of-graphrag-slides.md` | Genie, Neo4j MCP, and the multi-agent supervisor. Most detailed treatment. Spans GenAI foundations but the agent architecture is the primary content. |
| graph ML and enrichment | `databricks-in-depth/03-graph-enrichment-slides.md` | GDS algorithms, graph feature engineering, MLflow lift comparison, bidirectional data loop. |
| graph ML and enrichment | `databricks-in-depth/04-future-graph-enrichment-slides.md` | Agentic enrichment loop, confidence scoring, ontology validation. Spans agents cluster but graph ML is the primary content. |
| governance and integration | `databricks-in-depth/auth-sync-slides.md` | Four authorization sync patterns. Unique content; no overlap with other files. |

### Redundant Files

| File | Redundant Because | Proposed Action |
|------|-------------------|-----------------|
| `overview-databricks-neo4j/SUMMARY.md` | Condensed plain-text version of `01-databricks-neo4j-integration-slides.md`. No unique content. | Mark for deletion in Phase 3. |
| `databricks-in-depth/slides.md` | Narrative arc planning document, not a deliverable slide deck. No slide content to preserve. | Move to `docs/` during Phase 4; not a candidate for a topic folder. |

**Reference docs kept as-is (not moved to topic folders):**

| File | Kept Because |
|------|-------------|
| `docs/building-knowledge-graphs.md` | Participant reference format (no Marp). Serves a different delivery need than the five Marp files it mirrors. Content is preserved in those files. |
| `docs/overview-and-genai-foundations.md` | Same reasoning: reference format for a different delivery context than the four Marp files it mirrors. |

### Gaps Identified in Phase 2

No dedicated slide file exists for:
- JDBC federation and SQL-to-Cypher translation (mentioned in `overview-databricks-neo4j/01` but not developed as standalone slides)
- Databricks Vector Search as a pluggable external vector store (mentioned in one slide, not developed)
- Genie Space setup and configuration steps (covered in workshop notebooks, not in slides)

These are content gaps to address in a future content phase, not part of the reorganization.

---

---

### Phase 6: Fix Issues and Fill Gaps

**Status: In progress**

**Goal:** Address the 10 issues and 6 gaps documented in Phase 5.

**Fixing:**
- Stale title slide in `01-neo4j-aura-overview-slides.md`
- Stale "Next: Microsoft Agent Framework" pointer in `agents/08`
- Sequence-dependent openings in `genai-foundations/03` and `04`
- Use case mismatch in all four `retrieval-patterns/` files and `agents/08` (finance to aircraft)
- Sort order in `agents/` by renaming `08-from-retrievers-to-agents-slides.md` to `01-`
- Webinar partnership recap slides in `graph-ml/03` and `graph-ml/04`
- Gap: add `GraphRAG` class slides to `retrieval-patterns/01-retrievers-overview-slides.md`
- Gap: add Databricks Vector Search slide to `retrieval-patterns/01-retrievers-overview-slides.md`
- Gap: expand Aura Agents content in `platform-overview/01-neo4j-aura-overview-slides.md`

**Not fixing:**
- Four `01-` prefix files in `platform-overview/` — naming, not content; renaming would break history and links
- Content overlap on incremental sync in `graph-ml/` — editorial decision deferred
- LangGraph agent framework slides — insufficient workshop-specific content to write accurately
- JDBC federation standalone intro — content already covered in `governance/auth-sync-slides.md`
- Genie Space setup/configuration — covered in workshop notebooks, not slides

**Done when:** All items above marked complete. No new content errors introduced.

---

## Ways to Further Organize the Slides

### 1. By Audience and Delivery Context

The decks currently mix workshop instruction, webinar content, and deep technical reference. Tagging each file by its intended delivery context would help clarify what gets used when:

- **Workshop labs**: `overview-knowledge-graph/`, `overview-retrievers/`, `overview-databricks-neo4j/`
- **Webinar / conference talks**: `databricks-in-depth/01`, `02`, `03`, `04`
- **Internal / partner deep dives**: `databricks-in-depth/auth-sync-slides.md`

### 2. By Topic Cluster

A natural grouping by subject area:

| Cluster | Files |
|---------|-------|
| Data Engineering | `databricks-in-depth/01`, Medallion Architecture, Spark Connector, incremental sync |
| GenAI Foundations | `overview-knowledge-graph/02`, `03`, `04` |
| Knowledge Graph Construction | `overview-knowledge-graph/05`, `06`, `07`, `08`, `09` |
| Retrieval and Agents | `overview-retrievers/01`-`04`, `08` |
| Multi-Agent Architecture | `databricks-in-depth/02`, `overview-databricks-neo4j/01` (agent sections) |
| Graph ML and Feature Engineering | `databricks-in-depth/03`, `04` |
| Governance | `databricks-in-depth/auth-sync-slides.md` |

### 3. By Depth Level

- **Level 1 (conceptual)**: `overview-databricks-neo4j/01`, `overview-knowledge-graph/01-workshop-over`, `02`
- **Level 2 (practitioner)**: `overview-knowledge-graph/03`-`09`, `overview-retrievers/`
- **Level 3 (technical deep dive)**: `databricks-in-depth/01`-`04`, `auth-sync`

### 4. Redundancy Audit

Several topics appear in multiple decks with slightly different framing. A redundancy pass would identify which version to keep as the canonical source and which to remove or consolidate:

- GraphRAG: covered in `databricks-in-depth/02`, `overview-knowledge-graph/04`, `overview-databricks-neo4j/01`
- Multi-agent supervisor: covered in `databricks-in-depth/02`, `04`, `overview-databricks-neo4j/01`
- Spark Connector: covered in `databricks-in-depth/01`, `03`, `04`, `overview-databricks-neo4j/01`
- Graph feature engineering enrichment loop: overlaps between `03` and `04` in `databricks-in-depth/`

### 5. Sequential Story Arc

The decks do not currently share a single narrative spine. Mapping them to a learning path would reveal gaps and ordering issues:

```
Why graphs? → What is Neo4j Aura? → Why LLMs fail alone? → Traditional RAG →
Context ROT → GraphRAG solution → Building KGs → Schema → Chunking →
Entity Resolution → Vectors → Retrievers → Agents → Multi-agent systems →
Graph ML → Enrichment loops → Authorization
```

Checking whether any slide deck assumes knowledge not yet introduced would identify sequencing problems.

### 6. Use Case Coverage

The current decks use two primary use cases: aircraft digital twins and financial fraud detection. Mapping which topics are demonstrated with which use case, and which topics have no concrete example, would surface gaps where a worked example would help.
