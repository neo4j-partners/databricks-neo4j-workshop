# Expand v3: Labs 5 and 6, Plan of Record

Replaces `expand-v2.md`. Same facts, rewritten to be read. Where this document and `expand.md` or `expand-v2.md` disagree, this one wins.

**Status date:** 2026-08-09. Every claim below was checked against files on disk or against a job run, not inferred.

**Three things a reader should know before starting:**

- **Lab 5 works end to end, deployed.** All three tools answer through a Model Serving endpoint, including the Genie tool that was failing on authorization.
- **Lab 6 works and its central claim now holds.** Memory-on beats memory-off on the referring-question test, on a cleared instance, against a scorer tightened after the loose one reported a false pass.
- **One question can still kill Lab 6:** whether AuraDB Free tolerates the combined index and constraint count of Labs 3 and 6 on one instance. Unrun. Everything else is polish.

---

## 1. The Goal, and Why

**What we are building.** Two required labs at the end of the workshop.

- **Lab 5:** a LangGraph supervisor agent routing across three tools. Genie over Delta telemetry, Cypher over the participant's own Aura instance, GraphRAG over the maintenance manuals.
- **Lab 6:** memory for that agent, stored in the same Aura instance.

**The problem they fix.**

- Labs 1 through 3 build a graph in the participant's own database.
- Lab 4 Part B then answered questions against somebody else's database, over a shared MCP server, and said so in writing.
- So the payoff moment used none of the participant's work, and the Lab 3 GraphRAG retrievers were never wired into an agent at all.

**The shape of the fix.**

- Part B becomes a 10 minute instructor demo.
- Lab 5 becomes the single participant continuation from Part A.
- Every required lab reads and writes one database, and each lab's output is the next lab's input. Lab 2 loads the fleet, Lab 3 adds manuals and vector indexes, Lab 5 queries both, Lab 6 writes memory back.

**Why memory is the ending.** Memory nodes and fleet nodes land in one graph, so one Cypher query traverses both.

- The headline demo asks which aircraft several technicians independently asked about this week, and whether those are the ones actually failing.
- Neither half answers it alone. That is the argument for memory in Neo4j rather than in a memory product.

**Result.** Roughly five hours of required lab time. A full-day advanced format, with a half-day split as a later, best-effort option.

---

## 2. What Is Done

### Loader and data

- **One embedding path.** `populate_aircraft_db` embeds through `databricks-bge-large-en`, the same endpoint Lab 3 uses. Cross-path cosine measured at 1.0000000000, so embedder drift is gone rather than mitigated.
- **Loading without an LLM key.** `--skip-extraction` builds a Lab 5 shaped graph using the library's own splitter, embedder and writer, so Document and Chunk nodes match the full path.
  - Measured: 5 `Document`, 286 `Chunk` all embedded, both indexes ONLINE, 20 `OperatingLimit` from CSV.
  - Only the LLM-extracted entities are missing. Everything GraphRAG needs is on the graph.
- **Operating limits load deterministically.** 20 canonical rows from `nodes_operating_limits.csv`, 288 `HAS_LIMIT` edges, no LLM. Lab 3's `limit_retriever` returns populated results on a skip-extraction graph.
- **Units and magnitudes fixed.**
  - `EGT` to `°C` and `N1Speed` to `% RPM`, matching the manual limit tables. All 288 sensors join `OperatingLimit` on a plain string compare.
  - N1 readings are now percent of an `n1_reference_rpm` per engine, in the 94 to 100 range against limits of 92, 100 and 104.
- **Two names, not one.** Extraction writes `ExtractedLimit`. `OperatingLimit` means the 20 CSV rows. Applied across `schema.py`, `data_utils.py`, all three Lab 3 notebooks, `SAMPLE_QUERIES.md` and the Lab 5 tools.
- **The uniqueness constraint keys on `limit_id`,** at `schema.py:26`. The old `name` constraint killed two live enrichment runs.
- **Startup fixed.** `neo4j_database` is a real settings field at `config.py:33`, so Pydantic no longer raises on every subcommand.
- **Full load measured.** Empty instance to complete graph in 4:23, no LLM key. Idempotent: a second run took 4:09 with node counts unchanged.

### Lab 5, the agent itself

- **Three tools built and live.** `genie_node`, `cypher_node`, `graphrag_node`, the last on `VectorCypherRetriever` lifted from Lab 3.
- **Routing measured at 48 of 48 across 9 groups,** against the current `tools.py`, on a participant-shaped instance carrying zero `Reading` nodes. That last detail is what makes the numbers mean anything.
- **The anchor question runs end to end.** Genie names the engines with abnormal EGT, the graph returns their maintenance history including a bearing wear fault, the manual's high-EGT procedure closes the answer.
- **Supervisor model settled:** `databricks-meta-llama-3-3-70b-instruct`, one constant, one endpoint across Labs 3 and 5.
- **Credentials wired.** Lab 5 reads the `fleet-ops-<user-slug>` secret scope that Lab 3 creates. No plaintext password anywhere in Lab 5.
- **Degradation path built.** A missing vector index drops `graphrag_node` from the routing list instead of raising at import.
- **Write guard fixed.** It was matching write keywords inside string literals. `MATCH (r:Removal)` was never a false positive, and any note claiming otherwise is wrong.

**Four Cypher generation defects found and closed. Two are worth reading, because both failed silently.**

- **Backwards relationship arrow.** `cypher_node` wrote `(:Aircraft)-[:AFFECTS_AIRCRAFT]->(:MaintenanceEvent)`. The arrow actually runs the other way.
  - It matched nothing and **returned zero rows with no error**, on an aircraft carrying 23 maintenance events, more than any other in the fleet. Deterministic, 5 runs of 5.
  - Cause: this is the only relationship in the schema pointing toward `Aircraft`, and `Aircraft` is the noun nearly every question starts from. The model anchored on the named noun and pointed the arrow away from it.
  - Fixed with a schema bullet at `tools.py:286-294`. After: 0 of 5 zero-row runs, 23 rows with real severities, direction sweep 0 misses of 6.
- **An invented relationship type.** The components-for-an-aircraft question was nondeterministic across 10 runs, producing six distinct queries.
  - **4 of 10 invented an `AFFECTS_COMPONENT` relationship that does not exist.** 3 of 10 walked a loose two-hop chain. 3 of 10 were correct.
  - A nonexistent relationship type **does not error**. Neo4j matches nothing, so the agent reports "no components found" with total confidence about an aircraft that has 9 of them.
  - Fixed with a schema bullet at `tools.py:295-305`. Ten runs after: 0 invented, 0 loose, 0 zero-row, all ten writing the identical correct traversal.
  - **Residual, accepted.** Row counts still vary between 9, 10 and 23 because some runs add extra columns to the `RETURN DISTINCT` and fan rows back out. The traversal is identical every time and no run returns the wrong component set.

### Lab 5, deployment

- **A live endpoint.** `fleet-ops-assistant-ryan-knight-neo4j-com`, from UC model `databricks-neo4j-workshop.agents.fleet_ops_assistant`, on `aws-partner-rk`.
  - Cold deploy timed at 15.8 minutes. A later redeploy took 9.1 minutes.
  - Shared with Lab 6, as decided. Four served versions exist, 100 percent of traffic on the newest. The older ones sit at zero traffic as the rollback path and cost nothing.
- **Genie through the endpoint works, and that was the hard part.** A fleet-average EGT question routed to `genie_node` and returned **866.65373875 C** against a rebuilt CSV average of 866.7, with no authorization error anywhere in the response.
- **It took two independent fixes, and both are lessons worth teaching.**
  - **Declaring the Genie space is not enough.** Declaring the space grants the space, declaring the warehouse grants the compute, and neither grants the data. The original four-entry resource list was written from an error message naming the SQL endpoint and was never tested against a query that reads a table.
  - **Dropping a Delta table destroys the grants MLflow issued for it.** After the gold-table rebuild, `SHOW GRANTS` on `sensor_readings` showed nothing for the endpoint's service principal. **The operational rule: rebuilding a gold table obsoletes every endpoint logged before it, and the repair is a redeploy, not a regrant.**
  - **The fix is one shared function,** `build_resources(genie_space_id, warehouse_id)` at `agent.py:147`. Twelve entries: the Genie space, the SQL warehouse, the eight gold tables, and the supervisor and embedding endpoints. Both the Lab 5 deploy notebook and Lab 6 call it, so the two labs cannot drift.
- **The deploy notebook ships executed.** `02_deploy_and_evaluate.ipynb`, 30 cells, 13 code, ran top to bottom with zero errors and the committed file carries the outputs.
  - Evaluation scored 6 pairs: routing 1.0 on all six, correctness yes on five of six.
  - **No credential reached any output.** All four Neo4j values were checked against the saved file by value and none appear.
- **Requirements are pinned, not inferred.** Inferred requirements read the cluster, and a cluster carrying the Lab 6 memory wheel yields a requirement that resolves from no index. The container then fails to build about fifteen minutes after anybody stopped watching. Documented at `Lab_5_LangGraph_Agent/README.md:240-244`.

### Lab 6, memory

- **The library research is settled.**
  - Version pinned to a wheel built from the `mentions` branch of the `neo4j-partners` fork, checked in at `lab/courseware/wheels/`.
  - **An upstream defect was found and fixed:** the released version silently drops every `MENTIONS` edge, which is the exact edge the headline query traverses. Fix written, three regression tests, pushed to the fork.
  - The library hard-codes no LLM provider. About 130 lines of adapter binds Databricks Foundation Model endpoints, verified live.
  - Three library API errors were caught by reading the unzipped wheel rather than trusting prose, before any code ran against it.
- **The files exist and are clean.** `memory.py` at 47K, `01_agent_memory.ipynb` at 54 cells, `02_instructor_demos.ipynb` at 32 cells, `README.md` at 383 lines. Every code cell parses. Ruff-clean under the project config. No leaked instance id in either notebook.
- **The headline demo works.** Adopting 36 `Aircraft` takes 3.1 seconds. The joining Cypher runs in under a second and produces a genuine "neither source alone" answer.
- **Lab 6 redeploys the endpoint Lab 5 created,** rather than logging an unregistered run or inventing a second endpoint.

**Three memory defects, each visible only after the previous one was fixed. All closed.**

- **Memory never reached the tools.** The supervisor's only output was a route, and the tool nodes read the raw question. So memory could choose which tool ran and could never tell that tool which aircraft. Genie replied asking for a tail number.
  - **Fix:** the supervisor now emits a resolved question above its route line and rewrites the question once, on the first pass, keeping the original in a separate state key. `memory.py` only. Lab 5's tools are untouched, which is what keeps the memory-off comparison honest.
- **Recall returned the question being asked.** Every run writes the question into the graph, and recall then runs a vector search over message content using that same text. **An exact copy of a string is the nearest neighbour any embedding can return.** Three prior runs had put three copies of the question into the instance, and they took all three recall slots.
  - **Fix:** drop any recalled message whose content matches the question being asked.
  - **Two consequences, worth separating.** The self-recall is real on any instance. The three-identical-copies form is an artifact of re-running the same notebook against the same instance, which a participant does not do.
- **Recall preferred the wrong aircraft.** A follow-up asking "Which system was that on?" resolved to an aircraft from a week of seeded shift notes instead of the one named five seconds earlier in the same session.
  - **Semantic search finds what is related. It cannot know what "that" means, because that is a fact about time, not meaning.**
  - **Fix, two parts.** Recall reads the conversation's own recent turns first and puts the semantic search behind them, deduped. And the scorer was tightened, because the loose one had already reported a false pass: it now requires the expected tail number to appear and no other one to appear.
  - **Result:** the comparison section scores `0/2 off, 2/2 on` on a cleared instance under the strict scorer. The engine names are a second independent check, since the two aircraft fly different engine types.

Full account in `worklog/lab6-memory-defects.md`.

### Lab 6, timing

Machine time only, read off a job run rather than estimated. No reading, no typing.

```
section                                          seconds     m:ss
------------------------------------------------------------------
Section 1: Install                                  40.5     0:40
Section 2: Configuration                            18.5     0:18
Section 3: Connecting the memory client              4.3     0:04
Section 4: Adopting the fleet graph                  1.2     0:01
Section 5: A week of shift history                  10.1     0:10
Section 6: The query that needs both halves          1.0     0:01
Section 7: Recall and remember                       2.0     0:02
Section 8: The thing Lab 5 could not do             38.5     0:38
Section 9: What did memory actually buy?           136.9     2:16
Section 10: Redeploying the endpoint                 7.1     0:07
Section 11: What you built, and what to watch        0.2     0:00
------------------------------------------------------------------
TOTAL                                              260.4     4:20
```

- **Budget is 75 minutes. Cell time is not the constraint** and no demo needs cutting for time.
- **One cell dominates:** the memory-off versus memory-on comparison, because it runs four full agent invocations twice over. Everything else is under 45 seconds.
- **The other 70 minutes are reading, typing and the instructor talking.** No harness can measure those. A dry run with a human still has to.

### Lakehouse gold tables

- **The four original tables held values from an older generator run on the wrong scale, and were dropped and rebuilt.** Full record in `worklog/lakehouse-rebuild.md`.

  | type | was | now |
  |---|---|---|
  | N1Speed | 2500.7 to 5282.7, avg 4648.3 | 75.2 to 107.1, avg 93.5 |
  | EGT | 616.0 to 731.1, avg 654.6 | 635.8 to 1072.9, avg 866.7 |
  | FuelFlow | 0.8 to 1.5, avg 1.1 | 1.0 to 2.1, avg 1.4 |
  | Vibration | 0.1 to 1.1, avg 0.3 | 0.1 to 1.1, avg 0.3 |

  All four now match the committed CSVs exactly.
- **N1 was the serious one.** The tables were in RPM while the graph, the CSVs and the documented limit of 97.0 are in percent, so **Genie answered N1 questions with 5283 against a limit of 97**. Row counts already matched. Only values were wrong.
- **All eight gold tables now exist,** at parity with the graph: 155,520 readings, 288 sensors, 144 systems, 36 aircraft, 14,543 flights, 286 maintenance events. **Four of the eight did not exist before.**
- **The blocker that had to be cleared first.** The pipeline refuses to materialize over a table it does not own. The four tables had been created months earlier by Spark with no owning pipeline, so they had to be dropped.
- **The drop also invalidated the deployed endpoint,** which was not obvious at the time. See the deployment section above.

### Workspace and instance findings

- **The restart cell in Section 1 of both Lab 6 notebooks is load-bearing.** The install line moves `typing_extensions` and `pydantic` to new majors, and importing the memory library in the same interpreter fails with an error naming `typing_extensions` and giving no hint that the fix is a restart. **The install line is correct as written.** Recorded so nobody deletes the restart.
- **Lab 6 gets its dependencies from cluster libraries, not from its own `%pip` line.** `lab/course.env:71` installs the whole set. Labs 3 and 5 carry no pip cell at all. **A test run outside Vocareum gets none of it and fails in a way that reads like a lab bug and is not one.**
- **Upload every module a notebook imports, then diff each one back.** A workspace import of one module silently leaves the others stale, and the resulting traceback names a notebook line rather than the stale file. This cost one failed job run.
- **The development instance has no database named `neo4j`.** Its home database is named after the instance.
  - `verify_connectivity()` succeeds and anything routed at `system` succeeds, so **the instance looks healthy right up to the first real query.**
  - Handled by a fourth secret key, `neo4j-database`, read the same way as the password. Resolution order is model config, then environment variable, then `SHOW DATABASES`.
  - A participant scope written by Lab 3 carries the right value from the start. Only pre-existing development scopes need the key written by hand.
- **Adopting the fleet graph was correctly scoped to `Aircraft` only.** `System.type`, `Sensor.type` and `Component.type` are untouched, all fleet counts unchanged, both GraphRAG indexes still ONLINE with 286 of 286 chunks embedded. **It is inert for Lab 5,** because `tools.py` uses a static schema string and never introspects the database.

### Capacity

- **A participant finishing Labs 1 through 3 holds about 21,613 nodes,** 10.8 percent of the AuraDB Free cap, with roughly 178,000 nodes of headroom. Memory costs about 20 nodes per participant per session. Full analysis in `worklog/aura-node-budget.md`.
- **The 59 indexes coexisting on the development instance prove nothing about Free.** That instance is multi-database and is not Free. **Participants get Free.** Read the 59 as evidence the schema installs, never as evidence the cap tolerates it.

### Content and cleanup

- **Lab 4 Part B reframed** as an instructor demo, with the banner in place and the procedure kept in full. It carries zero code cells by design.
- **Labs 1 and 4 ship as notebooks.** A Vocareum student never clones the repository and never sees a rendered README, so a browser lab whose instructions live only in markdown reaches them as no instructions.
- **Documentation audit done.** 24 factual-drift findings across every top-level, lab and setup markdown file. All 4 blocking and all 12 major are fixed. The 8 remaining are minor and carried in section 3.
- **Smaller fixes landed:** the Aura signup page points at Free and warns off the trial button by name, the GDS notebook says it cannot run on Free, the Lab 2 write mode is corrected to Append, and 2.3M of dead courseware is deleted.

---

## 3. What Remains

### The one thing that can still say no

- **Confirm AuraDB Free tolerates the Lab 3 plus Lab 6 index and constraint total on one instance.**
  - Lab 6 installs 33 indexes and 12 constraints on top of Lab 3's.
  - **The combined total is measured: 59 indexes and 24 constraints,** at 177,382 nodes and 207,605 relationships.
  - **What is missing is the tier.** `dbms.components()` reports `enterprise` on every Aura instance regardless of tier, so no probe from inside the database settles it.
  - **Closing it needs one fresh AuraDB Free instance.** The check itself is written and durable at `workshop-setup/verify/src/verify_aura_caps/main.py`, run as `uv run verify-aura-caps`, in read-only and apply-then-roll-back modes. It reads the home database out of `SHOW DATABASES` rather than assuming `neo4j`.
  - **If Free caps below those numbers, Lab 6 fails for every participant simultaneously.** Ryan's to provision.

### Also blocking delivery

- **Check the Model Serving endpoint quota** against the largest expected class size. Deployment is required, so this is a hard prerequisite. Size the test against the measured 15.8 minute cold deploy.
- **Deploy a second endpoint as a different user** and confirm both stay healthy. Depends on the quota check.

### Lab 5

- **The tool is handed the question rather than the finding.** The anchor question routed all three tools and still reported no maintenance history available, on a graph holding 23 events for that aircraft.
  - The anchor names no aircraft. Genie finds one, then the Cypher tool receives the original question text, because the supervisor's only output is a route. It had nothing to put in a `WHERE` clause, so it refused.
  - **This is the same shape as the Lab 6 memory defect, with a finding in place of a memory, and the Lab 6 fix would close both.**
  - **Moderate severity:** single-tool questions are unaffected, and those are what the labs demonstrate.
  - **It is the only failing pair of six in the shipped notebook's evaluation,** and it fails on the question the lab builds toward. **Decide whether the notebook ships ending on a visible 5 of 6.**
- **Re-capture the memory-off baseline.** The existing artifact is dated on four axes: a superseded `tools.py`, a pre-rebuild lakehouse, no Genie answer at all, and a maintenance-history answer taken before the backwards-arrow fix.
  - **The trap to avoid:** a memory-on run returning 23 maintenance events is the arrow fix landing, not memory improving recall. Whoever reads the comparison has to be told this inside the comparison.
  - Carry forward what is still valid: the 15.8 minute cold deploy, the interpretation notes, and the rule that expected-tools is a subset test and never an exact match, because the supervisor retries on an empty or failed tool.
- **One line prints an empty result to every participant.** Cell 19 of the deploy notebook prints the usage block, and the endpoint returns an empty one, so every participant sees `Usage: {}` immediately after a fifteen minute deploy. Drop the line, or say in the markdown above it that Model Serving returns no token counts here and latency is the only cost signal.
- **Exercise the extracted-entity routing path** against a graph loaded with extraction on. Blocked on a working LLM key.
- **Decide whether `eval/questions.jsonl` is still wanted.** It does not exist. The deploy notebook carries its question set inline.
- **Optional hybrid retrieval exercise** for participants who ran Lab 3 notebook 03. Cuttable.

### Lab 6

- **Test the batch seeding path.** The spike measured only single-message adds. The seed helper adds in batches. Still unmeasured.
- **Verify the two Foundation Model endpoints from this workspace** directly: the embedding endpoint returning 1024-dimension vectors and the supervisor endpoint answering. Written into three probe runs and never reached a successful execution.
- **Get the `MENTIONS` fix upstream** into `neo4j-labs`. Worth doing whether or not Lab 6 ships, and it has been carried unactioned across three passes.
- **An independent look at the memory results.** Every measurement was taken by the session that wrote the fixes, on one instance, against one Genie space, and the scores that matter are two-question samples.

### Loader hygiene

- **Drop `Reading` and `HAS_READING` from the loader.** Decided, not done. Nothing in the workshop queries them, and their presence means an admin debugging a participant issue works against a graph 155,520 nodes larger than any participant has. About 75 minutes, confined to three files and two documents.
- **Add `OperatingLimit` to the Lab 2 README node list.** The other half of a fix that half landed.
- **Load `OperatingLimit` in the Lab 2 validation harness.** It never did, which is how the limit collision reached Lab 3 unnoticed.

### Delivery

- **Full dry run of Labs 1 through 6** on a fresh Aura instance and a fresh workspace user, with timings recorded per lab and per demo.
- **Rerun Part B as an instructor demo** against the instructor's own instance.
- **Finish the Vocareum notebook list.** 13 entries at `lab/course.env:134-146`, all backed by files.
  - **The list is order sensitive.** The first entry is the student's landing page, so the smoke test stays first and anything new goes where a student reaches it, never appended.
  - **Confirm each `.py` helper uploads as a FILE and not a NOTEBOOK.** This behavior lives in a pinned external package, so an upload against an old lock ships the defect and hash-verifies cleanly. Whoever runs the final upload checks that first.
  - **Two checks before any helper joins the list:** a notebook the student opens must import it, and its first line must not be the Databricks notebook marker. Both current helpers pass, and the importing notebook does not have to live in the same lab.
- **Confirm nothing in Labs 5 or 6 reads a fallback instance.** The fallback is dropped, so a leftover override path is a credential nobody should have.

### Downstream content

- **The architecture diagram still shows the old MCP topology.** Both the root README and the Lab 4 README display it. The Excalidraw source sits beside the PNG, so this is an edit and not a redraw.
- **The Antora site stops at Lab 4, and the problem is absence rather than contradiction.** Navigation lists Lab 1 through Lab 4 and nothing after, and no Lab 5 or Lab 6 page exists. **The root README links to the published site on line 1** and the site publishes on every push to main, so this is the first thing a participant following that link sees.
- **The site and the slides carry pre-regeneration dataset numbers.** Eight files say "345,600+ hourly readings", 160 sensors, 80 systems, 20 aircraft. The committed CSVs hold **155,520 readings, 288 sensors, 144 systems, 36 aircraft**. The root README and the data generator guide already carry the right numbers, so the repository disagrees with itself across three surfaces.
- **The slides carry no Lab 5 or Lab 6 content.** The MCP framing in them is already corrected. What is missing is the two new labs.
- **Half-day split guidance:** paused and deleted Aura instances, endpoint survival between sessions, secret scope and Genie access survival, a between-sessions note, and a foundation-session ending that stands alone.

---

## 4. Major Decisions Made

**Scope and shape**

- **Lab 4 Part B is an instructor demo, and the per-participant MCP server is removed.** Participants watch. All Part B and MCP documentation stays, because the instructor needs the procedure and the no-code contrast is the point.
  - Runner-up: optional-but-buildable, which lost on setup cost against a benefit nobody was collecting.
- **Lab 5 is the single participant continuation from Part A.**
- **The Lab 5 catch-up cell is dropped, as too complex.** It required vendoring a non-serverless loader into a notebook cell and leaving three code paths that must produce one schema, all so a participant could skip the labs the workshop teaches.
  - **The cost is honest: somebody an hour behind at 2pm loses Labs 5 and 6.** The loader work built for it stays and is load-bearing elsewhere.
- **There is no broken-instance fallback, and that is deliberate.** No second read-only instance, no shared credentials, no override. A participant whose instance breaks makes a new Free instance and re-runs Lab 2 and Lab 3.
  - Runner-up: a second loaded instance handed out on request, which lost because it is an instance to keep alive, a credential to distribute, and a database a stray clean command can wipe mid-class.
  - **Consequence for instructors: a stalled Lab 2 has to be caught in Lab 2.**
- **Labs get written before anything that describes them.** Lab 5, then Lab 6, then the Vocareum notebook list, then the site and slides in one pass.

**Platform**

- **The class uses AuraDB Free.** The 200,000 node and 400,000 relationship caps apply, and every capacity number is measured against them.
- **LangGraph for Lab 5, direct bolt driver for the Neo4j tools.** No per-participant MCP server to host.
- **Model Serving deployment is required, not optional.** Service principal auth is the lesson that separates a notebook demo from a product.
- **Labs 5 and 6 share one endpoint per participant, redeployed by Lab 6.** Runner-up was two endpoints, which lost on the class-size quota.
  - **Consequence, load-bearing:** the memory-off baseline has to be a persisted artifact captured before Lab 6 redeploys over the endpoint. A passing eval run with no durable baseline leaves Lab 6 nothing to compare against.
- **Participants create their own secret scope in Lab 3.** Not provisioned, not shared. Removes the scope from the Vocareum hooks entirely, and no participant's password is visible to another.
- **Browser labs ship as notebooks.** Delivery format, not lesson content. The source markdown stays where it is.

**Data and modeling**

- **One embedding path, `databricks-bge-large-en`,** for the loader and for Lab 3 alike.
- **`databricks-meta-llama-3-3-70b-instruct` as the supervisor model,** closed on measured routing accuracy. The one-line swap to a Claude endpoint stays available and is not needed.
- **`graphrag_node` uses `VectorCypherRetriever`, not a plain vector retriever.** The Cypher tail after the vector hit is what makes it GraphRAG. The cost is that it sits close to `cypher_node`, which is why routing between that pair is measured as its own number.
- **Extraction writes `ExtractedLimit`; `OperatingLimit` means the 20 canonical CSV rows.** Runner-up was filtering on `limit_id` at every authoritative site, which left every workaround in place and added filters in three more.
- **The limit uniqueness constraint keys on `limit_id`, not `name`.** A uniqueness constraint is not enforced against nodes lacking the property, so `limit_id` binds the canonical rows and ignores everything else.
- **The memory library runs on the self-hosted bolt path, pinned to the fork wheel, adopting `Aircraft` only, writing in explicit mode.** Four conditions, each of which fails silently rather than loudly.
- **The Lab 4 Genie space attaches four tables:** `sensor_readings`, `aircraft`, `sensors`, `systems`.
- **Do not attach the two derived tables, and drop their Genie comments.** The evidence closed this one.
  - **The health-status column can never emit its documented `ANOMALY` value.** The rule fires on `p95 > avg + 2*stddev` while `p95` is approximately `avg + 1.645*stddev`, so the threshold is unreachable. Measured across all 288 sensors: **284 WARNING, 4 NORMAL, 0 ANOMALY.**
  - A table whose documented status value never occurs is a table Genie would answer wrongly from, so the comment that promises it goes. Both tables keep their SELECT grant and stay browsable.
  - Runner-up was fixing the rule so `ANOMALY` can fire, which lost because nothing attaches the table and the fix would change a published gold table for no consumer.

**How Cypher defects get fixed**

- **A relationship-direction error gets fixed with a schema bullet, never by making the traversal undirected.** Nine lines of schema text took the backwards-arrow defect from 5 zero-row runs of 5 to 0 of 5, with the regression suite still at 48 of 48.
  - Runner-up was dropping the arrow so the pattern matches either way, which lost twice over: it teaches participants a Cypher habit the workshop spends Lab 1 arguing against, and it hides the next direction defect instead of surfacing it.
  - **The generalization is the point.** The model anchors on the noun the question names and points every arrow away from it, so any relationship pointing toward a frequently-named node needs its own bullet.
- **A schema bullet must name the wrong road as well as the right one.** The components bullet does both: it says components reach maintenance events through `HAS_EVENT`, and it says there is no `AFFECTS_COMPONENT` and that writing one matches nothing. **The second half is what moved the number.**
- **Known tradeoff, taken with eyes open: every one of these fixes is prompt engineering against an observed failure, not a structural fix.**
  - **What it costs.** The schema block is static, hand-written, never read from the live graph, and sent on **every** Cypher call. Four defects each added prose and it now runs roughly 140 lines. Each new bullet competes for attention with the ones already there.
  - **What it buys.** No per-question routing logic and no code branching, and it behaves identically on the deployed agent because the schema travels with the model.
  - **The structural alternative, not built.** Validate generated Cypher against the real schema before running it and reject unknown labels, relationship types and properties outright. That catches the whole class at once and turns a silent zero-row answer into an error the repair path can act on. **It is the first thing to build if this agent outlives the workshop.**

---

## 5. Outstanding Questions

Each says what the decision is, what the evidence is, and what it blocks.

### Holding up delivery

- **Does AuraDB Free tolerate 59 indexes and 24 constraints on one instance?**
  - The combined Lab 3 plus Lab 6 total is measured. Only the tier is unknown, and no probe from inside the database can report it.
  - **Read the tier off the Aura console, or run the check against a fresh Free instance.** Cheap either way.
  - **Blocks Lab 6 entirely. It is the one remaining no-go.**
- **Regenerate the Antora site, or drop the link from README line 1?**
  - The site stops at Lab 4 and carries pre-regeneration dataset numbers, and it publishes on every push to main.
  - Writing two lab pages is content creation, not drift repair, which is why the audit left it.
  - **Nothing else in the downstream-content work can be scoped until this is answered.**
- **Do the Lab 6 instructor demos ship to participants, or stay instructor-only?**
  - `02_instructor_demos.ipynb` is not in the Vocareum notebook list and no document mentions it.
  - **If it ships,** it needs a list entry and a row in the Lab 6 README file table. **If it does not,** one sentence in that README stops the next reader asking.
  - The four demos in it are the Lab 6 payoff, so this is not a formatting question. Blocks the Vocareum notebook list.
- **Enrich the Genie comment strings, or stop restating what the pipeline already wrote?**
  - The pipeline writes a comment, then the Genie provisioning stage overwrites it with a thinner one. Nothing errors, and every provisioned workspace ships the thinner comment.
  - **Comments are what Genie reads to write SQL, so this lands on the participant path in Lab 4.**
- **Leave the configured warehouse name as Vocareum-only, or fall back to the sole warehouse in the workspace?**
  - `lab/course.env:154` names a warehouse that exists in no workspace this repository has been run against. On Vocareum the name is correct by construction. Everywhere else it is a name for nothing.
  - Provisioning fails loudly rather than silently, but its message says the warehouse-ensure step did not run, which is true on Vocareum and misleading anywhere else.
  - **Blocks nothing on the Vocareum path.** Blocks any admin or instructor provisioning into a workspace they did not build with the init script, which is how every measurement in this document was taken.

### Contained, or not holding anything up

- **The refusal string in `cypher_node` is wrong for write requests.** A declined write answers "The graph holds no sensor readings." Nothing writes and no data is wrong, but the wrong sentence reaches synthesis.
  - **A second refusal string gives the model two to choose between, which is exactly the shape that produced the first routing defect.** Recommendation is to leave it.
- **Drop the fifth table, `aircraft_fleet_metrics`?** Produced by no pipeline and referenced nowhere. It still holds 36 rows from the same stale generator run that forced the gold rebuild, and it was left in place because it was outside that authorization.
- **Both LLM keys are dead.** Anthropic credit too low, OpenAI 401. **Blocks only the LLM-extracted entities** and therefore the extraction-on routing exercise. Everything GraphRAG needs is already loaded without them.

### Answered, kept because the reasoning is reusable

- **Which instance does Lab 6 write to?** The development instance, as the secret scope already points, chosen so the shipped credential path gets exercised.
  - Runner-up was overriding the environment to write to the memory instance, which lost because the path a participant runs is the path worth testing.
  - **The cost is real:** adoption puts a label and a property on all 36 aircraft permanently, so **any Lab 5 measurement taken from here names the memory schema as part of the graph it measured.**
- **Do the notebooks hardcode the database name?** No longer. A fourth secret key carries it the same way the password travels, with a single fallback in one file for scopes written before the key existed.
  - **What is left:** an older scope reads back the fallback, which is right on Free and wrong on anything else. Instructors and admins on a non-Free instance write the key by hand once. **No lab content carries an override path**, per the no-fallback decision.
- **Does the memory library reject the counts query?** Its guard fires on inline subqueries only, so procedure calls were always fine and the earlier claim that it rejects all `CALL` is wrong. The query was rewritten as top-level unions and the library needs no change.

### A standing hazard, not a question

- **The loader pins its own `.env` at import time,** and that file points at the memory instance. **A bare `populate-aircraft-db clean` from any directory wipes it, regardless of what the caller thought they were pointed at.**

---

## 6. Phased Implementation Plan

Six phases. Each has an entry condition, a body, and a completion criterion that is a measurement rather than a claim.

### Phase 0: Prove the risky parts

**Status:** in progress. Loader work done. Memory spike done, verdict go with conditions.

| Item | Blocks |
|---|---|
| AuraDB Free index tolerance, Labs 3 and 6 on one Free instance | Phase 3 entirely |
| Model Serving endpoint quota at class size | Phase 2 completion, Phase 4 |
| Batch seeding path through the memory library | Phase 3 seeding step |
| Serverless install of the loader, or pick the fallback | nothing participant-facing |
| Drop `Reading` and `HAS_READING` from the loader | nothing, but it makes every later debug session honest |

**Completion:** the index tolerance question returns a yes, or Lab 6 is formally re-scoped.

**Still open, and now carrying more weight than it did.** Phase 3 was entered and built out with this question unanswered, on an explicit "proceed anyway". **A no no longer delays Lab 6, it invalidates four finished files.**

### Phase 1: Lab 5 core agent

**Status:** done except for one cosmetic item and one exercise blocked on a key.

- Routing re-measured against the current code: 48 of 48 across 9 groups.
- The backwards-arrow defect and the invented-relationship defect are both closed and measured.
- Remaining: exercise the extracted-entity path against an extraction-on graph, blocked on an LLM key. And the optional hybrid retrieval exercise, cuttable.

**Completion:** met. The anchor question is correct end to end, each routing case lands on the expected tool, and the close pair is reported as its own number, **against the code currently on disk**.

### Phase 2: Lab 5 ships, deployment included

**Entry:** Phase 1 re-run done. **Not done when the notebook is written. Done when a deployed endpoint answers as a service principal.**

**Status: completion criterion met.** The endpoint answers a Genie question through Model Serving with real numbers matching the rebuilt tables. The deploy notebook is written and ships executed.

Order inside the phase, because each step gates the next:

1. **Wrapper with resources declared at log time.** Done, and the lesson is that the Genie space alone is not enough. The warehouse and the gold tables have to be declared beside it.
2. **Secret scope read from the serving principal.** Done for all four keys. This was the silent failure the phase exists to catch.
3. **Log and deploy, and time the cold deploy.** Done, 15.8 minutes.
4. **Call the endpoint, one question per tool.** Done.
5. **Call the endpoint with the anchor question.** Done, and it is the one failing evaluation pair. See section 3.
6. **Second endpoint under a different user.** Open, gated on the quota check.
7. **Evaluation against the deployed endpoint.** Run and scored: routing 1.0 on all six pairs, correctness five of six.
   - **The baseline must be persisted as an artifact, not just run.** The two labs share one endpoint and Lab 6 redeploys over it, so a baseline that exists only as a passing run is gone by the time Lab 6 needs it.
   - **Re-capture is still owed,** because the existing artifact is dated on four axes. See section 3.
8. **Write the deploy notebook and finish the README.** Done.

**Completion:** a successful Genie call **through the endpoint**. Met. A successful deploy was never the criterion.

### Phase 3: Lab 6 memory

**Entry:** Phase 1 done, Phase 0 index question answered yes. **Entered early, on an explicit "proceed anyway", with the index question still open.**

**Status: built, run end to end, and its central claim holds.**

1. **Install and write conditions, each an explicit checklist item.** Done.
2. **Memory client and fleet adoption, with the dry run shown first.** Done.
3. **Recall and remember around the Lab 5 supervisor.** Done, and this is where all three memory defects lived.
4. **Seed script in a setup step, never a participant-run loop.** Done.
5. **Three hands-on demos, timed.** Done. Table in section 2.
6. **Four instructor demos as runnable cells,** each standalone because the shared names sit in one setup cell. Done.
7. **Memory off versus on harness.** Run, scoring `0/2 off, 2/2 on` under the strict scorer. **What is owed is re-capturing the comparison baseline on the current endpoint,** or narrowing the comparison to routing and saying so.
8. **README, carrying the pinned-version research answers.** Done.

**Completion:** the headline traversal returns a good answer, the comparison shows a measurable difference, and the demos fit inside 75 minutes measured rather than estimated. **All three are met on machine time.** What remains is the re-captured baseline and a dry run with a human.

### Phase 4: Delivery readiness

**Entry:** Phases 2 and 3 complete. **Owner: Ryan, personally, on a fresh Vocareum-shaped user and a fresh Aura instance.** Not a development workspace and not an account with leftover state.

- Full dry run, Labs 1 through 6.
- Model Serving exercised at class size, or the quota confirmed sufficient.
- Part B rerun as an instructor demo.
- Vocareum notebook list finished, helpers confirmed to upload as FILE and not NOTEBOOK.
- Timings recorded per lab and per demo.
- Confirm nothing in Labs 5 or 6 reads a fallback instance.

**Completion:** Ryan finishes the required path without intervening as the instructor, and the timings either match the day structure or the structure is corrected to match them.

### Phase 5: Downstream content and the half-day split

**Entry:** Phase 4 complete, because these surfaces describe the course and should be written once against what shipped.

- Lab 5 architecture diagram.
- Antora site, one pass, gated on the keep-or-drop decision in section 5.
- Slides, same pass.
- Half-day split guidance, written rather than coded.
- Dry run of the advanced half alone, from a deliberately cold state at least three days old.

**Completion:** somebody who did the foundation session, walked away for a week, and let their instance pause reaches the Lab 6 headline demo without instructor help.

### What to do next, in order

1. **Provision a fresh AuraDB Free instance and run the index tolerance check.** The only remaining no-go, and it touches nothing else, so it runs beside everything below.
2. **Re-capture the memory-off baseline** on the current endpoint, scoring it with the rules already agreed: expected tools as a subset test, row-count variance in the components question as known residual, and a 23-event maintenance answer as the arrow fix landing rather than memory improving recall.
3. **Decide the Lab 5 anchor question,** which is the same defect shape the Lab 6 fix already closed. It determines whether the shipped notebook ends on 5 of 6.
4. **Answer the four delivery questions in section 5.** Phase 4 hits all of them whether or not they are answered first.
5. **Push the `MENTIONS` fix upstream.** Carried unactioned across three passes, and worth doing whether or not Lab 6 ships.
6. **Loader hygiene and the quota check** in any gap. Each is under two hours and neither blocks anything.
