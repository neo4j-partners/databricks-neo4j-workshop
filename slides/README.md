# Workshop Slides

Presentation-ready slides formatted for [Marp](https://marp.app/).

## Quick Start

Requires Node.js 22 LTS (`brew install node@22`) and a one-time `npm install` in this directory.

```bash
cd slides
/opt/homebrew/opt/node@22/bin/node ./node_modules/.bin/marp platform-overview --server
```

Opens at http://localhost:8080/. Replace `platform-overview` with any topic folder name.

## Export All Presentations

```bash
cd slides
for dir in platform-overview/ genai-foundations/ kg-construction/ retrieval-patterns/ agents/ graph-ml/ governance/; do
  /opt/homebrew/opt/node@22/bin/node ./node_modules/.bin/marp "$dir" --pdf --allow-local-files
done
```

## Troubleshooting

**`require is not defined in ES module scope` error?**
- Marp CLI is incompatible with Node.js 25+. Install Node 22 LTS: `brew install node@22`

**Images not showing?**
- Use `--allow-local-files` flag with Marp CLI

---

## Slide Decks

Slides are organized by topic. Each folder contains all canonical files for that topic.

### `platform-overview/`
Why Databricks and Neo4j complement each other. Covers the dual-database architecture, the Neo4j Spark Connector, Neo4j Aura, and the workshop use case (aircraft digital twin). Four files: an aircraft-lens overview deck, a fraud-lens deep dive, the workshop opener, and the Aura product overview.

### `genai-foundations/`
LLM capabilities and limitations, traditional RAG, and the case for GraphRAG. Three files covering LLM limitations, the RAG retrieval pattern, and Context ROT.

### `kg-construction/`
The full pipeline for building a knowledge graph from unstructured documents. Five files covering SimpleKGPipeline, schema design, chunking strategies, entity resolution, and vectors and embeddings.

### `retrieval-patterns/`
GraphRAG retriever patterns. Four files covering the retriever overview and decision framework, Vector Retriever, Vector Cypher Retriever, and Text2Cypher Retriever.

### `agents/`
AI agents and multi-agent systems. Two files: `01-from-retrievers-to-agents-slides.md` covers the ReAct pattern and agent fundamentals; `02-power-of-graphrag-slides.md` covers Genie, Neo4j MCP, and the multi-agent supervisor in depth.

### `graph-ml/`
Graph Data Science and graph feature engineering. Two files: GDS algorithms, MLflow lift comparison, and bidirectional data loop; and the agentic graph enrichment loop with confidence scoring and ontology validation.

### `governance/`
Authorization sync and the semantic layer. One file covering four patterns for aligning access privileges between Unity Catalog and Neo4j.

---

## Participant Reference Docs

Condensed reference documents combining multiple slide decks into single-page markdown for easy review.

| Document | Covers |
|----------|--------|
| [Overview & GenAI Foundations](docs/overview-and-genai-foundations.md) | Workshop overview, digital twins, GenAI limitations, traditional RAG, Context ROT, and the GraphRAG solution |
| [Building Knowledge Graphs](docs/building-knowledge-graphs.md) | GraphRAG pipeline, schema design, chunking strategies, entity resolution, and vectors/semantic search |

## Slide Format

All slides use Marp markdown format with pagination, syntax-highlighted code blocks, tables, and two-column layouts. See any slide file for the frontmatter template.

## Additional Resources

- [Marp Documentation](https://marpit.marp.app/)
- [Marp CLI Usage](https://github.com/marp-team/marp-cli)
- [Marp Themes](https://github.com/marp-team/marp-core/tree/main/themes)
- [Creating Custom Themes](https://marpit.marp.app/theme-css)
