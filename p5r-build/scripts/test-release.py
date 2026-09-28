"""Offline tests: never call Git or GitHub."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def simulate(self, failure=None):
        calls = []
        config = json.loads((release.ROOT / 'p5rpc.skillrename/ModConfig.json').read_text(encoding='utf-8-sig'))
        tag = 'v' + config['ModVersion']
        folder = release.ROOT / 'p5r-build/dist' / tag

        def command(*args):
            calls.append(args)
            if args[:4] == ('git', 'remote', 'get-url', 'origin'):
                return 'https://github.com/example/mod.git'
            if args[:2] == ('git', 'rev-parse'):
                return 'a' * 40
            if args[:2] == ('git', 'symbolic-ref'):
                return 'main'
            if args[:2] == ('git', 'status'):
                return ' M changelog/0.4.4.md' if failure == 'dirty' else ''
            if args[:3] == ('gh', 'release', 'list'):
                return json.dumps([{'tagName': tag, 'isDraft': False}]) if failure == 'existing' else '[]'
            if args[:3] == ('git', 'ls-remote', '--heads'):
                return 'a' * 40 + '\trefs/heads/main'
            if args[:3] == ('gh', 'release', 'create') and failure == 'upload':
                raise ValueError('simulated upload failure')
            if args[:3] == ('gh', 'release', 'view'):
                if args[-1] == 'assets':
                    assets = [{'name': p.name, 'size': p.stat().st_size} for p in
                              (folder / f'p5rpc.skillrename-{tag}.zip', folder / 'SHA256SUMS.txt')]
                    return json.dumps({'assets': [] if failure == 'assets' else assets})
                return json.dumps({'isDraft': False, 'url': 'https://github.com/example/mod/releases/' + tag})
            return ''

        with patch.object(release.shutil, 'which', return_value='available'), patch.object(release, 'run', side_effect=command):
            if failure:
                with self.assertRaises(ValueError):
                    release.publish()
            else:
                release.publish()
        return calls

    def test_publish_order_and_notes(self):
        calls = self.simulate()
        push = next(i for i, c in enumerate(calls) if c[:2] == ('git', 'push'))
        create = next(i for i, c in enumerate(calls) if c[:3] == ('gh', 'release', 'create'))
        publish = next(i for i, c in enumerate(calls) if c[:3] == ('gh', 'release', 'edit'))
        self.assertLess(push, create)
        self.assertLess(create, publish)
        self.assertIn('--notes-file', calls[create])
        self.assertIn('--draft', calls[create])
        self.assertIn('--target', calls[create])
        self.assertIn('a' * 40, calls[create])

    def test_failures_do_not_publish(self):
        for failure in ('dirty', 'existing', 'upload', 'assets'):
            with self.subTest(failure=failure):
                calls = self.simulate(failure)
                self.assertFalse(any(c[:3] == ('gh', 'release', 'edit') for c in calls))
                if failure in ('dirty', 'existing'):
                    self.assertFalse(any(c[:2] == ('git', 'push') for c in calls))


if __name__ == '__main__':
    unittest.main()
