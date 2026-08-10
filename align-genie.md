# align-genie.md

Generic "Genie" in the site should be **Genie Agent** where it names the product object you build and call. Bare "Genie" is fine only where it means the model behavior inside that agent ("Genie generates SQL", "Genie marks the response as Trusted") or the wider Genie family.

## Background from the web

- Databricks renamed **Genie Spaces** to **Genie Agents** (docs: "Genie Agents were formerly known as Genie Spaces"). Rename posted in the AI/BI 2026 release notes, Feb 18 2026 entries.
- "Genie Agents are part of the Genie family": **Genie Agents** (curated NL-to-SQL over UC datasets), **Genie One** (single chat surface for business users across data, dashboards, apps), **Genie Code** (dev assistant for code, pipelines, dashboards).
- Docs moved from `/genie/` to `/genie-agents/`. Release notes page is now "AI/BI and Genie One release notes".
- Old names still in the wild: "Genie Space", "AI/BI Genie", "Genie AI/BI". Treat all three as legacy.
- Guidance from practitioners: write "Genie Agents (formerly Genie Spaces)" on first mention for a while.

## Main places to update

### site/modules/ROOT/pages/lab4.adoc

- `:57` heading `=== Genie` -> `=== Genie Agents`. This is the concept section for the product, and the section right below it is `=== Agent Bricks`.
- `:59` "Genie specializes in one problem" -> "A **Genie Agent** specializes in one problem". First mention in the section, so add "(formerly Genie Spaces)".
- `:61` collapsible title `.How Genie works` -> `.How a Genie Agent works`.
- `:64` "Genie operates as a compound AI system" -> "a Genie Agent operates as a compound AI system".
- `:66` "Genie draws its context from Unity Catalog metadata" -> "A Genie Agent draws its context". Keep "Genie marks the response as **Trusted**" as is.
- `:68` "Genie also provides a **Knowledge Store**" -> "Genie Agents also provide a **Knowledge Store**".
- `:101` "teach Genie the aircraft terminology" -> "teach the agent the aircraft terminology".
- `:103` `.How Genie handles a sensor question` -> `.How the Genie Agent handles a sensor question`.
- `:161`-`:163` routing table, tool column reads `Genie` three times -> `Genie Agent`. This table is the one participants read as the routing contract, so the product name matters most here.

### site/modules/ROOT/pages/databricks-platform.adoc

- `:98` "or through Genie" -> "or through a Genie Agent".
- `:103` ASCII diagram row `BI tools (Power BI, Tableau) / Genie / notebooks` -> `... / Genie Agents / notebooks`.
- `:135` "Genie can answer questions about them" -> "a Genie Agent can answer questions about them".
- `:159` "The **Genie agent** translates natural language into SQL" -> "Genie Agent", capitalized, and "aggregations and trends go to Genie" -> "go to the Genie Agent". Lowercase "agent" here reads as a generic agent, not the product.
- `:161` image alt text "routes between Genie and the Neo4j MCP agent" -> "between the Genie Agent and the Neo4j MCP agent".
- `:208` bullet starts `* **Genie** translates natural language` -> `* **Genie Agents** translate natural language`. Same bullet then says "Domain experts configure Genie Agents with...", so the bold lead-in is the inconsistent part. Later in the bullet, "questions ... route to Genie, which generates SQL" -> "route to the Genie Agent".
- `:211` "the hands-on implementation of Genie" -> "of the Genie Agent".
- `:233` link `https://docs.databricks.com/en/genie/index.html[Databricks Genie]` -> `https://docs.databricks.com/aws/en/genie-agents/[Genie Agents]`. The old `/genie/` paths still resolve (200, no redirect to `/genie-agents/`), so this is a name fix, not a broken link.

### site/modules/ROOT/pages/index.adoc

- `:105` table row `Compound AI Agents: Genie + Supervisor` -> `Compound AI Agents: Genie Agent + Supervisor`.
- `:136` `None. Genie queries Unity Catalog` -> `None. The Genie Agent queries Unity Catalog`.
- `:160` tech table row `| **Genie**` -> `| **Genie Agent**`.
- `:214` link `https://docs.databricks.com/aws/en/genie/[Genie]` -> `https://docs.databricks.com/aws/en/genie-agents/[Genie Agents]`.
- `:61` "over Genie, your own graph and the Lab 3 retrievers" -> "over your Genie Agent, your own graph...".

### site/modules/ROOT/pages/part3-agents.adoc

- `:19` table row `Compound AI Agents: Genie + Supervisor` -> `Genie Agent + Supervisor`. Must match the same row in `index.adoc:105`.

### site/modules/ROOT/pages/glossary.adoc

- `:36` "sensor trend questions route to Genie and not to Cypher" -> "route to the Genie Agent".
- `:160` "reached through Genie in Lab 4" -> "reached through the Genie Agent in Lab 4".
- No glossary entry for Genie Agent exists. Worth adding one, defining it and noting the former name, since the glossary already defines the other workshop nouns.

### site/modules/ROOT/pages/lab2.adoc

- `:145` already says "a Genie Agent". No change.

### Already correct, leave alone

- `lab5.adoc` and `lab6.adoc` say "Genie Agent" and "your Genie Agent" throughout. `lab5.adoc:132` "Genie named the engines" is behavior, not the product object, so it can stay.
- `production-path.adoc:58` says "The Genie Agent". No change.
- `lab4.adoc:92`, `:149` already say "Genie Agents" for the subagent type.

## Audit: slides/ and 04_genie_agent.ipynb

Same rule as above. "Genie Agent" for the product object, bare "Genie" only for behavior.

Two clean results first:

- **No legacy naming anywhere in the repo.** `grep -rni "genie space\|genie spaces\|ai/bi genie\|genie ai/bi"` returns nothing. The only `GenieSpace` string is `DatabricksGenieSpace` in `overview-agent/01-supervisor-agent-slides.md:282`, which is the real MLflow resource class. **Do not change it.** `Lab_5_LangGraph_Agent/agent.py:188` already carries a comment saying the API keyword stayed `genie_space_id` while the product renamed.
- **`slides/databricks-in-depth/intelligence-platform-flow.{svg,excalidraw}` already say "Genie Agent (SQL)".** No change. `organize.md:507` records the svg as orphaned anyway.

### 04_genie_agent.ipynb: clean, no changes needed

23 mentions across 10 markdown cells, all already correct. Every product reference says "Genie Agent", including the section headings (`## Step 2: Create the Genie Agent`, `## Step 4: Test the Genie Agent`) and the UI label at cell 12 (`Click **Genie Agents** in the left sidebar`), which matches the current sidebar. The bare "Genie" uses are all behavior: "Genie writes plausible SQL", "Genie walks that chain", "Genie answers *how much*", "the query Genie wrote".

One optional: cell 0 prerequisite "A Databricks workspace with Genie access". "Genie access" reads as the workspace entitlement rather than the object, so it is defensible as is.

### Slides that need changes

All nine files below ship. `build-slides.sh:29` builds the eight `overview-*` topics, and passes `background/` whole, so `background/agents/` and `background/graph-ml/` build too and are reachable from `nav.adoc:28` and `:33` under Additional Background.

**`background/agents/02-power-of-graphrag-slides.md`** is the worst of them, and the direct parallel to the `lab4.adoc` heading already fixed.

- `:267` heading `## Databricks Genie: Natural Language to SQL` -> `## Databricks Genie Agents: Natural Language to SQL`.
- `:276` "Genie is not a single LLM. It's a compound AI system" -> "A Genie Agent is not a single LLM".
- `:279` "Genie queries any data registered in Unity Catalog" -> "A Genie Agent queries any data".
- `:282` "the metadata that makes Genie smart" -> "makes a Genie Agent smart".
- `:309` "Just as Genie is purpose-built for SQL" -> "Just as a Genie Agent is purpose-built".
- `:413` "**Agent layer:** Genie (SQL) + Neo4j MCP (Cypher)" -> "Genie Agent (SQL)".
- `:426` "Genie for SQL, the Neo4j MCP agent for Cypher" -> "the Genie Agent for SQL".
- Leave `:289`, `:291`, `:294` (behavior). `:287` and the `:394` diagram already say Genie Agent.

**`overview-mcp/01-mcp-agent-bricks-slides.md`** carries the lowercase-`agent` bug fixed in `databricks-platform.adoc:159`, three times.

- `:201`, `:217`, `:235` "the Genie agent" -> "the Genie Agent". `:217` and `:235` are bold on the slide face, so the casing is visible to the room.
- `:162` "Genie is the agent participants already built in Lab 4 Part A" -> "The Genie Agent is the one participants already built".
- `:242` "exactly two subagents, Genie and the Neo4j MCP agent" -> "the Genie Agent and the Neo4j MCP agent".
- `:273` comparison table, both cells: "Genie and the Neo4j MCP agent" and "Genie, Cypher over your own Aura" -> "Genie Agent". This table is the deck's summary slide.
- Heading `:154` and `:253` already correct.

**`background/graph-ml/04-future-graph-enrichment-slides.md`** (financial-services narrative, not aircraft).

- `:255` bullet `- **Genie:** translates natural language into SQL` -> `- **Genie Agent:**`. Same bold lead-in pattern as `databricks-platform.adoc:208`.
- `:659` bullet `- **Genie** queries Delta tables` -> `- **Genie Agent** queries`.
- `:241`, `:264`, `:274`, `:650`, `:666` bare "Genie" in speaker notes -> "the Genie Agent".
- `:195` "Genie queries the extracted Delta tables" -> "the Genie Agent queries".
- Leave `:253` "the Genie endpoint", which means the serving endpoint. `:229` diagram already says Genie Agent.

**`overview-platform/01-neo4j-databricks-slides.md`**

- `:76` comparison table cell "Foundation Models, Genie" -> "Foundation Models, Genie Agents".
- `:165` bullet `- **Genie over Delta:**` -> `- **Genie Agent over Delta:**`.
- `:92` speaker note "Genie appears once, in the AI capability row" -> "Genie Agents appear once". The note is instruction to the presenter and should name the row correctly.

**`background/connectors/09-neo4j-connectors-slides.md`**

- `:51` and `:65` "Power BI, Tableau and Genie" -> "Power BI, Tableau and Genie Agents". Matches the `databricks-platform.adoc:103` diagram fix, and `:51` is on the slide face.

**`background/governance/auth-sync-slides.md`**

- `:97` bullet `- **Genie natural language queries:**` -> `- **Genie Agent natural language queries:**`.

**`overview-graphrag/01-graphrag-retrieval-slides.md`**

- `:425` speaker note "several retrieval patterns plus Genie" -> "plus the Genie Agent". `:419` already correct.

**`overview-agent/01-supervisor-agent-slides.md`**

- `:104` speaker note "every measurement question routes to Genie" -> "routes to the Genie Agent".
- Leave `:199` "**Genie** named the engines", a result narration parallel to "**The graph**" and "**The manual**". Leave `:282` `DatabricksGenieSpace`. `:79`, `:98`, `:284`, `:339` already correct.

### Judgment calls I would leave alone

- **Three-way shorthand next to Cypher and GraphRAG.** `overview-architecture:41`, `:48`, `:175` and `overview-business-story:172` read "across Genie, Cypher, and GraphRAG". The other two items are a query language and a retrieval pattern, not products, so "Genie" here is the parallel shorthand for the tool node, not a product name. Both decks already say "Genie Agent" where they name the thing built (`overview-architecture:40`, `:171`, `overview-business-story:135`).
- **`overview-agent-memory:204`, `:208`** "reaches Genie as `N10011`", "hands the word 'that' to Genie". Describes what a tool call carries. Behavior.
- **`slides/organize.md`**, 15 mentions. A planning and inventory doc, same category as this file and `expand.md`. Not built by `build-slides.sh` and not published. Updating it would edit a record of intent.

## Audit: OPTIONAL_COMPOUND_AGENT_DEMO.md, README files, images

Same rule as the two rounds above. Product name where the text names the thing;
bare "Genie" where it names behavior or an identifier.

### `Lab_4_Compound_AI_Agents/OPTIONAL_COMPOUND_AGENT_DEMO.md`

15 mentions, 11 already correct. Four to change:

- `:1` title `# Optional: Compound AI Agent over Genie and Neo4j MCP` -> `over the Genie Agent and Neo4j MCP`.
- `:5` "It takes the Genie agent you built in the lab" -> "the Genie Agent you built". Lowercase `agent` in a product name.
- `:155` heading `### 4.2 Configure the Genie subagent` -> `Configure the Genie Agent subagent`. Debatable: "Genie subagent" is arguably a role, not a product name, and `:145` and `:146` already say "Genie Agent" three lines up.
- `:407` bullet `- **Genie plus Lakehouse for time-series data.**` -> `- **Genie Agent plus Lakehouse for time-series data.**`. A takeaways bullet naming the product.

Already correct and untouched: `:11`, `:20`, `:141`, `:143`, `:145` (the literal UI label "click **Genie Agent**"), `:146`, `:213`, `:360`, `:420`, `:437`, `:441`.

### `workshop-setup/README.md`

- `:342` troubleshooting heading `**Genie answers plausibly rather than correctly**` -> `**The Genie Agent answers plausibly rather than correctly**`. `:14` in the same file already says "a Genie Agent that answered plausibly", so the two drifted apart.
- `:398` link `[Databricks Genie](https://docs.databricks.com/en/genie/index.html)` -> `[Genie Agents](https://docs.databricks.com/aws/en/genie-agents/)`. Same fix already applied at `databricks-platform.adoc:233`. The old path still resolves; this is a name fix.
- Leave `:265` "debugging the Genie comments". Internal shorthand for the table `COMMENT` DDL, and the sentence's subject is the `genie` CLI subcommand.

### `workshop-setup/docs/MANUAL_SETUP.md`

- `:40` "the summaries Lab 4 asks Genie about" -> "asks the Genie Agent about". `:33` and `:42` already correct.

### `workshop-setup/populate_aircraft_db/README.md`

- `:186` "a question about a measured value routes to Genie rather" -> "routes to the Genie Agent rather".

### `workshop-setup/populate_aircraft_db/DATA_GENERATOR.md`

- `:98` "for SQL analytics and Genie natural language queries" -> "and Genie Agent natural language queries".
- `:125` table cell `| Genie queries Delta tables |` -> `| The Genie Agent queries Delta tables |`.
- Leave `:77` "Genie queries over the readings surface", `:189` "the gold tables Genie reads", `:198` "lets Genie answer questions like". All three describe what the model does at query time, not the object you create.

### `vocareum/docs/README.md`

- `:19` table cell "Genie and Agent Bricks, guided by a notebook" -> "Genie Agents and Agent Bricks". Parallel to the product name next to it.
- Leave `:35` "**Genie node**", a LangGraph node name matching `build_genie_node`. `:42`, `:75`, `:102` already correct.

### Images

Two published SVGs carry a bare "Genie" label. These are decisions for you, not
obvious fixes.

- **`site/modules/ROOT/images/graphrag-multiplatform-retrieval.svg`** has the visible label `Genie (SQL)`. Hand-authored SVG, so a one-word text edit is safe. It is now out of sync with `background/agents/02-power-of-graphrag-slides.md:413`, which this round changed to "Genie Agent (SQL)". Referenced at `databricks-platform.adoc:161`, whose alt text is already updated. **I would change this one.**
- **`site/modules/ROOT/images/dual-database-architecture.svg`** has "Natural language queries via Genie" inside the Databricks box. Behavior phrasing, so it is defensible as-is. It is also Excalidraw-exported, source at `images/dual-database-architecture.excalidraw`, so a correct fix means editing both files; and `slides/organize.md:498` records this asset was deliberately left alone despite other stale content. It ships as a full-bleed background at `overview-platform/01-neo4j-databricks-slides.md:58` and on the site index. **I would leave this one.**

`images/workshop-infrastructure.{svg,excalidraw}` already read "Genie Agent + Neo4j MCP Agent". No change.

### Code comments and docstrings

Bare "Genie" in non-published Python and shell comments. Lower priority, and
none of it is participant-facing text: `Lab_5_LangGraph_Agent/tools.py:5`,
`:244`, `:293`; `Lab_5_LangGraph_Agent/agent.py:14`, `:165`;
`Lab_6_Agent_Memory/memory.py:1405`, `:1505`; `lab/workshop.py:271`, `:423`,
`:439`; `lab/courseware/dlt_fleet_etl.py:6`, `:52`, `:300`, `:309`, `:482`,
`:493`; `lab/workspace_init.sh:129`, `:141`; `lab/course.env:117`;
`workshop-setup/auto_scripts/sync_notebooks.py:6`.

### Identifiers, never change

The `genie` CLI subcommand, `genie_statements()`, `provision_genie`,
`genie_node`, `build_genie_node`, `DatabricksGenieSpace`, `genie_space_id`.

### Clean, no changes needed

`Lab_5_LangGraph_Agent/README.md`, root `README.md`, `lab/README.md`,
`workshop-setup/auto_scripts/README.md`, `vocareum/SETUP_GUIDE.md`, `CLAUDE.md`,
`Lab_3_Semantic_Search/data_utils.py`,
`workshop-setup/auto_scripts/workshop_module.py`.

### Excluded

`worklog/*` (historical records) and `.venv/` (dependencies).
