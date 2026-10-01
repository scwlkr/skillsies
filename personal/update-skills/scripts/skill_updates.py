#!/usr/bin/env python3
"""Check and update tracked skills in others/ without model inference."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from inventory import check, print_report, summary


def digest_tree(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.relative_to(root).parts or path.name == ".DS_Store":
            continue
        if path.is_file() or path.is_symlink():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(str(path.readlink()).encode() if path.is_symlink() else path.read_bytes())
    return digest.hexdigest()


def update(root, lock_path, records, run=subprocess.run, verify=check):
    names = [r["name"] for r in records if r["status"] in {"update", "moved"}]
    if any(r["status"] == "error" for r in records):
        raise RuntimeError("Upstream checks failed; fix those errors before updating")
    if not names:
        return records, None
    if root.name != "others":
        raise RuntimeError("Refusing to update a directory that is not the others/ bucket")
    if (Path.home() / ".agents/skills").resolve() != root:
        raise RuntimeError("Global skills.sh destination does not point to this others/ directory")
    if lock_path.resolve() != (Path.home() / ".agents/.skill-lock.json").resolve():
        raise RuntimeError("Updates require the real global skills.sh source lock")
    personal = root.parent / "personal"
    before = digest_tree(personal)
    backups = root.parent / ".local/skill-update-backups"
    backups.mkdir(parents=True, exist_ok=True)
    with (backups / "update.lock").open("a") as guard:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another skill update is already running") from None
        # Re-check provenance immediately before writing; never use a stale plan.
        refreshed = verify(root, lock_path)
        if refreshed != records:
            raise RuntimeError("The update plan changed; run check/update again")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup = backups / stamp
        backup.mkdir()
        shutil.copy2(lock_path, backup / "skill-lock.json")
        for name in names:
            shutil.copytree(root / name, backup / "others" / name, symlinks=True)
        (backup / "plan.json").write_text(json.dumps(records, indent=2) + "\n")
        command = ["npx", "--yes", "skills@latest", "update", *names, "-g", "-y"]
        print(f"Updating {len(names)} tracked downloads; backup: {backup}", flush=True)
        with (backup / "update.log").open("w") as log:
            result = run(command, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        if digest_tree(personal) != before:
            raise RuntimeError(f"Personal skill files changed unexpectedly; inspect {backup}")
        if result.returncode:
            raise RuntimeError(f"Updater failed (exit {result.returncode}); see {backup / 'update.log'}")
        after = verify(root, lock_path)
        by_name = {r["name"]: r for r in after}
        incomplete = [name for name in names if by_name.get(name, {}).get("status") != "current"]
        if incomplete:
            raise RuntimeError(f"Updates not verified for: {', '.join(incomplete)}. See {backup / 'update.log'}")
        (backup / "result.json").write_text(json.dumps(after, indent=2) + "\n")
        return after, backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "update"])
    parser.add_argument("--json", action="store_true", help="Print a JSON check report (check only)")
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".agents/skills")
    parser.add_argument("--lock-file", type=Path, default=Path.home() / ".agents/.skill-lock.json")
    args = parser.parse_args()
    if args.command == "update" and args.json:
        parser.error("--json is available for check only")
    root, lock_path = args.skills_dir.expanduser().resolve(), args.lock_file.expanduser().resolve()
    try:
        records = check(root, lock_path)
        if args.command == "update":
            records, backup = update(root, lock_path, records)
            if backup:
                print("Update verified; personal skills preserved.")
        if args.json:
            print(json.dumps({"directory": str(root), "summary": summary(records), "skills": records}, indent=2))
        else:
            print_report(records)
        return 2 if any(r["status"] == "error" for r in records) else 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"skill-updates: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
