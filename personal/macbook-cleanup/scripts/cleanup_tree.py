"""Anchored inventories and conservative recovery for generated hard-linked files."""
import hashlib
import json
import os
import stat
from collections import Counter
from pathlib import Path

try:
    from .cleanup_items import protected_parts
except ImportError:
    from cleanup_items import protected_parts


class SafetyError(ValueError):
    pass


def identity(info):
    return {"device": info.st_dev, "inode": info.st_ino, "mode": info.st_mode,
            "uid": info.st_uid, "gid": info.st_gid}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def installed_package(directory_fd, name, relative):
    """Only real package slots with matching regular manifests exempt fixture names."""
    parts = Path(relative.lstrip("/")).parts
    if not parts:
        return False
    parent = parts[-2] if len(parts) > 1 else "node_modules"
    scoped = parent.startswith("@") and (len(parts) == 2 or parts[-3] == "node_modules")
    if parent != "node_modules" and not scoped:
        return False
    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
    descriptor = None
    try:
        descriptor = os.open("package.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=child)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > 4_000_000:
            return False
        manifest = json.loads(os.read(descriptor, 4_000_001))
        expected = f"{parent}/{parts[-1]}" if scoped else parts[-1]
        return isinstance(manifest, dict) and manifest.get("name") == expected
    except (OSError, ValueError):
        return False
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(child)


def installed_package_link(directory_fd, name, relative, root_fd):
    """Authenticate a pnpm package link through anchored, non-symlink directories."""
    link = os.readlink(name, dir_fd=directory_fd)
    internal = os.path.normpath(str(Path(relative.lstrip("/")).parent / link))
    if Path(link).is_absolute() or internal == ".." or internal.startswith("../"):
        return False
    parts = Path(internal).parts
    if not parts:
        return False
    descriptor = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return installed_package(descriptor, parts[-1], relative)
    except OSError:
        return False
    finally:
        os.close(descriptor)


def content_hash(directory_fd, name, info):
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
    try:
        before = os.fstat(descriptor)
        if identity(before) != identity(info):
            raise SafetyError("Linked file changed during inspection")
        digest = hashlib.sha256()
        while data := os.read(descriptor, 1024 * 1024):
            digest.update(data)
        after = os.fstat(descriptor)
        if (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink) != (
                info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink):
            raise SafetyError("Linked file changed during inspection")
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def tree_evidence(parent_fd, name, uid, device, dependency_tree=False, linked_inodes=()):
    records, files, seen = [], {}, set()
    totals, root_identity, root_ctime, inventory_root = [0, 0, 0], None, None, None

    def visit(directory_fd, entry, relative, trusted_package=False):
        nonlocal root_identity, root_ctime, inventory_root
        info = os.stat(entry, dir_fd=directory_fd, follow_symlinks=False)
        if dependency_tree and stat.S_ISDIR(info.st_mode) and not trusted_package:
            trusted_package = installed_package(directory_fd, entry, relative)
        if dependency_tree and stat.S_ISLNK(info.st_mode) and not trusted_package:
            trusted_package = installed_package_link(directory_fd, entry, relative, inventory_root)
        if not trusted_package and protected_parts(Path(relative).parts):
            raise SafetyError("Protected backup, evidence or runtime data exists inside this item")
        if info.st_uid != uid:
            raise SafetyError("Ownership differs from the current user")
        if info.st_dev != device:
            raise SafetyError("Nested or external mount is protected")
        link = None
        if stat.S_ISLNK(info.st_mode) and relative:
            link = os.readlink(entry, dir_fd=directory_fd)
            internal = os.path.normpath(str(Path(relative.lstrip("/")).parent / link))
            if Path(link).is_absolute() or internal == ".." or internal.startswith("../"):
                raise SafetyError("Absolute or outside symbolic-link target is protected")
            checked = os.stat(entry, dir_fd=directory_fd, follow_symlinks=False)
            if identity(checked) != identity(info) or checked.st_ctime_ns != info.st_ctime_ns:
                raise SafetyError("Symbolic link changed during inspection")
        elif not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            raise SafetyError("Symlink or special file is protected")
        inode = f"{info.st_dev}:{info.st_ino}"
        # Renaming an archive legitimately changes its ctime; freeze its content too.
        digest = (content_hash(directory_fd, entry, info) if stat.S_ISREG(info.st_mode)
                  and (inode in linked_inodes or not relative) else None)
        record = [relative, identity(info), info.st_size, info.st_blocks, info.st_mtime_ns,
                  info.st_ctime_ns if relative else 0, info.st_nlink, link, digest]
        records.append(record)
        if inode not in seen:
            totals[0] += info.st_blocks * 512
            totals[1] += info.st_size if stat.S_ISREG(info.st_mode) else 0
            seen.add(inode)
        totals[2] += 1
        if stat.S_ISREG(info.st_mode):
            file = files.setdefault(inode, {"links": info.st_nlink, "count": 0,
                                           "allocated_bytes": info.st_blocks * 512})
            file["count"] += 1
        if not relative:
            root_identity, root_ctime = identity(info), info.st_ctime_ns
        if stat.S_ISDIR(info.st_mode):
            child_fd = os.open(entry, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                               dir_fd=directory_fd)
            try:
                if identity(os.fstat(child_fd)) != identity(info):
                    raise SafetyError("Directory changed during inspection")
                if not relative:
                    inventory_root = child_fd
                for child in sorted(os.listdir(child_fd)):
                    visit(child_fd, child, f"{relative}/{child}", trusted_package)
                final = os.fstat(child_fd)
                if final.st_mtime_ns != info.st_mtime_ns or final.st_ctime_ns != info.st_ctime_ns:
                    raise SafetyError("Directory changed during inspection")
            finally:
                os.close(child_fd)

    visit(parent_fd, name, "")
    return {"identity": root_identity, "root_ctime_ns": root_ctime,
            "tree_digest": hashlib.sha256(encoded(records)).hexdigest(),
            "allocated_bytes": totals[0], "logical_bytes": totals[1], "entries": totals[2],
            "records": records, "files": files, "dependency_tree": dependency_tree}


def recovery_estimates(operations):
    """Charge each inode once, and zero files retaining links outside this batch."""
    counts = Counter()
    last, shared = {}, {}
    for index, row in enumerate(operations):
        files = row["evidence"]["files"]
        row["allocated_bytes"] -= sum(file["allocated_bytes"] for file in files.values())
        row["shared_bytes"] = 0
        for inode, file in files.items():
            counts[inode] += file["count"]
            last[inode] = index, file
    for inode, (index, file) in last.items():
        if counts[inode] == file["links"]:
            operations[index]["allocated_bytes"] += file["allocated_bytes"]
        else:
            shared[inode] = file["allocated_bytes"]
            operations[index]["shared_bytes"] += file["allocated_bytes"]
    return sum(row["allocated_bytes"] for row in operations), sum(shared.values())


def matches_after_unlinks(current, expected, removed):
    """Permit only the exact nlink/ctime updates our completed removals explain."""
    if current["identity"] != expected["identity"] or current["entries"] != expected["entries"]:
        return False
    if current["root_ctime_ns"] != expected["root_ctime_ns"]:
        root = expected["records"][0]
        inode = f"{root[1]['device']}:{root[1]['inode']}"
        if not removed.get(inode) or root[8] is None:
            return False
    if len(current["records"]) != len(expected["records"]):
        return False
    for now, before in zip(current["records"], expected["records"]):
        inode = f"{before[1]['device']}:{before[1]['inode']}"
        count = removed.get(inode, 0) if before[8] is not None else 0
        adjusted = list(before)
        if count:
            adjusted[6] -= count
            adjusted[5] = now[5]
        if now != adjusted:
            return False
    return True


def same_metadata(current, expected):
    """A hash-only refinement must not conceal changes since the metadata pass."""
    without_hash = lambda value: {key: ([record[:-1] for record in data] if key == "records" else data)
                                  for key, data in value.items() if key != "tree_digest"}
    return without_hash(current) == without_hash(expected)


def hashed_inodes(evidence):
    return {f"{record[1]['device']}:{record[1]['inode']}" for record in evidence["records"]
            if record[8] is not None}
