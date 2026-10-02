---
name: scwlkr-project-setup
description: "Apply scwlkr's setup + preferred stack to new/existing projects: agent instructions, Rust CLI, Linear routing, migration handoff."
---
Run from skill directory; `ROOT` = target project. Read [assets/technical-stack.md](assets/technical-stack.md).
Scope: instructions/CLI/handoff; no product migration, test audit, CI configuration/dispatch, docs sweep, app tests, dependency installs or service provisioning.

1. `python3 scripts/setup.py inspect ROOT` → inventory + prompt; resolve existing Linear destinations via tools; ask only missing/ambiguous team/project or conflicting product choices.
2. `python3 scripts/setup.py apply ROOT --team TEAM --linear-project URL` → omit known values; `--name NAME` overrides detected name. Rust `./project` even in non-Rust repos; collisions → targeted repair, preserve unrelated files.
3. Reconcile root `AGENTS.md`: commands → `./project`, preserve flags/behavior, wire missing routes; merge asset standards + full stack, preserve domain rules/explicit exceptions. `SETUP-TODO.md` → current→target gaps, exception reasons, bounded migrations. Raw examples only under `## CLI bootstrap` / `## CLI repair`. CI hints ≠ compliance; correct false positives in place, preserve checkbox IDs/owner work.
4. `python3 scripts/setup.py check ROOT` → fix failures; repeat `apply` must return `changed: []`; record unwired app commands in handoff.
5. Delivery → repository rules + [assets/AGENTS.md](assets/AGENTS.md) local CI gates. Report changed/already set/missing, CLI invocation, checks/landing/gaps. Scaffold readiness ≠ app proof or CI compliance; CI alignment stays pending until verified.

Scripts own setup; read source only for failure diagnosis. CLI → real tools + preserved exit codes; extend `tools/project-cli/src/routes.rs`; reuse existing Rust CLI, preserve implementation.
