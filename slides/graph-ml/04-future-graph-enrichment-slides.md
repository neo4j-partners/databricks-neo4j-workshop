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

# Beyond Entity Extraction

Agentic Graph Enrichment with Neo4j and Databricks

---

---

# Why Standard KG Pipelines Are Not Enough

---

## Recap: The KG Construction Pipeline

```
Documents → Chunk → Embed → Extract Entities → Resolve → Cross-Link
```

- **Chunk and embed:** documents split into overlapping pieces, each embedded as a vector. A vector index enables semantic search across the corpus
- **Entity extraction:** an LLM reads each chunk and extracts structured nodes (regulations, thresholds, sectors). Entities link back to source chunks via FROM_CHUNK
- **Entity resolution:** the same entity mentioned in five chunks becomes one node with five links, not five duplicates
- **Cross-linking:** extracted entities connect to the operational graph built by the Spark Connector, bridging unstructured knowledge and structured data

<!--
Quick recap of the KG construction pipeline from the previous
session. Documents get split into chunks and embedded for vector
search. An LLM extracts structured entities from each chunk:
regulations, thresholds, procedures, sectors. Entity resolution
deduplicates so the same concept mentioned across multiple
documents becomes a single node with multiple provenance links.

Cross-linking is the step that connects the knowledge graph to
the operational graph. An extracted sector entity links to the
sector nodes that the Spark Connector built from Delta tables.
This is what makes GraphRAG traversals possible: vector search
finds relevant chunks, and graph traversal follows entities
through to the operational data.

This pipeline works well for what it does. The next slide shows
the resulting graph structure.
-->

---

## Graph-Enhanced Retrieval

![GraphRAG Retrieval Flow](../databricks-in-depth/graphrag-retrieval-flow.png)

- **Vector / fulltext search** finds the chunks closest in meaning to the question
- **Graph traversal** follows extracted entities and relationships from those chunks into the operational graph
- **Graph-enriched context** combines document text with structured data for the agent

<!--
Two layers in one graph. The top half is what KG construction
adds: documents split into chunks with embeddings for vector
search, and entities extracted from those chunks. The bottom half
is the operational graph the Spark Connector built from Delta
tables: customers, accounts, positions, and securities.

Cross-linking bridges the two layers. An extracted Sector entity
from a customer profile connects to the same sector nodes that
securities belong to. An extracted Interest or Goal connects back
to the customer node it was extracted from.

GraphRAG exploits both layers. Vector search finds the chunks
closest in meaning to the question. Graph traversal follows the
extracted entities through cross-links into the operational data.
The agent receives structured holdings alongside document context.

This is what works well. The next slide explains where it stops.
-->

---

## The Limits of Document-First Extraction

- **What KG construction does well:** structured and unstructured data is transformed in Databricks, then loaded into a Neo4j knowledge graph. Entity extraction captures what documents mention: holdings, accounts, interests, sectors
- **Where it falls short:** KG construction pipelines operate document-first. They record what documents say but have no awareness of what the graph already contains. Knowing a customer mentioned renewable energy is not the same as knowing their portfolio contains none of it
- **The missing step:** extraction writes entities and relationships to the graph, but never compares what it wrote against what was already there. The graph accumulates facts from documents without reasoning over whether those facts reveal gaps in the existing structure

<!--
Knowledge graph construction pipelines do one thing well: they
read documents, extract entities and relationships, and write them
to the graph. The pipeline captures what documents mention.

The limitation is that extraction operates document-first. It has
no awareness of what the graph already contains. It can extract
"interested in renewable energy" from a customer profile. What it
cannot do is check that customer's portfolio, discover they hold
zero renewable energy positions, and flag the contradiction. That
reasoning requires two data sources in the same context: the
document that states intent and the structured data that records
behavior.

The graph accumulates facts from documents, but no step in the
pipeline asks whether those facts reveal something missing in
the existing structure. That comparison is what enrichment adds.
-->

---

# Graph Enrichment: The Enrichment Loop

---

## Enrichment Starts from the Graph

- Agents read the graph's current state first, then analyze unstructured documents against that state
- When a customer profile mentions renewable energy and the graph shows zero renewable energy positions, agents flag the contradiction, score confidence, and propose a new INTERESTED_IN relationship to write back
- The graph grows from what documents reveal is **missing**, not just what they contain

<!--
Graph enrichment starts from the other direction. Instead of
reading a document and writing what it finds, agents read the
graph's current state first: what customers exist, what they hold,
what relationships connect them. They then analyze unstructured
documents against that state.

When a customer profile mentions renewable energy and the graph
shows that customer holds zero renewable energy positions, agents
flag the contradiction. They score their confidence and propose a
new INTERESTED_IN relationship to write back. The graph grows not
from what documents contain but from what documents reveal is
missing.
-->

---

## Each Cycle Changes What the Next Cycle Discovers

- Enrichment is **cyclic**, not one-shot
- Each pass builds on what the previous pass **wrote**, not on a static snapshot
- New relationships enable new algorithms, new algorithms reveal new gaps

<!--
This is the key architectural difference from extraction. Entity
extraction runs once per document: parse, extract, write, done.
The enrichment loop is cyclic. Each enrichment cycle changes the
graph's state, which changes what the next cycle discovers.

Each pass builds on what the previous pass wrote. An INTERESTED_IN
relationship written in cycle one enables community detection in
cycle two. The communities discovered in cycle two inform the gap
analysis in cycle three. The compounding is the point.
-->

---

## The Seven-Step Enrichment Loop

1. **Extract:** Spark Connector writes graph data to Delta Lake tables
2. **Analyze:** agents compare structured graph data against unstructured documents
3. **Propose:** gaps become enrichment candidates with confidence scores
4. **Validate:** ontology checks prevent schema conflicts and near-duplicate relationship types
5. **Enrich:** approved relationships write back to Neo4j via Cypher MERGE statements
6. **Query:** graph algorithms and GraphRAG operate on enriched relationships
7. **Repeat:** new documents and graph changes trigger incremental analysis

<!--
The enrichment loop runs in seven steps. Each cycle starts from
the graph's current state and ends with new relationships that
change what the next cycle discovers.

Extract uses the Spark Connector to pull graph data into Delta
Lake tables in the lakehouse. Analyze happens entirely within
the Databricks compute layer: Genie queries the extracted Delta
tables for structured holdings, the Knowledge Assistant reads
unstructured documents from Unity Catalog Volumes, and the
supervisor synthesizes both in a single session without crossing
system boundaries. The lakehouse is the environment where the
cross-source comparison happens.

Propose converts detected gaps into enrichment candidates with
confidence scores. Validate checks proposed relationship types
against the existing schema. Enrich writes approved relationships
back to Neo4j. Query lets graph algorithms and GraphRAG operate
on the enriched structure. Repeat triggers the next cycle when
new documents arrive or graph state changes.

Every downstream consumer benefits from each cycle. GraphRAG
retrieval traverses more paths. Graph algorithms operate on a
denser, more expressive structure.
-->

---

# Agent Architecture

---

## The Multi-Agent Enrichment System

```
                    User Question / Enrichment Task
                                |
                                v
                   +--- Supervisor Agent ---+
                   |                       |
                   v                       v
           Genie Agent            Knowledge Assistant
        (Lakehouse / SQL)         (Documents / RAG)
                   |                       |
                   +--- Augmentation Agent -+
                                |
                                v
                     Enrichment Proposals
```

<!--
The multi-agent system is built on Mosaic AI Agent Bricks. The
supervisor agent sits at the top, routing questions to the right
specialist based on data shape. Genie handles structured queries
against Delta Lake tables. The Knowledge Assistant handles
document analysis via retrieval-augmented generation. The
augmentation agent calls the supervisor endpoint, reasons over
combined results from both specialists, and generates enrichment
proposals with confidence scores.
-->

---

## Data Retrieval Agents

- **Multi-Agent Supervisor:** a coordinator on Mosaic AI Agent Bricks with access to both the Genie endpoint and the Knowledge Assistant endpoint
  - Routes questions to the right specialist, synthesizes responses into unified context
- **Genie:** translates natural language into SQL against Delta Lake tables
  - Handles quantitative questions: account balances, portfolio values, position sizes
  - Knows what customers hold; cannot determine what they want
- **Knowledge Assistant:** an Agent Bricks managed agent with access to unstructured data via RAG
  - Surfaces themes, concerns, and life events from documents
  - Cannot check what those customers actually hold

<!--
Three components handle data retrieval. The supervisor routes
and synthesizes. Genie answers "what does this customer hold?" by
generating SQL queries against Delta Lake tables that contain
graph data extracted by the Spark Connector — customer nodes,
account details, holdings, and relationship edges. These aren't
raw lakehouse tables; they carry the graph's relationship
structure in tabular form. The Knowledge Assistant answers "what
does this customer want?" by searching unstructured documents in
Unity Catalog Volumes: customer profiles, advisor notes, and
market research.

Neither agent alone can detect a gap. Genie knows the portfolio
contains only tech stocks. The Knowledge Assistant knows the
customer mentioned renewable energy. The supervisor brings both
answers into the same context so the next layer can reason over
the comparison.
-->

---

## Enrichment and Extraction Agents

- **Augmentation Agent:** calls the supervisor endpoint, reasons over combined structured and unstructured results, generates enrichment proposals with confidence scores
- **Batch Inference:** AI Query sends prompts to served model endpoints for batch extraction of missing entities as tabular results

<!--
The augmentation agent sits on top of the data retrieval layer.
It calls the supervisor endpoint, receives the combined structured
and unstructured results, and reasons over the comparison to
generate enrichment proposals with confidence scores. This is
where gap detection happens: the augmentation agent identifies
that a customer's stated interests conflict with their actual
holdings and proposes a new relationship to write back.

AI Query handles batch extraction at scale, sending prompts to
served model endpoints and structuring both input and output as
tabular results, queryable from notebooks and pipelines. When
the enrichment pipeline needs to process hundreds of flagged
customers at once, AI Query handles that extraction as a single
batch operation rather than individual agent calls.
-->

---

# Gap Types the Agents Detect

---

## Cross-Source Comparison Reveals Hidden Gaps

The multi-agent system reveals gaps invisible to either data source alone:

| Customer | Expressed Interest | Current Holdings | Gap Type |
|---|---|---|---|
| Customer A | Renewable energy, retail investment | TCOR, SMTC, MOBD (all tech) | Interest-holding mismatch |
| Customer B | ESG/sustainable investing | GFIN (financial sector) | Values-portfolio mismatch |
| Customer C | Aggressive growth, active trading | Mixed portfolio | No gap (profile matches behavior) |

<!--
The multi-agent system reveals gaps invisible to either data
source alone. Customer A's documents mention renewable energy
repeatedly, but their portfolio is entirely tech stocks. That's
an interest-holding mismatch: a cross-sell opportunity, an
overdue advisor conversation, or intent that hasn't translated
into action.

Customer B describes ESG and sustainability priorities that
conflict with current holdings. Customer C is the important
counterexample: their profile matches their actual behavior.
Confirming alignment is equally valuable. It validates that the
structured record accurately reflects their situation.
-->

---

# Feature Engineering

---

## From Enrichment to ML Features

- Enrichment adds INTERESTED_IN and HAS_GOAL relationships to the graph
- But does a richer graph produce **better ML features**?
- Traditional features (income, credit score, portfolio value) describe customers **in isolation**
- Graph features capture a customer's **position in the network**: connections, neighborhoods, communities

<!--
The enrichment loop writes new relationships back to the graph
and the cycle compounds. But nothing in the pipeline so far
measures whether those new relationships actually improve
downstream machine learning.

Traditional ML features for a customer portfolio come from
tabular data: annual income, credit score, portfolio value,
transaction counts. These describe each customer in isolation.
Graph feature engineering adds a second source of features
derived from the customer's position in the network: how they
connect to other customers, stocks, companies, and sectors
through the graph topology. The question is whether the
enriched topology produces better features than the base graph.
-->

---

## FastRP: Graph Structure as Features

- FastRP computes a **128-dimensional vector** for every node in the graph
- Each dimension encodes **neighborhood structure**: which stocks held, which companies, how many shared neighbors
- These are **structural** embeddings, not semantic — they encode graph topology, not word meaning
- 128 new feature columns alongside existing tabular features

<!--
FastRP, Fast Random Projection, is the algorithm that performs
the extraction. It computes a fixed-length numeric vector for
every node, where each dimension encodes some aspect of the
node's neighborhood structure. A 128-dimensional FastRP
embedding for a customer captures the shape of that customer's
connections: which stocks they hold, which companies those
stocks belong to, how many other customers hold the same stocks,
and how those neighbors connect outward in turn.

The critical distinction: FastRP embeddings are not semantic
similarity embeddings. A text embedding, like the ones the
enrichment pipeline uses for document retrieval, encodes the
meaning of words. A FastRP embedding encodes graph structure.
It does not know what "renewable energy" means. It knows that
Customer A is two hops from Stock X through Account Y and
shares three holding-neighbors with Customer B. The features
it produces are structural, not semantic.

These 128 numbers become 128 new feature columns in a training
dataset, sitting alongside the tabular features.
-->

---

## Before and After Enrichment

- **Baseline:** project the base graph (Customer, Account, Position, Stock), run FastRP, train a classifier
- **Enrich:** run the enrichment pipeline, add INTERESTED_IN and HAS_GOAL relationships
- **Re-embed:** project the enriched graph, run FastRP with the **same parameters**
- **Result:** enriched embeddings encode richer topology — better features, better model

<!--
The before-and-after story is straightforward. Compute FastRP
embeddings on the base graph: Customer, Account, Position, and
Stock nodes with HAS_ACCOUNT, HAS_POSITION, and OF_SECURITY
relationships. Export as 128 feature columns alongside tabular
features. Train a classifier and record accuracy, precision,
and recall.

Run the enrichment pipeline. The write-back step adds
INTERESTED_IN relationships connecting customers to sectors
and investment themes, HAS_GOAL relationships connecting
customers to financial objectives, and new intermediate nodes
like INVESTMENT_THEME and FINANCIAL_GOAL.

Re-project the graph with the new node types and relationships
included. Run FastRP again with the same embedding dimension
and parameters. The embeddings now encode not just what
customers hold but what they want: interests, goals, and
thematic connections that only exist because the enrichment
loop discovered them. Train the same classifier and compare.

Same algorithm, same parameters, richer topology, better model.
-->

---

## Community Detection as a Feature Column

- **Louvain** assigns every node to a community — **one feature column**
- Before enrichment: communities form around **shared holdings**
- After enrichment: communities incorporate **interests and goals**
- "Tech investors" splits into "tech growth" and "tech income" once HAS_GOAL relationships are visible

<!--
Once the FastRP projection exists, adding Louvain community
detection is a single additional algorithm call on the same
in-memory graph. Unlike FastRP's 128 embedding dimensions,
Louvain produces a single feature column: a community ID per
node.

Louvain assigns every node to a community by optimizing
modularity, a measure of how densely connected nodes within a
group are compared to connections between groups. On the base
graph, communities form around shared holdings. Customers who
hold stocks from the same companies end up in the same
community.

On the enriched graph, communities incorporate interest and
goal relationships. A community that was previously "customers
who hold tech stocks" might split into "tech investors focused
on growth" and "tech investors focused on income" once
HAS_GOAL relationships distinguish their objectives. The
community ID feature column changes, and a model trained with
enriched community IDs can distinguish customer segments that
the base graph could not separate.

One more feature column, alongside the 128 FastRP dimensions,
that a downstream model can consume.
-->

---

## The Bi-Directional Loop

- **Write to Neo4j:** FastRP embeddings and Louvain community IDs persist as node properties, available to all downstream Cypher queries
- **Spark Connector to Gold tables:** reads scored nodes back into Delta Lake Gold tables. Embedding vectors and community IDs become columns alongside original customer attributes
- **Feature Store registration:** graph-derived features register in Databricks Feature Store alongside tabular features. MLflow captures dependencies
- **The loop closes:** Gold tables feed ML training in Databricks. Model predictions write back to Neo4j via the Spark Connector

<!--
GDS write mode persists algorithm results as node properties in
Neo4j. FastRP embedding vectors and Louvain community IDs become
queryable properties the moment they land. Cypher queries,
GraphRAG traversals, and agent tools all operate on the enriched,
algorithm-scored graph immediately.

The Spark Connector then reads those scored nodes back into
Delta Lake Gold tables. The 128 FastRP embedding dimensions and
Louvain community IDs become columns alongside original customer
attributes like income, credit score, and portfolio value.

Graph-derived features register in Databricks Feature Store
alongside tabular features. MLflow captures the dependencies
between graph algorithm runs and model training. Point-in-time
lookups ensure training uses the embedding from when an event
occurred, not today's embedding computed on a different graph
state.

The loop fully closes when model predictions flow back to
Neo4j. Risk scores, churn probabilities, and classification
labels become node properties that agents in the next enrichment
cycle can reason over alongside documents and graph structure.
The graph and the lakehouse become a single analytical surface.
-->

---

## Quantifying Lift

- **Baseline:** tabular features only (income, credit score, portfolio value). Train a classifier, record AUC / precision / recall
- **Add graph features:** append 128 FastRP embedding columns + Louvain community ID to the same model. Retrain
- **Compare:** enriched embeddings capture structural patterns invisible to flat tables
- **MLflow tracking:** both experiments tracked, feature importance shows which graph features drove the lift

<!--
The way to prove graph features matter is to measure the
difference. Train a baseline model using only tabular features
from Delta Lake: annual income, credit score, portfolio value,
transaction counts. Record AUC, precision, and recall.

Then add the 128 FastRP embedding columns and the Louvain
community ID to the same model architecture. Retrain with the
combined feature set and compare. The enriched embeddings
capture structural patterns that flat tables cannot see: a
customer might look normal in isolation, but their position in
the graph, connected to a cluster of customers who all share
an interest in a particular sector, carries signal that no
column in a Delta table encodes.

MLflow tracks both experiments. Feature importance plots show
exactly which graph features drove the improvement. The results
are auditable, reproducible, and versioned.

The lift is not static. Each enrichment cycle produces more
INTERESTED_IN relationships for FastRP to encode. The
embeddings after Cycle 2 are richer than after Cycle 1. Model
performance improves as the graph grows.
-->

---

## Incremental Data Sync

- **Change Data Feed:** enable Delta Lake's CDF on Gold tables
- When new customers or positions appear, a Spark Structured Streaming job detects the change
- Pushes only the **delta** to Neo4j via the Spark Connector — no full reloads
- Costs stay proportional to **change volume**, not total data volume

<!--
Running full enrichment analysis across all customers and
documents after every update becomes prohibitively expensive.
The architecture supports incremental processing at every stage.

Delta Lake's Change Data Feed detects new or modified rows in
Gold tables. A Spark Structured Streaming job picks up those
changes and pushes only the delta to Neo4j through the Spark
Connector. No full reloads required. An organization with
100,000 customer profiles doesn't reprocess all of them daily;
it processes the hundreds that changed since yesterday.
-->

---

## Incremental Enrichment

- **Document triggers:** when a customer profile updates, re-analyze **that customer only**
- **Batch triggers:** when new market research arrives, batch-analyze **that document type**
- **Algorithm refresh:** GDS runs on a schedule (nightly or after each enrichment cycle). Results write to Neo4j and extract to refreshed Gold tables
- Agent inference costs stay proportional to **what changed**, not the full corpus

<!--
On the enrichment side, incremental triggers control what gets
reprocessed. When a customer profile document updates, the
system re-analyzes that specific customer against their current
graph state. When new market research arrives, a batch job
analyzes all documents of that type.

GDS algorithms run on a schedule tied to the enrichment cadence.
After each enrichment cycle writes new relationships, FastRP
and Louvain re-run on the updated graph. Results write to
Neo4j properties and extract to refreshed Gold tables. Feature
Store versions track which algorithm run produced which features.
-->

---

## Pipeline Orchestration

- **Databricks Jobs** chain the full loop as tasks:
  1. Extract changed graph data
  2. Run enrichment agents on changed documents
  3. Write approved enrichments to Neo4j
  4. Run GDS algorithms on enriched graph
  5. Extract scores to Gold tables
  6. Register updated features
- **Human-in-the-loop** checkpoints can gate any step

<!--
The full pipeline is orchestrated as a Databricks Job with each
step as a task. Extract pulls changed graph data into Delta
tables. Enrichment agents analyze changed documents against
current graph state. Approved enrichments write back to Neo4j.
GDS algorithms run on the updated graph. Scores extract to Gold
tables. Updated features register in the Feature Store.

Human-in-the-loop checkpoints can gate any step in the chain.
During early cycles, you might gate the write-back step so data
architects review proposals before they reach the graph. As
confidence in the pipeline grows, those gates shift to exception
handling rather than full review.
-->

---

# Demo

---

## Source Graph: Financial Services in Aura

- **Nodes:** customers, accounts, positions, securities, sectors
- **Relationships:** HAS_ACCOUNT, HAS_POSITION, OF_SECTOR
- **Aura free tier:** fully functional for this demo
- Holdings and account structure loaded via **Spark Connector**

<!--
The demo uses a financial services knowledge graph running in
Neo4j Aura on the free tier. The graph contains customers,
accounts, positions, securities, and sectors connected by
relationships like HAS_ACCOUNT, HAS_POSITION, and OF_SECTOR.

This is the same graph structure we've been discussing. Holdings
and account structure were loaded via the Spark Connector from
governed Delta tables, following the pipeline we built in the
first webinar.
-->

---

## Data Extraction to Delta Tables

- **Spark Connector** pulls tabular and graph data into Databricks
- **Flat tables:** customer nodes, account details, holdings
- **Graph tables:** node start, relationship, node end with properties
- Both registered as **Unity Catalog** governed assets

<!--
The Neo4j Spark Connector pulls both flat tabular data and full
graph data into Databricks Delta tables. The flat tables contain
customer nodes, account details, and holdings as standard rows
and columns. The graph tables preserve the full relationship
structure: start node, relationship type and properties, end node.

Both formats are registered as Unity Catalog governed assets,
available to Genie for SQL queries and to downstream pipeline
tasks.
-->

---

## Gap Detection via Multi-Agent Supervisor

- **Supervisor** compares graph holdings against document profiles
- **Genie** queries Delta tables for actual portfolio positions
- **Knowledge Assistant** reads customer profiles from Unity Catalog Volume
- **Result:** customers with interests but no matching holdings

<!--
The multi-agent supervisor compares graph contents, the structured
holdings, against customer profile documents stored in a Unity
Catalog Volume. Genie queries the Delta tables to determine what
each customer actually holds. The Knowledge Assistant reads the
customer profile documents to surface stated interests and
preferences.

The supervisor synthesizes both responses and identifies customers
whose stated interests have no corresponding positions in their
portfolios. These become the enrichment candidates.
-->

---

## Entity Extraction and Pipeline Assembly

- **AI Query** extracts interest entities for flagged customers
- Returns structured columns saved as **governed data assets**
- **Databricks Job** chains extraction, formatting, and write-back
- Produces a table of proposed **INTERESTED_IN** relationships

<!--
AI Query prompts the agent to extract interest entities and
relationship candidates for flagged customers. For example,
Customer A mentions renewable energy but holds only tech stocks.
The extraction returns structured columns saved as a Unity Catalog
governed data asset.

The extraction query is added as a task in a Databricks Job
pipeline, followed by a formatting notebook, producing a table of
proposed INTERESTED_IN relationships ready for write-back to Neo4j.
-->

---

## Human-in-the-Loop Option

- Pipeline can write **directly** to the graph
- Or output to a **review table** for human validation
- Data architects approve, modify, or reject proposals
- Approved enrichments write back via **Cypher MERGE**

<!--
Instead of writing directly to the graph, the pipeline can output
to a review table for human validation before integration. Data
architects review the proposed relationships, their confidence
scores, and the source evidence. They can approve, modify, or
reject individual proposals.

This human-in-the-loop checkpoint is especially important during
early enrichment cycles when you're establishing the patterns
and confidence thresholds that will govern later automation.
-->

---

# Enrichment Process Detail

---

## Confidence Scoring

| Extraction Pattern | Confidence | Action |
|---|---|---|
| "expressed strong interest in" | ~0.95 | Auto-approve |
| "mentioned considering" | ~0.70 | Approve with flag |
| "advisor suggested" | ~0.40 | Queue for review |
| Ambiguous context | < 0.30 | Reject |

- **Cross-referencing** multiple documents boosts consolidated confidence above any single extraction

<!--
Agent extractions are assigned confidence levels based on
linguistic strength. "Expressed strong interest in" yields high
confidence and auto-approves. "Mentioned considering" is moderate
and gets flagged. "Advisor suggested" is lower because the
interest comes from a third party and queues for review. Ambiguous
context scores below 0.30 and is rejected outright.

Cross-referencing improves confidence. If three documents mention
the same customer's renewable energy interest, the consolidated
confidence exceeds any single extraction.
-->

---

## Ontology Validation and Schema Governance

- A validation layer compares proposed relationship types against the existing schema using **semantic similarity**, catching near-duplicates (INTERESTED_IN vs. HAS_INTEREST_IN vs. SHOWS_INTEREST_FOR) and reusing existing types
- **Novel relationship types** (DISLIKES, CONCERNED_ABOUT) queue for human review by data architects

<!--
Without validation, agents create semantically equivalent
relationship types with different names, and the schema becomes
harder to query over time. The validation layer catches
near-duplicates by comparing proposed types against the existing
schema using semantic similarity. If a sufficiently similar type
exists, the proposal reuses it.

Novel types queue for human review. One agent processing customer
profiles might propose WORRIED_ABOUT while another processing
advisor notes proposes HAS_CONCERNS. A data architect recognizes
these as the same concept and consolidates them.
-->

---

## Idempotent Write-Back with Provenance

```cypher
MERGE (sector:Sector {sectorId: 'RenewableEnergy'})
SET sector.name = 'Renewable Energy'

MATCH (c:Customer {customerId: 'C0001'})
MATCH (s:Sector {sectorId: 'RenewableEnergy'})
MERGE (c)-[r:INTERESTED_IN]->(s)
SET r.confidence = 0.92,
    r.source_document = 'customer_profile_001.txt'
```

- **MERGE** ensures no duplicate relationships
- **Provenance properties:** source document, extracted phrase, timestamp, confidence score

<!--
Validated enrichments become Cypher MERGE statements, ensuring
that running the same enrichment twice does not create duplicate
relationships. Properties on each relationship capture provenance:
which document contained the evidence, what phrase was extracted,
when the enrichment occurred, and what confidence level the agent
assigned.

Stakeholders can query provenance directly in Cypher to answer
"Why does the system think this customer wants renewable energy?"
and trace the answer back to specific document phrases. This
transparency builds trust in agent-generated enrichments and
supports compliance requirements in regulated industries.
-->

---

# What Enrichment Unlocks: Compounding Cycles

---

## Before Enrichment: Intent Has No Graph Path

- **GraphRAG** is bounded by holdings, accounts, positions
- A query about customer **intent** has no path to follow
- Retrieval falls back to vector similarity over documents
- Loses the structural grounding that makes GraphRAG valuable

<!--
Before enrichment, GraphRAG retrieval is bounded by the graph's
original structure: holdings, accounts, positions. Portfolio-level
questions work because the traversal paths exist. But a query
about customer intent has no graph path to follow.

Retrieval falls back to vector similarity over documents, losing
the structural grounding that makes GraphRAG valuable. The graph
knows what customers hold. It has no idea what they want.
-->

---

## After Cycle 1: Intent Becomes Traversable

```cypher
MATCH (c:Customer)-[:INTERESTED_IN]->(s:Sector {name: 'Renewable Energy'})
WHERE NOT EXISTS {
    MATCH (c)-[:HAS_ACCOUNT]->()-[:HAS_POSITION]->()
           -[:OF_SECURITY]->()-[:OF_COMPANY]->(co)
    WHERE co.sector = 'Renewable Energy'
}
RETURN c.customerId, c.firstName, c.lastName
```

- Previously **impossible**, now a straightforward traversal
- INTERESTED_IN makes intent a **first-class graph entity**

<!--
After the first enrichment cycle, a query that was previously
impossible becomes a straightforward traversal. "Find customers
interested in renewable energy who hold no renewable energy
stocks" works because INTERESTED_IN relationships, extracted from
profile documents and validated through the enrichment pipeline,
make intent a first-class graph entity alongside transactional
data.

GraphRAG can now link a customer to a sector through an enriched
relationship, then fan out to related documents, advisor notes,
and market research. Retrieval is grounded in graph structure,
not just embedding similarity.
-->

---

## Cycle 2: Algorithms on Enriched Relationships

- **Jaccard similarity** identifies customer clusters by interest profile
- **Louvain community detection** reveals organic segments
- These algorithms operate on relationships that **did not exist** before cycle 1
- No one designed these segments upfront

<!--
Starting from a richer graph, similarity algorithms and community
detection operate on relationships that did not exist before the
first cycle. Jaccard similarity identifies clusters of customers
with similar interest profiles. Louvain community detection
reveals organic segments no one designed upfront.

These segments emerge from the enriched structure itself. They
weren't anticipated in any schema design. They became visible
only because the first enrichment cycle wrote the INTERESTED_IN
relationships that the algorithms now operate on.
-->

---

## Cycle 3+: Cross-Referencing Against New Data

- New documents (market research, updated profiles) arrive
- Agents cross-reference against **interest communities** from cycle 2
- Matches span customer preference, portfolio gap, **and** market opportunity
- Each cycle expands what GraphRAG can traverse

<!--
Subsequent cycles cross-reference newly ingested documents like
market research and updated profiles against the interest
communities and clusters that only became visible through earlier
enrichments. The matches now span multiple layers of inference:
customer preference, portfolio gap, and market opportunity.

Each enrichment cycle expands the surface area that GraphRAG can
traverse. Retrieval quality is directly tied to the graph's
expressiveness, and the enrichment loop is what makes the graph
more expressive over time.
-->

---

## Extraction vs. Enrichment

- **Extraction** asks: "what does this document say?"
- **Enrichment** asks: "what relationships are missing?"
- That question, repeated across cycles, **compounds**
- The graph after six months captures patterns no schema designer anticipated

<!--
Entity extraction asks: what does this document say? Agentic
enrichment asks: what relationships are missing? That question,
repeated across cycles, compounds into organizational memory.

The graph after six months of enrichment captures patterns that
no schema designer could have anticipated, because those patterns
only became visible after earlier enrichments connected data that
was never connected before. The first cycle finds obvious gaps.
The second cycle runs algorithms on those new relationships. The
third cycle cross-references new data against communities that
only exist because of the first two cycles.
-->

---

## Key Takeaways

- **Three-part distinction:** entity extraction builds the graph; the enrichment loop detects what's missing and fills it; GDS algorithms turn enriched relationships into computable features
- **Gap detection, not just extraction:** the enrichment loop's value is comparing documents against current graph state, not just parsing documents for entities
- **Compounding cycles:** each enrichment pass changes the graph, which changes what algorithms compute, which changes what the next pass discovers
- **Graph features improve models:** combining graph-derived features with tabular data in Feature Store produces measurably better predictions than either source alone
- **The loop is bi-directional:** graph scores flow to Gold tables; model predictions flow back to Neo4j. The Spark Connector and Feature Store make the graph and lakehouse a single analytical surface

<!--
Five things to take away. First, there are three distinct phases:
extraction builds the initial graph, the enrichment loop detects
what's missing and fills it, and GDS algorithms turn those
enriched relationships into computable features for ML.

Second, the enrichment loop's value is gap detection, not parsing.
It compares documents against the graph's current state.

Third, the cycles compound. Each pass changes the graph, which
changes what algorithms compute, which changes what the next pass
discovers.

Fourth, graph features measurably improve models. Combining graph
features with tabular features in the Databricks Feature Store
produces better predictions than either source alone.

Fifth, the loop is fully bi-directional. Graph scores flow to
Gold Delta tables. Model predictions flow back to Neo4j. The
Spark Connector and Feature Store make the graph and the
lakehouse a single analytical surface.
-->
