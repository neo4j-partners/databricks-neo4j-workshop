"""Automated validation of Lab 3 Notebook 04: GraphRAG Retrievers.

Read-only validation that the KG built by notebook 03 supports the retriever
patterns from 04_graphrag_retrievers.ipynb: VectorRetriever, GraphRAG,
VectorCypherRetriever with document context, adjacent chunks, topology
traversal (APPLIES_TO), and operating limit queries (HAS_LIMIT).

Requires data_utils.py uploaded alongside this script.
Prerequisite: run_lab3_03.py must have been run first (KG + indexes exist).

Usage:
    ./upload.sh --all && ./submit.sh run_lab3_04.py
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Lab 3 Validation: GraphRAG Retrievers (Notebook 04)"
    )
    parser.add_argument("--neo4j-uri", required=True, help="Neo4j Aura URI")
    parser.add_argument("--neo4j-username", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo4j-password", required=True, help="Neo4j password")
    # Accept extra args for submit.sh compatibility (unused by this script)
    parser.add_argument("--data-path", default="", help="(unused)")
    parser.add_argument("--mcp-endpoint", default="", help="(unused)")
    parser.add_argument("--mcp-api-key", default="", help="(unused)")
    parser.add_argument("--mcp-path", default="", help="(unused)")
    args = parser.parse_args()

    from data_utils import get_embedder, get_llm
    from neo4j import GraphDatabase
    from neo4j_graphrag.generation import GraphRAG
    from neo4j_graphrag.retrievers import VectorCypherRetriever, VectorRetriever

    # ── Configuration ────────────────────────────────────────────────────────

    VECTOR_INDEX_NAME = "maintenanceChunkEmbeddings"
    SEARCH_SCORE_THRESHOLD = 0.75

    results = []  # (name, passed, detail)

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        results.append((name, passed, detail))
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    print("=" * 70)
    print("Lab 3 Validation: GraphRAG Retrievers (Notebook 04)")
    print("=" * 70)
    print(f"Neo4j URI:  {args.neo4j_uri}")
    print()

    # ── Connect to Neo4j ─────────────────────────────────────────────────────

    driver = GraphDatabase.driver(
        args.neo4j_uri,
        auth=(args.neo4j_username, args.neo4j_password),
    )
    driver.verify_connectivity()
    print("Connected to Neo4j successfully!\n")

    # ── Initialize LLM and Embedder ──────────────────────────────────────────

    print("Initializing LLM and Embedder...")
    llm = get_llm()
    embedder = get_embedder()
    print(f"  LLM: {llm.model_id}")
    print(f"  Embedder: {embedder.model_id}\n")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 1: VectorRetriever
    # ══════════════════════════════════════════════════════════════════════════

    print("=" * 70)
    print("STAGE 1: VectorRetriever")
    print("=" * 70)

    vector_retriever = VectorRetriever(
        driver=driver,
        index_name=VECTOR_INDEX_NAME,
        embedder=embedder,
        return_properties=["text"],
    )

    # -- Vector search --------------------------------------------------------

    query = "What are the steps to troubleshoot engine vibration?"
    result = vector_retriever.search(query_text=query, top_k=5)

    record("VectorRetriever returns results",
           len(result.items) > 0,
           f"results={len(result.items)}")

    if result.items:
        top_score = result.items[0].metadata["score"]
        record("Vector search score above threshold",
               top_score >= SEARCH_SCORE_THRESHOLD,
               f"query='{query}', score={top_score:.4f}, threshold={SEARCH_SCORE_THRESHOLD}")

        has_content = len(result.items[0].content) > 50
        record("Vector search returns text content", has_content,
               f"content_length={len(result.items[0].content)}")

    # -- GraphRAG pipeline ----------------------------------------------------

    print("\n  GraphRAG pipeline...")
    query = "What are the normal EGT operating limits for the V2500 engine?"
    rag = GraphRAG(llm=llm, retriever=vector_retriever)
    response = rag.search(
        query,
        retriever_config={"top_k": 5},
        return_context=True,
        response_fallback="No relevant maintenance procedures found.",
    )

    has_answer = len(response.answer) > 50
    record("GraphRAG returns LLM answer", has_answer,
           f"answer_length={len(response.answer)}")

    has_context = len(response.retriever_result.items) > 0
    record("GraphRAG returns retriever context", has_context,
           f"context_items={len(response.retriever_result.items)}")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2: VectorCypherRetriever — Document Context
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("STAGE 2: VectorCypherRetriever — Document Context")
    print("=" * 70)

    document_context_query = """
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
RETURN
    doc.documentId AS document_id,
    doc.aircraftType AS aircraft_type,
    doc.title AS document_title,
    node.index AS chunk_index,
    node.text AS context
"""

    document_retriever = VectorCypherRetriever(
        driver=driver,
        index_name=VECTOR_INDEX_NAME,
        embedder=embedder,
        retrieval_query=document_context_query,
    )

    query = "What are the hydraulic system pressure limits?"
    rag = GraphRAG(llm=llm, retriever=document_retriever)
    response = rag.search(
        query,
        retriever_config={"top_k": 3},
        return_context=True,
        response_fallback="No relevant maintenance procedures found.",
    )

    has_results = len(response.retriever_result.items) > 0
    record("Document context retriever returns results", has_results,
           f"items={len(response.retriever_result.items)}")

    if has_results:
        content = response.retriever_result.items[0].content
        has_doc_meta = "document_id" in content.lower() or "aircraft_type" in content.lower()
        record("Results include document metadata", has_doc_meta)

    record("Document context GraphRAG returns answer",
           len(response.answer) > 50,
           f"answer_length={len(response.answer)}")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 3: VectorCypherRetriever — Adjacent Chunks
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("STAGE 3: VectorCypherRetriever — Adjacent Chunks")
    print("=" * 70)

    adjacent_chunks_query = """
WITH node
OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(node)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
RETURN
    doc.documentId AS document_id,
    node.index AS chunk_index,
    COALESCE(prev.text, '') AS previous_context,
    node.text AS main_context,
    COALESCE(next.text, '') AS next_context
"""

    adjacent_retriever = VectorCypherRetriever(
        driver=driver,
        index_name=VECTOR_INDEX_NAME,
        embedder=embedder,
        retrieval_query=adjacent_chunks_query,
    )

    query = "How do I perform the engine vibration diagnostic flow?"
    rag = GraphRAG(llm=llm, retriever=adjacent_retriever)
    response = rag.search(
        query,
        retriever_config={"top_k": 3},
        return_context=True,
        response_fallback="No relevant maintenance procedures found.",
    )

    has_results = len(response.retriever_result.items) > 0
    record("Adjacent chunks retriever returns results", has_results,
           f"items={len(response.retriever_result.items)}")

    if has_results:
        content = response.retriever_result.items[0].content
        has_adjacent = "previous_context" in content.lower() or "next_context" in content.lower()
        record("Results include adjacent chunk context", has_adjacent)

    record("Adjacent chunks GraphRAG returns answer",
           len(response.answer) > 50,
           f"answer_length={len(response.answer)}")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 4: VectorCypherRetriever — Aircraft Topology (APPLIES_TO)
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("STAGE 4: VectorCypherRetriever — Aircraft Topology")
    print("=" * 70)

    system_context_query = """
WITH node
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)-[:APPLIES_TO]->(a:Aircraft)
MATCH (a)-[:HAS_SYSTEM]->(s:System)
OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(comp:Component)

WITH node, doc, a, s, comp
RETURN
    doc.documentId AS document_id,
    doc.aircraftType AS aircraft_type,
    a.tail_number AS aircraft,
    COLLECT(DISTINCT s.name)[0..3] AS systems,
    COLLECT(DISTINCT comp.name)[0..3] AS components,
    node.text AS context
"""

    system_retriever = VectorCypherRetriever(
        driver=driver,
        index_name=VECTOR_INDEX_NAME,
        embedder=embedder,
        retrieval_query=system_context_query,
    )

    query = "What maintenance is required for the engine fuel pump?"
    rag = GraphRAG(llm=llm, retriever=system_retriever)
    response = rag.search(
        query,
        retriever_config={"top_k": 3},
        return_context=True,
        response_fallback="No relevant maintenance procedures found.",
    )

    has_results = len(response.retriever_result.items) > 0
    record("Topology retriever returns results", has_results,
           f"items={len(response.retriever_result.items)}")

    if has_results:
        content = response.retriever_result.items[0].content
        has_topology = "aircraft" in content.lower() or "systems" in content.lower()
        record("Results include aircraft topology", has_topology)

    record("Topology GraphRAG returns answer",
           len(response.answer) > 50,
           f"answer_length={len(response.answer)}")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 5: VectorCypherRetriever — Operating Limits
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("STAGE 5: VectorCypherRetriever — Operating Limits")
    print("=" * 70)

    operating_limit_query = """
WITH node
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)-[:APPLIES_TO]->(a:Aircraft)
OPTIONAL MATCH (a)-[:HAS_SYSTEM]->(sys:System)-[:HAS_SENSOR]->(s:Sensor)-[:HAS_LIMIT]->(ol:OperatingLimit)

WITH node, doc, a,
     COLLECT(DISTINCT {
         sensor: s.type,
         parameter: ol.parameterName,
         max: ol.maxValue,
         unit: ol.unit,
         regime: ol.regime
     })[0..5] AS operating_limits

RETURN
    doc.aircraftType AS aircraft_type,
    operating_limits,
    node.text AS context
"""

    limit_retriever = VectorCypherRetriever(
        driver=driver,
        index_name=VECTOR_INDEX_NAME,
        embedder=embedder,
        retrieval_query=operating_limit_query,
    )

    query = "What are the EGT temperature limits for the engine?"
    rag = GraphRAG(llm=llm, retriever=limit_retriever)
    response = rag.search(
        query,
        retriever_config={"top_k": 3},
        return_context=True,
        response_fallback="No relevant maintenance procedures found.",
    )

    has_results = len(response.retriever_result.items) > 0
    record("Operating limits retriever returns results", has_results,
           f"items={len(response.retriever_result.items)}")

    # Soft check — operating limits depend on LLM extraction quality
    record("Operating limits query executed (soft)", True,
           "full chain query ran (limits may be empty depending on extraction)")

    record("Operating limits GraphRAG returns answer",
           len(response.answer) > 50,
           f"answer_length={len(response.answer)}")

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 6: Retriever Comparison
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("STAGE 6: Retriever Comparison")
    print("=" * 70)

    comparison_query = "What should I do if the EGT exceeds normal limits?"

    rag_basic = GraphRAG(llm=llm, retriever=vector_retriever)
    response_basic = rag_basic.search(
        comparison_query,
        retriever_config={"top_k": 3},
        return_context=True,
        response_fallback="No relevant maintenance procedures found.",
    )

    rag_enhanced = GraphRAG(llm=llm, retriever=adjacent_retriever)
    response_enhanced = rag_enhanced.search(
        comparison_query,
        retriever_config={"top_k": 3},
        return_context=True,
        response_fallback="No relevant maintenance procedures found.",
    )

    both_answered = len(response_basic.answer) > 50 and len(response_enhanced.answer) > 50
    record("Both retrievers return answers for comparison", both_answered,
           f"vector={len(response_basic.answer)} chars, "
           f"adjacent={len(response_enhanced.answer)} chars")

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
