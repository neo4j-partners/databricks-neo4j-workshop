# Expand v2: Labs 5 and 6, Plan of Record

Supersedes the status and planning halves of `expand.md`. The reasoning, the measurements, and the defect narratives stay in `expand.md` and are cited here rather than copied. Where the two disagree on what is done, this document wins, because its status was checked against the code on disk on 2026-08-08.

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

### Lab 6, all of Phase 3

`Lab_6_Agent_Memory/` does not exist. Everything below is new. **File layout decided:** `01_agent_memory.ipynb` for the 75 minute hands-on path, `02_instructor_demos.ipynb` for the four run-and-read demos, `memory.py` for the adapters, the `recall` and `remember` nodes, the seed helper and the headline Cypher, and `README.md`. `memory.py` mirrors Lab 5's `tools.py`.

- Install from the volume wheel with `httpx>=0.27.0` alongside it, never from PyPI and never from git.
- Adopt `Aircraft` only, showing the `dry_run=True` report first.
- Write with `extraction_mode="explicit"` and `EntityRef`.
- Pass the wheel path to `log_model` explicitly, because the local version segment resolves from nowhere.
- **Test the `extraction_mode="explicit"` batch path.** The spike measured only singular `add_message`; seeding will use `add_messages`.
- Memory client against the participant's Aura, `recall` and `remember` nodes around the Lab 5 supervisor.
- Ship the memory adapters as lab-provided code, not an exercise. **Name them `MemoryEmbeddings` and `MemoryLLM` in `memory.py`.** `DatabricksEmbeddings` and `DatabricksLLM` are already taken at `Lab_3_Semantic_Search/data_utils.py:43` and `:97`, implementing neo4j-graphrag's synchronous `Embedder` and `LLMInterface`. `neo4j-agent-memory` wants a different async Protocol. One sentence of lab text explains why the two libraries want different Protocols.
- Three hands-on demos, four instructor demos, seeded conversation history, and each hands-on demo timed against its share of 75 minutes.
- Memory off versus on evaluation harness reusing the Phase 2 baseline.
- Get the `MENTIONS` fix upstream into `neo4j-labs`. Worth doing whether or not Lab 6 ships.

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

**Entry:** Phase 1 done, Phase 0 index question answered yes.

1. The four install and write conditions, each as an explicit checklist item.
2. Memory client, `adopt_existing_graph` on `Aircraft` with the dry run shown first.
3. `recall` and `remember` around the Lab 5 supervisor.
4. Seed script in a setup step, never a participant-run loop.
5. Three hands-on demos, timed individually.
6. Four instructor demos, shipped complete as runnable cells.
7. Memory off versus on harness against the Phase 2 baseline.
8. `README.md`, carrying the four pinned-version research answers moved out of `expand.md`.

**Completion:** the headline traversal returns a good answer, the comparison shows a measurable difference in tool calls, tokens or accuracy, and the three hands-on demos fit inside 75 minutes **measured, not estimated**.

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
