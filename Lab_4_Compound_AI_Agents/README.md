# Lab 4 - Compound AI Agents for Aircraft Analytics

In this lab, you'll build a compound AI agent system using Databricks Agent Bricks that combines a **Genie space** for sensor time-series analytics with **Neo4j MCP** for graph relationship queries. The Supervisor Agent routes each question to the right system and, for complex questions spanning both, queries each sequentially and synthesizes a combined answer.

> **Part A is required. Part B is optional and advanced.**
>
> **Part A** builds the Genie space over shared Lakehouse tables in Unity Catalog. Lab 5 uses that Genie space as one of its three tools, so Part A is on the required path.
>
> **Part B** builds the no-code supervisor. Its Neo4j MCP agent queries the shared **Reference Aura Instance**, an administrator-managed graph that is always fully populated, rather than the Aura instance you loaded in Lab 2. You do not need data in your personal Aura instance for Part B, and you do not need Part B for Lab 5 or Lab 6.

## Multi-Agent Architecture

![Lab Architecture Overview](../images/lab-architecture-overview.png)

## Prerequisites

Before starting, make sure you have:
- Running in a **Databricks workspace** with Agent Bricks access
- Neo4j MCP server connection configured in Unity Catalog

**Recommended:** Complete **Lab 2** before starting this lab. Lab 4 runs against shared workshop infrastructure rather than your personal Aura instance, but Lab 2 gives you familiarity with the data model the agents here query: the aircraft topology, sensor relationships, flights, and maintenance events. Labs 5 and 6 do require your own loaded instance.

## Lab Overview

This lab is documentation-driven and focuses on **configuration over code**. You'll use the Databricks UI to create intelligent agents that automatically route questions to the right data source.

### Part A: Genie space for Sensor Analytics (~30 min)

Create an AI/BI Genie space that enables natural language queries over sensor telemetry:
- Connect data sources: `sensor_readings`, `sensors`, `systems`, `aircraft`
- Add sample questions and domain-specific instructions (sensor types, normal ranges, fleet info)
- Test natural language to SQL queries for time-series aggregations and anomaly detection

### Part B: Supervisor Agent (~45 min, optional)

Build a supervisor agent that coordinates two specialized sub-agents. This runs against the Reference Aura Instance, not your own:
- Add the **Neo4j MCP subagent** for graph relationship queries (topology, maintenance, flights)
- Add the **Genie space subagent** for time-series sensor analytics (readings, trends, fleet comparisons)
- Configure routing rules so the Supervisor Agent directs questions to the right subagent
- Test single-agent routing and combined multi-agent queries
- Deploy as a serving endpoint for programmatic access

## Getting Started

1. **[Part A](PART_A.md)** (~30 min, required): Create and configure the Genie space for sensor analytics
2. **[Part B](PART_B.md)** (~45 min, optional): Build the no-code Supervisor Agent with Neo4j MCP integration

After Part A, continue to **[Lab 5](../Lab_5_LangGraph_Agent)**, which routes across this Genie space, Cypher over your own Aura instance, and the GraphRAG retrievers you built in Lab 3.

## Files

| File | Description |
|------|-------------|
| `README.md` | This overview document |
| `PART_A.md` | Genie space configuration guide |
| `PART_B.md` | Supervisor Agent setup guide |

## Next Steps

Continue to **[Lab 5](../Lab_5_LangGraph_Agent)**, which builds a LangGraph supervisor over three tools: the Genie space from Part A, Cypher against your own Aura instance, and the GraphRAG retrievers from Lab 3. It ends with the agent deployed to Model Serving and authenticating as a service principal.

After the workshop you can:
- Create custom tools for specific maintenance workflows
- Integrate with external systems via additional MCP servers
- Add agent memory so the system remembers across sessions, which is **[Lab 6](../Lab_6_Agent_Memory)**
