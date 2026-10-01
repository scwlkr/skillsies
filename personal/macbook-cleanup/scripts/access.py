#!/usr/bin/env python3
"""Prepare a private Terminal launcher or show the macOS access status."""

import argparse
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parent
SETTINGS_URL = "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
ACCESS_STEPS = (
    "System Settings > Privacy & Security > Full Disk Access > enable Terminal. "
    "If Terminal is missing, add /System/Applications/Utilities/Terminal.app. "
    "Then quit Terminal completely (Command-Q), reopen it, and run the launcher again."
)


def access_status(home=None):
    """Probe metadata access, not private contents; this is not a complete TCC test."""
    home = Path(home or Path.home())
    blocked = []
    checked = []
    unavailable = []
    for relative in ("Library/Mail", "Library/Messages", "Library/Safari"):
        path = home / relative
        try:
            with os.scandir(path):
                pass
            checked.append(str(path))
        except FileNotFoundError:
            unavailable.append(str(path))
        except PermissionError:
            blocked.append(str(path))
        except OSError as error:
            unavailable.append(f"{path}: {error.strerror}")
    return {
        "status": "blocked" if blocked else "probe_passed" if checked else "unverified",
        "blocked": blocked,
        "checked": checked,
        "unavailable": unavailable,
        "note": "A metadata probe cannot guarantee full coverage. sudo does not grant Full Disk Access.",
        "next_step": ACCESS_STEPS if blocked else "The audit will report any remaining inaccessible paths.",
    }


def open_settings():
    subprocess.run(["/usr/bin/open", SETTINGS_URL], check=True, timeout=15)


def write_launcher(output, admin=False, python_executable=None, scripts_dir=None):
    output = Path(output).expanduser().absolute()
    if output.is_symlink():
        raise ValueError("Launcher output must not be a symlink")
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    output = output.resolve()
    output.chmod(0o700)
    scripts_dir = Path(scripts_dir or SCRIPTS).resolve()
    executable = Path(python_executable or sys.executable).resolve()
    command = [str(executable), str(scripts_dir / "launch_session.py"), "--output", str(output)]
    if admin:
        command.append("--admin")
    launcher = output / "macbook-cleanup.command"
    # Exclusive creation prevents following existing symlinks or replacing prior launchers.
    fd = os.open(launcher, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o700)
    with os.fdopen(fd, "w") as stream:
        stream.write("#!/bin/zsh\nset -eu\numask 077\nexec " + shlex.join(command) + "\n")
    return launcher


def launch_terminal(launcher):
    subprocess.run(["/usr/bin/open", "-a", "Terminal", str(launcher)], check=True, timeout=15)
    # Terminal does not expose native fullscreen in its scripting dictionary.
    # Using System Events would add an Accessibility gate to the access workflow.
    return "Terminal opened. Use Control-Command-F for fullscreen; automatic fullscreen is not guaranteed."


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Private launcher directory; audit goes in its audit/ child.")
    parser.add_argument("--admin", action="store_true", help="Ask sudo once inside Terminal for read-only scanning.")
    parser.add_argument("--launch", action="store_true", help="Open the generated launcher in Terminal.")
    parser.add_argument("--settings", action="store_true", help="Open Full Disk Access settings; only you can grant access.")
    parser.add_argument("--status", action="store_true", help="Print a read-only access probe as JSON.")
    args = parser.parse_args(argv)
    if platform.system() != "Darwin":
        parser.error("The Terminal access workflow requires macOS.")
    if not args.output and not args.settings and not args.status:
        parser.error("Provide --output, --settings, or --status.")
    if (args.launch or args.admin) and not args.output:
        parser.error("--launch and --admin require --output.")
    if args.settings:
        open_settings()
    result = {"access": access_status(), "setup": ACCESS_STEPS}
    if args.output:
        launcher = write_launcher(args.output, args.admin)
        result["launcher"] = str(launcher)
        result["audit"] = str(launcher.parent / "audit")
        result["terminal"] = launch_terminal(launcher) if args.launch else "Prepared; Terminal was not launched."
        result["dashboard"] = "Graphs and selection buttons open in a local browser dashboard; Terminal shows progress and results."
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    os.umask(0o077)
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"macbook-cleanup access: {error}", file=sys.stderr)
        sys.exit(1)
