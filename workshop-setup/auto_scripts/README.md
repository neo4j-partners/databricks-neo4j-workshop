# Admin scripts

Two programs, for the case where this workshop runs in a Databricks workspace an
instructor provisioned by hand rather than one Vocareum created. They are the two
jobs `lab/workshop.py` and `voclab.py` do not cover.

They define nothing. Every catalog, schema, volume, table and pipeline name they
touch is read from `lab/workshop.py`, which is this course's one definition of
its Databricks objects.

| Script | What it does |
| --- | --- |
| `sync_notebooks.py` | Publishes the lab notebooks into `/Shared/databricks-neo4j-workshop` so participants can browse and clone them. |
| `teardown.py` | Deletes the catalog, its schemas, the volume, the `Fleet Digital Twin ETL` pipeline and the shared notebook tree. |
| `workshop_module.py` | Not a command. The seam that puts `lab/workshop.py` on the import path for the two above. |

## Running them

Run from the repository root, so `uv` resolves `dbx-vocareum-tools`, which is
where `voclab.py` and therefore the HTTP layer come from.

```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=dapi...

uv run python workshop-setup/auto_scripts/sync_notebooks.py
uv run python workshop-setup/auto_scripts/teardown.py           # prompts
uv run python workshop-setup/auto_scripts/teardown.py --yes     # does not
```

Both accept `--host` and `--token` instead of the environment variables. There
is no `.databrickscfg` profile support: the credential resolves in one place,
`voclab.build_workspace`, the same one the Vocareum hooks use.

Narration goes to stderr. Results come back on stdout as `key=value` lines, the
same output contract `lab/workshop.py` and `voclab.py` use. Exit `0` ok, `1` a
failure carrying an `error_code`, and for `teardown.py` `3` means it was refused
and deleted nothing.

`teardown.py` refuses rather than proceeds when `--yes` is absent and stdin is
not a terminal, so a scripted call that forgot the flag cannot delete a live
class's catalog.

## What used to be here

This directory held a `databricks-setup` Typer CLI with its own
`databricks-sdk`, `typer`, `rich` and `python-dotenv` stack. Almost all of it
was a second copy of something that now has exactly one owner.

| Retired | Who owns that job now |
| --- | --- |
| `lakehouse_tables.py`, `load_lakehouse_data.py` | `lab/workshop.py`. The four tables it built are eight gold tables published by the `Fleet Digital Twin ETL` DLT pipeline, and the eighteen `COMMENT` statements a Genie space reads are `workshop.genie_statements()`. |
| `data_upload.py` | `workshop.provision_data`, which uploads the courseware out of the same hash-verified archive the hooks travel in. |
| `cluster.py` | `voclab.py cluster-ensure`, called from `lab_setup.sh` and `user_setup.sh`. |
| `libraries.py` | `voclab.py cluster-ensure`, from `VOC_COURSE_LIBRARIES` in `lab/course.env`. |
| `warehouse.py` | `voclab.py warehouse-ensure` for the warehouse, `workshop.execute_sql` for statements. |
| `config.py` volume, cluster, library and warehouse settings | `lab/course.env` and `lab/workshop.py`. |
| `main.py setup` | `workshop.py provision`, run by `workspace_init.sh`. |
| `models.py`, `log.py`, `utils.py` | Nothing. They existed to serve the modules above. |
| `cleanup.py` | `teardown.py` here, rewritten to read its names from `workshop.py` and to reclaim the `aircraft_pipeline` schema and the DLT pipeline, neither of which it knew about. |
| `notebooks.py` | `sync_notebooks.py` here. |

The two that survived are the two nothing else covers. `voclab.py`'s
`notebook-import` is not a substitute for `sync_notebooks.py`: it targets
`/Users/<email>`, imports the one notebook `VOC_COURSE_NOTEBOOKS` names, and
skips a file that is already there so a student's edits survive a `stop`. This
targets `/Shared`, imports the whole lab set, and overwrites.

A third script, `build_data_zip.py`, was deleted on 2026-08-08 along with the
`vocareum/courseware/` directory it wrote into. It packed
`workshop-setup/aircraft_digital_twin_data/` into a zip, and no lab, guide, hook
or other script ever told anyone to fetch or unpack that zip. It had no consumer
because it could not have one: the files it packed are tracked in this
repository, so anyone setting up by hand has them from the clone, and the
Vocareum path reads the directory through the `lab/courseware/` symlink and never
sees an archive.

Why one definition rather than two: the gold `systems` and `sensors` tables were
once renamed to match the copy in this directory, and the symptom of the two
copies having drifted was a Genie space answering plausibly rather than
correctly. That is the hardest class of workshop failure to notice in a room of
thirty people.
