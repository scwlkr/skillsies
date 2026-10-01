## Linear work queue

- Team: **WLKR LABS**.
- Project: [maitools](https://linear.app/wlkr-labs/project/maitools-8fb9ab2a495b).
- Linear is the task source of truth. Existing GitHub issues and Markdown plans are historical context; this section supersedes older tracker or backlog guidance.
- Before starting substantive work, read the Linear issue and discussion and check for existing work. Find or create a Linear issue for substantive user-requested work, not every question or minor action.
- Keep status current, include the issue ID in branches and PRs, and post concise outcomes or blockers. Mark Done only when completion criteria are met.
- Do not maintain a competing Markdown backlog or import or sync GitHub issues.

## Skill ownership and installation

- Put authored and intentionally customized global skills in `personal/<skill-name>/`. Track those files in Git.
- `others/` contains downloads and is ignored. Do not force-add downloaded skills, backups, or machine-local lock state.
- Normal global skills.sh installs use `npx skills add <source> -g -a codex`; the existing `~/.agents/skills` link routes them to `others/` automatically.
- For the built-in Codex installer, pass `--dest <this-checkout>/others`. Use the personal directory explicitly with the built-in skill creator.
- Run `python3 scripts/setup.py` to connect a fresh checkout or consolidate older direct Codex installs. Preserve `.system`, plugin caches, and project-scoped skills.
- Verify setup with `python3 -m unittest discover -s tests -v`; verify real discovery and Git exclusion after changing the live folder links.
