#!/usr/bin/env python3
"""Merge WiGLE CSV exports into one upload-ready WiGLE CSV file."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import sys
import tempfile


DEFAULT_PATTERN = "*.wigle.csv"
DEFAULT_OUTPUT = "merged.wigle.csv"
EXPECTED_FIRST_COLUMN = "MAC"


class WigleCsvError(ValueError):
    """Raised when an input is not a compatible WiGLE CSV file."""


def read_wigle_file(path: Path) -> tuple[str, list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        metadata = source.readline().rstrip("\r\n")
        if not metadata.startswith("WigleWifi-"):
            raise WigleCsvError("first line does not start with 'WigleWifi-'")

        reader = csv.reader(source)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise WigleCsvError("missing column header") from exc

        if not header or header[0] != EXPECTED_FIRST_COLUMN:
            raise WigleCsvError("second line is not a WiGLE column header")

        rows: list[list[str]] = []
        for line_number, row in enumerate(reader, start=3):
            if not row or all(not value for value in row):
                continue
            if len(row) != len(header):
                raise WigleCsvError(
                    f"line {line_number} has {len(row)} columns; expected {len(header)}"
                )
            rows.append(row)

    return metadata, header, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine WiGLE CSV files while keeping only one metadata/header pair."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help=f"files to merge (default: {DEFAULT_PATTERN} in the current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(DEFAULT_OUTPUT),
        help=f"output file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="remove rows that are exactly identical in multiple files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.resolve()

    candidates = args.inputs or sorted(Path.cwd().glob(DEFAULT_PATTERN))
    excluded_outputs = {output}
    if not args.inputs:
        # Also ignore the conventional output if a custom -o path is used.
        excluded_outputs.add((Path.cwd() / DEFAULT_OUTPUT).resolve())
    inputs = [path for path in candidates if path.resolve() not in excluded_outputs]
    if not inputs:
        print(f"Error: no input files matched {DEFAULT_PATTERN}", file=sys.stderr)
        return 1

    metadata: str | None = None
    header: list[str] | None = None
    merged_rows: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    duplicate_count = 0

    for path in inputs:
        try:
            file_metadata, file_header, rows = read_wigle_file(path)
        except (OSError, UnicodeError, csv.Error, WigleCsvError) as exc:
            print(f"Error in {path}: {exc}", file=sys.stderr)
            return 1

        if header is None:
            metadata, header = file_metadata, file_header
        elif file_header != header:
            print(f"Error in {path}: column header differs from the first file", file=sys.stderr)
            return 1

        for row in rows:
            row_key = tuple(row)
            if args.deduplicate and row_key in seen:
                duplicate_count += 1
                continue
            seen.add(row_key)
            merged_rows.append(row)

        print(f"Read {len(rows):,} rows from {path}")

    assert metadata is not None and header is not None
    output.parent.mkdir(parents=True, exist_ok=True)

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as destination:
            temporary_name = destination.name
            destination.write(metadata + "\n")
            writer = csv.writer(destination, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(merged_rows)
        os.replace(temporary_name, output)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)

    summary = f"Created {output} with {len(merged_rows):,} rows from {len(inputs)} files."
    if args.deduplicate:
        summary += f" Removed {duplicate_count:,} exact duplicate rows."
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
