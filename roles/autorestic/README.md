# Backblaze backups

Deploy only backup tooling and configuration with `make backup-maintenance`.
This does not run Proxmox provisioning or host-wide package upgrades. Downloads
are pinned to Autorestic 1.8.3 and Restic 0.19.1 and checked against published
SHA-256 hashes. The binaries live under `/usr/local/lib/autorestic`; the system
package binaries remain available for rollback. Existing repositories are not
migrated, forgotten, or pruned by this role.

`autorestic.timer` runs every five minutes. Locations keep their existing daily
UTC schedules. The runner uses an OS file lock shared with integrity checking.
Before starting, it refuses to overlap an existing Autorestic/Restic process.
It clears an abandoned `running: true` flag only after that process check,
keeping a copy of the old file and preserving cron history.

## Health and alerts

Autorestic's cron command can return success despite a failed location.
`autorestic-health.timer` therefore queries Backblaze independently every 30
minutes. Each expected host/path must have a snapshot no older than 36 hours.
A failed backup hook or failed integrity check also makes that location
unhealthy, including when a partial snapshot was written recently.

Success hooks record the result locally; a single successful dataset cannot
mark the overall backup healthy. Failure hooks report immediately. The checker
updates the aggregate Backblaze monitor and individual Uptime Kuma push
monitors, retaining the existing Discord notification integration. Each
individual monitor expects a checker heartbeat within two hours, so a dead
checker is detected too.

Secrets live in root-only `/etc/autorestic/.autorestic.yaml` and
`/etc/autorestic/monitoring.yaml`. To reproduce the per-dataset monitors on a new
host, store a map named `autorestic_location_push_urls` in Ansible Vault, keyed
by location name. If this variable is omitted, deployment preserves the
existing map on the host. No push tokens belong in plaintext Git files.

Read the latest result at `/var/lib/autorestic-health/latest.json` or run:

```sh
sudo /usr/local/lib/autorestic/autorestic-health.py check
sudo journalctl -u autorestic.service -u autorestic-health.service
```

The health service intentionally fails when any location is stale. During a
large catch-up upload this remains an accurate failure until a new snapshot
has actually been committed.

## Integrity and restore verification

`autorestic-integrity.timer` wakes daily at 12:00 UTC with up to 30 minutes of
jitter. Each repository receives a structural check and a random 64 MiB data
sample when its last successful check is at least seven days old. Busy backup
processes defer the check to a later timer run. This is sampled verification,
not a full read of every stored byte. Failure state remains visible until a
subsequent check succeeds.

For an individual repository check when it is not being backed up:

```sh
sudo /usr/local/lib/autorestic/autorestic-health.py integrity --backend remote-docker-dbs
```

Verify restored files in a new temporary directory or stream a selected file
with `restic dump`, using the stored repository credentials. Do not restore
over live application data. Snapshot freshness alone does not establish that
all application data is consistent; database exports and restore tests remain
necessary.

## Tests

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s roles/autorestic/tests -v
```

Tests cover refusing lock recovery during a running backup, retaining cron
history, Restic nanosecond timestamps on Python 3.9, host/path matching,
freshness thresholds, failed partial backups, and preventing one successful
location from masking another failed location.
