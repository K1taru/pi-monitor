"""
Database helpers — connection context manager and schema initialisation.
"""
import sqlite3
import contextlib
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get('DB_PATH', 'raspy_monitor.db')


@contextlib.contextmanager
def db_connection():
    """Context manager yielding a SQLite connection.

    - WAL journal mode: lets the background collector write while Flask
      reads concurrently without 'database is locked' errors.
    - check_same_thread=False: connection is created per-call so it is
      safe to use across the thread that opens it.
    - Auto-commits on clean exit; rolls back and re-raises on exception.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows accessible by column name
    conn.execute('PRAGMA journal_mode=WAL') # concurrent reads + writes
    conn.execute('PRAGMA synchronous=NORMAL')  # safe + faster than FULL with WAL
    try:
        yield conn
        conn.commit()
    except Exception:
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

    if not default_users_env:
        existing = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if existing == 0:
            print(
                '[warn] DEFAULT_USERS is not set and no users exist.\n'
                '       Set DEFAULT_USERS in .env before starting the service.\n'
                '       Example: DEFAULT_USERS=yourname:yourpassword:1'
            )
        return

    # Parse the DEFAULT_USERS format
    for user_spec in default_users_env.split(';'):
        user_spec = user_spec.strip()
        if not user_spec:
            continue

        # rsplit on the last two colons to support passwords containing colons
        parts = user_spec.rsplit(':', 2)
        if len(parts) != 3:
            print(f"[warn] Invalid user spec (expected 'username:password:is_admin'): {user_spec}")
            continue

        username, password, is_admin_str = parts
        username = username.strip()
        password = password.strip()

        try:
            is_admin = int(is_admin_str.strip())
        except ValueError:
            print(f"[warn] Invalid is_admin value (expected 0 or 1): {is_admin_str}")
            continue

        existing = conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone()
        if existing:
            print(f"[info] User '{username}' already exists, skipping")
            continue

        try:
            conn.execute(
                'INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), is_admin),
            )
            print(f"[info] Created user '{username}' (admin={bool(is_admin)})")
        except sqlite3.IntegrityError as e:
            print(f"[warn] Error creating user '{username}': {e}")


def init_db():
    """Create tables and initialize users from DEFAULT_USERS."""
    with db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         username TEXT UNIQUE NOT NULL,
                         password_hash TEXT NOT NULL,
                         is_admin INTEGER DEFAULT 0,
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS metrics_history
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         cpu_temp REAL,
                         cpu_freq REAL,
                         cpu_percent REAL,
                         ram_percent REAL,
                         disk_percent REAL)''')

        # Index speeds up the time-range queries the chart endpoint runs constantly
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
                        ON metrics_history (timestamp)''')

        _create_default_users(conn)
