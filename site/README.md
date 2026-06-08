# Databricks + Neo4j Workshop Site

**Live site:** https://neo4j-partners.github.io/databricks-neo4j-workshop

## Publishing slides

Build the Marp slides into static HTML that the site embeds:

```bash
cd slides
npm run build:html
```

This outputs HTML to `site/modules/ROOT/attachments/slides/` under two directories:

- `overview/` — Databricks + Neo4j Integration overview
- `databricks-in-depth/` — Introduction to Databricks + Neo4j, The Power of GraphRAG

Commit the generated HTML files — they are checked into git so the Antora build does not depend on Marp.

## Running locally

```bash
cd site
npm install
npm run build
npm run serve
```

Opens the site at http://localhost:8080.

## Previewing slides while editing

```bash
cd slides
/opt/homebrew/opt/node@22/bin/node ./node_modules/.bin/marp . --server
```

Opens a live-reload preview of the Marp slides (requires Node 22).
