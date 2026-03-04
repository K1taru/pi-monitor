#!/bin/bash
# init-users.sh — Initialize or reinitialize users from DEFAULT_USERS env variable
#
# Usage:
#   ./init-users.sh [--reset]
#
# Options:
#   --reset    Delete existing database and reinitialize users from .env
#   (no args)  Only create users that don't exist (safe, non-destructive)
#
# Requires:
#   - Python 3.7+
#   - Flask, python-dotenv, werkzeug installed
#   - Working .env file with DEFAULT_USERS variable
#
# Example .env:
#   DEFAULT_USERS=k1taru:mypassword:1;guest:guestpass:0

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo "ERROR: Backend directory not found at $BACKEND_DIR" >&2
    exit 1
fi

cd "$BACKEND_DIR"

# Load environment
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found in $BACKEND_DIR" >&2
    echo "Copy .env.example to .env and fill in your values" >&2
    exit 1
fi

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate || {
        echo "ERROR: Failed to activate venv" >&2
        exit 1
    }
fi

# Check for --reset flag
RESET=0
if [ "$1" = "--reset" ]; then
    RESET=1
    echo "[warn] --reset flag set: will delete existing database"
fi

python3 << 'PYTHON_SCRIPT'
import os
import sys
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# Load .env
from dotenv import load_dotenv
load_dotenv()

RESET = int(sys.argv[1]) if len(sys.argv) > 1 else 0
DB_PATH = os.environ.get('DB_PATH', 'monitor.db')

# Delete if --reset
if RESET:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"[info] Deleted {DB_PATH}")
    else:
        print(f"[info] Database does not exist, will be created fresh")

# Import and run init_db (creates tables and users)
from database import init_db
init_db()

print("[info] Database initialized successfully")

# Show what users exist
conn = sqlite3.connect(DB_PATH)
rows = conn.execute("SELECT id, username, is_admin FROM users ORDER BY id").fetchall()
print("\n[info] Current users in database:")
for row_id, username, is_admin in rows:
    admin_badge = "👤 (admin)" if is_admin else "👤"
    print(f"  {admin_badge} {username}")
print()

conn.close()
PYTHON_SCRIPT

PYTHON_EXIT=$?
if [ $PYTHON_EXIT -ne 0 ]; then
    echo "ERROR: Python initialization failed" >&2
    exit $PYTHON_EXIT
fi

echo "[success] User initialization complete"
echo "Restart the service with: sudo systemctl restart pi-monitor"
