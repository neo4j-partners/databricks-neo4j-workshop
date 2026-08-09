# Optional: Compound AI Agent over Genie and Neo4j MCP

> **This section is optional.** It requires a hosted Neo4j MCP server and the Unity Catalog connection that fronts it, both of which are outside the scope of the workshop. The instructor demos it.
>
> **Why it is here.** It takes the Genie agent you built in the lab and makes it one half of a compound AI agent. A supervisor sits above it and a second agent queries Neo4j over MCP, so one question box reaches both the Lakehouse and the graph. Agent Bricks Multi-Agent Supervisor gets there through configuration alone, with no code. A Unity Catalog HTTP connection using OAuth2 M2M against a hosted MCP server is what governed agent access to Neo4j looks like in production.
>
> **[Lab 5](../Lab_5_LangGraph_Agent)** builds the same routing in code, against your own graph, and it is where the lab continues.
>
> **Instructors:** everything from Prerequisites down is the procedure for building the demo.

The supervisor routes questions to either the **Genie Agent** for sensor analytics or the **Neo4j MCP agent** for graph relationships. Natural language queries then span both data sources.

**Demo runtime:** about 10 minutes on screen. Build it ahead of class.

---

## Prerequisites

The instructor running the demo needs:
- A Genie Agent in the demo workspace, built as in [`04_genie_agent.ipynb`](./04_genie_agent.ipynb). The
  current one is `aircraft-genie`, agent id `01f1661b55731a0293c3f84ac9c5ba52`
- Access to the Unity Catalog schema `databricks-neo4j-workshop.aircraft`, meaning tables and volume
- The `neo4j_agentcore_mcp` Unity Catalog connection, created ahead of time per [`MCP-MANUAL-SETUP.md`](../workshop-setup/MCP-MANUAL-SETUP.md)

> **The graph behind the demo.** The MCP server points at the instructor's demo Aura instance, loaded before class with `workshop-setup/populate_aircraft_db`. It holds the complete dataset: the full fleet with all systems, components, sensors, maintenance events, flights, and delays. Nobody in the room connects to it or needs credentials for it.

---

## Step 1: Verify Neo4j MCP Connection

Confirm the connection is present and working in the demo workspace before the session starts.

### 1.1 Check Unity Catalog Connections

1. In the left navigation pane, click **Catalog**
2. Click **External connections**, or navigate to the **Connections** tab
3. Locate the Neo4j MCP connection named `neo4j_agentcore_mcp`
4. Verify the connection status shows as configured

### 1.2 Verify MCP Tools Are Available

The Neo4j MCP server provides these tools:
- `get_neo4j_schema`: Retrieves the Neo4j graph schema, meaning labels, relationships, and properties
- `read_neo4j_cypher`: Executes read-only Cypher queries

The AgentCore Gateway prefixes both names, so in the tool list they appear as
`neo4j-mcp-server-target___get_neo4j_schema` and `neo4j-mcp-server-target___read_neo4j_cypher`.

Test these in AI Playground before creating the supervisor:
1. Navigate to **Playground** in the left navigation
2. Select **GPT OSS 120B**
3. Click **Add your own tool** > **+ Add tool** > **MCP Servers** > **External MCP Servers** > **neo4j_agentcore_mcp**
4. Ask:

```
What is the schema of the database?
Which aircraft had critical maintenance events?
```

---

## Step 2: Create the Multi-Agent Supervisor

### 2.1 Navigate to Agent Bricks

1. In the left navigation pane, click **Agents**
2. Find the **Multi-Agent Supervisor** tile
3. Click **Build**

### 2.2 Configure Basic Settings

1. **Name:** `Aircraft Intelligence Hub [YOUR_INITIALS]`
   - Example: `Aircraft Intelligence Hub RK`
2. **Description:**
   ```
   Intelligent coordinator for aircraft analytics combining sensor telemetry
   data from Unity Catalog with knowledge graph relationships from Neo4j.
   ```

---

## Step 3: Add the Neo4j Graph Agent

### 3.1 Add and Configure the External MCP Server

1. Under **Tools and sub-agents** in the left side pane, click **External MCP server**
2. From the **Unity Catalog connection** dropdown, select `neo4j_agentcore_mcp`
3. The **Agent Name** `mcp-neo4j-agentcore-mcp` will auto-populate

![MCP Connection Configuration](../site/modules/ROOT/images/lab4-mcp-connection.png)

4. In the **Describe the content** field, paste the following. The supervisor uses this description to decide which agent handles each question, so detail matters:

```
Queries the Neo4j knowledge graph to explore aircraft relationships, topology, and operational data.

BEST FOR:
- Aircraft topology: "What systems does aircraft AC1001 have?"
- Component hierarchy: "Show all components in the hydraulics system"
- Maintenance events: "Which aircraft had critical maintenance events?"
- Flight operations: "Find flights delayed due to maintenance"
- Relationship patterns: "Which airports does ExampleAir fly to?"
- Graph traversals: "Show the path from aircraft to sensor"

DATA AVAILABLE (loaded from /Volumes/databricks-neo4j-workshop/aircraft/raw_data/):
- Aircraft: Fleet inventory with tail numbers, models, operators
- Systems: Engines, Avionics, Hydraulics per aircraft
- Components: Turbines, Compressors, Pumps, etc.
- Sensors: Monitoring equipment metadata
- MaintenanceEvents: Faults, severity, corrective actions
- Flights: Operations with departure/arrival
- Delays: Delay causes and durations
- Airports: Route network locations

RELATIONSHIP TYPES:
- HAS_SYSTEM: Aircraft -> System
- HAS_COMPONENT: System -> Component
- HAS_SENSOR: System -> Sensor
- HAS_EVENT: Component -> MaintenanceEvent
- OPERATES_FLIGHT: Aircraft -> Flight
- DEPARTS_FROM / ARRIVES_AT: Flight -> Airport
- HAS_DELAY: Flight -> Delay

DO NOT USE FOR:
- Time-series sensor readings (use sensor_data_agent instead)
- Statistical aggregations over readings
- Trend analysis or rolling averages
```

---

## Step 4: Add the Genie Agent

### 4.1 Add Genie Agent

1. Under **Tools and sub-agents** in the left side pane, click **Genie Agent**
2. From the dropdown that appears, select the demo workspace's own Genie Agent,
   `aircraft-genie`, agent id `01f1661b55731a0293c3f84ac9c5ba52`

> **Pick it by id, not by name.** The lab has everyone title their agent
> `Aircraft Sensor Analyst <THEIR INITIALS>`, so there is no one name to look up
> and nothing named `Aircraft Sensor Analyst` in the demo workspace. The id is in
> the agent's URL, after `/genie/rooms/`. Substitute your own id if you built the
> demo agent yourself rather than reusing `aircraft-genie`.

### 4.2 Configure the Genie Subagent

1. **Agent Name:** `sensor_data_agent`
   - Edit the auto-populated name if needed
2. **Description:**

```
Analyzes aircraft sensor telemetry data using SQL queries over Unity Catalog tables.

DATA LOCATION:
- Catalog: databricks-neo4j-workshop
- Schema: aircraft
- Tables: sensor_readings, sensors, systems, aircraft

BEST FOR:
- Time-series analytics: "What is the average EGT over the last 30 days?"
- Statistical analysis: "Show sensors above the 95th percentile"
- Trend detection: "Show daily vibration trends for Engine 1"
- Fleet comparisons: "Compare fuel flow between Boeing and Airbus"
- Anomaly detection: "Find B737-800 EGT readings above 950 degrees"
- Aggregations: "What was the maximum N1 speed recorded?"

DATA AVAILABLE:
- sensor_readings: Telemetry every 4 hours over 90 days
- sensors: Sensor metadata (type, unit, system)
- systems: Aircraft system information
- aircraft: Fleet metadata (model, operator)

SENSOR TYPES:
- EGT: Exhaust Gas Temperature (unit column value °C). Per model: A320-200 620-680, A220-300 855-890, E190 870-900, B737-800 900-950, A321neo 980-1040
- Vibration: Engine vibration (0.05-0.50, unit column value ips)
- N1Speed: Fan speed (85-100, unit column value % RPM)
- FuelFlow: Fuel consumption (unit column value kg/s). Per model: E190 1.00-1.20, A220-300 1.15-1.35, B737-800 1.20-1.50, A320-200 1.20-1.95, A321neo 1.50-2.00

DO NOT USE FOR:
- Relationship queries (use mcp-neo4j-agentcore-mcp)
- Maintenance event details
- Flight operations or delays
- Component-level fault tracking
```

---

## Step 5: Create the Agent

Click **Create Agent** to deploy the supervisor.

> **Note:** Deployment may take several minutes to complete. The status will update when ready.

---

## Step 6: Configure Supervisor Instructions

### 6.1 Set Supervisor Instructions

1. Scroll to the bottom of the agent configuration page
2. Expand the **Optional** section
3. In the **Instructions** field, enter the following:

```
# Aircraft Intelligence Hub - Routing Instructions

You are an intelligent coordinator for aircraft analytics. Your role is to understand user questions and route them to the appropriate specialized agent.

## Available Agents

### sensor_data_agent (Genie Agent - Unity Catalog SQL)
Use for questions about:
- Sensor readings and telemetry data
- Time-series analytics (averages, trends, rolling windows)
- Statistical analysis (percentiles, standard deviation)
- Fleet-wide comparisons of sensor metrics
- Anomaly detection based on readings
- Questions containing: EGT, vibration, N1, fuel flow, temperature, readings, averages, trends

### mcp-neo4j-agentcore-mcp (Neo4j Knowledge Graph - Cypher)
Use for questions about:
- Aircraft structure and topology
- Component relationships and hierarchy
- Maintenance events and fault history
- Flight operations, routes, delays
- "Which", "what systems", "connected to", "related to" questions
- Questions about maintenance, flights, delays, airports

## Routing Rules

1. **Sensor values/readings** -> sensor_data_agent
   - "What is the EGT for..."
   - "Show vibration readings..."
   - "Average fuel flow..."

2. **Relationships/structure** -> mcp-neo4j-agentcore-mcp
   - "What systems does aircraft X have?"
   - "Which components..."
   - "Show maintenance events..."

3. **Flights/operations** -> mcp-neo4j-agentcore-mcp
   - "Which flights were delayed?"
   - "What airports does..."
   - "Show flight routes..."

4. **Maintenance history** -> mcp-neo4j-agentcore-mcp
   - "What maintenance events..."
   - "Which components had faults?"
   - "Critical maintenance..."

5. **Statistical aggregations on readings** -> sensor_data_agent
   - "Average", "maximum", "minimum", "percentile"
   - "Trend", "over time", "daily", "monthly"
   - "Compare", "between", "by model"

## Complex Queries (Multi-Agent)

For questions that need BOTH sources, process sequentially:

1. **"Find aircraft with high vibration AND recent maintenance"**
   - First: sensor_data_agent -> Get aircraft with high vibration
   - Then: mcp-neo4j-agentcore-mcp -> Get maintenance events for those aircraft

2. **"Which engines have abnormal EGT and what components were serviced?"**
   - First: sensor_data_agent -> Find abnormal EGT readings
   - Then: mcp-neo4j-agentcore-mcp -> Find maintenance events for those engines

3. **"Compare sensor trends for aircraft that had delays"**
   - First: mcp-neo4j-agentcore-mcp -> Get aircraft with delays
   - Then: sensor_data_agent -> Get sensor trends for those aircraft

## Response Guidelines

1. For single-agent queries: Return the agent's response directly
2. For multi-agent queries: Synthesize a combined response that integrates both perspectives
3. Always cite which data source provided each piece of information
4. If a query cannot be answered by either agent, explain what data would be needed
```

### 6.2 Save Changes

Click **Update Agent** to save the instructions.

---

## Step 7: Test the Multi-Agent System

### 7.1 Start Testing

Once deployment completes:
1. Use the **Test your Agent** panel on the right side of the Build tab
2. Or click **Open in Playground** for expanded testing with AI Judge features

### 7.2 Test Single-Agent Routing

**Test 1: Sensor Analytics (should route to sensor_data_agent)**
```
What is the average EGT temperature across the fleet?
```
Verify: The query is routed to sensor_data_agent and returns a numerical average

**Test 2: Graph Relationships (should route to mcp-neo4j-agentcore-mcp)**
```
What systems does aircraft AC1001 have?
```
Verify: The query is routed to mcp-neo4j-agentcore-mcp and returns engine, avionics, hydraulics systems

**Test 3: Maintenance Events (should route to mcp-neo4j-agentcore-mcp)**
```
Show me all critical maintenance events in the last month
```
Verify: Returns maintenance events with severity=CRITICAL

**Test 4: Fleet Comparison (should route to sensor_data_agent)**
```
Compare average vibration readings between Boeing and Airbus aircraft
```
Verify: Returns grouped statistics by manufacturer

### 7.3 Test Multi-Agent Queries

**Test 5: Combined Query**
```
Find B737-800 aircraft with EGT readings above 950 degrees and show their maintenance history
```
Expected behavior:
1. Supervisor routes to sensor_data_agent for high EGT aircraft
2. Supervisor routes to mcp-neo4j-agentcore-mcp for maintenance history
3. Response synthesizes both data sources

**Test 6: Another Combined Query**
```
Which engines had above-average vibration, and what components were recently serviced on those engines?
```
Expected behavior:
1. Get high-vibration engines from sensor_data_agent
2. Get maintenance events from mcp-neo4j-agentcore-mcp
3. Combine and present results

> **What a weak answer looks like.** It answers only half the question, or it answers the second half about the whole fleet rather than about the aircraft the first half returned. Watch for that, because these two tests are the point of the whole demo. Neither subagent can answer them alone.

---

## Step 8: Improve Through Feedback

### 8.1 Add Example Questions

1. Navigate to the **Examples** tab
2. Click **+ Add** to introduce test questions
3. Enter questions that represent common user queries

### 8.2 Share with Subject Matter Experts

1. Share the configuration page link with domain experts
2. Grant experts `CAN_MANAGE` permission on the supervisor
3. Ensure experts have appropriate access to each subagent

### 8.3 Add Guidelines

1. Select each example question
2. Add **Guidelines** labels that refine routing behavior
3. Test again to validate improvements
4. Click **Update Agent** to save changes

---

## Step 9: Optional - Query the Endpoint Programmatically

1. Click **See Agent status** or **Open in Playground**
2. Select **Get code** to retrieve API examples
3. Choose between **Curl API** or **Python API**

Example Python usage:
```python
import requests

# Get your endpoint URL from the agent status page
ENDPOINT_URL = "https://<workspace>.databricks.com/serving-endpoints/<agent-name>/invocations"

headers = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
    "Content-Type": "application/json"
}

response = requests.post(
    ENDPOINT_URL,
    headers=headers,
    json={"messages": [{"role": "user", "content": "What systems does AC1001 have?"}]}
)
print(response.json())
```

---

## Summary

The demo shows a multi-agent system that combines two purpose-built data platforms:

- **Genie plus Lakehouse for time-series data.** SQL analytics over sensor telemetry readings, right for aggregations, trends, and statistics.
- **Neo4j for relationship data.** Graph traversals across aircraft topology, maintenance events, flights, and delays, right for relationship queries and multi-hop navigation.
- **Intelligent routing.** The supervisor directs each question to the right data source on its own.
- **Cross-source synthesis.** Questions that span both systems get answered by querying each in turn and combining the results.
- **Natural language access.** Users need neither SQL nor Cypher.

---

## Troubleshooting

### "Agent not responding"
- Check MCP connection status in **Catalog** > **Connections**
- Verify Neo4j instance is running
- Test Genie Agent independently in AI Playground
- Ensure user has `USE CONNECTION` permission on the MCP connection

### "Wrong agent selected"
- Review and enhance agent descriptions with more specific keywords
- Add explicit routing patterns in supervisor instructions
- Use the Examples tab to add labeled training questions

### "Cypher query failed"
- Check that the demo Aura instance was loaded correctly with `workshop-setup/populate_aircraft_db`
- Verify node labels and relationship types match documentation
- Review Cypher syntax for errors
- Test queries directly in Neo4j Aura console first

### "SQL query failed"
- Verify table names in Unity Catalog: `databricks-neo4j-workshop.aircraft`
- Check column names match documentation
- Ensure Genie Agent has access to all required tables
- Test queries directly in SQL Editor first

### "Permission denied"
- For Genie Agent: User needs access to the agent AND underlying data tables
- For MCP server: User needs `USE CONNECTION` permission on the Unity Catalog connection
- For supervisor: User needs `CAN QUERY` permission on the agent endpoint

---

## Sample Queries Reference

### Sensor Analytics (sensor_data_agent)
```
What is the average EGT temperature for aircraft N10000?
Show daily vibration trends for Engine 1 in August 2024
Find all sensors with readings above the 95th percentile
Compare fuel flow rates by aircraft model
What was the maximum N1 speed recorded?
```

### Graph Queries (mcp-neo4j-agentcore-mcp)
```
What systems does aircraft AC1001 have?
Show all components in the hydraulics system
Which aircraft had critical maintenance events?
Find flights that were delayed due to maintenance
What airports are in the route network?
```

### Combined Queries (both agents)
```
Find aircraft with high EGT and show their recent maintenance
Which engines have abnormal vibration and what was serviced?
Compare sensor trends for aircraft that had delays vs. those that didn't
Show maintenance events for aircraft with the lowest fuel efficiency
```

---

## Next Steps

**[Lab 5](../Lab_5_LangGraph_Agent)** builds this same routing in code, against your own graph and with no MCP server needed.

Extensions worth showing or mentioning during the demo:

1. **Add Documentation Agent**: Integrate semantic search as a third agent for maintenance procedures

2. **Create Unity Catalog Functions**: Build custom Python functions as additional tools

3. **Production Deployment**: Deploy as a REST API for integration with other systems

4. **Add Guardrails**: Configure output validation and safety filters

5. **Enable Feedback**: Set up user feedback collection for continuous improvement

---

## References

- [Multi-Agent Supervisor Documentation](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor)
- [External MCP Servers](https://docs.databricks.com/aws/en/generative-ai/mcp/external-mcp)
- [Agent Bricks Overview](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/)
- [Unity Catalog Connections](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
