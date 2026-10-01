"""Local HTTP review-contract tests, restricted to synthetic temporary data."""
import contextlib
import http.client
import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from review_server import ReviewServer


class ReviewServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name).resolve()
        self.report = self.home / "report"
        self.report.mkdir()
        self.target = self.home / "project/target"
        self.target.mkdir(parents=True)
        (self.target.parent / "Cargo.toml").write_text("fixture manifest")
        (self.target / "artifact").write_text("generated fixture")
        summary = {"capacity": {"target_percent": 50}, "candidates": [
            {"path": str(self.target), "allocated_bytes": 4096, "category": "build"}]}
        (self.report / "summary.json").write_text(json.dumps(summary))
        (self.report / "scan.json").write_text('{}')
        self.assets = self.home / "assets"
        self.assets.mkdir()
        (self.assets / "index.html").write_text("local dashboard fixture")
        self.server = ReviewServer(self.report, preview=True, home=self.home, assets=self.assets)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.active = patch("cleanup_plan.check_active")
        self.active.start()
        self.addCleanup(self.close)

    def close(self):
        self.active.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, payload=None, headers=None, auth=True, origin=True):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        supplied = {}
        if auth:
            supplied["Authorization"] = f"Bearer {self.server.token}"
        if origin:
            supplied["Origin"] = self.server.origin
        if payload is not None:
            supplied["Content-Type"] = "application/json"
        supplied.update(headers or {})
        connection.request("POST" if payload is not None else "GET", path,
                           json.dumps(payload) if payload is not None else None, supplied)
        response = connection.getresponse()
        data = response.read()
        status, returned = response.status, dict(response.getheaders())
        connection.close()
        return status, json.loads(data) if returned["Content-Type"] == "application/json" else data, returned

    def plan(self):
        status, result, _ = self.request("/api/plan", {"ids": [self.server.items[0]["id"]]})
        self.assertEqual(status, 200)
        return result

    def test_session_auth_and_no_cors(self):
        self.assertEqual(self.request("/api/session", auth=False)[0], 401)
        status, session, headers = self.request("/api/session")
        self.assertEqual(status, 200)
        self.assertTrue(session["preview"])
        self.assertEqual(session["items"][0]["path"], str(self.target))
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertNotIn(self.server.token, json.dumps(session))

    def test_csrf_and_host_rejected_before_mutation(self):
        payload = {"ids": [self.server.items[0]["id"]]}
        for headers, origin in (({}, False), ({"Origin": "https://attacker.invalid"}, True),
                                ({"Host": "evil.invalid"}, True),
                                ({"Origin": self.server.origin.replace("127.0.0.1", "localhost")}, True)):
            self.assertEqual(self.request("/api/plan", payload, headers, origin=origin)[0], 403)
        self.assertIsNone(self.server.plan)
        self.assertTrue(self.target.exists())

    def test_selection_spoof_and_wrong_approval_refused(self):
        self.assertEqual(self.request("/api/plan", {"ids": [str(self.target)]})[0], 400)
        plan = self.plan()
        self.assertEqual(self.request("/api/confirm", {"confirmed": True})[0], 400)
        self.assertEqual(self.request("/api/confirm", {"plan_id": plan["id"], "digest": "bad", "confirmed": True})[0], 400)
        self.assertEqual(self.server.status["state"], "planned")
        self.assertTrue(self.target.exists())

    def test_final_preview_and_replay_contract(self):
        plan = self.plan()
        consent = {"plan_id": plan["id"], "digest": plan["digest"], "confirmed": True}
        with contextlib.redirect_stdout(io.StringIO()):
            status, result, _ = self.request("/api/confirm", consent)
        self.assertEqual(status, 200)
        self.assertEqual(result["state"], "preview")
        self.assertTrue(self.target.exists())
        self.assertEqual(self.request("/api/confirm", consent)[0], 400)
        self.assertEqual(self.request("/api/plan", {"ids": [self.server.items[0]["id"]]})[0], 400)
        self.assertTrue(self.server.finished.is_set())
        self.assertEqual(self.request("/api/status")[1]["state"], "preview")
        self.assertTrue(self.server.observed.is_set())

    def test_clear_invalidates_exact_pending_batch(self):
        plan = self.plan()
        self.assertEqual(self.request("/api/clear", {})[0], 200)
        self.assertEqual(self.request("/api/confirm", {"plan_id": plan["id"], "digest": plan["digest"], "confirmed": True})[0], 400)
        self.assertTrue(self.target.exists())

    def test_real_http_confirmation_deletes_only_generated_fixture(self):
        self.server.preview = False
        keep = self.home / "keep.txt"
        keep.write_text("unselected fixture")
        plan = self.plan()
        self.assertTrue(self.target.exists())
        consent = {"plan_id": plan["id"], "digest": plan["digest"], "confirmed": True}
        with patch("cleanup_execute.check_active"), \
             patch("cleanup_execute.measure", return_value={"used_percent": 49}), \
             contextlib.redirect_stdout(io.StringIO()):
            status, result, _ = self.request("/api/confirm", consent)
        self.assertEqual(status, 200)
        self.assertEqual(result["state"], "complete")
        self.assertEqual(result["capacity_after"]["used_percent"], 49)
        self.assertFalse(self.target.exists())
        self.assertTrue(keep.exists())
        self.assertEqual(self.request("/api/confirm", consent)[0], 400)

    def test_static_assets_no_traversal_or_remote_requests(self):
        status, contents, _ = self.request("/", auth=False, origin=False)
        self.assertEqual(status, 200)
        self.assertIn(b"dashboard fixture", contents)
        self.assertEqual(self.request("/%2e%2e/keep.txt", auth=False)[0], 404)
        self.assertEqual(self.request("/", headers={"Host": "elsewhere.invalid"})[0], 403)

    def test_request_size_and_content_type(self):
        self.assertEqual(self.request("/api/clear", {}, {"Content-Length": "65537"})[0], 400)
        self.assertEqual(self.request("/api/clear", {}, {"Content-Type": "text/plain"})[0], 400)
        self.assertEqual(self.request("/api/clear", {}, {"Transfer-Encoding": "chunked"})[0], 400)

    def test_private_report_directory_session_and_source_files(self):
        self.assertEqual(self.report.stat().st_mode & 0o777, 0o700)
        for name in ("summary.json", "scan.json", "review-session.json"):
            self.assertEqual((self.report / name).stat().st_mode & 0o777, 0o600)
        session = json.loads((self.report / "review-session.json").read_text())
        self.assertIn("#token=", session["url"])
        self.assertEqual(session["port"], self.server.server_port)
        self.assertEqual(self.server.server_address[0], "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
