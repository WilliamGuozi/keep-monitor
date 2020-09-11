#!/bin/sh
#
# Created by William Guozi
#

sed -i "s%SLACK_WEB_HOOK%${SLACK_WEB_HOOK:-}%g" /scripts/keep-monitor.py
sed -i "s%GRAPHITE_URL%${GRAPHITE_URL:-}%g" /scripts/keep-monitor.py
sed -i "s%CONTAINER_BEACON%${CONTAINER_BEACON:-}%g" /scripts/keep-monitor.py
sed -i "s%CONTAINER_ECDSA%${CONTAINER_ECDSA:-}%g" /scripts/keep-monitor.py

exec "$@"