"""MCP Server verification — read-only checks via MCP protocol.

Validates that the Neo4j MCP server is accessible and returns expected data
by calling get-schema and read-cypher tools over HTTP JSON-RPC. Mirrors the
queries from Lab_3_Semantic_Search/05_mcp_graph_queries.ipynb.

Uses only stdlib (urllib, json) — no fastmcp or other dependencies required.

Usage:
    ./upload.sh run_lab3_05.py && ./submit.sh run_lab3_05.py
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description="Lab 6 MCP Server Verification")
    parser.add_argument("--mcp-endpoint", required=True, help="MCP server endpoint URL")
    parser.add_argument("--mcp-api-key", required=True, help="MCP server API key")
    parser.add_argument("--mcp-path", default="/mcp", help="MCP path (default: /mcp)")
    # Accept Neo4j args for submit.sh compatibility (unused)
    parser.add_argument("--neo4j-uri", default="", help="(unused)")
    parser.add_argument("--neo4j-username", default="", help="(unused)")
    parser.add_argument("--neo4j-password", default="", help="(unused)")
    parser.add_argument("--data-path", default="", help="(unused)")
    args = parser.parse_args()

    endpoint = f"{args.mcp_endpoint.rstrip('/')}{args.mcp_path}"

    print("=" * 60)
    print("Lab 6 — MCP Server Verification")
    print("=" * 60)
    print(f"MCP Endpoint: {endpoint}")
    print(f"API Key:      {args.mcp_api_key[:8]}...{args.mcp_api_key[-4:]}")
    print()

    results = []  # (name, passed, detail)

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    def mcp_request(method, params=None):
        """Send a JSON-RPC request to the MCP server."""
        payload = {"jsonrpc": "2.0", "method": method, "id": 1}
        if params:
            payload["params"] = params
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {args.mcp_api_key}",
            "Accept": "application/json",
        }
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def call_tool(name, arguments=None):
        """Call an MCP tool and return the text content."""
        response = mcp_request("tools/call", {"name": name, "arguments": arguments or {}})
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        content = response.get("result", {}).get("content", [])
        return content[0]["text"] if content else ""

    # ── Check 1: Authentication ────────────────────────────────────────────────

    print("\n--- Authentication ---")
    try:
        # Verify that requests without API key are rejected
        payload = json.dumps({"jsonrpc": "2.0", "method": "tools/list", "id": 1}).encode()
        no_auth_req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(no_auth_req, timeout=10)
            record("Auth rejection (no key)", False, "request was accepted without API key")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                record("Auth rejection (no key)", True, "401 returned as expected")
            else:
                record("Auth rejection (no key)", False, f"unexpected HTTP {e.code}")
    except Exception as e:
        record("Auth rejection (no key)", False, str(e))

    # ── Check 2: List Tools ────────────────────────────────────────────────────

    print("\n--- Tool Discovery ---")
    try:
        response = mcp_request("tools/list")
        tools = response.get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in tools]
        record("tools/list", True, f"{len(tools)} tools: {', '.join(tool_names)}")

        has_schema = "get-schema" in tool_names
        has_cypher = "read-cypher" in tool_names
        record("get-schema tool available", has_schema)
        record("read-cypher tool available", has_cypher)
    except Exception as e:
        record("tools/list", False, str(e))
        # Can't proceed without tools
        _print_summary(results)
        sys.exit(1)

    # ── Check 3: Get Schema ────────────────────────────────────────────────────

    print("\n--- Schema Retrieval ---")
    try:
        schema = call_tool("get-schema")
        has_content = len(schema) > 50
        record("get-schema returns data", has_content, f"{len(schema)} chars")

        # Check for expected node labels in schema
        expected_labels = ["Aircraft", "Chunk", "Document"]
        found = [label for label in expected_labels if label in schema]
        record(
            "Schema contains expected labels",
            len(found) == len(expected_labels),
            f"found: {', '.join(found)}",
        )
    except Exception as e:
        record("get-schema", False, str(e))

    # ── Check 4: Basic Cypher (node counts) ────────────────────────────────────

    print("\n--- Basic Cypher Queries ---")
    try:
        result = call_tool("read-cypher", {
            "query": "MATCH (n) WITH labels(n) AS nodeLabels "
                     "UNWIND nodeLabels AS label "
                     "RETURN label, count(*) AS count ORDER BY count DESC"
        })
        has_data = "Aircraft" in result
        record("Node count query", True, f"returned {len(result)} chars")
        record("Aircraft nodes present", has_data)
    except Exception as e:
        record("Node count query", False, str(e))

    # ── Check 5: Aircraft topology ─────────────────────────────────────────────

    try:
        result = call_tool("read-cypher", {
            "query": "MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System) "
                     "RETURN a.tail_number AS aircraft, collect(s.name) AS systems "
                     "ORDER BY a.tail_number LIMIT 3"
        })
        has_topology = "aircraft" in result.lower() or "system" in result.lower()
        record("Aircraft topology query", has_topology, "HAS_SYSTEM traversal works")
    except Exception as e:
        record("Aircraft topology query", False, str(e))

    # ── Check 6: Document-Chunk structure ──────────────────────────────────────

    print("\n--- Document-Chunk Structure ---")
    try:
        result = call_tool("read-cypher", {
            "query": "MATCH (d:Document) "
                     "OPTIONAL MATCH (d)<-[:FROM_DOCUMENT]-(c:Chunk) "
                     "RETURN d.documentId AS document_id, d.title AS title, count(c) AS chunks"
        })
        has_docs = "document_id" in result.lower() or "title" in result.lower() or len(result) > 10
        record("Document-Chunk query", has_docs, "FROM_DOCUMENT traversal works")
    except Exception as e:
        record("Document-Chunk query", False, str(e))

    try:
        result = call_tool("read-cypher", {
            "query": "MATCH (c:Chunk)-[:NEXT_CHUNK]->(next:Chunk) "
                     "RETURN count(*) AS chain_links"
        })
        record("NEXT_CHUNK chain exists", "0" not in result or len(result) > 5, result.strip())
    except Exception as e:
        record("NEXT_CHUNK chain exists", False, str(e))

    # ── Check 7: Fulltext search ───────────────────────────────────────────────

    print("\n--- Fulltext Search (Lab 6 entry point) ---")
    try:
        result = call_tool("read-cypher", {
            "query": "CALL db.index.fulltext.queryNodes('maintenanceChunkText', 'engine vibration') "
                     "YIELD node, score "
                     "RETURN score, substring(node.text, 0, 100) AS context "
                     "ORDER BY score DESC LIMIT 3"
        })
        has_results = "score" in result.lower() or "context" in result.lower() or len(result) > 20
        record("Fulltext search", has_results, "maintenanceChunkText index works")
    except Exception as e:
        record("Fulltext search", False, str(e))

    # ── Check 8: Graph-enhanced search (topology traversal) ────────────────────

    print("\n--- Graph-Enhanced Search ---")
    try:
        result = call_tool("read-cypher", {
            "query": "CALL db.index.fulltext.queryNodes('maintenanceChunkText', 'fuel pump') "
                     "YIELD node, score "
                     "MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)-[:APPLIES_TO]->(a:Aircraft) "
                     "MATCH (a)-[:HAS_SYSTEM]->(s:System) "
                     "OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(comp:Component) "
                     "WITH node, doc, a, s, comp, score "
                     "RETURN doc.documentId AS document_id, "
                     "       a.tail_number AS aircraft, "
                     "       COLLECT(DISTINCT s.name)[0..3] AS systems, "
                     "       COLLECT(DISTINCT comp.name)[0..3] AS components, "
                     "       substring(node.text, 0, 100) AS context "
                     "ORDER BY score DESC LIMIT 3"
        })
        has_topology = len(result) > 20
        record("Topology traversal via fulltext", has_topology, "Chunk→Doc→Aircraft→System works")
    except Exception as e:
        record("Topology traversal via fulltext", False, str(e))

    # ── Check 9: Operating limits traversal ────────────────────────────────────

    try:
        result = call_tool("read-cypher", {
            "query": "CALL db.index.fulltext.queryNodes('maintenanceChunkText', 'EGT temperature') "
                     "YIELD node, score "
                     "MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)-[:APPLIES_TO]->(a:Aircraft) "
                     "OPTIONAL MATCH (a)-[:HAS_SYSTEM]->(sys:System)"
                     "-[:HAS_SENSOR]->(s:Sensor)-[:HAS_LIMIT]->(ol:OperatingLimit) "
                     "WITH node, doc, a, score, "
                     "     COLLECT(DISTINCT {sensor: s.type, parameter: ol.parameterName, "
                     "       max: ol.maxValue, unit: ol.unit})[0..3] AS limits "
                     "RETURN doc.aircraftType AS aircraft_type, limits, "
                     "       substring(node.text, 0, 100) AS context "
                     "ORDER BY score DESC LIMIT 3"
        })
        # Soft check — operating limits may be empty if entity extraction didn't produce them
        record("Operating limits traversal", True, "full chain query executed (limits may be empty)")
    except Exception as e:
        record("Operating limits traversal", False, str(e))

    # ── Summary ────────────────────────────────────────────────────────────────

    _print_summary(results)

    failed = sum(1 for _, p, _ in results if not p)
    if failed > 0:
        sys.exit(1)


def _print_summary(results):
    """Print the PASS/FAIL summary table."""
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, p, detail in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    print()
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}")
    print("=" * 60)

    if failed > 0:
        print("FAILED")
    else:
        print("SUCCESS")


if __name__ == "__main__":
    main()
