#!/usr/bin/env python3
"""Compile requirements.in into the lock every student's cluster installs.

Run from anywhere, with ``uv`` on the PATH::

    python3 lab/courseware/requirements/regenerate.py           # recompile, then check
    python3 lab/courseware/requirements/regenerate.py --check   # check only

Recompiling keeps every pin already in ``requirements.txt`` that still
satisfies ``requirements.in``. ``uv pip compile`` prefers the versions in an
existing output file, so editing one line of ``requirements.in`` moves only what
that line forces. Add ``--upgrade`` to take the latest of everything.

The lock is installed on top of a runtime that already holds about four hundred
packages, and it must not break any of them. ``runtime-constraints.txt`` lists
them all, and the compile takes two steps:

1. Resolve ``requirements.in`` together with every runtime package as a
   requirement. Each one is pinned at its runtime version unless it is freed,
   and a freed one is required by name. Requiring them, rather than only
   constraining them, puts each runtime package's own dependency bounds into the
   resolve. A constraint bounds only a package something already pulls in, so
   the runtime's ``datasets``, which nothing in the labs needs, never got to
   say that it caps ``fsspec``. The lock moved ``fsspec`` past that cap and
   ``pip check`` failed on the cluster. This step is what ``pip check`` tests.
2. Compile ``requirements.in`` alone, constrained to step 1's versions. That is
   the lock: only what the labs need, at versions known to sit beside the whole
   runtime. Its ``# via`` lines name step 1's output as ``runtime-resolve.txt``,
   a file that exists only while this script runs.

``runtime-constraints.txt`` is the runtime's whole package list, one
``name==version`` per line. Two markers take a line out, each with a required
reason, and both keep the runtime version on record::

    # freed: mlflow-skinny==3.0.1  the lock moves it to 3.18.0, which ...
    # not-required: torch==2.7.0+cpu  a +cpu build from the PyTorch index, ...

A freed package is one the labs need at another version. It stays in step 1 by
name, so its dependents' bounds still apply. A not-required package is left out
of step 1 altogether: one not on PyPI, or one ``pip check`` already fails on a
clean cluster, either of which leaves nothing to solve. A line that is neither
a pin nor a marker fails the check rather than being skipped, and so does a pin
commented out any other way, so no runtime package goes unchecked because of
how its line was written. The markers ignore case. The constraints are checked
before the compile as well as after it, so a malformed line is named by line
number rather than reported as a uv failure.

The check, run after every compile and alone with ``--check``, fails on any of:

* a runtime pin the lock moves;
* a freed package the lock does not move, which should be pinned again;
* a not-required package the lock installs, which would replace the runtime's
  own build;
* a lock that cannot be installed beside the whole runtime, which is step 1
  rerun with the lock as constraints.

A changed lock reaches no workspace on its own. It is uploaded to the volume by
``lab/workshop.py provision``, which ``workspace_init.sh`` runs once per
workspace. See "The Python library lock" in ``workshop-setup/README.md``.

Standard library only, against Python 3.9, like ``lab/workshop.py``.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "requirements.in"
CONSTRAINTS = HERE / "runtime-constraints.txt"
LOCK = HERE / "requirements.txt"

# Step 1's input and output, under the names the lock's ``# via`` lines give
# them. Both live in a temporary directory, so nothing intermediate is written
# into lab/, which is uploaded whole.
FULL_NAME = "runtime-full.in"
RESOLVE_NAME = "runtime-resolve.txt"

# Databricks Runtime 17.3 LTS ML runs Python 3.12 on x86_64 Linux. The lock is
# compiled for that target, not for the machine running this script.
PYTHON_VERSION = "3.12"
PYTHON_PLATFORM = "x86_64-unknown-linux-gnu"

# What the lock's header names as the command that made it, so a reader of
# requirements.txt is sent here rather than to a bare ``uv pip compile``.
COMPILE_COMMAND = "python3 lab/courseware/requirements/regenerate.py"

NAME = r"[A-Za-z0-9][A-Za-z0-9._-]*"
PIN = re.compile(rf"^({NAME})==([^\s;#]+)")

# A runtime package taken out of the pins. The runtime version stays on record,
# and the reason is required.
MARKED = re.compile(
    rf"^#\s*(freed|not-required):\s*({NAME})==(\S+)\s*(.*)$", re.IGNORECASE
)

# A comment that looks like a marker, or that holds a pin anywhere in it, such as
# a marker spelled wrong. Either one would otherwise drop a runtime package with
# no reason and no error. A pin here is ``name==`` and a digit, so the header's
# ``name==version`` placeholders are not read as one.
COMMENTED_PIN = re.compile(
    rf"^#\s*(freed\b|not-required\b|.*\b{NAME}\s*==\s*\d)", re.IGNORECASE
)


class Marked(NamedTuple):
    version: str
    reason: str


class Constraints(NamedTuple):
    pins: dict[str, str]
    freed: dict[str, Marked]
    not_required: dict[str, Marked]
    problems: list[str]


def normalize(name: str) -> str:
    """A package name as pip compares it, per PEP 503."""
    return re.sub(r"[-_.]+", "-", name).lower()


def read_pins(path: Path) -> dict[str, str]:
    """Every ``name==version`` line in a requirements file, keyed by name."""
    pins = {}
    for line in path.read_text().splitlines():
        match = PIN.match(line.strip())
        if match:
            pins[normalize(match.group(1))] = match.group(2)
    return pins


def read_constraints() -> Constraints:
    """The runtime pins, the two kinds of marked package, and every bad line.

    The problems are: a line that is not a pin, a marker with no reason, a pin
    commented out without a marker, and a package listed twice in different
    ways.
    """
    pins: dict[str, str] = {}
    marked: dict[str, dict[str, Marked]] = {"freed": {}, "not-required": {}}
    problems = []
    for number, raw in enumerate(CONSTRAINTS.read_text().splitlines(), start=1):
        line = raw.strip()
        where = f"{CONSTRAINTS.name}:{number}"
        if match := MARKED.match(line):
            kind, name = match.group(1).lower(), normalize(match.group(2))
            reason = match.group(4).strip()
            if not reason:
                problems.append(f"{where}: {name} is {kind} with no reason given")
            marked[kind][name] = Marked(match.group(3), reason)
        elif COMMENTED_PIN.match(line):
            problems.append(
                f"{where}: a commented-out pin must be written "
                f"'# freed: name==version reason' or "
                f"'# not-required: name==version reason': {line}"
            )
        elif not line or line.startswith("#"):
            continue
        elif match := PIN.match(line):
            pins[normalize(match.group(1))] = match.group(2)
        else:
            problems.append(f"{where}: not a name==version pin: {line}")
    freed, not_required = marked["freed"], marked["not-required"]
    for first, second, label in (
        (pins, freed, "pinned and freed"),
        (pins, not_required, "pinned and not-required"),
        (freed, not_required, "freed and not-required"),
    ):
        problems.extend(
            f"{CONSTRAINTS.name}: {name} is both {label}"
            for name in sorted(first.keys() & second.keys())
        )
    return Constraints(pins, freed, not_required, problems)


def write_full_requirements(constraints: Constraints, workdir: Path) -> None:
    """Step 1's input: requirements.in plus every runtime package not left out."""
    lines = [SOURCE.read_text().rstrip("\n"), ""]
    lines += [
        f"{name}=={version}" for name, version in sorted(constraints.pins.items())
    ]
    lines += sorted(constraints.freed)
    (workdir / FULL_NAME).write_text("\n".join(lines) + "\n")


def uv_compile(
    workdir: Path,
    source: str,
    output: str,
    constraint: str | None = None,
    upgrade: bool = False,
) -> bool:
    """Run ``uv pip compile`` in ``workdir`` with the flags the lock depends on.

    Returns whether it solved. uv's own explanation of a failure goes to stderr
    unchanged, because it names the packages that conflict and nothing here
    could say it better. Paths are relative to ``workdir``, so they are what the
    output's ``# via`` lines show.
    """
    command = [
        "uv",
        "pip",
        "compile",
        "--quiet",
        source,
        "--python-version",
        PYTHON_VERSION,
        "--python-platform",
        PYTHON_PLATFORM,
        "--custom-compile-command",
        COMPILE_COMMAND,
        "--output-file",
        output,
    ]
    if constraint:
        command += ["--constraint", constraint]
    if upgrade:
        command.append("--upgrade")
    return subprocess.run(command, cwd=workdir, check=False).returncode == 0


def compile_lock(constraints: Constraints, upgrade: bool) -> bool:
    """Steps 1 and 2. Writes ``requirements.txt`` only if both solve.

    Each step gets the current lock as its existing output file unless
    ``upgrade`` is set, which is what makes uv keep the versions already there.
    """
    with tempfile.TemporaryDirectory() as name:
        work = Path(name)
        write_full_requirements(constraints, work)
        shutil.copyfile(SOURCE, work / SOURCE.name)
        if not upgrade and LOCK.exists():
            shutil.copyfile(LOCK, work / RESOLVE_NAME)
            shutil.copyfile(LOCK, work / LOCK.name)
        if not uv_compile(work, FULL_NAME, RESOLVE_NAME, upgrade=upgrade):
            print(
                "Step 1 failed: requirements.in cannot be installed beside the "
                "runtime. uv names the conflict above. Free the runtime package "
                "it names, with a reason, or change requirements.in.",
                file=sys.stderr,
            )
            return False
        if not uv_compile(
            work, SOURCE.name, LOCK.name, constraint=RESOLVE_NAME, upgrade=upgrade
        ):
            print("Step 2 failed. uv names the conflict above.", file=sys.stderr)
            return False
        shutil.copyfile(work / LOCK.name, LOCK)
    return True


def fits_runtime(constraints: Constraints) -> bool:
    """Whether the lock, as it stands, can be installed beside the whole runtime."""
    with tempfile.TemporaryDirectory() as name:
        work = Path(name)
        write_full_requirements(constraints, work)
        shutil.copyfile(LOCK, work / LOCK.name)
        return uv_compile(work, FULL_NAME, RESOLVE_NAME, constraint=LOCK.name)


def check_lock(constraints: Constraints) -> list[str]:
    """Name every way the lock fails the runtime. See the module docstring.

    A pinned runtime package the lock does not mention passes. Nothing the labs
    need pulled it in, so pip leaves the runtime's copy alone.
    """
    locked = read_pins(LOCK)
    problems = [
        f"{name}: the lock pins {locked[name]}, the runtime ships {version}"
        for name, version in sorted(constraints.pins.items())
        if name in locked and locked[name] != version
    ]
    for name, (version, _reason) in sorted(constraints.freed.items()):
        if locked.get(name) == version:
            problems.append(
                f"{name}: freed, but the lock keeps the runtime's {version}. "
                f"Pin it again."
            )
        elif name not in locked:
            problems.append(
                f"{name}: freed, but the lock does not install it, so the "
                f"cluster keeps the runtime's {version} and step 1 did not "
                f"check that. Pin it again."
            )
    problems.extend(
        f"{name}: not-required, but the lock installs {locked[name]}, which "
        f"replaces the runtime's {version}"
        for name, (version, _reason) in sorted(constraints.not_required.items())
        if name in locked
    )
    if not fits_runtime(constraints):
        problems.append(
            "the lock cannot be installed beside the runtime packages. uv names "
            "the conflict above."
        )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="check the existing lock against the runtime without recompiling",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="take the latest version of everything rather than keeping current pins",
    )
    args = parser.parse_args()

    constraints = read_constraints()
    if constraints.problems:
        print(f"{CONSTRAINTS.name} cannot be checked:", file=sys.stderr)
        for line in constraints.problems:
            print(f"  {line}", file=sys.stderr)
        return 1

    try:
        if not args.check and not compile_lock(constraints, args.upgrade):
            return 1
        problems = check_lock(constraints)
    except FileNotFoundError:
        print(
            "uv is not on the PATH. Install it from https://docs.astral.sh/uv/",
            file=sys.stderr,
        )
        return 1

    if problems:
        print(f"{LOCK.name} fails the runtime check:", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 1
    locked = read_pins(LOCK)
    print(
        f"{LOCK.name}: {len(locked)} pins. Runtime packages: "
        f"{len(constraints.pins)} kept, {len(constraints.freed)} freed, "
        f"{len(constraints.not_required)} not required."
    )
    for name, (version, reason) in sorted(constraints.freed.items()):
        print(f"  freed {name} {version} -> {locked[name]}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
