#!/bin/sh
# Call autorestic cron
autorestic -c /etc/autorestic/.autorestic.yaml --ci cron
