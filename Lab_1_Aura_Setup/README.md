# Lab 1: Neo4j Aura Setup

In this lab, you will set up your Neo4j Aura database and save your connection credentials for use in later labs.

## Prerequisites

- A valid email address

## Part 1: Neo4j Aura Signup

Sign up for a Neo4j Aura free trial:

- Follow the [Neo4j Aura Free Trial Signup](Aura_Free_Trial.md) guide to create your own account
- This provides a 14-day free trial with an automatically created instance

### Save Your Credentials

When your instance is created during signup, a dialog appears showing your database credentials (Username and Password). Click **Download to continue** to save the credentials file. If you followed the signup guide above, you have already done this.

> **CRITICAL:** The password is only shown once and will not be available after you close this dialog. Download the credentials file and store it somewhere safe. You will need these credentials in later labs to connect your applications to Neo4j.

You will enter these credentials in the Configuration cell of each Databricks notebook:

```python
NEO4J_URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "<your-password>"
```

## Part 2: Introduction to Cypher

Cypher is Neo4j's query language. Before you load data in Lab 2, practice the basics by creating and querying a small graph.

### Open the Query Interface

1. Go to [console.neo4j.io](https://console.neo4j.io)
2. Select your instance
3. Click **Query** to open the query editor

This is where you will run the Cypher examples below.

### Creating Nodes

Create an Aircraft node with properties:

```cypher
CREATE (a:Aircraft {tail_number: 'N12345', model: 'B737-800', manufacturer: 'Boeing'})
RETURN a
```

`CREATE` makes a node. `:Aircraft` is a **label** (like a type). Properties go inside curly braces.

### Reading Nodes

Find all Aircraft nodes and return their properties:

```cypher
MATCH (a:Aircraft)
RETURN a.tail_number, a.model, a.manufacturer
```

`MATCH` finds patterns in the graph. `RETURN` selects what to display.

### Creating Relationships

Create two nodes connected by a relationship:

```cypher
CREATE (a:Aircraft {tail_number: 'N12345', model: 'B737-800'})
CREATE (s:System {name: 'Engine #1', type: 'CFM56-7B'})
CREATE (a)-[:HAS_SYSTEM]->(s)
RETURN a, s
```

`-[:HAS_SYSTEM]->` creates a directed relationship from the Aircraft to the System.

### Querying Relationships

Traverse relationships to find connected nodes:

```cypher
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)
RETURN a.tail_number, s.name, s.type
```

### Filtering with WHERE

Add conditions to narrow results:

```cypher
MATCH (a:Aircraft)
WHERE a.manufacturer = 'Boeing'
RETURN a.tail_number, a.model
```

### Cleaning Up

Remove all nodes and relationships to start fresh:

```cypher
MATCH (n) DETACH DELETE n
```

`DETACH DELETE` removes nodes and all their relationships.

> **Note:** Run this cleanup before starting Lab 2 so you begin with an empty graph.

> **Tip:** These examples are for learning. In Lab 2 you will load the full Aircraft Digital Twin dataset programmatically using the Spark Connector.

## Next Steps

After completing this lab, continue to [Lab 2 - Databricks ETL to Neo4j](../Lab_2_Databricks_ETL_Neo4j) to load the Aircraft Digital Twin dataset into your Neo4j Aura instance.
