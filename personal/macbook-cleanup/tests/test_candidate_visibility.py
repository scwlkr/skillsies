"""Largest items and model explanations remain visible without blanket deletion."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from cleanup_items import build_items


class VisibilityTests(unittest.TestCase):
    def test_large_models_precede_small_selectable_builds_and_keep_next_step(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            models = home / '.ollama/models'
            models.mkdir(parents=True)
            build = home / 'project/target'
            build.mkdir(parents=True)
            (build.parent / 'Cargo.toml').write_text('[package]\n')
            rows = [{'path': str(build), 'category': 'build', 'allocated_bytes': 8192},
                    {'path': str(models), 'category': 'models', 'allocated_bytes': 1024**3,
                     'action': 'List models and remove selected unused models through Ollama.'}]
            items = build_items({'candidates': rows}, {}, home)
            self.assertEqual(items[0]['path'], str(models))
            self.assertFalse(items[0]['selectable'])
            self.assertIn('not one model', items[0]['reason'])
            self.assertIn('Ollama', items[0]['next_step'])
            self.assertTrue(items[1]['selectable'])

    def test_each_recognized_model_root_explains_aggregate_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            rows = []
            for relative in ('.ollama/models', '.lmstudio/models', '.cache/huggingface'):
                path = home / relative
                path.mkdir(parents=True)
                rows.append({'path': str(path), 'category': 'models', 'allocated_bytes': 8192})
            items = build_items({'candidates': rows}, {}, home)
            self.assertEqual(len(items), 3)
            for row in items:
                self.assertFalse(row['selectable'])
                self.assertIn('individual model identities', row['reason'])


if __name__ == '__main__':
    unittest.main()
