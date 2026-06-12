"""Utilities for data loading, Neo4j operations, and Databricks AI services.

This module provides embedding generation using Databricks Foundation Model APIs
(hosted models like BGE and GTE) which are pre-deployed and ready to use.

Available Databricks Embedding Models:
- databricks-bge-large-en: 1024 dimensions, 512 token context
- databricks-gte-large-en: 1024 dimensions, 8192 token context

These models use OpenAI-compatible API format and are accessed via
the MLflow deployments client when running in Databricks.
"""

import asyncio
import concurrent.futures
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import mlflow.deployments
from neo4j import GraphDatabase, Record
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.experimental.components.text_splitters.base import TextSplitter
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.experimental.components.types import TextChunks
from neo4j_graphrag.llm.base import LLMInterface, LLMInterfaceV2
from neo4j_graphrag.llm.types import LLMResponse
from neo4j_graphrag.types import LLMMessage, RetrieverResultItem


# =============================================================================
# Default Model Configuration
# =============================================================================

DEFAULT_EMBEDDING_MODEL = "databricks-bge-large-en"
DEFAULT_LLM_MODEL = "databricks-meta-llama-3-3-70b-instruct"


# =============================================================================
# Databricks Embeddings
# =============================================================================

class DatabricksEmbeddings(Embedder):
    """Generate embeddings using Databricks Foundation Model APIs.

    Databricks provides pre-deployed embedding models as part of the
    Foundation Model APIs. These are ready to use without deployment.

    Available Models:
    - databricks-bge-large-en: 1024 dims, 512 token context
    - databricks-gte-large-en: 1024 dims, 8192 token context

    API Format (OpenAI-Compatible):
        Input:  {"input": ["text1", "text2"]}
        Output: {"data": [{"embedding": [0.1, ...]}, ...]}

    Example:
        >>> embedder = DatabricksEmbeddings(model_id="databricks-bge-large-en")
        >>> embedding = embedder.embed_query("test text")
        >>> len(embedding)
        1024
    """

    def __init__(self, model_id: str = "databricks-bge-large-en"):
        """Initialize the Databricks embeddings provider.

        Args:
            model_id: The Databricks Foundation Model endpoint name.
                      Default: databricks-bge-large-en (1024 dimensions)
        """
        self.model_id = model_id
        self._client = mlflow.deployments.get_deploy_client("databricks")

    def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single text string.

        Uses the MLflow deployments client to call the Databricks
        Foundation Model API with OpenAI-compatible format.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector (1024 dimensions)
        """
        response = self._client.predict(
            endpoint=self.model_id,
            inputs={"input": [text]},
        )
        return response["data"][0]["embedding"]


# =============================================================================
# Databricks LLM
# =============================================================================

class DatabricksLLM(LLMInterface, LLMInterfaceV2):
    """LLM interface using Databricks Foundation Model APIs.

    Implements both LLMInterface (for SimpleKGPipeline) and LLMInterfaceV2
    (for GraphRAG and LangChain compatibility).

    Supports Databricks-hosted LLM endpoints like:
    - databricks-meta-llama-3-3-70b-instruct
    - databricks-llama-4-maverick

    Uses MLflow deployments client for API calls.
    """

    def __init__(self, model_id: str = "databricks-meta-llama-3-3-70b-instruct"):
        """Initialize the Databricks LLM provider.

        Args:
            model_id: The Databricks Foundation Model endpoint name.
        """
        LLMInterfaceV2.__init__(self, model_name=model_id)
        self.model_id = model_id
        self._client = mlflow.deployments.get_deploy_client("databricks")

    def _predict(self, messages: list[dict[str, str]]) -> LLMResponse:
        """Send messages to the Databricks endpoint and return the response."""
        response = self._client.predict(
            endpoint=self.model_id,
            inputs={
                "messages": messages,
                "max_tokens": 2048,
            },
        )
        content = response["choices"][0]["message"]["content"]
        return LLMResponse(content=content)

    def invoke(
        self,
        input: Union[str, List[LLMMessage]],
        message_history: Optional[Union[List[LLMMessage], Any]] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Supports both V1 (string input) and V2 (message list input) calling
        conventions so this class works with SimpleKGPipeline (V1) and
        GraphRAG (V2).

        Args:
            input: Text prompt (V1) or list of LLMMessage dicts (V2).
            message_history: Optional previous messages (V1 only).
            system_instruction: Optional system message (V1 only).

        Returns:
            LLMResponse containing the generated text.
        """
        if isinstance(input, list):
            messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in input
            ]
            return self._predict(messages)

        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        if message_history:
            messages.extend(
                {"role": msg["role"], "content": msg["content"]}
                for msg in message_history
            )
        messages.append({"role": "user", "content": input})
        return self._predict(messages)

    async def ainvoke(
        self,
        input: Union[str, List[LLMMessage]],
        message_history: Optional[Union[List[LLMMessage], Any]] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Async version of invoke (runs synchronously)."""
        return self.invoke(
            input, message_history=message_history,
            system_instruction=system_instruction, **kwargs,
        )


# =============================================================================
# AI Services Factory Functions
# =============================================================================

def get_embedder(model_id: str = DEFAULT_EMBEDDING_MODEL) -> DatabricksEmbeddings:
    """Get embedder using Databricks Foundation Model APIs.

    Args:
        model_id: Databricks embedding endpoint name.
                  Default: databricks-bge-large-en (1024 dimensions)

    Returns:
        DatabricksEmbeddings configured for the specified model
    """
    return DatabricksEmbeddings(model_id=model_id)


def get_llm(model_id: str = DEFAULT_LLM_MODEL) -> DatabricksLLM:
    """Get LLM using Databricks Foundation Model APIs.

    Args:
        model_id: Databricks LLM endpoint name.
                  Default: databricks-meta-llama-3-3-70b-instruct

    Returns:
        DatabricksLLM configured for the specified model
    """
    return DatabricksLLM(model_id=model_id)


# =============================================================================
# Neo4j Connection
# =============================================================================

class Neo4jConnection:
    """Manages Neo4j database connection."""

    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """Initialize and connect to Neo4j.

        Args:
            uri: Neo4j URI (e.g., "neo4j+s://xxxxxxxx.databases.neo4j.io")
            username: Neo4j username (typically "neo4j")
            password: Neo4j password
            database: Neo4j database name (default "neo4j")
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )

    def verify(self):
        """Verify the connection is working."""
        self.driver.verify_connectivity()
        print("Connected to Neo4j successfully!")
        return self

    def clear_chunks(self):
        """Remove all enrichment nodes: Document, Chunk, OperatingLimit, and pipeline internals.

        Preserves the aircraft operational graph from Lab 2.
        Uses batched deletes to avoid transaction timeouts on large graphs.
        """
        labels = ["Chunk", "Document", "OperatingLimit", "__Entity__", "__KGBuilder__"]
        deleted_total = 0
        for label in labels:
            while True:
                records, _, _ = self.driver.execute_query(
                    f"MATCH (n:{label}) WITH n LIMIT 500 DETACH DELETE n RETURN count(*) AS deleted",
                    database_=self.database,
                )
                count = records[0]["deleted"]
                deleted_total += count
                if count == 0:
                    break
        print(f"Cleared {deleted_total} enrichment nodes (Document, Chunk, OperatingLimit)")
        return self

    def get_graph_stats(self):
        """Show current graph statistics."""
        records, _, _ = self.driver.execute_query("""
            MATCH (n)
            WITH labels(n) as nodeLabels
            UNWIND nodeLabels as label
            RETURN label, count(*) as count
            ORDER BY label
        """, database_=self.database)
        print("=== Graph Statistics ===")
        for record in records:
            print(f"  {record['label']}: {record['count']}")
        return self

    def close(self):
        """Close the database connection."""
        self.driver.close()
        print("Connection closed.")


# =============================================================================
# Data Loading
# =============================================================================

# Default Volume path for workshop data
DEFAULT_VOLUME_PATH = "/Volumes/databricks-neo4j-workshop/aircraft/raw_data"


class DataLoader:
    """Handles loading text data from files (local or Unity Catalog Volume)."""

    def __init__(self, file_path: str):
        """Initialize with path to data file.

        Args:
            file_path: Path to the file. Can be:
                - Relative path (loaded from current directory)
                - Absolute local path
                - Volume path (e.g., /Volumes/catalog/schema/volume/file.md)
        """
        self.file_path = Path(file_path)
        self._text = None

    @property
    def text(self) -> str:
        """Load and return the text content from the file."""
        if self._text is None:
            self._text = self.file_path.read_text().strip()
        return self._text

    def get_metadata(self) -> dict:
        """Return metadata about the loaded file."""
        return {
            "path": str(self.file_path),
            "name": self.file_path.name,
            "size": len(self.text)
        }


class VolumeDataLoader:
    """Handles loading text data from Unity Catalog Volumes.

    Unity Catalog Volumes are accessible as file paths in Databricks:
    /Volumes/<catalog>/<schema>/<volume>/<file>

    Example:
        >>> loader = VolumeDataLoader("maintenance_manual.md")
        >>> text = loader.text
    """

    def __init__(self, file_name: str, volume_path: str = DEFAULT_VOLUME_PATH):
        """Initialize with file name and optional Volume path.

        Args:
            file_name: Name of the file in the Volume (e.g., "maintenance_manual.md")
            volume_path: Path to the Unity Catalog Volume.
                        Defaults to /Volumes/databricks-neo4j-workshop/aircraft/raw_data
        """
        self.volume_path = Path(volume_path)
        self.file_name = file_name
        self.file_path = self.volume_path / file_name
        self._text = None

    @property
    def text(self) -> str:
        """Load and return the text content from the Volume."""
        if self._text is None:
            self._text = self.file_path.read_text().strip()
        return self._text

    def get_metadata(self) -> dict:
        """Return metadata about the loaded file."""
        return {
            "path": str(self.file_path),
            "name": self.file_name,
            "volume": str(self.volume_path),
            "size": len(self.text)
        }


# =============================================================================
# Text Splitting
# =============================================================================

def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Split text into chunks using FixedSizeSplitter.

    Args:
        text: Text to split
        chunk_size: Maximum characters per chunk
        chunk_overlap: Characters to overlap between chunks

    Returns:
        List of chunk text strings
    """
    splitter = FixedSizeSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        approximate=True
    )
    # Run in a separate thread to avoid "asyncio.run() cannot be called from
    # a running event loop" in Jupyter/Databricks environments.
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(asyncio.run, splitter.run(text)).result()
    return [chunk.text for chunk in result.chunks]


# =============================================================================
# Embedding Configuration
# =============================================================================

# Databricks BGE and GTE models produce 1024-dimensional vectors
EMBEDDING_DIMENSIONS = 1024


# =============================================================================
# Context-Aware Text Splitter
# =============================================================================

class ContextPrependingSplitter(TextSplitter):
    """Wraps a TextSplitter and prepends a context line to every chunk.

    SimpleKGPipeline passes document_metadata only to the graph builder for
    storage on Document nodes -- it is never injected into the LLM extraction
    prompt. The LLM sees only raw chunk text. After splitting a 30,000-character
    manual into ~40 chunks, most chunks land deep in engine-specific sections
    where the engine designation (e.g. "LEAP-1A") dominates and the aircraft
    model (e.g. "A321neo") is never mentioned. Without explicit context, the LLM
    confuses engine types for aircraft types.

    This wrapper solves the problem by prepending a short context header to
    every chunk so the LLM always has access to the document-level aircraft type.

    Set ``context`` before each call to ``pipeline.run_async()``.
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


# =============================================================================
# Entity Extraction Schema and Prompt
# =============================================================================

def build_extraction_schema():
    """Build a GraphSchema for SimpleKGPipeline entity extraction.

    Extracts OperatingLimit entities -- aircraft operating parameter thresholds
    (EGT limits, vibration thresholds, etc.). Entity names are qualified with
    aircraft type (e.g. "EGT - A320-200") so entity resolution does not merge
    limits from different aircraft.
    """
    from neo4j_graphrag.experimental.components.schema import (
        GraphSchema,
        NodeType,
        PropertyType,
    )

    node_types = [
        NodeType(
            label="OperatingLimit",
            description="An operating parameter limit for an aircraft system.",
            properties=[
                PropertyType(
                    name="name",
                    type="STRING",
                    description=(
                        "Unique identifier combining parameter and aircraft type, "
                        "e.g. 'EGT - A320-200', 'N1Speed - B737-800'. "
                        "Always append ' - <aircraft type>'."
                    ),
                ),
                PropertyType(
                    name="parameterName",
                    type="STRING",
                    description="Base parameter name matching sensor type, e.g. EGT, Vibration, N1Speed, FuelFlow",
                ),
                PropertyType(name="unit", type="STRING", description="Unit of measurement"),
                PropertyType(name="regime", type="STRING", description="Operating regime, e.g. takeoff, cruise"),
                PropertyType(name="minValue", type="STRING", description="Minimum value"),
                PropertyType(name="maxValue", type="STRING", description="Maximum value"),
                PropertyType(name="aircraftType", type="STRING", description="Aircraft type, e.g. A320-200"),
            ],
            additional_properties=False,
        ),
    ]

    return GraphSchema(
        node_types=tuple(node_types),
        relationship_types=(),
        patterns=(),
        additional_node_types=False,
        additional_relationship_types=False,
        additional_patterns=False,
    )


EXTRACTION_PROMPT = """\
You are an expert aviation engineer extracting structured operating-limit \
data from aircraft maintenance manuals to build a knowledge graph.

Your task: extract entities (nodes) and relationships from the input text \
according to the schema below.

Return result as JSON using this format:
{{"nodes": [{{"id": "0", "label": "OperatingLimit", "properties": {{"name": "EGT - A320-200", "parameterName": "EGT", "aircraftType": "A320-200", "unit": "\u00b0C", "maxValue": "695"}}}}],
"relationships": []}}

Use only the following node and relationship types:
{schema}

IMPORTANT RULES:

1. DOCUMENT CONTEXT: The input text starts with a [DOCUMENT CONTEXT] line \
that identifies the aircraft type and title. Use the aircraft type from this \
context line as the `aircraftType` property on every extracted entity.

2. AIRCRAFT TYPE vs ENGINE MODEL: The `aircraftType` property must be the \
airframe model (the aircraft you fly, e.g. A320-200, A321neo, B737-800), \
NOT the engine designation (e.g. V2500, LEAP-1A, CFM56-7B, PW1100G). \
Maintenance manuals are organized by aircraft type. Engine models appear \
throughout the text but they are components OF the aircraft, not the \
aircraft type itself.

3. PARAMETER NAMES: The `parameterName` should use the short sensor \
monitoring names from the document's sensor tables (e.g. EGT, Vibration, \
N1Speed, FuelFlow). Prefer concise sensor-style names over verbose \
descriptions.

4. ENTITY NAME FORMAT: The `name` property must follow the pattern \
"<parameterName> - <aircraftType>" (e.g. "EGT - A320-200"). This creates \
a unique identifier per parameter per aircraft type.

5. Only extract entities when the text contains specific numeric limits, \
thresholds, or operating ranges. Do not create entities for general \
descriptions without measurable values.

Assign a unique ID (string) to each node and reuse it for relationships.

Output rules:
- Return ONLY the JSON object, no additional text.
- Omit any backticks \u2014 output raw JSON.
- The JSON must be a single object, not wrapped in a list.
- Property names must be in double quotes.

{examples}

Input text:

{text}
"""


# =============================================================================
# SimpleKGPipeline Runner
# =============================================================================

def run_pipeline(
    driver,
    llm: LLMInterface,
    embedder: Embedder,
    text: str,
    document_metadata: Dict[str, str],
    context: str,
    *,
    neo4j_database: Optional[str] = None,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> None:
    """Run SimpleKGPipeline to chunk, embed, and extract entities from text.

    This is the automated equivalent of manually creating Document nodes,
    splitting text into Chunks, generating embeddings, and extracting entities.
    The pipeline handles all of these steps in a single pass.

    Args:
        driver: Neo4j driver instance.
        llm: LLM for entity extraction.
        embedder: Embedder for chunk embeddings.
        text: Full document text to process.
        document_metadata: Dict with documentId, aircraftType, title, type.
        context: Context string prepended to every chunk for LLM extraction
                 (e.g. "[DOCUMENT CONTEXT] Aircraft Type: A320-200 | Title: ...").
        neo4j_database: Neo4j database to write to (defaults to the server default).
        chunk_size: Characters per chunk (default 800).
        chunk_overlap: Overlap between chunks (default 100).
    """
    from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline

    inner_splitter = FixedSizeSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        approximate=True,
    )
    splitter = ContextPrependingSplitter(inner_splitter, context=context)

    schema = build_extraction_schema()

    pipeline = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        neo4j_database=neo4j_database,
        embedder=embedder,
        schema=schema,
        text_splitter=splitter,
        from_pdf=False,
        on_error="IGNORE",
        perform_entity_resolution=True,
        prompt_template=EXTRACTION_PROMPT,
    )

    print(f"Processing {len(text):,} characters ({document_metadata.get('documentId', 'unknown')})...")
    print(f"  Chunk size: {chunk_size}, overlap: {chunk_overlap}")
    print(f"  LLM: {getattr(llm, 'model_id', llm.model_name)}")
    print(f"  Embedder: {getattr(embedder, 'model_id', 'unknown')}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(
            asyncio.run,
            pipeline.run_async(text=text, document_metadata=document_metadata),
        ).result()

    print("Pipeline complete!")


def format_operating_limit_record(record: Record) -> RetrieverResultItem:
    """Format an operating-limit record into clean, displayable HTML.

    The default VectorCypherRetriever formatter sets ``content`` to ``str(record)``,
    which prints the raw neo4j Record wrapper with the manual's HTML tags showing
    literally. This formatter builds well-formed HTML instead, so the operating-limit
    query results render nicely with ``IPython.display.HTML`` and read cleanly when
    passed to the LLM as context.

    Expects the record to expose ``aircraft_type``, ``operating_limits`` (a list of
    dicts with ``sensor``/``parameter``/``max``/``unit``/``regime``), and ``context``.
    """
    aircraft = record.get("aircraft_type") or "Unknown"
    limits = [
        limit
        for limit in (record.get("operating_limits") or [])
        if limit.get("parameter")
    ]
    if limits:
        rows = "".join(
            f"<li><b>{limit['parameter']}</b> ({limit['sensor']}): "
            f"max {limit['max']} {limit['unit']} — {limit['regime']}</li>"
            for limit in limits
        )
        limits_html = f"<ul>{rows}</ul>"
    else:
        limits_html = "<p><i>No operating limits extracted for this aircraft.</i></p>"

    context = record.get("context") or ""
    content = (
        "<div style='border:1px solid #ddd;padding:8px;margin:6px 0'>"
        f"<h4 style='margin:0'>Aircraft: {aircraft}</h4>"
        "<p style='margin:4px 0'><b>Operating limits:</b></p>"
        f"{limits_html}"
        "<p style='margin:4px 0'><b>Context:</b></p>"
        f"<div>{context}</div>"
        "</div>"
    )
    return RetrieverResultItem(content=content, metadata={"aircraft_type": aircraft})
