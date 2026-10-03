# Scrutiny collectors

`make scrutiny-maintenance` deploys only the collectors on Gaara and Tsukuyomi.
It does not reprovision Proxmox, restart application stacks, or update images.
The image is pinned to the already deployed digest; upgrades are separate.

The collector configuration is copied before its individual read-only bind
mount is created. The dedicated compose project is then started, with six
physical disks on Gaara and three on Tsukuyomi. Host WWN paths are mapped to
fixed `/dev/sd*` names inside the container, so host device enumeration changes
do not silently remove disks from collection. Missing configured WWNs fail
deployment before the existing collector is stopped.

The obsolete `scrutiny-collector-old` container is stopped, its restart policy
is disabled, and it is retained under a timestamped name for rollback. Its old
root compose file is archived only if it contains that one obsolete service.
The PVE role no longer installs a competing collector definition.

Collection runs on startup and daily through the image's cron service. Verify
uploads in the container logs and check every expected WWN's
`smart.collector_date` at `https://scrutiny.iyer.app/api/summary`. A healthy web
server alone does not establish that collectors are uploading readings.
