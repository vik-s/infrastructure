# ZFS replication

`make zfs-maintenance` updates only replication configuration on Tsukuyomi.
It uses the existing Sanoid/Syncoid installation and SSH key. Normal replication
runs at 12:05 UTC daily, with an independent snapshot check every 30 minutes.

Gaara's child datasets under `tank` are pulled into `tank/gaara/<name>` on
Tsukuyomi; `rpool/docker` is pulled into `tank/gaara/docker`. The Docker dataset
itself contains persistent application data; ephemeral Docker child datasets
remain outside the original backup scope. Source `tank/docker` is rejected
because it would collide with that explicit mapping.

The fresh namespace avoids destroying or rolling back divergent legacy
replicas. Existing `tank/backups`, `tank/cloud`, and other old copies remain
available. The backup host's Sanoid configuration preserves their snapshots;
retention applies only below `tank/gaara`. Removing legacy copies later needs
separate review after restore verification.

Receives are unmounted and explicitly read-only, and use `--no-rollback`.
There is no forced deletion, automatic rollback, or destructive reseeding.
The first copy sends only the newest snapshot; subsequent incrementals include
intermediate snapshots so the existing hourly/daily/monthly retention policy
can operate. Interrupted receives retain Syncoid's normal resume support.

The runner attempts every dataset and preserves each exit status. Monitoring
reports success only when every expected destination contains a source-matching
snapshot GUID no older than 36 hours and the last transfer run has no failures.
The prior script's final successful curl could hide failed transfers.

Inspect `/var/lib/syncoid-health/latest.json`, `run.json`, and
`journalctl -u syncoid.service`. Secrets are stored only in root-readable
`/etc/syncoid/config.json`; never commit the Uptime Kuma push URL.

```sh
sudo /usr/bin/python3 /opt/syncoid/replicate.py check
sudo systemctl start --no-block syncoid.service
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s roles/zfs/tests -v
```

A fresh first copy requires space alongside the old replicas and can take
hours. A healthy monitor confirms recent replicated snapshots; it does not
replace periodic file restores and pool scrubs.
