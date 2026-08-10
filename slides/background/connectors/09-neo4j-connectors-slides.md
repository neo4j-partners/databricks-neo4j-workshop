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

# Neo4j Connectors in Depth

Reference material for the connection patterns the workshop names but does not build

<!--
This is a background deck. Deck 3's Connection Patterns slide lists
five connectors by platform stage. Two of them, the Neo4j Custom JDBC
Unity Catalog Connector and the Virtual Graph, are production patterns that no lab
touches. This deck is where those two are covered in full.

Use it when someone asks the question, not as part of the main run.
-->

---

## Neo4j Custom JDBC Unity Catalog Connector

- **SQL over the graph:** joined with Delta tables in one query, and nothing moves
- **Setup:** upload the connector to a UC Volume, register Neo4j as a JDBC connection
- **The driver rewrites SQL as Cypher:** `SELECT COUNT(*) FROM Aircraft` arrives as `MATCH (n:Aircraft) RETURN count(n)`. Node labels behave like tables
- **`remote_query`:** runs Cypher inside Neo4j and hands the rows back as a table
- **Puts graph data in Power BI, Tableau and Genie Agents** with nobody learning a second language
- **Public Preview:** custom-driver JDBC reached Public Preview at Runtime 18.1

<!--
SQL Federation is the one that moves nothing, and it is for the
analyst who knows SQL and has never written Cypher. Upload the Neo4j
Custom JDBC Unity Catalog Connector to a UC Volume, register Neo4j as a JDBC
connection, and the driver rewrites SQL as Cypher on the way in.
SELECT COUNT(*) FROM Aircraft arrives at the graph as MATCH
(n:Aircraft) RETURN count(n). Node labels behave like tables.

The remote_query function is how you call it. It runs the query
inside Neo4j and hands the rows back as a table, so one statement can
join graph results to Delta tables. That is what puts graph data in
Power BI, Tableau and Genie Agents with nobody learning a second language.

Custom-driver JDBC reached Public Preview at Runtime 18.1. No lab
builds this. It is on the slide so you know the option exists.
-->

---

## Neo4j Virtual Graph

- **A composite, logical view** rather than a second copy of the data
- **Silver and Gold tables project into it,** no batch load required
- **Composite graphs stitch** the materialized graph and the lakehouse tables into one queryable surface
- **The agent does not need to know where a property lives:** a Cypher question does not care which side it physically sits on
- **A production pattern, not a workshop lab**

<!--
The Neo4j Virtual Graph is a composite, logical view rather than a
second copy of the data. Silver and Gold tables project into it, and
composite graphs stitch the materialized graph and the lakehouse
tables into one queryable surface. An agent asking a Cypher question
does not need to know which side a given property physically lives
on.

This workshop's graph is a direct load, not a virtual projection, so
none of this appears in a lab. It is where a team takes the pattern
once they operate at enterprise scale.
-->

---

![bg contain](../../databricks-in-depth/spark-connector-virtual-graph.png)

<!--
This diagram shows a production pattern, not this workshop's build. No
lab here creates a Neo4j Virtual Graph or composite graphs.

This is where a team takes the workshop's pattern once they operate
at enterprise scale, so read it as "later," not "Lab 2." The
Medallion Architecture with Neo4j attached to it. Structured and
unstructured sources land in Bronze as raw staging. Bronze feeds
Silver, the cleaned and conformed Delta tables, and Silver is the
layer everything else reads from.

Two arrows leave Silver. The Neo4j Spark Connector batch-loads Silver
tables into the Neo4j Enterprise Knowledge Graph as nodes and
relationships. The dashed arrow coming back is graph enrichment:
algorithm results, community scores, and derived relationships
written back into Silver so they become ordinary columns other
consumers can join on. That round trip is the point. Silver feeds the
graph, the graph feeds Silver.

Silver also flows down to Gold, the curated business analytics layer.

The Neo4j Virtual Graph on the lower right is a composite, logical
view rather than a second copy of the data. Silver and Gold tables
project into it, and the dashed line from the Enterprise Knowledge
Graph shows composite graphs stitching the materialized graph and the
lakehouse tables into one queryable surface. An agent asking a Cypher
question does not need to know which side a given property physically
lives on. This workshop's graph is a direct load, not a virtual
projection, so none of this appears again until you take the pattern
into production.
-->
