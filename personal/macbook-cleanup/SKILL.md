---
name: macbook-cleanup
description: Fast, read-only MacBook disk audits using a cached parallel Rust scanner and local reports with a measured plan toward 50 percent disk usage or less. Use whenever the user wants to find what is taking up Mac storage, investigate System Data, reclaim disk space, review caches, models, build artifacts or developer runtimes, or get their MacBook disk half full. Also use for an authorized cleanup follow-up, with fresh verification of each approved item.
compatibility: macOS, Python 3.9 or newer, Rust/Cargo for the first release build; subsequent unchanged runs use the cached executable. No sudo required.
---

# MacBook cleanup

## Run the audit

Resolve this skill's directory from the loaded path. Run its bundled tooling instead of writing a new scanner or launching several recursive `du` processes. Metadata-only parallel traversal avoids reading file contents and saves repeat work. The first build downloads pinned Rust dependencies; subsequent runs use the cached release binary.

```sh
python3 <skill-directory>/scripts/scan.py --output <workspace>/outputs/macbook-cleanup-<timestamp>
```

Default: scan `/System/Volumes/Data`, eight workers, 100 MiB minimum candidate, 50 percent physical APFS container usage target. Keep reports private in a new output folder; never commit real filenames or upload reports without the user's request. A full audit can take longer on millions of files; report the measured duration rather than promising a speedup.

For a focused first pass or follow-up, repeat `--root` with exact directories. Use `--exclude` for user-specified exclusions, `--target-percent` for another target, and `--threads` to tune load. A scoped scan is not whole-disk coverage. Use `--help` for the full CLI. `--timeout` fails the audit if exceeded; retain the baseline, narrow the roots and retry, without presenting a timed-out scan as complete.

## Read and explain the results

Read `summary.json` and `report.md`; show `report.html` with `open_in_codex` when available. Link the local report and raw `scan.json` evidence.

- Lead with current container usage and the bytes that must be freed to reach 50 percent. Physical free space includes the macOS/shared-volume overhead; the Data volume's `df` percentage is a separate metric.
- Name the largest actionable paths, their allocated sizes, the owning tool, and the specific check needed before removal. Prioritize inactive rebuildable artifacts and caches, then unused models/installers/apps, then verified cloud offload or external storage.
- Treat candidate sizes as an optimistic upper bound, not guaranteed reclaim. State the remaining target gap. If candidates fall short, say so and identify large user-data categories to review or offload; do not invent a safe path to 50 percent.
- Directory and large-file tables overlap. Only the disjoint candidate list may be summed. Logical file sizes are context, not recovery estimates.
- State selected roots, duration, permission/error count, excluded paths, cloud placeholders and mount skips. Permission gaps mean partial coverage. Suggest **System Settings → Privacy & Security → Full Disk Access → the terminal/Codex application performing the scan**, relaunch it, then rerun only when the missing coverage matters. Never invoke sudo to bypass macOS privacy controls.
- APFS clones, snapshots and hard links outside the scan can prevent estimated bytes from being freed. Metadata cannot prove duplicate contents or inactivity. Consult [storage rules](references/storage-rules.md) for category-specific follow-up.

## Authorized cleanup follow-up

An audit request authorizes reading metadata and writing reports. It does not authorize deleting files. Finish the report and concrete itemized proposal before asking for deletion approval. Respect existing explicit approval for exact items; never repeatedly ask for the same authorization.

Before acting, refresh each approved path's size, identity, ownership and current use. Preserve source, uncommitted work, running builds/services, active devices/models, release evidence, backups and credentials. Use the owning application's cleanup/uninstall tool for runtimes, VMs, models and applications. Verify cloud upload completion and offline needs before Finder **Remove Download**; cloud deletion and offload are different actions.

Never bulk-delete `~/Library`, `~/Library/Containers`, app databases, simulator trees, APFS snapshots, swap/sleepimage or system-managed data. A directory name or old modification time is insufficient evidence of disposability. Moving items to Trash does not reclaim their blocks until emptied.

After approved changes, rerun the audit and compare measured physical free space. Claim success only when current usage meets the target; otherwise state the measured recovery and remaining gap. The scanner itself has no delete/prune mode.

## Verification

Run `cargo test --locked --manifest-path <skill-directory>/scanner/Cargo.toml` and `python3 -m unittest discover -s <skill-directory>/tests -v` after implementation changes. Scanner fixture tests require a built binary via `MACBOOK_SCAN_BINARY` or the wrapper's normal cache location. Evals are in `evals/evals.json`; exercise both real audit and difficult target/coverage follow-ups.

