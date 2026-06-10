"""CSV writing utilities."""

from __future__ import annotations

import csv
from pathlib import Path


def write_csv(rows: list[dict], path: Path) -> int:
    """Write rows to a CSV file. Returns the number of rows written."""
    if not rows:
        path.write_text("")
        return 0
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_csv_streaming(rows_iter, fieldnames: list[str], path: Path) -> int:
    """Write an iterator of row dicts to CSV without buffering all rows in memory."""
    count = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_iter:
            writer.writerow(row)
            count += 1
    return count
