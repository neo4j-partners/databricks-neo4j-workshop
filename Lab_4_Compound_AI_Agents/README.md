# Lab 4 - Compound AI Agents for Aircraft Analytics

In this lab, you'll build a compound AI agent system using Databricks Agent Bricks that combines a **Genie space** (for sensor time-series analytics) with **Neo4j MCP** (for graph relationship queries). The Supervisor Agent routes each question to the right system and, for complex questions spanning both, queries each sequentially and synthesizes a combined answer.

> **Infrastructure:** This lab uses **shared** workshop resources — the Genie space queries shared Lakehouse tables in Unity Catalog, and the Neo4j MCP agent queries the **Reference Aura Instance** (the fully populated graph). You do not need data in your personal Aura instance for this lab.

## Multi-Agent Architecture

![Lab Architecture Overview](../images/lab-architecture-overview.png)

## Prerequisites

Before starting, make sure you have:
- Running in a **Databricks workspace** with Agent Bricks access
- Neo4j MCP server connection configured in Unity Catalog

**Recommended:** Complete **Lab 2** (Databricks ETL) before starting this lab. Lab 4 uses shared workshop infrastructure (not your personal Aura instance), but completing Lab 2 gives you familiarity with the data model — the aircraft topology, sensor relationships, flights, and maintenance events — that the agents in this lab query.

## Lab Overview

This lab is documentation-driven and focuses on **configuration over code**. You'll use the Databricks UI to create intelligent agents that automatically route questions to the right data source.

### Part A: Genie space for Sensor Analytics (~30 min)

Create an AI/BI Genie space that enables natural language queries over sensor telemetry:
- Connect data sources: `sensor_readings`, `sensors`, `systems`, `aircraft`
- Add sample questions and domain-specific instructions (sensor types, normal ranges, fleet info)
- Test natural language to SQL queries for time-series aggregations and anomaly detection

### Part B: Supervisor Agent (~45 min)

Build a supervisor agent that coordinates two specialized sub-agents:
- Add the **Neo4j MCP subagent** for graph relationship queries (topology, maintenance, flights)
- Add the **Genie space subagent** for time-series sensor analytics (readings, trends, fleet comparisons)
- Configure routing rules so the Supervisor Agent directs questions to the right subagent
- Test single-agent routing and combined multi-agent queries
- Deploy as a serving endpoint for programmatic access

## Getting Started

1. **[Part A](PART_A.md)** (~30 min): Create and configure the Genie space for sensor analytics
2. **[Part B](PART_B.md)** (~45 min): Build the Supervisor Agent with Neo4j integration

## Files

| File | Description |
|------|-------------|
| `README.md` | This overview document |
| `PART_A.md` | Genie space configuration guide |
| `PART_B.md` | Supervisor Agent setup guide |

## Next Steps

After completing the workshop, you can:
- Add more subagents (e.g., documentation search from Lab 3)
- Create custom tools for specific maintenance workflows
- Deploy the agent as a production service
- Integrate with external systems via additional MCP servers
