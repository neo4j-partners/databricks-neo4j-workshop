# Aura Explore: Aircraft Digital Twin Walkthrough

Five progressive queries that build a live graph visualization story in [Neo4j Aura Explore](https://console.neo4j.io).

Run them in order. Each query adds a layer — by the end you have a complete picture of one aircraft's operational health and the peers that share its degradation signature.

---

## Step 1 — Start with the aircraft

```cypher
MATCH (a:Aircraft {tail_number: 'N10082'})
RETURN a
```

> One node. Orient the audience: this is a B737-800 operated in the fleet. All the operational complexity — systems, sensors, maintenance history, peer relationships — radiates from here.

---

## Step 2 — Expand to onboard systems

```cypher
MATCH (a:Aircraft {tail_number: 'N10082'})-[hs:HAS_SYSTEM]->(s:System)
RETURN a, hs, s
```

> The aircraft's physical subsystems fan out as connected nodes. Each edge is a `HAS_SYSTEM` relationship. This is the first level of the digital twin — the aircraft decomposed into its major mechanical domains.

---

## Step 3 — Drill into components

```cypher
MATCH (a:Aircraft {tail_number: 'N10082'})
      -[hs:HAS_SYSTEM]->(s:System)
      -[hc:HAS_COMPONENT]->(c:Component)
RETURN a, hs, s, hc, c
```

> Each system expands into its constituent components. The graph now shows the full mechanical hierarchy — the structure that maintenance events and sensor readings attach to.

---

## Step 4 — Surface the critical maintenance events

```cypher
MATCH (a:Aircraft {tail_number: 'N10082'})
      -[hs:HAS_SYSTEM]->(s:System)
      -[hc:HAS_COMPONENT]->(c:Component)
      -[he:HAS_EVENT]->(m:MaintenanceEvent)
WHERE m.severity = 'CRITICAL'
RETURN a, hs, s, hc, c, he, m
```

> Filter to `CRITICAL` severity events only. N10082 has 31 — they attach to specific components and light up which parts of the aircraft are under stress. The graph now tells the maintenance story: which systems are failing, how often, and where in the hierarchy the failures concentrate.

---

## Step 5 — The peer alert: who else to inspect?

> **Prerequisite:** This query only works after notebook [`04_gds_knn_aircraft.ipynb`](04_gds_knn_aircraft.ipynb) has run, since that notebook creates the `SIMILAR_PROFILE` relationships.

```cypher
MATCH (a:Aircraft {tail_number: 'N10082'})-[r:SIMILAR_PROFILE]->(peer:Aircraft)
RETURN a, r, peer
```

> The payoff. kNN found 6 aircraft with the same operational feature signature as N10082 — same sensor behavior, same maintenance burden. When N10082 shows a fault, these are the peers to proactively inspect. Each `SIMILAR_PROFILE` edge carries a `similarity_score` property visible on hover. This is the graph doing something a relational database cannot: surfacing latent risk across the fleet from structure alone.
