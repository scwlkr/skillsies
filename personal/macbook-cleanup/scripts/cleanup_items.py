"""Derive selectable operations from locally measured scanner records."""
import hashlib
import os
from pathlib import Path

PROTECTED = {"backup", "backups", "evidence", "release-proof", "release_proof",
             "release-evidence", "releases", ".git", "cloudstorage", "mobile documents",
             "coresimulator", "containers", ".tart", ".ollama", ".lmstudio",
             ".env", ".ssh", ".gnupg", "id_rsa", "id_ed25519", "credentials",
             "credentials.json", "secrets", "secrets.json"}
CACHE_APPS = {"com.apple.dt.Xcode", "com.google.Chrome", "org.mozilla.firefox",
              "com.microsoft.VSCode", "com.spotify.client", "com.brave.Browser",
              "com.apple.Safari", "com.apple.helpd"}


def normalized(path):
    value = str(path)
    prefix = "/System/Volumes/Data/"
    if value.startswith(prefix):
        value = "/" + value[len(prefix):]
    result = Path(os.path.normpath(value))
    if not result.is_absolute() or ".." in Path(value).parts:
        raise ValueError("Path must be absolute without parent traversal")
    return result


def protected_parts(parts):
    return any(part.lower() in PROTECTED or part.lower().startswith("backup-")
               or part.lower().startswith(".env.")
               or "evidence" in part.lower() or "release-proof" in part.lower()
               for part in parts)


def eligibility(path, home):
    """Policy is deliberately narrower than scanner review categories."""
    try:
        path, home = normalized(path), Path(home)
        relative = path.relative_to(home)
    except ValueError:
        return False, "Outside this user's home; use the owning tool", None
    if relative.as_posix() in (".ollama/models", ".lmstudio/models", ".cache/huggingface"):
        return False, "Model storage is an aggregate, not one model. Review individual model identities before removing them with the owning model manager.", None
    if protected_parts(relative.parts):
        return False, "Protected backup, evidence, cloud, runtime or source-control data", None
    if path == home or len(relative.parts) < 2:
        return False, "Whole storage roots require owning-tool review", None
    if path.name in ("target", "node_modules"):
        manifest = path.parent / ("Cargo.toml" if path.name == "target" else "package.json")
        if manifest.is_file() and not manifest.is_symlink():
            return True, "Generated project data; close all related builds first", manifest
        return False, "A regular project manifest is required", None
    derived = home / "Library/Developer/Xcode/DerivedData"
    if path.parent == derived:
        return True, "One Xcode project's generated data; close Xcode and builds first", None
    caches = home / "Library/Caches"
    if path.parent == caches and path.name in CACHE_APPS:
        return True, "Recognized application cache; close the application first", None
    if relative.parts[0] == "Downloads" and path.suffix.lower() in {".dmg", ".pkg", ".xip", ".zip"}:
        return True, "Downloaded archive; confirm it is replaceable and not release evidence", None
    return False, "Use the owning app or tool; this aggregate or personal data is not a deletion operation", None


def build_items(summary, scan, home=None):
    home = Path(home or Path.home()).resolve()
    measured = {str(normalized(row["path"])): row for group in
                (scan.get("top_directories", []), scan.get("top_files", []))
                for row in group if row.get("path")}
    candidates = summary.get("candidates", scan.get("candidates", []))
    rows = []
    for candidate in candidates:
        path = normalized(candidate["path"])
        expansions = []
        if path in (home / "Library/Caches", home / "Library/Developer/Xcode/DerivedData"):
            expansions = [dict(row, category=candidate.get("category", "build"))
                          for value, row in measured.items() if normalized(value).parent == path]
        rows.extend(expansions or [candidate])
    items, seen = [], set()
    for row in rows:
        path = normalized(row["path"])
        if str(path) in seen:
            continue
        seen.add(str(path))
        selectable, reason, _ = eligibility(path, home)
        try:
            if path.is_symlink() or not path.exists():
                selectable, reason = False, "Missing or symbolic-link path; rescan or review manually"
            elif selectable and path.name in ("target", "node_modules") and not path.is_dir():
                selectable, reason = False, "Generated artifact must be a directory"
        except OSError:
            selectable, reason = False, "Cannot inspect this path; complete access setup then rescan"
        operation = "delete_permanently" if selectable else "owning_tool_review"
        identifier = hashlib.sha256(f"{operation}\0{path}".encode()).hexdigest()[:24]
        items.append({"id": identifier, "path": str(path), "label": path.name,
                      "category": row.get("category", "review"),
                      "allocated_bytes": max(0, int(row.get("allocated_bytes", 0))),
                      "logical_bytes": max(0, int(row.get("logical_bytes", 0))),
                      "action": operation, "risk": "requires review" if selectable else "app-managed",
                      "selectable": selectable, "reason": reason,
                      "next_step": row.get("action", "Review this exact item before deciding whether to remove it.")})
    return sorted(items, key=lambda row: (-row["allocated_bytes"], row["path"]))
