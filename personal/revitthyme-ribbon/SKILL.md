---
name: revitthyme-ribbon
description: Design and implement RevitThyme ribbon organization, native controls, command labels and tooltips, and SVG icon families. Use when adding or reviewing RevitThyme ribbon commands, choosing button sizes or menus, or authoring its ribbon icons.
---

# RevitThyme ribbon

Make tasks easy to find, predict, and run through native Revit controls. SVG is the editable source of truth for icons; raster files are reproducible delivery assets.

## Start from the actual command

In a RevitThyme checkout, read `docs/RIBBON.md` before changing ribbon organization or icons. That maintained project standard owns the current command map, palette, asset paths, and export route. Follow its current decisions rather than copying an older layout from this skill. If it is absent, use the principles below and record project-specific decisions with the implementation.

Inspect the ribbon registration and the command behavior. Identify what clicking opens or changes, supported document/view contexts, and existing toolkit keys (`PushButtonData.Name`). Keep those keys stable for toolkit automation. Revit's generated native `CustomCtrl` paths also contain panel names; panel moves can change shortcut and Quick Access Toolbar paths despite stable toolkit keys. Assess existing mappings and document any reassignment needed rather than promising they survive. Work within the authorized commands; empty space is not a reason to invent features.

## Choose organization and controls

- Group panels around user tasks, using familiar Revit terms. Keep a command in one predictable home. Put everyday work before optional assistance and maintenance. A distinct task can justify a one-command panel; avoid fragmentation that makes discovery harder.
- Use a large push button for a primary task or important entry point. Use labeled small buttons in related stacks of two or three when compact visible access is useful. Decide from importance, frequency, and discovery together.
- Use a pulldown for two or more meaningfully related commands without an obvious default. Use a split button when the family has a useful default plus alternatives. Keep that default stable unless remembering the last choice intentionally serves the workflow. A lone command stays direct.
- Put rare settings or maintenance in a slide-out only when reduced discoverability is acceptable. Keep primary work visible and document the secondary location. Add separators for real subgroups.
- Use toggles for actual mutually exclusive modes and inputs for genuinely compact settings. Put complex or interdependent settings in the command's window.
- Let supported `Autodesk.Revit.UI` APIs own layout, sizing, theming, and interactions. Use native APIs rather than internal ribbon visual trees or unsupported UI patches. Confirm target-version API details in the installed SDK or official Autodesk documentation when needed.

## Explain the action

Use a short, truthful label meaningful without the icon. For example, opening an agent pane is a different action from connecting a runtime inside it. Keep intentional line breaks between words.

Every actionable command needs a one-sentence short tooltip and an extended tooltip. State the immediate purpose, supported target or context, expected next step/result, and material limits. Describe preview, edits, and Undo only as implemented. Put explanations on actionable child buttons where a group or split control cannot display its own tooltip.

Give F1 a real maintained command topic and verify the destination. Keep document-dependent commands visible but unavailable when a fast, read-only context check rules them out. The operation still validates full preconditions and explains detailed refusals. Utilities that work without a model should remain accessible.

## Draw and export icons

- Author separate 16 × 16 and 32 × 32 SVG optical masters. Start with 1-unit and 2-unit strokes respectively, crisp pixel alignment, consistent caps/joins, and breathing room. Simplify the small drawing instead of merely shrinking detail.
- Use a recognizable task/object silhouette, a restrained action accent, and consistent apparent weight. Related variants share a base metaphor. Labels and shape carry meaning alongside color.
- Keep transparent backgrounds and editable paths/shapes. Use a renderer-supported SVG subset without embedded rasters, external assets, fonts, effects, or decorative shadows. Avoid tiny text, emoji, and badges on every command.
- Design light and dark variants together. RevitThyme's default neutral/blue pairs are `#52606D`/`#006EAF` for light and `#D6DEE8`/`#70C5FF` for dark; use the repository's maintained palette if it changes. Let native controls render disabled/hover states.
- Regenerate PNGs through the repository export script. Each optical master needs 1× at 96 DPI and 2× at 192 DPI, preserving alpha and the same logical size. Set both small `Image` and `LargeImage` resources, including for Quick Access Toolbar use. Handle theme changes through supported Revit APIs.
- Inspect each icon at actual size and in a contact sheet on both backgrounds. Check strokes, gaps, clipping, contrast, and quick distinction between neighboring icons. Update SVGs rather than editing generated pixels.

## Deliver observable evidence

Keep the project command map and relevant help paths aligned with the implementation. Check source metadata, vector/export dimensions, DPI, transparency, deterministic regeneration, and packaged resource coverage; run required repository checks.

Qualify rendered controls and command launches in a separately pinned disposable Revit process/fixture when available. Inspect panel order, small/large imagery, tooltip expansion, F1, slide-outs, availability, theme changes, and available display scales. Preserve working models and installations. Report source/icon checks, build/package checks, and actual Revit observations separately; identify any missing host or scale evidence rather than treating a preview or build as a native pass.
