---
name: macbook-cleanup
description: Scan MacBook storage quickly with a cached parallel Rust scanner, then show storage bars, largest items, search, selection and one exact cleanup confirmation inside native Terminal. Use when the user wants to investigate Mac disk usage or System Data, reclaim space toward 50 percent usage or less, or review caches, AI models and build artifacts. Includes Terminal permission setup, verified batch deletion and measured results. A shadcn web dashboard is optional when explicitly requested.
compatibility: macOS; Python 3.11 or newer; Rust/Cargo for the first scanner build. Terminal review uses Python curses without Node or a browser. Optional administrator authentication elevates only the metadata scanner; Full Disk Access requires Settings approval. Node.js/npm are needed only for the optional web dashboard.
---

# MacBook cleanup

## Open Terminal and scan

Resolve this skill directory from its loaded path and use the bundled tooling. Start a new private session and actually open its launcher:

```sh
python3 <skill-directory>/scripts/access.py --output <workspace>/outputs/macbook-cleanup-session-<timestamp> --admin --launch
```

The launcher builds the cached Rust scanner as the user, requests native access inside Terminal, scans, then opens the interactive Terminal review. It does not launch a browser. The scanner reads metadata in parallel without reading file contents or deleting files. First builds download locked dependencies; unchanged later runs reuse the binary. Omit `--admin` for a scoped audit that needs no elevated scan.

Default audit: `/System/Volumes/Data`, eight workers, 100 MiB minimum candidate, 50 percent physical APFS container target. The report goes under the session's `audit/`. A repeated launcher preserves old reports and chooses a fresh audit directory. `session-state.json` records the current stage and Terminal device; use it to distinguish an app launch request from a running session. An accepted `open` command alone does not prove the launcher ran or the user granted access. If computer-use tools prohibit Terminal control, respect that restriction and explain the supported **Control-Command-F** fullscreen shortcut.

For a scoped scan, use `scan.py --output <new-private-report-directory> --no-dashboard`, repeating `--root` for exact roots. Other options include `--exclude`, `--threads`, `--target-percent` and `--timeout`. Review an existing audit with `launch_session.py --output <private-session-directory> --report-dir <audit-directory>`. Scoped inventory is not whole-disk coverage. A timeout is a failed audit: preserve evidence, narrow the scope and retry.

## Request access once

Inside Terminal, the launcher probes protected directories. If blocked, it offers **s** to open Full Disk Access settings, **c** to explicitly continue with partial coverage, or **q** to quit. Full Disk Access requires the user to enable Terminal in **System Settings → Privacy & Security → Full Disk Access**, quit Terminal completely and relaunch it, then rerun the same `.command`. The script cannot grant that toggle or defeat system protections.

With `--admin`, Terminal asks for the Mac password using `sudo -v`; typing is hidden. Only the read-only scanner runs elevated. Review and deletion run as the user. Administrator authentication and Full Disk Access are separate from final deletion approval. Surface remaining access errors instead of promising unrestricted access. Read [access workflow](references/access.md) for exact steps.

## Show the largest items and explain actions

The Terminal review shows physical used/free space, the 50 percent gap, observed category bars and an optimistic selection projection. All candidates are ordered by allocated size, including model storage and other items requiring investigation. Avoid burying those items behind selectable build folders.

Candidates come from measured, recognized storage locations and file types, not an exhaustive AI judgment of everything disposable. The default size cutoff can omit smaller items. Parent/child candidates are collapsed to avoid double counting. Permission gaps, symlinks and unrecognized/custom model locations can limit discovery. Rust recognizes aggregate Ollama, LM Studio and Hugging Face storage; it does not list individual model identities. If models are important, follow up with the owning manager or a targeted scan of the actual custom location. Do not infer that absence from the list means no models exist.

Use arrows to move, **Space** to select, **/** to search, **f** to cycle filters, **d** for full paths and next steps, **a** to select the visible page, and **c** to clear. **--** means the item is visible for investigation but has no exact deletion operation yet. Model aggregates need individual model review through their owning manager; do not delete entire model roots. Preserve local fine-tunes and active workloads. Read [storage rules](references/storage-rules.md).

## Review and confirm the exact batch

An audit authorizes scanning and reporting. Selections draft a list. **Enter/r** prepares a fresh batch and shows validated exact paths separately from skipped items, with allocation and shared-link estimates. The user types **DELETE** and presses Enter once to approve only that frozen validated batch. **Escape** returns to editing. One skipped path does not disable valid items; skipped paths stay intact. With `--preview`, approval saves the plan and never deletes.

Selectable operations include manifest-backed project `target`/`node_modules`, individual Xcode DerivedData projects, allowlisted app caches and replaceable Downloads archives. Close related applications/builds first. Large models, applications, cloud folders, runtimes, VMs and broad library roots require a specific owning-tool action. Do not turn scan approval into blanket cleanup approval.

The backend checks owner, identity, manifest, subtree, protected descendants, mounts, symlinks and active processes. Normal installed dependency fixtures such as a package's `backup`, `evidence`, `.env` or `containers` are allowed only within verified package boundaries; actual user evidence and backups remain protected. Hardlinked generated files can be unlinked while preserving outside links. Recovery counts each inode once and excludes file bytes retained outside the approved batch. Links shared across selected items receive content verification during cleanup preparation; the fast metadata scan still reads no contents.

Whole-batch preflight precedes anchored staging and final rechecks. Durable approval and staging records preserve recovery evidence. If an active-process check is inconclusive, show its reason and retry after access setup or closing related workloads. Resolve failed checks instead of bypassing them. If exact paths are already authorized in chat, execute only those operations under the same checks without asking for duplicate consent. Never use broad `rm`, sudo cleanup, automated snapshot pruning or blanket Trash emptying.

## Report measured outcomes briefly

Keep chat to roughly 5–8 lines: measured disk usage, target gap, leading large items (including models when significant), coverage and Terminal session status. When the target is met, say no cleanup is needed. Save detailed evidence as `scan.json`, `summary.json`, `report.md` and basic `report.html`; don't open the HTML unless requested.

Physical capacity and observed file allocation are separate. Shared APFS extents, snapshots and skipped paths can reduce recovery. Do not add overlapping inventory tables or describe logical file sizes as reclaimed space. State the remaining gap even if every candidate were removed; do not invent a path to 50 percent.

After final approval, read `cleanup-results.json` and `approved-plan.json`. Terminal displays measured capacity, recovery and remaining gap, plus skipped/failed/partially removed items and recovery paths. Rerun the audit after substantial cleanup. Claim the goal met only when fresh measured physical usage is at or below target.

## Optional web dashboard

Only when the user explicitly asks for a browser UI, run `scan.py` without `--no-dashboard`, then `review_server.py --report-dir <audit> --wait` as a background session. Open its exact loopback URL; its fragment contains a private token. Keep the server alive for selection and confirmation. It uses shadcn components and Recharts. Saved `report.html` is exploratory and cannot delete; live confirmation uses the same backend as Terminal. Never publish reports or tokens.

## Verify changes

Run the Python suite (`python3 -m unittest discover -s <skill-directory>/tests -v`) and skill validation. Scanner changes also require locked Cargo clippy and scanner fixtures. Web changes require `npm test` and `npm run build` in `dashboard/`. Test consent and deletion only on temporary fixtures, including cancellation, mixed blocked/valid batches, hardlinks and protected user evidence. Evals are in `evals/evals.json`.
