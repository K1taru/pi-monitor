"""
Power routes — /system/reboot  (admin only)
"""
import subprocess
from flask import Blueprint, jsonify

from utils.decorators import admin_required
from utils.logger import app_log, ops_log

power_bp = Blueprint('system_power', __name__)


@power_bp.route('/reboot', methods=['POST'])
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
