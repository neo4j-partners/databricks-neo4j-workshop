# Lab 5 modules

Developer documentation for the Python in this folder. **The lab itself is the
notebooks**, and the concepts are on the site:
[Lab 5: The LangGraph Supervisor Agent](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab5.html).

| File | What it is |
|---|---|
| `01_langgraph_agent.ipynb` | Build the three tools, write the supervisor, wire the graph, run it, measure the routing |
| `02_deploy_and_evaluate.ipynb` | Log to Unity Catalog, deploy to Model Serving, evaluate with MLflow judges |
| `tools.py` | Node builders, the supervisor prompt, and the graph schema the text-to-Cypher tool is given |
| `agent.py` | The same graph wrapped as an MLflow `ResponsesAgent` |

## `tools.py`

Builds the three nodes and carries the two prompts that matter.

| Name | What it does |
|---|---|
| `build_genie_node` | Calls your Genie space. Needs `GENIE_AGENT_ID` |
| `build_cypher_node` | Text to Cypher, run in a read transaction, one retry with the error attached |
| `build_graphrag_node` | `VectorCypherRetriever` over `maintenanceChunkEmbeddings`. Returns a self-explaining stub if the index is missing, rather than raising |
| `SUPERVISOR_PROMPT` | Routes on where a question *starts*, not on what a tool does at the end |
| `GRAPH_SCHEMA` | The schema string given to the Cypher tool |

`GRAPH_SCHEMA` is not generated from the live graph and should not be. It states
relationship directions explicitly, tells the tool to refuse reading questions
instead of substituting an operating limit for a measurement, and names the
failures each rule prevents. A schema promising labels the graph does not have
produces queries that return zero rows with no error. **Edit it when the graph
shape changes, and re-run Section 9 of notebook 01 to confirm routing held.**

### What `GRAPH_SCHEMA` says about `OperatingLimit`

The twenty canonical limits Lab 2 loads from CSV: four parameters for each of
five aircraft models. Never empty, never duplicated, no filter needed. The rules
in the schema exist because each of these was got wrong:

- **A limit is not a measurement.** `maxValue` is a model-wide ceiling from a
  manual, so it can never answer "what was the average" or "which is highest".
- **Ten have no floor.** `minValue` is null on the Vibration and N1Speed limits
  for all five models. Check `IS NOT NULL` before comparing. Both bounds are
  `FLOAT`, so nothing needs casting.
- **All belong to a regime.** A takeoff bound held against cruise readings
  reports the whole fleet out of range.
- **Extraction writes a different label.** Lab 3 notebook 01 writes
  `ExtractedLimit`, never `OperatingLimit`. The two never mix. `ExtractedLimit`
  varies between graphs and is empty when Lab 3 ran without extraction. Treat
  `OperatingLimit` as the authority.

## `agent.py`

The notebook-01 graph as an MLflow `ResponsesAgent`, which is what gets logged
and served. It reads credentials from **environment variables** bound to
`{{secrets/<scope>/<key>}}` rather than from `dbutils`, because `dbutils` does
not exist inside a serving container, and everything else from model config
logged beside it.

`FleetOpsAgent` is the class Lab 6 subclasses. It does it in `memory_agent.py`,
which notebook 01 of Lab 6 writes out with `%%writefile` rather than shipping on
disk, so read that cell to see the subclass. The registered model
name and the endpoint name are constants here rather than strings a participant
types, because Lab 6 redeploys **this** endpoint rather than creating a second
one. Renaming either breaks Lab 6.

## Cross-lab imports, and why the folders must stay siblings

`tools.py` imports the embedder, the LLM and the secret-scope helpers from
`../Lab_3_Semantic_Search/data_utils.py` rather than carrying copies. That is not
tidiness: the vectors in your `maintenanceChunkEmbeddings` index were written by
that embedder, and a query embedded by a different model does not match them.

`Lab_6_Agent_Memory/memory.py` in turn imports from both `data_utils.py` and this
folder's `tools.py`. **Keep `Lab_3_Semantic_Search`, `Lab_5_LangGraph_Agent` and
`Lab_6_Agent_Memory` as siblings**, in the repository and in the workspace, and
every import resolves on its own. Moving any one of them breaks the other two.

## Measured results

Routing accuracy, the anchor question, and the caveat on both are on the
[site page](https://neo4j-partners.github.io/databricks-neo4j-workshop/databricks-neo4j-workshop/1.0/lab5.html#measured-routing).
Section 9 of notebook 01 is what reproduces them. **If you edit
`SUPERVISOR_PROMPT`, re-run it and update the site page.**
