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
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.experimental.components.text_splitters.base import TextSplitter
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.experimental.components.types import TextChunks
from neo4j_graphrag.llm.base import LLMInterface, LLMInterfaceV2
from neo4j_graphrag.llm.types import LLMResponse
from neo4j_graphrag.types import LLMMessage


# =============================================================================
# Model endpoints
# =============================================================================

# Mirrors LLM_ENDPOINT and EMBEDDING_ENDPOINT in
# Lab_3_Semantic_Search/data_utils.py. This copy exists so the validation
# harness can import without the lab folders on sys.path; it has to name the
# same two endpoints the labs run on.
LLM_ENDPOINT = "databricks-claude-sonnet-5"
EMBEDDING_ENDPOINT = "databricks-bge-large-en"


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

    def __init__(self, model_id: str = EMBEDDING_ENDPOINT):
        """Initialize the Databricks embeddings provider.

        Args:
            model_id: The Databricks Foundation Model endpoint name.
                      Default: EMBEDDING_ENDPOINT (1024 dimensions)
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
# Chat Response Helpers
# =============================================================================

# Mirrors extract_text and json_schema_format in
# Lab_3_Semantic_Search/data_utils.py. The harness imports this copy instead of
# the lab folder, so the two have to stay the same shape: a fix that lands in
# one and not the other is a validation run that passes on code the lab does
# not run.

def extract_text(content: Any) -> str:
    """Flatten a chat endpoint's message content down to plain text.

    A hybrid reasoning model does not always answer with a string. When
    ``databricks-claude-sonnet-5`` decides a prompt is worth thinking about,
    ``choices[0].message.content`` comes back as a list of content parts: a
    ``reasoning`` part carrying the thinking summary, then a ``text`` part
    carrying the answer. Whether the model thinks depends on the prompt, so
    the same code path sees both shapes on different calls.

    Every caller in this workshop wants the answer and none of them want the
    thinking, so this keeps the ``text`` parts in the order they arrived and
    drops everything else. Parts that are not dicts, or that are missing the
    keys, are skipped rather than raised on: a malformed part is not worth
    failing a lab over.

    Args:
        content: The raw ``message.content`` value from a chat endpoint. It
            may be a string, None, or a list of content parts.

    Returns:
        The plain text of the response, or an empty string when there is none.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "text":
                continue
            text = part.get("text")
            if isinstance(text, str):
                texts.append(text)
        return "".join(texts)
    return str(content)


def json_schema_format(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Wrap a JSON Schema in the response_format envelope FMAPI expects.

    Asking a reasoning model for JSON in the prompt and hoping is not
    reliable. Databricks structured outputs make the endpoint itself enforce
    the shape, and they accept ``json_schema`` only: the ``json_object`` mode
    other providers offer is not supported here. The schema has to be named
    and marked strict, may hold at most 64 keys, and cannot use ``pattern``,
    ``anyOf``, ``oneOf``, ``allOf``, or ``$ref``. Flat schemas work best.

    One request cannot carry both ``response_format`` and ``tools``. This
    workshop uses structured outputs and not tool calling, so that is a
    constraint to know about rather than one to work around.

    Args:
        name: Short name for the schema, which the endpoint quotes back in
            any validation error.
        schema: The JSON Schema the model's response must satisfy.

    Returns:
        The dict to pass as the request's ``response_format`` field.
    """
    return {
        "type": "json_schema",
        "json_schema": {"name": name, "schema": schema, "strict": True},
    }


# =============================================================================
# Databricks LLM
# =============================================================================

class DatabricksLLM(LLMInterface, LLMInterfaceV2):
    """LLM interface using Databricks Foundation Model APIs.

    Implements both LLMInterface (for SimpleKGPipeline) and LLMInterfaceV2
    (for GraphRAG and LangChain compatibility).

    Supports Databricks-hosted LLM endpoints like:
    - databricks-claude-sonnet-5
    - databricks-meta-llama-3-3-70b-instruct

    Uses MLflow deployments client for API calls.
    """

    def __init__(self, model_id: str = LLM_ENDPOINT, *, max_tokens: int = 4096) -> None:
        """Initialize the Databricks LLM provider.

        Args:
            model_id: The Databricks Foundation Model endpoint name.
            max_tokens: Output token budget for every call this instance
                makes. The default is 4096 rather than something smaller
                because reasoning tokens count against max_tokens, so a
                thinking response can spend most of the budget before it
                reaches the text part and come back truncated.
        """
        LLMInterfaceV2.__init__(self, model_name=model_id)
        self.model_id = model_id
        self.max_tokens = max_tokens
        self._client = mlflow.deployments.get_deploy_client("databricks")

    def _predict(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Send messages to the Databricks endpoint and return the response.

        Args:
            messages: Chat messages in role/content form.
            response_format: Optional structured-output envelope from
                json_schema_format(), which makes the endpoint enforce the
                shape of the reply. Omitted from the request when None,
                because the endpoint rejects the field if it is null.

        Returns:
            LLMResponse containing the response text.
        """
        inputs: dict[str, Any] = {
            "messages": messages,
            "max_tokens": self.max_tokens,
        }
        if response_format is not None:
            inputs["response_format"] = response_format
        response = self._client.predict(endpoint=self.model_id, inputs=inputs)
        # LLMResponse.content is typed as a plain string, and a reasoning
        # model hands back a list of content parts whenever it thinks, so
        # flatten the raw content before it reaches the model.
        content = extract_text(response["choices"][0]["message"]["content"])
        return LLMResponse(content=content)

    def invoke(
        self,
        input: Union[str, List[LLMMessage]],
        message_history: Optional[Union[List[LLMMessage], Any]] = None,
        system_instruction: Optional[str] = None,
        *,
        response_format: dict[str, Any] | None = None,
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
            response_format: Optional structured-output envelope from
                json_schema_format(). Callers that need a machine-readable
                answer pass one, and neither calling convention changes.

        Returns:
            LLMResponse containing the generated text.
        """
        if isinstance(input, list):
            messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in input
            ]
            return self._predict(messages, response_format=response_format)

        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        if message_history:
            messages.extend(
                {"role": msg["role"], "content": msg["content"]}
                for msg in message_history
            )
        messages.append({"role": "user", "content": input})
        return self._predict(messages, response_format=response_format)

    async def ainvoke(
        self,
        input: Union[str, List[LLMMessage]],
        message_history: Optional[Union[List[LLMMessage], Any]] = None,
        system_instruction: Optional[str] = None,
        *,
        response_format: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Async version of invoke (runs synchronously)."""
        return self.invoke(
            input, message_history=message_history,
            system_instruction=system_instruction,
            response_format=response_format, **kwargs,
        )


# =============================================================================
# AI Services Factory Functions
# =============================================================================

def get_embedder(model_id: str = EMBEDDING_ENDPOINT) -> DatabricksEmbeddings:
    """Get embedder using Databricks Foundation Model APIs.

    Args:
        model_id: Databricks embedding endpoint name.
                  Default: EMBEDDING_ENDPOINT (1024 dimensions)

    Returns:
        DatabricksEmbeddings configured for the specified model
    """
    return DatabricksEmbeddings(model_id=model_id)


def get_llm(model_id: str = LLM_ENDPOINT) -> DatabricksLLM:
    """Get LLM using Databricks Foundation Model APIs.

    Args:
        model_id: Databricks LLM endpoint name.
                  Default: LLM_ENDPOINT

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

    def clear_enrichment(self):
        """Remove what this lab created: Document, Chunk, and extracted entities.

        A rerun guard. SimpleKGPipeline creates chunks with no dedup key, so a
        second run of notebook 01 doubles the chunk count, puts duplicate
        embeddings in every vector search result, and doubles the node budget.

        Preserves the operational graph from Lab 2, including the canonical
        OperatingLimit nodes it loads from ``silver_operating_limits``. What
        extraction produces carries the ``ExtractedLimit`` label instead, so
        clearing by label reaches this lab's output and nothing else.

        Uses batched deletes to avoid transaction timeouts on large graphs.
        """
        matches = [
            "MATCH (n:Chunk)",
            "MATCH (n:Document)",
            # Extraction output only. Lab 2 owns the OperatingLimit label and
            # this lab does not delete what Lab 2 loaded.
            "MATCH (n:ExtractedLimit)",
            "MATCH (n:__Entity__)",
            "MATCH (n:__KGBuilder__)",
        ]
        deleted_total = 0
        for match_clause in matches:
            while True:
                records, _, _ = self.driver.execute_query(
                    f"{match_clause} WITH n LIMIT 500 DETACH DELETE n "
                    "RETURN count(*) AS deleted",
                    database_=self.database,
                )
                count = records[0]["deleted"]
                deleted_total += count
                if count == 0:
                    break
        print(
            f"Cleared {deleted_total} enrichment nodes "
            "(Document, Chunk, extracted entities)"
        )
        print("Kept the aircraft graph and the operating limits loaded in Lab 2.")
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

    Extracts ExtractedLimit entities -- aircraft operating parameter thresholds
    (EGT limits, vibration thresholds, etc.) as stated in the manual text. The
    label is deliberately not OperatingLimit: that one means the 20 canonical
    rows Lab 2 loads from CSV. Entity names are qualified with aircraft type
    (e.g. "EGT - A320-200") so entity resolution does not merge limits from
    different aircraft.
    """
    from neo4j_graphrag.experimental.components.schema import (
        GraphSchema,
        NodeType,
        PropertyType,
    )

    node_types = [
        NodeType(
            label="ExtractedLimit",
            description=(
                "An operating parameter limit stated in a maintenance manual."
            ),
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
{{"nodes": [{{"id": "0", "label": "ExtractedLimit", "properties": {{"name": "EGT - A320-200", "parameterName": "EGT", "aircraftType": "A320-200", "unit": "\u00b0C", "maxValue": "695"}}}}],
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
