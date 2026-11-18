# Refactor

You own the contract. The structure changes and the behavior doesn't. If the cleanup turns up a missing feature or a real bug, ship the structural change first and route the rest to `feature` or `bug-fix`.

1. Trace the code to learn its contract. Find every copy of the pattern being changed, not only the ones the request names. Fold in the copies the same pin covers, and list the rest.
2. Pin the behavior before any structure moves. Write characterization tests through the public callers, run them against the current code, and commit them on their own. Type checks and lint are not a pin.
3. Name the target shape: the module layout, types, and call graph you would build today. The reshape must delete branches or states, not add indirection. On the large path, run pstack's `architect` if the shape crosses a function boundary.
4. Subtract first. Delete dead code, one-caller wrappers, and redundant checks before adding the new shape.
5. Move in small steps that keep the pin green. Migrate every caller and delete the old API in the same change, with no shims. Check every rename against the files, including strings and docs. Small: make the edits here. Large: brief `sstack:sstack-agent` with the names being moved and the behavior to hold.
6. Prove the behavior is unchanged. Run the pin and the full suite. For a larger reshape, also diff the old and new outputs on real inputs.
7. Commit the reshape. Break it on purpose in the riskiest spot per SKILL.md, confirm the pin fails, and restore it.
8. Check that the diff lowers reader load somewhere. If it doesn't, revert it.
9. Check every added comment per Comments in SKILL.md. Order the commits: pin, subtraction, reshape.
10. If the refactor removed duplicate copies of a pattern, offer `/sstack:lint-pack add` to stop a new copy from appearing.
11. Run `opening-a-pr`.

**Reply:** the structure that changed, the pin it held against, the proof, the copies you folded in or left, and the reader-load change in lines. No new behavior.
