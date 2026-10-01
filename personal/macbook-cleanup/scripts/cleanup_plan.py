"""Freeze exact local operations and revalidate filesystem evidence before consent."""
import hashlib
import json
import os
import secrets
import stat
import subprocess
import time
from pathlib import Path

try:
    from .cleanup_items import eligibility, normalized
    from .cleanup_tree import SafetyError, tree_evidence, recovery_estimates, same_metadata
except ImportError:
    from cleanup_items import eligibility, normalized
    from cleanup_tree import SafetyError, tree_evidence, recovery_estimates, same_metadata


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def private_json(path, value):
    path = Path(path)
    # Atomic replacement never follows a pre-existing destination symlink.
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def identity(info):
    return {"device": info.st_dev, "inode": info.st_ino, "mode": info.st_mode,
            "uid": info.st_uid, "gid": info.st_gid}


def open_parent(path):
    """Anchor each component with O_NOFOLLOW so ancestor swaps cannot redirect I/O."""
    path = normalized(path)
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    chain = []
    try:
        for part in path.parent.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_fd
            info = os.fstat(descriptor)
            chain.append([info.st_dev, info.st_ino])
        return descriptor, chain
    except Exception:
        os.close(descriptor)
        raise


def check_active(path):
    command = ["lsof", "-nP", "-F", "p"]
    command += ["+D", str(path)] if path.is_dir() else ["--", str(path)]
    try:
        result = subprocess.run(command, capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise SafetyError("Active-workload lookup failed; close apps and retry") from exc
    if result.returncode == 0 and result.stdout.strip():
        raise SafetyError("An active process is using this item")
    if result.returncode != 1 or result.stdout.strip() or result.stderr.strip():
        raise SafetyError("Active-workload lookup was inconclusive; no deletion allowed")


def inspect(item, home, linked_inodes=()):
    path = normalized(item["path"])
    allowed, reason, manifest = eligibility(path, home)
    if not allowed or not item.get("selectable"):
        raise SafetyError(reason)
    parent_fd, chain = open_parent(path)
    try:
        root = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        downloads = path.is_relative_to(Path(home) / "Downloads")
        if downloads != stat.S_ISREG(root.st_mode):
            raise SafetyError("Expected an installer file or generated directory")
        if root.st_dev != os.stat(home).st_dev:
            raise SafetyError("External mount is protected")
        result = tree_evidence(parent_fd, path.name, os.getuid(), root.st_dev,
                               dependency_tree=path.name == "node_modules", linked_inodes=linked_inodes)
        result["parent_chain"] = chain
        if manifest:
            if manifest.is_symlink():
                raise SafetyError("Project manifest is a symbolic link")
            descriptor = os.open(manifest.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
            try:
                info = os.fstat(descriptor)
                if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode) or info.st_size > 4_000_000:
                    raise SafetyError("Project manifest cannot be verified")
                result["manifest"] = {"identity": identity(info),
                                      "digest": hashlib.sha256(os.read(descriptor, 4_000_001)).hexdigest()}
            finally:
                os.close(descriptor)
    finally:
        os.close(parent_fd)
    check_active(path)
    return result


def create_plan(ids, items, home, lifetime=600):
    if not isinstance(ids, list) or not ids or len(ids) > 200:
        raise SafetyError("Choose between 1 and 200 items")
    if any(not isinstance(value, str) for value in ids) or len(set(ids)) != len(ids):
        raise SafetyError("Item identifiers must be unique strings")
    known = {row["id"]: row for row in items}
    if any(value not in known for value in ids):
        raise SafetyError("Unknown item identifier; paths cannot be supplied by clients")
    selected_paths = [normalized(known[value]["path"]) for value in ids]
    for index, path in enumerate(selected_paths):
        if any(path == other or path in other.parents or other in path.parents
               for other in selected_paths[index + 1:]):
            raise SafetyError("Selected operations overlap; choose one concrete root per item")
    operations, blocked = [], []
    for value in ids:
        item = known[value]
        try:
            evidence = inspect(item, home)
            operations.append({"id": value, "path": item["path"], "label": item["label"],
                               "action": "delete_permanently", "evidence": evidence,
                               "identity": evidence["identity"],
                               "allocated_bytes": evidence["allocated_bytes"],
                               "logical_bytes": evidence["logical_bytes"]})
        except (OSError, SafetyError) as exc:
            blocked.append({"id": value, "path": item["path"], "reason": str(exc)})
    # Only links crossing approved item boundaries need content verification after unlink.
    seen, cross_item = set(), set()
    for row in operations:
        inodes = set(row["evidence"]["files"])
        cross_item.update(seen & inodes)
        seen.update(inodes)
    refined = []
    for row in operations:
        try:
            if cross_item & row["evidence"]["files"].keys():
                fresh = inspect(dict(row, selectable=True), home, cross_item)
                if not same_metadata(fresh, row["evidence"]):
                    raise SafetyError("Item changed while preparing linked-file approval")
                row["evidence"] = fresh
            refined.append(row)
        except (OSError, SafetyError) as exc:
            blocked.append({"id": row["id"], "path": row["path"], "reason": str(exc)})
    operations = refined
    estimated, shared = recovery_estimates(operations)
    plan = {"id": secrets.token_hex(16), "items": operations, "blocked": blocked,
            "estimated_bytes": estimated, "shared_bytes": shared,
            "expires_at": time.time() + lifetime, "consumed": False}
    plan["digest"] = hashlib.sha256(encode(plan)).hexdigest()
    return plan


def public_plan(plan):
    return {key: ([{field: value for field, value in row.items() if field != "evidence"}
                   for row in plan[key]] if key == "items" else plan[key])
            for key in ("id", "digest", "items", "blocked", "estimated_bytes", "shared_bytes", "expires_at")}


def validate_confirmation(plan, payload):
    if not plan or plan.get("consumed") or plan["expires_at"] < time.time():
        raise SafetyError("Plan is absent, expired, or already consumed; review a new plan")
    if payload.get("confirmed") is not True or payload.get("plan_id") != plan["id"]:
        raise SafetyError("Exact final batch confirmation is required")
    digest = payload.get("digest")
    if not isinstance(digest, str) or not secrets.compare_digest(digest, plan["digest"]):
        raise SafetyError("Plan digest does not match the reviewed batch")
    if not plan["items"]:
        raise SafetyError("No validated items remain; nothing can be confirmed")
