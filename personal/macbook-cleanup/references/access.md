# macOS access and Terminal workflow

Prepare a private, inspectable launcher:

```sh
python3 scripts/access.py --output /absolute/private/path/session
```

Add `--launch` to open that launcher in Terminal, and `--admin` only when a
read-only administrator scan is needed. The generated `.command` uses the
canonical Python executable and skill location, safely quoted as shell arguments.
Preparation alone does not scan, launch apps, grant permissions, or delete data.
Use a fresh session directory for each audit; its report lives under `audit/`.

## One-time Full Disk Access

macOS requires the person using the Mac to grant Full Disk Access:

1. Open **System Settings → Privacy & Security → Full Disk Access**.
2. Enable **Terminal**. If missing, add
   `/System/Applications/Utilities/Terminal.app` with the **+** button.
3. Quit Terminal completely with **Command-Q**, then reopen it.
4. Run the prepared `macbook-cleanup.command` again.

`python3 scripts/access.py --settings` opens the relevant Settings pane. If the
system does not honor that deep link, follow the navigation above. `--status`
prints a read-only metadata probe without opening Settings or Terminal.

The probe checks existing Mail, Messages, and Safari directories. It is useful
for detecting blocked access, but it cannot certify Full Disk Access or complete
filesystem coverage. Missing directories produce **unverified** rather than a
false approval. The final audit remains authoritative about inaccessible paths.

The launcher offers to open Settings when it detects blocked directories. If
accepted, it stops before scanning so Terminal can be quit and relaunched. If
declined or running noninteractively, it reports partial access and continues.
It never edits the TCC database, disables SIP, or changes directory permissions.

The launcher builds its cached Rust scanner and dashboard as the normal user
before requesting a password, so first-build work does not consume the sudo
authentication window. Optional `--admin` asks for `sudo -v` inside the
interactive Terminal once;
`scan.py --admin` elevates only its read-only scanner. Administrator access can
resolve Unix permissions, but does not grant Full Disk Access. Some system paths
remain protected even with both permissions. A password prompt is not deletion
approval. Review and cleanup run as the normal user, without blanket sudo.

## Terminal presentation and dashboard

Terminal owns the scan banner, progress, capacity summary, and coverage status.
The actual shadcn components, charts, selection buttons, and final confirmation
run in a separate local browser dashboard; native Terminal cannot render a web UI.
The launcher starts `review_server.py --report-dir ... --wait` after a successful
audit and keeps the session attached until review ends. After final review,
Terminal prints measured usage, used-space reduction, the remaining target gap,
and each approved item's deletion or recovery outcome from
`cleanup-results.json`. Preview sessions explicitly say nothing was deleted.

**Control-Command-F** switches Terminal to fullscreen. Opening Terminal does not
guarantee fullscreen: its native scripting dictionary exposes zoom and bounds,
but no fullscreen property. Automating its green button through System Events
would require an additional Accessibility permission. This workflow avoids that
extra gate and leaves the supported keyboard shortcut visible in the banner.
No third-party terminal emulator or extra UI permission is needed.

Selecting an item only drafts a cleanup list. The final confirmation must name
the exact items to delete. The model uses that confirmed list and reports each
outcome; initial scan authorization and access setup never authorize deletion.

## Sources

- [Apple: Privacy & Security settings](https://support.apple.com/guide/mac-help/mchl211c911f/mac)
  describes Full Disk Access and adding an app.
- [Apple: Controlling app access to files](https://support.apple.com/guide/security/secddd1d86a6/web)
  describes macOS consent and protected locations.
- [Apple Developer: Accessing files from the macOS App Sandbox](https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox)
  explains that an app cannot grant itself Full Disk Access through code.
- Terminal's installed native scripting dictionary can be inspected with
  `/usr/bin/sdef /System/Applications/Utilities/Terminal.app`.
