# Expand v2: Labs 5 and 6, Plan of Record

Supersedes the status and planning halves of `expand.md`. The reasoning, the measurements, and the defect narratives stay in `expand.md` and are cited here rather than copied. Where the two disagree on what is done, this document wins, because its status was checked against the code on disk on 2026-08-08.

**Last status pass: 2026-08-09, against `HEAD` at `1be478f` with three modified files, `Lab_6_Agent_Memory/01_agent_memory.ipynb`, `Lab_6_Agent_Memory/memory.py` and this file.** `1be478f` swept in `tools.py`, `agent.py`, `lab/workshop.py`, `Lab_5_LangGraph_Agent/02_deploy_and_evaluate.ipynb` and both Lab 6 notebooks, so the Lab 5 work described below is committed rather than pending.

**Closed this pass, both verified rather than inferred.** `genie_node` authorization is fixed: the endpoint holds three READY versions, and a fleet-average EGT question routed to `genie_node` and returned **866.65373875 C**, matching the rebuilt CSV average of 866.7 with no authorization error anywhere in the response. Defect F is fixed and measured at 0 invented, 0 loose and 0 zero-row across 10 after-runs. The gold-table Genie edit is applied. Before that: the Lab 6 `CALL {}` blocker is fixed, the resource list moved into one shared `build_resources` at `agent.py:147` and grew from four entries to twelve, and Lab 6 now registers into the same UC model Lab 5 created rather than logging an unregistered run. The pass before that landed `b82ca4b` and `5fb3097`, closing 9.1; rebuilt the lakehouse gold tables; fixed defect E; and closed 16 of 24 documentation findings.

**Two things a reader should not misread.** The `neo4j-database` change is **still uncommitted** and has grown to 14 modified files, so `HEAD` at `5fb3097` shows none of this. And the Lab 6 timing measurement, which is Phase 3's completion criterion, is **still unmeasured**: two attempts have now failed for environment reasons rather than lab reasons, and the third is running. Every line below follows the section 8 rules: three states, evidence named, verified against disk.

---

## 1. The Goal, and Why

**What we are building.** Two new required labs at the end of the workshop. Lab 5 is a LangGraph supervisor agent that routes across three tools: Genie over Delta telemetry, Cypher over the participant's own Aura instance, and GraphRAG over the maintenance manuals. Lab 6 gives that agent memory in the same Aura instance.

**The problem they fix.** Labs 1 through 3 build a graph in the participant's own database. Lab 4 Part B then answered questions against somebody else's database over a shared MCP server, and told participants so in writing. The workshop's payoff moment used none of the participant's work, and the Lab 3 GraphRAG retrievers were never wired into an agent at all.

**The shape of the fix.** Part B becomes a 10 minute instructor demo. Lab 5 becomes the single participant continuation from Part A. Every required lab now reads and writes one database, and each lab's output is the next lab's input. Lab 2 loads the fleet, Lab 3 adds manuals and vector indexes, Lab 5 queries both, Lab 6 writes memory back.

**Why the memory lab is the ending.** Memory nodes and fleet nodes land in one graph, so one Cypher traverses both. The headline demo asks which aircraft several technicians independently asked about this week, and whether those are the ones actually failing. Neither the fleet graph nor the memory graph answers it alone. That is the argument for doing memory in Neo4j rather than in a memory product.

**Result.** Roughly five hours of required lab time, a full-day advanced format, with a half-day split as a later, best-effort option.

---

## 2. What Is Done

Verified against code on disk unless marked otherwise.

### Loader and data

- **`databricks` embedding provider.** `populate_aircraft_db` embeds through `databricks-bge-large-en`, the same endpoint Lab 3 uses. Cross-path cosine measured at 1.0000000000, so embedder drift is gone rather than mitigated.
- **`--skip-extraction` flag.** Loads a Lab 5 shaped graph with no LLM key. Assembles the library's own splitter, embedder, lexical graph builder and writer, so Document and Chunk nodes match the full path.
- **Deterministic `OperatingLimit` loading.** 20 canonical rows from `workshop-setup/aircraft_digital_twin_data/nodes_operating_limits.csv`, 288 `HAS_LIMIT` edges, no LLM. `limit_retriever` from Lab 3 notebook 02 returns populated results on a skip-extraction graph.
- **Sensor units normalized.** `EGT` to `°C`, `N1Speed` to `% RPM`, matching the manual limit tables. 288 sensors join `OperatingLimit` on a plain string compare, 0 do not.
- **N1Speed magnitudes fixed.** Readings are now percent of an `n1_reference_rpm` per engine, measured in the 94 to 100 range against limits of 92, 100 and 104. `specs.py` carries the reference and the calibration comment.
- **`ExtractedLimit` split landed.** Extraction writes `ExtractedLimit`. `OperatingLimit` means the 20 CSV rows. Present in `schema.py`, `Lab_3_Semantic_Search/data_utils.py`, all three Lab 3 notebooks, `SAMPLE_QUERIES.md`, and the Lab 5 tools.
- **`OperatingLimit` constraint keyed on `limit_id`.** `schema.py:26`. Matches Lab 2's notebook. The old `name` constraint killed two live enrichment runs.
- **`populate-aircraft-db` startup fixed.** `neo4j_database` is a real settings field at `config.py:33`, so Pydantic no longer raises `extra_forbidden` on every subcommand.
- **Full load measured.** Empty Aura instance to complete graph in 4 minutes 23 seconds, no OpenAI or Anthropic key. Idempotent: a second run finished in 4 minutes 9 seconds with node counts unchanged.
- **MEASURED: GraphRAG enrichment loaded without an LLM key**, through `enrich --skip-extraction`. 5 `Document`, 286 `Chunk` all embedded, both indexes ONLINE, 20 `OperatingLimit` from CSV. **Only the LLM-extracted entities are missing, `ExtractedLimit` among them.** Everything the GraphRAG lab needs is on the graph.

### Lab 5 core

- **Three tools built and live.** `genie_node`, `cypher_node`, `graphrag_node`, the last on `VectorCypherRetriever` lifted from Lab 3 notebook 02.
- **Routing measured.** 38 cells, 0 errors, 12 of 12 overall, 4 of 4 per tool, **8 of 8 on the hard `cypher_node` versus `graphrag_node` slice**. Run against a rebuilt participant-shaped instance carrying zero `Reading` nodes, which is what makes the numbers mean anything.
- **Anchor question runs end to end.** Genie named the engines with abnormal EGT, the graph returned their maintenance history including a bearing wear fault, and the manual's high-EGT procedure closed the answer.
- **Supervisor model settled.** `databricks-meta-llama-3-3-70b-instruct`, one constant, one endpoint across Labs 3 and 5.
- **Credential wiring done.** Lab 5 reads the `fleet-ops-<user-slug>` secret scope Lab 3 notebook 01 creates. No plaintext password in Lab 5. A scope-creation block sits commented out as the recovery path.
- **Degradation path done.** A missing vector index drops `graphrag_node` from the routing list through `available_tools` instead of raising at import.
- **Cypher refusal rule landed.** `tools.py:255`, never substitute a limit, threshold or ceiling for a measurement. Unmeasured: the 12 of 12 run predates it.
- **Routing re-measured once, at 19 of 20**, then invalidated by the defect fixes that run produced. `worklog/lab5-test-results.md`, and see 9.3. Superseded by the regression suite below, which was run against the current file.
- **MEASURED: defects A, B and C fixed, regression suite 48 of 48 across 9 groups.** B was a string-literal masking bug in the write guard. `MATCH (r:Removal)` was never a false positive, and any note claiming otherwise is wrong.
- **MEASURED: defect E fixed and verified, committed as `5fb3097`, a 9-line addition and nothing else.** `cypher_node` wrote the `AFFECTS_AIRCRAFT` arrow backwards, deterministically 5 runs of 5, generating `MATCH (a:Aircraft {tail_number:'N10004'})-[:AFFECTS_AIRCRAFT]->(me:MaintenanceEvent)`. The relationship runs from `MaintenanceEvent` to `Aircraft`, so it matched nothing and **returned zero rows with no error**, while `N10004` actually has 23 maintenance events, more than any other aircraft in the fleet. Root cause: `AFFECTS_AIRCRAFT` is the only relationship in the schema pointing toward `Aircraft`, and `Aircraft` is the noun nearly every question starts from, so the model anchored on the named noun and pointed the arrow away from it. Fixed with a `GRAPH_SCHEMA` bullet at `tools.py:286-294`. After: 0 of 5 zero-row runs, 23 rows with real `CRITICAL`/`MAJOR`/`MINOR` severities, direction sweep 0 misses of 6, regression suite 48 of 48.
- **MEASURED: defect F fixed, an 11-line `GRAPH_SCHEMA` addition at `tools.py:295-305`.** The components-for-an-aircraft question was nondeterministic. Ten runs before the fix produced six distinct queries: **4 of 10 invented an `AFFECTS_COMPONENT` relationship that does not exist in the graph**, 3 of 10 walked the loose `AFFECTS_SYSTEM` then `HAS_COMPONENT` chain, 3 of 10 were correct. Ten runs after: 0 invented, 0 loose, 0 zero-row, all ten writing the identical `MATCH (c:Component)-[:HAS_EVENT]->(me:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(a:Aircraft {tail_number: 'N10004'})`. Ground truth read from `f024ea61` is **9 distinct components carrying 23 events**; the loose chain reached 10, the extra being `AC1005-S01-C05`, which never had an event and appears in no after-run. Regression 48 of 48, group 5 refused 3 of 3, group 8 refused 5 of 5, nothing written to the graph. Recorded as Round 4 in `worklog/lab5-test-results.md`.
- **The invented relationship is the finding that matters, and it was worse than the defect as first reported.** A wrong-but-real traversal returns a wrong-ish answer somebody might question. A relationship type that does not exist **does not error**. Neo4j matches nothing and returns zero rows, so the agent reports "no components found" with total confidence about an aircraft that has 9 of them. It is the failure mode that cannot be caught by reading the output, and the first report of defect F, 0 rows then 25 rows, understated it by describing only the loose-chain half.
- **Residual, accepted.** After-run row counts still vary, 9 seven times, 10 twice, 23 once. The traversal is identical every time and the variance is projection: some runs add `me.fault`, `me.severity` or `me.event_id` to the `RETURN DISTINCT` and fan the rows back out. No run returns zero and no run returns the wrong component set, so the participant-facing failure is gone. Pinning the projection would mean dictating output columns per question shape, which is the over-constraining that produced defect A.

### Lab 5 deployment

**State: LANDED, and MEASURED in part. The endpoint exists. The one measurement that closes Phase 2 has not been taken.**

- **MEASURED: a deployed endpoint, with a persisted baseline.** `fleet-ops-assistant-ryan-knight-neo4j-com`, from UC model `databricks-neo4j-workshop.agents.fleet_ops_assistant` version 1, on `aws-partner-rk`. Cold deploy 15.8 minutes, deploy call `2026-08-08T23:41:44Z`, ready by `23:57:42Z`. `endpoint_shared_with_lab6: true`, so the one-endpoint decision held. Full artifact: `worklog/lab5_memory_off_baseline.json`.
- **MEASURED: routing survives the trip through Model Serving.** Six questions. The artifact's own `results_interpretation` names what is valid, `tools_called`, `available_tools` and `latency_seconds`, and what is not: the usage block, which is always empty, every number sourced from `sensor_readings`, and every answer whose `tools_called` includes `genie_node`.
- **MEASURED: the Phase 2 memory-off baseline is captured and persisted.** `worklog/lab5_memory_off_baseline.json`. Endpoint `fleet-ops-assistant-ryan-knight-neo4j-com`, model version 1, six questions with ordered tool calls, answers and latency. It carries a `neo4j_provenance` block stamping instance `f024ea61` with `agent_memory_schema_installed: false`, and a `lakehouse_provenance` block marking the state as pre-rebuild with the four measured ranges.

  **Four caveats ship with it and must be read beside it.** `genie_node` was unauthorized at capture time, so routing is valid and Genie answer text is not. The endpoint returns an empty usage block, so there are no token counts, only latency. Three of six questions called more tools than expected, because the supervisor retries on an empty or failed tool, so **expected-tools is a subset test, never an exact match**. And the `cypher_maintenance_history` answer is known-bad, captured before defect E was fixed: **a memory-on run returning 23 events is the defect E fix landing, not memory improving recall.**
- **MEASURED: a `DatabricksGenieSpace` resource on its own does not reach the warehouse under the space.** The endpoint deployed cleanly, routed correctly, and answered every sensor question with "is not authorized to use or monitor this SQL Endpoint".
- **LANDED: the fix for it, and it is now twelve resources rather than four.** `Lab_5_LangGraph_Agent/agent.py` gained `GOLD_SCHEMA`, `GOLD_TABLES` and `build_resources(genie_space_id, warehouse_id)`, which returns the Genie space, the SQL warehouse, the **eight gold `DatabricksTable` entries**, and the two `DatabricksServingEndpoint` entries. `02_deploy_and_evaluate.ipynb` cell 7 and `Lab_6_Agent_Memory/01_agent_memory.ipynb` cell 50 both call it, so the two labs cannot drift. `mlflow.models.resources` is imported inside the function, because it is a log-time API the serving container never calls. **Unmeasured: the redeploy is running as this line is written.** This is still the single item between here and Phase 2's completion criterion.

  **Why the tables joined the list.** Declaring the space grants the space and declaring the warehouse grants the compute. Neither grants the data. The four-entry list was written from an error message naming the SQL endpoint, and it was never tested against a query that reads a table.
- **LANDED: `02_deploy_and_evaluate.ipynb`**, 30 cells, 13 code, committed in `b82ca4b`. Configuration, a pre-log run, resources, log, credentials, deploy, wait, ask, evaluate, and a "when it fails" section. Closes the Lab 5 README gap that the documentation audit flagged.
- **LANDED: `pip_requirements` pinned rather than inferred.** Inferred requirements read the cluster, and a cluster carrying the Lab 6 memory wheel yields a requirement with a local version segment that resolves from no index. The container then fails to build about fifteen minutes after anybody stopped watching. Recorded at `Lab_5_LangGraph_Agent/README.md:240-244`.

### Memory research

- **Spike verdict: GO, with two hard conditions.** Full report in `worklog/memory-spike.md`.
- **Provider question settled.** The library hard-codes no provider. About 130 lines of adapter binds Databricks Foundation Model endpoints through `mlflow.deployments`, verified live.
- **Version pinned.** `0.5.1.dev0+mentions`, a wheel built from the `mentions` branch of the `neo4j-partners` fork, checked in at `lab/courseware/wheels/`.
- **Upstream defect found and fixed.** Released 0.5.0 silently drops every `MENTIONS` edge, which is the exact edge the headline query traverses. Fix written, tested with three regression tests, pushed to the fork.
- **Headline demo measured.** Adoption of 36 `Aircraft` in 3.1 seconds. The joining Cypher runs in 0.6 to 0.7 seconds and produces a genuine "neither source alone" answer on `N10011`.
- **Pacing measured.** 5.6 seconds per message in explicit mode, 9.2 with auto extraction, 22.4 seconds for first connect and schema creation.

### Lab 6, files on disk

**State: LANDED. Nothing here is MEASURED, because no notebook in this lab has been executed end to end against a live instance.**

- **`Lab_6_Agent_Memory/` exists**, four files, written 2026-08-08. `memory.py` at 47,359 bytes, `01_agent_memory.ipynb` at 54 cells, 29 code and 25 markdown, `02_instructor_demos.ipynb` at 32 cells, 21 code and 11 markdown, `README.md` at 383 lines and 2,629 words. Every code cell parses under `ast.parse`. No escaped-quote leaks and no forbidden instance id in either notebook.
- **`memory.py` carries the adapters, the nodes, the seed helper and the headline Cypher**, mirroring Lab 5's `tools.py` as decided. Ruff-clean under the project's own `select` of `E,W,F,I,B,C4,UP,SIM`. A bare `uvx ruff check` reports four RUF100 "unused noqa" hits, which is a false positive: ruff's default rule set excludes E402, and under the project config those `# noqa: E402` directives are required, because the Lab 3 and Lab 5 imports follow `ensure_labs_on_path()`.
- **`memory.py` passes the FILE-not-NOTEBOOK check.** First line is a docstring, not `# Databricks notebook source`. It fails the other Phase 4 check for now, since it has to ship together with the notebook that imports it.
- **The adapters are named `MemoryEmbeddings` and `MemoryLLM`**, as decided, and the README carries the one section explaining why the two libraries want different Protocols. The Protocols are async: `embed` and `embed_one` on the embedder, `complete` and `complete_structured` on the LLM.
- **All nine names `memory.py` imports from Lab 3 and Lab 5 still resolve** after a peer session edited `Lab_5_LangGraph_Agent/tools.py`. Re-verified rather than assumed.
- **The four pinned-version research answers moved into `Lab_6_Agent_Memory/README.md`**, out of `expand.md`, as section 8 requires: exact version, the API surface this lab depends on, the Neo4j version floor, and the owner and re-check cadence.
- **Three library API defects found and fixed before execution**, each caught by reading the unzipped wheel rather than trusting prose. `HAS_TOOL_CALL` does not exist and the edge is `USES_TOOL`. `TOUCHED` hangs off `ReasoningStep`, not `ToolCall`, per `graph/queries.py:668` and `memory/reasoning.py:608`. `ToolCallStatus.FAILURE` does not increment `Tool.failed_calls`; only `error` and `timeout` do, per `queries.py:526`, so the routing demo uses `ToolCallStatus.ERROR`.
- **LANDED: the `CALL {}` blocker in cell 20 is fixed, and it closes section 5 question 14.** The counts query is now three `MATCH` clauses joined by top-level `UNION` rather than a `CALL {...UNION...}` subquery. **The guard was narrower than first reported.** `neo4j_agent_memory/core/query.py:26-50` rejects on `r"\bCALL\s+\{"` only, so `CALL db.labels()` and `CALL apoc.x()` were always fine; the earlier claim that the guard rejects `CALL` outright is wrong. The rewrite dodges the one pattern that fires and needs no library change. **Measured only as far as a run reaching cell 20**, which is what the in-flight job settles.
- **LANDED: Lab 6 registers into the same UC model Lab 5 created.** Cell 50 previously called `log_model` with no `registered_model_name` and no `mlflow.set_registry_uri("databricks-uc")`, so it produced a run artifact and nothing an endpoint can point at, while cell 51's markdown snippet named a `version` variable nothing defined. Cell 50 now sets the registry URI, passes `registered_model_name=UC_MODEL_NAME`, and prints `MODEL_VERSION` and `ENDPOINT_NAME`; cell 51's snippet uses both and passes `endpoint_name=` explicitly. **Without that argument `agents.deploy` invents a name from the model**, which is the second endpoint the one-endpoint decision exists to prevent.
- **LANDED: `WAREHOUSE_ID` joins `GENIE_SPACE_ID` in Lab 6's configuration cell**, with the same empty-value warning. Section 10 declares it through `build_resources`.

### Lab 6, workspace findings

Measured against `aws-partner-rk`, host `dbc-cc887abc-9779`, on 2026-08-08.

- **MEASURED: `restartPython()` in Section 1 of both notebooks is load-bearing.** The lab's install line takes `typing_extensions` from 4.4.0 to 4.16.0 and `pydantic` from 1.10.6 to 2.13.4. Importing `neo4j_agent_memory` in the same already-running interpreter raises `ImportError: cannot import name 'Sentinel' from 'typing_extensions'`, because the preloaded 4.4.0 shadows the new install. A fresh interpreter, which is what `restartPython()` produces, imports cleanly. **The install line is correct as written and needs no change.** Recorded because the error message names `typing_extensions` and gives no hint that the fix is a restart, so a participant who skips that cell will not self-diagnose.
- **LANDED: the wheel now exists in this workspace's volume.** `neo4j_agent_memory-0.5.1.dev0+mentions-py3-none-any.whl` was absent from `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/` and has been uploaded by hand. Section 1 of both notebooks would have failed here before that. **This is a property of this one workspace, not a gap in the provisioning path.** `lab/workshop.py:224` defines `WHEELS_DIR`, `:714` resolves it and `:734` enumerates the wheels, so a Vocareum provision does upload it. `aws-partner-rk` is a plain workspace that was never provisioned that way. Corrects an earlier note here that read "nothing in the provisioning path puts it there yet", which was wrong.
- **MEASURED: a test run against a stale workspace copy fails as a lab defect and is not one.** A Lab 6 job failed at 80 seconds with `KeyError: 'database'` from `read_neo4j_secrets`, because `agent.py` had been uploaded to the test workspace and `data_utils.py` had not. The traceback names the notebook line and nothing about staleness. **The lesson is a step, not a note:** upload every module the notebook imports, then verify each by exporting it back and diffing against the local file. Four files matter here, `Lab_3_Semantic_Search/data_utils.py`, `Lab_5_LangGraph_Agent/tools.py`, `Lab_5_LangGraph_Agent/agent.py` and `Lab_6_Agent_Memory/memory.py`, and a workspace `import` of one of them silently leaves the other three at whatever they were.
- **MEASURED: Lab 6 gets its dependencies from cluster libraries, not from its own `%pip` line, and the delivery path is sound.** `lab/course.env:71` `VOC_COURSE_LIBRARIES` installs `neo4j`, `langgraph`, `pydantic`, `langchain-core`, `databricks-langchain`, `neo4j-graphrag`, `databricks-agents` and the memory wheel itself as cluster libraries. Labs 3 and 5 carry no `%pip` cell at all and rely on this entirely. Lab 6's `%pip` line therefore covers the wheel a second time, which is harmless. **No Lab 6 defect here.** Recorded because a serverless job run outside Vocareum gets none of those libraries and fails at `data_utils.py:22` on `neo4j_graphrag`, which reads like a lab bug and is not one. Any test harness outside Vocareum has to install the `course.env` set itself.

### Lakehouse gold tables

- **MEASURED: the four gold tables held values from an older generator run on the wrong scale, and were dropped and rebuilt on 2026-08-08.** `worklog/lakehouse-rebuild.md`, warehouse `b0fffb8e3255bf85` on `aws-partner-rk`. Rebuilt by the DLT pipeline "Fleet Digital Twin ETL", pipeline `a9859aeb-a5e3-4087-812f-a384160d3cbd`, update `d8e7107e-10e0-4f9f-94d0-61638012d0c8`.
- **MEASURED: before and after, per sensor type.** Min to max, average in the middle.

  | type | was | now |
  |---|---|---|
  | N1Speed | 2500.7 to 5282.7, avg 4648.3 | 75.2 to 107.1, avg 93.5 |
  | EGT | 616.0 to 731.1, avg 654.6 | 635.8 to 1072.9, avg 866.7 |
  | FuelFlow | 0.8 to 1.5, avg 1.1 | 1.0 to 2.1, avg 1.4 |
  | Vibration | 0.1 to 1.1, avg 0.3 | 0.1 to 1.1, avg 0.3 |

  All four now match the committed CSVs exactly.
- **The N1Speed defect was the serious one.** The tables were in RPM while the graph, the CSVs and the documented `OperatingLimit` of 97.0 are in percent, so **Genie answered N1 questions with 5283 against a limit of 97**. Row counts already matched; only values were wrong.
- **MEASURED: all eight gold tables now exist**, at parity with the graph. `aircraft`, `systems`, `sensors`, `sensor_readings`, `flights`, `maintenance_events`, `fleet_readiness`, `sensor_health`. **The last four did not exist before.** Counts: 155,520 readings, 288 sensors, 144 systems, 36 aircraft, 14,543 flights, 286 maintenance events. `aircraft_pipeline` went from empty to 32 tables, 22 bronze and 10 silver. The genie stage applied 18 comments and 8 grants.
- **The blocker that had to be cleared first.** DLT refuses to materialize over a table it does not own, failing with "Could not materialize ... because a MANAGED table already exists with that name". The four tables had been created 2026-06-12 by Spark with no owning pipeline, so they had to be dropped.
- **A fifth table, `aircraft_fleet_metrics`, was deliberately left in place.** It is produced by no current pipeline and referenced nowhere in the repository. Section 5 asks what happens to it.
- **This dates the memory-off baseline a second time.** The artifact records `lakehouse_provenance: pre-rebuild`. See 9.4.

### Instance `f024ea61`

The Track A Lab 5 measurement graph, and the instance the secret scope points at.

- **MEASURED: `f024ea61` verified after the Lab 6 agent-memory schema landed on it. Adoption was correctly scoped to `Aircraft` only.** `System.type` still holds Avionics/Engine/Hydraulics, `Sensor.type` still holds EGT/FuelFlow/N1Speed/Vibration, `Component.type` still holds its 12 values. `Aircraft` now carries `type='AIRCRAFT'` and an `:Entity` label, on exactly 36 nodes. **That is inert for Lab 5**, because `tools.py` uses a static `GRAPH_SCHEMA` and never introspects the database. All fleet counts unchanged.
- **MEASURED: GraphRAG survived the adoption.** `maintenanceChunkEmbeddings` VECTOR ONLINE, `maintenanceChunkText` FULLTEXT ONLINE, 286 of 286 `Chunk` embedded, 59 indexes in total.
- **MEASURED: `f024ea61` has no database named `neo4j`. Its home database is named after the instance.** A `database="neo4j"` call fails with `DatabaseNotFound` while `verify_connectivity()` and anything routed at `system` succeed, so **the instance looks healthy right up to the first real query**. `agent.py` already resolves the name by asking the server, in `resolve_database`. See section 5.
- **MEASURED: `resolve_database` cannot rescue this instance on its own, and that is by design.** It returns `neo4j` when present, the sole database when there is exactly one, and raises otherwise. `f024ea61` holds two databases and neither is `neo4j`, so an endpoint deployed without `NEO4J_DATABASE` raises at startup with a message telling the reader to store the name as the `neo4j-database` key. **Correct for participants and fatal here**, because AuraDB Free serves exactly one database named `neo4j` and hits the first branch.
- **LANDED: the `neo4j-database` key now exists in `fleet-ops-ryan-knight-neo4j-com`.** The scope held three keys, so `read_neo4j_secrets` returned the `neo4j` fallback and `serving_environment_vars` omitted the variable entirely, breaking both the notebook path and the endpoint path in different ways. The key was written with the instance's home database name, read from `SHOW DATABASES YIELD name, home`, with no value printed and the URI asserted against `neo4j+s://f024ea61` first. **This is a development-scope repair, not a lab change.** A participant scope written by Lab 3 notebook 01 carries the right value from the start.

### Documentation

- **MEASURED: 24 factual-drift findings across every top-level, lab and setup markdown file. 16 fixed.** `worklog/docs-audit.md`. All 4 BLOCKING and all 12 MAJOR are fixed and committed in `b82ca4b`. Every claim was checked against code on disk, with no write and no Neo4j instance touched. The 8 remaining are MINOR or out of scope and are carried in section 3.

### Capacity

- **Aura node budget measured.** A participant finishing Labs 1 through 3 holds about 21,613 nodes, 10.8 percent of the AuraDB Free cap, with roughly 178,000 nodes of headroom. Memory costs about 20 nodes per participant per session. Full analysis in `worklog/aura-node-budget.md`.
- **The 59 indexes coexisting on `f024ea61` prove nothing about AuraDB Free.** `f024ea61` is a multi-database instance and is not Free. **Participants get Free.** Read the 59 as evidence the schema installs, never as evidence the cap tolerates it. The index tolerance check in section 3 is still unrun and still needs its own fresh Free instance.

### Content and cleanup

- **Lab 4 Part B reframed.** Instructor-demo banner in place at `PART_B.md:1`. Procedure kept in full.
- **`Lab_1_Aura_Setup/Aura_Free_Trial.md` rewritten.** Points at AuraDB Free and warns off the 14-day trial button by name.
- **Lab 2 GDS note added.** `02_gds_knn_aircraft.ipynb` says it cannot run on AuraDB Free.
- **Lab 2 write mode corrected** to Append in the README.
- **`vocareum/courseware/` deleted**, 10 files and 2.3M, along with `build_data_zip.py`. Nothing read either.
- **Repository documentation complete**, plus `agenda.md` and the object names in `lab/workshop.py`.
- **Labs 1 and 4 ship as notebooks.** `Lab_1_Aura_Setup/01_aura_setup.ipynb` at 25 cells and `Lab_4_Compound_AI_Agents/04_genie_agent.ipynb` at 31 cells, both nbformat 4.5 with no stale outputs and every image URL resolving to a tracked file. A Vocareum student never clones the repository and never sees a rendered README, so a browser lab whose instructions live only in markdown reaches them as no instructions. The click-through steps are markdown cells beside the few runnable ones. The source markdown files stay where they are. **Part B carries zero code cells by design**, so a participant who scrolls into the instructor demo can run nothing.
- **`Lab_5_LangGraph_Agent/` is complete as a lab.** `agent.py` at 19.7K, `tools.py` at 41.4K, `01_langgraph_agent.ipynb` at 35.4K, `02_deploy_and_evaluate.ipynb` at 27.6K, `README.md` at 12.3K. Corrects an earlier line here that read "`02_deploy_and_evaluate.ipynb` does not" exist.

### In flight, uncommitted

**State: LANDED in the working tree, not in `HEAD`.** Recorded separately because a reader checking out `5fb3097` sees none of it.

- **A fourth secret key, `neo4j-database`.** `data_utils.py` gains `SECRET_KEY_NEO4J_DATABASE` and `DEFAULT_NEO4J_DATABASE`, and `read_neo4j_secrets` returns a fourth key, falling back to `neo4j` when a scope written before this change has only three. `agent.py` gains `ENV_NEO4J_DATABASE`, a `scope_has_key` probe that reads key names and never values, and a `serving_environment_vars` that adds the reference only when the key exists, so an older three-key scope still deploys. `memory.py` reads the same variable in `open_from_env` and the same scope key in `open_from_secrets`. `lab/workshop.py` names the key.
- **What it fixes.** `verify_connectivity()` succeeds against an instance whose home database is not named `neo4j`, and the first real query then fails with `Neo.ClientError.Database.DatabaseNotFound`. This is the caveat 9.5 records, turned into a credential path instead of a warning. Resolution order is model config, then the environment variable, then `SHOW DATABASES`.
- **Still uncommitted, and now 14 files.** `git status` against `5fb3097`: `Lab_3_Semantic_Search/` notebooks 01, 02 and 03, its README and `data_utils.py`; `Lab_5_LangGraph_Agent/` notebooks 01 and 02, `agent.py` and `tools.py`; `Lab_6_Agent_Memory/` notebooks 01 and 02 and `memory.py`; `lab/workshop.py`; and this file. **9.1's rule has now been broken twice on the same change**: work that has been measured gets committed before the next measurement starts.
- **The resource and registration work rides in the same uncommitted tree.** `build_resources`, the twelve-entry list, the Lab 6 UC registration and the cell 20 `UNION` rewrite are all in these 14 files, so a reader on `HEAD` sees a four-entry resource list and an unregistered Lab 6 log call.
- **`tools.py` is modified, and not by the `neo4j-database` change.** The defect E fix is committed at `5fb3097` and the 48 of 48 regression suite was run against that committed file. Defect F is what the separate edit is.

### In flight, running now

- **`lab5-02-deploy-e2e`, job `640691439045913`.** Runs a harness copy of `02_deploy_and_evaluate.ipynb` that prepends the `VOC_COURSE_LIBRARIES` install and asserts the write target, and changes nothing else. It logs, registers version 2, deploys, waits for READY, asks one question per tool and runs the MLflow evaluation. **It settles Phase 2's completion criterion**, which is a Genie answer through the endpoint.
- **`lab6-timed-e2e`, job `38420397665184`.** Runs an instrumented copy of `01_agent_memory.ipynb` that stamps a wall clock at the end of every code cell and prints a per-section report against 75 minutes. **It settles Phase 3's timing criterion.** Lab 6 never queries the serving endpoint, so the two runs are independent and run together.
- **Two earlier attempts failed for environment reasons, not lab reasons.** One ran a stale workspace copy of `data_utils.py`; one hit a `CALL {}` rejection that is now fixed. Neither produced a timing.

---

## 3. What Remains

### Blocking the plan

- **Confirm AuraDB Free tolerates the Lab 3 plus Lab 6 index and constraint total on one instance.** Lab 6 installs 33 indexes and 12 constraints on top of whatever Lab 3 already created. **The number that matters is the combined total, not Lab 6 alone.** `f024ea61` carries 59 indexes today and that is not evidence, because `f024ea61` is a multi-database instance and not Free. Closing this needs a fresh Free instance. **This is the one item that can still flip Lab 6 to no-go.**
- **Check the Model Serving endpoint quota** against the largest expected class size. Deployment is required, so this is a hard prerequisite.
- **Confirm `populate_aircraft_db` installs and runs from a serverless notebook cell**, or pick the job or vendored fallback. Admin path only now, so it no longer blocks any lab.

### Lab 5, to finish Phase 1

- ~~Re-measure routing against the current `tools.py`.~~ **Done. 48 of 48 across 9 groups against the committed `5fb3097`**, with defects A, B, C and E all fixed. Defect E adds its own numbers: 0 of 5 zero-row runs, direction sweep 0 misses of 6. Section 2, Lab 5 core.
- ~~**Defect F is open and it is nondeterminism, not a wrong answer.**~~ **Closed.** The first report, 0 rows then 25 rows on two consecutive runs against an identical graph, described only half of it. Ten measured runs found 4 of 10 inventing a nonexistent `AFFECTS_COMPONENT` alongside 3 of 10 walking the loose `AFFECTS_SYSTEM` chain. Fixed and verified at 0 and 0 across 10 after-runs. See section 2.
- **Exercise the extracted-entity routing path** against a graph loaded with extraction on. Blocked on an LLM key, section 5.
- **Optional hybrid retrieval exercise** for participants who ran Lab 3 notebook 03. Cuttable.

### Lab 5, the rest of Phase 2

**Most of this phase ran. The list is now short and the completion criterion is one call.** What closed moved up to section 2.

- ~~**Redeploy with `DatabricksSQLWarehouse` and the gold `DatabricksTable` entries declared, then put one Genie question through the endpoint.**~~ **DONE, Phase 2's completion criterion met.** The declaration is written and shared, `build_resources` at `agent.py:147`, twelve entries: one `DatabricksGenieSpace`, one `DatabricksSQLWarehouse`, the eight gold `DatabricksTable` entries, and two `DatabricksServingEndpoint` entries for the supervisor and embedding models. The endpoint now holds three READY versions with `config_update: NOT_UPDATING`. Verified by asking it the fleet-average EGT question: it routed to `genie_node`, wrote SQL joining `sensor_readings` to `sensors` on `type = 'EGT'`, and returned **866.65373875 C** against a rebuilt CSV average of 866.7. The string "not authorized" appears nowhere in the response. Section 5 question 2 closed.
- **Re-capture the memory-off baseline on that redeploy.** The existing one is dated on four axes: a superseded `tools.py`, a pre-rebuild lakehouse, no Genie answer at all, and a `cypher_maintenance_history` answer taken before defect E was fixed. See 9.4.
- **Deploy a second endpoint as a different user and confirm both stay healthy.** Untouched, and it depends on the quota check.
- **MLflow evaluation against the fixed question set**, run against the deployed endpoint. Notebook 02 section 8 holds the cells; the scores are unmeasured.
- **`eval/questions.jsonl` does not exist.** Notebook 02 carries its question set inline. Decide whether the file is still wanted or the notebook is the question set.
- **Measure how the serving principal reads the secret scope.** Partly answered: the endpoint resolved `NEO4J_*` from `{{secrets/...}}` and reached Aura, so the mechanism works. The fourth key, `neo4j-database`, is uncommitted and has never been deployed.

### Lab 6, the rest of Phase 3

**The files are written. What is left is execution.** The build items that closed moved up to section 2. Everything below is a measurement Phase 3 cannot complete without, plus one thing outside the lab.

- **Run `01_agent_memory.ipynb` end to end against a live instance. RUNNING**, job `38420397665184`. Two earlier attempts stopped early, one on a stale workspace module and one on the `CALL {}` guard, and both causes are fixed. **The write target is settled** and the run costs `f024ea61`'s status as a clean Lab 5 measurement graph. The memory schema has already landed there, so that cost is paid rather than pending.
- ~~Decide which Aura instance the test writes to.~~ **Decided: option B, `f024ea61`, as the secret scope already points.** Recorded in section 7. The consequence is that adoption puts an `:Entity` label and a `type` property on all 36 `Aircraft` permanently, so any Lab 5 measurement taken after it names the memory schema as part of the graph it measured.
- **Time each hands-on demo individually against its share of 75 minutes.** MEASURED, not estimated, per the Phase 3 completion criterion. **Nothing is timed today**, and the running job is the third attempt to change that. The instrumented copy stamps a wall clock at the end of every code cell and maps each cell to the `## Section N` heading above it, so the report is per section rather than one total.
- **Test the `extraction_mode="explicit"` batch path.** The spike measured only singular `add_message`; the seed helper uses `add_messages`. Still unmeasured.
- **Verify the two Foundation Model endpoints from this workspace.** `databricks-bge-large-en` returning 1024-dimension vectors, and `databricks-meta-llama-3-3-70b-instruct` answering. Written into three probe runs, never reached a successful execution.
- **Memory off versus on evaluation harness.** **No longer blocked on a missing baseline. Blocked on a usable one.** `worklog/lab5_memory_off_baseline.json` exists and its routing half is sound, but its Genie half is empty, its `tools.py` is superseded and its lakehouse numbers are pre-rebuild. Either re-capture on the Phase 2 redeploy, or compare routing only and say so. See 9.4.
- ~~Put the wheel into the provisioning path.~~ **Withdrawn, it was already there.** `lab/workshop.py:224` and `:714` upload it, and `lab/course.env:71` installs it as a cluster library. The hand upload was needed because `aws-partner-rk` is a plain workspace, not a Vocareum-provisioned one. Kept visible rather than deleted, because the wrong version of this line sat in section 2 for part of a session.
- **Get the `MENTIONS` fix upstream into `neo4j-labs`.** Worth doing whether or not Lab 6 ships. Unchanged.

### Loader hygiene

- **Drop `Reading` and `HAS_READING` from `populate_aircraft_db`.** Decided, not done. `loader.py` still writes them at lines 43, 337, 343, 893, 914. Nothing in the workshop queries them, and their presence means an admin debugging a participant issue works against a graph 155,520 nodes larger than any participant has. About 75 minutes, confined to `loader.py`, `schema.py`, `agent_samples.py`, and two documents.
- **Add `OperatingLimit` to the Lab 2 README node list.** The Append fix landed; this half did not.
- **Load `OperatingLimit` in the Lab 2 validation harness.** It never did, which is how the limit collision reached Lab 3 unnoticed.

### Delivery, Phase 4

- Full dry run of Labs 1 through 6 on a fresh Aura instance and a fresh workspace user.
- Model Serving exercised at class size, or the quota confirmed sufficient.
- Part B rerun as an instructor demo against the instructor's own instance.
- **Finish `VOC_COURSE_NOTEBOOKS` in `lab/course.env`. Partially done, and the checklist stays open.** The list names 13 entries at `:134-146`, all backed by files on disk, Labs 1 through 6, plus `data_utils.py`, `tools.py`, `agent.py` and `memory.py`. **One file is missing and it is the one that landed most recently: `Lab_5_LangGraph_Agent/02_deploy_and_evaluate.ipynb`.** It belongs between `01_langgraph_agent.ipynb` and `tools.py`. Also open: whether `Lab_6_Agent_Memory/02_instructor_demos.ipynb` ships, which is a question in section 5. **The list is order sensitive.** `lab/user_setup.sh:134` makes the first entry the student's landing page, so `00_cluster_smoke_test.ipynb` stays first and anything new goes where a student reaches it, never appended. Confirm each `.py` helper lands as a FILE and not a NOTEBOOK, the `lab3-fix.md` defect.

  **The FILE-not-NOTEBOOK behavior lives outside this repository, which is why it bites invisibly.** It is in the pinned `dbx-vocareum-tools` package, verified at `.venv/lib/python3.13/site-packages/dbx_vocareum_tools/labruntime/voclab.py`: `NOTEBOOK_FORMATS[".py"]` must read `("AUTO", None)` and `NOTEBOOK_KEEP_EXTENSIONS` must read `(".py",)`. An upload against a lock older than `dbx-vocareum` commit `68e63a5` ships the defect and hash-verifies cleanly, so nothing downstream notices. **Whoever runs the final upload checks that pair first.**

  **Two checks before any `.py` helper joins the list.** Does a notebook the student actually opens import it, and does its first line lack `# Databricks notebook source`. **Both helpers now pass both checks, and the importing notebook does not have to live in the same lab.** `agent.py` is imported four times by `Lab_5_LangGraph_Agent/02_deploy_and_evaluate.ipynb` and three times by `Lab_6_Agent_Memory/01_agent_memory.ipynb`; `memory.py` by the Lab 6 notebooks. Both first lines are docstrings. **The open half is the reverse of what this paragraph used to say:** `agent.py` is in the list and the notebook that imports it is not.
- Timings recorded per lab and per Lab 6 demo.

### Downstream content, Phase 5

- **The Lab 5 architecture diagram.** The shipped PNG still shows the Part B MCP topology, and both the root README and the Lab 4 README display it.
- **The Antora site stops at Lab 4, and the problem is absence rather than contradiction.** `site/nav.adoc` lists Lab 1 through Lab 4 and nothing after. `site/modules/ROOT/pages/` holds `lab1.adoc` through `lab4.adoc` with no Lab 5 or Lab 6 page, and `workshop-overview.adoc:47` describes Lab 4 as the last lab. **The root `README.md` links to the published site on line 1**, and `deploy-antora.yml` publishes on every push to `main`, so this is the first thing a participant following that link sees. The old claims are gone: `lab4-instructions.adoc:557` now hands off to Lab 5. Writing two lab pages is content creation, not drift repair, which is why the audit left it. **Section 5 asks whether the site is still a shipped surface at all.**
- **The site and the slides carry pre-regeneration dataset numbers.** `site/.../workshop-overview.adoc:24` and `:35`, `site/.../lab4.adoc:3`, `slides/platform-overview/01-workshop-over.md:89` and `:101`, `slides/docs/overview-and-genai-foundations.md:53` and `:63`, `slides/organize.md:63`, and `slides/kg-construction/05-building-knowledge-graphs-slides.md:102` all say "345,600+ hourly readings", 160 sensors, 80 systems, 20 aircraft. Counted against the committed CSVs it is **155,520 readings at a 4-hour interval, 288 sensors, 144 systems, 36 aircraft**. The root `README.md` and `DATA_GENERATOR.md` already carry the right numbers, so the repository disagrees with itself across three surfaces.
- **The slides carry no Lab 5 or Lab 6 content.** The MCP framing is already corrected: `platform-overview/01-workshop-over.md:128` reads "used only in the Part B demo", `:144` reads "Lab 4 Part B is an instructor demo". What is missing is the two new labs.
- Half-day split guidance: paused and deleted Aura instances, endpoint survival between sessions, secret scope and Genie access survival, a between-sessions note, and a foundation-session ending that stands alone.

---

## 4. Major Decisions Made

- **Lab 4 Part B is an instructor demo, and the MCP server is removed.** Participants watch. All Part B and MCP documentation stays, because the instructor needs the procedure and the no-code contrast is the point. Runner-up was optional-but-buildable, which lost on setup cost against a benefit nobody was collecting.
- **Lab 5 is the single participant continuation from Part A.**
- **The Lab 5 catch-up cell is dropped, as too complex.** It required vendoring a non-serverless loader into a notebook cell and leaving three code paths that must produce one schema, all so a participant could skip the labs the workshop teaches. **The cost is honest: somebody an hour behind at 2pm loses Labs 5 and 6.** The loader work built for it stays and is load-bearing elsewhere.
- **The class uses AuraDB Free.** The 200,000 node and 400,000 relationship caps apply, and every capacity number is measured against them.
- **LangGraph for Lab 5, direct bolt driver for the Neo4j tools.** No per-participant MCP server to host.
- **`graphrag_node` uses `VectorCypherRetriever`, not a plain vector retriever.** The Cypher tail after the vector hit is what makes it GraphRAG. The cost is that it sits close to `cypher_node`, which is why routing between that pair is measured as its own number.
- **`databricks-meta-llama-3-3-70b-instruct` as the supervisor model.** Closed on measured routing accuracy. The one-line swap to `databricks-claude-sonnet-4-5` stays available and is not needed.
- **One embedding path, `databricks-bge-large-en`**, for the loader and for Lab 3 alike.
- **Model Serving deployment is required, not optional.** Service principal auth is the lesson that separates a notebook demo from a product.
- **Participants create their own secret scope in Lab 3 notebook 01.** Not provisioned, not shared. Removes the scope from the Vocareum hooks entirely, and no participant's Aura password is visible to another.
- **Extraction writes `ExtractedLimit`; `OperatingLimit` means the 20 canonical CSV rows.** Runner-up was filtering on `limit_id` at every authoritative site, which left every workaround in place and added filters in three more.
- **The `OperatingLimit` uniqueness constraint keys on `limit_id`, not `name`.** A uniqueness constraint is not enforced against nodes lacking the property, so `limit_id` binds the canonical rows and ignores everything else.
- **`neo4j-agent-memory` on the self-hosted bolt path, pinned to the fork wheel, adopting `Aircraft` only, writing in explicit mode.** Four conditions, each of which fails silently rather than loudly.
- **The broken-instance fallback is dropped. There is no recovery path, and that is deliberate.** No second read-only Aura instance, no shared credentials, no override. A participant whose instance is broken or expired makes a new AuraDB Free instance and re-runs Lab 2 and Lab 3 notebook 01. Participants do the course; there is no alternative to doing it. Runner-up was a second loaded instance handed out on request, which lost because it is an instance to keep alive, a credential to distribute, and a database a stray `populate-aircraft-db clean` can wipe mid-class.

  **The consequence, stated plainly for instructors:** somebody who stalls in Lab 2 has no shortcut back at 2pm, so a stalled Lab 2 has to be caught in Lab 2. Closes Open Decision 10, and closes the Phase 4 item that was blocked on it.
- **Labs 5 and 6 share one Model Serving endpoint per participant, redeployed by Lab 6.** Closes an ambiguity `expand.md` carried without ever stating it as a decision. Runner-up was two endpoints, which lost on the Phase 4 class-size quota. **The consequence is load-bearing: the memory-off baseline has to be a persisted artifact captured from the Lab 5 endpoint before Lab 6 redeploys over it.** A Phase 2 that ends with a passing eval run and no durable baseline leaves Lab 6's off-versus-on comparison with nothing to compare against, and Phase 2 gets re-run.
- **The Lab 4 Genie space attaches four tables: `sensor_readings`, `aircraft`, `sensors`, `systems`.** `fleet_readiness` and `sensor_health` are not attached. Decided by Ryan on 2026-08-08, relayed through the Vocareum session. So `PART_A.md:40` is correct as written, `04_genie_agent.ipynb` is correct as written, and **nothing changes in either.**

  **The residue is on the provisioning side, and it is inert rather than broken.** `lab/workshop.py:374-375` writes table comments for `fleet_readiness` and `sensor_health`, and `:392-400` writes column comments for `readiness_status` and `health_status`. A Genie space reads comments only for tables in its scope, so those four statements provably do nothing for Lab 4. Both tables stay in `GOLD_TABLES` for reasons unrelated to Genie, so this is dead weight, not a defect. **Recorded as known-inert, not queued as cleanup.**
- **Do not attach `fleet_readiness` or `sensor_health`, and drop their Genie comments from `lab/workshop.py`.** This is the new decision the line above said somebody would have to make, and the evidence closed it. **`sensor_health.health_status` can never emit `ANOMALY`.** The rule fires on `p95 > avg + 2*stddev` while `p95` is approximately `avg + 1.645*stddev`, so the threshold is unreachable. Measured across all 288 sensors: **284 WARNING, 4 NORMAL, 0 ANOMALY.** A table whose documented status value never occurs is a table Genie would answer wrongly from, so the comment that promises it goes. Removes two `TABLE_COMMENTS` and two `COLUMN_COMMENTS` entries. `GOLD_TABLES` and the attach list are untouched. Runner-up was to fix the rule so `ANOMALY` can fire, which lost because nothing attaches the table and the fix would change a published gold table for no consumer. Applied, section 5 question 3 closed.
- **A relationship-direction error in `cypher_node` gets fixed with a `GRAPH_SCHEMA` bullet, never by making the traversal undirected.** Defect E was `AFFECTS_AIRCRAFT` written backwards, and 9 lines of schema text took it from 5 zero-row runs of 5 to 0 of 5, with the regression suite still at 48 of 48. Runner-up was dropping the arrow so the pattern matches either way, which lost twice over: it teaches participants a Cypher habit the workshop spends Lab 1 arguing against, and it hides the next direction defect instead of surfacing it. **The generalization is the point.** The model anchors on the noun the question names and points every arrow away from it, so any relationship pointing toward a frequently-named node needs its own schema bullet.
- **A schema bullet must name the wrong road as well as the right one.** Defect F's bullet does both: it says components reach maintenance events through `HAS_EVENT`, and it says there is no `AFFECTS_COMPONENT` and that writing one matches nothing. The second half is what moved the number. Naming only the correct traversal left the model free to keep inventing a relationship type whose name reads plausibly beside `AFFECTS_AIRCRAFT` and `AFFECTS_SYSTEM`.
- **Known tradeoff, taken with eyes open: every one of these fixes is prompt engineering against an observed failure, not a structural fix.** `GRAPH_SCHEMA` is static, hand-written, and never read from the live graph. It is interpolated into `CYPHER_GENERATION_PROMPT` at `tools.py:339-340` and into `CYPHER_REPAIR_PROMPT` at `tools.py:361-362`, so a bullet added for one question shape is sent on **every** Cypher call. Defects A, C, E and F each added prose, and the block now runs roughly 140 lines.
  - **What it buys.** No per-question routing logic and no code branching, and it behaves identically on the deployed agent because the schema travels with the model rather than sitting in notebook-side code.
  - **What it costs.** Prompt length on every call, and no guarantee. Defect F went from 4-of-10 invented relationships to 0-of-10, which is **a measured rate, not a proof**. Each new bullet also competes for attention with the ones already there, and defect A came from giving the model two strings to choose between.
  - **The structural alternative, not built.** Validate the generated Cypher against the real schema before running it and reject unknown labels, relationship types and properties outright. That catches defects E and F, and the invented `AFFECTS_COMPONENT`, **as a class rather than one at a time**, and it turns a silent zero-row answer into an error the repair path can act on. Not built now, because the labs ship soon and 48 of 48 holds. It is the right answer if this agent outlives the workshop.
- **Browser labs ship as notebooks.** Labs 1 and 4 join the notebook set, because a Vocareum student sees no rendered README. Delivery format, not lesson content. The source markdown stays where it is, so this sits outside the "do not rewrite Labs 1 through 3" fence.
- **Labs get written before anything that describes them.** Lab 5, then Lab 6, then the Vocareum notebook list, then the site and slides in one pass.
- **This document set owns the plan.** `proposed-outline.md` and `workshop-improve.md` carry superseded banners.

---

## 5. Outstanding Questions

Fourteen, numbered. Each says what the decision is, what the evidence is, and what it blocks. **Questions 1 through 4 all closed during this pass** and are struck through rather than deleted, so each decision and its evidence stay readable. **Nothing is in flight.** Questions 5 through 14 are open, and every one of them is waiting on a decision from Ryan rather than on work in progress.

### Closed this pass

1. ~~**Lab 5 has no notebook 02 in the participant path.**~~ **CLOSED, built and committed in `1be478f`.** `Lab_5_LangGraph_Agent/02_deploy_and_evaluate.ipynb`, 30 cells, 17 markdown and 13 code. It logs `agent.py` with the twelve-entry `build_resources`, pins `pip_requirements` rather than letting MLflow infer them, registers to Unity Catalog, deploys, waits for READY, and queries the endpoint. Lab 6 now has the prerequisite it lists. **One caveat: no cell in the committed notebook carries an execution count**, so the notebook itself has not been run top to bottom in the form a participant will meet it. The code path is proven, because the deploy that produced the three READY versions ran through a job against the same `build_resources`, but a participant-shaped run of this file is still owed. That belongs in the Phase 4 dry run.
2. ~~**`genie_node` is unauthorized from the serving principal.**~~ **CLOSED, fixed and verified.** The failure was "is not authorized to use or monitor this SQL Endpoint" at `auth_type=model-serving`, because declaring `DatabricksGenieSpace` at log time does not carry the SQL warehouse behind the space. `DatabricksSQLWarehouse` and the eight gold `DatabricksTable` entries now sit beside it in `build_resources` at `agent.py:147`. Verified against the live endpoint: the fleet-average EGT question routed to `genie_node` and returned **866.65373875 C**, matching the rebuilt CSV average of 866.7, with no authorization error in the response. **This one mattered most of the four**, because every participant who deploys Lab 5 hit it, and because it invalidated every Genie number in the memory-off baseline.
3. ~~**The gold-table Genie edit to `lab/workshop.py`.**~~ **CLOSED, applied.** Settled as do-not-attach. `sensor_health.health_status` can never emit `ANOMALY`, because the rule fires on `p95 > avg + 2*stddev` while `p95` is approximately `avg + 1.645*stddev`. Measured 284 WARNING, 4 NORMAL, 0 ANOMALY across 288 sensors. The edit removes two `TABLE_COMMENTS` and two `COLUMN_COMMENTS` entries. Applied: `genie_statements()` now emits 22 statements, down from 26, being 6 table comments, 8 column comments, 8 grants. The grant loop iterates `GOLD_TABLES`, not `TABLE_COMMENTS`, so both tables keep their SELECT grant and stay browsable. Decision recorded in section 4.
4. ~~**Defect F: the components-for-an-aircraft question is nondeterministic.**~~ **CLOSED, fixed and measured.** Ten runs before: 4 of 10 invented a nonexistent `AFFECTS_COMPONENT`, 3 of 10 walked the loose `AFFECTS_SYSTEM` chain, 3 of 10 correct. Ten runs after: 0, 0, 0, all writing the identical `HAS_EVENT` traversal against a ground truth of 9 components and 23 events. Regression 48 of 48. Detail in section 2, decision and its tradeoff in section 4. **What it leaves open is not a question so much as a standing risk:** four defects have now been fixed by adding prose to a static `GRAPH_SCHEMA` sent on every call, and the measured pass rate is not a proof. Validating generated Cypher against the real schema would close the whole class. Not built, and it is the first thing to build if this agent outlives the workshop.

### Holding up delivery

5. ~~**The notebooks hardcode `NEO4J_DATABASE = "neo4j"`.**~~ **ANSWERED by the fourth secret key, and one gap is left.** The notebooks now read `read_neo4j_secrets(...)["database"]`, so the value travels the same path as the password and the split is gone. The fallback to `"neo4j"` lives in exactly one place, `data_utils.py`, for scopes written before the key existed.

    **What is left is a scope written by an older Lab 3 run.** It reads back as `neo4j`, which is right on Free and wrong on anything else, and on a multi-database instance `resolve_database` then raises rather than guessing. **Instructors and admins on a non-Free instance write the `neo4j-database` key by hand once**, exactly as the error message says. No lab content should carry a fallback or override path, per the decision in section 4. Blocks nothing for the class as scoped.
6. **AuraDB Free index and constraint caps.** Lab 6 installs 33 indexes and 12 constraints on top of whatever Lab 3 already created. **The number that matters is Lab 3 plus Lab 6 on one instance, not Lab 6 alone.** If Free caps below the combined total, **Lab 6 fails for every participant simultaneously**. Closing this empirically needs a fresh Free instance, which is Ryan's to provision. Blocks Phase 3 entirely, and it is the one remaining no-go.
7. **`genie_statements()` in `lab/workshop.py` overwrites richer DLT comments with thinner ones.** The pipeline already writes a comment; the genie stage then restates it with less. **Enrich the strings, or stop restating what the pipeline already wrote?** Nothing errors, and every provisioned workspace ships the thinner comment. Comments are what Genie reads to write SQL, so this lands on Lab 4 Part A, the participant path.
8. **Does `Lab_6_Agent_Memory/02_instructor_demos.ipynb` ship to participants or stay instructor-only?** It is not in `VOC_COURSE_NOTEBOOKS` and no document mentions it. **If it ships**, it needs a `course.env` entry and a row in the Lab 6 README file table. **If it does not**, one sentence in that README stops the next reader asking. The four demos in it are the Lab 6 payoff, so this is not a formatting question. Blocks the Vocareum notebook list, a Phase 4 item.
9. **The Antora site is stale.** `site/nav.adoc` stops at Lab 4 and the site carries pre-regeneration numbers, 345,600 readings / 160 sensors / 80 systems / 20 aircraft, against the actual **155,520 / 288 / 144 / 36**. It is linked from line 1 of the root `README.md` and published on every push to `main`. **Regenerate it, or drop the link on README line 1?** Nothing else in Phase 5 can be scoped until this is answered.
10. **`lab/course.env:154` names a SQL warehouse that exists in no workspace this repository has been run against.** `VOC_COURSE_WAREHOUSE_NAME=shared_warehouse`. On Vocareum the name is correct by construction, because `voclab.py warehouse-ensure` creates it from that variable during `workspace_init.sh`. Everywhere else it is a name for nothing. In `aws-partner-rk` the only warehouse is `vg demo sql warehouse`, id `b0fffb8e3255bf85`, and every Genie and deployment measurement taken this pass used that id rather than the configured name. `lab/workshop.py:812-819` fails loudly with `MISSING_WAREHOUSE` rather than silently, and its message says the warehouse-ensure step did not run, which is a true statement on Vocareum and a misleading one anywhere else. **Leave it as a Vocareum-only name, or let `resolve_warehouse` fall back to the sole warehouse in the workspace when the configured name is absent?** Blocks nothing on the Vocareum path, and blocks any admin or instructor provisioning into a workspace they did not build with `workspace_init.sh`, which is how every measurement in this document was taken.

### Contained, or not holding anything up

11. **Defect D, cosmetic.** `cypher_node` has one refusal string, the sensor-readings one, so a declined write request answers "The graph holds no sensor readings." Nothing writes and no data is wrong, but the wrong sentence reaches synthesis. **A second refusal string gives the model two to choose between, which is the shape that produced defect A.** Recommendation is to leave it.
12. **`aircraft_fleet_metrics`, the fifth table in the `aircraft` schema.** Produced by no pipeline and referenced nowhere in the repository. It still holds 36 rows from the same stale generator run that forced the gold rebuild, and it was deliberately left in place because it was outside that authorization. **Drop it separately?** Blocks nothing.
13. **Both LLM keys are dead.** Anthropic credit too low, OpenAI 401. **Blocks only `ExtractedLimit` and the other LLM-extracted entities**, and therefore the extraction-on routing exercise. Everything GraphRAG needs is already loaded through `enrich --skip-extraction`.
14. ~~**Lab 6's Section 5 blocker.**~~ **CLOSED.** Cell 20 is rewritten as a top-level `UNION`. The guard at `neo4j_agent_memory/core/query.py:26-50` fires on `r"\bCALL\s+\{"` and on nothing else in the `CALL` family, so the rewrite is the whole fix and the library needs no change. **The narrower reading matters for anyone writing the next cell:** `CALL db.labels()` and `CALL apoc.x()` pass, subqueries do not.

---

## 6. Phased Implementation Plan

Six phases. Each has an entry condition, a body, and a completion criterion that is a measurement rather than a claim.

### Phase 0: Prove the risky parts

**Status:** In progress. Loader work done. Memory spike done, GO with conditions.

| Item | Owner track | Blocks |
|---|---|---|
| AuraDB Free index tolerance, Lab 3 plus Lab 6 on one Free instance | B | Phase 3 entirely |
| Model Serving endpoint quota at class size | A | Phase 2 completion, Phase 4 |
| `explicit_mode` batch path through `add_messages` | B | Phase 3 seeding step |
| Serverless install of `populate_aircraft_db`, or pick the fallback | A | nothing participant-facing |
| Drop `Reading` and `HAS_READING` from the loader | A | nothing, but it makes every later debug session honest |

**Completion:** the index tolerance question returns a yes, or Lab 6 is formally re-scoped.

**Still open, and now carrying more weight than it did.** Phase 3 was entered and built out with this question unanswered, on an explicit "proceed anyway". A no no longer delays Lab 6, it invalidates four files that are already written.

### Phase 1: Lab 5 core agent

**Status:** Core built and measured. The re-measure is done at 48 of 48 against `5fb3097`. Defect F is what stands between here and completion.

1. ~~Re-measure routing with the refusal rule in place.~~ Done. 48 of 48 across 9 groups, defects A, B, C and E fixed.
2. ~~Close defect F, the nondeterministic components-for-an-aircraft question.~~ **Done.** 10 runs after the fix at 0 invented, 0 loose, 0 zero-row, regression 48 of 48.
3. Exercise the extracted-entity path against an extraction-on graph. Blocked on an LLM key, section 5 question 12.
4. The hybrid retrieval exercise, optional and cuttable.

**Completion:** the anchor question is correct end to end and each routing case lands on the expected tool, with `cypher_node` versus `graphrag_node` reported as its own number, **against the code currently on disk**.

### Phase 2: Lab 5 ships, deployment included

**Entry:** Phase 1 re-run done. **Not done when the notebook is written. Done when a deployed endpoint answers as a service principal.**

**Status: entered ahead of Phase 1's re-run, and it ran. Steps 1, 3, 4, 5, 7 and 8 are done. Step 2 is now done for all four keys. Steps 4 and 5 are done for two tools of three, and the third is the criterion.** An endpoint exists, a baseline is persisted, notebook 02 is written and the cold deploy is timed at 15.8 minutes. Genie returned "is not authorized to use or monitor this SQL Endpoint" for the reason step 1 exists to prevent. **The fix is written, shared between both labs, and running as job `640691439045913`.** Step 6 is untouched.

Order inside the phase, because each step gates the next:

1. `ResponsesAgent` wrapper, resources declared at log time. **Measured: `DatabricksGenieSpace` alone is not enough. `DatabricksSQLWarehouse` has to be declared beside it, or every sensor question comes back unauthorized from an endpoint that deployed cleanly and routed correctly.**
2. Secret scope read from the serving principal. Measure it. This is the silent failure.
3. Log and deploy. Time the cold deploy.
4. Call the endpoint, one question per tool. **Genie is the one that fails here, not Neo4j.**
5. Call the endpoint with the anchor question.
6. Second endpoint under a different user.
7. MLflow evaluation against the deployed endpoint. **This is the Lab 6 baseline, and it must be persisted as an artifact, not just run.** Labs 5 and 6 share one endpoint and Lab 6 redeploys over it, so a baseline that exists only as a passing run is gone by the time Lab 6 needs it.
8. Write `02_deploy_and_evaluate.ipynb` and finish the README.

**Completion:** a successful Genie call **through the endpoint**. A successful deploy is not the criterion.

### Phase 3: Lab 6 memory

**Entry:** Phase 1 done, Phase 0 index question answered yes. **Entered early, on Ryan's "proceed anyway", with the index tolerance question still open.** Lab 6 is therefore built against a non-final GO, and a no on that question invalidates the build rather than delaying it.

**Status: written, running for the third time. Steps 1 through 6 and 8 are LANDED. Steps 7 and every timing are open.** Two earlier runs stopped early, one on a stale workspace module and one on the `CALL {}` guard. **Neither was a lab defect in the sense that matters**, but the second was a real content defect and it is fixed.

1. LANDED. The four install and write conditions, each as an explicit checklist item.
2. LANDED. Memory client, `adopt_existing_graph` on `Aircraft` with the dry run shown first.
3. LANDED. `recall` and `remember` around the Lab 5 supervisor.
4. LANDED. Seed script in a setup step, never a participant-run loop.
5. LANDED as cells, **open as a measurement.** Three hands-on demos exist. None is timed.
6. LANDED. Four instructor demos, shipped complete as runnable cells in `02_instructor_demos.ipynb`, each standalone because the shared names sit in one setup cell.
7. OPEN. Memory off versus on harness against the Phase 2 baseline. **The baseline now exists and its routing half is sound**, so this is no longer blocked on absence. It is blocked on the baseline being re-captured after the Phase 2 redeploy, or on the comparison being narrowed to routing and saying so.
8. LANDED. `README.md`, carrying the four pinned-version research answers moved out of `expand.md`.

**Completion:** the headline traversal returns a good answer, the comparison shows a measurable difference in tool calls, tokens or accuracy, and the three hands-on demos fit inside 75 minutes **measured, not estimated**. **None of the three is satisfied today.** Writing the cells is not the criterion, and the gap between "the lab exists" and "Phase 3 is done" is exactly one end-to-end run plus a stopwatch.

### Phase 4: Delivery readiness

**Entry:** Phases 2 and 3 complete. **Owner: Ryan, personally, on a fresh Vocareum-shaped user and a fresh Aura instance.** Not a development workspace and not an account with leftover state.

- Full dry run, Labs 1 through 6.
- Model Serving at class size.
- Part B as an instructor demo.
- `VOC_COURSE_NOTEBOOKS` updated, `.py` helpers confirmed as FILE not NOTEBOOK.
- Timings recorded per lab and per demo.
- Confirm nothing in Labs 5 or 6 reads a fallback instance. The fallback is dropped, so a leftover override path is a credential nobody should have.

**Completion:** Ryan finishes the required path without intervening as the instructor, and the timings either match the day structure or the structure is corrected to match them.

### Phase 5: Downstream content and the half-day split

**Entry:** Phase 4 complete, because these surfaces describe the course and should be written once against what shipped.

- Lab 5 architecture diagram.
- Antora site, one pass across 9 `.adoc` files.
- Slides, same pass.
- Half-day split guidance, written rather than coded.
- Dry run of the advanced half alone, from a deliberately cold state at least three days old.

**Completion:** somebody who did the foundation session, walked away for a week, and let their instance pause reaches the Lab 6 headline demo without instructor help.

---

## 7. How the Work Parallelizes

### Three tracks

| Track | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---|---|---|---|---|---|---|
| **A. Engineering** | Loader hygiene, serverless check, quota check | Re-run and measure | Deploy and evaluate | joins from Track B | Dry run | idle |
| **B. Memory research** | Index tolerance, batch path | idle | idle | Lab 6 build | Dry run | idle |
| **C. Content and infra** | Lab 2 README and harness gaps | Eval question set | Eval question set | Lab 6 README | Timings, Vocareum list | Diagram, site, slides, split guidance |

### What actually blocks what

- **Only Phase 3 hard-depends on Phase 1**, because the memory nodes attach to the Lab 5 supervisor.
- **Phase 0's index tolerance check blocks Phase 3 and nothing else.** Run it first and run it alone; it is one connect against a fresh AuraDB Free instance.
- **The Lab 5 eval question set can be written on day one.** It is a list of questions and expected routes, and it is the input to Phase 2 step 7 and Phase 3 step 7.
- **The loader is no longer a participant-facing prerequisite.** It is the admin and dry-run load path. Loader work never blocks lab work.
- **Phase 5 depends on Phase 4, not Phase 3.** The dependency that used to run the other way was the dropped catch-up cell.
- **Phase 2 and Phase 3 can overlap once Phase 1 closes**, if two people are available. Lab 6 builds against the in-notebook agent; only the memory off versus on harness needs the deployed endpoint.

### Database separation, which is what makes parallelism safe

Two Aura instances, one per track, so neither track's writes corrupt the other's evidence.

| Instance | Track | Credentials |
|---|---|---|
| `f024ea61` | A. Lab 5 development, already loaded | `workshop-setup/.env` |
| `1a2c98cc` | B. Memory | `workshop-setup/.env.memory` |

`f024ea61` is reset with `populate-aircraft-db clean` and reloaded when a test needs a clean graph. **Add a third instance before Phase 3, participant-shaped and extraction-on**, because Phase 1's remaining re-run and Phase 3's adoption work both want a graph the other is not mutating.

**MEASURED 2026-08-08: the separation does not hold through the workspace, and this is the open decision blocking Phase 3.** The secret scope `fleet-ops-ryan-knight-neo4j-com` in `aws-partner-rk` points at `f024ea61`, the Track A instance. Lab 6 reads that scope, because Lab 5 does and the two labs share one credential path by design. So running Lab 6 as written writes adoption changes and roughly 20 memory nodes into Track A's active Lab 5 measurement graph. Determined without printing any secret value, by emitting booleans only.

Two ways out, and they trade different things:

| Option | What it costs |
|---|---|
| **A. Override `NEO4J_*` in the environment and write to `1a2c98cc`**, Track B, credentials in `workshop-setup/.env.memory` | Clean isolation, but the shipped secret-scope read path goes unexercised, which is the path a participant actually runs |
| **B. Run against `f024ea61` as the scope points** | Exercises the real path, and mutates Track A's graph mid-measurement. Section 8's rule that measurements name their instance is what makes this expensive: it invalidates Phase 1 numbers taken on that graph |

**DECIDED by Ryan on 2026-08-08: option B.** Lab 6 writes to `f024ea61`, as the secret scope already points, and the shipped credential path gets exercised. The recommendation here had been A, and it lost because the path a participant runs is the path worth testing. **The cost is the one option B names.** Adoption puts an `:Entity` label and a `type` property on all 36 `Aircraft` permanently, and `worklog/lab5_memory_off_baseline.json` records `agent_memory_schema_installed: false`, so it was captured before that. Every Lab 5 measurement taken after the Lab 6 run either runs on a freshly reloaded graph or names the memory schema as part of the graph it measured. See 9.8.

**Hazard, unchanged and worth repeating here.** `populate_aircraft_db/config.py:13` pins `populate_aircraft_db/.env` at import time, and that file points at `1a2c98cc`. A bare `populate-aircraft-db clean` run from any directory wipes the memory instance regardless of what the caller thought they were pointed at.

**With one person on all three tracks, the tracks collapse to sequential in wall-clock terms.** The separation still earns its keep, because it means a failing loader test is a loader problem and nothing else.

### Recommended order for one operator

**Superseded by 9.8, which is the same order rewritten against what has since run.** Kept because the shape has not changed: the index check first and alone, then Phase 1's re-run, then Phase 2 straight through, then Phase 3, then Phases 4 and 5.

Slot the validation harness gap and the `Reading` drop into any waiting period. Each is under two hours and none blocks anything.

---

## 8. Tracking Status and Progress

`expand.md` drifted from the repository in a specific and repeatable way: items were written as done on the day they were decided, and several stayed written as "in flight" for the whole session after they had landed. On 2026-08-08 the document listed eleven in-flight items and at least eight of them were already on disk. **The tracking rules below exist to make that failure mode impossible rather than to add ceremony.**

### The rules

- **Three states, never two.** `DECIDED`, `LANDED`, `MEASURED`. Decided means the choice is made and no code exists. Landed means the code is on disk. Measured means a number was produced by running it. **Nothing moves to MEASURED on the strength of a plan.**
- **Every status line names its evidence.** A commit SHA, an instance ID, a file path with a line number, or a measured number with its units. A status line with no evidence is a DECIDED line.
- **Verify against disk before writing a status.** Grep for the symbol, read the line, list the directory. The most common error in `expand.md` was reporting a decision as if it were a file.
- **Measurements name what they were measured against.** `f024ea61` and a participant-shaped instance are different graphs and give different answers. The 88.7 percent cap figure misled this plan for a week because it did not say which instance it came from.
- **A prompt change invalidates the routing numbers taken before it.** Applies to `tools.py` and the supervisor prompt. The refusal rule is the live example.
- **Completion criteria are measurements.** "Deployment succeeded" is not a Phase 2 criterion. "The deployed endpoint answered a Genie question as the serving principal" is.
- **Silent failures get their own checklist item.** The four memory conditions, the serving principal's secret read, and the Genie table grant all fail without an error message. Each is a line item, never a note in a paragraph.

### Where status lives

- **`expand-v2.md`**, this file, holds the plan and the phase-level status. Sections 2, 3 and 6 are the ones that change.
- **`worklog/*.md`** holds each investigation's full report and its raw numbers. `memory-spike.md` and `aura-node-budget.md` are the existing pattern, and it works. **New investigations get a new worklog file rather than another paragraph here.**
- **Each lab's README** holds the operational facts a participant or instructor needs. The four pinned-version research answers move from `expand.md` into `Lab_6_Agent_Memory/README.md` when Phase 3 creates it.

### Cadence

- **On landing any item:** update its bullet in section 3, move it to section 2, and name the evidence.
- **At each phase boundary:** re-verify section 2 against disk, then write the phase completion measurement.
- **On any decision:** add it to section 4 with its runner-up and why the runner-up lost. The runner-up is the part that stops the decision being relitigated.
- **Weekly, or at any phase boundary:** re-read the two external dependency risks, the `neo4j-agent-memory` pin and the Part B MCP server, together.

### Definition of done for the whole effort

A participant creates one AuraDB Free instance in Lab 1 and finishes Lab 6 having used only that instance, with a deployed Model Serving endpoint answering questions as a service principal across all three tools, and with Lab 4 Part B and all MCP material intact as an instructor demo.

---

## 9. Suggested Fixes

Checked 2026-08-08 against the **working tree**, not against `HEAD`. Re-checked the same evening against `HEAD` at `5fb3097` plus 13 modified files.

Ordered by what it costs to fix, not by which section it corrects. 9.4 is the critical path, 9.9 is the process change that stops the list regenerating.

**Closed since the first draft:** 9.1 entirely, F4d, and the two `.py`-helper checks in 9.2. **Opened since:** F4e, and the `course.env` entry that notebook 02 arrived without. Each closed item is struck through rather than deleted, because half of them were closed by a different session and the record of who fixed what is the only thing stopping the same work happening twice.

**Corrected after peer review, same day.** Three claims in the first draft were wrong and are gone: that `lab/workshop.py` does not upload the memory wheel, it does, at `:820-853`; that the index check also settles the Lab 6 write target, Ryan chose `f024ea61` instead; and that Lab 6 "redeploys over nothing", an endpoint exists. Each was published before the evidence was checked, which is the same failure 9.9 is about, committed by this section while writing it.

### 9.1 Commit, before anything else. CLOSED

**Both fixed on 2026-08-08 in `b82ca4b`.** Nineteen files, 1,506 insertions. `lab/Lab_6_Agent_Memory` is now a tracked symlink beside the other five, so a fresh clone ships Lab 6 and the Vocareum upload resolves. `Lab_6_Agent_Memory/README.md` is tracked. `5fb3097` followed with 9 more lines in `tools.py`.

**Kept, not deleted, because the pattern recurred inside one day.** The working tree carries the uncommitted `neo4j-database` change across nine files as of this pass, and the deployed endpoint's provenance is still a sha of a file in one working tree, per F4c. **The rule is the fix, not the one commit: work that has been measured gets committed before the next measurement starts.**

- ~~F1. None of this work is committed.~~ Closed by `b82ca4b`.
- ~~F2. `lab/Lab_6_Agent_Memory` is untracked, and the Vocareum upload reads through it.~~ Closed by `b82ca4b`.

### 9.2 Correct sections 2 and 3

**A concurrent session corrected the Lab 6 half of sections 2 and 3 while this review was running.** "`Lab_6_Agent_Memory/` does not exist" is gone, replaced by the LANDED block and the workspace findings. Those corrections are right and are not repeated here. The rows below are what is left.

Landed, and still written in section 3 as remaining:

| Section 3 says | On disk |
|---|---|
| "Add `OperatingLimit` to the Lab 2 README node list" | Landed at `Lab_2_Databricks_ETL_Neo4j/README.md:52` |
| "Re-measure routing with the refusal rule in place" | Run. `worklog/lab5-test-results.md`, 19 of 20, 6 of 6 on supervisor routing, 3 of 3 on `graphrag_node`. Then invalidated again, see F3 |
| "`VOC_COURSE_NOTEBOOKS` names 10 entries ... only `data_utils.py` and `tools.py`" | 13 entries. `agent.py` and `memory.py` joined. Order is still right: `00_cluster_smoke_test.ipynb` first, Lab 5 before Lab 6 |
| "`slides/platform-overview/01-workshop-over.md:126-143` still lists MCP as required shared provisioning" | It does not. `:128` reads "used only in the Part B demo", `:129` "in the instructor's workspace", `:144` "Lab 4 Part B is an instructor demo ... You need no credential". **Rescope the item:** what is left is that the slides carry no Lab 5 or Lab 6 content at all |
| "`lab4-instructions.adoc:552` still says 'You have completed the workshop'" | That line is gone. `:557` now hands off to Lab 5. **Rescope the item:** what is left is absence, not contradiction. `site/nav.adoc` has no Lab 5 or Lab 6 entry and no `lab5*.adoc` or `lab6*.adoc` exists |

Two more that belong in section 2 and are recorded nowhere:

- **Genie space identified by ID, never by name.** `PART_A.md` section 5.2 now has the participant copy the 32 character ID out of `.../genie/rooms/<SPACE_ID>`, and `PART_B.md` pins the demo space `aircraft-genie`, `01f1661b55731a0293c3f84ac9c5ba52`. Lab 5 section 1 and Lab 6 section 2 both read `GENIE_SPACE_ID`. This closes a real break: every participant titles their space differently, so nothing downstream could have looked one up by name.
- **`mlflow.langchain.autolog()` guarded.** `agent.py` calls it only behind `importlib.util.find_spec("langchain")`. Unguarded it turns a missing optional package into a container that cannot load the model, and nothing in the agent needs `langchain` itself.

**One rule in section 3 is now satisfied by a route it did not predict. CLOSED, and the section 3 wording is updated.** The two checks before a `.py` helper joins the list said `agent.py` fails the first, because `01_langgraph_agent.ipynb` does not import it. `Lab_6_Agent_Memory/01_agent_memory.ipynb` imports it three times and `Lab_5_LangGraph_Agent/02_deploy_and_evaluate.ipynb` four, so both helpers pass both checks and **the importing notebook can live in a different lab than the helper**. What the rule did not anticipate is the failure that actually landed: the helper shipped and its notebook did not.

### 9.3 The measurement that had to be retaken. CLOSED

**Retaken. 48 of 48 across 9 groups against `5fb3097`, defects A, B, C and E all fixed.** The record below stands as the reason it had to be retaken. Defect F, the nondeterministic components question, is now fixed too, at Round 4 in `worklog/lab5-test-results.md`: 0 invented, 0 loose and 0 zero-row across 10 runs, regression still 48 of 48. All five known `cypher_node` defects are closed except defect D, which is cosmetic and held.

**F3. `tools.py` changed by 56 lines after the 19 of 20 run, so that number was void.**

`worklog/lab5-test-results.md` closes with three defects filed as "found, reported and not fixed". All three are fixed in the working tree:

- **A, the reading refusal swallowing limit questions.** `tools.py:260`, a new "Decide by what is being asked for, not by the words it is asked in" rule, plus the A321neo case worked out longhand at `:269`.
- **B, `_reject_writes` matching inside string literals.** `_STRING_LITERAL` at `tools.py:554`, masked before `_WRITE_CLAUSE.search` at `:582`.
- **C, `OperatingLimit.parameterName` values undocumented.** `tools.py:295` now names all four.

Each fix is right and each one edits the prompt the 19 of 20 was taken against. Section 8's own rule applies without exception, and the rerun is what closed this. **One correction to carry forward: B was a string-literal masking bug in the write guard. `MATCH (r:Removal)` was never a false positive, and any note claiming otherwise is wrong.** `worklog/lab5-test-results.md` still closes with these three filed as unfixed; edit it in place rather than writing a third worklog.

### 9.4 The critical path: Phase 2 ran, and it did not pass its own criterion

**Corrected 2026-08-08 after `worklog/lab5_memory_off_baseline.json` was found.** The earlier draft of this subsection said Lab 6 "redeploys over nothing". That was wrong. An endpoint exists.

**What is done.** `fleet-ops-assistant-ryan-knight-neo4j-com`, from UC model `databricks-neo4j-workshop.agents.fleet_ops_assistant` version 1. Cold deploy timed at 15.8 minutes. `endpoint_shared_with_lab6: true`, so the one-endpoint decision held. The baseline is persisted as an artifact, which is what section 4 called load-bearing. Phase 2 steps 1, 3 and 7 are done.

**F4a. Phase 2 has not met its completion criterion, and the criterion is exactly what failed.** Section 6 says "Completion: a successful Genie call **through the endpoint**. A successful deploy is not the criterion." The baseline records `genie_node_unauthorized`: the endpoint returns "is not authorized to use or monitor this SQL Endpoint". Cause recorded in the artifact: the model was logged with `DatabricksGenieSpace` alone, and a Genie space resource does not carry the SQL warehouse behind it, so the serving principal reaches the space and not the compute under it.

This is the silent failure section 3 predicted twice, once as "the credential most likely to fail silently until the first request" and once as "**Genie is the one that fails here, not Neo4j**". The prediction was right. Routing results in the baseline still stand, because the supervisor routed to `genie_node` correctly; no Genie-sourced number in that run does.

**Updated this pass: the fix is written and unrun.** `02_deploy_and_evaluate.ipynb:208-211` declares `DatabricksGenieSpace`, `DatabricksSQLWarehouse` and two `DatabricksServingEndpoint` entries in one list, and `Lab_5_LangGraph_Agent/README.md:233-238` teaches the defect as a lesson. **What is left is one redeploy and one Genie question through the endpoint.** Until that call returns an answer instead of an authorization error, Phase 2 is open and the fix is a hypothesis with good evidence behind it.

**F4b. The baseline was captured against a `tools.py` that no longer exists, so the memory comparison is confounded.** Measured:

| File | Deployed sha256 | Working tree |
|---|---|---|
| `agent.py` | `80106bbd…` | same |
| `data_utils.py` | `3b4f2e00…` | same |
| **`tools.py`** | **`c837dd50…`** | **`a2706012…`, differs** |

The artifact's own note says the deployed `tools.py` carries the two schema fixes, the regime casing and the traversal. It predates defects A, B and C from 9.3. So a memory-on run against the current file compared to this memory-off baseline attributes a supervisor-prompt change to memory. **Either re-capture the baseline after redeploying with the current `tools.py`, or record the sha mismatch in Lab 6 section 9 so the comparison is read with it.** Re-capture is cleaner, and F4a forces a redeploy anyway.

**F4c. The deployed model was built from uncommitted code.** The artifact records `tools_py_uncommitted: true` against `tools_py_last_commit: 9193b92`. The endpoint's provenance is a sha of a file that exists in one working tree and nowhere else. F1 stops being hygiene and becomes the thing that makes this endpoint reproducible.

**F4d. `02_deploy_and_evaluate.ipynb` still does not exist. CLOSED.** It landed in `b82ca4b` at 30 cells, 13 code, and it was written from the run that already happened, exactly as suggested: it carries the endpoint name, the UC model name, the pinned requirements, the cold-deploy timing and the resource defect. The Lab 5 README documents the warehouse defect and the requirements pin as lessons rather than as gaps. **The one thing it did not carry with it is a `lab/course.env` entry**, so the notebook a participant needs is the one file in Lab 5 the Vocareum upload does not ship. That is now in section 3.

**F4e, new this pass. The baseline is dated on a third axis, and this one is not fixed by a redeploy alone.** The artifact records `lakehouse_provenance: pre-rebuild`. The gold tables have since been rebuilt, `worklog/lakehouse-rebuild.md`, and N1Speed moved from an RPM scale of 2500.7 to 5282.7 to a percent scale of 75.2 to 107.1. So even a Genie answer captured in that run would not reproduce today. The artifact says as much itself: `effect_on_this_baseline` notes that "no genie numeric answer captured now would have reproduced after the rebuild". **Re-capture is the only option that leaves a comparable baseline**, and it is cheap, because F4a forces the redeploy anyway.

**F4f. A fourth axis, and it is the one most likely to be misread as a win.** The baseline's `cypher_maintenance_history` answer is known-bad. It was captured before defect E was fixed, when `cypher_node` wrote the `AFFECTS_AIRCRAFT` arrow backwards and returned zero rows with no error. **A memory-on run returning 23 events for `N10004` is the defect E fix landing, not memory improving recall.** Whoever reads the off-versus-on comparison has to be told this in the comparison itself, not here.

### 9.5 Reorder Phase 0, because Lab 6 is now built against an unchecked assumption

- **F5. The AuraDB Free index tolerance check has still not run.** Section 3 calls it "the one item that can still flip Lab 6 to no-go" and section 7 says run it first and run it alone. Lab 6 is now 116K of finished material written against the assumption it passes. The cost of a "no" is no longer a plan paragraph. It is one connect against a fresh AuraDB Free instance.

  **It does not close the write-target decision as well.** An earlier draft here said it did, on the strength of section 7 recommending a fresh instance. Ryan chose option B instead: Lab 6 writes to `f024ea61`, as the secret scope already points. The check still needs its own fresh AuraDB Free instance, and it is now a separate provision from anything Lab 6 does.

  **Measure Lab 3 plus Lab 6 on one instance, and do not take `f024ea61` as reassurance.** It carries 59 indexes today, and it is a multi-database instance, not Free. Participants get Free.

  **Discover the home database, never assume `neo4j`.** `f024ea61` carries four databases and none is named `neo4j`; its home database is named `f024ea61`. `verify_connectivity()` succeeds and anything routed at `system` succeeds, so an instance looks healthy right up to the first real query, which fails with `Neo.ClientError.Database.DatabaseNotFound`. A tolerance check hardcoding `neo4j` reports a false pass or an unreadable failure. **Read the target out of `SHOW DATABASES` first.**
- **F6. Model Serving endpoint quota.** Unchanged, and it now gates step 6 of Phase 2, the second endpoint under a different user. Note the measured cold deploy of 15.8 minutes when sizing a class-wide test.

### 9.6 Cheap items that keep getting deferred

- **Drop `Reading` and `HAS_READING` from the loader.** Still not done. `workshop-setup/populate_aircraft_db/.../loader.py` lines 18, 43, 104, 198, 202, 337, 342, 343, 892-896, 913-917. The test worklog's label census shows `Reading 155520` on the development instance, which is what makes an admin's graph unlike any participant's while debugging.
- **The Lab 2 validation harness still does not load `OperatingLimit`.** The README half landed, this half did not, and it is how the limit collision reached Lab 3 unnoticed.
- **The architecture diagram.** `images/lab-architecture-overview.png` still shows the Part B MCP topology, rendered at `README.md:36` and `Lab_4_Compound_AI_Agents/README.md:13`. `lab-architecture-overview.excalidraw` sits beside it, so this is an edit and not a redraw.

### 9.7 One decision worth reopening, on new information. TAKEN

**Taken as recorded in section 4: do not attach, and drop the two `TABLE_COMMENTS` and two `COLUMN_COMMENTS` entries.** Applied. Section 5 question 3 is closed. The record below is why.

**F7. `worklog/genie-gold-tables.md` and section 4 disagreed, and the worklog carried a fact section 4 did not.**

Section 4 records the four `fleet_readiness` and `sensor_health` comment statements as known-inert. The worklog agrees they are dead for Genie, and additionally finds one of them **factually wrong**: `lab/workshop.py:397-399` comments `sensor_health.health_status` as "NORMAL, WARNING, or ANOMALY based on 2-sigma deviation", and ANOMALY never occurs.

Inert and wrong are different things. A wrong comment on an unattached table costs nothing today and becomes a wrong Genie answer the moment somebody attaches the table.

**Independently confirmed with numbers, from a second source.** `worklog/lab5_memory_off_baseline.json` records `sensor_health_defect`: the rule `p95 > avg + 2*stddev` is unreachable, and the table emits **284 WARNING, 4 NORMAL and 0 ANOMALY across 288 sensors**. Two investigations reached this separately, which moves it from an opinion about a comment to a measured property of the table.

**Suggested, and this is a new decision rather than finishing the old one:** keep the attach decision untouched, apply the worklog's 4b and 4c, skip 4a. That deletes the wrong column comment and rewrites the `lab/workshop.py:134-135` comment that currently asserts the opposite of the decision. Leaving 4a alone keeps `GOLD_TABLES` and `expected.json` unchanged, so nothing needs re-verifying.

### 9.8 Next steps, in order

**Rewritten 2026-08-09.** Steps 2 and 6 of the previous order are running right now, so the list below starts from what happens when they land.

0. **Commit.** Fourteen files, `HEAD` at `5fb3097`. **This is the second pass in a row that opens with this line**, which is the point 9.1 keeps making. The two running jobs are measuring code that exists in one working tree, so their results have the same provenance problem F4c named. Commit as soon as they report.
1. **Read the two running jobs and record what they say.**
   - `640691439045913` closes Phase 2 or reopens the resource question. **Read the per-tool cell first**: a `genie_node` answer with real numbers is the criterion, and a deploy that reaches READY is not.
   - `38420397665184` prints a per-section table against 75 minutes. **Record the table verbatim into a worklog**, not a summary sentence, because the per-section split is what says which demo to cut.
2. **Re-capture the memory-off baseline on the version 2 endpoint.** F4b, F4e and F4f. The current one is dated on four axes and step 1 forces the redeploy regardless. Carry forward what is still valid: the 15.8 minute cold deploy, the `results_interpretation` block, the subset-not-exact rule for expected tools, and the defect notes. **Score Section 9 with the rules already agreed**: expected tools as a subset test, a zero-row components result as defect F variance rather than a memory result, and `cypher_maintenance_history` at 23 events as defect E landing rather than memory improving recall.
3. **Provision a fresh AuraDB Free instance and run the index tolerance check**, reading the home database out of `SHOW DATABASES` rather than assuming `neo4j`. F5. **Still the only remaining no-go, still unrun**, and it touches nothing else, so it can run beside anything here. `scratchpad/aura_free_index_check.py` is written and has a read-only `check` and an apply-then-roll-back `probe`. **Ryan's to provision.**
4. **Add `Lab_5_LangGraph_Agent/02_deploy_and_evaluate.ipynb` to `VOC_COURSE_NOTEBOOKS`**, between `01_langgraph_agent.ipynb` and `tools.py`. Minutes, and without it Lab 6's prerequisite is a notebook no participant receives. **Verified this pass by reading `lab/course.env:134-146`: the list holds 13 entries and both Lab 6 rows are already there**, `01_agent_memory.ipynb` and `memory.py`. The only Lab 5 or Lab 6 file missing is notebook 02. Whether `02_instructor_demos.ipynb` joins them is section 5 question 8.
5. **Close defect F**, the nondeterministic components question, and edit `worklog/lab5-test-results.md` in place so its closing section stops reading as an open defect list.
6. **Answer the delivery questions in section 5**, questions 6 through 10, all of which Phase 4 hits whether or not they are answered first. Question 5 and question 14 are now closed.
7. **Get the `MENTIONS` fix upstream into `neo4j-labs/agent-memory`.** Worth doing whether or not Lab 6 ships, and it has been carried unactioned across three passes.
8. F6 and 9.6 in any gap. F7 is taken.

**Steps 1 and 2 are one piece of work.** Step 3 runs in parallel with all of it. Step 4 is independent and takes minutes.

**One process step earned by this pass.** Before launching any workspace test run, export every module the notebook imports and diff it against the local file. A workspace `import` of one module leaves the rest at whatever they were, and the resulting traceback names a notebook line rather than the stale file.

**The Lab 5 measurement graph already stopped being what it was.** Ryan chose option B, so Lab 6 writes into `f024ea61`, and the agent-memory schema has landed there. Adoption was verified as correctly scoped to `Aircraft`: 36 nodes gained `type='AIRCRAFT'` and an `:Entity` label, `System.type`, `Sensor.type` and `Component.type` are untouched, all fleet counts unchanged, and both GraphRAG indexes are still ONLINE with 286 of 286 `Chunk` embedded. **It is inert for Lab 5**, because `tools.py` uses a static `GRAPH_SCHEMA` and never introspects. The baseline artifact records it was captured before that, with `agent_memory_schema_installed: false`. **Any Lab 5 measurement taken from here names the memory schema as part of the graph it measured**, per section 8's rule. Silence is not an option.

Watch the section 7 hazard throughout: `populate_aircraft_db/config.py:13` pins `.env` at import time, so a bare `populate-aircraft-db clean` from any directory wipes `1a2c98cc`, whatever the caller believed they were pointed at.

### 9.9 The process fix

Section 8's rules are right and were not applied. **Every correction in 9.2 is a section 3 bullet whose evidence probe is a single `grep` or `ls`.**

Suggested change: each section 3 bullet carries its probe inline. "The list currently names 10 entries" should have carried `grep -c ipynb lab/course.env`, and it would have corrected itself the first time anyone ran it. Re-verification becomes a command instead of a re-read, which is the difference between a rule that holds and one that gets skipped at the end of a long session.

**The same drift is now in a worklog, not just here.** `worklog/lab5-test-results.md` closes with three defects marked unfixed that are fixed, and section 9.3 is only visible because somebody read the code instead of the report. Extend the rule: **a worklog's open-defect list gets edited when the defect closes, or it becomes a second stale plan.**
