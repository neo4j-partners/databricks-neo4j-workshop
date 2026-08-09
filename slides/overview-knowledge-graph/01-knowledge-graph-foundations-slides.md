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

# Knowledge Graph Foundations

Graph databases, Cypher, and the aircraft digital twin graph

---

## What Is a Graph Database?

A graph database models data as **nodes** and **relationships**.

- **Nodes** represent entities: aircraft, systems, components, sensors, maintenance events
- **Relationships** represent connections: `HAS_SYSTEM`, `HAS_COMPONENT`, `HAS_EVENT`
- **Properties** are key-value pairs on both nodes and relationships

Connections are **stored as first-class structures**, not computed at query time through joins.

<!-- The whole workshop rests on this reframe: a relational database figures out how rows connect at query time, through a join. A graph database stores the connection itself, as a relationship, at write time. -->

---

![bg contain](../aircraft/aircraft-digital-twin-property-graph.svg)

<!-- The property graph view of one aircraft: node types, relationship types, and a few properties each carries. We build this shape up piece by piece for the rest of the deck. -->

---

## Graph Notation

Parentheses denote nodes. Brackets denote relationships:

```
(:Aircraft {tail_number})-[:HAS_SYSTEM]->(:System {name})
```

Each Aircraft node carries properties like `tail_number` and `model`. Each HAS_SYSTEM relationship connects an aircraft to one of its systems. The relationship is directional, typed, and stored alongside the nodes it connects.

<!-- This notation reappears in every Cypher query for the rest of the workshop. -->

---

## Graphs vs Relational Databases

**"Which components sit on aircraft N10007's engines?"**

**In SQL:** join aircraft to systems, then systems to components, filtering for engine type at each step.

**In Cypher:**
```cypher
MATCH (a:Aircraft {tail_number: 'N10007'})
      -[:HAS_SYSTEM]->(s:System {type: 'Engine'})
      -[:HAS_COMPONENT]->(c:Component)
RETURN s.name, c.name, c.type
```

The query reads like the traversal it executes.

<!-- Quick preview. A harder question gets the full side-by-side treatment two slides from now. -->

---

## Cypher Query Language

Cypher uses **pattern-matching syntax** that mirrors graph structure:

```cypher
MATCH (a:Aircraft {model: 'A320-200'})-[:HAS_SYSTEM]->(s:System {type: 'Engine'})
RETURN s.name ORDER BY s.name LIMIT 10
```

- `MATCH` finds nodes and relationships that fit a pattern
- `(a:Aircraft {model: 'A320-200'})` binds an Aircraft node to variable `a`
- `-[:HAS_SYSTEM]->` follows outbound HAS_SYSTEM relationships
- `RETURN` selects which properties to include in results

<!-- Every Cypher query in this workshop is built from these four pieces. -->

---

<style scoped>
section { font-size: 22px; }
</style>

## The Same Question, Two Languages

**Question:** starting from the component that triggered a critical maintenance event, which other aircraft could share the same root cause through common ground infrastructure?

Answering it means walking Component to System to Aircraft, then fanning out through the flights and airports those aircraft share. Neo4j stores every one of those hops as a relationship. The Databricks gold layer stores four tables, `sensor_readings`, `sensors`, `systems`, and `aircraft`, joined in one fixed chain.

**What SQL reaches:** which other aircraft show elevated readings on the same sensor type.

```sql
WITH origin AS (
  SELECT sen.type, s.aircraft_id
  FROM sensors sen JOIN systems s ON sen.system_id = s.system_id
  WHERE sen.sensor_id = 'AC1001-S01-SN01'
)
SELECT a2.tail_number, a2.model, AVG(r2.value) AS avg_value
FROM origin o
JOIN sensors sen2 ON sen2.type = o.type
JOIN systems s2 ON sen2.system_id = s2.system_id AND s2.aircraft_id != o.aircraft_id
JOIN aircraft a2 ON s2.aircraft_id = a2.aircraft_id
JOIN sensor_readings r2 ON r2.sensor_id = sen2.sensor_id
GROUP BY a2.tail_number, a2.model ORDER BY avg_value DESC
```

<!-- This SQL is real and it runs, but it is a self-join on sensor type: fixed depth, no recursion, one shared signal. The shared ground infrastructure the question asks about lives only in Neo4j. Set up the next slide as the same question, run in full. -->

---

<style scoped>
section { font-size: 22px; }
</style>

## The Same Question in Cypher

Every hop the question needs is stored as a relationship, so the traversal runs as written:

```cypher
MATCH (c:Component {component_id: 'AC1001-S01-C04'})
      <-[:HAS_COMPONENT]-(:System)<-[:HAS_SYSTEM]-(origin:Aircraft)
MATCH (origin)-[:OPERATES_FLIGHT|DEPARTS_FROM|ARRIVES_AT*2..6]-(other:Aircraft)
WHERE other <> origin
RETURN DISTINCT other.tail_number, other.model
```

Searching two hops deeper means changing `*2..6` to `*2..10`. One number, no new tables, no new joins.

<!-- Walk the pattern: the component sits under a system, under an aircraft, and from there the query fans out through Flight and Airport nodes to any aircraft within the hop range. The variable-length pattern is the whole point. In SQL, each extra hop is another join; here it is a digit. -->

---

<style scoped>
section { font-size: 22px; }
</style>

## The Aircraft Digital Twin Graph

Nine node labels carry the fleet, its operating history, and its maintenance record.

| Node Label | Example |
|---|---|
| **Aircraft** | N10000, B737-800, NorthernJet |
| **System** | Engine, CFM56-7B #1 |
| **Component** | Turbine, Fuel Pump, Hydraulic Actuator |
| **Sensor** | EGT, Exhaust Gas Temperature, °C |
| **MaintenanceEvent** | MINOR severity, fault: Bearing wear |
| **Flight** | FL00001, NO571, MIA to PHL |
| **Airport** | JFK, John F. Kennedy International Airport |
| **Delay** | Weather, 40 minutes |
| **Removal** | work order WO2408-0001, OUT_WARRANTY |

<!-- Every node label in the base graph, before Lab 3 layers on Document, Chunk, and extracted-entity types. Sensor readings themselves never appear here, only sensor metadata; measured values live in the Databricks sensor_readings table. -->

---

![bg contain](../aircraft/knowledge-graph-structure.svg)

<!-- The full structure: every node label from the last slide, connected by the relationship types coming up next. -->

---

## Relationships in the Graph

```
(Aircraft)-[:HAS_SYSTEM]->(System)
(System)-[:HAS_COMPONENT]->(Component)
(System)-[:HAS_SENSOR]->(Sensor)
(Component)-[:HAS_EVENT]->(MaintenanceEvent)
(MaintenanceEvent)-[:AFFECTS_SYSTEM]->(System)
(MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(Aircraft)
(Aircraft)-[:OPERATES_FLIGHT]->(Flight)
(Flight)-[:DEPARTS_FROM]->(Airport)
(Flight)-[:ARRIVES_AT]->(Airport)
(Flight)-[:HAS_DELAY]->(Delay)
(Aircraft)-[:HAS_REMOVAL]->(Removal)
(Removal)-[:REMOVED_COMPONENT]->(Component)
```

**Aircraft** is the central hub. Systems, flights, and removals attach directly to it, and maintenance events affect it even when they start three hops down at a component.

<!-- Twelve relationship types, all directional and typed. AFFECTS_SYSTEM and AFFECTS_AIRCRAFT both radiate from the same MaintenanceEvent, connecting back to two levels of the topology at once. -->

---

## Why This Schema Design

**Separate relationship types** rather than generic RELATES_TO:

- `AFFECTS_SYSTEM` and `AFFECTS_AIRCRAFT` are distinct types
- Cypher filters by relationship type during traversal, which is indexed and fast
- A property filter on a generic relationship requires checking every connection

**Typed relationships** let traversal patterns follow specific paths efficiently.

<!-- The alternative is one CONNECTED_TO type with a {kind: "affects_system"} property. Neo4j indexes relationship types, not arbitrary property values, so typed relationships stay fast as the graph grows. -->

---

## Multi-Hop Queries

The graph answers questions that require traversing multiple connections:

```cypher
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System {type: 'Engine'})
      -[:HAS_COMPONENT]->(c:Component)
      -[:HAS_EVENT]->(m:MaintenanceEvent {severity: 'CRITICAL'})
RETURN a.tail_number, c.name, m.fault, m.reported_at
ORDER BY m.reported_at DESC
```

Three hops: Aircraft to System to Component to MaintenanceEvent. Each hop follows a stored connection rather than computing a join.

<!-- Each arrow is a relationship that already exists in the graph; nothing is computed at query time. -->

---

![bg contain](../aircraft/step1-flat-tables-foreign-keys.svg)

<!--
Lab 2 starts here. Aircraft, systems, and sensors live as rows in
Databricks Delta tables, joined only by foreign keys, implicit until a
query names them. An Aircraft table, a Systems table, a foreign key
column. The connection is real but only exists as a value a JOIN has
to interpret every time.
-->

---

![bg contain](../aircraft/step2-spark-connector-mapping.svg)

<!--
The Neo4j Spark Connector is the two-way bridge. Databricks to Neo4j,
it turns Delta rows into nodes and foreign keys into typed
relationships. Neo4j to Databricks, it pulls graph data back into
DataFrames. Only the subset that fits a graph model makes the trip.
Lab 2's job: run the connector against aircraft, systems, and sensors
and watch rows become nodes. Sensor readings stay in Delta; topology
and maintenance history move because they are relationship-heavy.

Moving the data is one option of three. The Neo4j Unity Catalog
Connector goes the other way, translating SQL into Cypher so
Databricks reads the graph in place, and a virtual graph translates
Cypher into SQL so Neo4j reads the lakehouse in place. This workshop
loads the graph because every lab after this one traverses it.
-->

---

![bg contain](../aircraft/step3-connected-graph.svg)

<!--
The foreign key that once required a join is now a stored, named,
traversable HAS_SYSTEM relationship. Lab 2 ends with this graph loaded
and queryable. The rest of the workshop, GraphRAG in Lab 3 through the
supervisor agent in Lab 5, builds on this graph existing and staying
queryable.
-->

---

## Neo4j Aura

Neo4j Aura is a **fully managed cloud graph database service**. No infrastructure to maintain, automatic scaling with data and query volume, enterprise-grade security, deployed on AWS, GCP, or Azure.

Traditional relational databases struggle with connected data. Finding friends of friends means chained joins that slow as the chain grows. Graphs traverse those chains natively, so relationship-heavy queries that would need dozens of joins in SQL run as a single pattern match.

This workshop runs on AuraDB Free.

<!-- Aura is the hosted product everything else builds on. Same argument as the earlier SQL-vs-Cypher slides, restated for the database service itself. -->

---

<style scoped>
section { font-size: 24px; }
</style>

## Aura Developer Tools

**Query Workspace:** Cypher editor with syntax highlighting, auto-completion, saved query collections, and log forwarding to your cloud logging service.

**Explore:** visual, no-code graph exploration on an interactive canvas, no Cypher required.

**Dashboards:** low-code bar charts, line charts, geographic maps, and 3D graph visualizations for non-technical stakeholders.

**Graph Analytics:** Explore includes centrality and community detection. The full 65-plus algorithm library runs through Aura Graph Analytics serverless sessions. AuraDB Free carries none of it: the GDS notebooks here are take-home material, read now, run later on an instance with the plugin.

<!-- Query Workspace is where most lab time is spent. Be direct about the Free tier limit: no PageRank or community detection on this instance. -->

---

## The Value of Aura for AI and GenAI

Aura is the foundation this workshop builds GraphRAG on.

- **Built-in vector indexes** for embeddings, the same index type Lab 3 uses over maintenance manual chunks
- **Cypher** as the query language for graph-context retrieval
- **Graph traversal** for relationship reasoning: a match plus everything it connects to
- **APIs** for integration with LLM frameworks

Store the knowledge graph once. Query it for structure, for meaning, or for both.

<!-- The bridge into the rest of the workshop: one database holding both the structured fleet graph and the semantic layer over the maintenance manuals, queryable together. -->

---

## Indexes That Power Search

Beyond the uniqueness constraints used during loading, the graph carries indexes that make retrieval fast, the foundation GraphRAG builds on in Lab 3.

**Vector index**, over Chunk embeddings from the maintenance manuals:
```cypher
CREATE VECTOR INDEX maintenanceChunkEmbeddings IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 1024,
         `vector.similarity_function`: 'cosine'}}
```

**Fulltext index**, `maintenanceChunkText`, supports keyword search over chunk text, complementing vector search.

**Constraints** enforce uniqueness, on `Aircraft.aircraft_id` and every other node label's key property, so `MERGE` matches an existing node instead of scanning the whole label.

<!-- 1024 dimensions because embeddings always come from the databricks-bge-large-en serving endpoint, cosine similarity for distance. No constraint means no index means a full label scan on every load. -->
