#!/usr/bin/env python3
"""Connect this checkout to the global skill folders without losing local files."""

import argparse
import filecmp
from pathlib import Path
import shutil


def same_tree(left, right):
    comparison = filecmp.dircmp(left, right, ignore=[".DS_Store", "__pycache__"])
    if comparison.left_only or comparison.right_only or comparison.common_funny:
        return False
    for name in comparison.common_files:
        if not filecmp.cmp(left / name, right / name, shallow=False):
            return False
    return all(same_tree(left / name, right / name) for name in comparison.common_dirs)


def exists(path):
    return path.exists() or path.is_symlink()


def link(path, target):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        if path.resolve() == target.resolve():
            return
        raise RuntimeError(f"Existing link points elsewhere: {path}")
    if exists(path):
        raise RuntimeError(f"Refusing to replace existing path: {path}")
    path.symlink_to(target, target_is_directory=True)


def plan(repo, home):
    personal, others = repo / "personal", repo / "others"
    canonical = home / ".agents/skills"
    codex = home / ".codex/skills"
    moves = []
    if canonical.is_symlink():
        if canonical.resolve() != others.resolve():
            raise RuntimeError(f"Existing global skills link points elsewhere: {canonical}")
    elif canonical.exists():
        if not canonical.is_dir():
            raise RuntimeError(f"Global skills path is not a directory: {canonical}")
        for source in canonical.iterdir():
            if source.name.startswith("."):
                continue
            if source.is_symlink():
                raise RuntimeError(f"Review existing canonical skill link first: {source}")
            if not source.is_dir():
                raise RuntimeError(f"Review unexpected global skill file first: {source}")
            dest = (personal if (personal / source.name).exists() else others) / source.name
            moves.append((source, dest, False))
    if codex.is_symlink():
        raise RuntimeError(f"Review existing Codex skills root link first: {codex}")
    if codex.exists():
        for source in codex.iterdir():
            if source.name.startswith(".") or source.name == "codex-primary-runtime":
                continue
            if source.is_symlink():
                continue
            if source.is_dir():
                dest = (personal if (personal / source.name).exists() else others) / source.name
                moves.append((source, dest, True))
    for source, dest, _ in moves:
        if exists(dest) and (not dest.is_dir() or not same_tree(source, dest)):
            raise RuntimeError(f"Conflicting skill copies; no changes made: {source} and {dest}")
    # Check collisions between the two incoming global roots before moving anything.
    pending = {}
    for source, dest, _ in moves:
        if dest in pending and not same_tree(source, pending[dest]):
            raise RuntimeError(f"Conflicting incoming skill copies: {source} and {pending[dest]}")
        pending[dest] = source
    for name, target in [("skillsies", repo), ("personal", personal)]:
        endpoint = codex / name
        if exists(endpoint) and (not endpoint.is_symlink() or endpoint.resolve() != target.resolve()):
            raise RuntimeError(f"Review existing discovery path first: {endpoint}")
    backup = repo / ".local/backups"
    for source, dest, keep_alias in moves:
        saved = backup / ("codex" if keep_alias else "agents") / source.name
        if exists(dest) and exists(saved):
            raise RuntimeError(f"Backup path already exists: {saved}")
    if canonical.exists() and not canonical.is_symlink() and exists(backup / "agents-root"):
        raise RuntimeError(f"Backup path already exists: {backup / 'agents-root'}")
    if canonical.is_symlink():
        for skill in personal.iterdir():
            if exists(others / skill.name):
                raise RuntimeError(f"Downloaded skill conflicts with personal skill: {skill.name}")
    return moves


def setup(repo, home):
    if not (repo / "personal").is_dir():
        raise RuntimeError(f"Missing personal skill folder: {repo}")
    moves = plan(repo, home)
    others, canonical = repo / "others", home / ".agents/skills"
    others.mkdir(exist_ok=True)
    # Keep original copies for recovery, outside Git and outside discovery roots.
    backup = repo / ".local/backups"
    for source, dest, keep_alias in moves:
        if exists(dest):
            saved = backup / ("codex" if keep_alias else "agents") / source.name
            if exists(saved):
                raise RuntimeError(f"Backup path already exists: {saved}")
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(saved))
        else:
            shutil.move(str(source), str(dest))
        if keep_alias:
            link(source, dest)
    if canonical.exists() and not canonical.is_symlink():
        saved = backup / "agents-root"
        if exists(saved):
            raise RuntimeError(f"Backup path already exists: {saved}")
        saved.parent.mkdir(parents=True, exist_ok=True)
        canonical.rename(saved)
    link(canonical, others)
    link(home / ".codex/skills/personal", repo / "personal")
    # Preserve the existing skillsies discovery link and install it on fresh machines.
    link(home / ".codex/skills/skillsies", repo)
    print(f"Personal: {repo / 'personal'}")
    print(f"Downloaded: {others}")
    print(f"Global download path: {canonical} -> {others}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home(), help="Agent home (for setup checks)")
    args = parser.parse_args()
    setup(Path(__file__).resolve().parent.parent, args.home.expanduser().resolve())


if __name__ == "__main__":
    main()
