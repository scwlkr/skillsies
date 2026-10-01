"""Build a local, review-first disk report from scanner and capacity evidence."""
import json
import re
from pathlib import Path

try:
    from .render import html_report
except ImportError:
    from render import html_report


LIMITATIONS = [
    "Candidate sizes are metadata-based upper bounds, not confirmed reclaimable space. Review each item before acting; this scan deletes nothing.",
    "APFS clones can share extents, and snapshots can retain deleted data. Summed allocated bytes do not prove physical space recoverable.",
    "Sparse or compressed files can have logical sizes much larger than allocated sizes; rankings use allocated bytes.",
    "Hard links are counted once within the scan. Other links outside the scanned scope may keep the data alive after removal.",
    "Large files and directory totals overlap. Their tables are never added together; directory totals are inclusive.",
    "Skipped paths, cloud placeholders, external mounts, exclusions, and permission errors limit coverage. The scan is not a complete inventory of every byte on the disk.",
]
PERMISSION_GUIDANCE = (
    "For permission gaps, open System Settings > Privacy & Security > Full Disk Access; "
    "enable the terminal or Codex app doing the scan, then quit and relaunch that app and rerun the scan. "
    "Grant access only to the app you chose to run this local audit."
)


def human_size(number):
    value = float(number)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(value) < 1024 or unit == "PiB":
            return f"{value:,.1f} {unit}" if unit != "B" else f"{value:,.0f} B"
        value /= 1024


def md_escape(value):
    value = str(value).replace("\n", "\\n").replace("\r", "\\r")
    return re.sub(r"([\\`*_{}\[\]()<>|#!])", r"\\\1", value)


def _priority(item):
    category = str(item.get("category", "review")).lower()
    risk = str(item.get("risk", "review")).lower()
    if category == "cloud" or "offload" in category:
        return 3
    if any(word in category for word in ("cache", "build", "regenerable")):
        return 0
    if risk == "app-managed" or category in ("models", "developer assets") or any(
            word in category for word in ("app", "managed", "docker", "simulator")):
        return 1
    return 2


def _candidates(scan):
    items = sorted(scan.get("candidates", []),
                   key=lambda item: (_priority(item), -item["allocated_bytes"], str(item["path"])))
    chosen = []
    for item in items:
        path = Path(item["path"])
        if item["allocated_bytes"] < 0:
            raise ValueError("Candidate allocation cannot be negative")
        # Defend against accidental overlap even though the scanner emits disjoint candidates.
        if any(path == Path(other["path"]) or path in Path(other["path"]).parents
               or Path(other["path"]) in path.parents for other in chosen):
            continue
        chosen.append(item)
    return chosen


def _action(item):
    if item.get("action"):
        return str(item["action"])
    category = str(item.get("category", "review")).lower()
    if "cache" in category or "build" in category or "regenerable" in category:
        return "Confirm this is disposable generated data; quit the owning app and use its cleanup controls where available. Expect regeneration time."
    if _priority(item) == 1:
        return "Open the owning app's storage manager; remove only data you recognize and no longer need."
    return "Review the contents and ownership. Back up or move useful data to verified external storage before considering removal."


def _table(items, candidates=False):
    lines = ["| Allocated | Logical | Path |" + (" Category / next step |" if candidates else ""),
             "| ---: | ---: | --- |" + (" --- |" if candidates else "")]
    for item in items:
        row = f"| {human_size(item['allocated_bytes'])} | {human_size(item.get('logical_bytes', 0))} | {md_escape(item['path'])} |"
        if candidates:
            row += f" {md_escape(item.get('category', 'review'))}: {md_escape(_action(item))} Risk: {md_escape(item.get('risk', 'requires review'))}. |"
        lines.append(row)
    if not items:
        lines.append("| — | — | No items found in this scan. |" + (" — |" if candidates else ""))
    return "\n".join(lines)


def generate(scan: dict, capacity: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates = _candidates(scan)
    estimate = sum(item["allocated_bytes"] for item in candidates)
    needed = capacity["reclaim_needed_bytes"]
    after = max(0, capacity["used_bytes"] - estimate)
    residual = max(0, needed - estimate)
    status = "already_met" if not needed else (
        "candidate_estimate_short" if residual else "enough_candidates_to_review")
    summary = {
        "capacity": capacity,
        "candidate_upper_bound_bytes": estimate,
        "optimistic_used_bytes": after,
        "optimistic_used_percent": after * 100 / capacity["total_bytes"],
        "optimistic_residual_gap_bytes": residual,
        "target_plausibility": status,
        "candidates": [dict(item, action=_action(item)) for item in candidates],
        "coverage": {key: scan.get(key, [] if key in ("roots", "excluded", "errors") else 0)
                     for key in ("roots", "excluded", "errors", "elapsed_seconds", "allocated_bytes",
                                 "logical_bytes", "files", "directories", "error_count",
                                 "hardlink_duplicates", "symlinks_skipped", "dataless_skipped",
                                 "external_mounts_skipped")},
        "limitations": LIMITATIONS,
    }
    summary["coverage"]["scope"] = scan.get("scope", "Selected roots only")
    summary["coverage"]["permission_guidance"] = PERMISSION_GUIDANCE
    if status == "already_met":
        assessment = "The measured disk is already at or below the target. No removal is needed to meet it."
    elif residual:
        assessment = f"Even if every candidate freed its full estimate, {human_size(residual)} would still need to be reclaimed to reach the target. Broaden the scan or review larger personal data for offloading."
    else:
        assessment = "The candidate estimates could cover the target gap, but this is an optimistic scenario. Actual recovery must be measured after any approved cleanup."
    summary["assessment"] = assessment
    summary["next_step"] = (
        "No cleanup is needed for this goal. Keep existing data; investigate coverage gaps only if you need fuller storage attribution. Remeasure after future storage changes."
        if status == "already_met" else
        "Review candidate contents, confirm backups for personal data, and choose specific cleanup actions. Rescan after approved cleanup to verify the measured percentage."
    )
    coverage = summary["coverage"]
    sections = [
        "# MacBook disk review", "", f"Measured: {md_escape(capacity['measured_at'])}", "",
        f"**{capacity['used_percent']:.1f}% used · target {capacity['target_percent']:g}%**",
        f"{human_size(capacity['used_bytes'])} used / {human_size(capacity['total_bytes'])} total; {human_size(capacity['free_bytes'])} available.",
        f"**Space needed to reach target: {human_size(needed)}.**", "",
        assessment, "",
        f"Review candidates: **up to {human_size(estimate)}**. Optimistic usage after all candidates: **{summary['optimistic_used_percent']:.1f}%**. Residual target gap: **{human_size(residual)}**.",
        "These estimates are not a deletion plan or a promise of recovered space.", "",
        f"Capacity source: {md_escape(capacity['source'])}",
        *[f"- {md_escape(warning)}" for warning in capacity.get("warnings", [])], "",
        "## Ranked review candidates", "", _table(summary["candidates"], True), "",
        "## Largest directories (inclusive)", "", _table(scan.get("top_directories", [])[:20]), "",
        "## Largest files", "", _table(scan.get("top_files", [])[:20]), "",
        "## Scan coverage", "",
        f"**Scope: {md_escape(coverage['scope'])}.** Capacity describes the target disk; inventory covers only the selected roots below.",
        f"Elapsed {coverage['elapsed_seconds']:.2f}s; {coverage['files']:,} files; {coverage['directories']:,} directories; {human_size(coverage['allocated_bytes'])} allocated observed.",
        f"Skipped: {coverage['hardlink_duplicates']} duplicate hard links, {coverage['symlinks_skipped']} symlinks, {coverage['dataless_skipped']} cloud placeholders, {coverage['external_mounts_skipped']} external mounts.",
        f"Errors: {coverage['error_count']} (up to 100 details retained).", "",
        *(["**Coverage incomplete: scan errors leave some paths unmeasured.**", PERMISSION_GUIDANCE, ""] if coverage["error_count"] else []),
        "Selected scan roots:", *[f"- {md_escape(path)}" for path in coverage["roots"]], "",
        "Exclusions:", *[f"- {md_escape(path)}" for path in coverage["excluded"]], "",
        "Errors:", *[f"- {md_escape(error)}" for error in coverage["errors"]], "",
        "## Limits and next step", "", *[f"- {line}" for line in LIMITATIONS], "",
        summary["next_step"] + " Paths stay in these local report files.",
    ]
    paths = {name: str(output_dir / filename) for name, filename in
             (("markdown", "report.md"), ("html", "report.html"), ("summary", "summary.json"))}
    Path(paths["markdown"]).write_text("\n".join(sections) + "\n", encoding="utf-8")
    Path(paths["summary"]).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    Path(paths["html"]).write_text(html_report(summary, scan), encoding="utf-8")
    return paths
