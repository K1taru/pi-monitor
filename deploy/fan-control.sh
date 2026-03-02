#!/bin/bash
# raspy-fan-control — privileged wrapper for Pi fan PWM control
#
# Install with:
#   sudo install -m 0755 deploy/fan-control.sh /usr/local/bin/raspy-fan-control
#
# Usage:
#   raspy-fan-control write-pwm <0-255>
#   raspy-fan-control write-mode <0|1|2>    (0=off, 1=manual, 2=auto)

set -e

# Find the hwmon directory that has PWM fan control
HWMON_DIR=""
for d in /sys/class/hwmon/hwmon*; do
    if [ -f "$d/pwm1" ]; then
        HWMON_DIR="$d"
        break
    fi
done

if [ -z "$HWMON_DIR" ]; then
    echo "ERROR: No fan PWM control found under /sys/class/hwmon/" >&2
    exit 1
fi

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
    *)
        echo "Usage: $0 write-pwm <0-255> | write-mode <0|1|2>" >&2
        exit 1
        ;;
esac
