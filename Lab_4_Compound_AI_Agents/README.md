# Lab 4 - Compound AI Agents for Aircraft Analytics

Lab 4 combines a **Genie space** for sensor time-series analytics with **Neo4j MCP** for graph relationship queries. A Supervisor Agent routes each question to the right system and, for complex questions spanning both, queries each sequentially and synthesizes a combined answer.

> **Part A is yours to build. Part B is an instructor demo.**
>
> **Part A** builds the Genie space over shared Lakehouse tables in Unity Catalog. Lab 5 uses that Genie space as one of its three tools, so Part A is on the participant path.
>
> **Part B** is the no-code supervisor, demonstrated by the instructor from the front of the room. It runs against the instructor's demo Aura instance and the instructor's MCP connection. You need no Aura instance, no MCP connection, and no OAuth credential to watch it. After Part A, continue to Lab 5.

## Multi-Agent Architecture

![Lab Architecture Overview](../images/lab-architecture-overview.png)

## Prerequisites

For Part A, make sure you have:
- A **Databricks workspace** with AI/BI Genie enabled and a serverless SQL warehouse you can select as the space's default. Agent Bricks is a Part B thing and Part A needs none of it

Part B needs nothing from you. The instructor supplies the demo workspace, the MCP connection, and the graph behind it.

**Recommended:** Complete **Lab 2** before starting this lab. Part A runs against shared Lakehouse tables rather than your personal Aura instance, but Lab 2 gives you familiarity with the data model: the aircraft topology, sensor relationships, flights, and maintenance events. Labs 5 and 6 do require your own loaded instance.

## Lab Overview

This lab is documentation-driven and focuses on **configuration over code**. You use the Databricks UI to create an agent that turns questions into SQL over the Lakehouse.

### Part A: Genie space for Sensor Analytics (~30 min, you build it)

Create an AI/BI Genie space that enables natural language queries over sensor telemetry:
- Connect data sources: `sensor_readings`, `sensors`, `systems`, `aircraft`
- Add sample questions and domain-specific instructions covering sensor types, normal ranges, and fleet info
- Test natural language to SQL queries for time-series aggregations and anomaly detection

### Part B: Supervisor Agent (instructor demo, watch only)

The instructor demonstrates a supervisor agent that coordinates two specialized sub-agents, running against the instructor's demo instance:
- The **Neo4j MCP subagent** for graph relationship queries covering topology, maintenance, and flights
- The **Genie space subagent** for time-series sensor analytics covering readings, trends, and fleet comparisons
- Routing rules that send each question to the right subagent
- Single-agent routing and combined multi-agent queries
- Deployment as a serving endpoint for programmatic access

The demo makes one point: the same routing architecture as Lab 5, built with no code and with centrally governed access to Neo4j through Unity Catalog.

## Getting Started

1. **[Part A](PART_A.md)** (~30 min): Create and configure the Genie space for sensor analytics
2. **[Part B](PART_B.md)**: Follow along while the instructor builds the no-code Supervisor Agent over Neo4j MCP

After Part A, continue to **[Lab 5](../Lab_5_LangGraph_Agent)**, which routes across this Genie space, Cypher over your own Aura instance, and the GraphRAG retrievers you built in Lab 3.

## Files

| File | Description |
|------|-------------|
| `README.md` | This overview document |
| `PART_A.md` | Genie space configuration guide |
| `PART_B.md` | Supervisor Agent instructor demo, including the build procedure |
| `04_genie_agent.ipynb` | The Part A notebook. Browses the four Lakehouse tables in the workspace, then walks the same Genie space build. This is the file `VOC_COURSE_NOTEBOOKS` ships to a participant's folder |

## Next Steps

Continue to **[Lab 5](../Lab_5_LangGraph_Agent)**, which builds a LangGraph supervisor over three tools: the Genie space from Part A, Cypher against your own Aura instance, and the GraphRAG retrievers from Lab 3. It ends with the agent deployed to Model Serving and authenticating as a service principal.

After the workshop you can:
- Create custom tools for specific maintenance workflows
- Integrate with external systems via additional MCP servers
- Add agent memory so the system remembers across sessions, which is **[Lab 6](../Lab_6_Agent_Memory)**
