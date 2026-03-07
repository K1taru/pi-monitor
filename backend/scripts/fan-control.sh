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
        # Disable the thermal zone governor loop by setting mode=disabled.
        #
        # On Pi 5, the firmware locks the thermal zone policy so 'user_space'
        # cannot be written (EINVAL).  However, writing 'disabled' to the zone's
        # 'mode' file stops step_wise from running its governor callbacks at all,
        # so it never calls set_cur_state() on the cooling device.
        #
        # Without this, step_wise fires every few seconds and — due to the
        # unpatched pwm-fan driver bug (PR#5617) — writes cur_state=0 directly
        # to the firmware, bypassing pwm1_enable=1 and zeroing pwm1.
        #
        # Our software control loop provides equivalent thermal protection.
        _ZONE=/sys/class/thermal/thermal_zone0
        _MODE_BACKUP=/run/pi-monitor-thermal-mode-backup

        # Clean up leftovers from previous (trip-point / policy) approaches
        rm -f /run/pi-monitor-trip-backup /run/pi-monitor-thermal-policy-backup

        if [ -f "$_ZONE/mode" ]; then
            cat "$_ZONE/mode" > "$_MODE_BACKUP"
            echo "disabled" > "$_ZONE/mode"
        fi
        ;;
    enable-thermal-fan)
        # Re-enable the thermal zone governor.
        _MODE_BACKUP=/run/pi-monitor-thermal-mode-backup
        _ZONE=/sys/class/thermal/thermal_zone0
        if [ -f "$_MODE_BACKUP" ]; then
            orig=$(cat "$_MODE_BACKUP")
            echo "$orig" > "$_ZONE/mode" 2>/dev/null || true
            rm -f "$_MODE_BACKUP"
        else
            echo "enabled" > "$_ZONE/mode" 2>/dev/null || true
        fi
        ;;
    *)
        echo "Usage: pi-monitor-fan-control write-pwm <0-255> | write-mode <0|1|2> | read-pwm | read-mode | read-rpm | disable-thermal-fan | enable-thermal-fan" >&2
        exit 1
        ;;
esac
