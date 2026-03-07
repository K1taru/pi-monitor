"""
Centralised logging for Pi Monitor.

Two loggers are configured so you can monitor them independently:

  1. 'app'  — prints to STDOUT (visible via journalctl -u pi-monitor-*)
             Purpose: high-level startup messages, warnings, errors.

  2. 'ops'  — writes to  backend/logs/pi-monitor-ops.log  (rotated, 5 × 2 MB)
             Purpose: verbose trace of every significant action — DB calls,
             user creation, login attempts, fan/governor changes, metrics
             collection, etc.

Usage in any module:

    from utils.logger import app_log, ops_log

    app_log.info('Server starting on port %s', port)
    ops_log.info('User "%s" authenticated successfully', username)

Monitor the ops log separately with:

    tail -f ~/pi-monitor/backend/logs/pi-monitor-ops.log
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ---------------------------------------------------------------------------
# Paths — logs go to backend/logs/, one level above this file's package dir
# ---------------------------------------------------------------------------
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
_OPS_LOG = os.path.join(_LOG_DIR, 'pi-monitor-ops.log')

# Ensure log directory exists
os.makedirs(_LOG_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------
_CONSOLE_FMT = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

_FILE_FMT = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# ---------------------------------------------------------------------------
# App logger  →  STDOUT  (shows in journalctl)
# ---------------------------------------------------------------------------
app_log = logging.getLogger('app')
app_log.setLevel(logging.INFO)

_stdout_handler = logging.StreamHandler()
_stdout_handler.setFormatter(_CONSOLE_FMT)
app_log.addHandler(_stdout_handler)
app_log.propagate = False

# ---------------------------------------------------------------------------
# Ops logger  →  rotating file  (tail -f logs/pi-monitor-ops.log)
# ---------------------------------------------------------------------------
ops_log = logging.getLogger('ops')
ops_log.setLevel(logging.DEBUG)

_file_handler = RotatingFileHandler(
    _OPS_LOG,
    maxBytes=2 * 1024 * 1024,   # 2 MB per file
    backupCount=5,               # keep 5 rotated copies
    encoding='utf-8',
)
_file_handler.setFormatter(_FILE_FMT)
ops_log.addHandler(_file_handler)
ops_log.propagate = False
