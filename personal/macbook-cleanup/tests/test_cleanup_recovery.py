"""Interruption and staged-tree race fixtures preserve private recovery evidence."""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import test_cleanup as fixtures
from cleanup_plan import create_plan


class RecoveryTests(unittest.TestCase):
    setUp = fixtures.CleanupTests.setUp
    items = fixtures.CleanupTests.items
    plan = fixtures.CleanupTests.plan
    consent = fixtures.CleanupTests.consent
    run_plan = fixtures.CleanupTests.run_plan

    def test_protected_descendants_are_never_planned(self):
        for name in ("evidence", "backups", "release-proof"):
            child = self.target / name
            child.mkdir()
            (child / "irreplaceable.txt").write_text("release proof")
            self.assertTrue(self.plan()["blocked"])
            (child / "irreplaceable.txt").unlink()
            child.rmdir()
        self.assertTrue((self.target / "artifact").exists())

    def test_credential_names_inside_generated_tree_block_without_content_reads(self):
        for name in (".env", ".env.production", ".ssh", ".gnupg", "id_rsa", "id_ed25519",
                     "credentials", "credentials.json", "secrets", "secrets.json"):
            child = self.target / name
            child.write_text("synthetic credential fixture")
            with patch("pathlib.Path.read_text", side_effect=AssertionError("Do not read credentials")), \
                 patch("builtins.open", side_effect=AssertionError("Do not read credentials")):
                plan = self.plan()
            self.assertTrue(plan["blocked"], name)
            self.assertTrue(child.exists())
            child.unlink()

    def test_mapping_is_durable_before_rename_and_interruption(self):
        plan = self.plan()
        original_rename = os.rename

        class SimulatedTermination(BaseException):
            pass

        def interrupted(source, destination, **kwargs):
            journal = json.loads((self.report / "cleanup-results.json").read_text())
            self.assertEqual(journal["staging"][0]["state"], "prepared")
            self.assertEqual(journal["staging"][0]["original_path"], str(self.target))
            self.assertEqual(journal["staging"][0]["identity"], plan["items"][0]["identity"])
            original_rename(source, destination, **kwargs)
            raise SimulatedTermination()

        with patch("cleanup_execute.os.rename", side_effect=interrupted):
            with self.assertRaises(SimulatedTermination):
                self.run_plan(plan)
        journal = json.loads((self.report / "cleanup-results.json").read_text())
        stage = Path(journal["staging"][0]["staged_path"])
        self.assertTrue((stage / "artifact").exists())
        self.assertFalse(self.target.exists())
        self.assertEqual(journal["state"], "running")

    def test_first_staged_tree_changed_while_second_stages_restores_everything(self):
        other = self.home / "second/target"
        other.mkdir(parents=True)
        (other.parent / "Cargo.toml").write_text("second manifest")
        (other / "artifact").write_text("second generated fixture")
        rows = self.items() + self.items(other)
        plan = create_plan([row["id"] for row in rows], rows, self.home)
        original_rename = os.rename
        count = 0

        def mutate_first(source, destination, **kwargs):
            nonlocal count
            original_rename(source, destination, **kwargs)
            if str(destination).startswith(".macbook-cleanup-"):
                count += 1
                if count == 2:
                    journal = json.loads((self.report / "cleanup-results.json").read_text())
                    first = Path(journal["staging"][0]["staged_path"])
                    (first / "new-work").write_text("new unreviewed data")

        with patch("cleanup_execute.os.rename", side_effect=mutate_first):
            result = self.run_plan(plan)
        self.assertEqual(result["state"], "error")
        self.assertTrue((self.target / "new-work").exists())
        self.assertTrue((self.target / "artifact").exists())
        self.assertTrue((other / "artifact").exists())
        self.assertFalse(any(row["status"] == "deleted" for row in result["results"]))

    def test_partial_removal_reports_only_remaining_contents_restored(self):
        second = self.target / "second-file"
        second.write_text("remaining fixture")
        plan = self.plan()

        def partial_remove(name, dir_fd):
            child_fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY, dir_fd=dir_fd)
            try:
                os.unlink("artifact", dir_fd=child_fd)
            finally:
                os.close(child_fd)
            raise OSError("simulated error after first fixture file removed")

        with patch("cleanup_execute.shutil.rmtree", side_effect=partial_remove) as mocked:
            mocked.avoids_symlink_attacks = True
            result = self.run_plan(plan)
        self.assertEqual(result["state"], "error")
        self.assertFalse((self.target / "artifact").exists())
        self.assertTrue(second.exists())
        restored = next(row for row in result["results"] if row["status"] == "restored_remaining")
        self.assertTrue(restored["partial_deletion_possible"])
        self.assertIn("only remaining", restored["message"])
        self.assertEqual(result["staging"][0]["state"], "restored_remaining")

    def test_post_staging_installer_rewrite_with_restored_mtime_refused(self):
        downloads = self.home / "Downloads"
        downloads.mkdir()
        first, second = downloads / "first.zip", downloads / "second.zip"
        first.write_bytes(b"first")
        second.write_bytes(b"other")
        rows = self.items(first) + self.items(second)
        plan = create_plan([row["id"] for row in rows], rows, self.home)
        original_rename = os.rename
        count = 0

        def rewrite_first(source, destination, **kwargs):
            nonlocal count
            original_rename(source, destination, **kwargs)
            if str(destination).startswith(".macbook-cleanup-"):
                count += 1
                if count == 2:
                    journal = json.loads((self.report / "cleanup-results.json").read_text())
                    staged = Path(journal["staging"][0]["staged_path"])
                    before = staged.stat()
                    staged.write_bytes(b"newer")
                    os.utime(staged, ns=(before.st_atime_ns, before.st_mtime_ns))

        with patch("cleanup_execute.os.rename", side_effect=rewrite_first):
            result = self.run_plan(plan)
        self.assertEqual(result["state"], "error")
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())
        self.assertEqual(first.read_bytes(), b"newer")

    def test_active_process_at_staged_path_refuses_removal(self):
        plan = self.plan()
        from cleanup_plan import SafetyError
        with patch("cleanup_execute.check_active", side_effect=SafetyError("new active workload")):
            result = self.run_plan(plan)
        self.assertEqual(result["state"], "error")
        self.assertTrue((self.target / "artifact").exists())
        self.assertTrue(any(row["status"] == "restored" for row in result["results"]))


if __name__ == "__main__":
    unittest.main()
