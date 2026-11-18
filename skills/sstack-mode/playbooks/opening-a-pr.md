# Opening a PR

Every code playbook ends here.

1. Confirm the work is on a branch, not the default branch, with only this task's changes.
2. Order the commits so each one ends in a passing check. Apply pstack's `unslop` to every commit message.
3. If the operator's request asked for a PR, push the branch and open it with `gh pr create`, not as a draft. Otherwise stop here, and put the branch name and the `gh pr create` command in the reply.

Title: `type(scope): subject`, naming the symbol that carries the change.

Body: under 40 lines, with these `##` headings in order, dropping empty ones: `Why`, `What changed`, `Scope`, `Tradeoffs` (only rejected alternatives a reviewer would ask about), `Blast radius`, `Verification`. Apply `unslop`. Put long logs in a PR comment and link to it.
