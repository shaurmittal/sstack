from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import check_suppressions as cs  # noqa: E402
import baseline  # noqa: E402

TODAY = dt.date(2026, 11, 17)


class SuppressionTests(unittest.TestCase):
    def check(self, text: str) -> list[str]:
        return [f["message"] for f in cs.check_text("f.py", text, TODAY, 180)]

    def test_bare_suppressions_fail(self):
        for line in [
            "x = 1  # noqa: E501",
            "x = f()  # type: ignore[arg-type]",
            "// eslint-disable-next-line no-console",
            "// @ts-expect-error",
            "// ast-grep-ignore: no-explicit-any",
            "# ruff: noqa",
            "x = 1  # pyright: ignore[reportAny]",
        ]:
            self.assertEqual(self.check(line), ["suppression has no reason and expiry date"], line)

    def test_reason_and_expiry_on_same_line_passes(self):
        self.assertEqual(self.check("x = 1  # noqa: E501  # reason: generated table; expires: 2027-01-31"), [])

    def test_reason_and_expiry_on_line_above_passes(self):
        text = "// reason: vendor types are wrong; expires: 2027-02-01\n// @ts-expect-error\nconst x: number = 'a'"
        self.assertEqual(self.check(text), [])

    def test_expired_fails(self):
        self.assertEqual(
            self.check("x = 1  # noqa: E501  # reason: old; expires: 2026-11-16"),
            ["suppression expired on 2026-11-16"],
        )

    def test_far_future_expiry_fails(self):
        self.assertEqual(
            self.check("x = 1  # noqa: E501  # reason: forever; expires: 2099-01-01"),
            ["expiry 2099-01-01 is more than 180 days out"],
        )

    def test_reason_without_text_fails(self):
        self.assertEqual(self.check("x = 1  # noqa  # reason: ; expires: 2027-01-01")[0], "suppression has no reason and expiry date")

    def test_exclude_skips_generated_files(self):
        with tempfile.TemporaryDirectory() as d:
            gen = Path(d) / "gen" / "api.js"
            gen.parent.mkdir()
            gen.write_text("/* eslint-disable */\n")
            out = subprocess.run(
                [sys.executable, str(Path(cs.__file__)), "--json", "--exclude", "*/gen/*", str(gen)],
                capture_output=True, text=True,
            )
            self.assertEqual(json.loads(out.stdout), [])
            out = subprocess.run([sys.executable, str(Path(cs.__file__)), "--json", str(gen)], capture_output=True, text=True)
            self.assertEqual(len(json.loads(out.stdout)), 1)

    def test_skips_its_own_source(self):
        script = Path(cs.__file__).resolve()
        self.assertNotEqual(cs.check_text("x", script.read_text(), TODAY, 180), [], "the pattern list itself looks like suppressions")
        out = subprocess.run([sys.executable, str(script), "--json", str(script)], capture_output=True, text=True)
        self.assertEqual(json.loads(out.stdout), [])

    def test_plain_comments_pass(self):
        self.assertEqual(self.check("# this mentions types but ignores nothing\nx = 1"), [])


def V(rule: str, file: str, tool: str = "ast-grep") -> baseline.Violation:
    return baseline.Violation(tool, rule, file, 1, "msg")


class BaselineTests(unittest.TestCase):
    def test_new_violation_in_baselined_file_regresses(self):
        base = baseline.count([V("r", "a.ts")])
        cur = baseline.count([V("r", "a.ts"), V("r", "a.ts")])
        self.assertEqual(baseline.compare(base, cur), ({("ast-grep", "r", "a.ts")}, set()))

    def test_new_file_regresses(self):
        self.assertEqual(baseline.compare({}, baseline.count([V("r", "b.ts")]))[0], {("ast-grep", "r", "b.ts")})

    def test_fix_is_improvement_not_regression(self):
        base = baseline.count([V("r", "a.ts"), V("r", "a.ts")])
        self.assertEqual(baseline.compare(base, baseline.count([V("r", "a.ts")])), (set(), {("ast-grep", "r", "a.ts")}))

    def test_tighten_never_raises(self):
        base = baseline.count([V("r", "a.ts")])
        cur = baseline.count([V("r", "a.ts"), V("r", "a.ts"), V("r", "new.ts")])
        self.assertEqual(baseline.tighten(base, cur), base)

    def test_tighten_drops_fixed(self):
        base = baseline.count([V("r", "a.ts"), V("q", "b.ts")])
        self.assertEqual(baseline.tighten(base, baseline.count([V("q", "b.ts")])), {"ast-grep": {"q": {"b.ts": 1}}})

    def test_parsers(self):
        sg = json.dumps({"ruleId": "no-explicit-any", "file": "a.tsx", "range": {"start": {"line": 4}}, "message": "m", "note": "n"})
        self.assertEqual(baseline.parse_ast_grep("ast-grep", sg + "\n"), [baseline.Violation("ast-grep", "no-explicit-any", "a.tsx", 5, "m", "n")])
        ruff = json.dumps([{"code": "BLE001", "filename": "x.py", "message": "m", "location": {"row": 3}, "fix": None}])
        self.assertEqual(baseline.parse_ruff("ruff", ruff)[0].rule, "BLE001")
        pyright = json.dumps({"generalDiagnostics": [
            {"file": "x.py", "severity": "error", "message": "m", "rule": "reportAny", "range": {"start": {"line": 0}}},
            {"file": "x.py", "severity": "warning", "message": "w", "range": {"start": {"line": 0}}},
        ]})
        self.assertEqual([v.rule for v in baseline.parse_pyright("pyright", pyright)], ["reportAny"])
        mypy = '{"file": "x.py", "line": 2, "column": 0, "message": "m", "hint": null, "code": "no-untyped-def", "severity": "error"}\n'
        self.assertEqual(baseline.parse_mypy("mypy", mypy)[0].rule, "no-untyped-def")
        dc = json.dumps({"summary": {"violations": [{"from": "app/a.ts", "to": "convex/b.ts", "rule": {"name": "no-app-from-convex", "severity": "error"}}],
                                     "ruleSetUsed": {"forbidden": [{"name": "no-app-from-convex", "comment": "fix it"}]}}})
        self.assertEqual(baseline.parse_depcruise("depcruise", dc)[0].note, "fix it")


class BaselineCliTests(unittest.TestCase):
    """Drive the real CLI with a fake tool, the way CI runs it."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / "lint").mkdir()
        self.out = self.root / "violations.json"
        tool = [sys.executable, "-c", f"print(open({str(self.out)!r}).read())"]
        (self.root / "lint" / "tools.json").write_text(json.dumps({"tools": [{"name": "fake", "format": "sstack", "cmd": tool}]}))

    def tearDown(self):
        self.dir.cleanup()

    def emit(self, *files: str) -> None:
        self.out.write_text(json.dumps([{"rule": "r", "file": f, "line": 1, "message": "bad", "note": "use good()"} for f in files]))

    def run_cli(self, cmd: str) -> subprocess.CompletedProcess:
        script = Path(__file__).resolve().parent.parent / "baseline.py"
        return subprocess.run([sys.executable, str(script), cmd], cwd=self.root, capture_output=True, text=True, env={**os.environ})

    def test_flow(self):
        self.emit("a.py")
        self.assertEqual(self.run_cli("init").returncode, 0)
        self.assertEqual(self.run_cli("check").returncode, 0)

        self.emit("a.py", "b.py")
        res = self.run_cli("check")
        self.assertEqual(res.returncode, 1)
        self.assertIn("b.py: fake r went from 0 to 1", res.stdout)
        self.assertIn("use good()", res.stdout)

        self.emit()
        res = self.run_cli("check")
        self.assertEqual(res.returncode, 1)
        self.assertIn("tighten", res.stdout)
        self.assertEqual(self.run_cli("tighten").returncode, 0)
        self.assertEqual(self.run_cli("check").returncode, 0)
        self.assertEqual(json.loads((self.root / "lint" / "baseline.json").read_text()), {})

    def test_unreadable_tool_output_is_an_error_not_a_pass(self):
        self.out.write_text("not json")
        self.assertEqual(self.run_cli("check").returncode, 2)

    def test_init_refuses_to_overwrite(self):
        self.emit("a.py")
        self.run_cli("init")
        self.assertEqual(self.run_cli("init").returncode, 1)


if __name__ == "__main__":
    unittest.main()
