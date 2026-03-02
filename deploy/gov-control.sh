#!/bin/bash
# raspy-gov-control — privileged wrapper for CPU governor writes
#
# Install with:
#   sudo install -m 0755 deploy/gov-control.sh /usr/local/bin/raspy-gov-control
#
# Usage:
#   raspy-gov-control <governor>
#   e.g. raspy-gov-control performance

set -e

GOV_PATH="/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
AVAIL_PATH="/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"

if [ -z "$1" ]; then
    echo "Usage: $0 <governor>" >&2
    exit 1
fi

# Validate governor
AVAILABLE=$(cat "$AVAIL_PATH")
VALID=0
for g in $AVAILABLE; do
    if [ "$g" = "$1" ]; then
        VALID=1
        break
    fi
done

if [ "$VALID" -ne 1 ]; then
    echo "ERROR: Invalid governor '$1'. Available: $AVAILABLE" >&2
    exit 1
fi

# Write to all CPU cores
for cpu_gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    if [ -f "$cpu_gov" ]; then
        echo "$1" > "$cpu_gov"
    fi
done
