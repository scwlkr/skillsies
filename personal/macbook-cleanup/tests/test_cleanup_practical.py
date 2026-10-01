"""Realistic pnpm and mixed-selection fixtures; no user paths are removed."""
import json
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

import test_cleanup as fixtures
from cleanup_plan import create_plan


class PracticalCleanupTests(unittest.TestCase):
    setUp = fixtures.CleanupTests.setUp
    items = fixtures.CleanupTests.items
    consent = fixtures.CleanupTests.consent
    run_plan = fixtures.CleanupTests.run_plan

    def modules(self, project="npm-project"):
        root = self.home / project
        root.mkdir()
        (root / "package.json").write_text('{"name":"fixture"}')
        modules = root / "node_modules"
        modules.mkdir()
        return modules

    def batch(self, *paths):
        rows = [row for path in paths for row in self.items(path)]
        return create_plan([row["id"] for row in rows], rows, self.home)

    def test_two_pnpm_trees_unlink_without_touching_external_store(self):
        first, second = self.modules("first"), self.modules("second")
        store = self.home / "pnpm-store"
        store.mkdir()
        source = store / "payload"
        source.write_bytes(b"dependency fixture" * 8192)
        before = source.read_bytes()
        os.link(source, first / "payload")
        os.link(source, second / "payload")
        plan = self.batch(first, second)
        self.assertFalse(plan["blocked"])
        self.assertEqual(plan["shared_bytes"], source.stat().st_blocks * 512)
        directory_bytes = first.stat().st_blocks * 512 + second.stat().st_blocks * 512
        self.assertEqual(plan["estimated_bytes"], directory_bytes)
        result = self.run_plan(plan)
        self.assertEqual(result["state"], "complete", result)
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(source.stat().st_nlink, 1)

    def test_shared_inode_fully_selected_is_counted_once_and_deleted(self):
        first, second = self.modules("first"), self.modules("second")
        (first / "payload").write_bytes(b"fixture" * 8192)
        os.link(first / "payload", second / "payload")
        allocation = sum(path.stat().st_blocks * 512 for path in (first, second, first / "payload"))
        plan = self.batch(first, second)
        self.assertEqual(plan["estimated_bytes"], allocation)
        self.assertEqual(plan["shared_bytes"], 0)
        self.assertEqual(self.run_plan(plan)["state"], "complete")
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())

    def test_single_external_link_does_not_read_generated_file_contents(self):
        modules = self.modules()
        source = self.home / "store-payload"
        source.write_bytes(b"fixture")
        os.link(source, modules / "payload")
        with patch("cleanup_tree.content_hash", side_effect=AssertionError("No hash needed")):
            plan = self.batch(modules)
            self.assertEqual(self.run_plan(plan)["state"], "complete")
        self.assertEqual(source.read_bytes(), b"fixture")

    def test_two_hardlinked_installer_names_are_counted_once(self):
        downloads = self.home / "Downloads"
        downloads.mkdir()
        first, second = downloads / "first.zip", downloads / "second.zip"
        first.write_bytes(b"archive" * 8192)
        os.link(first, second)
        allocation = first.stat().st_blocks * 512
        plan = self.batch(first, second)
        self.assertEqual(plan["estimated_bytes"], allocation)
        self.assertEqual(self.run_plan(plan)["state"], "complete")
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())

    def test_installer_rewrite_immediately_after_rename_is_refused(self):
        downloads = self.home / "Downloads"
        downloads.mkdir()
        archive = downloads / "fixture.zip"
        archive.write_bytes(b"first")
        plan = self.batch(archive)
        original_rename = os.rename

        def rename_then_rewrite(source, destination, **kwargs):
            original_rename(source, destination, **kwargs)
            if str(destination).startswith(".macbook-cleanup-"):
                staged = downloads / destination
                before = staged.stat()
                staged.write_bytes(b"other")
                os.utime(staged, ns=(before.st_atime_ns, before.st_mtime_ns))

        with patch("cleanup_execute.os.rename", side_effect=rename_then_rewrite):
            result = self.run_plan(plan)
        self.assertEqual(result["state"], "error")
        self.assertIn("changed during staging", result["error"])
        self.assertEqual(archive.read_bytes(), b"other")
        self.assertFalse(any(row["status"] == "deleted" for row in result["results"]))

    def test_internal_hardlinks_are_counted_once(self):
        modules = self.modules()
        payload = modules / "a"
        payload.write_bytes(b"fixture" * 8192)
        os.link(payload, modules / "b")
        plan = self.batch(modules)
        self.assertEqual(plan["estimated_bytes"], (modules.stat().st_blocks + payload.stat().st_blocks) * 512)
        self.assertEqual(plan["shared_bytes"], 0)
        self.assertEqual(self.run_plan(plan)["state"], "complete")

    def test_verified_dependency_package_names_and_fixtures_are_generated(self):
        modules = self.modules()
        package = modules / ".pnpm/containers@1.0/node_modules/containers"
        package.mkdir(parents=True)
        (package / "package.json").write_text('{"name":"containers","version":"1.0"}')
        for name in ("backups", "evidence", "credentials", ".env", "release-proof"):
            child = package / "test/fixtures" / name
            child.parent.mkdir(parents=True, exist_ok=True)
            child.write_text("synthetic package fixture")
        (modules / "containers").symlink_to(".pnpm/containers@1.0/node_modules/containers")
        plan = self.batch(modules)
        self.assertFalse(plan["blocked"], plan)
        self.assertEqual(self.run_plan(plan)["state"], "complete")
        self.assertFalse(modules.exists())

    def test_mismatched_or_symlink_package_manifest_does_not_exempt_evidence(self):
        modules = self.modules()
        package = modules / "containers"
        package.mkdir()
        manifest = package / "package.json"
        manifest.write_text('{"name":"not-containers"}')
        self.assertTrue(self.batch(modules)["blocked"])
        manifest.unlink()
        manifest.symlink_to(modules.parent / "package.json")
        self.assertTrue(self.batch(modules)["blocked"])
        self.assertTrue(modules.exists())

    def test_top_level_user_evidence_outside_verified_packages_stays_blocked(self):
        modules = self.modules()
        evidence = modules / "evidence"
        evidence.mkdir()
        (evidence / "proof.txt").write_text("user evidence")
        plan = self.batch(modules)
        self.assertFalse(plan["items"])
        self.assertTrue(plan["blocked"])
        self.assertTrue((evidence / "proof.txt").exists())

    def test_mixed_confirmation_deletes_only_exact_validated_subset(self):
        modules = self.modules()
        (modules / "dependency").write_text("generated")
        evidence = self.target / "evidence"
        evidence.mkdir()
        proof = evidence / "proof.txt"
        proof.write_text("keep user proof")
        plan = self.batch(modules, self.target)
        self.assertEqual([row["path"] for row in plan["items"]], [str(modules)])
        self.assertEqual([row["path"] for row in plan["blocked"]], [str(self.target)])
        result = self.run_plan(plan)
        self.assertEqual(result["state"], "complete")
        self.assertFalse(modules.exists())
        self.assertEqual(proof.read_text(), "keep user proof")
        approved = json.loads((self.report / "approved-plan.json").read_text())
        self.assertEqual([row["path"] for row in approved["items"]], [str(modules)])

    def test_linked_content_rewrite_hidden_by_expected_ctime_change_is_refused(self):
        first, second = self.modules("first"), self.modules("second")
        source = self.home / "external-store-file"
        source.write_bytes(b"first")
        os.link(source, first / "payload")
        os.link(source, second / "payload")
        plan = self.batch(first, second)
        original_remove = shutil.rmtree
        count = 0

        def delete_then_mutate(name, **kwargs):
            nonlocal count
            original_remove(name, **kwargs)
            count += 1
            if count == 1:
                before = source.stat()
                source.write_bytes(b"other")
                os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))

        with patch("cleanup_execute.shutil.rmtree", side_effect=delete_then_mutate) as mocked:
            mocked.avoids_symlink_attacks = True
            result = self.run_plan(plan)
        self.assertEqual(result["state"], "error")
        self.assertFalse(first.exists())
        self.assertTrue(second.exists())
        self.assertIn("changed immediately", result["error"])


if __name__ == "__main__":
    unittest.main()
