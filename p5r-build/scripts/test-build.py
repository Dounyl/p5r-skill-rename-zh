"""Check the new builder against the preserved pre-migration table."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('builder', Path(__file__).with_name('build-mod.py'))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'build'
        self.mod = Path(self.directory.name) / 'mod'
        for folder in (self.root / 'config', self.root / 'input', self.mod):
            folder.mkdir(parents=True)
        for name in ('config/changes.json', 'config/naming-guide.md', 'input/SC-NAME.TBL'):
            shutil.copyfile(builder.ROOT / name, self.root / name)
        shutil.copyfile(builder.MOD / 'ModConfig.json', self.mod / 'ModConfig.json')

    def build(self):
        with patch.object(builder, 'ROOT', self.root), patch.object(builder, 'MOD', self.mod):
            builder.build()

    def test_current_table_matches_existing_mod(self):
        self.build()
        self.assertEqual((self.mod / 'Data/NAME.TBL').read_bytes(), (builder.MOD / 'Data/NAME.TBL').read_bytes())
        report = json.loads((self.root / 'temp/current/changes.json').read_text(encoding='utf-8'))
        self.assertEqual(report['changed_entries'], 522)

    def test_duplicate_and_wrong_original_do_not_write_output(self):
        path = self.root / 'config/changes.json'
        original = json.loads(path.read_text(encoding='utf-8'))
        for failure in ('duplicate', 'old_name'):
            rules = json.loads(json.dumps(original))
            if failure == 'duplicate':
                rules['changes'].append(rules['changes'][0])
            else:
                rules['changes'][0]['old'] = 'incorrect original'
            path.write_text(json.dumps(rules), encoding='utf-8')
            with self.assertRaises(ValueError):
                self.build()
            self.assertFalse((self.mod / 'Data').exists())


if __name__ == '__main__':
    unittest.main()
