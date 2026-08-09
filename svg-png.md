# PNGs without an SVG equivalent

Scope: repository-owned images only. `node_modules/`, `.venv/`, and `site/build/`
(generated output) are excluded.

## Diagrams — should have an SVG, do not

| PNG | Notes |
|---|---|
| `slides/images/context_rot_hero_plot.png` | Plot image. No `.excalidraw` and no `.svg` source anywhere. |

That is the only one. Every other diagram in the repo ships as SVG, usually with
an `.excalidraw` source beside it.

## Screenshots — no SVG possible

UI captures. SVG is not a meaningful equivalent; listed so the inventory is
complete.

### `Lab_1_Aura_Setup/images/`
- `FREE_01_WHERE.png`
- `FREE_02_Create_Instances.png`

### `site/modules/ROOT/images/`
- `lab1-backup-restore.png`
- `lab1-create-instance-alt.png`
- `lab1-create-instance.png`
- `lab1-download-credentials.png`
- `lab1-instance-details.png`
- `lab2-change-compute.png`
- `lab2-clone-dialog.png`
- `lab2-clone-menu.png`
- `lab2-compute-overview.png`
- `lab2-csv-volume-data.png`
- `lab2-dbx-login-error.png`
- `lab4-configure-genie.png`
- `lab4-genie-connect-data.png`
- `lab4-lakehouse-sensor-readings.png`
- `lab4-mcp-connection.png`

## PNGs that do have an SVG

| PNG | Matching SVG |
|---|---|
| `images/dual-database-architecture.png` | `images/dual-database-architecture.svg` |
| `images/lab-architecture-overview.png` | `images/lab-architecture-overview.svg` |

Both pairs sit in the same directory.

## SVG with no PNG

`images/workshop-infrastructure.svg`; `site/modules/ROOT/images/` —
`graphrag-multiplatform-retrieval.svg`, `lab1-property-graph.svg`, the two
`lab3-*.svg`, the three `step*.svg`; and everything under `slides/aircraft/` and
`slides/databricks-in-depth/`.

---

# Fixes applied

Three defects the inventory turned up, all now closed.

## 1. Slide decks referenced images that were not there

**Was broken:** all three published decks, not just the one first spotted. Marp
copies relative image paths into the HTML verbatim and never copies the image
files, so every reference pointed at a file that did not exist next to the
output:

| Deck | Referenced | Present |
|---|---|---|
| `overview/01-databricks-neo4j-integration-slides.html` | `dual-database-architecture.png` | no |
| `databricks-in-depth/01-intro-databricks-neo4j-slides.html` | `fraud-ring-dual-architecture.png` | yes, hand-copied |
| `databricks-in-depth/01-intro-databricks-neo4j-slides.html` | `intelligence-platform-flow.png` | no |

**Root cause:** `slides/package.json` `build:html` read from
`overview-databricks-neo4j/` and `databricks-in-depth/`. The decks moved to
`slides/platform-overview/` and `slides/agents/`, leaving those two directories
holding only diagram assets and PDFs. The script had built nothing since. The
checked-in HTML was output from before the move, when the sources still said
`.png`.

**Fix:** rewrote `build:html` to name the three published decks explicitly,
rather than globbing a directory, so it builds exactly what the site iframes and
nothing more:

- `platform-overview/01-databricks-neo4j-integration-slides.md` -> `attachments/slides/overview/`
- `platform-overview/01-intro-databricks-neo4j-slides.md` -> `attachments/slides/databricks-in-depth/`
- `agents/02-power-of-graphrag-slides.md` -> `attachments/slides/databricks-in-depth/`

Added a `build:assets` step that copies the three referenced SVGs to the paths
the emitted HTML resolves against, and deleted
`site/modules/ROOT/attachments/slides/databricks-in-depth/fraud-ring-dual-architecture.png`.

**Verified:** 3 image references, 0 missing, both in
`site/modules/ROOT/attachments/` and in the rebuilt `site/build/`.

Globbing was not restored on purpose. `platform-overview/` holds four decks and
the site publishes one, so `-I` would have published three decks nobody links.

## 2. `site/build/` held stale and orphaned PNGs

`site/build/` is gitignored with zero tracked files, so it was deleted and
rebuilt with `npm run build` from `site/`.

Cleared: `lab3-graphrag-retrieval-flow.png`, `lab3-knowledge-graph-structure.png`,
`step1-flat-tables-foreign-keys.png`, `step2-spark-connector-mapping.png` and
`step3-connected-graph.png`, all of whose sources are now `.svg`, plus
`mcp-architecture.png`, which no page referenced and no source produced.

## 3. Four lab4 screenshots existed twice

The two copies were byte-identical but both live, on different delivery paths:
`Lab_4_Compound_AI_Agents/images/*.png` served `PART_A.md`, `PART_B.md` and
`04_genie_agent.ipynb` (via `raw.githubusercontent.com` on `main`), while
`site/modules/ROOT/images/lab4-*.png` served `lab4-instructions.adoc`.

`site/modules/ROOT/images/` is now the single source, keeping the published site
self-contained. `Lab_4_Compound_AI_Agents/images/` is deleted, and its three
consumers point at the surviving files:

| File | Now references |
|---|---|
| `PART_A.md:25,45,53` | `../site/modules/ROOT/images/lab4-*.png` |
| `PART_B.md:96` | `../site/modules/ROOT/images/lab4-mcp-connection.png` |
| `04_genie_agent.ipynb` | `raw.githubusercontent.com/.../main/site/modules/ROOT/images/lab4-*.png` |

The notebook's raw URLs only resolve once these changes land on `main`.
