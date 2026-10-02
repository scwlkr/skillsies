"""Bounded CI hints, not workflow parsing or compliance verification."""

import re
from itertools import islice

POLICY = {
    "ci-scope": "Separate lightweight documentation checks from full code verification; use focused code checks only with reliable scope detection, otherwise run full verification. Acceptance: docs-only changes avoid app builds; shared code, dependencies, build/CI configuration and uncertain scope run the full suite. Generated docs and executable examples receive their actual behavior checks.",
    "ci-cache": "Review repeated CI installs/builds and cache useful dependencies, tools and outputs with platform/toolchain/lockfile-aware keys. Acceptance: a warm run reuses work and dependency/toolchain changes invalidate affected caches; document any intentionally uncached expensive step.",
    "ci-verify": "Verify local CI routing with representative docs, code, dependency and CI configuration changes. Acceptance: retain the exact clean commit SHA, commands and aggregate results; applicable local checks pass before push/merge, skipped work cannot hide failures, and edits or a new commit SHA require fresh checks. Hosted runners need a documented external requirement; required hosted results also pass on the current commit before merge/Done. Local keyword detection does not prove this.",
}
PATTERNS = {
    "scope": r"paths(?:-ignore)?\s*:|(?:paths-filter|changed-files)@|git\s+diff\b|changes\s*:",
    "cache": r"(?:actions/cache(?:/\w+)?|[\w-]+/rust-cache)@|\bcache\s*:",
    "expensive": r"\b(?:cargo|npm|pnpm|yarn|bun|pip|pip3|uv|poetry|go|dotnet|mvn|gradle|docker)\s+(?:install|ci|build|test|check|clippy|sync|restore|download)\b",
}


def inspect_ci(root):
    paths = set()
    truncated = False
    for directory in (".github/workflows", ".circleci", ".buildkite"):
        folder = root / directory
        if folder.is_dir() and not folder.is_symlink() and not folder.parent.is_symlink():
            entries = list(islice(folder.iterdir(), 65))
            truncated |= len(entries) > 64
            paths.update(path for path in entries[:64] if path.suffix in (".yml", ".yaml"))
    for name in (".gitlab-ci.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml", "Jenkinsfile", ".travis.yml"):
        if (root / name).exists():
            paths.add(root / name)
    signals, unread = [], []
    ordered = sorted(paths)
    for path in ordered[:32]:
        name = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
            unread.append(name)
            continue
        try:
            content = path.read_text()
        except (OSError, UnicodeError):
            unread.append(name)
            continue
        content = "\n".join(line for line in content.splitlines() if not line.lstrip().startswith("#"))
        signals.append({"file": name, **{key: bool(re.search(pattern, content, re.I))
                                         for key, pattern in PATTERNS.items()}})
    truncated |= len(ordered) > 32
    todos = []
    if not paths and not truncated:
        todos.append({"id": "ci-discovery", "text": "Locate existing local CI gates or plan them behind `./project` when implementation is scheduled; no standard hosted CI config was found, which is not a gap by itself. Acceptance: document proportional checks, useful caching, and exact clean commit SHA/commands/results; passing applicable local checks gate push/merge, and changed commits require fresh checks. Hosted runners need a documented external requirement. Setup does not provision CI."})
    else:
        # Per-file hints avoid treating one cached/filtered workflow as coverage for all.
        for key, predicate in (("scope", lambda row: not row["scope"]),
                               ("cache", lambda row: row["expensive"] and not row["cache"])):
            affected = [row["file"] for row in signals if predicate(row)]
            if affected:
                todos.append({"id": "ci-" + key, "text": POLICY["ci-" + key] +
                              " No local " + key + " signal: " + ", ".join(f"`{name}`" for name in affected) + "."})
        if unread or truncated:
            todos.append({"id": "ci-review", "text": "Review CI files omitted by bounded inspection: " +
                          ", ".join([*(f"`{name}`" for name in unread),
                                     *(["additional files beyond scan limits"] if truncated else [])]) +
                          "; verify proportional checks and caching."})
        todos.append({"id": "ci-verify", "text": POLICY["ci-verify"]})
    return {"alignment": "pending", "basis": "Local text hints only; local gates, commit evidence, hosted necessity, routing and cache effectiveness unverified",
            "files": signals, "unread": unread, "truncated": truncated, "todos": todos}


def append_todos(existing, todos):
    additions = [f"- [ ] {item['text']} <!-- setup:{item['id']} -->" for item in todos
                 if f"<!-- setup:{item['id']} -->" not in existing]
    if not additions:
        return existing
    return (existing.rstrip() + "\n\n" if existing else "# Setup handoff\n\n") + "\n".join(additions) + "\n"
