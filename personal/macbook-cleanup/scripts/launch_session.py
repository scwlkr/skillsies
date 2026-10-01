#!/usr/bin/env python3
"""Run the Terminal audit, then keep its local review dashboard available."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from access import ACCESS_STEPS, SCRIPTS, access_status, open_settings


def display(value):
    """Prevent filenames or errors from injecting terminal escape sequences."""
    return json.dumps(str(value), ensure_ascii=False)[1:-1]


def banner():
    if sys.stdout.isatty():
        print("\033[2J\033[H\033[1;36mMACBOOK CLEANUP\033[0m")
    else:
        print("MACBOOK CLEANUP")
    print("Scan → choose items in your dashboard → confirm the exact final list")
    print("Control-Command-F makes Terminal fullscreen. Graphs open in your browser.\n")


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
    """Build both caches as the user before any sudo credential lifetime begins."""
    from scan import build as build_scanner
    from dashboard import build as build_dashboard

    print("Preparing cached scanner and dashboard…", flush=True)
    build_scanner(Path.home() / "Library/Caches/macbook-cleanup")
    build_dashboard()


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


def run_session(output, admin=False):
    output = Path(output).expanduser().resolve()
    report_dir = output / "audit"
    banner()
    access = access_status()
    if access["blocked"]:
        print("Protected directories could not be read. One-time setup:")
        print(ACCESS_STEPS)
        if sys.stdin.isatty():
            answer = input("Open Full Disk Access settings now? [y/N] ").strip().lower()
            if answer in ("y", "yes"):
                open_settings()
                print("After granting access, quit/reopen Terminal and run the same launcher again.")
                return 78
        print("Continuing with partial access; blocked paths will appear in the report.\n")
    if admin and not sys.stdin.isatty():
        raise RuntimeError("Administrator scanning needs an interactive Terminal for sudo authentication.")
    prepare_tools()
    if admin:
        print("Administrator password: read-only scan access. This does not approve deletion.")
        subprocess.run(["/usr/bin/sudo", "-v"], check=True)
    command = [sys.executable, str(SCRIPTS / "scan.py"), "--output", str(report_dir)]
    if admin:
        command.append("--admin")
    print("Scanning file metadata…", flush=True)
    with (output / "scan-result.json").open("x") as stream:
        subprocess.run(command, check=True, stdout=stream)
    print("\nAudit complete.")
    print_summary(report_dir)
    print("\nOpening dashboard. Choose items, then review and confirm the final deletion list.")
    print("This launcher has not deleted anything. Keep this Terminal open for the review session.\n", flush=True)
    subprocess.run([sys.executable, str(SCRIPTS / "review_server.py"),
                    "--report-dir", str(report_dir), "--wait"], check=True)
    print_cleanup_summary(report_dir)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--admin", action="store_true")
    args = parser.parse_args(argv)
    return run_session(args.output, args.admin)


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
