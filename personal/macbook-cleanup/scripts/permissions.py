"""Request native macOS access from the user's interactive Terminal session."""
import subprocess
import sys

from access import ACCESS_STEPS, access_status, open_settings


def request_access(admin=False):
    if not sys.stdin.isatty():
        raise RuntimeError("Start the launcher in an interactive Terminal to approve access.")
    status = access_status()
    if status["blocked"]:
        print("\nFULL DISK ACCESS REQUIRED FOR PROTECTED USER FOLDERS")
        print(ACCESS_STEPS)
        print("macOS requires this Settings toggle. A Terminal password cannot grant it.")
        choice = input("[s] Open Settings  [c] Scan with partial access  [q] Quit: ").strip().lower()
        if choice in ("s", "y", "yes"):
            open_settings()
            print("Enable Terminal, quit/reopen Terminal, then run this same .command file again.")
            return False
        if choice != "c":
            return False
        print("Continuing with partial access; the report will identify remaining gaps.")
    if admin:
        print("\nADMINISTRATOR ACCESS")
        print("Enter your Mac password at sudo's prompt (typing is hidden).")
        print("This grants read-only scanner access. Deletion requires its own exact final list.")
        subprocess.run(["/usr/bin/sudo", "-v"], check=True)
    return True
