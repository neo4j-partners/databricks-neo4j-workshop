"""SimpleKGPipeline-based document enrichment: chunking, embedding, and entity extraction."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from neo4j import Driver
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.base import TextSplitter
from neo4j_graphrag.experimental.components.types import TextChunks

# Labels for extracted entity nodes (used by clear/verify logic).
EXTRACTED_LABELS = [
    "AircraftModel",
    "SystemReference",
    "ComponentReference",
    "Fault",
    "MaintenanceProcedure",
    "OperatingLimit",
]

# ---------------------------------------------------------------------------
# Document metadata registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DocumentMeta:
    filename: str
    document_id: str
    aircraft_type: str
    title: str


DOCUMENTS: list[DocumentMeta] = [
    DocumentMeta(
        filename="MAINTENANCE_A320.md",
        document_id="AMM-A320-2024-001",
        aircraft_type="A320-200",
        title="A320-200 Maintenance and Troubleshooting Manual",
    ),
    DocumentMeta(
        filename="MAINTENANCE_A321neo.md",
        document_id="AMM-A321neo-2024-001",
        aircraft_type="A321neo",
        title="A321neo Maintenance and Troubleshooting Manual",
    ),
    DocumentMeta(
        filename="MAINTENANCE_B737.md",
        document_id="AMM-B737-2024-001",
        aircraft_type="B737-800",
        title="B737-800 Maintenance and Troubleshooting Manual",
    ),
    DocumentMeta(
        filename="MAINTENANCE_E190.md",
        document_id="AMM-E190-2024-001",
        aircraft_type="E190",
        title="E190 Maintenance and Troubleshooting Manual",
    ),
    DocumentMeta(
        filename="MAINTENANCE_A220.md",
        document_id="AMM-A220-2024-001",
        aircraft_type="A220-300",
        title="A220-300 Maintenance and Troubleshooting Manual",
    ),
]


# ---------------------------------------------------------------------------
# Context-aware text splitter
# ---------------------------------------------------------------------------


class ContextPrependingSplitter(TextSplitter):
    """Wraps a ``TextSplitter`` and prepends a context line to every chunk.

    **Why this is necessary:**  ``SimpleKGPipeline`` passes ``document_metadata``
    (which includes the aircraft type) only to the lexical graph builder for
    storage on ``Document`` nodes — it is never injected into the LLM extraction
    prompt.  The LLM sees only the raw chunk text.  After the inner splitter
    divides a 30 000-character maintenance manual into ~40 chunks of ~800
    characters, most chunks land deep in engine-specific sections where the
    engine designation (e.g. "LEAP-1A") dominates and the aircraft model
    (e.g. "A321neo") is never mentioned.  Without explicit context, the LLM
    confuses engine types for aircraft types, breaking downstream cross-links
    that match on ``OperatingLimit.aircraftType == Aircraft.model``.

    This wrapper solves the problem by delegating splitting to the inner
    splitter, then prepending a short context header to *every* resulting
    chunk so the LLM always has access to the document-level aircraft type.

    Set :attr:`context` before each call to ``pipeline.run_async()``.
    """

    def __init__(self, inner: TextSplitter, context: str = "") -> None:
        self.inner = inner
        self.context = context

    async def run(self, text: str) -> TextChunks:
        result = await self.inner.run(text)
        if self.context:
            for chunk in result.chunks:
                chunk.text = self.context + chunk.text
        return result


# ---------------------------------------------------------------------------
# Dimension-aware embedder wrapper
# ---------------------------------------------------------------------------


class DimensionAwareOpenAIEmbeddings(OpenAIEmbeddings):
    """OpenAIEmbeddings that always passes ``dimensions`` to the API.

    The pipeline's ``TextChunkEmbedder`` calls ``embed_query(text)`` without
    a ``dimensions`` kwarg, so we override to inject it automatically.
    """

    def __init__(self, dimensions: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._dimensions = dimensions

    def embed_query(self, text: str, **kwargs: Any) -> list[float]:
        return super().embed_query(text, dimensions=self._dimensions, **kwargs)


# ---------------------------------------------------------------------------
# Extraction prompt template
# ---------------------------------------------------------------------------

# Custom prompt that teaches the LLM domain reasoning for aircraft maintenance
# manuals and keeps extracted manual entities model-scoped.
#
# Placeholders: {schema}, {examples}, {text} (required by ERExtractionTemplate).
# Literal braces must be doubled for Python str.format().

EXTRACTION_PROMPT = """\
You are an expert aviation engineer extracting structured maintenance-manual \
knowledge to build an aircraft digital twin graph.

Your task: extract entities (nodes) and relationships from the input text \
according to the schema below.

Return result as JSON using this format:
{{"nodes": [
  {{"id": "0", "label": "AircraftModel", "properties": {{"name": "A320-200"}}}},
  {{"id": "1", "label": "ComponentReference", "properties": {{"name": "EGT Sensor - A320-200", "componentType": "EGT Sensor", "aircraftType": "A320-200"}}}},
  {{"id": "2", "label": "OperatingLimit", "properties": {{"name": "EGT - A320-200", "parameterName": "EGT", "aircraftType": "A320-200", "unit": "°C", "maxValue": "695"}}}}
],
"relationships": [
  {{"start_node_id": "1", "end_node_id": "2", "type": "HAS_LIMIT", "properties": {{}}}}
]}}

Use only the following node and relationship types:
{schema}

IMPORTANT RULES:

1. DOCUMENT CONTEXT: The input text starts with a [DOCUMENT CONTEXT] line \
that identifies the aircraft type and title. Use the aircraft type from this \
context line as the `aircraftType` property on every extracted entity except \
AircraftModel, where it is the `name`.

2. AIRCRAFT TYPE vs ENGINE MODEL: The `aircraftType` property must be the \
airframe model (the aircraft you fly, e.g. A320-200, A321neo, B737-800), \
NOT the engine designation (e.g. V2500, LEAP-1A, CFM56-7B, PW1100G). \
Maintenance manuals are organized by aircraft type. Engine models appear \
throughout the text but they are components OF the aircraft, not the \
aircraft type itself.

3. EXTRACT USEFUL MANUAL KNOWLEDGE: Extract aircraft models, systems, \
components, faults, procedures, and operating limits when they are explicitly \
mentioned in the text. Do not invent part numbers, fault codes, intervals, or \
limits that are not present.

4. PARAMETER NAMES: For OperatingLimit, `parameterName` should use short \
sensor names from monitoring tables (e.g. EGT, Vibration, N1Speed, FuelFlow). \
Prefer concise sensor-style names over verbose descriptions.

5. ENTITY NAME FORMAT: For SystemReference, ComponentReference, Fault, \
MaintenanceProcedure, and OperatingLimit, the `name` property must follow \
"<specific name> - <aircraftType>" (e.g. "EGT - A320-200"). AircraftModel \
uses the aircraft type only (e.g. "A320-200"). This prevents cross-model \
entity resolution mistakes.

6. RELATIONSHIPS: Create relationships only when the text supports them. \
Prefer the schema patterns: AircraftModel HAS_SYSTEM SystemReference, \
SystemReference HAS_COMPONENT ComponentReference, ComponentReference HAS_FAULT \
Fault, Fault CORRECTED_BY MaintenanceProcedure, and component/system HAS_LIMIT \
OperatingLimit.

Assign a unique ID (string) to each node and reuse it for relationships.

Output rules:
- Return ONLY the JSON object, no additional text.
- Omit any backticks — output raw JSON.
- The JSON must be a single object, not wrapped in a list.
- Property names must be in double quotes.
- Property values must be strings, numbers, booleans, or arrays of those values.
- Omit unknown or unavailable properties; do not use null or nested objects.

{examples}

Input text:

{text}
"""


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------


def _create_extraction_llm(
    *,
    provider: str,
    openai_api_key: str | None,
    anthropic_api_key: str | None,
    llm_model: str,
    llm_max_tokens: int,
):
    """Create the LLM used for maintenance-manual entity extraction."""
    if provider == "openai":
        from neo4j_graphrag.llm.openai_llm import OpenAILLM

        return OpenAILLM(
            model_name=llm_model,
            model_params={
                "max_completion_tokens": llm_max_tokens,
                "response_format": {"type": "json_object"},
            },
            api_key=openai_api_key,
        )
    if provider == "anthropic":
        from neo4j_graphrag.llm.anthropic_llm import AnthropicLLM

        return AnthropicLLM(
            model_name=llm_model,
            model_params={"max_tokens": llm_max_tokens},
            api_key=anthropic_api_key,
        )
    raise ValueError(f"Unknown LLM provider: {provider!r}")


def _create_pipeline(
    driver: Driver,
    *,
    provider: str,
    openai_api_key: str | None,
    anthropic_api_key: str | None,
    llm_model: str,
    llm_max_tokens: int,
    embedding_model: str,
    embedding_dimensions: int,
    chunk_size: int,
    chunk_overlap: int,
):
    """Build a ``SimpleKGPipeline`` configured for maintenance-manual enrichment."""
    from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
        FixedSizeSplitter,
    )
    from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline

    from .schema import build_extraction_schema

    # --- LLM ---
    llm = _create_extraction_llm(
        provider=provider,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        llm_model=llm_model,
        llm_max_tokens=llm_max_tokens,
    )

    # --- Embedder ---
    embedder = DimensionAwareOpenAIEmbeddings(
        dimensions=embedding_dimensions,
        model=embedding_model,
        api_key=openai_api_key,
    )

    # --- Text splitter (with per-chunk context injection) ---
    inner_splitter = FixedSizeSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        approximate=True,
    )
    splitter = ContextPrependingSplitter(inner_splitter)

    # --- Schema ---
    schema = build_extraction_schema()

    pipeline = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        schema=schema,
        text_splitter=splitter,
        from_file=False,
        on_error="IGNORE",
        perform_entity_resolution=True,
        prompt_template=EXTRACTION_PROMPT,
    )
    return pipeline, splitter


def debug_extract_chunks(
    document_dir: Path,
    *,
    filename: str,
    chunk_indexes: list[int],
    provider: str,
    openai_api_key: str | None,
    anthropic_api_key: str | None,
    llm_model: str,
    llm_max_tokens: int,
    chunk_size: int,
    chunk_overlap: int,
) -> bool:
    """Run extractor validation for selected chunks without writing to Neo4j."""
    from neo4j_graphrag.experimental.components.entity_relation_extractor import (
        LLMEntityRelationExtractor,
        OnError,
    )
    from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
        FixedSizeSplitter,
    )

    from .schema import build_extraction_schema

    meta = next((doc for doc in DOCUMENTS if doc.filename == filename), None)
    if meta is None:
        names = ", ".join(doc.filename for doc in DOCUMENTS)
        raise ValueError(f"Unknown document {filename!r}. Expected one of: {names}")

    llm = _create_extraction_llm(
        provider=provider,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        llm_model=llm_model,
        llm_max_tokens=llm_max_tokens,
    )
    extractor = LLMEntityRelationExtractor(
        llm=llm,
        prompt_template=EXTRACTION_PROMPT,
        create_lexical_graph=False,
        on_error=OnError.RAISE,
        use_structured_output=llm.supports_structured_output,
    )
    splitter = ContextPrependingSplitter(
        FixedSizeSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            approximate=True,
        ),
        context=(
            f"[DOCUMENT CONTEXT] Aircraft Type: {meta.aircraft_type} | "
            f"Title: {meta.title}\n\n"
        ),
    )
    schema = build_extraction_schema()

    async def _run() -> bool:
        text = (document_dir / filename).read_text(encoding="utf-8").strip()
        chunks = await splitter.run(text)
        print(f"Document: {filename}")
        print(f"Total chunks: {len(chunks.chunks)}")
        print(f"LLM: {provider}/{llm_model} max_tokens={llm_max_tokens}")

        ok = True
        for index in chunk_indexes:
            if index < 0 or index >= len(chunks.chunks):
                print(f"  [FAIL] chunk_index={index} is out of range")
                ok = False
                continue
            chunk = chunks.chunks[index]
            try:
                graph = await extractor.extract_for_chunk(schema, "", chunk)
            except Exception as exc:
                print(f"  [FAIL] chunk_index={index}: {exc}")
                ok = False
                continue
            print(
                f"  [OK] chunk_index={index}: "
                f"{len(graph.nodes)} nodes, {len(graph.relationships)} relationships"
            )
        return ok

    return asyncio.run(_run())


# ---------------------------------------------------------------------------
# Document processing
# ---------------------------------------------------------------------------


def process_all_documents(
    driver: Driver,
    document_dir: Path,
    *,
    provider: str,
    openai_api_key: str | None,
    anthropic_api_key: str | None,
    llm_model: str,
    llm_max_tokens: int,
    embedding_model: str,
    embedding_dimensions: int,
    chunk_size: int,
    chunk_overlap: int,
    enrich_sample_size: int = 0,
) -> None:
    """Run the SimpleKGPipeline over every maintenance manual.

    When *enrich_sample_size* > 0 the input text for each document is truncated
    so that approximately that many chunks are produced.  Useful for quick test
    runs without processing the full manuals.
    """
    pipeline, splitter = _create_pipeline(
        driver,
        provider=provider,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        llm_model=llm_model,
        llm_max_tokens=llm_max_tokens,
        embedding_model=embedding_model,
        embedding_dimensions=embedding_dimensions,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Pre-compute max text length when sample size is set.
    # Each chunk beyond the first advances by (chunk_size - chunk_overlap) chars.
    if enrich_sample_size > 0:
        max_chars = chunk_size + (enrich_sample_size - 1) * (chunk_size - chunk_overlap)
    else:
        max_chars = 0  # 0 = unlimited

    async def _run_all():
        for meta in DOCUMENTS:
            print(f"\nProcessing: {meta.filename}")
            filepath = document_dir / meta.filename
            text = filepath.read_text(encoding="utf-8").strip()
            print(f"  Read {len(text):,} characters.")

            if max_chars and len(text) > max_chars:
                text = text[:max_chars]
                print(f"  Truncated to {max_chars:,} chars (~{enrich_sample_size} chunks).")

            # Update the splitter's context so every chunk the LLM sees starts
            # with the aircraft type.  The custom EXTRACTION_PROMPT instructs
            # the LLM to read this header.
            splitter.context = (
                f"[DOCUMENT CONTEXT] Aircraft Type: {meta.aircraft_type} | "
                f"Title: {meta.title}\n\n"
            )

            await pipeline.run_async(
                text=text,
                document_metadata={
                    "documentId": meta.document_id,
                    "aircraftType": meta.aircraft_type,
                    "title": meta.title,
                    "type": "maintenance_manual",
                    "path": meta.filename,
                },
            )
            print(f"  [OK] Pipeline complete for {meta.document_id}")

    asyncio.run(_run_all())


# ---------------------------------------------------------------------------
# Cross-links to existing operational graph
# ---------------------------------------------------------------------------


def link_to_existing_graph(driver: Driver) -> None:
    """Create relationships between enrichment data and the operational graph."""

    # Document -[:APPLIES_TO]-> Aircraft (via document metadata aircraftType)
    records, _, _ = driver.execute_query("""
        MATCH (d:Document) WHERE d.aircraftType IS NOT NULL
        MATCH (a:Aircraft {model: d.aircraftType})
        MERGE (d)-[:APPLIES_TO]->(a)
        RETURN count(*) AS count
    """)
    print(f"  [OK] {records[0]['count']} Document -[:APPLIES_TO]-> Aircraft")

    # AircraftModel -[:DESCRIBES_MODEL]-> Aircraft
    # (model-level manual entity to tail-level fleet)
    records, _, _ = driver.execute_query("""
        MATCH (am:AircraftModel)
        MATCH (a:Aircraft {model: am.name})
        MERGE (am)-[:DESCRIBES_MODEL]->(a)
        RETURN count(*) AS count
    """)
    print(f"  [OK] {records[0]['count']} AircraftModel -[:DESCRIBES_MODEL]-> Aircraft")

    # SystemReference -[:DESCRIBES_SYSTEM]-> System
    # (conservative model + system type/name match)
    records, _, _ = driver.execute_query("""
        MATCH (sr:SystemReference)
        WHERE sr.aircraftType IS NOT NULL
        WITH sr, toLower(replace(sr.name, ' - ' + sr.aircraftType, '')) AS refName
        MATCH (a:Aircraft {model: sr.aircraftType})-[:HAS_SYSTEM]->(s:System)
        WHERE toLower(s.type) = toLower(coalesce(sr.systemType, ''))
           OR toLower(s.name) = refName
        MERGE (sr)-[:DESCRIBES_SYSTEM]->(s)
        RETURN count(*) AS count
    """)
    print(f"  [OK] {records[0]['count']} SystemReference -[:DESCRIBES_SYSTEM]-> System")

    # ComponentReference -[:DESCRIBES_COMPONENT]-> Component
    # (model + component type/name match)
    records, _, _ = driver.execute_query("""
        MATCH (cr:ComponentReference)
        WHERE cr.aircraftType IS NOT NULL
        WITH cr,
             toLower(replace(cr.name, ' - ' + cr.aircraftType, '')) AS refName,
             toLower(coalesce(cr.componentType, '')) AS refType
        MATCH (a:Aircraft {model: cr.aircraftType})
            -[:HAS_SYSTEM]->(:System)
            -[:HAS_COMPONENT]->(c:Component)
        WHERE toLower(c.type) IN [refName, refType]
           OR toLower(c.name) IN [refName, refType]
        MERGE (cr)-[:DESCRIBES_COMPONENT]->(c)
        RETURN count(*) AS count
    """)
    print(
        f"  [OK] {records[0]['count']} "
        "ComponentReference -[:DESCRIBES_COMPONENT]-> Component"
    )

    # Sensor -[:HAS_LIMIT]-> OperatingLimit (match parameterName + aircraftType)
    records, _, _ = driver.execute_query("""
        MATCH (a:Aircraft)-[:HAS_SYSTEM]->(sys:System)-[:HAS_SENSOR]->(s:Sensor)
        MATCH (ol:OperatingLimit {parameterName: s.type, aircraftType: a.model})
        MERGE (s)-[:HAS_LIMIT]->(ol)
        RETURN count(*) AS count
    """)
    print(f"  [OK] {records[0]['count']} Sensor -[:HAS_LIMIT]-> OperatingLimit")


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


def clear_enrichment_data(driver: Driver) -> None:
    """Delete all Document, Chunk, and extracted entity nodes (preserves operational graph)."""
    labels_to_clear = ["Document", "Chunk"] + EXTRACTED_LABELS
    deleted_total = 0

    print("Clearing enrichment data (Documents, Chunks, extracted entities)...")
    for label in labels_to_clear:
        while True:
            records, _, _ = driver.execute_query(
                f"MATCH (n:{label}) WITH n LIMIT 500 DETACH DELETE n RETURN count(*) AS deleted"
            )
            count = records[0]["deleted"]
            deleted_total += count
            if count == 0:
                break

    # Clean up __Entity__ and __KGBuilder__ labeled nodes left by the pipeline
    for label in ["__Entity__", "__KGBuilder__"]:
        while True:
            records, _, _ = driver.execute_query(
                f"MATCH (n:{label}) WITH n LIMIT 500 DETACH DELETE n RETURN count(*) AS deleted"
            )
            count = records[0]["deleted"]
            deleted_total += count
            if count == 0:
                break

    print(f"  [OK] Cleared {deleted_total} enrichment nodes.")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_SAMPLE_SIZE = 5


def _get_existing_schema_tokens(driver: Driver) -> tuple[set[str], set[str]]:
    """Return labels and relationship types currently present in the graph."""
    label_rows, _, _ = driver.execute_query("CALL db.labels() YIELD label RETURN label")
    rel_rows, _, _ = driver.execute_query(
        "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
    )
    return (
        {row["label"] for row in label_rows},
        {row["relationshipType"] for row in rel_rows},
    )


def validate_enrichment(driver: Driver) -> None:
    """Run sample queries to verify embeddings, entities, and cross-links."""

    print(f"\nValidation (sample size {_SAMPLE_SIZE}):")
    labels, rel_types = _get_existing_schema_tokens(driver)

    # 1. Chunks with embeddings linked to documents
    rows = []
    if {"Chunk", "Document"}.issubset(labels) and "FROM_DOCUMENT" in rel_types:
        rows, _, _ = driver.execute_query(f"""
            MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
            WHERE c.embedding IS NOT NULL
            RETURN DISTINCT d.documentId AS doc, elementId(c) AS chunk_id, size(c.embedding) AS dims
            LIMIT {_SAMPLE_SIZE}
        """)
    print(f"\n  Chunks with embeddings -> Document ({len(rows)} samples):")
    for r in rows:
        print(f"    {r['chunk_id'][:12]}...  dims={r['dims']}  doc={r['doc']}")
    if not rows:
        print("    [WARN] No chunks with embeddings found!")

    # 2. Extracted manual entities
    rows, _, _ = driver.execute_query(
        """
        UNWIND $labels AS label
        OPTIONAL MATCH (n)
        WHERE label IN labels(n)
        RETURN label, count(n) AS count
        ORDER BY label
        """,
        labels=EXTRACTED_LABELS,
    )
    print("\n  Extracted manual entities:")
    for r in rows:
        print(f"    {r['label']}: {r['count']}")

    # 3. Cross-links to operational graph
    if "Aircraft" not in labels:
        print("\n  Cross-links to operational graph:")
        print("    [WARN] No Aircraft nodes found. Run `uv run populate-aircraft-db setup`")
        print("           or load CSV data before running enrichment-only validation.")
        return

    queries = [
        (
            "Document -[:APPLIES_TO]-> Aircraft",
            "MATCH (d:Document)-[:APPLIES_TO]->(a:Aircraft) "
            f"RETURN d.title AS src, a.tail_number AS tgt LIMIT {_SAMPLE_SIZE}",
        ),
        (
            "AircraftModel -[:DESCRIBES_MODEL]-> Aircraft",
            "MATCH (am:AircraftModel)-[:DESCRIBES_MODEL]->(a:Aircraft) "
            f"RETURN am.name AS src, a.tail_number AS tgt LIMIT {_SAMPLE_SIZE}",
        ),
        (
            "ComponentReference -[:DESCRIBES_COMPONENT]-> Component",
            "MATCH (cr:ComponentReference)-[:DESCRIBES_COMPONENT]->(c:Component) "
            f"RETURN cr.name AS src, c.name AS tgt LIMIT {_SAMPLE_SIZE}",
        ),
        (
            "Sensor -[:HAS_LIMIT]-> OperatingLimit",
            "MATCH (s:Sensor)-[:HAS_LIMIT]->(ol:OperatingLimit) "
            f"RETURN s.type AS src, ol.name AS tgt LIMIT {_SAMPLE_SIZE}",
        ),
    ]
    print("\n  Cross-links to operational graph:")
    for label, query in queries:
        if label.startswith("Document") and not {
            "Document",
            "Aircraft",
            "APPLIES_TO",
        }.issubset(labels | rel_types):
            rows = []
        elif label.startswith("AircraftModel") and not {
            "AircraftModel",
            "Aircraft",
            "DESCRIBES_MODEL",
        }.issubset(labels | rel_types):
            rows = []
        elif label.startswith("ComponentReference") and not {
            "ComponentReference",
            "Component",
            "DESCRIBES_COMPONENT",
        }.issubset(labels | rel_types):
            rows = []
        elif label.startswith("Sensor") and not {
            "Sensor",
            "OperatingLimit",
            "HAS_LIMIT",
        }.issubset(labels | rel_types):
            rows = []
        else:
            rows, _, _ = driver.execute_query(query)
        if rows:
            pairs = ", ".join(f"{r['src']}->{r['tgt']}" for r in rows)
            print(f"    {label}: {pairs}")
        else:
            print(f"    {label}: (none)")
