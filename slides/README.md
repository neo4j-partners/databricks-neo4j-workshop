# Workshop Slides

Presentation-ready slides formatted for [Marp](https://marp.app/).

## Quick Start

Requires Node.js 22 LTS (`brew install node@22`) and a one-time `npm install` in this directory.

```bash
cd slides
/opt/homebrew/opt/node@22/bin/node ./node_modules/.bin/marp overview-business-story --server
```

Opens at http://localhost:8080/. Replace `overview-business-story` with any topic folder name.

## Export All Presentations

```bash
cd slides
for dir in overview-*/ background/; do
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

Eight workshop decks, one folder each, listed in run-of-show order. Anything not in that sequence lives under `background/` and is not presented.

| # | Folder | Deck | Pairs with |
|---|--------|------|-----------|
| 1 | `overview-business-story/` | The Business Case for GraphRAG | Opening |
| 2 | `overview-architecture/` | Workshop Architecture and Roadmap | Opening |
| 3 | `overview-knowledge-graph/` | Knowledge Graph Foundations | Labs 1 and 2 |
| 4 | `overview-graphrag/` | GraphRAG Foundations | Lab 3 |
| 5 | `overview-retrievers/` | GraphRAG Retriever Patterns | Lab 3 |
| 6 | `overview-agent/` | The Supervisor Agent and Deployment | Labs 4A and 5 |
| 7 | `overview-agent-memory/` | Agent Memory with Neo4j | Lab 6 |
| 8 | `overview-mcp/` | Neo4j MCP and Agent Bricks | Lab 4B, instructor demo |

### Assets

- **`aircraft/`** — the aircraft digital twin diagrams used by decks 3 and 4
- **`databricks-in-depth/`** — platform architecture diagrams
- **`images/`** — concept art shared across decks

### `background/`

Reference material kept for reuse, never presented in the run of show.

- **`background/agents/`** — the long-form GraphRAG and multi-agent deck decks 1, 4 and 8 were drawn from
- **`background/graph-ml/`** — Graph Data Science, MLflow lift comparison, and the agentic graph enrichment loop
- **`background/governance/`** — four patterns for aligning access privileges between Unity Catalog and Neo4j
- **`background/kg-construction/`** — SimpleKGPipeline, schema design, and entity resolution

Decks under `background/` sit one directory deeper than workshop decks, so their `../` image references need one more `..`. See the header comment in `build-slides.sh`.

---

## Slide Format

All slides use Marp markdown format with pagination, syntax-highlighted code blocks, tables, and two-column layouts. See any slide file for the frontmatter template.

## Additional Resources

- [Marp Documentation](https://marpit.marp.app/)
- [Marp CLI Usage](https://github.com/marp-team/marp-cli)
- [Marp Themes](https://github.com/marp-team/marp-core/tree/main/themes)
- [Creating Custom Themes](https://marpit.marp.app/theme-css)
