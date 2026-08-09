# Align the Site

Suggested improvements to `site/`, drawn from the Antora site in
`/Users/ryanknight/projects/aws/neo4j-bedrock-graphrag-workshop`. That site runs
the same shape of workshop through six labs and a deck set, so its choices are
directly comparable.

**Scope:** structure, flow and format only. `fix-site-slides.md` already owns the
content fixes: dataset counts, the AuraDB Free tier claim, the notebook-first
split, the deck build. Nothing below repeats those.

**Reference layout:** 31 pages, 4 part pages, 1 slides page, 8 decks published as
their own gallery. **This site:** 13 pages plus 24 seven-line slide stubs, no part
pages, decks embedded as iframes.

---

## 1. The home page is a stub

- **Now:** `index.adoc` is 13 lines. Three links and a paragraph. The arc, the
  dataset, the architecture and the lab table all sit one click away in
  `workshop-overview.adoc`.
- **Reference:** `index.adoc` is 140 lines and is the whole front door. Welcome,
  At a Glance, the four-stage arc, the dataset, two architecture diagrams, lab
  tables with durations, prerequisites.
- **Do:** fold `workshop-overview.adoc` into `index.adoc`. Keep the arc, the
  diagram, the lab table with durations and the prerequisites. A participant
  landing cold should see what they are building without a second click.
- **Watch:** `workshop-overview.adoc` has two tables the reference has no
  equivalent of, "Which Aura Instance Each Lab Uses" and "Key Technologies".
  Both are good. Keep them, on the merged page.

## 2. No part pages, so the arc is invisible

- **Now:** `nav.adoc` has a bare text node, `Labs`, over six flat entries. Bare
  text does not click and has no landing page.
- **Reference:** four part pages group the labs into a story. Each is 11 to 19
  lines: what this part gets you, then its labs.
- **Do:** add three part pages and nest the labs under them. Suggested split,
  matching what the labs already do:
  - **Part 1, Graph Foundations:** Labs 1 and 2.
  - **Part 2, Retrieval:** Lab 3.
  - **Part 3, Agents:** Labs 4, 5 and 6.
- **Cost:** three files of about 15 lines each. It is the cheapest change here
  and it is the one that makes the sidebar readable.

## 3. Slides are 24 nav entries of iframe

- **Now:** 24 pages under `pages/slides/`, each 7 lines wrapping an iframe at a
  fixed 600px. Every one has its own nav line. Slides outnumber labs four to
  one in the sidebar.
- **Reference:** one `slides.adoc`. A table of `Deck | Covers | Pairs With`,
  linking out to a standalone gallery at `/slides`. The gallery index is
  generated from a deck manifest carrying title and description.
- **Do, recommended:** publish the decks as their own surface, the way the
  reference does. `deploy-antora.yml` copies `site/build/site` to `_site/workshop`,
  the deck build to `_site/slides`, and a small `landing/index.html` to the root.
  Replace the 24 stubs with one `slides.adoc` table.
- **Do, cheaper:** keep the iframes, but collapse the 24 nav lines to one
  `slides.adoc` index that links them, and add a full-screen "open deck" link on
  each. Fixes the sidebar, not the reading experience.
- **Take the first.** It also deletes the `../../site/modules/ROOT/images/` path
  mirroring in `build-slides.sh`, because a self-contained deck folder reaches
  nothing outside itself.

## 4. Lab pages have no link to their deck

- **Now:** zero lab pages reference a deck. The mapping exists only in the
  presenter's head.
- **Reference:** `slides.adoc` carries a `Pairs With` column pointing at labs.
- **Do:** both directions. A `Pairs With` column on the slides index, and one
  line on each lab page: "Slides for this lab: <deck>."

## 5. The lab page template is inconsistent

Six lab pages, four shapes. Verified:

| Page | At a Glance | TIP to notebook | Next Steps |
|---|---|---|---|
| lab1, lab2, lab3, lab6 | yes | yes | yes |
| lab4 | yes | no, uses "What You Build in This Lab" | yes |
| lab5 | yes | no | yes |
| appendix-a | yes | no | yes |

- **Reference:** every lab page is the same five parts, in order. Title, one
  paragraph placing the lab in the arc, `TIP` jump to the steps, `.**At a
  Glance**`, concept sections, `== Next Steps`.
- **Do:** add the missing `TIP` block to lab4, lab5 and appendix-a. Lab 4's
  "What You Build in This Lab" is useful content, so keep it as a section and
  put the `TIP` above it.

## 6. Lab 6 is the only lab with an instructions page

- **Now:** `lab6-instructions.adoc` is 706 lines, ten numbered procedure
  sections, cell-by-cell code. It is 25% of the site by line count. Labs 1 to 5
  moved their procedure into notebooks.
- **Reference:** every lab has an instructions page. The split is consistent
  either way, which is the point.
- **Do:** move the procedure into `01_agent_memory.ipynb` and cut the page,
  matching Labs 1 to 5. The notebook is where a participant runs the steps
  anyway, and the site copy is what goes stale.
- **Alternative:** keep it and restore instructions pages for all six labs.
  Larger job, and it reverses the notebook-first decision in `fix-site-slides.md`.

## 7. Missing pages the reference has

- **Lab 0, sign in.** The reference opens with a 26-line page on getting into the
  cloud console. This site starts at Lab 1 and assumes the Databricks workspace
  is already open. `vocareum/docs/README.md` covers it and never reaches the
  site. **Add a Lab 0 page.**
- **Configuration reference.** The reference has one page listing every
  credential, what it is and where it comes from. Here the secret scope,
  `GENIE_AGENT_ID`, `WAREHOUSE_ID` and the Aura URI are scattered across four lab
  pages. **Add `configuration.adoc`, one table.**
- **Production path.** The reference closes with 65 lines on what changes between
  a workshop and production, plus a resource list. This site ends at Lab 6 with
  no closing page. **Add one.** Most of the material is already written inside
  lab5 and lab6 as asides.
- **Admin setup.** The reference publishes its admin guide. Here
  `workshop-setup/README.md` stays in the repo. **Optional.** Publish it only if
  instructors are expected to read the site rather than the repo.

## 8. The dual-database explanation runs three times

- **Now:** `dual-database-architecture.svg` appears on `workshop-overview.adoc`
  and `lab1.adoc`, and the same argument is made a third time in prose on
  `databricks-platform.adoc`.
- **Reference:** one page owns each concept. The lab pages xref it rather than
  restating it.
- **Do:** the merged home page owns the dual-database split. `lab1.adoc` keeps
  its collapsible aside and drops the diagram. `databricks-platform.adoc` keeps
  the depth, the five integration patterns, and stops re-arguing the premise.

## 9. Sample queries cover two labs of six

- **Now:** `lab2-sample-queries.adoc` and `lab3-sample-queries.adoc` exist. Labs
  1, 5 and 6 have none, and Lab 6 has the most interesting Cypher in the
  workshop, the query that crosses memory and fleet.
- **Do:** add `lab6-sample-queries.adoc` when the instructions page is cut. The
  cross-half query and the reasoning-trace query are worth a page a participant
  can paste from.

## 10. Small format items

- **Home has no At a Glance.** Every reference overview page opens with one.
  Add it to the merged home page.
- **`Slides` and `Labs` in nav are bare text.** Point them at the slides index
  and at Part 1 once those pages exist.
- **Page length spread is wide.** 7 lines to 706. Under the changes above the
  spread lands at roughly 80 to 200, which matches the reference.
- **`site-extra.css` is 17 lines and identical to the reference.** Nothing to do.

---

## Order to do it in

1. **Part pages and nav.** Cheapest, and it makes the rest visible.
2. **Merge `workshop-overview.adoc` into `index.adoc`.**
3. **Slides gallery.** Deletes 24 pages and the asset mirroring together.
4. **Lab page template sweep.** Three `TIP` blocks, one deck link per lab.
5. **Cut `lab6-instructions.adoc` into the notebook.**
6. **New pages:** Lab 0, configuration, production path.
