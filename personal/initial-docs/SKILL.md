---
name: initial-docs
description: Create an initial modular documentation system for a new or early-stage software project. Use this when a project needs AI-friendly docs that can grow into a fuller mature documentation structure later.
---

# initial-docs

Use this skill to create a compact documentation system for a brand new or early-stage software project.

The goal is to document the project’s real current state without creating a large mature documentation tree too early.

## Core Purpose

Create the initial documentation structure that:

- helps humans understand the project quickly
- helps AI/Codex know what to read and where to work
- keeps docs compact and modular
- separates verified behavior from planned or unverified behavior

## Process to Follow

1. Inspect the target project before writing docs.

   Understand:

   - What is this project?
   - What problem does it solve?
   - What stage is it in?
   - What currently works?
   - What is partial, missing, or unverified?
   - How does the project run?
   - How is the project tested or verified?
   - What source folders, scripts, config files, and entrypoints exist?
   - What docs already exist, if any?

2. Compare the current project state to any existing docs.

   Look for:

   - outdated claims
   - missing setup steps
   - missing run commands
   - features documented as real but not implemented
   - useful docs that should be preserved
   - docs that should move into `docs/todo/`

3. Create or update the initial documentation structure.

   Do not blindly overwrite useful existing docs.
   Merge, simplify, split, or relocate docs as needed.

4. Keep normal docs factual and verified.

   If a behavior is not confirmed from source, tests, scripts, config, or a working command, place it in `docs/todo/needs-verification.md`.

5. Leave future ideas and unimplemented features in `docs/todo/`.

   Do not document future features as if they already work.

---

# Documentation Structure Template

Create this structure unless the user asks otherwise.

```txt
AGENTS.md                                      # compact repo-level AI/Codex instructions
README.md                                      # human-facing project overview, current status, and quick start
CHANGELOG.md                                   # versioned history once changes/releases matter

docs/                                          # modular documentation folder
docs/index.md                                  # docs homepage and table of contents
docs/map.md                                    # routing file that tells AI what docs to load by task
docs/status.md                                 # truth file for implemented, partial, planned, and unverified behavior

docs/concepts/                                 # explanation docs for core project ideas
docs/concepts/index.md                         # table of contents for concept docs
docs/concepts/project.md                       # what the project is, why it exists, and what it is not
docs/concepts/core-workflow.md                 # normal end-to-end workflow in plain language

docs/guides/                                   # task-based how-to documentation
docs/guides/index.md                           # table of contents for guides
docs/guides/installation.md                    # how to install or set up the project
docs/guides/first-run.md                       # fastest path from setup to first successful run
docs/guides/troubleshooting.md                 # common problems, causes, and fixes

docs/reference/                                # exact factual reference docs
docs/reference/index.md                        # table of contents for reference docs
docs/reference/cli.md                          # commands, flags, arguments, and examples if the project has a CLI
docs/reference/config.md                       # config fields, defaults, examples, and behavior if config exists
docs/reference/env.md                          # environment variables and required secrets if the project uses them

docs/architecture/                             # lightweight internal design docs
docs/architecture/index.md                     # table of contents for architecture docs
docs/architecture/overview.md                  # current system shape, main parts, and boundaries
docs/architecture/file-layout.md               # repo/source layout and what each major folder does
docs/architecture/data-flow.md                 # how data moves from input to output

docs/decisions/                                # short records explaining important choices
docs/decisions/index.md                        # table of contents for decision records
docs/decisions/0001-project-shape.md           # initial project architecture/docs/tooling direction

docs/todo/                                     # WIP, planned, missing, uncertain, or unverified docs
docs/todo/index.md                             # table of contents for todo docs
docs/todo/docs-todo.md                         # docs that still need to be written, split, or cleaned
docs/todo/missing-features.md                  # features not implemented yet but planned or discussed
docs/todo/needs-verification.md                # claims, workflows, or commands that need source/test verification

src/                                           # main source code folder
src/...                                        # actual implementation files

tests/                                         # test files once behavior needs verification
tests/...                                      # actual test implementation files
```

---

# Rules

## 1. Verified docs only

Docs outside `docs/todo/` must describe real, verified project behavior.

A claim is verified only when confirmed by one or more of:

- source code
- tests
- package scripts
- config files
- examples
- working commands
- existing accurate docs

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

Create the structure, but avoid filling files with fake content.

If a section cannot be verified yet, write a short placeholder like:

```md
# CLI Reference

No CLI commands have been verified yet.

See [Needs Verification](../todo/needs-verification.md).
```

## 5. Separate now from later

Use this boundary:

```txt
docs/        # implemented or verified project facts
docs/todo/   # planned, missing, uncertain, or unverified information
```

Never mix planned features into normal docs unless clearly labeled as planned and linked to `docs/todo/`.

## 6. Prefer source truth over docs truth

If existing docs disagree with source code, trust the source code and mark the old docs as outdated or needing verification.

---

# Required Files and What to Put in Them

## `AGENTS.md`

Purpose: compact repo-level instructions for AI/Codex.

Include:

- project summary
- source and docs locations
- setup/run/test commands
- doc loading rules
- verification rules
- do-not-invent rule

Keep this file short.

## `README.md`

Purpose: human-facing front door.

Include:

- project name
- one-paragraph description
- current project status
- install/setup
- quick start
- links to docs

Do not turn the README into the full manual.

## `CHANGELOG.md`

Purpose: versioned project history.

If the project has no releases yet, create a minimal file:

```md
# Changelog

This project has no tagged releases yet.
```

## `docs/index.md`

Purpose: documentation homepage.

Include links to:

- status
- map
- concepts
- guides
- reference
- architecture
- decisions
- todo

## `docs/map.md`

Purpose: AI routing file.

Include task-based loading guidance.

Example:

```md
# Documentation Map

Load only the docs needed for the task.

## If changing setup or install behavior

Read:

1. `docs/guides/installation.md`
2. `docs/guides/first-run.md`
3. `docs/status.md`

## If changing CLI behavior

Read:

1. `docs/reference/cli.md`
2. `docs/architecture/overview.md`
3. `docs/status.md`

## If changing config or environment behavior

Read:

1. `docs/reference/config.md`
2. `docs/reference/env.md`
3. `docs/status.md`

## If updating docs

Read:

1. `docs/index.md`
2. `docs/map.md`
3. `docs/status.md`
4. `docs/todo/needs-verification.md`
```

## `docs/status.md`

Purpose: source-of-truth project status.

Include sections:

```md
# Project Status

## Implemented

## Partial

## Planned

## Missing

## Needs Verification
```

This file is critical. Keep it current.

## `docs/concepts/project.md`

Purpose: explain what the project is and is not.

Include:

- purpose
- target user
- current scope
- non-goals

## `docs/concepts/core-workflow.md`

Purpose: explain the normal workflow in plain language.

Include:

- input
- main steps
- output
- what currently works
- what is not verified

## `docs/guides/installation.md`

Purpose: setup instructions.

Include only verified install/setup steps.

## `docs/guides/first-run.md`

Purpose: fastest successful path.

Include:

- prerequisites
- command sequence
- expected output
- troubleshooting links

## `docs/guides/troubleshooting.md`

Purpose: known problems and fixes.

Include only issues found in source, tests, README, existing docs, or project history.

## `docs/reference/cli.md`

Purpose: exact CLI reference.

If no CLI exists, state that no CLI has been verified yet.

If CLI exists, include:

- commands
- usage
- flags
- arguments
- examples
- expected behavior

## `docs/reference/config.md`

Purpose: exact config reference.

If no config exists, state that no config file has been verified yet.

If config exists, include:

- config file names
- fields
- types
- defaults
- examples

## `docs/reference/env.md`

Purpose: environment variables and secrets.

Include:

- variable name
- required or optional
- purpose
- example placeholder value
- where it is used

Never include real secrets.

## `docs/architecture/overview.md`

Purpose: explain current system shape.

Include:

- main components
- important boundaries
- runtime entrypoints
- external services if any

## `docs/architecture/file-layout.md`

Purpose: explain repo/source layout.

Include major folders only. Do not document every tiny file unless important.

## `docs/architecture/data-flow.md`

Purpose: explain how data moves through the project.

If data flow is not yet clear, add a short verified summary and put unknowns in `docs/todo/needs-verification.md`.

## `docs/decisions/0001-project-shape.md`

Purpose: first lightweight decision record.

Use this format:

```md
# 0001: Project Shape

## Status

Accepted

## Context

## Decision

## Consequences
```

## `docs/todo/docs-todo.md`

Purpose: track docs work.

Include:

- missing docs
- docs that need cleanup
- docs that need splitting
- docs that need examples

## `docs/todo/missing-features.md`

Purpose: track unimplemented features.

Include only planned or discussed features that are not implemented.

## `docs/todo/needs-verification.md`

Purpose: track uncertain claims.

Include:

- claim
- where it came from
- how to verify it
- current status

---

# Output Requirements

When finished, provide:

1. A short summary of what changed.
2. A list of docs created, updated, moved, or removed.
3. Any project claims that were moved to `docs/todo/needs-verification.md`.
4. Any commands used to verify behavior.
5. Any remaining documentation gaps.

Do not claim the documentation is complete unless all major project behavior has been verified.
