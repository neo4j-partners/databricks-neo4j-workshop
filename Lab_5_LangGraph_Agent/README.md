# Lab 5 - The LangGraph Supervisor Agent

In this lab you build the agent the workshop has been assembling parts for. It
routes a question across three stores: the Genie space from Lab 4 Part A for
sensor telemetry, Cypher over the fleet graph from Lab 2, and the GraphRAG
retrievers from Lab 3 for the maintenance manuals.

> **Infrastructure:** This lab uses your **personal** Aura instance, the one you
> loaded in Lab 2 and enriched in Lab 3, plus your own Genie space. Nothing here
> writes to the graph.

## Prerequisites

| Lab | What this lab needs from it | Required |
|---|---|---|
| [Lab 2](../Lab_2_Databricks_ETL_Neo4j) | Aircraft, System, Component, Flight, Delay, MaintenanceEvent, Removal in your Aura instance | Yes |
| [Lab 3 notebook 01](../Lab_3_Semantic_Search/01_data_and_embeddings.ipynb) | The `fleet-ops-<your-user>` secret scope, and the `maintenanceChunkEmbeddings` vector index | Yes for three tools |
| [Lab 3 notebook 02](../Lab_3_Semantic_Search/02_graphrag_retrievers.ipynb) | Understanding of `VectorCypherRetriever`, which `graphrag_node` is built from | Recommended |
| [Lab 3 notebook 03](../Lab_3_Semantic_Search/03_hybrid_retrievers.ipynb) | The `maintenanceChunkText` fulltext index, for the optional Section 10 exercise | Optional |
| [Lab 4 Part A](../Lab_4_Compound_AI_Agents/PART_A.md) | Your Genie space, and its space ID | Yes |

Lab 4 Part B is not a prerequisite. Its routing instructions are where this
lab's supervisor prompt started, and you can read them without having built the
Agent Bricks version.

## Files

| File | What it is |
|---|---|
| `01_langgraph_agent.ipynb` | Build the three tools, write the supervisor, wire the graph, run it, measure the routing |
| `tools.py` | Node builders, prompts, and the graph schema the text-to-Cypher tool is given |

`tools.py` imports the embedder, the LLM, and the secret-scope helpers from
`../Lab_3_Semantic_Search/data_utils.py` rather than carrying copies. That is not
tidiness. The vectors in your `maintenanceChunkEmbeddings` index were written by
that embedder, and a query embedded by a different model does not match them.
Keep the two lab folders as siblings, in the repository and in the workspace, and
the import resolves on its own.

## What you build

```
                    question
                       |
                       v
              +------------------+
              |    supervisor    |<---------+
              | Llama 3.3 70B    |          |
              +------------------+          |
                       |                    |
        +--------------+--------------+     |
        v              v              v     |
  +-----------+  +-----------+  +----------------+
  | genie     |  | cypher    |  | graphrag       |
  | Delta     |  | Neo4j     |  | Neo4j vector   |
  | telemetry |  | traversal |  | + Cypher tail  |
  +-----------+  +-----------+  +----------------+
        |              |              |     |
        +--------------+--------------+-----+
                       |
                       v
                  synthesize --> answer
```

Each tool reports back to the supervisor rather than answering. That edge is what
separates a supervisor from a router: a router picks one tool and is done, while
this one sees what came back and gets to pick again. It is also what lets a
single question use three tools in sequence, each choice informed by the last
result.

### The three tools

**`genie_node`** asks your Genie space, which writes SQL over the four Lakehouse
tables and runs it. This is the only tool that can see a sensor reading. Your
graph has `Sensor` nodes with no readings on them, because 155,000 timestamped
values belong in Delta where scanning them is cheap.

**`cypher_node`** generates Cypher from the question and runs it in a read
transaction. The schema it is given is the one your graph actually has, which
matters: a schema promising nodes that are not there produces queries returning
zero rows and an agent that says it found nothing. A failed query gets one retry
with its error message attached, because most text-to-Cypher failures are a
mistyped property or a relationship pointing the wrong way, and the error says
which.

**`graphrag_node`** is the Lab 3 notebook 02 retriever, wrapped as a node. The
question is embedded, the vector index returns the closest manual chunks, and a
Cypher tail runs from each hit. The tail is the point. It walks sideways along
`NEXT_CHUNK`, so a procedure split across a chunk boundary arrives whole, and
upward through the `Document` to the aircraft the manual applies to. Neither of
those is in the embedding. Both are one hop away in the graph.

### The prompt is the lab

The wiring is thirty lines and it is not the interesting part.

`cypher_node` and `graphrag_node` both end in a Neo4j traversal. A supervisor
that describes its tools by what they do at the end cannot tell them apart, and
it sends manual questions to Cypher, where they return nothing, because manual
text is not a property you can filter on.

So the prompt tells the model to decide on where the question **starts**:

> Starts with a name you could put in a `WHERE` clause -> `cypher_node`
> Starts with a phrase you would search a manual for -> `graphrag_node`

Section 9 of the notebook measures this. It runs twelve questions through the
supervisor alone and reports the `cypher_node` against `graphrag_node` number
separately from the overall score, because folding the hard pair into an average
hides the one thing worth knowing.

## Running the lab

1. Open `01_langgraph_agent.ipynb` on a Databricks cluster or serverless notebook.
2. Set `GENIE_SPACE_ID` in Section 1 to your own space ID, from the Genie space URL.
3. Run the cells in order.

Section 1 also holds a commented-out block that creates the secret scope. It is a
recovery path for anyone who skipped Lab 3, not the normal path. Leave it
commented out unless the next cell tells you the scope is missing.

## If you skipped Lab 3 notebook 01

`graphrag_node` reads the `maintenanceChunkEmbeddings` vector index, and without
it `VectorCypherRetriever` raises. Rather than turning a skipped notebook into a
failure several cells before the agent exists, the builder checks for the index
first and returns a node that explains itself. The agent still compiles, still
runs, and answers from telemetry and the graph.

You will see this in Section 5, and the supervisor drops to two tools in Section
6. Run Lab 3 notebook 01 and all three come back with no other change.

## What the operating limits will and will not do

`OperatingLimit` is never empty. Lab 2 loads twenty canonical limits from CSV,
four per aircraft model, and each one carries a `limit_id`. Three consequences
follow.

**A name can appear twice.** Lab 3 notebook 01 also extracts operating limits
from the manual prose, and its prompt mandates the same
`<parameterName> - <aircraftType>` name the CSV uses. `EGT - A320-200` can
therefore exist twice with different bounds. Only the canonical copy has a
`limit_id`, so the schema in `tools.py` tells the model to filter
`WHERE ol.limit_id IS NOT NULL` when the question asks for the documented or
official limit.

**Ten have no floor.** `minValue` is null on ten of the twenty, the Vibration
and N1Speed limits for each of the five models, because those are ceilings and
nothing else. The schema says to check `IS NOT NULL` before comparing. Both
bounds are Double on both populations, so nothing needs casting.

**All belong to a regime.** Each limit carries the phase of flight it applies
to. A takeoff bound held against cruise readings is a category error rather
than a comparison, and it reports the whole fleet out of range.

## What comes next

Notebook 02 logs this graph as an MLflow model, deploys it to Model Serving, and
evaluates it against a question set with MLflow's LLM judges. Lab 6 gives it
memory, in Neo4j, so it can be asked a follow-up.
