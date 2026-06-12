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

**Goal:** Every slide file has a written label stating its topic cluster, audience level, and primary use case example.

- Read each slide file and write a one-line label for it: topic cluster, depth level (overview / practitioner / deep dive), and which use case it uses (aircraft, fraud, portfolio, generic).
- Record the labels in a simple table in this file under a new section called "File Inventory."
- Flag any file that does not fit cleanly into one topic cluster.

**Done when:** Every non-empty `.md` slide file under `slides/` (excluding `node_modules/`) has a row in the File Inventory table.

---

### Phase 2: Decide the Target Folder Structure

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

**Goal:** Each topic has exactly one canonical slide file. Redundant files are either merged into the canonical file or marked for deletion.

- For each topic with more than one file, compare the versions side by side. Identify any content in the non-canonical versions that is not in the canonical version.
- If unique content exists in a non-canonical file, move that content into the canonical file.
- If a non-canonical file has nothing unique, mark it for deletion.
- Do not delete files yet. Add a `# REDUNDANT - merge complete` comment at the top of files marked for removal.

**Done when:** Every topic cluster has a single canonical file. No unique content remains in files marked redundant.

---

### Phase 4: Move Files into Topic Folders

**Goal:** Files live under topic-named folders matching the Target Structure from Phase 2.

- Create the topic folders.
- Move each canonical file into its target folder.
- Update the README to reflect the new folder names and what belongs in each.
- Delete files marked redundant in Phase 3.

**Done when:** The folder structure matches the Target Structure. No slide files remain in the old delivery-context folders. The README describes the new layout.

---

### Phase 5: Walk Through and Validate

**Goal:** Confirm the reorganized slides tell a coherent story and nothing important was lost.

- Read through the canonical file for each topic cluster in the order listed in Phase 2.
- Check that each file can stand alone without assuming the reader has seen a previous deck.
- Note any topic from the Key Topics Summary above that no file covers adequately. Record these as gaps.
- Write a short "what is missing" list in this file.

**Done when:** Every topic cluster has been reviewed. Gaps are written down. No content from the original files has been silently lost.

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
