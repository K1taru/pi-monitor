"""
Database helpers — connection context manager and schema initialisation.
"""
import sqlite3
import contextlib
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get('DB_PATH', 'raspy_monitor.db')


def db_connection():
    """Context manager that yields a DB connection and always closes it."""
    return contextlib.closing(sqlite3.connect(DB_PATH))


def init_db():
    """Create tables and default admin user if they don't exist."""
    with db_connection() as conn:
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      is_admin INTEGER DEFAULT 0,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS metrics_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      cpu_temp REAL,
                      cpu_freq REAL,
                      cpu_percent REAL,
                      ram_percent REAL,
                      disk_percent REAL)''')

        c.execute("SELECT id FROM users WHERE username = ?", ('admin',))
        if not c.fetchone():
            default_hash = generate_password_hash('admin123')  # CHANGE THIS!
            c.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
                ('admin', default_hash),
            )

        conn.commit()
