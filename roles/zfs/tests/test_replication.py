import importlib.util
import pathlib
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('replication', pathlib.Path(__file__).parents[1] / 'files/replicate.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReplicationSafety(unittest.TestCase):
    def setUp(self):
        self.config = dict(target_root='tank/gaara', source_host='host', ssh_key='/key')

    def test_names_are_not_sufficient_without_guid_match(self):
        src = [dict(name='same', created=100, guid='a')]
        dst = [dict(name='same', created=100, guid='b')]
        self.assertFalse(m.compare(src, dst, 101, 36)['ok'])

    def test_matching_but_stale_snapshot_fails(self):
        snaps = [dict(name='copy', created=100, guid='a')]
        self.assertFalse(m.compare(snaps, snaps, 100 + 37 * 3600, 36)['ok'])
        self.assertTrue(m.compare(snaps, snaps, 200, 36)['ok'])

    def test_preserves_legacy_destinations_and_rejects_collision(self):
        self.assertEqual(m.target(self.config, 'tank/cloud'), 'tank/gaara/cloud')
        self.assertEqual(m.target(self.config, 'rpool/docker'), 'tank/gaara/docker')
        for name in ['tank/docker', 'rpool', 'tank/cloud;touch']:
            with self.assertRaises(ValueError):
                m.target(self.config, name)

    def test_fresh_snapshots_do_not_hide_a_failed_transfer(self):
        self.config['max_age_hours'] = 36
        snap = dict(name='copy', created=100, guid='a')
        with mock.patch.object(m, 'datasets', return_value=[('tank/cloud', 1)]), \
             mock.patch.object(m, 'snapshots', side_effect=[{'tank/cloud': [snap]}, {'tank/gaara/cloud': [snap]}]), \
             mock.patch.object(m.time, 'time', return_value=200), \
             mock.patch.object(m, 'read', return_value={'results': {'tank/cloud': 1}}), \
             mock.patch.object(m, 'save'), mock.patch.object(m, 'push') as push:
            self.assertEqual(m.check(self.config), 1)
            self.assertFalse(push.call_args.args[1])

    def test_no_rollback_and_initial_latest_only_then_intermediate_snapshots(self):
        cmd = m.command(self.config, 'tank/cloud', initial=True)
        self.assertIn('--no-rollback', cmd)
        self.assertIn('--no-stream', cmd)
        self.assertNotIn('--force-delete', cmd)
        self.assertNotIn('-F', cmd)
        self.assertIn('--recvoptions=u o readonly=on o mountpoint=none', cmd)
        self.assertNotIn('--no-stream', m.command(self.config, 'tank/cloud'))


if __name__ == '__main__':
    unittest.main()
