#!/usr/bin/env python3
"""
Raspberry Pi System Monitor — application entry point.
"""
from dotenv import load_dotenv
load_dotenv()  # Must run before any os.environ access

import os
from flask import Flask
from flask_cors import CORS

import config
from logger import app_log, ops_log
from extensions import socketio, jwt
from database import init_db
from metrics import start_collector
from routes.auth import auth_bp
from routes.metrics import metrics_bp
from routes.system import system_bp, fan_boost_on_start
from routes.frontend import frontend_bp
from sockets.terminal import register_handlers


def create_app() -> Flask:
    ops_log.info('=== APP STARTUP BEGIN ===')

    app = Flask(__name__)

    # Configuration
    ops_log.info('Loading configuration ...')
    config.init_app(app)
    ops_log.info('Configuration loaded')

    # CORS
    origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
    CORS(app, resources={r"/api/*": {"origins": origins}})
    ops_log.info('CORS configured for origins: %s', origins)

    # Extensions
    jwt.init_app(app)
    ops_log.info('JWT extension initialised (token expiry: %s)', app.config.get('JWT_ACCESS_TOKEN_EXPIRES'))
    socketio.init_app(app, cors_allowed_origins=origins, async_mode='threading')
    ops_log.info('SocketIO initialised (async_mode=threading)')

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(frontend_bp)
    ops_log.info('Registered blueprints: auth, metrics, system, frontend')

    # WebSocket handlers
    register_handlers()
    ops_log.info('WebSocket terminal handlers registered')

    # Database & background collector
    init_db()
    start_collector()
    fan_boost_on_start(duration=180)  # Max fan speed for first 3 minutes

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

    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
