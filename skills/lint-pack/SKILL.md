---
name: lint-pack
description: Install sstack's lint rules in a Python, React, or JS/TS repo, or turn one review correction into a lint rule whose error names the fix. Use for /lint-pack.
disable-model-invocation: true
argument-hint: "install | add <the correction>"
---

# Lint pack

Agents copy the nearest example and take the shortest path that compiles. A rule that fails CI with a message naming the fix stops a mistake for every later agent. A line in AGENTS.md stops nothing, because no check fails when an agent skips it.

Run `install` once per repo. Run `add` each time the operator corrects the same mistake twice.

The skill folder is the base directory Claude Code printed when this skill loaded. Below, `<skill>` is that folder and `<packs>` is `<skill>/../../rule-packs`.

## One tool per job

| Job | JS and TS | Python |
|---|---|---|
| Code patterns and banned imports | ast-grep | ast-grep |
| Folder boundaries | dependency-cruiser with `parser: "swc"` | import-linter |
| Standard rule sets | none | ruff |
| Types | the repo's `tsc` | the repo's type checker, set to strict |

Every rule this skill writes is an ast-grep rule, because `ast-grep test` runs each rule's bad and good examples in CI. Folder boundaries are the one exception, because they need real module resolution.

Don't add ESLint. typescript-eslint's parser supports only TypeScript below 6.1, and ast-grep parses every TypeScript version. If the repo already runs ESLint, leave its config alone and put new rules in ast-grep.

Don't add a second type checker. If the repo runs mypy, make mypy strict. Add pyright only when the repo has no checker.

## install

Work on a branch. Never commit to the default branch.

1. Read `package.json` or `pyproject.toml`, the CI workflow, the existing lint and typecheck commands, and the top-level folders. Note the package manager, the TypeScript version, and the Python version.
2. Add dev dependencies, pinned to exact versions:
   - JS/TS: `@ast-grep/cli`, `dependency-cruiser`, `@swc/core`.
   - Python: `ast-grep-cli`, `ruff` if missing, `import-linter` if step 5 adds boundaries, `pyright` if step 6 needs it.
3. Copy the rules for each language the repo uses:
   - `<packs>/react/rules/*` and `<packs>/react/rule-tests/*` for JS/TS.
   - `<packs>/python/rules/*` and `<packs>/python/rule-tests/*` for Python.
   Put rules in `lint/ast-grep/rules/` and tests in `lint/ast-grep/rule-tests/`. Write `sgconfig.yml` at the repo root:
   ```yaml
   ruleDirs: [lint/ast-grep/rules]
   testConfigs:
     - testDir: lint/ast-grep/rule-tests
   languageGlobs:            # JS/TS repos only
     tsx: ["*.ts", "*.js", "*.jsx", "*.mjs", "*.cjs", "*.mts", "*.cts"]
   ```
   Add `ignores` to a rule only for generated code, such as `convex/_generated/**`. Never use `ignores` to skip product code that breaks a rule. The baseline in step 7 handles that.
4. Copy `<skill>/scripts/baseline.py` and `<skill>/scripts/check_suppressions.py` into `lint/`.
5. Folder boundaries. List the top-level source folders and count the imports between each pair. Pick the boundaries that protect the layering the code already follows, such as "the backend never imports UI code". Skip a boundary that nothing comes close to breaking. Tell the operator your picks in plain words, one sentence each, and go ahead unless they object. Write them:
   - JS/TS: copy `<packs>/react/dependency-cruiser.cjs` to `.dependency-cruiser.cjs` and add each boundary to `forbidden`. Each `comment` is the error text, so it names the fix.
   - Python: write `.importlinter` contracts.
6. Python only. Read `<packs>/python/pyproject-snippet.toml`. Put the ruff codes the repo doesn't already select into the ruff command's `--extend-select` in step 7, not into `pyproject.toml`. The repo's own `ruff check` calls in scripts and pre-commit would fail on every existing violation of a new code, and `ruff check --fix` in pre-commit would rewrite unrelated code. Move a code into `pyproject.toml` once its baseline count reaches zero. If the repo runs no type checker, add pyright in strict mode. If it runs one, make sure it is strict and leave it.
7. Write `lint/tools.json`, one entry per tool. `format` is one of `ast-grep`, `depcruise`, `ruff`, `pyright`, `mypy`, `sstack`, or `exitcode`. A tool with `exitcode` must pass outright and is never baselined, which suits import-linter, whose contracts list allowed exceptions in `ignore_imports`. Commands run from the repo root:
   ```json
   {
     "tools": [
       {"name": "ast-grep", "format": "ast-grep", "cmd": ["npx", "--no-install", "ast-grep", "scan", "--json=stream"]},
       {"name": "depcruise", "format": "depcruise", "cmd": ["npx", "--no-install", "depcruise", "app", "shared", "--output-type", "json"]},
       {"name": "suppressions", "format": "sstack", "cmd": ["python3", "lint/check_suppressions.py", "--json"]}
     ]
   }
   ```
   For Python, call tools through the repo's runner, such as `["uv", "run", "ruff", "check", "src", "tests", "--extend-select", "BLE,SIM,RUF,PGH", "--output-format", "json", "--quiet"]`.
   Keep generated code out. Add `"--globs", "!<dir>/**"` to the ast-grep command and `"--exclude", "<dir>/*"` to the suppressions command. Never baseline generated files, because the generator rewrites them.
   List a tool here only if it has violations to baseline. A type checker that already passes stays where the repo runs it.
   Then run `python3 lint/baseline.py init`. It writes `lint/baseline.json` with every existing violation. From then on, `check` fails when a count for a tool, rule, and file goes up.
8. Prove every check works in this repo. A tool that exits 0 may have read nothing. dependency-cruiser's default parser skips every `.ts` file under TypeScript 7 and still reports no violations. For each rule and each boundary:
   - Add one violation to a real product file.
   - Run `python3 lint/baseline.py check` and confirm it fails with the rule's message and note.
   - Revert the file and confirm `check` passes.
   Then run `npx ast-grep test --skip-snapshot-tests` and confirm every rule test passes.
9. Wire it in where the repo already runs lint. Run `ast-grep test --skip-snapshot-tests` and then `python3 lint/baseline.py check`:
   - With an npm `lint` script, or a new one, plus a CI step next to typecheck.
   - With a line in the repo's lint script, such as `scripts/lint.sh`.
   - With a pre-commit hook using `pass_filenames: false`, if CI runs pre-commit.
   Leave the repo's existing lint commands as they are. Run every lint, typecheck, and test command locally before you finish.
10. Commit with the baseline counts in the message.

**Reply:** tools added, boundaries accepted and declined, baseline counts per rule, the proof from step 8 for each rule, and the command to run.

## add

`$ARGUMENTS` after `add` is the correction, such as "don't call fetch in components, use useQuery from lib/api".

1. Name the mistake class in one sentence. Find every instance with `ast-grep run` or `rg`. Quote two real instances. If you find fewer than two and the operator didn't say it repeats, say so and stop.
2. Try a higher level first, and say why it fails before you go lower:
   - Architecture: can the wrong thing become impossible to write? Stop exporting the internal, give the state one owner, or delete the old way.
   - Types: can the type system reject it?
   If one works, propose it to the operator instead of a lint rule.
3. Write the rule in `lint/ast-grep/rules/<id>.yml`, unless it is a folder boundary, which goes in step 5 of `install`.
   - `message` says what is wrong in one sentence.
   - `note` names the fix: the file, function, hook, or type to use instead.
   - Match the smallest pattern that catches every instance from step 1.
4. Write `lint/ast-grep/rule-tests/<id>-test.yml`. Use at least two `invalid` cases trimmed from the real instances, and at least one `valid` case that shows the fix from `note`.
5. Prove the test can fail. Break the rule, for example by deleting a condition, and confirm `ast-grep test --skip-snapshot-tests` fails. Restore the rule and confirm it passes.
6. Run `python3 lint/baseline.py check`. If the repo already has instances, fix them when the fix is mechanical. Otherwise add only the new rule's counts to `lint/baseline.json`, and list the files in your reply as open work.
7. If the agent instruction file has a rule table, add a row pairing the rule with `lint/ast-grep/rules/<id>.yml`, and delete any prose rule it replaces.
8. Commit the rule, its test, and baseline changes together.

**Reply:** the mistake class with its two instances, why architecture and types didn't work, the rule's message and note, the proof from step 5, and the baseline counts.

## Exceptions

A suppression needs `reason: <why>; expires: YYYY-MM-DD` on its line or the line above, with the date at most 180 days out. `check_suppressions.py` enforces this. Ask the operator before you add one.
