"""Memory plumbing for the Lab 6 agent.

Lab 5 built a supervisor over three stores and it forgot everything between
questions. Lab 6 gives it memory, and the memory lives in the same Aura
instance as the fleet graph, which is the entire reason this lab is worth
doing. A remembered aircraft is not a copy of an aircraft. It is the same
node Lab 2 loaded, so a single Cypher statement can walk from "who asked
about this" to "what maintenance actually found" without a join key.

What this module provides:

- ``MemoryEmbeddings`` and ``MemoryLLM``  The two adapters that let
  ``neo4j-agent-memory`` run on Databricks Foundation Model endpoints.
- ``NotebookLoop`` and ``MemorySession``  A long-lived event loop so an
  async client can be opened in one notebook cell and used in the next.
- ``adoption_dry_run`` and ``adopt_aircraft``  Adoption of the fleet graph,
  with the guard rail that keeps it to ``Aircraft``.
- ``aircraft_mentions`` and ``seed_memory``  Explicit-mention writing, and
  the seeded shift history the demos read.
- ``HEADLINE_QUERY`` and its two controls.
- ``build_recall_node`` and ``build_remember_node``  The two nodes that go
  either side of the Lab 5 supervisor.

The embedder and the secret helpers come from ``Lab_3_Semantic_Search``, and
the agent state and the tool nodes come from ``Lab_5_LangGraph_Agent``. This
lab adds memory to that agent; it does not rebuild it.

Two names in here look like duplicates of Lab 3 and are not.
``data_utils.DatabricksEmbeddings`` and ``data_utils.DatabricksLLM`` satisfy
neo4j-graphrag's ``Embedder`` and ``LLMInterface``, which are synchronous.
``neo4j-agent-memory`` asks for a different contract: three ``async``
Protocols in ``neo4j_agent_memory.llm.protocol``. Two libraries, two shapes,
one pair of endpoints underneath. ``MemoryEmbeddings`` and ``MemoryLLM`` are
named apart from the Lab 3 pair so nobody has to work out which is which.

Install note. This module imports ``neo4j_agent_memory`` lazily, inside the
functions that need it, so the notebook can import ``memory.py`` and print a
useful message before the ``%pip install`` cell has run.
"""

from __future__ import annotations

import asyncio
import re
import sys
import threading
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import Future
from pathlib import Path
from typing import Any

# =============================================================================
# Locating the labs this one builds on
# =============================================================================

LAB3_DIRNAME = "Lab_3_Semantic_Search"
LAB5_DIRNAME = "Lab_5_LangGraph_Agent"


def _add_sibling_to_path(dirname: str, marker: str) -> Path:
    """Put a sibling lab directory on ``sys.path`` and return it.

    Args:
        dirname: Directory name to find, e.g. ``Lab_3_Semantic_Search``.
        marker: File that must exist inside it, e.g. ``data_utils.py``.

    Returns:
        The directory holding ``marker``.

    Raises:
        FileNotFoundError: The directory is not beside this lab.
    """
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / dirname,
        Path.cwd().parent / dirname,
        Path.cwd() / dirname,
        here,
    ]
    for candidate in candidates:
        if (candidate / marker).is_file():
            path = str(candidate)
            if path not in sys.path:
                sys.path.insert(0, path)
            return candidate
    searched = "\n  ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"Could not find {marker} from {dirname}. Lab 6 builds on it rather "
        "than carrying a copy. Import that folder into the workspace next to "
        f"this one. Searched:\n  {searched}"
    )


def ensure_labs_on_path() -> tuple[Path, Path]:
    """Put Lab 3 and Lab 5 on ``sys.path``.

    Returns:
        The Lab 3 directory and the Lab 5 directory, in that order.
    """
    return (
        _add_sibling_to_path(LAB3_DIRNAME, "data_utils.py"),
        _add_sibling_to_path(LAB5_DIRNAME, "tools.py"),
    )


ensure_labs_on_path()

from data_utils import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_LLM_MODEL,
    DEFAULT_NEO4J_DATABASE,
    read_neo4j_secrets,
    secret_scope_name,
)
from tools import (  # noqa: E402
    SUPERVISOR_PROMPT,
    AgentState,
)

__all__ = [
    "ADOPT_LABEL_TO_TYPE",
    "ADOPT_NAME_PROPERTY",
    "DESTRUCTIVE_ADOPTION_LABELS",
    "EMBEDDING_DIMENSIONS",
    "EMBEDDING_MODEL",
    "ENV_CREDENTIAL_NAMES",
    "ENV_DATABASE_NAME",
    "FLEET_ONLY_QUERY",
    "HEADLINE_QUERY",
    "HTTPX_REQUIREMENT",
    "INSTALL_COMMAND",
    "MEMORY_ONLY_QUERY",
    "MEMORY_SUPERVISOR_PROMPT",
    "MEMORY_LLM_MODEL",
    "RECALL_LIMIT",
    "SEED_MESSAGES",
    "TAIL_NUMBER_RE",
    "WHEEL_PATH",
    "MemoryAgentState",
    "MemoryEmbeddings",
    "MemoryLLM",
    "MemorySession",
    "NotebookLoop",
    "SeedMessage",
    "adopt_aircraft",
    "adoption_dry_run",
    "aircraft_mentions",
    "build_memory_settings",
    "build_memory_supervisor_node",
    "build_recall_node",
    "build_remember_node",
    "describe_adoption_report",
    "ensure_labs_on_path",
    "format_recalled",
    "guard_write_target",
    "seed_memory",
]


# =============================================================================
# Install, pinned
# =============================================================================

# The wheel is built from the `mentions` branch of
# https://github.com/neo4j-partners/agent-memory, checked into
# lab/courseware/wheels/, and uploaded to the volume by
# `workshop.py provision-data`. Three reasons it is a wheel on a volume rather
# than a PyPI pin, and each of them fails silently rather than loudly:
#
#   1. Released 0.5.0 drops most MENTIONS edges on the automatic extraction
#      path. MENTIONS is the exact edge HEADLINE_QUERY walks. No exception, no
#      warning, no edge.
#   2. A wheel carries no extras, and the bolt path needs httpx. It is imported
#      transitively by MemoryClient.connect(), so a bare install fails at
#      connect time rather than at import time, in front of the room.
#   3. The local version segment `+mentions` resolves from nowhere, so anything
#      that pins by version alone has to be handed this path instead. That
#      includes MLflow's inferred requirements when the agent is logged.
#
# The per-participant cluster already installs this through VOC_COURSE_LIBRARIES
# in lab/course.env. The notebook line is the safety net for a cluster that
# predates that list.
WHEEL_PATH = (
    "/Volumes/databricks-neo4j-workshop/aircraft/raw_data/"
    "neo4j_agent_memory-0.5.1.dev0+mentions-py3-none-any.whl"
)
HTTPX_REQUIREMENT = "httpx>=0.27.0"
INSTALL_COMMAND = f"%pip install {WHEEL_PATH} {HTTPX_REQUIREMENT}"


# =============================================================================
# Model endpoints
# =============================================================================

# Aliases onto the two endpoints Lab 3 and Lab 5 already use, so Lab 6 does not
# introduce a third place the endpoint names are written.
EMBEDDING_MODEL = DEFAULT_EMBEDDING_MODEL
MEMORY_LLM_MODEL = DEFAULT_LLM_MODEL

# databricks-bge-large-en returns 1024 floats. The library reads this number
# off the adapter and sizes all six of its vector indexes to match, then
# re-validates on every later connect and raises
# EmbeddingDimensionMismatchError if it has moved. Changing the embedding
# endpoint therefore means dropping the vector indexes, not just editing a
# constant.
EMBEDDING_DIMENSIONS = 1024

# The three variables Lab 5's agent.py binds to secret references when it
# deploys. Repeated here rather than imported, because importing agent.py runs
# its mlflow.models.set_model() call, and a notebook that imports memory.py
# should not be declaring itself a model.
ENV_CREDENTIAL_NAMES = ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD")

# The fourth variable, which is optional. An endpoint deployed from a scope
# without a neo4j-database key does not carry it, and the AuraDB Free name
# stands in.
ENV_DATABASE_NAME = "NEO4J_DATABASE"

# How many past messages the recall node pulls in. Each one is a vector search
# hit, and the whole search costs 3.4 to 5.0 seconds regardless of limit, so
# this trades answer context against nothing much.
RECALL_LIMIT = 3


# =============================================================================
# The async bridge
# =============================================================================


class NotebookLoop:
    """An event loop on a background thread, alive for the notebook session.

    ``neo4j-agent-memory`` is async all the way down, and a notebook is not.
    The usual fix, ``asyncio.run`` per call, opens and closes a loop each
    time, which is fine for a one-shot coroutine and wrong for a client that
    holds a Neo4j driver: the driver binds to the loop that created it, and
    the next cell gets a driver attached to a loop that no longer exists.

    So the loop outlives the cell. One thread, one loop, started on first use
    and stopped by :meth:`close`. Every coroutine in this module is submitted
    to it with :meth:`run`, which blocks until the result is ready and so
    reads like ordinary synchronous code in a cell.

    Example:
        >>> loop = NotebookLoop()
        >>> loop.run(some_coroutine())
        >>> loop.close()
    """

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_forever, name="lab6-memory-loop", daemon=True
        )
        self._thread.start()

    def _run_forever(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro: Any, *, timeout: float | None = None) -> Any:
        """Run a coroutine on the background loop and return its result.

        Args:
            coro: The coroutine to run.
            timeout: Seconds to wait. ``None`` waits indefinitely.

        Returns:
            Whatever the coroutine returned.

        Raises:
            RuntimeError: The loop has been closed.
        """
        if not self._loop.is_running():
            raise RuntimeError(
                "The memory event loop is closed. Re-open the session with "
                "MemorySession.open_from_secrets(...)."
            )
        future: Future[Any] = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout)

    def close(self) -> None:
        """Stop the loop and join its thread. Safe to call twice."""
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=10)
        if not self._loop.is_closed():
            self._loop.close()


# =============================================================================
# The two provider adapters
# =============================================================================


class MemoryEmbeddings:
    """Databricks embeddings, shaped for ``neo4j-agent-memory``.

    Satisfies ``neo4j_agent_memory.llm.protocol.EmbeddingProvider``: a
    ``model`` string, a ``dimensions`` int, ``async embed`` over a batch, and
    ``async embed_one``. Nothing is subclassed. The library type-checks
    ``MemorySettings.embedding`` as ``Any`` and accepts any object that has
    those four members, which is what makes a provider it has never heard of
    work without a library change.

    The endpoint call itself is synchronous, so it is pushed onto a worker
    thread with ``asyncio.to_thread`` rather than blocking the event loop.

    Args:
        model: Foundation Model embedding endpoint name.
        dimensions: Vector width the endpoint returns.
        batch_size: Texts per request.

    Example:
        >>> embedder = MemoryEmbeddings()
        >>> embedder.dimensions
        1024
    """

    def __init__(
        self,
        model: str = EMBEDDING_MODEL,
        *,
        dimensions: int = EMBEDDING_DIMENSIONS,
        batch_size: int = 16,
    ) -> None:
        import mlflow.deployments

        self.model = model
        self.dimensions = dimensions
        self._batch_size = batch_size
        self._client = mlflow.deployments.get_deploy_client("databricks")

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch, one request per ``batch_size`` texts."""
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            window = texts[start : start + self._batch_size]
            response = self._client.predict(
                endpoint=self.model, inputs={"input": window}
            )
            vectors.extend(row["embedding"] for row in response["data"])
        return vectors

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts.

        Args:
            texts: Texts to embed. May be empty.

        Returns:
            One vector per input text, in the same order.
        """
        if not texts:
            return []
        return await asyncio.to_thread(self._embed_sync, list(texts))

    async def embed_one(self, text: str) -> list[float]:
        """Embed a single text.

        Args:
            text: Text to embed.

        Returns:
            One vector of length ``dimensions``.
        """
        return (await self.embed([text]))[0]


class MemoryLLM:
    """A Databricks chat endpoint, shaped for ``neo4j-agent-memory``.

    Satisfies both ``LLMProvider`` and ``StructuredExtractor``. The first is
    a plain completion. The second has to return a validated Pydantic model,
    which Foundation Model endpoints cannot guarantee: unlike the OpenAI
    structured-output API they do not enforce a JSON Schema server-side, so
    something has to inject the schema, parse what comes back, and ask again
    when it does not validate.

    That loop is not written here. ``neo4j_agent_memory.llm.structured``
    ships ``schema_aligned_extract`` for exactly this case, and delegating to
    it means the retry behaviour, the fence stripping and the error feedback
    match every other adapter the library supports rather than being this
    workshop's own version of them.

    Args:
        model: Foundation Model chat endpoint name.
        default_max_tokens: Cap applied when a caller does not set one.

    Example:
        >>> llm = MemoryLLM()
        >>> llm.model
        'databricks-meta-llama-3-3-70b-instruct'
    """

    def __init__(
        self,
        model: str = MEMORY_LLM_MODEL,
        *,
        default_max_tokens: int = 2048,
    ) -> None:
        import mlflow.deployments

        self.model = model
        self._default_max_tokens = default_max_tokens
        self._client = mlflow.deployments.get_deploy_client("databricks")

    def _complete_sync(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        stop: Sequence[str] | None,
    ) -> dict[str, Any]:
        """One blocking call to the chat endpoint."""
        inputs: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stop:
            inputs["stop"] = list(stop)
        return self._client.predict(endpoint=self.model, inputs=inputs)

    async def complete(
        self,
        messages: Sequence[Any],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        stop: Sequence[str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Run a chat completion.

        Args:
            messages: ``ChatMessage`` values, in order.
            temperature: Sampling temperature. 0.0 is deterministic.
            max_tokens: Completion cap. Falls back to the constructor value.
            stop: Optional stop sequences.
            timeout: Accepted for Protocol conformance and not forwarded;
                the deployments client carries its own timeout.

        Returns:
            A ``neo4j_agent_memory.llm.types.Completion``.
        """
        from neo4j_agent_memory.llm.types import Completion, Usage

        payload = [{"role": m.role, "content": m.content} for m in messages]
        response = await asyncio.to_thread(
            self._complete_sync,
            payload,
            temperature,
            max_tokens or self._default_max_tokens,
            stop,
        )
        choice = response["choices"][0]
        reported = response.get("usage") or {}
        return Completion(
            content=choice["message"]["content"] or "",
            model=response.get("model", self.model),
            finish_reason=choice.get("finish_reason"),
            usage=Usage(
                prompt_tokens=reported.get("prompt_tokens", 0),
                completion_tokens=reported.get("completion_tokens", 0),
                total_tokens=reported.get("total_tokens", 0),
            ),
        )

    async def complete_structured(
        self,
        messages: Sequence[Any],
        response_model: type[Any],
        *,
        temperature: float = 0.0,
        max_retries: int = 2,
        timeout: float | None = None,
    ) -> Any:
        """Return a validated instance of ``response_model``.

        Args:
            messages: ``ChatMessage`` values, in order.
            response_model: Pydantic model the answer must validate against.
            temperature: Sampling temperature.
            max_retries: Retries after the first attempt, so ``max_retries + 1``
                calls at worst.
            timeout: Per-call timeout, forwarded to each attempt.

        Returns:
            A validated ``response_model`` instance.

        Raises:
            StructuredExtractionError: Every attempt failed to parse or validate.
        """
        from neo4j_agent_memory.llm.structured import schema_aligned_extract

        return await schema_aligned_extract(
            self,
            messages,
            response_model,
            temperature=temperature,
            max_retries=max_retries,
            timeout=timeout,
        )


# =============================================================================
# Settings, the write guard, and the session
# =============================================================================


def guard_write_target(uri: str, expected_prefix: str | None) -> None:
    """Refuse to connect to an instance that is not the expected one.

    Lab 6 writes. Adoption relabels nodes and memory adds them, so pointing
    this notebook at the wrong instance is not a failed query, it is a
    modified graph. When a participant runs this lab there is only one
    instance in play and ``expected_prefix`` is ``None``, which skips the
    check. Anyone running it against several instances should pass the prefix.

    Args:
        uri: The URI about to be connected to.
        expected_prefix: Required start of the URI, or ``None`` to allow any.

    Raises:
        ValueError: The URI does not start with ``expected_prefix``.
    """
    if expected_prefix and not uri.startswith(expected_prefix):
        raise ValueError(
            f"Refusing to connect. Expected a URI starting {expected_prefix!r} "
            f"and got {uri!r}. Lab 6 writes to the graph it connects to."
        )


def build_memory_settings(
    uri: str,
    username: str,
    password: str,
    *,
    database: str = DEFAULT_NEO4J_DATABASE,
    entity_types: Sequence[str] = ("AIRCRAFT",),
) -> Any:
    """Build ``MemorySettings`` pointed at the participant's Aura instance.

    The embedding and LLM providers are passed as objects rather than as
    provider-name strings. ``MemorySettings`` types both fields as ``Any``
    and its validator accepts anything satisfying the Protocol, which is the
    whole extension point.

    ``entity_types`` is deliberately short. Entities the library creates take
    a label derived from their type, so an entity of type ``SYSTEM`` becomes
    ``:System:Entity`` and collides with the fleet's own ``System`` label. A
    ``MATCH (s:System)`` in Lab 2 or Lab 4 would then return conversation
    artifacts next to real systems. One type, ``AIRCRAFT``, matched to the
    one label this lab adopts, keeps that from happening.

    Args:
        uri: Aura bolt URI.
        username: Neo4j user.
        password: Neo4j password.
        database: Neo4j database name.
        entity_types: Entity types the schema allows.

    Returns:
        A ``MemorySettings`` ready for ``MemoryClient``.
    """
    from neo4j_agent_memory.config.settings import (
        MemorySettings,
        Neo4jConfig,
        SchemaConfig,
        SchemaModel,
    )
    from pydantic import SecretStr

    return MemorySettings(
        neo4j=Neo4jConfig(
            uri=uri,
            username=username,
            password=SecretStr(password),
            database=database,
        ),
        embedding=MemoryEmbeddings(),
        llm=MemoryLLM(),
        schema_config=SchemaConfig(
            model=SchemaModel.CUSTOM,
            entity_types=list(entity_types),
            enable_subtypes=False,
        ),
    )


class MemorySession:
    """An open ``MemoryClient`` that survives from one notebook cell to the next.

    Holds the background loop, the connected client, and the identity the
    memory is written under. Open it once near the top of the notebook, use
    it from every cell after that, close it at the end.

    First connect is the expensive one. The library creates 33 indexes and 12
    constraints, six of them vector indexes sized from
    ``MemoryEmbeddings.dimensions``, and that took 22.4 seconds when measured.
    It happens once per database rather than once per session, so a second run
    of the notebook connects quickly.

    Attributes:
        client: The connected ``MemoryClient``.
        loop: The background loop it runs on.
    """

    def __init__(self, client: Any, loop: NotebookLoop) -> None:
        self.client = client
        self.loop = loop

    @classmethod
    def open(
        cls,
        uri: str,
        username: str,
        password: str,
        *,
        database: str = DEFAULT_NEO4J_DATABASE,
        expected_uri_prefix: str | None = None,
    ) -> MemorySession:
        """Connect to Aura and return an open session.

        Args:
            uri: Aura bolt URI.
            username: Neo4j user.
            password: Neo4j password.
            database: Neo4j database name.
            expected_uri_prefix: Passed to :func:`guard_write_target`.

        Returns:
            An open :class:`MemorySession`.
        """
        from neo4j_agent_memory import MemoryClient

        guard_write_target(uri, expected_uri_prefix)
        settings = build_memory_settings(
            uri, username, password, database=database
        )
        loop = NotebookLoop()
        client = MemoryClient(settings)
        try:
            loop.run(client.connect())
        except Exception:
            loop.close()
            raise
        return cls(client, loop)

    @classmethod
    def open_from_env(
        cls,
        *,
        database: str | None = None,
        expected_uri_prefix: str | None = None,
    ) -> MemorySession:
        """Connect using the environment variables serving provides.

        A Model Serving container has no ``dbutils`` and no notebook user, so
        Lab 5's ``agent.py`` deploys the endpoint with ``NEO4J_URI``,
        ``NEO4J_USERNAME`` and ``NEO4J_PASSWORD`` bound to
        ``{{secrets/<scope>/<key>}}`` references. Memory reads the same three
        rather than opening a second connection path, so the redeployed
        endpoint needs no new secrets and no new environment block.

        Args:
            database: Neo4j database name. Read from ``NEO4J_DATABASE`` when
                omitted, falling back to the AuraDB Free name.
            expected_uri_prefix: Passed to :func:`guard_write_target`.

        Returns:
            An open :class:`MemorySession`.

        Raises:
            RuntimeError: One of the three variables is missing or empty.
        """
        import os

        missing = [name for name in ENV_CREDENTIAL_NAMES if not os.environ.get(name)]
        if missing:
            raise RuntimeError(
                f"Missing environment variables: {', '.join(missing)}. The "
                "endpoint deploys these as secret references; see "
                "agent.serving_environment_vars in Lab 5."
            )
        uri, username, password = (os.environ[name] for name in ENV_CREDENTIAL_NAMES)
        return cls.open(
            uri,
            username,
            password,
            database=(
                database
                or os.environ.get(ENV_DATABASE_NAME, "").strip()
                or DEFAULT_NEO4J_DATABASE
            ),
            expected_uri_prefix=expected_uri_prefix,
        )

    @classmethod
    def open_from_secrets(
        cls,
        dbutils: Any,
        scope: str | None = None,
        *,
        spark: Any = None,
        database: str | None = None,
        expected_uri_prefix: str | None = None,
    ) -> MemorySession:
        """Connect using the credentials Lab 3 notebook 01 stored.

        The values are read, used and dropped inside this call, so nothing in
        the notebook binds a password to a name. Same scope, same keys and same
        helpers as Lab 5.

        Args:
            dbutils: The notebook's dbutils handle.
            scope: Scope name. Derived from ``current_user()`` when omitted.
            spark: Active SparkSession, required when ``scope`` is omitted.
            database: Neo4j database name. Read from the scope when omitted.
            expected_uri_prefix: Passed to :func:`guard_write_target`.

        Returns:
            An open :class:`MemorySession`.

        Raises:
            ValueError: Neither ``scope`` nor ``spark`` was given.
        """
        if scope is None:
            if spark is None:
                raise ValueError("Pass either a scope name or a SparkSession.")
            scope = secret_scope_name(spark)
        credentials = read_neo4j_secrets(dbutils, scope)
        return cls.open(
            credentials["uri"],
            credentials["username"],
            credentials["password"],
            database=database or credentials["database"],
            expected_uri_prefix=expected_uri_prefix,
        )

    def run(self, coro: Any, *, timeout: float | None = None) -> Any:
        """Run a coroutine on this session's loop.

        Args:
            coro: The coroutine to run.
            timeout: Seconds to wait.

        Returns:
            Whatever the coroutine returned.
        """
        return self.loop.run(coro, timeout=timeout)

    def cypher(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Run read-only Cypher through the memory client.

        ``client.query.cypher`` replaces the deprecated
        ``client.graph.execute_read``, which the library removes in 0.6.0. It
        rejects write queries before the round trip, so it cannot be used to
        modify the graph by accident.

        Args:
            query: A read-only Cypher statement.
            params: Query parameters.

        Returns:
            Result rows as dictionaries.
        """
        return self.run(self.client.query.cypher(query, params or {}))

    def close(self) -> None:
        """Close the client and stop the loop. Safe to call twice."""
        try:
            self.run(self.client.close(), timeout=30)
        finally:
            self.loop.close()


# =============================================================================
# Adoption
# =============================================================================

# What Lab 6 adopts, and it is one label on purpose.
ADOPT_LABEL_TO_TYPE = {"Aircraft": "AIRCRAFT"}

# Aircraft nodes have no `name` property, so the name has to come from
# somewhere. tail_number is the identifier a technician actually says out
# loud, which is also what makes regex extraction of mentions work.
ADOPT_NAME_PROPERTY = {"Aircraft": "tail_number"}

# Adopting any of these destroys data, and nothing warns you. The adoption
# Cypher guards `id` and `name` with coalesce and sets `type` unconditionally,
# so a label that already carries a meaningful `type` loses it. Measured
# during the Phase 0 spike: adopting Component turned every Component.type
# from 'Turbine' to 'COMPONENT', and recovery was a full reload at 4m32s.
#
# The values in the third column are what Lab 2 and Lab 4 queries filter on.
DESTRUCTIVE_ADOPTION_LABELS = {
    "System": (144, "'Engine', 'Avionics', 'Hydraulics'"),
    "Component": (612, "'Turbine' and other component types"),
    "Sensor": (288, "'EGT', 'Vibration' and the other sensor types"),
    "Document": (5, "the document type"),
}


def _check_adoption_labels(label_to_type: dict[str, str]) -> None:
    """Refuse to adopt a label whose ``type`` property would be destroyed.

    Args:
        label_to_type: The adoption map about to be used.

    Raises:
        ValueError: The map names a label carrying a meaningful ``type``.
    """
    unsafe = sorted(set(label_to_type) & set(DESTRUCTIVE_ADOPTION_LABELS))
    if not unsafe:
        return
    detail = "\n".join(
        f"  {label}: {DESTRUCTIVE_ADOPTION_LABELS[label][0]} nodes, "
        f"type currently holds {DESTRUCTIVE_ADOPTION_LABELS[label][1]}"
        for label in unsafe
    )
    raise ValueError(
        "Refusing to adopt "
        + ", ".join(unsafe)
        + ".\nAdoption sets n.type unconditionally, so these nodes would lose "
        "the type values Lab 2 and Lab 4 filter on:\n"
        + detail
        + "\nRecovering means reloading the graph. Adopt Aircraft only."
    )


def adoption_dry_run(
    session: MemorySession,
    *,
    label_to_type: dict[str, str] | None = None,
    name_property_per_label: dict[str, str] | None = None,
) -> Any:
    """Report what adoption would do, without writing anything.

    Run this first, every time. The report names the counts per label, and
    reading it is how you notice you are about to adopt the wrong thing while
    it is still free to notice.

    Args:
        session: An open session.
        label_to_type: Adoption map. Defaults to ``Aircraft`` only.
        name_property_per_label: Name property per label.

    Returns:
        An ``AdoptionReport``.
    """
    label_to_type = label_to_type or dict(ADOPT_LABEL_TO_TYPE)
    _check_adoption_labels(label_to_type)
    return session.run(
        session.client.schema.adopt_existing_graph(
            label_to_type,
            name_property_per_label=name_property_per_label
            or dict(ADOPT_NAME_PROPERTY),
            dry_run=True,
        )
    )


def adopt_aircraft(
    session: MemorySession,
    *,
    label_to_type: dict[str, str] | None = None,
    name_property_per_label: dict[str, str] | None = None,
) -> Any:
    """Adopt the fleet ``Aircraft`` nodes as long-term memory entities.

    Each node gains the ``:Entity`` label plus ``id``, ``type`` and ``name``.
    That is what makes a remembered aircraft the same node as a maintained
    aircraft: from here on, memory writes that mention ``N10004`` land on the
    node Lab 2 loaded rather than on a parallel copy of it.

    Idempotent. Running it twice reports the second set as already adopted.

    Args:
        session: An open session.
        label_to_type: Adoption map. Defaults to ``Aircraft`` only.
        name_property_per_label: Name property per label.

    Returns:
        An ``AdoptionReport``.
    """
    label_to_type = label_to_type or dict(ADOPT_LABEL_TO_TYPE)
    _check_adoption_labels(label_to_type)
    return session.run(
        session.client.schema.adopt_existing_graph(
            label_to_type,
            name_property_per_label=name_property_per_label
            or dict(ADOPT_NAME_PROPERTY),
            dry_run=False,
        )
    )


def describe_adoption_report(report: Any) -> str:
    """Render an ``AdoptionReport`` as one line per label.

    Args:
        report: The report returned by adoption.

    Returns:
        A printable summary.
    """
    lines = []
    for entry in getattr(report, "by_label", []) or []:
        lines.append(
            f"  {getattr(entry, 'label', '?')}: "
            f"migrated={getattr(entry, 'migrated_count', '?')} "
            f"already={getattr(entry, 'already_adopted_count', '?')} "
            f"skipped={getattr(entry, 'skipped_count', '?')}"
        )
    return "\n".join(lines) or f"  {report}"


# =============================================================================
# Explicit mentions
# =============================================================================

# Tail numbers in this fleet are the letter N and five digits. The word
# boundaries keep it from matching inside a longer identifier.
TAIL_NUMBER_RE = re.compile(r"\bN\d{5}\b")


def aircraft_mentions(text: str) -> list[Any]:
    """Find the aircraft a message is about, as ``EntityRef`` values.

    This is the whole of explicit-mention extraction for this lab, and it is
    a regex rather than an LLM call because tail numbers have a format. That
    is the point worth taking away: an agent normally already knows which
    entities its tools touched, so it can name them instead of paying a model
    to rediscover them. Explicit mode is measurably cheaper for it, 5.6
    seconds per message against 9.2, one fewer LLM call on the critical path.

    ``EntityRef`` is not exported from the package root. It has to be
    imported from ``neo4j_agent_memory.schema.models``, which looks internal
    and is the documented path.

    Args:
        text: Message content.

    Returns:
        One ``EntityRef`` per distinct tail number, in first-seen order.
    """
    from neo4j_agent_memory.schema.models import EntityRef

    seen: list[str] = []
    for tail in TAIL_NUMBER_RE.findall(text):
        if tail not in seen:
            seen.append(tail)
    return [
        EntityRef(name=tail, type="AIRCRAFT", label="Aircraft") for tail in seen
    ]


# =============================================================================
# Seeded shift history
# =============================================================================


class SeedMessage:
    """One seeded message: who said it, in which session, and what.

    Attributes:
        technician: User identifier the message is attributed to.
        session_id: Conversation the message belongs to.
        content: What was said.
    """

    __slots__ = ("technician", "session_id", "content")

    def __init__(self, technician: str, session_id: str, content: str) -> None:
        self.technician = technician
        self.session_id = session_id
        self.content = content


# Five technicians, five sessions, ten messages, replayed from the Phase 0
# spike so the demos read against a known answer. The distribution is the
# demo: three separate technicians each pulled the EGT trend on N10011
# without knowing the others had, and the fleet graph ranks N10011 last of
# six on critical events. Neither source says anything interesting alone.
#
# This is seeded in a setup step rather than written by the participant in a
# loop, because a message costs about 5.6 seconds and ten of them is a minute
# of watching a progress counter.
SEED_MESSAGES: tuple[SeedMessage, ...] = (
    SeedMessage(
        "tech:rivera",
        "shift-rivera-01",
        "N10004 came in with an EGT exceedance on the number two engine "
        "last night.",
    ),
    SeedMessage(
        "tech:rivera",
        "shift-rivera-01",
        "Also pulled the trend data on N10011, the EGT margin looks like it "
        "is walking down.",
    ),
    SeedMessage(
        "tech:okafor",
        "shift-okafor-01",
        "Anything known about N10004? It was written up for a hot start on "
        "Tuesday.",
    ),
    SeedMessage(
        "tech:okafor",
        "shift-okafor-01",
        "I want to compare it against N10021 before we swap the turbine.",
    ),
    SeedMessage(
        "tech:lindqvist",
        "shift-lindqvist-01",
        "Working the deferred item on N10004 tonight, the EGT exceedance "
        "from the weekend.",
    ),
    SeedMessage(
        "tech:lindqvist",
        "shift-lindqvist-01",
        "Give me the fuel system history on N10020 as well.",
    ),
    SeedMessage(
        "tech:navarro",
        "shift-navarro-01",
        "N10011 is the one I care about, the EGT margin has been trending "
        "for two weeks.",
    ),
    SeedMessage(
        "tech:navarro",
        "shift-navarro-01",
        "N10021 also needs a look, there was a hydraulic caution on the "
        "last leg.",
    ),
    SeedMessage(
        "tech:abiodun",
        "shift-abiodun-01",
        "Pull everything you have on N10011 please, the EGT trend again.",
    ),
    SeedMessage(
        "tech:abiodun",
        "shift-abiodun-01",
        "And N10027, the landing gear write-up from Tuesday.",
    ),
)


def seed_memory(
    session: MemorySession,
    messages: Iterable[SeedMessage] = SEED_MESSAGES,
    *,
    on_progress: Callable[[int, int, int], None] | None = None,
) -> int:
    """Write the seeded shift history, one message at a time.

    One message at a time is not an oversight. ``add_messages_batch`` is the
    fast path and it takes no ``extraction_mode`` and no ``explicit_mentions``
    at all, so batching would mean either automatic extraction, whose
    ``MENTIONS`` edges are the thing this lab depends on, or no mentions.
    Ten singular writes at about 5.6 seconds each is roughly a minute, which
    is the price of the edges being correct.

    Args:
        session: An open session.
        messages: Messages to write.
        on_progress: Called with ``(index, total, mentions_linked)`` after
            each write.

    Returns:
        Total mentions linked.
    """
    items = list(messages)
    linked = 0
    for index, item in enumerate(items, start=1):
        mentions = aircraft_mentions(item.content)
        session.run(
            session.client.short_term.add_message(
                item.session_id,
                "user",
                item.content,
                extraction_mode="explicit",
                explicit_mentions=mentions,
                user_identifier=item.technician,
            )
        )
        linked += len(mentions)
        if on_progress:
            on_progress(index, len(items), len(mentions))
    return linked


# =============================================================================
# The headline query and its two controls
# =============================================================================

# The one that matters. Line for line the point is the `(ac)` on the second
# MATCH: it is bound in the memory half and reused in the fleet half. Same
# node. No join key, no federation, no second query, because the conversation
# graph and the fleet graph are one graph.
HEADLINE_QUERY = """
// 1. Conversation memory: which aircraft are technicians actually asking about
MATCH (u:User)-[:HAS_CONVERSATION]->(c:Conversation)-[:HAS_MESSAGE]->(m:Message)
      -[:MENTIONS]->(ac:Aircraft)
WITH ac,
     count(DISTINCT u)              AS technicians,
     collect(DISTINCT u.identifier) AS who,
     count(DISTINCT m)              AS mentions
WHERE technicians >= $min_technicians

// 2. Same node, fleet graph: what maintenance actually found
MATCH (ac)<-[:AFFECTS_AIRCRAFT]-(ev:MaintenanceEvent)-[:AFFECTS_SYSTEM]->(sys:System)
RETURN ac.tail_number                                       AS aircraft,
       technicians,
       who                                                  AS asked_by,
       mentions,
       count(ev)                                            AS events,
       count(CASE WHEN ev.severity = 'CRITICAL' THEN 1 END) AS critical,
       collect(DISTINCT sys.type)[0..4]                     AS systems
ORDER BY technicians DESC, critical DESC
"""

# Control one. What a dashboard built on maintenance data alone shows. This
# is the ranking that puts N10011 last.
FLEET_ONLY_QUERY = """
MATCH (ac:Aircraft)<-[:AFFECTS_AIRCRAFT]-(ev:MaintenanceEvent)
RETURN ac.tail_number                                       AS aircraft,
       count(ev)                                            AS events,
       count(CASE WHEN ev.severity = 'CRITICAL' THEN 1 END) AS critical
ORDER BY critical DESC
LIMIT $limit
"""

# Control two. What a memory product with no domain graph shows. This is the
# ranking that puts N10011 joint first.
MEMORY_ONLY_QUERY = """
MATCH (u:User)-[:HAS_CONVERSATION]->(:Conversation)-[:HAS_MESSAGE]->(m:Message)
      -[:MENTIONS]->(ac:Aircraft)
RETURN ac.tail_number   AS aircraft,
       count(DISTINCT u) AS technicians,
       count(DISTINCT m) AS mentions
ORDER BY technicians DESC, mentions DESC
LIMIT $limit
"""


# =============================================================================
# recall and remember, either side of the Lab 5 supervisor
# =============================================================================


class MemoryAgentState(AgentState, total=False):
    """Lab 5's state plus what memory adds.

    Attributes:
        session_id: Conversation this run belongs to. Continuity across
            notebook restarts comes from reusing this value.
        user_identifier: Who is asking. The headline query counts distinct
            values of this.
        recalled: Past messages the recall node found, already formatted.
        remembered: Mentions linked by the remember node, for the trace.
        asked: The question as it was typed. Lab 5 documents ``question`` as
            unchanged for the whole run, and Lab 6 breaks that on purpose:
            the supervisor rewrites ``question`` once, so that the tools see
            the aircraft memory resolved rather than the word "that". The
            original is kept here so nothing is lost.
    """

    session_id: str
    user_identifier: str
    recalled: str
    remembered: int
    asked: str


def format_recalled(messages: Sequence[Any]) -> str:
    """Render recalled messages for a prompt.

    Args:
        messages: ``Message`` values from ``search_messages``.

    Returns:
        One bullet per message, or a line saying there were none.
    """
    if not messages:
        return "(nothing relevant in memory)"
    return "\n".join(f"- {getattr(m, 'content', m)}" for m in messages)


def build_recall_node(
    session: MemorySession,
    *,
    limit: int = RECALL_LIMIT,
    threshold: float = 0.7,
) -> Callable[[MemoryAgentState], dict[str, Any]]:
    """Build the node that reads memory before the supervisor routes.

    Semantic search over past messages, across every session and every
    technician. This is what makes "any vibration trends on that aircraft?"
    resolve after a restart: the aircraft is not in the question, it is in
    what was said last time.

    The search costs 3.4 to 5.0 seconds, and it runs once per question rather
    than once per tool call. Participants will see a Neo4j deprecation warning
    naming ``db.index.vector.queryNodes``; it works on 5.27-aura.

    Args:
        session: An open session.
        limit: Messages to pull back.
        threshold: Minimum similarity.

    Returns:
        A LangGraph node that sets ``recalled``.
    """

    def recall_node(state: MemoryAgentState) -> dict[str, Any]:
        messages = session.run(
            session.client.short_term.search_messages(
                state["question"], limit=limit, threshold=threshold
            )
        )
        return {"recalled": format_recalled(messages)}

    return recall_node


def build_remember_node(
    session: MemorySession,
    *,
    default_session_id: str = "lab6-session-01",
    default_user: str = "tech:you",
) -> Callable[[MemoryAgentState], dict[str, Any]]:
    """Build the node that writes the exchange back to memory.

    Both halves are written, the question and the answer, because the next
    session's recall searches message content and an answer is where the
    findings are. Mentions are taken from the question and the answer
    together, so an aircraft the agent named in its answer is linked even
    when the participant never typed a tail number.

    Args:
        session: An open session.
        default_session_id: Used when the state carries no ``session_id``.
        default_user: Used when the state carries no ``user_identifier``.

    Returns:
        A LangGraph node that sets ``remembered``.
    """

    def remember_node(state: MemoryAgentState) -> dict[str, Any]:
        session_id = state.get("session_id") or default_session_id
        user = state.get("user_identifier") or default_user
        answer = state.get("answer", "")

        linked = 0
        for role, content in (("user", state["question"]), ("assistant", answer)):
            if not content:
                continue
            mentions = aircraft_mentions(f"{state['question']}\n{answer}")
            session.run(
                session.client.short_term.add_message(
                    session_id,
                    role,
                    content,
                    extraction_mode="explicit",
                    explicit_mentions=mentions,
                    user_identifier=user,
                )
            )
            linked += len(mentions)
        return {"remembered": linked}

    return remember_node


# The Lab 5 routing prompt with one paragraph in front of it. Lab 5's
# build_supervisor_node formats exactly three keys, so a prompt carrying a
# fourth needs its own builder rather than a different string.
MEMORY_SUPERVISOR_PROMPT = (
    """\
Before the question, here is what this team has said about the fleet in
earlier sessions. Treat it as context about what people care about, not as
evidence about the aircraft. It can tell you which aircraft "that one" means.
It cannot tell you a measurement.

Recalled from memory:
{recalled}

"""
    + SUPERVISOR_PROMPT
    + """
## Resolving the question first

Routing is not the only thing memory is for. The tools receive the question
text, so a question saying "that aircraft" reaches Genie as "that aircraft"
and Genie asks you which one. Resolve it here instead.

Add one line above the NEXT line:

RESOLVED: <the question, with every reference to an earlier one replaced>

Replace "that aircraft", "it", "the same one" and the like with the tail
number the recalled messages point at. Change nothing else: same wording,
same intent, no extra conditions. When the question already names everything
it needs, or memory holds nothing that resolves it, repeat the question
exactly as it was asked.

Question: Are there any vibration readings I should worry about on that aircraft?
Memory holds: N10011 is the one I care about, the EGT margin has been trending.
Two lines back:

RESOLVED: Are there any vibration readings I should worry about on N10011?
NEXT: genie_node
"""
)


RESOLVED_PREFIX = "RESOLVED:"


def _parse_resolved(decision: str) -> str | None:
    """Pull the rewritten question out of a supervisor reply.

    Args:
        decision: The supervisor's raw reply.

    Returns:
        The text after ``RESOLVED:``, or ``None`` when the reply carries no
        such line or the line is empty.
    """
    for line in decision.splitlines():
        stripped = line.strip()
        if stripped.startswith(RESOLVED_PREFIX):
            return stripped[len(RESOLVED_PREFIX):].strip() or None
    return None


def _pick_tool(text: str, tools: Sequence[str]) -> tuple[str, int]:
    """Lab 5's rule: the tool named last in the reply is the one chosen.

    Args:
        text: The part of the reply to read.
        tools: Tool names the supervisor may name.

    Returns:
        The chosen name and the position it was found at. A position below
        zero means no tool was named at all.
    """
    chosen, best = "synthesize", -1
    for tool in (*tools, "synthesize"):
        position = text.rfind(tool)
        if position > best:
            best, chosen = position, tool
    return chosen, best


def build_memory_supervisor_node(
    llm: Any,
    *,
    available_tools: Sequence[str] | None = None,
    max_tool_calls: int | None = None,
    prompt: str = MEMORY_SUPERVISOR_PROMPT,
) -> Callable[[MemoryAgentState], dict[str, Any]]:
    """Build the Lab 5 supervisor with recalled memory in its prompt.

    Same decision rule as Lab 5 and the same reading of the tool name from the
    end of the reply. Keeping that identical is what makes the memory-off
    versus memory-on comparison mean anything.

    Two things are new. The prompt carries a fourth variable, ``recalled``.
    And on the first pass the node rewrites ``question`` from a ``RESOLVED:``
    line, because routing alone is not enough: the tools are handed the
    question text, so "that aircraft" reaches Genie as "that aircraft" and
    Genie asks which one. Resolving it here is what lets memory change an
    answer rather than only a route.

    Args:
        llm: A ``data_utils.DatabricksLLM``.
        available_tools: Tools the supervisor may name. Defaults to Lab 5's.
        max_tool_calls: Calls allowed before synthesis is forced.
        prompt: Routing prompt, carrying ``{recalled}`` as well as Lab 5's
            ``{question}``, ``{called}`` and ``{findings}``.

    Returns:
        A LangGraph node that sets ``route``.
    """
    from tools import MAX_TOOL_CALLS, TOOL_NAMES, _format_findings

    tools = tuple(available_tools if available_tools is not None else TOOL_NAMES)
    ceiling = MAX_TOOL_CALLS if max_tool_calls is None else max_tool_calls

    def supervisor_node(state: MemoryAgentState) -> dict[str, Any]:
        trace = state.get("trace", [])
        if len(trace) >= ceiling:
            return {"route": "synthesize"}

        rendered = prompt.format(
            question=state["question"],
            called=", ".join(trace) or "(none yet)",
            findings=_format_findings(state.get("findings", [])),
            recalled=state.get("recalled", "(memory not consulted)"),
        )
        decision = llm.invoke(rendered).content

        # The rewrite happens on the first pass only. After a tool has run the
        # question already carries the tail number, and rewriting a rewrite is
        # how a question drifts.
        update: dict[str, Any] = {}
        resolved = _parse_resolved(decision) if not trace else None
        if resolved and resolved != state["question"]:
            update["asked"] = state.get("asked") or state["question"]
            update["question"] = resolved

        # Read the route from below the RESOLVED line. The resolved question is
        # the participant's words, and a tool name inside it would otherwise
        # win the rfind.
        tail = decision
        marker = tail.find(RESOLVED_PREFIX)
        if marker >= 0:
            newline = tail.find("\n", marker)
            tail = tail[newline + 1:] if newline >= 0 else ""

        chosen, best = _pick_tool(tail, tools)
        if best < 0:
            # A reply that put NEXT above RESOLVED leaves nothing below it.
            chosen, best = _pick_tool(decision, tools)
        update["route"] = chosen if best >= 0 else "synthesize"
        return update

    return supervisor_node
