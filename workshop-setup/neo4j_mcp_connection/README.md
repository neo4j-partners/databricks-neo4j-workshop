# Neo4j MCP Connection for Databricks

Sample notebooks for integrating Neo4j MCP Server with Databricks via Unity Catalog HTTP connections.

## Quick Start

### Prerequisites

- **Neo4j MCP server deployed** to an external hosting platform (container service, VM, etc.) with an HTTP endpoint and OAuth2 M2M credentials
- **Databricks CLI** installed and authenticated (`databricks auth login`)
- **Databricks cluster** running Runtime 15.4 LTS or later with [required libraries](#cluster-setup) installed
- **Unity Catalog** enabled on your workspace

### Step 1: Deploy the Neo4j MCP Server

Deploy the Neo4j MCP server to your hosting platform of choice. The server must expose an HTTP endpoint that accepts JSON-RPC 2.0 requests and supports OAuth2 M2M authentication.

After deployment, you need these OAuth2 credentials:
- **Gateway host URL** (the MCP server endpoint)
- **Client ID** and **Client Secret**
- **Token endpoint** (for OAuth2 token exchange)
- **OAuth scope**

### Step 2: Configure Databricks Secrets

Store the OAuth2 credentials in a Databricks secret scope:

```bash
# Create the secret scope
databricks secrets create-scope mcp-neo4j-secrets

# Store each credential
echo -n "https://your-mcp-server-host" | databricks secrets put-secret mcp-neo4j-secrets gateway_host
echo -n "your-client-id" | databricks secrets put-secret mcp-neo4j-secrets client_id
echo -n "your-client-secret" | databricks secrets put-secret mcp-neo4j-secrets client_secret
echo -n "https://your-token-endpoint/oauth2/token" | databricks secrets put-secret mcp-neo4j-secrets token_endpoint
echo -n "your-oauth-scope" | databricks secrets put-secret mcp-neo4j-secrets oauth_scope
```

### Step 3: Import and Run the HTTP Connection Notebook

1. Import `neo4j-mcp-http-connection.ipynb` into your Databricks workspace
2. Attach it to a cluster running Databricks Runtime 15.4 LTS or later
3. Update the configuration cell with your secret scope name (default: `mcp-neo4j-secrets`)
4. Run all cells to create the connection and test it

### Step 4: Enable MCP on the Connection

The notebook creates an HTTP connection, but you must manually enable MCP:

1. In the Databricks sidebar, click **Catalog**
2. Navigate to **External Data** > **Connections**
3. Click on your connection name (e.g., `neo4j_agentcore_mcp`)
4. Click the **three-dot menu** and select **Edit**
5. Check the **Is MCP connection** box
6. Click **Update** to save

### Step 5 (Optional): Deploy the LangGraph Agent

To deploy a full LangGraph agent that queries Neo4j:

1. Create Unity Catalog resources: catalog `mcp_demo_catalog` with schema `agents`
2. Import `neo4j_mcp_agent.py` and `neo4j-mcp-agent-deploy.ipynb` into your workspace
3. Run `neo4j-mcp-agent-deploy.ipynb` to test, evaluate, and deploy the agent

## Cluster Setup

Before running the notebooks, configure your Databricks cluster with the required libraries.

### Create or Edit a Cluster

1. Navigate to **Compute** in the Databricks sidebar
2. Create a new cluster or edit an existing one
3. Under **Performance**, check **Machine learning** to enable ML Runtime
4. Select **Databricks Runtime**: 17.3 LTS ML or later recommended
5. Enable **Single node** for development/testing (optional)

### Install Required Libraries

Go to the **Libraries** tab on your cluster and install these packages from PyPI:

| Library | Version | Notes |
|---------|---------|-------|
| `databricks-agents` | `>=1.2.0` | Agent deployment framework |
| `databricks-langchain` | `>=0.11.0` | Databricks LangChain integration |
| `langgraph` | `==1.0.5` | LangGraph agent framework |
| `langchain-core` | `>=1.2.0` | LangChain core |
| `langchain-openai` | `==1.1.2` | OpenAI integration (for embeddings) |
| `mcp` | latest | Model Context Protocol |
| `databricks-mcp` | latest | Databricks MCP client |
| `pydantic` | `==2.12.5` | Data validation |
| `neo4j` | `==6.0.2` | Neo4j Python driver (optional) |
| `neo4j-graphrag` | `>=1.10.0` | Neo4j GraphRAG (optional) |

**To add a library:**
1. Click **Install new** on the Libraries tab
2. Select **PyPI** as the source
3. Enter the package name with version (e.g., `langgraph==1.0.5`)
4. Click **Install**

## Overview

This sample demonstrates how to connect Databricks to a Neo4j graph database through the Model Context Protocol (MCP). Instead of connecting directly to Neo4j, Databricks uses a Unity Catalog HTTP connection that acts as a secure proxy to an external MCP server.

Here's how it works:

1. **MCP Server Deployment**: The Neo4j MCP server is deployed to an external hosting platform, accessible via an HTTP endpoint with OAuth2 authentication.

2. **Unity Catalog HTTP Connection**: Databricks creates an HTTP connection in Unity Catalog that stores the endpoint URL and OAuth2 M2M credentials (client ID, client secret, token endpoint). Databricks automatically handles token exchange and refresh.

3. **Secure Proxy**: When notebooks or SQL queries call the MCP tools, Databricks routes requests through its internal proxy (`/api/2.0/mcp/external/{connection_name}`). This proxy handles OAuth2 authentication and forwards requests to the MCP server.

4. **Tool Execution**: The MCP server parses JSON-RPC requests, executes Cypher queries against Neo4j, and returns results.

This architecture provides several benefits:
- **Centralized credential management** via Databricks secrets
- **Automatic token refresh** — Databricks handles OAuth2 token lifecycle
- **Governance and auditing** through Unity Catalog
- **Network isolation** — the MCP server can be locked down to only accept requests from authorized sources
- **Consistent interface** — notebooks and agents use the same MCP protocol

## Why External Hosting?

The official Neo4j MCP server ([github.com/neo4j/mcp](https://github.com/neo4j/mcp)) is **written in Go** and distributed as a **compiled binary or Docker container**. This creates an incompatibility with Databricks Apps, which only supports Python and Node.js runtimes.

This external hosting pattern is **Databricks' recommended approach** for MCP servers that cannot run natively in Databricks Apps. By deploying the MCP server to an external container service, you get:

1. **Full compatibility** — Run any MCP server regardless of language or runtime
2. **Managed infrastructure** — The hosting platform handles scaling, security, and availability
3. **Secure integration** — Unity Catalog HTTP connections provide governance
4. **Automatic auth** — Databricks manages OAuth2 token lifecycle

This pattern applies to any MCP server built with Go, Rust, C++, or other compiled languages, not just Neo4j.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DATABRICKS WORKSPACE                                  │
│                                                                                          │
│  ┌──────────────────┐      ┌─────────────────────────────────────────────────────────┐  │
│  │                  │      │                   UNITY CATALOG                          │  │
│  │   Notebooks /    │      │  ┌─────────────────┐    ┌────────────────────────────┐  │  │
│  │   SQL Queries    │─────>│  │  HTTP Connection │    │  Secrets Scope             │  │  │
│  │                  │      │  │  (neo4j_agentcore│<───│  - gateway_host            │  │  │
│  │  http_request()  │      │  │   _mcp)          │    │  - client_id               │  │  │
│  │  or LangGraph    │      │  │                  │    │  - client_secret           │  │  │
│  │                  │      │  │  Is MCP: Y       │    │  - token_endpoint          │  │  │
│  │                  │      │  │  OAuth2 M2M      │    │  - oauth_scope             │  │  │
│  └──────────────────┘      │  └────────┬────────┘    └────────────────────────────┘  │  │
│                            └───────────┼──────────────────────────────────────────────┘  │
│                                        │                                                 │
│  ┌─────────────────────────────────────┼─────────────────────────────────────────────┐  │
│  │                    DATABRICKS HTTP PROXY                                           │  │
│  │                    /api/2.0/mcp/external/{connection_name}                         │  │
│  │                                                                                    │  │
│  │    OAuth2 Token Exchange ──>  Forwards JSON-RPC  ──>  Returns MCP Response        │  │
│  │    (automatic refresh)                                                             │  │
│  └─────────────────────────────────────┬─────────────────────────────────────────────┘  │
│                                        │                                                 │
└────────────────────────────────────────┼─────────────────────────────────────────────────┘
                                         │
                                         │ HTTPS (OAuth2 JWT Bearer Token)
                                         │ JSON-RPC 2.0 over HTTP
                                         v
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL MCP SERVER                                         │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           NEO4J MCP SERVER                                         │  │
│  │                                                                                    │  │
│  │   Tools:                                                                           │  │
│  │   - get-schema: Returns node labels, relationships                                │  │
│  │   - read-cypher: Executes read-only Cypher queries                                │  │
│  │                                                                                    │  │
│  │   Config: NEO4J_READ_ONLY=true (write-cypher disabled)                            │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                                 │
└────────────────────────────────────────┼─────────────────────────────────────────────────┘
                                         │
                                         │ Bolt Protocol (neo4j+s://)
                                         v
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              NEO4J AURA                                                  │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           GRAPH DATABASE                                           │  │
│  │                                                                                    │  │
│  │   (Nodes)──[:RELATIONSHIPS]──>(Nodes)                                             │  │
│  │                                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
1. Notebook calls http_request() or agent invokes MCP tool
                    │
                    v
2. Unity Catalog resolves connection settings (OAuth2 M2M credentials)
                    │
                    v
3. Databricks proxy exchanges credentials for JWT, forwards to MCP server
                    │
                    v
4. MCP server parses JSON-RPC, executes Cypher against Neo4j
                    │
                    v
5. Results returned through proxy to notebook
```

## Files

| File | Description |
|------|-------------|
| [neo4j-mcp-http-connection.ipynb](./neo4j-mcp-http-connection.ipynb) | Setup and test an HTTP connection to query Neo4j via MCP |
| [neo4j_mcp_agent.py](./neo4j_mcp_agent.py) | LangGraph agent that connects to Neo4j via external MCP HTTP connection |
| [neo4j-mcp-agent-deploy.ipynb](./neo4j-mcp-agent-deploy.ipynb) | Test, evaluate, and deploy the Neo4j MCP agent |

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `get-schema` | Retrieve database schema |
| `read-cypher` | Execute read-only Cypher queries |

Note: Tool names may be prefixed by a gateway if your MCP server uses one (e.g., `neo4j-mcp-server-target___get-schema`).

## Example Usage

After completing the Quick Start, you can query Neo4j from any notebook:

```python
# Using the helper function from the HTTP connection notebook
result = query_neo4j("MATCH (n:Person) RETURN n.name LIMIT 10")

# Or directly with SQL
spark.sql("""
    SELECT http_request(
      conn => 'neo4j_agentcore_mcp',
      method => 'POST',
      path => '',
      headers => map('Content-Type', 'application/json'),
      json => '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get-schema","arguments":{}},"id":1}'
    )
""")
```

## Agent Configuration

Edit `neo4j_mcp_agent.py` to customize:

| Setting | Description | Default |
|---------|-------------|---------|
| `LLM_ENDPOINT_NAME` | Databricks LLM endpoint | `databricks-claude-3-7-sonnet` |
| `CONNECTION_NAME` | HTTP connection name | `neo4j_agentcore_mcp` |
| `SECRET_SCOPE` | Secrets scope name | `mcp-neo4j-secrets` |
| `system_prompt` | Agent instructions | Neo4j query assistant |

## Security

This integration provides **read-only access** to Neo4j. The MCP server is deployed with `NEO4J_READ_ONLY=true`, which disables the `write-cypher` tool at the server level.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Secret not found | Create the secrets scope and store OAuth2 credentials (see Step 2) |
| Connection already exists | Drop it with `DROP CONNECTION IF EXISTS neo4j_agentcore_mcp` |
| HTTP timeout | Verify MCP server is running and accessible |
| 401 Unauthorized | Verify OAuth2 credentials are correct and re-store secrets |
| Tool not found | Check the tool name; it may be prefixed by the gateway |

## Related Documentation

- [Neo4j MCP Server](https://github.com/neo4j/mcp)
- [Databricks HTTP Connections](https://docs.databricks.com/aws/en/query-federation/http)
- [Databricks External MCP](https://docs.databricks.com/aws/en/generative-ai/mcp/external-mcp)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
