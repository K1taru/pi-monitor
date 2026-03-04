"""
WebSocket terminal handlers — admin only.
"""
import subprocess
from flask import request
from flask_socketio import emit, disconnect
from flask_jwt_extended import decode_token

from extensions import socketio
from logger import ops_log

# Commands that are blocked regardless of admin status
_BLOCKED_COMMANDS = (
    'rm -rf /', 'mkfs', ':(){:|:&};:', '> /dev/sda',
    'dd if=/dev/zero', 'chmod -R 777 /', 'chown -R',
    # Power-off / sleep are never allowed — only reboot via the API endpoint
    'poweroff', 'shutdown', 'halt', 'systemctl halt',
    'systemctl poweroff', 'systemctl suspend', 'systemctl hibernate',
    'systemctl sleep', 'pm-suspend', 'pm-hibernate',
)

_active_terminals: dict = {}


def register_handlers():
    """Attach all socket event handlers to the socketio instance.

    Called once from app.py after socketio.init_app().
    """

    @socketio.on('connect')
    def handle_connect():
        token = request.args.get('token')
        if not token:
            ops_log.warning('Terminal WS connect rejected — no token (sid=%s)', request.sid)
            disconnect()
            return False
        try:
            decoded = decode_token(token)
            if not decoded.get('is_admin'):
                ops_log.warning('Terminal WS connect rejected — not admin (sid=%s)', request.sid)
                disconnect()
                return False
            ops_log.info('Terminal WS connected — user=%s sid=%s', decoded.get('username', '?'), request.sid)
            emit('connected', {'message': 'Connected to terminal'})
        except Exception as e:
            ops_log.error('Terminal WS connect error (sid=%s): %s', request.sid, e)
            disconnect()
            return False

    @socketio.on('disconnect')
    def handle_disconnect():
        proc = _active_terminals.pop(request.sid, None)
        if proc is not None:
            try:
                proc.terminate()
            except OSError:
                pass
        ops_log.info('Terminal WS disconnected (sid=%s)', request.sid)

    @socketio.on('terminal_input')
    def handle_terminal_input(data):
        command = data.get('input', '').strip()
        lower   = command.lower()

        for blocked in _BLOCKED_COMMANDS:
            if blocked in lower:
                ops_log.warning('BLOCKED command from sid=%s: %s', request.sid, command)
                emit('terminal_output', {'output': 'Command blocked for safety reasons.\n'})
                return

        ops_log.info('Terminal exec (sid=%s): %s', request.sid, command)

        try:
            result = subprocess.run(
                command, shell=True,
                capture_output=True, text=True, timeout=30,
            )
            output = result.stdout + result.stderr
            ops_log.debug('Terminal output (sid=%s): %d chars, exit=%d', request.sid, len(output), result.returncode)
            emit('terminal_output', {'output': output or '(no output)\n'})
        except subprocess.TimeoutExpired:
            ops_log.warning('Terminal command timed out (sid=%s): %s', request.sid, command)
            emit('terminal_output', {'output': 'Command timed out (30 s limit).\n'})
        except Exception as e:
            ops_log.error('Terminal exec error (sid=%s): %s', request.sid, e)
            emit('terminal_output', {'output': f'Error: {str(e)}\n'})
