# Expand v2: Labs 5 and 6, Plan of Record

Supersedes the status and planning halves of `expand.md`. The reasoning, the measurements, and the defect narratives stay in `expand.md` and are cited here rather than copied. Where the two disagree on what is done, this document wins, because its status was checked against the code on disk on 2026-08-08.

**Last status pass: 2026-08-08, late.** Section 2 gained a Lab 6 subsection, section 3's Phase 3 list shrank to what is genuinely left, and section 7 gained the secret scope collision. Every line below follows the section 8 rules: three states, evidence named, verified against disk.

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

### Lab 5 core

- **Three tools built and live.** `genie_node`, `cypher_node`, `graphrag_node`, the last on `VectorCypherRetriever` lifted from Lab 3 notebook 02.
- **Routing measured.** 38 cells, 0 errors, 12 of 12 overall, 4 of 4 per tool, **8 of 8 on the hard `cypher_node` versus `graphrag_node` slice**. Run against a rebuilt participant-shaped instance carrying zero `Reading` nodes, which is what makes the numbers mean anything.
- **Anchor question runs end to end.** Genie named the engines with abnormal EGT, the graph returned their maintenance history including a bearing wear fault, and the manual's high-EGT procedure closed the answer.
- **Supervisor model settled.** `databricks-meta-llama-3-3-70b-instruct`, one constant, one endpoint across Labs 3 and 5.
- **Credential wiring done.** Lab 5 reads the `fleet-ops-<user-slug>` secret scope Lab 3 notebook 01 creates. No plaintext password in Lab 5. A scope-creation block sits commented out as the recovery path.
- **Degradation path done.** A missing vector index drops `graphrag_node` from the routing list through `available_tools` instead of raising at import.
- **Cypher refusal rule landed.** `tools.py:255`, never substitute a limit, threshold or ceiling for a measurement. Unmeasured: the 12 of 12 run predates it.

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

### Lab 6, workspace findings

Measured against `aws-partner-rk`, host `dbc-cc887abc-9779`, on 2026-08-08.

- **MEASURED: `restartPython()` in Section 1 of both notebooks is load-bearing.** The lab's install line takes `typing_extensions` from 4.4.0 to 4.16.0 and `pydantic` from 1.10.6 to 2.13.4. Importing `neo4j_agent_memory` in the same already-running interpreter raises `ImportError: cannot import name 'Sentinel' from 'typing_extensions'`, because the preloaded 4.4.0 shadows the new install. A fresh interpreter, which is what `restartPython()` produces, imports cleanly. **The install line is correct as written and needs no change.** Recorded because the error message names `typing_extensions` and gives no hint that the fix is a restart, so a participant who skips that cell will not self-diagnose.
- **LANDED: the wheel now exists in this workspace's volume.** `neo4j_agent_memory-0.5.1.dev0+mentions-py3-none-any.whl` was absent from `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/` and has been uploaded by hand. Section 1 of both notebooks would have failed here before that. **This is a property of this one workspace, not a gap in the provisioning path.** `lab/workshop.py:224` defines `WHEELS_DIR`, `:714` resolves it and `:734` enumerates the wheels, so a Vocareum provision does upload it. `aws-partner-rk` is a plain workspace that was never provisioned that way. Corrects an earlier note here that read "nothing in the provisioning path puts it there yet", which was wrong.
- **MEASURED: Lab 6 gets its dependencies from cluster libraries, not from its own `%pip` line, and the delivery path is sound.** `lab/course.env:71` `VOC_COURSE_LIBRARIES` installs `neo4j`, `langgraph`, `pydantic`, `langchain-core`, `databricks-langchain`, `neo4j-graphrag`, `databricks-agents` and the memory wheel itself as cluster libraries. Labs 3 and 5 carry no `%pip` cell at all and rely on this entirely. Lab 6's `%pip` line therefore covers the wheel a second time, which is harmless. **No Lab 6 defect here.** Recorded because a serverless job run outside Vocareum gets none of those libraries and fails at `data_utils.py:22` on `neo4j_graphrag`, which reads like a lab bug and is not one. Any test harness outside Vocareum has to install the `course.env` set itself.

### Capacity

- **Aura node budget measured.** A participant finishing Labs 1 through 3 holds about 21,613 nodes, 10.8 percent of the AuraDB Free cap, with roughly 178,000 nodes of headroom. Memory costs about 20 nodes per participant per session. Full analysis in `worklog/aura-node-budget.md`.

### Content and cleanup

- **Lab 4 Part B reframed.** Instructor-demo banner in place at `PART_B.md:1`. Procedure kept in full.
- **`Lab_1_Aura_Setup/Aura_Free_Trial.md` rewritten.** Points at AuraDB Free and warns off the 14-day trial button by name.
- **Lab 2 GDS note added.** `02_gds_knn_aircraft.ipynb` says it cannot run on AuraDB Free.
- **Lab 2 write mode corrected** to Append in the README.
- **`vocareum/courseware/` deleted**, 10 files and 2.3M, along with `build_data_zip.py`. Nothing read either.
- **Repository documentation complete**, plus `agenda.md` and the object names in `lab/workshop.py`.
- **Labs 1 and 4 ship as notebooks.** `Lab_1_Aura_Setup/01_aura_setup.ipynb` at 25 cells and `Lab_4_Compound_AI_Agents/04_genie_agent.ipynb` at 31 cells, both nbformat 4.5 with no stale outputs and every image URL resolving to a tracked file. A Vocareum student never clones the repository and never sees a rendered README, so a browser lab whose instructions live only in markdown reaches them as no instructions. The click-through steps are markdown cells beside the few runnable ones. The source markdown files stay where they are. **Part B carries zero code cells by design**, so a participant who scrolls into the instructor demo can run nothing.
- **`Lab_5_LangGraph_Agent/agent.py` exists**, 15.6K, written 2026-08-08. `02_deploy_and_evaluate.ipynb` does not.

---

## 3. What Remains

### Blocking the plan

- **Confirm AuraDB Free tolerates 59 indexes and six vector indexes.** The memory library creates 33 indexes and 12 constraints on first connect. **This is the one item that can still flip Lab 6 to no-go.**
- **Check the Model Serving endpoint quota** against the largest expected class size. Deployment is required, so this is a hard prerequisite.
- **Confirm `populate_aircraft_db` installs and runs from a serverless notebook cell**, or pick the job or vendored fallback. Admin path only now, so it no longer blocks any lab.

### Lab 5, to finish Phase 1

- **Re-measure routing with the refusal rule in place.** It edits the prompt the 12 of 12 was taken against.
- **Exercise the extracted-entity routing path** against a graph loaded with extraction on. Same run as the item above.
- **Optional hybrid retrieval exercise** for participants who ran Lab 3 notebook 03. Cuttable.

### Lab 5, all of Phase 2

- `ResponsesAgent` wrapper with MLflow autologging.
- **Measure how the serving principal reads the secret scope.** Expected fix is an endpoint environment variable plus READ for the endpoint principal. Unmeasured, and it is the credential most likely to fail silently until the first request.
- Genie space and model endpoint declared as resources at log time.
- Serving principal confirmed against the Unity Catalog tables behind the Genie space, not just the space.
- Log to Unity Catalog, deploy, **then call the deployed endpoint** with one question per tool and with the anchor question.
- Time a cold deploy so the lab names the number.
- Deploy a second endpoint as a different user and confirm both stay healthy.
- MLflow evaluation against the fixed question set, run against the deployed endpoint.
- `02_deploy_and_evaluate.ipynb`, `eval/questions.jsonl`, and the Lab 5 README completion. `agent.py` landed 2026-08-08; the other two do not exist.

### Lab 6, the rest of Phase 3

**The files are written. What is left is execution.** The build items that closed moved up to section 2. Everything below is a measurement Phase 3 cannot complete without, plus one thing outside the lab.

- **Run `01_agent_memory.ipynb` end to end against a live instance.** Nothing in this lab has ever been executed. Blocked on the write-target question below, which is the next decision anybody picks this up needs.
- **Decide which Aura instance the test writes to.** The secret scope Lab 6 reads points at Track A. See section 7, where the collision is recorded. **This is a decision, not a task**, and it is the single thing standing between Lab 6 and its first end-to-end run.
- **Time each hands-on demo individually against its share of 75 minutes.** MEASURED, not estimated, per the Phase 3 completion criterion. Nothing is timed today.
- **Test the `extraction_mode="explicit"` batch path.** The spike measured only singular `add_message`; the seed helper uses `add_messages`. Still unmeasured.
- **Verify the two Foundation Model endpoints from this workspace.** `databricks-bge-large-en` returning 1024-dimension vectors, and `databricks-meta-llama-3-3-70b-instruct` answering. Written into three probe runs, never reached a successful execution.
- **Memory off versus on evaluation harness.** Blocked on the Phase 2 baseline artifact, which does not exist. See the Phase 2 entry.
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
- **Finish `VOC_COURSE_NOTEBOOKS` in `lab/course.env`. Partially done, and the checklist stays open.** The list currently names 10 entries, all backed by files on disk, including Labs 1, 4 and 5. Still to add: `02_deploy_and_evaluate.ipynb`, and whatever Lab 6 ships. **The list is order sensitive.** `lab/user_setup.sh:134` makes the first entry the student's landing page, so `00_cluster_smoke_test.ipynb` stays first and anything new goes where a student reaches it, never appended. Confirm each `.py` helper lands as a FILE and not a NOTEBOOK, the `lab3-fix.md` defect. Only `data_utils.py` and `tools.py` are in the list today.

  **The FILE-not-NOTEBOOK behavior lives outside this repository, which is why it bites invisibly.** It is in the pinned `dbx-vocareum-tools` package, verified at `.venv/lib/python3.13/site-packages/dbx_vocareum_tools/labruntime/voclab.py`: `NOTEBOOK_FORMATS[".py"]` must read `("AUTO", None)` and `NOTEBOOK_KEEP_EXTENSIONS` must read `(".py",)`. An upload against a lock older than `dbx-vocareum` commit `68e63a5` ships the defect and hash-verifies cleanly, so nothing downstream notices. **Whoever runs the final upload checks that pair first.**

  **Two checks before any `.py` helper joins the list.** Does a notebook the student actually opens import it, and does its first line lack `# Databricks notebook source`. `agent.py` passes the second, its first line is a docstring, and fails the first: `01_langgraph_agent.ipynb` does not import it, so shipping it today hands a student a module nothing they have opens. `agent.py` and `02_deploy_and_evaluate.ipynb` therefore go in together, in one pass. `memory.py` gets the same two checks.
- Timings recorded per lab and per Lab 6 demo.

### Downstream content, Phase 5

- **The Lab 5 architecture diagram.** The shipped PNG still shows the Part B MCP topology, and both the root README and the Lab 4 README display it.
- **Rewrite the Antora site in `site/`.** Roughly 30 stale lines across 9 `.adoc` files. Two are the exact claims this work exists to remove: `lab4-instructions.adoc:16` still says participants need no data in their own instance, and `:552` still says "You have completed the workshop." **`deploy-antora.yml` publishes on every push to `main`, so until this lands the published site contradicts the repository.**
- **Rewrite the slides in `slides/`.** `platform-overview/01-workshop-over.md:126-143` still lists MCP as required shared provisioning.
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

  **The residue is on the provisioning side, and it is inert rather than broken.** `lab/workshop.py:374-375` writes table comments for `fleet_readiness` and `sensor_health`, and `:392-400` writes column comments for `readiness_status` and `health_status`. A Genie space reads comments only for tables in its scope, so those four statements provably do nothing for Lab 4. Both tables stay in `GOLD_TABLES` for reasons unrelated to Genie, so this is dead weight, not a defect. **Recorded as known-inert, not queued as cleanup.** Somebody who later wants the four statements dropped is making a new decision, not finishing this one. Closes the section 5 question.
- **Browser labs ship as notebooks.** Labs 1 and 4 join the notebook set, because a Vocareum student sees no rendered README. Delivery format, not lesson content. The source markdown stays where it is, so this sits outside the "do not rewrite Labs 1 through 3" fence.
- **Labs get written before anything that describes them.** Lab 5, then Lab 6, then the Vocareum notebook list, then the site and slides in one pass.
- **This document set owns the plan.** `proposed-outline.md` and `workshop-improve.md` carry superseded banners.

---

## 5. Outstanding Questions

- **When does the local `mcp-neo4j-cypher` section land in Lab 5?** Proposed as a future section rather than first release, since it is the part most likely to behave differently on serverless.
- **How long does Part B stay maintained, and what is the review date?** A break now costs one demo instead of a lab. Set the date alongside the `neo4j-agent-memory` re-check date so both external dependencies get looked at together.
- **Does the half-day split ship as supported, or stay best effort?** Phase 5 answers this, and it owes written guidance rather than code now that both catch-up cells are dropped.
- **Does `expand.md` get retired, archived, or kept as the reasoning appendix?** This document cites it heavily. Two live planning documents drift.

---

## 6. Phased Implementation Plan

Six phases. Each has an entry condition, a body, and a completion criterion that is a measurement rather than a claim.

### Phase 0: Prove the risky parts

**Status:** In progress. Loader work done. Memory spike done, GO with conditions.

| Item | Owner track | Blocks |
|---|---|---|
| AuraDB Free index tolerance, 59 indexes and 6 vector indexes | B | Phase 3 entirely |
| Model Serving endpoint quota at class size | A | Phase 2 completion, Phase 4 |
| `explicit_mode` batch path through `add_messages` | B | Phase 3 seeding step |
| Serverless install of `populate_aircraft_db`, or pick the fallback | A | nothing participant-facing |
| Drop `Reading` and `HAS_READING` from the loader | A | nothing, but it makes every later debug session honest |

**Completion:** the index tolerance question returns a yes, or Lab 6 is formally re-scoped.

**Still open, and now carrying more weight than it did.** Phase 3 was entered and built out with this question unanswered, on an explicit "proceed anyway". A no no longer delays Lab 6, it invalidates four files that are already written.

### Phase 1: Lab 5 core agent

**Status:** Core built and measured. Three items left, two of which close in one run.

1. Re-measure routing with the refusal rule in place.
2. Exercise the extracted-entity path against an extraction-on graph. Same run as 1.
3. The hybrid retrieval exercise, optional and cuttable.

**Completion:** the anchor question is correct end to end and each routing case lands on the expected tool, with `cypher_node` versus `graphrag_node` reported as its own number, **against the code currently on disk**.

### Phase 2: Lab 5 ships, deployment included

**Entry:** Phase 1 re-run done. **Not done when the notebook is written. Done when a deployed endpoint answers as a service principal.**

Order inside the phase, because each step gates the next:

1. `ResponsesAgent` wrapper, resources declared at log time.
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

**Status: written, not run. Steps 1 through 6 and 8 are LANDED. Steps 7 and every timing are open.**

1. LANDED. The four install and write conditions, each as an explicit checklist item.
2. LANDED. Memory client, `adopt_existing_graph` on `Aircraft` with the dry run shown first.
3. LANDED. `recall` and `remember` around the Lab 5 supervisor.
4. LANDED. Seed script in a setup step, never a participant-run loop.
5. LANDED as cells, **open as a measurement.** Three hands-on demos exist. None is timed.
6. LANDED. Four instructor demos, shipped complete as runnable cells in `02_instructor_demos.ipynb`, each standalone because the shared names sit in one setup cell.
7. OPEN, and blocked. Memory off versus on harness against the Phase 2 baseline, which does not exist yet.
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

**Recommendation: A for the first end-to-end run, then B once on a freshly reloaded graph** to prove the scope path before Phase 4. That gets both properties without ever putting Track A's evidence at risk while it is being used.

**Hazard, unchanged and worth repeating here.** `populate_aircraft_db/config.py:13` pins `populate_aircraft_db/.env` at import time, and that file points at `1a2c98cc`. A bare `populate-aircraft-db clean` run from any directory wipes the memory instance regardless of what the caller thought they were pointed at.

**With one person on all three tracks, the tracks collapse to sequential in wall-clock terms.** The separation still earns its keep, because it means a failing loader test is a loader problem and nothing else.

### Recommended order for one operator

1. Phase 0 index tolerance check. It is the only remaining no-go.
2. Phase 1 re-run, on the extraction-on instance.
3. Phase 2, straight through, since each step gates the next.
4. Phase 3.
5. Phase 4, then Phase 5.

Slot the Lab 2 README gaps, the validation harness gap, and the `Reading` drop into any waiting period. Each is under two hours and none blocks anything.

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

Checked 2026-08-08 against the **working tree**, not against `HEAD`. The two differ by 15 modified files and 2 untracked paths, which is the first fix below.

Ordered by what it costs to fix, not by which section it corrects. 9.1 is minutes, 9.4 is the critical path, 9.9 is the process change that stops the list regenerating.

### 9.1 Commit, before anything else

- **F1. None of this work is committed.** `git status` against `694e5ca` shows 15 modified files and 2 untracked paths. That includes the whole of `Lab_6_Agent_Memory/README.md`, a 56 line `tools.py` schema rewrite, a 51 line `agent.py` change, and the `lab/course.env` notebook list. One stray `git checkout` loses the last session entirely.
- **F2. `lab/Lab_6_Agent_Memory` is untracked, and the Vocareum upload reads through it.** `lab/course.env` names `Lab_6_Agent_Memory/01_agent_memory.ipynb` and `Lab_6_Agent_Memory/memory.py` relative to `lab/`. Both resolve only through the symlink `lab/Lab_6_Agent_Memory -> ../Lab_6_Agent_Memory`, and it is the one lab symlink git does not have. The other five are tracked. **An upload from a fresh clone finds no Lab 6.**

**Fix:** `git add lab/Lab_6_Agent_Memory Lab_6_Agent_Memory/README.md`, then commit the lot. Minutes, and it is the cheapest item here.

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

**One rule in section 3 is now satisfied by a route it did not predict.** The two checks before a `.py` helper joins the list say `agent.py` fails the first, because `01_langgraph_agent.ipynb` does not import it. True, and no longer the whole picture: `Lab_6_Agent_Memory/01_agent_memory.ipynb:962` does `from agent import`. `memory.py` clears the same check through the same notebook, and section 2 already notes it "has to ship together with the notebook that imports it", which `lab/course.env` now does. So both helpers shipping today is defensible. **Update the rule's worked example rather than pulling either entry**, and note that the importing notebook can live in a different lab than the helper.

### 9.3 The measurement that has to be retaken

**F3. `tools.py` changed by 56 lines after the 19 of 20 run, so that number is void.**

`worklog/lab5-test-results.md` closes with three defects filed as "found, reported and not fixed". All three are fixed in the working tree:

- **A, the reading refusal swallowing limit questions.** `tools.py:260`, a new "Decide by what is being asked for, not by the words it is asked in" rule, plus the A321neo case worked out longhand at `:269`.
- **B, `_reject_writes` matching inside string literals.** `_STRING_LITERAL` at `tools.py:554`, masked before `_WRITE_CLAUSE.search` at `:582`.
- **C, `OperatingLimit.parameterName` values undocumented.** `tools.py:295` now names all four.

Each fix is right and each one edits the prompt the 19 of 20 was taken against. Section 8's own rule applies without exception. **Rerun the same harness against the current file, and edit `lab5-test-results.md` in place rather than writing a third worklog.** As it stands its closing section reads as an open defect list, and it is not one.

### 9.4 The critical path: Lab 5 has no deploy notebook

**F4. Lab 6 hard-depends on an endpoint that no notebook creates.**

- `Lab_6_Agent_Memory/README.md:25` lists "the Model Serving endpoint you deployed" as a **required** Lab 5 prerequisite.
- `01_agent_memory.ipynb` imports `FleetOpsAgent` at `:962`, calls `mlflow.pyfunc.log_model` at `:1126`, and calls `agents.deploy` at `:1164`.
- `Lab_5_LangGraph_Agent/` holds no notebook 02. Its notebook 01 closing cell still promises one, and the Lab 5 README already flags the gap in writing.

So Lab 6 section 10 redeploys over nothing, and the memory-off baseline that section 4 calls load-bearing has no source. **Phase 2 has gone from a tail item to the only thing between here and an end-to-end run.**

Two options:

- **(a) Write `02_deploy_and_evaluate.ipynb` as planned.** Keeps the one-endpoint-redeployed decision, and gives Lab 6 its persisted baseline.
- **(b) Move the first deploy into Lab 6 and drop notebook 02.** Cheaper, but it deletes the "Deploying the Agent" item from `agenda.md` and leaves off-versus-on with nothing to compare against.

**Take (a).** Section 4, `agenda.md`, and Lab 6's own README all already tell the participant it happened.

Worth noting in section 7's favor: Lab 6 was built against the in-notebook agent while Phase 2 stayed open, exactly as the parallelism table said it could be. What did not happen is Phase 2.

### 9.5 Reorder Phase 0, because Lab 6 is now built against an unchecked assumption

- **F5. The AuraDB Free index tolerance check has still not run.** Section 3 calls it "the one item that can still flip Lab 6 to no-go" and section 7 says run it first and run it alone. Lab 6 is now 116K of finished material written against the assumption it passes. The cost of a "no" is no longer a plan paragraph. It is one connect against a fresh AuraDB Free instance. **Run it before anything in 9.4.**

  **It also answers Phase 3's write-target decision for free.** Section 7 recommends option A, a fresh instance, for Lab 6's first end-to-end run, precisely so Lab 6 stops writing into Track A's measurement graph. The index check needs a fresh AuraDB Free instance and Lab 6's first run wants one. **Make it the same instance and both items close on one provision.**
- **F6. Model Serving endpoint quota.** Unchanged, and it now gates step 6 of Phase 2, the second endpoint under a different user.

### 9.6 Cheap items that keep getting deferred

- **Drop `Reading` and `HAS_READING` from the loader.** Still not done. `workshop-setup/populate_aircraft_db/.../loader.py` lines 18, 43, 104, 198, 202, 337, 342, 343, 892-896, 913-917. The test worklog's label census shows `Reading 155520` on the development instance, which is what makes an admin's graph unlike any participant's while debugging.
- **The Lab 2 validation harness still does not load `OperatingLimit`.** The README half landed, this half did not, and it is how the limit collision reached Lab 3 unnoticed.
- **The architecture diagram.** `images/lab-architecture-overview.png` still shows the Part B MCP topology, rendered at `README.md:36` and `Lab_4_Compound_AI_Agents/README.md:13`. `lab-architecture-overview.excalidraw` sits beside it, so this is an edit and not a redraw.

### 9.7 One decision worth reopening, on new information

**F7. `worklog/genie-gold-tables.md` and section 4 disagree, and the worklog carries a fact section 4 does not.**

Section 4 records the four `fleet_readiness` and `sensor_health` comment statements as known-inert. The worklog agrees they are dead for Genie, and additionally finds one of them **factually wrong**: `lab/workshop.py:397-399` comments `sensor_health.health_status` as "NORMAL, WARNING, or ANOMALY based on 2-sigma deviation", and ANOMALY never occurs.

Inert and wrong are different things. A wrong comment on an unattached table costs nothing today and becomes a wrong Genie answer the moment somebody attaches the table.

**Suggested, and this is a new decision rather than finishing the old one:** keep the attach decision untouched, apply the worklog's 4b and 4c, skip 4a. That deletes the wrong column comment and rewrites the `lab/workshop.py:134-135` comment that currently asserts the opposite of the decision. Leaving 4a alone keeps `GOLD_TABLES` and `expected.json` unchanged, so nothing needs re-verifying.

### 9.8 Suggested order

1. **Commit.** F1 and F2. Minutes.
2. **Provision one fresh AuraDB Free instance**, run the index tolerance check on it, and keep it as Lab 6's write target. F5, plus section 7's write-target decision, on one provision. Only remaining no-go.
3. **Rerun the Lab 5 harness** against the current `tools.py`, on `f024ea61`. F3.
4. **`02_deploy_and_evaluate.ipynb`**, straight through Phase 2 including the persisted baseline. F4.
5. **Lab 6 measurement**, which is all Phase 3 has left.
6. F6, F7 and 9.6 in any gap.

Steps 2 and 3 no longer contend for a graph, which is the point of doing 2 the way it is written. Step 3 stays on `f024ea61`, step 2 never touches it, and on two people they run together. Watch the section 7 hazard while doing either: `populate_aircraft_db/config.py:13` pins `.env` at import time, so a bare `populate-aircraft-db clean` from any directory wipes `1a2c98cc`.

### 9.9 The process fix

Section 8's rules are right and were not applied. **Every correction in 9.2 is a section 3 bullet whose evidence probe is a single `grep` or `ls`.**

Suggested change: each section 3 bullet carries its probe inline. "The list currently names 10 entries" should have carried `grep -c ipynb lab/course.env`, and it would have corrected itself the first time anyone ran it. Re-verification becomes a command instead of a re-read, which is the difference between a rule that holds and one that gets skipped at the end of a long session.

**The same drift is now in a worklog, not just here.** `worklog/lab5-test-results.md` closes with three defects marked unfixed that are fixed, and section 9.3 is only visible because somebody read the code instead of the report. Extend the rule: **a worklog's open-defect list gets edited when the defect closes, or it becomes a second stale plan.**
