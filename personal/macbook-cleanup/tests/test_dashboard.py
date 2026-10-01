import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import dashboard
import scan


class DashboardTests(unittest.TestCase):
    def test_export_is_self_contained_and_escapes_script_closing_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'index.html').write_text('<html><head><script type="module" src="./main.js"></script><link rel="stylesheet" href="./main.css"></head><body><div id="root"></div></body></html>')
            (root / 'main.js').write_text('console.log("bundle")')
            (root / 'main.css').write_text('body{color:white}')
            output = root / 'report.html'
            summary = {'candidates': [], 'assessment': '</script><img src=x onerror=alert(1)>'}
            dashboard.export(summary, {}, output, root)
            html = output.read_text()
            self.assertIn('window.__MACBOOK_REPORT__=', html)
            self.assertIn('\\u003c/script\\u003e', html)
            self.assertNotIn('<img src=x', html)
            self.assertNotIn('src="./main.js"', html)
            self.assertNotIn('href="./main.css"', html)
            self.assertIn("connect-src 'none'", html)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_admin_only_elevates_scanner_with_existing_authentication(self):
        with patch.object(scan.subprocess, 'run') as command:
            self.assertEqual(scan.scanner_command(['/scanner', '--root', '/Data'], False), ['/scanner', '--root', '/Data'])
            command.assert_not_called()
            self.assertEqual(scan.scanner_command(['/scanner'], True), ['/usr/bin/sudo', '-n', '/scanner'])
            command.assert_called_once_with(['/usr/bin/sudo', '-n', 'true'], check=True, timeout=10)
