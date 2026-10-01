---
name: update-skills
description: Check and update downloaded global skills in the skillsies others folder using a deterministic CLI. Use when asked to refresh installed third-party skills or check for upstream updates.
---

# Update Skills

When invoked as `$update-skills`, immediately run `python3 <this-skill>/scripts/skill_updates.py update`. Resolve `<this-skill>` from this SKILL.md's directory. No preliminary planning, questions, or separate check is needed; the CLI checks before updating.

If explicitly asked only to check, run the same command with `check` instead of `update`. On the owner's machine, `skill-updates update` and `skill-updates check` are equivalent shortcuts.

The CLI makes no model calls. It inventories downloaded skills, compares recorded GitHub folder revisions, backs up changed downloads and source metadata under ignored `.local/skill-update-backups/`, and verifies updates. It preserves personal skills and leaves untracked, missing, or ambiguous upstream folders intact.

Return one short summary of applied/available updates, skipped folders, and failures. Do not inspect or compare individual skill instructions, repeat checks after a successful command, guess missing sources, or force-refresh skipped copies. Surface errors with the exact next step when known.

Direct CLI use requires Python 3.10+, authenticated GitHub CLI (`gh`), and Node/npm (`npx`). The ordinary commands use `~/.agents/skills` and `~/.agents/.skill-lock.json`; `check --json` provides a machine-readable report. Checks compare recorded upstream revisions, not local edits or the semantic quality of a skill. Updates preserve a backup of any local download edits before replacing them.
