---
name: scwlkr-project-setup
description: "Apply scwlkr's basic setup to new or existing projects: agent instructions, a Rust automation CLI, Linear routing, and a small migration handoff."
---

# Project setup

Run from this skill's directory; `ROOT` is the target project.

1. `python3 scripts/setup.py inspect ROOT` — use its compact inventory and the user's prompt; ask only for missing or ambiguous Linear team/project or conflicting product decisions. Resolve existing Linear destinations through available tools before asking.
2. `python3 scripts/setup.py apply ROOT --team TEAM --linear-project URL` — omit known values; `--name NAME` overrides the detected project name. Creates the Rust `./project` CLI even in non-Rust projects. A path collision requires a targeted repair, never overwriting unrelated files.
3. Reconcile root `AGENTS.md`, including old command examples: use `./project`, preserve flags/behavior, and wire missing routes. Merge current asset standards into preserved setup blocks without losing domain rules. Raw bootstrap/repair commands belong under `## CLI bootstrap` or `## CLI repair`. No code migration, test audit, CI setup, or documentation sweep. Keep alignment gaps in `SETUP-TODO.md`; scripts append CI acceptance checkboxes, preserving existing work. CI signals are advisory: resolve false positives in place, retaining checkbox IDs; never infer compliance from keywords or configure/manually dispatch CI during setup.
4. `python3 scripts/setup.py check ROOT` — resolve setup failures, rerun `apply`, and confirm `changed: []`. A working CLI scaffold does not prove the app works; record unwired app commands in the handoff. Never run app tests, install dependencies, or provision services merely to scaffold setup.
5. Follow repository delivery rules. Before merging or marking Done, wait for applicable CI on the current commit to pass (`gh pr checks PR --watch --fail-fast` on GitHub); pending/missing expected checks block completion. Without CI, use existing local gates. Report changed / already set / missing, CLI invocation, and landing/check status; distinguish scaffold readiness from CI alignment pending in the handoff. Report CI compliance only with actual verification; never call incomplete setup ready.

Scripts own deterministic setup; inspect their source only to diagnose a failure. CLI commands delegate to real tools, preserve exit codes, and grow in `tools/project-cli/src/routes.rs`. Reuse an existing Rust CLI through this entry point; preserve its implementation. Defaults live in `assets/AGENTS.md`, not in duplicated skill prose.
