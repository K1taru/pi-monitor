"""
Application configuration — reads from environment / .env file.
"""
import os
from datetime import timedelta

from logger import app_log, ops_log

_DEFAULT_SECRET = 'CHANGE_ME_USE_ENV_VAR_SECRET_KEY'
_DEFAULT_JWT    = 'CHANGE_ME_USE_ENV_VAR_JWT_SECRET'


def init_app(app):
    """Apply configuration to the Flask app instance."""
    app.config['SECRET_KEY']     = os.environ.get('SECRET_KEY',     _DEFAULT_SECRET)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', _DEFAULT_JWT)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=12)

    ops_log.info('SECRET_KEY       = %s', 'SET (env)' if app.config['SECRET_KEY'] != _DEFAULT_SECRET else 'DEFAULT (insecure!)')
    ops_log.info('JWT_SECRET_KEY   = %s', 'SET (env)' if app.config['JWT_SECRET_KEY'] != _DEFAULT_JWT else 'DEFAULT (insecure!)')
    ops_log.info('JWT token expiry = %s', app.config['JWT_ACCESS_TOKEN_EXPIRES'])

    if app.config['SECRET_KEY'] == _DEFAULT_SECRET:
        app_log.warning('SECRET_KEY is not set via environment variable!')
    if app.config['JWT_SECRET_KEY'] == _DEFAULT_JWT:
        app_log.warning('JWT_SECRET_KEY is not set via environment variable!')
