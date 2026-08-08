# Superseded: updating Vocareum when labs change

This file described a hand-run ritual: copy each changed notebook into
`vocareum/courseware/data/`, rebuild `neo4j-databricks-workshop.dat` and its
byte-identical `.dbc` twin with `zip -r`, diff the two, then upload both to
`/voc/private/courseware/` through the Vocareum UI. None of that is how the
course reaches Vocareum any more, and following it now would build archives
nothing reads.

**Deletion is proposed for this file.** Nothing in the repository links to it.
It is left in place only so that whoever finds it does not follow it.

## What replaced it

The notebooks live in one place, the repository's `Lab_2_Databricks_ETL_Neo4j/`
and `Lab_3_Semantic_Search/` directories. `lab/` reaches them by symlink,
`VOC_COURSE_NOTEBOOKS` in `lab/course.env` states which of them ship, and one
upload carries the whole of `lab/` to `/voc/scripts` with a hash check on every
member:

```bash
uv run dbx-vocareum-upload lab/ --dry-run   # show the archive, send nothing
uv run dbx-vocareum-upload lab/             # upload and verify
```

Exit `3` means a hash mismatch. Do not start a lab against it.

`voclab.py notebook-import`, called from `lab/user_setup.sh`, then places each
named notebook in the student's own workspace folder and skips one that is
already there, which is what preserves a student's work across a stop. A bundle
that unpacks again on resume hands the student a blank copy of the notebook they
spent the first session filling in, and that is one of the two reasons the
bundle route was dropped. The other is that nothing had ever measured what
Vocareum does with the `.cfg` `content.src` and `content.entry` keys, while the
import route ran end to end on 2026-08-07 and placed the notebook where it said
it would.

The staging copy under `vocareum/courseware/data/` was a second copy of files
that already existed in the repository, and the guide that maintained it said
outright that skipping the ritual meant Vocareum silently drifting from the
workshop everyone else runs. Deleting the second copy deleted the drift.

## Where to look instead

| Question | Where |
|----------|-------|
| What provisions the workshop, and what is still manual | [`../README.md`](../README.md) |
| Which files ship to a Vocareum student | `lab/course.env`, `VOC_COURSE_NOTEBOOKS` |
| What the four hooks do and in what order | `lab/README.md` |
| Deploying, and the admin-side Vocareum steps | [`../../vocareum/SETUP_GUIDE.md`](../../vocareum/SETUP_GUIDE.md) |
| Vocareum REST API shapes, including the nesting measurement | `dbx-vocareum/docs/vocareum-api.md` |
</content>
