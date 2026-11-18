#!/usr/bin/env python3
"""Require a reason and an expiry date on every lint or type suppression.

Copied into a repo by sstack's lint-pack skill. A suppression passes when
its line, or the line above it, says:

    reason: <why>; expires: YYYY-MM-DD

The date must not be past, and must be at most --max-days ahead.
Prints violations as JSON with --json, for lint/baseline.py.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

SOURCE_SUFFIXES = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"}

SUPPRESSION = re.compile(
    r"eslint-disable|@ts-expect-error|@ts-ignore|@ts-nocheck|ast-grep-ignore|biome-ignore"
    r"|#\s*noqa\b|#\s*ruff:\s*noqa|#\s*type:\s*ignore|#\s*pyright:\s*(?:ignore|basic|strict\s*=\s*false)"
    r"|#\s*mypy:\s*ignore-errors|#\s*pylint:\s*disable"
)
EXCEPTION = re.compile(r"reason:\s*\w[^;]*;\s*expires:\s*(\d{4}-\d{2}-\d{2})")

NOTE = "Add `reason: <why>; expires: YYYY-MM-DD` on the same line or the line above, or fix the code and drop the suppression."


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [Path(p) for p in out.split("\0") if p and Path(p).suffix in SOURCE_SUFFIXES]


def check_text(path: str, text: str, today: dt.date, max_days: int) -> list[dict]:
    found = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not SUPPRESSION.search(line):
            continue
        m = EXCEPTION.search(line) or (EXCEPTION.search(lines[i - 1]) if i > 0 else None)
        if m is None:
            problem = "suppression has no reason and expiry date"
        else:
            try:
                expires = dt.date.fromisoformat(m.group(1))
            except ValueError:
                problem = f"expiry {m.group(1)} is not a real date"
            else:
                if expires < today:
                    problem = f"suppression expired on {expires}"
                elif (expires - today).days > max_days:
                    problem = f"expiry {expires} is more than {max_days} days out"
                else:
                    continue
        found.append({"rule": "suppression-needs-reason-and-expiry", "file": path, "line": i + 1, "message": problem, "note": NOTE})
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-days", type=int, default=180)
    ap.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    ap.add_argument("--exclude", action="append", default=[], help="glob for generated files, such as 'convex/_generated/*'")
    ap.add_argument("paths", nargs="*", type=Path)
    args = ap.parse_args(argv)

    this_file = Path(__file__).resolve()
    found = []
    for path in args.paths or tracked_files():
        if path.resolve() == this_file or any(fnmatch.fnmatch(path.as_posix(), g) for g in args.exclude):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        found += check_text(path.as_posix(), text, args.today, args.max_days)

    if args.json:
        print(json.dumps(found))
        return 0
    for f in found:
        print(f"{f['file']}:{f['line']}  {f['message']}")
    if found:
        print(NOTE)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
