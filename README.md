# skillsies

[![skills.sh](https://skills.sh/b/scwlkr/skillsies)](https://skills.sh/scwlkr/skillsies)

My global agent skills: personal skills in Git, downloaded skills on disk.

```text
skillsies/
  personal/<skill-name>/SKILL.md   # Authored/customized skills, tracked and pushed
  others/<skill-name>/SKILL.md     # Downloaded skills, ignored by Git
  scripts/setup.py                # Connect the global installation folders
```

## Set up this checkout

```sh
python3 scripts/setup.py
```

This links `~/.agents/skills` to `others/`, so global skills.sh downloads and updates automatically use that directory. Codex discovers personal skills through a link in `~/.codex/skills`. Existing Codex skill directories move into the appropriate folder with links preserving their old paths. Identical existing personal copies are preserved under ignored `.local/backups/`; conflicting copies stop setup before migration. Running setup again is safe.

Codex's built-in `.system` skills, plugin caches, and project-scoped skills stay in their managed locations. The skills.sh source/update lock stays at `~/.agents/.skill-lock.json`; downloaded skill files and machine-local lock state are never uploaded here.

## Write a personal skill

Create `personal/<skill-name>/SKILL.md`:

```md
---
name: my-skill
description: What it does and when to use it.
---

Instructions for the task.
```

New folders inside `personal/` are discovered through the existing links. No separate installation step is needed. If a skill does not appear, restart Codex.

Commit and push personal changes normally. Downloads are automatic; Git uploads remain deliberate.

## Download other people's skills

Use global scope and Codex as the target:

```sh
npx skills add owner/repo -g -a codex
npx skills update -g
```

For an inference-free inventory and verified update with backups:

```sh
python3 personal/update-skills/scripts/skill_updates.py check
python3 personal/update-skills/scripts/skill_updates.py update
```

On my machine these are also installed as `skill-updates check` and `skill-updates update`. Invoking `$update-skills` immediately runs this same CLI to check and apply updates, then returns a brief summary. The CLI makes no model calls. It compares recorded GitHub folder revisions, reports downloads with missing provenance or upstream paths, and updates changed tracked skills through the existing skills CLI. Backups and update logs stay in ignored `.local/skill-update-backups/`. It leaves personal skills, untracked downloads, and upstream-deleted skills intact. Python 3.10+, authenticated `gh`, and Node/npm are required; `check --json` emits a machine-readable report. A successful exit means the operation completed; the report still lists any untracked or missing upstream folders, whose freshness is unverified.

The ordinary global symlink installation mode writes directly into `others/` through `~/.agents/skills`. No wrapper or background watcher is required. Installs without `-g` remain local to the current project. Avoid `--copy` if you want one canonical copy.

For Codex's built-in GitHub installer, explicitly pass this checkout's `others/` directory with `--dest`; its default destination is a separate Codex folder. An older direct Codex install can be consolidated by running setup again.

## Personal skills

| Skill | Use it for |
| --- | --- |
| `wstack` | Route requests through connected personal workflows; project setup is the first member. |
| `initial-docs` | Create compact project documentation. |
| `perfect-docs` | Improve an existing project's documentation system. |
| `spring-cleaning` | Consolidate and standardize project docs. |
| `design-refine` | Refine design decisions and produce synced design artifacts. |
| `write-a-skill` | Write reusable agent skills. |
| `relentless-execution` | Add an execution mandate to a prompt. |
| `bubbas-public-style` | Apply the Bubba's Fireworks public-page visual system. |
| `test-audit` | Assess test value using the active repository's own conventions. |
| `update-skills` | Check and update downloaded skills with a deterministic CLI. |

`test-audit` is a locally customized version of [OpenClaw's test-audit](https://github.com/openclaw/openclaw/tree/main/.agents/skills/test-audit), retained as personal work so upstream updates cannot silently replace the adaptations. Keep attribution when editing or sharing derived skills.

## Install these skills elsewhere

```sh
npx skills add scwlkr/skillsies
npx skills add scwlkr/skillsies --list
```

The skills CLI recursively discovers the committed `personal/` tree. `others/` is absent from GitHub, so it is never redistributed by these commands.

## Verify setup logic

```sh
python3 -m unittest discover -s tests -v
```
