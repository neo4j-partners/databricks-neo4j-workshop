"""MCP Server verification via the Unity Catalog HTTP connection.

Validates that the Neo4j MCP server is reachable through the Unity Catalog HTTP
connection (deployed on AWS AgentCore) and returns expected data. Mirrors
Lab_3_Semantic_Search/04_mcp_graph_queries.ipynb exactly: it calls the MCP
server with the built-in http_request() SQL function over Spark, discovers
tools, retrieves the graph schema, and runs the same Cypher queries the
notebook runs.

Unlike the notebook there is no driver and no MCP credentials in the script.
The connection name is the only configuration; Unity Catalog handles the OAuth2
machine-to-machine flow and token refresh.

Requires:
    - A Spark session on DBR 16.2+ (for http_request()).
    - The Unity Catalog HTTP connection created via
      workshop-setup/MCP-MANUAL-SETUP.md (url ends in /mcp, is_mcp_connection
      = true).
    - The Document-Chunk structure and indexes from run_lab3_01.py loaded into
      the graph (Part 2 and Part 3 checks depend on it).

Usage:
    ./upload.sh run_lab3_04_uc.py && ./submit.sh run_lab3_04_uc.py
"""

import argparse
import json
import sys

# Name of the Unity Catalog HTTP connection that points at the Neo4j MCP server.
# Created via workshop-setup/MCP-MANUAL-SETUP.md. Mirrors the MCP_SERVER constant
# in 04_mcp_graph_queries.ipynb.
MCP_CONNECTION = "aircraft_mcp_server"

# The AgentCore Gateway prefixes every tool name with its target id.
TOOL_GET_SCHEMA = "neo4j-mcp-server-target___get_neo4j_schema"
TOOL_READ_CYPHER = "neo4j-mcp-server-target___read_neo4j_cypher"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lab 3 Validation: Neo4j MCP server via UC HTTP connection"
    )
    parser.add_argument(
        "--mcp-connection",
        default=MCP_CONNECTION,
        help=f"Unity Catalog HTTP connection name (default: {MCP_CONNECTION})",
    )
    # parse_known_args() ignores any other arguments submit.sh injects
    # (Neo4j credentials, data path) — this script needs none of them.
    args, _ = parser.parse_known_args()

    connection = args.mcp_connection

    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()

    print("=" * 70)
    print("Lab 3 Validation: Neo4j MCP server via UC HTTP connection")
    print("=" * 70)
    print(f"Connection:   {connection}")
    print(f"Spark:        {spark.version}")
    print()

    results: list[tuple[str, bool, str]] = []  # (name, passed, detail)

    def record(name: str, passed: bool, detail: str = "") -> None:
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    # ── MCP transport helpers (mirror the notebook) ──────────────────────────

    def http_request(payload_json: str) -> tuple[int, str]:
        """POST a JSON-RPC body to the MCP server through the UC connection.

        The connection name is a SQL string constant; the body binds as a
        parameter so quotes and newlines inside Cypher need no escaping.
        """
        row = spark.sql(
            f"""
            SELECT http_request(
              conn => '{connection}',
              method => 'POST',
              path => '',
              headers => map('Content-Type', 'application/json'),
              json => :payload
            ) AS response
            """,
            args={"payload": payload_json},
        ).collect()[0]["response"]
        return row["status_code"], row["text"]

    def parse_jsonrpc(text: str) -> dict:
        """Parse a JSON-RPC response, tolerating a server-sent-event wrapper."""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("data:"):
                text = stripped[len("data:"):].strip()
                break
        return json.loads(text)

    def mcp_rpc(method: str, params: dict | None = None) -> dict:
        """Send a JSON-RPC request and return its `result` object."""
        payload = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
        )
        status, text = http_request(payload)
        if status != 200:
            raise RuntimeError(f"HTTP {status}: {text}")
        body = parse_jsonrpc(text)
        if "error" in body:
            raise RuntimeError(f"MCP error: {body['error']}")
        return body.get("result", {})

    def mcp_call_tool(tool_name: str, arguments: dict | None = None) -> str:
        """Call an MCP tool and return its concatenated text payload."""
        result = mcp_rpc("tools/call", {"name": tool_name, "arguments": arguments or {}})
        return "\n".join(part.get("text", "") for part in result.get("content", []))

    def read_cypher(query: str) -> str:
        """Run a Cypher query through the MCP read_neo4j_cypher tool."""
        return mcp_call_tool(TOOL_READ_CYPHER, {"query": query})

    def row_count(result_text: str) -> int | None:
        """Best-effort count of rows in a read_neo4j_cypher JSON payload.

        Returns None when the payload is not a JSON list (so callers can fall
        back to substring checks).
        """
        try:
            parsed = json.loads(result_text)
        except (json.JSONDecodeError, TypeError):
            return None
        return len(parsed) if isinstance(parsed, list) else None

    # ══════════════════════════════════════════════════════════════════════════
    # PART 1: Discover and Explore (transport + Lab 2 data)
    # ══════════════════════════════════════════════════════════════════════════

    print("=" * 70)
    print("PART 1: Discover and Explore")
    print("=" * 70)

    # -- Tool discovery -------------------------------------------------------

    try:
        result = mcp_rpc("tools/list")
        tools = result.get("tools", [])
        tool_names = [t["name"] for t in tools]
        record("tools/list", True, f"{len(tools)} tools: {', '.join(tool_names)}")
        record("get_neo4j_schema tool available", TOOL_GET_SCHEMA in tool_names)
        record("read_neo4j_cypher tool available", TOOL_READ_CYPHER in tool_names)
    except Exception as e:  # noqa: BLE001 — surface any transport failure to the report
        record("tools/list", False, str(e))
        _print_summary(results)
        sys.exit(1)  # nothing else can run without a working transport

    # -- Graph schema ---------------------------------------------------------

    try:
        schema = mcp_call_tool(TOOL_GET_SCHEMA)
        record("get_neo4j_schema returns data", len(schema) > 50, f"{len(schema)} chars")
    except Exception as e:  # noqa: BLE001
        record("get_neo4j_schema returns data", False, str(e))

    # -- Node counts ----------------------------------------------------------

    try:
        result = read_cypher("""
        MATCH (n)
        WITH labels(n) AS nodeLabels
        UNWIND nodeLabels AS label
        RETURN label, count(*) AS count
        ORDER BY count DESC
""")
        count = row_count(result)
        record("Node count query returns data",
               (count or 0) > 0 if count is not None else len(result) > 10,
               f"{count} labels" if count is not None else f"{len(result)} chars")
        record("Aircraft nodes present", "Aircraft" in result)
    except Exception as e:  # noqa: BLE001
        record("Node count query returns data", False, str(e))

    # -- Fleet topology (HAS_SYSTEM) ------------------------------------------

    try:
        result = read_cypher("""
        MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)
        RETURN a.tail_number AS aircraft, a.model AS model,
               collect(s.name) AS systems
        ORDER BY a.tail_number
        LIMIT 5
""")
        count = row_count(result)
        record("Fleet topology query (HAS_SYSTEM)",
               (count or 0) > 0 if count is not None else len(result) > 10,
               f"{count} aircraft" if count is not None else f"{len(result)} chars")
    except Exception as e:  # noqa: BLE001
        record("Fleet topology query (HAS_SYSTEM)", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # PART 2: Document-Chunk Queries (require run_lab3_01.py)
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("PART 2: Document-Chunk Queries")
    print("=" * 70)

    try:
        result = read_cypher("""
        MATCH (d:Document)
        OPTIONAL MATCH (d)<-[:FROM_DOCUMENT]-(c:Chunk)
        RETURN d.documentId AS document_id, d.title AS title,
               d.aircraftType AS aircraft_type, count(c) AS chunks
""")
        count = row_count(result)
        has_docs = (count or 0) > 0 if count is not None else len(result) > 10
        record("Document overview query", has_docs,
               f"{count} documents" if count is not None
               else "run run_lab3_01.py if empty")
    except Exception as e:  # noqa: BLE001
        record("Document overview query", False, str(e))

    try:
        result = read_cypher("""
        MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
        WHERE c.index IS NOT NULL
        OPTIONAL MATCH (c)-[:NEXT_CHUNK]->(next:Chunk)
        RETURN c.index AS chunk_index,
               substring(c.text, 0, 80) AS preview,
               next.index AS next_chunk
        ORDER BY c.index
        LIMIT 5
""")
        count = row_count(result)
        record("Chunk chain traversal (NEXT_CHUNK)",
               (count or 0) > 0 if count is not None else len(result) > 10,
               f"{count} chunks" if count is not None else "run run_lab3_01.py if empty")
    except Exception as e:  # noqa: BLE001
        record("Chunk chain traversal (NEXT_CHUNK)", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # PART 3: Graph-Enhanced Search (require fulltext index from run_lab3_01.py)
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("PART 3: Graph-Enhanced Search")
    print("=" * 70)

    try:
        result = read_cypher("""
        CALL db.index.fulltext.queryNodes('maintenanceChunkText', 'engine vibration troubleshoot')
        YIELD node, score
        MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
        RETURN doc.documentId AS document_id,
               doc.aircraftType AS aircraft_type,
               doc.title AS title,
               node.index AS chunk_index,
               score,
               substring(node.text, 0, 200) AS context
        ORDER BY score DESC
        LIMIT 3
""")
        count = row_count(result)
        record("Example 1: document context (fulltext + FROM_DOCUMENT)",
               (count or 0) > 0 if count is not None else len(result) > 20,
               f"{count} results" if count is not None else "requires run_lab3_01.py")
    except Exception as e:  # noqa: BLE001
        record("Example 1: document context (fulltext + FROM_DOCUMENT)", False, str(e))

    try:
        result = read_cypher("""
        CALL db.index.fulltext.queryNodes('maintenanceChunkText', 'hydraulic pressure limits')
        YIELD node, score
        OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(node)
        OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
        MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
        RETURN doc.documentId AS document_id,
               node.index AS chunk_index,
               substring(COALESCE(prev.text, ''), 0, 100) AS previous_context,
               substring(node.text, 0, 200) AS main_context,
               substring(COALESCE(next.text, ''), 0, 100) AS next_context
        ORDER BY score DESC
        LIMIT 3
""")
        count = row_count(result)
        record("Example 2: adjacent chunks (fulltext + NEXT_CHUNK)",
               (count or 0) > 0 if count is not None else len(result) > 20,
               f"{count} results" if count is not None else "requires run_lab3_01.py")
    except Exception as e:  # noqa: BLE001
        record("Example 2: adjacent chunks (fulltext + NEXT_CHUNK)", False, str(e))

    try:
        result = read_cypher("""
        CALL db.index.fulltext.queryNodes('maintenanceChunkText', 'fuel pump maintenance')
        YIELD node, score
        MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)-[:APPLIES_TO]->(a:Aircraft)
        MATCH (a)-[:HAS_SYSTEM]->(s:System)
        OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(comp:Component)
        WITH node, doc, a, s, comp, score
        RETURN doc.documentId AS document_id,
               doc.aircraftType AS aircraft_type,
               a.tail_number AS aircraft,
               COLLECT(DISTINCT s.name)[0..3] AS systems,
               COLLECT(DISTINCT comp.name)[0..3] AS components,
               substring(node.text, 0, 200) AS context,
               score
        ORDER BY score DESC
        LIMIT 3
""")
        count = row_count(result)
        record("Example 3: topology traversal (Chunk->Doc->Aircraft->System)",
               (count or 0) > 0 if count is not None else len(result) > 20,
               f"{count} results" if count is not None else "requires run_lab3_01.py")
    except Exception as e:  # noqa: BLE001
        record("Example 3: topology traversal (Chunk->Doc->Aircraft->System)", False, str(e))

    # Operating limits depend on what the LLM extracted in notebook 01, so this
    # is a soft check: it passes when the full-chain query executes, even if the
    # operating_limits collection comes back empty.
    try:
        read_cypher("""
        CALL db.index.fulltext.queryNodes('maintenanceChunkText', 'EGT temperature limits')
        YIELD node, score
        MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)-[:APPLIES_TO]->(a:Aircraft)
        OPTIONAL MATCH (a)-[:HAS_SYSTEM]->(sys:System)-[:HAS_SENSOR]->(s:Sensor)-[:HAS_LIMIT]->(ol:OperatingLimit)
        WITH node, doc, a, score,
             COLLECT(DISTINCT {
                 sensor: s.type,
                 parameter: ol.parameterName,
                 max: ol.maxValue,
                 unit: ol.unit,
                 regime: ol.regime
             })[0..5] AS operating_limits
        RETURN doc.aircraftType AS aircraft_type,
               operating_limits,
               substring(node.text, 0, 200) AS context
        ORDER BY score DESC
        LIMIT 3
""")
        record("Example 4: operating limits chain (soft)", True,
               "full-chain query executed (limits may be empty depending on extraction)")
    except Exception as e:  # noqa: BLE001
        record("Example 4: operating limits chain (soft)", False, str(e))

    # ── Summary ──────────────────────────────────────────────────────────────

    _print_summary(results)

    failed = sum(1 for _, passed, _ in results if not passed)
    if failed > 0:
        sys.exit(1)


def _print_summary(results: list[tuple[str, bool, str]]) -> None:
    """Print the PASS/FAIL summary table."""
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, p, detail in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    print()
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}")
    print("=" * 70)

    if failed > 0:
        print("FAILED")
    else:
        print("SUCCESS")


if __name__ == "__main__":
    main()
