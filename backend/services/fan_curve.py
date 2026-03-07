"""
Fan curve controller — software-based automatic fan speed control.

Modes
-----
  auto   — Background loop reads CPU temp and sets PWM from the user's curve
  manual — User sets speed directly via API; loop does nothing
  turbo  — Fan locked at 100 %

The hardware is always kept in manual mode (pwm1_enable = 1) so that our
software has full authority over the PWM duty cycle.
"""
import os
import subprocess
import threading
import time

from database import db_connection
from services.metrics import get_cpu_temperature
from utils.logger import app_log, ops_log

_FAN_CONTROL_BIN = os.environ.get(
    'FAN_CONTROL_BIN', '/usr/local/bin/pi-monitor-fan-control'
)

# ── Runtime state ────────────────────────────────────────────────────────────
_fan_mode: str = 'auto'
_mode_lock = threading.Lock()

DEFAULT_CURVE: list[dict[str, int]] = [
    {'temp': 40, 'speed': 0},
    {'temp': 50, 'speed': 25},
    {'temp': 60, 'speed': 50},
    {'temp': 70, 'speed': 75},
    {'temp': 80, 'speed': 100},
]


# ── Mode ─────────────────────────────────────────────────────────────────────

def get_mode() -> str:
    with _mode_lock:
        return _fan_mode


def set_mode(mode: str) -> None:
    global _fan_mode
    if mode not in ('auto', 'manual', 'turbo'):
        raise ValueError(f'Invalid fan mode: {mode}')
    with _mode_lock:
        _fan_mode = mode
    if mode == 'turbo':
        _write_pwm(255)
    ops_log.info('Fan mode → %s', mode)


# ── Curve persistence ────────────────────────────────────────────────────────

def get_curve() -> list[dict[str, int]]:
    """Return the saved curve from DB, or the built-in default."""
    try:
        with db_connection() as conn:
            rows = conn.execute(
                'SELECT temp, speed FROM fan_curve ORDER BY temp ASC'
            ).fetchall()
            if rows:
                return [{'temp': r['temp'], 'speed': r['speed']} for r in rows]
    except Exception as e:
        ops_log.error('Failed to read fan curve: %s', e)
    return [dict(p) for p in DEFAULT_CURVE]


def set_curve(points: list[dict[str, int]]) -> None:
    """Validate and persist a new fan curve (1–10 points)."""
    if not 1 <= len(points) <= 10:
        raise ValueError('Curve must have 1–10 points')
    for p in points:
        t, s = int(p['temp']), int(p['speed'])
        if not (0 <= t <= 110 and 0 <= s <= 100):
            raise ValueError(f'Out of range: temp={t}, speed={s}')
    with db_connection() as conn:
        conn.execute('DELETE FROM fan_curve')
        for p in points:
            conn.execute(
                'INSERT INTO fan_curve (temp, speed) VALUES (?, ?)',
                (int(p['temp']), int(p['speed'])),
            )
    ops_log.info('Fan curve saved (%d points)', len(points))


# ── Interpolation ────────────────────────────────────────────────────────────

def interpolate_speed(temp: float, curve: list[dict[str, int]]) -> int:
    """Linear-interpolate fan speed (0–100 %) for the given temperature."""
    if not curve:
        return 50
    curve = sorted(curve, key=lambda p: p['temp'])
    if temp <= curve[0]['temp']:
        return curve[0]['speed']
    if temp >= curve[-1]['temp']:
        return curve[-1]['speed']
    for i in range(len(curve) - 1):
        t1, s1 = curve[i]['temp'], curve[i]['speed']
        t2, s2 = curve[i + 1]['temp'], curve[i + 1]['speed']
        if t1 <= temp <= t2:
            ratio = (temp - t1) / (t2 - t1) if t2 != t1 else 0
            return round(s1 + ratio * (s2 - s1))
    return curve[-1]['speed']


# ── PWM helpers ──────────────────────────────────────────────────────────────

def _write_pwm(value: int) -> None:
    try:
        subprocess.run(
            ['sudo', _FAN_CONTROL_BIN, 'write-pwm', str(value)],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        ops_log.error('write-pwm %d failed: %s', value, e.stderr or str(e))


def set_manual_speed(speed_pct: int) -> None:
    """Apply a manual fan speed (0–100 %). Only meaningful in manual mode."""
    pwm = max(0, min(255, round(speed_pct / 100 * 255)))
    _write_pwm(pwm)
    ops_log.info('Manual fan speed: %d%% (PWM %d)', speed_pct, pwm)


def _ensure_hw_manual() -> None:
    """Keep hardware in manual mode so our software controls PWM directly."""
    try:
        subprocess.run(
            ['sudo', _FAN_CONTROL_BIN, 'write-mode', '1'],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError:
        pass


def _disable_thermal_fan() -> None:
    """Switch the thermal zone to the 'user_space' governor.

    The step_wise governor, even with pwm1_enable=1, writes cooling_device
    cur_state=0 whenever the CPU temp is below the active trip point.  On
    unpatched Pi 5 kernels (https://github.com/raspberrypi/linux/pull/5617)
    that write bypasses pwm1_enable and zeroes pwm1.  Switching to
    'user_space' stops the governor from ever autonomously writing cooling
    states, giving our software loop exclusive PWM authority.
    """
    try:
        subprocess.run(
            ['sudo', _FAN_CONTROL_BIN, 'disable-thermal-fan'],
            check=True, capture_output=True, text=True,
        )
        ops_log.info('Kernel thermal fan management disabled')
    except subprocess.CalledProcessError as e:
        ops_log.warning('Could not disable thermal fan: %s', e.stderr or str(e))


def _enable_thermal_fan() -> None:
    """Re-enable kernel thermal governor fan management."""
    try:
        subprocess.run(
            ['sudo', _FAN_CONTROL_BIN, 'enable-thermal-fan'],
            check=True, capture_output=True, text=True,
        )
        ops_log.info('Kernel thermal fan management re-enabled')
    except subprocess.CalledProcessError as e:
        ops_log.warning('Could not enable thermal fan: %s', e.stderr or str(e))


# ── Background control loop ─────────────────────────────────────────────────

def _control_loop() -> None:
    ops_log.info('Fan curve controller loop started')
    last_pwm = -1

    while True:
        try:
            mode = get_mode()

            if mode == 'auto':
                temp = get_cpu_temperature()
                curve = get_curve()
                speed_pct = interpolate_speed(temp, curve)
                pwm = max(0, min(255, round(speed_pct / 100 * 255)))
                if pwm != last_pwm:
                    _write_pwm(pwm)
                    last_pwm = pwm
                    ops_log.debug(
                        'Fan auto: %.1f°C → %d%% (PWM %d)', temp, speed_pct, pwm
                    )

            elif mode == 'turbo':
                if last_pwm != 255:
                    _write_pwm(255)
                    last_pwm = 255

            else:  # manual — user controls via API
                last_pwm = -1  # reset so next auto switch recalculates

        except Exception as e:
            ops_log.error('Fan control loop error: %s', e)

        time.sleep(3)


# ── Startup ──────────────────────────────────────────────────────────────────

def start_fan_controller() -> None:
    """Ensure hardware manual mode and start the background control loop."""
    _ensure_hw_manual()
    _disable_thermal_fan()
    threading.Thread(
        target=_control_loop, daemon=True, name='fan-controller'
    ).start()


def fan_boost_on_start(duration: int = 60) -> None:
    """Run fan at 100 % for *duration* seconds on startup, then switch to auto."""
    def _boost():
        try:
            set_mode('turbo')
            app_log.info('Fan boost started — turbo for %ds', duration)
            ops_log.info('Fan boost: turbo, duration=%ds', duration)
            time.sleep(duration)
            set_mode('auto')
            app_log.info('Fan boost finished — switched to auto')
            ops_log.info('Fan boost complete → auto')
        except Exception as e:
            app_log.error('Fan boost error: %s', e)
            ops_log.error('Fan boost error: %s', e)

    threading.Thread(target=_boost, daemon=True, name='fan-boost').start()
