"""
Process list routes — /processes
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from services.metrics import get_processes

processes_bp = Blueprint('processes_metrics', __name__)


@processes_bp.route('/processes', methods=['GET'])
@jwt_required()
def get_process_list():
    return jsonify(get_processes()), 200
