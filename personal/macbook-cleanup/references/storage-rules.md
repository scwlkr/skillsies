# Storage accounting and follow-up

The baseline is APFS physical container capacity minus container free bytes. A Data-volume-only `df` percentage can exclude shared system/VM/preboot overhead. The report uses `max(0, used_bytes - floor(total_bytes * target_percent / 100))` for the target gap. If APFS metrics are unavailable, label the `df` fallback as volume-only and retain the warning.

Rust uses `lstat` metadata and 512-byte allocated blocks, not apparent file length. Sparse virtual disks and cloud placeholders may have very large logical sizes. Dataless File Provider files/directories are skipped, symlinks are not followed, and mount points on a different device are not traversed. Hard-linked files are counted once per device/inode across all roots. APFS clone sharing and snapshot retention cannot be inferred from these counters; actual recovery must be measured after cleanup. This scan does not hash or read file contents, so it cannot establish byte-identical duplicates.

## Candidate checks

| Category | Inspect first | How to reclaim after approval |
| --- | --- | --- |
| Rust `target`, Node `node_modules`, Xcode DerivedData | Confirm manifests, dependency availability and inactive builds; preserve patched dependencies and unique outputs | Scope to the exact inactive project's generated files |
| App/package caches | Inspect largest children; check for offline media and current installs | Prefer the owning app or package manager's cache controls |
| Ollama / LM Studio / Hugging Face models | List model identities and active workloads; preserve unreproducible local fine-tunes | Use the model manager to remove selected unused models |
| Simulator runtimes/devices, Android SDK/AVDs, Tart, Docker, Rust toolchains | Inspect with `xcrun simctl list`, Android tools, `tart list`, `docker system df`, `rustup toolchain list` as relevant; do not start stopped services just to inspect | Remove selected obsolete assets through their owning tools; Docker volume deletion can destroy databases |
| Application bundles | Confirm unused; distinguish stable and beta installations | Use the app's native uninstaller, especially Adobe Creative Cloud |
| Downloads/installers | Confirm installed and reproducible; preserve offline installers and release evidence | Remove the exact selected archive |
| CloudStorage / Mobile Documents | Verify synchronization, cloud copy and offline/pinned needs using provider/Finder state | Finder Remove Download or provider equivalent; remeasure physical free space |
| Trash | Review exact items and recovery needs | Empty only approved items; Trash on the same volume still consumes space |
| Source / worktrees / evidence / Photos / mail | Check Git state, chat ownership, backup and uniqueness | Review individually; archive completed Codex worktrees with the app's archive_worktree tool when appropriate |
| System Data | Explain permission gaps, shared APFS volumes and snapshot retention | Investigate with `diskutil apfs list`, `tmutil listlocalsnapshots /` and native Storage UI; do not manually remove VM/swap or snapshots |

Do not sum a parent directory, its child directory and files below it. Candidate selection retains the outer classified path and suppresses descendants; that prevents arithmetic double counting but does not approve removing the entire parent. The interactive inventory orders all items by allocated size, including nonselectable model roots. Open details for the reason and next step; use the selectable filter only when specifically choosing generated artifacts. Drill into a large cache or app-managed tree with a targeted rerun before proposing exact items.

## Sources

- [Apple stat API](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/stat.2.html): allocated blocks and link identity.
- [Apple filesystem flags](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/stat.h): `SF_DATALESS`.
- [jwalk directory traversal](https://docs.rs/jwalk/latest/jwalk/struct.WalkDirGeneric.html): parallel traversal and skipping directory children.

Performance depends on file counts, metadata latency, privacy permissions and disk load. Separate first-build time, Rust traversal time and end-to-end report time in any comparison; never label a warm-cache comparison as a universal speed guarantee.

Cleanup preparation is separate from the fast scan: it may read selected archive
contents and generated files hardlinked across selected items to verify identity
through staging. Unlinking a dependency hardlink does not delete its external
package-store copy; file bytes retained outside the selected batch are excluded
from the recovery estimate. Files inside verified installed packages are treated
as generated dependencies, including ordinary fixture names. Preserve custom
patches and unique outputs before approving dependency removal.
