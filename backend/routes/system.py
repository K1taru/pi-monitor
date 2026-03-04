"""
System control routes — /api/system/*  (admin only)
"""
import glob
import os
import subprocess
import threading
import time
from flask import Blueprint, jsonify, request

from decorators import admin_required
from logger import app_log, ops_log

system_bp = Blueprint('system', __name__, url_prefix='/api/system')

_GOVERNOR_PATH   = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
_AVAILABLE_PATH  = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors'
_FAN_CONTROL_BIN = os.environ.get('FAN_CONTROL_BIN', '/usr/local/bin/pi-monitor-fan-control')
_GOV_CONTROL_BIN = os.environ.get('GOV_CONTROL_BIN', '/usr/local/bin/pi-monitor-gov-control')
_HWMON_CACHE     = '/run/pi-monitor-fan-hwmon'

# Module-level cache — populated once, revalidated only when the path disappears.
_fan_hwmon_cached: str | None = None


def _find_fan_hwmon() -> str | None:
    """Return the hwmon sysfs directory that exposes PWM fan control.

    The result is cached in memory and in /run/raspy-fan-hwmon so that both
    this process and fan-control.sh agree on the path without re-scanning on
    every call (hwmon index shifts on reboot but stays stable at runtime).
    """
    global _fan_hwmon_cached

    # Fast path: in-memory cache is still valid
    if _fan_hwmon_cached and os.path.exists(f'{_fan_hwmon_cached}/pwm1'):
        return _fan_hwmon_cached

    # Try the on-disk cache written by fan-control.sh
    try:
        with open(_HWMON_CACHE) as fh:
            cached = fh.read().strip()
        if os.path.exists(f'{cached}/pwm1'):
            _fan_hwmon_cached = cached
            return _fan_hwmon_cached
    except OSError:
        pass

    # Full scan — only reaches here on first use or after a hwmon index shift
    for path in sorted(glob.glob('/sys/class/hwmon/hwmon*')):
        if os.path.exists(f'{path}/pwm1'):
            _fan_hwmon_cached = path
            try:
                with open(_HWMON_CACHE, 'w') as fh:
                    fh.write(path)
            except OSError:
                pass  # /run may not be writable without sudo; shell script will handle it
            return _fan_hwmon_cached

    _fan_hwmon_cached = None
    return None


def fan_boost_on_start(duration: int = 180):
    """Run fan at 100% for `duration` seconds on startup, then return to auto.

    Runs in a background daemon thread — call once from app.py.
    """
    def _boost():
        try:
            subprocess.run(['sudo', _FAN_CONTROL_BIN, 'write-pwm', '255'],
                           check=True, capture_output=True, text=True)
            subprocess.run(['sudo', _FAN_CONTROL_BIN, 'write-mode', '1'],
                           check=True, capture_output=True, text=True)
            app_log.info('Fan boost started — max speed for %ds', duration)
            ops_log.info('Fan boost: PWM=255, mode=1 (manual), duration=%ds', duration)
            time.sleep(duration)
            subprocess.run(['sudo', _FAN_CONTROL_BIN, 'write-mode', '2'],
                           check=True, capture_output=True, text=True)
            app_log.info('Fan boost finished — returned to auto')
            ops_log.info('Fan boost complete: mode=2 (auto)')
        except Exception as e:
            app_log.error('Fan boost error: %s', e)
            ops_log.error('Fan boost error: %s', e)

    t = threading.Thread(target=_boost, daemon=True, name='fan-boost')
    t.start()

@system_bp.route('/governor', methods=['GET', 'POST'])
@admin_required
def cpu_governor():
    if request.method == 'GET':
        try:
            with open(_GOVERNOR_PATH) as f:
                current = f.read().strip()
            with open(_AVAILABLE_PATH) as f:
                available = f.read().strip().split()
            ops_log.debug('Governor GET — current=%s, available=%s', current, available)
            return jsonify({'current': current, 'available': available}), 200
        except (OSError, IOError) as e:
            ops_log.error('Governor GET failed: %s', e)
            return jsonify({'error': str(e)}), 500

    # POST
    governor = (request.get_json() or {}).get('governor')
    if not governor:
        return jsonify({'error': 'Governor required'}), 400

    ops_log.info('Governor change requested: %s', governor)

    try:
        with open(_AVAILABLE_PATH) as f:
            available = f.read().strip().split()
        if governor not in available:
            return jsonify({'error': f'Invalid governor: {governor}'}), 400

        subprocess.run(
            ['sudo', _GOV_CONTROL_BIN, governor],
            capture_output=True, text=True, check=True,
        )
        ops_log.info('CPU governor changed to "%s"', governor)
        return jsonify({'message': f'Governor set to {governor}'}), 200
    except (OSError, subprocess.CalledProcessError) as e:
        err = getattr(e, 'stderr', None) or str(e)
        ops_log.error('Failed to set governor to "%s": %s', governor, err)
        return jsonify({'error': err}), 500


@system_bp.route('/fan', methods=['GET', 'POST'])
@admin_required
def fan_control():
    hwmon = _find_fan_hwmon()

    if request.method == 'GET':
        if not hwmon:
            return jsonify({'available': False, 'message': 'Fan PWM control not found on this system'}), 200
        try:
            with open(f'{hwmon}/pwm1') as f:
                pwm = int(f.read().strip())
            with open(f'{hwmon}/pwm1_enable') as f:
                mode = int(f.read().strip())  # 0=off, 1=manual, 2=auto
            rpm = 0
            if os.path.exists(f'{hwmon}/fan1_input'):
                with open(f'{hwmon}/fan1_input') as f:
                    rpm = int(f.read().strip())
            return jsonify({
                'available': True,
                'speed': round(pwm / 255 * 100),
                'pwm': pwm,
                'rpm': rpm,
                'auto': mode == 2,
                'mode': mode,
            }), 200
        except (OSError, IOError) as e:
            return jsonify({'error': str(e)}), 500

    # POST
    if not hwmon:
        return jsonify({'error': 'Fan PWM control not available on this system'}), 501

    data = request.get_json() or {}
    try:
        if data.get('auto') is True:
            subprocess.run(
                ['sudo', _FAN_CONTROL_BIN, 'write-mode', '2'],
                check=True, capture_output=True, text=True,
            )
        else:
            speed = data.get('speed')
            if speed is not None:
                pwm = max(0, min(255, round(int(speed) / 100 * 255)))
                subprocess.run(
                    ['sudo', _FAN_CONTROL_BIN, 'write-pwm', str(pwm)],
                    check=True, capture_output=True, text=True,
                )
            # Ensure manual mode is set
            subprocess.run(
                ['sudo', _FAN_CONTROL_BIN, 'write-mode', '1'],
                check=True, capture_output=True, text=True,
            )
        ops_log.info('Fan settings updated via API')
        return jsonify({'message': 'Fan settings updated'}), 200
    except subprocess.CalledProcessError as e:
        ops_log.error('Fan control error: %s', e.stderr or str(e))
        return jsonify({'error': e.stderr or str(e)}), 500


@system_bp.route('/reboot', methods=['POST'])
@admin_required
def reboot_system():
    try:
        app_log.warning('System reboot requested via API')
        ops_log.warning('REBOOT initiated from API')
        subprocess.Popen(['sudo', 'reboot'])
        return jsonify({'message': 'System rebooting...'}), 200
    except (OSError, subprocess.SubprocessError) as e:
        ops_log.error('Reboot failed: %s', e)
        return jsonify({'error': str(e)}), 500
