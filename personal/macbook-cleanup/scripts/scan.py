#!/usr/bin/env python3
"""Build the cached Rust scanner and write a private, read-only disk audit."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from datetime import datetime

from capacity import measure
from report import generate
from dashboard import export as export_dashboard


SKILL = Path(__file__).resolve().parents[1]


def build(cache):
    scanner = SKILL / "scanner"
    sources = [scanner / "Cargo.toml", scanner / "Cargo.lock", *sorted((scanner / "src").glob("*.rs"))]
    digest = hashlib.sha256(platform.machine().encode())
    for path in sources:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    signature = digest.hexdigest()
    cache.mkdir(parents=True, exist_ok=True)
    binary = cache / "target/release/macbook-scan"
    stamp = cache / "source.sha256"
    with (cache / "build.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not binary.exists() or not stamp.exists() or stamp.read_text() != signature:
            if not shutil.which("cargo"):
                raise RuntimeError("Rust is required for the first build. Install Rust with rustup.rs or Homebrew, then rerun this command.")
            print("Building release scanner (cached for subsequent runs)…", file=sys.stderr)
            subprocess.run(["cargo", "build", "--release", "--locked", "--manifest-path", str(scanner / "Cargo.toml"),
                            "--target-dir", str(cache / "target")], check=True, timeout=600)
            stamp.write_text(signature)
    return binary


def scanner_command(command, admin):
    """Use only an already authenticated administrator session for metadata scanning."""
    if not admin:
        return command
    subprocess.run(["/usr/bin/sudo", "-n", "true"], check=True, timeout=10)
    return ["/usr/bin/sudo", "-n", *command]


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=Path, help="Directory to scan; repeat for disjoint scopes. Default: macOS Data volume.")
    parser.add_argument("--volume", type=Path, default=Path("/System/Volumes/Data"), help="Volume for the capacity target.")
    parser.add_argument("--home", type=Path, default=Path.home(), help="User home for cleanup classification.")
    parser.add_argument("--exclude", action="append", type=Path, default=[], help="Skip an exact path and its descendants.")
    parser.add_argument("--target-percent", type=float, default=50, help="Desired physical container usage (default: 50).")
    parser.add_argument("--threads", type=int, default=8, help="Scanner workers, 1..64 (default: 8).")
    parser.add_argument("--top", type=int, default=50, help="Number of largest files/directories to retain.")
    parser.add_argument("--min-candidate-mib", type=int, default=100, help="Minimum cleanup candidate size (default: 100 MiB).")
    parser.add_argument("--timeout", type=int, default=600, help="Maximum scanner runtime in seconds; a timeout is a failed audit, not a complete report.")
    parser.add_argument("--cache-dir", type=Path, default=Path.home() / "Library/Caches/macbook-cleanup", help="Cached release build location.")
    parser.add_argument("--output", type=Path, help="New report folder (default: ./outputs/macbook-cleanup-TIMESTAMP).")
    parser.add_argument("--admin", action="store_true", help="Use existing sudo authentication for the read-only Rust scanner only. Start with access.py --admin for one Terminal password prompt.")
    args = parser.parse_args()
    if platform.system() != "Darwin":
        parser.error("This wrapper requires macOS. The Rust scanner can be tested separately on Unix.")
    if not 0 < args.target_percent <= 100 or not 1 <= args.threads <= 64 or args.top < 1 or args.min_candidate_mib < 0 or args.timeout < 1:
        parser.error("target must be 0..100 (exclusive of 0), threads 1..64, top/timeout positive, minimum nonnegative")
    return args


def main():
    args = arguments()
    output = (args.output or Path.cwd() / "outputs" / f"macbook-cleanup-{datetime.now():%Y%m%d-%H%M%S}").expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"Report folder must be empty; preserve previous audits: {output}")
    roots = [root.expanduser().absolute() for root in (args.root or [args.volume])]
    volume = args.volume.expanduser().resolve()
    volume_device = volume.stat().st_dev
    if any(root.stat().st_dev != volume_device for root in roots):
        raise RuntimeError("Every scan root must belong to the target volume. Audit external disks separately with --volume.")
    binary = build(args.cache_dir.expanduser().absolute())
    capacity_before = measure(volume, args.target_percent)
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    output.chmod(0o700)
    command = [str(binary), "--home", str(args.home.expanduser().absolute()), "--threads", str(args.threads),
               "--top", str(args.top), "--min-candidate-bytes", str(args.min_candidate_mib * 1024 * 1024)]
    for root in roots:
        command += ["--root", str(root)]
    for excluded in [*args.exclude, output]:
        command += ["--exclude", str(excluded.expanduser().resolve())]
    print(f"Scanning metadata with {args.threads} workers…", file=sys.stderr)
    command = scanner_command(command, args.admin)
    raw = subprocess.run(command, check=True, stdout=subprocess.PIPE, timeout=args.timeout).stdout
    scan = json.loads(raw)
    scan["capacity_before_scan"] = capacity_before
    scan["scope"] = "Data volume" if roots == [Path("/System/Volumes/Data")] else "Selected roots only"
    capacity = measure(volume, args.target_percent)
    (output / "scan.json").write_text(json.dumps(scan, indent=2) + "\n")
    paths = generate(scan, capacity, output)
    try:
        export_dashboard(json.loads(Path(paths["summary"]).read_text()), scan, paths["html"])
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Dashboard build unavailable: {error}. Opening the basic report still works.", file=sys.stderr)
    print(json.dumps({"output": str(output), "elapsed_seconds": scan["elapsed_seconds"],
                      "files": scan["files"], "coverage_errors": scan["error_count"],
                      "used_percent": capacity["used_percent"], "reclaim_needed_bytes": capacity["reclaim_needed_bytes"],
                      "reports": {name: str(path) for name, path in paths.items()}}, indent=2))


if __name__ == "__main__":
    # Restrict files containing private filenames, even with a permissive caller umask.
    os.umask(0o077)
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f"macbook-cleanup: {error}", file=sys.stderr)
        sys.exit(1)
