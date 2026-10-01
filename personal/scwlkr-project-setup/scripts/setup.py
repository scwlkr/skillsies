#!/usr/bin/env python3
"""Inspect, apply or verify basic project setup; Python standard library only."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from inventory import block_parts, inspect, metadata, read
from instructions import command_conflicts
from scaffold import apply
from ci import inspect_ci


def check(root):
    state = metadata(root)
    missing = [path for path in ("AGENTS.md", "project", "tools/project-cli/Cargo.toml",
                                "tools/project-cli/src/main.rs", "tools/project-cli/src/routes.rs")
               if not (root / path).is_file()]
    if missing or not state:
        return {"ready": False, "missing": missing or ["tools/project-cli/setup.json"]}
    agents = read(root, "AGENTS.md")
    _, block, _ = block_parts(agents)
    missing = [key for key in ("team", "linear_project")
               if not state.get(key) or state[key] not in block]
    conflicts = command_conflicts(agents)
    if conflicts:
        return {"ready": False, "missing": missing, "command_conflicts": conflicts,
                "next": "Route examples through ./project; raw calls belong only under CLI bootstrap/repair headings"}
    results = {}
    for name, args in (("help", ["--help"]), ("doctor", ["doctor"])):
        try:
            process = subprocess.run([str(root / "project"), *args], cwd=root,
                                     text=True, capture_output=True, timeout=60,
                                     env={**os.environ, "RUSTUP_AUTO_INSTALL": "0"})
            results[name] = {"exit": process.returncode,
                             "output": (process.stdout + process.stderr).strip()[-4000:]}
        except (OSError, subprocess.TimeoutExpired) as error:
            results[name] = {"exit": 1, "output": str(error)}
            break
    ready = not missing and all(value["exit"] == 0 for value in results.values())
    return {"ready": ready, "missing": missing, "checks": results,
            "ci_alignment": inspect_ci(root)["alignment"],
            "scope": "CLI scaffold and prerequisites; app behavior remains separately verified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inspect", "apply", "check"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--name")
    parser.add_argument("--team")
    parser.add_argument("--linear-project")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    try:
        if root.exists() and not root.is_dir():
            raise ValueError("Project root must be a directory")
        if args.action == "inspect":
            result = inspect(root)
        elif args.action == "apply":
            result = apply(root, args)
        else:
            result = check(root)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 1 if result.get("ready") is False else 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
