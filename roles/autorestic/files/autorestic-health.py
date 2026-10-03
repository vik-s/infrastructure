#!/usr/bin/env python3
"""Check each repository independently and report backup health to Uptime Kuma."""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

import yaml

UTC = dt.timezone.utc


def atomic_json(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as output:
            json.dump(value, output, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def timestamp(value):
    # Restic emits nanoseconds; Python 3.9 accepts only millisecond/microsecond
    # fractions, unlike newer Python versions which silently truncate them.
    value = re.sub(r'\.(\d+)(?=Z|[+-])', lambda m: '.' + m.group(1)[:6].ljust(6, '0'), value)
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


def assess(snapshots, paths, hostname, max_hours, event, now):
    matching = [s for s in snapshots if s.get('hostname') == hostname and set(s.get('paths', [])) == set(paths)]
    if not matching:
        return False, 'No snapshot for the expected host and paths'
    latest = max(matching, key=lambda s: timestamp(s['time']))
    age = (now - timestamp(latest['time'])).total_seconds() / 3600
    if age < -0.1:
        return False, 'Snapshot timestamp is in the future; check clock synchronization'
    if event.get('status') == 'failure':
        return False, 'Latest backup attempt failed at ' + event['time']
    summary = 'snapshot %s, age %.1fh' % (latest['id'][:8], age)
    return age <= float(max_hours), summary


class Health:
    def __init__(self, config, settings):
        self.config = config
        self.settings = settings
        self.state = Path(settings.get('state_directory', '/var/lib/autorestic-health'))
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)

    def restic(self, backend, arguments, timeout):
        b = self.config['backends'][backend]
        env = os.environ.copy()
        env.update({str(k).upper(): str(v) for k, v in b.get('env', {}).items()})
        env['RESTIC_PASSWORD'] = str(b['key'])
        env['RESTIC_REPOSITORY'] = b['type'] + ':' + b['path']
        return subprocess.run([self.settings['restic_binary'], *arguments], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)

    def push(self, url, ok, message):
        if not url:
            return
        parts = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(parts.query))
        query.update(status='up' if ok else 'down', msg=message[:2000])
        endpoint = urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))
        # Never print the endpoint: its path contains a bearer token.
        try:
            with urllib.request.urlopen(endpoint, timeout=15) as response:
                result = json.load(response)
            if result.get('ok') is not True:
                raise RuntimeError('Push rejected')
        except Exception as error:
            raise RuntimeError('Uptime Kuma push failed (' + type(error).__name__ + ')') from None

    def event(self, location, status):
        if location not in self.config['locations']:
            raise ValueError('Unknown backup location')
        with open(self.state / 'events.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            events = load_json(self.state / 'events.json')
            events[location] = {'status': status, 'time': dt.datetime.now(UTC).isoformat()}
            atomic_json(self.state / 'events.json', events)
        # Success is reported only after querying the remote snapshot independently.
        if status == 'failure':
            message = location + ': backup failed; inspect autorestic.service logs'
            self.push(self.settings.get('location_push_urls', {}).get(location), False, message)
            self.push(self.settings.get('aggregate_push_url'), False, message)

    def check(self):
        events = load_json(self.state / 'events.json')
        integrity = load_json(self.state / 'integrity.json')
        results = {}
        now = dt.datetime.now(UTC)
        for name, location in self.config['locations'].items():
            paths = location['from'] if isinstance(location['from'], list) else [location['from']]
            backends = location['to'] if isinstance(location['to'], list) else [location['to']]
            messages = []
            ok = True
            for backend in backends:
                try:
                    arguments = ['--no-lock', 'snapshots', '--json', '--latest', '1',
                                 '--host', socket.gethostname()]
                    for path in paths:
                        arguments.extend(['--path', path])
                    reply = self.restic(backend, arguments, 180)
                    if reply.returncode:
                        raise RuntimeError('Snapshot query failed (exit %d)' % reply.returncode)
                    healthy, message = assess(json.loads(reply.stdout), paths, socket.gethostname(),
                                              self.settings.get('max_age_hours', 36), events.get(name, {}), now)
                    if integrity.get(backend, {}).get('ok') is False:
                        healthy = False
                        message += '; last repository integrity check failed'
                    ok = ok and healthy
                    messages.append(backend + ': ' + message)
                except Exception as error:
                    ok = False
                    messages.append(backend + ': ' + (str(error) if isinstance(error, RuntimeError) else type(error).__name__))
            message = name + ': ' + '; '.join(messages)
            results[name] = {'ok': ok, 'message': message}
            print(('OK ' if ok else 'FAIL ') + message, flush=True)
            try:
                self.push(self.settings.get('location_push_urls', {}).get(name), ok, message)
            except RuntimeError as error:
                results[name]['ok'] = False
                print(str(error), file=sys.stderr)
        atomic_json(self.state / 'latest.json', {'checked_at': now.isoformat(), 'locations': results})
        failures = [r['message'] for r in results.values() if not r['ok']]
        self.push(self.settings.get('aggregate_push_url'), not failures,
                  '; '.join(failures) if failures else 'All %d backup locations have fresh snapshots' % len(results))
        return 1 if failures else 0

    def integrity(self, selected):
        results = load_json(self.state / 'integrity.json')
        failed = False
        for backend in selected or self.config['backends']:
            previous = results.get(backend, {})
            if not selected and previous.get('ok') and (dt.datetime.now(UTC) - timestamp(previous['checked_at'])).days < 7:
                continue
            try:
                result = self.restic(backend, ['check', '--read-data-subset=' +
                                               self.settings.get('integrity_read_data_subset', '64M')], 21600)
                ok = result.returncode == 0
            except Exception:
                ok = False
            results[backend] = {'ok': ok, 'checked_at': dt.datetime.now(UTC).isoformat()}
            atomic_json(self.state / 'integrity.json', results)
            print(('OK ' if ok else 'FAIL ') + 'repository integrity: ' + backend, flush=True)
            if not ok:
                failed = True
                self.push(self.settings.get('aggregate_push_url'), False, 'Repository integrity check failed: ' + backend)
        return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('/etc/autorestic/.autorestic.yaml'))
    parser.add_argument('--settings', type=Path, default=Path('/etc/autorestic/monitoring.yaml'))
    parser.add_argument('command', choices=['check', 'success', 'failure', 'integrity'])
    parser.add_argument('--backend', action='append')
    args = parser.parse_args()
    health = Health(yaml.safe_load(args.config.read_text()), yaml.safe_load(args.settings.read_text()))
    if args.command == 'check':
        return health.check()
    if args.command == 'integrity':
        return health.integrity(args.backend)
    health.event(os.environ['AUTORESTIC_LOCATION'], args.command)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('Backup health checker failed: ' + type(error).__name__, file=sys.stderr)
        sys.exit(1)
