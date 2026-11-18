# Bug fix

You own the fix. Every shipped line traces to evidence from running the code. A change that "might help" is a hypothesis, and it doesn't ship. When evidence refutes a hypothesis, revert what it motivated.

1. Reproduce it yourself by running the code: a test, the CLI, a script, or the app. If it won't reproduce, narrow the conditions or add logging until it does. Ask the operator only after that fails, and say what you couldn't reach.
2. Find the cause by elimination. List the candidate causes, then rule them out with evidence, picking each time the check that removes the most candidates. For a regression, run pstack's `why`. When program state is unclear, add logging and read it as the code runs. Confirm the mechanism by running it before you plan the fix.
3. State the scope in one line before editing: what the fix will change and what it will leave alone. Search for every other place the same mechanism breaks. Fix the ones the same root cause covers. If the wider fix would change a public API's behavior, follow Autonomy in SKILL.md.
4. Write a failing test that reproduces the bug, and commit it on its own.
5. Size the change per SKILL.md. Small: fix it here. Large: run pstack's `architect` if the fix crosses a function boundary, then brief `sstack:sstack-agent`.
6. Verify on the same surface as step 1. The original repro now passes. A unit test shows the branch works, not that the bug is gone.
7. Commit the fix. Break it on purpose per SKILL.md, confirm the test fails, and restore it.
8. Check every added comment per Comments in SKILL.md.
9. Run `opening-a-pr`.

**Reply:** what was broken, the root cause, the fix, the scope you left alone, and how you verified it. Paste the failing-then-passing repro output.
