# Gap log

Every problem from the baseline runs in [baseline-runs.md](baseline-runs.md). This log decides which pstack skills sstack forks and changes on Thursday.

| repo | task | what went wrong or didn't fit | pyramid level that would fix it | skill to build or change |
|---|---|---|---|---|
| both | both | pstack's subagent delegation never ran. Claude Code's system prompt says not to spawn agents unless the user asks, and that beat poteto-mode's "mandatory" delegation. calhacks B skipped it as too small. typer B quoted the system prompt. | 4, prose. The skill must say that typing `/sstack-mode` is the user's request for the subagents its playbooks name. | `sstack-mode`: fork poteto-mode and its feature, refactor, and bug-fix playbooks |
| calhacks | refactor | pstack cost $3.11 against $1.07 and took 10 minutes against 3.7, for a 30-line refactor. On Claude Pro that cuts how many runs fit in a day. | 4, prose. Scale the ceremony to the diff size. | `sstack-mode`: one path for diffs under about 50 lines, which pins tests and verifies without delegating or running the principle ritual |
| both | both | Each B reply ended with a 4 to 8 bullet "principles that shaped it" section, because poteto-mode makes citing principles non-negotiable. The reader gets a longer report and no new facts. | 4, prose | `sstack-mode`: keep principles as reading, drop the citation section from the reply |
| typer | bug fix | B skipped `/deslop` because it lives in `cursor-team-kit`, a second Cursor plugin that isn't installed. | 4, prose | `sstack-mode`: replace the deslop step with pstack's `unslop` plus `no-comments` |
| calhacks | refactor | A wrote a parity test that compared the old and new `claude.ts`, then deleted it. `claude.ts` still has no direct test. B committed characterization tests first. | 3, verification | `sstack-mode` refactor playbook: pin current behavior with tests that stay, and commit them before the change |
| calhacks | refactor | A did the literal task, two helpers, and left a third hand-written race in `policyAnswerWithin`. Nothing stops a fourth copy. | 2, deterministic. An ast-grep rule that bans `Promise.race` with `setTimeout` outside `shared/budget.ts` or `shared/timeout.ts`. | `lint-pack add` on calhacks, after one of the refactors lands |
| typer | bug fix | Both arms lost turns because 11 tests fail at 80 columns. typer's `scripts/test.sh` sets `TERMINAL_WIDTH=3000`, but both agents ran `pytest` directly. | 2, deterministic. A conftest check that fails fast with "run scripts/test.sh" when the width isn't set. A line in AGENTS.md comes second. | `agents-md`: the commands section names the repo's test script, and it suggests the fail-fast check when a suite needs environment variables |
| typer | bug fix | A widened scope without asking. It fixed command and group help too, changing what the public `Command.help` attribute holds. That may be right, but the operator learned it after the work. | 4, judgment | `sstack-mode` bug-fix playbook: state the scope boundary before editing, and ask only when the change crosses a public API |
| calhacks | refactor | The two arms picked opposite error semantics for the merged helper, swallow versus pass-through. Both were correct, and neither explained the choice before writing code. | 4, judgment | none. B's choice is the more composable one. Note for `python-practices` and `react-practices`: prefer helpers that pass errors through and let callers catch. |

| calhacks, typer | refactor, bug fix | sstack-mode, first runs: both wiped their own uncommitted fix while breaking it on purpose. | 4, prose: commit before breaking | `sstack-mode`, patched 2026-11-17 |
| calhacks, typer | refactor, bug fix | sstack-mode, first runs: neither wrote the size line or ran the comment step, and neither said so. | 4, prose, made checkable: an outcome line per step in the reply | `sstack-mode`, patched 2026-11-17 |

## What works as is

- Reading `docs/harness/claude-code.md` first. Both B runs did, and pstack's model mapping worked: Comment Sicko ran as `opus medium` from `~/.claude/rules/pstack-models.md`.
- Failing tests first, and deliberately breaking each change to prove the tests catch it. Keep this from pstack unchanged.
- `no-comments` and Comment Sicko. B added 4 and 0 comment lines, against 10 and 8 for A.

## Decision for Thursday

Fork `poteto-mode` into `sstack-mode` with five playbooks. The changes come from rows 1 to 5 and row 8. Keep `no-comments`, `create-verification-skill`, `interrogate`, and `unslop` from pstack. No run touched `correct`, so it stays unforked until a run shows a gap.
