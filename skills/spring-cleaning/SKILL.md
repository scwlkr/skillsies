---
name: spring-cleaning
description: Ruthlessly clean, consolidate, and standardize project documentation into a coherent user-manual path with canonical language, structure, formatting, and a verified active-docs audit.
---

# Spring Cleaning

Use when a project needs cleaner docs, fewer scattered files, one project voice, canonical language, a better README, or planning notes turned into current documentation.

## Rules

- Docs-only by default: edit prose docs, not source, tests, configs, manifests, lockfiles, generated files, build output, vendored files, migrations, schemas, notebooks, or generated API/static-site output.
- You may inspect code, manifests, scripts, CI, and existing docs as evidence for commands, paths, architecture clues, assets, and mechanical facts.
- Do not substantively edit legal, governance, or compliance docs; only safe formatting is allowed.
- Do not invent project facts, commands, features, badges, screenshots, diagrams, roadmap items, or architecture intent.
- Direct cleanup request means edit directly; audit/review/preview/plan means dry run; unclear project meaning means ask one focused question with a recommended answer.
- Do not browse for README trends during a normal run; use durable GitHub readability conventions and repo evidence.

## Required Core

Ensure these exist and are useful: `README.md`, `docs/README.md`, `docs/glossary.md`, `docs/style-guide.md`, `docs/architecture.md`, and `docs/deprecated/`.

- `README.md`: accurate, scannable branded GitHub landing page, not plain docs; keep project identity, quick start, useful links, real badges/assets only, and status.
  Add strong visual identity, memorable section names, tasteful badges/tables, project-world language, and a little project-specific weirdness without cringe.
- `docs/README.md`: canonical documentation map and reader path.
- `docs/glossary.md`: prescriptive project language; rewrite active docs to match it.
- `docs/style-guide.md`: project-specific doc voice, headings, links, filenames, examples, deprecation rules, and cleanup standards.
- `docs/architecture.md`: observable structure, components, data flow, dependencies, decisions, and unresolved questions; never invent intent.

## Workflow

1. Inventory documentation and exclude generated/legal/governance/compliance files from normal editing.
2. Verify mechanical facts against repo evidence before documenting commands, paths, scripts, services, assets, dependencies, CI, config names, or tests.
3. Build the active reader path from `README.md` to `docs/README.md` to focused topic docs.
4. Consolidate duplicate explanations into one canonical home and replace repeats with short links.
5. Convert planning, phase, proposal, PRD/SDD/TDD, roadmap, notes, draft, TODO, TBD, WIP, speculative, or historical content into current facts, unresolved questions, or deprecated artifacts.
6. Rename active docs toward lowercase kebab-case, clear nouns, sentence-case headings, and user-manual filenames.
7. Move retired docs to `docs/deprecated/` while preserving original paths and adding a short note with reason, replacement, and original path.
8. Delete only empty, accidental, verbatim duplicate, generated, explicitly safe, or explicitly approved docs.
9. Repair links after every move, rename, merge, or deletion; do not guess ambiguous targets.
10. Run only existing safe docs-only formatters when configured.

## Done Criteria

- Every active doc has a clear reader need, canonical role, current filename, place in the reader path, and no unjustified duplicate or planning residue.
- Suspicious active docs with names like plan, phase, contract, PRD, SDD, TDD, spec, draft, or notes are renamed, merged, deprecated, or explicitly justified.
- Active docs use the glossary and style guide, present tense, concrete language, and verified repo facts.
- Final chat report lists created, updated, renamed, merged, deprecated, deleted, link repairs, validation, language/style decisions, active-docs audit, suspicious docs kept, and unresolved questions.
