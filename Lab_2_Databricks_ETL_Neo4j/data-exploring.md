# Data Exploring: Aircraft Digital Twin Graph (v2)

Sample Cypher queries for the v2 dataset. Copy and paste into the [Neo4j Aura Query interface](https://console.neo4j.io) to explore the graph.

## Creating Nodes and Relationships

### Create an aircraft

```cypher
MERGE (a:Aircraft {tail_number: 'N99999'})
ON CREATE SET
  a.manufacturer = 'Boeing',
  a.model        = '737-800',
  a.operator     = 'Demo Airlines'
RETURN a
```

> **Concepts**: `MERGE` finds the node if it already exists or creates it — safe to run more than once. `ON CREATE SET` only fires when a new node is actually created, so re-running will not overwrite existing properties. The lookup key (`tail_number`) should be unique and indexed.

### Create a system, attach it to the aircraft, and add a component

```cypher
MERGE (a:Aircraft {tail_number: 'N99999'})
MERGE (s:System {name: 'Hydraulic System A'})
  ON CREATE SET s.type = 'Hydraulic'
MERGE (a)-[:HAS_SYSTEM]->(s)
MERGE (c:Component {name: 'Hydraulic Pump 1'})
  ON CREATE SET c.type = 'Pump'
MERGE (s)-[:HAS_COMPONENT]->(c)
RETURN a, s, c
```

> **Concepts**: Chaining multiple `MERGE` statements in one query is idempotent — running it twice produces the same graph. Each `MERGE` on a relationship (`HAS_SYSTEM`, `HAS_COMPONENT`) also implies both endpoint nodes already exist, so node `MERGE`s must come first. Returning `a, s, c` renders the three-node subgraph visually in Neo4j Browser.

---

## Graph Schema

### Node labels and counts

```sql
MATCH (n)
RETURN labels(n)[0] AS Label, count(n) AS Count
ORDER BY Count DESC
```

> **Concepts**: `labels(n)` returns a list of labels on a node; `[0]` takes the first. Gives a census of the entire graph. Expected: ~14.5K Flights, ~5.5K Delays, ~612 Components, 286 MaintenanceEvents, 57 Removals, 36 Aircraft, 288 Sensors, 144 Systems, 40 Airports.

### Visualize the full graph schema

```sql
CALL db.schema.visualization()
```

> **Concepts**: Built-in procedure that returns every node label, relationship type, and how they connect — useful for orienting yourself before writing queries.

### Count relationship types

```sql
MATCH ()-[r]->()
RETURN type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC
```

> **Concepts**: `type(r)` returns the relationship type as a string. Running this shows you all 12 relationship types in this dataset and how many of each exist.

---

## Aircraft Topology

### One aircraft's full hierarchy

```sql
MATCH (a:Aircraft {tail_number: 'N10000'})-[:HAS_SYSTEM]->(s:System)-[:HAS_COMPONENT]->(c:Component)
RETURN a, s, c
```

> **Concepts**: Multi-hop pattern in a single `MATCH`. Returns nodes and relationships as a graph visualization in Neo4j Browser.

### System and component breakdown (tabular)

```sql
MATCH (a:Aircraft {tail_number: 'N10000'})-[:HAS_SYSTEM]->(s:System)
OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(c:Component)
RETURN a.tail_number AS Aircraft,
       s.type AS SystemType,
       s.name AS System,
       count(c) AS ComponentCount,
       collect(c.name) AS Components
ORDER BY s.type, s.name
```

> **Concepts**: `OPTIONAL MATCH` keeps systems that have no components; `collect()` groups component names into a list per system; `count(c)` counts components per system.

### Fleet breakdown by manufacturer and model

```sql
MATCH (a:Aircraft)
RETURN a.manufacturer AS Manufacturer,
       a.model AS Model,
       count(a) AS Count,
       collect(DISTINCT a.operator) AS Operators
ORDER BY Manufacturer, Model
```

> **Concepts**: `collect(DISTINCT ...)` de-duplicates operator names within each group. Non-aggregated columns (`Manufacturer`, `Model`) form the implicit group key.

### How many systems and sensors does each aircraft have?

```sql
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)
WITH a, count(DISTINCT s) AS SystemCount
MATCH (a)-[:HAS_SYSTEM]->(s2:System)-[:HAS_SENSOR]->(sn:Sensor)
RETURN a.tail_number AS TailNumber,
       a.model AS Model,
       SystemCount,
       count(DISTINCT sn) AS SensorCount
ORDER BY SensorCount DESC
```

> **Concepts**: `WITH` pipes aggregated results into the next `MATCH`; using `DISTINCT` inside `count()` prevents double-counting when multiple paths reach the same node.

---

## Flight Operations

### Recent flights for one aircraft

```sql
MATCH (a:Aircraft {tail_number: 'N10000'})-[:OPERATES_FLIGHT]->(f:Flight)
WHERE f.scheduled_departure IS NOT NULL
RETURN f.flight_number AS Flight,
       f.origin AS Origin,
       f.destination AS Destination,
       f.scheduled_departure AS Departure,
       f.scheduled_arrival AS Arrival
ORDER BY f.scheduled_departure DESC
LIMIT 10
```

> **Concepts**: `IS NOT NULL` guard on the sort property prevents nulls from appearing unexpectedly at the top or bottom of results.

### Busiest routes by flight count

```sql
MATCH (f:Flight)-[:DEPARTS_FROM]->(dep:Airport),
      (f)-[:ARRIVES_AT]->(arr:Airport)
RETURN dep.iata AS Origin,
       arr.iata AS Destination,
       count(f) AS Flights
ORDER BY Flights DESC
LIMIT 15
```

> **Concepts**: Two relationship traversals in one `MATCH` clause. `iata` is the standard 3-letter airport code.

### Airports with the most departures

```sql
MATCH (f:Flight)-[:DEPARTS_FROM]->(a:Airport)
RETURN a.iata AS IATA,
       a.name AS Airport,
       a.city AS City,
       count(f) AS Departures
ORDER BY Departures DESC
LIMIT 10
```

> **Concepts**: Traversing the graph in the same direction as stored relationships. You can reverse direction with `<-[:DEPARTS_FROM]-` if needed.

### Flights that experienced delays

```sql
MATCH (f:Flight)-[:HAS_DELAY]->(d:Delay)
WHERE d.minutes IS NOT NULL
RETURN f.flight_number AS Flight,
       f.origin AS Origin,
       f.destination AS Destination,
       d.cause AS DelayCause,
       d.minutes AS DelayMinutes
ORDER BY d.minutes DESC
LIMIT 20
```

> **Concepts**: Filters to flights that have a `HAS_DELAY` relationship, exposing both the flight and delay details in the same row.

### Delay causes ranked by total minutes lost

```sql
MATCH (f:Flight)-[:HAS_DELAY]->(d:Delay)
WHERE d.minutes IS NOT NULL
RETURN d.cause AS Cause,
       count(d) AS Occurrences,
       sum(d.minutes) AS TotalMinutes,
       avg(d.minutes) AS AvgMinutes
ORDER BY TotalMinutes DESC
```

> **Concepts**: Multiple aggregation functions (`count`, `sum`, `avg`) can be used in a single `RETURN`. All operate on the same grouped key (`d.cause`).

---

## Maintenance Events

### All maintenance events with severity

```sql
MATCH (c:Component)-[:HAS_EVENT]->(m:MaintenanceEvent)
RETURN m.severity AS Severity,
       count(m) AS EventCount,
       collect(DISTINCT m.fault)[..5] AS SampleFaults
ORDER BY EventCount DESC
```

> **Concepts**: `[..5]` slices a list to the first 5 elements — handy for sampling without returning huge arrays.

### Maintenance events on one aircraft, newest first

```sql
MATCH (m:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(a:Aircraft {tail_number: 'N10000'})
WHERE m.reported_at IS NOT NULL
RETURN m.event_id AS EventID,
       m.fault AS Fault,
       m.severity AS Severity,
       m.corrective_action AS Action,
       m.reported_at AS ReportedAt
ORDER BY m.reported_at DESC
```

> **Concepts**: Traverses the `AFFECTS_AIRCRAFT` relationship in reverse to find all events that touched a specific aircraft.

### Which systems have the most maintenance events?

```sql
MATCH (m:MaintenanceEvent)-[:AFFECTS_SYSTEM]->(s:System)
RETURN s.type AS SystemType,
       s.name AS SystemName,
       count(m) AS Events,
       collect(DISTINCT m.severity) AS Severities
ORDER BY Events DESC
LIMIT 10
```

> **Concepts**: `AFFECTS_SYSTEM` links a maintenance event to the system it occurred in. Aggregating by system type reveals where problems concentrate.

### Full maintenance context: component → event → system → aircraft

```sql
MATCH (c:Component)-[:HAS_EVENT]->(m:MaintenanceEvent)-[:AFFECTS_SYSTEM]->(s:System)<-[:HAS_SYSTEM]-(a:Aircraft)
WHERE m.severity = 'CRITICAL'
RETURN a.tail_number AS Aircraft,
       a.model AS Model,
       s.type AS System,
       c.name AS Component,
       m.fault AS Fault,
       m.reported_at AS ReportedAt
ORDER BY m.reported_at DESC
```

> **Concepts**: A four-hop pattern that stitches component, event, system, and aircraft into a single row — the kind of join that would require multiple SQL tables and explicit foreign key joins.

---

## Component Removals

### All removals with reason and cost

```sql
MATCH (a:Aircraft)-[:HAS_REMOVAL]->(r:Removal)
WHERE r.removal_date IS NOT NULL
RETURN a.tail_number AS Aircraft,
       r.removal_id AS RemovalID,
       r.reason AS Reason,
       r.removal_date AS Date,
       r.tsn AS TimeOnWing,
       r.csn AS CyclesAtRemoval
ORDER BY r.removal_date DESC
LIMIT 20
```

> **Concepts**: `tsn` (time since new, in hours) and `csn` (cycles since new) are key metrics in aviation maintenance for tracking component wear.

### Which component was removed?

```sql
MATCH (a:Aircraft)-[:HAS_REMOVAL]->(r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
WHERE r.removal_date IS NOT NULL
RETURN a.tail_number AS Aircraft,
       c.type AS ComponentType,
       c.name AS Component,
       r.reason AS Reason,
       r.tsn AS HoursOnWing,
       r.csn AS Cycles,
       r.removal_date AS Date
ORDER BY r.removal_date DESC
```

> **Concepts**: Note that `REMOVED_COMPONENT` points from `Removal` to `Component` — read the relationship as "this removal event removed this component." Traversing to both endpoints in one pattern gives full context.

### Components removed most frequently

```sql
MATCH (r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
RETURN c.type AS ComponentType,
       c.name AS Component,
       count(r) AS Removals
ORDER BY Removals DESC
LIMIT 10
```

> **Concepts**: Aggregating by component reveals which parts are replaced most often — useful for spare parts planning.

---

## Multi-Hop Patterns

### Aircraft with both maintenance events and delays on the same route

```sql
MATCH (a:Aircraft)-[:OPERATES_FLIGHT]->(f:Flight)-[:HAS_DELAY]->(d:Delay),
      (m:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(a)
WHERE d.cause = 'Maintenance'
RETURN a.tail_number AS Aircraft,
       count(DISTINCT f) AS DelayedFlights,
       count(DISTINCT m) AS MaintenanceEvents,
       sum(d.minutes) AS TotalDelayMinutes
ORDER BY TotalDelayMinutes DESC
LIMIT 10
```

> **Concepts**: Two separate `MATCH` patterns joined by the shared `a` variable. This links operational delay data to maintenance history for the same aircraft.

### Sensor-to-aircraft chain

```sql
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)-[:HAS_SENSOR]->(sn:Sensor)
WHERE sn.type IS NOT NULL
RETURN a.tail_number AS Aircraft,
       s.type AS SystemType,
       sn.type AS SensorType,
       sn.name AS SensorName,
       sn.unit AS Unit
ORDER BY a.tail_number, s.type, sn.type
LIMIT 30
```

> **Concepts**: Three-hop traversal from aircraft down to individual sensors. The `unit` property shows what each sensor measures (e.g., `C` for Celsius on an EGT sensor).

### Find which aircraft share the same airport as both origin and destination (round-trip routes)

```sql
MATCH (a:Aircraft)-[:OPERATES_FLIGHT]->(f1:Flight)-[:DEPARTS_FROM]->(ap:Airport),
      (a)-[:OPERATES_FLIGHT]->(f2:Flight)-[:ARRIVES_AT]->(ap)
WHERE f1.flight_id <> f2.flight_id
RETURN a.tail_number AS Aircraft,
       ap.iata AS HubAirport,
       count(DISTINCT f1) AS DepartureFlights,
       count(DISTINCT f2) AS ArrivalFlights
ORDER BY DepartureFlights DESC
LIMIT 10
```

> **Concepts**: The same aircraft variable `a` appears in two `MATCH` patterns — Neo4j treats this as an equi-join on `aircraft_id`. `f1.flight_id <> f2.flight_id` prevents matching a flight against itself.
