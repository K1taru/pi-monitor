"""
System metrics collection — helpers + background collector thread.
"""
import time
import threading
import psutil
from datetime import datetime, timedelta

from database import db_connection
from logger import app_log, ops_log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_cpu_temperature():
    """Read CPU temperature from the Pi's thermal sysfs node."""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return round(float(f.read().strip()) / 1000.0, 2)
    except (OSError, IOError, ValueError):
        return 0.0


def get_cpu_frequency():
    """Return current CPU frequency in MHz."""
    try:
        freq = psutil.cpu_freq()
        return round(freq.current, 2) if freq else 0.0
    except (OSError, AttributeError):
        return 0.0


def get_network_stats():
    """Return cumulative network I/O counters."""
    net_io = psutil.net_io_counters()
    return {
        'bytes_sent':    net_io.bytes_sent,
        'bytes_recv':    net_io.bytes_recv,
        'packets_sent':  net_io.packets_sent,
        'packets_recv':  net_io.packets_recv,
    }


def get_uptime():
    """Return system uptime in seconds."""
    return int(time.time() - psutil.boot_time())


def get_system_metrics():
    """Collect and return a snapshot of all system metrics."""
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    memory = psutil.virtual_memory()
    disk   = psutil.disk_usage('/')

    return {
        'timestamp': datetime.now().isoformat(),
        'cpu': {
            'temperature': get_cpu_temperature(),
            'frequency':   get_cpu_frequency(),
            'percent':     round(sum(cpu_percent) / len(cpu_percent), 2),
            'per_core':    [round(p, 2) for p in cpu_percent],
            'count':       psutil.cpu_count(),
        },
        'memory': {
            'total':     memory.total,
            'available': memory.available,
            'percent':   memory.percent,
            'used':      memory.used,
        },
        'disk': {
            'total':   disk.total,
            'used':    disk.used,
            'free':    disk.free,
            'percent': disk.percent,
        },
        'network': get_network_stats(),
        'uptime':  get_uptime(),
    }


def get_processes():
    """Return the top 20 processes sorted by CPU usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append({
                'pid':    proc.info['pid'],
                'name':   proc.info['name'],
                'cpu':    round(proc.info['cpu_percent'],    2),
                'memory': round(proc.info['memory_percent'], 2),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(key=lambda x: x['cpu'], reverse=True)
    return processes[:20]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def store_metrics(conn):
    """Persist the current metrics snapshot to the database."""
    m = get_system_metrics()
    conn.execute(
        '''INSERT INTO metrics_history
           (cpu_temp, cpu_freq, cpu_percent, ram_percent, disk_percent)
           VALUES (?, ?, ?, ?, ?)''',
        (
            m['cpu']['temperature'],
            m['cpu']['frequency'],
            m['cpu']['percent'],
            m['memory']['percent'],
            m['disk']['percent'],
        ),
    )
    ops_log.debug(
        'Stored metrics — cpu=%.1f%% temp=%.1f°C freq=%.0fMHz ram=%.1f%% disk=%.1f%%',
        m['cpu']['percent'], m['cpu']['temperature'], m['cpu']['frequency'],
        m['memory']['percent'], m['disk']['percent'],
    )


def cleanup_old_metrics(conn):
    """Delete metrics older than 24 hours."""
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    result = conn.execute('DELETE FROM metrics_history WHERE timestamp < ?', (cutoff,))
    deleted = result.rowcount
    if deleted:
        ops_log.info('Cleaned up %d old metric(s) (before %s)', deleted, cutoff)


# ---------------------------------------------------------------------------
# Background collector
# ---------------------------------------------------------------------------

def _collector_loop():
    ops_log.info('Metrics collector thread started (interval=60s)')
    while True:
        try:
            with db_connection() as conn:
                store_metrics(conn)
                cleanup_old_metrics(conn)
        except Exception as e:
            app_log.error('Metrics collector error: %s', e)
            ops_log.error('Metrics collector error: %s', e)
        time.sleep(60)


def start_collector():
    """Start the background metrics collection thread (call once at startup)."""
    app_log.info('Starting background metrics collector')
    ops_log.info('Launching metrics-collector daemon thread')
    t = threading.Thread(target=_collector_loop, daemon=True, name='metrics-collector')
    t.start()
