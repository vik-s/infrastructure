#!/usr/bin/env python3
"""Additive replication: no rollback, force-delete, pruning, or target mounts."""
import datetime
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

CONFIG = pathlib.Path('/etc/syncoid/config.json')
STATE = pathlib.Path('/var/lib/syncoid-health')


def save(name, value):
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(dir=STATE)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2)
    os.replace(path, STATE / name)


def read(name, default):
    try:
        return json.loads((STATE / name).read_text())
    except FileNotFoundError:
        return default


def ssh(config):
    return ['ssh', '-i', config['ssh_key'], '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=15',
            config['source_host']]


def output(argv, config=None):
    if config:
        argv = ssh(config) + [shlex.join(['sudo', '-n'] + argv)]
    return subprocess.check_output(argv, text=True, timeout=180, stderr=subprocess.PIPE)


def target(config, source):
    root = config['target_root']
    if not re.fullmatch(r'tank/[A-Za-z0-9_-]+', root):
        raise ValueError('Target must be a dedicated child of tank')
    if source == 'rpool/docker':
        return root + '/docker'
    if source.startswith('tank/') and all(re.fullmatch(r'[A-Za-z0-9_.:-]+', x) for x in source.split('/')):
        if source.split('/')[1] == 'docker':
            raise ValueError('Source tank/docker conflicts with rpool/docker mapping')
        return root + '/' + source[5:]
    raise ValueError('Unexpected source dataset')


def datasets(config):
    rows = output(['zfs', 'list', '-H', '-p', '-t', 'filesystem', '-o', 'name,refer', '-r', 'tank'], config)
    items = [(name, int(size)) for name, size in (line.split('\t') for line in rows.splitlines()) if name != 'tank']
    docker = output(['zfs', 'list', '-H', '-p', '-o', 'name,refer', 'rpool/docker'], config).strip().split('\t')
    items.append((docker[0], int(docker[1])))
    # Replicate small datasets first, and parents before children.
    return sorted(items, key=lambda row: (row[0].count('/'), row[1]))


def snapshots(config=None):
    roots = ['tank', 'rpool/docker'] if config else ['tank']
    rows = output(['zfs', 'list', '-H', '-p', '-t', 'snapshot', '-o', 'name,creation,guid', '-r'] + roots, config)
    result = {}
    for line in rows.splitlines():
        name, created, guid = line.split('\t')
        dataset, snap = name.split('@', 1)
        result.setdefault(dataset, []).append({'name': snap, 'created': int(created), 'guid': guid})
    return result


def compare(source, destination, now, max_age):
    guids = {s['guid'] for s in source}
    common = [s for s in destination if s['guid'] in guids]
    if not common:
        return {'ok': False, 'message': 'No replicated snapshot with a matching source GUID'}
    newest = max(common, key=lambda s: s['created'])
    age = (now - newest['created']) / 3600
    return {'ok': 0 <= age <= max_age, 'snapshot': newest['name'],
            'guid': newest['guid'], 'age_hours': round(age, 2)}


def push(config, ok, message):
    parsed = urllib.parse.urlsplit(config['monitor_url'])
    query = dict(urllib.parse.parse_qsl(parsed.query))
    query.update(status='up' if ok else 'down', msg=message)
    url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))
    with urllib.request.urlopen(url, timeout=20) as response:
        if not json.load(response).get('ok'):
            raise RuntimeError('Monitoring rejected heartbeat')


def check(config):
    try:
        wanted = datasets(config)
        source, destination = snapshots(config), snapshots()
        statuses = {name: compare(source.get(name, []), destination.get(target(config, name), []),
                                  time.time(), float(config['max_age_hours'])) for name, _ in wanted}
        last = read('run.json', {})
        failed = [name for name, code in last.get('results', {}).items() if code]
        ok = bool(statuses) and all(row['ok'] for row in statuses.values()) and not failed
        report = {'ok': ok, 'datasets': statuses, 'last_run_failures': failed}
        message = '{}/{} datasets have fresh matching snapshots'.format(sum(s['ok'] for s in statuses.values()), len(statuses))
        if failed:
            message += '; last transfer failed: ' + ', '.join(failed)
    except Exception as exc:
        ok = False
        report = {'ok': False, 'error': type(exc).__name__}
        message = 'Replication verification failed: ' + type(exc).__name__
    report['checked_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save('latest.json', report)
    print(message, flush=True)
    push(config, ok, message)
    return 0 if ok else 1


def command(config, source, initial=False):
    return ['/usr/sbin/syncoid', '--no-rollback', '--no-sync-snap',
            '--recvoptions=u o readonly=on o mountpoint=none',
            '--sshoption=BatchMode=yes', '--sshoption=StrictHostKeyChecking=yes',
            '--sshoption=ConnectTimeout=15', '--sshkey=' + config['ssh_key'],
            config['source_host'] + ':' + source, target(config, source)] + (['--no-stream'] if initial else [])


def run(config):
    record = {'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'results': read('run.json', {}).get('results', {}).copy()}
    try:
        # Root is created by deployment; fail if it can be written or mounted.
        properties = output(['zfs', 'get', '-H', '-o', 'value', 'readonly,mountpoint', config['target_root']]).splitlines()
        if properties != ['on', 'none']:
            raise RuntimeError('Unsafe replication root properties')
        existing_snapshots = snapshots()
        for source, _ in datasets(config):
            print('Replicating ' + source + ' -> ' + target(config, source), flush=True)
            code = subprocess.run(command(config, source, initial=not existing_snapshots.get(target(config, source)))).returncode
            record['results'][source] = code
            save('run.json', record)
            if code:
                push(config, False, 'Replication failed: ' + source)
        record['results'].pop('runner', None)
        record['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save('run.json', record)
    except Exception as exc:
        record['results']['runner'] = 1
        record['error'] = type(exc).__name__
        save('run.json', record)
        print('Replication runner failed: ' + type(exc).__name__, flush=True)
    return check(config)


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('run', 'check'):
        raise SystemExit('Usage: replicate.py run|check')
    try:
        config = json.loads(CONFIG.read_text())
        code = run(config) if sys.argv[1] == 'run' else check(config)
    except Exception as exc:
        print('Replication monitoring failed: ' + type(exc).__name__, file=sys.stderr)
        code = 1
    raise SystemExit(code)
