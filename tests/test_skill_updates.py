from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


scripts = Path(__file__).resolve().parents[1] / "personal/update-others/scripts"
sys.path.insert(0, str(scripts))
import inventory
import skill_updates


class SkillUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.repo, self.home = base / "repo", base / "home"
        self.root = self.repo / "others"
        self.root.mkdir(parents=True)
        (self.repo / "personal/mine").mkdir(parents=True)
        (self.repo / "personal/mine/SKILL.md").write_text("my instructions")
        canonical = self.home / ".agents/skills"
        canonical.parent.mkdir(parents=True)
        canonical.symlink_to(self.root)
        self.lock_path = self.home / ".agents/.skill-lock.json"
        self.lock = {"version": 3, "skills": {}}

    def add(self, name, source="owner/repo", revision="1" * 40):
        folder = self.root / name
        folder.mkdir()
        (folder / "SKILL.md").write_text("old instructions")
        self.lock["skills"][name] = {"source": source, "sourceType": "github",
                                    "skillPath": f"skills/{name}/SKILL.md", "skillFolderHash": revision}
        self.lock_path.write_text(json.dumps(self.lock))

    def pending(self):
        return inventory.records_for(self.root, self.lock)

    def plan(self):
        return inventory.compare(self.pending(), lambda *_: {"skills/upstream": "2" * 40})

    def run_update(self, records, run, verify):
        with patch.object(Path, "home", return_value=self.home), contextlib.redirect_stdout(io.StringIO()):
            return skill_updates.update(self.root, self.lock_path, records, run=run, verify=verify)

    def test_upstream_check_batches_same_source_and_handles_moved_folders(self):
        self.add("first")
        self.add("second")
        calls = []
        def fetch(*group):
            calls.append(group)
            return {"skills/first": "1" * 40}
        records = inventory.compare(self.pending(), fetch)
        self.assertEqual(len(calls), 1)
        self.assertEqual([r["status"] for r in records], ["current", "missing"])

    def test_unique_moved_folder_is_delegated_to_official_updater(self):
        self.add("upstream")
        records = inventory.compare(self.pending(), lambda *_: {"new-location/upstream": "2" * 40})
        self.assertEqual(records[0]["status"], "moved")
        self.assertEqual(records[0]["replacementPath"], "new-location/upstream")

    def test_untracked_personal_overlap_and_linked_downloads_are_skipped(self):
        self.add("mine")
        self.add("linked")
        (self.root / "linked/SKILL.md").unlink()
        (self.root / "linked").rmdir()
        (self.root / "linked").symlink_to(self.repo / "personal/mine")
        (self.root / "untracked").mkdir()
        records = self.pending()
        self.assertTrue(all(r["status"] == "skipped" for r in records))
        self.assertEqual(len(records), 3)

    def test_upstream_failure_is_an_error_not_current(self):
        self.add("upstream")
        def unavailable(*_):
            raise RuntimeError("network unavailable")
        records = inventory.compare(self.pending(), unavailable)
        self.assertEqual(records[0]["status"], "error")
        with self.assertRaisesRegex(RuntimeError, "checks failed"):
            self.run_update(records, None, None)
        self.assertFalse((self.repo / ".local").exists())

    def test_repo_root_skill_and_null_source_metadata(self):
        self.add("root-skill")
        self.lock["skills"]["root-skill"]["skillPath"] = "SKILL.md"
        records = inventory.compare(self.pending(), lambda *_: {"": "2" * 40})
        self.assertEqual(records[0]["status"], "update")
        self.lock["skills"]["root-skill"]["source"] = None
        self.assertEqual(self.pending()[0]["status"], "skipped")

    def test_update_selects_changed_tracked_names_and_preserves_a_backup(self):
        self.add("upstream")
        (self.root / "untracked").mkdir()
        records = self.plan()
        after = deepcopy(records)
        after[1].update(status="current", installed="2" * 40)
        checks = iter([records, after])
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            (self.root / "upstream/SKILL.md").write_text("new instructions")
            self.lock["skills"]["upstream"]["skillFolderHash"] = "2" * 40
            self.lock_path.write_text(json.dumps(self.lock))
            return subprocess.CompletedProcess(command, 0)
        original_lock = self.lock_path.read_bytes()
        result, backup = self.run_update(records, run, lambda *_: next(checks))
        self.assertEqual(calls[0], ["npx", "--yes", "skills@latest", "update", "upstream", "-g", "-y"])
        self.assertEqual((backup / "others/upstream/SKILL.md").read_text(), "old instructions")
        self.assertEqual((backup / "skill-lock.json").read_bytes(), original_lock)
        self.assertEqual((self.repo / "personal/mine/SKILL.md").read_text(), "my instructions")
        self.assertEqual(result[1]["status"], "current")

    def test_updater_success_without_verified_update_is_a_failure(self):
        self.add("upstream")
        records = self.plan()
        with self.assertRaisesRegex(RuntimeError, "not verified"):
            self.run_update(records, lambda command, **_: subprocess.CompletedProcess(command, 0), lambda *_: records)

    def test_changed_plan_stops_before_downloads_are_modified(self):
        self.add("upstream")
        records = self.plan()
        with self.assertRaisesRegex(RuntimeError, "plan changed"):
            self.run_update(records, None, lambda *_: [])
        self.assertEqual((self.root / "upstream/SKILL.md").read_text(), "old instructions")

    def test_wrong_global_destination_cannot_be_updated(self):
        self.add("upstream")
        records = self.plan()
        canonical = self.home / ".agents/skills"
        canonical.unlink()
        canonical.mkdir()
        with self.assertRaisesRegex(RuntimeError, "destination"):
            self.run_update(records, None, None)

    def test_changed_personal_content_is_reported(self):
        self.add("upstream")
        records = self.plan()
        def unexpected(command, **_):
            (self.repo / "personal/mine/SKILL.md").write_text("unexpected")
            return subprocess.CompletedProcess(command, 0)
        with self.assertRaisesRegex(RuntimeError, "Personal skill files changed"):
            self.run_update(records, unexpected, lambda *_: records)


if __name__ == "__main__":
    unittest.main()
