import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock

import yaml


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / 'files' / (name + '.py'))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


health = module('autorestic-health')
guard = module('autorestic-guard')
NOW = dt.datetime(2026, 10, 3, 18, tzinfo=dt.timezone.utc)


def snapshot(hours=1, host='gaara', path='/data'):
    return {'id': 'abcdef123456', 'time': (NOW - dt.timedelta(hours=hours)).isoformat(),
            'hostname': host, 'paths': [path]}


class RecoveryTests(unittest.TestCase):
    def test_restic_nanosecond_timestamp_is_compatible_with_python39(self):
        self.assertEqual(health.timestamp('2026-10-03T17:49:43.53334642Z').microsecond, 533346)
        self.assertEqual(health.timestamp('2026-10-03T17:49:43.5Z').microsecond, 500000)

    def test_stale_lock_recovery_preserves_cron_and_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.autorestic.lock.yml'
            original = {'running': True, 'cron': {'cloud': 12345}}
            path.write_text(yaml.safe_dump(original))
            self.assertTrue(guard.recover(path, []))
            self.assertEqual(yaml.safe_load(path.read_text()), {'running': False, 'cron': {'cloud': 12345}})
            saved = next(Path(directory).glob('*.recovered-*'))
            self.assertEqual(yaml.safe_load(saved.read_text()), original)
            self.assertFalse(guard.recover(path, []))

    def test_running_process_prevents_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'lock'
            path.write_text('running: true\ncron: {cloud: 12345}\n')
            original = path.read_bytes()
            with self.assertRaises(RuntimeError):
                guard.recover(path, [123])
            self.assertEqual(path.read_bytes(), original)

    def test_fresh_snapshot_does_not_hide_another_stale_location(self):
        self.assertTrue(health.assess([snapshot()], ['/data'], 'gaara', '36', {}, NOW)[0])
        self.assertFalse(health.assess([snapshot(37)], ['/data'], 'gaara', 36, {}, NOW)[0])

    def test_wrong_host_or_paths_do_not_count_as_backup(self):
        for candidate in [snapshot(host='other'), snapshot(path='/wrong'), snapshot(-1)]:
            self.assertFalse(health.assess([candidate], ['/data'], 'gaara', 36, {}, NOW)[0])

    def test_failed_attempt_is_unhealthy_even_with_fresh_partial_snapshot(self):
        event = {'status': 'failure', 'time': NOW.isoformat()}
        self.assertFalse(health.assess([snapshot()], ['/data'], 'gaara', 36, event, NOW)[0])

    def test_all_repositories_must_pass_for_aggregate_success(self):
        with tempfile.TemporaryDirectory() as directory:
            config = {'locations': {'good': {'from': '/data', 'to': 'a'}, 'bad': {'from': '/data', 'to': 'b'}}}
            settings = {'state_directory': directory, 'aggregate_push_url': 'aggregate', 'location_push_urls': {'good': 'good', 'bad': 'bad'}}
            checker = health.Health(config, settings)
            current = snapshot(host=health.socket.gethostname())
            current['time'] = dt.datetime.now(dt.timezone.utc).isoformat()
            checker.restic = Mock(side_effect=[types.SimpleNamespace(returncode=0, stdout=json.dumps([current])),
                                               types.SimpleNamespace(returncode=1, stdout=b'')])
            checker.push = Mock()
            self.assertEqual(checker.check(), 1)
            self.assertFalse(checker.push.call_args.args[1])
            report = health.load_json(Path(directory) / 'latest.json')['locations']
            self.assertTrue(report['good']['ok'])
            self.assertFalse(report['bad']['ok'])

    def test_success_hook_cannot_mark_aggregate_healthy(self):
        with tempfile.TemporaryDirectory() as directory:
            checker = health.Health({'locations': {'cloud': {}}}, {'state_directory': directory})
            checker.push = Mock()
            checker.event('cloud', 'success')
            checker.push.assert_not_called()
            self.assertEqual(health.load_json(Path(directory) / 'events.json')['cloud']['status'], 'success')


if __name__ == '__main__':
    unittest.main()
