"""Read download provenance and compare recorded GitHub folder revisions."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote


def records_for(root, lock):
    if not root.is_dir():
        raise ValueError(f"Downloaded skills directory is missing: {root}")
    if not isinstance(lock.get("skills"), dict):
        raise ValueError("Source lock has no skills mapping")
    personal = root.parent / "personal"
    records = []
    for folder in sorted(root.iterdir()):
        if folder.name.startswith(".") or not folder.is_dir():
            continue
        record = {"name": folder.name, "status": "skipped"}
        entry = lock["skills"].get(folder.name)
        reason = None
        if folder.is_symlink():
            reason = "Linked folder; update destination requires review"
        elif (personal / folder.name).exists():
            reason = "Name overlaps a personal skill"
        elif not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", folder.name):
            reason = "Folder name cannot be passed safely to the updater"
        elif not isinstance(entry, dict):
            reason = "No source recorded in the skills.sh lock"
        elif entry.get("sourceType") != "github":
            reason = "Source is not a tracked GitHub download"
        elif not isinstance(entry.get("source"), str) or not re.fullmatch(r"[\w.-]+/[\w.-]+", entry["source"]):
            reason = "Source repository is missing or unsupported"
        elif not isinstance(entry.get("skillFolderHash"), str) or not re.fullmatch(r"[0-9a-f]{40}", entry["skillFolderHash"]):
            reason = "No upstream folder revision recorded"
        else:
            path = entry.get("skillPath", "")
            if not isinstance(path, str) or (path != "SKILL.md" and not path.endswith("/SKILL.md")) or ".." in Path(path).parts or path.startswith("/"):
                reason = "No valid upstream skill path recorded"
        if reason:
            record["reason"] = reason
        else:
            record.update(status="pending", source=entry["source"],
                          ref=entry.get("ref") or "HEAD", path="" if entry["skillPath"] == "SKILL.md" else entry["skillPath"].removesuffix("/SKILL.md"),
                          installed=entry["skillFolderHash"])
        records.append(record)
    return records


def fetch_tree(source, ref):
    result = subprocess.run(
        ["gh", "api", f"repos/{source}/git/trees/{quote(ref, safe='')}?recursive=1"],
        capture_output=True, text=True, timeout=90,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[-400:] or "GitHub API request failed")
    tree = json.loads(result.stdout)
    if tree.get("truncated"):
        raise RuntimeError("GitHub returned an incomplete repository tree")
    if not isinstance(tree.get("tree"), list):
        raise RuntimeError("GitHub returned no repository tree")
    folders = {entry["path"]: entry["sha"] for entry in tree["tree"] if entry["type"] == "tree"}
    folders[""] = tree["sha"]
    return folders


def compare(records, fetch=fetch_tree):
    groups = sorted({(r["source"], r["ref"]) for r in records if r["status"] == "pending"})

    def load(group):
        try:
            return group, fetch(*group), None
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            return group, None, str(error)

    with ThreadPoolExecutor(max_workers=4) as executor:
        trees = {key: (tree, error) for key, tree, error in executor.map(load, groups)}
    for record in records:
        if record["status"] != "pending":
            continue
        tree, error = trees[(record["source"], record["ref"])]
        if error:
            record.update(status="error", reason=error)
        elif record["path"] not in tree:
            candidates = [path for path in tree if Path(path).name == record["name"]]
            if len(candidates) == 1:
                record.update(status="moved", replacementPath=candidates[0],
                              reason=f"Upstream folder moved to {candidates[0]}; official updater will resolve it")
            else:
                record.update(status="missing", reason="Upstream folder missing; no unique matching folder")
        else:
            record["upstream"] = tree[record["path"]]
            record["status"] = "current" if record["installed"] == record["upstream"] else "update"
    return records


def check(root, lock_path):
    lock = json.loads(lock_path.read_text())
    return compare(records_for(root, lock))


def summary(records):
    return {status: sum(r["status"] == status for r in records)
            for status in ["current", "update", "moved", "missing", "skipped", "error"]}


def print_report(records):
    counts = summary(records)
    print(f"{len(records)} downloaded folders: {counts['current']} current, "
          f"{counts['update']} updates, {counts['moved']} moved, {counts['missing']} missing upstream, "
          f"{counts['skipped']} untracked/skipped, {counts['error']} errors")
    for record in records:
        if record["status"] != "current":
            detail = record.get("reason", record.get("source", ""))
            print(f"  {record['status']:7} {record['name']}: {detail}")
