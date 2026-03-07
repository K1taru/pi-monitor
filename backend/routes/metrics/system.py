"""
System metrics routes — /metrics/current, /metrics/history
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta

from database import db_connection
from services.metrics import get_system_metrics

system_bp = Blueprint('system_metrics', __name__)


@system_bp.route('/metrics/current', methods=['GET'])
@jwt_required()
def get_current_metrics():
    return jsonify(get_system_metrics()), 200


@system_bp.route('/metrics/history', methods=['GET'])
@jwt_required()
def get_metrics_history():
    hours  = min(request.args.get('hours', default=1, type=int), 24)
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')

    with db_connection() as conn:
        rows = conn.execute(
            '''SELECT timestamp, cpu_temp, cpu_freq, cpu_percent, ram_percent, disk_percent
               FROM metrics_history
               WHERE timestamp >= ?
               ORDER BY timestamp ASC''',
            (cutoff,),
        ).fetchall()

    history = [
        {
            'timestamp':    r['timestamp'],
            'cpu_temp':     r['cpu_temp'],
            'cpu_freq':     r['cpu_freq'],
            'cpu_percent':  r['cpu_percent'],
            'ram_percent':  r['ram_percent'],
            'disk_percent': r['disk_percent'],
        }
        for r in rows
    ]
    return jsonify(history), 200
