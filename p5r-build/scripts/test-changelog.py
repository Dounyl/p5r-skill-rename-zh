import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('packager', Path(__file__).with_name('package-release.py'))
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class ChangelogTests(unittest.TestCase):
    def test_only_current_version_and_history_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '0.4.4.md').write_text('# 0.4.4\n\n## Fixed\n\n- Current\n', encoding='utf-8')
            (root / '0.4.3.md').write_text('# 0.4.3\n\n- Historical\n', encoding='utf-8')
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            self.assertEqual(packager.release_changes(root, '0.4.4'), '## Fixed\n\n- Current')
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    def test_invalid_notes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                packager.release_changes(root, '0.4.4')
            for text in ('# 0.4.3\n- Wrong', '# 0.4.4\n', '# 0.4.4\n<!-- pending -->', '# 0.4.4\n- New\n# 0.4.3\n- Old'):
                with self.subTest(text=text):
                    (root / '0.4.4.md').write_text(text, encoding='utf-8')
                    with self.assertRaises(ValueError):
                        packager.release_changes(root, '0.4.4')


if __name__ == '__main__':
    unittest.main()
