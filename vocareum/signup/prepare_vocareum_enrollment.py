#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Create grouped Vocareum enrollment CSV files from an event attendance CSV.

Example:
    uv run vocareum/signup/prepare_vocareum_enrollment.py
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

PERSONAL_EMAIL_DOMAINS = {
    "aol.com",
    "att.net",
    "gmail.com",
    "hotmail.com",
    "icloud.com",
    "live.cn",
    "live.com",
    "mac.com",
    "mail.com",
    "me.com",
    "msn.com",
    "outlook.com",
    "pm.me",
    "proton.me",
    "protonmail.com",
    "yahoo.com",
}
VOCAREUM_HEADERS = ("Email", "ID", "Name")
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = SCRIPT_DIR / "sample-event-export.csv"
DEFAULT_OUTPUT = SCRIPT_DIR / "vocareum-enrollment-sample"


@dataclass(frozen=True)
class Student:
    email: str
    name: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--target-batch-size",
        type=int,
        default=25,
        help="Preferred number of participants in each CSV, from 20 through 30.",
    )
    return parser.parse_args()


def normalise_name(first_name: str, last_name: str) -> str:
    """Form a readable name while retaining deliberate mixed-case spellings."""
    parts = first_name.split() + last_name.split()
    if not parts:
        raise ValueError("Attendance record has no first or last name")

    def clean(part: str) -> str:
        return part.capitalize() if part.islower() or part.isupper() else part

    return " ".join(clean(part) for part in parts)


def read_students(source: Path) -> list[Student]:
    with source.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required_headers = {"First Name", "Last Name", "Email"}
        if reader.fieldnames is None or not required_headers <= set(reader.fieldnames):
            required = ", ".join(sorted(required_headers))
            raise ValueError(f"{source} must include: {required}")

        students: list[Student] = []
        emails: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            email = (row["Email"] or "").strip().lower()
            if email.count("@") != 1 or email.startswith("@") or email.endswith("@"):
                raise ValueError(
                    f"Invalid email on source line {line_number}: {email!r}"
                )
            if email in emails:
                raise ValueError(
                    f"Duplicate email on source line {line_number}: {email}"
                )
            emails.add(email)
            students.append(
                Student(
                    email=email,
                    name=normalise_name(
                        (row["First Name"] or "").strip(),
                        (row["Last Name"] or "").strip(),
                    ),
                )
            )
    return students


def group_name(email: str) -> str:
    domain = email.rsplit("@", maxsplit=1)[1]
    if domain == "neo4j.com" or domain.endswith(".neo4j.com"):
        return "neo4j_email"
    if domain in PERSONAL_EMAIL_DOMAINS:
        return "personal_email"
    if domain.endswith(".edu"):
        return "school_email"
    return "work_email"


def split_batches(
    students: list[Student], target_size: int, min_size: int = 20, max_size: int = 30
) -> tuple[list[list[Student]], bool]:
    """Return balanced batches and whether their size falls outside the limit."""
    if not students:
        return [], False

    lowest_batch_count = -(-len(students) // max_size)
    highest_batch_count = len(students) // min_size
    if lowest_batch_count > highest_batch_count:
        batch_count = max(1, round(len(students) / target_size))
    else:
        batch_count = min(
            range(lowest_batch_count, highest_batch_count + 1),
            key=lambda count: (abs(len(students) / count - target_size), count),
        )

    base_size, oversized_batch_count = divmod(len(students), batch_count)
    batches = []
    start = 0
    for batch_index in range(batch_count):
        size = base_size + (batch_index < oversized_batch_count)
        batches.append(students[start : start + size])
        start += size
    has_size_exception = any(
        len(batch) < min_size or len(batch) > max_size for batch in batches
    )
    return batches, has_size_exception


def write_batch(path: Path, students: list[Student]) -> None:
    with path.open("x", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=VOCAREUM_HEADERS)
        writer.writeheader()
        for student in students:
            writer.writerow({"Email": student.email, "ID": "", "Name": student.name})


def main() -> None:
    args = parse_args()
    if not 20 <= args.target_batch_size <= 30:
        raise ValueError("--target-batch-size must be from 20 through 30")
    if args.output_dir.exists():
        raise FileExistsError(
            f"Output directory already exists: {args.output_dir}. "
            "Choose a new --output-dir to avoid overwriting enrollment files."
        )

    grouped_students: dict[str, list[Student]] = defaultdict(list)
    for student in read_students(args.source):
        grouped_students[group_name(student.email)].append(student)

    args.output_dir.mkdir(parents=True)
    manifest_lines = ["Vocareum enrollment export", f"Source: {args.source}", ""]
    for name in ("neo4j_email", "personal_email", "work_email", "school_email"):
        students = grouped_students[name]
        batches, has_size_exception = split_batches(students, args.target_batch_size)
        manifest_lines.append(f"{name}: {len(students)} participant(s)")
        if not batches:
            manifest_lines.append("  No files created.")
            continue
        for index, batch in enumerate(batches, start=1):
            filename = f"{name}_{index:02d}_of_{len(batches):02d}.csv"
            write_batch(args.output_dir / filename, batch)
            manifest_lines.append(f"  {filename}: {len(batch)} participant(s)")
        if has_size_exception:
            manifest_lines.append(
                "  Note: this group cannot be divided into 20-30 person files "
                "without creating an undersized file."
            )

    (args.output_dir / "README.txt").write_text(
        "\n".join(manifest_lines) + "\n", encoding="utf-8"
    )
    print("\n".join(manifest_lines))


if __name__ == "__main__":
    main()
