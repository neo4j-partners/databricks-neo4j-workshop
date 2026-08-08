# Lab 3 defect: `data_utils` lands as a notebook, so `import data_utils` fails

Working document. Status as of 2026-08-08:

- **Done.** The legacy site 3 is deleted and its references are scrubbed. See The legacy cleanup.
- **Done.** B1 is measured. See B1, which is no longer a hypothesis.
- **Done.** Site 1 is fixed, scoped to `.py`. See What was fixed, and how.
- **Not done.** Site 2, `sync_notebooks.py`, still ships a notebook to non-Vocareum workspaces.
- **Not done here.** The fix reaches students only after a dependency resync and an upload from this repository. See Getting the fix to a student.
- **Dead.** B2 is not available. The Files API refuses a `/Workspace` path outright. See B2.

## What was fixed, and how

**Site 1, `neo4j-partners/dbx-vocareum`, commit `68e63a5`.** B1, scoped to `.py`. Three files, 109 insertions, and the full test suite green.

Two edits in `src/dbx_vocareum_tools/labruntime/voclab.py`, which is the "two changes, not one" this document already called for:

1. **`NOTEBOOK_FORMATS[".py"]`** from `("SOURCE", "PYTHON")` to `("AUTO", None)`. The other plain-text extensions stay `SOURCE`. Nothing imports a `.sql` or a `.scala`, so a notebook is what a course naming one is asking for, and moving them would silently change what arrives. That answers open question 4.
2. **A new `NOTEBOOK_KEEP_EXTENSIONS = (".py",)`**, read by `notebook_workspace_path`. `.py` keeps its extension on the target path. Everything else is still stripped.

Neither edit works alone, and the reason is sharper than "two changes". A third measurement, which this document did not have when it recommended B1, is that **AUTO stores anything at an extensionless path as a FILE, whatever the content**. So shipping edit 1 without edit 2 would not merely leave `data_utils` broken. It would turn every `.ipynb` in every course into a workspace file, silently, because `voclab.py` strips the extension before it posts. The scoping to `.py` is what contains that.

The comment blocks on both constants carry the measurements, because `labruntime/README.md` in that repository is the canonical account of what runs in Vocareum and it stated the old rule as fact. Its notebook-delivery section was rewritten in the same commit.

### Tests

Three added to `tests/test_voclab.py`, one fixture corrected:

| Test | What it pins |
| --- | --- |
| `test_a_python_module_keeps_its_extension_on_the_way_in` | the path half of the change |
| `test_a_python_module_is_imported_as_auto_with_no_language` | `format=AUTO`, and no `language` key in the body |
| `test_a_module_the_student_already_has_is_left_alone` | the check and the write name the same path, so a returning student is not overwritten |
| `test_every_parent_folder_is_created_before_any_notebook_is_written` | its fixture stubbed `Lab_3/data_utils` and now stubs `Lab_3/data_utils.py`. It failed on the first run of the change, which is the test doing its job |

### A hazard this document did not name

`notebook_import_one` is idempotent by skipping a taken path, and `notebook_exists` decides that by asking `GET /api/2.0/workspace/get-status` for **the path `voclab.py` itself constructed**. If the path written and the path checked ever differ, the check 404s on every run, `user_setup.sh` re-imports on every start including the one after a `stop`, and the student's work is destroyed. That is the same class of mistake the `$VOC_END_LAB_BEHAVIOR` branch in `lab_end.sh` exists to avoid.

So "keep the extension" cannot be a general rule. It is safe for `.py` only because of where the extension survives, which is decided by Databricks and differs by format. **Measured 2026-08-08**, importing into `/Users/<email>/scratch-jupyter-probe` and reading the stored paths back from `workspace list`:

| format | outcome | stored path |
| --- | --- | --- |
| `JUPYTER`, path `jup_ext.ipynb` | NOTEBOOK | `jup_ext.ipynb`, **extension kept** |
| `JUPYTER`, path `jup_noext` | NOTEBOOK | `jup_noext` |
| `AUTO` deciding FILE | FILE | as written, extension kept |
| `AUTO` deciding NOTEBOOK | NOTEBOOK | extension stripped by Databricks |

**This corrects a claim made during the fix and confirms line 138 of this document.** An intermediate version of the code comment asserted that Databricks strips the extension off every notebook, so keeping `.ipynb` would 404 the existence check forever. That is false for `JUPYTER`, which is the format `.ipynb` actually uses: it stores at the path as written. Stripping `.ipynb` remains correct for the original cosmetic reason only, that a notebook displayed as `00_cluster_smoke_test.ipynb` reads to a student as a stray file. The 404 hazard is real but reachable only through the fourth row, which no entry in `NOTEBOOK_FORMATS` can reach today. `NOTEBOOK_KEEP_EXTENSIONS` is a list of one rather than a rule so that it stays unreachable.

### Getting the fix to a student

The fix is in a separate repository and does not arrive by editing this one. `dbx-vocareum-upload` injects `voclab.py` **from the installed package**, and this repository pins that package by commit:

```
uv.lock:279  source = { git = "...dbx-vocareum.git#9402144dc1985d5e08f1e701532f9f47504e8a3e" }
```

Uploading against that lock ships the defect, verifies it by hash, and reports success. The order is:

```bash
uv lock --upgrade-package dbx-vocareum-tools && uv sync
rtk proxy grep -n '".py":' .venv/lib/python3.13/site-packages/dbx_vocareum_tools/labruntime/voclab.py
# must read ("AUTO", None) before going further
uv run dbx-vocareum-upload lab/ --dry-run
uv run dbx-vocareum-upload lab/
```

No version bump is involved. `pyproject.toml:23` names the dependency as `git+https://...` with no tag and no rev, so it tracks the branch and `uv.lock` is the only pin.

**Rerun Init does not deliver this.** `notebook-import` is called only from `lab/user_setup.sh:126`; `workspace_init.sh` never calls it. Students get the fixed delivery on their **next session start**.

**Returning students get a second object, not a replacement.** The stored path changes from `.../data_utils`, a NOTEBOOK, to `.../data_utils.py`, a FILE. Different paths, so the existence check misses and the import writes the new file **alongside** the stale notebook rather than skipping. Nothing has to be deleted for the import to succeed. Whether the stale extensionless `data_utils` notebook still shadows the new file on `from data_utils import ...` has **not** been measured. Check it on the first returning student. A fresh lab identity is clean either way.

### The notebooks need no change

All four import sites across the three Lab 3 notebooks are bare `from data_utils import ...`, and no Fix A bootstrap cell was ever added to any of them. B1 is the whole fix on the notebook side, and there is nothing to remove in the same pass.

## What broke

A participant on Vocareum ran `Lab_3_Semantic_Search/01_data_and_embeddings.ipynb` and got:

```
NotebookImportException: Unable to import module `data_utils`. The following file appears to be a notebook:

/Workspace/Users/labuser16122702_1786222711@vocareum.com/Lab_3_Semantic_Search/data_utils.py

Importing notebooks directly is not supported. Use dbutils.import_notebook("data_utils") instead.
[Trace ID: 00-918c924d556c01e742a920852cf0df65-8fb75f48073d96d9-00]
```

Every Lab 3 notebook is blocked. The failing cell is the first one that runs real work.

| Notebook | First `from data_utils import` |
| --- | --- |
| `Lab_3_Semantic_Search/01_data_and_embeddings.ipynb` | cell 4 |
| `Lab_3_Semantic_Search/02_graphrag_retrievers.ipynb` | cell 2 |
| `Lab_3_Semantic_Search/03_hybrid_retrievers.ipynb` | cell 2 |

## How to reproduce

1. Start a Vocareum lab so `lab/user_setup.sh:126` runs `voc_voclab notebook-import --user "$user_email"`.
2. Open `Lab_3_Semantic_Search/01_data_and_embeddings.ipynb` in the student's own folder.
3. Run the cells in order. Cell 4 raises `NotebookImportException`.

Confirm the object type without running the notebook:

```bash
databricks workspace get-status /Users/<email>/Lab_3_Semantic_Search/data_utils
```

`object_type: NOTEBOOK` is the defect. `object_type: FILE` is the goal state.

## Root cause

`data_utils.py` reaches the workspace as a **notebook object**, not a workspace file. `/Workspace` surfaces a PYTHON notebook to the driver filesystem with a `.py` suffix, so Python's import machinery finds a plausible module on `sys.path`, the Databricks loader inspects it, sees a notebook, and refuses.

The cause is the `POST /api/2.0/workspace/import` call being made with `format=SOURCE, language=PYTHON`. That pair always produces a notebook. There is no header or content analysis in that path.

**Correction to the reported description.** The stored workspace path has **no extension**. Both delivery paths strip it:

- `voclab.py`, `notebook_workspace_path`: `stem = os.path.splitext(relative_name)[0]`, docstring "The extension comes off."
- `workshop-setup/auto_scripts/sync_notebooks.py:210`: `remote_path = f"{SHARED_FOLDER}/{subfolder}/{local_path.stem}"`

So the object is `/Users/<email>/Lab_3_Semantic_Search/data_utils`. The `.py` in the error message is the FUSE view of a PYTHON notebook, not the stored name. This matters twice below: it changes the path Fix A must export, and it means Fix B is **two** changes, not one.

**Also verified.** `Lab_3_Semantic_Search/data_utils.py` starts with a module docstring. It carries no `# Databricks notebook source` header. That is the precondition the `format=AUTO` hypothesis needs.

## The three sites carrying the same mistake

| # | Site | The line | Reaches | Live? |
| --- | --- | --- | --- | --- |
| 1 | `dbx-vocareum/src/dbx_vocareum_tools/labruntime/voclab.py:271` | `NOTEBOOK_FORMATS = {..., ".py": ("SOURCE", "PYTHON"), ...}`, consumed at line 1743, posted at line 1759 | every Vocareum student | **fixed 2026-08-08**, commit `68e63a5` |
| 2 | `workshop-setup/auto_scripts/sync_notebooks.py:134-152` (`import_one`) | `body["format"] = "SOURCE"; body["language"] = "PYTHON"` | `/Shared/databricks-neo4j-workshop` on non-Vocareum workspaces | yes |
| 3 | `vocareum/courseware/neo4j-databricks-workshop.dat` and `.dbc` | zip entry `Lab_3_Semantic_Search/data_utils.py`; a zip archive import makes every entry a notebook | nobody | **deleted 2026-08-08**, off disk and untracked |

Site 1 is a **separate repository**, `neo4j-partners/dbx-vocareum`, depended on through `pyproject.toml`. The file list comes from `VOC_COURSE_NOTEBOOKS` in `lab/course.env:113-118`, which names `Lab_3_Semantic_Search/data_utils.py` as its last entry.

The comment block above that variable, `lab/course.env:109-112`, already called this shot:

> Unmeasured, and it matters: Lab 3 does `from data_utils import ...`, which needs
> a workspace file. notebook-import creates a workspace notebook and strips the
> extension. Whether that import resolves has not been tested. data_utils.py is
> named here because absent is certainly broken and present may not be.

The error is the measurement. It resolves the way the comment feared.

Site 3 was dead and is now gone. It is kept in the table because it is the reason the mistake had three copies, and because deleting it is what closed the three `expand.md` items that had been keeping it alive on a to-do list.

## Lab 5 has the same exposure, not yet triggered

`Lab_5_LangGraph_Agent/tools.py:42-76` (`ensure_lab3_on_path`) searches four candidate directories for a real `data_utils.py` using `Path.is_file()`, then does `from data_utils import ...` at line 80. A notebook object satisfies `is_file()` through the FUSE view and then fails the same way at import.

Lab 5 is **not delivered anywhere today**. It appears in neither `VOC_COURSE_NOTEBOOKS` nor the `NOTEBOOKS` tuple in `sync_notebooks.py`. When it is added, it needs `tools.py` as a workspace file too, so it carries a double exposure, not a single one.

## Fix A: notebook-side bootstrap cell

One cell added above the first `from data_utils import ...` in the three Lab 3 notebooks. It exports the workspace notebook object as SOURCE, writes it to a real `.py` on the driver, and puts that directory on `sys.path`.

```python
import base64, os, sys
from databricks.sdk import WorkspaceClient

folder = os.path.dirname(
    dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
)
src = base64.b64decode(
    WorkspaceClient().workspace.export(path=f"{folder}/data_utils", format="SOURCE").content
).decode()
os.makedirs("/tmp/lab3_modules", exist_ok=True)
open("/tmp/lab3_modules/data_utils.py", "w").write(src)
sys.path.insert(0, "/tmp/lab3_modules")
```

**Corrected from the proposal.** The export path is `f"{folder}/data_utils"`, without `.py`. Both delivery paths strip the extension, so `f"{folder}/data_utils.py"` would 404 on Vocareum today. Should Fix B land later and turn the object into a real file, the export call fails and the cell needs a fallback or removal, so Fix A is a temporary measure by construction.

**Pros:** works whichever delivery path put the file there. Unblocks a class that is running now. No cross-repo change and no redeploy.

**Cons:** three notebooks carry a bootstrap cell of noise a participant has to be told to ignore. Does nothing for `Lab_5_LangGraph_Agent/tools.py`. Silently breaks when the object becomes a file.

**Note:** the exported SOURCE gains a leading `# Databricks notebook source` comment line. Harmless Python.

## Fix B: fix the delivery

Make `.py` land as a workspace file. **This is two changes per site, not one.** Changing only the format leaves the extension stripped, and a workspace file named `data_utils` with no suffix is invisible to `import data_utils`. Both of these must move together:

1. the `format` and `language` sent to `workspace/import`
2. the path construction, so `.py` keeps its extension

Site 1: `voclab.py` `NOTEBOOK_FORMATS` at line 271 and `notebook_workspace_path` at line 1674. Site 2: `sync_notebooks.py` `import_one` at lines 134-152 and the `local_path.stem` at line 210.

`notebook_workspace_path` stripping the extension is deliberate and correct for `.ipynb`, so the change has to be conditioned on the format rather than removed.

### B1: `format=AUTO`, no `language` field

**Measured 2026-08-08** against workspace `dbc-cc887abc-9779.cloud.databricks.com`, importing the same header-less file three ways and reading `object_type` back from `/api/2.0/workspace/list`:

| posted path | format | `object_type` | stored path |
| --- | --- | --- | --- |
| `plain.py` | `SOURCE` + `PYTHON` | `NOTEBOOK` | `plain.py` |
| `plain.py` | `AUTO` | **`FILE`** | `plain.py` |
| `headered.py`, first line `# Databricks notebook source` | `AUTO` | `NOTEBOOK` | `headered`, extension stripped by Databricks |

AUTO does what the documentation says. A header-less `.py` becomes a file and keeps its extension; the header is how a course states it meant a notebook, and Databricks strips the extension itself in that case. `Lab_3_Semantic_Search/data_utils.py` opens with a module docstring and carries no header, verified.

The first row also reproduces the defect exactly: SOURCE plus PYTHON on a header-less file gives a notebook whose path keeps `.py`, which is what the participant's traceback shows.

**One consequence for the path change.** Databricks strips the extension only on the AUTO-decides-notebook path. JUPYTER does not, which is why `notebook_workspace_path` strips it by hand and why that stripping has to stay for `.ipynb`. So the path change is conditional on format: keep the extension for AUTO, strip it for JUPYTER and SOURCE. Confirmed by direct measurement during the fix; see the table in A hazard this document did not name.

**A third row the table above was missing.** Posting to a path with **no extension at all** gives a FILE under AUTO, whatever the content, including a `.ipynb` payload. That is why edit 1 without edit 2 would have turned every notebook in every course into a workspace file.

B1 is adopted and shipped, scoped to `.py`.

### B2: the Files API, and why it is dead

The proposal was `PUT /api/2.0/fs/files{path}` with the raw bytes: deterministic, a workspace file, no header analysis. **Measured 2026-08-08 and it does not work.** The Files API refuses a workspace path outright:

```json
{
  "error_code": "BAD_REQUEST",
  "message": "Invalid path: unsupported first path component: Workspace",
  "details": [{"reason": "FILES_API_INVALID_PATH", "domain": "filesystem.databricks.com"}]
}
```

It accepts `/Volumes` and not `/Workspace`. B2 is not a fallback, it is not available. Do not reach for it if B1 is ever revisited.

### Blast radius

Fix B on `voclab.py` touches a shared tool other courses use. `NOTEBOOK_FORMATS` and `notebook_workspace_path` are generic, so any course shipping a `.py` changes behavior, and B1 changes it silently. That is the cost that was accepted, and the containment is the scoping: only `.py` moved, and only `.py` keeps its extension. The behavior change another course would notice is a `.py` that used to arrive as a notebook and now arrives as a workspace file. A course that wanted the notebook says so by putting `# Databricks notebook source` on the file's first line, which is the line Databricks' own export writes.

Fix B also fixes Lab 5, because a real workspace file is exactly what `ensure_lab3_on_path` searches for.

## The legacy cleanup

**Done on 2026-08-08.** `vocareum/courseware/` is off disk and no longer tracked, and the references below are rewritten. The deletion ran in two passes: `dlt_fleet_etl.py` and the committed bytecode went first, and the remaining 10 files, 2.3M, went last, which is when the three documents that had already recorded the deletion became true. What was in it, for the record:

| Path | Notes |
| --- | --- |
| `neo4j-databricks-workshop.dat` | 34K zip, 5 files: the Lab 2 notebook, the 3 Lab 3 notebooks, `data_utils.py` |
| `neo4j-databricks-workshop.dbc` | byte-identical to the `.dat`, confirmed with `cmp` |
| `neo4j-databricks-workshop.cfg` | course config: cluster libraries, `shared_warehouse`, default catalog |
| `data/Lab_2_Databricks_ETL_Neo4j/01_aircraft_etl_to_neo4j.ipynb` | tracked copy |
| `data/Lab_3_Semantic_Search/` | tracked copies of the 3 notebooks plus `data_utils.py` |
| `aircraft_digital_twin_data.zip` | 2.1M. Nothing replaces it, see below |
| `.DS_Store` | untracked, 6.0K |
| `dlt_fleet_etl.py` | 24.3K, deleted in the first pass |
| `__pycache__/dlt_fleet_etl.cpython-314.pyc`, `data/Lab_3_Semantic_Search/__pycache__/data_utils.cpython-314.pyc` | committed bytecode, deleted in the first pass |

**The zip's build script went with it.** `workshop-setup/auto_scripts/build_data_zip.py` was the only thing that wrote `aircraft_digital_twin_data.zip`, and it is deleted too. The zip had no consumer, and could not have had one: the files it packed are tracked at `workshop-setup/aircraft_digital_twin_data/`, so anyone setting up outside Vocareum has them from the clone, and the Vocareum path reads that directory through the `lab/courseware/` symlink and never sees an archive. Across the whole repository the zip was named only by this document recording its size and by the script's own README entry.

The script was well built, which is why keeping it was considered first: it took its file list from `lab/workshop.py`'s `data_files()` so it could not drift from what the volume gets, staged to `.zip.partial` and `os.replace`d, verified with `testzip()` plus a per-entry size check, and fixed every timestamp at 1980 so two runs were byte-identical. None of that gives an artifact nobody fetches a reason to exist. The determinism was also the answer to a drift the tracked zip had already suffered, missing `nodes_operating_limits.csv` and carrying pre-recalibration `nodes_readings.csv`, `nodes_sensors.csv` and five maintenance manuals. Deleting both the artifact and its builder removes the drift and the machinery against it in one move.

**The `data/` copies had diverged.** Before the deletion, `diff` reported `vocareum/courseware/data/Lab_3_Semantic_Search/data_utils.py` differing from the top-level file. `expand.md:67` names the cause, the 2026-08-08 secret-scope change landing on the top-level copies alone.

**`dlt_fleet_etl.py` was a byte-identical duplicate.** `diff -q` against `lab/courseware/dlt_fleet_etl.py` reported no difference, and nothing read the `vocareum/` copy. `lab/workshop.py:204,208` sets `COURSEWARE_DIR = "/voc/scripts/courseware"` and `DLT_NOTEBOOK = f"{COURSEWARE_DIR}/dlt_fleet_etl.py"`, and `lab/courseware/` is what travels in the hook archive. `lab/courseware/dlt_fleet_etl.py` is the surviving copy and is untouched.

References rewritten alongside the directory:

- `vocareum/SETUP_GUIDE.md`, the `courseware/` table row and the sentence that existed to say the directory is not used, both replaced by a paragraph recording what was deleted and why, plus a table saying where each deleted thing lives now
- `expand.md:67`, the "Known state" entry about the diverged copies, now a record of the deletion
- `expand.md:373` and `expand.md:587`, the deferred resync item and its Phase 4 checklist twin, both reframed. The Vocareum content job for Labs 5 and 6 is now editing `VOC_COURSE_NOTEBOOKS` in `lab/course.env`, which is real work, rather than rebuilding a bundle, which is not
- Six further "courseware bundle" mentions across `expand.md` (lines 17, 63, 427, 429, 612, 618, 624) renamed to "Vocareum notebook list"
- `.claude/settings.local.json`, eighteen permission entries for unzipping, copying and rebuilding those archives
- `lab/course.env`, the paragraph above `VOC_COURSE_NOTEBOOKS` that warned about the mirror, plus the "Unmeasured, and it matters" comment, which is now the measurement
- `workshop-setup/auto_scripts/README.md`, the `build_data_zip.py` table row and the "The data zip" section, both removed, and the opening count corrected from three programs to two

Deleting the directory closed three open items and removed a third copy of the defect. Nothing pointed at it that was not itself a note explaining that nothing pointed at it, or the one script that wrote into it, which is deleted too.

## Recommendation

**B1 is done at site 1.** Revised 2026-08-08, after the fix landed.

Fix A was never written into the notebooks and is now not worth writing. It was the only thing that could unblock a class already running mid-session, and no class is. It also breaks by construction once B1 lands, because the export call it makes has no object to export.

What remains:

1. **Resync and upload from this repository.** See Getting the fix to a student. Nothing reaches a student until that happens.
2. **Site 2, `sync_notebooks.py`.** Same two changes: `import_one` at lines 134-152 and the `local_path.stem` at line 210. Non-Vocareum workspaces still get a notebook.
3. **The consolidation that makes site 2 stop existing.** `sync_notebooks.py` already imports `voclab` for `VoclabError`, `ApiError` and `names_error_code`, but restates `voclab.NOTEBOOK_FORMATS` by hand in `import_one`. Read the map from `voclab` instead, and take `NOTEBOOK_KEEP_EXTENSIONS` with it for the path half. Then the format rule is stated once, in the tool, and sites 1 and 2 stop being two sites. Doing the consolidation *is* doing item 2.

## Open questions

1. ~~**Has `format=AUTO` been measured?**~~ Answered 2026-08-08. It has, and it does what B1 needs. See the table in B1.
2. **Does Lab 5 need the same treatment?** Yes, and more of it. `tools.py` imports `data_utils` and must itself be a workspace file. It is delivered nowhere today, so add it to `VOC_COURSE_NOTEBOOKS` and to `sync_notebooks.py` only after Fix B lands, or it ships broken on arrival.
3. **Does keeping `.py` on the workspace path break anything else?** Partly answered. The idempotency question is settled: AUTO stores a headerless module at the path as written, so the write and the `get-status` check agree and a returning student is not overwritten, pinned by `test_a_module_the_student_already_has_is_left_alone`. Still open is the landing page. `voclab.py` names the first imported notebook as the landing page through `voclab_notebook_path`, and a `.py` first in `VOC_COURSE_NOTEBOOKS` would now point it at a workspace file. This course never does that. Confirm no other course does.
4. ~~**Do the other extensions in `NOTEBOOK_FORMATS` want the same change?**~~ Answered 2026-08-08. No. `.sql`, `.scala` and `.r` stayed `SOURCE`, and the fix is scoped to `.py`.
5. **Does `dbutils.import_notebook("data_utils")`, which the error message suggests, actually work here?** Untested and now moot for Lab 3, since Fix A is not being written. Left on the list because Lab 5 may want it if `tools.py` ever ships before its delivery is fixed.
6. **Does a stale `data_utils` notebook shadow the new `data_utils.py` file?** Unmeasured, and it is the one thing that could make a returning student's session still fail after the upload. Both objects will sit in the same folder. Check it on the first returning student.
