"""Safety and consent checks use only temporary directories, never user data."""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import cleanup_plan
from cleanup_execute import execute
from cleanup_items import build_items
from cleanup_plan import SafetyError, create_plan, validate_confirmation


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name).resolve()
        self.report = self.home / "report"
        self.report.mkdir()
        self.project = self.home / "dev/project"
        self.project.mkdir(parents=True)
        (self.project / "Cargo.toml").write_text('[package]\nname="fixture"\n')
        self.target = self.project / "target"
        self.target.mkdir()
        (self.target / "artifact").write_bytes(b"fixture data" * 512)
        self.unselected = self.home / "keep.txt"
        self.unselected.write_text("keep me")
        self.active = patch("cleanup_plan.check_active")
        self.active.start()
        self.execution_active = patch("cleanup_execute.check_active")
        self.execution_active.start()
        self.addCleanup(self.active.stop)
        self.addCleanup(self.execution_active.stop)
        self.addCleanup(self.temp.cleanup)

    def items(self, path=None):
        return build_items({"candidates": [{"path": str(path or self.target),
                            "allocated_bytes": 4096, "category": "build"}]}, {}, self.home)

    def plan(self):
        items = self.items()
        return create_plan([items[0]["id"]], items, self.home)

    def consent(self, plan):
        return {"plan_id": plan["id"], "digest": plan["digest"], "confirmed": True}

    def run_plan(self, plan, preview=False):
        with patch("cleanup_execute.measure", return_value={"used_percent": 40}):
            return execute(plan, self.consent(plan), self.report, self.home, preview)

    def test_plan_does_not_delete_and_exact_consent_is_required(self):
        plan = self.plan()
        self.assertTrue(self.target.exists())
        for payload in ({"confirmed": True}, dict(self.consent(plan), digest="wrong"),
                        dict(self.consent(plan), confirmed="true")):
            with self.assertRaises(SafetyError):
                execute(plan, payload, self.report, self.home)
        self.assertTrue(self.target.exists())
        self.assertFalse((self.report / "approved-plan.json").exists())

    def test_execute_deletes_only_selected_fixture_and_measures_after(self):
        plan = self.plan()
        result = self.run_plan(plan)
        self.assertEqual(result["state"], "complete")
        self.assertFalse(self.target.exists())
        self.assertEqual(self.unselected.read_text(), "keep me")
        self.assertEqual(result["capacity_after"]["used_percent"], 40)
        self.assertTrue((self.project / "Cargo.toml").exists())

    def test_preview_never_deletes(self):
        plan = self.plan()
        result = self.run_plan(plan, preview=True)
        self.assertEqual(result["state"], "preview")
        self.assertEqual(result["results"][0]["status"], "preview_only")
        self.assertTrue(self.target.exists())

    def test_replay_and_expired_consent_refused(self):
        plan = self.plan()
        self.run_plan(plan, True)
        with self.assertRaises(SafetyError):
            self.run_plan(plan)
        plan = self.plan()
        plan["expires_at"] = time.time() - 1
        with self.assertRaises(SafetyError):
            validate_confirmation(plan, self.consent(plan))

    def test_unknown_duplicate_and_client_path_selection_refused(self):
        items = self.items()
        for ids in ([str(self.target)], ["unknown"], [items[0]["id"]] * 2, [False], []):
            with self.assertRaises(SafetyError):
                create_plan(ids, items, self.home)

    def test_overlapping_selected_roots_refused(self):
        inner = self.target / "project/target"
        inner.mkdir(parents=True)
        (inner.parent / "Cargo.toml").write_text("nested manifest")
        rows = self.items() + self.items(inner)
        with self.assertRaises(SafetyError):
            create_plan([row["id"] for row in rows], rows, self.home)
        self.assertTrue(inner.exists())

    def test_changed_tree_blocks_whole_batch_before_deletion(self):
        plan = self.plan()
        (self.target / "new-file").write_text("new work")
        result = self.run_plan(plan)
        self.assertEqual(result["state"], "error")
        self.assertTrue((self.target / "new-file").exists())
        self.assertTrue(self.target.exists())

    def test_changed_root_identity_refused(self):
        plan = self.plan()
        self.target.rename(self.target.with_name("old-target"))
        self.target.mkdir()
        (self.target / "artifact").write_text("replacement")
        self.assertEqual(self.run_plan(plan)["state"], "error")
        self.assertTrue(self.target.exists())

    def test_changed_installer_with_restored_size_and_mtime_refused(self):
        downloads = self.home / "Downloads"
        downloads.mkdir()
        installer = downloads / "fixture.zip"
        installer.write_bytes(b"first")
        items = self.items(installer)
        plan = create_plan([items[0]["id"]], items, self.home)
        before = installer.stat()
        installer.write_bytes(b"other")
        os.utime(installer, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(self.run_plan(plan)["state"], "error")
        self.assertTrue(installer.exists())

    def test_manifest_changes_refused(self):
        plan = self.plan()
        (self.project / "Cargo.toml").write_text("new manifest")
        self.assertEqual(self.run_plan(plan)["state"], "error")
        self.assertTrue(self.target.exists())

    def test_symlink_outside_and_hardlinks_refused(self):
        (self.target / "escape").symlink_to(self.unselected)
        plan = self.plan()
        self.assertTrue(plan["blocked"])
        with self.assertRaises(SafetyError):
            self.run_plan(plan)
        (self.target / "escape").unlink()
        os.link(self.unselected, self.target / "hardlink")
        self.assertTrue(self.plan()["blocked"])
        self.assertEqual(self.unselected.read_text(), "keep me")

    def test_internal_node_modules_symlinks_delete_link_without_following(self):
        project = self.home / "npm-project"
        project.mkdir()
        (project / "package.json").write_text('{"name":"fixture"}')
        modules = project / "node_modules"
        (modules / ".bin").mkdir(parents=True)
        (modules / "package").mkdir()
        (modules / "package/tool").write_text("regenerable tool")
        (modules / ".bin/tool").symlink_to("../package/tool")
        rows = self.items(modules)
        plan = create_plan([rows[0]["id"]], rows, self.home)
        self.assertFalse(plan["blocked"])
        result = self.run_plan(plan)
        self.assertEqual(result["state"], "complete")
        self.assertFalse(modules.exists())
        self.assertTrue((project / "package.json").exists())
        self.assertEqual(self.unselected.read_text(), "keep me")

    def test_absolute_and_lexical_escape_links_refused(self):
        package = self.target / "package"
        package.mkdir()
        (package / "tool").write_text("generated fixture")
        link = self.target / "link"
        for destination in (str(package / "tool"), "../keep.txt", "../../keep.txt"):
            link.symlink_to(destination)
            self.assertTrue(self.plan()["blocked"])
            link.unlink()

    def test_ancestor_symlink_refused(self):
        self.project.rename(self.project.with_name("real-project"))
        self.project.symlink_to(self.project.with_name("real-project"), target_is_directory=True)
        self.assertTrue(self.plan()["blocked"])

    def test_protected_release_evidence_and_aggregate_roots_disabled(self):
        for relative in ("backups/project/target", "release-proof/project/target", "evidence/project/target"):
            path = self.home / relative
            path.mkdir(parents=True)
            (path.parent / "Cargo.toml").write_text("manifest")
            self.assertFalse(self.items(path)[0]["selectable"])
        cache = self.home / "Library/Caches"
        cache.mkdir(parents=True)
        self.assertFalse(self.items(cache)[0]["selectable"])
        self.assertFalse(self.items(self.home)[0]["selectable"])

    def test_measured_cache_children_expand_but_unknown_apps_disabled(self):
        caches = self.home / "Library/Caches"
        caches.mkdir(parents=True)
        known, unknown = caches / "com.apple.dt.Xcode", caches / "personal-app"
        known.mkdir()
        unknown.mkdir()
        rows = [{"path": str(path), "allocated_bytes": 4096} for path in (known, unknown)]
        items = build_items({"candidates": [{"path": str(caches), "allocated_bytes": 8192}]},
                            {"top_directories": rows}, self.home)
        self.assertEqual(len(items), 2)
        self.assertTrue(next(row for row in items if row["path"] == str(known))["selectable"])
        self.assertFalse(next(row for row in items if row["path"] == str(unknown))["selectable"])

    def test_active_workload_blocks_plan(self):
        with patch("cleanup_plan.check_active", side_effect=SafetyError("active process")):
            self.assertTrue(self.plan()["blocked"])

    def test_lsof_timeout_and_ambiguous_errors_fail_closed(self):
        import subprocess
        self.active.stop()
        with patch("cleanup_plan.subprocess.run", side_effect=subprocess.TimeoutExpired("lsof", 20)):
            with self.assertRaises(SafetyError):
                cleanup_plan.check_active(self.target)
        for code, out, err in ((0, b"p123", b""), (1, b"", b"permission denied"), (2, b"", b"")):
            with patch("cleanup_plan.subprocess.run", return_value=subprocess.CompletedProcess("lsof", code, out, err)):
                with self.assertRaises(SafetyError):
                    cleanup_plan.check_active(self.target)

    def test_post_staging_failure_restores_data(self):
        plan = self.plan()
        with patch("cleanup_execute.shutil.rmtree", side_effect=OSError("fixture deletion error")) as mocked:
            mocked.avoids_symlink_attacks = True
            result = self.run_plan(plan)
        self.assertEqual(result["state"], "error")
        self.assertTrue((self.target / "artifact").exists())
        self.assertTrue(any(row["status"] == "restored_remaining" for row in result["results"]))

    def test_private_approval_and_result_files(self):
        self.run_plan(self.plan(), True)
        for name in ("approved-plan.json", "cleanup-results.json"):
            self.assertEqual((self.report / name).stat().st_mode & 0o777, 0o600)
            self.assertIsInstance(json.loads((self.report / name).read_text()), dict)


if __name__ == "__main__":
    unittest.main()
