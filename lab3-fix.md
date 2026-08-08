# Lab 3 defect: `data_utils` lands as a notebook, so `import data_utils` fails

Working document. Status as of 2026-08-08:

- **Done.** The legacy site 3 is deleted and its references are scrubbed. See The legacy cleanup.
- **Done.** B1 is measured. See B1, which is no longer a hypothesis.
- **Not done.** Neither delivery path is fixed. Sites 1 and 2 still ship a notebook, so a class running today still hits this.

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
| 1 | `dbx-vocareum/src/dbx_vocareum_tools/labruntime/voclab.py:271` | `NOTEBOOK_FORMATS = {..., ".py": ("SOURCE", "PYTHON"), ...}`, consumed at line 1743, posted at line 1759 | every Vocareum student | yes |
| 2 | `workshop-setup/auto_scripts/sync_notebooks.py:134-152` (`import_one`) | `body["format"] = "SOURCE"; body["language"] = "PYTHON"` | `/Shared/databricks-neo4j-workshop` on non-Vocareum workspaces | yes |
| 3 | `vocareum/courseware/neo4j-databricks-workshop.dat` and `.dbc` | zip entry `Lab_3_Semantic_Search/data_utils.py`; a zip archive import makes every entry a notebook | nobody | **deleted 2026-08-08** |

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

**One consequence for the path change.** Databricks strips the extension only on the AUTO-decides-notebook path. JUPYTER does not, which is why `notebook_workspace_path` strips it by hand and why that stripping has to stay for `.ipynb`. So the path change is conditional on format: keep the extension for AUTO, strip it for JUPYTER and SOURCE.

B1 is adopted. B2 below is kept only as the fallback that is no longer needed.

### B2: the Files API

`PUT /api/2.0/fs/files{path}` with the raw bytes. Deterministic. It creates a workspace file, no header analysis involved. Costs more code than B1: a second endpoint, a second content encoding since it is raw rather than base64, and a branch in `import_one` and in `notebook_import_one`.

### Blast radius

Fix B on `voclab.py` touches a shared tool other courses use. `NOTEBOOK_FORMATS` and `notebook_workspace_path` are generic, so any course shipping a `.py` changes behavior. B1 changes it silently. B2 changes it only on an explicit branch, which is the safer shape for a shared tool.

Fix B also fixes Lab 5, because a real workspace file is exactly what `ensure_lab3_on_path` searches for.

## The legacy cleanup

**Done on 2026-08-08.** `vocareum/courseware/` is deleted, `git rm -r`, and the five references below are rewritten. What was in it, for the record:

| Path | Notes |
| --- | --- |
| `neo4j-databricks-workshop.dat` | 34K zip, 5 files: the Lab 2 notebook, the 3 Lab 3 notebooks, `data_utils.py` |
| `neo4j-databricks-workshop.dbc` | byte-identical to the `.dat`, confirmed with `cmp` |
| `neo4j-databricks-workshop.cfg` | course config: cluster libraries, `shared_warehouse`, default catalog |
| `data/Lab_2_Databricks_ETL_Neo4j/01_aircraft_etl_to_neo4j.ipynb` | tracked copy |
| `data/Lab_3_Semantic_Search/` | tracked copies of the 3 notebooks plus `data_utils.py` |
| `aircraft_digital_twin_data.zip` | 2.1M |
| `dlt_fleet_etl.py` | 24.3K |
| `__pycache__/dlt_fleet_etl.cpython-314.pyc`, `data/Lab_3_Semantic_Search/__pycache__/data_utils.cpython-314.pyc` | committed bytecode |

**The `data/` copies have diverged.** `diff` reports `vocareum/courseware/data/Lab_3_Semantic_Search/data_utils.py` differs from the top-level file. `expand.md:67` names the cause, the 2026-08-08 secret-scope change landing on the top-level copies alone.

**`dlt_fleet_etl.py` is a byte-identical duplicate.** `diff -q vocareum/courseware/dlt_fleet_etl.py lab/courseware/dlt_fleet_etl.py` reports no difference. Nothing reads the `vocareum/` copy. `lab/workshop.py:204,208` sets `COURSEWARE_DIR = "/voc/scripts/courseware"` and `DLT_NOTEBOOK = f"{COURSEWARE_DIR}/dlt_fleet_etl.py"`, and `lab/courseware/` is what travels in the hook archive. The `vocareum/` copy is dead weight that can drift from the live one.

References rewritten alongside the directory:

- `vocareum/SETUP_GUIDE.md`, the `courseware/` table row and the sentence that existed to say the directory is not used, both replaced by one paragraph recording what was deleted and why
- `expand.md:67`, the "Known state" entry about the diverged copies, now a record of the deletion
- `expand.md:373` and `expand.md:587`, the deferred resync item and its Phase 4 checklist twin, both reframed. The Vocareum content job for Labs 5 and 6 is now editing `VOC_COURSE_NOTEBOOKS` in `lab/course.env`, which is real work, rather than rebuilding a bundle, which is not
- Six further "courseware bundle" mentions across `expand.md` (lines 17, 63, 427, 429, 612, 618, 624) renamed to "Vocareum notebook list"
- `.claude/settings.local.json`, eighteen permission entries for unzipping, copying and rebuilding those archives
- `lab/course.env`, the paragraph above `VOC_COURSE_NOTEBOOKS` that warned about the mirror, plus the "Unmeasured, and it matters" comment, which is now the measurement

Deleting the directory closed three open items and removed a third copy of the defect. Nothing pointed at it that was not itself a note explaining that nothing pointed at it.

## Recommendation

**Take Fix A now, B1 next.** Revised 2026-08-08, after the measurement and the cleanup landed.

Fix A is still the only thing that unblocks a class already running, because B1 needs a `dbx-vocareum` change, a push, a dependency resync here, and a `dbx-vocareum-upload`. None of that reaches a student mid-session.

B1 is no longer a gamble. Take it at both sites, as two changes each, format and path, and remove the Fix A cells in the same pass so the export call cannot fail against the new file object.

**One consolidation worth doing with it.** `sync_notebooks.py` already imports `voclab` for `VoclabError`, `ApiError` and `names_error_code`, but restates `voclab.NOTEBOOK_FORMATS` by hand in `import_one`. Read the map from `voclab` instead. Then the format rule is stated once, in the tool, and sites 1 and 2 stop being two sites.

## Open questions

1. ~~**Has `format=AUTO` been measured?**~~ Answered 2026-08-08. It has, and it does what B1 needs. See the table in B1.
2. **Does Lab 5 need the same treatment?** Yes, and more of it. `tools.py` imports `data_utils` and must itself be a workspace file. It is delivered nowhere today, so add it to `VOC_COURSE_NOTEBOOKS` and to `sync_notebooks.py` only after Fix B lands, or it ships broken on arrival.
3. **Does keeping `.py` on the workspace path break anything else?** `voclab.py` names the first imported notebook as the landing page through `voclab_notebook_path`. A `.py` helper is never first in `VOC_COURSE_NOTEBOOKS`, but confirm no other course puts one there.
4. **Do the other extensions in `NOTEBOOK_FORMATS` want the same change?** `.sql`, `.scala` and `.r` are almost certainly meant to stay notebooks. Scope Fix B to `.py` unless a course says otherwise.
5. **Does `dbutils.import_notebook("data_utils")`, which the error message suggests, actually work here?** Untested. It would be a smaller notebook-side change than Fix A, but it binds the labs to a Databricks-only API and would break the plain-Python import path the repository checkout uses. Not recommended, but worth one measurement before Fix A is written into three notebooks.
