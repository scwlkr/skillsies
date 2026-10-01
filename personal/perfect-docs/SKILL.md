---
name: perfect-docs
description: Upgrade an existing software project into a mature, compact, modular, verified documentation system for humans and AI agents.
---

# perfect-docs

Use this skill to audit an existing project and improve its docs into a mature modular documentation system.

The goal is accurate, compact docs that help humans and AI/Codex find the right context fast.

## Core Purpose

Create or repair docs that:

- reflect the real current project state
- explain setup, usage, architecture, and reference behavior clearly
- tell AI/Codex which docs to load for a task
- separate verified behavior from planned or unverified behavior
- preserve useful existing docs
- add deeper docs only where the project needs them

## Process to Follow

1. Inspect the target project before changing docs.

   Understand:

   - project purpose, target user, and current stage
   - what works, what is partial, and what is missing
   - how the project runs, tests, builds, and deploys
   - source layout, scripts, configs, env vars, APIs, CLIs, and entrypoints
   - stable architecture vs still-fluid design choices
   - what docs already exist

2. Compare existing docs to the real project.

   Look for:

   - accurate docs worth keeping
   - outdated or unverified claims
   - missing setup, run, test, build, or deploy steps
   - documented features that are not implemented
   - duplicate docs that should be merged
   - large docs that should be split
   - stale docs that should move to `docs/todo/`

3. Create or update the documentation structure.

   Use the template below as the default mature shape.
   Keep it close, but do not create irrelevant folders just to fill space.

4. Keep normal docs factual and verified.

   If a claim is not confirmed from source, tests, scripts, config, examples, working commands, or accurate existing docs, move it to `docs/todo/needs-verification.md`.

5. Keep future ideas and missing behavior in `docs/todo/`.

   Do not document planned features as if they already work.

6. Re-read changed docs before finishing.

   Check links, paths, commands, and status claims.

---

# Documentation Structure Template

Create this structure unless the user asks otherwise or the project clearly does not need part of it.

```txt
AGENTS.md                                      # compact repo-level AI/Codex instructions
README.md                                      # human-facing overview, status, and quick start
CHANGELOG.md                                   # versioned history once changes/releases matter

docs/                                          # modular documentation folder
docs/AGENTS.md                                 # docs-specific AI/Codex instructions if useful
docs/index.md                                  # docs homepage and table of contents
docs/map.md                                    # routing file that tells AI what docs to load by task
docs/status.md                                 # implemented, partial, planned, missing, and unverified behavior

docs/concepts/                                 # explanation docs for project ideas and mental models
docs/concepts/index.md                         # table of contents for concept docs
docs/concepts/project.md                       # what the project is, why it exists, and what it is not
docs/concepts/core-workflow.md                 # normal end-to-end workflow in plain language
docs/concepts/workspace.md                     # workspace/project model if relevant
docs/concepts/configuration.md                 # config model if relevant

docs/guides/                                   # task-based how-to documentation
docs/guides/index.md                           # table of contents for guides
docs/guides/installation.md                    # setup steps
docs/guides/first-run.md                       # fastest path to a successful run
docs/guides/common-workflows.md                # repeated real-world workflows
docs/guides/troubleshooting.md                 # known problems, causes, and fixes

docs/reference/                                # exact factual reference docs
docs/reference/index.md                        # table of contents for reference docs
docs/reference/cli.md                          # CLI commands, flags, args, and examples if relevant
docs/reference/config.md                       # config fields, defaults, examples, and behavior if relevant
docs/reference/env.md                          # environment variables and required secrets if relevant
docs/reference/api.md                          # endpoints, schemas, and examples if relevant

docs/architecture/                             # internal design and system behavior docs
docs/architecture/index.md                     # table of contents for architecture docs
docs/architecture/overview.md                  # current system shape, main parts, and boundaries
docs/architecture/file-layout.md               # repo/source layout and major folder responsibilities
docs/architecture/data-flow.md                 # how data moves through the project
docs/architecture/lifecycle.md                 # startup, execution, shutdown, and errors if relevant
docs/architecture/dependencies.md              # important dependencies and why they exist

docs/decisions/                                # short records explaining important choices
docs/decisions/index.md                        # table of contents for decision records
docs/decisions/0001-docs-structure.md          # why this docs structure exists

docs/todo/                                     # WIP, planned, missing, uncertain, or unverified docs
docs/todo/index.md                             # table of contents for todo docs
docs/todo/docs-todo.md                         # docs that still need writing, splitting, or cleanup
docs/todo/missing-features.md                  # planned/discussed features not implemented yet
docs/todo/needs-verification.md                # claims, workflows, or commands needing verification
```

Do not add `.codex/`, `.agents/`, custom skills, or helper scripts unless the project already uses them or the user asks for them.

---

# Rules

## 1. Verified docs only

Docs outside `docs/todo/` must describe real behavior verified by source, tests, scripts, config, examples, working commands, or accurate existing docs.

If it cannot be verified, move it to `docs/todo/needs-verification.md`.

## 2. Keep docs compact

Target size:

- ideal: 80-200 lines per file
- hard max: 300 lines unless the user explicitly asks otherwise

If a doc grows too large, split it and link to the deeper doc.

## 3. Keep docs linked

Every doc should include a short `Related` section when another doc has useful context.

Example:

```md
## Related

- [Project status](../status.md)
- [File layout](../architecture/file-layout.md)
```

## 4. Do not create empty bloat

Create useful structure, not fake completeness.

If a section cannot be verified yet, write a short placeholder and link to `docs/todo/needs-verification.md`.

## 5. Fit the project

The template is a strong default, not a law.

- Use one CLI/API/config reference file until the surface is large enough to split.
- Skip workspace, config, lifecycle, dependency, or API docs when there is no meaningful content.
- Add project-specific docs only when they reduce confusion.

## 6. Separate now from later

Use this boundary:

```txt
docs/        # implemented or verified project facts
docs/todo/   # planned, missing, uncertain, or unverified information
```

Never mix planned features into normal docs unless clearly labeled as planned and linked to `docs/todo/`.

## 7. Prefer source truth over docs truth

If existing docs disagree with source code, trust the source code and mark the old docs as outdated or needing verification.

---

# Required Content

## Core files

- `AGENTS.md`: AI/Codex instructions, doc loading rules, run/test commands, and do-not-invent rules.
- `README.md`: project name, description, current status, setup, quick start, and docs links.
- `CHANGELOG.md`: release/change history. If no releases exist, say there are no tagged releases yet.
- `docs/index.md`: docs homepage and table of contents.
- `docs/map.md`: task-based routing for which docs to load.
- `docs/status.md`: source of truth for implemented, partial, planned, missing, and unverified behavior.

## Doc families

- `docs/concepts/`: project purpose, scope, mental models, and core workflow.
- `docs/guides/`: install, first run, common workflows, and troubleshooting.
- `docs/reference/`: exact CLI, config, env, API, schema, or data reference.
- `docs/architecture/`: system shape, file layout, data flow, lifecycle, and dependencies.
- `docs/decisions/`: short decision records for important choices.
- `docs/todo/`: planned, missing, stale, uncertain, or unverified docs and behavior.

## Status file

Keep `docs/status.md` current with these sections:

- `Implemented`
- `Partial`
- `Planned`
- `Missing`
- `Needs Verification`

---

# Output Requirements

When finished, provide:

1. A short summary of what changed.
2. A list of docs created, updated, moved, or removed.
3. Any project claims moved to `docs/todo/needs-verification.md`.
4. Any commands used to verify behavior.
5. Any remaining documentation gaps.

Do not claim the documentation is complete unless all major project behavior has been verified.
