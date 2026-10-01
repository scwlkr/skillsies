"""Build the pinned shadcn UI once, then export a self-contained private report."""
import fcntl
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from cleanup_items import build_items

ROOT = Path(__file__).resolve().parents[1] / "dashboard"


def build():
    sources = [ROOT / name for name in ("package.json", "package-lock.json", "vite.config.ts", "tsconfig.json", "index.html")]
    sources += sorted(path for path in (ROOT / "src").rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for source in sources:
        digest.update(str(source.relative_to(ROOT)).encode())
        digest.update(source.read_bytes())
    signature = digest.hexdigest()
    ROOT.mkdir(parents=True, exist_ok=True)
    with (ROOT / ".build.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        stamp = ROOT / "dist/source.sha256"
        if stamp.is_file() and stamp.read_text() == signature and (ROOT / "dist/index.html").is_file():
            return ROOT / "dist"
        npm = shutil.which("npm")
        if not npm:
            raise RuntimeError("Node.js/npm is required for the first dashboard build. The Markdown report remains available.")
        print("Building shadcn dashboard (cached for subsequent runs)…", file=sys.stderr)
        # npm ci also repairs an incomplete or stale dependency tree.
        subprocess.run([npm, "ci", "--no-audit", "--no-fund"], cwd=ROOT, check=True,
                       stdout=sys.stderr, timeout=600)
        subprocess.run([npm, "run", "build"], cwd=ROOT, check=True, stdout=sys.stderr, timeout=300)
        stamp.write_text(signature)
    return ROOT / "dist"


def export(summary, scan, output, assets=None):
    assets = Path(assets or build()).resolve()
    session = {"summary": summary, "scan": scan, "items": build_items(summary, scan),
               "status": {"state": "ready"}, "preview": True}
    # Escape before embedding JSON in an executable script context.
    payload = json.dumps(session, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    source = (assets / "index.html").read_text()
    def inline_script(match):
        file = (assets / match.group(1).removeprefix("./")).resolve()
        if not file.is_relative_to(assets):
            raise ValueError("Dashboard asset escaped its build directory")
        js = file.read_text().replace("</script", "<\\/script")
        return f'<script>window.__MACBOOK_REPORT__={payload};</script><script type="module">{js}</script>'
    def inline_css(match):
        file = (assets / match.group(1).removeprefix("./")).resolve()
        if not file.is_relative_to(assets):
            raise ValueError("Dashboard stylesheet escaped its build directory")
        return '<style>' + file.read_text().replace("</style", "<\\/style") + '</style>'
    source = re.sub(r'<script[^>]*src="([^"]+)"[^>]*></script>', inline_script, source)
    source = re.sub(r'<link[^>]*rel="stylesheet"[^>]*href="([^"]+)"[^>]*>', inline_css, source)
    policy = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'"
    source = source.replace('<head>', f'<head><meta http-equiv="Content-Security-Policy" content="{policy}">')
    Path(output).write_text(source, encoding="utf-8")
    Path(output).chmod(0o600)
    return str(output)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args()
    assets = build()
    if args.report_dir:
        report = args.report_dir
        export(json.loads((report / "summary.json").read_text()),
               json.loads((report / "scan.json").read_text()), report / "report.html", assets)
