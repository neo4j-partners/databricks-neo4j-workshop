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

# Graph Feature Engineering with Neo4j GDS and Databricks

Feature Engineering in Unity Catalog + scikit-learn + MLflow

---

---

## What You'll Learn

- What feature engineering is and why graph structure produces features flat tables cannot
- How Neo4j GDS algorithms generate features from graph topology
- The bi-directional pattern: GDS features flow to Feature Engineering in Unity Catalog, classifier predictions flow back to Neo4j
- How to measure the lift graph features add to a classifier
- Sync strategies for keeping Neo4j and Databricks aligned

<!--
Five things by the end of this session. First, what graph feature
engineering actually is and why it matters. Second, which GDS
algorithms produce useful features. Third, the full loop between
Neo4j and Databricks. Fourth, how to measure whether graph features
actually improve a classifier. Fifth, how to keep the two systems
in sync without manual intervention.
-->

---

## The Dual Architecture for This Use Case

- **Databricks holds the analytical layer:** Delta tables with customer demographics and transaction history, plus UC Volumes with unstructured documents like customer profiles and investment research
- **Neo4j holds the relationship layer:** the Customer → Account → Position → Stock portfolio topology, plus document nodes with vector embeddings that bridge unstructured content into the graph

<!--
Let's start with what lives where. This is the same dual
architecture from the first webinar, applied to the portfolio
use case.

Databricks holds the analytical layer. Delta tables contain
customer demographics and transaction history. UC Volumes store
unstructured documents: customer profiles and investment research.

Neo4j holds the relationship layer. The portfolio topology runs
from Customer to Account to Position to Stock. Document nodes
with vector embeddings bridge unstructured content into the
graph, so text and structure live side by side.
-->

---

## Graph-Enriched Retrieval

- **The graph data pipeline** analyzed customer profiles to extract interests, goals, and concerns, then linked them to customer nodes with relationships like INTERESTED_IN, HAS_GOAL, and CONCERNED_ABOUT
- **GraphRAG combines both layers:** vector search finds relevant document chunks, graph traversal follows extracted entities into operational data
- **Agents receive richer context** than text search alone: structured holdings alongside document content

<!--
The graph data pipeline analyzed customer profiles to extract
interests, goals, and concerns. Those entities became nodes
linked to customers with relationships like INTERESTED_IN,
HAS_GOAL, and CONCERNED_ABOUT. These relationships didn't exist
in the raw data.

GraphRAG combines both layers. Vector search finds the chunks
most relevant to the user's question. Graph traversal follows
extracted entities from those chunks into the operational data.
The agent receives structured holdings alongside document context
in a single response.

This works well for questions that documents can answer. But it
has a coverage limit, which is where we're headed next.
-->

---

![bg contain](../databricks-in-depth/graphrag-retrieval-flow.png)

---

## The GraphRAG Gap

- **Semantic search now finds customers by risk profile.** The pipeline linked profiles to customers, and GraphRAG retrieves across that structure
- **Only some customers have profile documents.** For the remaining customers, there are no documents to retrieve and no chunks to traverse from
- **The graph still holds structural information** about those customers: who they connect to, what they hold, how they cluster. But GraphRAG can't surface it because it starts from text, not topology

<!--
Here is the concrete problem. Semantic search can now find
customers by risk profile because the pipeline linked profiles
to customer nodes. GraphRAG retrieves across that structure
beautifully.

But only some customers have profile documents. For the
remaining customers, there is nothing for vector search to find, which
means there are no starting points for graph traversal.

The graph itself still encodes useful information about those
remaining customers: their portfolio connections, account
structures, and relationships to stocks and sectors. But GraphRAG
cannot surface structural patterns because it enters the graph
through text, not through topology. We need a different approach
for the rest.
-->

---

## What's Missing: Structural Similarity

- **The customers without documents** still have rich graph structure: accounts, positions, stocks, sectors. The same topology as the labeled customers
- **Customers with similar portfolios likely share similar risk profiles.** If Alice holds the same stocks as Bob and Alice is high-risk, Bob probably is too
- **We need a way to quantify structural similarity** across the graph and use it to classify the unlabeled customers

<!--
The unlabeled customers are not empty rows. They have accounts,
positions, stocks, sector connections. The same topology as the
labeled customers. The structure is there,
just no documents.

The intuition is straightforward: customers with similar
portfolios likely share similar risk profiles. If Alice holds
the same stocks as Bob and Alice is labeled high-risk, Bob
probably is too. The pattern is in the graph structure, not
in any document.

What we need is a way to quantify that structural similarity
across the entire graph and use it to classify the unlabeled
customers. That is exactly what graph feature engineering does.
-->

---

## The Solution: Graph Feature Engineering

- **What if we could group customers by the structure of their connections?** Customers who hold similar stocks, connect to similar sectors, and share neighbors likely belong in the same category
- **Graph Data Science computes these from the graph:** which group a customer belongs to, how influential they are, etc. These become the features an ML model trains on
- **An ML model trained on these features** learns the patterns from labeled customers and predicts labels for the rest. Predictions write back to Neo4j, closing the coverage gap

<!--
This is the core idea for the rest of the webinar. What if we
could group customers by the structure of their connections?
Customers who hold similar stocks, connect to similar sectors,
and share graph neighbors likely belong in the same risk
category.

Neo4j Graph Data Science computes these from the graph: which
group a customer belongs to, how influential they are in the
network, and a numeric fingerprint of their connections. Think
of it as a summary of who they're connected to, compressed into
numbers. Customers with similar fingerprints have similar
connection patterns. These computed values become the features
an ML model trains on.

An ML model trained on the labeled customers learns which
feature patterns correspond to which risk category, then
predicts labels for the rest. Those predictions write back to
Neo4j through the Spark Connector. Now every customer has a
risk classification, even without a profile document.
-->

---

# Foundations: Features and Classifiers

---

## What Are Features and Classifiers?

- **Feature:** a column describing an entity: age, balance, number of connections, or a category like community membership
- **Classifier:** takes rows of features and predicts a label like risk category. Features in, label out
- **Feature engineering:** creating new, informative features from raw data
- **Graph feature engineering:** uses relationships and network structure to create new, more meaningful features for ML models

<!--
Quick vocabulary for anyone new to ML terminology. A feature is
a column that describes something about an entity. It can be
numeric like age or balance, or categorical like community
membership. A classifier takes rows of features and learns to
predict a label.

Feature engineering is the process of creating new features from
raw data. Graph feature engineering uses relationships and
network structure to create new features: who connects to whom,
who shares neighbors, who belongs to which community. These
structural features capture information that no single table
column encodes.
-->

---

## Example: Features and Classification

| Customer | Income | Portfolio Value | Community | Risk Category |
|----------|--------|-----------------|-----------|---------------|
| Alice    | 95K    | 240K            | 3         | **High**      |
| Bob      | 88K    | 310K            | 3         | **High**      |
| Carol    | 62K    | 85K             | 7         | **Low**       |
| Dave     | 91K    | 275K            | 3         | ???           |

- **Columns are features:** income, portfolio value, and community ID each describe something about a customer
- **Risk category is the label** the classifier learns to predict
- **Dave looks like Alice and Bob:** similar income, similar portfolio, same community. The classifier predicts **High**

<!--
A concrete example makes the vocabulary real. Each row is a
customer. Each column is a feature: income, portfolio value,
and community ID from Louvain. Risk category is the label the
classifier learns to predict.

Alice and Bob are labeled High. Carol is labeled Low. Dave has
no label yet. The classifier looks at the feature columns and
notices Dave's pattern matches Alice and Bob: similar income,
similar portfolio value, and the same community ID. It predicts
High.

Community ID is the graph feature here. Without it, the
classifier only sees income and portfolio value. With it, the
classifier knows Dave clusters with Alice and Bob in the graph,
not with Carol. That structural signal is what graph feature
engineering adds.
-->

---

# Graph Feature Engineering

---

## GDS Foundations

- **Graph projections:** algorithms run on in-memory projections, not the live database. A projection selects specific node labels and relationship types, creating an optimized in-memory copy
- **Projection configuration:** which node labels, relationship types, and relationship properties you include determines the features you get. Different projections of the same graph produce different results
- **Execution modes:** stream (return results), stats (summary only), mutate (add to projection for chaining), write (persist to database)

<!--
Three foundational concepts before we run algorithms. First,
algorithms run on in-memory projections, not the live database.
You select which node labels and relationship types to include,
and GDS creates an optimized copy for algorithm execution.

Second, what you include in the projection matters. Node labels,
relationship types, and relationship properties all shape algorithm
output. Include position value as a relationship property and
PageRank weights by it. Include INTERESTED_IN relationships from
enrichment and FastRP encodes richer neighborhoods. Different
projections of the same database produce different features.

Third, every algorithm supports four execution modes. Stream
returns results without persisting. Stats gives summary metrics.
Mutate adds results to the in-memory projection for chaining.
Write persists to the database. We will use mutate for chaining
and write for final output.
-->

---

## Five GDS Algorithm Categories

- **Centrality:** who is important (PageRank, Betweenness)
- **Community Detection:** who clusters together (Louvain, Label Propagation)
- **Similarity:** who resembles whom (Jaccard, Cosine)
- **Pathfinding:** how entities connect (Shortest Path, Dijkstra)
- **Node Embeddings:** vector representations for ML (FastRP, Node2Vec)

<!--
GDS organizes its 65+ algorithms into five categories. Centrality
answers who is important: PageRank, Betweenness Centrality.
Community Detection answers who clusters together: Louvain,
Label Propagation. Similarity answers who resembles whom: Jaccard,
Cosine. Pathfinding answers how entities connect: Shortest Path,
Dijkstra. Node Embeddings produce vector representations for ML:
FastRP, Node2Vec.

For this webinar we use algorithms from four of the five
categories: Node Embeddings (FastRP), Centrality (PageRank),
Community Detection (Louvain), and Similarity (Jaccard). The full
library gives you options to match your domain.
-->

---

## FastRP: Capturing Graph Structure

- **Vector embedding for each customer:** FastRP compresses a customer's connections into numbers like a fingerprint, capturing which stocks are held, how their neighbors overlap, etc.
- **Similar connections, similar fingerprints:** two customers who hold the same stocks through similar account structures produce similar fingerprints
- **Every customer gets a fingerprint,** including those with no profile documents. Graph structure exists for every node, not just the ones with text

<!--
FastRP compresses a customer's connections into numbers: which
stocks they hold, which accounts link where, how their neighbors
overlap with other customers.

Two customers who hold the same stocks through similar account
structures produce similar fingerprints because they occupy
similar positions in the graph.

And every customer gets a fingerprint, including those with no
profile documents. Graph structure exists for every node, not
just the ones with text. That is what closes the coverage gap
we identified earlier.
-->

---

## Example: Projecting the Portfolio Graph

```cypher
CALL gds.graph.project(
    'portfolio-graph',
    ['Customer', 'Account', 'Position', 'Stock'],
    {
        HAS_ACCOUNT:  { type: 'HAS_ACCOUNT',  orientation: 'UNDIRECTED' },
        HAS_POSITION: { type: 'HAS_POSITION', orientation: 'UNDIRECTED',
                        properties: ['positionValue'] },
        OF_SECURITY:  { type: 'OF_SECURITY',  orientation: 'UNDIRECTED' }
    }
)
```

- **Four node labels, three relationship types:** the full portfolio topology in one projection
- **`positionValue` on `HAS_POSITION`:** each customer's position has its own value, enabling weighted PageRank later
- **`UNDIRECTED`:** algorithms traverse in both directions

<!--
This is the actual projection call for the portfolio graph. Four
node labels capture the full entity set: Customer, Account,
Position, Stock. Three relationship types capture the connections
between them.

The positionValue property on HAS_POSITION is projected so that
PageRank can weight by dollar value later. Each customer's
position has its own value, so the property lives on HAS_POSITION,
not OF_SECURITY. Without projecting this property, PageRank
treats all relationships equally.

UNDIRECTED orientation means algorithms can traverse in both
directions. A customer reaches a stock through HAS_ACCOUNT,
HAS_POSITION, OF_SECURITY. The stock also reaches back to all
customers who hold it. This bidirectional traversal is what
lets FastRP encode shared-holding neighborhoods.
-->

---

## Example: Running FastRP on the Projection

```cypher
CALL gds.fastRP.write('portfolio-graph', {
    embeddingDimension: 128,
    writeProperty: 'embedding',
    iterationWeights: [0.0, 1.0, 1.0, 0.8]
})
```

- **`write` mode:** persists embeddings as node properties, ready for the Spark Connector
- **`iterationWeights`:** controls how much each hop contributes. Four weights = four hops deep
- **128 dimensions** stored as a single array property per node

<!--
One call, and every node in the projection gets a 128-dimensional
embedding persisted as a node property.

iterationWeights controls how much each hop contributes to the
embedding. Four weights means the algorithm looks four hops deep.
The first weight is 0.0, which means the node's own properties
are excluded. Weights of 1.0, 1.0, and 0.8 mean immediate
neighbors and two-hop neighbors contribute fully, while three-hop
neighbors contribute slightly less.

The result is a 128-dimensional array property on every node in
the projection. The Spark Connector reads these arrays into Delta
Lake Gold tables in the next step.
-->

---

## Example: What a Node Looks Like After GDS

```
(:Customer {
  name: 'Alice',
  customerId: 'C001',
  income: 95000,
  portfolioValue: 240000,
  embedding: [0.12, -0.34, 0.71, ...],   // FastRP (128d)
  pageRank: 0.042,                         // Centrality
  communityId: 3                           // Louvain
})
```

- **Original properties** (name, income, portfolioValue) unchanged
- **GDS write mode added three new properties** directly to the node
- **Every Customer node** now carries its graph fingerprint, influence score, and community assignment
- **Immediately queryable:** Cypher, GraphRAG, and agent tools can use these properties right away

<!--
After the algorithm pipeline completes, each Customer node carries
three new properties alongside its original attributes. The
embedding array is the FastRP graph fingerprint. The pageRank
score reflects influence in the portfolio network. The communityId
is the Louvain cluster assignment.

These properties are written directly to Neo4j by the GDS write
calls we just saw. They are immediately queryable. A Cypher query
can filter customers by community. A GraphRAG traversal can use
pageRank to prioritize high-influence nodes. An agent tool can
retrieve the embedding for similarity comparison.

In the next section, the Spark Connector reads these enriched
nodes back into Delta Lake Gold tables, combining graph properties
with tabular features for classifier training.
-->

---

# The Bi-Directional Loop: Neo4j and Databricks

---

## Spark Connector Brings Results to Gold Tables

- **Spark Connector reads enriched nodes** back into Delta Lake Gold tables. Embeddings become columns alongside original customer attributes
- **The result is a feature table** that combines graph-derived columns (embeddings, PageRank, community ID) with tabular attributes (income, portfolio value) in a single governed table in Unity Catalog
- **Feature tables carry lineage and versioning:** you know which algorithm run produced which features, and every downstream model records which feature table version it trained on

<!--
The Spark Connector then reads those enriched nodes back into
Delta Lake Gold tables. The embedding array, PageRank score,
and community ID become columns alongside original customer
attributes like income and portfolio value.

The result is a feature table in Unity Catalog that combines
graph-derived and tabular columns. That feature table is what
the classifier trains on in the next step. Unity Catalog tracks
lineage and versioning, so you know which algorithm run produced
which features and which model version consumed them.
-->

---

## What the Feature Table Looks Like

- **Each row is a customer** with tabular features from Delta Lake (income, portfolio value) and graph features from GDS (embedding, PageRank, community ID) side by side
- **Customers with similar graph structure have similar embeddings.** Customers who share holdings and neighbors end up with embedding values pointing in the same direction
- **Community ID confirms the grouping.** Customers in the same community share dense connections in the graph
- **This combined table is what the ML model receives.** Tabular and graph features together, ready for prediction

<!--
The combined feature table holds everything the classifier needs
in a single row per customer. The tabular columns — income and
portfolio value — come from Delta Lake. The graph columns —
embedding array, PageRank score, and community ID — come from
GDS write output read back through the Spark Connector.

Customers with similar portfolio topology produce embeddings that
point in the same direction. Two customers who hold the same
stocks through similar account structures occupy similar positions
in the graph, so their fingerprints align. That alignment is
invisible in a flat table but captured by the embedding.

Community ID adds a categorical signal on top. Customers who
cluster together in the graph share dense connections and end up
in the same community. The classifier sees both the continuous
signal from embeddings and the categorical signal from community
ID — two complementary views of the same structural similarity.

This combined table is what the classifier receives. Graph-derived
and tabular features together, ready for training.
-->

---

## What Is a Classifier?

- **Pattern matcher:** learns which combinations of features correspond to which categories from labeled examples
- **Prediction:** applies those learned patterns to unlabeled rows, assigning each a category and a confidence score
- **In our example:** the classifier learns from customers whose risk category an analyst already assigned, then predicts risk categories (High, Medium, Low) for the customers who have no profile documents

<!--
A classifier is a type of ML model that assigns categories to
data. You give it examples where you already know the answer,
and it learns which feature patterns map to which categories.
Once trained, it applies those patterns to rows where the answer
is unknown.

In our portfolio example, some customers already have risk
categories assigned by an analyst through their profile documents.
The classifier learns from those labeled customers and predicts
High, Medium, or Low risk for the remaining customers who have
no documents. That is how we close the coverage gap from earlier.
-->

---

## Training a Classifier on Graph Features

- **Input:** the feature table from the previous step, with graph-derived features (embeddings, community IDs) alongside tabular attributes (income, portfolio value)
- **The classifier learns from labeled customers** and predicts risk categories for the rest
- **Multiple classifiers compete:** several different classifiers each train on the same data. Each finds patterns differently, and the best performer wins

<!--
The classifier receives the feature table we just built. Some
customers already have risk categories assigned by an analyst.
The classifier learns which feature patterns correspond to each
category, then predicts categories for the remaining customers.

Several classifiers each train on the same data. Each finds
patterns differently. Running them all reveals which approach
fits best for this dataset.
-->

---

## The Bi-Directional Data Flow

```
Neo4j GDS                    Spark Connector                  Databricks
+-----------------+          +---------------+          +-------------------+
| FastRP          |          |               |          | Gold Tables       |
| PageRank        |--write-->| Neo4j Spark   |--read--->| (Delta Lake)      |
| Louvain         |          | Connector     |          |                   |
| Node properties |          |               |<--write--| Classifier        |
+-----------------+          +---------------+          | predictions       |
                                                        +-------------------+
                                                               |
                                                        +-------------------+
                                                        | Feature           |
                                                        | Engineering in    |
                                                        | Unity Catalog     |
                                                        +-------------------+
```

<!--
Now you can see the full loop. GDS algorithms write results as
node properties in Neo4j. The Spark Connector reads those
properties into the feature table. Classifiers train on the
feature table and the best model's predictions write back
through the Spark Connector as node properties in Neo4j. The
loop is fully bidirectional: graph topology produces features,
features train models, model predictions become graph properties.
-->

---

## What Is MLflow?

- **The problem:** we just trained several classifiers on the feature table. How do we know which one performed best, and whether graph features actually helped?
- **MLflow:** Databricks' experiment tracking platform that automatically logs parameters, accuracy metrics, and the trained model for every run
- **Why it matters here:** we want to compare classifiers trained with only tabular features against classifiers trained with graph features added. MLflow makes that comparison side by side

<!--
We just trained several classifiers on the combined feature table.
That raises two questions: which classifier performed best, and
did the graph features actually help? MLflow answers both.

MLflow is Databricks' experiment tracking platform. It
automatically logs parameters, accuracy metrics, and the trained
model for every run. No manual logging code needed.

The key use for us is comparing two experiments side by side:
one trained with only tabular features, one with graph features
added. That comparison tells us exactly how much lift graph
topology contributes.
-->

---

## Measuring Graph Feature Lift with MLflow

- **This is that side-by-side comparison.** MLflow tracks two experiments against the same feature table
- **Baseline experiment:** train classifiers with only tabular features like income and portfolio value. This is the benchmark to beat
- **Graph-enhanced experiment:** train the same classifiers with graph features (embeddings, community IDs) added. The difference in accuracy shows exactly how much lift graph topology contributes

<!--
This is the comparison we set up on the previous slide. MLflow
tracks two experiments against the same feature table.

The baseline experiment trains classifiers with only tabular
features: income, portfolio value, and other attributes from
Delta Lake. This establishes the benchmark.

The graph-enhanced experiment trains the same classifiers with
graph features added: FastRP embeddings and Louvain community
IDs. MLflow shows both experiments side by side. The difference
in accuracy tells you exactly how much graph topology
contributes on top of what tabular features already provide.
-->

---

## How Classifiers and LLMs Work Together

- **Classifiers fill structural gaps:** predict missing risk categories from graph topology. Customers with similar holdings and neighborhood structure likely share a risk category
- **LLMs fill semantic gaps:** extract interests and goals from unstructured documents that no algorithm can parse
- **Each improves the other:** richer graph features (from LLM-extracted relationships) produce better classifiers. Better predictions (from classifiers) give agents more structured context to reason over

<!--
Two systems, complementary contributions. The classifier fills
structural gaps: it predicts missing risk categories using graph
topology. Customers who look similar in the graph, similar
holdings, similar neighborhood structure, likely share a risk
category. The classifier discovers that pattern.

The LLM fills semantic gaps: it extracts interests and goals from
documents that no algorithm can parse. Together, each improves
the other. The LLM-extracted relationships from enrichment make
the graph richer, which gives GDS algorithms more structure to
work with, which produces better classifier features. The
classifier's predictions become node properties that give agents
more structured context to reason over. The cycle compounds with
each iteration.
-->

---

# Keeping It All in Sync

---

## Lakeflow Jobs Pipeline

- **Lakeflow Jobs** chains the full loop as tasks:

1. **Extract** changed graph data to Delta tables
2. **Run enrichment agents** on changed documents
3. **Write approved enrichments** to Neo4j
4. **Run GDS algorithms** on the enriched graph
5. **Extract scores** to Gold tables
6. **Register updated features** in Feature Engineering in Unity Catalog

- **Human-in-the-loop** checkpoints can gate any step

<!--
Lakeflow Jobs is Databricks' workflow orchestration service. It
lets you define a pipeline as a directed acyclic graph of tasks,
where each task is a notebook, Python script, SQL query, or other
compute unit. Tasks can depend on each other, run in parallel
where dependencies allow, and retry on failure. You configure
schedules, alerts, and permissions through the Lakeflow Jobs UI
or the REST API.

For this pipeline, each step in the feature engineering loop
becomes a task. Extract pulls changed graph data into Delta
tables. Enrichment agents analyze changed documents against
current graph state. Approved enrichments write back to Neo4j.
GDS algorithms run on the updated graph. Scores extract to Gold
tables. Updated features register in Feature Engineering in
Unity Catalog.

Human-in-the-loop checkpoints can gate any step in the chain.
During early cycles, you might gate the write-back step so data
architects review proposals before they reach the graph. As
confidence grows, those gates shift to exception handling rather
than full review.
-->

---

## Incremental Sync with Change Data Feed

- **Change Data Feed:** enable on Gold tables with `delta.enableChangeDataFeed = true`. Only changes after enablement are captured
- **Structured Streaming:** a Spark Structured Streaming job detects new customers and positions, pushes deltas to Neo4j via the Spark Connector
- **Incremental enrichment triggers:** customer profile updates re-analyze that customer only. New market research triggers batch analysis of that document type
- **Cost proportional to change volume,** not total data volume

<!--
Running full analysis across all customers after every update is
prohibitively expensive. Change Data Feed on Delta tables enables
incremental processing. You enable it per table with the
delta.enableChangeDataFeed property set to true. Only changes
made after enablement are captured, so enable it before the
pipeline starts writing.

A Spark Structured Streaming job picks up changes and pushes
only the delta to Neo4j through the Spark Connector. No full
reloads. On the enrichment side, document triggers control what
gets reprocessed. A customer profile update re-analyzes that
customer only. New market research triggers batch analysis of
that document type. Costs stay proportional to what changed.
-->

---

## Key Takeaways

- **Graph features capture what flat tables miss:** network position, community membership, centrality, structural similarity
- **Feature Engineering in Unity Catalog + scikit-learn + MLflow** trains classifiers on the combined picture: graph-derived and tabular features together
- **The loop is bi-directional:** GDS scores flow to Gold tables, model predictions flow back to Neo4j via the Spark Connector
- **Lift is measurable:** MLflow tracks exactly how much accuracy graph features add over tabular features alone
- **Lakeflow Jobs orchestrates the full pipeline** end-to-end with incremental sync via Change Data Feed

<!--
Five things to take away. First, graph features capture structural
patterns that flat tables miss: network position, community
membership, centrality scores, and structural similarity.

Second, Feature Engineering in Unity Catalog and scikit-learn
train classifiers on the combined picture. Graph-derived features sit
alongside tabular features in the same governed feature table.

Third, the loop is fully bi-directional. GDS scores flow to Gold
tables. Model predictions flow back to Neo4j. The Spark Connector
handles both directions.

Fourth, lift is measurable. MLflow experiment tracking shows
exactly how much accuracy graph features add over tabular
features alone.

Fifth, Lakeflow Jobs orchestrates the full pipeline end-to-end.
Change Data Feed keeps the sync incremental. Costs stay
proportional to what changed, not total data volume.
-->
