# Optional: Compound AI Agent over the Genie Agent and Neo4j MCP

> **This section is optional.** It requires a hosted Neo4j MCP server and the Unity Catalog connection that fronts it, both of which are outside the scope of the workshop. The instructor demos it.
>
> **Why it is here.** It takes the Genie Agent you built in the lab and makes it one half of a compound AI agent. A supervisor sits above it and a second agent queries Neo4j over MCP, so one question box reaches both the Lakehouse and the graph. Agent Bricks Supervisor Agent gets there through configuration alone, with no code. A Unity Catalog HTTP connection using OAuth2 M2M against a hosted MCP server is what governed agent access to Neo4j looks like in production.
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

## Step 2: Create the Supervisor Agent

### 2.1 Create the agent

1. In the left navigation pane, click **Agents**
2. Click **Create Agent**
3. Select **Supervisor Agent**

The agent is created immediately and opens its configuration page. Everything that
follows happens on that one page: subagents in the left side pane, **Instructions**
and **Description** below them, and a chat pane on the right for testing. There is no
separate build-then-deploy step.

### 2.2 Configure basic settings

1. **Name:** `Aircraft Intelligence Hub [YOUR_INITIALS]`
   - Example: `Aircraft Intelligence Hub RK`
2. **Description:** this is shown to users and used for search.
   ```
   Intelligent coordinator for aircraft analytics combining sensor telemetry
   data from Unity Catalog with knowledge graph relationships from Neo4j.
   ```

> **Code execution comes for free.** Every supervisor includes a sandboxed code
> execution tool by default, so it can run Python, SQL or shell to compute over what
> the subagents return. Nothing to enable, and nothing to add under **Tools and
> sub-agents**. The sandbox has no internet access and no data access of its own.

---

## Step 3: Add the Neo4j Graph Agent

### 3.1 Add and configure the external MCP server

1. Under **Tools and sub-agents** in the left side pane, click **External MCP server**.
   The search bar at the top of the pane finds it too.
2. From the dropdown that appears, select the `neo4j_agentcore_mcp` Unity Catalog connection
3. The agent name `mcp-neo4j-agentcore-mcp` auto-populates
4. Click the subagent tile to open its **Description**, and paste the block below. The
   supervisor reads this to decide which subagent handles each question, so detail matters:

```
Queries the Neo4j knowledge graph to explore aircraft relationships, topology, and operational data.

BEST FOR:
- Aircraft topology: "What systems does aircraft AC1001 have?"
- Component hierarchy: "Show all components in the hydraulics system"
- Maintenance events: "Which aircraft had critical maintenance events?"
- Flight operations: "Find flights delayed due to maintenance"
- Relationship patterns: "Which airports does ExampleAir fly to?"
- Graph traversals: "Show the path from aircraft to sensor"

NODE LABELS:
- Aircraft: Fleet inventory with tail numbers, models, operators
- System: Engines, Avionics, Hydraulics per aircraft
- Component: Turbines, Compressors, Pumps, etc.
- Sensor: Monitoring equipment metadata
- MaintenanceEvent: Faults, severity, corrective actions
- Removal: Component removals, with the reason and the replacement part
- OperatingLimit: Per-model manual limits for each sensor type
- Flight: Operations with departure/arrival
- Delay: Delay causes and durations
- Airport: Route network locations

RELATIONSHIP TYPES:
- HAS_SYSTEM: Aircraft -> System
- HAS_COMPONENT: System -> Component
- HAS_SENSOR: System -> Sensor
- HAS_LIMIT: Sensor -> OperatingLimit
- HAS_EVENT: Component -> MaintenanceEvent
- AFFECTS_SYSTEM: MaintenanceEvent -> System
- AFFECTS_AIRCRAFT: MaintenanceEvent -> Aircraft
- HAS_REMOVAL: Aircraft -> Removal
- REMOVED_COMPONENT: Removal -> Component
- OPERATES_FLIGHT: Aircraft -> Flight
- DEPARTS_FROM / ARRIVES_AT: Flight -> Airport
- HAS_DELAY: Flight -> Delay

For "what was serviced" or "what was replaced", use Removal and REMOVED_COMPONENT, not MaintenanceEvent.

DO NOT USE FOR:
- Time-series sensor readings (use sensor_data_agent instead)
- Statistical aggregations over readings
- Trend analysis or rolling averages
```

---

## Step 4: Add the Genie Agent

### 4.1 Add the Genie Agent

1. Under **Tools and sub-agents** in the left side pane, click **Genie Agent**
2. From the dropdown that appears, select the demo workspace's own Genie Agent,
   `aircraft-genie`, agent id `01f1661b55731a0293c3f84ac9c5ba52`

> **Pick it by id, not by name.** The lab has everyone title their agent
> `Aircraft Sensor Analyst <THEIR INITIALS>`, so there is no one name to look up
> and nothing named `Aircraft Sensor Analyst` in the demo workspace. The id is in
> the agent's URL, after `/genie/rooms/`. Substitute your own id if you built the
> demo agent yourself rather than reusing `aircraft-genie`.

### 4.2 Configure the Genie Agent subagent

1. **Agent Name:** `sensor_data_agent`
   - Edit the auto-populated name if needed
2. Click the subagent tile to open its **Description**, and paste:

```
Analyzes aircraft sensor telemetry data using SQL queries over Unity Catalog tables.

DATA LOCATION:
- Catalog: databricks-neo4j-workshop
- Schema: aircraft
- Tables: sensor_readings, sensors, systems, aircraft

BEST FOR:
- Time-series analytics: "What is the average EGT in September 2024?"
- Statistical analysis: "Show sensors above the 95th percentile"
- Trend detection: "Show daily vibration trends for Engine 1"
- Fleet comparisons: "Compare fuel flow between Boeing and Airbus"
- Anomaly detection: "Find B737-800 EGT readings above 950 degrees"
- Aggregations: "What was the maximum N1 speed recorded?"

DATA AVAILABLE:
- sensor_readings: Telemetry every 4 hours, 2024-07-01 through 2024-09-28
- sensors: Sensor metadata (type, unit, system)
- systems: Aircraft system information
- aircraft: Fleet metadata (model, operator)

The data ends on 2024-09-28. Read "recent" and "the last month" as September 2024, and never filter on CURRENT_DATE.

SENSOR TYPES:
- EGT: Exhaust Gas Temperature (unit column value C, no degree sign). Per model: A320-200 620-680, A220-300 855-890, E190 870-900, B737-800 900-950, A321neo 980-1040
- Vibration: Engine vibration (unit column value ips). Per-model maximum, no minimum: A320-200 2.0, A220-300 2.5, A321neo 2.5, B737-800 3.0, E190 3.0
- N1Speed: Fan speed (unit column value % RPM). Per-model maximum, no minimum: A321neo 97, A220-300 100, E190 100, A320-200 104, B737-800 104
- FuelFlow: Fuel consumption (unit column value kg/s). Per model: E190 1.00-1.20, A220-300 1.15-1.35, B737-800 1.20-1.50, A320-200 1.20-1.95, A321neo 1.50-2.00

DO NOT USE FOR:
- Relationship queries (use mcp-neo4j-agentcore-mcp)
- Maintenance event details
- Flight operations or delays
- Component-level fault tracking
```

---

## Step 5: Set the Supervisor Instructions

The subagent descriptions above tell the supervisor what each one is good for. The
**Instructions** field tells it how to behave: the routing policy, the multi-step
plans, and the rules for writing an answer.

In the left side panel, below **Tools and sub-agents**, paste this into **Instructions**:

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

---

## Step 6: Test the Supervisor

### 6.1 Start testing

Once the supervisor finishes initializing:
1. Chat with it in the pane on the right side of the configuration page
2. Or click **Open in Playground**. With AI assistive features enabled, Playground adds
   **AI Judge** and **Synthetic task generation**

### 6.2 Test single-agent routing

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
Show me all critical maintenance events in September 2024
```
Verify: Returns maintenance events with severity=CRITICAL. Say the month rather than "the last month": the data ends 2024-09-28, so a relative date returns nothing

**Test 4: Fleet Comparison (should route to sensor_data_agent)**
```
Compare average vibration readings between Boeing and Airbus aircraft
```
Verify: Returns grouped statistics by manufacturer

### 6.3 Test multi-agent queries

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
Which engines had above-average vibration, and what components were removed from those engines in September 2024?
```
Expected behavior:
1. Get high-vibration engines from sensor_data_agent
2. Get maintenance events from mcp-neo4j-agentcore-mcp
3. Combine and present results

> **What a weak answer looks like.** It answers only half the question, or it answers the second half about the whole fleet rather than about the aircraft the first half returned. Watch for that, because these two tests are the point of the whole demo. Neither subagent can answer them alone.

---

## Step 7: Improve Through Feedback

Supervisor Agent retrains itself on labeled feedback, so routing mistakes get corrected
without editing the Instructions block.

### 7.1 Add example questions

1. Open the **Examples** tab
2. Click **+ Add**
3. Type the question into the **Add a question** modal, then click **Add**
4. Repeat for each question worth evaluating. The kebab menu on a question deletes it

### 7.2 Share with subject matter experts

1. Share a link to the agent's configuration page with your domain experts
2. In the upper right corner, click the kebab menu, then **Manage permissions**, and
   grant the experts **Can Manage**
3. Give them access to each subagent as well: the Genie Agent and its Unity Catalog
   objects, and `USE CONNECTION` on `neo4j_agentcore_mcp`

> **Partial access degrades quietly.** An expert with access to no subagent gets the
> conversation ended. An expert with access to some subagents gets steered away from
> the ones they cannot reach, rather than an error.

### 7.3 Add guidelines

1. Click an example question
2. Add **Guidelines** in the panel that appears. They apply as soon as they are saved
3. Test again, in the configuration page or in Playground

---

## Step 8: Optional - Query the Endpoint Programmatically

1. On the agent page, click **Endpoint** for the endpoint details
2. Or click **Open in playground**, then **Get code**
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

- **Genie Agent plus Lakehouse for time-series data.** SQL analytics over sensor telemetry readings, right for aggregations, trends, and statistics.
- **Neo4j for relationship data.** Graph traversals across aircraft topology, maintenance events, flights, and delays, right for relationship queries and multi-hop navigation.
- **Intelligent routing.** The supervisor directs each question to the right data source on its own.
- **Cross-source synthesis.** Questions that span both systems get answered by querying each in turn and combining the results.
- **Natural language access.** Users need neither SQL nor Cypher.

---

## Troubleshooting

### "Agent not responding"
- Check MCP connection status in **Catalog** > **External connections**
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
- For supervisor: User needs **Can Query**, granted from the kebab menu on the **Agents** page

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
Find aircraft with high EGT and show their September 2024 maintenance
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

- [Supervisor Agent](https://docs.databricks.com/aws/en/agents/agent-bricks/multi-agent-supervisor)
- [Connect agents to third-party tools with MCP Services](https://docs.databricks.com/aws/en/agents/mcp-tools/mcp-services)
- [Agent Bricks Overview](https://docs.databricks.com/aws/en/agents/agent-bricks/)
- [Unity Catalog Connections](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
