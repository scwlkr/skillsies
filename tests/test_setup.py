import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("setup", Path(__file__).resolve().parents[1] / "scripts/setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo, self.home = self.base / "repo", self.base / "home"
        (self.repo / "personal").mkdir(parents=True)

    def skill(self, path, content="instructions"):
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(content)
        (path / "scripts").mkdir()
        (path / "scripts/helper.py").write_text("print('hello')\n")
        return path

    def run_setup(self):
        with contextlib.redirect_stdout(io.StringIO()):
            setup.setup(self.repo, self.home)

    def test_migration_preserves_content_and_old_codex_paths(self):
        self.skill(self.repo / "personal/mine")
        downloaded = self.skill(self.home / ".agents/skills/upstream")
        mine = self.skill(self.home / ".agents/skills/mine")
        codex = self.skill(self.home / ".codex/skills/browser")
        system = self.skill(self.home / ".codex/skills/.system/builtin")
        self.run_setup()
        self.assertEqual(downloaded.resolve(), self.repo / "others/upstream")
        self.assertEqual((self.repo / "others/upstream/scripts/helper.py").read_text(), "print('hello')\n")
        self.assertEqual(codex.resolve(), self.repo / "others/browser")
        self.assertEqual((codex / "SKILL.md").read_text(), "instructions")
        self.assertFalse(mine.exists())
        self.assertEqual((self.repo / ".local/backups/agents/mine/SKILL.md").read_text(), "instructions")
        self.assertFalse((self.repo / "others/mine").exists())
        self.assertFalse(system.is_symlink())
        self.run_setup()

    def test_conflicting_personal_copy_stops_before_any_move(self):
        self.skill(self.repo / "personal/mine", "custom")
        downloaded = self.skill(self.home / ".agents/skills/upstream")
        mine = self.skill(self.home / ".agents/skills/mine", "different")
        with self.assertRaisesRegex(RuntimeError, "Conflicting skill copies"):
            self.run_setup()
        self.assertFalse((self.repo / "others").exists())
        self.assertTrue(downloaded.is_dir())
        self.assertEqual((mine / "SKILL.md").read_text(), "different")

    def test_conflicting_incoming_copies_stop_before_any_move(self):
        canonical = self.skill(self.home / ".agents/skills/upstream", "first")
        codex = self.skill(self.home / ".codex/skills/upstream", "second")
        with self.assertRaisesRegex(RuntimeError, "Conflicting incoming"):
            self.run_setup()
        self.assertEqual((canonical / "SKILL.md").read_text(), "first")
        self.assertEqual((codex / "SKILL.md").read_text(), "second")

    def test_fresh_setup_routes_future_downloads_and_personal_skills(self):
        self.run_setup()
        download = self.skill(self.home / ".agents/skills/new-download")
        personal = self.skill(self.repo / "personal/new-personal")
        self.assertEqual(download.resolve(), self.repo / "others/new-download")
        discovered = self.home / ".codex/skills/personal/new-personal"
        self.assertEqual(discovered.resolve(), personal)
        self.assertEqual((discovered / "SKILL.md").read_text(), "instructions")
        self.run_setup()

    def test_existing_link_elsewhere_is_not_replaced(self):
        other = self.base / "other"
        other.mkdir()
        root = self.home / ".agents/skills"
        root.parent.mkdir(parents=True)
        root.symlink_to(other)
        with self.assertRaisesRegex(RuntimeError, "points elsewhere"):
            self.run_setup()
        self.assertEqual(root.resolve(), other)


if __name__ == "__main__":
    unittest.main()
