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

# Authorization Sync Between Unity Catalog and Neo4j

Bridging two privilege models through a common semantic layer

---

## Neo4j JDBC Lakehouse Federation: Working Prototype

- **Prototype validated:** Neo4j JDBC registered as a UC JDBC connector, working end-to-end in Databricks
- **Neo4j JDBC driver enables SQL-to-Cypher translation:** `SELECT COUNT(*) FROM Aircraft` becomes `MATCH (n:Aircraft) RETURN count(n)` automatically
- **Federated queries:** Neo4j graph data joins with Delta tables in a single Spark SQL statement
- **Current issue:** custom connectors run in an isolated sandbox, adding 13-16 seconds of overhead per query

<!--
The working prototype lives in the neo4j-uc-integration repository.
It uses a custom JDBC connector JAR that bundles the Neo4j driver
and a SQL-to-Cypher translator, registered as a UC Connection.
Analysts write standard SQL in Databricks and the connector
translates it to Cypher under the hood.

The prototype handles Spark's schema-probing subqueries through a
Spark Cleaner module that unwraps the generated wrapper queries
for correct execution. It also resolved a critical metaspace
exhaustion issue in Databricks' SafeSpark sandbox with tuned
Spark config settings.

All fourteen validated query patterns pass: aggregates, COUNT
DISTINCT, WHERE clauses, GROUP BY, HAVING, ORDER BY, LIMIT/OFFSET,
and JOINs. Federated queries that join Neo4j graph data with Delta
tables work in a single statement.
-->

---

## Status: Reviewing with Databricks

- **Passed technical validation** with the Databricks Partner Solution Architect
- **Waiting on product management** approval to list Neo4j as an officially supported data source
- **Native status would place Neo4j** alongside PostgreSQL, Snowflake, MySQL, BigQuery, and other supported sources
- **Customer demand:** Boeing, Syngenta, IBM Federal, Gilead, and multiple Databricks Federal accounts

<!--
The prototype has passed Databricks technical validation with
Prasad Kona, Partner Solution Architect. The next step is approval
from the Unity Catalog PM to list Neo4j as an officially supported
data source.

Customer demand is strong. Boeing, Syngenta, IBM Federal, and
Gilead have all requested a common analysis layer that lets
SQL-only teams combine Neo4j graph queries with Delta tables.
The Databricks Federal field team has also surfaced several
interested accounts.
-->

---

## What Official Federated Data Source Status Unlocks

- **Foreign catalog creation:** `CREATE FOREIGN CATALOG` registers Neo4j as a browsable three-level namespace in Unity Catalog
- **Table-level permissions:** UC grants (`SELECT`, `USE CATALOG`, `BROWSE`) on individual Neo4j-backed tables, not just connection-level access
- **Managed OAuth:** built-in IdP flows (Entra ID, Okta) instead of manually embedding credentials
- **Per-table audit logging:** every query appears in `system.access.audit` with full context
- **Genie natural language queries:** users ask about graph data in plain English without materialized Delta copies
- **Optimized query pushdown:** filters, aggregates, sorts, and joins pushed down as Cypher rather than generic JDBC

<!--
Today, anyone with USE CONNECTION can reach all data behind the
connector. Official status replaces connection-level-only governance
with table-level permissions: SELECT, USE CATALOG, USE SCHEMA, and
BROWSE on individual Neo4j-backed tables.

Foreign catalog creation means node labels and relationship types
appear automatically as tables in Catalog Explorer without manual
materialization or External Metadata API workarounds. Column-level
data lineage would track which Neo4j tables and columns are read
by notebooks, jobs, and dashboards. Data tagging and classification
become available for compliance and data discovery.

On the performance side, dialect-specific query pushdown would
replace the generic Spark JDBC pushdown with optimized Cypher
translation. Join pushdown could convert cross-table joins into
graph traversals. And native status eliminates the SafeSpark
sandbox overhead that currently adds 13-16 seconds per query.

This would collapse the current complexity of custom JARs, sandbox
tuning, manual metadata sync, and materialized table prerequisites
into a first-class, governed, zero-configuration integration.
-->

---

## UC Table-Level Access Controls: Partial Coverage

- **When queries flow through DBSQL:** UC enforces `SELECT`, column masks, and row filters on federated Neo4j tables
- **An analyst querying `neo4j_catalog.default.person`** sees only the columns and rows their UC role permits
- **But this only covers the SQL path:** access controls apply at the Databricks layer, not inside Neo4j
- **Direct Neo4j access bypasses UC entirely:** a user connecting via Bolt or Cypher Shell sees whatever their Neo4j role permits, regardless of UC grants

<!--
When Neo4j becomes a native UC data source, table-level access
controls give you real governance for the SQL consumption path.
An analyst who queries neo4j_catalog.default.person through DBSQL
is subject to the same SELECT grants, column masks, and row
filters that apply to any other UC-governed table. This is
significant because it means SQL-only teams get governed access
to graph data without any Neo4j-side configuration.

But the coverage stops at the Databricks boundary. A data
scientist connecting directly to Neo4j via Bolt, a Cypher Shell
session, or an MCP agent tool bypasses UC entirely. Their access
is governed by Neo4j's own privilege model, which has no awareness
of UC grants.

This is the gap that authorization sync addresses. UC table-level
controls handle the SQL path. The four patterns in this deck
handle the rest: aligning privileges across both systems so that
a restriction in one is reflected in the other, regardless of
which access path a user takes.
-->

---

# Beyond the SQL Path

What happens when access doesn't flow through Unity Catalog

---

## The Governance Gap

- **Two systems, overlapping data:** UC governs tables, Neo4j governs graph traversal
- **No shared understanding:** a `Person` table and a `:Person` label represent the same concept through different structures
- **Permission granted in one, absent in the other:** users blocked from legitimate work or accessing data they shouldn't
- **Different access semantics:** `SELECT` on rows is not the same as `MATCH` on nodes

<!--
Unity Catalog governs who can query what across the Databricks
Lakehouse. Neo4j governs who can traverse which labels,
relationships, and properties in the graph. When both systems
hold overlapping data, a permission granted in one but absent
in the other creates a governance gap.

A user who can query a materialized Person table in UC but cannot
traverse Person nodes in Neo4j will either be blocked from
legitimate work or will access data they shouldn't. The two
systems have no shared understanding of what their data means.
Bridging this gap requires a common semantic layer.
-->

---

## The Dual Database Architecture

![Fraud Ring Dual Database Architecture](../databricks-in-depth/fraud-ring-dual-architecture.png)

<!--
Consider a financial fraud detection architecture where both
systems hold overlapping customer, account, and transaction data.
The Lakehouse stores customers, accounts, transactions, and
merchants as relational tables optimized for aggregation, time
series analysis, and regulatory reporting. Neo4j stores the same
entities as nodes connected by typed relationships like OWNS,
TRANSFERRED_TO, and PURCHASED_AT, optimized for circular payment
chain detection, fraud ring discovery, and multi-hop traversal.

A Customer is a row in the customers table on the Lakehouse side
and a Customer node with HAS_SSN, HAS_PHONE, and OWNS
relationships on the graph side. Without a shared semantic layer,
every integration between the two systems must rediscover and
re-encode these mappings independently.
-->

---

## What Is a Semantic Layer?

- **Declarative description** of what your data means, placed on top of the data
- **Any consumer shares** a common understanding of how data should be interpreted
- **Two levels of abstraction:** concept layer (business meaning) and metadata layer (physical structures)
- **Built as a graph** connecting business concepts to UC tables and Neo4j labels

<!--
The term "semantic layer" carries many definitions across the
industry. This proposal uses the one from Jesús Barrasa's Going
Meta series: a declarative description of what your data means,
placed on top of the data so that any consumer shares a common
understanding of how it should be interpreted.

In practice this means building a graph that maps business
concepts to their physical representations in both systems. A
concept layer captures business concepts, their relationships,
metrics, dimensions, and business rules. A metadata layer maps
those concepts down to physical structures in each system: UC
tables, columns, and join paths on one side, and Neo4j labels,
relationship types, and properties on the other.
-->

---

## The Semantic Layer Data Model

```
(:Concept {name: "Portfolio"})
    -[:MEASURED_BY]-> (:Metric)
        -[:SOURCED_FROM]-> (:Column)
            <-[:HAS_COLUMN]- (:Table {schema: "neo4j_catalog"})

(:Concept {name: "Portfolio"})
    -[:MAPS_TO]-> (:Label {name: "Portfolio"})   // Neo4j side
```

- **Concept to UC:** Portfolio connects through metrics and columns to `fact_positions`, `dim_account`, `dim_customer`
- **Concept to Neo4j:** Portfolio maps directly to the `:Portfolio` label
- **One definition, two systems:** the graph already knows what "Portfolio" means in both

<!--
A concept like Portfolio connects via MEASURED_BY to a metric,
which connects via SOURCED_FROM to a column, which connects via
HAS_COLUMN to a UC table. The same concept maps to a Neo4j label.
The graph already knows that Portfolio means both Portfolio nodes
in Neo4j and fact_positions joined through dim_account in UC.

This two-layer model is a simplification. Organizations that need
formal taxonomies or OWL-based reasoning can expand the concept
layer into a separate ontology layer and a metrics/rules layer.
The two-layer version is sufficient for the authorization sync
patterns described here.
-->

---

# Proposed Authorization Sync Patterns

Four approaches to aligning privileges across both systems

Different tradeoffs for consistency, operational overhead, and privilege granularity

---

## Pattern 1: Shared Identity Provider

- **Single IdP for both systems:** Okta, Microsoft Entra ID, or Google
- **Group membership drives role assignment** in both systems independently
- **No running sync job:** both systems authenticate against the same provider
- **One-time configuration:** Neo4j admin defines roles and Cypher privileges per IdP group

<!--
The simplest approach avoids a running sync job. Both Databricks
and Neo4j support OIDC-based single sign-on. If both systems
authenticate against the same identity provider, group membership
in the IdP can drive role assignment in both systems independently.

Define groups that reflect data access tiers: graph-analysts,
graph-admins, compliance-team. Map IdP groups to UC roles on the
Databricks side and configure group-to-role mapping in neo4j.conf
on the Neo4j side. When an admin adds a user to graph-analysts
in the IdP, that user gains read access in both UC and Neo4j on
their next authentication.
-->

---

## Pattern 1: UC to Neo4j Privilege Mapping

| UC Concept | Neo4j Equivalent | Example |
|---|---|---|
| Table-level `SELECT` | Label-level `MATCH` | `GRANT MATCH {*} ON GRAPH * NODES Person TO analyst` |
| Column projection | Property-level `READ` | `GRANT READ {name, email} ON GRAPH * NODES Person TO analyst` |
| Row filter | Property-based access control | `GRANT READ {*} ... FOR (n:Account) WHERE n.region = 'EU'` |
| Column mask | Property-level `DENY READ` | `DENY READ {ssn} ON GRAPH * NODES Person TO general_users` |

<!--
This table summarizes how UC privilege concepts map to Neo4j
equivalents. These are the kinds of grants an admin must configure
for each role. The mapping is incomplete in both directions.
Relationships, multi-hop traversal, and PBAC property conditions
have no direct UC equivalent. UC row filters and column masks use
per-table SQL expressions that do not round-trip to Neo4j's
single-property PBAC model.

Property-based access control requires Neo4j 5.12+ Enterprise
Edition or AuraDB Business Critical / Virtual Dedicated Cloud.
-->

---

## Pattern 1: The Mapping Problem

- **A UC table is not a Neo4j label:** `SELECT` returns rows, `MATCH` returns nodes that participate in traversals
- **Relationships have no UC equivalent:** `TRAVERSE` on `:WORKS_AT` controls edge traversal, UC has no concept of this
- **PBAC has no table-side analog:** Neo4j restricts by property value, UC row filters use different syntax and semantics
- **Graph traversal is compositional:** revoking one label mid-chain changes query behavior in non-obvious ways

<!--
Shared identity solves "who is this person?" but not "what can
they access?" The two systems' privilege models operate on
fundamentally different primitives, and an IdP group cannot
encode the mapping between them.

A user with MATCH on Person but not on Account can still discover
that Account nodes exist through relationship endpoints. Granting
"read access to Person data" means something different in each
system. A Cypher query traversing Person to Company to Country
requires privileges on three labels and two relationship types.
No equivalent composition exists in UC's table privilege model.

This pattern fits organizations with coarse-grained access tiers
where the number of distinct policies is small. It falls short as
the graph schema grows and access policies become more granular.
-->

---

## Pattern 2: Shared IdP Plus Semantic Layer

- **Access policies defined at the business concept level**, not per-system
- **Semantic layer encodes the mapping** between business concepts and both privilege models
- **Sync process traverses the graph** to derive system-specific privileges automatically
- **Schema changes propagate** through existing `GOVERNED_BY` relationships

<!--
The mapping problem has a structural solution. The common semantic
layer already encodes the relationship between business concepts,
graph structure, and physical tables. Extending this graph with
access policy nodes creates a single place to define who can
access what, expressed in business terms rather than the privilege
syntax of either system.

Instead of an admin reasoning about UC tables and Neo4j labels
simultaneously, the admin defines access at the concept level and
the graph-driven sync process handles the translation. When the
graph schema changes, the semantic layer update propagates through
existing GOVERNED_BY relationships automatically.
-->

---

## Pattern 2: The Access Policy Model

```cypher
// Define an access policy on a business concept
CREATE (ap:AccessPolicy {name: "portfolio-read", effect: "ALLOW"})

// Link policy to the business concept it governs
MATCH (c:Concept {name: "Portfolio"}), (ap:AccessPolicy {name: "portfolio-read"})
CREATE (c)-[:GOVERNED_BY]->(ap)

// Link policy to the IdP group that holds it
CREATE (g:Group {name: "graph-analysts", provider: "okta"})
CREATE (ap)-[:GRANTED_TO]->(g)
```

<!--
AccessPolicy nodes link to business concepts via GOVERNED_BY and
to IdP groups via GRANTED_TO. A sync process traverses from the
AccessPolicy node through the semantic layer to derive
system-specific privileges for both UC and Neo4j.

For Neo4j, the concept name is the label: the process issues
GRANT MATCH on the corresponding label. For UC, the process
traverses from the concept through MEASURED_BY, SOURCED_FROM,
and HAS_COLUMN to discover every UC table and column the concept
touches, then issues GRANT SELECT on those tables.

Relationship privileges also become derivable. If the semantic
layer encodes that Customer connects to Portfolio via :holds,
and both concepts share an access policy, the sync process can
grant TRAVERSE on the connecting relationship type.
-->

---

## Pattern 2: Deriving Privileges from the Graph

```cypher
// Derive UC tables that require SELECT for a given access policy
MATCH (ap:AccessPolicy {name: "portfolio-read"})<-[:GOVERNED_BY]-(c:Concept)
MATCH (c)-[:MEASURED_BY]->(m:Metric)-[:SOURCED_FROM]->(col:Column)
      <-[:HAS_COLUMN]-(t:Table)
RETURN DISTINCT t.name AS uc_table, COLLECT(col.name) AS columns

// Derive Neo4j label privileges for the same policy
MATCH (ap:AccessPolicy {name: "portfolio-read"})<-[:GOVERNED_BY]-(c:Concept)
RETURN c.name AS neo4j_label
```

- **One policy definition** produces grants for both systems
- **Cross-boundary conflicts** surface as flagged edges, not silent misconfigurations

<!--
Starting from an AccessPolicy node, the sync process walks
GOVERNED_BY back to the business concept, then branches. For UC,
it traverses through metrics and columns to discover every table
that needs a SELECT grant. For Neo4j, the concept name maps
directly to the label.

PBAC rules can be encoded as AccessCondition nodes linked to the
policy. A condition like region equals EU on Portfolio translates
to both a Neo4j PBAC rule on Portfolio nodes and a UC row filter
on the materialized table. The semantic layer provides the column
name and the table it lives on, so the sync process can generate
both commands.
-->

---

## Pattern 3: UC as Source of Truth, Push to Neo4j

1. **Read UC privilege state:** query `INFORMATION_SCHEMA.TABLE_PRIVILEGES` for materialized Neo4j tables
2. **Map UC grants to Neo4j privileges:** `SELECT` on table `person` becomes `GRANT MATCH {*} ON GRAPH * NODES Person`
3. **Apply to Neo4j:** connect via Bolt, execute Cypher admin commands against the system database
4. **Detect drift:** compare Neo4j privilege state against desired state on each run, revoke stale grants

<!--
When UC is the governance hub and Neo4j privileges must mirror UC
grants, a scheduled sync job polls UC's permission state and
issues Cypher admin commands to align Neo4j.

The mapping requires a naming convention linking UC table names to
Neo4j labels. If the materialization process names tables after
their source labels, the table-level mapping is direct. Column-level
control requires a second step: inspect column masks and translate
each mask's intent into property-level GRANT READ or DENY READ.
This translation is lossy because a UC column mask can wrap a
value in an arbitrary SQL expression while Neo4j's DENY READ can
only hide the property outright.

Configure Neo4j to authenticate via OIDC but resolve authorization
locally, so Cypher GRANT/REVOKE statements remain the sole source
of role assignments.
-->

---

## Pattern 3: The Sync Job

```python
with GraphDatabase.driver(NEO4J_BOLT_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
    with driver.session(database="system") as session:
        session.run("CREATE ROLE uc_analyst IF NOT EXISTS")
        session.run("GRANT MATCH {*} ON GRAPH * NODES Person TO uc_analyst")
        session.run("GRANT MATCH {*} ON GRAPH * NODES Company TO uc_analyst")
        session.run("DENY READ {ssn} ON GRAPH * NODES Person TO uc_analyst")
```

- **Eventually consistent:** bounded by the job schedule
- **Fits when:** UC is the established governance layer and Neo4j is downstream

<!--
The sync process runs as a Databricks job on a schedule. It reads
UC's privilege state from INFORMATION_SCHEMA.TABLE_PRIVILEGES,
maps those grants to Neo4j equivalents using the naming convention,
connects via Bolt using an admin credential, and issues the
derived Cypher admin commands.

On each run, it compares the current Neo4j privilege state via
SHOW ROLE privileges against the desired state derived from UC.
Privileges that no longer have a corresponding UC grant are
revoked. All changes are logged for audit.

The consistency window is bounded by the job schedule. A privilege
revoked in UC remains active in Neo4j until the next sync run.
For sensitive data, this window may be unacceptable.
-->

---

## Pattern 4: Neo4j as Source of Truth, Push to UC

1. **Read Neo4j privilege state:** execute `SHOW PRIVILEGES` via Cypher for `TRAVERSE`, `READ`, `MATCH`
2. **Map Neo4j privileges to UC grants:** `MATCH` on `:Person` becomes `GRANT SELECT ON TABLE neo4j_catalog.default.person`
3. **Apply to UC:** execute `GRANT`/`REVOKE` via Statement Execution API or SQL warehouse connection
4. **Column masks for property denials:** `DENY READ {ssn}` becomes `ALTER TABLE ... ALTER COLUMN ... SET MASK`

<!--
The reverse flow applies when graph administrators define access
at the label and property level and UC privileges on materialized
tables should reflect those decisions. The same naming convention
applies in reverse.

This pattern fits graph-centric architectures where the Neo4j DBA
defines the access model and materialized tables in UC are
read-only projections that should inherit the graph's access
policies.

UC's privilege model is richer in some dimensions (row filters,
column masks, fine-grained sharing) and less expressive in others
(no equivalent to Neo4j's PBAC property-value conditions). The
mapping is lossy in both directions.
-->

---

## Choosing a Pattern

| Consideration | Pattern 1: Shared IdP | Pattern 2: IdP + Semantic Layer | Pattern 3: UC to Neo4j | Pattern 4: Neo4j to UC |
|---|---|---|---|---|
| Sync job required | No | Yes | Yes | Yes |
| Source of truth | Identity provider | Semantic layer graph | Unity Catalog | Neo4j |
| Consistency | Immediate (on auth) | Eventually consistent | Eventually consistent | Eventually consistent |
| Property-level control | Manual Neo4j config | Derived from semantic layer | Via UC column masks (lossy) | Via generated UC column masks |
| Relationship privileges | Manual Neo4j config | Derived from semantic layer edges | No natural mapping | No natural mapping |
| Operational overhead | Low | Medium | Medium | Medium |

<!--
Pattern 1 works for coarse-grained access tiers where the number
of distinct policies is small. When access policies become
granular per-label or per-property, Pattern 2 absorbs the mapping
complexity that would otherwise fall on the admin.

Patterns 3 and 4 are viable when only one system's privileges
need to drive the other, but they struggle with relationship
privileges and PBAC because the target system lacks equivalent
primitives. Pattern 2 handles this by deriving system-appropriate
privileges from a shared concept model rather than translating
one system's privilege syntax into another's.
-->

---

## The External Metadata API: Visibility Without Enforcement

- **Registers Neo4j labels and relationships** as metadata objects in Unity Catalog
- **Supports `BROWSE`, `MODIFY`, `MANAGE`:** controls who can see and manage the metadata registration
- **Does not propagate to Neo4j:** granting `BROWSE` on a `:Person` metadata object does not grant `TRAVERSE` on `:Person` nodes
- **No permission change events:** both systems require polling, neither offers push-based webhooks

<!--
The External Metadata API registers Neo4j node labels and
relationship types as metadata objects in Unity Catalog. This is
useful for discoverability and lineage tracking, but the API's
privilege model stops at the metadata objects themselves.

Two constraints rule out a metadata-API-driven approach to
authorization sync. Neither UC nor Neo4j offers push-based
webhooks when privileges change. UC records updatePermissions
events in system.access.audit but these must be polled. Neo4j
writes security events to audit log files with no event stream.
And the API has no concept of mapping a UC privilege to an
external system action.

The API does remain valuable as part of the broader governance
picture. The metadata objects make Neo4j labels visible in UC's
lineage graph. The patterns above provide the enforcement layer.
-->

---

## Authorization Sync: The Combined Picture

- **Pattern 1 (Shared IdP):** simplest, no sync job, but manual mapping and coarse-grained
- **Pattern 2 (Semantic Layer):** graph-derived privileges, handles relationships and PBAC, requires semantic layer maintenance
- **Pattern 3 (UC to Neo4j):** UC-governed environments, scheduled push, lossy on column masks
- **Pattern 4 (Neo4j to UC):** graph-governed environments, scheduled push, lossy on PBAC
- **Semantic layer** relocates complexity from admin reasoning to graph traversal

<!--
The four patterns form a spectrum from simple to comprehensive.
Pattern 1 is the starting point for organizations that already
centralize identity management and can express access as coarse
group membership. Pattern 2 is the most complete solution but
requires building and maintaining the semantic layer. Patterns 3
and 4 fit when one system clearly owns the privilege model and
the other should follow.

The semantic layer is the key architectural decision. It serves
authorization sync, but also powers semantic search, metric
lineage, and data discovery across both platforms. The
authorization patterns build on that foundation.
-->
