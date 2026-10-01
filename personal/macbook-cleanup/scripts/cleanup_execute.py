"""Execute one explicitly confirmed, immutable batch with recoverable staging."""
import os
from collections import Counter
import secrets
import shutil
import stat
import time
from pathlib import Path

try:
    from .cleanup_tree import matches_after_unlinks, hashed_inodes
    from .capacity import measure
    from .cleanup_plan import (SafetyError, check_active, identity, inspect, open_parent, private_json,
                               public_plan, tree_evidence, validate_confirmation)
except ImportError:
    from cleanup_tree import matches_after_unlinks, hashed_inodes
    from capacity import measure
    from cleanup_plan import (SafetyError, check_active, identity, inspect, open_parent, private_json,
                              public_plan, tree_evidence, validate_confirmation)


def inventory(row, parent_fd, name):
    evidence = row["evidence"]
    linked = hashed_inodes(evidence)
    return tree_evidence(parent_fd, name, os.getuid(), row["identity"]["device"],
                         dependency_tree=evidence["dependency_tree"], linked_inodes=linked)


def staging_matches(current, expected, renamed):
    root = current["identity"]
    inode = f"{root['device']}:{root['inode']}"
    allow_ctime = inode in renamed and inode in hashed_inodes(expected)
    return all(value == expected[key] for key, value in current.items()
               if key != "root_ctime_ns" or not allow_ctime)


def execute(plan, payload, report_dir, home, preview=False, target_percent=50):
    validate_confirmation(plan, payload)
    plan["consumed"] = True  # Any attempted batch consumes consent, including a failed preflight.
    approval = dict(public_plan(plan), confirmed=True, confirmed_at=time.time(), preview=preview)
    private_json(Path(report_dir) / "approved-plan.json", approval)
    results = {"state": "preview" if preview else "running", "preview": preview,
               "plan_id": plan["id"], "results": [], "staging": [], "started_at": time.time()}
    private_json(Path(report_dir) / "cleanup-results.json", results)
    if preview:
        results["results"] = [{"id": row["id"], "path": row["path"],
                               "status": "preview_only", "message": "Approved selection saved; nothing deleted"}
                              for row in plan["items"]]
    else:
        staged, removed, renamed = [], Counter(), set()
        try:
            if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
                raise SafetyError("This Python lacks descriptor-safe directory deletion")
            # Validate the whole batch before moving or removing any entry.
            for row in plan["items"]:
                if Path(report_dir).resolve().is_relative_to(Path(row["path"])):
                    raise SafetyError("Cleanup reports or approval evidence lie inside a selected item")
                fresh = inspect(dict(row, selectable=True), home, hashed_inodes(row["evidence"]))
                if fresh != row["evidence"]:
                    raise SafetyError(f"Filesystem evidence changed: {row['path']}")
            for row in plan["items"]:
                parent_fd, chain = open_parent(row["path"])
                record = {"row": row, "parent_fd": parent_fd, "staged": False,
                          "name": f".macbook-cleanup-{secrets.token_hex(16)}"}
                staged.append(record)
                original = Path(row["path"]).name
                if chain != row["evidence"]["parent_chain"]:
                    raise SafetyError("Parent directory changed")
                before = inventory(row, parent_fd, original)
                if not staging_matches(before, row["evidence"], renamed):
                    raise SafetyError("Item changed before staging")
                # Random exclusive destination in the same anchored parent keeps data on-volume.
                try:
                    os.stat(record["name"], dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise SafetyError("Staging destination unexpectedly exists")
                record["journal"] = {"id": row["id"], "original_path": row["path"],
                                     "staged_path": str(Path(row["path"]).parent / record["name"]),
                                     "identity": row["identity"], "state": "prepared"}
                results["staging"].append(record["journal"])
                # Durable mapping precedes rename, so a killed process leaves recovery evidence.
                private_json(Path(report_dir) / "cleanup-results.json", results)
                os.rename(original, record["name"], src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                record["staged"] = True
                root = row["identity"]
                renamed.add(f"{root['device']}:{root['inode']}")
                os.fsync(parent_fd)
                record["journal"]["state"] = "staged"
                private_json(Path(report_dir) / "cleanup-results.json", results)
                after = inventory(row, parent_fd, record["name"])
                if any(after[key] != row["evidence"][key] for key in after if key != "root_ctime_ns"):
                    raise SafetyError("Item changed during staging")
                record["staged_evidence"] = after
            # Recheck the whole staged batch before the first permanent removal.
            for record in staged:
                row = record["row"]
                current = inventory(row, record["parent_fd"], record["name"])
                if not staging_matches(current, record["staged_evidence"], renamed):
                    raise SafetyError("Staged batch changed before removal")
                record["staged_evidence"] = current
            # Only after all items are frozen and staged does permanent removal begin.
            for record in staged:
                row, parent_fd = record["row"], record["parent_fd"]
                staged_path = Path(row["path"]).parent / record["name"]
                check_active(staged_path)
                current = inventory(row, parent_fd, record["name"])
                if not matches_after_unlinks(current, record["staged_evidence"], removed):
                    raise SafetyError("Staged item changed immediately before removal")
                info = os.stat(record["name"], dir_fd=parent_fd, follow_symlinks=False)
                if identity(info) != row["identity"]:
                    raise SafetyError("Staged item identity changed")
                record["deletion_started"] = True
                record["journal"]["state"] = "deleting"
                private_json(Path(report_dir) / "cleanup-results.json", results)
                if stat.S_ISDIR(info.st_mode):
                    shutil.rmtree(record["name"], dir_fd=parent_fd)
                else:
                    os.unlink(record["name"], dir_fd=parent_fd)
                record["staged"] = False
                removed.update({inode: file["count"] for inode, file in row["evidence"]["files"].items()})
                os.fsync(parent_fd)
                record["journal"]["state"] = "deleted"
                results["results"].append({"id": row["id"], "path": row["path"],
                                           "status": "deleted", "estimated_bytes": row["allocated_bytes"]})
                private_json(Path(report_dir) / "cleanup-results.json", results)
            results["state"] = "complete"
        except Exception as exc:
            results["state"] = "error"
            results["error"] = str(exc)
            # Restore remaining staged entries without overwriting any newly created original.
            for record in reversed(staged):
                if not record["staged"]:
                    continue
                original, parent_fd = Path(record["row"]["path"]).name, record["parent_fd"]
                try:
                    os.stat(original, dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError:
                    try:
                        staged_info = os.stat(record["name"], dir_fd=parent_fd, follow_symlinks=False)
                        if identity(staged_info) != record["row"]["identity"]:
                            raise OSError("Staged identity changed; recovery requires manual review")
                        os.rename(record["name"], original, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                        os.fsync(parent_fd)
                        partial = record.get("deletion_started", False)
                        status = "restored_remaining" if partial else "restored"
                        record["journal"]["state"] = status
                        private_json(Path(report_dir) / "cleanup-results.json", results)
                        results["results"].append({"id": record["row"]["id"],
                                                   "path": record["row"]["path"], "status": status,
                                                   "partial_deletion_possible": partial,
                                                   "message": "Removal began; only remaining contents were returned" if partial
                                                   else "Nothing deleted; staged item returned to its original path"})
                        continue
                    except OSError as restore_error:
                        message = str(restore_error)
                except OSError as restore_error:
                    message = str(restore_error)
                else:
                    message = "Original path exists; recovery will not overwrite it"
                record["journal"]["state"] = "recovery_required"
                results["results"].append({"id": record["row"]["id"], "status": "recovery_required",
                                           "path": str(Path(record["row"]["path"]).parent / record["name"]),
                                           "message": message})
        finally:
            for record in staged:
                os.close(record["parent_fd"])
    if not preview:
        try:
            results["capacity_after"] = measure(Path(home), target_percent)
        except Exception as exc:
            results["capacity_error"] = str(exc)
    results["finished_at"] = time.time()
    private_json(Path(report_dir) / "cleanup-results.json", results)
    return results
