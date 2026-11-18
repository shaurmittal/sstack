# Plan: principal-engineer skills plugin

Working name: `sstack`. Rename it before the first commit if you want something else.

## Goal

Build a Claude Code plugin that makes agents write code a principal engineer would approve, for Python, React, and JavaScript projects. Finish v0.1 of the skills by Friday 2026-11-20. Next week, use them as the foundation for a project built 90 to 95% by agents.

The plugin builds on [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT license) and her talk "All Code is Slop (Except Mine)". pstack is written for Cursor. This plugin is written for Claude Code and targets your stack.

## The rule everything follows: the trust pyramid

Spend effort in this order. A problem solved at a higher level never reaches a lower one.

1. **Codebase and architecture.** Give each piece of state one owner, give each task one supported path, and delete old patterns. Agents copy whatever is already in the repo.
2. **Deterministic checks.** Types, lint rules, import boundaries, tests. A lint error message names the fix.
3. **Verification.** Runtime verification drives the real app and captures evidence. Property tests and formal verification check invariants. Expect most tokens to go here.
4. **Prose.** AGENTS.md, rules, and skills, used only for judgment calls nothing can check.

When an agent makes a mistake twice, fix it at the highest level that works. A new line in AGENTS.md is the last resort, because nothing fails when an agent ignores it.

## Ground rules for building the plugin

- Write every skill in Claude Code terms: the `Agent` tool, `.claude/skills/`, `model: opus | sonnet | haiku`. No translation table.
- Keep pstack installed for the skills that work as they are. Copy a pstack skill into this plugin only when Wednesday's gap log shows it needs to change.
- A skill is done only after it has run once on a real repo and done what it claims. A skill that was never run is a draft.
- Run every skill through pstack's `unslop` rules before committing it.
- Skills that change code use `disable-model-invocation: true` so they run only when you type them. Turn auto-invocation on only for skills you trust.

## Repository layout

```
sstack/
├── .claude-plugin/
│   ├── plugin.json          # name, version, description
│   └── marketplace.json     # lets you /plugin marketplace add <your-github>/sstack
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── references/      # examples and long material the skill loads on demand
│       └── scripts/         # CLIs the skill runs, with their own tests
├── agents/                  # subagent definitions
├── hooks/                   # optional: run lint and typecheck after edits
├── rule-packs/
│   ├── react/               # ESLint config, dependency-cruiser config, bad-example fixtures
│   └── python/              # ruff, pyright, and import-linter configs, ast-grep rules, fixtures
├── evals/                   # Friday's test tasks and results
├── AGENTS.md                # how agents work on this repo, written last
└── PLAN.md                  # this file
```

## Wednesday: install, study, baseline

### Setup (30 minutes)

1. Install the **Claude Code** extension in VS Code and sign in.
2. Create the empty `sstack` repo on GitHub, clone it, and open it in VS Code.
3. In the Claude Code panel:
   ```
   /plugin marketplace add cursor/plugins
   /plugin install pstack@cursor-plugins
   /pstack:setup-pstack
   ```
4. Commit this PLAN.md.

### Study (2 to 3 hours)

Read these in order. For each one, write down the answer to the question in `notes/wednesday.md`. Ask Claude "why does this rule exist?" for any line you can't explain.

| Read | Answer this |
|---|---|
| `skills/poteto-mode/SKILL.md` and `playbooks/feature.md` | How does one entry skill pick a playbook, and why are the steps copied into a todo list word for word? |
| `skills/correct/SKILL.md` | Why does it put architecture above types, types above lint, and docs last? |
| `skills/no-comments/SKILL.md` and `agents/comment-sicko.md` | Why does a separate subagent judge the comments, instead of the agent that wrote them? |
| `skills/create-verification-skill/SKILL.md` | What is a feature map, and why must the generated skill prove itself before handoff? |
| `skills/create-formal-verification-skill/SKILL.md` | Why must every property be shown failing on a broken variant first? |
| `skills/interrogate/SKILL.md` | Why keep only findings that a run proves? |
| `skills/principle-encode-lessons-in-structure/SKILL.md` | What makes an instruction a symptom? |
| `docs/harness/claude-code.md` | What exactly breaks when a Cursor skill runs in Claude Code? |

### Baseline run (2 to 3 hours)

Pick two repos. Each needs a test suite, local setup that takes under 10 minutes, and either Python or React. Use one of your own and one open-source repo.

On each repo, run one small real task twice in separate git worktrees:

- **A:** plain Claude Code with no plugin.
- **B:** `/pstack:poteto-mode` with the same prompt.

Write every problem into `notes/gap-log.md` with this shape:

```
| repo | task | what went wrong or didn't fit | pyramid level that would fix it | skill to build or change |
```

The gap log decides which pstack skills get copied and changed on Thursday.

## Thursday: build the plugin

Build in this order. Each line says when the skill is done.

### New skills

| Skill | What it does | Done when |
|---|---|---|
| `lint-pack` | Installs the starter rule pack for the repo's stack, then turns one correction into a new rule whose error message names the fix. Code patterns and banned imports in both languages: ast-grep. Folder boundaries: dependency-cruiser with the swc parser for JS/TS, import-linter for Python. Python rule sets: ruff. Existing violations go in `lint/baseline.json`, and CI fails only when a count goes up. | Each rule has a bad-example fixture that it fails on and a good one it passes, and both run in CI. |
| `python-practices` | Python counterpart to pstack's `typescript-best-practices`: typing discipline, dataclasses and pydantic at boundaries, no bare `except`, and the repo's own conventions read from the code. | One baseline task redone with it produces fewer gap-log entries. |
| `react-practices` | Bans `useEffect` in product code except inside named wrappers, bans imperative timers, keeps derived state out of state, and prefers server data hooks. Every rule that can be linted is in `lint-pack`, and this skill keeps only the judgment parts. | Same as above, on the React repo. |
| `property-tests` | Finds a function or component with an invariant and writes property tests with Hypothesis (Python) or fast-check (JS). Each property is shown failing on a broken variant first. | One property in a baseline repo catches a seeded bug. |
| `agents-md` | Generates AGENTS.md from the code: commands to run, folder layout, and a table that pairs each rule with what enforces it. Prose only for what nothing can check. | The generated file has no rule that lint already enforces. |
| `ui-system` | Agents use your shadcn-based components and tokens. Adds lint bans on raw HTML form controls in product code and on Radix or other UI imports outside `components/ui`. Covers when a new component belongs in the registry. | A UI task in the React repo uses only registry components, and the lint fails when it doesn't. |

### Forked from pstack (only what the gap log asks for)

Likely candidates: a lighter entry skill (`sstack-mode`) with five playbooks (feature, bug fix, refactor, investigation, opening a PR), plus `no-comments` and `correct`, rewritten in Claude Code terms. Keep `create-verification-skill`, `create-formal-verification-skill`, `statechart`, `interrogate`, and `unslop` from pstack unless the gap log shows a problem.

### Optional: a hook

A Claude Code hook that runs lint and typecheck after edits and feeds errors back to the agent. It moves the pyramid's second level into the harness itself. Build it if Thursday has time left.

## Friday: test, measure, tag v0.1

1. Write three tasks per repo in `evals/tasks.md`: one feature, one bug fix, one refactor.
2. Run each task twice in separate worktrees: plain Claude Code, then `/sstack-mode`.
3. Score each run in `evals/results.md`:
   - review findings you would leave on the PR
   - how many of those findings are now caught by an automated check
   - bugs caught by verification that the plain run missed
   - comments added in the diff
   - lines changed (fewer is better when the behavior is the same)
4. Use pstack's eval playbook to compare blind, so you don't know which run you're scoring.
5. Fix the three weakest results. Tag `v0.1.0`.

Six tasks is a small sample. Treat the numbers as a direction, not proof.

## Next week: the automated project

1. **UI registry first.** Build your own shadcn registry (`registry.json`) of improved components, borrowing from 21st.dev where useful. Check each component's states with Playwright screenshots and pstack's visual-parity playbook.
2. **Pipeline.** Spec, then plan, then build, then verify, then PR, chained from `sstack-mode`. Plan it in the project thread once the skills have passed Friday's test. A sloppy loop automated is still sloppy, so the pipeline waits for the foundation.

## Decisions log

- **2026-11-17.** Baseline repos are `calhacks` (React, Next 16, TypeScript 7, 38 vitest files) and `fastapi/typer` (Python, strict mypy). No Python repo of ours has tests.
- **2026-11-17.** Skipped the rest of Wednesday's study and built `lint-pack` before the baseline run. The gap log still decides which pstack skills get forked.
- **2026-11-17.** lint-pack uses ast-grep, not ESLint. typescript-eslint only supports TypeScript below 6.1, and calhacks is on TypeScript 7. ast-grep parses any version, and `ast-grep test` runs each rule's bad and good examples in CI.
- **2026-11-17.** dependency-cruiser runs with `parser: "swc"`. Its default parser read zero `.ts` files under TypeScript 7 and still reported no violations.
- **2026-11-17.** No Fable models anywhere. Code work stays on Opus. Sonnet only fills the former Fable seat in pstack's review panels.

## Risks

- **Friday is tight.** If Thursday runs over, cut `property-tests` and the hook first. Keep `lint-pack` and `agents-md`, because they're the heart of the pyramid.
- **pstack keeps changing.** Pin the version you copied from in each forked skill's header and check upstream changes weekly.
- **Over-strict rules slow agents down.** Every lint rule needs an escape hatch: an inline exception with a reason and an expiry date.
