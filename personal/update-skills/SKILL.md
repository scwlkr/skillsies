---
name: update-others
description: Check and update downloaded global skills in the skillsies others folder using a deterministic CLI. Use when asked to refresh installed third-party skills or check for upstream updates.
---

# Update Downloaded Skills

Run the bundled CLI; do not spend model inference comparing skill instructions or rebuilding an updater.

- Check only: `python3 <this-skill>/scripts/skill_updates.py check`.
- Apply updates when requested: `python3 <this-skill>/scripts/skill_updates.py update`.
- On the owner's machine, the same commands are available as `skill-updates check` and `skill-updates update`.

The CLI inventories the global downloaded directory, reads the skills.sh source lock, compares GitHub folder revisions, and delegates updates to the existing skills CLI. It backs up changed downloads and lock metadata under the checkout's ignored `.local/skill-update-backups/`, then checks the result. It never selects personal skills, installs new upstream skills, or deletes folders missing upstream.

Report available/applied updates and any skipped folders or failures. A folder without provenance is untracked, not verified current; do not guess its source. A uniquely matching moved folder is delegated to the official updater and must pass verification. Missing or ambiguous upstream folders are reported and left intact. Do not force-refresh customized or untracked copies.

Direct CLI use requires Python 3.10+, authenticated GitHub CLI (`gh`), and Node/npm (`npx`). The ordinary commands use `~/.agents/skills` and `~/.agents/.skill-lock.json`; `check --json` provides a machine-readable report. Checks compare recorded upstream revisions, not local edits or the semantic quality of a skill. Updates preserve a backup of any local download edits before replacing them.
