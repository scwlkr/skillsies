# DESIGN.md Format

Use the Google Labs Code `design.md` alpha format unless the target repo already has a stricter compatible convention: https://github.com/google-labs-code/design.md

`DESIGN.md` is a self-contained design system for humans and agents. It has two layers:

1. YAML front matter at the top with machine-readable design tokens.
2. Markdown `##` sections with human-readable design rationale.

The tokens are normative. Prose explains why the tokens exist and how to apply them.

## Required File Shape

Start every new `DESIGN.md` with YAML front matter delimited by exact `---` lines:

```yaml
---
version: alpha
name: Example Design System
description: Replace this with the project-specific design-system scope.
colors:
  primary: "#000000"
  on-primary: "#ffffff"
  secondary: "#666666"
  tertiary: "#b8422e"
  on-tertiary: "#ffffff"
  neutral: "#f7f5f2"
  surface: "#ffffff"
  on-surface: "#111111"
  error: "#ba1a1a"
  on-error: "#ffffff"
typography:
  headline-display:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: 600
    lineHeight: 20px
    letterSpacing: 0.01em
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 32px
  xl: 64px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-md}"
    rounded: "{rounded.md}"
    padding: 12px
    height: 48px
  button-primary-hover:
    backgroundColor: "{colors.secondary}"
  page-shell:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.on-surface}"
  card-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "{spacing.md}"
  badge-accent:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    typography: "{typography.label-md}"
    rounded: "{rounded.full}"
    padding: "{spacing.xs}"
  badge-error:
    backgroundColor: "{colors.error}"
    textColor: "{colors.on-error}"
    typography: "{typography.label-md}"
    rounded: "{rounded.full}"
    padding: "{spacing.xs}"
---
```

Replace the sample name, description, fonts, colors, scale values, and component set before writing the final file.

## Token Rules

- Colors must be sRGB hex strings like `"#1A1C1E"` in `colors`.
- Use `primary`, `secondary`, `tertiary`, `neutral`, `surface`, `on-surface`, and `error` when they fit before inventing project-specific color names.
- Typography tokens are objects with `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `fontFeature`, and `fontVariation` as needed.
- Rounded and spacing tokens should use `px`, `rem`, or `em`; unitless spacing is acceptable only for deliberate numeric scales such as column counts.
- Component token properties should be limited to `backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, and `width`.
- Component states are separate related entries: `button-primary`, `button-primary-hover`, `button-primary-active`.
- Token references use `{path.to.token}` and must resolve, for example `{colors.primary}` or `{typography.body-md}`.
- Define component tokens for the real interface atoms the project uses: buttons, inputs, cards, lists, chips, nav, badges, tooltips, checkboxes, radios, and domain-specific atoms when relevant.

## Section Order

After front matter, write rationale in this `##` order. Omit only sections that are genuinely irrelevant.

1. `## Overview` or `## Brand & Style`
2. `## Colors`
3. `## Typography`
4. `## Layout` or `## Layout & Spacing`
5. `## Elevation & Depth` or `## Elevation`
6. `## Shapes`
7. `## Components`
8. `## Do's and Don'ts`

Do not add duplicate `##` headings. Preserve unknown project-required sections only when the repo already has them, and keep the canonical sections in order.

## Prose Rules

- `Overview` names the product feeling, audience, density, emotional response, and what the UI must not become.
- `Colors` maps color names to exact token values and explains semantic use.
- `Typography` explains type roles, hierarchy, weights, and readability behavior.
- `Layout` defines grid/fluid behavior, spacing rhythm, max widths, grouping, and responsive rules.
- `Elevation & Depth` explains hierarchy through shadows, layers, borders, blur, contrast, or tonal stacking.
- `Shapes` defines radius discipline, icon stroke style, image/container shapes, and when exceptions are allowed.
- `Components` describes how tokenized component atoms behave, including hover/focus/active/disabled states.
- `Do's and Don'ts` captures practical guardrails that prevent predictable design drift.

## Validation

When Node/npm is available, validate the finished file:

```bash
npx @google/design.md lint DESIGN.md
```

Fix errors and broken references. Treat warnings about missing primary color, missing typography, low contrast, out-of-order sections, orphaned tokens, and unknown component properties as design quality feedback.

## DESIGN.html Sync

`DESIGN.html` is a separate visual audit artifact for this skill. It must reflect the `DESIGN.md` tokens and rationale, but it must not introduce a second design source of truth or require non-`DESIGN.md` sections.
