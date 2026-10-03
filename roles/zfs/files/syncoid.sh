#!/bin/sh
set -eu
exec /usr/bin/flock -n /run/lock/syncoid-operation.lock /usr/bin/python3 /opt/syncoid/replicate.py run
