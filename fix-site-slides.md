# Fix the Site and the Slides

What is wrong, what is missing, and what has to be added on the two surfaces that describe the course but were never updated with it: the Antora site in `site/` and the Marp decks in `slides/`.

**Source of truth:** the lab folders on disk, then `expand-v3.md` section 3, and its outstanding question on whether the Antora site is regenerated or delinked. `expand.md` is reasoning only. Where the site and a lab folder disagree, the lab folder is right.

**Why now:** `README.md` line 1 links the published site, and `.github/workflows/deploy-antora.yml` publishes on every push to `main`.

**Status:** every decision is made. This is a work order, not a proposal. One empirical unknown remains, the AuraDB Free index cap, and it is step 0.

**Two other surfaces carry the same stale claims and are in scope for the sweeps only**, not for restructuring: `vocareum/docs/README.md` and `vocareum/SETUP_GUIDE.md`, which a Vocareum student can reach, and `workshop-setup/docs/MANUAL_SETUP.md`, which admins read. Neither gets a concepts page. Both get the tier fix. `worklog/` is a record and is left alone; `worklog/aura-node-budget.md:79` states the tier question this document closes, which is worth knowing but not worth editing.

**Every file and line number below was re-verified against the repo on 2026-08-08.** Where an earlier draft named a count or a file list from memory, the verified list replaces it.

---

## Decisions Taken

**Every open item in this document is now closed.** Nothing below is a question. The `**DECIDED:**` markers throughout carry the reasoning for each; this list is the summary.

### Shape of the work

- **The site ships.** It is the only rendered surface a Vocareum student can reach.
- **The site becomes background and overview only.** Every step-by-step procedure moves into the lab notebooks. This is the largest decision here and it rewrites most of what follows. See "What the Notebook-First Split Changes" below.
- **Labs 5, 6 and Appendix A get pages.** That is the point of this document.
- **A short root `README.md` survives**, cut to about 30 lines of pointers. It carries no content of its own, so it cannot go stale.

### What comes out

- **Dataset counts come out.** No reading counts, no node counts, no per-label tables on the site or in the decks. **Two numbers survive** and both are structural rather than statistical: **zero** `Reading` nodes in Neo4j, and the 200,000 node / 400,000 relationship caps.
- **Drop every mention of Aura Agents.** Not part of this workshop.
- **The four participant-facing lab READMEs go away**, along with `PART_A.md`. Labs 5 and 6 keep their READMEs as module documentation, because those folders ship Python. `PART_B.md` stays as the instructor's demo script.
- **Three build-output slide folders get deleted.** `aircraft/` and `databricks-in-depth/` stay: they hold diagram sources, not decks.

### What gets fixed

- **AuraDB Free is the tier. Everywhere, no exceptions.** Not the 14-day trial, not Professional. Every surface uses those three words.
- **`02_gds_knn_aircraft.ipynb` is optional and unrunnable in class**, because GDS is not on Free. State it as a skip, not a prerequisite.
- **Screenshots are `raw.githubusercontent.com` URLs on `main`**, the pattern `04_genie_agent.ipynb` already uses. Concept diagrams stay on the site; only the 15 PNGs move.
- **Two architecture diagrams, not one.** Lab 5 topology becomes the default; the MCP drawing is retitled as the Part B demo and appears only on `lab4.adoc`. **One file per drawing first**, since both currently exist in two directories with four consumers split between them.
- **CI builds the decks.** `deploy-antora.yml` gets a marp step. Today it never invokes marp, so every published deck is hand-committed HTML, and the committed HTML is already stale.
- **Fix and keep:** the slide build script, the secret scope story, `agents/02-power-of-graphrag-slides.md` reframed rather than rewritten.

### What gets built

- **Only workshop decks get published.** Everything else moves under an "Additional Background" grouping rather than being deleted. Governance goes there; `graph-ml/` does not.
- **Two new agent decks, not one.** LangGraph supervisor and deployment stay separate, because deployment is what gets cut when the day runs late.
- **Appendix A is take-home**, since nobody in the room can run GDS on Free. Its `graph-ml/` decks are still taught, because the argument survives without anyone running a `gds.` call.
- **`02_instructor_demos.ipynb` ships, instructor-only.** Two slides of the memory deck run out of it. Needs a `course.env` entry.
- **The agent memory deck uses the 2026 taxonomy**, short-term / long-term / reasoning, because that is what `memory.py` implements.
- **Routing accuracy numbers go on the site**, stated with the date measured and the prompt version.

### The one thing not decided by anyone here

- **The AuraDB Free index-cap check is unrun**, and it is step 0. It can still flip Lab 6 to no-go, and it is the only item that can invalidate work already written. **The script that was supposed to run it does not exist**, so step 0 is write-then-run. Only the run needs a fresh Free instance.

---

## What the Notebook-First Split Changes

The decision to move all procedure into notebooks is not a tidy-up. It deletes about 1,300 lines of site content and takes two live defects with it.

- **Retired outright:** `lab1-instructions.adoc` (135 lines), `lab2-instructions.adoc` (78), `lab3-instructions.adoc` (79), `lab4-instructions.adoc` (557). No `lab5-instructions.adoc` or `lab6-instructions.adoc` ever gets written.
- **Both live defects die with the pages that carried them.** Verified on disk: `Lab_1_Aura_Setup/01_aura_setup.ipynb` contains no backup-restore procedure, and `Lab_4_Compound_AI_Agents/04_genie_agent.ipynb` already carries the corrected Genie instruction block (`every 4 hours`, `CFM56-5B`, `LEAP-1A`, September 28). The notebooks were right the whole time; only the site copies were stale.
- **It matches a decision already made.** `expand-v3.md` section 4: "Browser labs ship as notebooks. Labs 1 and 4 join the notebook set, because a Vocareum student sees no rendered README." Both notebooks exist. The site split is the same reasoning applied one layer up.
- **The duplication direction reverses, which is the whole win.** Today the site is a stale copy of the lab markdown. After the split the notebook is the only copy of any procedure, and the site can never drift from it because it no longer states it.

### The site after the split

- **Keeps:** `index.adoc`, `databricks-platform.adoc`, `workshop-overview.adoc`, one concepts page per lab (`lab1.adoc` through `lab6.adoc`), an Appendix A page, and the slide pages.
- **Every concepts page ends the same way:** what this lab teaches, then "open notebook X in your workspace." No steps, no screenshots, no credentials.
- **`nav.adoc` collapses** from Lab-plus-Instructions-plus-Sample-Queries to one entry per lab.

### Three problems it creates

- **Screenshots have no home. RESOLVED, but not the way this document first said.** An earlier draft of this item called for moving the screenshots *out* to per-lab `images/` folders. **That direction is reversed. `site/modules/ROOT/images/` is the single source and nothing moves out of it.** Ryan decided this on 2026-08-08, after a separate session had already implemented it in the working tree and recorded it in `svg-png.md`.

  **Why the site directory wins.** It is the only location that keeps the *published site* self-contained. An Antora page uses `image::name.png[]` and resolves it locally, with no dependency on `raw.githubusercontent.com` staying reachable, staying public, or resolving at all. Notebooks already reach the network for everything else they do, so making the notebook the side that hot-links costs nothing it was not already paying.

  **Notebooks reference it by absolute raw URL**, the pattern `Lab_4_Compound_AI_Agents/04_genie_agent.ipynb` already ships:

  ```
  ![Configure Genie](https://raw.githubusercontent.com/neo4j-partners/databricks-neo4j-workshop/main/site/modules/ROOT/images/lab4-configure-genie.png)
  ```

  So the convention has exactly two halves, and both point at one directory:

  | Consumer | How it references an image |
  |---|---|
  | Antora page under `site/` | `image::lab2-clone-menu.png[]`, resolved locally |
  | Lab notebook | `raw.githubusercontent.com/.../main/site/modules/ROOT/images/lab2-clone-menu.png` |

  **`site/modules/ROOT/images/` holds 24 files.** Nothing in it moves. Two things leave and two arrive:

  | Kind | Count | Do |
  |---|---|---|
  | Screenshots | 15 `.png`, `lab1-*`, `lab2-*`, `lab4-*` | **Stay.** Both consumers point here |
  | Concept diagrams | 7 `.svg` | **Stay.** They belong to concepts pages that survive the split |
  | Duplicated diagrams | 2 `.svg`, `lab-architecture-overview`, `dual-database-architecture` | **Delete the site copy.** See the architecture-diagram item below. Step 7 owns this |
  | `lab1-backup-restore.png` | 1 `.png` | **Delete.** Its only consumer was `lab1-instructions.adoc:37-47`, the dead backup-restore procedure, and `01_aura_setup.ipynb` never had that procedure |
  | `Lab_1_Aura_Setup/images/FREE_*.png` | 2 `.png` | **Move in.** They are the only screenshots living outside the single source, and they are the AuraDB Free screenshots the tier decision makes load-bearing |

  **Two things the notebook half costs, both acceptable, neither zero:**

  - **It only works on a public repo.** `raw.githubusercontent.com` on `main` needs no auth today. If this repo ever goes private, every image in every notebook breaks at once. The site half keeps working, which is the point of choosing this direction.
  - **It pins to `main`, so images update the moment they merge.** A participant on an older notebook copy sees the newest screenshot. For screenshots that is usually right, occasionally confusing.

  **DECIDED: this is the standard**, said once in the repository so the next person adding a screenshot does not invent a third pattern.

- **The sample-queries pages are reference, not procedure.** `lab2-sample-queries.adoc` (140 lines) and `lab3-sample-queries.adoc` (353 lines) are copy-paste Cypher for the Neo4j Query workspace, which is a browser, not a notebook. They do not fit "move it to the notebook."

  **DECIDED:** Keep both on the site. The target is the Neo4j Query browser, so a notebook is the wrong home, and a participant with Cypher open in one tab wants the queries in another. They are the one thing the split does not swallow.

- **The lab-folder markdown becomes ambiguous.** `Lab_1_Aura_Setup/README.md`, `Lab_4_Compound_AI_Agents/PART_A.md` and `PART_B.md` currently hold the procedure that the notebooks also hold. After the split, are they the instructor's copy, or dead weight?

  **DECIDED:** Split the difference, because these two files are not alike. **`PART_B.md` stays** as the instructor's build script for the demo, since no participant notebook can carry it and somebody has to build the thing on stage. **`PART_A.md` goes**, because `04_genie_agent.ipynb` already carries it and carries it better. Same rule as the READMEs: keep it only if a participant notebook cannot hold it.

### Do the per-lab READMEs survive? Answer: mostly no.

There are six, and they total 1,049 lines.

| File | Lines | What it holds | Verdict |
|---|---|---|---|
| `Lab_1_Aura_Setup/README.md` | 112 | Signup steps, tier warning | **Delete.** Into `01_aura_setup.ipynb` |
| `Lab_2_Databricks_ETL_Neo4j/README.md` | 127 | Notebook list, graph shape | **Delete.** Shape to `lab2.adoc`, rest to the notebook |
| `Lab_3_Semantic_Search/README.md` | 108 | Secret-scope key table | **Delete.** Key table into notebook 01, which writes them |
| `Lab_4_Compound_AI_Agents/README.md` | 69 | Part A / Part B framing | **Delete.** `04_genie_agent.ipynb` already opens with a better version |
| `Lab_5_LangGraph_Agent/README.md` | 250 | Module reference for `tools.py`, `agent.py` | **Keep, shrink.** See below |
| `Lab_6_Agent_Memory/README.md` | 383 | Module reference for `memory.py`, demo notes | **Keep, shrink.** See below |

**The rule that separates them: does a Python module live in this folder?** Labs 1 through 4 are notebooks and data. Labs 5 and 6 ship `tools.py`, `agent.py` and `memory.py`, which are source files someone will open in an editor rather than run in a cell. That folder needs a README the same way any Python package does, and it is a **developer** README, not a participant one.

**So the two survivors change job.** They stop being lab instructions, which the notebooks now carry, and become module documentation: what each function does, what imports across lab folders (`memory.py` reaches into both `Lab_3_Semantic_Search/data_utils.py` and `Lab_5_LangGraph_Agent/tools.py`, which is why the three folders must stay siblings), and what breaks if you move things. That should cut 250 and 383 lines to about 80 each.

**The four deletions are the point of the notebook-first split**, not a side effect. A Vocareum student never sees a rendered README, so today those 416 lines are written for an audience that cannot read them while duplicating what the notebooks say.

  **DECIDED:** The table as drawn. The one thing to check before deleting each of the four: does the README hold anything the notebook does not? Lab 2's graph-shape block and Lab 3's secret-key table are the two likely finds, and both have a named destination above.

---

## 0. Cross-Cutting

- **The site ships. DECIDED.** Regenerate it as the participant-facing surface.

  **The root `README.md` and the site's `index.adoc` plus `workshop-overview.adoc` say the same things today, at 12.4K of duplication.** The site wins that overlap.

  **DECIDED:** Cut `README.md` from 12.4K to about 30 lines and keep it. It is the first thing anyone sees on GitHub and an empty front door is worse than a thin one. It carries no content of its own after the cut, only pointers, so it cannot go stale. Everything it currently duplicates moves to `index.adoc`.

- **Dataset counts come out entirely. DECIDED.** Not corrected, removed. Replace each with shape language: "hourly-scale telemetry over 90 days across a multi-model fleet."

  **The drift already happened, which settles the argument.** The site and decks say `345,600+` readings. `README.md:57` says "roughly 155K". Those are the same dataset described two ways that differ by more than 2x, and nobody noticed. No number in this class of fact is worth maintaining.

  **The verified sweep list. Nine files, and the earlier list missed three of them plus every table row:**

  | File | Lines | Holds |
  |---|---|---|
  | `site/modules/ROOT/pages/workshop-overview.adoc` | 24, 35 | `345,600+`, plus `sensors` (160) / `systems` (80) / `aircraft` (20) inline |
  | `site/modules/ROOT/pages/lab4.adoc` | 3 | `345,600+` in the sentence motivating the whole lab |
  | `slides/platform-overview/01-workshop-over.md` | **85-91**, 101 | The full per-label table, not just the readings row |
  | `slides/docs/overview-and-genai-foundations.md` | **49-55**, 63 | The same table, duplicated |
  | `slides/organize.md` | 63 | "A fleet of 20 aircraft" |
  | `slides/kg-construction/05-building-knowledge-graphs-slides.md` | 102 | "20 aircraft across 4 operators" |
  | `README.md` | **57** | "roughly 155K readings". Dies anyway with the 30-line cut, but do not leave it for that |

  The two table blocks are the bulk of the work and were absent from the earlier list, which named only the `Sensor Readings` row in each. **The per-label table is exactly what the no-counts decision deletes**, so all seven rows go, not one.

  **One count is load-bearing and it stays: zero.** Lab 2 writes **no `Reading` nodes** to Neo4j. That is not a statistic that drifts, it is the dual-database argument itself.

  **DECIDED:** Keep zero, drop every other number. The test for any count that survives: would changing the dataset change it? A reading count moves the moment the generator is re-run. "Zero `Reading` nodes in Neo4j" and "200,000 node cap" do not move at all, because one is a design decision and the other is a product limit.

- **`site/nav.adoc` stops at Lab 4. DECIDED to fix.** Add Lab 5, Lab 6, Appendix A. Collapse the Instructions children per the notebook-first split. Add a nav group for slides.

  **Three slide pages exist and are unreachable**, in `site/modules/ROOT/pages/slides/`: `slides-overview.adoc`, `slides-intro-databricks-neo4j.adoc`, `slides-power-of-graphrag.adoc`. Each is a four-line `iframe` wrapper around a built HTML file under `_attachments/`. No `nav.adoc` line points at any of them, so nothing on the published site can reach them. **The wrapper pattern is already established**, which makes the remaining slide pages a copy-and-retarget job rather than authoring. Adding the nav group still waits for step 10, when the full deck split decides what goes in it.

- **The slide build script is broken in three ways, not one. DECIDED to fix all three.**

  1. **Its inputs are outputs.** `slides/package.json` `build:html` targets `overview-databricks-neo4j/` and `databricks-in-depth/`; neither holds a `.md` any more. Rewrite it to iterate the real topic folders and output one attachment directory per folder.
  2. **It hardcodes one machine's interpreter.** The script calls `/opt/homebrew/opt/node@22/bin/node` twice by absolute path. That works on one Mac and fails everywhere else, CI included. Use the `marp` bin directly and let `npm` resolve node.
  3. **Nothing ever runs it.** `.github/workflows/deploy-antora.yml` runs `npm run build` in `site/`, and `site/package.json` `build` is bare `antora antora-playbook.yml`. Marp is never invoked in CI. **Decks reach the published site only as pre-built HTML committed by hand into `site/modules/ROOT/attachments/`.**

  **DECIDED: add a marp step to `deploy-antora.yml` ahead of the Antora build**, rather than keeping committed build output. Committed HTML is what produced the current mess: the attachments directory holds `databricks-in-depth/01-intro-databricks-neo4j-slides.html` and `databricks-in-depth/02-power-of-graphrag-slides.html` and `overview/01-databricks-neo4j-integration-slides.html`, whose sources now live in `slides/platform-overview/` and `slides/agents/`. The folder names describe where those decks used to be. **Clear `site/modules/ROOT/attachments/slides/` and regenerate**, or the site keeps serving decks built from folders step 3 deletes.

  Fixing item 1 alone publishes nothing. All three, or the step does not do what it says.

- **Split the decks into workshop and background. DECIDED, mechanism open.** Move the decks no session uses into `slides/background/<topic>/` and build them to `site/modules/ROOT/attachments/slides/background/<topic>/`.

  **On how to link it:** `site/antora.yml` takes `nav:` as a list, so a second file is possible, but the simpler answer is one nav file with a nested top-level entry:

  ```
  * Additional Background
  ** xref:slides/background-chunking.adoc[Chunking Strategies]
  ** xref:slides/background-entity-resolution.adoc[Entity Resolution]
  ```

  One file, no config change, and it renders as a collapsible group in the sidebar below the labs. **DECIDED: that one.**

  **What the split is, plainly.** `slides/` holds **24 decks across 8 folders**. A one-day workshop presents maybe 8 of them. The other 16 are good material written for other talks, and right now all 24 sit in one flat pile with nothing marking which is which. Nothing gets deleted. It is a filing decision.

  It changes three things:

  - **Which folder each deck sits in** on disk, `slides/<topic>/` or `slides/background/<topic>/`
  - **Where it appears in the site sidebar**, under its lab or under a collapsed "Additional Background" group at the bottom
  - **Whether it needs a slot in `worklog/agenda.md`.** A workshop deck costs minutes in a fixed day; a background deck costs nothing

  **The split, DECIDED:**

  | Folder | Decks | Suggested | Why |
  |---|---|---|---|
  | `platform-overview/` | 4 | Workshop | Opens the day |
  | `genai-foundations/` | 3 | Workshop | Sets up Lab 3 |
  | `retrieval-patterns/` | 4 | Workshop | Lab 3 and Lab 5 both lean on Vector Cypher |
  | `agents/` | 2 now, 5 after this plan | Workshop | Labs 4, 5, 6 |
  | `kg-construction/` | 5 | Background, except chunking and vectors | The extraction material is a different course |
  | `graph-ml/` | 2 | Background, unless Appendix A is taught | Depends on the Appendix A question below |
  | `governance/` | 1 | Background | Nothing in the labs touches it |
  | `docs/` | 3 | Neither, it is not a deck folder | Looks like scratch. Confirm before it gets built |

  **Five folders hold no `.md` at all, and they are not all the same thing.** Correcting an earlier line here that called them all deletable:

  | Folder | Holds | Do |
  |---|---|---|
  | `aircraft/` | 6 `.excalidraw` + `.svg` diagram pairs, including the three ETL steps | **Keep.** It is the diagram source, not a deck |
  | `databricks-in-depth/` | 3 diagram pairs and one built PDF | **Keep the diagrams**, delete the PDF |
  | `overview-databricks-neo4j/` | One built PDF | **Delete.** Build output |
  | `overview-knowledge-graph/` | 10 built HTML files | **Delete.** Build output from a retired build |
  | `overview-retrievers/` | Nothing | **Delete** |

  **The two the build script points at are both build-output folders**, which is exactly why it fails: the script's inputs were outputs all along. Deleting them first makes the rewrite obvious.

  **DECIDED:** The folder table above, and Workshop / Background exactly as drawn. If a session is dropped, the safe direction is Workshop to Background, never delete.

- **The architecture diagram shows the retired topology. DECIDED to fix.** `images/lab-architecture-overview.svg` draws the Agent Bricks supervisor over the Neo4j MCP server. That is the Lab 4 Part B instructor demo now.

  **DECIDED:** Two diagrams. One cannot carry both, because the whole Lab 4 point is that Part B and Lab 5 are the same architecture reached two ways, and a merged diagram makes them look like one system. **Lab 5 topology becomes the default**, shown on `README.md`, `workshop-overview.adoc` and `lab5.adoc`. The existing MCP drawing keeps its file, gets retitled "Part B: Instructor Demo," and appears only on `lab4.adoc`.

  **The drawing exists three times in two directories, and every consumer picks a different one.** This has to be collapsed first or the redraw has to be done twice:

  | Consumer | Line | References |
  |---|---|---|
  | `README.md` | 36 | `images/lab-architecture-overview.png` |
  | `Lab_4_Compound_AI_Agents/04_genie_agent.ipynb` | 12 | the raw URL to `images/lab-architecture-overview.png` |
  | `site/modules/ROOT/pages/workshop-overview.adoc` | 53 | `lab-architecture-overview.svg`, resolved from `site/modules/ROOT/images/` |
  | `site/modules/ROOT/pages/lab4.adoc` | 117 | the same site-local `.svg` |

  `dual-database-architecture` has the identical problem: `README.md:45` and `Lab_4_Compound_AI_Agents/README.md:13` take the root PNG, `workshop-overview.adoc:31` and `lab1.adoc:90` take the site SVG.

  **DECIDED: delete both `.svg` copies under `site/modules/ROOT/images/` and have the site reference the root `images/` copies.** `images/` is where the `.excalidraw` sources live, so it is the only place a redraw can start. One source, one export, four consumers. Do this before step 7 or the redraw ships to half the pages.

- **Nothing anywhere mentions the secret scope. DECIDED to fix.** Lab 3 notebook 01 creates `fleet-ops-<user-slug>` with four keys and Labs 3, 5 and 6 read it. The site still shows a plaintext `NEO4J_PASSWORD` in every notebook's config cell. On the site this becomes concept, not procedure: one paragraph on the Lab 3 page about why credentials get written once and read four times.

- **The tier claim. DECIDED: AuraDB Free, everywhere, no exceptions.** Not the 14-day trial, not Professional. Every surface says the same three words. Full sweep list at the top of Lab 1.

---

## Lab 1: Neo4j Aura Setup

### Needs fixed

- **The tier. DECIDED: AuraDB Free. Not the 14-day trial. Not Professional.** `Lab_1_Aura_Setup/README.md` was right all along and everything else conforms to it. This closes `expand.md` Open Decision 6 on every surface, not just in the plan.

  **Consequences that follow, and they are not optional:**

  | Follows from Free | What it means |
  |---|---|
  | 200,000 node / 400,000 relationship caps | Real. Worth one sentence in Lab 1 so nobody panics later |
  | GDS unavailable | Lab 2 `02_gds_knn_aircraft.ipynb` is optional and skippable. Appendix A likewise |
  | Never expires | No mid-course expiry, so a multi-session format is safe |
  | Lab 6 index cap | Still unmeasured. The AuraDB Free index and constraint question in `expand-v3.md` section 5 stays open and stays the one no-go |

  **Every place the wrong tier is still written down. Verified by grep, and it is sixteen lines across ten files, not four.** The earlier four-row list caught the site and missed the notebooks entirely.

  **Dies with step 1, no edit needed:**

  | File | Line | Says |
  |---|---|---|
  | `site/modules/ROOT/pages/lab1-instructions.adoc` | 13, 15, 16 | "Neo4j Aura free trial", "14-day free trial" |
  | `site/modules/ROOT/pages/lab2-instructions.adoc` | 31 | "requires AuraDB Professional" |

  **Live and needs a real edit:**

  | File | Line | Says | Fix |
  |---|---|---|---|
  | `Lab_1_Aura_Setup/slides/07-lab-steps-1.md` | 6, 12 | "free trial signup process", "free trial instance" | Both become "AuraDB Free" |
  | `Lab_1_Aura_Setup/Aura_Free_Trial.md` | filename | Body is correct. The **name** reads as the thing it warns against | Folded into the notebook and deleted |
  | `README.md` | 96, 158 | "Create an Aura free trial", "Neo4j Aura free trial account" | Rewrite in the 30-line cut |
  | `vocareum/docs/README.md` | 74 | "your own Neo4j Aura free trial instance" | Edit in place |
  | `workshop-setup/docs/MANUAL_SETUP.md` | 118 | "Graph Data Science needs Aura Professional" | Reframe as a skip, not a prerequisite |

  **The Appendix A notebooks are the largest miss, and they carry the exact framing this decision rejects.** Every one of them states Professional as a **prerequisite to go acquire**, which is what `lab2-instructions.adoc:31` was condemned for:

  | File | Line | Says |
  |---|---|---|
  | `Appendix_A_GDS_Graph_Analytics/community_detection/02_gds_louvain_maintenance.ipynb` | 12, 32, 194 | "Requires AuraDB Professional", "AuraDB Professional or higher" |
  | `Appendix_A_GDS_Graph_Analytics/centrality/04_gds_pagerank_airports.ipynb` | 12, 32 | same |
  | `Appendix_A_GDS_Graph_Analytics/similarity/05_gds_node_similarity_aircraft.ipynb` | 12, 37 | same |
  | `Appendix_A_GDS_Graph_Analytics/gds-exploring.md` | 25 | "AuraDB Professional ships with GDS included" |

  This matters beyond wording. **The Appendix A page decided below opens with "nobody in the room can run this," and the notebooks it points at open with "go get Professional."** Those two cannot both ship. All four files take the same reframing `02_gds_knn_aircraft.ipynb:7` already has: skip it, here is why, everything else runs on Free.

  **Already correct, leave alone:** `Lab_1_Aura_Setup/README.md:14`, `Lab_1_Aura_Setup/Aura_Free_Trial.md:15,37`, `Lab_1_Aura_Setup/01_aura_setup.ipynb:61,99`, `Lab_2_Databricks_ETL_Neo4j/02_gds_knn_aircraft.ipynb:7,38`. These say AuraDB Free and warn off the trial button by name. They are the model the other ten conform to.

  **`Aura_Free_Trial.md` should be renamed or folded in.** A participant who sees the filename and skips the body clicks exactly the wrong button. **DECIDED: fold the whole file into `01_aura_setup.ipynb` and delete it**, which the notebook-first split calls for anyway.

- **`lab1-instructions.adoc:37-47`, the dead backup-restore procedure. RESOLVED by the notebook-first split.** The page is retired; `01_aura_setup.ipynb` never had the procedure. No fix needed, just deletion.

- **`lab1.adoc:117` points Aura Agents at Lab 4. DECIDED: drop every mention of Aura Agents.** Nothing replaces it.

  **It is two edits, not one block.** `lab1.adoc:114-117` is the titled section, and `lab1.adoc:12` also lists Aura Agents in the sentence describing what Neo4j Aura is: "with built-in vector search, Graph Data Science, and Aura Agents." Deleting only the section leaves the feature named on the page, and line 12 additionally advertises Graph Data Science on the tier that does not have it. **Rewrite line 12 and delete 114-117.**

- **The signup guide is misquoted. DECIDED to fix.** The guide's body already points at AuraDB Free and warns off the trial button by name. The site paraphrased it backwards. Fixed by deleting the site copy and folding the guide into the notebook.

### Missing

- **The node and relationship caps. DECIDED to add, one sentence.** The class is on Free, so 200,000 nodes and 400,000 relationships are real numbers a participant can hit. These two are not the drifting dataset counts the no-counts rule targets; they are product limits, and they change about never.

- **`Aura_Free_Trial.md` folds into `01_aura_setup.ipynb` and is deleted.** It is a signup procedure, so the notebook-first split takes it. Deleting it also retires a filename that argues against its own contents.

### To add

- **One line on what the instance carries forward. DECIDED to add.** This instance is the one database every later lab reads and writes. There is no fallback instance, by decision, so a lost password means redoing Labs 2 and 3.

### Slides

- **`platform-overview/01-neo4j-aura-overview-slides.md` is not embedded. DECIDED to publish**, after checking it for the tier claim.

- **`Lab_1_Aura_Setup/slides/07-lab-steps-1.md:6,12 say "free trial". DECIDED to fix.** Both lines become "AuraDB Free". This deck lives in the lab folder rather than `slides/`, so the deck-split table below does not cover it and it will be missed unless someone looks for it.

> **STATUS: DONE. The four Lab 1 items no numbered step owned are closed.** Steps 1 and 2 took the rest of this section; these were decided here and then never picked up by a step, so they are done as their own pass.
>
> **Aura Agents is gone from `lab1.adoc`.** Both edits, as the item said: the `Aura Agents: no-code agent platform` block deleted, and the At-a-Glance line rewritten. That line had a second problem the item named, advertising Graph Data Science on the tier that does not have it, so it now reads "with built-in vector search. You use **AuraDB Free**, which never expires and holds up to 200,000 nodes and 400,000 relationships." **The caps sentence from "Missing" lands in the same line**, which is where a participant will actually meet it.
>
> **The GDS claim ran deeper than line 12.** The `Vector search, Graph Data Science, and AI capabilities` collapsible also promised "Graph Data Science algorithms like PageRank and community detection run directly within Aura", to a room that cannot run one. It is now two collapsibles: **What AuraDB Free gives you, and what it does not**, carrying the caps, the never-expires point and the GDS skip in the same take-home framing step 2 gave the Appendix A notebooks; and **Vector search and AI capabilities**, which is the old block with the GDS bullet removed and "Both are on Free" added.
>
> **The carry-forward line from "To add" is now an `IMPORTANT` admonition in the opening**, not a buried sentence: one instance, no fallback, a lost password means redoing Labs 2 and 3.
>
> **`lab1.adoc:3` said "This is Lab 1 of 4."** Not in any list, and false since Labs 5 and 6 shipped. Now "the first of six labs", and the sentence names what Labs 5 and 6 do with the instance rather than stopping at Lab 4.
>
> **`Aura_Free_Trial.md` was verified folded before step 5 deleted it**, not assumed. `01_aura_setup.ipynb` cells `part1-header` through `part1-limits` carry all seven signup steps, both screenshots, the caps, the one-instance and 30-day-inactivity limits, and the GDS skip. The notebook is the better version: the trial warning is a `WARNING` block and the password-shown-once point is a `CRITICAL` block.
>
> **Aura Agents swept beyond the site, because "every mention" was decided.** `platform-overview/01-workshop-over.md:45` and `docs/overview-and-genai-foundations.md:17` both listed "**Create** a no-code Aura Agent" as a workshop learning objective. Nobody creates one. Those were the two worst instances found, worse than the site's, because they are a promise on the opening deck. Deleted. `platform-overview/01-neo4j-aura-overview-slides.md` lost its three Aura Agents slides and its summary bullet.
>
> **The tier check on `01-neo4j-aura-overview-slides.md` is done, and it failed.** Its `Graph Analytics in Explore` slide lists 65-plus algorithms with no hint that the workshop instance has none of them. A note now says so, in the take-home framing. **Step 10 can publish this deck.**
>
> **Left, deliberately, and both need a decision rather than an edit:**
> - `01-intro-databricks-neo4j-slides.md:99,189` name Aura Agent in two lists of what the Neo4j product includes. Neither claims a participant builds one, so this is product-capability content on a product-overview deck, not a false promise. Deleting a product from a capabilities slide is a different call from deleting a false learning objective, so it is Ryan's.
> - `workshop-setup/docs/EXAMPLE_QUERIES.md` is an entire file of questions written for an Aura Agent, and `workshop-setup/README.md:361` describes it as such. Admin material, participant-invisible. It either gets retargeted or retired, and neither is a wording fix.
>
> **One count noticed and left.** `01_aura_setup.ipynb` cell `part1-limits` says "about 21,613 nodes, which is 10.8 percent of the node cap". Re-running the generator moves it, so the no-counts rule catches it, but its whole job is to reassure a participant they fit inside the cap and a vaguer sentence does that worse. Not in step 4's swept list. Flagged, not changed.
>
> **Verified.** `npm run build` in `site/`, clean.

---

## Lab 2: Databricks ETL to Neo4j

### Needs fixed

- **The GDS notebook tier gate. DECIDED: make it optional.** The class is on AuraDB Free, GDS is not on Free, so `02_gds_knn_aircraft.ipynb` cannot run for anybody in the room. Say that plainly and mark it skippable. Drop `lab2-instructions.adoc:31`'s "requires AuraDB Professional" framing, which reads as a prerequisite to go acquire rather than a reason to skip.

- **`lab2-instructions.adoc:77` sends participants to Lab 4 for the supervisor. RESOLVED by the split**, page retired. The equivalent handoff on `lab2.adoc` still needs to point at Lab 3, then Lab 4 Part A, then Lab 5.

  **DECIDED.**
- **`lab2-instructions.adoc:35-37` is a two-sentence stub for the longest lab. RESOLVED by the split**, page retired. The procedure is already in the notebook.

### Missing

- **What Lab 2 does *not* load.** Lab 2 writes zero `Reading` nodes to Neo4j; telemetry stays in Delta. Belongs on `lab2.adoc` as concept, and it is the one count worth keeping.

  **DECIDED.**
- **The canonical `OperatingLimit` rows and the `HAS_LIMIT` edges.** The graph-shape block omits `HAS_LIMIT` entirely, and Lab 5's limit questions depend on it. Add the edge to the shape diagram, no counts.

  **DECIDED.**
- **`CLEAR_DATABASE = True` as a contract, not a cure.** Today it appears only in troubleshooting. On the notebook side it belongs in the procedure; on the site side, one line on `lab2.adoc` about why the load is destructive by design.

  **DECIDED.**
- **Sensor units.** `EGT` is `°C` and `N1Speed` is `% RPM`, matching the manual limit tables so `Sensor.unit = OperatingLimit.unit` joins on a plain string compare. This is why Lab 5's limit questions work at all. Concept, belongs on the page.

  **DECIDED.**
### To add

- **A per-label expected-count table. DROPPED** by the no-counts decision. Verification belongs in the notebook, where it can be a query that prints live numbers instead of prose that goes stale.

- **A pointer to Appendix A.** Currently promises an Appendix A the site does not have. Fixed when the Appendix A page lands.

### Slides

- **`slides/aircraft/` holds the three-step ETL diagrams** (`step1-flat-tables-foreign-keys`, `step2-spark-connector-mapping`, `step3-connected-graph`). They are already in `site/modules/ROOT/images/` but no published deck teaches them. This is the clearest visual in the repository for what the Spark Connector does.

  **DECIDED:** `platform-overview/`, in the deck that introduces the dual-database story, and shown again on `lab2.adoc` itself. Not `kg-construction/`: these three diagrams are about the Spark Connector turning foreign keys into edges, which is a Lab 2 idea, while `kg-construction/` is about extracting a graph from text, which is Lab 3's. Putting them in the wrong deck buries the clearest visual in the repository under material filed as Background.

- **`kg-construction/05-building-knowledge-graphs-slides.md:102`** carries the "20 aircraft" count. Covered by the no-counts sweep.

---

## Lab 3: Semantic Search

### Needs fixed

- **`lab3-instructions.adoc` teaches plaintext credentials, misdescribes the volume path, and hands off to the wrong lab. RESOLVED by the split**, page retired. All three are already right in the notebooks.

- **`lab3.adoc` has no `OperatingLimit` versus `ExtractedLimit` split.** `lab3-sample-queries.adoc:133-204` has it correct; the concepts page never introduces the distinction its own sample queries depend on. `OperatingLimit` means the canonical CSV rows, `ExtractedLimit` is what the LLM read out of the manual.

  **DECIDED:** Add it, and make it the page's central idea rather than a definition. Two labels for the same fact, one trusted and one inferred, is the honest version of what LLM extraction produces. Lab 5's refusal rule ("never substitute a limit for a measurement") only makes sense to someone who already knows these are two different things.

### Missing

- **The secret scope as a teaching beat.** Four keys, scope name derived from `current_user()` because scope names are workspace-unique rather than per-user. This is the credential handoff the entire back half of the workshop rides on, and it is the kind of thing that belongs on a concepts page precisely because it is not a step.

  **DECIDED:** Add it, one paragraph. Written once in Lab 3, read by Labs 3, 5 and 6, which is why a Lab 3 mistake surfaces two labs later as a failure that looks like Lab 5's fault. Say that out loud and the debugging story writes itself.

- **`NEO4J_DATABASE` as the fourth key.** Newly threaded through Labs 3, 5 and 6. Worth a line only if the tier answer means the value is ever anything but `neo4j`. See the database-name question in `expand-v3.md` section 5, under answered questions.

  **DECIDED:** One line, not a paragraph. On AuraDB Free the value is always `neo4j`, so for every participant this key is a constant. It exists for the instructor's multi-database instance and for anyone who later points the labs at their own. Say it is there and why, then move on.

- **The embedding model, named once.** `databricks-bge-large-en`, 1024 dimensions, the same endpoint the admin loader uses, which is why loader-written vectors and notebook-written query vectors are comparable at all.

  **DECIDED:** Add it. The "same endpoint both sides" point is the one that matters, not the model name: vectors from two different models are not comparable and the failure is silent, returning plausible nonsense rather than an error. That is the reusable lesson.

- **Index names and what breaks without them.** `maintenanceChunkEmbeddings` and the fulltext index. If the vector index is missing, Lab 5 silently drops `graphrag_node` from its routing list rather than failing loudly. That is a concept worth teaching, not a troubleshooting note.

  **DECIDED:** Add it, and put it on `lab5.adoc` as well as `lab3.adoc`. A participant who skipped Lab 3 gets a Lab 5 agent that works, answers, and quietly cannot reach the manuals. Silent degradation is a design choice worth defending on the page, since the alternative, failing at import, would strand them entirely.

### To add

- **A "what Lab 3 leaves in your graph" close**, as shape rather than counts: documents, embedded chunks, two indexes, one secret scope. That list is exactly Lab 5's entry condition.

  **DECIDED:** Add it, and reuse the same four bullets verbatim as Lab 5's "before you start" list. One list stated twice from both ends is how a participant self-checks without an instructor.

### Slides

- **`retrieval-patterns/` is four decks, none published.** Filed Workshop in the table above. Deck 03, Vector Cypher Retriever, is now load-bearing for Lab 3 and Lab 5 both.
- **`kg-construction/` is five decks, none published.** Split: vectors and chunking to Workshop, schema design and entity resolution to Background.

  **DECIDED:** As stated. Chunking and vectors are the two things Lab 3 notebook 01 actually does, so a participant needs them before running it. Schema design and entity resolution are craft topics with no Lab 3 step behind them, which is what makes them Background rather than cuts.

---

## Lab 4: Compound AI Agents

### Needs fixed

- **The stale Genie instruction block. RESOLVED by the split.** This was the worst defect in the document: a participant pastes it into their own Genie space and Genie then answers from it. `04_genie_agent.ipynb` is verified correct on disk. Retiring `lab4-instructions.adoc` removes the bad copy rather than fixing it.

- **`lab4.adoc:3` uses the stale reading count.** Covered by the no-counts sweep. The sentence motivating the whole lab has to be rewritten around shape: the full telemetry ledger never enters the graph, so GraphRAG cannot reach it.

- **`lab4.adoc:12` and `workshop-overview.adoc:51` still call the Agent Bricks supervisor the final architecture. DECIDED to fix. Not a question, a sequencing constraint.**

  The Part B reframing landed on `lab4-instructions.adoc` and nowhere else. That page is the one the split deletes. So the deletion, on its own, would take the *only* corrected copy off the site and leave the two stale ones standing.

  **The constraint that falls out: fix `lab4.adoc` and `workshop-overview.adoc` in the same change that deletes `lab4-instructions.adoc`, never after.** Doing them in the other order leaves `main` published, briefly, saying the retired architecture is the destination. Nothing to decide, just an ordering not to get wrong. It is reflected in the work order below.

### Missing

- **Which tables the Genie space attaches.** Four of the eight gold tables. Concept-level: Genie reads table and column comments, so scope is a modelling decision, not a permissions one.

  **DECIDED:** Add it, and merge it with the eight-versus-four item below into one beat. They are the same idea twice. The lesson: what you *hide* from Genie shapes its answers as much as what you show it, and the comments in `lab/workshop.py` are written to be read by a model.

- **The Genie space ID.** Participants copy the 32-character ID out of the room URL because everyone titles their space differently, and Lab 5 and Lab 6 both read `GENIE_SPACE_ID`. **Procedure, so it lives in the notebook.** The site's job is one line saying Lab 4 produces a value Lab 5 consumes.

  **DECIDED:** One line on the site, procedure in the notebook. This is the second cross-lab handoff after the Lab 3 secret scope, so name it as one: Lab 4 produces a value, Lab 5 consumes it, and losing it costs a rebuild.

- **The eight gold tables versus the four Genie sees.** Concept, belongs on the page.

  **DECIDED:** Fold into the first item above. One beat, not two.

### To add

- **An explicit Part A / Part B split at the top of `lab4.adoc`.** You build Part A, you watch Part B.

- **A closing contrast for Part B:** no-code Agent Bricks over a governed MCP connection, versus the same routing written in code in Lab 5. That contrast is the only reason Part B survives as a demo.

  **DECIDED:** Add it, and make it a table rather than prose. Two columns, Part B and Lab 5, across rows for how it is built, where credentials live, who can change it, and what it costs to extend. Without that contrast Part B reads as a lab that got cancelled.

### Slides

- **`agents/02-power-of-graphrag-slides.md` needs reframing, not replacing.** Its last five sections present MCP plus Agent Bricks as *the* architecture. Retitle that run as the Part B demo and put the Lab 5 path beside it.

  **DECIDED:** Reframe, do not rewrite. Five section titles and a lead-in slide, not new content. The material is correct; only its billing as the destination is wrong.

- **`platform-overview/01-databricks-neo4j-integration-slides.md:300-313`** already has "Alternative Architecture: Agent as a Serving Endpoint." That is now the primary architecture. Promote it and retitle.

  **DECIDED:** Retitle to "Agent as a Serving Endpoint" with the word "Alternative" removed, and move it ahead of the MCP section rather than after it. Order is the argument here: whatever comes first reads as the default.

- **`01-workshop-over.md:120-143`** already reads "used only in the Part B demo." Correct as-is, leave it.

---

## Lab 5: LangGraph Agent

**Nothing exists on either surface. This is the workshop's payoff lab.**

### Missing, site

- **`lab5.adoc`, one concepts page.** No instructions page, per the split. LangGraph state graph, the supervisor as a routing node, three tool nodes, and why a direct bolt driver rather than a per-participant MCP server.
- **A `nav.adoc` entry.**

### To add

- **The three tools, one line each.** `genie_node` for SQL over Delta telemetry, `cypher_node` for traversal over the participant's own Aura instance, `graphrag_node` for a `VectorCypherRetriever` over the Lab 3 manual chunks.

- **The routing lesson, which is the lab.** `cypher_node` and `graphrag_node` sit close together because the GraphRAG retriever has a Cypher tail. **The measured routing numbers go on the site.** They are the strongest evidence in the repository. Routing accuracy differs from dataset counts: it is a claim about the workshop's own quality, and it goes stale only when the prompt changes.

  **DECIDED:** Put them on the site. The no-counts rule was aimed at dataset facts that drift on every regeneration; a routing accuracy figure is a measurement of this workshop's own quality and it moves only when someone edits the prompt. State it with the date it was measured and the prompt version, which is what makes a number honest rather than decorative.

- **The prompt is the artifact.** Two rules earned their place from measured failures. The refusal rule: never substitute a limit, threshold or ceiling for a measurement. The direction rule: an `AFFECTS_AIRCRAFT` arrow written backwards was fixed with nine lines of schema text rather than by dropping the arrow, because dropping it teaches a Cypher habit Lab 1 spends its time arguing against.

  **DECIDED:** Add both rules with the failure that produced each one. A prompt rule with its bug attached is a lesson; the same rule without it is a wall of text nobody reads. The direction rule is the better of the two to lead with, because "we fixed the prompt rather than the schema" is the non-obvious call.

- **The anchor question, end to end.** Genie names the engines with abnormal EGT, the graph returns their maintenance history including a bearing wear fault, the manual closes with the high-EGT procedure. One question, three tools, one answer. This is the demo the whole workshop builds toward and it belongs on the page.

- **Deployment as its own beat.** Logging to Unity Catalog, then serving as an endpoint that authenticates as a **service principal** rather than as the notebook user. That is the line between a notebook demo and a product, and `worklog/agenda.md` already treats it as its own topic.

  **Lab 5 ships two notebooks, and the second one is this beat.** `01_langgraph_agent.ipynb` builds the graph; `02_deploy_and_evaluate.ipynb` logs, registers, serves and evaluates it. The deck split decided below falls out of the folder structure rather than being a judgment call: one deck per notebook. It is also where the measured routing numbers get re-run, so the site states the claim and cites the date, and the notebook is what reproduces it.

- **The credential path.** Reads the Lab 3 scope. No plaintext password anywhere in Lab 5.

- **Degradation, stated.** A missing vector index drops `graphrag_node` from `available_tools` rather than raising at import.

- **A new architecture diagram.** Supervisor node, three tool nodes, two backends, one Model Serving endpoint. This is the one that replaces the MCP topology on `README.md:36`.

### Missing, slides

- **A LangGraph supervisor deck, `agents/03-langgraph-supervisor-slides.md`.** `agents/01-from-retrievers-to-agents-slides.md` teaches ReAct and tools generically and stops well before any of this.

- **A deployment deck, `agents/04-deploy-the-agent-slides.md`.** MLflow `ResponsesAgent`, Unity Catalog registration, Model Serving, service principal auth. `worklog/agenda.md` lists "Deploying the Agent" as its own topic and no deck backs it.

  **DECIDED:** Two decks. `worklog/agenda.md` already treats deployment as its own topic, and the audiences differ: the supervisor deck is for whoever is writing the graph, the deployment deck is for whoever has to explain service principal auth to a security reviewer. Merging them buries the second inside the first. Two decks also survive a shortened day better, since deployment is the one that gets cut.

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

  **DECIDED:** One line on the site, procedure in the notebook. Say plainly that it is a fork and name what the fork fixes. A pinned fork wheel on a volume is the kind of thing a participant will try to reproduce at work, and they need to know whether they are waiting on an upstream release or carrying a patch forever.

- **One endpoint, redeployed.** Lab 6 redeploys the endpoint Lab 5 created rather than making a second one, which is why the memory-off baseline has to be captured before Lab 6 overwrites it.

- **Graph cost. DECIDED to include.** The class is on Free, so the cap is real and the arithmetic reassures rather than worries: memory costs about 20 nodes per participant per session against roughly 178,000 nodes of headroom after Labs 1 through 3.

- **`02_instructor_demos.ipynb` ships.** Closes the question in `expand-v3.md` section 5 on whether the Lab 6 instructor demos ship to participants. **The four demos in it are the Lab 6 payoff**, and the memory deck below leans on demo 1.

  **DECIDED:** Ship it, as an instructor notebook rather than a participant one. Slide 5 and slide 8 of the memory deck both run out of it, so cutting it means rewriting the deck around material that no longer exists. Instructor-only keeps it off the participant critical path while the demos stay runnable on stage. That needs the `course.env` entry.

### Missing, slides

- **An agent memory deck, `agents/05-agent-memory-slides.md`.** `slides/images/graph_mem.jpg` already exists and no deck uses it. Slide-by-slide flow in the "Intro to Agent Memory" section below.

### Open, do not write around it

- **AuraDB Free index and constraint caps.** Lab 6 installs 33 indexes and 12 constraints on top of Lab 3's, untested on a fresh Free instance. If the combined total exceeds the cap, Lab 6 fails for the whole room at once. **Do not publish a Lab 6 page promising it works until this is measured.** The tier decision does not close this one, it confirms it: Free is the tier, so the cap applies, and the AuraDB Free index and constraint question in `expand-v3.md` section 5 stays the single remaining no-go.

  **The check script does not exist.** Both this document and the plan of record used to describe `scratchpad/aura_free_index_check.py` as written, with "a read-only `check` and an apply-then-roll-back `probe`." There is no `scratchpad/` directory in the repository and nothing in git history ever created one. It was written into an ephemeral session scratchpad and is gone. **Correct both documents and treat the script as unwritten.**

  **DECIDED:** Step 0 is two jobs, not one. **Write the script, then run it.** It needs a durable home in the repository this time, not a scratchpad: `workshop-setup/verify/` already exists as the package that replays lab queries against Aura, and this is the same shape of thing. Give it the two modes the lost version had, read-only `check` first so it can run against any instance safely.

  It still blocks only `lab6.adoc`, and it still cannot be started by anyone without a fresh Free instance to point it at. **Ryan provisions; the script can be written before the instance exists.**

---

## Appendix A: GDS Graph Analytics

### Missing

- **Any site page at all.** Three notebook families on disk (Louvain community detection, PageRank plus Betweenness centrality, Node Similarity), plus `gds-exploring.md`, plus a nav entry. `lab2-instructions.adoc:33` already points at an Appendix A that does not exist.

### To add

- **The tier statement, up top. DECIDED, and it is now a warning rather than a footnote.** The class is on AuraDB Free and GDS is not on Free, so **nobody in the room can run Appendix A on their workshop instance.** State that in the first paragraph, not the fifth. Without it the appendix is a trap: a participant works through the setup and fails at the first `gds.` call.

- **The dependency chain.** All of it needs Lab 2 notebook 01. Node Similarity additionally assumes `02_gds_knn_aircraft.ipynb` has run.

- **Appendix A is take-home.** Its `graph-ml/` decks are still taught.

  **DECIDED:** Take-home, and the tier decides it rather than the agenda. Nobody in the room can run GDS on an AuraDB Free instance, so "taught" could only mean watching an instructor demo, and the day has no spare slot for one. **Keep the `graph-ml/` decks as Workshop anyway**, which is the one place I would break my own table: the concepts, graph features feeding an ML model and the bidirectional loop back to Databricks, stand on their own without anyone running a `gds.` call. Teach the idea, hand out the notebooks.

### Slides

- **`graph-ml/03-graph-enrichment-slides.md` and `04-future-graph-enrichment-slides.md`** are the conceptual half of this appendix and are unpublished. They cover the GDS algorithms, the MLflow lift comparison, and the bidirectional data loop, which is the `worklog/agenda.md` topic "Graph Algorithms: From Connected Data to Analytical Features."

  **DECIDED:** Publish both as Workshop, per the answer above. They are the only decks backing a named agenda topic, and they are the half of Appendix A that survives the tier constraint. The notebooks go take-home; the argument stays on stage.

---

## Governance, Not a Lab

- **`governance/auth-sync-slides.md`** covers four patterns for aligning Unity Catalog and Neo4j privileges. PDF only, no HTML, referenced by nothing. Filed Background above.

  **DECIDED:** Publish under Additional Background. It costs one nav line and it answers the question a customer asks right after the workshop lands: who is allowed to see what, once the same data lives in two systems. Dropping it deletes the only material in the repository on that. Note it is PDF-only today, so it needs its source rebuilt to HTML before it can go anywhere.

---

## Suggested Flow: Intro to Agent Memory

The deck Lab 6 is missing, `agents/05-agent-memory-slides.md`. Nine slides, about 16 minutes. Full research and sources were in `scratch-agent-memory-research.md`, deleted in the docs cleanup and readable at `git show 1be478f:scratch-agent-memory-research.md`. The slide-by-slide below is the working record. Assumes GraphRAG and the Lab 5 supervisor are already taught, and lands on Lab 6's own demo.

### The one decision to make before writing a word

- **Neo4j ships two taxonomies and they conflict.** The 2025 developer blog, Alex Gilmore, borrows LangGraph's: short-term versus long-term, with long-term splitting into semantic, episodic and procedural. The 2026 Labs and hosted-service line uses short-term / long-term / **reasoning**. Neo4j's own glossary maps external "episodic" onto short-term, which inverts the LangGraph mapping.
- **Use the 2026 one.** `Lab_6_Agent_Memory/memory.py` and `02_instructor_demos.ipynb` are built on `short_term`, `long_term` and `reasoning`, so the deck has to match the code participants run. Name the conflict in one sentence, cite Gilmore as the cross-walk, move on.

  **DECIDED:** Use the 2026 taxonomy. The deck has to match the code participants run, and `memory.py` is built on `short_term`, `long_term` and `reasoning`. Naming the conflict once is also worth doing on its own merits: anyone who reads a Neo4j blog after the workshop will hit the other taxonomy, and one sentence now saves them the confusion later.

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

**DECIDED:** The nine as ordered, with one caution. **Slides 5 and 6 are the soft middle.** They are the most interesting to a practitioner and the least connected to anything a participant runs, so they are where a room's attention goes if the day is running late. If time is short, cut 6 into a line on 7 and keep 5, because 5 has a live demo behind it and 6 does not. Slide 8 is the argument for the entire lab and never gets cut.

### Notes for whoever builds it

- **Cutting to 15 minutes:** fold slide 6 into one line on slide 7. Do not cut 8.
- **`slides/images/graph_mem.jpg` already exists** and no deck uses it. Slide 3 or 4.
- **Three different things share the "Neo4j memory" name.** The old `mcp-neo4j-memory` server under `neo4j-contrib`, the `neo4j-agent-memory` library Lab 6 pins, and the hosted service. Do not conflate them on a citation slide.
- **Comparison points worth naming once:** Zep/Graphiti, mem0, LangGraph checkpointers and store, Letta. Letta's operating-system hierarchy, core memory as RAM, recall as disk cache, archival as cold storage, is the cleanest borrowed analogy if slide 3 needs a second one.
- **Slide 8 depends on `02_instructor_demos.ipynb`**, so the open question about whether that notebook ships reaches this deck too.

---

## Suggested Order of Work

Revised for the notebook-first split. The early steps are deletions, which is why they come first: they remove about 1,300 lines of site content and 416 lines of README that would otherwise have to be edited.

**Step 0, and it starts before everything:** the AuraDB Free index-cap check, which is **write the script, then run it**. The version both this document and the plan of record described as existing did not. Give it a durable home under `workshop-setup/verify/`. Writing it blocks on nothing; running it blocks on Ryan provisioning a fresh Free instance. It is the only item here that can invalidate work already written.

> **STATUS: script written, run still owed.** `workshop-setup/verify/src/verify_aura_caps/main.py`, registered as `verify-aura-caps` in that package's `pyproject.toml`. Two commands as decided: read-only `check` and apply-then-roll-back `probe`. Ruff clean. `check` was run against the instructor instance `f024ea61` and reports 59 indexes and 24 constraints, so Lab 6 would project to 92 and 36 there. **That is not the answer**, because `f024ea61` is not Free. The run that closes this needs a fresh Free instance.
>
> **It already earned its keep once.** `home_database()` reads the home database out of `SHOW DATABASES` rather than assuming `neo4j`, and on `f024ea61` the answer is `f024ea61`. A version that assumed `neo4j` would have failed on the first real query.
>
> `expand-v3.md` corrected to match: the script is unwritten there no longer, and the false "read-only `check` and apply-then-roll-back `probe`" claim is replaced by what actually exists.

1. **Retire the four instructions pages, correct `lab4.adoc` and `workshop-overview.adoc`, and collapse `nav.adoc`, as one change.** Both live defects die here. The three parts ship together because deleting `lab4-instructions.adoc` alone would leave only the uncorrected Agent Bricks framing on a site that publishes on every push. Confirm each notebook carries what its page carried before deleting. **Do not add the slides nav group here**; it has no pages to point at until step 10.

> **STATUS: DONE.** `849` lines of site content deleted across the four pages. `npm run build` in `site/` completes with no warnings, so no `xref` was left pointing at a deleted page.
>
> **What moved rather than died.** Three things the deleted pages held were concept, not procedure, and would have been lost:
> - **The full graph shape**, now on `lab2.adoc` **with `HAS_LIMIT` added**, which the old block omitted entirely. Lab 5's limit questions depend on that edge. The sensor-unit point (`EGT` is `°C` on both sides, `N1Speed` is `% RPM`) is stated there too, since it is why the join is a plain string compare.
> - **`CLEAR_DATABASE = True` as a contract**, now its own short section on `lab2.adoc` rather than a troubleshooting note. Appending twice gives you two of everything; wiping first is what makes the load repeatable.
> - **Zero `Reading` nodes**, now a named section on `lab2.adoc`. The one count the no-counts rule keeps.
>
> **`lab4.adoc` was further along than the plan assumed.** Line 121 already carried a correct Part B note. What was missing was the framing above it, so the page now opens with a "Part A you build, Part B you watch" section, the At-a-Glance bullets are labelled by part, and the Part B versus Lab 5 contrast table decided in the Lab 4 section is written. The architecture image is retitled as the Part B demo in its alt text.
>
> **`workshop-overview.adoc` lost its architecture image rather than gaining a new one.** The section now describes the Lab 5 endpoint in prose and points at `lab4.adoc` for the Agent Bricks contrast. **Step 7 owes it the Lab 5 topology drawing.** Its "What You Will Learn" list gained Lab 5 and Lab 6 as plain text; step 8 turns those into `xref`s once the pages exist.
>
> **Left for the step that owns it:** the lab table on `workshop-overview.adoc` still stops at Lab 4, because adding rows means adding `xref`s to pages that step 8 writes.
2. **Sweep the tier language. Sixteen lines across ten files**, tabled under Lab 1. Two files die with step 1. The other eight need real edits, and **four of them are the Appendix A notebooks**, which today tell participants to go acquire Professional. Everything says AuraDB Free.

> **STATUS: DONE except the two lines step 5 owns.** Seven files edited. A repo-wide grep for `free trial`, `AuraDB Professional`, `Aura Professional` and `14-day` now returns only lines that name the trial in order to warn participants off it, plus the two below.
>
> **The Appendix A notebooks are fixed and they were the point.** All three now open with the same skip framing `02_gds_knn_aircraft.ipynb:7` already had, and add the take-home line: read it now, run it later on an instance that has GDS. Their prerequisite lists no longer say "Neo4j Aura credentials (AuraDB Professional or higher)", which read as a shopping instruction; they say "An instance with the GDS plugin, which your AuraDB Free workshop instance is not." Applied with a checked script, `scratchpad/tier_sweep.py`, that fails loudly on any pattern it cannot find. All four reported `ok`.
>
> **Two corrections to this document's own table.**
> - **`workshop-setup/docs/MANUAL_SETUP.md:118` needed no edit.** It already carries the skip framing: "Graph Data Science needs Aura Professional and Vocareum participants are on Aura Free, so shipping either one hands a student a notebook that cannot run." That is a reason, not a prerequisite. Left alone.
> - **`Lab_2_Databricks_ETL_Neo4j/02_gds_knn_aircraft.ipynb:38` was not already correct**, though the table listed it that way. Line 7 had the skip framing and line 38's prerequisite list still said "AuraDB Professional or higher — GDS plugin required", so the notebook contradicted itself two screens apart. Fixed to match line 7.
>
> **Also swept, and not in the table:** `Lab_1_Aura_Setup/slides/07-lab-steps-1.md` needed more than a wording change. Its Step 2 said the instance "is created automatically", which is the trial path. It now says which button not to click and where the AuraDB Free option hides.
>
> **Left for step 5, as planned:** `README.md:96` and `:158`, which the 30-line cut rewrites, and `Lab_1_Aura_Setup/Aura_Free_Trial.md`, whose body is correct and whose filename is the problem.
3. **Delete the three build-output slide folders, clear the stale attachments, then fix the build script three ways.** `overview-databricks-neo4j/`, `overview-knowledge-graph/` and `overview-retrievers/` go; `aircraft/` and `databricks-in-depth/` stay, because they hold diagram sources. Clear `site/modules/ROOT/attachments/slides/`, whose folder names describe where decks used to live. Then: point the script at real topic folders, drop the hardcoded `/opt/homebrew/opt/node@22/bin/node`, and **add a marp step to `deploy-antora.yml`**, which today never builds a deck at all. Items 1 and 2 without item 3 publish nothing.
> **STATUS: DONE. The decks now reach the published site, which they never did before.**
>
> **Folders gone.** `overview-databricks-neo4j/`, `overview-knowledge-graph/` and `overview-retrievers/` are deleted. Only one file among them was tracked, a built PDF; the rest was untracked build output. `slides/databricks-in-depth/auth-sync-slides.pdf` went with them, for the same reason.
>
> **The script had already been half-fixed** by an uncommitted earlier pass: `build:decks` no longer feeds built HTML back in as input. What was left was the hardcoded interpreter and the missing CI step.
>
> **The hardcoded path was hiding a real break, not a preference.** `/opt/homebrew/opt/node@22/bin/node` was pinning marp to Node 22 because `@marp-team/marp-cli@4.2.3` dies on newer Node with `ReferenceError: require is not defined in ES module scope`, thrown from its bundled `yargs`. Dropping the path to a bare `marp` therefore broke the build until the real cause was fixed: **marp-cli is upgraded to `^4.5.0`**, which builds clean on the Node 26 this machine runs and on the Node 20 CI runs. `slides/package-lock.json` moved with it.
>
> **CI builds decks now.** `deploy-antora.yml` gained `npm ci` and `npm run build:html` in `slides/`, both ahead of the Antora build, and `cache-dependency-path` now lists both lockfiles.
>
> **Committed build output is retired**, which is what makes the CI step the delivery path rather than a duplicate of it. `site/modules/ROOT/attachments/` is gitignored and `git rm -r --cached`'d. Three tracked HTML decks and one stale PNG left the index. Nothing under that directory is authored; all six files it holds are produced by `build:html`.
>
> **Verified from a clean tree.** `rm -rf site/modules/ROOT/attachments`, then `npm run build:html` in `slides/`, then `npm run build` in `site/`. Antora finished with no warnings and the three decks plus three SVGs land in `site/build/site/databricks-neo4j-workshop/1.0/_attachments/slides/`.
4. **Sweep the dataset counts out** of the nine files tabled in section 0, **including both full per-label tables** and `README.md:57`. Mechanical, but larger than the earlier list implied.
> **STATUS: DONE. Every tabled file swept, plus three the table missed.**
>
> **The seven tabled files.** `workshop-overview.adoc:24,35`, `lab4.adoc:3`, `01-workshop-over.md:85-91,101`, `overview-and-genai-foundations.md:49-55,63`, `organize.md:63`, `05-building-knowledge-graphs-slides.md:102`, `README.md:57`. Both per-label tables lost their `Count` column outright rather than losing seven rows, which keeps the entity list, the part that teaches, and drops the part that drifts.
>
> **Replacement language, used consistently:** "hourly-scale telemetry over 90 days" and "a multi-model fleet". Table cells that existed only to hold a number are gone.
>
> **Three the verified list missed**, all the same class and all participant-facing:
> - `README.md:66` said "telemetry every 4 hours over 90 days" while the site said hourly. A second live contradiction in the same fact, sitting nine lines below the one the table did catch.
> - `vocareum/docs/README.md:29` carried the "roughly 155K" figure. This is the front page of the participant's own Databricks workspace, so it is not a minor surface.
> - `Lab_2_Databricks_ETL_Neo4j/01_aircraft_etl_to_neo4j.ipynb` said "155,520 sensor readings" in the very cell that argues the dual-database split. The sentence reads better without it.
>
> **What deliberately stayed.** The same notebook cell's "20 documented takeoff thresholds" and "these 20 rows and only these 20 rows" pass the decision's own test: they are transcribed from the manuals and Lab 3 compares its extraction against them. Re-running the generator does not move them. `workshop-setup/populate_aircraft_db/DATA_GENERATOR.md` keeps its counts too, because there they are the specification of what the generator emits, not a claim to a participant.
>
> **Not fixed, and it is now wrong: `slides/organize.md` paths.** Step 3 deleted `overview-knowledge-graph/`, `overview-databricks-neo4j/` and `overview-retrievers/`, and roughly 60 lines of this inventory still cite files by those paths. It is an internal planning document, not a participant surface, and **step 10 rewrites the deck inventory anyway**, so the repair belongs there rather than as an unscoped edit here. Flagging it so it is not forgotten.
>
> **Verified.** `npm run build:html` in `slides/` then `npm run build` in `site/`, both clean.
5. **Collapse the four participant-facing lab READMEs into their notebooks**, delete `PART_A.md`, keep `PART_B.md`, and shrink the Lab 5 and Lab 6 READMEs to module documentation. Cut the root `README.md` to about 30 lines of pointers, which also retires its two tier mentions and its count.
> **STATUS: DONE, except the Lab 5 and Lab 6 README shrink, which moves to step 8.**
>
> **Six files deleted:** the four participant-facing lab READMEs, `Lab_1_Aura_Setup/Aura_Free_Trial.md`, and `Lab_4_Compound_AI_Agents/PART_A.md`. `PART_B.md` kept, as decided. `Aura_Free_Trial.md` was checked against `01_aura_setup.ipynb` before deleting and was already fully folded in; the detail is in the Lab 1 status block above.
>
> **Two salvages, both landed before the delete.** The instruction to check each README for content the notebook does not have was worth following twice:
> - Lab 2's README held five troubleshooting cases the notebook never covered, and pointers to `SAMPLE_QUERIES.md`, `aura-explore.md` and `data-exploring.md`. Both are now cells in `01_aircraft_etl_to_neo4j.ipynb`: a new `lab2-troubleshooting` markdown cell before `next-steps`, and a "Go deeper on your own" table inside `next-steps`.
> - Lab 3's README held the four-key table for the `fleet-ops-<user>` secret scope, the one place naming `neo4j-database` and saying to leave it `neo4j` on Free. It is now in cell `627fcbcb` of `01_data_and_embeddings.ipynb`, which is the cell that writes the scope.
>
> **Five inbound `PART_A.md` links repointed** at `04_genie_agent.ipynb`: both Lab 5 notebooks, both Lab 5 and Lab 6 READMEs, and the root `README.md`. No dead link left in the repository, checked by grep.
>
> **Root `README.md` cut from 219 lines to 34**, and it now carries no content of its own beyond the one paragraph saying what the workshop builds. A lab table pointing at folders, an instructor table pointing at `workshop-setup/`, `DATA_GENERATOR.md`, `slides/` and `site/README.md`, and the feedback link. Both tier mentions and the reading count went with the cut.
>
> **Its homeless content moved to `workshop-overview.adoc` first, not deleted.** The doc's line "everything it duplicates moves to `index.adoc`" is not literally satisfiable: `index.adoc` is 13 lines and is a front door, not a container. `workshop-overview.adoc` is the page that actually duplicated the README, so that is where the three orphans went: the **Which Aura Instance Each Lab Uses** table, a **Reference Documentation** section holding both link lists, and the specific technology rows the site's vaguer table was missing, `databricks-bge-large-en`, `databricks-claude-sonnet-5`, LangGraph, Neo4j Agent Memory and Model Serving.
>
> **One falsehood fixed in passing.** `workshop-overview.adoc` listed "A Neo4j Aura instance (pre-provisioned by workshop administrators)" as a prerequisite. Participants create their own in Lab 1. Same class of error as the tier claims step 2 swept, on the page a participant reads before Lab 1.
>
> **Deferred to step 8: shrinking `Lab_5_LangGraph_Agent/README.md`, 250 lines, and `Lab_6_Agent_Memory/README.md`, 383 lines.** Their conceptual content has a named destination in step 8, `lab5.adoc` and `lab6.adoc`, and this document already decided at "**DECIDED:** Put them on the site." Shrinking them now would destroy the routing lesson, the operating-limits rules, the measured 12/12 results and the deploy notes with nowhere for any of it to go. The two halves are one move, and step 8 is where it belongs.
6. **Make `site/modules/ROOT/images/` the single source for every screenshot, and keep it that way.** REVERSED from this document's first draft, which moved them out; see the screenshots item in section 0 for why the site directory wins. Site pages reference locally with `image::`, notebooks reference by absolute `raw.githubusercontent.com` URL against `main`, both pointing at the one directory. **Move `Lab_1_Aura_Setup/images/FREE_*.png` in**, the only screenshots still outside it, and delete the emptied per-lab folders. **Delete `lab1-backup-restore.png`**, whose only consumer was the dead backup-restore procedure. **Leave the 7 concept `.svg` files where they are.** Write the convention down once so nobody invents a third.
> **STATUS: DONE, after the reversal.**
>
> **The direction changed before any of it ran.** This step originally moved screenshots out to per-lab folders. A separate session had already implemented the opposite and recorded it in `svg-png.md`. Both could not ship. Ryan chose the site directory as the single source on 2026-08-08, and this document was rewritten to match before execution, rather than executing against a decision that had been overtaken.
>
> **Two screenshots moved in**, the only ones left outside the single source: `Lab_1_Aura_Setup/images/FREE_01_WHERE.png` and `FREE_02_Create_Instances.png`. **Renamed on the way** to `lab1-free-tier-location.png` and `lab1-free-create-instance.png`, because `SCREAMING_SNAKE` names sitting beside fifteen kebab-case ones is exactly the third pattern this item exists to prevent. Both consumers repointed: `01_aura_setup.ipynb` by raw URL, `Aura_Free_Trial.md` by relative path, the second of which step 5 deletes anyway.
>
> **`lab1-backup-restore.png` deleted.** Its only consumer was the page step 1 removed. Confirmed nothing else referenced it.
>
> **Three empty per-lab `images/` folders removed**, Lab 1, Lab 2 and Lab 3. Two held nothing but a `.DS_Store`. There is now no `images/` directory anywhere under a lab folder, which is what makes "single source" checkable rather than aspirational.
>
> **The convention is written down once, in `site/README.md`**, as a two-row table: pages use `image::`, notebooks use the raw URL, both against the same directory. It also carries the naming rule, `lab<n>-<subject>.png`.
>
> **`site/README.md` had gone stale from step 3 and was fixed in the same pass.** It told the reader to commit the generated deck HTML, which is now gitignored and built in CI, and its preview command still carried the hardcoded `/opt/homebrew/opt/node@22/bin/node`. Both were false the moment step 3 landed.
>
> **Left to step 7, unchanged:** the two duplicated `.svg` diagrams. Deleting the site copy of those is a different decision from where screenshots live, and step 7 owns it.
>
> **Verified.** `npm run build` in `site/`, clean.
7. **Collapse the duplicated diagram files, then redraw as two.** REVERSED from this document's first draft, which kept the root `images/` copies and deleted the site's. **The site directory wins, for the same reason step 6 gives.** Delete `dual-database-architecture.svg`, `dual-database-architecture.png` and `lab-architecture-overview.svg` from root `images/`, move `lab-architecture-overview.png` into `site/modules/ROOT/images/`, and repoint the three slide decks, `build:assets` and `04_genie_agent.ipynb` at the surviving copies. The `.excalidraw` files stay in root `images/`: they are editing sources rather than published assets, and Antora would otherwise ship 120KB nobody fetches. Then the Lab 5 topology becomes the default and the MCP drawing is retitled as the Part B demo, kept on `lab4.adoc` alone. Collapsing first is what stops the redraw shipping to half the consumers.

> **STATUS: step 7 done.**
>
> **The collapse.** Three files deleted from root `images/`: `dual-database-architecture.svg`, `dual-database-architecture.png`, `lab-architecture-overview.svg`. `lab-architecture-overview.png` moved to `site/modules/ROOT/images/`. Root `images/` now holds the three `.excalidraw` sources and `workshop-infrastructure.svg`, nothing else. The `.png` had zero live consumers, checked before deleting.
>
> **Five consumers repointed.** Three Marp deck sources (`platform-overview/01-databricks-neo4j-integration-slides.md`, `platform-overview/01-workshop-over.md`, `docs/overview-and-genai-foundations.md`), `build:assets` in `slides/package.json`, and the raw-URL reference in `04_genie_agent.ipynb`. That notebook also got its alt text fixed: it was `Lab Architecture Overview`, which named nothing, and is now "Part B instructor demo: an Agent Bricks supervisor routing to Genie and a Neo4j MCP agent".
>
> **One thing the plan did not anticipate: Marp does not copy images.** It writes a relative path into the emitted HTML verbatim. The published deck lands at `attachments/slides/<topic>/`, so `../../site/modules/ROOT/images/...` resolves against `attachments/`, not against the repository root, and the repointed decks shipped a broken image. Fix: `build:assets` now mirrors the SVG into `site/modules/ROOT/attachments/site/modules/ROOT/images/`. That nested path is deliberate. Any other reference would break either the live preview or the published deck, since the two resolve from different trees. **Written down in `site/README.md`** under "The one odd path, and why it is not a mistake", so nobody corrects it back.
>
> **The redraw.** `site/modules/ROOT/images/lab5-agent-topology.svg` is new: supervisor, the three tool nodes, the two stores, and the return path that makes routing a loop rather than a one-shot decision. It is placed on `workshop-overview.adoc` in `== Architecture`, which step 1 stripped and step 7 owed it. The MCP drawing stayed on `lab4.adoc` and needs no retitle: it never claimed to be the workshop's destination.
>
> **For Ryan.** The topology SVG is hand-authored, so it is vector-clean and reads well, but it does not match the sketched Excalidraw style of the other diagrams. If you would rather redraw it there, the `.excalidraw` source belongs in root `images/` per the convention step 6 wrote down.
>
> **Verified.** `npm run build:html` in `slides/`, then every emitted reference resolved on disk. `npm run build` in `site/`, clean, with `_images/lab5-agent-topology.svg`, `_images/lab-architecture-overview.{svg,png}` and `_attachments/site/modules/ROOT/images/dual-database-architecture.svg` all present. The new SVG was rendered to PNG and inspected twice: the first pass overflowed the supervisor box and crossed two labels through arrows, both fixed.
8. **Write `lab5.adoc` and `lab6.adoc`**, plus the Appendix A page and their nav entries. Appendix A opens with the tier warning in its first paragraph, and step 2 has already made its notebooks agree with it.

> **STATUS: step 8 done except Lab 6, which is gated and stays gated.**
>
> **`lab5.adoc` written**, 100 lines of concepts and no procedure. It carries the three tools, the shape of the agent with the step 7 diagram, the routing lesson, both prompt rules with the failure that produced each, the measured routing table, the anchor question, the credential path, the degradation behaviour, deployment as its own section, and why a Bolt driver rather than MCP. The direction rule leads, because "we fixed the prompt rather than the schema" is the non-obvious call this document asked to put first.
>
> **The routing numbers are on the site, dated and sourced.** `Recorded 2026-08-08 from a full run of 01_langgraph_agent.ipynb, against SUPERVISOR_PROMPT in Lab_5_LangGraph_Agent/tools.py as it stands today`, with the note that they go stale when someone edits the prompt and not before. 2026-08-08 is the date the numbers landed in the repository, which is the only date the history actually supports: the repository was squashed to a single `first pass` commit on that day and the run itself is undated. Say so if a more precise date is wanted.
>
> **`appendix-a.adoc` written**, and the tier statement is the first thing on the page, as a `WARNING` admonition rather than a paragraph. It says plainly that nobody in the room can run it, that the appendix is take-home, and that the concepts are still taught. The dependency chain, the projection concept and the feature-loop-back-to-Databricks argument are all on it.
>
> **Nav and the lab table.** `nav.adoc` gains Lab 5 under Labs and Appendix A as a top-level entry. `workshop-overview.adoc`'s lab table gains three rows: Lab 5 and Appendix A as xrefs, Lab 6 as plain text until its page exists.
>
> **One thing this document asked for and did not get: the Lab 5/6 bullets in `What You Will Learn` are still plain text.** So are the Lab 1 through 4 bullets, which set that pattern before step 8 arrived. Making only 5 and 6 into links would read as an accident. The table directly below them is the xref surface. Change all six or none.
>
> **`Lab_5_LangGraph_Agent/README.md` cut from 250 lines to 88**, and it changed job as decided. It is module documentation now: what `tools.py` and `agent.py` export, why `GRAPH_SCHEMA` is hand-written rather than generated, the four `OperatingLimit` rules a maintainer needs, why `FleetOpsAgent`'s two names cannot be renamed, and the sibling-folder import constraint. Everything conceptual moved to `lab5.adoc` and the README links to it, including a deep link to the routing table.
>
> **`Lab_6_Agent_Memory/README.md` is unshrunk, deliberately.** Step 5 deferred it here because its conceptual half had no destination. `lab6.adoc` is still gated, so it still has none. Shrinking it now would delete the material rather than move it. **Both jobs unblock together.**
>
> **What Lab 6 still owes, once the step 0 probe passes:** `lab6.adoc`, its nav entry, the xref at the end of `lab5.adoc` (plain text today), the `Lab 6` row in the `workshop-overview.adoc` lab table (plain text today), and the README shrink. Nothing else in step 8 is waiting on it.
>
> **Verified.** `npm run build` in `site/`, clean, three times across the step. `lab5.html` and `appendix-a.html` both publish, and the README's deep link was checked against the generated anchor id rather than guessed.
> **STATUS: review pass over steps 1 through 8. Seven defects found and fixed.**
>
> A full read of every changed surface: site pages, `nav.adoc`, the slides, the root and per-lab READMEs, the touched notebooks, and the deploy workflow.
>
> **Clean.** Every `image::`, every `xref:`, and every notebook `raw.githubusercontent.com` URL resolves. No orphaned images. No dangling reference to any deleted page, README, `PART_A.md`, `Aura_Free_Trial.md` or root diagram outside `worklog/`. `npm run build` in `site/` is warning-free. The workflow builds the slides before Antora and `site/.gitignore` excludes the output, so the two halves agree. Lab 1's tier statements agree across page, notebook and deck. `tools.py` exports every name the Lab 5 README claims.
>
> **Fixed.**
> - **`04_genie_agent.ipynb` contradicted itself on the telemetry grain.** The step 7 no-counts edit made cell `step1-header` say `Hourly-scale`, while cell `explore-readings` says 155,520 rows and cells `step3-instructions` and `partb-genie-subagent` both say every 4 hours. Those last two are Genie prompt text, where the grain is load-bearing. Reverted to `Telemetry every 4 hours over 90 days`. **The no-counts rule stops at a prompt block.** The site and slides keep the hedged wording, which is the split the rule intends.
> - **`Lab_5_LangGraph_Agent/README.md` named the wrong file.** It said Lab 6's `memory.py` subclasses `FleetOpsAgent`. `memory.py` imports only `data_utils` and `tools`. The subclass is in `memory_agent.py`, which `01_agent_memory.ipynb` writes out with `%%writefile`. Claim inherited from the old README and re-asserted in the rewrite.
> - **`lab5.adoc` overclaimed on credentials.** `No plaintext password appears anywhere in Lab 5` is false on the documented recovery path: notebook 01 carries a commented-out fallback cell. Scoped to the normal path and the fallback named.
> - **Lab 4's duration disagreed.** Root README 30 + 10 = 40, `workshop-overview.adoc` 75, the notebook 30 + 20 = 50, `PART_B.md` 20. **Ryan's answer: 40.** The site row is now 40 and Part B is 10 in both notebook cells and in `PART_B.md`. The 20-minute figure was the instructor demo's own runtime estimate, so **check it against a real run before class.**
> - **The Aura instance table omitted Appendix A**, the one entry that needs an instance the participant does not have. Row added.
> - **`site/README.md` undercounted the slide build.** It said two output directories and named them without their `slides/` prefix; `build:assets` writes a third. Now three, correctly pathed, pointing at the section that explains the odd one. `Two consumers, one directory` also headed a three-row table.
> - **`appendix-a.adoc` said `most` of `gds-exploring.md` is ordinary Cypher.** Actual: 20 of 35 blocks plain, 15 call `gds.`. Now `many`.
>
> **Two paths in this document went stale under it.** `agenda.md` was deleted and now lives at `worklog/agenda.md`; steps 9 and 10 below still cite the old path. `expand-v2.md`, whose false claim started this work, was deleted too, and the claim does not reappear in `expand-v3.md`.
>
> **New Aura Agents leftovers**, beyond the list already left for step 10: `agent_samples.py:1` and `main.py:506` docstrings. Cosmetic, in an admin CLI.
9. **Write the three new decks:** LangGraph supervisor, deployment, agent memory. Two agent decks, not one, matching Lab 5's two notebooks.

> **STATUS, step 9: done.** Three decks written, one agent each, in parallel.
>
> - **`slides/agents/03-langgraph-supervisor-slides.md`**, 16 slides. Carries the direction rule and the never-substitute-a-limit-for-a-measurement rule as slides of their own, since both are prompt fixes a participant has to recognise before they can debug their own routing. Draws the topology from `site/modules/ROOT/images/lab5-agent-topology.svg` rather than redrawing it in ASCII.
> - **`slides/agents/04-deploy-the-agent-slides.md`**, 11 slides. The identity argument sits on slides 2 and 3 so it survives the deck being cut from the back, which is what happens when Lab 5 runs long.
> - **`slides/agents/05-agent-memory-slides.md`**, title slide plus 9, 16.5 minutes. 2026 taxonomy throughout, as decided above.
>
> **Two things the design above got wrong, found while writing.**
>
> - **`slides/images/graph_mem.jpg` is not unused.** The inventory calls it orphaned; `genai-foundations/04-context-and-rag-slides.md:144` already uses it. Deck 05 uses it too, which is fine, but it was never a free image.
> - **Slide 8's three ranked queries are not in `02_instructor_demos.ipynb`.** They live in `Lab_6_Agent_Memory/memory.py` and run from Section 6 of `01_agent_memory.ipynb`. Anyone demoing that slide should open notebook 01, not notebook 02.

10. **Split and publish the remaining decks**, Workshop against Additional Background. **This is where the slides nav group lands**, along with the remaining `.adoc` wrappers. Three exist already under `site/modules/ROOT/pages/slides/` and are unreachable; the rest copy their `iframe` pattern. `governance/auth-sync-slides.md` needs its source rebuilt to HTML first, since it is PDF-only.

> **STATUS, step 10: done. 24 decks published, all reachable.**
>
> **The split, by `git mv`.** `slides/governance/` to `slides/background/governance/`. Three of the five `kg-construction` decks to `slides/background/kg-construction/`: `05-building-knowledge-graphs`, `06-schema-design`, `08-entity-resolution`. `07-chunking` and `09-vectors` stayed, as decided. One casualty: `background/governance/auth-sync-slides.md:183` reached an image with `../` and now sits a directory deeper, so it needed a second `..`.
>
> **The build was rewritten, and that was the real work.** The old `build:decks` and `build:assets` one-liners named topic folders and individual image files by hand, which is how the site ended up serving decks whose source folder no longer existed. They are replaced by `slides/build-slides.sh`, run through `npm run build:html`. It clears `site/modules/ROOT/attachments/` first, builds each workshop topic folder, then passes `background/` whole and lets Marp recurse. It copies four asset roots rather than four files, so adding an image to a deck cannot silently ship a broken link. The header comments carry the two rules that make the paths look wrong: Marp copies a relative image path verbatim and never copies the file, and background decks emit one level deeper than workshop decks.
>
> **`auth-sync-slides.md` was not PDF-only.** The claim above is stale. It is ordinary Marp source and builds to HTML with everything else.
>
> **Wrappers.** The three under `site/modules/ROOT/pages/slides/` were deleted, not repaired: all three pointed at retired `databricks-in-depth/` attachment paths and one carried an em-dash. 24 replaced them, one per deck, generated from the same 6-line `iframe` template with each title taken from its deck's H1.
>
> **Nav.** `site/nav.adoc` gained a `Slides` group with six subgroups matching the topic folders, and an `Additional Background` group at the bottom with the four Background decks. Workshop decks stay under Slides; nothing was hidden.
>
> **Verified.** `npm run build:html` emits 24 HTML decks. A link check across the emitted HTML finds 17 local asset references, all resolving, counting CSS `url()` backgrounds as well as `src=` and `href=`, because Marp writes background images as the former and a naive checker misses them. `npm run build` in `site/` is warning-free and produces 24 wrapper pages whose `iframe` targets all resolve.
>
> **Left alone.** `fix-site-slides.md:162` still cites `slides/kg-construction/05-building-knowledge-graphs-slides.md`, the pre-split path. This document uses pre-split paths throughout, so repointing one line would make it inconsistent with itself. `slides/docs/` is still excluded from the build and still unconfirmed.

**Gates the last step, not the whole plan:** `02_instructor_demos.ipynb` needs its `course.env` entry before the memory deck can rely on slides 5 and 8.

**Blocks step 8 alone:** the AuraDB Free index-cap check from step 0. Do not publish `lab6.adoc` promising the lab works until it passes.
