#!/usr/bin/env python3
"""Rebuild ``vocareum/courseware/aircraft_digital_twin_data.zip`` from the source.

The zip is a convenience copy of the workshop data for someone setting a class up
by hand, off Vocareum. Nothing in this repository reads it. What reaches the
Unity Catalog volume the labs read is ``workshop-setup/aircraft_digital_twin_data/``,
which ``lab/courseware/`` symlinks, ``dbx-vocareum-upload`` follows into the
hash-verified archive, and ``workshop.provision_data`` uploads file by file. That
is why the zip could go stale without anything failing, and why this script
exists: a copy nobody rebuilds is a copy that drifts, and this one had, by one
whole file and six changed ones.

It states no file list of its own. The source directory name and the archive's
internal prefix are both ``Path(workshop.DATA_DIR).name``, and the set of files
is ``workshop.data_files``, the same call ``provision_data`` makes. So the zip
holds exactly what the volume holds, and a glob that matches nothing raises
``MISSING_COURSEWARE`` here for the same reason it does there.

Bytes are copied, never rewritten. Several CSVs carry CRLF line endings and no
quoting, and one is reproducible only under specific generator flags, so nothing
here opens a file in text mode or touches a ``csv`` module.

The build is deterministic: entries sorted, timestamps fixed, permissions fixed.
Rerunning on an unchanged source produces a byte-identical archive, so ``git
status`` after a run is the drift report.

The output contract is ``lab/workshop.py``'s: narration to **stderr**,
``key=value`` lines on **stdout**. Exit ``0`` ok, ``1`` a failure carrying an
``error_code``.

Standard library only, against Python 3.9, like everything else in this
directory. Run it from the repository root::

    uv run python workshop-setup/auto_scripts/build_data_zip.py
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
import zipfile
from pathlib import Path
from typing import Sequence

from workshop_module import REPO_ROOT, import_workshop

workshop = import_workshop()
voclab = workshop.voclab

# The source, reached the way the Vocareum archive reaches it. ``lab/courseware``
# is what ``dbx-vocareum-upload lab/`` walks, and the entry it finds there is a
# symlink to ``workshop-setup/aircraft_digital_twin_data``. Going through the
# symlink rather than around it means this script and the upload cannot disagree
# about which directory is the source of truth.
COURSEWARE_DIR = REPO_ROOT / "lab" / "courseware"
DATA_DIR_NAME = Path(workshop.DATA_DIR).name
SOURCE_DIR = COURSEWARE_DIR / DATA_DIR_NAME

DEFAULT_OUTPUT = REPO_ROOT / "vocareum" / "courseware" / (DATA_DIR_NAME + ".zip")

# The archive's internal layout, matching what the previous zip had: one
# directory entry, then every file under that prefix. Whatever unpacks it expects
# to get a directory rather than 28 loose files in the current working directory.
ARCHIVE_PREFIX = DATA_DIR_NAME + "/"

# Fixed so two runs over an unchanged source produce identical bytes. 1980-01-01
# is the earliest a DOS timestamp can express, which is the convention for a
# reproducible archive.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

DIR_ATTR = (0o40755 << 16) | 0x10
FILE_ATTR = 0o100644 << 16
CREATE_SYSTEM_UNIX = 3

READ_CHUNK = 1 << 20


EXIT_OK = 0
EXIT_FAILED = 1


def source_files() -> list[Path]:
    """Every file the archive has to hold, in the order the volume gets them.

    ``workshop.data_files`` rather than a glob written here, so this archive and
    the provisioned volume are the same set by construction. It raises
    ``MISSING_COURSEWARE`` when a glob matches nothing, which is the loud failure
    a silently partial archive would otherwise become.
    """
    if not SOURCE_DIR.is_dir():
        raise voclab.VoclabError(
            "MISSING_COURSEWARE",
            f"{SOURCE_DIR} is not a directory. It is the symlink "
            f"lab/courseware carries to workshop-setup/{DATA_DIR_NAME}, and "
            f"the archive is built from it.",
        )
    return workshop.data_files(SOURCE_DIR)


def add_file(archive: zipfile.ZipFile, path: Path) -> int:
    """Copy one file into the archive byte for byte, and return its size.

    ``ZipFile.write`` would do this, but it takes the timestamp and the mode off
    the filesystem, and a rebuild has to be reproducible rather than a record of
    when someone ran it.
    """
    info = zipfile.ZipInfo(ARCHIVE_PREFIX + path.name, date_time=ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = CREATE_SYSTEM_UNIX
    info.external_attr = FILE_ATTR
    written = 0
    with path.open("rb") as source, archive.open(info, "w") as target:
        while True:
            chunk = source.read(READ_CHUNK)
            if not chunk:
                break
            target.write(chunk)
            written += len(chunk)
    return written


def write_archive(destination: Path, files: Sequence[Path]) -> None:
    """Write every file under the directory entry, sorted, deflated."""
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        directory = zipfile.ZipInfo(ARCHIVE_PREFIX, date_time=ZIP_EPOCH)
        directory.create_system = CREATE_SYSTEM_UNIX
        directory.external_attr = DIR_ATTR
        archive.writestr(directory, b"")
        for path in sorted(files, key=lambda item: item.name):
            add_file(archive, path)


def verify_archive(path: Path, files: Sequence[Path]) -> tuple[int, int]:
    """Read the finished archive back and check it against the source.

    A truncated write, a short read, or a file that changed underneath the run
    all produce an archive that opens cleanly and is wrong, so the sizes are
    compared rather than trusted. Returns the entry count and the total
    uncompressed bytes.
    """
    expected = {ARCHIVE_PREFIX + item.name: item.stat().st_size for item in files}
    with zipfile.ZipFile(path) as archive:
        damaged = archive.testzip()
        if damaged is not None:
            raise voclab.VoclabError(
                "BAD_ARCHIVE",
                f"{path} failed its CRC check at {damaged}.",
            )
        found = {
            info.filename: info.file_size
            for info in archive.infolist()
            if not info.is_dir()
        }
    missing = sorted(set(expected) - set(found))
    if missing:
        raise voclab.VoclabError(
            "BAD_ARCHIVE",
            f"{path} came out without {', '.join(missing)}.",
        )
    wrong = sorted(name for name in expected if found[name] != expected[name])
    if wrong:
        raise voclab.VoclabError(
            "BAD_ARCHIVE",
            f"{path} holds a different number of bytes than the source "
            f"for {', '.join(wrong)}.",
        )
    return len(found), sum(found.values())


def build(destination: Path) -> dict:
    """Build the archive, verify it, then move it into place."""
    files = source_files()
    voclab.log(f"  {len(files)} files from {SOURCE_DIR}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Built beside the destination and moved on, so a failed run leaves the
    # previous archive intact rather than a half-written one in its place.
    staging = destination.with_name(destination.name + ".partial")
    try:
        write_archive(staging, files)
        entries, uncompressed = verify_archive(staging, files)
        os.replace(str(staging), str(destination))
    finally:
        if staging.exists():
            staging.unlink()

    voclab.log(f"  wrote {destination}")
    return {
        "archive": str(destination),
        "archive_prefix": ARCHIVE_PREFIX,
        "source_dir": str(SOURCE_DIR.resolve()),
        "entries": entries,
        "uncompressed_bytes": uncompressed,
        "archive_bytes": destination.stat().st_size,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the one option this has."""
    parser = argparse.ArgumentParser(
        prog="build_data_zip.py",
        description=(
            "Rebuild the aircraft data zip from "
            "workshop-setup/aircraft_digital_twin_data/."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the archive. Defaults to {DEFAULT_OUTPUT}.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the build, on ``lab/workshop.py``'s output contract."""
    args = parse_args(argv)
    voclab.log("Building the aircraft data archive")
    try:
        voclab.emit(build(args.output))
        return EXIT_OK
    except voclab.VoclabError as error:
        voclab.emit(dict(error.fields, error_code=error.code, message=error.message))
        return EXIT_FAILED
    except OSError as error:
        traceback.print_exc()
        voclab.emit(
            {
                "error_code": "BUILD_FAILED",
                "message": f"{type(error).__name__}: {error}",
            }
        )
        return EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
