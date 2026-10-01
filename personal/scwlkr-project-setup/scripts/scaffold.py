"""Plan every write before applying; preserve edits to previously generated files."""

import hashlib
import json
import re
from pathlib import Path

from inventory import STATE, block_parts, inspect, metadata, read

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def safe(root, relative):
    path = root / relative
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"Refusing to write through symlink: {relative}")
    if path.exists() and not path.is_file():
        raise ValueError(f"Expected file: {relative}")
    return path


def rust_string(text):
    return '"' + "".join(
        "\\" + char if char in '\\"' else f"\\u{{{ord(char):x}}}" if ord(char) < 32 else char
        for char in text
    ) + '"'


def routes_source(routes):
    lines = ["use crate::Route;", "", "#[rustfmt::skip]", "pub const ROUTES: &[Route] = &["]
    for route in routes:
        args = ", ".join(rust_string(arg) for arg in route["args"])
        lines.append("    Route { name: %s, program: %s, args: &[%s] }," % (
            rust_string(route["name"]), rust_string(route["program"]), args))
    return "\n".join([*lines, "];", ""])


def apply(root, args):
    info = inspect(root)
    old = metadata(root)
    config = {key: getattr(args, key, None) or info.get(key)
              for key in ("name", "team", "linear_project")}
    missing = [key for key, value in config.items() if not value]
    if missing:
        raise ValueError("Missing " + ", ".join(missing) + "; resolve from prompt/project/Linear, then pass flags")
    if any("\n" in value or "\r" in value for value in config.values()):
        raise ValueError("Setup values must be single-line strings")
    if not re.fullmatch(r"https://linear\.app/[\w-]+/project/[\w-]+(?:/overview)?", config["linear_project"]):
        raise ValueError("--linear-project must be a Linear project URL")
    writes, preserved = {}, []
    hashes = dict(old.get("hashes", {}))

    def put(relative, content):
        safe(root, relative)
        if read(root, relative) != content:
            writes[relative] = content

    def generated(relative, content):
        path = safe(root, relative)
        if path.exists():
            current = read(root, relative)
            if current != content:
                if relative not in hashes:
                    raise ValueError(f"Unowned path collision: {relative}; reconcile before applying")
                if digest(current) != hashes[relative]:
                    preserved.append(relative)
                    return
        put(relative, content)
        hashes[relative] = digest(content)

    for source in sorted((ASSETS / "cli").rglob("*")):
        if source.is_file():
            generated("tools/project-cli/" + source.relative_to(ASSETS / "cli").as_posix(), source.read_text())
    generated("project", (ASSETS / "project").read_text())
    generated("tools/project-cli/src/routes.rs", routes_source(info["routes"]))
    agents = read(root, "AGENTS.md")
    before, block, after = block_parts(agents)
    desired = (ASSETS / "AGENTS.md").read_text().format(**config).strip()
    if block and block != desired and digest(block) != hashes.get("agent_block"):
        if any(config[key] != old.get(key) for key in config):
            raise ValueError("Custom setup block conflicts with changed metadata; reconcile AGENTS.md first")
        preserved.append("AGENTS.md setup block")
    else:
        content = before + desired + after if block else agents.rstrip() + ("\n\n" if agents else "") + desired + "\n"
        put("AGENTS.md", content)
        hashes["agent_block"] = digest(desired)
    if not (root / "README.md").exists():
        put("README.md", f"# {config['name']}\n\nA project by wlkrlabs.\n")
    ignored = read(root, ".gitignore")
    ignore = "/tools/project-cli/target/"
    if ignore not in ignored.splitlines():
        put(".gitignore", ignored + ("\n" if ignored and not ignored.endswith("\n") else "") + ignore + "\n")
    if not info["routes"] and not (root / "SETUP-TODO.md").exists():
        put("SETUP-TODO.md", "# Setup handoff\n\n- [ ] Wire real app commands into `tools/project-cli/src/routes.rs`; exercise one real feature through `./project` and capture its result.\n")
    state = {"version": 1, **config, "hashes": hashes}
    put(STATE, json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    # Preflight above prevents collisions or missing configuration from causing partial setup.
    for relative, content in writes.items():
        path = safe(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    launcher = safe(root, "project")
    if not launcher.stat().st_mode & 0o111:
        launcher.chmod(launcher.stat().st_mode | 0o111)
        if "project" not in writes:
            writes["project"] = ""
    return {"changed": list(writes), "preserved": preserved,
            "next": "Review AGENTS.md conflicts; run setup.py check", "app_routes": len(info["routes"])}
