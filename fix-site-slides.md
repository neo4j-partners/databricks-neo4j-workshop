# Fix the Site and the Slides

What is wrong, what is missing, and what has to be added on the two surfaces that describe the course but were never updated with it: the Antora site in `site/` and the Marp decks in `slides/`.

**Source of truth:** the lab folders on disk, then `expand-v2.md` section 3 and section 5 question 9. `expand.md` is reasoning only. Where the site and a lab folder disagree, the lab folder is right.

**Why now:** `README.md` line 1 links the published site, and `.github/workflows/deploy-antora.yml` publishes on every push to `main`.

---

## Decisions Taken

Folded in from the review pass. Each is now an instruction to the plan below, not a question.

- **The site ships.** It is the only rendered surface a Vocareum student can reach.
- **The site becomes background and overview only.** Every step-by-step procedure moves into the lab notebooks. This is the largest decision here and it rewrites most of what follows. See "What the Notebook-First Split Changes" below.
- **Dataset counts come out.** No reading counts, no node counts, no per-label tables on the site or in the decks. They drift faster than anyone maintains them. Describe the dataset by shape, never by number.
- **Only workshop decks get published.** Everything else moves under an "Additional Background" grouping rather than being deleted.
- **Drop every mention of Aura Agents.** Not part of this workshop.
- **`02_gds_knn_aircraft.ipynb` is optional**, stated plainly, not gated on a tier claim.
- **Fix and keep:** the slide build script, the architecture diagram, the secret scope story, the tier claim.
- **Labs 5, 6 and Appendix A get pages.** That is the point of this document.

---

## What the Notebook-First Split Changes

The decision to move all procedure into notebooks is not a tidy-up. It deletes about 1,300 lines of site content and takes two live defects with it.

- **Retired outright:** `lab1-instructions.adoc` (135 lines), `lab2-instructions.adoc` (78), `lab3-instructions.adoc` (79), `lab4-instructions.adoc` (557). No `lab5-instructions.adoc` or `lab6-instructions.adoc` ever gets written.
- **Both live defects die with the pages that carried them.** Verified on disk: `Lab_1_Aura_Setup/01_aura_setup.ipynb` contains no backup-restore procedure, and `Lab_4_Compound_AI_Agents/04_genie_agent.ipynb` already carries the corrected Genie instruction block (`every 4 hours`, `CFM56-5B`, `LEAP-1A`, September 28). The notebooks were right the whole time; only the site copies were stale.
- **It matches a decision already made.** `expand-v2.md` section 4: "Browser labs ship as notebooks. Labs 1 and 4 join the notebook set, because a Vocareum student sees no rendered README." Both notebooks exist. The site split is the same reasoning applied one layer up.
- **The duplication direction reverses, which is the whole win.** Today the site is a stale copy of the lab markdown. After the split the notebook is the only copy of any procedure, and the site can never drift from it because it no longer states it.

### The site after the split

- **Keeps:** `index.adoc`, `databricks-platform.adoc`, `workshop-overview.adoc`, one concepts page per lab (`lab1.adoc` through `lab6.adoc`), an Appendix A page, and the slide pages.
- **Every concepts page ends the same way:** what this lab teaches, then "open notebook X in your workspace." No steps, no screenshots, no credentials.
- **`nav.adoc` collapses** from Lab-plus-Instructions-plus-Sample-Queries to one entry per lab.

### Three problems it creates

- **Screenshots have no home.** `site/modules/ROOT/images/` holds 14 procedural screenshots (`lab1-download-credentials.png`, `lab2-clone-menu.png`, `lab4-genie-connect-data.png`, and so on) that exist only for the instructions pages. Databricks notebook markdown cells cannot reliably render a repo-relative image path. Options: embed as base64 in the markdown cell, host them on the site and hot-link absolute URLs from the notebook, or drop them and write the steps in prose. **Hot-linking to the published site is the one that keeps both surfaces honest**, and it makes the site a dependency of the notebooks rather than a duplicate of them.

  **RESPONSE** :

- **The sample-queries pages are reference, not procedure.** `lab2-sample-queries.adoc` (140 lines) and `lab3-sample-queries.adoc` (353 lines) are copy-paste Cypher for the Neo4j Query workspace, which is a browser, not a notebook. They do not fit "move it to the notebook." **Recommend keeping them on the site** as reference pages under each lab.

  **RESPONSE** :

- **The lab-folder markdown becomes ambiguous.** `Lab_1_Aura_Setup/README.md`, `Lab_4_Compound_AI_Agents/PART_A.md` and `PART_B.md` currently hold the procedure that the notebooks also hold. After the split, are they the instructor's copy, or dead weight? **Recommend: they stay as the instructor and admin reference**, and the notebook is the participant's only path.

  **RESPONSE** :

---

## 0. Cross-Cutting

- **The site ships. DECIDED.** Regenerate it as the participant-facing surface.

  **Your question back was whether to drop the GitHub README and keep only the root README. There is only one README at the root, and it is the GitHub-rendered one, so I need to know which two things you are choosing between.** Best guess at what you meant: the root `README.md` and the site's `index.adoc` plus `workshop-overview.adoc` say the same things, and you want one of them to stop existing. If so, **recommend keeping a short root README** as the repository's front door for anyone browsing GitHub, cut to about 30 lines: what this is, who it is for, the link to the site, and the admin setup pointer. Everything participant-facing lives on the site.

  **RESPONSE** :

- **Dataset counts come out entirely. DECIDED.** Not corrected, removed. Affects `workshop-overview.adoc:24` and `:35`, `lab4.adoc:3`, `slides/platform-overview/01-workshop-over.md:89` and `:101`, `slides/docs/overview-and-genai-foundations.md:53` and `:63`, `slides/organize.md:63`, `slides/kg-construction/05-building-knowledge-graphs-slides.md:102`. Replace each with shape language: "hourly-scale telemetry over 90 days across a multi-model fleet."

  **One count is load-bearing and I would keep it: zero.** Lab 2 writes **no `Reading` nodes** to Neo4j. That is not a statistic that drifts, it is the dual-database argument itself.

  **RESPONSE** :

- **`site/nav.adoc` stops at Lab 4. DECIDED to fix.** Add Lab 5, Lab 6, Appendix A. Collapse the Instructions children per the notebook-first split. Add a nav group for slides, which today has none, so the three existing slide pages are unreachable.

- **The slide build script is broken. DECIDED to fix.** `slides/package.json` `build:html` targets `overview-databricks-neo4j/` and `databricks-in-depth/`; neither holds a `.md` any more. Rewrite it to iterate the real topic folders and output one attachment directory per folder. Until this is fixed nothing new can be published, so it goes first.

- **Split the decks into workshop and background. DECIDED, mechanism open.** Move the decks no session uses into `slides/background/<topic>/` and build them to `site/modules/ROOT/attachments/slides/background/<topic>/`.

  **On how to link it:** `site/antora.yml` takes `nav:` as a list, so a second file is possible, but the simpler answer is one nav file with a nested top-level entry:

  ```
  * Additional Background
  ** xref:slides/background-chunking.adoc[Chunking Strategies]
  ** xref:slides/background-entity-resolution.adoc[Entity Resolution]
  ```

  One file, no config change, and it renders as a collapsible group in the sidebar below the labs. **Recommend that.**

  **The split I would draw**, and this is the part I need you to confirm, because "part of the workshop" depends on which session is running:

  | Deck | Suggested |
  |---|---|
  | `platform-overview/` (4 decks) | Workshop |
  | `genai-foundations/` (3 decks) | Workshop |
  | `retrieval-patterns/` (4 decks) | Workshop, Lab 3 and Lab 5 both lean on Vector Cypher |
  | `agents/` (2 now, 5 after this plan) | Workshop |
  | `kg-construction/` (5 decks) | Background, except vectors and chunking |
  | `graph-ml/` (2 decks) | Background, unless Appendix A is being taught |
  | `governance/` (1 deck) | Background |

  **RESPONSE** :

- **The architecture diagram shows the retired topology. DECIDED to fix.** `images/lab-architecture-overview.svg` draws the Agent Bricks supervisor over the Neo4j MCP server. That is the Lab 4 Part B instructor demo now. `README.md:36`, `workshop-overview.adoc:53` and `lab4.adoc:117` all display it. Redraw as the Lab 5 topology and keep the MCP version as a second, clearly-labelled Part B diagram.

  **RESPONSE** : (confirm two diagrams, or one)

- **Nothing anywhere mentions the secret scope. DECIDED to fix.** Lab 3 notebook 01 creates `fleet-ops-<user-slug>` with four keys and Labs 3, 5 and 6 read it. The site still shows a plaintext `NEO4J_PASSWORD` in every notebook's config cell. On the site this becomes concept, not procedure: one paragraph on the Lab 3 page about why credentials get written once and read four times.

- **The tier claim is wrong in two directions. DECIDED to fix, but I need the right answer first.** See the question at the top of Lab 1.

---

## Lab 1: Neo4j Aura Setup

### Needs fixed

- **The tier claim, and your answer conflicts with the lab. BLOCKING.** You wrote "everything is Neo4j Aura free trial." `Lab_1_Aura_Setup/README.md` says the opposite in bold: take **AuraDB Free**, and *do not* take the 14-day free trial the console offers first, because that provisions AuraDB Professional and expires partway through the course.

  **These are different products and the difference reaches four other decisions:**

  | | AuraDB Free | 14-day Professional trial |
  |---|---|---|
  | Expires | Never | Day 14, mid-course for a multi-session format |
  | Node cap | 200,000 | None that binds |
  | GDS | Unavailable | Available |
  | Lab 2 `02_gds_knn_aircraft.ipynb` | Cannot run | Runs |
  | Appendix A | Cannot run | Runs |
  | Lab 6 index-cap risk (`expand-v2.md` q6) | Real, unmeasured | Gone |

  **If it is really the trial, the whole GDS problem disappears and so does the Lab 6 blocker.** If it is Free, the lab README is right and the site just needs correcting to match. Which is it?

  **RESPONSE** :

- **`lab1-instructions.adoc:37-47`, the dead backup-restore procedure. RESOLVED by the notebook-first split.** The page is retired; `01_aura_setup.ipynb` never had the procedure. No fix needed, just deletion.

- **`lab1.adoc:117` points Aura Agents at Lab 4. DECIDED: drop every mention of Aura Agents.** That is the whole of `lab1.adoc:115-120`. Nothing replaces it.

- **The signup guide is misquoted. DECIDED to fix**, contingent on the tier answer above, since the guide's own title is the thing in dispute.

### Missing

- **The node and relationship caps.** You asked whether this is needed. **Answer: only if the class is on AuraDB Free.** On Free it is worth one sentence so nobody panics in Lab 6. On the Professional trial it is noise and comes out. Blocked on the tier question.

  **RESPONSE** :

- **`Aura_Free_Trial.md` is not published.** You asked whether this is needed. **Answer: no, not under the notebook-first split.** It is a signup procedure, so it belongs in `01_aura_setup.ipynb` like everything else. Fold it into the notebook and delete the standalone file.

  **RESPONSE** :

### To add

- **One line on what the instance carries forward. DECIDED to add.** This instance is the one database every later lab reads and writes. There is no fallback instance, by decision, so a lost password means redoing Labs 2 and 3.

### Slides

- **`platform-overview/01-neo4j-aura-overview-slides.md` is not embedded. DECIDED to publish**, after checking it for the tier claim.

---

## Lab 2: Databricks ETL to Neo4j

### Needs fixed

- **The GDS notebook tier gate. DECIDED: make it optional**, stated plainly, without the AuraDB Professional claim. Exact wording depends on the tier answer.

- **`lab2-instructions.adoc:77` sends participants to Lab 4 for the supervisor. RESOLVED by the split**, page retired. The equivalent handoff on `lab2.adoc` still needs to point at Lab 3, then Lab 4 Part A, then Lab 5.

  **RESPONSE** :

- **`lab2-instructions.adoc:35-37` is a two-sentence stub for the longest lab. RESOLVED by the split**, page retired. The procedure is already in the notebook.

### Missing

- **What Lab 2 does *not* load.** Lab 2 writes zero `Reading` nodes to Neo4j; telemetry stays in Delta. Belongs on `lab2.adoc` as concept, and it is the one count worth keeping.

  **RESPONSE** :

- **The canonical `OperatingLimit` rows and the `HAS_LIMIT` edges.** The graph-shape block omits `HAS_LIMIT` entirely, and Lab 5's limit questions depend on it. Add the edge to the shape diagram, no counts.

  **RESPONSE** :

- **`CLEAR_DATABASE = True` as a contract, not a cure.** Today it appears only in troubleshooting. On the notebook side it belongs in the procedure; on the site side, one line on `lab2.adoc` about why the load is destructive by design.

  **RESPONSE** :

- **Sensor units.** `EGT` is `°C` and `N1Speed` is `% RPM`, matching the manual limit tables so `Sensor.unit = OperatingLimit.unit` joins on a plain string compare. This is why Lab 5's limit questions work at all. Concept, belongs on the page.

  **RESPONSE** :

### To add

- **A per-label expected-count table. DROPPED** by the no-counts decision. Verification belongs in the notebook, where it can be a query that prints live numbers instead of prose that goes stale.

- **A pointer to Appendix A.** Currently promises an Appendix A the site does not have. Fixed when the Appendix A page lands.

### Slides

- **`slides/aircraft/` holds the three-step ETL diagrams** (`step1-flat-tables-foreign-keys`, `step2-spark-connector-mapping`, `step3-connected-graph`). They are already in `site/modules/ROOT/images/` but no published deck teaches them. This is the clearest visual in the repository for what the Spark Connector does.

  **RESPONSE** : (which deck owns these three?)

- **`kg-construction/05-building-knowledge-graphs-slides.md:102`** carries the "20 aircraft" count. Covered by the no-counts sweep.

---

## Lab 3: Semantic Search

### Needs fixed

- **`lab3-instructions.adoc` teaches plaintext credentials, misdescribes the volume path, and hands off to the wrong lab. RESOLVED by the split**, page retired. All three are already right in the notebooks.

- **`lab3.adoc` has no `OperatingLimit` versus `ExtractedLimit` split.** `lab3-sample-queries.adoc:133-204` has it correct; the concepts page never introduces the distinction its own sample queries depend on. `OperatingLimit` means the canonical CSV rows, `ExtractedLimit` is what the LLM read out of the manual.

  **RESPONSE** :

### Missing

- **The secret scope as a teaching beat.** Four keys, scope name derived from `current_user()` because scope names are workspace-unique rather than per-user. This is the credential handoff the entire back half of the workshop rides on, and it is the kind of thing that belongs on a concepts page precisely because it is not a step.

  **RESPONSE** :

- **`NEO4J_DATABASE` as the fourth key.** Newly threaded through Labs 3, 5 and 6. Worth a line only if the tier answer means the value is ever anything but `neo4j`. See `expand-v2.md` question 5.

  **RESPONSE** :

- **The embedding model, named once.** `databricks-bge-large-en`, 1024 dimensions, the same endpoint the admin loader uses, which is why loader-written vectors and notebook-written query vectors are comparable at all.

  **RESPONSE** :

- **Index names and what breaks without them.** `maintenanceChunkEmbeddings` and the fulltext index. If the vector index is missing, Lab 5 silently drops `graphrag_node` from its routing list rather than failing loudly. That is a concept worth teaching, not a troubleshooting note.

  **RESPONSE** :

### To add

- **A "what Lab 3 leaves in your graph" close**, as shape rather than counts: documents, embedded chunks, two indexes, one secret scope. That list is exactly Lab 5's entry condition.

  **RESPONSE** :

### Slides

- **`retrieval-patterns/` is four decks, none published.** Recommended Workshop in the table above. Deck 03, Vector Cypher Retriever, is now load-bearing for Lab 3 and Lab 5 both.
- **`kg-construction/` is five decks, none published.** Recommended split: vectors and chunking to Workshop, schema design and entity resolution to Background.

  **RESPONSE** :

---

## Lab 4: Compound AI Agents

### Needs fixed

- **The stale Genie instruction block. RESOLVED by the split.** This was the worst defect in the document: a participant pastes it into their own Genie space and Genie then answers from it. `04_genie_agent.ipynb` is verified correct on disk. Retiring `lab4-instructions.adoc` removes the bad copy rather than fixing it.

- **`lab4.adoc:3` uses the stale reading count.** Covered by the no-counts sweep. The sentence motivating the whole lab has to be rewritten around shape: the full telemetry ledger never enters the graph, so GraphRAG cannot reach it.

- **`lab4.adoc:12` and `workshop-overview.adoc:51` still call the Agent Bricks supervisor the final architecture.** The instructions page was corrected to "instructor demo, your continuation is Lab 5"; the concepts page and the overview were not, and the instructions page is the one being deleted. **This is now the highest-priority remaining site edit**, because deleting the corrected page leaves only the uncorrected ones.

  **RESPONSE** :

### Missing

- **Which tables the Genie space attaches.** Four of the eight gold tables. Concept-level: Genie reads table and column comments, so scope is a modelling decision, not a permissions one.

  **RESPONSE** :

- **The Genie space ID.** Participants copy the 32-character ID out of the room URL because everyone titles their space differently, and Lab 5 and Lab 6 both read `GENIE_SPACE_ID`. **Procedure, so it lives in the notebook.** The site's job is one line saying Lab 4 produces a value Lab 5 consumes.

  **RESPONSE** :

- **The eight gold tables versus the four Genie sees.** Concept, belongs on the page.

  **RESPONSE** :

### To add

- **An explicit Part A / Part B split at the top of `lab4.adoc`.** You build Part A, you watch Part B.

- **A closing contrast for Part B:** no-code Agent Bricks over a governed MCP connection, versus the same routing written in code in Lab 5. That contrast is the only reason Part B survives as a demo.

  **RESPONSE** :

### Slides

- **`agents/02-power-of-graphrag-slides.md` needs reframing, not replacing.** Its last five sections present MCP plus Agent Bricks as *the* architecture. Retitle that run as the Part B demo and put the Lab 5 path beside it.

  **RESPONSE** :

- **`platform-overview/01-databricks-neo4j-integration-slides.md:300-313`** already has "Alternative Architecture: Agent as a Serving Endpoint." That is now the primary architecture. Promote it and retitle.

  **RESPONSE** :

- **`01-workshop-over.md:120-143`** already reads "used only in the Part B demo." Correct as-is, leave it.

---

## Lab 5: LangGraph Agent

**Nothing exists on either surface. This is the workshop's payoff lab.**

### Missing, site

- **`lab5.adoc`, one concepts page.** No instructions page, per the split. LangGraph state graph, the supervisor as a routing node, three tool nodes, and why a direct bolt driver rather than a per-participant MCP server.
- **A `nav.adoc` entry.**

### To add

- **The three tools, one line each.** `genie_node` for SQL over Delta telemetry, `cypher_node` for traversal over the participant's own Aura instance, `graphrag_node` for a `VectorCypherRetriever` over the Lab 3 manual chunks.

- **The routing lesson, which is the lab.** `cypher_node` and `graphrag_node` sit close together because the GraphRAG retriever has a Cypher tail. **Do the measured routing numbers go on the site, or stay in the lab README?** They are the strongest evidence in the repository, but they are also numbers, and the no-counts decision was about numbers drifting. Routing accuracy differs from dataset counts: it is a claim about the workshop's own quality, and it goes stale only when the prompt changes.

  **RESPONSE** :

- **The prompt is the artifact.** Two rules earned their place from measured failures. The refusal rule: never substitute a limit, threshold or ceiling for a measurement. The direction rule: an `AFFECTS_AIRCRAFT` arrow written backwards was fixed with nine lines of schema text rather than by dropping the arrow, because dropping it teaches a Cypher habit Lab 1 spends its time arguing against.

  **RESPONSE** :

- **The anchor question, end to end.** Genie names the engines with abnormal EGT, the graph returns their maintenance history including a bearing wear fault, the manual closes with the high-EGT procedure. One question, three tools, one answer. This is the demo the whole workshop builds toward and it belongs on the page.

- **Deployment as its own beat.** Logging to Unity Catalog, then serving as an endpoint that authenticates as a **service principal** rather than as the notebook user. That is the line between a notebook demo and a product, and `agenda.md` already treats it as its own topic.

- **The credential path.** Reads the Lab 3 scope. No plaintext password anywhere in Lab 5.

- **Degradation, stated.** A missing vector index drops `graphrag_node` from `available_tools` rather than raising at import.

- **A new architecture diagram.** Supervisor node, three tool nodes, two backends, one Model Serving endpoint. This is the one that replaces the MCP topology on `README.md:36`.

### Missing, slides

- **A LangGraph supervisor deck, `agents/03-langgraph-supervisor-slides.md`.** `agents/01-from-retrievers-to-agents-slides.md` teaches ReAct and tools generically and stops well before any of this.

- **A deployment deck, `agents/04-deploy-the-agent-slides.md`.** MLflow `ResponsesAgent`, Unity Catalog registration, Model Serving, service principal auth. `agenda.md` lists "Deploying the Agent" as its own topic and no deck backs it.

  **RESPONSE** : (one deck for both, or two?)

---

## Lab 6: Agent Memory

**Nothing exists on either surface. This is the closing argument of the workshop.**

### Missing, site

- **`lab6.adoc`, one concepts page**, plus a `nav.adoc` entry.

### To add

- **The thesis, one sentence.** Memory nodes and fleet nodes land in the same graph, so a single Cypher crosses from conversation history into maintenance history. That is the argument for memory in Neo4j rather than in a memory product.

- **The headline query.** Which aircraft several technicians independently asked about this week, and whether those are the ones actually failing. Neither graph answers it alone.

- **The graph shape.** A `recall` node before the supervisor, a `remember` node after it, three tools untouched.

- **Adopt `Aircraft`, and nothing else.** `adopt_existing_graph` overwrites the `type` property, and `System`, `Sensor` and `Component` all already use it. Adopting them corrupts the fleet graph silently. **This is a concept, not a step: it is what "the same node" costs.**

- **`extraction_mode="explicit"`** as the write mode.

- **The pinned install.** A fork wheel on the Unity Catalog volume, plus `httpx` alongside it because a wheel carries no extras. **Procedure, so it goes in the notebook.** The site gets one line that the library is pinned to a fork and why.

  **RESPONSE** :

- **One endpoint, redeployed.** Lab 6 redeploys the endpoint Lab 5 created rather than making a second one, which is why the memory-off baseline has to be captured before Lab 6 overwrites it.

- **Graph cost.** Only meaningful if the class is on Free. Blocked on the tier question.

- **Whether `02_instructor_demos.ipynb` ships.** `expand-v2.md` question 8, still open. If it ships it needs a `course.env` entry; if not, one sentence stops the next reader asking. **The four demos in it are the Lab 6 payoff**, and the memory deck below leans on demo 1.

  **RESPONSE** :

### Missing, slides

- **An agent memory deck, `agents/05-agent-memory-slides.md`.** `slides/images/graph_mem.jpg` already exists and no deck uses it. Slide-by-slide flow in the "Intro to Agent Memory" section below.

### Open, do not write around it

- **AuraDB Free index and constraint caps.** Lab 6 installs 33 indexes and 12 constraints on top of Lab 3's, untested on a fresh Free instance. If the combined total exceeds the cap, Lab 6 fails for the whole room at once. **Do not publish a Lab 6 page promising it works until this is measured, and it evaporates entirely if the class is on the Professional trial.**

  **RESPONSE** :

---

## Appendix A: GDS Graph Analytics

### Missing

- **Any site page at all.** Three notebook families on disk (Louvain community detection, PageRank plus Betweenness centrality, Node Similarity), plus `gds-exploring.md`, plus a nav entry. `lab2-instructions.adoc:33` already points at an Appendix A that does not exist.

### To add

- **The tier statement, up top.** GDS availability is the whole gate on this appendix, and what it says depends on the tier answer. On Free, the appendix is a trap without a warning; on the trial, it is simply part of the course.

  **RESPONSE** :

- **The dependency chain.** All of it needs Lab 2 notebook 01. Node Similarity additionally assumes `02_gds_knn_aircraft.ipynb` has run.

- **Is Appendix A taught, or is it take-home?** It changes whether `graph-ml/` is a Workshop deck or a Background one, and whether the appendix needs a slide slot in the agenda at all.

  **RESPONSE** :

### Slides

- **`graph-ml/03-graph-enrichment-slides.md` and `04-future-graph-enrichment-slides.md`** are the conceptual half of this appendix and are unpublished. They cover the GDS algorithms, the MLflow lift comparison, and the bidirectional data loop, which is the `agenda.md` topic "Graph Algorithms: From Connected Data to Analytical Features."

  **RESPONSE** :

---

## Governance, Not a Lab

- **`governance/auth-sync-slides.md`** covers four patterns for aligning Unity Catalog and Neo4j privileges. PDF only, no HTML, referenced by nothing. Recommended Background above. **Publish it under Additional Background, or drop it from `slides/` entirely?**

  **RESPONSE** :

---

## Suggested Flow: Intro to Agent Memory

The deck Lab 6 is missing, `agents/05-agent-memory-slides.md`. Nine slides, about 16 minutes. Full research and sources in `scratch-agent-memory-research.md`. Assumes GraphRAG and the Lab 5 supervisor are already taught, and lands on Lab 6's own demo.

### The one decision to make before writing a word

- **Neo4j ships two taxonomies and they conflict.** The 2025 developer blog, Alex Gilmore, borrows LangGraph's: short-term versus long-term, with long-term splitting into semantic, episodic and procedural. The 2026 Labs and hosted-service line uses short-term / long-term / **reasoning**. Neo4j's own glossary maps external "episodic" onto short-term, which inverts the LangGraph mapping.
- **Use the 2026 one.** `Lab_6_Agent_Memory/memory.py` and `02_instructor_demos.ipynb` are built on `short_term`, `long_term` and `reasoning`, so the deck has to match the code participants run. Name the conflict in one sentence, cite Gilmore as the cross-walk, move on.

  **RESPONSE** :

### The slides

1. **The agent you built is an amnesiac.** 1.0 min. Put the Lab 5 topology back up and ask what it knows at the start of question two. **Analogy:** a contractor whose memory is wiped every time they walk out of the hangar. **Quotable:** "Most agents you build today are amnesiacs."
2. **The fake fix, and where it runs out.** 1.5 min. Stuff the whole transcript back into the prompt. Fails three ways: cost, distraction, contradiction. **Quotable:** "Your 'memory' is just a pile of text chunks ranked by cosine similarity."
3. **Three layers, one graph.** 2.0 min. Short-term, long-term, reasoning. **Analogy:** the shift log, the permanent record, and the mechanic's own notebook of how they figured it out. Reasoning memory is the differentiator: traces, steps, tool calls, the "how did we get there" layer a vector store has nowhere to put.
4. **Why a graph, in one query.** 2.0 min. Walk one path on screen: tool call to entity to message to maintenance event. **Quotable, and this is the thesis line:** "Vector stores give you recall; the graph gives you understanding."
5. **Memory has to handle being wrong.** 2.0 min. Three live approaches side by side rather than one pitch: mem0 v3 went ADD-only and pushed contradiction into retrieval ranking after v2's LLM-decided ADD/UPDATE/DELETE proved fragile; Zep and Graphiti invalidate bi-temporally and never discard; Lab 6 supersedes with `SUPERSEDED_BY` and `valid_until`. **Framing:** State Clock versus Event Clock, what is true now versus what happened, when, and why. **Demo beat:** demo 1 from `02_instructor_demos.ipynb` — `active_only=True` returns engine one, `as_of=BEFORE_CORRECTION` returns engine two, and nothing was deleted.
6. **Hot path versus background write.** 1.5 min. Write during the turn and pay latency, or write after and accept staleness. **Hook for this audience:** the hosted service exposes queue lag as a freshness SLI, so staleness is a number, not a vibe.
7. **recall then act then remember.** 2.0 min. Lab 5's graph and Lab 6's graph side by side. Two nodes added, three tools untouched. **The point participants miss:** recall runs once per question, not once per tool call. Memory is routing context for the supervisor, not a fourth tool.
8. **The payoff. Never cut this one.** 3.0 min. Adoption in one line: stamping `:Entity` onto the Lab 2 `Aircraft` nodes means a remembered aircraft *is* the fleet node, so one traversal crosses both. Then the three queries in order. Fleet-only ranks N10011 **last of six**. Memory-only ranks it **joint first**. The joined query explains why. **Analogy:** the log is what got written down, the conversation is what the crew keeps worrying about, and the gap between them is where the next incident lives. **Optional 30 seconds:** an `APPLIES_TO`-scoped preference reaching any technician who touches that aircraft.
9. **Context graph, and where memory belongs.** 1.5 min. Databricks holds the telemetry, Neo4j holds the topology, the history, and now the memory. Memory belongs on the side where the joins are.

**RESPONSE** : (on the flow as a whole)

### Notes for whoever builds it

- **Cutting to 15 minutes:** fold slide 6 into one line on slide 7. Do not cut 8.
- **`slides/images/graph_mem.jpg` already exists** and no deck uses it. Slide 3 or 4.
- **Three different things share the "Neo4j memory" name.** The old `mcp-neo4j-memory` server under `neo4j-contrib`, the `neo4j-agent-memory` library Lab 6 pins, and the hosted service. Do not conflate them on a citation slide.
- **Comparison points worth naming once:** Zep/Graphiti, mem0, LangGraph checkpointers and store, Letta. Letta's operating-system hierarchy, core memory as RAM, recall as disk cache, archival as cold storage, is the cleanest borrowed analogy if slide 3 needs a second one.
- **Slide 8 depends on `02_instructor_demos.ipynb`**, so the open question about whether that notebook ships reaches this deck too.

---

## Suggested Order of Work

Revised for the notebook-first split. Steps 1 and 2 are deletions, which is why they come first: they remove about 1,300 lines that would otherwise have to be edited.

1. **Answer the tier question.** It gates Lab 1, Lab 2's optional notebook, Appendix A, and Lab 6's index-cap risk. Nothing below can be written correctly without it.
2. **Retire the four instructions pages** and collapse `nav.adoc`. Both live defects die here. Confirm each notebook carries what its page carried before deleting.
3. **Fix the slide build script**, so anything written afterward can actually be published.
4. **Sweep the dataset counts out** of the 8 files listed in section 0. Mechanical.
5. **Correct the Agent Bricks framing on `lab4.adoc` and `workshop-overview.adoc`**, which is now urgent because step 2 deletes the only page where it was already right.
6. **Redraw the architecture diagram.** Five pages display it.
7. **Write `lab5.adoc` and `lab6.adoc`**, plus the Appendix A page and their nav entries.
8. **Write the three new decks:** LangGraph supervisor, deployment, agent memory.
9. **Split and publish the remaining decks**, Workshop against Additional Background, and add the slides nav group that today does not exist.
