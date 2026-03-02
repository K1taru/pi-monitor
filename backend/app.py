#!/usr/bin/env python3
"""
Raspberry Pi System Monitor Backend
Provides REST API for system metrics, authentication, and system control
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, verify_jwt_in_request
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psutil
import os

# Load .env file before anything reads os.environ
load_dotenv()
import time
import sqlite3
import contextlib
from datetime import datetime, timedelta
import json
import threading
import subprocess
from functools import wraps

# Dangerous commands that must never be executed via the remote terminal
_BLOCKED_COMMANDS = (
    'rm -rf /', 'mkfs', ':(){:|:&};:', '> /dev/sda',
    'dd if=/dev/zero', 'chmod -R 777 /', 'chown -R',
)

app = Flask(__name__)
# Read secrets from the environment so they survive restarts.
# Generate strong values with: python -c "import secrets; print(secrets.token_hex(32))"
_DEFAULT_SECRET = 'CHANGE_ME_USE_ENV_VAR_SECRET_KEY'
_DEFAULT_JWT    = 'CHANGE_ME_USE_ENV_VAR_JWT_SECRET'
app.config['SECRET_KEY']     = os.environ.get('SECRET_KEY',     _DEFAULT_SECRET)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', _DEFAULT_JWT)
if app.config['SECRET_KEY'] == _DEFAULT_SECRET:
    print('WARNING: SECRET_KEY is not set via environment variable!')
if app.config['JWT_SECRET_KEY'] == _DEFAULT_JWT:
    print('WARNING: JWT_SECRET_KEY is not set via environment variable!')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=12)

# Restrict CORS origins via the environment variable CORS_ORIGINS (comma-separated).
# Defaults to localhost in development; set explicitly in production.
_cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
CORS(app, resources={r"/api/*": {"origins": _cors_origins}})
socketio = SocketIO(app, cors_allowed_origins=_cors_origins, async_mode='threading')
jwt = JWTManager(app)

# Database initialization
DB_PATH = 'raspy_monitor.db'

def db_connection():
    """Context manager that yields a DB connection and always closes it."""
    return contextlib.closing(sqlite3.connect(DB_PATH))


def init_db():
    """Initialize SQLite database"""
    with db_connection() as conn:
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      is_admin INTEGER DEFAULT 0,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # System metrics history
        c.execute('''CREATE TABLE IF NOT EXISTS metrics_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      cpu_temp REAL,
                      cpu_freq REAL,
                      cpu_percent REAL,
                      ram_percent REAL,
                      disk_percent REAL)''')
        
        # Create default admin user if not exists
        c.execute("SELECT * FROM users WHERE username = ?", ('admin',))
        if not c.fetchone():
            default_password = generate_password_hash('admin123')  # CHANGE THIS!
            c.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
                      ('admin', default_password))
        
        conn.commit()

init_db()

# Helper functions
def get_cpu_temperature():
    """Get CPU temperature from Raspberry Pi"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read().strip()) / 1000.0
            return round(temp, 2)
    except (OSError, IOError, ValueError):
        return 0.0

def get_cpu_frequency():
    """Get current CPU frequency"""
    try:
        freq = psutil.cpu_freq()
        return round(freq.current, 2) if freq else 0.0
    except (OSError, AttributeError):
        return 0.0

def get_system_metrics():
    """Collect all system metrics"""
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'timestamp': datetime.now().isoformat(),
        'cpu': {
            'temperature': get_cpu_temperature(),
            'frequency': get_cpu_frequency(),
            'percent': round(sum(cpu_percent) / len(cpu_percent), 2),
            'per_core': [round(p, 2) for p in cpu_percent],
            'count': psutil.cpu_count()
        },
        'memory': {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        },
        'network': get_network_stats(),
        'uptime': get_uptime()
    }

def get_network_stats():
    """Get network interface statistics"""
    net_io = psutil.net_io_counters()
    return {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv
    }

def get_uptime():
    """Get system uptime in seconds"""
    return int(time.time() - psutil.boot_time())

def get_processes():
    """Get top processes by CPU and memory"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'cpu': round(proc.info['cpu_percent'], 2),
                'memory': round(proc.info['memory_percent'], 2)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Sort by CPU usage and return top 20
    processes.sort(key=lambda x: x['cpu'], reverse=True)
    return processes[:20]

def store_metrics():
    """Store current metrics in database"""
    metrics = get_system_metrics()
    with db_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO metrics_history 
                     (cpu_temp, cpu_freq, cpu_percent, ram_percent, disk_percent)
                     VALUES (?, ?, ?, ?, ?)''',
                  (metrics['cpu']['temperature'],
                   metrics['cpu']['frequency'],
                   metrics['cpu']['percent'],
                   metrics['memory']['percent'],
                   metrics['disk']['percent']))
        conn.commit()

def cleanup_old_metrics():
    """Remove metrics older than 24 hours"""
    with db_connection() as conn:
        c = conn.cursor()
        cutoff = datetime.now() - timedelta(hours=24)
        c.execute("DELETE FROM metrics_history WHERE timestamp < ?", (cutoff,))
        conn.commit()

# Background task to store metrics every minute
def metrics_collector():
    while True:
        try:
            store_metrics()
            cleanup_old_metrics()
        except Exception as e:
            print(f"Error storing metrics: {e}")
        time.sleep(60)

# Start metrics collection thread
metrics_thread = threading.Thread(target=metrics_collector, daemon=True)
metrics_thread.start()

# Authentication routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username = ?", 
                  (username,))
        user = c.fetchone()
    
    if user and check_password_hash(user[2], password):
        access_token = create_access_token(identity={
            'id': user[0],
            'username': user[1],
            'is_admin': bool(user[3])
        })
        return jsonify({
            'access_token': access_token,
            'username': user[1],
            'is_admin': bool(user[3])
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Verify JWT token"""
    current_user = get_jwt_identity()
    return jsonify({'user': current_user}), 200

@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    current_user = get_jwt_identity()
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Old and new password required'}), 400
    
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE id = ?", (current_user['id'],))
        user = c.fetchone()
        
        if user and check_password_hash(user[0], old_password):
            new_hash = generate_password_hash(new_password)
            c.execute("UPDATE users SET password_hash = ? WHERE id = ?", 
                      (new_hash, current_user['id']))
            conn.commit()
            return jsonify({'message': 'Password changed successfully'}), 200
    
    return jsonify({'error': 'Invalid old password'}), 401

# System monitoring routes
@app.route('/api/metrics/current', methods=['GET'])
@jwt_required()
def get_current_metrics():
    """Get current system metrics"""
    return jsonify(get_system_metrics()), 200

@app.route('/api/metrics/history', methods=['GET'])
@jwt_required()
def get_metrics_history():
    """Get historical metrics"""
    hours = request.args.get('hours', default=1, type=int)
    hours = min(hours, 24)  # Max 24 hours
    
    cutoff = datetime.now() - timedelta(hours=hours)
    
    with db_connection() as conn:
        c = conn.cursor()
        c.execute('''SELECT timestamp, cpu_temp, cpu_freq, cpu_percent, ram_percent, disk_percent
                     FROM metrics_history 
                     WHERE timestamp >= ?
                     ORDER BY timestamp ASC''', (cutoff,))
        rows = c.fetchall()
    
    history = []
    for row in rows:
        history.append({
            'timestamp': row[0],
            'cpu_temp': row[1],
            'cpu_freq': row[2],
            'cpu_percent': row[3],
            'ram_percent': row[4],
            'disk_percent': row[5]
        })
    
    return jsonify(history), 200

@app.route('/api/processes', methods=['GET'])
@jwt_required()
def get_process_list():
    """Get list of running processes"""
    return jsonify(get_processes()), 200

# System control routes (admin only)
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user = get_jwt_identity()
        if not current_user.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

@app.route('/api/system/governor', methods=['GET', 'POST'])
@admin_required
def cpu_governor():
    """Get or set CPU governor"""
    if request.method == 'GET':
        try:
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r') as f:
                current = f.read().strip()
            
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors', 'r') as f:
                available = f.read().strip().split()
            
            return jsonify({
                'current': current,
                'available': available
            }), 200
        except (OSError, IOError) as e:
            return jsonify({'error': str(e)}), 500
    
    else:  # POST
        data = request.get_json()
        governor = data.get('governor')
        
        if not governor:
            return jsonify({'error': 'Governor required'}), 400
        
        try:
            # Write the governor value directly instead of using a shell command,
            # which prevents shell injection attacks.
            governor_path = (
                '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
            )
            # Validate the governor is in the available list before writing
            with open(
                '/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors', 'r'
            ) as f:
                available = f.read().strip().split()
            if governor not in available:
                return jsonify({'error': f'Invalid governor: {governor}'}), 400
            subprocess.run(
                ['sudo', 'tee', governor_path],
                input=governor,
                capture_output=True,
                text=True,
                check=True,
            )
            return jsonify({'message': f'Governor set to {governor}'}), 200
        except (OSError, subprocess.CalledProcessError) as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/system/fan', methods=['GET', 'POST'])
@admin_required
def fan_control():
    """Get or set fan speed (if fan control is available)"""
    # This is a placeholder - implement based on your fan control setup
    if request.method == 'GET':
        return jsonify({
            'speed': 50,
            'auto': True,
            'available': False,
            'message': 'Fan control not configured'
        }), 200
    else:
        return jsonify({'error': 'Fan control not implemented'}), 501

@app.route('/api/system/reboot', methods=['POST'])
@admin_required
def reboot_system():
    """Reboot the system"""
    try:
        subprocess.Popen(['sudo', 'reboot'])
        return jsonify({'message': 'System rebooting...'}), 200
    except (OSError, subprocess.SubprocessError) as e:
        return jsonify({'error': str(e)}), 500

# WebSocket terminal (admin only)
active_terminals = {}

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    try:
        # Verify JWT from connection args
        token = request.args.get('token')
        if not token:
            disconnect()
            return False
        
        # Manual JWT verification for WebSocket
        from flask_jwt_extended import decode_token
        decoded = decode_token(token)
        user = decoded['sub']
        
        if not user.get('is_admin'):
            disconnect()
            return False
        
        emit('connected', {'message': 'Connected to terminal'})
    except Exception as e:
        print(f"Connection error: {e}")
        disconnect()
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    session_id = request.sid
    proc = active_terminals.pop(session_id, None)
    if proc is not None:
        try:
            proc.terminate()
        except OSError:
            pass

@socketio.on('terminal_input')
def handle_terminal_input(data):
    """Handle terminal input from client"""
    command = data.get('input', '').strip()

    # Block obviously dangerous patterns
    lower = command.lower()
    for blocked in _BLOCKED_COMMANDS:
        if blocked in lower:
            emit('terminal_output', {'output': 'Command blocked for safety reasons.\n'})
            return

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout + result.stderr
        emit('terminal_output', {'output': output or '(no output)\n'})
    except subprocess.TimeoutExpired:
        emit('terminal_output', {'output': 'Command timed out (30 s limit).\n'})
    except Exception as e:
        emit('terminal_output', {'output': f'Error: {str(e)}\n'})

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting Raspberry Pi Monitor Backend on port {port}...")
    print("Default credentials: admin / admin123 (PLEASE CHANGE!)")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
