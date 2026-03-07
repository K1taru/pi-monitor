"""
Metrics package — /metrics/*, /processes
"""
from flask import Blueprint

from .system import system_bp
from .processes import processes_bp

metrics_bp = Blueprint('metrics', __name__)
metrics_bp.register_blueprint(system_bp)
metrics_bp.register_blueprint(processes_bp)

__all__ = ['metrics_bp']
