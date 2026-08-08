"""The Lab 5 supervisor graph, wrapped as an MLflow ``ResponsesAgent``.

``01_langgraph_agent.ipynb`` builds the agent inside a notebook, where ``spark``
and ``dbutils`` exist and the participant owns every credential the tools need.
A Model Serving container has none of that. This module is the same agent with
those two assumptions removed:

- **Credentials arrive as environment variables**, not from ``dbutils``. The
  endpoint is deployed with ``NEO4J_URI``, ``NEO4J_USERNAME`` and
  ``NEO4J_PASSWORD`` bound to ``{{secrets/<scope>/<key>}}`` references, so the
  password is resolved by the serving control plane and never written down.
- **Everything else arrives as model config**, logged beside the model, so the
  Genie space the endpoint may reach is fixed at log time and matches the
  ``DatabricksGenieSpace`` resource declared in the same call.

The nodes themselves come from ``tools.py`` unchanged. Only the wiring is
repeated here, and it is repeated rather than shared because Section 7 of the
notebook is a teaching artifact that should stay readable in place.

The module is loaded by ``mlflow.pyfunc.log_model(python_model="agent.py")``.
The last line hands :data:`AGENT` to MLflow, which is what makes this file the
model rather than a library beside it.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import mlflow
from mlflow.models import ModelConfig, set_model
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

from tools import (
    EMBEDDING_MODEL,
    MAX_TOOL_CALLS,
    SUPERVISOR_MODEL,
    TOOL_NAMES,
    AgentState,
    build_cypher_node,
    build_genie_node,
    build_graphrag_node,
    build_neo4j_driver,
    build_supervisor_node,
    build_synthesize_node,
    get_embedder,
    get_llm,
    read_neo4j_secrets,
    route_from_supervisor,
)

__all__ = [
    "AGENT",
    "DEFAULT_CONFIG",
    "ENV_NEO4J_PASSWORD",
    "ENV_NEO4J_URI",
    "ENV_NEO4J_USERNAME",
    "MISSING_CREDENTIAL_MESSAGE",
    "AgentRuntime",
    "FleetOpsAgent",
    "build_runtime",
    "export_neo4j_env",
    "resolve_database",
    "serving_environment_vars",
]


# =============================================================================
# Configuration
# =============================================================================

# The three names the endpoint's environment block binds to secret references.
# They are read here and nowhere else, so a rename is one edit.
ENV_NEO4J_URI = "NEO4J_URI"
ENV_NEO4J_USERNAME = "NEO4J_USERNAME"
ENV_NEO4J_PASSWORD = "NEO4J_PASSWORD"

# Everything that is not a credential travels as model config instead, logged
# with the model. genie_space_id in particular has to agree with the
# DatabricksGenieSpace resource declared at log time, and config keeps the two
# in one cell rather than in two places that can drift.
DEFAULT_CONFIG: dict[str, Any] = {
    "genie_space_id": "",
    "neo4j_database": "",
    "supervisor_model": SUPERVISOR_MODEL,
    "embedding_model": EMBEDDING_MODEL,
    "top_k": 3,
    "max_tool_calls": MAX_TOOL_CALLS,
}

MISSING_CREDENTIAL_MESSAGE = (
    "This agent could not open its Neo4j connection, so no tool ran.\n\n"
    "{detail}\n\n"
    "The endpoint reads its Aura credentials from the environment variables "
    f"{ENV_NEO4J_URI}, {ENV_NEO4J_USERNAME} and {ENV_NEO4J_PASSWORD}, each "
    "deployed as a '{{secrets/<scope>/<key>}}' reference into the "
    "'fleet-ops-<your-user>' scope from Lab 3 notebook 01. Check that the "
    "endpoint carries all three, and that whoever created the endpoint can "
    "still read that scope."
)


def export_neo4j_env(dbutils: Any, scope: str) -> tuple[str, ...]:
    """Copy the Lab 3 secret scope into this process's environment.

    The notebook needs the same three variables the endpoint will get, so that
    what it tests locally is what gets deployed. The values are read, written
    to ``os.environ`` and dropped inside this call, so no notebook cell binds a
    password to a name of its own.

    Args:
        dbutils: The notebook's dbutils handle.
        scope: Scope name from ``tools.secret_scope_name``.

    Returns:
        The environment variable names that were set.
    """
    credentials = read_neo4j_secrets(dbutils, scope)
    os.environ[ENV_NEO4J_URI] = credentials["uri"]
    os.environ[ENV_NEO4J_USERNAME] = credentials["username"]
    os.environ[ENV_NEO4J_PASSWORD] = credentials["password"]
    return (ENV_NEO4J_URI, ENV_NEO4J_USERNAME, ENV_NEO4J_PASSWORD)


def serving_environment_vars(scope: str) -> dict[str, str]:
    """Build the environment block a serving endpoint needs for Neo4j.

    Each value is a secret reference rather than a secret. Model Serving
    resolves ``{{secrets/scope/key}}`` when the endpoint config is applied, so
    the password exists only inside the container and never appears in the
    notebook, in MLflow, or in the endpoint's own configuration.

    Args:
        scope: Scope name from ``tools.secret_scope_name``.

    Returns:
        A mapping suitable for ``agents.deploy(environment_vars=...)``.
    """
    from data_utils import (
        SECRET_KEY_NEO4J_PASSWORD,
        SECRET_KEY_NEO4J_URI,
        SECRET_KEY_NEO4J_USERNAME,
    )

    return {
        ENV_NEO4J_URI: f"{{{{secrets/{scope}/{SECRET_KEY_NEO4J_URI}}}}}",
        ENV_NEO4J_USERNAME: f"{{{{secrets/{scope}/{SECRET_KEY_NEO4J_USERNAME}}}}}",
        ENV_NEO4J_PASSWORD: f"{{{{secrets/{scope}/{SECRET_KEY_NEO4J_PASSWORD}}}}}",
    }


# =============================================================================
# Building the runtime
# =============================================================================


@dataclass(frozen=True)
class AgentRuntime:
    """Everything the served agent builds once and reuses per request.

    Attributes:
        graph: The compiled LangGraph.
        driver: The connected ``neo4j.Driver`` the graph's two Neo4j tools share.
        database: The Neo4j database those tools query.
        available_tools: The tools the supervisor was offered. ``graphrag_node``
            drops out of this when the vector index is absent.
    """

    graph: Any
    driver: Any
    database: str
    available_tools: tuple[str, ...]


def resolve_database(driver: Any, requested: str = "") -> str:
    """Name the Neo4j database the tools should query.

    An Aura instance answers to ``neo4j``, and that is what Lab 2 and Lab 3 use.
    Some instances carry a database named after the instance instead, and a
    hardcoded ``neo4j`` fails against those with a routing error rather than a
    readable one. An empty request therefore asks the server.

    Args:
        driver: A connected ``neo4j.Driver``.
        requested: Database name from the model config, or empty to resolve.

    Returns:
        The database name to pass as ``database_``.

    Raises:
        RuntimeError: The instance holds several databases and none is
            ``neo4j``, so the choice cannot be made here.
    """
    if requested:
        return requested
    records, _, _ = driver.execute_query(
        "SHOW DATABASES YIELD name RETURN DISTINCT name", database_="system"
    )
    names = [record["name"] for record in records if record["name"] != "system"]
    if "neo4j" in names:
        return "neo4j"
    if len(names) == 1:
        return names[0]
    raise RuntimeError(
        f"Cannot choose a Neo4j database among {names}. Set 'neo4j_database' "
        "in the model config to the one this agent should query."
    )


def build_runtime(config: Mapping[str, Any]) -> AgentRuntime:
    """Open the connections and wire the graph.

    The wiring is Section 7 of ``01_langgraph_agent.ipynb``: ``START`` to the
    supervisor, the supervisor's route to one tool or to synthesis, every tool
    back to the supervisor, synthesis to ``END``.

    Args:
        config: The logged model config. See :data:`DEFAULT_CONFIG`.

    Returns:
        A built :class:`AgentRuntime`.

    Raises:
        RuntimeError: A required credential or config value is missing.
    """
    from databricks.sdk import WorkspaceClient
    from langgraph.graph import END, START, StateGraph

    genie_space_id = config.get("genie_space_id") or ""
    if not genie_space_id:
        raise RuntimeError(
            "No 'genie_space_id' in the model config. The agent was logged "
            "without one, so genie_node has nothing to ask."
        )
    missing = [
        name
        for name in (ENV_NEO4J_URI, ENV_NEO4J_USERNAME, ENV_NEO4J_PASSWORD)
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}.")

    driver = build_neo4j_driver(
        os.environ[ENV_NEO4J_URI],
        os.environ[ENV_NEO4J_USERNAME],
        os.environ[ENV_NEO4J_PASSWORD],
    )
    database = resolve_database(driver, config.get("neo4j_database") or "")

    llm = get_llm(config.get("supervisor_model", SUPERVISOR_MODEL))
    embedder = get_embedder(config.get("embedding_model", EMBEDDING_MODEL))

    genie_node = build_genie_node(genie_space_id, WorkspaceClient())
    cypher_node = build_cypher_node(driver, llm, database=database)
    graphrag_node = build_graphrag_node(
        driver, llm, embedder, database=database, top_k=config.get("top_k", 3)
    )

    # Same rule as Section 6 of the notebook. A tool that cannot answer is
    # dropped from the supervisor's options rather than offered and refused.
    available = tuple(
        name
        for name in TOOL_NAMES
        if name != "graphrag_node" or getattr(graphrag_node, "available", False)
    )
    supervisor_node = build_supervisor_node(
        llm,
        available_tools=available,
        max_tool_calls=config.get("max_tool_calls", MAX_TOOL_CALLS),
    )
    synthesize_node = build_synthesize_node(llm)

    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("genie_node", genie_node)
    builder.add_node("cypher_node", cypher_node)
    builder.add_node("graphrag_node", graphrag_node)
    builder.add_node("synthesize", synthesize_node)
    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "genie_node": "genie_node",
            "cypher_node": "cypher_node",
            "graphrag_node": "graphrag_node",
            "synthesize": "synthesize",
        },
    )
    for tool_name in TOOL_NAMES:
        builder.add_edge(tool_name, "supervisor")
    builder.add_edge("synthesize", END)

    return AgentRuntime(
        graph=builder.compile(),
        driver=driver,
        database=database,
        available_tools=available,
    )


# =============================================================================
# The served agent
# =============================================================================


def _question_from_request(items: Sequence[Any]) -> str:
    """Pull the question out of a Responses API input list.

    The agent answers one question at a time, so the newest user turn is the
    whole input. Lab 6 is where earlier turns start to matter.

    Args:
        items: ``ResponsesAgentRequest.input``.

    Returns:
        The text of the most recent user message.

    Raises:
        ValueError: The request carried no user text.
    """
    for item in reversed(list(items)):
        data = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        if data.get("role") not in (None, "user"):
            continue
        content = data.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            text = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, Mapping)
            ).strip()
            if text:
                return text
    raise ValueError("The request carried no user message to answer.")


class FleetOpsAgent(ResponsesAgent):
    """The Lab 5 supervisor, served over the Responses API.

    Connections are opened on the first request rather than at load time. A
    container that fails while loading restarts, fails again, and leaves an
    endpoint that never reaches READY with the reason buried in build logs. A
    container that fails on the first request answers with the reason, which is
    the difference between a five-minute fix and an afternoon.
    """

    def __init__(self, config: ModelConfig | None = None) -> None:
        self._config = config or ModelConfig(development_config=DEFAULT_CONFIG)
        self._runtime: AgentRuntime | None = None
        self._build_error = ""

    def _ensure_runtime(self) -> AgentRuntime | None:
        """Build the runtime once, remembering a failure rather than retrying."""
        if self._runtime is None and not self._build_error:
            try:
                self._runtime = build_runtime(self._config.to_dict())
            except Exception as error:  # noqa: BLE001 - returned to the caller
                self._build_error = f"{type(error).__name__}: {error}"
        return self._runtime

    @mlflow.trace(name="fleet_ops_agent")
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        """Answer one question.

        Args:
            request: A Responses API request whose newest user message is the
                question.

        Returns:
            One output text item holding the synthesized answer, with the route
            the supervisor took in ``custom_outputs``.
        """
        runtime = self._ensure_runtime()
        if runtime is None:
            return ResponsesAgentResponse(
                output=[
                    self.create_text_output_item(
                        text=MISSING_CREDENTIAL_MESSAGE.format(
                            detail=self._build_error
                        ),
                        id=str(uuid.uuid4()),
                    )
                ],
                custom_outputs={"error": self._build_error, "trace": []},
            )

        question = _question_from_request(request.input)
        state = runtime.graph.invoke(
            {"question": question, "trace": [], "findings": []}
        )
        return ResponsesAgentResponse(
            output=[
                self.create_text_output_item(
                    text=state.get("answer", ""), id=str(uuid.uuid4())
                )
            ],
            custom_outputs={
                "trace": state.get("trace", []),
                "available_tools": list(runtime.available_tools),
                "findings": [
                    {"tool": finding["tool"], "content": finding["content"]}
                    for finding in state.get("findings", [])
                ],
            },
        )

    def predict_stream(
        self, request: ResponsesAgentRequest
    ) -> Iterator[ResponsesAgentStreamEvent]:
        """Emit the answer as one completed output item.

        The graph has no token stream to forward: every node returns a whole
        finding, and the answer is written in one call at the end. Streaming
        exists so a Responses API client that only speaks streaming still works.

        Args:
            request: The same request :meth:`predict` takes.

        Yields:
            One ``response.output_item.done`` event per output item.
        """
        response = self.predict(request)
        for item in response.output:
            yield ResponsesAgentStreamEvent(
                type="response.output_item.done",
                item=item,
                custom_outputs=response.custom_outputs,
            )


mlflow.langchain.autolog()

AGENT = FleetOpsAgent()
set_model(AGENT)
