# skillsies

[![skills.sh](https://skills.sh/b/scwlkr/skillsies)](https://skills.sh/scwlkr/skillsies)

Reusable agent skills I use for documentation, design critique, repo cleanup, and writing new skills.

## Install

```sh
npx skills add scwlkr/skillsies
```

To list the skills without installing them:

```sh
npx skills add scwlkr/skillsies --list
```

## Skills

| Skill | Use it for |
| --- | --- |
| `initial-docs` | Create a compact AI-friendly documentation system for new or early-stage software projects. |
| `perfect-docs` | Upgrade an existing software project into a mature, modular, verified documentation system. |
| `spring-cleaning` | Clean, consolidate, and standardize project docs into a coherent reader path. |
| `design-refine` | Run an intense design questioning session and produce synced `DESIGN.md` and `DESIGN.html` artifacts. |
| `write-a-skill` | Create new agent skills with proper structure, progressive disclosure, and bundled resources. |

## skills.sh

This repo is structured for skills.sh:

```txt
skills/<skill-name>/SKILL.md
```

The skills.sh page should appear at:

```txt
https://skills.sh/scwlkr/skillsies
```

skills.sh picks up repo pages after the repo is installed through the `skills` CLI, and page updates may wait on cache refreshes.
