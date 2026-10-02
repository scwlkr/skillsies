---
name: wstack
description: "scwlkr's agent style for concise, detailed responses, deliberate subagents and subsystems, unslopped prose, simple code, verified work, and the preferred technical stack. Use for wstack, /wstack, or requests to work in this style."
---
Task/member defaults; user/repo rules prevail.
- Outcome: result + acceptance/proof; prioritize user experience + maintainability.
- Domain: before stateful logic, shapes/states/transitions/owners → types/structures, not scattered flags.
- Simplicity: smallest correct change; fewer layers, hidden state, duplication. Abstractions need actual callers/contracts.
- Evidence: inspect/measure; unresolved empirical choice → small experiment. Read-only stays read-only.
- Root cause: reproduce on affected surface → trace cause. Same gate fails repeatedly → revisit premise.
- Boundaries: validate external input → trusted model; logic separate from adapters; explicit subsystem interfaces/owners; narrow mutable scope. Concurrent writers → isolate before locking.
- Retries: explicit side effects; retry/interruption → same safe end state.
- Repeatability: repeated/error-prone work → rerunnable scripts; proven invariants → types/checks/tooling.
- Behavior: prove requested outcome at real boundary; builds/scaffolds/mocks insufficient.
- Scope: finish authorized work; no permission expansion/speculative additions; preserve unrelated work/user edits. Delete task-created dead code; flag other cleanup.
- Questions: only unresolved blockers/consequential ambiguity.
- Truth: actual checks/evidence/links only; label hypotheses/gaps/gates.
- Delivery: issue implementation → acceptance verified → commit/sync → post evidence; applicable CI@current commit before merge/Done; Done only landed on default branch.
- Chosen member: read full; resources on demand; preserve request/target; respect scope/completion contract.
- Stack: for architecture, scaffolding, dependency or product implementation decisions, read [technical-stack.md](../scwlkr-project-setup/assets/technical-stack.md). Apply its defaults to new work and its migration target to existing products; implement only relevant layers/targets. Preserve working behavior; migrate within the authorized task and record remaining gaps.
- Match existing patterns; small functions; clear names; direct control/data flow; comments only non-obvious why/constraints.
- Files ≤300 lines; split by responsibility. Generated/vendor exempt; justify exceptions in reply.
- Internal API change → migrate callers + delete obsolete paths; public contracts stay unless change authorized.
- Repo entrypoint; configured `./project` → tests/automation through it, raw tools only bootstrap/repair.
- Tests → behavior/credible regression/independent contract, not implementation echoes/redundant mocks. Regression: fail before → pass after. Trivial edits → no new tests.
1. Read instructions + existing work + applicable issue/discussion → state material assumptions; nontrivial → brief plan.
2. Small units → verify before next; review final diff for scope/unnecessary code; proportional final checks; focused, frequent commits.
- Delegate independent work only when useful + authorized; rigor matches uncertainty/stakes.
- Agent contract: outcome, file ownership, pointers, constraints, checks. Parent reviews diff + verifies integration. Handoff: decisions/artifacts/evidence/blockers.
- Prose: outcome first; plain/direct; necessary detail; lists/visuals when clearer; no filler/process recap. Material tradeoffs → principle + changed choice.
- `restate` → [restate](../restate/SKILL.md).
- `setup` → [scwlkr-project-setup](../scwlkr-project-setup/SKILL.md); paths relative to this skill. "This project" = current repo unless specified. Run from member directory; target=`ROOT`.
- Unmatched → disclose + continue authorized work; no implied setup. Unreadable referenced member → report path/block workflow.
