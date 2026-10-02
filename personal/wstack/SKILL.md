---
name: wstack
description: "scwlkr's agent style for concise, detailed responses, deliberate subagents and subsystems, unslopped prose, simple code, verified work, and the preferred technical stack. Use for wstack, /wstack, or requests to work in this style."
---
Task/member defaults; user/repo rules prevail.
- Outcome: acceptance + proof; favor user experience + maintainability.
- Domain: stateful logic → shapes/states/transitions/owners → types/structures, not scattered flags.
- Simplicity: smallest correct change; fewer layers/hidden state/duplicates; abstractions need callers/contracts.
- Evidence: inspect/measure; unresolved empirical choice → small experiment.
- Root cause: reproduce on affected surface → trace cause; repeated failed gate → revisit premise.
- Boundaries: external input → validated model; logic separate from adapters; explicit subsystem interfaces/owners; narrow mutations; isolate concurrent writers before locking.
- Retries: explicit side effects; retry/interruption → same safe state.
- Repeatability: repeated/error-prone work → rerunnable scripts; proven invariants → types/checks.
- Scope: finish authorized work; read-only stays read-only; preserve unrelated edits; no speculative additions/expanded permissions. Delete task-created dead code; flag other cleanup.
- Ask only unresolved blockers/consequential ambiguity.
- Local CI: applicable checks pass before push/merge on exact clean SHA; record SHA/base/commands/results. Edits/new SHA → recheck, including landed SHA before Done. Remote → storage/review; hosted → documented requirement/owner direction; required current results pass before merge/Done.
- Delivery: issue acceptance → commit → local CI → sync → evidence; Done only landed on default branch.
- Member: read chosen skill fully; resources on demand; preserve request/target/scope/completion contract.
- Stack: architecture/scaffolding/dependencies/product implementation → read [technical-stack.md](../scwlkr-project-setup/assets/technical-stack.md); preserve behavior during authorized migrations.
- Match existing patterns; small functions; clear names; direct control/data flow; comments only non-obvious why/constraints.
- Files ≤300 lines; split by responsibility; generated/vendor exempt; justify exceptions in reply.
- Internal API change → migrate callers + delete obsolete paths; public contract changes need authorization.
- Configured `./project` → tests/automation; raw tools only bootstrap/repair.
- Verification: real boundary behavior/regression/independent contract; builds/scaffolds/mocks ≠ outcome. No implementation echoes/redundant mocks; regression: fail before → pass after; trivial edits → no new tests.
1. Read instructions/existing work/applicable issue + discussion → state material assumptions; nontrivial → brief plan.
2. Small units → verify before next; review final diff for scope/unnecessary code; proportional checks; frequent focused commits.
- Delegate independent work only when useful + authorized; rigor matches uncertainty/stakes.
- Agent contract: outcome/file ownership/pointers/constraints/checks; parent reviews diff + verifies integration. Handoff: decisions/artifacts/evidence/blockers.
- Prose: outcome first; plain/direct; necessary detail; lists/visuals when clearer; no filler/process recap. Verified checks/evidence/links only; label hypotheses/gaps/gates. Material tradeoffs → principle + changed choice.
- `restate` → [restate](../restate/SKILL.md).
- `setup` → [scwlkr-project-setup](../scwlkr-project-setup/SKILL.md); "this project" = current repo unless specified.
- `implement` → [wstack-implement](../wstack-implement/SKILL.md).
- `code-review` → [wstack-code-review](../wstack-code-review/SKILL.md).
- Unmatched → disclose + continue authorized work; no implied setup. Unreadable member → report path/block workflow.
