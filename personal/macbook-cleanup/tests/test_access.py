import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import access
import launch_session


class AccessTests(unittest.TestCase):
    def test_launcher_is_private_and_quotes_hostile_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "spaces ' $(touch PWNED) ; & `cmd`"
            scripts = Path(temp) / "skill ' folder"
            executable = Path(temp) / "python ' executable"
            launcher = access.write_launcher(output, True, executable, scripts)
            body = launcher.read_text()
            command = shlex.split(body.split("exec ", 1)[1])
            self.assertEqual(command, [str(executable.resolve()), str(scripts.resolve() / "launch_session.py"),
                                       "--output", str(output.resolve()), "--admin"])
            self.assertEqual(stat.S_IMODE(launcher.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
            subprocess.run(["/bin/zsh", "-n", str(launcher)], check=True)
            self.assertFalse((Path(temp) / "PWNED").exists())

    def test_launcher_executes_literal_arguments_without_shell_expansion(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "spaces ' $(touch PWNED) ; & `cmd`"
            scripts = Path(temp) / "skill ' ; $(touch PWNED)"
            scripts.mkdir()
            (scripts / "launch_session.py").write_text(
                "import json, sys\nfrom pathlib import Path\n"
                "(Path(sys.argv[2]) / 'argv.json').write_text(json.dumps(sys.argv[1:]))\n")
            launcher = access.write_launcher(output, True, sys.executable, scripts)
            subprocess.run(["/bin/zsh", str(launcher)], cwd=temp, check=True)
            self.assertEqual(json.loads((output / "argv.json").read_text()),
                             ["--output", str(output.resolve()), "--admin"])
            self.assertFalse((Path(temp) / "PWNED").exists())

    def test_launcher_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            launcher = output / "macbook-cleanup.command"
            launcher.write_text("owner content")
            with self.assertRaises(FileExistsError):
                access.write_launcher(output)
            self.assertEqual(launcher.read_text(), "owner content")

    def test_launcher_does_not_follow_output_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "link"
            output.symlink_to(Path(temp), target_is_directory=True)
            with self.assertRaises(ValueError):
                access.write_launcher(output)

    def test_launcher_does_not_follow_existing_command_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            protected = output / "owner.txt"
            protected.write_text("owner content")
            (output / "macbook-cleanup.command").symlink_to(protected)
            with self.assertRaises(FileExistsError):
                access.write_launcher(output)
            self.assertEqual(protected.read_text(), "owner content")

    def test_probe_reports_permission_denied_without_reading_contents(self):
        with patch.object(access.os, "scandir", side_effect=PermissionError):
            result = access.access_status(Path("/Users/owner"))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(len(result["blocked"]), 3)
        self.assertIn("sudo does not grant", result["note"])
        self.assertIn("quit Terminal", result["next_step"])

    def test_probe_absent_paths_are_unverified(self):
        with patch.object(access.os, "scandir", side_effect=FileNotFoundError):
            result = access.access_status(Path("/Users/owner"))
        self.assertEqual(result["status"], "unverified")
        self.assertFalse(result["blocked"])

    def test_probe_metadata_success_is_not_complete_coverage_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "Library/Mail").mkdir(parents=True)
            result = access.access_status(Path(temp))
        self.assertEqual(result["status"], "probe_passed")
        self.assertIn("cannot guarantee", result["note"])

    def test_terminal_and_settings_use_argument_lists(self):
        hostile = Path("/tmp/a ' ; $(anything)/macbook-cleanup.command")
        with patch.object(access.subprocess, "run") as run:
            message = access.launch_terminal(hostile)
            access.open_settings()
        self.assertEqual(run.call_args_list[0].args[0], ["/usr/bin/open", "-a", "Terminal", str(hostile)])
        self.assertEqual(run.call_args_list[1].args[0], ["/usr/bin/open", access.SETTINGS_URL])
        self.assertIn("not guaranteed", message)
        self.assertTrue(all("shell" not in call.kwargs for call in run.call_args_list))

    def test_status_cli_is_read_only_and_noninteractive(self):
        with patch.object(access.platform, "system", return_value="Darwin"), \
                patch.object(access, "access_status", return_value={"status": "unverified"}), \
                patch.object(access.subprocess, "run") as run, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(access.main(["--status"]), 0)
        self.assertEqual(json.loads(output.getvalue())["access"]["status"], "unverified")
        run.assert_not_called()

    def test_prepare_cli_does_not_launch_or_scan(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(access.platform, "system", return_value="Darwin"), \
                patch.object(access, "access_status", return_value={"status": "unverified"}), \
                patch.object(access.subprocess, "run") as run, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(access.main(["--output", temp]), 0)
            result = json.loads(output.getvalue())
            self.assertTrue(Path(result["launcher"]).exists())
            self.assertFalse(Path(result["audit"]).exists())
        run.assert_not_called()


class SessionTests(unittest.TestCase):
    def test_escape_terminal_sequences_and_newlines(self):
        value = launch_session.display("/path/\x1b[31m\nname")
        self.assertNotIn("\x1b", value)
        self.assertNotIn("\n", value)
        self.assertIn("\\u001b", value)

    def test_admin_refuses_noninteractive_authentication(self):
        with patch.object(launch_session, "access_status", return_value={"blocked": []}), \
                patch.object(launch_session.sys.stdin, "isatty", return_value=False), \
                patch.object(launch_session.subprocess, "run") as run, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "interactive Terminal"):
                launch_session.run_session(Path("/tmp"), admin=True)
        run.assert_not_called()

    def test_settings_handoff_stops_before_scan(self):
        with patch.object(launch_session, "access_status", return_value={"blocked": ["Mail"]}), \
                patch.object(launch_session.sys.stdin, "isatty", return_value=True), \
                patch("builtins.input", return_value="yes"), \
                patch.object(launch_session, "open_settings") as settings, \
                patch.object(launch_session.subprocess, "run") as run, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(launch_session.run_session(Path("/tmp")), 78)
        settings.assert_called_once()
        run.assert_not_called()

    def test_session_authenticates_once_and_runs_review_unprivileged(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(launch_session, "access_status", return_value={"blocked": []}), \
                patch.object(launch_session.sys.stdin, "isatty", return_value=True), \
                patch.object(launch_session, "print_summary"), \
                patch.object(launch_session, "print_cleanup_summary") as final_summary, \
                patch.object(launch_session, "prepare_tools") as prepare, \
                patch.object(launch_session.subprocess, "run") as run, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(launch_session.run_session(Path(temp), admin=True), 0)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0], ["/usr/bin/sudo", "-v"])
        self.assertIn("--admin", commands[1])
        self.assertIn("--wait", commands[2])
        self.assertNotIn("sudo", " ".join(commands[2]))
        self.assertEqual(len(commands), 3)
        prepare.assert_called_once()
        final_summary.assert_called_once_with(Path(temp).resolve() / "audit")

    def test_scan_failure_never_starts_review(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(launch_session, "access_status", return_value={"blocked": []}), \
                patch.object(launch_session, "prepare_tools"), \
                patch.object(launch_session.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "scan")) as run, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(subprocess.CalledProcessError):
                launch_session.run_session(Path(temp))
        self.assertEqual(run.call_count, 1)

    def test_prebuild_runs_scanner_and_dashboard_as_user(self):
        with patch("scan.build") as scanner, patch("dashboard.build") as dashboard, \
                patch.object(launch_session.subprocess, "run") as run, \
                contextlib.redirect_stdout(io.StringIO()):
            launch_session.prepare_tools()
        scanner.assert_called_once_with(Path.home() / "Library/Caches/macbook-cleanup")
        dashboard.assert_called_once_with()
        run.assert_not_called()

    def test_prebuild_finishes_before_sudo_authentication(self):
        events = []
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(launch_session, "access_status", return_value={"blocked": []}), \
                patch.object(launch_session.sys.stdin, "isatty", return_value=True), \
                patch.object(launch_session, "print_summary"), \
                patch.object(launch_session, "print_cleanup_summary"), \
                patch.object(launch_session, "prepare_tools", side_effect=lambda: events.append("build")), \
                patch.object(launch_session.subprocess, "run", side_effect=lambda command, **kwargs: events.append(command)), \
                contextlib.redirect_stdout(io.StringIO()):
            launch_session.run_session(Path(temp), admin=True)
        self.assertEqual(events[0], "build")
        self.assertEqual(events[1], ["/usr/bin/sudo", "-v"])

    def test_build_failure_never_authenticates_or_scans(self):
        with patch.object(launch_session, "access_status", return_value={"blocked": []}), \
                patch.object(launch_session.sys.stdin, "isatty", return_value=True), \
                patch.object(launch_session, "prepare_tools", side_effect=RuntimeError("build failed")), \
                patch.object(launch_session.subprocess, "run") as run, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "build failed"):
                launch_session.run_session(Path("/tmp"), admin=True)
        run.assert_not_called()

    def test_final_summary_reports_measurement_recovery_and_safe_item_outcomes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / "summary.json").write_text(json.dumps({"capacity": {"used_bytes": 80 * 1024**3}}))
            (path / "cleanup-results.json").write_text(json.dumps({
                "state": "error", "capacity_after": {"used_percent": 75, "used_bytes": 75 * 1024**3,
                                                        "reclaim_needed_bytes": 25 * 1024**3},
                "results": [{"status": "deleted", "path": "/path/\x1b[31m\nname"},
                            {"status": "recovery_required", "path": "/path/staged", "message": "Original exists"}],
                "staging": [{"state": "recovery_required", "staged_path": "/path/staged"}]}))
            with contextlib.redirect_stdout(io.StringIO()) as output:
                launch_session.print_cleanup_summary(path)
        text = output.getvalue()
        self.assertIn("75.0%", text)
        self.assertIn("reduction: 5.00 GiB", text)
        self.assertIn("goal: 25.00 GiB", text)
        self.assertIn("Recovery required: /path/staged", text)
        self.assertIn("deleted:", text)
        self.assertNotIn("\x1b", text)
        self.assertIn("\\u001b", text)

    def test_preview_does_not_claim_measured_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / "summary.json").write_text(json.dumps({"capacity": {"used_bytes": 100}}))
            (path / "cleanup-results.json").write_text(json.dumps({"state": "preview", "preview": True,
                "results": [{"status": "preview_only", "path": "/path/item"}]}))
            with contextlib.redirect_stdout(io.StringIO()) as output:
                launch_session.print_cleanup_summary(path)
        self.assertIn("nothing deleted", output.getvalue())
        self.assertNotIn("Measured", output.getvalue())

    def test_terminal_summary_includes_capacity_and_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / "summary.json").write_text(json.dumps({
                "capacity": {"used_percent": 80, "reclaim_needed_bytes": 5 * 1024**3},
                "coverage": {"error_count": 10}}))
            with contextlib.redirect_stdout(io.StringIO()) as output:
                launch_session.print_summary(path)
        text = output.getvalue()
        self.assertIn("80.0%", text)
        self.assertIn("5.0 GiB", text)
        self.assertIn("10 inaccessible paths", text)
        self.assertIn("cannot guarantee", text)


if __name__ == "__main__":
    unittest.main()
