"""Reach ``lab/workshop.py`` from the admin scripts, so nothing here restates it.

``lab/workshop.py`` is this course's one definition of its Databricks objects:
the catalog, the four schemas, the volume, the DLT pipeline, the eight gold
tables and the comments a Genie space reads. The Vocareum hook calls it, and the
two admin scripts beside this file call it too, which is the whole point. The
previous arrangement had a second copy of the catalog name, the schema names and
eighteen COMMENT statements living in ``src/databricks_setup/``; those two copies
diverged once already and the symptom was a Genie space answering plausibly
rather than correctly.

There is no ``sys.path`` trick that finds ``voclab.py``, so this does not try
one. ``lab/workshop.py`` locates its own runtime, first beside itself (where
``dbx-vocareum-upload`` injects it) and then inside the installed
``dbx-vocareum-tools`` package (where a laptop finds it). All this file does is
put ``lab/`` on the path and let ``workshop.py`` do the rest, which means the
laptop and the Vocareum host resolve the runtime through exactly one piece of
code rather than two that can disagree.

Run these scripts from the repository root, where ``dbx-vocareum-tools`` is
already a dev dependency::

    uv run python workshop-setup/auto_scripts/sync_notebooks.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

# workshop-setup/auto_scripts/ -> workshop-setup/ -> repository root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LAB_DIR = REPO_ROOT / "lab"


def import_workshop() -> ModuleType:
    """Return ``lab/workshop.py`` as a module, or exit saying how to fix it.

    ``SystemExit`` rather than a raised ``ImportError`` because both callers are
    programs rather than libraries, and the two ways this fails are both
    actionable: either the checkout is incomplete or the script was run outside
    the environment that holds ``dbx-vocareum-tools``.
    """
    if not (LAB_DIR / "workshop.py").is_file():
        raise SystemExit(
            f"{LAB_DIR / 'workshop.py'} is not there. It is the course's one "
            f"definition of its Databricks objects and these scripts do "
            f"nothing without it."
        )
    if str(LAB_DIR) not in sys.path:
        sys.path.insert(0, str(LAB_DIR))
    import workshop

    return workshop
