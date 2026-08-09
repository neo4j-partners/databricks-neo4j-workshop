# Lab 6 - Agent Memory

The Lab 5 agent answers one question at a time. Ask it a follow-up and it has
forgotten the question before it. This lab gives it a memory, and puts that
memory in the same database the fleet already lives in.

That last part is the whole lab. Memory nodes and fleet nodes land in one Aura
instance, so a single Cypher query can ask something neither half can answer on
its own: which aircraft are the technicians worried about, and are those the
ones actually failing?

> **Infrastructure:** This lab writes to your **personal** Aura instance, the
> one you loaded in Lab 2 and enriched in Lab 3. It is the first lab that
> writes. Everything it writes is removable, and Section 11 says how.

## Prerequisites

| Lab | What this lab needs from it | Required |
|---|---|---|
| [Lab 2](../Lab_2_Databricks_ETL_Neo4j) | `Aircraft` nodes in your Aura instance, with `tail_number`. The memory library adopts them | Yes |
| [Lab 3 notebook 01](../Lab_3_Semantic_Search/01_data_and_embeddings.ipynb) | The `fleet-ops-<your-user>` secret scope, and `data_utils.py` beside it on disk | Yes |
| [Lab 5](../Lab_5_LangGraph_Agent) | `tools.py` and `agent.py`, and the Model Serving endpoint you deployed | Yes |
| [Lab 4 Part A](../Lab_4_Compound_AI_Agents/PART_A.md) | Your Genie space ID, for the `genie_node` the memory agent keeps | Yes |

`memory.py` imports from both `../Lab_3_Semantic_Search/data_utils.py` and
`../Lab_5_LangGraph_Agent/tools.py`. Keep the three lab folders as siblings, in
the repository and in the workspace, and `ensure_labs_on_path()` resolves the
imports on its own.

## Files

| File | What it is |
|---|---|
| `01_agent_memory.ipynb` | The 75 minute hands-on path. Adopt, seed, run the headline query, wire recall and remember, measure, redeploy |
| `02_instructor_demos.ipynb` | Four run-and-read demos. Not on the participant path |
| `memory.py` | The Databricks adapters, the recall and remember nodes, the seed helper, and the headline Cypher |

`memory.py` is lab-provided code, not an exercise, for the same reason
`tools.py` is in Lab 5. Writing an async embedding adapter is not what anyone
came for.

### Why the adapters are named `MemoryEmbeddings` and `MemoryLLM`

`DatabricksEmbeddings` and `DatabricksLLM` already exist, in
`Lab_3_Semantic_Search/data_utils.py`. Those implement neo4j-graphrag's
synchronous `Embedder` and `LLMInterface`. `neo4j-agent-memory` wants a
different thing: async Protocols, `embed` and `embed_one` on the embedder,
`complete` and `complete_structured` on the LLM. Two libraries, two sets of
Protocols, four classes, and the names have to differ or the second import
silently shadows the first.

## What you build

```
                    question
                       |
                       v
              +------------------+
              |     recall       |   <-- new
              | search memory,   |
              | put hits in the  |
              | supervisor prompt|
              +------------------+
                       |
                       v
              +------------------+
              |    supervisor    |<---------+
              +------------------+          |
                       |                    |
        +--------------+--------------+     |
        v              v              v     |
    genie_node    cypher_node   graphrag_node
        |              |              |     |
        +--------------+--------------+-----+
                       |
                       v
                  synthesize
                       |
                       v
              +------------------+
              |    remember      |   <-- new
              | write the turn   |
              | with EntityRefs  |
              +------------------+
                       |
                       v
                    answer
```

Two new nodes on either side of the Lab 5 graph. The three tools are untouched.
The supervisor is the same node with a memory preamble in front of its prompt,
`MEMORY_SUPERVISOR_PROMPT` in `memory.py`, which is Lab 5's prompt with a
`{recalled}` block prepended. That is the entire code delta between the two
labs' agents.

## The headline query

The lab seeds ten messages from five technicians across five shifts, then runs
one Cypher query that touches both halves of the graph.

Ranked by the fleet's own severity data, `N10011` comes **last of six**:

```
N10004 events=23 critical=17
N10021 events=23 critical=16
N10020 events=22 critical=13
N10027 events=18 critical=13
N10000 events=18 critical=12
N10011 events=21 critical=11
```

Ranked by how much attention the technicians gave it, `N10011` is **joint
first**:

```
N10011 technicians=3 mentions=3
N10004 technicians=3 mentions=3
N10021 technicians=2 mentions=2
N10027 technicians=1 mentions=1
N10020 technicians=1 mentions=1
```

Three technicians on three shifts each pulled the EGT trend on `N10011`, none
of them knowing the others had, on an aircraft the severity model puts at the
bottom of the page. The inverse reads just as well: `N10020` and `N10027`
carry 13 critical events each and one technician apiece has looked at them.

The query binds `ac` in the memory half and reuses the same node in the fleet
half. No join key, no federation, no second query. It runs in 0.6 to 0.7
seconds. Section 6 of the notebook runs the two halves separately first, so the
contrast is something the participant produces rather than reads about.

## Adopt `Aircraft`, and nothing else

`client.schema.adopt_existing_graph()` makes existing nodes into memory
entities. It also sets `type` unconditionally, which is destructive on any
label whose `type` property already means something.

| Label | Nodes | What adopting it would destroy |
|---|---|---|
| `System` | 144 | `type` is the system category Lab 2 and Lab 4 filter on |
| `Component` | 612 | `type` is the component class |
| `Sensor` | 288 | `type` is the sensor kind, joined to `OperatingLimit` |
| `Document` | 5 | `type` is the manual category |

`Aircraft` has no `type` property, so adopting it costs nothing, and the
headline query needs `Aircraft` and nothing else. `memory.py` refuses the other
four by name rather than trusting the notebook to get it right. Section 4 shows
the refusal, on purpose, before it shows the successful adoption.

Run the dry run first. `adopt_existing_graph(dry_run=True)` returns an
`AdoptionReport` and writes nothing.

## Explicit mentions

Every memory write in this lab passes `extraction_mode="explicit"` with a list
of `EntityRef`. Two reasons, and the second is the one that generalizes.

**It is the mode that works.** Released 0.5.0 silently drops every `MENTIONS`
edge under automatic extraction, which is the exact edge the headline query
traverses. Details are under "The pinned version" below. The fork fixes it, and
explicit mode stays the recommendation anyway.

**It is the better production pattern.** An agent normally knows which entities
its tools touched. Paying an LLM to rediscover them from the message text costs
about 3.6 seconds per message and can get them wrong.

`memory.py` extracts tail numbers with a regex, `aircraft_mentions()`, because
a tail number is `N` followed by five digits and a regex is the honest tool for
that. A production system would take the refs from the tool calls themselves.

## Running the lab

1. Open `01_agent_memory.ipynb` on a Databricks cluster or serverless notebook.
2. Set `GENIE_SPACE_ID` in Section 2 to your own space ID.
3. Run the cells in order.

Section 1 installs the wheel and restarts Python. That restart clears every
name in the notebook, so Section 2 runs after it, not before.

Section 10 redeploys **the same Model Serving endpoint** you created in Lab 5,
with the two new nodes in it. One endpoint per participant across both labs.

### Instructor demos

`02_instructor_demos.ipynb` is run-and-read. Four demos, each standalone after
the shared setup cell, so an instructor short on time can run one.

| Demo | The question it answers | Minutes |
|---|---|---|
| 1. Correction | When a technician says "no, it was the *left* engine", what happens to what the agent already believed? | 6 |
| 2. Learned preferences | Can the agent remember *how* someone likes to be answered? | 5 |
| 3. Shift handoff | Can it brief the incoming shift on what the outgoing shift was worried about? | 6 |
| 4. Routing memory | Can the agent remember which tool worked last time? | 8 |

Demo 3 reads the shift history `01_agent_memory.ipynb` seeds, and Demo 4's
audit query resolves only because notebook 01 adopted the `Aircraft` nodes.
Run notebook 01 first.

Demo 4 is the one to run if there is time for one. It turns routing from a
fixed prompt into something that improves with use, and its closing query walks
from an aircraft back through tool calls to the reasoning that produced them.

## The pinned version

`neo4j-agent-memory` is a `neo4j-labs` project, which means a pre-1.0 API and
no compatibility promise. A notebook that installs the latest version can break
between the dry run and delivery day without a line of workshop code changing,
and it breaks in a room, live. Four answers, from the 2026-08-08 spike.

### Exact version

Not PyPI. Released 0.5.0 silently drops `MENTIONS` edges. The package is built
once from the `mentions` branch of the fork
https://github.com/neo4j-partners/agent-memory and distributed as a wheel on
the Unity Catalog volume, the same artifact the cluster and Model Serving both
install:

```
%pip install /Volumes/databricks-neo4j-workshop/aircraft/raw_data/neo4j_agent_memory-0.5.1.dev0+mentions-py3-none-any.whl httpx>=0.27.0
dbutils.library.restartPython()
```

The wheel is checked into `lab/courseware/wheels/` and reaches the volume
through `workshop.py provision-data`. The per-participant cluster installs the
same path already through `VOC_COURSE_LIBRARIES` in `lab/course.env`, so the
notebook line is a safety net for a cluster that predates the library list
rather than the primary install.

`workshop-setup/README.md`, section "The `neo4j-agent-memory` wheel", is the
operational account: how it is built, how to rebuild it, and the Model Serving
trap that follows from the version.

A wheel carries no extras, which is why `httpx` is named separately. The
`[nams]` extra contains exactly one thing, `httpx>=0.27.0`.

The branch bumps `pyproject.toml` to `0.5.1.dev0+mentions`, so `pip list` tells
a patched install from an unpatched one at a glance. The cost of that local
version segment is that it does not resolve from PyPI, so anything pinning by
version alone has to be handed the wheel path explicitly. MLflow's inferred
requirements are the case that matters, and Section 10 passes the path.

The base is released 0.5.0: wheel uploaded 2026-05-30T23:23:11, upstream
repository https://github.com/neo4j-labs/agent-memory, tag `python-v0.5.0`,
source commit `ece2e6ee1c594359381a7066ac05b2219ebf9cfb`, 2026-05-30, William
Lyon. `requires-python >=3.10`.

### API surface this lab depends on

Documented, from the project README: `MemoryClient(settings, extractor=...)` as
an async context manager, `MemorySettings(neo4j=, embedding=, llm=,
schema_config=, extraction=)`, `Neo4jConfig`, `SchemaConfig`,
`SchemaModel.CUSTOM`, `ExtractionConfig`, `ExtractorType.LLM`,
`client.short_term.add_message(...)`, `client.short_term.search_messages(text,
limit=)`, and `client.query.cypher(query, params)`.

Documented in `docs/modules/ROOT/pages/how-to/adopt-existing-graph.adoc`:
`client.schema.adopt_existing_graph(label_to_type=,
name_property_per_label=)`, which also accepts `dry_run=True` and returns an
`AdoptionReport` without writing.

**Docstring only, so these are the ones that move:** `add_message(...,
extraction_mode="explicit", explicit_mentions=[EntityRef(...)])` at
`memory/short_term.py:661`, and `EntityRef` itself, which is not exported at
package root and must be imported from `neo4j_agent_memory.schema.models`.

**Undocumented, read off the source:** the `LLMEntityExtractor` constructor at
`extraction/llm_extractor.py:140`, needed only for a custom
`extraction_prompt`, which `ExtractionConfig` does not expose.

Use `client.query.cypher` from day one. `client.graph.execute_read` emits a
deprecation warning naming v0.6.0 for removal.

`add_messages_batch` takes no `extraction_mode` and no `explicit_mentions`, so
the seed step uses singular `add_message` in a loop. Ten messages, about a
minute. That is the one place in the lab where a loop over memory writes is the
right answer, and it is why the seed is a setup step rather than an exercise.

### Neo4j version floor

5.20, for vector indexes. The spike instance reported `5.27-aura`, enterprise,
Cypher 5 and 25, against Neo4j Python driver 6.2.0. The floor is met with room.

One Neo4j-side wrinkle is cosmetic: `search_messages` emits `db.index.vector.queryNodes
is deprecated. It is replaced by SEARCH.` It works on 5.27-aura, and
participants will see the warning in notebook output.

### Owner and cadence

William Lyon authored 373 of the repository's commits and cut every tag, so he
is the contact for a breaking-change warning. Ryan Knight has 5 commits in the
repository, so the internal channel is open without an introduction. Other
recent contributors: Prakriti Solankey, Andreas Berger, Tomaz Bratanic,
kaustubh-darekar, muddybootscode.

**The cadence is the risk, and it is concrete.** Thirteen PyPI releases between
2026-01-22 and 2026-05-30, about one every eleven days, and the series skipped
0.3 entirely, going 0.2.1 to 0.4.0 in thirteen days. `main` sits **38 commits
ahead of the 0.5.0 tag**, among them `7b2f872 Generic backend-typed
MemoryClient (agnostic Protocols + connect())`, which rewrites the exact
Protocol surface `MemoryEmbeddings` and `MemoryLLM` bind to, plus six commits
titled `Type-safety Phase 1` through `Phase 6` ending with mypy and ty blocking
in CI. Expect the adapters to need work on the next release.

**Pin, and stay pinned.** Treat any upgrade as a code change with its own test
pass, not as a version bump. Set a re-check date alongside the Lab 4 Part B
review date, so both external dependencies get looked at together.

## The upstream defect, and why it matters here

In released 0.5.0, `_extract_and_link_entities` generates a `uuid4`, runs
`MERGE (e:Entity {name, type})` whose `ON MATCH SET` never assigns `e.id`,
discards the `RETURN e`, then links with `MATCH (e:Entity {id: $entity_id})` on
the throwaway uuid. When the `MERGE` matches an existing node, that node keeps
its own id, both `MATCH` clauses fail to bind, and the write is a no-op. No
exception, no warning, no edge.

Two consequences. Every entity adopted from the fleet graph becomes unreachable
from memory, because adoption gives `Aircraft` an id of `aircraft:N10004` and
the uuid never matches it. Every repeat mention of any entity is lost, so only
the message that first creates an entity gets an edge. A ten-message
auto-extraction run dropped all ten tail numbers.

The fix reads the id back from the write with `RETURN e, e.id AS id` and adds
`ON MATCH SET e.id = COALESCE(e.id, $id)`, so the link lands on the node the
`MERGE` actually matched. Three regression tests confirm it, failing without
the fix and passing with it, run live against Aura. It sits on the `mentions`
branch of the fork. Getting it upstream into `neo4j-labs` is tracked separately
and is worth doing whether or not this lab ships.

**A second reason to prefer explicit mode: label collision.** Entities the
library creates take a label derived from their type, so type `SYSTEM` becomes
`:System:Entity` and `COMPONENT` becomes `:Component:Entity`, colliding with
the fleet's own labels. During the auto-extraction run the `System` count went
from 144 to 148 and `Component` from 612 to 613, with names like `Engine`,
`hydraulic` and `turbine`. A `MATCH (s:System)` in Lab 2 or Lab 4 would then
return conversational artifacts alongside real systems.

## Measured numbers

From the Phase 0 spike, against a live Aura instance and live Databricks
Foundation Model endpoints.

| Operation | Time |
|---|---|
| First connect plus schema creation, empty schema | 22.4 s, once per database |
| Adopting 36 `Aircraft` | 3.1 s, `migrated=36 already=0 skipped=0` |
| One `databricks-bge-large-en` embedding call, warm | 1.85 s |
| One short `databricks-meta-llama-3-3-70b-instruct` call, warm | 1.84 s |
| One message, explicit mode | 5.6 s |
| One message, automatic extraction | 9.2 s |
| Ten-message seed | about 56 s |
| The headline query | 0.6 to 0.7 s |
| `search_messages`, three hits | 3.4 to 5.0 s |

The two endpoint latencies set the floor for everything else. They are why the
seed is ten messages and not fifty.

### Graph cost

The memory library creates 33 indexes and 12 constraints on first connect.
Memory itself costs about 20 nodes per participant per session, against roughly
178,000 nodes of headroom on AuraDB Free after Labs 1 through 3.

## What stays in your graph

`01_agent_memory.ipynb` leaves what it wrote in place. Section 11 closes the
client and the driver, and that is all it does. Lab 6 is the last lab, the
seeded history is about 20 nodes, and a participant who wants to keep poking at
the headline query needs those nodes to still be there.

`02_instructor_demos.ipynb` ends with a cleanup cell, because its preferences
and reasoning traces are demo scaffolding rather than something to keep. It is
skippable, and the notebook says so.

Adoption is the one thing no cleanup undoes. It added the `:Entity` label and
`id`, `type` and `name` properties to your 36 `Aircraft` nodes. `Aircraft` had
no `type` of its own, so nothing was overwritten and no query in any lab
changes behaviour. That is the whole reason `Aircraft` was the safe label.

`MemorySession.cypher()` is read-only by design and rejects a write query
before the round trip, so the cleanup cell goes through a plain driver from
`tools.open_driver_from_secrets` instead.
