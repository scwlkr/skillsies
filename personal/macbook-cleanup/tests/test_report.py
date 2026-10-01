import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import capacity
import report


def result(content):
    return subprocess.CompletedProcess([], 0, stdout=content, stderr=b"")


def measure_result(total=1000, free=200):
    return result(plistlib.dumps({"APFSContainerSize": total, "APFSContainerFree": free}))


def candidate(path="/tmp/cache", allocated=400, category="cache"):
    return {"path": path, "allocated_bytes": allocated, "logical_bytes": allocated * 2,
            "category": category, "action": "Review and use app cleanup.", "risk": "regeneration"}


def scan(candidates=None):
    return {"roots": ["/tmp"], "elapsed_seconds": 0.25,
            "allocated_bytes": 650, "logical_bytes": 900, "files": 3, "directories": 2,
            "hardlink_duplicates": 1, "symlinks_skipped": 2, "dataless_skipped": 1,
            "external_mounts_skipped": 1, "error_count": 1,
            "errors": ["Permission denied: /tmp/private"], "excluded": ["/tmp/offline"],
            "top_files": [{"path": "/tmp/large", "allocated_bytes": 500, "logical_bytes": 800}],
            "top_directories": [{"path": "/tmp", "allocated_bytes": 650, "logical_bytes": 900}],
            "candidates": candidates or []}


class CapacityTests(unittest.TestCase):
    def test_apfs_container_wins_over_df_disagreement(self):
        with patch.object(capacity.subprocess, "run", return_value=measure_result()) as command:
            measured = capacity.measure(Path("/"))
        self.assertEqual(command.call_count, 1)
        self.assertEqual(measured["used_bytes"], 800)
        self.assertEqual(measured["reclaim_needed_bytes"], 300)
        self.assertEqual(measured["source"], "diskutil APFS container")

    def test_already_below_target(self):
        with patch.object(capacity.subprocess, "run", return_value=measure_result(free=700)):
            measured = capacity.measure(Path("/"))
        self.assertEqual(measured["reclaim_needed_bytes"], 0)
        self.assertEqual(measured["used_percent"], 30)

    def test_missing_diskutil_falls_back_honestly(self):
        df = b"Filesystem 1024-blocks Used Available Capacity Mounted on\n/dev/disk 1000 700 250 74% /\n"
        with patch.object(capacity.subprocess, "run", side_effect=[FileNotFoundError(), result(df)]):
            measured = capacity.measure(Path("/"))
        self.assertEqual(measured["used_bytes"], 750 * 1024)
        self.assertIn("volume-only", measured["source"])
        self.assertTrue(measured["warnings"])

    def test_corrupt_plist_falls_back(self):
        df = b"Filesystem 1024-blocks Used Available Capacity Mounted on\nx 1000 750 250 75% /\n"
        for corrupt in (b"not a plist", b"<?xml version='1.0'?><plist><dict>"):
            with self.subTest(corrupt=corrupt):
                with patch.object(capacity.subprocess, "run", side_effect=[result(corrupt), result(df)]):
                    self.assertEqual(capacity.measure(Path("/"))["free_bytes"], 250 * 1024)

    def test_invalid_metrics_fail_instead_of_switching_sources(self):
        for total, free in ((0, 0), (1000, 1100), (1000, -1), (True, 0)):
            with self.subTest(total=total, free=free):
                with patch.object(capacity.subprocess, "run", return_value=measure_result(total, free)) as command:
                    with self.assertRaises(ValueError):
                        capacity.measure(Path("/"))
                self.assertEqual(command.call_count, 1)

    def test_both_commands_unavailable(self):
        with patch.object(capacity.subprocess, "run", side_effect=FileNotFoundError()):
            with self.assertRaises(RuntimeError):
                capacity.measure(Path("/"))

    def test_malformed_df_and_timeout(self):
        for second in (result(b"bad"), subprocess.TimeoutExpired("df", 15)):
            with patch.object(capacity.subprocess, "run", side_effect=[FileNotFoundError(), second]):
                with self.assertRaises(RuntimeError):
                    capacity.measure(Path("/"))

    def test_invalid_targets(self):
        for target in (0, -1, 101, float("nan"), float("inf"), True, "50"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    capacity.measure(Path("/"), target)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.output = Path(self.tmp.name)
        with patch.object(capacity.subprocess, "run", return_value=measure_result()):
            self.capacity = capacity.measure(Path("/"))

    def tearDown(self):
        self.tmp.cleanup()

    def generate(self, input_scan, cap=None):
        paths = report.generate(input_scan, cap or self.capacity, self.output)
        return json.loads(Path(paths["summary"]).read_text()), Path(paths["html"]).read_text(), Path(paths["markdown"]).read_text()

    def test_target_is_plausible_but_not_promised(self):
        summary, html, markdown = self.generate(scan([candidate()]))
        self.assertEqual(summary["target_plausibility"], "enough_candidates_to_review")
        self.assertEqual(summary["optimistic_used_percent"], 40)
        self.assertEqual(summary["optimistic_residual_gap_bytes"], 0)
        self.assertIn("not confirmed reclaimable", markdown)
        self.assertIn("optimistic scenario", html)

    def test_estimate_short_reports_residual(self):
        summary, html, markdown = self.generate(scan([candidate(allocated=100)]))
        self.assertEqual(summary["target_plausibility"], "candidate_estimate_short")
        self.assertEqual(summary["optimistic_residual_gap_bytes"], 200)
        self.assertIn("still need to be reclaimed", html)
        self.assertIn("200 B", markdown)

    def test_no_candidates_still_reports_gap(self):
        summary, _, _ = self.generate(scan())
        self.assertEqual(summary["optimistic_residual_gap_bytes"], 300)

    def test_already_met_does_not_call_for_removal(self):
        with patch.object(capacity.subprocess, "run", return_value=measure_result(free=700)):
            measured = capacity.measure(Path("/"))
        summary, html, markdown = self.generate(scan(), measured)
        self.assertEqual(summary["target_plausibility"], "already_met")
        self.assertIn("No removal is needed", html)
        self.assertIn("No cleanup is needed for this goal", html)
        self.assertNotIn("choose specific cleanup actions", html)
        self.assertNotIn("choose specific cleanup actions", markdown)

    def test_html_and_markdown_escape_private_paths(self):
        dangerous = "/tmp/<script>alert('x')</script>|[x](javascript:x)_`\n"
        data = scan([candidate(dangerous)])
        data["errors"] = [dangerous]
        summary, html, markdown = self.generate(data)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("\\|\\[x\\]", markdown)
        self.assertIn("\\_\\`", markdown)
        self.assertEqual(summary["candidates"][0]["path"], dangerous)
        self.assertIn("connect-src 'none'", html)

    def test_partial_coverage_is_visible(self):
        summary, html, markdown = self.generate(scan())
        self.assertEqual(summary["coverage"]["error_count"], 1)
        for output in (html, markdown):
            self.assertIn("Permission denied", output)
            self.assertIn("cloud placeholders", output)
            self.assertIn("snapshots", output)
            self.assertIn("outside", output)
            self.assertIn("System Settings", output)
            self.assertIn("Full Disk Access", output)
            self.assertIn("relaunch", output)

    def test_candidate_overlaps_and_top_tables_are_not_summed(self):
        data = scan([candidate("/tmp/cache", 400), candidate("/tmp/cache/child", 200)])
        summary, _, _ = self.generate(data)
        self.assertEqual(summary["candidate_upper_bound_bytes"], 400)
        self.assertEqual(len(summary["candidates"]), 1)

    def test_generated_data_first_then_app_then_review(self):
        data = scan([candidate("/tmp/review", 500, "review"),
                     candidate("/tmp/app", 300, "app-managed"), candidate("/tmp/build", 100, "build")])
        summary, _, _ = self.generate(data)
        self.assertEqual([item["category"] for item in summary["candidates"]], ["build", "app-managed", "review"])

    def test_cloud_last_and_app_managed_risk_controls_order(self):
        items = [candidate("/cloud", 1000, "cloud"), candidate("/review", 900, "trash"),
                 candidate("/models", 800, "models"), candidate("/assets", 600, "developer assets"),
                 candidate("/unknown", 700, "tools"), candidate("/build", 10, "build")]
        items[4]["risk"] = "app-managed"
        summary, _, _ = self.generate(scan(items))
        self.assertEqual([item["category"] for item in summary["candidates"]],
                         ["build", "models", "tools", "developer assets", "trash", "cloud"])

    def test_scope_and_selected_roots_are_explicit(self):
        data = scan()
        data["scope"] = "Selected roots only"
        summary, html, markdown = self.generate(data)
        self.assertEqual(summary["coverage"]["scope"], "Selected roots only")
        for output in (html, markdown):
            self.assertIn("Scope: Selected roots only", output)
            self.assertIn("Selected scan roots", output)


if __name__ == "__main__":
    unittest.main()
