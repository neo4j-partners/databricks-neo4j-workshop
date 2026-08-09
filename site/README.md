# Databricks + Neo4j Workshop Site

**Live site:** https://neo4j-partners.github.io/databricks-neo4j-workshop

## Publishing slides

The Marp decks in `slides/` are built into static HTML that the site embeds:

```bash
cd slides
npm run build:html
```

This writes to `site/modules/ROOT/attachments/`, under three directories:

- `slides/overview/` — Databricks + Neo4j Integration overview
- `slides/databricks-in-depth/` — Introduction to Databricks + Neo4j, The Power of GraphRAG
- `site/modules/ROOT/images/` — the shared diagrams those decks reference. See [The one odd path](#the-one-odd-path-and-why-it-is-not-a-mistake) below

**Do not commit the output.** `site/modules/ROOT/attachments/` is gitignored. The deploy workflow runs `npm run build:html` in `slides/` before the Antora build, so every push to `main` publishes the decks from their Markdown sources. Committing the HTML was how stale decks used to ship.

## Running locally

```bash
cd site
npm install
npm run build
npm run serve
```

Opens the site at http://localhost:8080. Run the slide build first if you want the decks to render.

## Previewing slides while editing

```bash
cd slides
npm run marp -- . --server
```

Opens a live-reload preview of the Marp decks.

## Where images live

**`site/modules/ROOT/images/` is the single source for every screenshot and concept diagram.** There is no second copy anywhere, and nothing is stored next to the notebook that uses it.

Three consumers, one directory:

| Consumer | How to reference an image |
|---|---|
| An Antora page under `site/` | `image::lab2-clone-menu.png[Alt text]` |
| A lab notebook | `![Alt text](https://raw.githubusercontent.com/neo4j-partners/databricks-neo4j-workshop/main/site/modules/ROOT/images/lab2-clone-menu.png)` |
| A Marp deck under `slides/` | `![bg contain](../../site/modules/ROOT/images/dual-database-architecture.svg)` |

Notebooks use an absolute `raw.githubusercontent.com` URL against `main` because a Databricks notebook has no path back to the repository. Pages use a local reference so the published site stays self-contained: it never depends on GitHub being reachable, and it does not break if this repository ever goes private.

Name new files `lab<n>-<subject>.png`, lowercase and hyphenated, so they sort next to the lab they belong to.

### The one odd path, and why it is not a mistake

`build:assets` in `slides/package.json` copies any image a published deck references into `site/modules/ROOT/attachments/site/modules/ROOT/images/`. That nested path looks wrong and is not.

Marp copies a relative image path into its HTML verbatim and never copies the file. The emitted deck lands two directories deep, in `attachments/slides/<topic>/`, so `../../site/modules/ROOT/images/...` resolves against `attachments/` rather than against the repository root. The copy exists to put the file where the emitted HTML looks for it. Writing the deck's reference any other way would either break the live preview (`npm run marp -- . --server`, which resolves from the source tree) or break the published deck. This way both work and the file still exists exactly once.

`.excalidraw` files stay in the repository root's `images/`. They are editing sources rather than published assets, and Antora would otherwise ship them to every visitor.
