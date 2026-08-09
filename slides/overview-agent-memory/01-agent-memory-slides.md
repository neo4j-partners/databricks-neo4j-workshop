---
marp: true
theme: default
paginate: true
---

<style>
section {
  --marp-auto-scaling-code: false;
}

li {
  opacity: 1 !important;
  animation: none !important;
  visibility: visible !important;
}

/* Disable all fragment animations */
.marp-fragment {
  opacity: 1 !important;
  visibility: visible !important;
}

ul > li,
ol > li {
  opacity: 1 !important;
}
</style>

# Agent Memory with Neo4j

Giving the Lab 5 supervisor a memory, in the graph it already queries. Lab 6 redeploys that same Model Serving endpoint rather than standing up a second one.

<!--
Thirteen slides, about 19 minutes. Assumes GraphRAG and the Lab 5 supervisor are already taught. Lands on Lab 6's own demo.
Cutting to 15 minutes: fold Hot Path Versus Background Write into the one line already written on recall, then act, then remember, and skip it entirely. Never cut The Payoff, the argument for the whole lab. Memory Has to Handle Being Wrong and Hot Path are the soft middle, most interesting to a practitioner and least connected to what a participant runs; Handle Being Wrong keeps its place because a live demo backs it, Hot Path has none.
-->

---

## What This Covers

- **The amnesiac.** The Lab 5 supervisor holds nothing from the question before
- **The fake fix.** Replaying the transcript costs, distracts, and contradicts itself
- **Three layers, one graph.** Short term, long term, reasoning, beside the fleet
- **Being wrong.** Supersede the old belief, keep it, stamp when it stopped being true
- **recall, act, remember.** Two nodes added, and one query that crosses both halves

<!--
0.5 minutes. Read the five lines, do not explain them. Point at the last one: everything above it is memory the way any product does memory. The last line only works because the memory lives in the fleet graph, and it is where the deck ends up.
Cut order if the day runs late: this slide first, then the Summary slide down to its Next line, then Hot Path, already marked as the cut that brings the deck under its original budget. Never cut The Payoff.
-->

---

## The Agent You Built Is an Amnesiac

![bg right:40% contain](../../site/modules/ROOT/images/lab5-agent-topology.svg)

- **Lab 5 shipped this:** one supervisor, three tools, one endpoint. It routes well and answers well
- **Ask it about `N10011`.** Then ask "any maintenance events on that aircraft?" and it has no idea what *that* means
- **At the start of question two it holds** the question, the schema, and the prompt. Nothing about question one
- **Close the notebook** and everything it worked out is gone

**"Most agents you build today are amnesiacs."**

<!--
1.0 minute. Put the Lab 5 topology back up first. The room built this yesterday or an hour ago, and the point lands harder against work they recognize as good.
Analogy: a contractor whose memory is wiped every time they walk out of the hangar. Brilliant while in the room. You brief them from scratch every morning, and they never notice the thing they saw three days running.
Not a criticism of Lab 5. The supervisor is stateless by construction, and that is the correct default until you decide otherwise on purpose.
-->

---

## The Fake Fix, and Where It Runs Out

- **The obvious move:** stuff the whole transcript back into the prompt every turn
- **Cost.** Every turn pays for every turn before it, forever
- **Distraction.** Context rot: the model's performance drops as the window fills with material unrelated to this question
- **Contradiction.** The wrong answer from Monday and the corrected one from Tuesday sit side by side, and nothing in the window says which won
- **The second obvious move:** dump the transcript into a vector store

**"Your 'memory' is just a pile of text chunks ranked by cosine similarity."**

<!--
1.5 minutes. Context rot was taught in the GenAI foundations deck; one callback sentence is enough, do not re-teach it.
Dwell on the contradiction failure; it sets up Memory Has to Handle Being Wrong. Both statements sit in the window, both are fluent, both name the same aircraft, and retrieval has no principled way to prefer one. The model picks whichever it happened to attend to.
Name the field once: LangGraph's own checkpointers and store are where most people put this first, and mem0, Zep/Graphiti, and Letta are the dedicated products, all solving the same three failures above.
-->

---

## Three Layers, One Graph

![bg right:38% contain](../images/graph_mem.jpg)

- **Short term.** The shift log: this conversation and recent ones, messages, who said them, which entities they mention
- **Long term.** The permanent record: preferences and durable facts that outlive any one session
- **Reasoning.** The mechanic's own notebook of how they worked it out: traces, steps, tool calls, what worked
- **Reasoning memory is the differentiator.** A vector store has nowhere to put "which tool I tried, what it returned, and whether that was the right call"

<!--
2.0 minutes. Not a taxonomy invented for the slide: these are the namespaces the lab calls, client.short_term.add_message, client.long_term.add_preference, client.reasoning.start_trace. The words match memory.py if someone opens it at the break.
Taxonomy conflict, one sentence: Neo4j ships two. The 2025 developer blog, Alex Gilmore, borrows LangGraph's split of short term versus long term, with long term dividing into semantic, episodic, and procedural. The 2026 Labs and hosted-service line uses short term, long term, and reasoning, which is what this deck and Lab 6 use since it is what the code participants run is built on. Cite Gilmore as the cross walk; do not spend a slide arguing it.
Second analogy if wanted: Letta describes its hierarchy as an operating system, core memory as RAM, recall as disk cache, archival as cold storage.
-->

---

![bg contain](../../site/modules/ROOT/images/lab6-memory-graph.svg)

<!--
1.5 minutes. No title on purpose. The picture is full bleed and you are the caption. Walk it in four moves, finger on the screen.
Short term: a User, a Conversation, the Messages inside it, the only layer the participant notebook writes. Long term: the durable record, preferences that supersede one another rather than overwrite. Reasoning: a trace, the steps inside it, the tool calls those steps made. Then the right side, built in Lab 2: Aircraft, Systems, Components, MaintenanceEvents. Color does the grouping; each layer has its own.
Land on the one edge that crosses: MENTIONS, from a Message to an Aircraft. Finger on it: "After adoption that is not a copy of the aircraft. It is the aircraft." One node wearing two labels, :Aircraft and :Entity. That edge is the whole lab. Left of it is memory any product sells you. Right of it is the fleet. The edge is what makes the query on The Payoff slide possible at all.
If short on time: show the picture, say that last sentence, and move on. Thirty seconds.
-->

---

## Why a Graph, in One Query

```cypher
MATCH (:ReasoningTrace)-[:HAS_STEP]->(s:ReasoningStep)-[:USES_TOOL]->(tc:ToolCall)
MATCH (s)-[:TOUCHED]->(ac:Aircraft)
RETURN ac.tail_number AS aircraft, tc.tool_name AS tool,
       tc.status AS status, s.observation AS observation
```

- **Read the path out loud:** a reasoning trace, to the step inside it, to the tool that step called, to the aircraft that call touched
- **The question it answers:** which agent decisions touched this aircraft, and which of them failed
- **`:TOUCHED` hangs off the step**, not the tool call: step to entity for the audit, step to call for the mechanics
- **In a system where traces are log lines and the fleet is a database,** that question is a support ticket

**"Vector stores give you recall; the graph gives you understanding."**

<!--
2.0 minutes. This is the thesis slide. Walk the path with a finger on the screen. Do not read the Cypher as Cypher; read it as a sentence: trace, step, tool call, aircraft.
Verbatim from Demo 4 of Lab_6_Agent_Memory/02_instructor_demos.ipynb. It runs; that is the notebook to open if the room wants proof.
The caveat that returns on The Payoff: that last MATCH only resolves because the lab adopted the fleet's Aircraft nodes. Without adoption the memory library creates its own N10011 Entity beside yours, the pattern matches nothing, and you are back to two stores joined by string comparison in Python.
-->

---

## Memory Has to Handle Being Wrong

- **mem0.** v2 had an LLM decide ADD, UPDATE, or DELETE per fact. That proved fragile, so v3 went ADD-only and pushed contradiction into retrieval ranking instead
- **Zep and Graphiti.** Invalidate bi-temporally and never discard anything
- **Lab 6.** Supersedes: an edge from old to new, and the old one's `valid_until` stamped with the moment it stopped being true

```cypher
MATCH (old:Preference)-[:SUPERSEDED_BY]->(new:Preference)
RETURN old.preference AS superseded,
       old.valid_until AS stopped_being_true,
       new.preference  AS replacement
```

- **State Clock versus Event Clock:** what is true now, against what happened, when, and why

<!--
2.0 minutes. A live demo backs this one, which is why it survives a shortened day when Hot Path does not.
Demo beat, Demo 1 of 02_instructor_demos.ipynb, run it or narrate it. Monday: add_preference says the EGT exceedance on N10004 is on the number two engine. Tuesday: the borescope says otherwise; a second preference says number ONE engine, then supersede_preference(old, new). get_preferences_for(active_only=True) now returns the number ONE engine, what the agent believes now; the same call with active_only=False, as_of=BEFORE_CORRECTION returns the number two engine, what it believed on Monday.
Nothing was deleted. The wrong answer is still attached to the aircraft and to the technician who gave it, stamped with the moment it stopped being true. An audit can reconstruct exactly what the agent knew at any point; delete the row instead and the agent cannot explain itself in an incident review.
Do not pitch this as Neo4j beating mem0. Three live systems made three defensible calls. Handling being wrong is a design decision you have to make, not a feature you get.
-->

---

## Hot Path Versus Background Write

- **Two choices, and only two.** Write during the turn and pay the latency, or write after the turn and accept staleness
- **Lab 6 writes on the hot path.** `recall` costs 3 to 5 seconds, `remember` about 11, so roughly 15 seconds a question
- **That is a good trade for a shift-handover agent** where the questions are few and the context is everything, and a bad one for a high-volume lookup endpoint
- **Push it to the background and staleness becomes the question:** how far behind is memory right now?
- **The hosted service exposes queue lag as a freshness SLI**, which makes staleness a number rather than a vibe

<!--
1.5 minutes, and this is the slide to cut if the day is running late. Fold it into the one line already on recall, then act, then remember, and move on.
The numbers are measured, from Section 9 of 01_agent_memory.ipynb, against live Aura and live Databricks Foundation Model endpoints. Say that they are measured; the honest version of this lab prints its own latency cost and lets the participant decide.
Lab 6 stays on the hot path to teach, not to engineer: a participant who cannot see the write happen cannot debug it. A production handover agent would move the write off the turn.
-->

---

## recall, then act, then remember

```
  Lab 5                          Lab 6

  question                       question -> recall
     |                                        |
  supervisor <--+                  supervisor <--+
     |          |                     |          |
     +-> genie / cypher / graphrag ---+ (unchanged)
     |                                |
  synthesize                       synthesize -> remember
     |                                             |
   answer                                       answer
```

- **Two nodes added. Three tools untouched.** The supervisor is the same node with a `{recalled}` block in front of its prompt
- **`recall` runs once per question, not once per tool call.** That single decision keeps the cost from being three times worse
- **Memory is routing context for the supervisor, not a fourth tool.** Nobody asks memory a question
- **It also rewrites the question.** The supervisor returns a `resolved` field, so "that aircraft" reaches Genie as `N10011`

<!--
2.0 minutes. Worth stating twice: recall runs once per question. Wire it as a tool and the supervisor can call it three times in one turn, at three to five seconds each, for no extra information.
The rewrite is the half people do not anticipate. Memory that only changes the route still hands the word "that" to Genie, which asks which aircraft you mean. Tools receive question text, so the question has to be resolved before it leaves the supervisor. Section 8 of the notebook shows the resolved: line in the trace, on a question where the participant never typed a tail number.
If Hot Path was cut, its line goes here: memory costs about 15 seconds a question, and recall running once per question rather than once per tool call is what keeps it from being three times worse.
-->

---

## The Payoff

- **Adoption, in one line.** Stamping `:Entity` onto the Lab 2 `Aircraft` nodes means a remembered aircraft **is** the fleet node, so one traversal crosses both
- **Adopt `Aircraft` and nothing else.** `adopt_existing_graph` sets `type` unconditionally, and `System`, `Sensor`, `Component`, and `Document` all already use it. Adopting them corrupts the fleet graph silently
- **Fleet graph alone**, ranked by critical maintenance events: `N10011` comes **last of six**
- **Conversation memory alone**, ranked by distinct technicians asking: `N10011` is **joint first**
- **The joined query explains why:** three technicians, on three separate shifts, each pulled the EGT trend on `N10011` without knowing the others had

```cypher
MATCH (u:User)-[:HAS_CONVERSATION]->(c)-[:HAS_MESSAGE]->(m)-[:MENTIONS]->(ac:Aircraft)
WITH ac, count(DISTINCT u) AS technicians, ...
MATCH (ac)<-[:AFFECTS_AIRCRAFT]-(ev:MaintenanceEvent)-[:AFFECTS_SYSTEM]->(sys:System)
```

<!--
3.0 minutes. Never cut this slide. It is the argument for the entire lab.
Show the three queries in order and let the ranking do the work. Read separately, each list is unremarkable: an aircraft with few critical events is fine, an aircraft several people asked about is a busy week. Side by side, it is a different sentence.
Analogy: the log is what got written down, the conversation is what the crew keeps worrying about, and the gap between them is where the next incident lives. Either those three technicians are seeing something the record has not caught yet, or three people each wasted a shift on the same dead end. Both are worth a supervisor's attention; neither list says it alone.
The point is the (ac) on the second MATCH: bound in the memory half, reused in the fleet half. Same node, no join key, no federation, no second query. Without adoption that ac would be a memory Entity sharing a name with an Aircraft, and joining them means exporting both sides and matching strings in Python, where the tail number N10011 and the tail number "n10011 " go to disagree.
The adoption guard is a concept, not a step: it is what "the same node" costs. memory.py refuses the four unsafe labels by name rather than trusting the notebook to get it right, and the notebook shows the refusal on purpose before the successful adoption.

Optional 30 seconds, from Demo 2. A preference scoped with APPLIES_TO hangs off the aircraft, not the user:

  MATCH (ac:Aircraft {tail_number: $tail})<-[:APPLIES_TO]-(p:Preference)
  WHERE p.valid_until IS NULL
  RETURN p.category, p.preference

"On N10011 the EGT sensor reads about five degrees high" reaches any technician who touches that aircraft, since it is a property of the aircraft's situation rather than one person's profile. A preferences table keyed by user cannot express that without a join nobody writes.
-->

---

## Context Graph: Where Memory Belongs

- **Databricks holds the telemetry.** Timestamped sensor values at volume, where scanning them is cheap
- **Neo4j holds the topology, the history, and now the memory.** Same instance, same nodes
- **Memory belongs on the side where the joins are.** Put it anywhere else and every question that spans both halves becomes an export and a string match
- **The cost is small.** About 20 nodes per participant per session, against roughly 178,000 nodes of headroom on AuraDB Free after Labs 1 through 3
- **AuraDB Free caps at 200,000 nodes and 400,000 relationships.** The arithmetic is why this fits on the tier the room is running

<!--
1.5 minutes. Close here. The dual-database argument has run through the whole workshop; this is its last and cleanest instance: memory is relationship-rich, low-volume data whose value is entirely in what it connects to. Same test every other placement decision in this workshop used.
Three different things share the "Neo4j memory" name; keep them apart if anyone asks for links. mcp-neo4j-memory, the older MCP server under neo4j-contrib, is not what this lab uses. neo4j-agent-memory, the neo4j-labs library, is what Lab 6 pins and runs. The hosted service is the source of the queue-lag SLI on Hot Path. Conflating them on a citation slide sends people to the wrong repository.
The pin, if asked: Lab 6 installs a fork wheel from a Unity Catalog volume rather than a PyPI version, since the released 0.5.0 silently drops most MENTIONS edges, the exact edge The Payoff query walks. The fork fixes it. The library is pre-1.0; treat any upgrade as a code change with its own test pass.
-->

---

## What Memory Adds to the Lab 5 Agent

- **Stateless is a default, not a law.** Two nodes either side of the supervisor change it
- **Memory is a graph, not a pile of chunks.** Short term, long term, reasoning, and the edges between them
- **Adoption makes it one graph.** A remembered aircraft **is** the fleet's `Aircraft` node
- **Being wrong is modeled, not deleted.** Supersede, stamp `valid_until`, and an audit can replay what the agent believed
- **The bill is about 15 seconds a question.** Measured, printed by the notebook, yours to accept or move off the turn

**Next:** Lab 6 redeploys the Lab 5 endpoint rather than standing up a second one. Adopt `Aircraft`, seed the shift history, run the crossing query, then wire `recall` and `remember`.

<!--
1.0 minutes. Lab 6 is the last required lab, so this is the last thing the room hears before they open the notebook. Read the Next line as a list of what they are about to do, not as a summary of what you just said.
Linger on adoption: the only bullet that is a decision they make rather than a fact they receive. The other four follow from it.
If the day is running late, cut the five bullets and keep the Next line; the room still needs to know what they are opening. Second cut in the ladder written on What This Covers.
-->

---

## Appendix: References

**Three different things carry the "Neo4j memory" name. Only one is this lab.**

1. `mcp-neo4j-memory`, the older MCP server: github.com/neo4j-contrib/mcp-neo4j
2. `neo4j-agent-memory`, the Neo4j Labs library **Lab 6 runs**: github.com/neo4j-labs/agent-memory, docs at neo4j.com/labs/agent-memory/
3. The hosted Agent Memory service, source of the queue-lag freshness SLI

**Lab 6 installs a fork of 2:** github.com/neo4j-partners/agent-memory, branch `mentions`

- Context graphs, why AI agents need three types of memory (Webber): neo4j.com/blog/agentic-ai/context-graph-ai-agent-memory/
- Modeling agent memory (Gilmore): neo4j.com/blog/developer/modeling-agent-memory/
- Hands on with context graphs and Neo4j (Lyon): neo4j.com/blog/agentic-ai/hands-on-with-context-graphs-and-neo4j/

<!--
Not presented. Zero minutes. Leave it on screen while the room photographs it, or hand it out with the deck.
Exists because conflating those three names sends people to the wrong repository, and all three turn up in a search for "neo4j agent memory." One sentence if asked: the MCP server is not what you installed, the hosted service is not what you installed, and what you installed is a fork of the Labs library.
The fork, if asked why: released 0.5.0 silently drops most MENTIONS edges, the exact edge The Payoff query walks. The fork fixes it and the fix has not gone upstream yet. Pre-1.0 library; treat any upgrade as a code change with its own test pass.
Gilmore is the cross walk for anyone who reads the older short-term versus long-term taxonomy afterward and wonders why this deck says something different.
-->
