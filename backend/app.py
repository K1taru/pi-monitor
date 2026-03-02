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
from extensions import socketio, jwt
from database import init_db
from metrics import start_collector
from routes.auth import auth_bp
from routes.metrics import metrics_bp
from routes.system import system_bp, fan_boost_on_start
from routes.frontend import frontend_bp
from sockets.terminal import register_handlers


def create_app() -> Flask:
    app = Flask(__name__)

    # Configuration
    config.init_app(app)

    # CORS
    origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
    CORS(app, resources={r"/api/*": {"origins": origins}})

    # Extensions
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins=origins, async_mode='threading')

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(frontend_bp)

    # WebSocket handlers
    register_handlers()

    # Database & background collector
    init_db()
    start_collector()
    fan_boost_on_start(duration=180)  # Max fan speed for first 3 minutes

    return app


app = create_app()

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting Raspberry Pi Monitor Backend on port {port}...")
    
    # Show user initialization info
    default_users = os.environ.get('DEFAULT_USERS', '').strip()
    if default_users:
        print("Users will be initialized from DEFAULT_USERS env variable")
    else:
        print("No DEFAULT_USERS set; will use legacy admin account (admin / admin123)")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
