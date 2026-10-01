#!/usr/bin/env python3
"""Loopback-only dashboard and explicit batch-consent API; no remote telemetry."""
import argparse
import json
import mimetypes
import os
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    from .cleanup_items import build_items
    from .cleanup_plan import SafetyError, create_plan, private_json, public_plan, validate_confirmation
    from .cleanup_execute import execute
except ImportError:
    from cleanup_items import build_items
    from cleanup_plan import SafetyError, create_plan, private_json, public_plan, validate_confirmation
    from cleanup_execute import execute

MAX_BODY = 65536


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, report_dir, port=0, preview=False, home=None, assets=None):
        self.report_dir = Path(report_dir).resolve()
        if not self.report_dir.is_dir():
            raise ValueError("Report directory does not exist")
        os.chmod(self.report_dir, 0o700)
        self.home = Path(home or Path.home()).resolve()
        self.assets = Path(assets or Path(__file__).resolve().parents[1] / "dashboard/dist").resolve()
        self.summary = self.read_report("summary.json")
        self.scan = self.read_report("scan.json")
        self.items = build_items(self.summary, self.scan, self.home)
        self.preview, self.plan = preview, None
        self.status = {"state": "ready", "preview": preview}
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        self.finished, self.observed = threading.Event(), threading.Event()
        super().__init__(("127.0.0.1", port), ReviewHandler)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.url = f"{self.origin}/#token={self.token}"
        private_json(self.report_dir / "review-session.json",
                     {"url": self.url, "port": self.server_port, "pid": os.getpid(), "preview": preview})

    def read_report(self, name):
        path = self.report_dir / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"A regular local {name} is required")
        os.chmod(path, 0o600)
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
        if not isinstance(value, dict):
            raise ValueError(f"Invalid {name}")
        return value


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "LocalReview"

    def log_message(self, format, *args):
        pass  # Private paths and bearer tokens do not enter request logs.

    def response(self, code, value, kind="application/json"):
        body = json.dumps(value).encode() if kind == "application/json" else value
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def authorize(self, mutation=False):
        if self.headers.get("Host") != self.server.origin.removeprefix("http://"):
            self.response(403, {"error": "Unexpected host"})
            return False
        origin = self.headers.get("Origin")
        if (mutation and origin != self.server.origin) or (origin and origin != self.server.origin):
            self.response(403, {"error": "Same-origin request required"})
            return False
        supplied = self.headers.get("Authorization", "")
        if not secrets.compare_digest(supplied, f"Bearer {self.server.token}"):
            self.response(401, {"error": "Local session authorization required"})
            return False
        return True

    def do_GET(self):
        path = urlsplit(self.path).path
        if path.startswith("/api/"):
            if not self.authorize():
                return
            if path == "/api/session":
                self.response(200, {"summary": self.server.summary, "scan": self.server.scan,
                                    "items": self.server.items, "status": self.server.status,
                                    "preview": self.server.preview})
            elif path == "/api/status":
                self.response(200, self.server.status)
                if self.server.finished.is_set():
                    self.server.observed.set()
            else:
                self.response(404, {"error": "Unknown endpoint"})
            return
        if self.headers.get("Host") != self.server.origin.removeprefix("http://"):
            self.response(403, {"error": "Unexpected host"})
            return
        requested = unquote(path).lstrip("/") or "index.html"
        file = (self.server.assets / requested).resolve()
        if not file.is_relative_to(self.server.assets) or not file.is_file():
            self.response(404, {"error": "Dashboard asset unavailable; build dashboard first"})
            return
        self.response(200, file.read_bytes(), mimetypes.guess_type(str(file))[0] or "application/octet-stream")

    def payload(self):
        if self.headers.get("Transfer-Encoding"):
            raise SafetyError("Transfer encoding is not supported")
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise SafetyError("JSON content type required")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise SafetyError("Invalid content length") from exc
        if not 0 < length <= MAX_BODY:
            raise SafetyError("Request body exceeds limit or is empty")
        self.connection.settimeout(10)
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise SafetyError("JSON object required")
        return value

    def do_POST(self):
        if not self.authorize(mutation=True):
            return
        try:
            payload = self.payload()
            path = urlsplit(self.path).path
            with self.server.lock:
                if path == "/api/plan":
                    if self.server.finished.is_set():
                        raise SafetyError("Session is complete; rescan for another cleanup")
                    self.server.plan = create_plan(payload.get("ids"), self.server.items, self.server.home)
                    self.server.status = {"state": "planned", "preview": self.server.preview,
                                          "plan": public_plan(self.server.plan)}
                    self.response(200, public_plan(self.server.plan))
                elif path == "/api/confirm":
                    # Invalid consent must not alter a valid pending plan or authorize a later call.
                    validate_confirmation(self.server.plan, payload)
                    self.server.status = {"state": "running", "preview": self.server.preview}
                    from_cleanup = execute(self.server.plan, payload, self.server.report_dir,
                                           self.server.home, self.server.preview,
                                           self.server.summary["capacity"].get("target_percent", 50))
                    self.server.status = from_cleanup
                    self.server.finished.set()
                    print(json.dumps({"event": "cleanup-result", "result": from_cleanup}), flush=True)
                    self.response(200, from_cleanup)
                elif path == "/api/clear":
                    if self.server.finished.is_set():
                        raise SafetyError("Session is complete")
                    self.server.plan = None
                    self.server.status = {"state": "ready", "preview": self.server.preview}
                    self.response(200, self.server.status)
                else:
                    self.response(404, {"error": "Unknown endpoint"})
        except (ValueError, OSError, TimeoutError) as exc:
            self.response(400, {"error": str(exc)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", required=True, type=Path)
    parser.add_argument("--port", default=0, type=int)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="Print the local URL without opening a browser")
    parser.add_argument("--wait", action="store_true", help="Exit after final consent and a status polling grace period")
    args = parser.parse_args()
    server = ReviewServer(args.report_dir, args.port, args.preview)
    print(json.dumps({"event": "review-ready", "url": server.url, "preview": args.preview}), flush=True)
    if not args.no_open:
        webbrowser.open(server.url)
    try:
        if args.wait:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            server.finished.wait()
            server.observed.wait(10)
            server.shutdown()
            worker.join()
        else:
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
