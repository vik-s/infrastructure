#!/usr/bin/env python3
"""Recover an abandoned Autorestic flag only when no backup tool is alive."""
import argparse
import os
from pathlib import Path
import shutil
import time

import yaml


def active_tools(proc=Path('/proc')):
    active = []
    for entry in proc.glob('[0-9]*'):
        try:
            executable = Path(os.readlink(entry / 'exe').removesuffix(' (deleted)')).name
        except FileNotFoundError:
            continue
        except PermissionError:
            raise RuntimeError('Cannot inspect processes; refusing lock recovery')
        if executable == 'restic' or executable == 'autorestic' or executable.startswith(('restic-', 'autorestic-')):
            active.append(int(entry.name))
    return active


def recover(path, active):
    if active:
        raise RuntimeError('Backup tools are still running: ' + ', '.join(map(str, active)))
    if not path.exists():
        return False
    state = yaml.safe_load(path.read_text())
    if not isinstance(state, dict) or not isinstance(state.get('running'), bool):
        raise RuntimeError('Unexpected lock contents; refusing to modify it')
    if not state['running']:
        return False
    shutil.copy2(path, str(path) + '.recovered-' + str(time.time_ns()))
    state['running'] = False
    temporary = path.with_name(path.name + '.tmp')
    with open(temporary, 'w', opener=lambda p, f: os.open(p, f, 0o600)) as output:
        yaml.safe_dump(state, output)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lock', type=Path, default=Path('/etc/autorestic/.autorestic.lock.yml'))
    args = parser.parse_args()
    try:
        if recover(args.lock, active_tools()):
            print('Recovered abandoned Autorestic flag; scheduling history preserved')
    except Exception as error:
        parser.exit(1, str(error) + '\n')
