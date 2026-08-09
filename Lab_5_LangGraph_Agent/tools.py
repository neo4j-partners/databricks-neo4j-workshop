"""Tool construction for the Lab 5 supervisor agent.

Three retrieval tools and the two reasoning nodes that sit around them:

- ``genie_node``     Databricks Genie over the Lakehouse telemetry from Lab 4
                     Part A. Every reading and every aggregation over readings.
- ``cypher_node``    Text to Cypher over the Aura instance from Lab 2, run in a
                     read transaction.
- ``graphrag_node``  ``VectorCypherRetriever`` over the ``maintenanceChunkEmbeddings``
                     index from Lab 3, with the Cypher tail that makes it
                     GraphRAG rather than vector search.
- ``supervisor``     Picks the next tool, or stops.
- ``synthesize``     Turns the collected findings into one answer.

Each builder returns a plain callable that takes an :data:`AgentState` and
returns the part of the state it changed, which is the shape LangGraph wants
from a node. The graph itself is wired in ``01_langgraph_agent.ipynb`` so the
wiring stays visible.

Where this lab's defaults come from
-----------------------------------

Lab 5 declares almost no configuration of its own. Everything below is defined
in ``Lab_3_Semantic_Search/data_utils.py`` and imported here under its original
name, so there is one name per thing across the course and nothing to keep in
sync. Read that file when you want to know what a value is:

- ``LLM_ENDPOINT`` is the model behind the supervisor's routing decision and
  behind every node that writes text.
- ``EMBEDDING_ENDPOINT`` is the model that embeds the question ``graphrag_node``
  searches with. It has to be the model Lab 3 wrote the index with.
- ``secret_scope_name()`` names the Databricks secret scope holding your Aura
  credentials, and ``read_neo4j_secrets()`` reads them back out.

``lab/workshop.py`` names the same two endpoints for provisioning. That file is
standard-library-only and cannot import ``data_utils``, so the two are kept in
sync by hand. Change an endpoint in both or in neither.

To try a different supervisor model for one run, pass it to ``get_llm`` in the
notebook rather than editing anything here.

The supervisor's route and the Cypher this lab generates come back as JSON,
constrained by a schema the request carries in ``response_format``. That is the
Databricks-wide mechanism for structured outputs, so it works on any endpoint
that supports them, and it replaces reading a decision out of prose the model
wrote for a human. ``ROUTE_SCHEMA`` and ``CYPHER_SCHEMA`` below are the two
schemas. The old free-text scan is still in ``build_supervisor_node``, reached
only when the reply will not parse, so an edited prompt or an endpoint that
ignores ``response_format`` degrades rather than fails.

Embeddings and the LLM come from ``Lab_3_Semantic_Search/data_utils.py``. That
module is the workshop's one path to the Databricks Foundation Model endpoints,
and the vectors in ``maintenanceChunkEmbeddings`` were written through it. A
second embedding implementation here would be a second way to produce numbers
that have to match, so there is not one.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TypedDict

# =============================================================================
# Locating Lab 3's data_utils
# =============================================================================

LAB3_DIRNAME = "Lab_3_Semantic_Search"


def ensure_lab3_on_path() -> Path:
    """Put the Lab 3 directory on ``sys.path`` and return it.

    Lab 5 imports the embedder, the LLM, and the secret-scope helpers from
    ``data_utils.py`` rather than carrying copies. The two labs sit side by side
    in the repository and side by side in the workspace, so the sibling
    directory is the first place to look.

    Returns:
        The directory holding ``data_utils.py``.

    Raises:
        FileNotFoundError: ``data_utils.py`` is not beside this lab.
    """
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / LAB3_DIRNAME,
        Path.cwd().parent / LAB3_DIRNAME,
        Path.cwd() / LAB3_DIRNAME,
        here,
    ]
    for candidate in candidates:
        if (candidate / "data_utils.py").is_file():
            path = str(candidate)
            if path not in sys.path:
                sys.path.insert(0, path)
            return candidate
    searched = "\n  ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        "Could not find data_utils.py from Lab 3. Lab 5 imports the embedder "
        "and the LLM from it rather than defining its own. Import the "
        f"{LAB3_DIRNAME} folder into the workspace next to this one. Searched:"
        f"\n  {searched}"
    )


ensure_lab3_on_path()

from data_utils import (  # noqa: E402
    EMBEDDING_ENDPOINT,
    LLM_ENDPOINT,
    get_embedder,
    get_llm,
    json_schema_format,
    read_neo4j_secrets,
    secret_scope_name,
)

__all__ = [
    "CYPHER_GENERATION_PROMPT",
    "CYPHER_REPAIR_PROMPT",
    "CYPHER_SCHEMA",
    "EMBEDDING_ENDPOINT",
    "FULLTEXT_INDEX_NAME",
    "GRAPH_SCHEMA",
    "LLM_ENDPOINT",
    "MANUAL_CONTEXT_QUERY",
    "MAX_TOOL_CALLS",
    "MISSING_INDEX_MESSAGE",
    "ROUTE_SCHEMA",
    "SUPERVISOR_PROMPT",
    "SYNTHESIS_PROMPT",
    "TOOL_NAMES",
    "VECTOR_INDEX_NAME",
    "AgentState",
    "Finding",
    "build_cypher_node",
    "build_genie_node",
    "build_graphrag_node",
    "build_neo4j_driver",
    "build_supervisor_node",
    "build_synthesize_node",
    "ensure_lab3_on_path",
    "format_manual_chunk",
    "get_embedder",
    "get_llm",
    "open_driver_from_secrets",
    "read_neo4j_secrets",
    "route_from_supervisor",
    "secret_scope_name",
    "vector_index_exists",
]


# =============================================================================
# Model endpoints
# =============================================================================

# LLM_ENDPOINT and EMBEDDING_ENDPOINT are imported from data_utils above and
# re-exported here, under the same names, so `from tools import LLM_ENDPOINT`
# works in the notebook. They are not redefined: this lab adds no third place
# either string is written. See the module docstring for where they do live.

# The indexes Lab 3 created. The vector index is what graphrag_node reads. The
# fulltext index is optional and only the hybrid exercise touches it.
VECTOR_INDEX_NAME = "maintenanceChunkEmbeddings"
FULLTEXT_INDEX_NAME = "maintenanceChunkText"

TOOL_NAMES = ("genie_node", "cypher_node", "graphrag_node")

# How many tool calls the supervisor gets before synthesis is forced. The anchor
# question needs three. The guard exists so a supervisor that keeps asking for
# the same tool ends the run instead of the participant's patience.
MAX_TOOL_CALLS = 4


# =============================================================================
# Structured output schemas
# =============================================================================

# What the two nodes that have to read a reply ask the model for. Databricks
# structured outputs takes a JSON Schema on the request and constrains the
# generation to it, so the reply arrives as JSON rather than as prose a regular
# expression has to guess at. Both are flat on purpose: Databricks accepts
# json_schema only, caps the object at 64 keys, rejects pattern, anyOf, oneOf,
# allOf and $ref, and a flat schema is generated more reliably than a nested one.
ROUTE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "next": {
            "type": "string",
            "enum": ["genie_node", "cypher_node", "graphrag_node", "synthesize"],
        },
        "reason": {"type": "string"},
    },
    "required": ["next", "reason"],
}

# No code reads reason. It is in the schema because a model that has to write
# down why it picked a tool picks better, and because the free-text fallback in
# build_supervisor_node needs the tool named somewhere in the reply.

CYPHER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"cypher": {"type": "string"}},
    "required": ["cypher"],
}


# =============================================================================
# Agent state
# =============================================================================


class Finding(TypedDict):
    """One tool's answer to the current question."""

    tool: str
    content: str


class AgentState(TypedDict, total=False):
    """What flows between the nodes of the graph.

    Attributes:
        question: The participant's question, unchanged for the whole run.
        route: The supervisor's most recent decision. One of TOOL_NAMES or
            ``"synthesize"``.
        trace: Tools called so far, in order. This is the routing record the
            measurement cell reads.
        findings: One entry per tool call.
        answer: The synthesized final answer.
    """

    question: str
    route: str
    trace: list[str]
    findings: list[Finding]
    answer: str


# =============================================================================
# Graph schema, as the participant's own graph is shaped
# =============================================================================

# What Lab 2 loaded plus what Lab 3 added, and nothing else. Reading nodes are
# deliberately absent: Lab 2 never loads them, sensor readings live in Delta,
# and the supervisor prompt below leans on that fact to route reading questions
# to Genie. Adding Reading here would break the lesson and the routing at once.
GRAPH_SCHEMA = """\
Node labels and their properties:

  (:Aircraft)          aircraft_id, tail_number, model, manufacturer,
                       operator, icao24
  (:System)            system_id, aircraft_id, name, type
                       type is exactly one of 'Engine', 'Avionics',
                       'Hydraulics'. Note the plural on Hydraulics. There are
                       no other system types, so a question about fuel or
                       landing gear has no system to match.
  (:Component)         component_id, system_id, name, type
  (:Sensor)            sensor_id, system_id, name, type, unit
                       type is one of EGT, Vibration, N1Speed, FuelFlow
  (:MaintenanceEvent)  event_id, aircraft_id, system_id, component_id, fault,
                       severity, corrective_action, reported_at
  (:Flight)            flight_id, flight_number, aircraft_id, operator,
                       origin, destination, scheduled_departure,
                       scheduled_arrival
  (:Delay)             delay_id, cause, minutes
                       cause is exactly one of 'Weather', 'NAS', 'Maintenance',
                       'Carrier'. These are the four industry reporting
                       categories and nothing finer. A delay never names a
                       component or a fault.
  (:Airport)           airport_id, iata, icao, name, city, country, lat, lon
  (:Removal)           removal_id, aircraft_id, component_id, part_number,
                       serial_number, reason, removal_date, removal_priority,
                       cost_estimate, warranty_status
  (:OperatingLimit)    limit_id, name, parameterName, aircraftType, unit,
                       regime, minValue, maxValue
  (:Document)          documentId, title, aircraftType, type
  (:Chunk)             index, text

Relationships, with direction:

  (:Aircraft)-[:HAS_SYSTEM]->(:System)
  (:System)-[:HAS_COMPONENT]->(:Component)
  (:System)-[:HAS_SENSOR]->(:Sensor)
  (:Sensor)-[:HAS_LIMIT]->(:OperatingLimit)
  (:Component)-[:HAS_EVENT]->(:MaintenanceEvent)
  (:MaintenanceEvent)-[:AFFECTS_SYSTEM]->(:System)
  (:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(:Aircraft)
  (:Aircraft)-[:OPERATES_FLIGHT]->(:Flight)
  (:Flight)-[:DEPARTS_FROM]->(:Airport)
  (:Flight)-[:ARRIVES_AT]->(:Airport)
  (:Flight)-[:HAS_DELAY]->(:Delay)
  (:Aircraft)-[:HAS_REMOVAL]->(:Removal)
  (:Removal)-[:REMOVED_COMPONENT]->(:Component)
  (:Document)-[:APPLIES_TO]->(:Aircraft)
  (:Chunk)-[:FROM_DOCUMENT]->(:Document)
  (:Chunk)-[:NEXT_CHUNK]->(:Chunk)

Facts that change the query you write:

  - There are no sensor reading values in this graph. No :Reading label, no
    timestamps, no measured values. Sensor nodes are metadata only. A question
    about a measured value cannot be answered here.
  - Refuse reading questions rather than approximating them. If the question
    asks what a sensor read, or asks for an average, maximum, minimum, count
    or trend over readings, do not return a number. Return exactly this and
    nothing else:

        RETURN 'The graph holds no sensor readings.' AS cannot_answer

    Never substitute a limit, a threshold or a ceiling for a measurement.
    Answering "which aircraft has the highest average vibration" with
    maxValue 3.0 from the 'Vibration - B737-800' limit is wrong. 3.0 is the
    takeoff ceiling every B737-800 shares, transcribed from a manual. It is
    not a reading, it is not an average, and it is not that aircraft's.
  - Decide by what is being asked for, not by the words it is asked in. A
    question about what a sensor observed, or about the highest, lowest,
    average, typical or worst of what sensors observed, asks for a measurement
    and gets the refusal above. A question about what the fleet is held to, the
    ceiling, the redline, the rated, permitted, approved or allowed value, or
    what a model is limited to, asks for a limit and is answered from
    OperatingLimit. The graph holds a limit on the same parameter a sensor
    measures, so the parameter named is not the test and neither is the
    phrasing. The words documented and limit for do not have to appear.
  - "What N1 speed is the A321neo limited to on the runway roll?" asks what the
    model is held to, so it is an OperatingLimit query on N1Speed, A321neo and
    takeoff. "Which aircraft has the highest average vibration?" asks what
    sensors observed, so it is the refusal.
  - A limit is stored per aircraft type, not per tail number. A question naming
    a model reaches its limit directly. A question naming one aircraft reaches
    it through that aircraft's model property.
  - OperatingLimit is exactly the twenty canonical limits loaded in Lab 2,
    four parameters for each of five aircraft models. The twenty nodes are
    never empty and never duplicated, so the label needs no filter of its own
    to be trusted.
  - Reach a limit by matching (:OperatingLimit) directly and filtering it on
    its own properties, parameterName, aircraftType and regime. Do not walk in
    from Sensor or from Document. Many sensors point at one limit, so a
    traversal returns the same limit once per sensor and fills the result with
    identical rows even though the nodes behind them are unique. Where a
    traversal is unavoidable, RETURN DISTINCT.
  - A question naming an aircraft does not mean the arrow leaves the aircraft.
    AFFECTS_AIRCRAFT and AFFECTS_SYSTEM both run FROM the MaintenanceEvent TO
    the thing affected, so the maintenance events for a tail number are reached
    by matching (:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(:Aircraft
    {tail_number: ...}). Writing
    (:Aircraft {tail_number: 'N10004'})-[:AFFECTS_AIRCRAFT]->(:MaintenanceEvent)
    points the arrow away from the named noun and matches nothing, returning
    zero rows with no error, even though N10004 has 23 maintenance events and
    more of them than any other aircraft in the fleet.
  - A question about which components have had maintenance events is answered
    by the Component to MaintenanceEvent edge, not by the System. Match
    (:Component)-[:HAS_EVENT]->(:MaintenanceEvent), constrain that event with
    -[:AFFECTS_AIRCRAFT]->(:Aircraft {tail_number: ...}), and RETURN DISTINCT
    the component. Walking MaintenanceEvent to System and back down through
    HAS_COMPONENT instead returns every component those systems contain,
    including the ones that never had an event, so it answers a looser question
    than the one asked. There is no AFFECTS_COMPONENT relationship either, and
    writing one matches nothing and returns zero rows with no error.
    MaintenanceEvent does carry component_id as a property, but HAS_EVENT is
    the join to use.
  - minValue and maxValue are both FLOAT. Compare them directly.
  - minValue is null on ten of the twenty, because a vibration or speed limit
    is a ceiling with no floor. Check ol.minValue IS NOT NULL before comparing
    against it, or the row drops out with no error.
  - OperatingLimit.regime says which phase of flight a limit applies to. A
    limit is only meaningful against readings from that same regime, so return
    the regime alongside any limit you report.
  - regime values are lower case, and 'takeoff' is the only one loaded. Writing
    regime: 'Takeoff' matches nothing and returns zero rows with no error.
  - parameterName is spelled the way Sensor.type is, and the four values are
    exactly N1Speed, Vibration, EGT and FuelFlow. N1Speed carries no space.
    Writing 'N1 Speed' matches nothing and returns zero rows with no error.
  - ExtractedLimit is a separate label holding what the Lab 3 language model
    pulled out of the manual text. It exists only if the participant ran Lab 3
    with extraction on, its contents vary from one graph to the next, and it
    can be empty. It records what a manual said, not what the fleet is held
    to, so never treat it as authoritative. OperatingLimit is the authority.
  - Severity values are upper case, for example 'CRITICAL'.
  - Dates are ISO 8601 STRINGs, so compare them as strings or parse with
    date() and datetime().
  - Nothing in this graph attributes a delay to a fault. No relationship joins
    a MaintenanceEvent to a Flight, and Delay.cause is one of four broad
    categories that never names a component. A question asking which failure
    caused which delay cannot be answered here. Say so rather than walking
    MaintenanceEvent to Flight through the shared Aircraft, which pairs every
    event on that aircraft with every delayed flight it ever flew.
"""


CYPHER_GENERATION_PROMPT = """\
You write Cypher for a Neo4j aircraft fleet graph. Return one read-only Cypher
query, as a JSON object whose single field, cypher, holds the query.

Schema:
{schema}

Rules:
  - Read only. No CREATE, MERGE, SET, DELETE, REMOVE, DROP or LOAD CSV.
  - End with a RETURN that names every column with AS.
  - Add LIMIT {limit} unless the question asks for a count or an aggregate.
  - Use only labels, relationship types and properties from the schema.
  - A question about a measured value has no answer here. Return
    RETURN 'The graph holds no sensor readings.' AS cannot_answer rather than
    a limit, a threshold or any other number standing in for a measurement. A
    question about what the fleet is limited to is not one of these. Answer it
    from OperatingLimit however it is phrased.
  - The cypher field holds the query alone. No prose, no explanation, no
    markdown fence.

Question: {question}
"""


CYPHER_REPAIR_PROMPT = """\
The Cypher below failed. Fix it and return the corrected query alone, as a JSON
object whose single field, cypher, holds the query.

Schema:
{schema}

Question: {question}

Query:
{query}

Error:
{error}
"""


# =============================================================================
# The supervisor prompt
# =============================================================================

# Grown from the Agent Bricks supervisor instructions in Lab 4 Part B. Two
# things changed. There is a third tool, and the boundary between cypher_node
# and graphrag_node is stated as its own section, because both tools end in a
# graph traversal and that is the pair the model gets wrong.
SUPERVISOR_PROMPT = """\
# Fleet Operations Assistant, routing instructions

You coordinate three tools over one aircraft fleet. Read the question, read
what has already been gathered, then name the one tool to call next, or say
the answer can be assembled from what is already here.

## The tools

### genie_node, sensor telemetry in the Databricks Lakehouse
Every measured value and every aggregation over measured values. Averages,
maxima, percentiles, trends, rolling windows, daily or monthly breakdowns,
comparisons of readings across aircraft or models, anomaly detection over
readings. The readings are EGT, Vibration, N1Speed and FuelFlow, sampled every
four hours across 90 days.

This is the only tool that can see a reading. The graph holds no reading
values at all, so any question about what a sensor measured goes here.

### cypher_node, the fleet knowledge graph in Neo4j
Questions that start from a named thing in the graph and are answered by
following relationships from it. A tail number, an aircraft model, a system, a
component, a maintenance event, a flight, an airport, a part removal, or a
documented operating limit attached to a sensor.

Use it for topology, component hierarchy, maintenance and fault history,
flights, routes, delays, part removals, and the documented limit values stored
on OperatingLimit nodes.

It cannot see a reading. A documented limit is what the fleet is held to, not
what a sensor measured, so a question about a measured value goes to
genie_node even when the graph holds a limit on the same parameter.

### graphrag_node, the maintenance manuals
Questions that start from language in a manual rather than from a named node.
What a document says: a procedure, a troubleshooting sequence, an inspection
interval, what a fault code means, what to do when something happens. Semantic
similarity finds the passage, then a Cypher tail returns the surrounding
passages and the aircraft the manual applies to.

## The line between cypher_node and graphrag_node

Both end in a graph traversal, so do not decide on the ending. Decide on where
the question starts.

  Starts with a name you could put in a WHERE clause  -> cypher_node
  Starts with a phrase you would search a manual for  -> graphrag_node

  "What maintenance events did N10004 have?"
      -> cypher_node. N10004 is a node.
  "What is the procedure for an EGT exceedance?"
      -> graphrag_node. An EGT exceedance is a phrase in a manual, not a node.
  "What is the documented EGT limit for the A320-200?"
      -> cypher_node. The limit is a maxValue property on an OperatingLimit.
  "How do I troubleshoot engine vibration?"
      -> graphrag_node. A procedure, so it lives in the manual text.
  "Which components are in the hydraulic system of N10000?"
      -> cypher_node. A hierarchy walk from a named aircraft.
  "What does the manual say about borescope inspection intervals?"
      -> graphrag_node. It says so in words.

If the question names an entity and asks what a document says about it, the
document is what is being asked for, so use graphrag_node.

## Questions that need more than one tool

Ask for one tool at a time and let the result come back before choosing the
next. A typical order:

  1. genie_node    finds which aircraft or engine the readings point at
  2. cypher_node   returns that aircraft's maintenance and component history
  3. graphrag_node returns the procedure the manuals give for it

## Rules for choosing

  1. Call each tool at most once. A tool that has already run has given you
     everything it has, and calling it again returns the same thing.
  2. Choose synthesize as soon as every part of the question has a finding
     against it, even a partial finding. A partial answer beats another call
     that returns the same rows.
  3. Choose synthesize when the only part left is one no tool can answer.
  4. A question with one part needs one tool, then synthesize.

## What to answer with

Reply with a JSON object holding exactly two fields:

  next    the one tool to call: genie_node, cypher_node, graphrag_node, or
          synthesize
  reason  one sentence, naming that same tool, saying why it is the next one

## The question

{question}

## Tools already called

{called}

## Findings so far

{findings}
"""


SYNTHESIS_PROMPT = """\
Answer the question from the findings below. The findings are the only source,
so do not add facts from your own knowledge.

Write the answer first, in prose, using every number and name the findings give
you. Quote the actual values. Then, on a final line beginning 'Sources:', list
which tool supplied which part.

If a finding answers a question that is close to the one asked but not exactly
it, use the finding and say what it actually covers. Only say something is
unanswered when no finding bears on it at all.

If a finding says its tool could not answer, carry that through. Report that
the tool could not answer and do not fill the gap with a number from another
finding that measures something else.

Two findings that describe different quantities are not rival answers, so do
not present them side by side as though one contradicts the other. A measured
average and a documented limit are the clearest case: the average is what a
sensor read, the limit is the ceiling a manual sets for every aircraft of that
model. Name which is which, and give the measured value as the answer.

Be concise. No preamble.

Question: {question}

Findings:
{findings}
"""


# =============================================================================
# Shared helpers
# =============================================================================


def _format_findings(findings: Sequence[Finding]) -> str:
    """Render the findings list for a prompt."""
    if not findings:
        return "(nothing gathered yet)"
    return "\n\n".join(
        f"### {item['tool']}\n{item['content']}" for item in findings
    )


def _record(state: AgentState, tool: str, content: str) -> dict[str, Any]:
    """Build the state update a tool node returns."""
    return {
        "trace": [*state.get("trace", []), tool],
        "findings": [*state.get("findings", []), {"tool": tool, "content": content}],
    }


def _rows_to_text(rows: Sequence[dict[str, Any]], max_rows: int) -> str:
    """Render Neo4j records as one line per row, truncated."""
    if not rows:
        return "(no rows)"
    lines = [
        ", ".join(f"{key}={value!r}" for key, value in row.items())
        for row in rows[:max_rows]
    ]
    if len(rows) > max_rows:
        lines.append(f"... {len(rows) - max_rows} more rows")
    return "\n".join(lines)


def _strip_code_fence(text: str) -> str:
    """Remove a markdown fence the LLM wrapped around a query."""
    stripped = text.strip()
    fence = re.match(r"^```(?:\w+)?\s*(.*?)\s*```$", stripped, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return stripped


# Cypher that writes. The read transaction below is what actually enforces this,
# because the server rejects a write inside one. This check exists so the
# refusal is a sentence the participant can read rather than a driver error.
_WRITE_CLAUSE = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|FOREACH|LOAD\s+CSV)\b",
    re.IGNORECASE,
)

# One Cypher string literal, single or double quoted, backslash escapes inside.
# A search for a keyword has to skip these or a maintenance event whose
# corrective_action contains the word 'remove' reads as a write, and so does a
# fulltext call whose search terms happen to name one.
_STRING_LITERAL = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"", re.DOTALL)


def _mask_string_literals(query: str) -> str:
    """Empty every quoted string in the query, leaving the quotes.

    An unterminated quote matches nothing, so its text stays visible to the
    scan and the query is judged on it. That is the conservative direction: a
    malformed query is more likely to be refused, not less.

    Args:
        query: Generated Cypher.

    Returns:
        The query with the contents of each quoted string removed.
    """
    return _STRING_LITERAL.sub(lambda match: match.group(0)[0] * 2, query)


def _reject_writes(query: str) -> None:
    """Raise if the generated Cypher contains a write clause.

    Args:
        query: Generated Cypher.

    Raises:
        ValueError: The query would write.
    """
    match = _WRITE_CLAUSE.search(_mask_string_literals(query))
    if match:
        raise ValueError(
            f"Refusing to run generated Cypher containing '{match.group(1)}'. "
            "cypher_node is read-only."
        )


# =============================================================================
# genie_node
# =============================================================================


def build_genie_node(
    space_id: str,
    workspace_client: Any,
    *,
    max_rows: int = 20,
) -> Callable[[AgentState], dict[str, Any]]:
    """Build the node that asks a Genie space a question.

    Genie answers in two pieces. A text response, and zero or more attachments
    holding the SQL it generated plus that SQL's result set. Both are useful to
    the supervisor, so both go into the finding: the SQL shows what was actually
    computed, and the rows are the numbers.

    Args:
        space_id: The Genie space to ask. Each participant creates their own in
            Lab 4 Part A, so this comes from the notebook's configuration cell.
        workspace_client: A ``databricks.sdk.WorkspaceClient``.
        max_rows: Rows of the result set to keep.

    Returns:
        A LangGraph node.
    """

    def genie_node(state: AgentState) -> dict[str, Any]:
        question = state["question"]
        try:
            message = workspace_client.genie.start_conversation_and_wait(
                space_id=space_id, content=question
            )
        except Exception as error:  # noqa: BLE001 - reported, not swallowed
            return _record(
                state,
                "genie_node",
                f"Genie space {space_id} could not be reached: {error}",
            )

        parts: list[str] = []
        for attachment in message.attachments or []:
            if attachment.text is not None and attachment.text.content:
                parts.append(attachment.text.content)
            if attachment.query is None:
                continue
            if attachment.query.query:
                parts.append(f"SQL:\n{attachment.query.query}")
            try:
                result = workspace_client.genie.get_message_attachment_query_result(
                    space_id=space_id,
                    conversation_id=message.conversation_id,
                    message_id=message.message_id,
                    attachment_id=attachment.attachment_id,
                )
            except Exception as error:  # noqa: BLE001 - reported, not raised
                parts.append(f"The SQL ran but its rows could not be read: {error}")
            else:
                parts.append(_format_genie_result(result, max_rows))

        # GenieMessage.content is the question that was sent, not the reply, so
        # there is nothing to fall back to. Report the failure instead of
        # handing the supervisor its own question back as a finding.
        if not parts:
            detail = getattr(getattr(message, "error", None), "error", None)
            parts.append(
                f"Genie returned no answer. {detail}"
                if detail
                else "Genie returned no answer and no SQL for this question."
            )
        return _record(state, "genie_node", "\n\n".join(parts))

    return genie_node


def _format_genie_result(result: Any, max_rows: int) -> str:
    """Render a Genie statement result as a small text table."""
    manifest = getattr(getattr(result, "statement_response", None), "manifest", None)
    data = getattr(getattr(result, "statement_response", None), "result", None)
    if manifest is None or data is None or not data.data_array:
        return "(no rows)"
    columns = [column.name for column in manifest.schema.columns]
    lines = [" | ".join(columns)]
    for row in data.data_array[:max_rows]:
        lines.append(" | ".join("" if cell is None else str(cell) for cell in row))
    if len(data.data_array) > max_rows:
        lines.append(f"... {len(data.data_array) - max_rows} more rows")
    return "\n".join(lines)


# =============================================================================
# cypher_node
# =============================================================================


def build_cypher_node(
    driver: Any,
    llm: Any,
    *,
    database: str,
    schema: str = GRAPH_SCHEMA,
    max_rows: int = 25,
    repair_attempts: int = 1,
) -> Callable[[AgentState], dict[str, Any]]:
    """Build the node that writes and runs Cypher against the participant's Aura.

    The query runs in a read transaction, so Aura rejects a write even if the
    generated Cypher slips one past the check in :func:`_reject_writes`. Two
    guards rather than one, because the first is a regular expression and the
    second is the database.

    Args:
        driver: A connected ``neo4j.Driver``.
        llm: A ``data_utils.DatabricksLLM``.
        database: Neo4j database name.
        schema: Schema description handed to the LLM.
        max_rows: Rows kept from the result set.
        repair_attempts: How many times a failing query is sent back to the LLM
            with its error message.

    Returns:
        A LangGraph node.
    """
    from neo4j import RoutingControl

    cypher_format = json_schema_format("cypher_query", CYPHER_SCHEMA)

    def _ask(rendered: str) -> str:
        """Ask the LLM for one query and take it out of the reply.

        Args:
            rendered: A prompt with its placeholders already filled in.

        Returns:
            The Cypher query, with any markdown fence removed.
        """
        reply = llm.invoke(rendered, response_format=cypher_format).content
        try:
            query = json.loads(reply)["cypher"]
        except (KeyError, TypeError, ValueError):
            query = None
        if not isinstance(query, str):
            # The reply was not the JSON the schema asked for, so read the
            # whole reply as the query. That is what this node did before the
            # schema existed, and it keeps an endpoint that ignores
            # response_format producing something runnable.
            query = reply
        # The fence strip runs on either path. A model that honours the schema
        # can still put a fenced block inside the string it hands back.
        return _strip_code_fence(query)

    def _generate(question: str) -> str:
        prompt = CYPHER_GENERATION_PROMPT.format(
            schema=schema, question=question, limit=max_rows
        )
        return _ask(prompt)

    def _repair(question: str, query: str, error: str) -> str:
        prompt = CYPHER_REPAIR_PROMPT.format(
            schema=schema, question=question, query=query, error=error
        )
        return _ask(prompt)

    def cypher_node(state: AgentState) -> dict[str, Any]:
        question = state["question"]
        query = _generate(question)
        last_error = ""
        for attempt in range(repair_attempts + 1):
            try:
                _reject_writes(query)
                records, _, _ = driver.execute_query(
                    query,
                    database_=database,
                    routing_=RoutingControl.READ,
                )
            except Exception as error:  # noqa: BLE001 - fed back to the LLM
                last_error = str(error)
                if attempt < repair_attempts:
                    query = _repair(question, query, last_error)
                    continue
                return _record(
                    state,
                    "cypher_node",
                    f"Cypher failed.\n\nQuery:\n{query}\n\nError: {last_error}",
                )
            rows = [dict(record) for record in records]
            return _record(
                state,
                "cypher_node",
                f"Cypher:\n{query}\n\nRows ({len(rows)}):\n"
                f"{_rows_to_text(rows, max_rows)}",
            )
        return _record(state, "cypher_node", f"Cypher failed: {last_error}")

    return cypher_node


# =============================================================================
# graphrag_node
# =============================================================================

# Lifted from Lab 3 notebook 02. The vector hit lands on a Chunk; everything
# after WITH is the Cypher tail, and the tail is the reason this is GraphRAG
# rather than vector search. It walks two ways at once: sideways along
# NEXT_CHUNK so a procedure split across chunks arrives whole, and upward
# through the Document to the Aircraft the manual applies to and that
# aircraft's systems.
MANUAL_CONTEXT_QUERY = """
WITH node
OPTIONAL MATCH (previous:Chunk)-[:NEXT_CHUNK]->(node)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(following:Chunk)
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)-[:APPLIES_TO]->(a:Aircraft)-[:HAS_SYSTEM]->(s:System)
RETURN
    doc.documentId AS document_id,
    doc.aircraftType AS aircraft_type,
    COLLECT(DISTINCT a.tail_number)[0..5] AS aircraft,
    COLLECT(DISTINCT s.name)[0..5] AS systems,
    COALESCE(previous.text, '') AS previous_context,
    node.text AS context,
    COALESCE(following.text, '') AS next_context
"""


def format_manual_chunk(record: Any) -> Any:
    """Render a retrieved manual chunk as plain text.

    The default ``VectorCypherRetriever`` formatter sets ``content`` to
    ``str(record)``, which hands the LLM a printed ``neo4j.Record`` wrapper.
    Lab 3 solves the same problem with an HTML formatter because its results
    are displayed. These results are read by a model, so this one is text.

    Args:
        record: A ``neo4j.Record`` from :data:`MANUAL_CONTEXT_QUERY`.

    Returns:
        A ``RetrieverResultItem``.
    """
    from neo4j_graphrag.types import RetrieverResultItem

    aircraft_type = record.get("aircraft_type") or "unknown"
    systems = ", ".join(record.get("systems") or []) or "none recorded"
    tails = ", ".join(record.get("aircraft") or []) or "none recorded"
    body = " ".join(
        part
        for part in (
            record.get("previous_context") or "",
            record.get("context") or "",
            record.get("next_context") or "",
        )
        if part
    )
    content = (
        f"Document: {record.get('document_id')} (aircraft type {aircraft_type})\n"
        f"Applies to: {tails}\n"
        f"Systems: {systems}\n"
        f"Passage: {body}"
    )
    return RetrieverResultItem(
        content=content, metadata={"aircraft_type": aircraft_type}
    )


def vector_index_exists(driver: Any, index_name: str, database: str) -> bool:
    """Report whether a vector index of this name is online.

    Args:
        driver: A connected ``neo4j.Driver``.
        index_name: Index to look for.
        database: Neo4j database name.

    Returns:
        True when the index exists and is ONLINE.
    """
    records, _, _ = driver.execute_query(
        "SHOW INDEXES YIELD name, type, state "
        "WHERE name = $name AND type = 'VECTOR' AND state = 'ONLINE' "
        "RETURN count(*) AS found",
        name=index_name,
        database_=database,
    )
    return bool(records) and records[0]["found"] > 0


MISSING_INDEX_MESSAGE = (
    "The maintenance manual tool is not available. It reads the "
    "'{index}' vector index, which Lab 3 notebook 01 creates, and that index "
    "is not present on this Aura instance. Run "
    "Lab_3_Semantic_Search/01_data_and_embeddings.ipynb and this tool starts "
    "working. Until then the agent answers from telemetry and the graph alone."
)


def build_graphrag_node(
    driver: Any,
    llm: Any,
    embedder: Any,
    *,
    database: str,
    index_name: str = VECTOR_INDEX_NAME,
    retrieval_query: str = MANUAL_CONTEXT_QUERY,
    top_k: int = 3,
) -> Callable[[AgentState], dict[str, Any]]:
    """Build the node that answers from the maintenance manuals.

    A participant who skipped Lab 3 notebook 01 has no vector index, and
    ``VectorCypherRetriever`` raises when it cannot find one. Building the
    retriever eagerly would therefore turn a skipped notebook into a failure in
    this cell, several cells before the agent exists. So the index is checked
    first and the missing case returns a node that explains itself. The agent
    still builds, still runs, and answers with two tools.

    Args:
        driver: A connected ``neo4j.Driver``.
        llm: A ``data_utils.DatabricksLLM``.
        embedder: A ``data_utils.DatabricksEmbeddings``.
        database: Neo4j database name.
        index_name: Vector index to search.
        retrieval_query: The Cypher tail run after the vector hit.
        top_k: Chunks retrieved per question.

    Returns:
        A LangGraph node.
    """
    if not vector_index_exists(driver, index_name, database):
        message = MISSING_INDEX_MESSAGE.format(index=index_name)

        def graphrag_node_unavailable(state: AgentState) -> dict[str, Any]:
            return _record(state, "graphrag_node", message)

        graphrag_node_unavailable.available = False  # type: ignore[attr-defined]
        return graphrag_node_unavailable

    from neo4j_graphrag.generation import GraphRAG
    from neo4j_graphrag.retrievers import VectorCypherRetriever

    retriever = VectorCypherRetriever(
        driver=driver,
        neo4j_database=database,
        index_name=index_name,
        embedder=embedder,
        retrieval_query=retrieval_query,
        result_formatter=format_manual_chunk,
    )
    rag = GraphRAG(llm=llm, retriever=retriever)

    def graphrag_node(state: AgentState) -> dict[str, Any]:
        try:
            response = rag.search(
                state["question"],
                retriever_config={"top_k": top_k},
                return_context=True,
                response_fallback="No relevant maintenance procedures found.",
            )
        except Exception as error:  # noqa: BLE001 - reported, not raised
            return _record(
                state,
                "graphrag_node",
                f"Manual retrieval failed: {error}",
            )
        # retriever_result is absent when nothing cleared the similarity floor
        # and the fallback answered instead.
        items = getattr(response.retriever_result, "items", []) or []
        sources = ", ".join(
            sorted({str(item.metadata.get("aircraft_type")) for item in items})
        )
        return _record(
            state,
            "graphrag_node",
            f"{response.answer}\n\n(from {len(items)} manual passages, "
            f"aircraft types: {sources or 'unknown'})",
        )

    graphrag_node.available = True  # type: ignore[attr-defined]
    return graphrag_node


# =============================================================================
# supervisor and synthesize
# =============================================================================


def build_supervisor_node(
    llm: Any,
    *,
    available_tools: Sequence[str] = TOOL_NAMES,
    max_tool_calls: int = MAX_TOOL_CALLS,
    prompt: str = SUPERVISOR_PROMPT,
) -> Callable[[AgentState], dict[str, Any]]:
    """Build the routing node.

    Args:
        llm: A ``data_utils.DatabricksLLM``.
        available_tools: Tools the supervisor may name. Drop ``graphrag_node``
            from this when the vector index is absent and the supervisor stops
            offering an answer it cannot produce.
        max_tool_calls: Calls allowed before synthesis is forced.
        prompt: Routing prompt.

    Returns:
        A LangGraph node that sets ``route``.
    """
    allowed = (*available_tools, "synthesize")

    # ROUTE_SCHEMA names all three tools, and this agent may have only two, so
    # the enum is narrowed to what this agent was actually given. A schema the
    # model cannot leave is a better guard than a check after the fact, and the
    # check after the fact is kept anyway for the replies that arrive without
    # having gone through the schema at all.
    route_format = json_schema_format(
        "routing_decision",
        {
            **ROUTE_SCHEMA,
            "properties": {
                **ROUTE_SCHEMA["properties"],
                "next": {"type": "string", "enum": list(allowed)},
            },
        },
    )

    def supervisor_node(state: AgentState) -> dict[str, Any]:
        trace = state.get("trace", [])
        if len(trace) >= max_tool_calls:
            return {"route": "synthesize"}

        rendered = prompt.format(
            question=state["question"],
            called=", ".join(trace) or "(none yet)",
            findings=_format_findings(state.get("findings", [])),
        )
        decision = llm.invoke(rendered, response_format=route_format).content

        try:
            chosen = json.loads(decision)["next"]
        except (KeyError, TypeError, ValueError):
            chosen = None
        if chosen is not None:
            # A name outside available_tools becomes synthesize rather than a
            # call. graphrag_node is dropped from available_tools when the
            # participant has no vector index, and routing there anyway would
            # run a tool that can only report its own absence.
            return {"route": chosen if chosen in allowed else "synthesize"}

        # Nothing usable came back as JSON, so read the decision out of the
        # reply's own words. This is what the node did before the schema
        # existed, kept as the fallback because a participant who rewrites the
        # prompt, or points the lab at an endpoint that does not honour
        # response_format, should get the old behaviour rather than a crash.
        # The last tool named wins: a model that narrates before deciding
        # mentions several, and the last one is the one it settled on.
        chosen = "synthesize"
        best = -1
        for tool in allowed:
            position = decision.rfind(tool)
            if position > best:
                best, chosen = position, tool
        if best < 0:
            chosen = "synthesize"
        return {"route": chosen}

    return supervisor_node


def build_synthesize_node(
    llm: Any, *, prompt: str = SYNTHESIS_PROMPT
) -> Callable[[AgentState], dict[str, Any]]:
    """Build the node that writes the final answer.

    Args:
        llm: A ``data_utils.DatabricksLLM``.
        prompt: Synthesis prompt.

    Returns:
        A LangGraph node that sets ``answer``.
    """

    def synthesize_node(state: AgentState) -> dict[str, Any]:
        findings = state.get("findings", [])
        if not findings:
            return {"answer": "No tool returned anything for this question."}
        rendered = prompt.format(
            question=state["question"], findings=_format_findings(findings)
        )
        return {"answer": llm.invoke(rendered).content}

    return synthesize_node


def route_from_supervisor(state: AgentState) -> str:
    """Map the supervisor's decision onto the next node.

    Args:
        state: Current state.

    Returns:
        The name of the node to run next.
    """
    route = state.get("route", "synthesize")
    return route if route in TOOL_NAMES else "synthesize"


def build_neo4j_driver(uri: str, username: str, password: str) -> Any:
    """Open and verify a Neo4j driver.

    Kept here so the notebook never holds the password in a variable of its own.

    Args:
        uri: Aura connection URI.
        username: Neo4j user.
        password: Neo4j password.

    Returns:
        A connected ``neo4j.Driver``.
    """
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def open_driver_from_secrets(
    dbutils: Any, scope: str | None = None, *, spark: Any = None
) -> Any:
    """Open a Neo4j driver from the participant's secret scope.

    The three credential values are read, used, and dropped inside this
    function, so nothing in the notebook binds a password to a name.

    Args:
        dbutils: The notebook's dbutils handle.
        scope: Scope name. Derived from ``current_user()`` when omitted.
        spark: Active SparkSession, required when ``scope`` is omitted.

    Returns:
        A connected ``neo4j.Driver``.
    """
    if scope is None:
        if spark is None:
            raise ValueError("Pass either a scope name or a SparkSession.")
        scope = secret_scope_name(spark)
    credentials = read_neo4j_secrets(dbutils, scope)
    return build_neo4j_driver(
        credentials["uri"], credentials["username"], credentials["password"]
    )
