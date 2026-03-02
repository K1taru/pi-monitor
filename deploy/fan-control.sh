#!/bin/bash
# raspy-fan-control — privileged wrapper for Pi fan PWM control
#
# Install with:
#   sudo install -m 0755 deploy/fan-control.sh /usr/local/bin/raspy-fan-control
#
# Usage:
#   raspy-fan-control write-pwm <0-255>
#   raspy-fan-control write-mode <0|1|2>    (0=off, 1=manual, 2=auto)
#   raspy-fan-control read-pwm
#   raspy-fan-control read-mode
#   raspy-fan-control read-rpm
#
# The hwmon index (hwmon0/hwmon1/hwmon2) is discovered once and cached to
# /run/raspy-fan-hwmon.  The cache is re-validated on every invocation and
# re-scanned only if the cached path no longer has pwm1 (e.g. after reboot).

set -e

_HWMON_CACHE=/run/raspy-fan-hwmon

# ---------------------------------------------------------------------------
# Resolve the hwmon directory — check cache first, scan only when needed.
# ---------------------------------------------------------------------------
_find_hwmon() {
    # Cache hit: path still valid
    if [ -f "$_HWMON_CACHE" ]; then
        cached=$(cat "$_HWMON_CACHE")
        if [ -f "$cached/pwm1" ]; then
            echo "$cached"
            return 0
        fi
    fi

    # Cache miss or stale: scan and re-cache
    for d in /sys/class/hwmon/hwmon*; do
        if [ -f "$d/pwm1" ]; then
            echo "$d" > "$_HWMON_CACHE"
            echo "$d"
            return 0
        fi
    done

    return 1
}

HWMON_DIR=$(_find_hwmon) || {
    echo "ERROR: No fan PWM control found under /sys/class/hwmon/" >&2
    exit 1
}

case "$1" in
    write-pwm)
        if [[ ! "$2" =~ ^[0-9]+$ ]] || [ "$2" -lt 0 ] || [ "$2" -gt 255 ]; then
            echo "ERROR: PWM value must be 0-255" >&2
            exit 1
        fi
        echo "$2" > "$HWMON_DIR/pwm1"
        ;;
    write-mode)
        if [[ ! "$2" =~ ^[012]$ ]]; then
            echo "ERROR: Mode must be 0 (off), 1 (manual), or 2 (auto)" >&2
            exit 1
        fi
        echo "$2" > "$HWMON_DIR/pwm1_enable"
        ;;
    read-pwm)
        cat "$HWMON_DIR/pwm1"
        ;;
    read-mode)
        cat "$HWMON_DIR/pwm1_enable"
        ;;
    read-rpm)
        if [ -f "$HWMON_DIR/fan1_input" ]; then
            cat "$HWMON_DIR/fan1_input"
        else
            echo 0
        fi
        ;;
    *)
        echo "Usage: $0 write-pwm <0-255> | write-mode <0|1|2> | read-pwm | read-mode | read-rpm" >&2
        exit 1
        ;;
esac
