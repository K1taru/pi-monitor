"""
Metrics & process routes — /api/metrics/*, /api/processes
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta

from database import db_connection
from metrics import get_system_metrics, get_processes

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api')


@metrics_bp.route('/metrics/current', methods=['GET'])
@jwt_required()
def get_current_metrics():
    return jsonify(get_system_metrics()), 200


@metrics_bp.route('/metrics/history', methods=['GET'])
@jwt_required()
def get_metrics_history():
    hours  = min(request.args.get('hours', default=1, type=int), 24)
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

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


@metrics_bp.route('/processes', methods=['GET'])
@jwt_required()
def get_process_list():
    return jsonify(get_processes()), 200
