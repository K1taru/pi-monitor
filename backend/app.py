#!/usr/bin/env python3
"""
Raspberry Pi System Monitor — application entry point.
"""
from dotenv import load_dotenv
load_dotenv(override=True)  # Must run before any os.environ access; override=True
                             # ensures python-dotenv values win over systemd EnvironmentFile
                             # (systemd mangles special chars like ! in passwords)

import os
from flask import Flask
from flask_cors import CORS

import core.config as config
from utils.logger import app_log, ops_log
from core.extensions import jwt
from database import init_db
from services.metrics import start_collector
from routes.auth import auth_bp
from routes.metrics import metrics_bp
from routes.system import system_bp
from services.fan_curve import fan_boost_on_start, start_fan_controller
from routes.dist import frontend_bp


def create_app() -> Flask:
    ops_log.info('=== APP STARTUP BEGIN ===')

    app = Flask(__name__)

    # Configuration
    ops_log.info('Loading configuration ...')
    config.init_app(app)
    ops_log.info('Configuration loaded')

    # CORS
    origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
    CORS(app, resources={r"/*": {"origins": origins}})
    ops_log.info('CORS configured for origins: %s', origins)

    # Extensions
    jwt.init_app(app)
    ops_log.info('JWT extension initialised (token expiry: %s)', app.config.get('JWT_ACCESS_TOKEN_EXPIRES'))

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(frontend_bp)
    ops_log.info('Registered blueprints: auth, metrics, system, frontend')

    # Database & background collector
    init_db()
    start_collector()
    start_fan_controller()
    fan_boost_on_start(duration=60)  # Turbo for first minute, then auto

    ops_log.info('=== APP STARTUP COMPLETE ===')
    return app


app = create_app()

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    app_log.info('Starting Raspberry Pi Monitor Backend on port %s (debug=%s)', port, debug)
    ops_log.info('Serving on 0.0.0.0:%s  debug=%s', port, debug)

    # Show user initialization info
    default_users = os.environ.get('DEFAULT_USERS', '').strip()
    if default_users:
        app_log.info('Users will be initialized from DEFAULT_USERS env variable')
    else:
        app_log.warning('DEFAULT_USERS is not set. No users will be created unless the DB already has accounts.')

    app.run(host='0.0.0.0', port=port, debug=debug)
