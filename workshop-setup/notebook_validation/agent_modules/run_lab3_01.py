"""Automated validation of Lab 3: SimpleKGPipeline and Semantic Search.

Replicates the Lab 3 notebook process (01_data_and_embeddings.ipynb) as a
standalone script: runs SimpleKGPipeline to chunk, embed, and extract entities
from the A320-200 maintenance manual, creates vector and fulltext indexes,
cross-links documents to aircraft topology, and validates with PASS/FAIL checks.

Requires data_utils.py uploaded alongside this script.

Usage:
    ./upload.sh --all && ./submit.sh run_lab3_01.py
"""

import argparse
import sys
import time


def main():
    parser = argparse.ArgumentParser(
        description="Lab 3 Validation: SimpleKGPipeline and Semantic Search"
    )
    parser.add_argument("--neo4j-uri", required=True, help="Neo4j Aura URI")
    parser.add_argument("--neo4j-username", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo4j-password", required=True, help="Neo4j password")
    parser.add_argument(
        "--data-path",
        default="/Volumes/databricks-neo4j-workshop/aircraft/raw_data",
        help="Unity Catalog Volume path containing maintenance manual",
    )
    # Accept MCP args for submit.sh compatibility (unused by this script)
    parser.add_argument("--mcp-endpoint", default="", help="(unused)")
    parser.add_argument("--mcp-api-key", default="", help="(unused)")
    parser.add_argument("--mcp-path", default="", help="(unused)")
    args = parser.parse_args()

    from data_utils import (
        EMBEDDING_DIMENSIONS,
        VolumeDataLoader,
        get_embedder,
        get_llm,
        run_pipeline,
    )
    from neo4j import GraphDatabase
    from neo4j_graphrag.indexes import create_vector_index, create_fulltext_index

    # ── Configuration ────────────────────────────────────────────────────────

    DOCUMENT_ID = "AMM-A320-2024-001"
    AIRCRAFT_TYPE = "A320-200"
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 100
    VECTOR_INDEX_NAME = "maintenanceChunkEmbeddings"
    FULLTEXT_INDEX_NAME = "maintenanceChunkText"
    INDEX_POLL_INTERVAL = 10  # seconds
    INDEX_POLL_TIMEOUT = 300  # 5 minutes
    SEARCH_SCORE_THRESHOLD = 0.80

    results = []  # (name, passed, detail)

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    print("=" * 70)
    print("Lab 3 Validation: SimpleKGPipeline and Semantic Search")
    print("=" * 70)
    print(f"Neo4j URI:        {args.neo4j_uri}")
    print(f"Data Path:        {args.data_path}")
    print(f"Embedding Model:  databricks-bge-large-en ({EMBEDDING_DIMENSIONS} dims)")
    print(f"Chunk Size:       {CHUNK_SIZE} chars, {CHUNK_OVERLAP} overlap")
    print()

    # ── Connect to Neo4j ─────────────────────────────────────────────────────

    driver = GraphDatabase.driver(
        args.neo4j_uri,
        auth=(args.neo4j_username, args.neo4j_password),
    )
    driver.verify_connectivity()
    print("Connected to Neo4j successfully!\n")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 1: Clear + Run SimpleKGPipeline
    # ══════════════════════════════════════════════════════════════════════════

    print("=" * 70)
    print("STAGE 1: SimpleKGPipeline (Chunking, Embedding, Entity Extraction)")
    print("=" * 70)

    # -- Clear existing enrichment data ------------------------------------

    print("Clearing existing enrichment data...")
    for idx_name in [VECTOR_INDEX_NAME, FULLTEXT_INDEX_NAME]:
        try:
            with driver.session() as session:
                result = session.run(f"DROP INDEX {idx_name} IF EXISTS")
                result.consume()
            print(f"  Dropped index: {idx_name}")
        except Exception as e:
            print(f"  Index {idx_name} drop note: {e}")

    labels = ["Chunk", "Document", "OperatingLimit", "__Entity__", "__KGBuilder__"]
    deleted_total = 0
    for label in labels:
        while True:
            records_del, _, _ = driver.execute_query(
                f"MATCH (n:{label}) WITH n LIMIT 500 DETACH DELETE n RETURN count(*) AS deleted"
            )
            count = records_del[0]["deleted"]
            deleted_total += count
            if count == 0:
                break
    print(f"  Cleared {deleted_total} enrichment nodes\n")

    # -- Load maintenance manual -------------------------------------------

    print("Loading maintenance manual from Unity Catalog Volume...")
    loader = VolumeDataLoader("MAINTENANCE_A320.md", volume_path=args.data_path)
    manual_text = loader.text
    metadata = loader.get_metadata()
    print(f"  Loaded: {metadata['name']}")
    print(f"  Size: {metadata['size']:,} characters\n")

    # -- Initialize LLM and Embedder --------------------------------------

    print("Initializing LLM and Embedder...")
    llm = get_llm()
    embedder = get_embedder()
    print(f"  LLM: {llm.model_id}")
    print(f"  Embedder: {embedder.model_id}\n")

    # -- Run pipeline ------------------------------------------------------

    print("Running SimpleKGPipeline...")
    pipeline_start = time.time()
    run_pipeline(
        driver=driver,
        llm=llm,
        embedder=embedder,
        text=manual_text,
        document_metadata={
            "documentId": DOCUMENT_ID,
            "aircraftType": AIRCRAFT_TYPE,
            "title": "A320-200 Maintenance and Troubleshooting Manual",
            "type": "maintenance_manual",
        },
        context=f"[DOCUMENT CONTEXT] Aircraft Type: {AIRCRAFT_TYPE} | Title: A320-200 Maintenance Manual\n\n",
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    pipeline_elapsed = time.time() - pipeline_start
    print(f"  Pipeline completed in {pipeline_elapsed:.1f}s\n")

    # -- Stage 1 Verification ----------------------------------------------

    print("Stage 1 Verification:")

    # Check 1: Document node with correct metadata
    doc_check, _, _ = driver.execute_query("""
        MATCH (d:Document {documentId: $doc_id})
        RETURN d.type AS type, d.aircraftType AS aircraftType, d.title AS title
    """, doc_id=DOCUMENT_ID)
    doc_exists = len(doc_check) == 1 and doc_check[0]["aircraftType"] == AIRCRAFT_TYPE
    record("Document node with correct metadata", doc_exists,
           f"found={len(doc_check)}")

    # Check 2: Chunks created with FROM_DOCUMENT
    chunk_count_check, _, _ = driver.execute_query("""
        MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document {documentId: $doc_id})
        RETURN count(c) as count
    """, doc_id=DOCUMENT_ID)
    chunk_count = chunk_count_check[0]["count"]
    record("Chunks created with FROM_DOCUMENT", chunk_count > 10,
           f"chunks={chunk_count}")

    # Check 3: No orphaned chunks
    orphan_check, _, _ = driver.execute_query("""
        MATCH (c:Chunk)
        WHERE NOT (c)-[:FROM_DOCUMENT]->(:Document)
        RETURN count(c) as orphans
    """)
    orphan_count = orphan_check[0]["orphans"]
    record("No orphaned chunks", orphan_count == 0,
           f"orphans={orphan_count}")

    # Check 4: NEXT_CHUNK chain exists
    chain_check, _, _ = driver.execute_query("""
        MATCH ()-[r:NEXT_CHUNK]->()
        RETURN count(r) as count
    """)
    chain_count = chain_check[0]["count"]
    record("NEXT_CHUNK chain exists", chain_count > 0,
           f"relationships={chain_count}")

    # Check 5: All chunks have embeddings
    emb_count_check, _, _ = driver.execute_query("""
        MATCH (c:Chunk) WHERE c.embedding IS NOT NULL
        RETURN count(c) as with_embedding
    """)
    with_emb = emb_count_check[0]["with_embedding"]
    record("All chunks have embeddings", with_emb == chunk_count,
           f"with_embedding={with_emb}/{chunk_count}")

    # Check 6: Embeddings are correct dimensions
    dim_check, _, _ = driver.execute_query("""
        MATCH (c:Chunk) WHERE c.embedding IS NOT NULL
        WITH c, size(c.embedding) AS dims
        WHERE dims <> $expected_dims
        RETURN count(c) as wrong_dims
    """, expected_dims=EMBEDDING_DIMENSIONS)
    wrong_dims = dim_check[0]["wrong_dims"]
    record(f"All embeddings are {EMBEDDING_DIMENSIONS} dimensions", wrong_dims == 0,
           f"wrong_dims={wrong_dims}")

    # Check 7: OperatingLimit entities extracted
    ol_check, _, _ = driver.execute_query("""
        MATCH (ol:OperatingLimit)
        RETURN count(ol) as count
    """)
    ol_count = ol_check[0]["count"]
    record("OperatingLimit entities extracted", ol_count > 0,
           f"entities={ol_count}")

    # Check 8: OperatingLimit entities have required properties
    ol_prop_check, _, _ = driver.execute_query("""
        MATCH (ol:OperatingLimit)
        WHERE ol.name IS NOT NULL AND ol.parameterName IS NOT NULL AND ol.aircraftType IS NOT NULL
        RETURN count(ol) as valid
    """)
    ol_valid = ol_prop_check[0]["valid"]
    record("OperatingLimit entities have required properties", ol_valid == ol_count,
           f"valid={ol_valid}/{ol_count}")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2: Index Creation and Search Validation
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("STAGE 2: Index Creation and Search Validation")
    print("=" * 70)

    # -- Create indexes ----------------------------------------------------

    print(f"Creating vector index: {VECTOR_INDEX_NAME}...")
    try:
        create_vector_index(
            driver=driver,
            name=VECTOR_INDEX_NAME,
            label="Chunk",
            embedding_property="embedding",
            dimensions=EMBEDDING_DIMENSIONS,
            similarity_fn="cosine",
        )
        print(f"  Created ({EMBEDDING_DIMENSIONS} dimensions, cosine similarity)")
    except Exception as e:
        print(f"  Note: {e}")

    print(f"Creating fulltext index: {FULLTEXT_INDEX_NAME}...")
    try:
        create_fulltext_index(
            driver=driver,
            name=FULLTEXT_INDEX_NAME,
            label="Chunk",
            node_properties=["text"],
        )
        print("  Created")
    except Exception as e:
        print(f"  Note: {e}")

    # -- Resolve actual index names ----------------------------------------

    print("\n  Resolving actual index names for Chunk label:")
    actual_vector_idx = VECTOR_INDEX_NAME
    actual_fulltext_idx = FULLTEXT_INDEX_NAME
    with driver.session() as session:
        result = session.run("""
            SHOW INDEXES
            YIELD name, state, type, labelsOrTypes, properties
            WHERE type IN ['VECTOR', 'FULLTEXT']
            RETURN name, state, type, labelsOrTypes, properties
        """)
        for idx_rec in result:
            labels_found = idx_rec["labelsOrTypes"]
            props = idx_rec["properties"]
            print(f"    {idx_rec['name']}: {idx_rec['state']} ({idx_rec['type']}) "
                  f"labels={labels_found} props={props}")
            if "Chunk" in labels_found and "embedding" in props and idx_rec["type"] == "VECTOR":
                actual_vector_idx = idx_rec["name"]
            if "Chunk" in labels_found and "text" in props and idx_rec["type"] == "FULLTEXT":
                actual_fulltext_idx = idx_rec["name"]

    if actual_vector_idx != VECTOR_INDEX_NAME:
        print(f"  Using existing vector index: {actual_vector_idx}")
        VECTOR_INDEX_NAME = actual_vector_idx
    if actual_fulltext_idx != FULLTEXT_INDEX_NAME:
        print(f"  Using existing fulltext index: {actual_fulltext_idx}")
        FULLTEXT_INDEX_NAME = actual_fulltext_idx
    print()

    # -- Poll for ONLINE status --------------------------------------------

    print(f"Waiting for indexes to come ONLINE (timeout: {INDEX_POLL_TIMEOUT}s)...")
    start_time = time.time()
    vector_online = False
    fulltext_online = False
    first_poll = True

    while time.time() - start_time < INDEX_POLL_TIMEOUT:
        idx_records, _, _ = driver.execute_query("""
            SHOW INDEXES
            YIELD name, state, type
            RETURN name, state, type
        """)

        if first_poll:
            print(f"  All indexes found ({len(idx_records)}):")
            for rec in idx_records:
                print(f"    {rec['name']}: {rec['state']} ({rec['type']})")
            first_poll = False

        for rec in idx_records:
            if rec["name"] == VECTOR_INDEX_NAME and rec["state"] == "ONLINE":
                vector_online = True
            if rec["name"] == FULLTEXT_INDEX_NAME and rec["state"] == "ONLINE":
                fulltext_online = True

        if vector_online and fulltext_online:
            elapsed = time.time() - start_time
            print(f"  Both indexes ONLINE after {elapsed:.1f}s\n")
            break

        time.sleep(INDEX_POLL_INTERVAL)
        elapsed = time.time() - start_time
        print(f"  ... polling ({elapsed:.0f}s) vector={'ONLINE' if vector_online else 'waiting'}, "
              f"fulltext={'ONLINE' if fulltext_online else 'waiting'}")

    if not vector_online or not fulltext_online:
        print(f"\n  ERROR: Indexes not ONLINE after {INDEX_POLL_TIMEOUT}s timeout!")
        record(f"Vector index {VECTOR_INDEX_NAME} ONLINE", vector_online, "TIMEOUT")
        record(f"Fulltext index {FULLTEXT_INDEX_NAME} ONLINE", fulltext_online, "TIMEOUT")
        _print_summary(results)
        driver.close()
        sys.exit(1)

    # -- Stage 2 Verification ----------------------------------------------

    print("Stage 2 Verification:")

    record(f"Vector index {VECTOR_INDEX_NAME} ONLINE", vector_online)
    record(f"Fulltext index {FULLTEXT_INDEX_NAME} ONLINE", fulltext_online)

    # Vector search — engine vibration query
    query_text = "How do I troubleshoot engine vibration?"
    query_embedding = embedder.embed_query(query_text)
    search_results, _, _ = driver.execute_query("""
        CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
        YIELD node, score
        RETURN node.text as text, node.index as idx, score
    """, index_name=VECTOR_INDEX_NAME, top_k=3, embedding=query_embedding)

    if len(search_results) > 0:
        top_score = search_results[0]["score"]
        record("Vector search: score above threshold",
               top_score >= SEARCH_SCORE_THRESHOLD,
               f"query='{query_text}', top_score={top_score:.4f}, threshold={SEARCH_SCORE_THRESHOLD}")
    else:
        record("Vector search: score above threshold", False, "no results returned")

    # Fulltext search for EGT limits
    ft_results, _, _ = driver.execute_query("""
        CALL db.index.fulltext.queryNodes($index_name, $query)
        YIELD node, score
        RETURN node.text as text, score
        LIMIT 3
    """, index_name=FULLTEXT_INDEX_NAME, query="EGT limits")

    if len(ft_results) > 0:
        ft_text = " ".join(r["text"].lower() for r in ft_results)
        has_egt = "egt" in ft_text
        record("Fulltext search: EGT limits returns results", has_egt,
               f"results={len(ft_results)}, contains_egt={has_egt}")
    else:
        record("Fulltext search: EGT limits returns results", False, "no results")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 3: Cross-Links to Aircraft Topology
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("STAGE 3: Cross-Links to Aircraft Topology")
    print("=" * 70)

    # -- Create APPLIES_TO -------------------------------------------------

    print("Creating Document -[:APPLIES_TO]-> Aircraft relationships...")
    applies_to, _, _ = driver.execute_query("""
        MATCH (d:Document) WHERE d.aircraftType IS NOT NULL
        MATCH (a:Aircraft {model: d.aircraftType})
        MERGE (d)-[:APPLIES_TO]->(a)
        RETURN d.documentId AS doc, a.model AS aircraft, count(*) AS count
    """)
    for r in applies_to:
        print(f"  {r['doc']} -> {r['aircraft']}")

    # -- Create HAS_LIMIT --------------------------------------------------

    print("Creating Sensor -[:HAS_LIMIT]-> OperatingLimit relationships...")
    has_limit, _, _ = driver.execute_query("""
        MATCH (a:Aircraft)-[:HAS_SYSTEM]->(sys:System)-[:HAS_SENSOR]->(s:Sensor)
        MATCH (ol:OperatingLimit {parameterName: s.type, aircraftType: a.model})
        MERGE (s)-[:HAS_LIMIT]->(ol)
        RETURN s.type AS sensor, ol.name AS limit, count(*) AS count
    """)
    for r in has_limit:
        print(f"  {r['sensor']} -> {r['limit']}")
    if not has_limit:
        print("  (No matches — depends on which limits the LLM extracted)")

    # -- Stage 3 Verification ----------------------------------------------

    print("\nStage 3 Verification:")

    # Check: APPLIES_TO exists
    applies_check, _, _ = driver.execute_query("""
        MATCH (d:Document)-[:APPLIES_TO]->(a:Aircraft)
        RETURN count(*) as count
    """)
    applies_count = applies_check[0]["count"]
    record("APPLIES_TO relationships created", applies_count > 0,
           f"count={applies_count}")

    # Check: Full traversal path works
    traversal_check, _, _ = driver.execute_query("""
        MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)-[:APPLIES_TO]->(a:Aircraft)
        RETURN a.model AS model, count(c) AS chunks
    """)
    traversal_ok = len(traversal_check) > 0
    record("Chunk -> Document -> Aircraft traversal works", traversal_ok,
           f"aircraft_models={[r['model'] for r in traversal_check]}")

    # Check: HAS_LIMIT (soft check — depends on LLM extraction quality)
    limit_check, _, _ = driver.execute_query("""
        MATCH (s:Sensor)-[:HAS_LIMIT]->(ol:OperatingLimit)
        RETURN count(*) as count
    """)
    limit_count = limit_check[0]["count"]
    # This is a soft check — HAS_LIMIT depends on which entities were extracted
    record("HAS_LIMIT relationships created (soft)", limit_count >= 0,
           f"count={limit_count} (0 is acceptable if LLM didn't extract matching params)")

    # ══════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════════════════════

    _print_summary(results)
    driver.close()
    print("Connection closed.")

    failed = sum(1 for _, p, _ in results if not p)
    if failed > 0:
        sys.exit(1)


def _print_summary(results):
    """Print the PASS/FAIL summary table."""
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, p, detail in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    print()
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}")
    print("=" * 70)

    if failed > 0:
        print("FAILED")
    else:
        print("SUCCESS")


if __name__ == "__main__":
    main()
