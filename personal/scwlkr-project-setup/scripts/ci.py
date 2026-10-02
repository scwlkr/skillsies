"""Bounded CI hints, not workflow parsing or compliance verification."""

import re
from itertools import islice

POLICY = {
    "ci-scope": "Separate non-executable docs → light checks/no app builds; reliable scope → focused; shared code/dependencies/build/CI/uncertain scope → full suite; generated docs/executable examples → behavior checks. Verify routing.",
    "ci-cache": "Cache repeated installs/builds: dependencies/tools/outputs keyed by platform/toolchain/lockfile. Prove warm reuse + invalidation after dependency/toolchain changes; explain uncached costly steps.",
    "ci-verify": "Verify local CI routing: docs/code/dependency/CI changes. Applicable checks pass before push/merge on exact clean SHA; retain SHA/base/commands/aggregate results; skipped work cannot hide failures; edits/new SHA → recheck. Hosted → documented requirement/owner direction; required current results pass before merge/Done. Keywords ≠ proof.",
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
        todos.append({"id": "ci-discovery", "text": "Locate/plan local CI behind `./project`: proportional checks, useful caching, exact clean SHA/base/commands/results. Applicable checks pass before push/merge; edits/new SHA → recheck. No hosted config ≠ gap; hosted → documented requirement/owner direction. Setup does not provision CI."})
    else:
        # Per-file hints avoid treating one cached/filtered workflow as coverage for all.
        for key, predicate in (("scope", lambda row: not row["scope"]),
                               ("cache", lambda row: row["expensive"] and not row["cache"])):
            affected = [row["file"] for row in signals if predicate(row)]
            if affected:
                todos.append({"id": "ci-" + key, "text": POLICY["ci-" + key] +
                              " No " + key + " hint: " + ", ".join(f"`{name}`" for name in affected) + "."})
        if unread or truncated:
            todos.append({"id": "ci-review", "text": "Review unscanned CI: " +
                          ", ".join([*(f"`{name}`" for name in unread),
                                     *(["additional files beyond scan limits"] if truncated else [])]) +
                          "; verify proportional checks and caching."})
        todos.append({"id": "ci-verify", "text": POLICY["ci-verify"]})
    return {"alignment": "pending", "basis": "Text hints; gates/commit evidence/hosted necessity/routing/cache effectiveness unverified",
            "files": signals, "unread": unread, "truncated": truncated, "todos": todos}


def append_todos(existing, todos):
    additions = [f"- [ ] {item['text']} <!-- setup:{item['id']} -->" for item in todos
                 if f"<!-- setup:{item['id']} -->" not in existing]
    if not additions:
        return existing
    return (existing.rstrip() + "\n\n" if existing else "# Setup handoff\n\n") + "\n".join(additions) + "\n"
