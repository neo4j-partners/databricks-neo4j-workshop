# Align the Site

Suggested improvements to `site/`, drawn from the Antora site in
`/Users/ryanknight/projects/aws/neo4j-bedrock-graphrag-workshop`. That site runs
the same shape of workshop through six labs and a deck set, so its choices are
directly comparable.

**Status:** implemented. Each item below records what shipped. Two were skipped
on purpose, and both say why.

**Scope:** structure, flow and format only. `fix-site-slides.md` owns the
content fixes: dataset counts, the AuraDB Free tier claim, the notebook-first
split, the deck build. Nothing below repeats those.

---

## 1. The home page was a stub. Done

- **Was:** `index.adoc` at 13 lines. Three links and a paragraph. The arc, the
  dataset, the architecture and the lab table all sat one click away.
- **Now:** `workshop-overview.adoc` is folded into `index.adoc` and deleted.
  The home page carries the welcome, an At a Glance, the dataset, both
  architecture diagrams, the lab table with durations and part rows,
  prerequisites and the reference links.
- **Kept:** the two tables the reference has no equivalent of, "Which Aura
  Instance Each Lab Uses" and "Key Technologies".
- **Followed through:** the four inbound xrefs on `lab6.adoc`,
  `databricks-platform.adoc` and `nav.adoc`, plus the `README.md` link, which
  pointed at a page that no longer exists.

## 2. No part pages, so the arc was invisible. Done

- **Was:** a bare text node, `Labs`, over six flat entries. Bare text does not
  click and has no landing page.
- **Now:** three part pages, each with an At a Glance, a lab table, its decks
  and a Next Steps:
  - `part1-graph-foundations.adoc`, Labs 1 and 2.
  - `part2-retrieval.adoc`, Lab 3.
  - `part3-agents.adoc`, Labs 4, 5 and 6.
- **`nav.adoc` nests the labs under them.** No bare text nodes are left.

## 3. Slides were 15 nav entries of iframe. Done, the cheaper way

- **Was:** 15 pages under `pages/slides/`, each 7 lines wrapping an iframe at a
  fixed 600px, each with its own nav line.
- **Now:** `slides.adoc` is one index carrying two `Deck | Covers | Pairs With`
  tables, workshop decks and additional background. It is the nav entry; the 15
  wrappers nest under it. Every wrapper gained an **Open full screen** link and
  a link back to the index.
- **The reference's own-surface gallery was rejected.** It would have reworked
  `deploy-antora.yml` into `_site/workshop` plus `_site/slides` plus a landing
  page, moving every published URL, and it reverses the iframe-wrapper decision
  `fix-site-slides.md` already made and CI already implements.

## 4. Lab pages had no link to their deck. Done

- **Was:** zero lab pages referenced a deck. The mapping lived in the
  presenter's head.
- **Now:** both directions. `slides.adoc` carries the `Pairs With` column, and
  every lab page plus `appendix-a.adoc` carries a "Slides for this lab" line
  above its Next Steps. The part pages list their decks too.

## 5. The lab page template was inconsistent. Done

- **Was:** six lab pages, four shapes. `lab4`, `lab5` and `appendix-a` had no
  `TIP` block pointing at their notebooks.
- **Now:** all seven pages are Title, lede, `TIP` to the notebooks,
  `.**At a Glance**`, concept sections, `== Next Steps`. Lab 4's "What You Build
  in This Lab" stayed, with the `TIP` above it.

## 6. Lab 6 was the only lab with an instructions page. Done

- **Was:** `lab6-instructions.adoc`, 706 lines, ten numbered procedure sections,
  cell-by-cell code. The last instructions page on the site.
- **Now:** deleted. `01_agent_memory.ipynb` already carried every section,
  including the cleanup, so nothing moved. The three xrefs on `lab6.adoc` and
  the nav entry point at the notebook, matching Labs 1 to 5.

## 7. Missing pages the reference has. Partly done

- **Production path. Added.** `production-path.adoc` covers what changes between
  the workshop and production: the tier, memory off the hot path, the pinned
  fork, degrade-do-not-fail, the credential split, and index quota. Every claim
  comes from a measurement or a decision `lab5.adoc` and `lab6.adoc` already
  record.
- **Lab 0, sign in. Skipped.** Not requested.
- **Configuration reference. Dropped from the plan.** Every credential name
  (`SECRET_SCOPE`, `GENIE_AGENT_ID`, `WAREHOUSE_ID`) already lives in the
  notebook that uses it, and the site pages only mention them in prose. A config
  table on the site would be a second copy of notebook content, which is exactly
  the leak item 6 removed.
- **Admin setup. Skipped.** `workshop-setup/README.md` stays in the repo, where
  instructors already read it.

## 8. The dual-database explanation ran three times. Done

- **Was:** `dual-database-architecture.svg` on `workshop-overview.adoc` and
  `lab1.adoc`, and the same argument a third time in prose on
  `databricks-platform.adoc`.
- **Now:** the merged home page owns the split and the diagram. `lab1.adoc`
  keeps its collapsible aside, drops the diagram and xrefs the overview.
  `databricks-platform.adoc` keeps the depth and the five integration patterns,
  and points at the overview rather than restating the roadmap.

## 9. Sample queries covered two labs of six. Done for Lab 6

- **Was:** `lab2-sample-queries.adoc` and `lab3-sample-queries.adoc` only, while
  Lab 6 held the most interesting Cypher in the workshop.
- **Now:** `lab6-sample-queries.adoc` carries the memory-half schema table, the
  counting queries, the shift-handover query that crosses both halves, and the
  reasoning-trace audit query. Every query is copied verbatim from
  `01_agent_memory.ipynb` or `02_instructor_demos.ipynb` rather than written for
  the page.
- **Labs 1 and 5 still have none.** Lab 1's Cypher is inline on the page already,
  and Lab 5 runs its queries through the agent rather than by hand.

## 10. Small format items. Done

- **Home now opens with an At a Glance**, matching every reference overview page.
- **No bare text nav nodes remain.** `Labs` became three part pages and `Slides`
  became `slides.adoc`.
- **Page length spread is now 9 to 353 lines**, against 7 to 706 before. The
  353 is `lab3-sample-queries.adoc`, a query reference that is meant to be long.
  Excluding the two sample-query pages, the spread is 9 to 216.
- **`site-extra.css` is 17 lines and identical to the reference.** Nothing to do.

---

## Verification

- `npm run build` in `site/` is warning-free.
- A link check across all 17 emitted pages finds 0 broken local `href` or `src`,
  which covers fragment anchors and all 15 deck iframes.
- All 7 lab pages carry exactly one each of `TIP`, `At a Glance`, "Slides for
  this lab" and `== Next Steps`.
- Every `Covers` cell in `slides.adoc` was checked against its deck's own
  headings. Ten were rewritten after that check, including two that were wrong:
  the retriever deck covers Text2Cypher rather than hybrid retrievers, and the
  auth-sync deck is a prototype under review rather than shipped guidance.
- Every query in `lab6-sample-queries.adoc` is copied from a notebook cell.

## Open defect, not fixed

`lab4.adoc` and `lab5.adoc` both say the Databricks secret scope was **written
in Lab 3**. `Lab_1_Aura_Setup/02_credentials_and_cypher.ipynb` is what creates
it, and `lab1.adoc` says so. Two pages against one notebook and one page.
Left alone pending a decision, because it is pre-existing content rather than
part of this work.
