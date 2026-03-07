"""
CPU performance profile routes — /system/governor  (admin only)
"""
import os
import subprocess
from flask import Blueprint, jsonify, request

from utils.decorators import admin_required
from utils.logger import ops_log

governor_bp = Blueprint('system_governor', __name__)

_GOVERNOR_PATH   = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
_AVAILABLE_PATH  = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors'
_GOV_CONTROL_BIN = os.environ.get('GOV_CONTROL_BIN', '/usr/local/bin/pi-monitor-gov-control')


@governor_bp.route('/governor', methods=['GET', 'POST'])
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
