"""Terminal consent/controller checks; all paths are temporary fixtures."""
import curses
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terminal_review as terminal
import terminal_view as view
import cleanup_plan
import cleanup_execute


class Screen:
    def __init__(self, keys):
        self.keys = iter(keys)
        self.writes = []
    def get_wch(self):
        return next(self.keys)
    def getmaxyx(self):
        return (30, 120)
    def erase(self):
        pass
    def refresh(self):
        pass
    def addnstr(self, y, x, text, count, attr=0):
        self.writes.append(text[:count])


def item(identifier="one", selectable=True, path="/fixture/project/target"):
    return {"id": identifier, "path": path, "label": "target", "category": "build",
            "allocated_bytes": 8192, "logical_bytes": 8192, "selectable": selectable,
            "reason": "Close builds first" if selectable else "Use the owning tool"}


def plan(blocked=False):
    return {"id": "fixture-plan", "digest": "fixture-digest", "items": [item()],
            "blocked": [{"id": "skip", "path": "/fixture/skipped", "reason": "Busy"}] if blocked else [],
            "estimated_bytes": 8192, "shared_bytes": 0, "expires_at": 9999999999, "consumed": False}


class TerminalReviewTests(unittest.TestCase):
    def check_interrupted_job(self, approved):
        release, finished = threading.Event(), threading.Event()
        def work():
            release.wait(2)
            finished.set()
            return {"state": "complete"}
        draws = []
        def draw(*args):
            draws.append(args[1])
            if len(draws) == 1:
                raise KeyboardInterrupt
            release.set()
        with patch.object(view, "draw_work", side_effect=draw):
            if approved:
                self.assertEqual(terminal.job(Screen([]), "Applying", work, True), {"state": "complete"})
            else:
                with self.assertRaises(KeyboardInterrupt):
                    terminal.job(Screen([]), "Preparing", work)
        self.assertTrue(finished.is_set())
        self.assertGreaterEqual(len(draws), 2)

    def test_ctrl_c_preflight_waits_then_cancels_without_approval(self):
        self.check_interrupted_job(False)

    def test_ctrl_c_approved_batch_waits_for_saved_outcome(self):
        self.check_interrupted_job(True)

    def test_escape_controls_and_bidi_in_paths(self):
        rendered = view.safe("name\x1b[2J\n\r\t\u202e.txt\udcff")
        self.assertEqual(rendered, "name\\u001b[2J\\u000a\\u000d\\u0009\\u202e.txt\\udcff")
        self.assertNotIn("\x1b", rendered)

    def test_starts_with_nothing_selected(self):
        state = terminal.Selection([item()])
        self.assertEqual(state.selected, set())

    def test_space_toggles_only_selectable(self):
        state = terminal.Selection([item(), item("blocked", False)])
        state.toggle()
        self.assertEqual(state.selected, {"one"})
        state.toggle()
        self.assertFalse(state.selected)
        state.cursor = 1
        self.assertIn("Unavailable", state.toggle())
        self.assertFalse(state.selected)

    def test_search_and_filter_leave_selections_intact(self):
        state = terminal.Selection([item(), item("other", False, "/fixture/elsewhere")])
        state.toggle()
        state.query = "ELSEWHERE"
        self.assertEqual([row["id"] for row in state.visible()], ["other"])
        state.filter_next()
        self.assertEqual(state.visible(), [])
        self.assertEqual(state.selected, {"one"})

    def test_select_page_skips_disabled_and_other_pages(self):
        state = terminal.Selection([item("a"), item("b", False), item("c")])
        state.select_page(2)
        self.assertEqual(state.selected, {"a"})

    def test_consent_requires_exact_uppercase_and_enter(self):
        screen = Screen(list("delete\nDELETE\n"))
        with patch.object(terminal, "validate_confirmation") as validate:
            payload = terminal.confirm(screen, plan())
        self.assertEqual(payload, {"plan_id": "fixture-plan", "digest": "fixture-digest", "confirmed": True})
        validate.assert_called_once()

    def test_escape_cancels_even_after_typing_delete(self):
        with patch.object(terminal, "validate_confirmation") as validate:
            self.assertIsNone(terminal.confirm(Screen(list("DELETE\x1b")), plan()))
        validate.assert_not_called()

    def test_review_lists_exact_deletes_and_skips(self):
        lines = terminal.approval_lines(plan(True), False)
        self.assertTrue(any("DELETE" in line and "/fixture/project/target" in line for line in lines))
        self.assertIn("SKIPPED: these paths WILL NOT be deleted:", lines)
        self.assertIn("/fixture/skipped", lines)
        self.assertTrue(any("Busy" in line for line in lines))

    def test_no_valid_items_cannot_be_confirmed(self):
        empty = plan()
        empty["items"] = []
        with patch.object(terminal, "validate_confirmation") as validate:
            self.assertIsNone(terminal.confirm(Screen(list("DELETE\n\x1b")), empty))
        validate.assert_not_called()

    def test_noninteractive_refused_before_loading_any_report(self):
        with patch.object(sys.stdin, "isatty", return_value=False), patch.object(terminal, "load_report") as load:
            with self.assertRaisesRegex(RuntimeError, "interactive Terminal"):
                terminal.run_review("/does/not/exist")
        load.assert_not_called()

    def test_quit_list_never_creates_plan_or_executes(self):
        with patch.object(terminal.curses, "curs_set"), patch.object(terminal, "create_plan") as create, patch.object(terminal, "execute") as execute:
            result = terminal.interactive(Screen([" ", "q"]), Path("/fixture"), {}, {}, [item()])
        self.assertIsNone(result)
        create.assert_not_called()
        execute.assert_not_called()

    def test_review_cancel_returns_to_selection_without_execution(self):
        with patch.object(terminal.curses, "curs_set"), patch.object(terminal, "create_plan", return_value=plan()) as create, patch.object(terminal, "execute") as execute:
            result = terminal.interactive(Screen([" ", "r", "\x1b", "q"]), Path("/fixture"), {}, {}, [item()])
        self.assertIsNone(result)
        create.assert_called_once()
        execute.assert_not_called()

    def test_confirm_calls_shared_executor_with_frozen_exact_batch(self):
        frozen, screen = plan(), Screen([" ", "r"] + list("DELETE\n"))
        with patch.object(terminal.curses, "curs_set"), patch.object(terminal, "create_plan", return_value=frozen), patch.object(terminal, "validate_confirmation"), patch.object(terminal, "execute", return_value={"state": "complete"}) as execute:
            result = terminal.interactive(screen, Path("/fixture/report"), {}, {}, [item()])
        self.assertEqual(result["state"], "complete")
        self.assertIs(execute.call_args.args[0], frozen)
        self.assertTrue(execute.call_args.args[1]["confirmed"])
        self.assertFalse(execute.call_args.args[4])

    def test_permission_action_opens_settings_and_exits_for_restart(self):
        with patch.object(terminal.curses, "curs_set"), patch.object(terminal, "open_settings") as settings, patch.object(terminal, "execute") as execute:
            result = terminal.interactive(Screen(["p", "\n"]), Path("/fixture"), {}, {}, [])
        self.assertEqual(result, {"state": "access_setup", "exit_code": 78})
        settings.assert_called_once()
        execute.assert_not_called()

    def test_preview_approval_saves_results_and_preserves_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            target = home / "project/target"
            target.mkdir(parents=True)
            (target.parent / "Cargo.toml").write_text("[package]\nname='fixture'\n")
            (target / "data").write_bytes(b"fixture only")
            report = home / "report"
            report.mkdir()
            row = item(path=str(target))
            with patch.object(cleanup_plan, "check_active"), patch.object(terminal.curses, "curs_set"), patch.object(terminal.Path, "home", return_value=home):
                result = terminal.interactive(Screen([" ", "r"] + list("DELETE\n")), report, {}, {}, [row], True)
            self.assertEqual(result["state"], "preview")
            self.assertTrue((target / "data").exists())
            approval = json.loads((report / "approved-plan.json").read_text())
            self.assertEqual(approval["items"][0]["path"], str(target))
            self.assertTrue(approval["preview"])

    def test_report_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "actual").write_text("{}")
            (root / "summary.json").symlink_to(root / "actual")
            with self.assertRaisesRegex(ValueError, "regular local"):
                terminal.load_report(root, "summary.json")

    def test_typed_consent_deletes_only_the_temporary_selected_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            target = home / "project/target"
            target.mkdir(parents=True)
            manifest = target.parent / "Cargo.toml"
            manifest.write_text("[package]\nname='fixture'\n")
            (target / "disposable").write_bytes(b"temporary fixture")
            preserve = target.parent / "src.rs"
            preserve.write_text("user source fixture")
            report = home / "report"
            report.mkdir()
            row = item(path=str(target))
            with patch.object(cleanup_plan, "check_active"), patch.object(cleanup_execute, "check_active"), patch.object(cleanup_execute, "measure", return_value={"used_percent": 49}), patch.object(terminal.curses, "curs_set"), patch.object(terminal.Path, "home", return_value=home):
                result = terminal.interactive(Screen([" ", "r"] + list("DELETE\n")), report, {}, {}, [row])
            self.assertEqual(result["state"], "complete")
            self.assertFalse(target.exists())
            self.assertTrue(manifest.exists())
            self.assertEqual(preserve.read_text(), "user source fixture")
            self.assertEqual(result["results"][0]["path"], str(target))
            self.assertEqual(result["results"][0]["status"], "deleted")

    def test_bar_clamps_and_capacity_projection_never_negative(self):
        self.assertEqual(view.bar(200, 4), "[####]")
        self.assertEqual(view.bar(-2, 4), "[....]")
        summary = {"capacity": {"total_bytes": 100, "used_bytes": 80, "target_percent": 50}}
        self.assertIn("0.0%", view.capacity_lines(summary, 999, 120)[-1])


if __name__ == "__main__":
    unittest.main()
