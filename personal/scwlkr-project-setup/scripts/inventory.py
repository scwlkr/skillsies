"""Bounded, read-only discovery; never execute project code."""

import json
import re
import subprocess

START = "<!-- scwlkr-project-setup:start -->"
END = "<!-- scwlkr-project-setup:end -->"
STATE = "tools/project-cli/setup.json"
MANIFESTS = ("Cargo.toml", "package.json", "go.mod", "pyproject.toml", "Makefile", "justfile")


def read(root, relative):
    path = root / relative
    if not path.is_file():
        return ""
    if path.stat().st_size > 262144:
        raise ValueError(f"File too large for basic setup: {relative}")
    return path.read_text()


def metadata(root):
    raw = read(root, STATE)
    if not raw:
        return {}
    state = json.loads(raw)
    if state.get("version") != 1:
        raise ValueError(f"Unsupported setup metadata: {STATE}")
    return state


def block_parts(text):
    if START not in text and END not in text:
        return text, "", ""
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("Repair duplicate or incomplete setup markers in AGENTS.md")
    before, rest = text.split(START)
    block, after = rest.split(END)
    return before, START + block + END, after


def detect_routes(root):
    routes = []
    used = {"doctor", "help"}

    def add(name, program, args, family):
        if name in used:
            name = f"{family}:{name}"
        if name in used or name.startswith("-"):
            return
        used.add(name)
        routes.append({"name": name, "program": program, "args": args})

    cargo = read(root, "Cargo.toml")
    if cargo:
        for name, args in (("build", ["build"]), ("test", ["test"]),
                           ("check", ["check"]), ("fmt", ["fmt", "--check"])):
            add(name, "cargo", args, "rust")
        # A package with a library only has no runnable default binary.
        if (root / "src/main.rs").exists() or "[[bin]]" in cargo:
            add("run", "cargo", ["run", "--"], "rust")
    package = json.loads(read(root, "package.json") or "{}")
    manager = str(package.get("packageManager", "")).split("@")[0]
    if manager not in ("npm", "pnpm", "yarn", "bun"):
        locks = (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"),
                 ("bun.lock", "bun"), ("bun.lockb", "bun"), ("package-lock.json", "npm"))
        found = {manager for lock, manager in locks if (root / lock).exists()}
        if len(found) > 1:
            raise ValueError("Conflicting package-manager lockfiles; resolve the package manager first")
        manager = next(iter(found), "npm")
    for name in sorted(package.get("scripts", {})):
        args = ["run", name] + (["--"] if manager == "npm" else [])
        add(name, manager, args, "node")
    if (root / "go.mod").exists():
        for name, args in (("build", ["build", "./..."]), ("test", ["test", "./..."]),
                           ("check", ["vet", "./..."])):
            add(name, "go", args, "go")
    for file, program, pattern in (
        ("Makefile", "make", r"^([A-Za-z][\w-]*):(?!=)"),
        ("justfile", "just", r"^([A-Za-z][\w-]*)(?:\s+[^:\n]+)?:"),
    ):
        for name in dict.fromkeys(re.findall(pattern, read(root, file), re.M)):
            add(name, program, [name], program)
    return routes


def inspect(root):
    state = metadata(root)
    agents = read(root, "AGENTS.md")
    before, _, after = block_parts(agents)
    package = json.loads(read(root, "package.json") or "{}")
    urls = sorted({url.rstrip(".,;").removesuffix("/overview") for url in
                   re.findall(r"https://linear\.app/[^\s)<>]+/project/[^\s)<>]+", agents)})
    teams = sorted(set(re.findall(r"[Tt]eam:\s*\*\*([^*\n]+)\*\*", agents)))
    teams += re.findall(r"team \*\*([^*\n]+)\*\*, project", agents)
    manifests = [name for name in MANIFESTS if (root / name).is_file()]
    review = [line.strip()[:240] for line in (before + after).splitlines()
              if re.search(r"tracker|linear|github issues|backend|rust|tests?|worktree|merge|commit|CLI", line, re.I)]
    try:
        status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                                text=True, capture_output=True, timeout=5)
        dirty = len(status.stdout.splitlines()) if status.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        dirty = None
    return {
        "root": str(root), "name": state.get("name") or package.get("name") or root.name,
        "team": state.get("team") or (teams[0] if len(set(teams)) == 1 else None),
        "linear_project": state.get("linear_project") or (urls[0] if len(urls) == 1 else None),
        "linear_candidates": urls, "manifests": manifests, "git_changes": dirty,
        "routes": detect_routes(root), "review_instructions": review[:30],
        "review_truncated": len(review) > 30,
    }
