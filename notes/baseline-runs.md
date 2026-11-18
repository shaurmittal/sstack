# Baseline runs, 2026-11-17

Two tasks. Each ran twice, as a separate headless Claude Code session in its own worktree.

- **A:** plain Claude Code. User plugins off.
- **B:** `/pstack:poteto-mode` plus the same prompt. pstack 0.15.43 is the only plugin.

Both arms ran on Opus in `auto` permission mode, with `git push` and `gh pr` blocked. Each prompt ended with "commit on the current branch. Don't push and don't open a PR." Prompts, logs, and `run.sh` are in `~/Desktop/baseline/`. Branches are `baseline/A` and `baseline/B` in each repo.

One run per arm is a direction, not proof.

## Tasks

| Repo | Kind | Prompt |
|---|---|---|
| calhacks at `2aefcf2` | refactor | Two helpers race a promise against a time budget: `withinBudget` in `convex/lib/claude.ts` and `withTimeout` in `shared/verification/moss.ts`. Make it one helper that every caller uses. |
| typer at `695d845` | bug fix | [Discussion #1953](https://github.com/fastapi/typer/discussions/1953). `--help` crashes with `TypeError` when an Argument's help is a lazy string and `rich_markup_mode=None`. The reporter wants help coerced to str at render time, not before. |

The calhacks trap: `withTimeout` swallows a rejection, and `withinBudget` passes it on. The intake retry loop needs the error.

## Results

| | calhacks A | calhacks B | typer A | typer B |
|---|---|---|---|---|
| Minutes | 3.7 | 10.0 | 13.1 | 11.1 |
| Cost, USD | 1.07 | 3.11 | 3.05 | 2.52 |
| Turns | 21 | 61 | 56 | 53 |
| Correct | yes | yes | yes | yes |
| Source lines | +43 −38 | +32 −48 | +51 −22 | +11 −8 |
| Test lines | +52 | +129 | +240 | +72 |
| Comment lines added in source | 10 | 4 | 4, plus 4 docstrings | 0 |
| Commits | 1 | 2, tests first | 1 | 2, failing tests first |
| Subagents | none | Comment Sicko only | none | none |
| Tests left behind | moved tests only. Its parity test was deleted. | characterization tests committed before the change | 16 | 5 |
| Scope | the two helpers. Left a third race in `policyLookup.ts` and asked. | all three races | parameter, command, and group help, plus epilog and `short_help` | parameter help only. Listed command help as follow-up. |

## What each run did

**calhacks A.** Kept swallow-on-rejection. Intake turns errors into values before the race, so the log keeps the API's message. Wrote a side-by-side parity test of the old and new `claude.ts`, then deleted it. `claude.ts` still has no direct test. A leftover `catch` in `composeReply` is now nearly dead code.

**calhacks B.** Chose pass-through-on-rejection. The two callers that relied on swallowing each got their own `.catch`. Committed tests that pin the old behavior first and confirmed they passed on the old code. Proved four ways the tests can fail. Deleted a `call.catch(() => {})` and correctly explained why `Promise.race` already handles a late rejection. Did not delegate to a subagent, although the playbook calls that mandatory.

**typer A.** Fixed every help surface, and stopped `if help:` checks that would resolve a lazy string early through `len()`. Changes what `Command.help` holds. It flagged that for the release notes.

**typer B.** Fixed parameter help only, with an 11-line source change, and listed command help as a follow-up. Explained skipping delegation: "this session says not to spawn agents unless you ask." Skipped `/deslop` because `cursor-team-kit` isn't installed.

## Takeaways

1. On the small refactor, pstack cost three times as much. The extra bought tests that stay and a third duplicate removed. On the bug fix, pstack was cheaper and smaller than plain Claude Code, because the Laziness Protocol kept the scope to parameters.
2. pstack's delegation never happened in Claude Code. Claude Code's own system prompt tells the agent not to spawn agents unless the user asks, and that beat the playbook's "mandatory" in both B runs.
3. pstack added fewer comments: 4 and 0 lines against 10 and 8.
4. Plain Claude Code on Opus 5.5 already verifies a lot. Both A runs broke their own changes on purpose to check the tests. The difference is that B commits the evidence, and A sometimes deletes it.

## sstack-mode, first runs (2026-11-17)

Same prompts and base commits, run as `/sstack:sstack-mode` with sstack and pstack loaded. Branch `baseline/S` in each repo.

| | calhacks A | calhacks B | calhacks S | typer A | typer B | typer S |
|---|---|---|---|---|---|---|
| Minutes | 3.7 | 10.0 | 3.7 | 13.1 | 11.1 | 4.8 |
| Cost, USD | 1.07 | 3.11 | 1.05 | 3.05 | 2.52 | 0.98 |
| Turns | 21 | 61 | 23 | 56 | 53 | 26 |
| Source lines | +43 −38 | +32 −48 | +33 −48 | +51 −22 | +11 −8 | +14 −7 |
| Test lines | +52 | +129 | +118 | +240 | +72 | +67 |
| Pin or failing test committed first | no | yes | yes | no | yes | yes |
| Broke the change on purpose | yes | yes | yes | yes | yes | yes |
| Third race folded in or scope kept narrow | left | folded | folded | widened | narrow | narrow |

Both S runs picked the small path, ran no subagents, and ended with the branch and the `gh pr create` command instead of opening a PR.

**What went wrong:**
- Both S runs wiped their own uncommitted fix while breaking it on purpose, then reapplied it. SKILL.md now says to commit first, then break, then restore with `git checkout`.
- Neither run wrote the size line or ran the comment step, and neither said it skipped them. SKILL.md now requires a four-line first message, an outcome for every step at the end of the reply, and an inline comment check on the small path.

These patches are untested. Friday's eval is their first run.
