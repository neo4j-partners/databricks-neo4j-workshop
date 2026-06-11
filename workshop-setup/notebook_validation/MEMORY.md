# Aircraft Digital Twin Agent with Memory: Proposal

## The Problem

The workshop teaches participants how to load aircraft data into Neo4j and query it with Cypher, but the agent experience in Lab 4 routes questions to a stateless Neo4j MCP tool. The agent has no memory of what the user asked before, no ability to learn a maintenance engineer's focus areas, and no way to recall diagnostic reasoning from prior sessions. Every conversation starts from zero.

The retail assistant project solved this same gap for a shopping domain: session-scoped conversation memory, user-scoped preference tracking, reasoning traces that accumulate diagnostic patterns over time. The aircraft digital twin dataset is richer in structural relationships (nine node types, twelve relationship types, component hierarchies four levels deep) and carries a natural "maintenance analyst" persona that makes memory especially valuable. An engineer investigating N10000's engine vibration across multiple sessions should not have to re-explain their focus each time.

This proposal describes a set of prototype scripts, following the same upload-and-submit pattern already working in notebook_validation, that build an aircraft maintenance agent with memory, deploy it to a Databricks Model Serving endpoint, and exercise it with scripted multi-turn conversations that verify memory persistence, tool correctness, and end-to-end response quality.


## What Agent Memory Looks Like for Aircraft Data

Three tiers, matching the retail assistant's proven architecture but mapped to maintenance engineering workflows.

**Session memory** captures the thread of a single troubleshooting conversation. When an engineer says "show me the engine systems for N10000," then follows up with "what maintenance events affected those systems?", session memory carries the aircraft context forward so the second question resolves without repeating the tail number. Entity extraction pulls out aircraft IDs, system names, component types, and severity levels automatically, building a session-local knowledge overlay that the agent can search semantically.

**User memory** persists across sessions and tracks an individual engineer's profile. Preferences like "I'm responsible for the Airbus A320 fleet," "flag any critical severity events," or "I specialize in hydraulics and avionics" allow the agent to personalize responses. A returning user gets their fleet context loaded at session start without asking. The retail assistant stores these as categorized preferences with user-scoped metadata isolation; the same pattern works here with categories like fleet, system-focus, severity-threshold, and operator.

**Reasoning traces** record multi-step diagnostic workflows. When the agent investigates a vibration anomaly by traversing the aircraft hierarchy, checking maintenance events, cross-referencing flight delays, and arriving at a root cause, the full chain of thought, action, and observation gets recorded. The next time a similar symptom appears on a different aircraft, the agent recalls the prior trace by semantic similarity and applies the same investigative pattern. This is the memory tier that compounds in value over time.


## The Agent's Tool Set (MVP)

The minimum viable prototype starts with 8-10 tools across four categories, with knowledge tools deferred until Lab 3 validation is complete.

**Graph query tools** form the core (3-4 tools). Search aircraft by tail number, model, or operator. Retrieve the full hierarchy for an aircraft (systems, components, sensors). Find maintenance events filtered by severity, system, or date range. Get component removal history. These are Cypher queries executed against Neo4j via the neo4j driver, returning structured results the agent can reason over.

**Sensor query tool** provides direct access to Lakehouse telemetry (1 tool). Queries the sensor_readings Delta table (345,600+ rows of hourly EGT, vibration, N1 speed, and fuel flow data) via the databricks-sql-connector targeting the Starter Warehouse. Accepts natural-language-style filters (aircraft, sensor type, date range) and translates them to SQL against the Unity Catalog tables. This gives the single agent a capability that Lab 4 distributes across two agents, useful for validating end-to-end before the multi-agent architecture is needed.

**Memory tools** follow the retail assistant's pattern (3-5 tools). Remember, recall, and search for session memory. Track and retrieve for user preferences. Reasoning traces are included in the MVP tool set since they are lightweight to implement and demonstrate the most compelling memory behavior.

**An echo tool** for baseline validation (1 tool), same as the retail assistant.

**Deferred to Phase 2 (after Lab 3):** Knowledge tools (semantic search over maintenance manual chunks, hybrid search, diagnosis tools) and the diagnostic recommendation tool that combines user preferences with GraphRAG context. These depend on the vector indexes and entity graph that Lab 3's GraphRAG enrichment creates.


## The Deployment and Validation Flow

The scripts follow the same dbx_rd lifecycle already established in notebook_validation: local Python files uploaded to the Databricks workspace and submitted as one-time jobs on the existing cluster.

**Script 0: setup.sh.** Single idempotent prerequisite script that handles all one-time provisioning. Creates the `aircraft-agent-secrets` scope in Databricks and populates it with Neo4j credentials (neo4j-uri, neo4j-username, neo4j-password) and the SQL warehouse HTTP path (warehouse-http-path), all read from .env. Then creates the Unity Catalog schema (`CREATE SCHEMA IF NOT EXISTS databricks-neo4j-workshop.agents`) via the SQL warehouse. Keeps this prototype's secrets and schema separate from the workshop lab infrastructure. Run once before the first deploy; safe to re-run.

**Script 1: deploy_agent.py.** Constructs the LangGraph ReAct agent with the tool registry and system prompt. Logs it to MLflow as a ChatAgent using the models-from-code pattern (the serving adapter, agent definition, tool modules, and context dataclass bundled via code_paths). Registers the model to Unity Catalog at databricks-neo4j-workshop.agents.aircraft_agent. Deploys to a Model Serving endpoint via the Databricks agents API with Neo4j and warehouse credentials injected from the aircraft-agent-secrets scope. Waits for the endpoint to reach ready state. The endpoint is left running for manual exploration after validation.

**Script 2: check_agent.py.** Sends scripted multi-turn conversations to the deployed endpoint and validates responses with keyword checks. Covers: a stateless graph query (aircraft hierarchy lookup), a sensor telemetry query (average EGT for a specific aircraft), a multi-turn session where context carries forward, a preference-setting flow where the agent stores and later retrieves the user's fleet focus, and a diagnostic reasoning session that generates a trace. Reports PASS/FAIL for each turn.

**Script 3: verify_memory.py.** Creates a session in one invocation, stores preferences and a reasoning trace, then makes a fresh invocation with the same user ID but a different session ID. Validates that long-term preferences survived the session boundary and that a semantically similar question triggers recall of the prior reasoning trace. Memory clearing before the run is controlled by an optional CLEAR_MEMORY setting in .env, defaulting to true so each validation run starts clean. Administrators who want to observe memory accumulation across runs can set it to false.

**Script 4 (later phase): eval_agent.py.** MLflow Agent Evaluation with RelevanceToQuery and Safety scorers. Runs a structured evaluation dataset through the endpoint and produces scored results. Deferred to a later phase after the core agent and memory are validated.


## The System Prompt

The agent's identity is a maintenance engineering assistant with access to the aircraft digital twin graph, sensor analytics via direct Lakehouse queries, and persistent memory. The system prompt follows the retail assistant's sectioned structure: session start behavior (load user profile if user ID present), tool selection guide (graph tools for topology and relationships, sensor tool for telemetry aggregations, memory tools for context), preference tracking triggers (when the user states their fleet, system focus, severity threshold, or operator responsibility), and reasoning trace guidance (recall before multi-step diagnostic tasks, record after completing them).


## How This Relates to Existing Lab Content

This prototype sits between Lab 2 (data loading, already validated by run_lab2_02.py) and Lab 4 (multi-agent supervisor). Lab 2 proves the data is in Neo4j. This prototype proves a single agent can query that data intelligently with memory. Lab 4 then composes that agent with Genie into a multi-agent system.

The prototype is phased to respect the dependency on Lab 3. Phase 1 works with only the base graph from Lab 2 plus the Lakehouse sensor tables. Phase 2, built after Lab 3 validation exists, adds GraphRAG knowledge tools for semantic search over maintenance manuals.

The scripts do not replace any existing lab content. They validate the agent patterns that Lab 4 assumes are working and provide a reusable foundation that workshop administrators can run to verify the full agent stack before participants arrive. The endpoint is admin-only; participants interact with the multi-agent supervisor in Lab 4 instead.


## Implementation Phasing

**Phase 1 (current):** Graph query tools, sensor query tool, memory tools, echo tool. Deploy agent, exercise with keyword validation, verify memory persistence. Depends on: Lab 2 data loaded, SQL warehouse available, neo4j-agent-memory wheel on cluster.

**Phase 2 (after Lab 3):** Add knowledge tools (vector search, hybrid search, diagnosis), diagnostic recommendation tool. Extend check_agent.py with GraphRAG-specific exercises. Depends on: Lab 3 GraphRAG enrichment complete (vector indexes, entity graph).

**Phase 3 (later):** MLflow Agent Evaluation script with RelevanceToQuery and Safety scorers. Structured evaluation dataset.


---


## Decisions Locked In

1. **neo4j-agent-memory:** Available and pre-installed. MLflow pip requirements will reference it.
2. **LLM endpoint:** databricks-claude-sonnet-4-6.
3. **Secrets scope:** New scope `aircraft-agent-secrets` with keys: neo4j-uri, neo4j-username, neo4j-password, warehouse-http-path. Created by setup.sh.
4. **GraphRAG dependency:** Lab 3 validation built first. Agent Phase 1 works without it; Phase 2 adds knowledge tools after Lab 3 exists.
5. **Embedding endpoint:** databricks-bge-large-en (1024 dimensions), same as retail assistant.
6. **Unity Catalog location:** databricks-neo4j-workshop.agents.aircraft_agent. Schema created by setup.sh.
7. **Tool scope:** MVP set of 8-10 tools (graph, sensor, memory, echo). Knowledge tools deferred to Phase 2.
8. **Sensor integration:** Direct Lakehouse query via databricks-sql-connector targeting Starter Warehouse.
9. **Endpoint lifecycle:** Leave running after validation for manual exploration.
10. **Evaluation:** MLflow eval as fourth script, deferred to Phase 3.
11. **Setup script:** Single setup.sh handles secrets scope creation, credential population, and UC schema creation. Idempotent, run once before first deploy.
12. **Memory isolation:** Controlled by optional CLEAR_MEMORY in .env (default: true). Each validation run starts clean unless explicitly configured otherwise.
13. **Audience:** Admin-only validation tool. Participants use Lab 4 multi-agent supervisor.

All questions resolved. Ready for implementation.
