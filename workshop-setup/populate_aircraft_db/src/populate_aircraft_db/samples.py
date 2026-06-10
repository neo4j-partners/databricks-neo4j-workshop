"""Sample queries showcasing the Aircraft Digital Twin knowledge graph."""

from __future__ import annotations

from neo4j import Driver

_W = 70
_EXTRACTED_LABELS = ["OperatingLimit"]
_VECTOR_INDEX = "maintenanceChunkEmbeddings"
_FULLTEXT_INDEX = "maintenanceChunkText"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _header(title: str, description: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'=' * _W}")
    print(f"\n  {description}\n")


def _cypher(query: str) -> None:
    lines = query.strip().splitlines()
    indents = [len(ln) - len(ln.lstrip()) for ln in lines if ln.strip()]
    base = min(indents) if indents else 0
    print("  Cypher:")
    for ln in lines:
        print(f"    {ln[base:]}")
    print()


def _table(headers: list[str], rows: list[list], widths: list[int] | None = None) -> None:
    if not rows:
        print("  (no results)\n")
        return
    if widths is None:
        widths = []
        for i, h in enumerate(headers):
            col_max = len(h)
            for row in rows:
                col_max = max(col_max, len(str(row[i] if i < len(row) else "")))
            widths.append(min(col_max + 1, 50))
    print("  " + "  ".join(h.ljust(w) for h, w in zip(headers, widths, strict=False)))
    print("  " + "  ".join("\u2500" * w for w in widths))
    for row in rows:
        cells = []
        for val, w in zip(row, widths, strict=False):
            s = str(val) if val is not None else "\u2014"
            if len(s) > w:
                s = s[: w - 1] + "\u2026"
            cells.append(s.ljust(w))
        print("  " + "  ".join(cells))
    print()


def _val(v, max_len: int = 0) -> str:
    s = str(v) if v is not None else "\u2014"
    if max_len and len(s) > max_len:
        s = s[: max_len - 1] + "\u2026"
    return s


# ---------------------------------------------------------------------------
# 1. Aircraft Fleet (shows all — not limited by sample_size)
# ---------------------------------------------------------------------------

_FLEET_Q = """\
MATCH (a:Aircraft)
OPTIONAL MATCH (a)-[:HAS_SYSTEM]->(s:System)
OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(c:Component)
WITH a, count(DISTINCT s) AS systems, count(DISTINCT c) AS components
RETURN a.tail_number AS tail, a.model AS model,
       a.manufacturer AS mfr, systems, components
ORDER BY a.tail_number"""


def _aircraft_fleet(driver: Driver) -> None:
    _header(
        "1. Aircraft Fleet Overview",
        "Each aircraft with its model, manufacturer, and system/component counts.",
    )
    _cypher(_FLEET_Q)
    rows, _, _ = driver.execute_query(_FLEET_Q)
    _table(
        ["Tail #", "Model", "Manufacturer", "Systems", "Components"],
        [[r["tail"], r["model"], r["mfr"], r["systems"], r["components"]] for r in rows],
    )


# ---------------------------------------------------------------------------
# 2. System-Component hierarchy (shows one aircraft — structural limit)
# ---------------------------------------------------------------------------

_HIERARCHY_Q = """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)-[:HAS_COMPONENT]->(c:Component)
WITH a, s, c ORDER BY s.name, c.name
WITH a, s, collect(c.name) AS comps ORDER BY s.name
WITH a, collect({system: s.name, components: comps}) AS systems
RETURN a.tail_number AS tail, a.model AS model, systems
LIMIT 1"""


def _system_hierarchy(driver: Driver) -> None:
    _header(
        "2. System \u2192 Component Hierarchy",
        "Full hierarchy for one aircraft showing Systems and their Components.",
    )
    _cypher(_HIERARCHY_Q)
    rows, _, _ = driver.execute_query(_HIERARCHY_Q)
    if not rows:
        print("  (no results)\n")
        return
    r = rows[0]
    print(f"  Aircraft {r['tail']} ({r['model']})")
    systems = r["systems"]
    for i, sys in enumerate(systems):
        last_sys = i == len(systems) - 1
        print(f"  {'└── ' if last_sys else '├── '}{sys['system']}")
        for j, comp in enumerate(sys["components"]):
            branch = "    " if last_sys else "│   "
            leaf = "└── " if j == len(sys["components"]) - 1 else "├── "
            print(f"  {branch}{leaf}{comp}")
    print()


# ---------------------------------------------------------------------------
# 3. Flight network
# ---------------------------------------------------------------------------

_FLIGHTS_Q = """\
MATCH (f:Flight)-[:DEPARTS_FROM]->(dep:Airport),
      (f)-[:ARRIVES_AT]->(arr:Airport)
WITH dep.iata AS origin, arr.iata AS dest, count(f) AS flights
RETURN origin, dest, flights
ORDER BY flights DESC
LIMIT $limit"""


def _flight_operations(driver: Driver, limit: int) -> None:
    _header(
        "3. Flight Operations \u2014 Top Routes",
        "Most frequent routes by flight count.",
    )
    _cypher(_FLIGHTS_Q)
    rows, _, _ = driver.execute_query(_FLIGHTS_Q, limit=limit)
    _table(
        ["Origin", "Dest", "Flights"],
        [[r["origin"], r["dest"], r["flights"]] for r in rows],
    )


# ---------------------------------------------------------------------------
# 4. Maintenance events
# ---------------------------------------------------------------------------

_MAINT_Q = """\
MATCH (me:MaintenanceEvent)-[:AFFECTS_AIRCRAFT]->(a:Aircraft)
WHERE me.reported_at IS NOT NULL
OPTIONAL MATCH (me)-[:AFFECTS_SYSTEM]->(s:System)
RETURN a.tail_number AS aircraft, me.event_id AS event,
       me.reported_at AS date, me.severity AS severity, me.fault AS fault,
       s.name AS system
ORDER BY me.reported_at DESC
LIMIT $limit"""


def _maintenance_events(driver: Driver, limit: int) -> None:
    _header(
        "4. Maintenance Events",
        "Recent maintenance events with fault codes and affected systems.",
    )
    _cypher(_MAINT_Q)
    rows, _, _ = driver.execute_query(_MAINT_Q, limit=limit)
    _table(
        ["Aircraft", "Event ID", "Date", "Severity", "Fault", "System"],
        [
            [
                r["aircraft"],
                r["event"],
                _val(r["date"])[:10],
                r["severity"],
                _val(r["fault"], 20),
                _val(r["system"]),
            ]
            for r in rows
        ],
    )


# ---------------------------------------------------------------------------
# 5. Sensors
# ---------------------------------------------------------------------------

_SENSORS_Q = """\
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(sys:System)-[:HAS_SENSOR]->(s:Sensor)
RETURN a.tail_number AS aircraft, sys.name AS system,
       s.sensor_id AS sensor, s.type AS type, s.unit AS unit
ORDER BY a.tail_number, sys.name
LIMIT $limit"""


def _sensors(driver: Driver, limit: int) -> None:
    _header(
        "5. Sensors",
        "Sensors installed across the fleet with their type and unit.",
    )
    _cypher(_SENSORS_Q)
    rows, _, _ = driver.execute_query(_SENSORS_Q, limit=limit)
    _table(
        ["Aircraft", "System", "Sensor ID", "Type", "Unit"],
        [[r["aircraft"], r["system"], r["sensor"], r["type"], r["unit"]] for r in rows],
    )


# ---------------------------------------------------------------------------
# 6. Document-Chunk structure
# ---------------------------------------------------------------------------

_DOCS_Q = """\
MATCH (d:Document)
OPTIONAL MATCH (d)<-[:FROM_DOCUMENT]-(c:Chunk)
WITH d, count(c) AS chunks,
     sum(CASE WHEN c.embedding IS NOT NULL THEN 1 ELSE 0 END) AS embedded
RETURN d.documentId AS doc_id, d.aircraftType AS aircraft,
       d.title AS title, chunks, embedded
ORDER BY d.documentId"""

_CHAIN_Q = """\
MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
WHERE c.index IS NOT NULL
WITH d, c ORDER BY d.documentId, c.index
WITH d, c LIMIT $limit
OPTIONAL MATCH (c)-[:NEXT_CHUNK]->(next:Chunk)
RETURN d.documentId AS doc, c.index AS idx,
       substring(c.text, 0, 60) AS preview,
       next.index AS next_idx"""


def _document_chunks(driver: Driver, limit: int) -> None:
    _header(
        "6. Document-Chunk Structure",
        "Maintenance manuals loaded as Document \u2192 Chunk graphs with embedding stats.",
    )
    _cypher(_DOCS_Q)
    rows, _, _ = driver.execute_query(_DOCS_Q)
    if not rows:
        print("  (no documents \u2014 run 'setup' first)\n")
        return
    _table(
        ["Document ID", "Aircraft", "Chunks", "Embedded"],
        [[r["doc_id"], r["aircraft"], r["chunks"], r["embedded"]] for r in rows],
    )

    print(f"  Chunk chain (first {limit}):\n")
    _cypher(_CHAIN_Q)
    rows, _, _ = driver.execute_query(_CHAIN_Q, limit=limit)
    for r in rows:
        arrow = f" \u2192 Chunk {r['next_idx']}" if r["next_idx"] is not None else " (end)"
        print(f"    Chunk {r['idx']:>3} \u2502 {r['preview']}\u2026{arrow}")
    print()


# ---------------------------------------------------------------------------
# 7. Extracted entities
# ---------------------------------------------------------------------------

_ENTITIES_Q = """\
UNWIND $labels AS label
CALL (label) {
    MATCH (n) WHERE label IN labels(n)
    RETURN n.name AS name
    LIMIT $limit
}
RETURN label AS entity_type, collect(name) AS samples"""


def _extracted_entities(driver: Driver, limit: int) -> None:
    _header(
        "7. Extracted Entities",
        "Entity types extracted from maintenance manuals via SimpleKGPipeline.",
    )
    _cypher(_ENTITIES_Q)
    rows, _, _ = driver.execute_query(_ENTITIES_Q, labels=_EXTRACTED_LABELS, limit=limit)
    if not rows or all(len(r["samples"]) == 0 for r in rows):
        print("  (no extracted entities \u2014 run 'setup' first)\n")
        return
    for r in rows:
        names = r["samples"]
        if names:
            print(f"  {r['entity_type']}:")
            for name in names:
                print(f"    \u2022 {name}")
        else:
            print(f"  {r['entity_type']}: (none)")
    print()


# ---------------------------------------------------------------------------
# 8. Cross-links
# ---------------------------------------------------------------------------

_CROSSLINKS = [
    (
        "Document \u2192 Aircraft",
        """\
MATCH (d:Document)-[:APPLIES_TO]->(a:Aircraft)
RETURN d.title AS source, a.tail_number AS target
LIMIT $limit""",
        ["Document", "Aircraft"],
    ),
    (
        "Sensor \u2192 OperatingLimit",
        """\
MATCH (s:Sensor)-[:HAS_LIMIT]->(ol:OperatingLimit)
RETURN s.sensor_id AS source, ol.name AS target
LIMIT $limit""",
        ["Sensor", "OperatingLimit"],
    ),
    (
        "Provenance (OperatingLimit \u2192 Chunk \u2192 Document \u2192 Aircraft)",
        """\
MATCH (ol:OperatingLimit)-[:FROM_CHUNK]->(c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
      -[:APPLIES_TO]->(a:Aircraft)
RETURN ol.name AS source, substring(c.text, 0, 60) AS chunk,
       a.tail_number AS target
LIMIT $limit""",
        ["OperatingLimit", "Source Chunk", "Aircraft"],
    ),
]


def _cross_links(driver: Driver, limit: int) -> None:
    _header(
        "8. Cross-Links: Knowledge Graph \u2194 Operational Graph",
        "Relationships connecting extracted entities to the operational aircraft graph.",
    )
    any_results = False
    for title, query, headers in _CROSSLINKS:
        print(f"  {title}:")
        _cypher(query)
        rows, _, _ = driver.execute_query(query, limit=limit)
        if not rows:
            print("  (none)\n")
            continue
        any_results = True
        keys = list(rows[0].keys())
        _table(headers, [[r[k] for k in keys] for r in rows])
    if not any_results:
        print("  (no cross-links \u2014 run 'setup' first)\n")


# ---------------------------------------------------------------------------
# 9. Vector similarity search (no API key needed)
# ---------------------------------------------------------------------------

_VECTOR_Q = """\
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
CALL db.index.vector.queryNodes(
    'maintenanceChunkEmbeddings', $top_k, seed.embedding
) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT $limit
RETURN substring(seed.text, 0, 100) AS seed_text,
       score AS similarity,
       substring(node.text, 0, 100) AS match_text"""


def _vector_similarity(driver: Driver, limit: int) -> None:
    _header(
        "9. Vector Similarity Search",
        "Picks a random chunk and finds the most similar chunks using the\n"
        "  vector index (reuses stored embeddings \u2014 no API key needed).",
    )
    _cypher(_VECTOR_Q)
    try:
        rows, _, _ = driver.execute_query(_VECTOR_Q, limit=limit, top_k=limit + 1)
    except Exception:
        print("  (vector index not available \u2014 run 'setup' first)\n")
        return
    if not rows:
        print("  (no chunks with embeddings \u2014 run 'setup' first)\n")
        return
    print(f"  Seed: \"{rows[0]['seed_text']}\u2026\"\n")
    print(f"  {'Score':<8}  Similar chunk")
    print("  " + "\u2500" * 8 + "  " + "\u2500" * 56)
    for r in rows:
        print(f"  {r['similarity']:.4f}    {r['match_text']}\u2026")
    print()


# ---------------------------------------------------------------------------
# 10. Full-text search (Lab 3 — keyword search via fulltext index)
# ---------------------------------------------------------------------------

_FULLTEXT_Q = """\
CALL db.index.fulltext.queryNodes($index, $query) YIELD node, score
RETURN score,
       node.index AS chunk_idx,
       substring(node.text, 0, 120) AS preview
ORDER BY score DESC
LIMIT $limit"""


def _fulltext_search(driver: Driver, limit: int) -> None:
    _header(
        "10. Full-Text Search",
        "Keyword search over maintenance chunks using the fulltext index.\n"
        "  This mirrors the HybridRetriever's keyword component from Lab 3.",
    )
    search_terms = ["engine vibration", "hydraulic pressure", "EGT exceedance"]
    for term in search_terms:
        print(f"  Search: \"{term}\"")
        _cypher(_FULLTEXT_Q)
        try:
            rows, _, _ = driver.execute_query(
                _FULLTEXT_Q, index=_FULLTEXT_INDEX, query=term, limit=limit,
            )
        except Exception:
            print("  (fulltext index not available \u2014 run 'setup' first)\n")
            return
        if not rows:
            print("  (no results)\n")
            continue
        _table(
            ["Score", "Chunk", "Preview"],
            [[f"{r['score']:.4f}", r["chunk_idx"], _val(r["preview"], 80)] for r in rows],
        )


# ---------------------------------------------------------------------------
# 11. Vector search with document context (Lab 3 — VectorCypherRetriever)
# ---------------------------------------------------------------------------

_VECTOR_DOC_Q = """\
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
CALL db.index.vector.queryNodes(
    $index, $top_k, seed.embedding
) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT $limit
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
RETURN substring(seed.text, 0, 80) AS seed_text,
       score AS similarity,
       doc.documentId AS doc_id,
       doc.aircraftType AS aircraft_type,
       node.index AS chunk_idx,
       substring(node.text, 0, 80) AS match_text"""


def _vector_document_context(driver: Driver, limit: int) -> None:
    _header(
        "11. Vector Search \u2192 Document Context",
        "Semantic search enriched with source document metadata.\n"
        "  Mirrors the VectorCypherRetriever document-context pattern from Lab 3.",
    )
    _cypher(_VECTOR_DOC_Q)
    try:
        rows, _, _ = driver.execute_query(
            _VECTOR_DOC_Q, index=_VECTOR_INDEX, limit=limit, top_k=limit + 1,
        )
    except Exception:
        print("  (vector index not available \u2014 run 'setup' first)\n")
        return
    if not rows:
        print("  (no chunks with embeddings \u2014 run 'setup' first)\n")
        return
    print(f"  Seed: \"{rows[0]['seed_text']}\u2026\"\n")
    _table(
        ["Score", "Doc ID", "Aircraft", "Chunk", "Preview"],
        [
            [
                f"{r['similarity']:.4f}",
                r["doc_id"],
                _val(r["aircraft_type"]),
                r["chunk_idx"],
                _val(r["match_text"], 50),
            ]
            for r in rows
        ],
    )


# ---------------------------------------------------------------------------
# 12. Adjacent chunk retrieval (Lab 3 — VectorCypherRetriever + NEXT_CHUNK)
# ---------------------------------------------------------------------------

_ADJACENT_Q = """\
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
CALL db.index.vector.queryNodes(
    $index, $top_k, seed.embedding
) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT $limit
OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(node)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
RETURN substring(seed.text, 0, 80) AS seed_text,
       score AS similarity,
       doc.documentId AS doc_id,
       node.index AS chunk_idx,
       prev.index AS prev_idx,
       next.index AS next_idx,
       substring(node.text, 0, 80) AS match_text"""


def _adjacent_chunks(driver: Driver, limit: int) -> None:
    _header(
        "12. Adjacent Chunk Retrieval",
        "Vector search with surrounding context via NEXT_CHUNK traversal.\n"
        "  Mirrors the VectorCypherRetriever adjacent-chunks pattern from Lab 3.",
    )
    _cypher(_ADJACENT_Q)
    try:
        rows, _, _ = driver.execute_query(
            _ADJACENT_Q, index=_VECTOR_INDEX, limit=limit, top_k=limit + 1,
        )
    except Exception:
        print("  (vector index not available \u2014 run 'setup' first)\n")
        return
    if not rows:
        print("  (no chunks with embeddings \u2014 run 'setup' first)\n")
        return
    print(f"  Seed: \"{rows[0]['seed_text']}\u2026\"\n")
    for r in rows:
        prev = f"Chunk {r['prev_idx']}" if r["prev_idx"] is not None else "\u2014"
        nxt = f"Chunk {r['next_idx']}" if r["next_idx"] is not None else "\u2014"
        print(
            f"  {r['similarity']:.4f}  "
            f"[{prev} \u2190] Chunk {r['chunk_idx']} [\u2192 {nxt}]  "
            f"{r['match_text']}\u2026"
        )
    print()


# ---------------------------------------------------------------------------
# 13. Vector search → Aircraft topology (Lab 3 — system connection pattern)
# ---------------------------------------------------------------------------

_VECTOR_TOPO_Q = """\
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
CALL db.index.vector.queryNodes(
    $index, $top_k, seed.embedding
) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT $limit
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
CALL (node) {
    MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System)
    WHERE
        (node.text CONTAINS 'Engine' AND s.name CONTAINS 'Engine') OR
        (node.text CONTAINS 'Avionics' AND s.name CONTAINS 'Avionics') OR
        (node.text CONTAINS 'Hydraulic' AND s.name CONTAINS 'Hydraulic')
    RETURN a.tail_number AS tail, s.name AS sys_name
    LIMIT 3
}
RETURN substring(seed.text, 0, 80) AS seed_text,
       score AS similarity,
       doc.documentId AS doc_id,
       node.index AS chunk_idx,
       tail AS aircraft,
       sys_name AS system,
       substring(node.text, 0, 60) AS match_text"""


def _vector_topology(driver: Driver, limit: int) -> None:
    _header(
        "13. Vector Search \u2192 Aircraft Topology",
        "Semantic search connected to the operational graph (Aircraft \u2192 System).\n"
        "  Mirrors the VectorCypherRetriever system-context pattern from Lab 3.",
    )
    _cypher(_VECTOR_TOPO_Q)
    try:
        rows, _, _ = driver.execute_query(
            _VECTOR_TOPO_Q, index=_VECTOR_INDEX, limit=limit, top_k=limit + 1,
        )
    except Exception:
        print("  (vector index not available \u2014 run 'setup' first)\n")
        return
    if not rows:
        print("  (no topology connections found \u2014 run 'setup' first)\n")
        return
    print(f"  Seed: \"{rows[0]['seed_text']}\u2026\"\n")
    _table(
        ["Score", "Aircraft", "System", "Doc", "Chunk", "Preview"],
        [
            [
                f"{r['similarity']:.4f}",
                _val(r["aircraft"]),
                _val(r["system"]),
                r["doc_id"],
                r["chunk_idx"],
                _val(r["match_text"], 40),
            ]
            for r in rows
        ],
    )


# ---------------------------------------------------------------------------
# 14. Hybrid search comparison (Lab 3 — vector vs fulltext side-by-side)
# ---------------------------------------------------------------------------

_HYBRID_VECTOR_Q = """\
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
CALL db.index.vector.queryNodes(
    $index, $top_k, seed.embedding
) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT $limit
RETURN 'vector' AS method,
       substring(seed.text, 0, 80) AS seed_text,
       score AS score,
       node.index AS chunk_idx,
       substring(node.text, 0, 80) AS match_text"""

_HYBRID_FT_Q = """\
MATCH (seed:Chunk)
WHERE seed.embedding IS NOT NULL AND seed.text IS NOT NULL
WITH seed, rand() AS r ORDER BY r LIMIT 1
WITH seed,
     reduce(s = seed.text, x IN ['\\n', '.', ',', ':', ';'] |
         replace(s, x, ' ')) AS raw
WITH seed,
     [w IN split(raw, ' ') WHERE size(w) > 4] AS words
WITH seed, words[0..5] AS kw
WITH seed, reduce(s = '', w IN kw | s + ' ' + w) AS query_str
CALL db.index.fulltext.queryNodes($ft_index, query_str) YIELD node, score
WHERE node <> seed
WITH seed, node, score ORDER BY score DESC LIMIT $limit
RETURN 'fulltext' AS method,
       substring(seed.text, 0, 80) AS seed_text,
       score AS score,
       node.index AS chunk_idx,
       substring(node.text, 0, 80) AS match_text"""


def _hybrid_comparison(driver: Driver, limit: int) -> None:
    _header(
        "14. Hybrid Search Comparison",
        "Side-by-side vector vs fulltext results for the same seed chunk.\n"
        "  Demonstrates why Lab 3's HybridRetriever combines both approaches.",
    )

    # --- Vector results ---
    print("  [A] Vector similarity results:")
    _cypher(_HYBRID_VECTOR_Q)
    try:
        v_rows, _, _ = driver.execute_query(
            _HYBRID_VECTOR_Q, index=_VECTOR_INDEX, limit=limit, top_k=limit + 1,
        )
    except Exception:
        print("  (vector index not available \u2014 run 'setup' first)\n")
        return
    if v_rows:
        print(f"  Seed: \"{v_rows[0]['seed_text']}\u2026\"\n")
        _table(
            ["Method", "Score", "Chunk", "Preview"],
            [[r["method"], f"{r['score']:.4f}", r["chunk_idx"], _val(r["match_text"], 50)] for r in v_rows],
        )
    else:
        print("  (no results)\n")

    # --- Fulltext results ---
    print("  [B] Fulltext keyword results:")
    _cypher(_HYBRID_FT_Q)
    try:
        ft_rows, _, _ = driver.execute_query(
            _HYBRID_FT_Q, ft_index=_FULLTEXT_INDEX, limit=limit,
        )
    except Exception:
        print("  (fulltext index not available \u2014 run 'setup' first)\n")
        return
    if ft_rows:
        print(f"  Seed: \"{ft_rows[0]['seed_text']}\u2026\"\n")
        _table(
            ["Method", "Score", "Chunk", "Preview"],
            [[r["method"], f"{r['score']:.4f}", r["chunk_idx"], _val(r["match_text"], 50)] for r in ft_rows],
        )
    else:
        print("  (no results)\n")

    # --- Summary ---
    v_ids = {r["chunk_idx"] for r in v_rows} if v_rows else set()
    ft_ids = {r["chunk_idx"] for r in ft_rows} if ft_rows else set()
    overlap = v_ids & ft_ids
    print(f"  Overlap: {len(overlap)} chunk(s) in both result sets")
    if overlap:
        print(f"  Shared chunks: {sorted(overlap)}")
    print(f"  Vector-only: {len(v_ids - ft_ids)} | Fulltext-only: {len(ft_ids - v_ids)}")
    print()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_all_samples(driver: Driver, sample_size: int = 10) -> None:
    """Run all sample queries with formatted output."""
    print(f"\n{'#' * _W}")
    print("  Aircraft Digital Twin \u2014 Sample Queries")
    print(f"{'#' * _W}")
    print(f"\n  Sample size: {sample_size} rows per section\n")

    _aircraft_fleet(driver)
    _system_hierarchy(driver)
    _flight_operations(driver, sample_size)
    _maintenance_events(driver, sample_size)
    _sensors(driver, sample_size)
    _document_chunks(driver, sample_size)
    _extracted_entities(driver, sample_size)
    _cross_links(driver, sample_size)
    _vector_similarity(driver, sample_size)
    _fulltext_search(driver, sample_size)
    _vector_document_context(driver, sample_size)
    _adjacent_chunks(driver, sample_size)
    _vector_topology(driver, sample_size)
    _hybrid_comparison(driver, sample_size)

    print(f"{'#' * _W}")
    print("  All samples complete.")
    print(f"{'#' * _W}\n")
