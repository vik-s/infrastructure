#!/bin/sh
set -eu
# flock releases automatically on exit, including a killed process or reboot.
exec /usr/bin/flock -n -E 75 /run/lock/autorestic-operation.lock /bin/sh -ec '
  /usr/local/lib/autorestic/autorestic-guard.py
  exec /usr/local/lib/autorestic/autorestic-{{ autorestic_version }} \
    --restic-bin /usr/local/lib/autorestic/restic-{{ autorestic_restic_version }} \
    -c /etc/autorestic/.autorestic.yaml --ci cron
'
