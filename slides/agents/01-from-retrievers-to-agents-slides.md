---
marp: true
theme: default
paginate: true
---

<style>
section {
  --marp-auto-scaling-code: false;
}

li {
  opacity: 1 !important;
  animation: none !important;
  visibility: visible !important;
}

/* Disable all fragment animations */
.marp-fragment {
  opacity: 1 !important;
  visibility: visible !important;
}

ul > li,
ol > li {
  opacity: 1 !important;
}
</style>


# From Retrievers to Agents

---

## The Problem

You know three retrieval patterns:
- **Vector**: Semantic content search
- **Vector Cypher**: Content + relationships
- **Text2Cypher**: Precise facts

**But users don't know about retriever types.**

They just ask questions:
- "What causes turbine bearing wear?"
- "How many critical maintenance events are in the database?"
- "Which aircraft have engines with components that had recent faults?"

---

## The Solution: Agents

---

## What is an Agent?

In AI terms, an agent has **four components**:

| Component | What It Does |
|-----------|--------------|
| **Perception** | Receives input (questions, history, tool descriptions) |
| **Reasoning** | Analyzes the question and decides what to do |
| **Action** | Executes the selected tool(s) |
| **Response** | Returns output in natural language |

---

## Tools: How Agents Take Action

**Action** involves calling tools.

Tools are capabilities the agent can use—functions it can call to get information or perform tasks.

- During **Perception**, the agent sees what tools are available
- During **Reasoning**, it decides which tool fits the question
- During **Action**, it executes the tool

---

## How Agents Choose Tools

The agent matches questions to tool descriptions:

**Question:** "How many critical maintenance events are there?"

**Tool descriptions:**
- `get_graph_schema`: "Get database structure..."
- `search_content`: "Search for content about topics..."
- `query_database`: "Get answers to factual questions, counts..."

**Agent reasons:** "How many" → count → `query_database`

---

## Retrievers as Tools

Your retrievers become tools:

| Tool | Based On | When Agent Uses It |
|------|----------|-------------------|
| Schema Tool | Graph introspection | "What data exists in the graph?" |
| Semantic Search | Vector Retriever | "What causes...", "Describe..." |
| Database Query | Text2Cypher | "How many...", "List all..." |

Each tool has a description that tells the agent when to use it.

---

## The ReAct Pattern

Agents follow **ReAct** (Reasoning + Acting):

```
1. Receive question: "How many critical events does Engine #1 on N10001 have?"
2. Reason: "This asks for a count"
3. Act: Call Database Query Tool
4. Observe: Result = 7
5. Respond: "Engine #1 on N10001 has 7 critical maintenance events."
```

For complex questions, the agent may loop through multiple cycles.

---

## Multi-Tool Example

**Question:** "What bearing faults affect Engine #1 and which aircraft is it on?"

**Agent process:**
1. **Reason:** Need fault content AND aircraft relationship
2. **Act:** Call Semantic Search for bearing fault descriptions
3. **Observe:** Maintenance manual chunks about bearing wear
4. **Reason:** Now need the specific aircraft
5. **Act:** Call Database Query for aircraft linked to Engine #1
6. **Observe:** Aircraft tail number N10001
7. **Respond:** Combine both into a comprehensive answer

---

## Why Agents Matter

**Without agents:**
- Build separate interfaces for each retriever
- Force users to choose which retriever to use
- Complex user experience

**With agents:**
- Users ask natural questions
- System figures out how to answer
- Conversational, intuitive experience

---

## An Example: The GraphRAG Agent

An example of an agent is a GraphRAG system that:

1. **Receives** a user question
2. **Analyzes** what kind of question it is
3. **Selects** and executes the appropriate tool(s)
4. **Synthesizes** results into a coherent answer

Your retrievers become **tools** the agent can use.

---

## Summary

In this lesson, you learned:

- **Agents** have four components: Perception, Reasoning, Action, Response
- **Tools** are capabilities agents use to take action
- **Selection** happens through semantic matching to tool descriptions
- **ReAct pattern**: Reason → Act → Observe → Respond
- **Result**: Users ask naturally; agents figure out how to answer

**Next:** Learn how Databricks Genie, Neo4j MCP, and the multi-agent supervisor work together.
