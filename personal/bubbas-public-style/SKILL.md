---
name: bubbas-public-style
description: Applies the polished Bubba's Fireworks public-page visual system from the `/250` countdown page. Use when building or redesigning public Bubba's links, Public Surfaces, campaign landing pages, QR destinations, signup pages, offer pages, or when the user says to apply `bubbas-public-style`.
---

# Bubba's Public Style

## Quick Start

When applying this style, make the public page feel like a proud Bubba's Fireworks brand surface: bold, clean, patriotic, mobile-first, and shareable. Use the current `bubbas.info/250` page as the reference, not Media HQ or dashboard UI.

Core tokens:

```css
--bubbas-blue: #007ce8;
--bubbas-red: #cc0000;
--bubbas-navy: #03256c;
--bubbas-night: #001845;
--bubbas-ink: #131b23;
--bubbas-muted: #526075;
--bubbas-line: #d9e8fb;
--bubbas-white: #ffffff;
--bubbas-gold: #fed766;
```

## Visual Contract

- Build public pages as full-width brand bands, not dashboard cards.
- Use flat Bubba blue for major public hero and CTA bands; avoid blue gradients unless the user explicitly requests them.
- Use red as a decisive accent: top civic rule, primary CTAs, section dividers, underlines, and key emphasis.
- Use white content sections with strong navy display headings and restrained light-blue rules.
- Use gold only as a small premium accent, such as one script phrase or a small shimmer. Do not make gold the page theme.
- Keep the page seamless: sections should flow as bands with consistent rhythm, not feel like stacked disconnected panels.
- Avoid cream/parchment backgrounds, grid paper patterns, giant faded background marks, bokeh blobs, generic Bootstrap cards, and internal Media HQ styling.

## Typography

- Display: use Bubba's Eurostile extended black italic when available; fallback to `Arial Black`.
- Body and utility: use Montserrat when available; fallback to Arial or Helvetica.
- Headlines should be bold, italic, uppercase, and tightly composed without negative letter spacing.
- Use small uppercase kicker labels for metadata and section labels.
- A script/calligraphy font is allowed in one subtle place only, usually for an anniversary phrase like `America's 250th`.
- Keep mobile text readable and avoid headline line counts that feel clunky.

## Layout Pattern

Use this basic page spine for public landing pages:

1. A thin red/white/blue civic rule at the very top.
2. A flat Bubba-blue header with logo on the left and compact public URL/context on the right.
3. A first-viewport hero where the main action or offer is immediately visible.
4. A short CTA stack or row using red primary, white secondary, and blue/white outline buttons.
5. White sections for explanation, sharing, signup, or offer details.
6. Optional flat blue closing section for urgency or next action.
7. Dark ink footer with Bubba's logo, social links, public URL, and any required disclaimer.

## Components

- Buttons: 3px radius, bold uppercase text, lucide icons when useful, min-height around 3rem, red primary, white secondary, outline tertiary.
- Badges/labels: small uppercase, high weight, red or white, with simple underline or rule accents.
- Stats: use clean rows or simple grid cells with navy value text and muted supporting copy; avoid decorative cards.
- Dividers: prefer thick red section rules or thin navy/light-blue rules; no ornate frames.
- Motion: limited and purposeful. Respect `prefers-reduced-motion`. Use hover lift/glow lightly.
- Public URLs: visible links, canonical URLs, share URLs, and Open Graph URLs should use `bubbas.info` or `bubbasfireworks.com`, never internal `command-center` wording.

## Copy Tone

- Keep copy loud, simple, friendly, local, and patriotic.
- Use concrete phrases: `Find your closest stand`, `Save the date`, `Share the countdown`, `Celebrate with Bubba's`.
- Avoid political messaging, government impersonation, long explanations, and shameless over-promotion.

## Validation

Before finishing public-page work:

- Verify mobile first at about 390px and narrow mobile at about 320px.
- Verify desktop around 1440px.
- Check there is no horizontal overflow.
- Check public links resolve on `bubbas.info` without exposing internal project names.
- Run the repo's normal validation for the touched surface.
- Capture screenshots for meaningful visual changes.
