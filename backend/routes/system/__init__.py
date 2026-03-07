"""
System control package — /system/*  (admin only)

Sub-modules:
  governor  — CPU performance profile  (/system/governor)
  fan       — Fan PWM control          (/system/fan, /system/fan/curve)
  power     — Reboot                   (/system/reboot)
"""
from flask import Blueprint

from .governor import governor_bp
from .fan import fan_bp
from .power import power_bp

system_bp = Blueprint('system', __name__, url_prefix='/system')
system_bp.register_blueprint(governor_bp)
system_bp.register_blueprint(fan_bp)
system_bp.register_blueprint(power_bp)

__all__ = ['system_bp']
