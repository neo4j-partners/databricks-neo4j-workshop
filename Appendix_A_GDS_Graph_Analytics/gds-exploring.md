# GDS Exploring: Aircraft Digital Twin Graph

Sample GDS projection and algorithm queries from notebooks 03, 04, and 05. Copy and paste into the [Neo4j Aura Query interface](https://console.neo4j.io).

Notebooks run the full pipeline (feature compute → project → write) from Databricks. These queries let you explore the results in the Neo4j Browser and re-run individual GDS steps directly.

## What the Notebooks Write

| Notebook | Writes to Neo4j |
|---|---|
| 04 — kNN | `*_norm` properties on `Aircraft` nodes; `SIMILAR_PROFILE` relationships with `similarity_score` |
| 05 — PageRank / Betweenness | `pagerank_score` and `betweenness_score` properties on `Airport` nodes |
| 06 — Node Similarity | `SIMILAR_FAULT_PROFILE` relationships with `jaccard_score` |

---

## GDS Version and Projection Inventory

### Check the GDS version

```sql
RETURN gds.version() AS version
```

> **Concepts**: Confirms the GDS plugin is installed and returns the version. AuraDB Professional ships with GDS included — if this errors, your tier does not support GDS.

### List active in-memory projections

```sql
CALL gds.graph.list()
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount
```

> **Concepts**: Projections are held in heap memory and cleared on instance restart. Use this to confirm a projection exists before running an algorithm, or to spot stale projections consuming memory.

### Drop all projections at once

```sql
CALL gds.graph.list()
YIELD graphName
CALL gds.graph.drop(graphName, false)
YIELD graphName AS dropped
RETURN dropped
```

> **Tip**: Chains `list()` into `drop()` in a single query. The `false` argument suppresses errors if a projection disappears between the list and drop steps. Useful when restarting a lab or recovering from a failed run that left stale projections in memory.

---

## Notebook 03 — kNN Aircraft Similarity

Each aircraft gets a feature vector of 7 normalized metrics (sensor averages/std devs and maintenance counts). kNN finds the 3 most operationally similar peer aircraft using cosine similarity.

### Verify feature properties landed on Aircraft nodes

```sql
MATCH (a:Aircraft)
WHERE a.avg_egt_norm IS NOT NULL
RETURN a.tail_number                          AS TailNumber,
       round(a.avg_egt_norm, 3)               AS AvgEGT,
       round(a.stddev_vibration_norm, 3)      AS StddevVibration,
       round(a.avg_fuel_flow_norm, 3)         AS AvgFuelFlow,
       round(a.total_events_norm, 3)          AS TotalEvents,
       round(a.critical_events_norm, 3)       AS CriticalEvents
ORDER BY a.tail_number
LIMIT 10
```

> **Concepts**: The notebook writes 7 `*_norm` properties to each Aircraft node via the Spark Connector. `IS NOT NULL` filters to aircraft that have been enriched — useful if the feature write only covered a subset.

### Project Aircraft nodes for kNN

```sql
CALL gds.graph.drop('aircraft-profiles', false) YIELD graphName;

CALL gds.graph.project(
    'aircraft-profiles',
    {
        Aircraft: {
            properties: [
                'avg_egt_norm', 'stddev_egt_norm',
                'avg_vibration_norm', 'stddev_vibration_norm',
                'avg_fuel_flow_norm',
                'total_events_norm', 'critical_events_norm'
            ]
        }
    },
    '*'
)
YIELD graphName, nodeCount, relationshipCount
```

> **Concepts**: kNN operates purely on node properties — no relationships need to be traversed. `'*'` projects all relationship types as a wildcard (GDS 2026+ requires at least one relationship type even for property-only algorithms). The `gds.graph.drop('...', false)` before projection prevents an error if the named projection already exists. `false` means "fail silently if missing."

### Stream kNN similarity pairs

```sql
CALL gds.knn.stream('aircraft-profiles', {
    topK: 3,
    nodeProperties: [
        'avg_egt_norm', 'stddev_egt_norm',
        'avg_vibration_norm', 'stddev_vibration_norm',
        'avg_fuel_flow_norm',
        'total_events_norm', 'critical_events_norm'
    ],
    similarityCutoff: 0.4,
    randomSeed: 42,
    concurrency: 1
})
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).tail_number AS Aircraft,
       gds.util.asNode(node1).model       AS Model,
       gds.util.asNode(node2).tail_number AS PeerAircraft,
       gds.util.asNode(node2).model       AS PeerModel,
       round(similarity, 4)               AS SimilarityScore
ORDER BY Aircraft, SimilarityScore DESC
```

> **Concepts**: `stream` returns results as rows without writing to the database — use it to inspect before committing. `gds.util.asNode(nodeId)` resolves a GDS internal node ID back to the Neo4j node. `similarityCutoff: 0.4` drops pairs with cosine similarity below 0.4.

### Write SIMILAR_PROFILE relationships

```sql
CALL gds.knn.write('aircraft-profiles', {
    topK: 3,
    writeRelationshipType: 'SIMILAR_PROFILE',
    writeProperty: 'similarity_score',
    nodeProperties: [
        'avg_egt_norm', 'stddev_egt_norm',
        'avg_vibration_norm', 'stddev_vibration_norm',
        'avg_fuel_flow_norm',
        'total_events_norm', 'critical_events_norm'
    ],
    randomSeed: 42,
    concurrency: 1
})
YIELD relationshipsWritten, nodesCompared
```

> **Concepts**: `write` persists results back to the database. The `similarity_score` property on each relationship holds the cosine similarity (0–1). These relationships survive instance restarts; the projection does not.

### Visualize the full similarity network

```sql
MATCH (a:Aircraft)-[r:SIMILAR_PROFILE]->(peer:Aircraft)
RETURN a, r, peer
```

> **Concepts**: Returning full nodes and relationships renders as a graph visualization in Neo4j Browser. Each aircraft appears as a node; edges represent computed similarity.

### Top kNN pairs by similarity score

```sql
MATCH (a:Aircraft)-[r:SIMILAR_PROFILE]->(peer:Aircraft)
WHERE r.similarity_score IS NOT NULL
RETURN a.tail_number   AS Aircraft,
       a.model         AS Model,
       peer.tail_number AS Peer,
       peer.model       AS PeerModel,
       round(r.similarity_score, 4) AS Similarity
ORDER BY Similarity DESC
LIMIT 10
```

> **Concepts**: Sorted by `similarity_score` descending — the highest-similarity pairs are the most operationally aligned and make the strongest candidates for proactive inspection.

### Cross-model similarity — peers across model boundaries

```sql
MATCH (a:Aircraft)-[r:SIMILAR_PROFILE]->(peer:Aircraft)
WHERE a.model <> peer.model
  AND r.similarity_score IS NOT NULL
RETURN a.tail_number   AS Aircraft,
       a.model         AS Model,
       peer.tail_number AS Peer,
       peer.model       AS PeerModel,
       round(r.similarity_score, 4) AS Similarity
ORDER BY Similarity DESC
```

> **Concepts**: `a.model <> peer.model` filters to pairs where the two aircraft are different models. Cross-model similarity is operationally significant — it implies shared degradation patterns that transcend model type.

### Peer alert: who to inspect when a given aircraft flags an anomaly?

```sql
MATCH (a:Aircraft {tail_number: 'N10000'})-[r:SIMILAR_PROFILE]->(peer:Aircraft)
WHERE r.similarity_score IS NOT NULL
RETURN peer.tail_number AS PeerTail,
       peer.model       AS PeerModel,
       peer.operator    AS PeerOperator,
       round(r.similarity_score, 4) AS Similarity
ORDER BY Similarity DESC
```

> **Concepts**: The core operational use case — when one aircraft shows an anomaly, inspect its kNN peers, which share the same feature signature and may be on the same degradation trajectory. Swap `N10000` for any tail number in the fleet.

### Drop the projection when done

```sql
CALL gds.graph.drop('aircraft-profiles', false) YIELD graphName
```

> **Concepts**: Projections consume heap memory. Drop them after use; the `SIMILAR_PROFILE` relationships and `*_norm` properties on Aircraft nodes persist independently.

---

## Notebook 04 — PageRank and Betweenness Centrality on the Airport Route Network

Flights connect airports through intermediate Flight nodes — there are no direct Airport-to-Airport relationships in the base graph. The Cypher aggregation projection builds a virtual weighted Airport graph, where edge weight equals the number of flights on each route.

### Explore airport traffic before projecting

```sql
MATCH (f:Flight)-[:DEPARTS_FROM]->(ap:Airport)
WITH ap, count(f) AS Departures
OPTIONAL MATCH (f2:Flight)-[:ARRIVES_AT]->(ap)
RETURN ap.iata     AS IATA,
       ap.city     AS City,
       Departures,
       count(f2)   AS Arrivals
ORDER BY Departures DESC
```

> **Concepts**: `OPTIONAL MATCH` keeps airports with zero arrivals. This gives a traffic baseline before running centrality — useful to know whether algorithm rankings align with raw volume.

### Top routes by flight frequency

```sql
MATCH (f:Flight)-[:DEPARTS_FROM]->(dep:Airport),
      (f)-[:ARRIVES_AT]->(arr:Airport)
RETURN dep.iata AS Origin,
       arr.iata AS Destination,
       count(f) AS Flights
ORDER BY Flights DESC
LIMIT 15
```

> **Concepts**: Identifies the highest-frequency routes — these will dominate the PageRank calculation because weight equals flight count.

### Build the weighted airport route projection (Cypher aggregation)

```sql
CALL gds.graph.drop('airport-routes', false) YIELD graphName;

MATCH (dep:Airport)<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(arr:Airport)
WITH dep, arr, count(f) AS flight_count
RETURN gds.graph.project(
    'airport-routes',
    dep,
    arr,
    {
        sourceNodeLabels: ['Airport'],
        targetNodeLabels: ['Airport'],
        relationshipType: 'FLIES_TO',
        relationshipProperties: {weight: flight_count}
    },
    {undirectedRelationshipTypes: ['FLIES_TO']}
)
```

> **Concepts**: Cypher aggregation projection uses `RETURN gds.graph.project(...)` (a function, not a procedure). The `MATCH` pattern traverses through Flight nodes to build a virtual Airport-to-Airport graph. `undirectedRelationshipTypes: ['FLIES_TO']` treats every route bidirectionally — A→B and B→A are equivalent for centrality purposes.

### Stream PageRank — which airports are most influential?

```sql
CALL gds.pageRank.stream('airport-routes', {
    maxIterations: 20,
    dampingFactor: 0.85,
    relationshipWeightProperty: 'weight'
})
YIELD nodeId, score
WHERE score > 0
RETURN gds.util.asNode(nodeId).iata AS IATA,
       gds.util.asNode(nodeId).city AS City,
       round(score, 4)              AS PageRank
ORDER BY PageRank DESC
```

> **Concepts**: PageRank scores an airport by both the volume of connections and the importance of the airports it connects to. `relationshipWeightProperty: 'weight'` means high-frequency routes contribute more influence. `dampingFactor: 0.85` is the standard value (probability of following a link vs. jumping randomly).

### Stream Betweenness — which airports are critical connectors?

```sql
CALL gds.betweenness.stream('airport-routes')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).iata AS IATA,
       gds.util.asNode(nodeId).city AS City,
       round(score, 2)              AS Betweenness
ORDER BY Betweenness DESC
```

> **Concepts**: Betweenness measures how often an airport lies on the shortest path between any two other airports. A high-betweenness airport is a structural connector: removing it would fragment the network most severely. Compare the ranking with PageRank, since airports that rank high on both are simultaneously traffic hubs and critical connectors.

### Write PageRank and Betweenness scores to Airport nodes

```sql
CALL gds.pageRank.write('airport-routes', {
    writeProperty: 'pagerank_score',
    maxIterations: 20,
    relationshipWeightProperty: 'weight'
})
YIELD nodePropertiesWritten;

CALL gds.betweenness.write('airport-routes', {
    writeProperty: 'betweenness_score'
})
YIELD nodePropertiesWritten
```

> **Concepts**: `write` mode persists results as node properties, making them queryable from any Cypher client and visible in the graph visualization. Each statement runs sequentially using the same `airport-routes` projection.

### Airports ranked by PageRank with betweenness (after write)

```sql
MATCH (ap:Airport)
WHERE ap.pagerank_score IS NOT NULL
RETURN ap.iata                          AS IATA,
       ap.city                          AS City,
       round(ap.pagerank_score, 4)      AS PageRank,
       round(ap.betweenness_score, 1)   AS Betweenness
ORDER BY PageRank DESC
```

> **Concepts**: Once written, scores are plain node properties — queryable without any active projection. `IS NOT NULL` ensures only enriched Airport nodes appear.

### Hubs vs. connectors — where the two rankings disagree

```sql
MATCH (ap:Airport)
WHERE ap.pagerank_score IS NOT NULL
  AND ap.betweenness_score IS NOT NULL
RETURN ap.iata                          AS IATA,
       ap.city                          AS City,
       round(ap.pagerank_score, 4)      AS PageRank,
       round(ap.betweenness_score, 1)   AS Betweenness
ORDER BY Betweenness DESC
```

> **Concepts**: Sorting by betweenness instead of PageRank surfaces the disagreements. An airport with high PageRank but low betweenness is a busy hub inside a dense cluster; one with high betweenness but modest PageRank is a bridge between regions and a structural single point of failure.

### Maintenance delays departing from the top PageRank airport

```sql
MATCH (ap:Airport)
WHERE ap.pagerank_score IS NOT NULL
WITH ap ORDER BY ap.pagerank_score DESC LIMIT 1
MATCH (ap)<-[:DEPARTS_FROM]-(f:Flight)-[:HAS_DELAY]->(d:Delay {cause: 'Maintenance'})
RETURN ap.iata         AS Airport,
       ap.city         AS City,
       f.flight_number AS Flight,
       d.minutes       AS DelayMinutes
ORDER BY DelayMinutes DESC
LIMIT 20
```

> **Concepts**: Two-step pattern: first find the top airport by PageRank using `WITH ap ORDER BY ... LIMIT 1`, then traverse outward to flights with maintenance-caused delays. This joins graph topology (centrality) with operational data (delays) in a single Cypher query.

---

## Notebook 05 — Node Similarity on Aircraft Fault Profiles

Node Similarity computes Jaccard similarity — overlap of shared neighbors — on a bipartite Aircraft-FaultType graph. Aircraft nodes share no direct neighbors in the base graph (each component belongs to exactly one aircraft), so the notebook creates temporary `FaultType` nodes representing distinct `fault + severity` combinations.

### Explore fault type vocabulary

```sql
MATCH (m:MaintenanceEvent)
WITH m.fault + '_' + m.severity AS FaultKey,
     m.fault                    AS Fault,
     m.severity                 AS Severity
RETURN FaultKey, Fault, Severity, count(*) AS Occurrences
ORDER BY Occurrences DESC
```

> **Concepts**: Shows the distinct `fault × severity` combinations that form the similarity vocabulary. More distinct fault types means richer similarity signal — if all aircraft have identical fault types, every pair scores 1.0.

### Fault type diversity per aircraft

```sql
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(:System)-[:HAS_COMPONENT]->(:Component)
      -[:HAS_EVENT]->(m:MaintenanceEvent)
RETURN a.tail_number                                          AS Aircraft,
       a.model                                               AS Model,
       count(DISTINCT m.fault + '_' + m.severity)            AS DistinctFaultTypes,
       count(m)                                              AS TotalEvents
ORDER BY DistinctFaultTypes DESC
```

> **Concepts**: Four-hop traversal from Aircraft down to MaintenanceEvent. Aircraft with many distinct fault types carry more similarity information — those with only 1–2 fault types will have sparse similarity relationships after filtering.

### Create FaultType nodes (graph enrichment step)

```sql
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(:System)-[:HAS_COMPONENT]->(:Component)
      -[:HAS_EVENT]->(m:MaintenanceEvent)
WITH a,
     m.fault + '_' + m.severity AS fault_key,
     m.fault                    AS fault_name,
     m.severity                 AS severity
MERGE (ft:FaultType {key: fault_key})
    ON CREATE SET ft.fault = fault_name, ft.severity = severity
MERGE (a)-[:EXPERIENCED_FAULT]->(ft)
RETURN count(DISTINCT ft) AS FaultTypeNodes,
       count(DISTINCT a)  AS AircraftConnected
```

> **Concepts**: `MERGE` on `FaultType` is idempotent — running this twice creates no duplicates. The pattern makes cross-aircraft similarity computable: two aircraft that both experienced `bearing wear_MAJOR` both connect to the same `FaultType` node, giving them a shared neighbor that Jaccard similarity can measure.

### Verify the bipartite structure

```sql
MATCH (a:Aircraft)-[:EXPERIENCED_FAULT]->(ft:FaultType)
RETURN a.tail_number AS Aircraft,
       count(ft)     AS FaultTypes,
       collect(ft.key)[..5] AS SampleFaults
ORDER BY FaultTypes DESC
LIMIT 10
```

> **Concepts**: Confirms the enrichment worked. Each aircraft should connect to at least one FaultType. `[..5]` slices the collected list to the first 5 entries.

### Project the bipartite Aircraft-FaultType graph

```sql
CALL gds.graph.drop('aircraft-faulttype', false) YIELD graphName;

CALL gds.graph.project(
    'aircraft-faulttype',
    ['Aircraft', 'FaultType'],
    {EXPERIENCED_FAULT: {orientation: 'NATURAL'}}
)
YIELD graphName, nodeCount, relationshipCount
```

> **Concepts**: Node Similarity needs both node labels in the projection — `['Aircraft', 'FaultType']` — so GDS can traverse the bipartite graph. `orientation: 'NATURAL'` preserves direction (Aircraft → FaultType), which is what Jaccard similarity expects for bipartite graphs.

### Stream Node Similarity — top Jaccard pairs

```sql
CALL gds.nodeSimilarity.stream('aircraft-faulttype', {
    topK: 5,
    similarityCutoff: 0.2
})
YIELD node1, node2, similarity
WHERE gds.util.asNode(node1):Aircraft
  AND gds.util.asNode(node2):Aircraft
RETURN gds.util.asNode(node1).tail_number AS AircraftA,
       gds.util.asNode(node1).model       AS ModelA,
       gds.util.asNode(node2).tail_number AS AircraftB,
       gds.util.asNode(node2).model       AS ModelB,
       round(similarity, 4)               AS JaccardSimilarity
ORDER BY JaccardSimilarity DESC
LIMIT 20
```

> **Concepts**: The `WHERE gds.util.asNode(node1):Aircraft` filter discards Aircraft-FaultType pairs — we only want Aircraft-Aircraft results. `similarityCutoff: 0.2` drops pairs sharing fewer than 20% of their combined fault type portfolio. Jaccard = `|intersection| / |union|`.

### Write SIMILAR_FAULT_PROFILE relationships

```sql
CALL gds.nodeSimilarity.write('aircraft-faulttype', {
    topK: 5,
    similarityCutoff: 0.2,
    writeRelationshipType: 'SIMILAR_FAULT_PROFILE',
    writeProperty: 'jaccard_score'
})
YIELD nodesCompared, relationshipsWritten
```

> **Concepts**: Writes Jaccard scores as `SIMILAR_FAULT_PROFILE` relationships directly on Aircraft nodes. `topK: 5` means each aircraft gets at most 5 outgoing similarity relationships.

### Most similar aircraft pairs by Jaccard score (after write)

```sql
MATCH (a:Aircraft)-[r:SIMILAR_FAULT_PROFILE]->(b:Aircraft)
WHERE r.jaccard_score IS NOT NULL
RETURN a.tail_number        AS Aircraft,
       a.model              AS Model,
       b.tail_number        AS Peer,
       b.model              AS PeerModel,
       round(r.jaccard_score, 4) AS JaccardScore
ORDER BY JaccardScore DESC
LIMIT 15
```

### Cross-model fault profile similarity

```sql
MATCH (a:Aircraft)-[r:SIMILAR_FAULT_PROFILE]->(b:Aircraft)
WHERE a.model <> b.model
  AND r.jaccard_score IS NOT NULL
RETURN a.tail_number        AS Aircraft,
       a.model              AS Model,
       b.tail_number        AS Peer,
       b.model              AS PeerModel,
       round(r.jaccard_score, 4) AS JaccardScore
ORDER BY JaccardScore DESC
```

> **Concepts**: Cross-model pairs are the most operationally significant result — aircraft sharing failure modes despite being different models implies a fault pattern that is not model-specific (e.g., a common supplier component or maintenance practice).

### Visualize the fault profile similarity network

```sql
MATCH (a:Aircraft)-[r:SIMILAR_FAULT_PROFILE]->(b:Aircraft)
RETURN a, r, b
```

### Clean up FaultType scaffolding (preserves SIMILAR_FAULT_PROFILE)

```sql
CALL gds.graph.drop('aircraft-faulttype', false) YIELD graphName;

MATCH (ft:FaultType)
DETACH DELETE ft
```

> **Concepts**: `DETACH DELETE` removes the node and all its relationships (`EXPERIENCED_FAULT` edges). `SIMILAR_FAULT_PROFILE` relationships live between Aircraft nodes and are unaffected.

---

## Cross-Algorithm Queries

These require all three notebooks to have run (or the write steps above to have been executed).

### Compare kNN peers vs. fault-profile peers for one aircraft

```sql
MATCH (a:Aircraft {tail_number: 'N10000'})
CALL (a) {
  OPTIONAL MATCH (a)-[r:SIMILAR_FAULT_PROFILE]->(peer:Aircraft)
  RETURN collect({tail: peer.tail_number, jaccard: round(r.jaccard_score, 4)}) AS FaultProfilePeers
}
CALL (a) {
  OPTIONAL MATCH (a)-[r:SIMILAR_PROFILE]->(peer:Aircraft)
  RETURN collect({tail: peer.tail_number, knn: round(r.similarity_score, 4)}) AS KNNPeers
}
RETURN FaultProfilePeers, KNNPeers
```

> **Concepts**: Two `CALL (a) { ... }` subqueries execute independently against the same starting node and each collect their results into a list. This avoids the cartesian product that two `OPTIONAL MATCH` clauses on the same variable would produce. Peers appearing in both lists are aligned by both neighborhood structure (Jaccard) and feature-vector distance (kNN), making them the strongest signals for proactive maintenance.

### Aircraft that appear as peers in both similarity algorithms

```sql
MATCH (a:Aircraft)-[:SIMILAR_FAULT_PROFILE]->(peer:Aircraft)
MATCH (a)-[:SIMILAR_PROFILE]->(peer)
RETURN a.tail_number   AS Aircraft,
       peer.tail_number AS Peer,
       a.model          AS Model,
       peer.model       AS PeerModel
ORDER BY Aircraft
```

> **Concepts**: Matching against both `SIMILAR_FAULT_PROFILE` and `SIMILAR_PROFILE` in separate `MATCH` clauses requires the pattern to satisfy both — equivalent to a SQL INNER JOIN on the pair. These are the highest-confidence peer relationships in the dataset.

### Busiest airports by PageRank that also have high maintenance delay rates

```sql
MATCH (ap:Airport)
WHERE ap.pagerank_score IS NOT NULL
WITH ap ORDER BY ap.pagerank_score DESC LIMIT 10
MATCH (ap)<-[:DEPARTS_FROM]-(f:Flight)
OPTIONAL MATCH (f)-[:HAS_DELAY]->(d:Delay {cause: 'Maintenance'})
RETURN ap.iata                                       AS IATA,
       ap.city                                       AS City,
       round(ap.pagerank_score, 4)                   AS PageRank,
       round(ap.betweenness_score, 1)                AS Betweenness,
       count(DISTINCT f)                             AS TotalFlights,
       count(d)                                      AS MaintenanceDelays,
       round(100.0 * count(d) / count(DISTINCT f), 1) AS MaintenanceDelayPct
ORDER BY PageRank DESC
```

> **Concepts**: Limits to the top 10 airports by PageRank using `WITH ap ORDER BY ... LIMIT 10`, then aggregates delay data for those airports only. Dividing delay count by flight count normalizes for airport size — a 10% maintenance delay rate means something different at a 100-flight hub than at a 10-flight spoke.
