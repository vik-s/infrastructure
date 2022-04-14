#!/bin/sh
# Backup tank
/usr/sbin/syncoid -R --no-rollback --skip-parent --no-sync-snap --sshkey /home/ansible/.ssh/server_privkey ansible@192.168.1.210:tank tank
# Backup docker dataset
/usr/sbin/syncoid -F --skip-parent --no-sync-snap --sshkey /home/ansible/.ssh/server_privkey ansible@192.168.1.210:rpool/docker tank/docker
# Call uptime kuma
/usr/bin/curl -m 10 --retry 3 "https://status.iyer.app/api/push/55E2L8cPsl?msg=OK&ping="
