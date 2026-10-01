# Local storage review UI

React + TypeScript + Tailwind, using actual shadcn registry components and Recharts.
`npm ci && npm run build` creates local assets. `npm test` verifies selection projections.
The scanner wrapper caches this build and exports a standalone HTML dashboard.
`../scripts/review_server.py --report-dir PATH` enables local batch review and explicit consent.

Optional browser checks use an existing Playwright installation and Chrome; they do
not install packages or browsers. Build first, then run:

```sh
MACBOOK_PLAYWRIGHT_PATH=/absolute/path/to/playwright/index.mjs npm test
```

This creates a synthetic home and a preview-only server, tests keyboard selection,
search, filtering, exact batch review, final preview, and mobile layout, and verifies
that its fixture files survive. Without the environment variable these checks skip.
`MACBOOK_SAVED_REPORT` optionally checks a saved HTML file. Optional
`MACBOOK_LIVE_REPORT` plus `MACBOOK_SCREENSHOT` capture an existing session while
blocking every API mutation. `MACBOOK_BROWSER_PATH` can select an existing browser.
The final local workflow was also exercised through Codex computer use, including
the preview result in the browser and terminal; no real data was deleted.

Components in `src/components/ui/` were generated from the official shadcn registry
with `npx shadcn@latest add …` on 2026-10-01. These vendored components retain their
upstream structure; `chart.tsx` exceeds the authored-file size guideline.
Sources: https://ui.shadcn.com/docs/installation/vite and
https://github.com/shadcn-ui/ui (MIT). Locked dependencies carry their own licenses.
