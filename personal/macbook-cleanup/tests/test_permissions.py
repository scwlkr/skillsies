import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import permissions


class PermissionsTests(unittest.TestCase):
    def test_full_disk_access_cannot_be_substituted_by_sudo(self):
        with patch.object(permissions.sys.stdin, 'isatty', return_value=True), \
                patch.object(permissions, 'access_status', return_value={'blocked':['Mail']}), \
                patch('builtins.input', return_value='s'), \
                patch.object(permissions, 'open_settings') as settings, \
                patch.object(permissions.subprocess, 'run') as sudo, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertFalse(permissions.request_access(True))
        settings.assert_called_once()
        sudo.assert_not_called()
        self.assertIn('quit/reopen', output.getvalue())

    def test_one_native_admin_prompt_after_access_probe(self):
        with patch.object(permissions.sys.stdin, 'isatty', return_value=True), \
                patch.object(permissions, 'access_status', return_value={'blocked':[]}), \
                patch.object(permissions.subprocess, 'run') as sudo, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(permissions.request_access(True))
        sudo.assert_called_once_with(['/usr/bin/sudo','-v'], check=True)

    def test_partial_access_requires_explicit_choice(self):
        for choice, expected in [('c',True),('q',False),('',False)]:
            with self.subTest(choice=choice), \
                    patch.object(permissions.sys.stdin, 'isatty', return_value=True), \
                    patch.object(permissions, 'access_status', return_value={'blocked':['Mail']}), \
                    patch('builtins.input', return_value=choice), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(permissions.request_access(), expected)

    def test_noninteractive_authentication_is_never_attempted(self):
        with patch.object(permissions.sys.stdin, 'isatty', return_value=False), \
                patch.object(permissions.subprocess, 'run') as sudo:
            with self.assertRaises(RuntimeError):
                permissions.request_access(True)
        sudo.assert_not_called()
