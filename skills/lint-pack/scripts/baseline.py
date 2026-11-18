#!/usr/bin/env python3
"""Fail on new lint violations and let the existing ones be fixed over time.

Copied into a repo by sstack's lint-pack skill. Runs each tool in
lint/tools.json, counts violations per tool, rule, and file, and compares
the counts to lint/baseline.json.

  check    fail if any count went up, or went down without `tighten`
  init     write the first baseline (refuses to overwrite one)
  tighten  lower baseline counts to the current counts, never raise them
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

Counts = dict[str, dict[str, dict[str, int]]]


@dataclass(frozen=True)
class Violation:
    tool: str
    rule: str
    file: str
    line: int
    message: str
    note: str = ""


def _rel(path: str) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(Path.cwd())
        except ValueError:
            pass
    return p.as_posix()


def parse_ast_grep(tool: str, out: str) -> list[Violation]:
    found = []
    for line in out.splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        found.append(
            Violation(
                tool,
                m["ruleId"],
                _rel(m["file"]),
                m["range"]["start"]["line"] + 1,
                m.get("message", ""),
                m.get("note") or "",
            )
        )
    return found


def parse_depcruise(tool: str, out: str) -> list[Violation]:
    data = json.loads(out)
    comments = {
        r["name"]: r.get("comment", "")
        for r in data["summary"].get("ruleSetUsed", {}).get("forbidden", [])
    }
    return [
        Violation(
            tool,
            v["rule"]["name"],
            _rel(v["from"]),
            0,
            f"imports {v['to']}",
            comments.get(v["rule"]["name"], ""),
        )
        for v in data["summary"]["violations"]
    ]


def parse_ruff(tool: str, out: str) -> list[Violation]:
    return [
        Violation(
            tool,
            m["code"] or "syntax-error",
            _rel(m["filename"]),
            m["location"]["row"],
            m["message"],
            (m.get("fix") or {}).get("message") or "",
        )
        for m in json.loads(out)
    ]


def parse_pyright(tool: str, out: str) -> list[Violation]:
    return [
        Violation(
            tool,
            d.get("rule", "pyright"),
            _rel(d["file"]),
            d["range"]["start"]["line"] + 1,
            d["message"],
        )
        for d in json.loads(out)["generalDiagnostics"]
        if d["severity"] == "error"
    ]


def parse_mypy(tool: str, out: str) -> list[Violation]:
    found = []
    for line in out.splitlines():
        if not line.startswith("{"):
            continue
        m = json.loads(line)
        if m["severity"] != "error":
            continue
        found.append(
            Violation(tool, m.get("code") or "mypy", _rel(m["file"]), m["line"], m["message"], m.get("hint") or "")
        )
    return found


def parse_sstack(tool: str, out: str) -> list[Violation]:
    return [Violation(tool, m["rule"], m["file"], m["line"], m["message"], m.get("note", "")) for m in json.loads(out)]


PARSERS: dict[str, Callable[[str, str], list[Violation]]] = {
    "ast-grep": parse_ast_grep,
    "depcruise": parse_depcruise,
    "ruff": parse_ruff,
    "pyright": parse_pyright,
    "mypy": parse_mypy,
    "sstack": parse_sstack,
}


class ToolError(Exception):
    pass


def run_tool(spec: dict) -> list[Violation]:
    name, fmt, cmd = spec["name"], spec["format"], spec["cmd"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if fmt == "exitcode":
        if proc.returncode == 0:
            return []
        raise ToolError(f"{name} failed (exit {proc.returncode}). Fix it; this tool is not baselined.\n{proc.stdout}{proc.stderr}")
    try:
        return PARSERS[fmt](name, proc.stdout)
    except (ValueError, KeyError, TypeError) as e:
        raise ToolError(
            f"{name}: could not read its {fmt} output ({e!r}). Exit {proc.returncode}.\n{proc.stderr[-2000:]}"
        ) from e


def count(violations: list[Violation]) -> Counts:
    counts: Counts = {}
    for v in violations:
        files = counts.setdefault(v.tool, {}).setdefault(v.rule, {})
        files[v.file] = files.get(v.file, 0) + 1
    return counts


def _get(c: Counts, tool: str, rule: str, file: str) -> int:
    return c.get(tool, {}).get(rule, {}).get(file, 0)


def _keys(c: Counts) -> set[tuple[str, str, str]]:
    return {(t, r, f) for t, rules in c.items() for r, files in rules.items() for f in files}


def compare(baseline: Counts, current: Counts) -> tuple[set, set]:
    """Return (regressed, improved) sets of (tool, rule, file) keys."""
    regressed, improved = set(), set()
    for key in _keys(baseline) | _keys(current):
        b, c = _get(baseline, *key), _get(current, *key)
        if c > b:
            regressed.add(key)
        elif c < b:
            improved.add(key)
    return regressed, improved


def tighten(baseline: Counts, current: Counts) -> Counts:
    out: Counts = {}
    for t, r, f in sorted(_keys(baseline)):
        n = min(_get(baseline, t, r, f), _get(current, t, r, f))
        if n:
            out.setdefault(t, {}).setdefault(r, {})[f] = n
    return out


def _sorted(c: Counts) -> Counts:
    return {t: {r: dict(sorted(fs.items())) for r, fs in sorted(rs.items())} for t, rs in sorted(c.items())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["check", "init", "tighten"])
    ap.add_argument("--config", default="lint/tools.json")
    args = ap.parse_args(argv)

    config = json.loads(Path(args.config).read_text())
    baseline_path = Path(config.get("baseline", "lint/baseline.json"))

    violations: list[Violation] = []
    errors: list[str] = []
    for spec in config["tools"]:
        try:
            violations += run_tool(spec)
        except ToolError as e:
            errors.append(str(e))
    if errors:
        print("\n\n".join(errors), file=sys.stderr)
        return 2
    current = count(violations)

    if args.command == "init":
        if baseline_path.exists():
            print(f"{baseline_path} exists. Use `tighten` to lower it.", file=sys.stderr)
            return 1
        baseline_path.write_text(json.dumps(_sorted(current), indent=2) + "\n")
        print(f"Wrote {baseline_path}: {len(violations)} existing violations.")
        return 0

    baseline: Counts = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}

    if args.command == "tighten":
        baseline_path.write_text(json.dumps(_sorted(tighten(baseline, current)), indent=2) + "\n")
        print(f"Tightened {baseline_path}.")
        return 0

    regressed, improved = compare(baseline, current)
    for tool, rule, file in sorted(regressed):
        b, c = _get(baseline, tool, rule, file), _get(current, tool, rule, file)
        print(f"\n{file}: {tool} {rule} went from {b} to {c}.")
        for v in violations:
            if (v.tool, v.rule, v.file) == (tool, rule, file):
                print(f"  {v.file}:{v.line}  {v.message}")
                if v.note:
                    print("    " + v.note.strip().replace("\n", "\n    "))
    if improved:
        print(f"\n{len(improved)} baselined violation group(s) are fixed. Lock that in:")
        print(f"  python3 lint/baseline.py tighten   and commit {baseline_path}")
    if regressed:
        print("\nNew violations. Fix them. Don't raise the baseline.")
    if regressed or improved:
        return 1
    print(f"lint baseline: ok, {len(violations)} baselined violations left")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.exit(main())
