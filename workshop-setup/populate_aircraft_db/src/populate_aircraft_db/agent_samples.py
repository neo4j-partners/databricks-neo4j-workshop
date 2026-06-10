"""Simulate the Neo4j Aura Agent by sending natural language questions to the
configured LLM, generating Cypher or vector searches, and executing them."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from neo4j import Driver

_W = 70

# ---------------------------------------------------------------------------
# Graph schema description fed to the LLM for Cypher generation
# ---------------------------------------------------------------------------

GRAPH_SCHEMA = """\
Node labels and properties:
- Aircraft {aircraft_id, tail_number, icao24, model, manufacturer, operator}
- System {system_id, aircraft_id, type, name}  (type: Engine, Avionics, Hydraulics)
- Component {component_id, system_id, type, name}
- Sensor {sensor_id, system_id, type, name, unit}  (type: EGT, Vibration, N1Speed, FuelFlow)
- Reading {reading_id, sensor_id, timestamp, value}
- Airport {airport_id, name, city, country, iata, icao, lat, lon}
- Flight {flight_id, flight_number, aircraft_id, operator, origin, destination, scheduled_departure, scheduled_arrival}
- Delay {delay_id, cause, minutes}  (cause: Weather, Maintenance, Carrier, NAS)
- MaintenanceEvent {event_id, component_id, system_id, aircraft_id, fault, severity, reported_at, corrective_action}  (severity: MINOR, MAJOR, CRITICAL)
- Removal {removal_id, tracking_number, component_id, aircraft_id, removal_date, reason, work_order_number, technician_id, part_number, serial_number, tsn, flight_hours_at_removal, csn, replacement_required, shop_visit_required, warranty_status, removal_priority, cost_estimate, installation_date}
- Document {documentId, aircraftType, title, type}
- Chunk {text, index, embedding}
- AircraftModel {name, manufacturer}
- SystemReference {name, systemType, aircraftType}
- ComponentReference {name, componentType, partNumber, aircraftType}
- Fault {name, faultCode, severity, aircraftType}
- MaintenanceProcedure {name, procedureType, interval, aircraftType}
- OperatingLimit {name, parameterName, unit, regime, minValue, maxValue, aircraftType}

Relationships:
- (Aircraft)-[:HAS_SYSTEM]->(System)
- (System)-[:HAS_COMPONENT]->(Component)
- (System)-[:HAS_SENSOR]->(Sensor)
- (Sensor)-[:HAS_READING]->(Reading)
- (Component)-[:HAS_EVENT]->(MaintenanceEvent)
- (MaintenanceEvent)-[:AFFECTS_SYSTEM]->(System)
- (MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(Aircraft)
- (Aircraft)-[:OPERATES_FLIGHT]->(Flight)
- (Flight)-[:DEPARTS_FROM]->(Airport)
- (Flight)-[:ARRIVES_AT]->(Airport)
- (Flight)-[:HAS_DELAY]->(Delay)
- (Aircraft)-[:HAS_REMOVAL]->(Removal)
- (Removal)-[:REMOVED_COMPONENT]->(Component)
- (Document)-[:APPLIES_TO]->(Aircraft)
- (Chunk)-[:FROM_DOCUMENT]->(Document)
- (Chunk)-[:NEXT_CHUNK]->(Chunk)
- (AircraftModel)-[:DESCRIBES_MODEL]->(Aircraft)
- (SystemReference)-[:DESCRIBES_SYSTEM]->(System)
- (ComponentReference)-[:DESCRIBES_COMPONENT]->(Component)
- (AircraftModel)-[:HAS_SYSTEM]->(SystemReference)
- (SystemReference)-[:HAS_COMPONENT]->(ComponentReference)
- (ComponentReference)-[:HAS_FAULT]->(Fault)
- (Fault)-[:CORRECTED_BY]->(MaintenanceProcedure)
- (OperatingLimit)-[:FROM_CHUNK]->(Chunk)
- (Sensor)-[:HAS_LIMIT]->(OperatingLimit)

Sample tail numbers: N95040A (B737-800), N30268B (A320-200), N54980C (A321neo).
Operators: ExampleAir, SkyWays, RegionalCo, NorthernJet.
Airport IATA codes: JFK, LAX, ORD, ATL, DFW, DEN, SFO, SEA, MIA, BOS, MSP, DTW.
"""

SYSTEM_PROMPT = """\
You are an expert Neo4j Cypher query generator for an aircraft digital twin \
knowledge graph. Given a natural language question, generate a single Cypher \
query that answers it.

Rules:
- Return ONLY the Cypher query text. No explanation, no markdown, no commentary.
- Do NOT wrap the query in backticks or code fences.
- The very first character of your response must be a Cypher keyword (MATCH, OPTIONAL, WITH, CALL, UNWIND, RETURN).
- Use the schema provided to write correct queries.
- Always LIMIT results to 10 unless the question specifies otherwise.
- Use tail_number (not aircraft_id) when displaying aircraft to users.
- For general "tell me about" questions, return the node's key properties.
- For "summary" questions, aggregate with count/collect grouped by relevant fields.
- For date filtering use datetime() or string comparison on ISO timestamps.
- Do not use deprecated Cypher syntax. Use modern CALL subqueries where needed.

Graph schema:
""" + GRAPH_SCHEMA

VECTOR_SEARCH_PROMPT = """\
You are a query rewriter. Given a natural language question about aircraft \
maintenance, rewrite it as a short search phrase (3-8 words) optimized for \
semantic similarity search over maintenance manual chunks. Return ONLY the \
search phrase, nothing else."""

# ---------------------------------------------------------------------------
# Sample questions organized by agent tool type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SampleQuestion:
    question: str
    category: str
    tool: Literal["text2cypher", "similarity_search"]


SAMPLE_QUESTIONS: list[SampleQuestion] = [
    # -- Cypher Template style (answered via text2cypher) --
    SampleQuestion(
        "Tell me about aircraft N95040A",
        "Aircraft Overview",
        "text2cypher",
    ),
    SampleQuestion(
        "What are the sensor operating limits for N30268B?",
        "Sensor Operating Limits",
        "text2cypher",
    ),
    SampleQuestion(
        "Show the maintenance summary for N54980C",
        "Maintenance Summary",
        "text2cypher",
    ),
    SampleQuestion(
        "What faults do aircraft N95040A and N26760M share?",
        "Shared Faults",
        "text2cypher",
    ),
    SampleQuestion(
        "What maintenance manual applies to N30268B?",
        "Manual Lookup",
        "text2cypher",
    ),
    # -- Text2Cypher style --
    SampleQuestion(
        "Which aircraft has the most critical maintenance events?",
        "Maintenance Analysis",
        "text2cypher",
    ),
    SampleQuestion(
        "What are the top causes of flight delays?",
        "Delay Analysis",
        "text2cypher",
    ),
    SampleQuestion(
        "Which airports have the most delayed arrivals?",
        "Delay Analysis",
        "text2cypher",
    ),
    SampleQuestion(
        "Show all components in the hydraulics system",
        "Topology",
        "text2cypher",
    ),
    SampleQuestion(
        "Which sensors have operating limits defined?",
        "Cross-Domain",
        "text2cypher",
    ),
    SampleQuestion(
        "Trace the provenance of the EGT operating limit for B737-800",
        "Cross-Domain",
        "text2cypher",
    ),
    # -- Similarity Search style --
    SampleQuestion(
        "How do I troubleshoot engine vibration?",
        "Troubleshooting",
        "similarity_search",
    ),
    SampleQuestion(
        "What are the EGT limits during takeoff?",
        "Operating Limits",
        "similarity_search",
    ),
    SampleQuestion(
        "What is the engine inspection schedule?",
        "Scheduled Maintenance",
        "similarity_search",
    ),
]


# ---------------------------------------------------------------------------
# Formatting helpers (matching samples.py style)
# ---------------------------------------------------------------------------


def _header(title: str, description: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'=' * _W}")
    print(f"\n  {description}\n")


def _cypher_block(query: str) -> None:
    lines = query.strip().splitlines()
    indents = [len(ln) - len(ln.lstrip()) for ln in lines if ln.strip()]
    base = min(indents) if indents else 0
    print("  Generated Cypher:")
    for ln in lines:
        print(f"    {ln[base:]}")
    print()


def _result_table(records: list[dict[str, Any]], max_rows: int = 10) -> None:
    if not records:
        print("  (no results)\n")
        return
    keys = list(records[0].keys())
    widths = []
    for k in keys:
        col_max = len(k)
        for row in records[:max_rows]:
            col_max = max(col_max, len(str(row.get(k, ""))))
        widths.append(min(col_max + 1, 50))
    print("  " + "  ".join(k.ljust(w) for k, w in zip(keys, widths, strict=False)))
    print("  " + "  ".join("\u2500" * w for w in widths))
    for row in records[:max_rows]:
        cells = []
        for k, w in zip(keys, widths, strict=False):
            s = str(row.get(k, "")) if row.get(k) is not None else "\u2014"
            if len(s) > w:
                s = s[: w - 1] + "\u2026"
            cells.append(s.ljust(w))
        print("  " + "  ".join(cells))
    print()


# ---------------------------------------------------------------------------
# LLM client abstraction
# ---------------------------------------------------------------------------


def _create_llm_client(
    provider: str,
    *,
    openai_key: str | None = None,
    anthropic_key: str | None = None,
    llm_model: str,
    embedding_model: str,
    embedding_dimensions: int,
):
    """Return an LLM callable and an embed callable based on the provider."""

    if provider == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=openai_key)

        def chat(system: str, user: str) -> str:
            resp = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_completion_tokens=1000,
            )
            return resp.choices[0].message.content or ""

        def embed(text: str) -> list[float]:
            resp = client.embeddings.create(
                model=embedding_model,
                input=text,
                dimensions=embedding_dimensions,
            )
            return resp.data[0].embedding

    elif provider == "anthropic":
        import anthropic
        from openai import OpenAI

        anth_client = anthropic.Anthropic(api_key=anthropic_key)
        oai_client = OpenAI(api_key=openai_key)

        def chat(system: str, user: str) -> str:
            resp = anth_client.messages.create(
                model=llm_model,
                max_tokens=1000,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return resp.content[0].text

        def embed(text: str) -> list[float]:
            resp = oai_client.embeddings.create(
                model=embedding_model,
                input=text,
                dimensions=embedding_dimensions,
            )
            return resp.data[0].embedding

    else:
        raise ValueError(f"Unknown provider: {provider!r}")

    return chat, embed


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------


def _extract_cypher(raw: str) -> str:
    """Extract a Cypher query from LLM output, stripping markdown fencing and preamble."""
    text = raw.strip()
    # Strip markdown fencing if present
    if "```" in text:
        lines = text.splitlines()
        in_block = False
        block_lines: list[str] = []
        for ln in lines:
            stripped = ln.strip()
            if stripped.startswith("```"):
                if in_block:
                    break
                in_block = True
                continue
            if in_block:
                block_lines.append(ln)
        if block_lines:
            return "\n".join(block_lines).strip()
    # If no fencing, find the first line that looks like Cypher
    for i, ln in enumerate(text.splitlines()):
        upper = ln.strip().upper()
        if upper.startswith(("MATCH", "OPTIONAL", "WITH", "CALL", "UNWIND", "RETURN", "CREATE", "MERGE")):
            return "\n".join(text.splitlines()[i:]).strip()
    return text


_MAX_RETRIES = 2


def _run_text2cypher(
    driver: Driver,
    chat_fn,
    question: str,
) -> None:
    """Send a question to the LLM, generate Cypher, and execute it."""
    print(f"  Question: \"{question}\"\n")

    cypher = ""
    for attempt in range(_MAX_RETRIES):
        raw = chat_fn(SYSTEM_PROMPT, question).strip()
        cypher = _extract_cypher(raw)
        if cypher:
            break
        if attempt < _MAX_RETRIES - 1:
            print("  (empty response, retrying...)")

    if not cypher:
        print("  [SKIP] LLM returned empty Cypher after retries.\n")
        return

    _cypher_block(cypher)

    try:
        records, _, _ = driver.execute_query(cypher)
        rows = [dict(r) for r in records]
        _result_table(rows)
    except Exception as exc:
        print(f"  [ERROR] Cypher execution failed: {exc}\n")


def _run_similarity_search(
    driver: Driver,
    chat_fn,
    embed_fn,
    question: str,
    top_k: int = 5,
) -> None:
    """Embed the question and run a vector similarity search over chunks."""
    print(f"  Question: \"{question}\"\n")

    # Rewrite question into a search phrase
    search_phrase = chat_fn(VECTOR_SEARCH_PROMPT, question).strip()
    print(f"  Search phrase: \"{search_phrase}\"\n")

    embedding = embed_fn(search_phrase)

    query = """\
CALL db.index.vector.queryNodes(
    'maintenanceChunkEmbeddings', $top_k, $embedding
) YIELD node, score
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
RETURN score,
       doc.documentId AS document,
       doc.aircraftType AS aircraft_type,
       node.index AS chunk_idx,
       substring(node.text, 0, 120) AS preview
ORDER BY score DESC
LIMIT $top_k"""

    print("  Generated Cypher:")
    for ln in query.strip().splitlines():
        print(f"    {ln}")
    print()

    try:
        records, _, _ = driver.execute_query(
            query, embedding=embedding, top_k=top_k,
        )
        rows = [dict(r) for r in records]
        if rows:
            for r in rows:
                r["score"] = f"{r['score']:.4f}"
        _result_table(rows)
    except Exception as exc:
        print(f"  [ERROR] Vector search failed: {exc}\n")
        print("  (vector index may not be available \u2014 run 'setup' first)\n")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_agent_samples(
    driver: Driver,
    *,
    provider: str,
    openai_key: str | None = None,
    anthropic_key: str | None = None,
    llm_model: str,
    embedding_model: str,
    embedding_dimensions: int,
    sample_size: int = 0,
) -> None:
    """Run all agent sample questions with LLM-generated Cypher."""
    chat_fn, embed_fn = _create_llm_client(
        provider,
        openai_key=openai_key,
        anthropic_key=anthropic_key,
        llm_model=llm_model,
        embedding_model=embedding_model,
        embedding_dimensions=embedding_dimensions,
    )

    questions = SAMPLE_QUESTIONS
    if sample_size > 0:
        questions = questions[:sample_size]

    print(f"\n{'#' * _W}")
    print("  Aircraft Digital Twin \u2014 Agent Simulation")
    print(f"{'#' * _W}")
    print(f"\n  LLM: {provider}/{llm_model}")
    print(f"  Questions: {len(questions)}\n")

    current_category = ""
    for i, sq in enumerate(questions, 1):
        if sq.category != current_category:
            current_category = sq.category
            _header(f"{i}. [{sq.tool}] {sq.category}", f"Tool: {sq.tool}")

        if sq.tool == "text2cypher":
            _run_text2cypher(driver, chat_fn, sq.question)
        elif sq.tool == "similarity_search":
            _run_similarity_search(driver, chat_fn, embed_fn, sq.question)

    print(f"{'#' * _W}")
    print("  Agent simulation complete.")
    print(f"{'#' * _W}\n")
