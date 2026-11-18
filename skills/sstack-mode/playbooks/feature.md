# Feature

You own the design. Plan it, review it, and verify it.

1. Trace the affected subsystem. Name the data shape the feature needs before writing logic: a state machine over scattered booleans, a table over branching, a typed model over repeated shape assumptions.
2. Size the change per SKILL.md.
3. Large only. Run pstack's `architect` for the shape. Then write the throughput checkpoint as four todo items, marking one `n/a: <reason>` when it doesn't apply:
   - **Blocking first steps.** What must land before work can split.
   - **Independent workstreams.** Disjoint files or layers that can run in parallel.
   - **Shared mutable state.** Split the target so workers don't write the same file. Serialize only for a real invariant.
   - **Smallest safe split.** If one worker is best, say why.
4. Write a failing test for the behavior first, when there is a cheap local test path.
5. Small: implement it here. Large: brief `sstack:sstack-agent` per the Subagents section in SKILL.md, then read its diff and run its proof yourself.
6. If the design is contested and hard to undo, run pstack's `interrogate` before you go on.
7. Verify on the real surface. Run the CLI, call the endpoint, or load the page. A passing unit test is not proof that a UI or CLI works. "Inconclusive" is not a pass. Say so.
8. Check every added comment per Comments in SKILL.md.
9. Arrange the work as small ordered commits, each ending in a passing check.
10. Run `opening-a-pr`.

**Reply:** what you built, what you chose and why, with a table when you weighed alternatives, how you verified it, and open decisions.
