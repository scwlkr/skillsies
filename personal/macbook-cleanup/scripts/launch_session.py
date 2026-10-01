#!/usr/bin/env python3
"""Run the Terminal audit, then select and confirm cleanup entirely in Terminal."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime
import secrets

from access import SCRIPTS
from permissions import request_access
from cleanup_plan import private_json


def display(value):
    """Prevent filenames or errors from injecting terminal escape sequences."""
    return json.dumps(str(value), ensure_ascii=False)[1:-1]


def banner():
    if sys.stdout.isatty():
        print("\033[2J\033[H\033[1;36mMACBOOK CLEANUP\033[0m")
    else:
        print("MACBOOK CLEANUP")
    print("Scan → choose items here in Terminal → confirm the exact final list")
    print("Arrows move · Space selects · Enter reviews · DELETE confirms · q exits.\n")
    print("Control-Command-F makes this Terminal window full screen.\n")


def print_summary(report_dir):
    summary = json.loads((report_dir / "summary.json").read_text())
    capacity = summary.get("capacity", {})
    percent = capacity.get("used_percent", summary.get("used_percent"))
    if isinstance(percent, (int, float)):
        print(f"Storage used: {percent:.1f}%   Goal: 50%")
    needed = capacity.get("reclaim_needed_bytes", summary.get("reclaim_needed_bytes"))
    if isinstance(needed, (int, float)):
        print(f"Space needed: {needed / 1024 ** 3:.1f} GiB")
    errors = summary.get("coverage", {}).get("error_count", 0)
    print(f"Coverage: {errors} inaccessible paths" if errors else "Coverage: no scan errors reported")
    print(f"Private report: {display(report_dir / 'report.html')}")
    if errors:
        print("Full Disk Access and sudo cannot guarantee access to every protected system path.")


def prepare_tools():
    """Build the scanner as the user before any sudo credential lifetime begins."""
    from scan import build as build_scanner

    print("Preparing cached Rust scanner…", flush=True)
    build_scanner(Path.home() / "Library/Caches/macbook-cleanup")


def print_cleanup_summary(report_dir):
    path = report_dir / "cleanup-results.json"
    if not path.is_file():
        print("Review session ended without a saved cleanup result.")
        return
    results = json.loads(path.read_text())
    print(f"\nCleanup: {display(results.get('state', 'unknown'))}")
    if results.get("preview"):
        print("Preview only: nothing deleted.")
    capacity = results.get("capacity_after", {})
    percent = capacity.get("used_percent")
    if isinstance(percent, (int, float)):
        print(f"Measured storage now: {percent:.1f}% used")
    before = json.loads((report_dir / "summary.json").read_text()).get("capacity", {})
    used_before, used_after = before.get("used_bytes"), capacity.get("used_bytes")
    if all(isinstance(value, (int, float)) for value in (used_before, used_after)):
        recovered = used_before - used_after
        print(f"Measured used-space reduction: {recovered / 1024 ** 3:.2f} GiB")
        print("Volume changes from other apps and APFS can affect this measurement.")
    needed = capacity.get("reclaim_needed_bytes")
    if isinstance(needed, (int, float)):
        print(f"Remaining gap to goal: {needed / 1024 ** 3:.2f} GiB")
    for field in ("error", "capacity_error"):
        if results.get(field):
            print(f"{field}: {display(results[field])}")
    for row in results.get("results", []):
        text = f"  {display(row.get('status', 'unknown'))}: {display(row.get('path', row.get('id', 'item')))}"
        if row.get("message"):
            text += f" — {display(row['message'])}"
        print(text)
    for entry in results.get("staging", []):
        if entry.get("state") == "recovery_required":
            print(f"Recovery required: {display(entry.get('staged_path', 'see cleanup-results.json'))}")
    print(f"Saved outcomes: {display(path)}")


def start_review(report_dir, preview=False):
    from terminal_review import run_review
    return run_review(report_dir, preview)


def session_state(output, stage, **details):
    try:
        terminal = os.ttyname(sys.stdin.fileno()) if sys.stdin.isatty() else None
    except (OSError, ValueError):
        terminal = None
    private_json(Path(output) / "session-state.json", {
        "stage": stage, "pid": os.getpid(), "updated_at": datetime.now().astimezone().isoformat(),
        "terminal": terminal, **details,
    })


def run_session(output, admin=False, report_dir=None, preview=False):
    output = Path(output).expanduser().resolve()
    existing = report_dir is not None
    report_dir = Path(report_dir).expanduser().resolve() if existing else output / "audit"
    if not existing and report_dir.exists() and any(report_dir.iterdir()):
        report_dir = output / f"audit-{datetime.now():%Y%m%d-%H%M%S}-{secrets.token_hex(3)}"
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    output.chmod(0o700)
    banner()
    if not sys.stdin.isatty():
        raise RuntimeError("Administrator scanning and cleanup need an interactive Terminal.")
    session_state(output, "started", report_dir=str(report_dir))
    if not existing:
        session_state(output, "preparing_scanner")
        prepare_tools()
        session_state(output, "awaiting_access", admin=admin)
        if not request_access(admin):
            session_state(output, "access_setup_or_cancelled")
            return 78
        command = [sys.executable, str(SCRIPTS / "scan.py"), "--output", str(report_dir), "--no-dashboard"]
        if admin:
            command.append("--admin")
        print("Scanning all file metadata on the Data volume…", flush=True)
        session_state(output, "scanning", report_dir=str(report_dir))
        with (output / f"scan-result-{report_dir.name}.json").open("x") as stream:
            subprocess.run(command, check=True, stdout=stream)
        print("\nAudit complete.")
    elif admin:
        session_state(output, "awaiting_access", admin=admin)
        if not request_access(admin):
            session_state(output, "access_setup_or_cancelled")
            return 78
    print_summary(report_dir)
    print("\nStarting Terminal selection. Nothing is deleted until you type DELETE for the final list.", flush=True)
    session_state(output, "reviewing", report_dir=str(report_dir))
    result = start_review(report_dir, preview)
    session_state(output, result.get("state", "finished") if result else "cancelled")
    if result and result.get("exit_code"):
        if result.get("state") == "access_setup":
            print("Enable Terminal in Full Disk Access, quit/reopen Terminal, then rerun this launcher.")
        return result["exit_code"]
    if result:
        print_cleanup_summary(report_dir)
    else:
        print("Review cancelled. Nothing deleted.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--admin", action="store_true")
    parser.add_argument("--report-dir", type=Path, help="Review an existing audit in Terminal; no rescan.")
    parser.add_argument("--preview", action="store_true", help="Test selection and approval without deletion.")
    args = parser.parse_args(argv)
    try:
        return run_session(args.output, args.admin, args.report_dir, args.preview)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        if args.output.is_dir():
            session_state(args.output, "error", error=str(error))
        raise


if __name__ == "__main__":
    os.umask(0o077)
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nSession interrupted. Scan/review artifacts are preserved.", file=sys.stderr)
        sys.exit(130)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"macbook-cleanup: {display(error)}", file=sys.stderr)
        sys.exit(1)
