"""
Fan control routes — /system/fan  (admin only)

GET  /fan        — current fan status + software mode
POST /fan        — change mode (auto / manual / turbo) and optional speed
GET  /fan/curve  — current temp→speed curve
POST /fan/curve  — save a new curve (1–10 points)
"""
import glob
import os
from typing import Any, cast
from flask import Blueprint, jsonify, request

from utils.decorators import admin_required
from utils.logger import ops_log
from services.fan_curve import (
    get_mode, set_mode, get_curve, set_curve, set_manual_speed,
)

fan_bp = Blueprint('system_fan', __name__)

_HWMON_CACHE = '/run/pi-monitor-fan-hwmon'

# Module-level cache — populated once, revalidated only when the path disappears.
_fan_hwmon_cached: str | None = None


def _find_fan_hwmon() -> str | None:
    """Return the hwmon sysfs directory that exposes PWM fan control."""
    global _fan_hwmon_cached

    if _fan_hwmon_cached and os.path.exists(f'{_fan_hwmon_cached}/pwm1'):
        return _fan_hwmon_cached

    try:
        with open(_HWMON_CACHE) as fh:
            cached = fh.read().strip()
        if os.path.exists(f'{cached}/pwm1'):
            _fan_hwmon_cached = cached
            return _fan_hwmon_cached
    except OSError:
        pass

    for path in sorted(glob.glob('/sys/class/hwmon/hwmon*')):
        if os.path.exists(f'{path}/pwm1'):
            _fan_hwmon_cached = path
            try:
                with open(_HWMON_CACHE, 'w') as fh:
                    fh.write(path)
            except OSError:
                pass
            return _fan_hwmon_cached

    _fan_hwmon_cached = None
    return None


# ── /system/fan ──────────────────────────────────────────────────────────────

@fan_bp.route('/fan', methods=['GET', 'POST'])
@admin_required
def fan_control():
    hwmon = _find_fan_hwmon()

    if request.method == 'GET':
        if not hwmon:
            return jsonify({
                'available': False,
                'message': 'Fan PWM control not found on this system',
            }), 200
        try:
            with open(f'{hwmon}/pwm1') as f:
                pwm = int(f.read().strip())
            rpm = 0
            if os.path.exists(f'{hwmon}/fan1_input'):
                with open(f'{hwmon}/fan1_input') as f:
                    rpm = int(f.read().strip())
            mode = get_mode()
            return jsonify({
                'available': True,
                'speed': round(pwm / 255 * 100),
                'pwm': pwm,
                'rpm': rpm,
                'mode': mode,
            }), 200
        except (OSError, IOError) as e:
            return jsonify({'error': str(e)}), 500

    # POST — mode change and/or manual speed
    if not hwmon:
        return jsonify({'error': 'Fan PWM control not available on this system'}), 501

    raw_data = request.get_json(silent=True)
    data = cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}

    new_mode = data.get('mode')
    if new_mode:
        try:
            set_mode(new_mode)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    # Accept speed when switching to manual, or when already in manual
    effective_mode = new_mode or get_mode()
    if effective_mode == 'manual':
        speed = data.get('speed')
        if speed is not None:
            set_manual_speed(int(speed))

    ops_log.info('Fan settings updated via API')
    return jsonify({'message': 'Fan settings updated'}), 200


# ── /system/fan/curve ────────────────────────────────────────────────────────

@fan_bp.route('/fan/curve', methods=['GET', 'POST'])
@admin_required
def fan_curve_endpoint():
    if request.method == 'GET':
        return jsonify({'points': get_curve()}), 200

    raw_data = request.get_json(silent=True)
    data = cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}
    points = data.get('points')
    if not isinstance(points, list):
        return jsonify({'error': 'points array required'}), 400

    try:
        set_curve(points)
        return jsonify({'message': 'Fan curve updated'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
