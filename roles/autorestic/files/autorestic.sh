#!/bin/sh
# Call autorestic cron
autorestic -c /etc/autorestic/.autorestic.yaml --ci cron
# Call uptime kuma
/usr/bin/curl -m 10 --retry 3 "{{ hcid_autorestic }}"
