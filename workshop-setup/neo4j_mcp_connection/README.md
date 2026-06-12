# Neo4j MCP Connection for Databricks

Notebooks that support connecting Databricks to the Neo4j MCP server via a
Unity Catalog HTTP connection with OAuth2 M2M authentication.

## Setup

Follow **[`MCP-MANUAL-SETUP.md`](../MCP-MANUAL-SETUP.md)** to create the
connection in the Databricks UI. The two notebooks here cover edge cases:

| Notebook | When to use |
|----------|-------------|
| [`mcp-set-flag.ipynb`](./mcp-set-flag.ipynb) | The **Is MCP connection** checkbox was missing from the UI during connection creation |
| [`mcp-validate.ipynb`](./mcp-validate.ipynb) | Confirm the connection is live after setup |

## Architecture

```
Notebook / SQL query
      │
      │  http_request() or LangGraph tool call
      v
Unity Catalog HTTP Connection
      │  OAuth2 M2M (Databricks handles token exchange and refresh)
      v
Databricks HTTP Proxy  /api/2.0/mcp/external/{connection_name}
      │  HTTPS + JWT Bearer Token  ·  JSON-RPC 2.0
      v
Neo4j MCP Server  (AWS AgentCore)
      │  Bolt Protocol
      v
Neo4j Aura
```

### How it works

1. A Unity Catalog HTTP connection stores the MCP server endpoint and OAuth2
   credentials. Databricks handles token exchange and refresh automatically.
2. Notebooks call `http_request()` against the connection name, or a LangGraph
   agent invokes MCP tools via the `DatabricksMCPClient`.
3. Databricks routes the request through its internal proxy, which authenticates
   with the MCP server and forwards the JSON-RPC body.
4. The MCP server executes the Cypher query against Neo4j and returns results.

The proxy URL format is:
```
{workspace_host}/api/2.0/mcp/external/{connection_name}
```

## Available MCP tools

Tool names are prefixed by the AgentCore Gateway:

| Tool | Gateway name |
|------|--------------|
| `get_neo4j_schema` | `neo4j-mcp-server-target___get_neo4j_schema` |
| `read_neo4j_cypher` | `neo4j-mcp-server-target___read_neo4j_cypher` |

Run `tools/list` (Step 1 of `mcp-validate.ipynb`) to confirm the exact names
for your deployment.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Re-run `./deploy.sh credentials` in `neo4j-agentcore-mcp-server/`, then re-enter credentials in Catalog Explorer. |
| Connection not listed as MCP | Run `mcp-set-flag.ipynb`. |
| `url` ends in `:443/` not `/mcp` | Set `BASE_PATH` to `/mcp` in `mcp-set-flag.ipynb` and re-run. |
| HTTP timeout | Verify the MCP server is running: `cd neo4j-agentcore-mcp-server && ./cloud.sh`. |
| Tool not found | Use the Gateway-prefixed name. Run `tools/list` to discover the exact names. |

## Related documentation

- [`MCP-MANUAL-SETUP.md`](../MCP-MANUAL-SETUP.md) — step-by-step UI setup guide
- [Databricks HTTP Connections](https://docs.databricks.com/aws/en/query-federation/http)
- [Databricks External MCP](https://docs.databricks.com/aws/en/generative-ai/mcp/external-mcp)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
