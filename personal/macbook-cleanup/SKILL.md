---
name: macbook-cleanup
description: Scan MacBook storage quickly with a cached parallel Rust scanner, then present a compact local shadcn dashboard with storage charts and selectable cleanup items toward 50 percent usage or less. Use when the user wants to investigate Mac disk usage or System Data, reclaim space, review caches/models/build artifacts, or select items for one final cleanup approval. Includes Terminal access setup and an exact, verified batch deletion workflow.
compatibility: macOS; Python 3.11 or newer; Rust/Cargo and Node.js/npm for first builds. Cached binaries and dashboard assets are reused. Optional administrator authentication applies only to the metadata scanner; macOS Full Disk Access requires Settings approval.
---

# MacBook cleanup

## Scan and show the dashboard

Resolve this skill directory from its loaded path. Use its bundled tooling instead of writing another scanner or launching recursive du processes. The Rust scanner reads file metadata in parallel; it never reads contents or deletes files. First builds download locked dependencies; later unchanged runs reuse cached builds.

```sh
python3 <skill-directory>/scripts/scan.py --output <workspace>/outputs/macbook-cleanup-<timestamp>
python3 <skill-directory>/scripts/review_server.py --report-dir <same-output-directory> --wait
```

Run the review server as a background/PTY session so the user can select items while the model remains responsive. Read its `review-ready` event and open that exact loopback URL with `open_in_codex` or a browser. The private token is in the URL fragment. Never publish it or the report. Keep the session alive through selection and final confirmation; do not stop the server when sending a short chat update.

The dashboard uses actual shadcn components and Recharts. It shows measured physical used/free space, observed category allocation, the 50 percent gap, and an optimistic projection for selected items. Search, category filters, pagination and expandable details keep the initial view concise. `report.html` is a self-contained saved dashboard with exploratory selections; it cannot delete files. `report.md`, `summary.json` and `scan.json` retain detailed evidence. If the dashboard build is unavailable, preserve the basic HTML/Markdown report and state the missing dependency.

Default audit: `/System/Volumes/Data`, eight workers, 100 MiB minimum candidate, 50 percent physical APFS container target. Use a new private output folder. Repeat `--root` for exact scoped directories; use `--exclude`, `--target-percent`, `--threads` or `--timeout` as needed. Scoped inventory is not whole-disk coverage. A timeout is a failed audit: preserve evidence, narrow the scope and retry.

## Access setup and Terminal handoff

When access gaps matter, prepare and open one Terminal launcher:

```sh
python3 <skill-directory>/scripts/access.py --output <workspace>/outputs/macbook-cleanup-session-<timestamp> --launch --admin
```

This opens Terminal, shows progress, performs one optional sudo authentication for read-only Unix permission access, and opens the dashboard alongside it. Omit `--admin` when elevated scanning is unnecessary. Builds run as the user before authentication. Fullscreen shortcut: **Control-Command-F**. Terminal displays progress and final results; browser components cannot render inside a native terminal.

Full Disk Access cannot be granted by sudo or blanket approval. The launcher can open **System Settings → Privacy & Security → Full Disk Access**. The user enables Terminal (or their chosen scanning app), quits and relaunches it, then reruns the same launcher. Explain these exact steps only when needed, without repeated approval questions. Consult [access workflow](references/access.md). Respect system protections; surface remaining inaccessible paths instead of promising unrestricted access.

## Select, review, approve once

An audit authorizes scanning and reporting. It does not approve deletion. The dashboard lets the user select specific items and then click **Review selected**. The final dialog lists exact paths and freshly measured allocation. **Permanently delete N items** is the single final approval for that frozen batch. No deletion happens on selection or initial review. A preview server (`--preview`) saves the approved selection and never deletes.

The local API uses server-derived IDs, immutable plan identity/digest, expiry and one-use consent. It checks owner, file identity, manifest, entire subtree, protected descendants, mounts, hard links, symbolic links and active processes before acting. Whole-batch preflight precedes staging; staged items are rechecked before removal. Durable approval and staging records support recovery from interruption. Review blocked items, deselect them and create a new plan; never bypass failed checks.

Only narrowly recognized, measured operations are selectable: manifest-backed project `target`/`node_modules`, individual Xcode DerivedData projects, allowlisted app cache folders and replaceable installer/archive files in Downloads. Close related apps and builds first. Large models, applications, cloud folders, simulator/runtime/VM storage and broad library roots require the owning tool and specific follow-up. Read [storage rules](references/storage-rules.md). Preserve source, uncommitted work, credentials, backups and release evidence, including protected files inside otherwise generated trees.

If the user approves exact paths in chat, refresh and execute only those operations under the same safety checks; do not ask for the same authorization again or infer approval for new paths. Never replace this workflow with bulk rm, sudo cleanup, automated snapshot pruning or broad Trash emptying.

## Report outcomes briefly

Keep chat to roughly 5–8 lines: measured disk usage, target gap, leading actionable items, coverage limits and the dashboard link. When the target is already met, say no cleanup is needed. Put the inventory, error details and lengthy caveats behind dashboard details.

Physical capacity and observed file allocation are separate metrics. APFS shared extents, snapshots, skipped paths and outside hard links can prevent estimated space from being reclaimed. Never add overlapping directory/file tables or present logical file sizes as recovery. State the remaining gap even if every candidate were removed; do not invent a path to 50 percent.

After final approval, read `cleanup-results.json` and `approved-plan.json` or the terminal's `cleanup-result` event. Report actual measured capacity, recovery and remaining gap, plus any skipped/failed/partially removed items or recovery paths. Rerun the audit after substantial cleanup to refresh the inventory. Claim the goal met only when the fresh physical usage is at or below the target.

## Verify changes

Run `cargo clippy --locked --manifest-path <skill-directory>/scanner/Cargo.toml -- -D warnings`, `python3 -m unittest discover -s <skill-directory>/tests -v`, and `npm test` plus `npm run build` inside `dashboard/`. Scanner fixtures require a current release binary via `MACBOOK_SCAN_BINARY` or the normal cache. Test approval/deletion only on temporary fixtures. Verify the browser selection → exact review → preview/fixture confirmation flow, including mobile layout. Evals are in `evals/evals.json`.
