#!/bin/bash
# pi-monitor-fan-control — privileged wrapper for Pi fan PWM control
#
# Install with:
#   sudo install -m 0755 backend/scripts/fan-control.sh /usr/local/bin/pi-monitor-fan-control
#   (setup.sh does this automatically)
#
# Usage:
#   pi-monitor-fan-control write-pwm <0-255>
#   pi-monitor-fan-control write-mode <0|1|2>    (0=off, 1=manual, 2=auto)
#   pi-monitor-fan-control read-pwm
#   pi-monitor-fan-control read-mode
#   pi-monitor-fan-control read-rpm
#   pi-monitor-fan-control disable-thermal-fan
#   pi-monitor-fan-control enable-thermal-fan
#
# The hwmon index (hwmon0/hwmon1/hwmon2) is discovered once and cached to
# /run/pi-monitor-fan-hwmon.  The cache is re-validated on every invocation and
# re-scanned only if the cached path no longer has pwm1 (e.g. after reboot).

set -e

_HWMON_CACHE=/run/pi-monitor-fan-hwmon

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
    disable-thermal-fan)
        # Switch the thermal zone to the 'user_space' governor so the kernel
        # stops autonomously writing cooling-device states.
        #
        # The previous approach of pushing trip points to 110 °C was wrong:
        # step_wise sees temp < trip and actively sets cooling_device cur_state=0
        # (fan off), which on unpatched Pi 5 kernels bypasses pwm1_enable=1 and
        # zeroes pwm1.  With 'user_space' the governor does nothing on its own.
        # See: https://github.com/raspberrypi/linux/pull/5617
        _ZONE=/sys/class/thermal/thermal_zone0
        _POLICY_BACKUP=/run/pi-monitor-thermal-policy-backup

        # Clean up any trip-point changes from the old approach
        _TRIP_BACKUP=/run/pi-monitor-trip-backup
        if [ -f "$_TRIP_BACKUP" ]; then
            while IFS=: read -r idx orig; do
                tp_temp="$_ZONE/trip_point_${idx}_temp"
                echo "$orig" > "$tp_temp" 2>/dev/null || true
            done < "$_TRIP_BACKUP"
            rm -f "$_TRIP_BACKUP"
        fi

        if [ -f "$_ZONE/policy" ]; then
            cat "$_ZONE/policy" > "$_POLICY_BACKUP"
            echo "user_space" > "$_ZONE/policy"
        fi
        ;;
    enable-thermal-fan)
        # Restore the original thermal zone governor.
        _POLICY_BACKUP=/run/pi-monitor-thermal-policy-backup
        _ZONE=/sys/class/thermal/thermal_zone0
        if [ -f "$_POLICY_BACKUP" ]; then
            orig=$(cat "$_POLICY_BACKUP")
            echo "$orig" > "$_ZONE/policy" 2>/dev/null || true
            rm -f "$_POLICY_BACKUP"
        else
            echo "step_wise" > "$_ZONE/policy" 2>/dev/null || true
        fi
        ;;
    *)
        echo "Usage: pi-monitor-fan-control write-pwm <0-255> | write-mode <0|1|2> | read-pwm | read-mode | read-rpm | disable-thermal-fan | enable-thermal-fan" >&2
        exit 1
        ;;
esac
