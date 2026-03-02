# Pi Monitor

Real-time system monitoring dashboard for Raspberry Pi 5.

Live at **[raspy.gymms.space](https://raspy.gymms.space)**

## Features

- CPU temperature, frequency, and per-core usage
- Memory & disk stats
- Network I/O counters
- Historical charts (1h / 6h / 24h)
- Top processes list
- Remote terminal *(admin only)*
- CPU governor control & reboot *(admin only)*
- JWT-based authentication

## Stack

| Layer | Tech |
|-------|------|
| Backend | Flask, Flask-SocketIO, Flask-JWT-Extended, psutil, SQLite |
| Frontend | React 18, Vite, Recharts, Socket.IO, Lucide |
| Tunnel | Cloudflared → `https://raspy.gymms.space` |

## Project structure

```
pi-monitor/
├── backend/
│   ├── app.py              # Entry point (factory pattern)
│   ├── config.py            # Reads .env secrets
│   ├── extensions.py        # SocketIO + JWT instances
│   ├── database.py          # SQLite helpers
│   ├── metrics.py           # psutil collectors + background thread
│   ├── decorators.py        # admin_required
│   ├── routes/
│   │   ├── auth.py          # /api/auth/*
│   │   ├── metrics.py       # /api/metrics/*, /api/processes
│   │   ├── system.py        # /api/system/* (governor, reboot)
│   │   └── frontend.py      # SPA catch-all + /api/health
│   ├── sockets/
│   │   └── terminal.py      # WebSocket terminal
│   ├── scripts/
│   │   ├── fan-control.sh   # Fan PWM wrapper (installed to /usr/local/bin)
│   │   └── gov-control.sh   # CPU governor wrapper (installed to /usr/local/bin)
│   ├── requirements.txt
│   └── .env                 # secrets — copy from .env.example (gitignored)
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/           # Login, Dashboard
│   │   └── components/      # Terminal, SystemChart, ProcessList, SystemControls
│   ├── package.json
│   └── vite.config.js
├── setup/
│   ├── setup.sh             # One-shot automated setup script
│   ├── init-users.sh        # Re-initialize users from .env
│   ├── pi-monitor.service   # systemd unit template
│   ├── pi-monitor-sudoers   # sudoers template
│   └── SETUP.md             # Full setup guide
└── .gitattributes           # Enforces LF line endings for shell scripts
```

## Quick Start

```bash
# 1. Clone
git clone <your-repo-url> ~/pi-monitor
cd ~/pi-monitor

# 2. Configure
cp backend/.env.example backend/.env
nano backend/.env   # set SECRET_KEY, JWT_SECRET_KEY, DEFAULT_USERS

# 3. Run setup
sed -i 's/\r$//' setup/setup.sh && chmod +x setup/setup.sh
sudo ./setup/setup.sh k1taru
```

That's it. The script handles everything: frontend build, Python venv, system binaries, sudoers, systemd service, and database.

See **[setup/SETUP.md](setup/SETUP.md)** for the full guide.

## Requirements

- Python 3.9+
- Node.js + npm
- Git

## Credentials

Defined in `backend/.env` via `DEFAULT_USERS` — no hard-coded defaults.

## License

MIT
