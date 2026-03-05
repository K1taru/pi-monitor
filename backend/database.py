"""
Database helpers — connection context manager and schema initialisation.
"""
import sqlite3
import contextlib
import os
from werkzeug.security import generate_password_hash

from logger import app_log, ops_log

DB_PATH = os.environ.get('DB_PATH', 'monitor.db')


@contextlib.contextmanager
def db_connection():
    """Context manager yielding a SQLite connection.

    - WAL journal mode: lets the background collector write while Flask
      reads concurrently without 'database is locked' errors.
    - check_same_thread=False: connection is created per-call so it is
      safe to use across the thread that opens it.
    - Auto-commits on clean exit; rolls back and re-raises on exception.
    """
    ops_log.debug('Opening SQLite connection to %s', DB_PATH)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows accessible by column name
    conn.execute('PRAGMA journal_mode=WAL') # concurrent reads + writes
    conn.execute('PRAGMA synchronous=NORMAL')  # safe + faster than FULL with WAL
    try:
        yield conn
        conn.commit()
        ops_log.debug('SQLite connection committed and closing')
    except Exception as exc:
        ops_log.error('SQLite transaction rolled back: %s', exc)
        conn.rollback()
        raise
    finally:
        conn.close()


def _create_default_users(conn):
    """Parse DEFAULT_USERS from environment and create users that don't exist.

    Format: username:password:is_admin;username:password:is_admin
    Example: k1taru:password123:1;guest:guestpass:0

    If DEFAULT_USERS is not set and no users exist, a warning is printed
    and no accounts are created — there is intentionally no insecure
    default account.
    """
    default_users_env = os.environ.get('DEFAULT_USERS', '').strip()
    ops_log.info('Checking DEFAULT_USERS environment variable ...')

    if not default_users_env:
        existing = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if existing == 0:
            app_log.warning(
                'DEFAULT_USERS is not set and no users exist. '
                'Set DEFAULT_USERS in .env before starting the service. '
                'Example: DEFAULT_USERS=yourname:yourpassword:1'
            )
            ops_log.warning('No DEFAULT_USERS set and users table is empty — no accounts created')
        else:
            ops_log.info('DEFAULT_USERS not set but %d user(s) already exist in DB', existing)
        return

    # Parse the DEFAULT_USERS format
    user_specs = [s.strip() for s in default_users_env.split(';') if s.strip()]
    ops_log.info('Found %d user spec(s) in DEFAULT_USERS', len(user_specs))

    for idx, user_spec in enumerate(user_specs, 1):
        ops_log.debug('Parsing user spec #%d: %s', idx, user_spec)

        # rsplit on the last two colons to support passwords containing colons
        parts = user_spec.rsplit(':', 2)
        if len(parts) != 3:
            app_log.warning("Invalid user spec (expected 'username:password:is_admin'): %s", user_spec)
            ops_log.warning('Skipping malformed user spec #%d: %s', idx, user_spec)
            continue

        username, password, is_admin_str = parts
        username = username.strip()
        password = password.strip().strip("'").strip('"')  # strip accidental surrounding quotes

        try:
            is_admin = int(is_admin_str.strip())
        except ValueError:
            app_log.warning('Invalid is_admin value (expected 0 or 1): %s', is_admin_str)
            ops_log.warning('Invalid is_admin for user "%s": %s', username, is_admin_str)
            continue

        ops_log.info('Processing user "%s" (admin=%s)', username, bool(is_admin))

        existing = conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone()
        if existing:
            app_log.info('User "%s" already exists, skipping', username)
            ops_log.info('User "%s" already in DB (id=%s), skipping creation', username, existing['id'])
            continue

        try:
            conn.execute(
                'INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), is_admin),
            )
            app_log.info('Created user "%s" (admin=%s)', username, bool(is_admin))
            ops_log.info('INSERT user "%s" into DB — admin=%s, password hash generated', username, bool(is_admin))
        except sqlite3.IntegrityError as e:
            app_log.warning('Error creating user "%s": %s', username, e)
            ops_log.error('IntegrityError creating user "%s": %s', username, e)


def init_db():
    """Create tables and initialize users from DEFAULT_USERS."""
    app_log.info('Initialising database at %s', DB_PATH)
    ops_log.info('=== DATABASE INIT START ===')
    ops_log.info('DB path: %s', os.path.abspath(DB_PATH))

    with db_connection() as conn:
        ops_log.info('Creating table "users" if not exists ...')
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         username TEXT UNIQUE NOT NULL,
                         password_hash TEXT NOT NULL,
                         is_admin INTEGER DEFAULT 0,
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        ops_log.info('Table "users" — OK')

        ops_log.info('Creating table "metrics_history" if not exists ...')
        conn.execute('''CREATE TABLE IF NOT EXISTS metrics_history
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         cpu_temp REAL,
                         cpu_freq REAL,
                         cpu_percent REAL,
                         ram_percent REAL,
                         disk_percent REAL)''')
        ops_log.info('Table "metrics_history" — OK')

        # Index speeds up the time-range queries the chart endpoint runs constantly
        ops_log.info('Creating index "idx_metrics_timestamp" if not exists ...')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
                        ON metrics_history (timestamp)''')
        ops_log.info('Index "idx_metrics_timestamp" — OK')

        _create_default_users(conn)

    ops_log.info('=== DATABASE INIT COMPLETE ===')
