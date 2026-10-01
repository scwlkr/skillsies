---
name: scwlkr-project-setup
description: "Apply scwlkr's basic setup to new or existing projects: agent instructions, a Rust automation CLI, Linear routing, and a small migration handoff."
---

# Project setup

Run from this skill's directory; `ROOT` is the target project.

1. `python3 scripts/setup.py inspect ROOT` — use its compact inventory and the user's prompt; ask only for missing or ambiguous Linear team/project or conflicting product decisions. Resolve existing Linear destinations through available tools before asking.
2. `python3 scripts/setup.py apply ROOT --team TEAM --linear-project URL` — omit known values; `--name NAME` overrides the detected project name. Creates the Rust `./project` CLI even in non-Rust projects. A path collision requires a targeted repair, never overwriting unrelated files.
3. Read root `AGENTS.md`; remove or rewrite instructions directly contradicting the setup block. Preserve domain rules and user edits; no code migration, test audit, CI setup, or documentation sweep. Add any further alignment gaps to `SETUP-TODO.md` as short checkboxes.
4. `python3 scripts/setup.py check ROOT` — resolve setup failures, rerun `apply`, and confirm `changed: []`. A working CLI scaffold does not prove the app works; record unwired app commands in the handoff. Never run app tests, install dependencies, or provision services merely to scaffold setup.
5. Follow the repository's delivery rules; report changed / already set / missing and the CLI invocation. Never declare missing Linear routing or a failed CLI ready.

Scripts own deterministic setup; inspect their source only to diagnose a failure. CLI commands delegate to real tools, preserve exit codes, and grow in `tools/project-cli/src/routes.rs`. Reuse an existing Rust CLI through this entry point; preserve its implementation. Defaults live in `assets/AGENTS.md`, not in duplicated skill prose.
