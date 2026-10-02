<!-- scwlkr-project-setup:start -->
## Project standards

- Project: {name}. Rust `./project` → tests/automation; `--help` → usage; `doctor` → prerequisites. Extend `tools/project-cli/src/routes.rs`; raw tools only CLI bootstrap/repair.
- Verify real app outcomes/side effects through CLI/UI drivers; scaffold/build ≠ app proof. Retain evidence; stop only processes you started.
- Smallest correct change; preserve unrelated work. Files ≈300 lines, split by responsibility; generated/vendor exempt; justify exceptions in handoff.
- Tests → behavior/credible regression/uncovered independent contract; prefer one owner-boundary check. Verify before deleting redundant/implementation-coupled tests/test-only seams; preserve regression coverage. Regression: fail before → pass after. No quotas/trivial-change tests.
- Linear only: team **{team}**, project {linear_project}. Before substantive work: read issue/discussion, reuse/create issue; ID → branches/PRs; post verification/blockers. Done → acceptance verified + landed on default branch. `SETUP-TODO.md` = setup handoff, never backlog.
- Frequent focused commits/pushes; short-lived branches; merge verified work promptly within repo rules/authorization. Isolate active work; never commit unrelated edits for a clean status.
- Local CI: applicable `./project` checks pass before push/merge on exact clean SHA; retain SHA/base/commands/results. Edits/new SHA → recheck, including landed SHA before Done. Remote → storage/review; hosted → documented requirement/owner direction; required current results pass before merge/Done. Pending/missing/failed ≠ pass.
- CI changes: non-executable docs → light; reliable scope → focused; shared code/dependencies/build/CI/uncertain scope → full; generated/executable docs → behavior checks. Cache costly dependencies/tools/builds keyed by platform/toolchain/lockfile; verify routing/invalidation. Aggregate pass/fail@SHA covers applicable checks; filtering cannot hide failures. Unverified alignment → `SETUP-TODO.md`.
- Task boundaries/after landing → remove completed inactive worktrees/obsolete branches/disposable builds. First verify useful commits on GitHub, inspect uncommitted/untracked/ignored files, preserve useful local data; never upload secrets/caches. Keep active/shared worktrees; managed → host archive tool; creation → using-git-worktrees skill.
- Investigate first; state material assumptions; finish authorized work; ask only consequential blockers. Proportional checks; report verified outcomes/gaps/landing.

## Technical stack

{technical_stack}
<!-- scwlkr-project-setup:end -->
