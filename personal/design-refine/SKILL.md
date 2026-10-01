---
name: design-refine
description: Grilling session that combatively, but constructively generates or refines both a Google design.md-aligned DESIGN.md and a DESIGN.html visual audit after an intense questioning session.
---

Interview me relentlessly about every aspect of this projects design until we reach a shared design vision. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Operating contract

The end state is a shared design vision captured in both `DESIGN.md` and `DESIGN.html`.

Start by identifying the target project and existing design evidence: `DESIGN.md`, `DESIGN.html`, README, docs, screenshots, package metadata, routes, components, styles, and running app behavior when available. If the target project is unclear, ask one concrete question.

Treat existing code and docs as evidence. Ask the user only for decisions that cannot be answered from the repo or runtime.

## Interview loop

1. Ask exactly one design question at a time, then wait.
2. Include your recommended answer with each question and briefly explain why.
3. Be combative but constructive: challenge vague taste words, contradictions, hidden assumptions, weak constraints, and choices that do not fit the project.
4. Walk the design tree in dependency order: audience, product promise, core workflows, information architecture, content voice, visual language, interaction model, responsive behavior, accessibility, technical constraints, and success criteria.
5. Resolve upstream decisions before asking dependent questions. Reopen earlier answers when later evidence conflicts with them.
6. Keep a running decision log and unresolved-questions list during the session.

## DESIGN.md rules

- When the design vision is stable, create or update `DESIGN.md` and `DESIGN.html` together.
- `DESIGN.md` must follow the Google Labs Code `design.md` alpha model exactly: YAML front matter design tokens first, then markdown rationale sections.
- Use [DESIGN-FORMAT.md](./DESIGN-FORMAT.md) for the `DESIGN.md` structure unless the repo already has stricter compatible design-doc conventions.
- `DESIGN.md` is the design-system source of truth. Tokens are normative; prose explains why those values exist and how to apply them.
- Put machine-readable tokens in front matter: `version`, `name`, optional `description`, `colors`, `typography`, `rounded`, `spacing`, and `components`.
- Prefer recommended token names (`primary`, `secondary`, `tertiary`, `neutral`, `surface`, `on-surface`, `error`; `headline-*`, `body-*`, `label-*`; `none`, `sm`, `md`, `lg`, `xl`, `full`) before inventing custom names.
- Component states are separate related entries such as `button-primary`, `button-primary-hover`, and `input-field-focus`.
- Token references must use `{path.to.token}` and resolve.
- Markdown sections must use this order when present: `Overview`/`Brand & Style`, `Colors`, `Typography`, `Layout`/`Layout & Spacing`, `Elevation & Depth`/`Elevation`, `Shapes`, `Components`, `Do's and Don'ts`.
- Do not use the old `Design Vision`, `Audience and Jobs`, `Product Shape`, `Decision Log`, `Open Questions`, or `DESIGN.html Sync Notes` structure for `DESIGN.md`.
- Fold settled decisions into the canonical sections. Report remaining unresolved questions in the final response unless the repo already requires an unresolved-question section.
- If Node/npm is available, run `npx @google/design.md lint DESIGN.md` after writing and fix errors or broken references.
- Preserve existing good design decisions. Mark unresolved token gaps instead of filling them with guesses.

## DESIGN.html rules

- `DESIGN.html` is the visual audit artifact: a fixed static mock website visualizer that shows the agreed fonts, colors, layout, hierarchy, buttons, cards, sections, and states working together.
- Copy the `DESIGN-FORMAT.html` mock website literally: same section order, section purposes, labels, placeholder copy, and generic pricing/testimonials/FAQ/articles content every time.
- Never adapt, remove, rename, or remap mock website sections to match the target project, even when the real product would not have pricing, testimonials, FAQ, articles, or those component types.
- Do not add an editing toolbar. The only runtime control should be a top-right round lightbulb switch for light/dark mode.
- Put design choices in a clear token layer that mirrors `DESIGN.md` tokens for fonts, colors, radius, spacing, and component styling.
- Keep the two files synchronized. If one changes, update the other.

## Completion

Report the files changed, the major decisions captured, and any remaining open design questions. Do not claim implementation readiness, pixel-perfect approval, or final visual sign-off unless the user explicitly confirms it.
